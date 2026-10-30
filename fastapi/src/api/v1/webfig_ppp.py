# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: PPPoE, Perfiles, Secrets, Reconexión Rápida L1 y VPNs."""

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
from src.schemas.webfig_ops import (
    PppoeServerCreateRequest,
    PppoeServerUpdateRequest,
    PppProfileCreateRequest,
    PppProfileUpdateRequest,
    PppSecretCreateRequest,
    PppSecretUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/ppp", tags=["WebFig PPP"])

_ADMIN_ROLES = {SystemRoleEnum.SUPERADMIN_GLOBAL.value, SystemRoleEnum.TENANT_ADMIN.value}
_PPP_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
)


def _sanitize_secrets(raw_list: Any, role: str) -> Any:
    if not isinstance(raw_list, list):
        return raw_list
    if role in _ADMIN_ROLES:
        return raw_list
    sanitized = []
    for item in raw_list:
        if isinstance(item, dict):
            copy_item = dict(item)
            if "password" in copy_item:
                copy_item["password"] = "[REDACTED]"  # nosec B105
            sanitized.append(copy_item)
        else:
            sanitized.append(item)
    return sanitized


# ============================================================================
# ACTIVE SESSIONS (CONEXIONES Y RECONEXIÓN L1)
# ============================================================================


