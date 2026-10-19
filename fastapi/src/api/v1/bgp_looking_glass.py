# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de la Consola BGP Looking Glass Interno (Hito 18.2)."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_feature, require_roles
from src.api.v1.webfig_common import cached_mikrotik_get, get_router_and_client
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.bgp_looking_glass import (
    BgpLookingGlassAdvertisedItem,
    BgpLookingGlassAdvertisedResponse,
    BgpLookingGlassRouteItem,
    BgpLookingGlassRouteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bgp/looking-glass",
    tags=["BGP Looking Glass"],
    dependencies=[Depends(require_feature("bgp_looking_glass_enabled"))],
)

_BGP_LG_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.NOC_MONITOR,
)


def _parse_communities(raw: Any) -> list[str]:
    """Convierte cadenas o listas de comunidades BGP en una lista estándar."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(c).strip() for c in raw if c]
    if isinstance(raw, str):
        return [c.strip() for c in raw.split(",") if c.strip()]
    return [str(raw)]


def _parse_route_item(item: dict[str, Any]) -> BgpLookingGlassRouteItem:
    """Normaliza un registro de /routing/route en RouterOS v7."""
    dst = str(item.get("dst-address", item.get("dst", "")))
    gw = str(item.get("gateway", item.get("gw", "")))
    imm_gw = item.get("immediate-gw")
    as_path = str(item.get("as-path", item.get("bgp.as-path", "")))
    raw_comm = item.get("communities", item.get("bgp.communities", []))
    comm_list = _parse_communities(raw_comm)

    scope_val = item.get("scope")
    scope: int | None = None
    if scope_val is not None:
        try:
            scope = int(scope_val)
        except (ValueError, TypeError):
            scope = None

    active_val = item.get("active", True)
    is_active = active_val in (True, "true", "yes", 1)
    proto = str(item.get("protocol", item.get("routing-table", "bgp")))
    uptime = str(item.get("uptime", "")) or None

    return BgpLookingGlassRouteItem(
        prefix=dst,
        gateway=gw,
        immediate_gw=str(imm_gw) if imm_gw else None,
        as_path=as_path,
        communities=comm_list,
        scope=scope,
        active=is_active,
        protocol=proto,
        uptime=uptime,
        attributes=item,
    )


def _parse_advertised_item(peer_filter: str, item: dict[str, Any]) -> BgpLookingGlassAdvertisedItem:
    """Normaliza un prefijo exportado desde /routing/bgp/advertisements."""
    peer_name = str(item.get("peer", item.get("connection", peer_filter)))
    prefix = str(item.get("dst", item.get("dst-address", item.get("prefix", ""))))
    nexthop = str(item.get("nexthop", item.get("gateway", "")))
    as_path = str(item.get("as-path", "")) or None
    origin = str(item.get("origin", "")) or None
    raw_comm = item.get("communities", [])
    comm_list = _parse_communities(raw_comm)

    return BgpLookingGlassAdvertisedItem(
        peer=peer_name,
        prefix=prefix,
        nexthop=nexthop,
        as_path=as_path,
        origin=origin,
        communities=comm_list,
    )


@router.get("/route", response_model=BgpLookingGlassRouteResponse)
async def get_looking_glass_route(
    router_id: uuid.UUID = Query(..., description="ID del router BGP de consulta"),
    prefix: str = Query(..., min_length=1, max_length=64, description="Prefijo o CIDR a consultar"),
    refresh: bool = Query(default=False, description="Evitar caché de Redis y consultar directo al router"),
    claims: dict[str, Any] = Depends(require_roles(*_BGP_LG_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BgpLookingGlassRouteResponse:
    """Consulta la tabla de enrutamiento BGP en RouterOS v7 para un prefijo específico."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)

    async with client:
        raw_routes = await cached_mikrotik_get(
            redis=redis,
            tenant_id=tenant_id,
            router_id=router_id,
            endpoint="/routing/route",
            client=client,
            refresh=refresh,
            ttl_seconds=10,
        )

    matched: list[BgpLookingGlassRouteItem] = []
    prefix_clean = prefix.strip()
    prefix_base = prefix_clean.split("/")[0]

    if isinstance(raw_routes, list):
        for item in raw_routes:
            if not isinstance(item, dict):
                continue
            dst = str(item.get("dst-address", item.get("dst", ""))).strip()
            if dst == prefix_clean or (prefix_base in dst):
                matched.append(_parse_route_item(item))

    return BgpLookingGlassRouteResponse(
        router_id=router_id,
        prefix=prefix_clean,
        total_routes=len(matched),
        routes=matched,
    )


@router.get("/advertised", response_model=BgpLookingGlassAdvertisedResponse)
async def get_looking_glass_advertised(
    router_id: uuid.UUID = Query(..., description="ID del router BGP de consulta"),
    peer: str = Query(..., min_length=1, max_length=128, description="Nombre o IP del peer BGP"),
    refresh: bool = Query(default=False, description="Evitar caché de Redis y consultar directo al router"),
    claims: dict[str, Any] = Depends(require_roles(*_BGP_LG_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BgpLookingGlassAdvertisedResponse:
    """Lista los prefijos anunciados a un peer BGP específico sin requerir privilegios de shell."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)

    async with client:
        raw_adv = await cached_mikrotik_get(
            redis=redis,
            tenant_id=tenant_id,
            router_id=router_id,
            endpoint="/routing/bgp/advertisements",
            client=client,
            refresh=refresh,
            ttl_seconds=10,
        )

    matched: list[BgpLookingGlassAdvertisedItem] = []
    peer_clean = peer.strip().lower()

    if isinstance(raw_adv, list):
        for item in raw_adv:
            if not isinstance(item, dict):
                continue
            item_peer = str(item.get("peer", item.get("connection", ""))).lower()
            if peer_clean in item_peer or not peer_clean:
                matched.append(_parse_advertised_item(peer, item))

    return BgpLookingGlassAdvertisedResponse(
        router_id=router_id,
        peer=peer,
        total_advertised=len(matched),
        advertisements=matched,
    )
