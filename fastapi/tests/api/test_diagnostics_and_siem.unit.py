# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""
Pruebas unitarias para Paquete de Soporte 1-Click (.zip/.tar.gz) con Sanitización Zero-Leak
y Conector SIEM Multi-Protocolo del ISP (Spec 72 / Hito 29).
"""

import base64
import io
import json
import tarfile
import uuid
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.core.config import settings
from src.models.core import SystemRoleEnum
from src.schemas.diagnostics_siem import (
    DiagnosticBundleRequest,
    SiemForwarderConfigUpdateRequest,
    UiErrorTelemetryItem,
)
from src.services.diagnostics_and_siem import (
    _dispatch_siem_protocol,
    _InMemoryDiagnosticLogHandler,
    append_diagnostic_log_line,
    build_support_bundle_archive,
    ensure_diagnostic_log_handler,
    forward_event_to_isp_siem_if_enabled,
    get_siem_forwarder_config,
    record_ui_error_telemetry,
    redact_sensitive_diagnostic_text,
    send_siem_test_event,
    update_siem_forwarder_config,
)
from tests.conftest import FakeAsyncRedis


async def _create_test_session(fake_redis: FakeAsyncRedis, role: SystemRoleEnum) -> tuple[str, dict[str, str]]:
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = f"sess-diag-{role.value.lower()}"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": f"user_{role.value.lower()}",
            "role": role.value,
        },
    )

    token = create_jwt_access_token(user_id, tenant_id, "default-tenant", session_id, role.value, True)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": "test-csrf-token",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    return tenant_id, headers


def test_redact_sensitive_diagnostic_text_patterns() -> None:
    """Verifica que el motor de sanitización expurge Bearer tokens, contraseñas y llaves maestras."""
    raw = (
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz\n"
        '{"password": "supersecretpassword123", "api_key": "secret-key-abc", "safe": "value"}\n'
        "password=plain_pass_value; ROSGRID_MASTER_VAULT_KEY=vaultkey999\n"
    )
    clean, count = redact_sensitive_diagnostic_text(raw)
    assert count >= 4
    assert "supersecretpassword123" not in clean
    assert "secret-key-abc" not in clean
    assert "plain_pass_value" not in clean
    assert "vaultkey999" not in clean
    assert "eyJhbGciOi" not in clean
    assert "[REDACTED]" in clean
    assert '"safe": "value"' in clean


def test_redact_sensitive_diagnostic_text_empty_and_literal() -> None:
    """Verifica cadenas vacías y reemplazo de secretos literales de configuración."""
    assert redact_sensitive_diagnostic_text("") == ("", 0)
    if settings.ROSGRID_MASTER_VAULT_KEY:
        text = f"La llave es {settings.ROSGRID_MASTER_VAULT_KEY} para descifrar."
        clean, count = redact_sensitive_diagnostic_text(text)
        assert count >= 1
        assert settings.ROSGRID_MASTER_VAULT_KEY not in clean
        assert "[REDACTED]" in clean


def test_in_memory_log_handler_emit() -> None:
    """Verifica el handler circular en memoria de logs de backend."""
    import logging

    from src.services.diagnostics_and_siem import _BACKEND_LOG_RING_BUFFER

    ensure_diagnostic_log_handler()
    append_diagnostic_log_line("WARNING", "test.diagnostic", "Advertencia de prueba para ring buffer")
    assert any("Advertencia de prueba para ring buffer" in line for line in _BACKEND_LOG_RING_BUFFER)

    handler = _InMemoryDiagnosticLogHandler()
    record = logging.LogRecord("test", logging.INFO, "path", 10, "Mensaje de log record", (), None)
    handler.emit(record)
    assert any("Mensaje de log record" in line for line in _BACKEND_LOG_RING_BUFFER)
    with patch.object(handler, "format", side_effect=Exception("Format error")) as mock_fmt:
        handler.emit(record)
        mock_fmt.assert_called_once()


@pytest.mark.asyncio
async def test_build_support_bundle_empty_logs() -> None:
    """Verifica el comportamiento de fallback cuando el buffer de logs en memoria está vacío."""
    from src.services.diagnostics_and_siem import _BACKEND_LOG_RING_BUFFER

    req = DiagnosticBundleRequest(format="zip", log_lines_limit=50)
    saved_logs = list(_BACKEND_LOG_RING_BUFFER)
    try:
        _BACKEND_LOG_RING_BUFFER.clear()
        resp = await build_support_bundle_archive("tenant-empty", "SUPERADMIN_GLOBAL", req)
        assert resp.filename.endswith(".zip")
    finally:
        _BACKEND_LOG_RING_BUFFER.extend(saved_logs)


@pytest.mark.asyncio
async def test_build_support_bundle_archive_zip() -> None:
    """Verifica la generación del archivo .zip con sanitización y los 4 artefactos."""
    req = DiagnosticBundleRequest(
        format="zip",
        log_lines_limit=100,
        operator_notes="Nota de prueba de incidente NOC password=secreto",
        include_frontend_buffer=[
            UiErrorTelemetryItem(
                timestamp="2026-11-03T22:00:00Z",
                category="HTTP_ERROR",
                message="HTTP 502 Bad Gateway Bearer eyJtoken123",
                route="/inventory/routers",
                status_code=502,
            )
        ],
    )
    resp = await build_support_bundle_archive("tenant-unit-test", "SUPERADMIN_GLOBAL", req)
    assert resp.filename.endswith(".zip")
    assert resp.format == "zip"
    assert resp.content_type == "application/zip"
    assert resp.size_bytes > 0
    assert resp.redacted_secrets_count >= 1

    archive_bytes = base64.b64decode(resp.bundle_base64)
    assert zipfile.is_zipfile(io.BytesIO(archive_bytes))

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        names = zf.namelist()
        assert "metadata.json" in names
        assert "frontend/ui_errors.json" in names
        assert "backend/application_logs.log" in names
        assert "backend/siem_forwarder_status.json" in names

        meta_content = zf.read("metadata.json").decode("utf-8")
        meta = json.loads(meta_content)
        assert meta["tenant_id"] == "tenant-unit-test"
        assert meta["requested_by_role"] == "SUPERADMIN_GLOBAL"
        assert "secreto" not in meta_content

        ui_content = zf.read("frontend/ui_errors.json").decode("utf-8")
        assert "eyJtoken123" not in ui_content
        assert "[REDACTED]" in ui_content


@pytest.mark.asyncio
async def test_build_support_bundle_archive_targz() -> None:
    """Verifica la generación del archivo .tar.gz de diagnóstico."""
    req = DiagnosticBundleRequest(
        format="tar.gz",
        log_lines_limit=50,
        operator_notes="Diagnóstico tarball",
    )
    resp = await build_support_bundle_archive("tenant-tar-test", "TENANT_ADMIN", req)
    assert resp.filename.endswith(".tar.gz")
    assert resp.format == "tar.gz"
    assert resp.content_type == "application/gzip"
    assert resp.size_bytes > 0

    archive_bytes = base64.b64decode(resp.bundle_base64)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        members = tf.getnames()
        assert "metadata.json" in members
        assert "frontend/ui_errors.json" in members
        assert "backend/application_logs.log" in members
        assert "backend/siem_forwarder_status.json" in members


@pytest.mark.asyncio
async def test_record_ui_error_telemetry() -> None:
    """Verifica el registro de telemetría de fallos de interfaz en KeyDB."""
    item = UiErrorTelemetryItem(
        timestamp="2026-11-03T22:10:00Z",
        category="VUE_EXCEPTION",
        message="TypeError: cannot read property 'status' Authorization: Bearer abc123def",
        route="/enterprise/compliance",
    )
    res = await record_ui_error_telemetry(
        tenant_id="tenant-ui-test",
        item=item,
        reported_by_username="tech_l1",
        reported_by_role="SUPPORT_L1",
    )
    assert res.recorded is True
    assert res.buffered_count >= 1


@pytest.mark.asyncio
async def test_siem_config_and_test_event() -> None:
    """Verifica lectura, actualización y prueba de conectividad SIEM del ISP."""
    cfg = await get_siem_forwarder_config("tenant-siem-test")
    assert cfg.enabled is False
    assert cfg.protocol == "GELF_UDP"

    update_req = SiemForwarderConfigUpdateRequest(
        enabled=True,
        protocol="GELF_UDP",
        host="127.0.0.1",
        port=12201,
        min_level="ERROR",
        auth_token="token-secreto-siem",
    )
    updated = await update_siem_forwarder_config("tenant-siem-test", update_req)
    assert updated.enabled is True
    assert updated.has_auth_token is True

    test_res = await send_siem_test_event("tenant-siem-test")
    assert test_res.protocol == "GELF_UDP"
    assert test_res.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_dispatch_siem_protocol_variants() -> None:
    """Verifica el despacho de eventos en los 5 protocolos SIEM soportados con simulación de red."""
    cfg_base = {
        "host": "127.0.0.1",
        "port": 12201,
        "custom_stream_label": "test-label",
        "use_tls": False,
        "endpoint_path": "/gelf",
        "auth_token": "bearer-test",
    }

    with patch("src.services.diagnostics_and_siem._send_udp_datagram") as mock_udp:
        cfg = {**cfg_base, "protocol": "GELF_UDP"}
        target = await _dispatch_siem_protocol(cfg, "t1", "ERROR", "unit_test", "Msg UDP")
        assert "udp://" in target
        mock_udp.assert_called_once()

    with patch("src.services.diagnostics_and_siem._send_http_siem_payload", new_callable=AsyncMock) as mock_http:
        cfg = {**cfg_base, "protocol": "GELF_HTTP"}
        target = await _dispatch_siem_protocol(cfg, "t1", "ERROR", "unit_test", "Msg HTTP")
        assert "http://" in target
        mock_http.assert_awaited_once()

    with patch("src.services.diagnostics_and_siem._send_http_siem_payload", new_callable=AsyncMock) as mock_loki:
        cfg = {**cfg_base, "protocol": "LOKI_HTTP", "endpoint_path": "/loki/api/v1/push"}
        target = await _dispatch_siem_protocol(cfg, "t1", "INFO", "unit_test", "Msg Loki")
        assert "/loki/api/v1/push" in target
        mock_loki.assert_awaited_once()

    with patch("src.services.diagnostics_and_siem._send_tcp_syslog_frame") as mock_tcp:
        cfg = {**cfg_base, "protocol": "SYSLOG_TCP"}
        target = await _dispatch_siem_protocol(cfg, "t1", "WARNING", "unit_test", "Msg TCP Syslog")
        assert "tcp://" in target
        mock_tcp.assert_called_once()

    with patch("src.services.diagnostics_and_siem._send_udp_datagram") as mock_syslog_udp:
        cfg = {**cfg_base, "protocol": "SYSLOG_UDP"}
        target = await _dispatch_siem_protocol(cfg, "t1", "INFO", "unit_test", "Msg UDP Syslog")
        assert "udp://" in target
        mock_syslog_udp.assert_called_once()


@pytest.mark.asyncio
async def test_send_tcp_and_http_siem_helpers() -> None:
    """Verifica directamente los helpers de bajo nivel para envío TCP Syslog y HTTP con autenticación."""
    from src.services.diagnostics_and_siem import (
        _send_http_siem_payload,
        _send_tcp_syslog_frame,
    )

    with patch("socket.create_connection") as mock_conn:
        mock_sock = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_sock
        _send_tcp_syslog_frame("127.0.0.1", 514, b"<134>test")
        mock_sock.sendall.assert_called_once_with(b"<134>test\n")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp
        await _send_http_siem_payload("http://siem.local/gelf", {"short_message": "test"}, "secret-token")
        mock_post.assert_awaited_once()
        assert mock_post.await_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"


@pytest.mark.asyncio
async def test_forward_event_to_isp_siem_if_enabled_filters() -> None:
    """Verifica los filtros de severidad y habilitación en el reenvío SIEM."""
    with patch("src.services.diagnostics_and_siem._load_raw_siem_config") as mock_cfg:
        # 1. SIEM deshabilitado
        mock_cfg.return_value = {"enabled": False}
        assert await forward_event_to_isp_siem_if_enabled("t1", "ERROR", "backend", "test") is False

        # 2. Severidad inferior al umbral
        mock_cfg.return_value = {"enabled": True, "min_level": "ERROR", "include_frontend_errors": True}
        assert await forward_event_to_isp_siem_if_enabled("t1", "INFO", "backend", "test") is False

        # 3. Exclusión de errores de frontend
        mock_cfg.return_value = {"enabled": True, "min_level": "WARNING", "include_frontend_errors": False}
        assert await forward_event_to_isp_siem_if_enabled("t1", "ERROR", "frontend", "test") is False

        # 4. Reenvío exitoso
        mock_cfg.return_value = {
            "enabled": True,
            "min_level": "INFO",
            "include_frontend_errors": True,
            "protocol": "GELF_UDP",
            "host": "127.0.0.1",
            "port": 12201,
        }
        with patch("src.services.diagnostics_and_siem._dispatch_siem_protocol", new_callable=AsyncMock):
            assert await forward_event_to_isp_siem_if_enabled("t1", "INFO", "backend", "test") is True

        # 5. Reenvío con excepción fail-silent
        with patch("src.services.diagnostics_and_siem._dispatch_siem_protocol", side_effect=Exception("Network error")):
            assert await forward_event_to_isp_siem_if_enabled("t1", "INFO", "backend", "test") is False


# =============================================================================
# PRUEBAS DE ENDPOINTS FASTAPI (/api/v1/system/*)
# =============================================================================


@pytest.mark.asyncio
async def test_api_report_ui_error_telemetry_all_authenticated_roles(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que cualquier rol autenticado (SUPPORT_L1 o TENANT_ADMIN) pueda reportar errores de UI."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.services.diagnostics_and_siem.get_redis_client", lambda: fake_redis)

    # Anónimo -> 401
    resp_anon = await async_client.post(
        "/api/v1/system/diagnostics/ui-error",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"timestamp": "2026-11-03T22:30:00Z", "message": "Falla anónima", "route": "/login"},
    )
    assert resp_anon.status_code == 401

    # SUPPORT_L1 -> 200
    _, headers_l1 = await _create_test_session(fake_redis, SystemRoleEnum.SUPPORT_L1)
    headers_l1["Idempotency-Key"] = str(uuid.uuid4())
    resp_l1 = await async_client.post(
        "/api/v1/system/diagnostics/ui-error",
        headers=headers_l1,
        json={
            "timestamp": "2026-11-03T22:31:00Z",
            "category": "HTTP_ERROR",
            "message": "Falla técnica L1 en inventario",
            "route": "/inventory",
            "status_code": 500,
        },
    )
    assert resp_l1.status_code == 200
    assert resp_l1.json()["recorded"] is True

    # TENANT_ADMIN -> 200
    _, headers_admin = await _create_test_session(fake_redis, SystemRoleEnum.TENANT_ADMIN)
    headers_admin["Idempotency-Key"] = str(uuid.uuid4())
    resp_admin = await async_client.post(
        "/api/v1/system/diagnostics/ui-error",
        headers=headers_admin,
        json={
            "timestamp": "2026-11-03T22:32:00Z",
            "category": "VUE_EXCEPTION",
            "message": "Error de render en Wallboard",
            "route": "/wallboard",
        },
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["recorded"] is True


@pytest.mark.asyncio
async def test_api_create_diagnostic_bundle_rbac(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica control RBAC: 403 para SUPPORT_L1 y 200 para TENANT_ADMIN y SUPERADMIN_GLOBAL."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.services.diagnostics_and_siem.get_redis_client", lambda: fake_redis)

    payload = {"format": "zip", "log_lines_limit": 100, "operator_notes": "Auditoría de soporte"}

    # SUPPORT_L1 -> 403
    _, headers_l1 = await _create_test_session(fake_redis, SystemRoleEnum.SUPPORT_L1)
    headers_l1["Idempotency-Key"] = str(uuid.uuid4())
    resp_l1 = await async_client.post("/api/v1/system/diagnostics/bundle", headers=headers_l1, json=payload)
    assert resp_l1.status_code == 403

    # TENANT_ADMIN -> 200
    _, headers_admin = await _create_test_session(fake_redis, SystemRoleEnum.TENANT_ADMIN)
    headers_admin["Idempotency-Key"] = str(uuid.uuid4())
    resp_admin = await async_client.post("/api/v1/system/diagnostics/bundle", headers=headers_admin, json=payload)
    assert resp_admin.status_code == 200
    data_admin = resp_admin.json()
    assert data_admin["format"] == "zip"
    assert data_admin["bundle_base64"] != ""

    # SUPERADMIN_GLOBAL -> 200
    _, headers_super = await _create_test_session(fake_redis, SystemRoleEnum.SUPERADMIN_GLOBAL)
    headers_super["Idempotency-Key"] = str(uuid.uuid4())
    resp_super = await async_client.post(
        "/api/v1/system/diagnostics/bundle",
        headers=headers_super,
        json={"format": "tar.gz", "log_lines_limit": 50},
    )
    assert resp_super.status_code == 200
    assert resp_super.json()["format"] == "tar.gz"


@pytest.mark.asyncio
async def test_api_siem_config_endpoints_rbac(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica los endpoints GET, PUT y POST /siem-config con permisos de administración."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.services.diagnostics_and_siem.get_redis_client", lambda: fake_redis)

    # SUPPORT_L1 -> 403
    _, headers_l1 = await _create_test_session(fake_redis, SystemRoleEnum.SUPPORT_L1)
    assert (await async_client.get("/api/v1/system/siem-config", headers=headers_l1)).status_code == 403

    headers_l1_put = {**headers_l1, "Idempotency-Key": str(uuid.uuid4())}
    assert (
        await async_client.put(
            "/api/v1/system/siem-config",
            headers=headers_l1_put,
            json={"enabled": True, "protocol": "GELF_UDP", "host": "10.0.0.1", "port": 12201},
        )
    ).status_code == 403

    headers_l1_test = {**headers_l1, "Idempotency-Key": str(uuid.uuid4())}
    assert (await async_client.post("/api/v1/system/siem-config/test", headers=headers_l1_test)).status_code == 403

    # TENANT_ADMIN -> 200
    _, headers_admin = await _create_test_session(fake_redis, SystemRoleEnum.TENANT_ADMIN)
    resp_get = await async_client.get("/api/v1/system/siem-config", headers=headers_admin)
    assert resp_get.status_code == 200

    headers_admin_put = {**headers_admin, "Idempotency-Key": str(uuid.uuid4())}
    resp_put = await async_client.put(
        "/api/v1/system/siem-config",
        headers=headers_admin_put,
        json={
            "enabled": True,
            "protocol": "LOKI_HTTP",
            "host": "loki.internal",
            "port": 3100,
            "endpoint_path": "/loki/api/v1/push",
            "use_tls": False,
            "min_level": "WARNING",
            "include_frontend_errors": True,
            "include_audit_events": True,
            "custom_stream_label": "rosgrid-noc",
        },
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["protocol"] == "LOKI_HTTP"

    headers_admin_test = {**headers_admin, "Idempotency-Key": str(uuid.uuid4())}
    resp_test = await async_client.post("/api/v1/system/siem-config/test", headers=headers_admin_test)
    assert resp_test.status_code == 200
    assert resp_test.json()["protocol"] == "LOKI_HTTP"
