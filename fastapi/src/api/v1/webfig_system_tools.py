# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: System (Live-Status, Identity, Users, Scheduler) y Tools de Diagnóstico en Vivo."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
)
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_ops import (
    RouterPingRequest,
    RouterPingResponse,
    RouterTorchRequest,
    RouterTracerouteRequest,
    SystemIdentityUpdateRequest,
    SystemRebootRequest,
    SystemScriptCreateRequest,
    SystemUserCreateRequest,
    SystemUserUpdateRequest,
)

logger = logging.getLogger(__name__)

system_router = APIRouter(prefix="/routers/{router_id}/webfig/system", tags=["WebFig System"])
tools_router = APIRouter(prefix="/routers/{router_id}/webfig/tools", tags=["WebFig Tools"])

_SYSTEM_ADMIN_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


def _filter_schedulers(raw_schedulers: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_schedulers, list):
        return []
    filtered = []
    for s in raw_schedulers:
        if isinstance(s, dict):
            name = str(s.get("name", "")).lower()
            if not name.startswith("rosgrid-safemode-") and not name.startswith("rosgrid_safemode_"):
                filtered.append(s)
    return filtered


def _parse_ping_results(address: str, raw_results: Any, count: int) -> RouterPingResponse:
    items = raw_results if isinstance(raw_results, list) else []
    received = sum(1 for r in items if isinstance(r, dict) and r.get("status") in (None, "ok", 0))
    loss_pct = round(((count - received) / max(1, count)) * 100.0, 2)
    return RouterPingResponse(
        target=address,
        sent=count,
        received=received,
        packet_loss_pct=loss_pct,
        min_rtt_ms=None,
        avg_rtt_ms=None,
        max_rtt_ms=None,
        results=items,
    )


async def _fetch_system_health(client: MikrotikRestClient) -> dict[str, Any]:
    try:
        health = await client.get("/system/health")
        return health if isinstance(health, dict) else {}
    except Exception:
        return {}


async def _fetch_system_clock(client: MikrotikRestClient) -> dict[str, Any]:
    try:
        clock = await client.get("/system/clock")
        return clock if isinstance(clock, dict) else {}
    except Exception:
        return {}


# ============================================================================
# SYSTEM ENDPOINTS (LIVE-STATUS, IDENTITY, USERS, SCRIPTS, SCHEDULER, REBOOT)
# ============================================================================


