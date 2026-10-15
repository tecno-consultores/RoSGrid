# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite Completa de Pruebas Unitarias para WebSockets y Multiplexor de Telemetría Efímera."""

import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import WebSocketDisconnect

import src.api.v1.websockets as ws_api
import src.services.telemetry_multiplexer as telem_mux
from src.core.config import settings
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.models.inventory import Router, RouterCredentialsVault


# ============================================================================
# TELEMETRY MULTIPLEXER UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_telemetry_helpers_and_deltas() -> None:
    # _compute_iface_delta
    cur = {
        "name": "ether1",
        "running": "true",
        "disabled": "false",
        "rx-byte": "2000",
        "tx-byte": "1000",
        "rx-packet": "20",
        "tx-packet": "10",
    }
    prev = {"rx": 1000, "tx": 500, "rx_p": 10, "tx_p": 5}
    delta = telem_mux._compute_iface_delta(cur, prev, dt=1.0)
    assert delta["name"] == "ether1"
    assert delta["running"] is True
    assert delta["disabled"] is False
    assert delta["rx_bps"] == (1000 * 8)
    assert delta["tx_bps"] == (500 * 8)
    assert delta["rx_pps"] == 10
    assert delta["tx_pps"] == 5

    # _process_interfaces
    ifaces_raw = [cur, "invalid_entry", {"name": ""}]
    res_list, new_snap = telem_mux._process_interfaces(ifaces_raw, {"ether1": prev}, dt=1.0)
    assert len(res_list) == 1
    assert "ether1" in new_snap
    assert new_snap["ether1"]["rx"] == 2000

    # _build_telemetry_frame
    r_id = uuid.uuid4()
    sys_res = {
        "uptime": "1d02h",
        "cpu-load": "15",
        "cpu-count": "4",
        "cpu-frequency": "1200",
        "total-memory": "1000000",
        "free-memory": "800000",
        "free-hdd-space": "50000",
        "total-hdd-space": "100000",
    }
    health = {"temperature": "42.5", "voltage": "24.1"}
    frame = telem_mux._build_telemetry_frame(r_id, sys_res, health, res_list)
    assert frame["type"] == "TELEMETRY_TICK"
    assert frame["router_id"] == str(r_id)
    assert frame["system"]["cpu_load_pct"] == 15
    assert frame["system"]["temperature_c"] == 42.5
    assert frame["system"]["memory_used_pct"] == 20.0
    assert len(frame["interfaces"]) == 1


