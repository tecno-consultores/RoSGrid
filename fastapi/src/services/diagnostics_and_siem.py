# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""
Servicio de Paquete de Soporte 1-Click (.zip/.tar.gz) con Sanitización de Secretos
y Conector SIEM Multi-Protocolo del ISP (Graylog GELF / Grafana Loki / Syslog RFC 5424) — Spec 72.
"""

import asyncio
import base64
import io
import json
import logging
import platform
import re
import socket
import tarfile
import time
import zipfile
from collections import deque
from datetime import UTC, datetime
from typing import Any

import httpx

from src.core.config import settings
from src.redis_layer.client import get_redis_client
from src.schemas.diagnostics_siem import (
    DiagnosticBundleRequest,
    DiagnosticBundleResponse,
    SiemForwarderConfigResponse,
    SiemForwarderConfigUpdateRequest,
    SiemTestDeliveryResponse,
    UiErrorTelemetryItem,
    UiErrorTelemetryRecordResponse,
)

logger = logging.getLogger(__name__)

_BACKEND_LOG_RING_BUFFER: deque[str] = deque(maxlen=settings.ROSGRID_DIAGNOSTIC_LOG_RING_SIZE)
_RING_HANDLER_INSTALLED: bool = False

_SECRET_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9\-._~+/]+=*"), r"\1[REDACTED]"),
    (
        re.compile(
            r'(?i)("(?:password|passwd|secret|api_key|apikey|auth_token|access_token|refresh_token|private_key|master_vault_key|jwt_secret_key|csrf_hmac_secret)"\s*:\s*")[^"]*(")'
        ),
        r"\1[REDACTED]\2",
    ),
    (
        re.compile(
            r"(?i)((?:password|passwd|secret|api_key|apikey|auth_token|access_token|refresh_token|private_key|ROSGRID_MASTER_VAULT_KEY|ROSGRID_JWT_SECRET_KEY|ROSGRID_CSRF_HMAC_SECRET)\s*=\s*)[^\s,;\"']+"
        ),
        r"\1[REDACTED]",
    ),
)

_LEVEL_WEIGHTS: dict[str, int] = {
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


class _InMemoryDiagnosticLogHandler(logging.Handler):
    """Handler ligero en memoria que conserva las últimas líneas de log del backend (CC = 2)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            _BACKEND_LOG_RING_BUFFER.append(msg)
        except Exception:  # nosec B110
            pass


def ensure_diagnostic_log_handler() -> None:
    """Instala de forma idempotente el colector circular de logs en el root logger (CC = 2)."""
    global _RING_HANDLER_INSTALLED
    if _RING_HANDLER_INSTALLED:
        return
    handler = _InMemoryDiagnosticLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)
    _RING_HANDLER_INSTALLED = True


def append_diagnostic_log_line(level: str, logger_name: str, message: str) -> None:
    """Agrega manualmente una línea estructurada al Ring Buffer de diagnóstico (CC = 1)."""
    ensure_diagnostic_log_handler()
    ts = datetime.now(UTC).isoformat()
    _BACKEND_LOG_RING_BUFFER.append(f"{ts} [{level.upper()}] {logger_name}: {message}")


def _redact_literal_secrets(sanitized: str) -> tuple[str, int]:
    """Expurga secretos literales de configuración si aparecen en el texto (CC = 3)."""
    redacted = sanitized
    count = 0
    for literal in (
        settings.ROSGRID_MASTER_VAULT_KEY,
        settings.ROSGRID_JWT_SECRET_KEY,
        settings.ROSGRID_CSRF_HMAC_SECRET,
    ):
        if literal and literal in redacted:
            occurrences = redacted.count(literal)
            redacted = redacted.replace(literal, "[REDACTED]")
            count += occurrences
    return redacted, count


