# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Firewall (Filter, NAT, Mangle, RAW, Address-Lists, Connections y Move)."""

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
    intercept_maker_checker_if_needed,
    invalidate_webfig_cache,
)
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.operations import CriticalActionTypeEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_firewall import (
    AddressListCreateRequest,
    FirewallRuleCreateRequest,
    FirewallRuleMoveRequest,
    FirewallRuleUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/firewall", tags=["WebFig Firewall"])

_VALID_PROTOS = {"ip", "ipv6"}
_VALID_TABLES = {"filter", "nat", "mangle", "raw"}


def _validate_firewall_params(proto: str, table_type: str) -> None:
    if proto not in _VALID_PROTOS:
        raise HTTPException(status_code=400, detail=f"Protocolo inválido: {proto}. Use 'ip' o 'ipv6'")
    if table_type not in _VALID_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de tabla inválido: {table_type}. Use filter, nat, mangle o raw",
        )


def _check_input_chain_permission(chain: str | None, role: str) -> None:
    if chain and chain.lower() == "input":
        allowed = {
            SystemRoleEnum.SUPERADMIN_GLOBAL.value,
            SystemRoleEnum.TENANT_ADMIN.value,
            SystemRoleEnum.SUPERVISOR.value,
            SystemRoleEnum.SUPPORT_L3.value,
        }
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Modificaciones en la cadena 'input' exigen rol SUPPORT_L3 o aprobación Maker-Checker",
            )


# ============================================================================
# REGLAS DE FIREWALL (FILTER, NAT, MANGLE, RAW)
# ============================================================================


