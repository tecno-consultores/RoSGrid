# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Direccionamiento IPv4/IPv6, Rutas ECMP, ARP, Pools, DHCP, DNS y Servicios."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
    invalidate_webfig_cache,
)
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikApiError, MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_l1_net import (
    DhcpClientCreateRequest,
    DhcpClientUpdateRequest,
    DhcpLeaseUpdateRequest,
    DhcpNetworkCreateRequest,
    DhcpNetworkUpdateRequest,
    DhcpServerCreateRequest,
    DhcpServerUpdateRequest,
    IpAddressCreateRequest,
    IpAddressUpdateRequest,
    IpArpCreateRequest,
    IpPoolCreateRequest,
    IpRouteCreateRequest,
    IpRouteUpdateRequest,
    IpServiceUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/ip", tags=["WebFig IP"])


async def _verify_anti_suicide_rule(
    client: MikrotikRestClient,
    item_id: str,
    payload: IpServiceUpdateRequest,
) -> None:
    svc_data = await client.get(f"/ip/service/{item_id}")
    if not isinstance(svc_data, dict):
        return
    name = str(svc_data.get("name", "")).strip().lower()
    if name == "www-ssl":
        if payload.disabled is True or (payload.port is not None and payload.port != svc_data.get("port")):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Operación bloqueada: No puedes deshabilitar el servicio www-ssl a través del cual RoSGrid administra este MikroTik.",
            )


# ============================================================================
# IP ADDRESSES
# ============================================================================


@router.get("/addresses")
async def list_ip_addresses(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista direcciones IP configuradas en el router."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/address", client, refresh)


@router.post("/addresses", status_code=status.HTTP_201_CREATED)
async def create_ip_address(
    router_id: uuid.UUID,
    payload: IpAddressCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Asigna una nueva dirección IP a una interfaz bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "address": payload.address,
        "interface": payload.interface,
        "disabled": payload.disabled,
    }
    if payload.network:
        body["network"] = payload.network
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ip/address",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ip/address", json_data=body),
        )


@router.patch("/addresses/{item_id}")
async def update_ip_address(
    router_id: uuid.UUID,
    item_id: str,
    payload: IpAddressUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una dirección IP existente bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.address:
        patch_data["address"] = payload.address
    if payload.network:
        patch_data["network"] = payload.network
    if payload.interface:
        patch_data["interface"] = payload.interface
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/ip/address/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/address",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/address/{item_id}", json_data=patch_data),
        )


@router.delete("/addresses/{item_id}")
async def delete_ip_address(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una dirección IP existente bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ip/address/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/address",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ip/address/{item_id}"),
        )


# ============================================================================
# IP ROUTES (ECMP SUPPORT)
# ============================================================================


@router.get("/routes")
async def list_routes(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista la tabla de enrutamiento IPv4 del router."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/route", client, refresh)


@router.post("/routes", status_code=status.HTTP_201_CREATED)
async def create_route(
    router_id: uuid.UUID,
    payload: IpRouteCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una ruta estática o balanceada ECMP bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "dst-address": payload.dst_address,
        "gateway": payload.gateway,
        "distance": payload.distance,
        "routing-table": payload.routing_table,
        "disabled": payload.disabled,
    }
    if payload.check_gateway:
        body["check-gateway"] = payload.check_gateway
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ip/route",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ip/route", json_data=body),
        )


@router.patch("/routes/{item_id}")
async def update_route(
    router_id: uuid.UUID,
    item_id: str,
    payload: IpRouteUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una ruta existente bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.dst_address:
        patch_data["dst-address"] = payload.dst_address
    if payload.gateway:
        patch_data["gateway"] = payload.gateway
    if payload.distance is not None:
        patch_data["distance"] = payload.distance
    if payload.routing_table:
        patch_data["routing-table"] = payload.routing_table
    if payload.check_gateway is not None:
        patch_data["check-gateway"] = payload.check_gateway
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/ip/route/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/route",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/route/{item_id}", json_data=patch_data),
        )


@router.delete("/routes/{item_id}")
async def delete_route(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una ruta bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ip/route/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/route",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ip/route/{item_id}"),
        )


# ============================================================================
# ARP TABLE
# ============================================================================


@router.get("/arp")
async def list_arp(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista la tabla ARP del router."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/arp", client, refresh)


@router.post("/arp", status_code=status.HTTP_201_CREATED)
async def create_arp(
    router_id: uuid.UUID,
    payload: IpArpCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un amarre ARP estático."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "address": payload.address,
        "mac-address": payload.mac_address,
        "interface": payload.interface,
    }
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await client.put("/ip/arp", json_data=body)