def redact_sensitive_diagnostic_text(raw_text: str) -> tuple[str, int]:
    """Expurga secretos, tokens Bearer, llaves de bóveda y contraseñas de cualquier texto (CC = 3)."""
    if not raw_text:
        return "", 0
    sanitized = raw_text
    total_redactions = 0
    for pattern, replacement in _SECRET_REDACTION_PATTERNS:
        sanitized, count = pattern.subn(replacement, sanitized)
        total_redactions += count
    sanitized, lit_count = _redact_literal_secrets(sanitized)
    total_redactions += lit_count
    return sanitized, total_redactions


def _ui_errors_redis_key(tenant_id: str) -> str:
    """Clave KeyDB donde se almacena el Ring Buffer de errores de UI por tenant (CC = 1)."""
    return f"rg:diagnostics:ui_errors:{tenant_id or 'global'}"


def _siem_config_redis_key(tenant_id: str) -> str:
    """Clave KeyDB donde se almacena la configuración SIEM del ISP por tenant (CC = 1)."""
    return f"rg:siem:config:{tenant_id or 'global'}"


def _default_siem_config_dict() -> dict[str, Any]:
    """Retorna la configuración predeterminada del conector SIEM del ISP (CC = 1)."""
    return {
        "enabled": False,
        "protocol": "GELF_UDP",
        "host": "127.0.0.1",
        "port": 12201,
        "endpoint_path": "/gelf",
        "use_tls": False,
        "min_level": "WARNING",
        "include_frontend_errors": True,
        "include_audit_events": True,
        "custom_stream_label": "rosgrid-noc",
        "auth_token": "",
        "updated_at": None,
    }


def _to_siem_config_response(raw_cfg: dict[str, Any]) -> SiemForwarderConfigResponse:
    """Convierte el diccionario interno de configuración SIEM al esquema público sin token (CC = 1)."""
    merged = {**_default_siem_config_dict(), **raw_cfg}
    return SiemForwarderConfigResponse(
        enabled=bool(merged["enabled"]),
        protocol=merged["protocol"],
        host=str(merged["host"]),
        port=int(merged["port"]),
        endpoint_path=str(merged["endpoint_path"]),
        use_tls=bool(merged["use_tls"]),
        min_level=merged["min_level"],
        include_frontend_errors=bool(merged["include_frontend_errors"]),
        include_audit_events=bool(merged["include_audit_events"]),
        custom_stream_label=str(merged["custom_stream_label"]),
        has_auth_token=bool(merged.get("auth_token")),
        updated_at=merged.get("updated_at"),
    )


async def _load_raw_siem_config(tenant_id: str) -> dict[str, Any]:
    """Lee desde KeyDB la configuración SIEM del tenant con fallback seguro (CC = 3)."""
    base = _default_siem_config_dict()
    try:
        r = get_redis_client()
        raw_json = await r.get(_siem_config_redis_key(tenant_id))
        if raw_json:
            base.update(json.loads(raw_json))
    except Exception as exc:
        logger.debug("Fallback a configuración SIEM por defecto: %s", exc)
    return base


async def get_siem_forwarder_config(tenant_id: str) -> SiemForwarderConfigResponse:
    """Obtiene la configuración actual del conector SIEM del ISP (CC = 1)."""
    raw_cfg = await _load_raw_siem_config(tenant_id)
    return _to_siem_config_response(raw_cfg)


def _resolve_siem_token(current_token: str, new_token: str | None) -> str:
    """Conserva el token existente si el payload no provee uno nuevo (CC = 2)."""
    if new_token:
        return new_token
    return current_token or ""


def _build_updated_siem_dict(current: dict[str, Any], payload: SiemForwarderConfigUpdateRequest) -> dict[str, Any]:
    """Construye el diccionario de configuración SIEM consolidado (CC = 1)."""
    return {
        "enabled": payload.enabled,
        "protocol": payload.protocol,
        "host": payload.host.strip(),
        "port": payload.port,
        "endpoint_path": payload.endpoint_path.strip() or "/gelf",
        "use_tls": payload.use_tls,
        "min_level": payload.min_level,
        "include_frontend_errors": payload.include_frontend_errors,
        "include_audit_events": payload.include_audit_events,
        "custom_stream_label": payload.custom_stream_label.strip() or "rosgrid-noc",
        "auth_token": _resolve_siem_token(str(current.get("auth_token", "")), payload.auth_token),
        "updated_at": datetime.now(UTC).isoformat(),
    }