@router.get("/{proto}/{table_type}")
async def list_rules(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista reglas de Firewall en orden estricto con contadores de bytes y paquetes."""
    if table_type in {"address-list", "address-lists"}:
        return await list_address_lists(router_id=router_id, proto=proto, refresh=refresh, claims=claims, db=db)
    if table_type in {"connection", "connections"}:
        return await list_connections(router_id=router_id, refresh=refresh, claims=claims, db=db)
    _validate_firewall_params(proto, table_type)
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    endpoint = f"/{proto}/firewall/{table_type}"
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, endpoint, client, refresh)


@router.post("/{proto}/{table_type}", status_code=status.HTTP_201_CREATED)
async def create_rule(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
    payload: FirewallRuleCreateRequest,
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
    """Crea una nueva regla de Firewall protegida por Safe Mode o interceptada por Maker-Checker (L2)."""
    _validate_firewall_params(proto, table_type)

    body: dict[str, Any] = {"chain": payload.chain, "action": payload.action, "disabled": payload.disabled}
    if payload.src_address:
        body["src-address"] = payload.src_address
    if payload.dst_address:
        body["dst-address"] = payload.dst_address
    if payload.protocol:
        body["protocol"] = payload.protocol
    if payload.src_port:
        body["src-port"] = payload.src_port
    if payload.dst_port:
        body["dst-port"] = payload.dst_port
    if payload.in_interface:
        body["in-interface"] = payload.in_interface
    if payload.out_interface:
        body["out-interface"] = payload.out_interface
    if payload.comment:
        body["comment"] = payload.comment
    if payload.place_before:
        body["place-before"] = payload.place_before
    if payload.to_addresses:
        body["to-addresses"] = payload.to_addresses
    if payload.to_ports:
        body["to-ports"] = payload.to_ports
    body.update(payload.extra_params)

    menu = f"{proto}/firewall/{table_type}"
    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Crear regla Firewall {proto.upper()}/{table_type} (chain={payload.chain}, action={payload.action})",
        ros_rest_method="PUT",
        ros_rest_path=f"/{menu}",
        request_payload=body,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _check_input_chain_permission(payload.chain, claims.get("rol", ""))

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await execute_safe_mutation(
            client=client,
            menu=menu,
            action="create",
            before_state=body,
            coro_fn=lambda: client.put(f"/{menu}", json_data=body),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, f"/{menu}")
    return res


def _build_firewall_patch_data(payload: FirewallRuleUpdateRequest) -> dict[str, Any]:
    mapping: dict[str, Any] = {
        "chain": payload.chain,
        "action": payload.action,
        "src-address": payload.src_address,
        "dst-address": payload.dst_address,
        "protocol": payload.protocol,
        "src-port": payload.src_port,
        "dst-port": payload.dst_port,
        "in-interface": payload.in_interface,
        "out-interface": payload.out_interface,
        "to-addresses": payload.to_addresses,
        "to-ports": payload.to_ports,
        "comment": payload.comment,
        "disabled": payload.disabled,
    }
    patch_data = {k: v for k, v in mapping.items() if v is not None}
    patch_data.update(payload.extra_params)
    return patch_data


@router.patch("/{proto}/{table_type}/{rule_id}")
async def update_rule(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
    rule_id: str,
    payload: FirewallRuleUpdateRequest,
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
    """Modifica una regla de Firewall existente bajo Safe Mode o Maker-Checker (L2)."""
    _validate_firewall_params(proto, table_type)
    patch_data = _build_firewall_patch_data(payload)
    menu = f"{proto}/firewall/{table_type}"

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Modificar regla Firewall {proto.upper()}/{table_type} ({rule_id})",
        ros_rest_method="PATCH",
        ros_rest_path=f"/{menu}/{rule_id}",
        request_payload=patch_data,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _check_input_chain_permission(payload.chain, claims.get("rol", ""))

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/{menu}/{rule_id}")
        res = await execute_safe_mutation(
            client=client,
            menu=menu,
            action="set",
            item_id=rule_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/{menu}/{rule_id}", json_data=patch_data),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, f"/{menu}")
    return res


@router.delete("/{proto}/{table_type}/{rule_id}")
async def delete_rule(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
    rule_id: str,
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
    """Elimina una regla de Firewall bajo Safe Mode (deshabilitación preventiva) o Maker-Checker (L2)."""
    if table_type in {"address-list", "address-lists"}:
        return await delete_address_list(
            router_id=router_id,
            proto=proto,
            item_id=rule_id,
            claims=claims,
            db=db,
        )
    _validate_firewall_params(proto, table_type)
    menu = f"{proto}/firewall/{table_type}"

    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Eliminar regla Firewall {proto.upper()}/{table_type} ({rule_id})",
        ros_rest_method="DELETE",
        ros_rest_path=f"/{menu}/{rule_id}",
        request_payload={".id": rule_id},
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/{menu}/{rule_id}")
        if isinstance(before, dict):
            _check_input_chain_permission(before.get("chain"), claims.get("rol", ""))
        res = await execute_safe_mutation(
            client=client,
            menu=menu,
            action="delete",
            item_id=rule_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/{menu}/{rule_id}"),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, f"/{menu}")
    return res


@router.post("/{proto}/{table_type}/move")
async def move_rule(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
    payload: FirewallRuleMoveRequest,
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
    """Reordena una regla de Firewall (Drag & Drop) bajo Safe Mode."""
    _validate_firewall_params(proto, table_type)
    _, client = await get_router_and_client(router_id, claims, db)
    menu = f"{proto}/firewall/{table_type}"
    body = {"numbers": payload.numbers, "destination": payload.destination}
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu=menu,
            action="move",
            before_state=body,
            coro_fn=lambda: client.post(f"/{menu}/move", json_data=body),
        )


@router.post("/{proto}/{table_type}/reset-counters")
async def reset_counters(
    router_id: uuid.UUID,
    proto: str,
    table_type: str,
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
    """Reinicia a cero contadores de bytes y paquetes de las reglas de Firewall."""
    _validate_firewall_params(proto, table_type)
    _, client = await get_router_and_client(router_id, claims, db)
    endpoint = f"/{proto}/firewall/{table_type}/reset-counters-all"
    async with client:
        return await client.post(endpoint)


# ============================================================================
# ADDRESS LISTS
# ============================================================================


@router.get("/{proto}/address-lists")
@router.get("/{proto}/address-list")
async def list_address_lists(
    router_id: uuid.UUID,
    proto: str,
    list_name: str | None = Query(default=None, alias="list"),
    address: str | None = Query(default=None),
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista entradas de Address-List del Firewall."""
    if proto not in _VALID_PROTOS:
        raise HTTPException(status_code=400, detail="Protocolo inválido")
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    endpoint = f"/{proto}/firewall/address-list"
    async with client:
        res = await cached_mikrotik_get(redis, tenant_id, router_id, endpoint, client, refresh)
        if isinstance(res, list):
            if list_name:
                res = [item for item in res if item.get("list") == list_name]
            if address:
                res = [item for item in res if item.get("address") == address]
        return res


@router.post("/{proto}/address-lists", status_code=status.HTTP_201_CREATED)
@router.post("/{proto}/address-list", status_code=status.HTTP_201_CREATED)
async def create_address_list(
    router_id: uuid.UUID,
    proto: str,
    payload: AddressListCreateRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Agrega una IP o prefijo a una Address-List bajo Safe Mode o Maker-Checker (L2)."""
    if proto not in _VALID_PROTOS:
        raise HTTPException(status_code=400, detail="Protocolo inválido")
    body: dict[str, Any] = {"list": payload.list, "address": payload.address}
    if payload.timeout:
        body["timeout"] = payload.timeout
    if payload.comment:
        body["comment"] = payload.comment

    menu = f"{proto}/firewall/address-list"
    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Agregar Address-List {payload.list}: {payload.address}",
        ros_rest_method="PUT",
        ros_rest_path=f"/{menu}",
        request_payload=body,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        requester_justification=payload.comment,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await execute_safe_mutation(
            client=client,
            menu=menu,
            action="create",
            before_state=body,
            coro_fn=lambda: client.put(f"/{menu}", json_data=body),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, f"/{menu}")
    return res


@router.delete("/{proto}/address-lists/{item_id}")
@router.delete("/{proto}/address-list/{item_id}")
async def delete_address_list(
    router_id: uuid.UUID,
    proto: str,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una entrada de Address-List bajo Safe Mode o Maker-Checker (L2)."""
    if proto not in _VALID_PROTOS:
        raise HTTPException(status_code=400, detail="Protocolo inválido")
    menu = f"{proto}/firewall/address-list"
    intercepted = await intercept_maker_checker_if_needed(
        db=db,
        claims=claims,
        router_id=router_id,
        summary=f"Eliminar entrada Address-List {proto.upper()} ({item_id})",
        ros_rest_method="DELETE",
        ros_rest_path=f"/{menu}/{item_id}",
        request_payload={".id": item_id},
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
    )
    if intercepted is not None:
        return intercepted

    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/{menu}/{item_id}")
        res = await execute_safe_mutation(
            client=client,
            menu=menu,
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/{menu}/{item_id}"),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, f"/{menu}")
    return res


# ============================================================================
# CONNECTION TRACKING
# ============================================================================


@router.get("/connections")
@router.get("/{proto}/connections")
@router.get("/{proto}/connection")
async def list_connections(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Consulta la tabla de Connection Tracking (limitada a top 500)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/firewall/connection", client, refresh)


@router.delete("/connections/{conn_id}")
async def delete_connection(
    router_id: uuid.UUID,
    conn_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina/cierra una conexión activa de la tabla de Connection Tracking."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.delete(f"/ip/firewall/connection/{conn_id}")
