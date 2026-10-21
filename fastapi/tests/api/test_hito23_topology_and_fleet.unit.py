# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.fleet_metrics import _validate_scrape_auth, get_prometheus_fleet_metrics
from src.api.v1.topology_l2 import (
    _fetch_router_neighbors,
    _fetch_router_poe,
    get_layer2_topology,
)
from src.core.config import settings
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router
from src.schemas.topology_l2 import L2TopologyResponse, TopologyEdge, TopologyNode
from src.services.poe_aware_upgrade import (
    evaluate_safety_stop,
    order_routers_by_poe_stages,
)
from src.services.topology_l2 import (
    _build_canonical_edge_id,
    _extract_poe_status,
    _match_neighbor_to_router,
    get_cached_topology,
    process_topology_graph,
    save_cached_topology,
)


def test_build_canonical_edge_id_symmetry():
    r1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    r2 = uuid.UUID("00000000-0000-0000-0000-000000000002")

    edge1 = _build_canonical_edge_id(r1, "ether1", r2, "sfp-sfpplus1")
    edge2 = _build_canonical_edge_id(r2, "sfp-sfpplus1", r1, "ether1")
    assert edge1 == edge2


def test_extract_poe_status():
    neighbor = {"interface": "ether5"}
    poe_map = {
        "ether5": {"poe-out-status": "delivering-power", "poe-out-power": "14.2"},
        "ether6": {"poe-out-status": "powered-off"},
    }
    is_poe, watts = _extract_poe_status(neighbor, poe_map)
    assert is_poe is True
    assert watts == 14.2

    is_poe_off, watts_off = _extract_poe_status({"interface": "ether6"}, poe_map)
    assert is_poe_off is False
    assert watts_off is None


def test_process_topology_graph():
    r1 = Router(
        id=uuid.uuid4(),
        display_name="SW-PoE-Core",
        ros_identity="SW-Core",
        model_name="CRS328-24P-4S+RM",
        board_name="CRS328",
        ros_version="7.16",
        is_reachable=True,
        api_base_url="https://192.168.1.1:443",
    )
    r2 = Router(
        id=uuid.uuid4(),
        display_name="CAP-Office-North",
        ros_identity="CAP-North",
        model_name="cAP ax",
        board_name="cAP",
        ros_version="7.16",
        is_reachable=True,
        api_base_url="https://192.168.1.2:443",
    )

    neighbors = {
        r1.id: [
            {
                "interface": "ether1",
                "identity": "CAP-North",
                "interface-name": "ether1",
                "link-speed": "1Gbps",
                "discovery-protocol": "MNDP",
            }
        ],
        r2.id: [
            {
                "interface": "ether1",
                "identity": "SW-Core",
                "interface-name": "ether1",
                "link-speed": "1Gbps",
                "discovery-protocol": "MNDP",
            }
        ],
    }

    poe_map = {r1.id: {"ether1": {"poe-out-status": "delivering-power", "poe-out-power": "7.5"}}}

    topo = process_topology_graph([r1, r2], neighbors, poe_map)
    assert topo.total_nodes == 2
    assert topo.total_edges == 1
    edge = topo.edges[0]
    assert edge.is_poe_delivering is True
    assert edge.poe_power_watts == 7.5

    # Validar que r1 está marcado como PSE
    pse_nodes = [n for n in topo.nodes if n.is_pse]
    assert len(pse_nodes) == 1
    assert pse_nodes[0].id == r1.id


def test_evaluate_safety_stop():
    # 0 fallos
    assert evaluate_safety_stop(0, 10, 1.0) is False
    # 1 fallo de 100 routers = 1.0% >= 1.0% -> Activa
    assert evaluate_safety_stop(1, 100, 1.0) is True
    # 1 fallo de 200 routers = 0.5% < 1.0% -> No activa
    assert evaluate_safety_stop(1, 200, 1.0) is False
    # total <= 0
    assert evaluate_safety_stop(1, 0, 1.0) is False