async def update_siem_forwarder_config(
    tenant_id: str,
    payload: SiemForwarderConfigUpdateRequest,
) -> SiemForwarderConfigResponse:
    """Persiste en KeyDB la configuración del conector SIEM del ISP preservando el token si no cambia (CC = 2)."""
    current = await _load_raw_siem_config(tenant_id)
    updated = _build_updated_siem_dict(current, payload)
    try:
        r = get_redis_client()
        await r.set(_siem_config_redis_key(tenant_id), json.dumps(updated))
    except Exception as exc:
        logger.warning("No se pudo persistir configuración SIEM en KeyDB: %s", exc)
    append_diagnostic_log_line(
        "INFO",
        "siem.config",
        f"Configuración SIEM actualizada (enabled={updated['enabled']}, protocol={updated['protocol']}, target={updated['host']}:{updated['port']})",
    )
    return _to_siem_config_response(updated)


async def record_ui_error_telemetry(
    tenant_id: str,
    item: UiErrorTelemetryItem,
    reported_by_username: str = "anonymous",
    reported_by_role: str = "UNKNOWN",
) -> UiErrorTelemetryRecordResponse:
    """Almacena un error de UI (de cualquier operador L1/L2/Admin) en el Ring Buffer de KeyDB y lo reenvía al SIEM si aplica (CC = 3)."""
    sanitized_msg, _ = redact_sensitive_diagnostic_text(item.message)
    record_dict = item.model_dump()
    record_dict["message"] = sanitized_msg
    record_dict["reported_by_username"] = reported_by_username
    record_dict["reported_by_role"] = reported_by_role
    buffered_count = 1
    try:
        r = get_redis_client()
        key = _ui_errors_redis_key(tenant_id)
        await r.lpush(key, json.dumps(record_dict))
        await r.ltrim(key, 0, 99)
        await r.expire(key, 86400 * 7)
        buffered_count = int(await r.llen(key))
    except Exception as exc:
        logger.debug("No se pudo almacenar telemetría UI en KeyDB: %s", exc)

    forwarded = await forward_event_to_isp_siem_if_enabled(
        tenant_id=tenant_id,
        level="ERROR",
        source_layer="frontend",
        short_message=f"[{item.category}] ({reported_by_username}/{reported_by_role}) {sanitized_msg}",
        extra_fields={
            "route": item.route,
            "status_code": item.status_code,
            "url": item.url,
            "reported_by_username": reported_by_username,
            "reported_by_role": reported_by_role,
        },
    )
    return UiErrorTelemetryRecordResponse(
        recorded=True,
        buffered_count=buffered_count,
        forwarded_to_siem=forwarded,
    )


async def _fetch_buffered_ui_errors(tenant_id: str) -> list[dict[str, Any]]:
    """Recupera los eventos de error de UI almacenados en KeyDB para el tenant (CC = 3)."""
    items: list[dict[str, Any]] = []
    try:
        r = get_redis_client()
        raw_list = await r.lrange(_ui_errors_redis_key(tenant_id), 0, 99)
        items = [json.loads(entry) for entry in raw_list if entry]
    except Exception as exc:
        logger.debug("Fallback al leer errores de UI en KeyDB: %s", exc)
    return items


