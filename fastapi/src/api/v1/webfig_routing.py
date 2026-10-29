# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Enrutamiento Avanzado RouterOS v7 (BGP, OSPF, BFD, Tablas y Filtros)."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
    intercept_maker_checker_if_needed,
)
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.operations import CriticalActionTypeEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_firewall import (
    BgpConnectionCreateRequest,
    BgpConnectionUpdateRequest,
    BgpPeerStatusSummary,
    BgpSessionSummaryItem,
    RoutingFilterRuleCreateRequest,
    RoutingFilterRuleUpdateRequest,
    RoutingRuleCreateRequest,
    RoutingTableCreateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/routing", tags=["WebFig Routing"])

_ROUTING_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
)


def _parse_session_item(item: dict[str, Any]) -> BgpSessionSummaryItem:
    return BgpSessionSummaryItem(
        id=str(item.get(".id", item.get("id", ""))),
        name=str(item.get("name", "unknown")),
        remote_address=str(item.get("remote.address", item.get("remote-address", ""))),
        remote_as=int(item.get("remote.as", item.get("remote-as", 0))),
        local_as=int(item.get("local.as", item.get("local-as", 0))),
        established=item.get("established", False) in (True, "true"),
        uptime=str(item.get("uptime", "0s")),
        prefix_count=int(item.get("prefix-count", 0)),
        hold_time=str(item.get("hold-time", "1m30s")),
        keepalive_time=str(item.get("keepalive-time", "30s")),
    )


def _build_bgp_summary(raw_sessions: Any, raw_connections: Any) -> BgpPeerStatusSummary:
    sessions = []
    if isinstance(raw_sessions, list):
        for s in raw_sessions:
            if isinstance(s, dict):
                sessions.append(_parse_session_item(s))
    total_cfg = len(raw_connections) if isinstance(raw_connections, list) else len(sessions)
    established_cnt = sum(1 for s in sessions if s.established)
    return BgpPeerStatusSummary(
        total_configured_connections=total_cfg,
        established_sessions_count=established_cnt,
        sessions=sessions,
    )


# ============================================================================
# ROUTING TABLES & RULES
# ============================================================================


