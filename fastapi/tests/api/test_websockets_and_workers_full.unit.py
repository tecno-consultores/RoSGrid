# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite de pruebas unitarias exhaustivas para WebSockets, Multiplexor de Telemetría y Loops de Workers."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from src.api.v1.websockets import (
    _extract_ws_claims,
    _verify_ws_origin,
    _verify_ws_router_permission,
    router_live_telemetry_ws,
    tenant_events_ws,
)
from src.core.config import settings
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.models.inventory import Router, RouterAdminStateEnum, RouterCredentialsVault
from src.models.operations import AlertChannelTypeEnum, NotificationChannel, RouterBackup
from src.schemas.telemetry import (
    InterfaceLiveMetrics,
    SystemHealthMetrics,
    TelemetryTickFrame,
    TenantEventFrame,
)
from src.services.telemetry_multiplexer import (
    _build_telemetry_frame,
    _poll_loop,
    _resolve_router_client,
)
from src.workers.alert_dispatcher_worker import (
    _process_alert_payload,
    alert_dispatcher_worker_loop,
)
from src.workers.health_monitor_worker import (
    health_monitor_worker_loop,
    run_health_monitor_cycle,
)
from src.workers.nightly_backup_worker import (
    _purge_expired_backups,
    nightly_backup_worker_loop,
    run_nightly_backup_cycle,
)
from src.workers.runner import (
    main,
    main_workers_runner,
)
from src.workers.vault_rotation_worker import (
    run_vault_rotation_cycle,
    vault_rotation_worker_loop,
)


class MockScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class MockDbResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None):
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)

    def scalars(self) -> MockScalars:
        return MockScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single


# ============================================================================
# 1. SCHEMAS DE TELEMETRÍA (100% Cobertura src/schemas/telemetry.py)
# ============================================================================


def test_telemetry_pydantic_schemas() -> None:
    health = SystemHealthMetrics(
        uptime="10d05:12:00",
        cpu_load_pct=15,
        cpu_count=4,
        cpu_frequency_mhz=1200,
        free_memory_bytes=500000000,
        total_memory_bytes=1000000000,
        memory_used_pct=50.0,
        free_hdd_bytes=200000000,
        total_hdd_bytes=500000000,
        temperature_c=41.5,
        voltage_v=24.1,
    )
    assert health.cpu_load_pct == 15

    iface = InterfaceLiveMetrics(
        name="ether1",
        running=True,
        disabled=False,
        rx_bps=1000000,
        tx_bps=500000,
        rx_pps=1000,
        tx_pps=500,
    )
    assert iface.name == "ether1"

    r_id = uuid.uuid4()
    tick = TelemetryTickFrame(
        router_id=r_id,
        timestamp_iso=datetime.now(UTC).isoformat(),
        system=health,
        interfaces=[iface],
    )
    assert tick.router_id == r_id
    assert len(tick.interfaces) == 1

    t_id = uuid.uuid4()
    event = TenantEventFrame(
        tenant_id=t_id,
        timestamp_iso=datetime.now(UTC).isoformat(),
        event_name="TEST_EVENT",
        payload={"msg": "hello"},
    )
    assert event.tenant_id == t_id
    assert event.event_name == "TEST_EVENT"


# ============================================================================
# 2. WEBSOCKETS EXTRACT CLAIMS Y ROUTER PERMISSIONS
# ============================================================================


