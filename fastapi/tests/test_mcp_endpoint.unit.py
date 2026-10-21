# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite Completa de Pruebas Unitarias para el Endpoint MCP Protegido (/api/v1/mcp)."""

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import src.api.v1.mcp as api_mcp
from src.core.config import settings
from src.models.core import SystemRoleEnum, User
from src.models.inventory import Router
from src.models.operations import CriticalActionTypeEnum, RouterBackup
from src.schemas.mcp import McpJsonRpcRequest


@pytest.fixture
def mcp_context() -> dict[str, Any]:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {
        "tid": str(t_id),
        "sub": str(u_id),
        "rol": SystemRoleEnum.SERVICE_ACCOUNT.value,
        "preferred_username": "hermes_agent_sa",
        "all_r": True,
    }
    router_obj = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Core-Mikrotik-MCP",
        ros_identity="ROS7-MCP-EDGE",
        model_name="CCR2004-16G-2S+",
        ros_version="7.16",
        is_reachable=True,
        ssl_trust_status=None,
        api_base_url="https://10.0.0.1:443",
        api_port=443,
    )
    user_obj = User(
        id=u_id,
        tenant_id=t_id,
        username="hermes_agent_sa",
        email="hermes@rosgrid.local",
        full_name="Hermes Agent Service Account",
        password_hash="fakehash",
        role=SystemRoleEnum.SERVICE_ACCOUNT,
        allowed_cidr_list=[],
        has_all_routers_access=True,
    )
    client = AsyncMock()
    client.get.return_value = {"ret": "ok"}
    client.post.return_value = [{"ret": "ok"}]

    req = MagicMock()
    req.headers = {}
    req.client = MagicMock()
    req.client.host = "10.0.0.50"

    return {
        "t_id": t_id,
        "u_id": u_id,
        "r_id": r_id,
        "claims": claims,
        "router": router_obj,
        "user": user_obj,
        "client": client,
        "request": req,
    }


# ============================================================================
# 1. PRUEBAS DE ACCESO Y SEGURIDAD (404, 403, 401, CIDR, RATE-LIMIT)
# ============================================================================


@pytest.mark.asyncio
async def test_mcp_disabled_returns_404(mcp_context: dict[str, Any]) -> None:
    body = McpJsonRpcRequest(method="initialize")
    db = AsyncMock()
    with patch.object(settings, "ROSGRID_MCP_ENABLED", False):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert exc_info.value.status_code == 404
        assert "MCP endpoint is disabled" in exc_info.value.detail


@pytest.mark.asyncio
async def test_mcp_unauthorized_role_returns_403(mcp_context: dict[str, Any]) -> None:
    body = McpJsonRpcRequest(method="initialize")
    db = AsyncMock()
    claims = dict(mcp_context["claims"])
    claims["rol"] = SystemRoleEnum.SUPPORT_L1.value
    with patch.object(settings, "ROSGRID_MCP_ENABLED", True):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, claims, db)
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_mcp_user_not_found_returns_401(mcp_context: dict[str, Any]) -> None:
    body = McpJsonRpcRequest(method="initialize")
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = None
    db.execute.return_value = res_mock

    with patch.object(settings, "ROSGRID_MCP_ENABLED", True):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_mcp_cidr_validation_rejects_and_allows(mcp_context: dict[str, Any]) -> None:
    user = mcp_context["user"]
    user.allowed_cidr_list = ["192.168.1.0/24"]

    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = user
    db.execute.return_value = res_mock

    body = McpJsonRpcRequest(method="ping")

    # Caso 1: IP fuera de rango -> 403
    mcp_context["request"].client.host = "10.0.0.50"
    with patch.object(settings, "ROSGRID_MCP_ENABLED", True):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert exc_info.value.status_code == 403
        assert "CIDR" in exc_info.value.detail

    # Caso 2: IP inválida -> 403
    mcp_context["request"].client.host = "not-an-ip"
    with patch.object(settings, "ROSGRID_MCP_ENABLED", True):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert exc_info.value.status_code == 403

    # Caso 3: IP dentro de rango -> pasa
    mcp_context["request"].client.host = "192.168.1.50"
    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.jsonrpc == "2.0"
        assert resp.result == {}


