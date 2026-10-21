# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import logging
import uuid

from src.schemas.topology_l2 import TopologyEdge

logger = logging.getLogger(__name__)


def evaluate_safety_stop(failed_count: int, total_count: int, threshold_percent: float) -> bool:
    """Evalúa si la cantidad de fallos post-reinicio supera el umbral de parada de emergencia."""
    if total_count <= 0 or failed_count <= 0:
        return False
    failure_ratio = (failed_count / total_count) * 100.0
    return failure_ratio >= threshold_percent


def _filter_batch_poe_edges(
    target_router_ids: set[uuid.UUID],
    edges: list[TopologyEdge],
) -> list[TopologyEdge]:
    """Filtra aristas donde ambos extremos están en el lote y existe entrega activa de PoE."""
    return [
        e
        for e in edges
        if e.is_poe_delivering and e.source_router_id in target_router_ids and e.target_router_id in target_router_ids
    ]


def _extract_next_leaf_stage(
    remaining: set[uuid.UUID],
    powers_whom: dict[uuid.UUID, set[uuid.UUID]],
) -> list[uuid.UUID]:
    """Extrae los equipos que no entregan energía a ningún otro equipo restante en el lote."""
    stage: list[uuid.UUID] = []
    for r_id in list(remaining):
        fed_nodes = powers_whom.get(r_id, set()) & remaining
        if not fed_nodes:
            stage.append(r_id)
    return stage


def order_routers_by_poe_stages(
    target_router_ids: list[uuid.UUID],
    edges: list[TopologyEdge],
) -> list[list[uuid.UUID]]:
    """Ordena los routers en etapas (DAG inverso): Equipos alimentados (PD) primero, alimentadores (PSE) al final."""
    target_set = set(target_router_ids)
    poe_edges = _filter_batch_poe_edges(target_set, edges)

    # powers_whom[PSE] = {PD_1, PD_2, ...}
    powers_whom: dict[uuid.UUID, set[uuid.UUID]] = {}
    for e in poe_edges:
        powers_whom.setdefault(e.source_router_id, set()).add(e.target_router_id)

    stages: list[list[uuid.UUID]] = []
    remaining = set(target_router_ids)

    while remaining:
        current_stage = _extract_next_leaf_stage(remaining, powers_whom)
        if not current_stage:
            # En caso de ciclo o dependencia circular, procesar el remanente en una etapa final
            stages.append(list(remaining))
            break
        stages.append(current_stage)
        for node in current_stage:
            remaining.remove(node)

    return stages