@router.get("/active")
async def list_active_sessions(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista sesiones PPPoE/VPN activas (caller-id, IP asignada, uptime y encoding)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ppp/active", client, refresh)


@router.delete("/active/{session_id}")
async def disconnect_active_session(
    router_id: uuid.UUID,
    session_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Reconexión Rápida L1: Desconecta una sesión PPP activa para forzar reconexión del CPE."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ppp/active/{session_id}")


# ============================================================================
# PPP SECRETS & PROFILES
# ============================================================================


@router.get("/secrets")
async def list_secrets(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista cuentas de usuarios PPP con clave ofuscada a roles no administrativos."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        raw = await cached_mikrotik_get(redis, tenant_id, router_id, "/ppp/secret", client, refresh)
        return _sanitize_secrets(raw, claims.get("rol", ""))


@router.post("/secrets", status_code=status.HTTP_201_CREATED)
async def create_secret(
    router_id: uuid.UUID,
    payload: PppSecretCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una nueva cuenta de usuario PPP/VPN."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "password": payload.password,
        "service": payload.service,
        "profile": payload.profile,
        "disabled": payload.disabled,
    }
    if payload.local_address:
        body["local-address"] = payload.local_address
    if payload.remote_address:
        body["remote-address"] = payload.remote_address
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await client.put("/ppp/secret", json_data=body)


@router.patch("/secrets/{item_id}")
async def update_secret(
    router_id: uuid.UUID,
    item_id: str,
    payload: PppSecretUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica perfil de velocidad, IP o estado de un secret PPP."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name:
        patch_data["name"] = payload.name
    if payload.password:
        patch_data["password"] = payload.password
    if payload.service:
        patch_data["service"] = payload.service
    if payload.profile:
        patch_data["profile"] = payload.profile
    if payload.local_address:
        patch_data["local-address"] = payload.local_address
    if payload.remote_address:
        patch_data["remote-address"] = payload.remote_address
    if payload.routes is not None:
        patch_data["routes"] = payload.routes
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    async with client:
        return await client.patch(f"/ppp/secret/{item_id}", json_data=patch_data)


@router.delete("/secrets/{item_id}")
async def delete_secret(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una cuenta PPP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ppp/secret/{item_id}")


@router.get("/profiles")
async def list_profiles(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista perfiles PPP (límites de velocidad, DNS y pools)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ppp/profile", client, refresh)


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(
    router_id: uuid.UUID,
    payload: PppProfileCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un nuevo perfil PPP."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"name": payload.name}
    if payload.local_address:
        body["local-address"] = payload.local_address
    if payload.remote_address:
        body["remote-address"] = payload.remote_address
    if payload.rate_limit:
        body["rate-limit"] = payload.rate_limit
    if payload.dns_server:
        body["dns-server"] = payload.dns_server
    if payload.address_list:
        body["address-list"] = payload.address_list
    if payload.only_one:
        body["only-one"] = payload.only_one
    async with client:
        return await client.put("/ppp/profile", json_data=body)


@router.patch("/profiles/{item_id}")
async def update_profile(
    router_id: uuid.UUID,
    item_id: str,
    payload: PppProfileUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica un perfil PPP existente."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name:
        patch_data["name"] = payload.name
    if payload.local_address is not None:
        patch_data["local-address"] = payload.local_address
    if payload.remote_address is not None:
        patch_data["remote-address"] = payload.remote_address
    if payload.rate_limit is not None:
        patch_data["rate-limit"] = payload.rate_limit
    if payload.dns_server is not None:
        patch_data["dns-server"] = payload.dns_server
    if payload.address_list is not None:
        patch_data["address-list"] = payload.address_list
    if payload.only_one:
        patch_data["only-one"] = payload.only_one
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    async with client:
        return await client.patch(f"/ppp/profile/{item_id}", json_data=patch_data)


@router.delete("/profiles/{item_id}")
async def delete_profile(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina un perfil PPP personalizado."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ppp/profile/{item_id}")


# ============================================================================
# PPPoE SERVERS & IPSEC
# ============================================================================


@router.get("/pppoe-servers")
async def list_pppoe_servers(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista servidores concentradores PPPoE configurados por interfaz."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/pppoe-server/server", client, refresh)


@router.post("/pppoe-servers", status_code=status.HTTP_201_CREATED)
async def create_pppoe_server(
    router_id: uuid.UUID,
    payload: PppoeServerCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un servidor concentrador PPPoE bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "service-name": payload.service_name,
        "interface": payload.interface,
        "default-profile": payload.default_profile,
        "max-mtu": payload.max_mtu,
        "disabled": payload.disabled,
    }
    if payload.max_mru is not None:
        body["max-mru"] = payload.max_mru
    if payload.one_session_per_host is not None:
        body["one-session-per-host"] = "yes" if payload.one_session_per_host else "no"
    menu = "interface/pppoe-server/server"
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu=menu,
            action="create",
            before_state=body,
            coro_fn=lambda: client.put(f"/{menu}", json_data=body),
        )


@router.patch("/pppoe-servers/{item_id}")
async def update_pppoe_server(
    router_id: uuid.UUID,
    item_id: str,
    payload: PppoeServerUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica un servidor concentrador PPPoE existente bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.service_name is not None:
        patch_data["service-name"] = payload.service_name
    if payload.interface is not None:
        patch_data["interface"] = payload.interface
    if payload.default_profile is not None:
        patch_data["default-profile"] = payload.default_profile
    if payload.authentication is not None:
        patch_data["authentication"] = payload.authentication
    if payload.max_mtu is not None:
        patch_data["max-mtu"] = payload.max_mtu
    if payload.max_mru is not None:
        patch_data["max-mru"] = payload.max_mru
    if payload.one_session_per_host is not None:
        patch_data["one-session-per-host"] = "yes" if payload.one_session_per_host else "no"
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled

    menu = "interface/pppoe-server/server"
    async with client:
        before = await client.get(f"/{menu}/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu=menu,
            action="update",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/{menu}/{item_id}", json_data=patch_data),
        )


@router.delete("/pppoe-servers/{item_id}")
async def delete_pppoe_server(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_PPP_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una instancia de servidor concentrador PPPoE bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    menu = "interface/pppoe-server/server"
    async with client:
        before = await client.get(f"/{menu}/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu=menu,
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/{menu}/{item_id}"),
        )


@router.get("/ipsec/active-peers")
async def list_ipsec_peers(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista túneles IPsec activos."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/ipsec/active-peers", client, refresh)
