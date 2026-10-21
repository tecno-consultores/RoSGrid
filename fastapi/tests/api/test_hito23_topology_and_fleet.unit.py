# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.v1.fleet_metrics import get_prometheus_fleet_metrics
from src.api.v1.topology_l2 import get_layer2_topology
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router
from src.schemas.topology_l2 import TopologyEdge
from src.services.poe_aware_upgrade import (
    evaluate_safety_stop,
    order_routers_by_poe_stages,
)
from src.services.topology_l2 import (
    _build_canonical_edge_id,
    _extract_poe_status,
    process_topology_graph,
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
async def test_prometheus_fleet_metrics_endpoint():
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_res

    resp = await get_prometheus_fleet_metrics(db=db)
    assert resp.status_code == 200
    assert "rosgrid_router_status" in resp.body.decode("utf-8")