def test_order_routers_by_poe_stages():
    pse_id = uuid.uuid4()
    pd1_id = uuid.uuid4()
    pd2_id = uuid.uuid4()
    pd_leaf_id = uuid.uuid4()

    edges = [
        TopologyEdge(
            id="e1",
            source_router_id=pse_id,
            source_interface="ether1",
            target_router_id=pd1_id,
            target_interface="ether1",
            is_poe_delivering=True,
            poe_power_watts=12.0,
        ),
        TopologyEdge(
            id="e2",
            source_router_id=pd1_id,
            source_interface="ether2",
            target_router_id=pd_leaf_id,
            target_interface="ether1",
            is_poe_delivering=True,
            poe_power_watts=5.0,
        ),
        TopologyEdge(
            id="e3",
            source_router_id=pse_id,
            source_interface="ether3",
            target_router_id=pd2_id,
            target_interface="ether1",
            is_poe_delivering=True,
            poe_power_watts=8.0,
        ),
    ]

    all_ids = [pse_id, pd1_id, pd2_id, pd_leaf_id]
    stages = order_routers_by_poe_stages(all_ids, edges)

    # El DAG inverso debe tener varias etapas:
    # pd_leaf_id y pd2_id no alimentan a nadie restante -> etapa 0
    # pd1_id ahora no alimenta a nadie restante -> etapa 1
    # pse_id al final -> última etapa
    assert len(stages) >= 2
    assert pd_leaf_id in stages[0]
    assert pse_id in stages[-1]


@pytest.fixture
def sample_tenant() -> Tenant:
    return Tenant(
        id=uuid.uuid4(),
        name="Corp Net",
        slug="corp-net",
        status=TenantStatusEnum.ACTIVE,
        l2_topology_enabled=True,
    )


@pytest.fixture
def sample_claims(sample_tenant: Tenant) -> dict[str, str]:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(sample_tenant.id),
        "rol": "TENANT_ADMIN",
    }


@pytest.mark.asyncio
async def test_get_l2_topology_endpoint(sample_tenant: Tenant, sample_claims: dict[str, str]):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_res

    res = await get_layer2_topology(claims=sample_claims, db=db)
    assert res.total_nodes == 0
    assert res.total_edges == 0


