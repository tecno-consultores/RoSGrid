# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Control de Ancho de Banda (Simple Queues, Queue Tree y Queue Types)."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import cached_mikrotik_get, get_router_and_client
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_ops import (
    QueueMoveRequest,
    QueueSimpleCreateRequest,
    QueueSimpleUpdateRequest,
    QueueTreeCreateRequest,
    QueueTreeUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/queues", tags=["WebFig Queues"])

_QUEUE_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
)


# ============================================================================
# SIMPLE QUEUES (CON REORDENAMIENTO MOVE)
# ============================================================================


@router.get("/simple")
async def list_simple_queues(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista Simple Queues con límites de velocidad, contadores de bytes y tasa instantánea."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/queue/simple", client, refresh)


@router.post("/simple", status_code=status.HTTP_201_CREATED)
async def create_simple_queue(
    router_id: uuid.UUID,
    payload: QueueSimpleCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una nueva Simple Queue."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "target": payload.target,
        "max-limit": payload.max_limit,
        "disabled": payload.disabled,
    }
    if payload.limit_at:
        body["limit-at"] = payload.limit_at
    if payload.burst_limit:
        body["burst-limit"] = payload.burst_limit
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await client.put("/queue/simple", json_data=body)


@router.patch("/simple/{item_id}")
async def update_simple_queue(
    router_id: uuid.UUID,
    item_id: str,
    payload: QueueSimpleUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica límites de velocidad o estado de una Simple Queue."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name:
        patch_data["name"] = payload.name
    if payload.target:
        patch_data["target"] = payload.target
    if payload.max_limit:
        patch_data["max-limit"] = payload.max_limit
    if payload.limit_at:
        patch_data["limit-at"] = payload.limit_at
    if payload.burst_limit:
        patch_data["burst-limit"] = payload.burst_limit
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    async with client:
        return await client.patch(f"/queue/simple/{item_id}", json_data=patch_data)


@router.delete("/simple/{item_id}")
async def delete_simple_queue(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una Simple Queue."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/queue/simple/{item_id}")


@router.post("/simple/move")
async def move_simple_queue(
    router_id: uuid.UUID,
    payload: QueueMoveRequest,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Reordena la prioridad de evaluación de Simple Queues (Drag & Drop)."""
    _, client = await get_router_and_client(router_id, claims, db)
    body = {"numbers": payload.numbers, "destination": payload.destination}
    async with client:
        return await client.post("/queue/simple/move", json_data=body)


# ============================================================================
# QUEUE TREE & QUEUE TYPES
# ============================================================================


@router.get("/tree")
async def list_queue_trees(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista árbol jerárquico HTB de Queue Tree."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/queue/tree", client, refresh)


@router.post("/tree", status_code=status.HTTP_201_CREATED)
async def create_queue_tree(
    router_id: uuid.UUID,
    payload: QueueTreeCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un nodo en el árbol Queue Tree."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "parent": payload.parent,
        "queue": payload.queue,
        "priority": payload.priority,
    }
    if payload.packet_mark:
        body["packet-mark"] = payload.packet_mark
    if payload.max_limit:
        body["max-limit"] = payload.max_limit
    async with client:
        return await client.put("/queue/tree", json_data=body)


@router.patch("/tree/{item_id}")
async def update_queue_tree(
    router_id: uuid.UUID,
    item_id: str,
    payload: QueueTreeUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica un nodo en Queue Tree."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.parent:
        patch_data["parent"] = payload.parent
    if payload.packet_mark:
        patch_data["packet-mark"] = payload.packet_mark
    if payload.queue:
        patch_data["queue"] = payload.queue
    if payload.max_limit:
        patch_data["max-limit"] = payload.max_limit
    if payload.priority:
        patch_data["priority"] = payload.priority
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    async with client:
        return await client.patch(f"/queue/tree/{item_id}", json_data=patch_data)


@router.delete("/tree/{item_id}")
async def delete_queue_tree(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_QUEUE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina un nodo de Queue Tree."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/queue/tree/{item_id}")


@router.get("/types")
async def list_queue_types(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista disciplinas de encolamiento (PCQ, CAKE, FQ-CoDel, SFQ, FIFO)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/queue/type", client, refresh)
