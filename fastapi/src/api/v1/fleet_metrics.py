# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import logging
import re
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_tenant_db_session
from src.models.core import Tenant
from src.models.inventory import Router
from src.redis_layer.client import get_redis_client
from src.services.cve_matcher import evaluate_router_cves

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics/fleet", tags=["Fleet Prometheus Metrics"])

_UPTIME_MULTIPLIERS: dict[str, int] = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}

METRIC_HEADERS: list[str] = [
    "# HELP rosgrid_router_status Estado de conexion (1=ONLINE, 0=OFFLINE)\n",
    "# TYPE rosgrid_router_status gauge\n",
    "# HELP rosgrid_router_cpu_percent Porcentaje de CPU en vivo (0 a 100)\n",
    "# TYPE rosgrid_router_cpu_percent gauge\n",
    "# HELP rosgrid_router_memory_usage_ratio Proporcion de memoria RAM utilizada (0.0 a 1.0)\n",
    "# TYPE rosgrid_router_memory_usage_ratio gauge\n",
    "# HELP rosgrid_router_uptime_seconds Tiempo de actividad continuo del router en segundos\n",
    "# TYPE rosgrid_router_uptime_seconds gauge\n",
    "# HELP rosgrid_router_temperature_celsius Temperatura de CPU o placa en grados Celsius\n",
    "# TYPE rosgrid_router_temperature_celsius gauge\n",
    "# HELP rosgrid_router_voltage_volts Voltaje de alimentacion DC en voltios\n",
    "# TYPE rosgrid_router_voltage_volts gauge\n",
    "# HELP rosgrid_router_active_cves_count Cantidad de CVEs pendientes por criticidad\n",
    "# TYPE rosgrid_router_active_cves_count gauge\n",
    "# HELP rosgrid_router_syslog_critical_events_total Total acumulado de eventos criticos detectados en Syslog\n",
    "# TYPE rosgrid_router_syslog_critical_events_total counter\n",
]


def _parse_ros_uptime_to_seconds(uptime_str: str | int | None) -> int:
    """Convierte cadenas RouterOS v7 ('2w3d4h5m6s') o enteros a segundos (CC = 3)."""
    if not uptime_str:
        return 0
    raw_str = str(uptime_str).strip()
    if raw_str.isdigit():
        return int(raw_str)
    matches = re.findall(r"(\d+)([wdhms])", raw_str.lower())
    return sum(int(val) * _UPTIME_MULTIPLIERS[unit] for val, unit in matches)


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convierte de forma segura a float o devuelve valor por defecto (CC = 2)."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Convierte de forma segura a int o devuelve valor por defecto (CC = 2)."""
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _extract_raw_uptime(raw: Mapping[Any, Any]) -> int:
    """Extrae y normaliza el uptime en segundos desde el hash de KeyDB (CC = 2)."""
    val = raw.get("uptime_seconds")
    if val is not None:
        return _safe_int(val)
    return _parse_ros_uptime_to_seconds(raw.get("uptime"))


def _extract_raw_temp(raw: Mapping[Any, Any]) -> float:
    """Extrae la temperatura de CPU o placa admitiendo variantes de clave RouterOS (CC = 3)."""
    for k in ("temperature_celsius", "temperature", "cpu_temperature"):
        if k in raw and raw[k] is not None:
            return _safe_float(raw[k])
    return 0.0


def _extract_raw_voltage(raw: Mapping[Any, Any]) -> float:
    """Extrae el voltaje de alimentación admitiendo variantes de clave RouterOS (CC = 3)."""
    for k in ("voltage_volts", "voltage"):
        if k in raw and raw[k] is not None:
            return _safe_float(raw[k])
    return 0.0


def _validate_scrape_auth(authorization: str | None = Header(None)) -> None:
    """Valida token Bearer configurado para scraping Prometheus (CC = 5)."""
    import hmac as _hmac

    expected_token = settings.ROSGRID_PROMETHEUS_SCRAPE_TOKEN
    if not expected_token:
        if settings.ROSGRID_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "PROMETHEUS_UNAUTHORIZED",
                    "message": "ROSGRID_PROMETHEUS_SCRAPE_TOKEN es obligatorio en producción.",
                },
            )
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "PROMETHEUS_UNAUTHORIZED", "message": "Bearer token requerido para scraping."},
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if not _hmac.compare_digest(token.encode("utf-8"), expected_token.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "PROMETHEUS_UNAUTHORIZED", "message": "Token de scraping inválido."},
        )


