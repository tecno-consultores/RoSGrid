# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Multiplexor de Telemetría, WebSockets y Workers en segundo plano."""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.v1.websockets import (
    _handle_telemetry_msg,
    _verify_ws_router_permission,
)
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterCredentialsVault
from src.services.telemetry_multiplexer import (
    _compute_iface_delta,
    _fetch_raw_telemetry,
    _process_interfaces,
    cancel_poller_task,
    ensure_poller_active,
)
from src.workers.alert_dispatcher_worker import (
    _dispatch_smtp_sync,
    _dispatch_telegram,
    _dispatch_webhook,
)
from src.workers.health_monitor_worker import (
    _evaluate_single_router,
    _ping_router_resource,
    _publish_alert_and_event,
)
from src.workers.nightly_backup_worker import (
    _backup_single_router,
)
from src.workers.runner import (
    _setup_signal_handlers,
)
from src.workers.vault_rotation_worker import (
    _rotate_single_vault,
)


@pytest.fixture
def sample_router() -> Router:
    tenant_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        display_name="Edge01",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
        serial_number="SN999",
    )
    aad = f"{tenant_id}:{r.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"admin123", aad)
    r.vault = RouterCredentialsVault(
        id=uuid.uuid4(),
        router_id=r.id,
        tenant_id=tenant_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
    )
    return r


# ============================================================================
# TELEMETRY MULTIPLEXER TESTS
# ============================================================================


def test_compute_iface_delta() -> None:
    cur = {
        "name": "ether1",
        "running": "true",
        "disabled": "false",
        "rx-byte": 10000,
        "tx-byte": 20000,
        "rx-packet": 50,
        "tx-packet": 100,
    }
    prev = {"rx": 5000, "tx": 10000, "rx_p": 25, "tx_p": 50}
    dt = 1.0

    delta = _compute_iface_delta(cur, prev, dt)
    assert delta["name"] == "ether1"
    assert delta["running"] is True
    assert delta["disabled"] is False
    assert delta["rx_bps"] == (5000 * 8)
    assert delta["tx_bps"] == (10000 * 8)
    assert delta["rx_pps"] == 25
    assert delta["tx_pps"] == 50


def test_process_interfaces() -> None:
    raw = [
        {"name": "ether1", "rx-byte": 1000, "tx-byte": 2000},
        {"name": "ether2", "rx-byte": 500, "tx-byte": 800},
    ]
    prev_snap: dict[str, dict[str, int]] = {}
    ifaces, new_snap = _process_interfaces(raw, prev_snap, dt=1.0)
    assert len(ifaces) == 2
    assert "ether1" in new_snap
    assert "ether2" in new_snap


@pytest.mark.asyncio
async def test_fetch_raw_telemetry() -> None:
    client = AsyncMock()
    client.get.side_effect = [
        {"cpu-load": 20, "free-memory": 1000},  # resource
        [{"name": "temp", "value": "40"}],  # health
        [{"name": "ether1", "rx-byte": 100}],  # interface
    ]
    res, health, ifaces = await _fetch_raw_telemetry(client)
    assert res["cpu-load"] == 20
    assert len(health) == 1
    assert len(ifaces) == 1


def test_ensure_and_cancel_poller_task() -> None:
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    with patch("asyncio.create_task") as mock_create:
        mock_task = MagicMock()
        mock_create.return_value = mock_task
        ensure_poller_active(t_id, r_id)
        mock_create.assert_called_once()

        cancel_poller_task(t_id, r_id)
        mock_task.cancel.assert_called_once()


# ============================================================================
# WEBSOCKETS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_handle_telemetry_msg() -> None:
    ws = AsyncMock()

    # Normal telemetry message
    keep = await _handle_telemetry_msg(ws, "rg:pubsub:telemetry:1:2", '{"cpu": 10}', "sid1", "uid1")
    assert keep is True
    ws.send_text.assert_awaited_once_with('{"cpu": 10}')

    # Kill switch event matching current session
    kill_ev = json.dumps(
        {
            "event_name": "SESSION_KILLED",
            "payload": {"target_session_id": "sid1", "target_user_id": "uid1"},
        }
    )
    ws_kill = AsyncMock()
    keep_kill = await _handle_telemetry_msg(ws_kill, "rg:pubsub:events:1", kill_ev, "sid1", "uid1")
    assert keep_kill is False
    ws_kill.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_ws_router_permission() -> None:
    router_id = uuid.uuid4()
    # Admin allowed
    claims_admin = {"rol": SystemRoleEnum.TENANT_ADMIN.value}
    await _verify_ws_router_permission(claims_admin, router_id)

    # Support L3 with all_r allowed
    claims_l3 = {"rol": SystemRoleEnum.SUPPORT_L3.value, "all_r": True}
    await _verify_ws_router_permission(claims_l3, router_id)