@router.get("/tables")
async def list_tables(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista tablas de enrutamiento (main, VRFs y tablas FIB para ECMP/PBR)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/table", client, refresh)


@router.post("/tables", status_code=status.HTTP_201_CREATED)
async def create_table(
    router_id: uuid.UUID,
    payload: RoutingTableCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una nueva tabla de enrutamiento FIB bajo Safe Mode o Maker-Checker."""
    body: dict[str, Any] = {"name": payload.name, "fib": payload.fib}
    if payload.comment:
        body["comment"] = payload.comment

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Crear tabla de enrutamiento FIB {payload.name}",
        ros_rest_method="PUT",
        ros_rest_path="/routing/table",
        request_payload=body,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="routing/table",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/routing/table", json_data=body),
        )


@router.get("/rules")
async def list_rules(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista reglas de Policy Routing."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/rule", client, refresh)


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_rule(
    router_id: uuid.UUID,
    payload: RoutingRuleCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una regla de Policy Routing bajo Safe Mode o Maker-Checker."""
    body: dict[str, Any] = {"table": payload.table, "action": payload.action}
    if payload.src_address:
        body["src-address"] = payload.src_address
    if payload.dst_address:
        body["dst-address"] = payload.dst_address
    if payload.routing_mark:
        body["routing-mark"] = payload.routing_mark

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Crear regla Policy Routing (table={payload.table}, action={payload.action})",
        ros_rest_method="PUT",
        ros_rest_path="/routing/rule",
        request_payload=body,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="routing/rule",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/routing/rule", json_data=body),
        )


# ============================================================================
# BGP (TEMPLATES, CONNECTIONS, SESSIONS, ADVERTISEMENTS)
# ============================================================================


@router.get("/bgp/templates")
async def list_bgp_templates(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista plantillas BGP configuradas."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bgp/template", client, refresh)


@router.get("/bgp/connections")
async def list_bgp_connections(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista conexiones de peering BGP configuradas."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bgp/connection", client, refresh)


@router.post("/bgp/connections", status_code=status.HTTP_201_CREATED)
async def create_bgp_connection(
    router_id: uuid.UUID,
    payload: BgpConnectionCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una nueva conexión BGP en RouterOS v7 bajo Safe Mode o Maker-Checker."""
    body: dict[str, Any] = {
        "name": payload.name,
        "remote.address": payload.remote_address,
        "remote.as": payload.remote_as,
        "local.role": payload.local_role,
    }
    if payload.local_as is not None:
        body["local.as"] = payload.local_as
    if payload.templates:
        body["templates"] = payload.templates
    if payload.connect is not None:
        body["connect"] = "yes" if payload.connect else "no"
    if payload.listen is not None:
        body["listen"] = "yes" if payload.listen else "no"
    if payload.disabled is not None:
        body["disabled"] = payload.disabled

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Crear conexión BGP {payload.name} (AS {payload.remote_as})",
        ros_rest_method="PUT",
        ros_rest_path="/routing/bgp/connection",
        request_payload=body,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="routing/bgp/connection",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/routing/bgp/connection", json_data=body),
        )


@router.patch("/bgp/connections/{item_id}")
async def update_bgp_connection(
    router_id: uuid.UUID,
    item_id: str,
    payload: BgpConnectionUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica o habilita/deshabilita un peer BGP bajo Safe Mode o Maker-Checker."""
    patch_data: dict[str, Any] = {}
    if payload.remote_address:
        patch_data["remote.address"] = payload.remote_address
    if payload.remote_as:
        patch_data["remote.as"] = payload.remote_as
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Modificar conexión BGP ({item_id})",
        ros_rest_method="PATCH",
        ros_rest_path=f"/routing/bgp/connection/{item_id}",
        request_payload=patch_data,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/routing/bgp/connection/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="routing/bgp/connection",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/routing/bgp/connection/{item_id}", json_data=patch_data),
        )


@router.delete("/bgp/connections/{item_id}")
async def delete_bgp_connection(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una conexión BGP bajo Safe Mode o Maker-Checker."""
    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Eliminar conexión BGP ({item_id})",
        ros_rest_method="DELETE",
        ros_rest_path=f"/routing/bgp/connection/{item_id}",
        request_payload={".id": item_id},
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/routing/bgp/connection/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="routing/bgp/connection",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/routing/bgp/connection/{item_id}"),
        )


@router.get("/bgp/sessions", response_model=BgpPeerStatusSummary)
async def get_bgp_sessions(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BgpPeerStatusSummary:
    """Consulta estado en vivo de sesiones BGP (establecidas, prefijos recibidos y uptime)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        raw_sessions = await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bgp/session", client, refresh)
        raw_conns = await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bgp/connection", client, refresh)
        return _build_bgp_summary(raw_sessions, raw_conns)


@router.get("/bgp/advertisements")
async def get_bgp_advertisements(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista prefijos anunciados en vivo a los peers BGP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bgp/advertisements", client, refresh)


# ============================================================================
# OSPF & BFD
# ============================================================================


@router.get("/ospf/instances")
async def list_ospf_instances(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista instancias OSPF v2/v3."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/ospf/instance", client, refresh)


@router.get("/ospf/areas")
async def list_ospf_areas(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista áreas OSPF."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/ospf/area", client, refresh)


@router.get("/ospf/interface-templates")
async def list_ospf_interface_templates(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista plantillas de interfaz OSPF."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(
            redis, tenant_id, router_id, "/routing/ospf/interface-template", client, refresh
        )


@router.get("/ospf/neighbors")
async def list_ospf_neighbors(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista adyacencias OSPF en vivo (Full, 2-Way, Init)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/ospf/neighbor", client, refresh)


@router.get("/bfd/sessions")
async def list_bfd_sessions(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista sesiones BFD de detección ultra-rápida de caídas."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/bfd/session", client, refresh)


# ============================================================================
# ROUTING FILTERS
# ============================================================================


@router.get("/filters/rules")
async def list_filter_rules(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista reglas de filtros de enrutamiento de RouterOS v7."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/routing/filter/rule", client, refresh)


@router.post("/filters/rules", status_code=status.HTTP_201_CREATED)
async def create_filter_rule(
    router_id: uuid.UUID,
    payload: RoutingFilterRuleCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una regla de filtro de prefijos bajo Safe Mode o Maker-Checker."""
    body: dict[str, Any] = {"chain": payload.chain, "rule": payload.rule, "disabled": payload.disabled}
    if payload.comment:
        body["comment"] = payload.comment

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Crear filtro de enrutamiento ({payload.chain})",
        ros_rest_method="PUT",
        ros_rest_path="/routing/filter/rule",
        request_payload=body,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="routing/filter/rule",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/routing/filter/rule", json_data=body),
        )


@router.patch("/filters/rules/{item_id}")
async def update_filter_rule(
    router_id: uuid.UUID,
    item_id: str,
    payload: RoutingFilterRuleUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ROUTING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una regla de filtro de prefijos bajo Safe Mode o Maker-Checker."""
    patch_data: dict[str, Any] = {}
    if payload.chain:
        patch_data["chain"] = payload.chain
    if payload.rule:
        patch_data["rule"] = payload.rule
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Modificar filtro de enrutamiento ({item_id})",
        ros_rest_method="PATCH",
        ros_rest_path=f"/routing/filter/rule/{item_id}",
        request_payload=patch_data,
        action_type=CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/routing/filter/rule/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="routing/filter/rule",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/routing/filter/rule/{item_id}", json_data=patch_data),
        )