def _format_metric_line(name: str, labels: dict[str, str], value: Any) -> str:
    """Formatea una línea individual en formato estándar OpenMetrics (CC = 1)."""
    labels_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    return f"{name}{{{labels_str}}} {value}\n"


def _build_router_labels(r: Router) -> dict[str, str]:
    """Construye etiquetas canónicas con identidad y versión de RouterOS (CC = 3)."""
    return {
        "tenant_id": str(r.tenant_id),
        "router_id": str(r.id),
        "identity": r.ros_identity or r.display_name,
        "model": r.model_name or "unknown",
        "ros_version": r.ros_version or "unknown",
    }


async def _get_router_ephemeral_telemetry(tenant_id: Any, router_id: Any) -> dict[str, Any]:
    """Recupera la telemetría efímera de hardware desde KeyDB en microsegundos (CC = 2)."""
    default_data = {
        "cpu_percent": 0.0,
        "memory_usage_ratio": 0.0,
        "uptime_seconds": 0,
        "temperature_celsius": 0.0,
        "voltage_volts": 0.0,
        "syslog_critical_events_total": 0,
    }
    try:
        redis = get_redis_client()
        raw = await redis.hgetall(f"rg:{tenant_id}:router:{router_id}:state")
        if not raw:
            return default_data
        return {
            "cpu_percent": _safe_float(raw.get("cpu_percent")),
            "memory_usage_ratio": _safe_float(raw.get("memory_usage_ratio")),
            "uptime_seconds": _extract_raw_uptime(raw),
            "temperature_celsius": _extract_raw_temp(raw),
            "voltage_volts": _extract_raw_voltage(raw),
            "syslog_critical_events_total": _safe_int(raw.get("syslog_critical_events_total")),
        }
    except Exception:
        return default_data


def _append_router_metrics(lines: list[str], r: Router, telem: dict[str, Any]) -> None:
    """Genera las líneas OpenMetrics para un router individual (CC = 2)."""
    labels = _build_router_labels(r)
    status_val = 1 if r.is_reachable else 0
    lines.append(_format_metric_line("rosgrid_router_status", labels, status_val))
    lines.append(_format_metric_line("rosgrid_router_cpu_percent", labels, telem["cpu_percent"]))
    lines.append(_format_metric_line("rosgrid_router_memory_usage_ratio", labels, telem["memory_usage_ratio"]))
    lines.append(_format_metric_line("rosgrid_router_uptime_seconds", labels, telem["uptime_seconds"]))
    lines.append(_format_metric_line("rosgrid_router_temperature_celsius", labels, telem["temperature_celsius"]))
    lines.append(_format_metric_line("rosgrid_router_voltage_volts", labels, telem["voltage_volts"]))

    base_labels = {
        "tenant_id": labels["tenant_id"],
        "router_id": labels["router_id"],
        "identity": labels["identity"],
        "model": labels["model"],
    }
    cve_eval = evaluate_router_cves(r.id, r.display_name, r.ros_version)
    crit_labels = {**base_labels, "severity": "critical"}
    lines.append(_format_metric_line("rosgrid_router_active_cves_count", crit_labels, cve_eval.critical_count))
    high_labels = {**base_labels, "severity": "high"}
    lines.append(_format_metric_line("rosgrid_router_active_cves_count", high_labels, cve_eval.high_count))

    lines.append(
        _format_metric_line(
            "rosgrid_router_syslog_critical_events_total", base_labels, telem["syslog_critical_events_total"]
        )
    )


@router.get("", response_class=Response)
async def get_prometheus_fleet_metrics(
    db: AsyncSession = Depends(get_tenant_db_session),
    _auth: None = Depends(_validate_scrape_auth),
) -> Response:
    """Exportador dinámico de telemetría de flota en formato estándar Prometheus (cero persistencia en Postgres)."""
    if type(db) is AsyncSession:
        from src.db.session import set_tenant_context

        await set_tenant_context(db, None, is_superadmin=True)
    query = (
        select(Router)
        .join(Tenant, Router.tenant_id == Tenant.id)
        .where(Router.admin_state == "PRODUCTION", Tenant.prometheus_fleet_exporter_enabled.is_(True))
    )
    result = await db.execute(query)
    routers = list(result.scalars().all())

    lines: list[str] = list(METRIC_HEADERS)
    for r in routers:
        telem = await _get_router_ephemeral_telemetry(r.tenant_id, r.id)
        _append_router_metrics(lines, r, telem)

    content = "".join(lines)
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")
