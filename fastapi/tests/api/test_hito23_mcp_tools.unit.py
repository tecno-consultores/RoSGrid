# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para las 4 nuevas herramientas MCP del Hito 23.4."""

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

import src.api.v1.mcp as api_mcp
from src.main import app
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.schemas.topology_l2 import L2TopologyResponse, TopologyNode


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
        display_name="Edge-CCR2004",
        ros_identity="Edge-CCR",
        model_name="CCR2004-16G-2S+",
        ros_version="7.16",
        is_reachable=True,
        api_base_url="https://10.0.0.1:443",
        api_port=443,
    )
    return {
        "tenant_id": t_id,
        "user_id": u_id,
        "router_id": r_id,
        "claims": claims,
        "router_obj": router_obj,
    }


def test_mcp_tools_catalog_count():
    names = [t["name"] for t in api_mcp.MCP_TOOLS_CATALOG]
    assert "rosgrid_get_l2_topology" in names
    assert "rosgrid_check_fleet_cves" in names
    assert "rosgrid_get_recent_syslog" in names
    assert "rosgrid_execute_poe_aware_upgrade" in names
    assert len(names) >= 20


@pytest.mark.asyncio
async def test_handle_get_l2_topology_cached(mcp_context):
    t_id = mcp_context["tenant_id"]
    r_id = mcp_context["router_id"]
    db = AsyncMock()

    cached_topo = L2TopologyResponse(
        nodes=[
            TopologyNode(
                id=r_id,
                display_name="Edge-CCR",
                ros_identity="Edge-CCR",
                model_name="CCR2004",
                board_name="CCR2004",
                ros_version="7.16",
                status="ONLINE",
                ip_address="10.0.0.1",
                is_pse=False,
            )
        ],
        edges=[],
        total_nodes=1,
        total_edges=0,
        timestamp=datetime.now(timezone.utc),
    )

    with patch("src.api.v1.mcp.get_cached_topology", AsyncMock(return_value=cached_topo)):
        res = await api_mcp._handle_get_l2_topology(
            db, t_id, mcp_context["user_id"], mcp_context["claims"], {"refresh": False}
        )
        assert res["total_nodes"] == 1
        assert res["total_edges"] == 0


@pytest.mark.asyncio
async def test_handle_check_fleet_cves_single_router(mcp_context):
    t_id = mcp_context["tenant_id"]
    r_id = mcp_context["router_id"]
    router_obj = mcp_context["router_obj"]

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = router_obj
    db.execute = AsyncMock(return_value=mock_result)

    res = await api_mcp._handle_check_fleet_cves(
        db, t_id, mcp_context["user_id"], mcp_context["claims"], {"router_id": str(r_id)}
    )
    assert res["router_id"] == str(r_id)
    assert "total_vulnerabilities" in res
    assert "vulnerabilities" in res


@pytest.mark.asyncio
async def test_handle_get_recent_syslog(mcp_context):
    t_id = mcp_context["tenant_id"]
    r_id = mcp_context["router_id"]
    db = AsyncMock()

    from datetime import datetime, timezone

    from src.schemas.syslog import SyslogEvent

    fake_events = [
        SyslogEvent(
            timestamp=datetime.now(timezone.utc),
            facility="daemon",
            severity="warning",
            topics="interface,warning",
            message="ether1 link down",
            is_critical=True,
            raw="<12> interface,warning ether1 link down",
        )
    ]

    with patch("src.api.v1.mcp.get_router_syslog_events", AsyncMock(return_value=fake_events)):
        res = await api_mcp._handle_get_recent_syslog(
            db, t_id, mcp_context["user_id"], mcp_context["claims"], {"router_id": str(r_id), "limit": 10}
        )
        assert res["router_id"] == str(r_id)
        assert res["total_events"] == 1
        assert res["events"][0]["is_critical"] is True


