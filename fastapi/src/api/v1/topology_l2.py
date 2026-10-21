# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims
from src.api.v1.webfig_common import _create_client_from_vault
from src.db.session import get_tenant_db_session
from src.models.core import Tenant
from src.models.inventory import Router
from src.schemas.topology_l2 import L2TopologyResponse
from src.services.topology_l2 import (
    get_cached_topology,
    process_topology_graph,
    save_cached_topology,
)

router = APIRouter(prefix="/topology/l2", tags=["Layer 2 Topology"])


def _check_topology_feature(tenant: Tenant) -> None:
    if not getattr(tenant, "l2_topology_enabled", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_MODULE_DISABLED",
                "message": "La visualización de topología L2 no está habilitada para esta organización.",
            },
        )


async def _fetch_router_neighbors(
    tenant_id: uuid.UUID,
    router_obj: Router,
) -> list[dict[str, Any]]:
    """Consulta de forma segura `/rest/ip/neighbor` a través del cliente RouterOS v7."""
    try:
        client = _create_client_from_vault(router_obj, tenant_id)
        async with client:
            res = await client.get("ip/neighbor")
            return res if isinstance(res, list) else []
    except Exception:
        return []


async def _fetch_router_poe(
    tenant_id: uuid.UUID,
    router_obj: Router,
) -> dict[str, Any]:
    """Consulta el estado PoE de interfaces Ethernet si está soportado."""
    try:
        client = _create_client_from_vault(router_obj, tenant_id)
        async with client:
            res = await client.get("interface/ethernet/poe")
            if isinstance(res, list):
                return {str(item.get("name", item.get(".id", ""))): item for item in res if isinstance(item, dict)}
            res_eth = await client.get("interface/ethernet")
            if isinstance(res_eth, list):
                return {
                    str(item.get("name", item.get(".id", ""))): item
                    for item in res_eth
                    if isinstance(item, dict) and "poe-out" in item
                }
    except Exception:
        pass
    return {}


def _filter_topology_by_router(topology: L2TopologyResponse, router_id: uuid.UUID | None) -> L2TopologyResponse:
    """Filtra las aristas conectadas al router indicado si se especifica."""
    if not router_id:
        return topology
    filtered_edges = [e for e in topology.edges if e.source_router_id == router_id or e.target_router_id == router_id]
    return L2TopologyResponse(
        nodes=topology.nodes,
        edges=filtered_edges,
        total_nodes=topology.total_nodes,
        total_edges=len(filtered_edges),
        timestamp=topology.timestamp,
    )


async def _collect_live_topology_data(
    tenant_id: uuid.UUID,
    routers: list[Router],
) -> tuple[dict[uuid.UUID, list[dict[str, Any]]], dict[uuid.UUID, dict[str, Any]]]:
    """Recolecta tablas de vecinos y telemetría PoE de los routers alcanzables."""
    neighbors_map: dict[uuid.UUID, list[dict[str, Any]]] = {}
    poe_map: dict[uuid.UUID, dict[str, Any]] = {}

    for r in routers:
        if not r.is_reachable:
            neighbors_map[r.id] = []
            poe_map[r.id] = {}
            continue
        neighbors_map[r.id] = await _fetch_router_neighbors(tenant_id, r)
        poe_map[r.id] = await _fetch_router_poe(tenant_id, r)

    return neighbors_map, poe_map


@router.get("", response_model=L2TopologyResponse)
async def get_layer2_topology(
    router_id: uuid.UUID | None = Query(None, description="Filtrar adyacencias directas de un router específico"),
    refresh: bool = Query(False, description="Forzar refresco evadiendo la caché efímera de KeyDB"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> L2TopologyResponse:
    """Retorna el grafo de interconexión física L2 entre los routers y switches del tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_topology_feature(tenant)

    if not refresh:
        cached = await get_cached_topology(tenant_id)
        if cached:
            return _filter_topology_by_router(cached, router_id)

    query = select(Router).options(selectinload(Router.vault)).where(Router.tenant_id == tenant_id)
    result = await db.execute(query)
    routers = list(result.scalars().all())

    neighbors_map, poe_map = await _collect_live_topology_data(tenant_id, routers)
    topology = process_topology_graph(routers, neighbors_map, poe_map)
    await save_cached_topology(tenant_id, topology)

    return _filter_topology_by_router(topology, router_id)