def _create_zip_bytes(files_map: dict[str, str]) -> bytes:
    """Empaqueta un mapa de rutas y contenidos de texto en un archivo .zip en memoria (CC = 2)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in files_map.items():
            zf.writestr(arcname, content.encode("utf-8"))
    return buf.getvalue()


def _create_targz_bytes(files_map: dict[str, str]) -> bytes:
    """Empaqueta un mapa de rutas y contenidos de texto en un archivo .tar.gz en memoria (CC = 2)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for arcname, content in files_map.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=arcname)
            info.size = len(data)
            info.mtime = int(time.time())
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _collect_sanitized_Artifacts(
    tenant_id: str,
    user_role: str,
    request: DiagnosticBundleRequest,
    stored_ui_errors: list[dict[str, Any]],
    siem_cfg: SiemForwarderConfigResponse,
) -> tuple[dict[str, str], int]:
    """Construye y sanitiza los 4 artefactos del paquete de soporte (CC = 3)."""
    now_iso = datetime.now(UTC).isoformat()
    recent_logs = list(_BACKEND_LOG_RING_BUFFER)[-request.log_lines_limit :]
    if not recent_logs:
        recent_logs = [f"{now_iso} [INFO] rosgrid.diagnostics: Ring buffer inicializado sin errores críticos."]

    combined_ui_errors = [item.model_dump() for item in request.include_frontend_buffer] + stored_ui_errors
    metadata_doc = {
        "product": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "generated_at": now_iso,
        "tenant_id": tenant_id,
        "requested_by_role": user_role,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "operator_notes": request.operator_notes or "",
        "frontend_events_count": len(combined_ui_errors),
        "backend_log_lines_count": len(recent_logs),
    }
    raw_files = {
        "metadata.json": json.dumps(metadata_doc, indent=2, ensure_ascii=False),
        "frontend/ui_errors.json": json.dumps(combined_ui_errors, indent=2, ensure_ascii=False),
        "backend/application_logs.log": "\n".join(recent_logs),
        "backend/siem_forwarder_status.json": siem_cfg.model_dump_json(indent=2),
    }
    sanitized_files: dict[str, str] = {}
    total_redacted = 0
    for path, content in raw_files.items():
        clean_text, count = redact_sensitive_diagnostic_text(content)
        sanitized_files[path] = clean_text
        total_redacted += count
    return sanitized_files, total_redacted