@system_router.get("/live-status")
async def get_live_status(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> dict[str, Any]:
    """Consulta estado en vivo del router (Cero persistencia en PostgreSQL)."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        resource = await client.get("/system/resource")
        routerboard = await client.get("/system/routerboard")
        health = await _fetch_system_health(client)
        clock = await _fetch_system_clock(client)
        return {
            "resource": resource if isinstance(resource, dict) else {},
            "routerboard": routerboard if isinstance(routerboard, dict) else {},
            "health": health,
            "clock": clock,
        }


@system_router.patch("/identity")
async def update_identity(
    router_id: uuid.UUID,
    payload: SystemIdentityUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Cambia el identity interno del MikroTik y sincroniza la DB de RoSGrid."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    new_name = payload.name.strip()
    async with client:
        res = await client.post("/system/identity/set", json_data={"name": new_name})
    router_obj.ros_identity = new_name
    await db.commit()
    return res or {"name": new_name}


@system_router.get("/users")
async def list_system_users(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista usuarios internos y sesiones activas en el MikroTik."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        users = await client.get("/user")
        active = await client.get("/user/active")
        return {
            "users": users if isinstance(users, list) else [],
            "active_sessions": active if isinstance(active, list) else [],
        }


@system_router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_system_user(
    router_id: uuid.UUID,
    payload: SystemUserCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un usuario interno en el MikroTik bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "name": payload.name,
        "password": payload.password,
        "group": payload.group,
    }
    if payload.address:
        body["address"] = payload.address
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="user",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/user", json_data=body),
        )


def _build_user_patch_data(payload: SystemUserUpdateRequest) -> dict[str, Any]:
    mapping: dict[str, Any] = {
        "password": payload.password,
        "group": payload.group,
        "address": payload.address,
        "comment": payload.comment,
        "disabled": payload.disabled,
    }
    return {k: v for k, v in mapping.items() if v is not None}


def _check_disabling_api_user(router_obj: Any, before: Any, disabled: bool | None) -> None:
    if isinstance(before, dict) and router_obj.vault:
        if before.get("name") == router_obj.vault.api_username and disabled is True:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Operación bloqueada: No puedes deshabilitar el usuario API de RoSGrid.",
            )


@system_router.patch("/users/{item_id}")
async def update_system_user(
    router_id: uuid.UUID,
    item_id: str,
    payload: SystemUserUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica permisos o clave de un usuario interno bajo Safe Mode."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    patch_data = _build_user_patch_data(payload)

    async with client:
        before = await client.get(f"/user/{item_id}")
        _check_disabling_api_user(router_obj, before, payload.disabled)
        return await execute_safe_mutation(
            client=client,
            menu="user",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/user/{item_id}", json_data=patch_data),
        )


@system_router.get("/scripts")
async def list_scripts(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista scripts guardados en el router."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await client.get("/system/script")


@system_router.post("/scripts", status_code=status.HTTP_201_CREATED)
async def create_script(
    router_id: uuid.UUID,
    payload: SystemScriptCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un script en el MikroTik."""
    _, client = await get_router_and_client(router_id, claims, db)
    body = {"name": payload.name, "source": payload.source, "policy": payload.policy}
    async with client:
        return await client.put("/system/script", json_data=body)


@system_router.post("/scripts/{item_id}/run")
async def run_script(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Ejecuta un script interno bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="system/script",
            action="run",
            coro_fn=lambda: client.post("/system/script/run", json_data={".id": item_id}),
        )


@system_router.get("/scheduler")
async def list_schedulers(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista tareas programadas filtrando los schedulers internos de Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        raw = await client.get("/system/scheduler")
        return _filter_schedulers(raw)


@system_router.get("/packages")
async def list_packages(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista paquetes instalados y consulta disponibilidad de actualizaciones."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        packages = await client.get("/system/package")
        update_info = None
        try:
            update_info = await client.post("/system/package/update/check-for-updates")
        except Exception as exc:
            logger.debug("Error check-for-updates: %s", exc)
        return {
            "packages": packages if isinstance(packages, list) else [],
            "update_check": update_info if isinstance(update_info, (dict, list)) else {},
        }


@system_router.post("/reboot")
async def reboot_router(
    router_id: uuid.UUID,
    payload: SystemRebootRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> dict[str, str]:
    """Reinicia el router registrando el motivo en auditoría inmutable."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    ip_addr = request.client.host if request.client else "127.0.0.1"

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3),
        actor_ip=ip_addr,
        actor_user_agent=request.headers.get("User-Agent"),
        event_category="SYSTEM",
        event_action="ROUTER_REBOOT_TRIGGERED",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"reason": payload.reason},
    )
    await db.commit()

    async with client:
        await client.post("/system/reboot")
    return {"status": "REBOOT_INITIATED", "reason": payload.reason}


# ============================================================================
# DIAGNÓSTICO EN VIVO (TOOLS)
# ============================================================================


@tools_router.post("/ping", response_model=RouterPingResponse)
async def run_ping(
    router_id: uuid.UUID,
    payload: RouterPingRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterPingResponse:
    """Ejecuta comando Ping desde el MikroTik."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "address": payload.address,
        "count": payload.count,
        "size": payload.size,
        "routing-table": payload.routing_table,
    }
    if payload.src_address:
        body["src-address"] = payload.src_address
    if payload.interface:
        body["interface"] = payload.interface
    if payload.do_not_fragment:
        body["do-not-fragment"] = True

    async with client:
        raw_res = await client.post("/ping", json_data=body)
        return _parse_ping_results(payload.address, raw_res, payload.count)


@tools_router.post("/traceroute")
async def run_traceroute(
    router_id: uuid.UUID,
    payload: RouterTracerouteRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Ejecuta Traceroute desde el MikroTik hacia un destino."""
    _, client = await get_router_and_client(router_id, claims, db)
    body = {
        "address": payload.address,
        "count": payload.count,
        "max-hops": payload.max_hops,
        "timeout": payload.timeout,
    }
    async with client:
        return await client.post("/tool/traceroute", json_data=body)


@tools_router.post("/torch")
async def run_torch(
    router_id: uuid.UUID,
    payload: RouterTorchRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Captura y analiza flujos de consumo en vivo en una interfaz."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"interface": payload.interface, "duration": payload.duration_seconds}
    if payload.src_address:
        body["src-address"] = payload.src_address
    if payload.dst_address:
        body["dst-address"] = payload.dst_address
    if payload.port:
        body["port"] = payload.port
    if payload.protocol:
        body["protocol"] = payload.protocol
    async with client:
        return await client.post("/tool/torch", json_data=body)


@tools_router.get("/logs")
async def get_router_logs(
    router_id: uuid.UUID,
    topics: str | None = Query(default=None),
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Obtiene las últimas líneas del log de memoria del MikroTik."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        raw_logs = await cached_mikrotik_get(redis, tenant_id, router_id, "/log", client, refresh)
        if isinstance(raw_logs, list) and topics:
            t_filter = topics.lower()
            return [line for line in raw_logs if t_filter in str(line.get("topics", "")).lower()]
        return raw_logs