@pytest.mark.asyncio
async def test_get_l2_topology_tenant_not_found(sample_claims: dict[str, str]):
    db = AsyncMock()
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_layer2_topology(claims=sample_claims, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_l2_topology_feature_disabled(sample_tenant: Tenant, sample_claims: dict[str, str]):
    sample_tenant.l2_topology_enabled = False
    db = AsyncMock()
    db.get.return_value = sample_tenant
    with pytest.raises(HTTPException) as exc:
        await get_layer2_topology(claims=sample_claims, db=db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_l2_topology_cached_and_filtered(sample_tenant: Tenant, sample_claims: dict[str, str]):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    r1_id = uuid.uuid4()
    r2_id = uuid.uuid4()
    r3_id = uuid.uuid4()

    cached_topo = L2TopologyResponse(
        nodes=[
            TopologyNode(
                id=r1_id,
                display_name="R1",
                ros_identity="R1",
                model_name="CCR",
                board_name="CCR",
                ros_version="7.16",
                status="ONLINE",
                ip_address="10.0.0.1",
                is_pse=False,
            ),
            TopologyNode(
                id=r2_id,
                display_name="R2",
                ros_identity="R2",
                model_name="CCR",
                board_name="CCR",
                ros_version="7.16",
                status="ONLINE",
                ip_address="10.0.0.2",
                is_pse=False,
            ),
        ],
        edges=[
            TopologyEdge(
                id="e1",
                source_router_id=r1_id,
                source_interface="ether1",
                target_router_id=r2_id,
                target_interface="ether1",
            ),
            TopologyEdge(
                id="e2",
                source_router_id=r2_id,
                source_interface="ether2",
                target_router_id=r3_id,
                target_interface="ether1",
            ),
        ],
        total_nodes=2,
        total_edges=2,
        timestamp=datetime.now(timezone.utc),
    )

    with patch("src.api.v1.topology_l2.get_cached_topology", AsyncMock(return_value=cached_topo)):
        # Sin filtro de router_id
        res_all = await get_layer2_topology(router_id=None, refresh=False, claims=sample_claims, db=db)
        assert res_all.total_edges == 2

        # Con filtro de router_id (solo r1)
        res_r1 = await get_layer2_topology(router_id=r1_id, refresh=False, claims=sample_claims, db=db)
        assert res_r1.total_edges == 1
        assert res_r1.edges[0].id == "e1"


@pytest.mark.asyncio
async def test_get_l2_topology_live_with_unreachable(sample_tenant: Tenant, sample_claims: dict[str, str]):
    db = AsyncMock()
    db.get.return_value = sample_tenant

    r_reachable = Router(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        display_name="R-Online",
        ros_identity="R-Online",
        model_name="CCR2004",
        board_name="CCR",
        ros_version="7.16",
        is_reachable=True,
        api_base_url="https://10.0.0.1:443",
    )
    r_unreachable = Router(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        display_name="R-Offline",
        ros_identity="R-Offline",
        model_name="cAP ax",
        board_name="cAP",
        ros_version="7.16",
        is_reachable=False,
        api_base_url="https://10.0.0.2:443",
    )

    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [r_reachable, r_unreachable]
    db.execute.return_value = mock_res

    with (
        patch("src.api.v1.topology_l2.get_cached_topology", AsyncMock(return_value=None)),
        patch("src.api.v1.topology_l2._fetch_router_neighbors", AsyncMock(return_value=[])),
        patch("src.api.v1.topology_l2._fetch_router_poe", AsyncMock(return_value={})),
        patch("src.api.v1.topology_l2.save_cached_topology", AsyncMock()),
    ):
        res = await get_layer2_topology(refresh=True, claims=sample_claims, db=db)
        assert res.total_nodes == 2


def test_match_neighbor_by_ip_address():
    r1 = Router(id=uuid.uuid4(), ros_identity="Core", api_base_url="https://192.168.1.1:443")
    r2 = Router(id=uuid.uuid4(), ros_identity=None, api_base_url="https://192.168.1.2:443")
    by_ident = {"Core": r1}
    by_ip = {"192.168.1.2": r2}

    # Match por IP
    matched = _match_neighbor_to_router({"address": "192.168.1.2"}, by_ident, by_ip)
    assert matched == r2

    # Sin match
    no_match = _match_neighbor_to_router({"address": "10.0.0.1"}, by_ident, by_ip)
    assert no_match is None


@pytest.mark.asyncio
async def test_fetch_neighbors_and_poe_client_error():
    t_id = uuid.uuid4()
    r = Router(id=uuid.uuid4(), tenant_id=t_id, display_name="R1", api_base_url="https://10.0.0.1:443")

    with patch("src.api.v1.topology_l2._create_client_from_vault", side_effect=Exception("Vault fail")):
        nbrs = await _fetch_router_neighbors(t_id, r)
        assert nbrs == []
        poe = await _fetch_router_poe(t_id, r)
        assert poe == {}


@pytest.mark.asyncio
async def test_fetch_router_poe_fallback_interface_ethernet():
    t_id = uuid.uuid4()
    r = Router(id=uuid.uuid4(), tenant_id=t_id, display_name="R1", api_base_url="https://10.0.0.1:443")

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        {"detail": "poe not supported"},  # interface/ethernet/poe returns non-list
        [{"name": "ether1", "poe-out": "auto-on", "poe-out-status": "delivering-power"}],  # interface/ethernet
    ]
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.api.v1.topology_l2._create_client_from_vault", return_value=mock_client):
        res = await _fetch_router_poe(t_id, r)
        assert "ether1" in res


@pytest.mark.asyncio
async def test_cached_topology_keydb_helpers():
    t_id = uuid.uuid4()
    topo = L2TopologyResponse(nodes=[], edges=[], total_nodes=0, total_edges=0, timestamp=datetime.now(timezone.utc))

    # Error handling when redis fails
    with patch("src.services.topology_l2.get_redis_client", side_effect=Exception("Redis fail")):
        assert await get_cached_topology(t_id) is None
        # save should not raise
        await save_cached_topology(t_id, topo)


@pytest.mark.asyncio
async def test_prometheus_fleet_metrics_endpoint():
    db = AsyncMock()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="Core-R",
        ros_identity="Core",
        model_name="CCR2004",
        ros_version="7.10",
        is_reachable=True,
        admin_state="PRODUCTION",
    )
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [r]
    db.execute.return_value = mock_res

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {"cpu_percent": "15.5", "memory_usage_ratio": "0.42"}

    with patch("src.api.v1.fleet_metrics.get_redis_client", return_value=fake_redis):
        resp = await get_prometheus_fleet_metrics(db=db)
        assert resp.status_code == 200
        body = resp.body.decode("utf-8")
        assert "rosgrid_router_status" in body
        assert "rosgrid_router_cpu_percent" in body
        assert "rosgrid_router_memory_usage_ratio" in body
        assert "rosgrid_router_active_cves_count" in body


def test_validate_scrape_auth():
    # Without expected token configured: always passes
    with patch.object(settings, "ROSGRID_PROMETHEUS_SCRAPE_TOKEN", ""):
        _validate_scrape_auth(None)

    # With expected token configured
    with patch.object(settings, "ROSGRID_PROMETHEUS_SCRAPE_TOKEN", "secret-token"):
        # Valid token
        _validate_scrape_auth("Bearer secret-token")

        # Missing header
        with pytest.raises(HTTPException) as exc:
            _validate_scrape_auth(None)
        assert exc.value.status_code == 401

        # Invalid format
        with pytest.raises(HTTPException) as exc:
            _validate_scrape_auth("Basic 123")
        assert exc.value.status_code == 401

        # Wrong token
        with pytest.raises(HTTPException) as exc:
            _validate_scrape_auth("Bearer wrong")
        assert exc.value.status_code == 401