async def build_support_bundle_archive(
    tenant_id: str,
    user_role: str,
    request: DiagnosticBundleRequest,
) -> DiagnosticBundleResponse:
    """Ensambla el paquete .zip o .tar.gz de diagnóstico 1-Click con sanitización garantizada (CC = 2)."""
    ensure_diagnostic_log_handler()
    stored_ui_errors = await _fetch_buffered_ui_errors(tenant_id)
    siem_cfg = await get_siem_forwarder_config(tenant_id)
    files_map, redacted_count = _collect_sanitized_Artifacts(
        tenant_id=tenant_id,
        user_role=user_role,
        request=request,
        stored_ui_errors=stored_ui_errors,
        siem_cfg=siem_cfg,
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    if request.format == "tar.gz":
        archive_bytes = _create_targz_bytes(files_map)
        filename = f"rosgrid-support-bundle-{stamp}.tar.gz"
        content_type = "application/gzip"
    else:
        archive_bytes = _create_zip_bytes(files_map)
        filename = f"rosgrid-support-bundle-{stamp}.zip"
        content_type = "application/zip"

    return DiagnosticBundleResponse(
        filename=filename,
        format=request.format,
        content_type=content_type,
        size_bytes=len(archive_bytes),
        redacted_secrets_count=redacted_count,
        included_files=list(files_map.keys()),
        generated_at=datetime.now(UTC),
        bundle_base64=base64.b64encode(archive_bytes).decode("ascii"),
    )


def _send_udp_datagram(host: str, port: int, payload: bytes) -> None:
    """Envía un datagrama UDP hacia el colector Graylog GELF o Syslog del ISP (CC = 1)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(settings.ROSGRID_SIEM_FORWARDER_TIMEOUT_SECONDS)
        sock.sendto(payload, (host, port))


def _send_tcp_syslog_frame(host: str, port: int, payload: bytes) -> None:
    """Envía una trama Syslog RFC 5424 sobre TCP hacia el colector del ISP (CC = 1)."""
    with socket.create_connection((host, port), timeout=settings.ROSGRID_SIEM_FORWARDER_TIMEOUT_SECONDS) as sock:
        sock.sendall(payload + b"\n")


async def _send_http_siem_payload(
    url: str,
    body: dict[str, Any],
    auth_token: str,
) -> None:
    """Envía un payload JSON mediante HTTP POST hacia Graylog GELF HTTP o Grafana Loki (CC = 2)."""
    from src.services.network_events import is_safe_outbound_service_url

    if not is_safe_outbound_service_url(url):
        raise ValueError(f"URL de colector SIEM bloqueada por política Anti-SSRF: {url}")
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    async with httpx.AsyncClient(timeout=float(settings.ROSGRID_SIEM_FORWARDER_TIMEOUT_SECONDS)) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()


async def _dispatch_gelf(
    proto: str,
    host: str,
    port: int,
    scheme: str,
    path: str,
    stream_label: str,
    tenant_id: str,
    level: str,
    source_layer: str,
    clean_message: str,
    extra_fields: dict[str, Any] | None,
    auth_token: str,
) -> str:
    """Despacha un payload en formato Graylog GELF v1.1 vía UDP o HTTP (CC = 2)."""
    gelf_body: dict[str, Any] = {
        "version": "1.1",
        "host": stream_label,
        "short_message": clean_message,
        "timestamp": time.time(),
        "level": 3 if level in ("ERROR", "CRITICAL") else 4,
        "_tenant_id": tenant_id,
        "_source_layer": source_layer,
        "_severity": level,
    }
    if extra_fields:
        for k, v in extra_fields.items():
            gelf_body[f"_{k}"] = v
    if proto == "GELF_UDP":
        await asyncio.to_thread(_send_udp_datagram, host, port, json.dumps(gelf_body).encode("utf-8"))
        return f"udp://{host}:{port}"
    target_url = f"{scheme}://{host}:{port}{path}"
    await _send_http_siem_payload(target_url, gelf_body, auth_token)
    return target_url


async def _dispatch_loki(
    host: str,
    port: int,
    scheme: str,
    path: str,
    stream_label: str,
    tenant_id: str,
    level: str,
    source_layer: str,
    clean_message: str,
    auth_token: str,
) -> str:
    """Despacha una línea de log estructurada hacia Grafana Loki HTTP Push (CC = 1)."""
    target_url = f"{scheme}://{host}:{port}{path}"
    ns_ts = str(int(time.time() * 1_000_000_000))
    loki_body = {
        "streams": [
            {
                "stream": {
                    "app": "rosgrid",
                    "stream": stream_label,
                    "tenant_id": tenant_id,
                    "level": level,
                    "layer": source_layer,
                },
                "values": [[ns_ts, clean_message]],
            }
        ]
    }
    await _send_http_siem_payload(target_url, loki_body, auth_token)
    return target_url


async def _dispatch_syslog(
    proto: str,
    host: str,
    port: int,
    stream_label: str,
    level: str,
    source_layer: str,
    clean_message: str,
) -> str:
    """Despacha un mensaje RFC 5424 hacia el Syslog central del ISP sobre UDP o TCP (CC = 2)."""
    syslog_line = f"<134>1 {datetime.now(UTC).isoformat()} {stream_label} rosgrid - - - [{level}] [{source_layer}] {clean_message}"
    if proto == "SYSLOG_TCP":
        await asyncio.to_thread(_send_tcp_syslog_frame, host, port, syslog_line.encode("utf-8"))
        return f"tcp://{host}:{port}"
    await asyncio.to_thread(_send_udp_datagram, host, port, syslog_line.encode("utf-8"))
    return f"udp://{host}:{port}"


async def _dispatch_siem_protocol(
    cfg: dict[str, Any],
    tenant_id: str,
    level: str,
    source_layer: str,
    clean_message: str,
    extra_fields: dict[str, Any] | None = None,
) -> str:
    """Despacha el evento sanitizado según el protocolo SIEM configurado por el ISP (CC = 3)."""
    proto = str(cfg.get("protocol", "GELF_UDP"))
    host = str(cfg.get("host", "127.0.0.1"))
    port = int(cfg.get("port", 12201))
    stream_label = str(cfg.get("custom_stream_label", "rosgrid-noc"))
    scheme = "https" if cfg.get("use_tls") else "http"
    path = str(cfg.get("endpoint_path", "/gelf"))
    auth_token = str(cfg.get("auth_token", ""))

    if proto in ("GELF_UDP", "GELF_HTTP"):
        return await _dispatch_gelf(
            proto, host, port, scheme, path, stream_label, tenant_id, level, source_layer, clean_message, extra_fields, auth_token
        )
    if proto == "LOKI_HTTP":
        return await _dispatch_loki(
            host, port, scheme, path, stream_label, tenant_id, level, source_layer, clean_message, auth_token
        )
    return await _dispatch_syslog(proto, host, port, stream_label, level, source_layer, clean_message)


def _should_skip_siem_forward(cfg: dict[str, Any], level: str, source_layer: str) -> bool:
    """Evalúa si el evento debe descartarse según filtros de severidad y habilitación (CC = 3)."""
    if not cfg.get("enabled"):
        return True
    if source_layer == "frontend" and not cfg.get("include_frontend_errors", True):
        return True
    min_weight = _LEVEL_WEIGHTS.get(str(cfg.get("min_level", "WARNING")), 30)
    event_weight = _LEVEL_WEIGHTS.get(level.upper(), 20)
    return event_weight < min_weight


async def forward_event_to_isp_siem_if_enabled(
    tenant_id: str,
    level: str,
    source_layer: str,
    short_message: str,
    extra_fields: dict[str, Any] | None = None,
) -> bool:
    """Evalúa filtros de severidad y reenvía el evento de forma fail-silent al SIEM del ISP (CC = 2)."""
    cfg = await _load_raw_siem_config(tenant_id)
    if _should_skip_siem_forward(cfg, level, source_layer):
        return False
    clean_msg, _ = redact_sensitive_diagnostic_text(short_message)
    try:
        await _dispatch_siem_protocol(cfg, tenant_id, level.upper(), source_layer, clean_msg, extra_fields)
        return True
    except Exception as exc:
        logger.debug("Fallo fail-silent al reenviar evento al SIEM del ISP: %s", exc)
        return False


async def send_siem_test_event(tenant_id: str) -> SiemTestDeliveryResponse:
    """Dispara un evento de prueba hacia el colector SIEM configurado y mide la latencia (CC = 2)."""
    cfg = await _load_raw_siem_config(tenant_id)
    proto = cfg.get("protocol", "GELF_UDP")
    start = time.perf_counter()
    try:
        target = await _dispatch_siem_protocol(
            cfg=cfg,
            tenant_id=tenant_id,
            level="INFO",
            source_layer="diagnostics_probe",
            clean_message="Evento de prueba de conectividad SIEM enviado desde RoSGrid NOC.",
            extra_fields={"probe": "siem_connectivity_test"},
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return SiemTestDeliveryResponse(
            success=True,
            protocol=proto,
            target=target,
            latency_ms=elapsed_ms,
            detail=f"Evento de prueba entregado exitosamente a {target} ({proto}).",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
        target_fallback = f"{cfg.get('host', '127.0.0.1')}:{cfg.get('port', 12201)}"
        return SiemTestDeliveryResponse(
            success=False,
            protocol=proto,
            target=target_fallback,
            latency_ms=elapsed_ms,
            detail=f"Error al conectar con el colector SIEM ({proto}): {exc}",
        )