@router.delete("/arp/{item_id}")
async def delete_arp(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Limpia o elimina una entrada ARP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ip/arp/{item_id}")


# ============================================================================
# IP POOLS
# ============================================================================


@router.get("/pools")
async def list_pools(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista pools de direcciones IP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/pool", client, refresh)


@router.post("/pools", status_code=status.HTTP_201_CREATED)
async def create_pool(
    router_id: uuid.UUID,
    payload: IpPoolCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea o actualiza de forma idempotente un pool de direcciones IP."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"name": payload.name, "ranges": payload.ranges}
    if payload.next_pool:
        body["next-pool"] = payload.next_pool
    async with client:
        try:
            res = await client.put("/ip/pool", json_data=body)
        except MikrotikApiError:
            existing_pools = await client.get("/ip/pool")
            existing = (
                next(
                    (
                        p
                        for p in existing_pools
                        if isinstance(p, dict) and p.get("name") == payload.name and p.get(".id")
                    ),
                    None,
                )
                if isinstance(existing_pools, list)
                else None
            )
            if existing is None:
                raise
            res = await client.patch(f"/ip/pool/{existing['.id']}", json_data=body)
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/pool")
    return res


# ============================================================================
# DHCP SERVER LEASES
# ============================================================================


@router.get("/dhcp-server/leases")
async def list_dhcp_leases(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista concesiones de clientes DHCP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/dhcp-server/lease", client, refresh)


@router.post("/dhcp-server/leases/{item_id}/make-static")
async def make_dhcp_lease_static(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Convierte un lease DHCP dinámico en reservación estática."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.post("/ip/dhcp-server/lease/make-static", json_data={"numbers": item_id})


@router.patch("/dhcp-server/leases/{item_id}")
async def update_dhcp_lease(
    router_id: uuid.UUID,
    item_id: str,
    payload: DhcpLeaseUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una reservación estática DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.address:
        patch_data["address"] = payload.address
    if payload.rate_limit:
        patch_data["rate-limit"] = payload.rate_limit
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    async with client:
        return await client.patch(f"/ip/dhcp-server/lease/{item_id}", json_data=patch_data)


@router.delete("/dhcp-server/leases/{item_id}")
async def delete_dhcp_lease(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Libera o elimina una concesión DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ip/dhcp-server/lease/{item_id}")


# ============================================================================
# DHCP SERVERS & NETWORKS
# ============================================================================


@router.get("/dhcp-servers")
async def list_dhcp_servers(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista servidores DHCP configurados en el router."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/dhcp-server", client, refresh)


@router.post("/dhcp-servers", status_code=status.HTTP_201_CREATED)
async def create_dhcp_server(
    router_id: uuid.UUID,
    payload: DhcpServerCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea o actualiza de forma idempotente una instancia de servidor DHCP en una interfaz."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "interface": payload.interface,
        "address-pool": payload.address_pool,
        "lease-time": payload.lease_time,
        "disabled": payload.disabled,
    }

    async def _upsert_server() -> Any:
        try:
            return await client.put("/ip/dhcp-server", json_data=body)
        except MikrotikApiError:
            existing_srvs = await client.get("/ip/dhcp-server")
            existing = (
                next(
                    (
                        s
                        for s in existing_srvs
                        if isinstance(s, dict)
                        and s.get(".id")
                        and (s.get("name") == payload.name or s.get("interface") == payload.interface)
                    ),
                    None,
                )
                if isinstance(existing_srvs, list)
                else None
            )
            if existing is None:
                raise
            return await client.patch(f"/ip/dhcp-server/{existing['.id']}", json_data=body)

    async with client:
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server",
            action="create",
            before_state=body,
            coro_fn=_upsert_server,
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server")
    return res


@router.patch("/dhcp-servers/{item_id}")
async def update_dhcp_server(
    router_id: uuid.UUID,
    item_id: str,
    payload: DhcpServerUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Actualiza configuración de un servidor DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name is not None:
        patch_data["name"] = payload.name
    if payload.interface is not None:
        patch_data["interface"] = payload.interface
    if payload.address_pool is not None:
        patch_data["address-pool"] = payload.address_pool
    if payload.lease_time is not None:
        patch_data["lease-time"] = payload.lease_time
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled

    async with client:
        before = await client.get(f"/ip/dhcp-server/{item_id}")
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server",
            action="update",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/dhcp-server/{item_id}", json_data=patch_data),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server")
    return res


@router.delete("/dhcp-servers/{item_id}")
async def delete_dhcp_server(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una instancia de servidor DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ip/dhcp-server/{item_id}")
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ip/dhcp-server/{item_id}"),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server")
    return res


@router.get("/dhcp-server/networks")
async def list_dhcp_networks(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista las redes DHCP configuradas."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/dhcp-server/network", client, refresh)


@router.post("/dhcp-server/networks", status_code=status.HTTP_201_CREATED)
async def create_dhcp_network(
    router_id: uuid.UUID,
    payload: DhcpNetworkCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea o actualiza de forma idempotente una red para el servidor DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"address": payload.address}
    if payload.gateway:
        body["gateway"] = payload.gateway
    if payload.dns_server:
        body["dns-server"] = payload.dns_server
    if payload.domain:
        body["domain"] = payload.domain
    if payload.comment:
        body["comment"] = payload.comment

    async def _upsert_network() -> Any:
        try:
            return await client.put("/ip/dhcp-server/network", json_data=body)
        except MikrotikApiError:
            existing_nets = await client.get("/ip/dhcp-server/network")
            existing = (
                next(
                    (
                        n
                        for n in existing_nets
                        if isinstance(n, dict) and n.get("address") == payload.address and n.get(".id")
                    ),
                    None,
                )
                if isinstance(existing_nets, list)
                else None
            )
            if existing is None:
                raise
            patch_body = {k: v for k, v in body.items() if k != "address"}
            return await client.patch(f"/ip/dhcp-server/network/{existing['.id']}", json_data=patch_body)

    async with client:
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server/network",
            action="create",
            before_state=body,
            coro_fn=_upsert_network,
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/network")
    return res


@router.patch("/dhcp-server/networks/{item_id}")
async def update_dhcp_network(
    router_id: uuid.UUID,
    item_id: str,
    payload: DhcpNetworkUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una red existente del servidor DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.gateway is not None:
        patch_data["gateway"] = payload.gateway
    if payload.dns_server is not None:
        patch_data["dns-server"] = payload.dns_server
    if payload.domain is not None:
        patch_data["domain"] = payload.domain
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/ip/dhcp-server/network/{item_id}")
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server/network",
            action="update",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/dhcp-server/network/{item_id}", json_data=patch_data),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/network")
    return res


@router.delete("/dhcp-server/networks/{item_id}")
async def delete_dhcp_network(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una subred del servidor DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ip/dhcp-server/network/{item_id}")
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server/network",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ip/dhcp-server/network/{item_id}"),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/network")
    return res


# ============================================================================
# DHCP CLIENTS (WAN)
# ============================================================================


@router.get("/dhcp-clients")
async def list_dhcp_clients(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista clientes DHCP WAN configurados."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/dhcp-client", client, refresh)


@router.post("/dhcp-clients", status_code=status.HTTP_201_CREATED)
async def create_dhcp_client(
    router_id: uuid.UUID,
    payload: DhcpClientCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un nuevo cliente DHCP en una interfaz WAN."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "interface": payload.interface,
        "add-default-route": "yes" if payload.add_default_route else "no",
        "use-peer-dns": "yes" if payload.use_peer_dns else "no",
        "use-peer-ntp": "yes" if payload.use_peer_ntp else "no",
        "disabled": payload.disabled,
    }
    if payload.comment:
        body["comment"] = payload.comment

    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-client",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ip/dhcp-client", json_data=body),
        )


@router.patch("/dhcp-clients/{item_id}")
async def update_dhcp_client(
    router_id: uuid.UUID,
    item_id: str,
    payload: DhcpClientUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica opciones de un cliente DHCP WAN."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.add_default_route is not None:
        patch_data["add-default-route"] = "yes" if payload.add_default_route else "no"
    if payload.use_peer_dns is not None:
        patch_data["use-peer-dns"] = "yes" if payload.use_peer_dns else "no"
    if payload.use_peer_ntp is not None:
        patch_data["use-peer-ntp"] = "yes" if payload.use_peer_ntp else "no"
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/ip/dhcp-client/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-client",
            action="update",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/dhcp-client/{item_id}", json_data=patch_data),
        )


@router.delete("/dhcp-clients/{item_id}")
async def delete_dhcp_client(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina un cliente DHCP WAN."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/ip/dhcp-client/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-client",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/ip/dhcp-client/{item_id}"),
        )


@router.post("/dhcp-clients/{item_id}/renew")
async def renew_dhcp_client(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Renueva concesión WAN del cliente DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.post("/ip/dhcp-client/renew", json_data={"numbers": item_id})


@router.post("/dhcp-clients/{item_id}/release")
async def release_dhcp_client(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Libera concesión WAN del cliente DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.post("/ip/dhcp-client/release", json_data={"numbers": item_id})


# ============================================================================
# DNS & NEIGHBORS
# ============================================================================



@router.get("/dns")
async def get_dns_info(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Consulta configuración DNS y registros estáticos del MikroTik."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        dns_config = await client.get("/ip/dns")
        static_records = await client.get("/ip/dns/static")
        return {
            "config": dns_config if isinstance(dns_config, dict) else {},
            "static_records": static_records if isinstance(static_records, list) else [],
        }


@router.post("/dns/flush-cache")
async def flush_dns_cache(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Vacía la caché DNS del router."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.post("/ip/dns/cache/flush")


@router.get("/neighbors")
async def list_neighbors(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Descubre equipos vecinos conectados mediante MNDP/CDP/LLDP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/neighbor", client, refresh)


# ============================================================================
# IP SERVICES (CON REGLA ANTI-SUICIDIO)
# ============================================================================


@router.get("/services")
async def list_services(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista servicios activos del router (www-ssl, winbox, ssh, api, etc.)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/service", client, refresh)


@router.patch("/services/{item_id}")
async def update_service(
    router_id: uuid.UUID,
    item_id: str,
    payload: IpServiceUpdateRequest,
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
    """Modifica puerto o IPs permitidas de un servicio con regla anti-suicidio en www-ssl."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.port is not None:
        patch_data["port"] = payload.port
    if payload.address is not None:
        patch_data["address"] = payload.address
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled

    async with client:
        await _verify_anti_suicide_rule(client, item_id, payload)
        before = await client.get(f"/ip/service/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="ip/service",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/ip/service/{item_id}", json_data=patch_data),
        )
