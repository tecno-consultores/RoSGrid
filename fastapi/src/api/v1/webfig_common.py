# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Utilidades comunes para endpoints WebFig: resolución de router, RBAC, caché Redis y Safe Mode."""

import hashlib
import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.crypto import decrypt_aes_gcm
from src.mikrotik.client import MikrotikClientError, MikrotikRestClient
from src.mikrotik.safemode import build_rollback_command, execute_with_safemode
from src.mikrotik.ssl_tofu import MikrotikSSLError
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.models.inventory import Router, SSLTrustStatusEnum
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    CriticalActionTypeEnum,
)

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

    aad = f"{tenant_id}:{r.id}".encode()
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
        timeout=4.0,
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

    query = (
        select(Router).options(selectinload(Router.vault)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    client = _create_client_from_vault(r, tenant_id)

    if r.ssl_trust_status == SSLTrustStatusEnum.PENDING_TOFU or not r.ssl_sha256_fingerprint:
        try:
            fp = await client.ensure_ssl_verified()
            if fp:
                r.ssl_sha256_fingerprint = fp
                r.ssl_trust_status = SSLTrustStatusEnum.TRUSTED_PINNED
                r.ssl_pinned_at = datetime.now(UTC)
                client.ssl_pinned_fingerprint = fp
                r.is_reachable = True
                r.last_seen_at = datetime.now(UTC)
                if not r.ros_version or not r.ros_identity:
                    from src.api.v1.inventory_helpers import discover_hardware

                    await discover_hardware(client, r)
                    r.last_discovery_sync_at = datetime.now(UTC)
                await db.commit()
                logger.info("Auto-pinning TOFU exitoso en WebFig para router %s: %s", r.display_name, fp)
        except Exception as exc:
            logger.warning("Fallo al auto-fijar TOFU en WebFig para %s: %s", r.display_name, exc)

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
    ep_hash = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()[:16]
    cache_key = f"rg:{tenant_id}:rcache:{router_id}:{ep_hash}"

    if not refresh:
        raw_cached = await redis.get(cache_key)
        if raw_cached:
            try:
                return json.loads(raw_cached)
            except Exception as exc:
                logger.debug("Error al deserializar caché: %s", exc)

    try:
        data = await client.get(endpoint)
    except HTTPException:
        raise
    except (ConnectionError, TimeoutError, OSError, MikrotikClientError, MikrotikSSLError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo conectar al router MikroTik en {endpoint}: {exc}",
        ) from exc
    if data is not None:
        try:
            await redis.setex(cache_key, ttl_seconds, json.dumps(data))
        except Exception as exc:
            logger.debug("Fallo al escribir en caché Redis: %s", exc)
    return data


async def invalidate_webfig_cache(
    redis: Any,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    endpoint: str,
) -> None:
    """Invalida las entradas de caché corto de un endpoint WebFig tras una mutación."""
    if not redis:
        return
    clean_ep = endpoint.strip("/")
    for candidate in (f"/{clean_ep}", clean_ep):
        ep_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]
        cache_key = f"rg:{tenant_id}:rcache:{router_id}:{ep_hash}"
        try:
            await redis.delete(cache_key)
        except Exception as exc:
            logger.debug("Fallo al invalidar caché Redis %s: %s", cache_key, exc)


_MAKER_CHECKER_INTERCEPT_ROLES = {
    SystemRoleEnum.SUPPORT_L2.value,
    SystemRoleEnum.SUPPORT_L1.value,
}


async def intercept_maker_checker_if_needed(
    db: AsyncSession,
    claims: dict[str, Any],
    router_id: uuid.UUID,
    summary: str,
    ros_rest_method: str,
    ros_rest_path: str,
    request_payload: dict[str, Any],
    action_type: CriticalActionTypeEnum = CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
    previous_state_snapshot: dict[str, Any] | None = None,
    requester_justification: str | None = None,
    intercept_roles: set[str] | None = None,
) -> JSONResponse | None:
    """Intercepta mutaciones sensibles realizadas por roles L1/L2 y las envía a la bandeja Maker-Checker (HTTP 202)."""
    role = str(claims.get("rol", ""))
    target_roles = intercept_roles if intercept_roles is not None else _MAKER_CHECKER_INTERCEPT_ROLES
    if role not in target_roles:
        return None

    tenant_id = uuid.UUID(str(claims["tid"]))
    user_id = uuid.UUID(str(claims["sub"]))
    now_utc = datetime.now(UTC)
    clean_path = f"/{ros_rest_path.strip('/')}"

    try:
        perm_stmt = select(UserRouterPermission).where(
            UserRouterPermission.tenant_id == tenant_id,
            UserRouterPermission.user_id == user_id,
            UserRouterPermission.router_id == router_id,
        )
        perm_res = await db.execute(perm_stmt)
        perm = perm_res.scalar_one_or_none() if perm_res is not None and hasattr(perm_res, "scalar_one_or_none") else None
        if isinstance(perm, UserRouterPermission) and perm.bypass_maker_checker is True:
            return None

        dup_stmt = select(ApprovalRequest).where(
            ApprovalRequest.tenant_id == tenant_id,
            ApprovalRequest.router_id == router_id,
            ApprovalRequest.status == ApprovalStatusEnum.PENDING,
            ApprovalRequest.ros_rest_method == ros_rest_method.upper(),
            ApprovalRequest.ros_rest_path == clean_path,
        )
        dup_res = await db.execute(dup_stmt)
        scalars_obj = dup_res.scalars() if dup_res is not None and hasattr(dup_res, "scalars") else None
        candidates = scalars_obj.all() if scalars_obj is not None and hasattr(scalars_obj, "all") else []
        if isinstance(candidates, list):
            for existing in candidates:
                if (
                    isinstance(existing, ApprovalRequest)
                    and existing.request_payload == request_payload
                    and existing.expires_at > now_utc
                ):
                    return JSONResponse(
                        status_code=status.HTTP_202_ACCEPTED,
                        content={
                            "status": "INTERCEPTED_FOR_APPROVAL",
                            "approval_request_id": str(existing.id),
                            "deduplicated": True,
                            "detail": "Esta solicitud ya se encuentra en espera de aprobación humana en la bandeja Maker-Checker.",
                        },
                    )
    except Exception as exc:
        logger.debug("Omitiendo verificación previa de Maker-Checker: %s", exc)

    approval_id = uuid.uuid4()
    justification = (
        requester_justification
        or str(request_payload.get("comment") or "")
        or f"Cambio solicitado desde consola WebFig por operador ({role})"
    )

    approval = ApprovalRequest(
        id=approval_id,
        tenant_id=tenant_id,
        router_id=router_id,
        action_type=action_type,
        status=ApprovalStatusEnum.PENDING,
        summary=summary[:255],
        requester_justification=justification,
        ros_rest_method=ros_rest_method.upper(),
        ros_rest_path=clean_path,
        request_payload=request_payload,
        previous_state_snapshot=previous_state_snapshot,
        requested_by=user_id,
        expires_at=now_utc + timedelta(hours=24),
        created_at=now_utc,
    )
    db.add(approval)
    await db.commit()

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "INTERCEPTED_FOR_APPROVAL",
            "approval_request_id": str(approval.id),
            "detail": "Operación enviada a Maker-Checker. En espera de aprobación humana por Nivel 3, Supervisor o Administrador.",
        },
    )


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
    try:
        return await execute_with_safemode(
            client=client,
            rollback_cli=rollback_cmd,
            operation_fn=coro_fn,
            interval_seconds=60,
        )
    except HTTPException:
        raise
    except (ConnectionError, TimeoutError, OSError, MikrotikClientError, MikrotikSSLError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo ejecutar mutación en el router MikroTik ({menu}): {exc}",
        ) from exc