@pytest.mark.asyncio
async def test_extract_ws_claims_failures_and_success() -> None:
    # 1. Missing cookie
    ws1 = AsyncMock()
    ws1.cookies = {}
    with pytest.raises(WebSocketDisconnect):
        await _extract_ws_claims(ws1)
    ws1.close.assert_awaited_once_with(code=4401, reason="No autenticado (falta cookie de sesión)")

    # 2. Invalid token string
    ws2 = AsyncMock()
    ws2.cookies = {"rg_at": "invalid.jwt.token"}
    with pytest.raises(WebSocketDisconnect):
        await _extract_ws_claims(ws2)
    assert ws2.close.await_count == 1

    # 3. Missing sid or tid
    token_missing = jwt.encode({"sub": str(uuid.uuid4())}, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")
    ws3 = AsyncMock()
    ws3.cookies = {"__Host-rg_at": token_missing}
    with pytest.raises(WebSocketDisconnect):
        await _extract_ws_claims(ws3)

    # 4. Session dead in Redis
    tid = str(uuid.uuid4())
    sid = "sess-123"
    valid_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "tid": tid, "sid": sid, "rol": SystemRoleEnum.TENANT_ADMIN.value},
        settings.ROSGRID_JWT_SECRET_KEY,
        algorithm="HS256",
    )
    ws4 = AsyncMock()
    ws4.cookies = {"__Host-rg_at": valid_token}
    fake_redis = MagicMock()
    fake_redis.exists = AsyncMock(return_value=False)
    with patch("src.api.v1.websockets.get_redis_client", return_value=fake_redis):
        with pytest.raises(WebSocketDisconnect):
            await _extract_ws_claims(ws4)

        # 5. Success
        fake_redis.exists = AsyncMock(return_value=True)
        claims = await _extract_ws_claims(ws4)
        assert claims["tid"] == tid
        assert claims["sid"] == sid


