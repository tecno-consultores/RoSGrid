# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.models.inventory import Router
from src.redis_layer.client import get_redis_client
from src.schemas.topology_l2 import L2TopologyResponse, TopologyEdge, TopologyNode

logger = logging.getLogger(__name__)

TOPOLOGY_CACHE_TTL_SECONDS = 60


def _build_canonical_edge_id(r1: uuid.UUID, if1: str, r2: uuid.UUID, if2: str) -> str:
    """Genera un identificador canónico determinista para una arista bidireccional."""
    p1 = f"{r1}:{if1}"
    p2 = f"{r2}:{if2}"
    return f"edge_{p1}__{p2}" if p1 < p2 else f"edge_{p2}__{p1}"


def _match_neighbor_to_router(
    neighbor: dict[str, Any],
    routers_by_identity: dict[str, Router],
    routers_by_ip: dict[str, Router],
) -> Router | None:
    """Coteja un registro de vecino contra el mapa de routers adoptados en el tenant."""
    ident = neighbor.get("identity")
    if ident and ident in routers_by_identity:
        return routers_by_identity[ident]

    addr = neighbor.get("address")
    if addr and addr in routers_by_ip:
        return routers_by_ip[addr]

    return None


def _extract_poe_status(neighbor: dict[str, Any], poe_map: dict[str, Any]) -> tuple[bool, float | None]:
    """Determina si el puerto local entrega energía PoE al equipo vecino."""
    local_if = neighbor.get("interface", "")
    poe_info = poe_map.get(local_if, {})
    is_delivering = poe_info.get("poe-out-status") == "delivering-power"
    power = float(poe_info.get("poe-out-power", 0.0)) if is_delivering else None
    return is_delivering, power


def _process_single_neighbor(
    src_id: uuid.UUID,
    n: dict[str, Any],
    router_poe: dict[str, Any],
    routers_by_identity: dict[str, Router],
    routers_by_ip: dict[str, Router],
    pse_nodes: set[uuid.UUID],
) -> tuple[str, TopologyEdge] | None:
    """Procesa un registro de vecino determinando adyacencia y PoE."""
    target_router = _match_neighbor_to_router(n, routers_by_identity, routers_by_ip)
    if not target_router or target_router.id == src_id:
        return None

    src_if = n.get("interface", "unknown")
    tgt_if = n.get("interface-name", "unknown")
    edge_id = _build_canonical_edge_id(src_id, src_if, target_router.id, tgt_if)

    is_poe, watts = _extract_poe_status(n, router_poe)
    if is_poe:
        pse_nodes.add(src_id)

    edge = TopologyEdge(
        id=edge_id,
        source_router_id=src_id,
        source_interface=src_if,
        target_router_id=target_router.id,
        target_interface=tgt_if,
        link_speed=n.get("link-speed"),
        protocol=n.get("discovery-protocol", "MNDP"),
        is_poe_delivering=is_poe,
        poe_power_watts=watts,
    )
    return edge_id, edge


def _build_topology_nodes(routers: list[Router], pse_nodes: set[uuid.UUID]) -> list[TopologyNode]:
    """Genera la lista de nodos del grafo con su rol PoE detectado."""
    return [
        TopologyNode(
            id=r.id,
            display_name=r.display_name,
            ros_identity=r.ros_identity,
            model_name=r.model_name,
            board_name=r.board_name,
            ros_version=r.ros_version,
            status="ONLINE" if r.is_reachable else "OFFLINE",
            ip_address=r.api_base_url.split("://")[-1].split(":")[0],
            is_pse=(r.id in pse_nodes),
        )
        for r in routers
    ]


def process_topology_graph(
    routers: list[Router],
    neighbors_by_router_id: dict[uuid.UUID, list[dict[str, Any]]],
    poe_by_router_id: dict[uuid.UUID, dict[str, Any]] | None = None,
) -> L2TopologyResponse:
    """Construye el grafo topológico L2 a partir del inventario y las tablas de vecinos."""
    poe_data = poe_by_router_id or {}
    routers_by_identity = {r.ros_identity: r for r in routers if r.ros_identity}
    routers_by_ip = {r.api_base_url.split("://")[-1].split(":")[0]: r for r in routers}

    seen_edges: dict[str, TopologyEdge] = {}
    pse_nodes: set[uuid.UUID] = set()

    for src_id, neighbor_list in neighbors_by_router_id.items():
        router_poe = poe_data.get(src_id, {})
        for n in neighbor_list:
            res = _process_single_neighbor(src_id, n, router_poe, routers_by_identity, routers_by_ip, pse_nodes)
            if res and res[0] not in seen_edges:
                seen_edges[res[0]] = res[1]

    nodes = _build_topology_nodes(routers, pse_nodes)

    return L2TopologyResponse(
        nodes=nodes,
        edges=list(seen_edges.values()),
        total_nodes=len(nodes),
        total_edges=len(seen_edges),
        timestamp=datetime.now(timezone.utc),
    )


async def get_cached_topology(tenant_id: uuid.UUID) -> L2TopologyResponse | None:
    """Recupera la topología de la memoria volátil de KeyDB si no ha expirado."""
    try:
        redis = get_redis_client()
        raw = await redis.get(f"rg:{tenant_id}:topology:l2:cache")
        if raw:
            return L2TopologyResponse.model_validate_json(raw)
    except Exception as exc:
        logger.warning("Fallo al leer caché de topología L2: %s", exc)
    return None


async def save_cached_topology(tenant_id: uuid.UUID, topology: L2TopologyResponse) -> None:
    """Guarda el grafo de topología en KeyDB con TTL corto (60s) sin tocar Postgres."""
    try:
        redis = get_redis_client()
        await redis.set(
            f"rg:{tenant_id}:topology:l2:cache",
            topology.model_dump_json(),
            ex=TOPOLOGY_CACHE_TTL_SECONDS,
        )
    except Exception as exc:
        logger.warning("Fallo al almacenar caché de topología L2: %s", exc)