@pytest.mark.asyncio
async def test_telemetry_fetch_and_resolve() -> None:
    client = AsyncMock()
    client.get.side_effect = [
        {"cpu-load": 10},
        {"temperature": 40},
        [{"name": "ether1"}],
    ]
    res, health, ifaces = await telem_mux._fetch_raw_telemetry(client)
    assert res == {"cpu-load": 10}
    assert health == {"temperature": 40}
    assert len(ifaces) == 1

    # _resolve_router_client
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_exec

    with patch("src.services.telemetry_multiplexer.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        no_client = await telem_mux._resolve_router_client(t_id, r_id)
        assert no_client is None

        # Router with vault
        r_obj = Router(id=r_id, tenant_id=t_id, display_name="R1", api_base_url="https://1.1.1.1:443")
        r_obj.vault = RouterCredentialsVault(router_id=r_id, tenant_id=t_id)
        mock_exec.scalar_one_or_none.return_value = r_obj

        with patch("src.services.telemetry_multiplexer._create_client_from_vault") as mock_create:
            mock_create.return_value = client
            found_client = await telem_mux._resolve_router_client(t_id, r_id)
            assert found_client is client


@pytest.mark.asyncio
async def test_telemetry_poller_management() -> None:
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    poller_key = f"{t_id}:{r_id}"

    # ensure_poller_active & cancel_poller_task
    with (
        patch("src.services.telemetry_multiplexer._poll_loop", new_callable=AsyncMock) as mock_poll,
        patch("src.services.telemetry_multiplexer.get_redis_client") as mock_redis,
    ):
        mock_poll.return_value = None
        telem_mux.ensure_poller_active(t_id, r_id)
        assert poller_key in telem_mux._ACTIVE_POLLERS
        task = telem_mux._ACTIVE_POLLERS[poller_key]

        telem_mux.cancel_poller_task(t_id, r_id)
        assert poller_key not in telem_mux._ACTIVE_POLLERS
        await asyncio.sleep(0)
        assert task.cancelled() or task.done()

    # 1. _poll_loop when client is None
    fake_redis = AsyncMock()
    fake_redis.scard.return_value = 0
    with (
        patch("src.services.telemetry_multiplexer.get_redis_client", return_value=fake_redis),
        patch("src.services.telemetry_multiplexer._resolve_router_client", return_value=None),
    ):
        await telem_mux._poll_loop(t_id, r_id)

    # 2. _poll_loop running 1 cycle with telemetry tick and then breaking
    fake_redis.scard.side_effect = [1, 0]
    client = AsyncMock()
    client.get.side_effect = [{"cpu-load": 5, "total-memory": 1000}, {}, []]

    with (
        patch("src.services.telemetry_multiplexer.get_redis_client", return_value=fake_redis),
        patch("src.services.telemetry_multiplexer._resolve_router_client", return_value=client),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await telem_mux._poll_loop(t_id, r_id)
        assert fake_redis.publish.called
        client.close.assert_called_once()


# ============================================================================
# WEBSOCKETS ENDPOINTS & AUTH UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_websockets_auth_claims() -> None:
    ws = MagicMock()
    ws.close = AsyncMock()
    ws.cookies = {}

    # 1. Missing cookie
    with pytest.raises(WebSocketDisconnect) as exc1:
        await ws_api._extract_ws_claims(ws)
    assert exc1.value.code == 4401

    # 2. Invalid JWT token
    ws.cookies = {"rg_at": "invalid_jwt"}
    with pytest.raises(WebSocketDisconnect) as exc2:
        await ws_api._extract_ws_claims(ws)
    assert exc2.value.code == 4401

    # 3. Session revoked in Redis
    t_id = uuid.uuid4()
    s_id = uuid.uuid4()
    u_id = uuid.uuid4()
    payload = {
        "tid": str(t_id),
        "sid": str(s_id),
        "sub": str(u_id),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "exp": int(time.time()) + 3600,
    }
    valid_jwt = jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")
    ws.cookies = {"__Host-rg_at": valid_jwt}

    fake_redis = AsyncMock()
    fake_redis.exists.return_value = 0
    with patch("src.api.v1.websockets.get_redis_client", return_value=fake_redis):
        with pytest.raises(WebSocketDisconnect) as exc3:
            await ws_api._extract_ws_claims(ws)
        assert exc3.value.code == 4401

        # 4. Valid active session
        fake_redis.exists.return_value = 1
        claims = await ws_api._extract_ws_claims(ws)
        assert claims["tid"] == str(t_id)


@pytest.mark.asyncio
async def test_websockets_permissions_and_killswitch() -> None:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()

    # Admin role -> no permission query needed
    admin_claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    await ws_api._verify_ws_router_permission(admin_claims, r_id)

    # Operator role with permission
    op_claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.SUPPORT_L1.value}
    mock_session = AsyncMock()
    mock_exec = MagicMock()
    perm_obj = UserRouterPermission(tenant_id=t_id, user_id=u_id, router_id=r_id, can_read=True)
    mock_exec.scalar_one_or_none.return_value = perm_obj
    mock_session.execute.return_value = mock_exec

    with patch("src.api.v1.websockets.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        await ws_api._verify_ws_router_permission(op_claims, r_id)

        # Operator without permission
        mock_exec.scalar_one_or_none.return_value = None
        with pytest.raises(PermissionError):
            await ws_api._verify_ws_router_permission(op_claims, r_id)

    # _handle_telemetry_msg
    ws = MagicMock()
    ws.close = AsyncMock()
    ws.send_text = AsyncMock()

    # Regular telemetry frame
    res_normal = await ws_api._handle_telemetry_msg(ws, "rg:telemetry", '{"type":"TICK"}', "s1", "u1")
    assert res_normal is True
    ws.send_text.assert_called_once_with('{"type":"TICK"}')

    # Unrelated event on events channel
    res_ev = await ws_api._handle_telemetry_msg(
        ws, "rg:events", json.dumps({"event_name": "ROUTER_ADDED"}), "s1", "u1"
    )
    assert res_ev is True

    # Kill-Switch event matching target session
    kill_ev = json.dumps({"event_name": "SESSION_KILLED", "payload": {"target_session_id": "s1"}})
    res_killed = await ws_api._handle_telemetry_msg(ws, "rg:events", kill_ev, "s1", "u1")
    assert res_killed is False
    ws.close.assert_called_once_with(code=4401, reason="Sesión revocada por Kill-Switch")
