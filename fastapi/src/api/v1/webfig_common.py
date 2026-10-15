# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Utilidades comunes para endpoints WebFig: resolución de router, RBAC, caché Redis y Safe Mode."""

import hashlib
import json
import logging
import uuid
from typing import Any, Awaitable, Callable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.crypto import decrypt_aes_gcm
from src.mikrotik.client import MikrotikRestClient
from src.mikrotik.safemode import build_rollback_command, execute_with_safemode
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.models.inventory import Router

logger = logging.getLogger(__name__)

_GLOBAL_ACCESS_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
    SystemRoleEnum.SUPERVISOR.value,
    SystemRoleEnum.INVENTORY_MANAGER.value,
    SystemRoleEnum.AUDITOR.value,
}


async def _check_router_permission(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    router_id: uuid.UUID,
    claims: dict[str, Any],
) -> None:
    role = claims.get("rol")
    has_all = claims.get("all_r", False)
    if role in _GLOBAL_ACCESS_ROLES or has_all:
        return

    stmt = select(UserRouterPermission).where(
        UserRouterPermission.tenant_id == tenant_id,
        UserRouterPermission.user_id == user_id,
        UserRouterPermission.router_id == router_id,
        UserRouterPermission.can_read.is_(True),
    )
    perm = (await db.execute(stmt)).scalar_one_or_none()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso asignado para acceder a este router",
        )


def _create_client_from_vault(r: Router, tenant_id: uuid.UUID) -> MikrotikRestClient:
    if not r.vault:
        raise HTTPException(status_code=400, detail="El router no tiene credenciales en bóveda")

    aad = f"{tenant_id}:{r.id}".encode("utf-8")
    cur_pass = decrypt_aes_gcm(
        r.vault.current_password_ciphertext,
        r.vault.current_password_iv,
        r.vault.current_password_tag,
        aad,
    ).decode("utf-8")

    prev_pass: str | None = None
    if r.vault.previous_password_ciphertext and r.vault.previous_password_iv and r.vault.previous_password_tag:
        prev_pass = decrypt_aes_gcm(
            r.vault.previous_password_ciphertext,
            r.vault.previous_password_iv,
            r.vault.previous_password_tag,
            aad,
        ).decode("utf-8")

    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    return MikrotikRestClient(
        host=host,
        port=r.api_port,
        username=r.vault.api_username,
        password=cur_pass,
        previous_password=prev_pass,
        ssl_pinned_fingerprint=r.ssl_sha256_fingerprint,
        timeout=10.0,
    )


async def get_router_and_client(
    router_id: uuid.UUID,
    claims: dict[str, Any],
    db: AsyncSession,
) -> tuple[Router, MikrotikRestClient]:
    """Valida permisos del usuario y devuelve el router junto con su cliente REST configurado."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    await _check_router_permission(db, tenant_id, user_id, router_id, claims)

    query = select(Router).options(selectinload(Router.vault)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    client = _create_client_from_vault(r, tenant_id)
    return r, client


async def cached_mikrotik_get(
    redis: Any,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    endpoint: str,
    client: MikrotikRestClient,
    refresh: bool = False,
    ttl_seconds: int = 5,
) -> Any:
    """Ejecuta una petición GET con caché corto en Redis de 5s para evitar sobrecarga del router."""
    ep_hash = hashlib.md5(endpoint.encode("utf-8")).hexdigest()
    cache_key = f"rg:{tenant_id}:rcache:{router_id}:{ep_hash}"

    if not refresh:
        raw_cached = await redis.get(cache_key)
        if raw_cached:
            try:
                return json.loads(raw_cached)
            except Exception:
                pass

    data = await client.get(endpoint)
    if data is not None:
        try:
            await redis.setex(cache_key, ttl_seconds, json.dumps(data))
        except Exception as exc:
            logger.debug("Fallo al escribir en caché Redis: %s", exc)
    return data


async def execute_safe_mutation(
    client: MikrotikRestClient,
    menu: str,
    action: str,
    coro_fn: Callable[[], Awaitable[Any]],
    item_id: str | None = None,
    before_state: dict[str, Any] | None = None,
) -> Any:
    """Envuelve una mutación sensible en el motor Dead Man's Switch (Safe Mode a 60s)."""
    rollback_cmd = build_rollback_command(
        menu_path=menu,
        action=action,
        item_id=item_id,
        before_state=before_state,
    )
    return await execute_with_safemode(
        client=client,
        rollback_cli=rollback_cmd,
        operation_fn=coro_fn,
        interval_seconds=60,
    )