# ============================================================================
# WORKERS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_ping_router_resource() -> None:
    client = AsyncMock()
    client.get.return_value = {"cpu-load": 15, "total-memory": 1000, "free-memory": 600}
    ok, cpu, free_pct = await _ping_router_resource(client)
    assert ok is True
    assert cpu == 15
    assert free_pct == 60

    # Failure
    client.get.side_effect = Exception("Connect error")
    ok_f, cpu_f, free_f = await _ping_router_resource(client)
    assert ok_f is False
    assert cpu_f == 0


@pytest.mark.asyncio
async def test_publish_alert_and_event() -> None:
    fake_redis = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    await _publish_alert_and_event(fake_redis, t_id, r_id, "Edge01", "ROUTER_OFFLINE", "OFFLINE")
    assert fake_redis.publish.await_count == 2


@pytest.mark.asyncio
async def test_evaluate_single_router(sample_router: Router) -> None:
    session = AsyncMock()
    session.execute.return_value.scalar_one_or_none.return_value = None  # Not in maintenance

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {"state": "ONLINE", "consecutive_failures": "0"}

    with (
        patch("src.workers.health_monitor_worker._ping_router_resource", return_value=(True, 20, 70)),
        patch(
            "src.workers.health_monitor_worker.evaluate_router_monitoring_cycle",
            return_value=("ONLINE", None, {"state": "ONLINE"}),
        ),
    ):
        await _evaluate_single_router(session, fake_redis, sample_router)
        fake_redis.hset.assert_awaited_once()


@pytest.mark.asyncio
async def test_alert_dispatcher_channels() -> None:
    event_data = {
        "event_name": "ROUTER_OFFLINE",
        "router_display_name": "Core-01",
        "operational_status": "OFFLINE",
        "timestamp_iso": "2026-10-15T12:00:00Z",
    }

    # Dispatch to Telegram
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, is_success=True)
        ok = await _dispatch_telegram({"bot_token": "token", "chat_id": "123"}, event_data)
        assert ok is True

    # Dispatch to SMTP
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        _dispatch_smtp_sync({"smtp_host": "localhost", "to_addresses": ["test@test.com"]}, event_data)
        mock_smtp.assert_called_once()

    # Dispatch to Webhook
    with patch("httpx.AsyncClient.post") as mock_post_wh:
        mock_post_wh.return_value = MagicMock(status_code=200, is_success=True)
        ok_wh = await _dispatch_webhook({"url": "https://webhook.site/test", "hmac_secret": "secret"}, event_data)
        assert ok_wh is True


@pytest.mark.asyncio
async def test_backup_single_router(sample_router: Router) -> None:
    session = AsyncMock()
    fake_redis = AsyncMock()

    client = AsyncMock()
    client.post.return_value = "/interface ethernet set ether1 comment=test"

    with patch("src.workers.nightly_backup_worker._create_client_from_vault", return_value=client):
        await _backup_single_router(session, fake_redis, sample_router)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_vault_rotation_worker_single(sample_router: Router) -> None:
    session = AsyncMock()
    assert sample_router.vault is not None

    client = AsyncMock()
    client.patch.return_value = {}

    with (
        patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=client),
        patch("src.workers.vault_rotation_worker._generate_safe_password", return_value="NewGeneratedPass123!"),
    ):
        await _rotate_single_vault(session, sample_router.vault, sample_router)
        assert sample_router.vault.last_rotation_status == "SUCCESS"


def test_setup_signal_handlers() -> None:
    stop_event = asyncio.Event()
    _setup_signal_handlers(stop_event)