@pytest.mark.asyncio
async def test_mcp_rate_limiting_exceeded_429(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_mock

    body = McpJsonRpcRequest(method="ping")
    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 35  # Supera límite de 30

    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert exc_info.value.status_code == 429


# ============================================================================
# 2. PRUEBAS DE MÉTODOS PROTOCOLO (initialize, ping, tools/list)
# ============================================================================


@pytest.mark.asyncio
async def test_mcp_initialize(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_mock

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(id=1, method="initialize")
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.jsonrpc == "2.0"
        assert resp.id == 1
        assert resp.result is not None
        assert resp.result["protocolVersion"] == "2025-03-26"
        assert resp.result["serverInfo"]["name"] == "rosgrid-mcp-server"


@pytest.mark.asyncio
async def test_mcp_tools_list(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_mock

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(id=2, method="tools/list")
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.jsonrpc == "2.0"
        assert resp.id == 2
        assert resp.result is not None
        tools = resp.result.get("tools", [])
        assert len(tools) == 20
        names = {t["name"] for t in tools}
        assert "rosgrid_list_inventory" in names
        assert "rosgrid_get_router_health" in names
        assert "rosgrid_check_sfp_optical_ddm" in names
        assert "rosgrid_inspect_routing_bgp_ospf" in names
        assert "rosgrid_run_live_diagnostic" in names
        assert "rosgrid_compare_config_diff" in names
        assert "rosgrid_reconnect_pppoe_client" in names
        assert "rosgrid_propose_network_change" in names
        assert "rosgrid_run_360_diagnostics" in names
        assert "rosgrid_isolate_subscriber" in names
        assert "rosgrid_restore_subscriber" in names
        assert "rosgrid_change_rate_limit" in names
        assert "rosgrid_query_bgp_looking_glass" in names
        assert "rosgrid_check_config_drift" in names
        assert "rosgrid_run_cis_audit" in names
        assert "rosgrid_detect_mass_outage" in names
        assert "rosgrid_get_l2_topology" in names
        assert "rosgrid_check_fleet_cves" in names
        assert "rosgrid_get_recent_syslog" in names
        assert "rosgrid_execute_poe_aware_upgrade" in names


# ============================================================================
# 3. PRUEBAS DE INVOCACIÓN DE LAS 8 TOOLS (tools/call)
# ============================================================================


@pytest.mark.asyncio
async def test_mcp_tool_call_unknown_tool(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_mock

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(id=3, method="tools/call", params={"name": "unknown_tool", "arguments": {}})
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.error is not None
        assert resp.error.code == -32601


@pytest.mark.asyncio
async def test_tool_rosgrid_list_inventory(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = mcp_context["user"]
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mcp_context["router"]]
    res_mock.scalars.return_value = scalars_mock
    db.execute.return_value = res_mock

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=10,
        method="tools/call",
        params={"name": "rosgrid_list_inventory", "arguments": {"status_filter": "ONLINE"}},
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["total"] == 1
        assert content["data"]["routers"][0]["system_identity"] == "ROS7-MCP-EDGE"
        mock_audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_rosgrid_get_router_health(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    client = mcp_context["client"]
    client.get.side_effect = [
        {"cpu-load": 12, "free-memory": 104857600, "total-memory": 209715200, "uptime": "15d"},
        [{"name": "temperature", "value": 42.5}, {"name": "voltage", "value": 24.1}],
    ]

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=11,
        method="tools/call",
        params={"name": "rosgrid_get_router_health", "arguments": {"router_id": str(mcp_context["r_id"])}},
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert data["cpu_load"] == 12
        assert data["temperature_c"] == 42.5
        assert data["voltage_v"] == 24.1


@pytest.mark.asyncio
async def test_tool_rosgrid_check_sfp_optical_ddm(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    client = mcp_context["client"]
    client.post.return_value = [{"sfp-rx-power": "-22.5 dBm", "sfp-tx-power": "-3.1 dBm"}]

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=12,
        method="tools/call",
        params={
            "name": "rosgrid_check_sfp_optical_ddm",
            "arguments": {"router_id": str(mcp_context["r_id"]), "interface_name": "sfp-sfpplus1"},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert data["sfp_rx_power_dbm"] == -22.5
        assert data["optical_status"] == "WARNING"


@pytest.mark.asyncio
async def test_tool_rosgrid_inspect_routing_bgp_ospf(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    client = mcp_context["client"]
    client.get.side_effect = [
        [{"name": "bgp-peer-1", "state": "established", "prefix-count": 150}],
        [{"router-id": "10.255.255.1", "state": "Full"}],
    ]

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=13,
        method="tools/call",
        params={
            "name": "rosgrid_inspect_routing_bgp_ospf",
            "arguments": {"router_id": str(mcp_context["r_id"]), "protocol": "all"},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert len(data["bgp_sessions"]) == 1
        assert len(data["ospf_neighbors"]) == 1


@pytest.mark.asyncio
async def test_tool_rosgrid_run_live_diagnostic(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    client = mcp_context["client"]
    client.post.return_value = [{"avg-rtt": "2ms", "packet-loss": 0}]

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=14,
        method="tools/call",
        params={
            "name": "rosgrid_run_live_diagnostic",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "tool": "ping",
                "target": "8.8.8.8",
                "count": 4,
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert data["tool"] == "ping"
        assert data["count"] == 4


@pytest.mark.asyncio
async def test_tool_rosgrid_compare_config_diff(mcp_context: dict[str, Any]) -> None:
    t_id = mcp_context["t_id"]
    r_id = mcp_context["r_id"]
    base_b_id = uuid.uuid4()

    backup_mock = RouterBackup(
        id=base_b_id,
        tenant_id=t_id,
        router_id=r_id,
        ros_version_at_backup="7.16",
        rsc_sha256_hash="0" * 64,
        rsc_size_bytes=100,
        rsc_ciphertext=b"ciphertext",
        rsc_iv=b"iv",
        rsc_tag=b"tag",
    )

    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user
    db.get.return_value = backup_mock

    client = mcp_context["client"]
    client.post.return_value = "/ip firewall filter add chain=input action=accept"

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=15,
        method="tools/call",
        params={
            "name": "rosgrid_compare_config_diff",
            "arguments": {
                "router_id": str(r_id),
                "base_backup_id": str(base_b_id),
                "target_backup_id": "LIVE",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp._decrypt_backup_rsc", return_value="/ip firewall filter add chain=input action=drop"),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert "lines_added" in data
        assert "lines_removed" in data
        assert len(data["unified_diff"]) > 0


@pytest.mark.asyncio
async def test_tool_rosgrid_reconnect_pppoe_client(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    client = mcp_context["client"]
    client.get.return_value = [{"name": "cliente_pppoe_101", ".id": "*1A"}]
    client.post.return_value = {}

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=16,
        method="tools/call",
        params={
            "name": "rosgrid_reconnect_pppoe_client",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "pppoe_username": "cliente_pppoe_101",
                "reason": "Test PPPoE Reset",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["data"]["status"] == "RECONNECTED"
        client.post.assert_awaited_with("ppp/active/remove", {".id": "*1A"})


@pytest.mark.asyncio
async def test_tool_rosgrid_propose_network_change_maker_checker(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    body = McpJsonRpcRequest(
        id=17,
        method="tools/call",
        params={
            "name": "rosgrid_propose_network_change",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "category": "FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE",
                "ros_path": "/ip/firewall/filter",
                "http_method": "POST",
                "payload": {"chain": "input", "action": "drop", "comment": "MCP Emergency Drop"},
                "justification": "Mitigación de ataque detectado por IA",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        data = content["data"]
        assert data["status"] == "AWAITING_APPROVAL"
        assert "approval_request_id" in data
        db.add.assert_called_once()
        db.flush.assert_awaited_once()


# ============================================================================
# 4. PRUEBAS DE CASOS BORDE Y FUNCIONES AUXILIARES
# ============================================================================


def test_helper_edge_cases() -> None:
    assert api_mcp._classify_optical_rx(None) == "OPTIMAL"
    assert api_mcp._classify_optical_rx(-28.0) == "CRITICAL_LOW_LIGHT"
    assert api_mcp._classify_optical_rx(-21.0) == "WARNING"
    assert api_mcp._classify_optical_rx(-15.0) == "OPTIMAL"

    assert api_mcp._parse_rx_power(None) is None
    assert api_mcp._parse_rx_power("bad") is None
    assert api_mcp._parse_rx_power("-18.4 dBm") == -18.4

    assert api_mcp._find_pppoe_item_id("not-a-list", "usr") is None
    assert api_mcp._find_pppoe_item_id([{"name": "other"}], "usr") is None
    assert api_mcp._find_pppoe_item_id([{"name": "usr", ".id": "*2B"}], "usr") == "*2B"

    t, v = api_mcp._extract_health_metrics("not-a-list")
    assert t is None and v is None

    assert (
        api_mcp._resolve_critical_action("UNKNOWN_CAT") == CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE
    )


def test_client_ip_headers() -> None:
    req = MagicMock()
    req.headers = {"X-Real-IP": "203.0.113.195, 10.0.0.1"}
    assert api_mcp._extract_client_ip(req) == "203.0.113.195"

    req.headers = {"X-Forwarded-For": "198.51.100.12, 10.0.0.1"}
    assert api_mcp._extract_client_ip(req) == "198.51.100.12"

    req.headers = {}
    req.client.host = "192.168.1.1"
    assert api_mcp._extract_client_ip(req) == "192.168.1.1"


@pytest.mark.asyncio
async def test_reconnect_pppoe_not_found(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    client = mcp_context["client"]
    client.get.return_value = []

    with patch("src.api.v1.mcp.get_router_and_client", return_value=(mcp_context["router"], client)):
        with pytest.raises(HTTPException) as exc_info:
            await api_mcp._handle_reconnect_pppoe(
                db,
                mcp_context["t_id"],
                mcp_context["u_id"],
                mcp_context["claims"],
                {"router_id": str(mcp_context["r_id"]), "pppoe_username": "inexistente"},
            )
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_inventory_user_permissions_and_offline(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_mock = MagicMock()
    scalars_mock = MagicMock()
    offline_router = Router(
        id=uuid.uuid4(),
        tenant_id=mcp_context["t_id"],
        display_name="Offline-Router",
        ros_identity="ROS7-OFFLINE",
        model_name="RB5009",
        ros_version="7.15",
        is_reachable=False,
        ssl_trust_status="STRING_TRUST",
        api_base_url="https://10.0.0.2:443",
        api_port=443,
    )
    scalars_mock.all.return_value = [mcp_context["router"], offline_router]
    res_mock.scalars.return_value = scalars_mock
    db.execute.return_value = res_mock

    # Non-admin claims with all_r = False
    claims = dict(mcp_context["claims"])
    claims["all_r"] = False
    claims["rol"] = SystemRoleEnum.SERVICE_ACCOUNT.value

    # Test filtering with OFFLINE
    res = await api_mcp._handle_list_inventory(
        db,
        mcp_context["t_id"],
        mcp_context["u_id"],
        claims,
        {"status_filter": "OFFLINE"},
    )
    assert res["total"] == 1
    assert res["routers"][0]["display_name"] == "Offline-Router"
    assert res["routers"][0]["ssl_tofu_status"] == "STRING_TRUST"

    # Test SUPERADMIN_GLOBAL
    admin_claims = dict(claims)
    admin_claims["rol"] = SystemRoleEnum.SUPERADMIN_GLOBAL.value
    assert not api_mcp._should_filter_user_routers(admin_claims)


@pytest.mark.asyncio
async def test_config_diff_branches_and_errors(mcp_context: dict[str, Any]) -> None:
    t_id = mcp_context["t_id"]
    r_id = mcp_context["r_id"]
    base_b_id = uuid.uuid4()
    target_b_id = uuid.uuid4()

    base_backup = RouterBackup(
        id=base_b_id,
        tenant_id=t_id,
        router_id=r_id,
        ros_version_at_backup="7.16",
        rsc_sha256_hash="0" * 64,
        rsc_size_bytes=100,
        rsc_ciphertext=b"ct",
        rsc_iv=b"iv",
        rsc_tag=b"tag",
    )
    target_backup = RouterBackup(
        id=target_b_id,
        tenant_id=t_id,
        router_id=r_id,
        ros_version_at_backup="7.16",
        rsc_sha256_hash="1" * 64,
        rsc_size_bytes=110,
        rsc_ciphertext=b"ct2",
        rsc_iv=b"iv2",
        rsc_tag=b"tag2",
    )

    db = AsyncMock()

    # 1. Base backup not found -> 404
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await api_mcp._handle_config_diff(
            db,
            t_id,
            mcp_context["u_id"],
            mcp_context["claims"],
            {"router_id": str(r_id), "base_backup_id": str(base_b_id)},
        )
    assert exc.value.status_code == 404

    # 2. Target backup from DB success
    db.get.side_effect = [base_backup, target_backup]
    with patch(
        "src.api.v1.mcp._decrypt_backup_rsc",
        side_effect=["/ip route add dst=0.0.0.0/0", "/ip route add dst=10.0.0.0/8"],
    ):
        diff_res = await api_mcp._handle_config_diff(
            db,
            t_id,
            mcp_context["u_id"],
            mcp_context["claims"],
            {"router_id": str(r_id), "base_backup_id": str(base_b_id), "target_backup_id": str(target_b_id)},
        )
        assert diff_res["lines_added"] >= 1
        assert diff_res["lines_removed"] >= 1

    # 3. Target backup not found in DB -> 404
    db.get.side_effect = [None]
    with pytest.raises(HTTPException) as exc:
        await api_mcp._fetch_backup_rsc_from_db(str(target_b_id), r_id, t_id, db)
    assert exc.value.status_code == 404

    # 4. Target backup router mismatch -> 404
    mismatched_backup = RouterBackup(
        id=target_b_id,
        tenant_id=t_id,
        router_id=uuid.uuid4(),  # Different router
        ros_version_at_backup="7.16",
        rsc_sha256_hash="1" * 64,
        rsc_size_bytes=110,
        rsc_ciphertext=b"ct",
        rsc_iv=b"iv",
        rsc_tag=b"tag",
    )
    db.get.side_effect = [mismatched_backup]
    with pytest.raises(HTTPException) as exc:
        await api_mcp._fetch_backup_rsc_from_db(str(target_b_id), r_id, t_id, db)
    assert exc.value.status_code == 404


def test_pppoe_matching_and_metrics_extra() -> None:
    # Match using "id" instead of ".id"
    assert api_mcp._match_pppoe_entry({"name": "user1", "id": "*99"}, "user1") == "*99"
    # Match with no id attribute
    assert api_mcp._match_pppoe_entry({"name": "user1"}, "user1") == ""
    # Mismatch username
    assert api_mcp._match_pppoe_entry({"name": "other", "id": "*99"}, "user1") is None

    # Metric not found
    assert api_mcp._extract_metric_by_name([{"name": "fan-speed", "value": 3000}], "temperature") is None


# ============================================================================
# 4. PRUEBAS DE INVOCACIÓN DE LAS 8 NUEVAS TOOLS (HITO 21)
# ============================================================================


@pytest.mark.asyncio
async def test_tool_rosgrid_run_360_diagnostics(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "router_id": str(mcp_context["r_id"]),
        "target_ip": "192.168.88.50",
        "overall_status": "OPTIMAL",
    }

    body = McpJsonRpcRequest(
        id=20,
        method="tools/call",
        params={
            "name": "rosgrid_run_360_diagnostics",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "target_ip": "192.168.88.50",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.run_endpoint_360_diagnostics", new_callable=AsyncMock, return_value=mock_resp),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["overall_status"] == "OPTIMAL"
        mock_audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_rosgrid_isolate_subscriber(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    sub_id = uuid.uuid4()
    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "status": "ISOLATED",
        "service_id": str(sub_id),
        "endpoint_identifier": "ONU-TEST-001",
    }

    body = McpJsonRpcRequest(
        id=21,
        method="tools/call",
        params={
            "name": "rosgrid_isolate_subscriber",
            "arguments": {
                "subscriber_device_id": str(sub_id),
                "reason": "Suspicious traffic loop detected",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.isolate_network_service", new_callable=AsyncMock, return_value=mock_resp),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["status"] == "ISOLATED"


@pytest.mark.asyncio
async def test_tool_rosgrid_restore_subscriber(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    sub_id = uuid.uuid4()
    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "status": "RESTORED",
        "service_id": str(sub_id),
        "endpoint_identifier": "ONU-TEST-001",
    }

    body = McpJsonRpcRequest(
        id=22,
        method="tools/call",
        params={
            "name": "rosgrid_restore_subscriber",
            "arguments": {"subscriber_device_id": str(sub_id)},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.restore_network_service", new_callable=AsyncMock, return_value=mock_resp),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["status"] == "RESTORED"


@pytest.mark.asyncio
async def test_tool_rosgrid_change_rate_limit(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    sub_id = uuid.uuid4()
    prof_id = uuid.uuid4()
    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "status": "RATE_LIMIT_UPDATED",
        "service_id": str(sub_id),
        "bandwidth_profile_id": str(prof_id),
    }

    # Test standard name
    body = McpJsonRpcRequest(
        id=23,
        method="tools/call",
        params={
            "name": "rosgrid_change_rate_limit",
            "arguments": {
                "subscriber_device_id": str(sub_id),
                "bandwidth_profile_id": str(prof_id),
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.change_network_service_rate_limit", new_callable=AsyncMock, return_value=mock_resp),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["status"] == "RATE_LIMIT_UPDATED"

    # Test alias name
    body_alias = McpJsonRpcRequest(
        id=24,
        method="tools/call",
        params={
            "name": "rosgrid_change_subscriber_rate_limit",
            "arguments": {
                "subscriber_device_id": str(sub_id),
                "bandwidth_profile_id": str(prof_id),
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.change_network_service_rate_limit", new_callable=AsyncMock, return_value=mock_resp),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp_alias = await api_mcp.mcp_endpoint(mcp_context["request"], body_alias, mcp_context["claims"], db)
        assert resp_alias.result is not None
        content_alias = json.loads(resp_alias.result["content"][0]["text"])
        assert content_alias["status"] == "OK"


@pytest.mark.asyncio
async def test_tool_rosgrid_query_bgp_looking_glass(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    mock_route = MagicMock()
    mock_route.model_dump.return_value = {
        "router_id": str(mcp_context["r_id"]),
        "prefix": "1.1.1.0/24",
        "total_routes": 1,
    }
    mock_adv = MagicMock()
    mock_adv.model_dump.return_value = {
        "router_id": str(mcp_context["r_id"]),
        "peer": "ISP-UPLINK-1",
        "total_advertised": 5,
    }

    # 1. query_type = "route"
    body_route = McpJsonRpcRequest(
        id=25,
        method="tools/call",
        params={
            "name": "rosgrid_query_bgp_looking_glass",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "query_type": "route",
                "prefix": "1.1.1.0/24",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_looking_glass_route", new_callable=AsyncMock, return_value=mock_route),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body_route, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["prefix"] == "1.1.1.0/24"

    # 2. query_type = "advertised"
    body_adv = McpJsonRpcRequest(
        id=26,
        method="tools/call",
        params={
            "name": "rosgrid_query_bgp_looking_glass",
            "arguments": {
                "router_id": str(mcp_context["r_id"]),
                "query_type": "advertised",
                "peer_session": "ISP-UPLINK-1",
            },
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.get_looking_glass_advertised", new_callable=AsyncMock, return_value=mock_adv),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp_adv = await api_mcp.mcp_endpoint(mcp_context["request"], body_adv, mcp_context["claims"], db)
        assert resp_adv.result is not None
        content_adv = json.loads(resp_adv.result["content"][0]["text"])
        assert content_adv["status"] == "OK"
        assert content_adv["data"]["peer"] == "ISP-UPLINK-1"


@pytest.mark.asyncio
async def test_tool_rosgrid_check_config_drift(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    mock_drift = MagicMock()
    mock_drift.model_dump.return_value = {
        "router_id": str(mcp_context["r_id"]),
        "drift_detected": False,
        "total_drift_lines": 0,
    }

    body = McpJsonRpcRequest(
        id=27,
        method="tools/call",
        params={
            "name": "rosgrid_check_config_drift",
            "arguments": {"router_id": str(mcp_context["r_id"])},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.check_config_drift", new_callable=AsyncMock, return_value=mock_drift),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["drift_detected"] is False


@pytest.mark.asyncio
async def test_tool_rosgrid_run_cis_audit(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    mock_cis = MagicMock()
    mock_cis.model_dump.return_value = {
        "router_id": str(mcp_context["r_id"]),
        "security_score": 92,
        "passed_directives_count": 9,
    }

    body = McpJsonRpcRequest(
        id=28,
        method="tools/call",
        params={
            "name": "rosgrid_run_cis_audit",
            "arguments": {"router_id": str(mcp_context["r_id"])},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.run_cis_audit", new_callable=AsyncMock, return_value=mock_cis),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["security_score"] == 92


@pytest.mark.asyncio
async def test_tool_rosgrid_detect_mass_outage(mcp_context: dict[str, Any]) -> None:
    db = AsyncMock()
    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = mcp_context["user"]
    db.execute.return_value = res_user

    fake_redis = AsyncMock()
    fake_redis.incr.return_value = 1

    inc_id = uuid.uuid4()
    mock_incident = MagicMock()
    mock_incident.id = inc_id
    mock_incident.router_id = mcp_context["r_id"]
    mock_incident.pon_port = "gpon1"
    mock_incident.optical_box = "BOX-12"
    mock_incident.affected_onus_count = 14
    mock_incident.status = MagicMock()
    mock_incident.status.value = "DETECTED"
    mock_incident.incident_summary = "14 ONUs caídas en gpon1"

    body = McpJsonRpcRequest(
        id=29,
        method="tools/call",
        params={
            "name": "rosgrid_detect_mass_outage",
            "arguments": {"threshold_onus": 5},
        },
    )
    with (
        patch.object(settings, "ROSGRID_MCP_ENABLED", True),
        patch("src.api.v1.mcp.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.mcp.detect_fiber_cuts_engine", new_callable=AsyncMock, return_value=[mock_incident]),
        patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),
    ):
        resp = await api_mcp.mcp_endpoint(mcp_context["request"], body, mcp_context["claims"], db)
        assert resp.result is not None
        content = json.loads(resp.result["content"][0]["text"])
        assert content["status"] == "OK"
        assert content["data"]["total_incidents"] == 1
        assert content["data"]["incidents"][0]["pon_port"] == "gpon1"


@pytest.mark.asyncio
async def test_get_mcp_skill_markdown() -> None:
    resp = await api_mcp.get_mcp_skill()
    assert resp.status_code == 200
    assert "text/markdown" in resp.media_type
    assert resp.headers.get("content-disposition") == "inline; filename=SKILL.md"
    body_text = resp.body.decode("utf-8")
    assert "rosgrid-noc-operator" in body_text
    assert "Playbook" in body_text or "Operador NOC" in body_text


@pytest.mark.asyncio
async def test_get_mcp_skill_json() -> None:
    resp = await api_mcp.get_mcp_skill(format="json")
    assert resp.status_code == 200
    data = json.loads(resp.body.decode("utf-8"))
    assert data["name"] == "rosgrid-noc-operator"
    assert data["version"] == "1.0.0"
    assert "rosgrid-noc-operator" in data["content"]


def test_load_skill_markdown_fallback() -> None:
    from pathlib import Path

    non_existent = (Path("/tmp/non_existent_skill_path_12345/SKILL.md"),)
    with patch.object(api_mcp, "_SKILL_CANDIDATE_PATHS", non_existent):
        text = api_mcp._load_skill_markdown()
        assert "rosgrid-noc-operator" in text
        assert "Consulta https://github.com/tecno-consultores/RoSGrid" in text