@pytest.mark.asyncio
async def test_handle_execute_poe_aware_upgrade(mcp_context):
    t_id = mcp_context["tenant_id"]
    r_id = mcp_context["router_id"]
    db = AsyncMock()

    with (
        patch("src.api.v1.mcp._resolve_upgrade_stages", AsyncMock(return_value=[[r_id]])),
        patch(
            "src.api.v1.mcp._process_upgrade_stages",
            AsyncMock(return_value=([{"router_id": str(r_id), "status": "UPGRADE_TRIGGERED"}], False)),
        ),
    ):
        res = await api_mcp._handle_execute_poe_aware_upgrade(
            db, t_id, mcp_context["user_id"], mcp_context["claims"], {"router_ids": [str(r_id)], "poe_aware": True}
        )
        assert res["status"] == "COMPLETED"
        assert res["safety_stop_triggered"] is False
        assert res["processed_count"] == 1


@pytest.mark.asyncio
async def test_mcp_skill_public_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/mcp/skill")
        assert resp.status_code == 200
        assert "rosgrid-noc-operator" in resp.text
        assert "rosgrid_get_l2_topology" in resp.text

        # Test format=json
        resp_json = await client.get("/api/v1/mcp/skill?format=json")
        assert resp_json.status_code == 200
        data = resp_json.json()
        assert data["name"] == "rosgrid-noc-operator"
        assert "content" in data


@pytest.mark.asyncio
async def test_handle_get_l2_topology_live(mcp_context):
    t_id = mcp_context["tenant_id"]
    db = AsyncMock()

    mock_topo = L2TopologyResponse(
        nodes=[], edges=[], total_nodes=0, total_edges=0, timestamp=datetime.now(timezone.utc)
    )
    with patch("src.api.v1.mcp._fetch_and_cache_live_topology", AsyncMock(return_value=mock_topo)):
        res = await api_mcp._handle_get_l2_topology(
            db, t_id, mcp_context["user_id"], mcp_context["claims"], {"refresh": True}
        )
        assert res["total_nodes"] == 0
        assert res["total_edges"] == 0


@pytest.mark.asyncio
async def test_handle_check_fleet_cves_full_fleet(mcp_context):
    t_id = mcp_context["tenant_id"]
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [mcp_context["router_obj"]]
    db.execute.return_value = mock_res

    res = await api_mcp._handle_check_fleet_cves(db, t_id, mcp_context["user_id"], mcp_context["claims"], {})
    assert res["total_evaluated_routers"] == 1


@pytest.mark.asyncio
async def test_handle_check_fleet_cves_not_found(mcp_context):
    t_id = mcp_context["tenant_id"]
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(HTTPException) as exc:
        await api_mcp._handle_check_fleet_cves(
            db, t_id, mcp_context["user_id"], mcp_context["claims"], {"router_id": str(uuid.uuid4())}
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_handle_get_recent_syslog_missing_router_id(mcp_context):
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await api_mcp._handle_get_recent_syslog(
            db, mcp_context["tenant_id"], mcp_context["user_id"], mcp_context["claims"], {}
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_handle_execute_poe_aware_upgrade_missing_ids(mcp_context):
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await api_mcp._handle_execute_poe_aware_upgrade(
            db, mcp_context["tenant_id"], mcp_context["user_id"], mcp_context["claims"], {"router_ids": []}
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_record_mcp_audit_invalid_uuid(mcp_context):
    db = AsyncMock()
    with patch("src.api.v1.mcp.write_audit_log", AsyncMock()):
        await api_mcp._record_mcp_audit(
            db,
            mcp_context["tenant_id"],
            mcp_context["user_id"],
            mcp_context["claims"],
            "127.0.0.1",
            "test_tool",
            {"router_id": "not-a-valid-uuid"},
        )
        assert db.commit.called


def test_matches_status_filter_none():
    assert api_mcp._matches_status_filter(True, None) is True
    assert api_mcp._matches_status_filter(False, "") is True


def test_load_skill_markdown_fallback():
    with patch("src.api.v1.mcp._SKILL_CANDIDATE_PATHS", ()):
        content = api_mcp._load_skill_markdown()
        assert "rosgrid-noc-operator" in content