@pytest.mark.asyncio
async def test_verify_ws_router_permission_l2_with_db() -> None:
    r_id = uuid.uuid4()
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.SUPPORT_L2.value, "all_r": False}

    # Denied when no perm in DB
    mock_session = AsyncMock()
    mock_session.execute.return_value = MockDbResult([])
    with patch("src.api.v1.websockets.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        with pytest.raises(PermissionError):
            await _verify_ws_router_permission(claims, r_id)

    # Allowed when perm exists
    perm = UserRouterPermission(
        tenant_id=t_id,
        user_id=u_id,
        router_id=r_id,
        can_read=True,
    )
    mock_session.execute.return_value = MockDbResult([perm])
    with patch("src.api.v1.websockets.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        await _verify_ws_router_permission(claims, r_id)


# ============================================================================
# 3. WEBSOCKET ENDPOINTS (router_live_telemetry_ws and tenant_events_ws)
# ============================================================================


@pytest.mark.asyncio
async def test_router_live_telemetry_ws_endpoint() -> None:
    ws = AsyncMock()
    r_id = uuid.uuid4()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sid": "sess-abc", "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    fake_redis = MagicMock()
    fake_pubsub = MagicMock()
    fake_pubsub.subscribe = AsyncMock()
    fake_pubsub.unsubscribe = AsyncMock()
    fake_pubsub.close = AsyncMock()
    fake_redis.pubsub.return_value = fake_pubsub
    fake_redis.hset = AsyncMock()
    fake_redis.sadd = AsyncMock()
    fake_redis.srem = AsyncMock()
    fake_redis.hdel = AsyncMock()
    fake_redis.scard = AsyncMock(return_value=0)

    # Iteration: deliver 1 msg then disconnect
    msg1 = {"channel": f"rg:pubsub:telemetry:{t_id}:{r_id}", "data": '{"test": 1}'}
    fake_pubsub.get_message = AsyncMock(side_effect=[msg1, WebSocketDisconnect(code=1000)])

    with (
        patch("src.api.v1.websockets._extract_ws_claims", return_value=claims),
        patch("src.api.v1.websockets._verify_ws_router_permission", return_value=None),
        patch("src.api.v1.websockets.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.websockets.ensure_poller_active") as mock_ensure,
        patch("src.api.v1.websockets.cancel_poller_task") as mock_cancel,
    ):
        await router_live_telemetry_ws(ws, r_id)
        ws.accept.assert_awaited_once()
        mock_ensure.assert_called_once_with(t_id, r_id)
        mock_cancel.assert_called_once_with(t_id, r_id)


@pytest.mark.asyncio
async def test_tenant_events_ws_endpoint() -> None:
    ws = AsyncMock()
    t_id = uuid.uuid4()
    sid = "sess-xyz"
    uid = str(uuid.uuid4())
    claims = {"tid": str(t_id), "sid": sid, "sub": uid, "rol": SystemRoleEnum.TENANT_ADMIN.value}

    fake_redis = MagicMock()
    fake_pubsub = MagicMock()
    fake_pubsub.subscribe = AsyncMock()
    fake_pubsub.unsubscribe = AsyncMock()
    fake_pubsub.close = AsyncMock()
    fake_redis.pubsub.return_value = fake_pubsub

    # Normal event then disconnect
    ev_msg = {"channel": f"rg:pubsub:events:{t_id}", "data": json.dumps({"event_name": "TEST", "payload": {}})}
    fake_pubsub.get_message = AsyncMock(side_effect=[ev_msg, WebSocketDisconnect(code=1000)])

    with (
        patch("src.api.v1.websockets._extract_ws_claims", return_value=claims),
        patch("src.api.v1.websockets.get_redis_client", return_value=fake_redis),
    ):
        await tenant_events_ws(ws)
        ws.accept.assert_awaited_once()
        ws.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_ws_origin_security() -> None:
    ws = AsyncMock()

    # 1. Dev with wildcard -> always allowed
    with (
        patch("src.api.v1.websockets.settings.ROSGRID_ENV", "development"),
        patch("src.api.v1.websockets.settings.ROSGRID_CORS_ORIGINS", "*"),
    ):
        await _verify_ws_origin(ws)

    # 2. Prod with missing origin -> rejected with 4403
    ws.headers = {}
    with (
        patch("src.api.v1.websockets.settings.ROSGRID_ENV", "production"),
        patch("src.api.v1.websockets.settings.ROSGRID_CORS_ORIGINS", "https://app.rosgrid.com"),
    ):
        with pytest.raises(WebSocketDisconnect) as exc_missing:
            await _verify_ws_origin(ws)
        assert exc_missing.value.code == 4403
        ws.close.assert_awaited_with(code=4403, reason="Origen ausente en entorno de producción")

    # 3. Prod with unauthorized origin (CSWSH) -> rejected with 4403
    ws.headers = {"origin": "https://malicious-site.com"}
    with (
        patch("src.api.v1.websockets.settings.ROSGRID_ENV", "production"),
        patch("src.api.v1.websockets.settings.ROSGRID_CORS_ORIGINS", "https://app.rosgrid.com"),
    ):
        with pytest.raises(WebSocketDisconnect) as exc_unauth:
            await _verify_ws_origin(ws)
        assert exc_unauth.value.code == 4403
        ws.close.assert_awaited_with(code=4403, reason="Origen no autorizado (CSWSH)")

    # 4. Prod with authorized origin -> allowed
    ws.headers = {"origin": "https://app.rosgrid.com"}
    with (
        patch("src.api.v1.websockets.settings.ROSGRID_ENV", "production"),
        patch("src.api.v1.websockets.settings.ROSGRID_CORS_ORIGINS", "https://app.rosgrid.com"),
    ):
        await _verify_ws_origin(ws)


# ============================================================================
# 4. TELEMETRY MULTIPLEXER RESOLUTION & POLL LOOP
# ============================================================================


@pytest.mark.asyncio
async def test_resolve_router_client_and_frame() -> None:
    t_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="Core",
        api_base_url="https://192.168.1.1:443",
        api_port=443,
        serial_number="SN1",
    )
    aad = f"{t_id}:{r.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"pass", aad)
    r.vault = RouterCredentialsVault(
        router_id=r.id,
        tenant_id=t_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
    )

    mock_db = AsyncMock()
    mock_db.execute.return_value = MockDbResult([r])

    with patch("src.services.telemetry_multiplexer.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_db
        client = await _resolve_router_client(t_id, r.id)
        assert client is not None
        assert client.username == "admin"

    # Frame builder
    frame = _build_telemetry_frame(
        router_id=r.id,
        res={"uptime": "5m", "cpu-load": "10", "cpu-count": "2", "free-memory": "100", "total-memory": "200"},
        health={"temperature": "45.0"},
        ifaces=[{"name": "ether1"}],
    )
    assert frame["type"] == "TELEMETRY_TICK"
    assert frame["system"]["cpu_load_pct"] == 10
    assert frame["system"]["temperature_c"] == 45.0


@pytest.mark.asyncio
async def test_poll_loop_breaks_when_no_subs() -> None:
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    fake_redis = AsyncMock()
    fake_redis.scard.return_value = 0  # 0 subs -> break immediately

    mock_client = AsyncMock()

    with (
        patch("src.services.telemetry_multiplexer.get_redis_client", return_value=fake_redis),
        patch("src.services.telemetry_multiplexer._resolve_router_client", return_value=mock_client),
    ):
        await _poll_loop(t_id, r_id)
        mock_client.close.assert_awaited_once()


# ============================================================================
# 5. WORKERS CYCLES & LOOPS
# ============================================================================


@pytest.mark.asyncio
async def test_health_monitor_cycle_and_loop() -> None:
    session = AsyncMock()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="R1",
        admin_state=RouterAdminStateEnum.PRODUCTION,
    )
    session.execute.return_value = MockDbResult([r])

    with (
        patch("src.workers.health_monitor_worker.async_session_maker") as mock_maker,
        patch("src.workers.health_monitor_worker._evaluate_single_router") as mock_eval,
        patch("src.workers.health_monitor_worker.get_redis_client"),
    ):
        mock_maker.return_value.__aenter__.return_value = session
        await run_health_monitor_cycle()
        mock_eval.assert_awaited_once()

    # Loop iteration with CancelledError
    with (
        patch("src.workers.health_monitor_worker.run_health_monitor_cycle", side_effect=asyncio.CancelledError),
        patch("src.workers.health_monitor_worker.asyncio.sleep"),
    ):
        await health_monitor_worker_loop()


@pytest.mark.asyncio
async def test_alert_dispatcher_process_payload_and_loop() -> None:
    t_id = uuid.uuid4()
    ch = NotificationChannel(
        id=uuid.uuid4(),
        tenant_id=t_id,
        name="Telegram Channel",
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        is_enabled=True,
        subscribed_events=["ROUTER_OFFLINE"],
    )
    session = AsyncMock()
    session.execute.return_value = MockDbResult([ch])

    alert_raw = json.dumps({"event_name": "ROUTER_OFFLINE", "msg": "Down"})

    with (
        patch("src.workers.alert_dispatcher_worker.async_session_maker") as mock_maker,
        patch("src.workers.alert_dispatcher_worker._dispatch_to_channel") as mock_disp,
    ):
        mock_maker.return_value.__aenter__.return_value = session
        await _process_alert_payload(str(t_id), alert_raw)
        mock_disp.assert_awaited_once()

    # Alert dispatcher loop break
    fake_redis = MagicMock()
    fake_pubsub = MagicMock()
    fake_pubsub.psubscribe = AsyncMock()
    fake_pubsub.punsubscribe = AsyncMock()
    fake_pubsub.close = AsyncMock()
    fake_redis.pubsub.return_value = fake_pubsub
    fake_pubsub.get_message = AsyncMock(side_effect=asyncio.CancelledError)

    with (
        patch("src.workers.alert_dispatcher_worker.get_redis_client", return_value=fake_redis),
        patch("src.workers.alert_dispatcher_worker.asyncio.sleep"),
    ):
        await alert_dispatcher_worker_loop()
        fake_pubsub.punsubscribe.assert_awaited_once()


@pytest.mark.asyncio
async def test_vault_rotation_cycle_and_loop() -> None:
    t_id = uuid.uuid4()
    r = Router(id=uuid.uuid4(), tenant_id=t_id, display_name="R-Vault")
    v = RouterCredentialsVault(
        router_id=r.id,
        tenant_id=t_id,
        api_username="admin",
        current_password_ciphertext=b"1",
        current_password_iv=b"2",
        current_password_tag=b"3",
        auto_rotate_enabled=True,
    )
    v.router = r

    session = AsyncMock()
    session.execute.return_value = MockDbResult([v])

    with (
        patch("src.workers.vault_rotation_worker.async_session_maker") as mock_maker,
        patch("src.workers.vault_rotation_worker._rotate_single_vault") as mock_rot,
    ):
        mock_maker.return_value.__aenter__.return_value = session
        await run_vault_rotation_cycle()
        mock_rot.assert_awaited_once()

    # Loop with CancelledError
    with (
        patch("src.workers.vault_rotation_worker.run_vault_rotation_cycle", side_effect=asyncio.CancelledError),
        patch("src.workers.vault_rotation_worker.asyncio.sleep"),
    ):
        await vault_rotation_worker_loop()


@pytest.mark.asyncio
async def test_nightly_backup_purge_and_loop() -> None:
    session = AsyncMock()
    b = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        backup_type="AUTOMATIC_NIGHTLY",
        expires_at=datetime.now(UTC) - timedelta(days=1),
        created_at=datetime.now(UTC) - timedelta(days=35),
    )
    # 1st call for expired backups, 2nd call for latest_id
    session.execute.side_effect = [MockDbResult([b]), MockDbResult([], single=uuid.uuid4())]

    purged = await _purge_expired_backups(session)
    assert purged == 1
    session.delete.assert_awaited_once_with(b)

    # Nightly backup cycle
    r = Router(id=uuid.uuid4(), tenant_id=uuid.uuid4(), display_name="R-Backup")
    session.execute.side_effect = None
    session.execute.return_value = MockDbResult([r])
    with (
        patch("src.workers.nightly_backup_worker.async_session_maker") as mock_maker,
        patch("src.workers.nightly_backup_worker._backup_single_router") as mock_bk,
        patch("src.workers.nightly_backup_worker._purge_expired_backups", return_value=0),
    ):
        mock_maker.return_value.__aenter__.return_value = session
        await run_nightly_backup_cycle()
        mock_bk.assert_awaited_once()

    # Loop with CancelledError
    with (
        patch("src.workers.nightly_backup_worker.run_nightly_backup_cycle", side_effect=asyncio.CancelledError),
        patch("src.workers.nightly_backup_worker.asyncio.sleep"),
    ):
        await nightly_backup_worker_loop()


# ============================================================================
# 6. RUNNER ORCHESTRATOR
# ============================================================================


@pytest.mark.asyncio
async def test_runner_orchestrator_main() -> None:
    with (
        patch("src.workers.runner.health_monitor_worker_loop", side_effect=asyncio.CancelledError),
        patch("src.workers.runner.alert_dispatcher_worker_loop", side_effect=asyncio.CancelledError),
        patch("src.workers.runner.nightly_backup_worker_loop", side_effect=asyncio.CancelledError),
        patch("src.workers.runner.vault_rotation_worker_loop", side_effect=asyncio.CancelledError),
        patch("src.workers.runner.syslog_collector_worker_loop", side_effect=asyncio.CancelledError),
        patch("src.workers.runner.close_redis_client") as mock_close,
        patch("src.workers.runner._setup_signal_handlers") as mock_setup,
    ):

        async def trigger_stop(stop_event: asyncio.Event) -> None:
            stop_event.set()

        mock_setup.side_effect = lambda ev: asyncio.create_task(trigger_stop(ev))
        await main_workers_runner()
        mock_close.assert_awaited_once()

    # main() entrypoint
    with (
        patch("asyncio.run") as mock_run,
    ):
        main()
        mock_run.assert_called_once()
