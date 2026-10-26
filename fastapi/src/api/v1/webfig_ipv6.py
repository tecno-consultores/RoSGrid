# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Pila Dual IPv6, DHCPv6-PD, Pools y Descubrimiento NDP."""

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
)
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_l1_net import (
    Ipv6AddressCreateRequest,
    Ipv6DhcpClientCreateRequest,
    Ipv6DhcpServerCreateRequest,
    Ipv6PoolCreateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/ipv6", tags=["WebFig IPv6"])


# ============================================================================
# IPv6 ADDRESSES
# ============================================================================


@router.get("/addresses")
async def list_ipv6_addresses(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista direcciones IPv6 configuradas o aprendidas por SLAAC."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ipv6/address", client, refresh)


@router.post("/addresses", status_code=status.HTTP_201_CREATED)
async def create_ipv6_address(
    router_id: uuid.UUID,
    payload: Ipv6AddressCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Asigna una dirección IPv6 estática o activa EUI-64 en una interfaz."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "address": payload.address,
        "interface": payload.interface,
        "advertise": "yes" if payload.advertise else "no",
        "eui-64": "yes" if payload.eui_64 else "no",
        "disabled": payload.disabled,
    }
    if payload.comment:
        body["comment"] = payload.comment

    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/address",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ipv6/address", json_data=body),
        )


@router.delete("/addresses/{item_id}")
async def delete_ipv6_address(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una dirección IPv6."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ipv6/address/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/address",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ipv6/address/{item_id}"),
        )


# ============================================================================
# DHCPv6 CLIENT & PREFIX DELEGATION (PD)
# ============================================================================


@router.get("/dhcp-clients")
async def list_ipv6_dhcp_clients(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista clientes DHCPv6 configurados para solicitud de prefijo WAN."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ipv6/dhcp-client", client, refresh)


@router.post("/dhcp-clients", status_code=status.HTTP_201_CREATED)
async def create_ipv6_dhcp_client(
    router_id: uuid.UUID,
    payload: Ipv6DhcpClientCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un cliente DHCPv6 solicitando prefijo (PD) al proveedor."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "interface": payload.interface,
        "request": payload.request,
        "pool-prefix-length": payload.pool_prefix_length,
        "add-default-route": "yes" if payload.add_default_route else "no",
        "disabled": payload.disabled,
    }
    if payload.pool_name:
        body["pool-name"] = payload.pool_name
    if payload.comment:
        body["comment"] = payload.comment

    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/dhcp-client",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ipv6/dhcp-client", json_data=body),
        )


@router.delete("/dhcp-clients/{item_id}")
async def delete_ipv6_dhcp_client(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una instancia de cliente DHCPv6."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ipv6/dhcp-client/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/dhcp-client",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ipv6/dhcp-client/{item_id}"),
        )


# ============================================================================
# DHCPv6 SERVER
# ============================================================================


@router.get("/dhcp-servers")
async def list_ipv6_dhcp_servers(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista servidores DHCPv6 activos."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ipv6/dhcp-server", client, refresh)


@router.post("/dhcp-servers", status_code=status.HTTP_201_CREATED)
async def create_ipv6_dhcp_server(
    router_id: uuid.UUID,
    payload: Ipv6DhcpServerCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un servidor DHCPv6 para delegación de prefijos LAN."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "interface": payload.interface,
        "address-pool": payload.address_pool,
        "lease-time": payload.lease_time,
        "disabled": payload.disabled,
    }
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/dhcp-server",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ipv6/dhcp-server", json_data=body),
        )


@router.delete("/dhcp-servers/{item_id}")
async def delete_ipv6_dhcp_server(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una instancia de servidor DHCPv6."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ipv6/dhcp-server/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/dhcp-server",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ipv6/dhcp-server/{item_id}"),
        )


# ============================================================================
# IPv6 POOLS
# ============================================================================


@router.get("/pools")
async def list_ipv6_pools(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista pools de prefijos IPv6."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ipv6/pool", client, refresh)


@router.post("/pools", status_code=status.HTTP_201_CREATED)
async def create_ipv6_pool(
    router_id: uuid.UUID,
    payload: Ipv6PoolCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un nuevo pool de prefijos IPv6."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "prefix": payload.prefix,
        "prefix-length": payload.prefix_length,
    }
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/pool",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ipv6/pool", json_data=body),
        )


@router.delete("/pools/{item_id}")
async def delete_ipv6_pool(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina un pool IPv6."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ipv6/pool/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ipv6/pool",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ipv6/pool/{item_id}"),
        )


# ============================================================================
# IPv6 NEIGHBORS (NDP) & ROUTER ADVERTISEMENT (ND)
# ============================================================================


@router.get("/neighbors")
async def list_ipv6_neighbors(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Descubre vecinos IPv6 en la red local mediante Neighbor Discovery Protocol."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ipv6/neighbor", client, refresh)


@router.get("/nd")
async def list_ipv6_nd_settings(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Consulta configuración de Neighbor Discovery (RA / SLAAC) en interfaces."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.get("/ipv6/nd")
