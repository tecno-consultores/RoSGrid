# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status

from src.core.config import settings
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client


def extract_token_from_request(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


async def get_current_user_claims(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.ROSGRID_JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de acceso inválido o expirado: {exc}",
        ) from exc

    session_id = payload.get("sid")
    tenant_id = payload.get("tid")
    user_id = payload.get("sub")
    role = payload.get("rol")

    if not session_id or not tenant_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado (claims requeridos faltantes)",
        )

    # Verificación en tiempo real contra Redis (Kill-Switch inmediato)
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_alive = await redis.exists(sess_key)
    if not session_alive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o revocada por Kill-Switch",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


def require_roles(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


FEATURE_MODULE_DISABLED_CODE = "FEATURE_MODULE_DISABLED"
FEATURE_CACHE_TTL_SECONDS = 300


def feature_disabled_exception(flag_name: str) -> HTTPException:
    """Construye la respuesta HTTP 403 estándar para módulos deshabilitados por tenant."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": FEATURE_MODULE_DISABLED_CODE,
            "message": f"El módulo '{flag_name}' no está habilitado para esta empresa.",
        },
    )


async def _read_cached_feature(cache_key: str, flag_name: str) -> bool | None:
    """Lee el flag desde la caché L2 de KeyDB. Retorna None si no existe o KeyDB no responde."""
    try:
        raw = await get_redis_client().hget(cache_key, flag_name)
    except Exception:
        return None
    if raw is None:
        return None
    val_str = raw.decode() if isinstance(raw, bytes) else str(raw)
    return val_str.lower() in ("1", "true")


async def _store_cached_feature(cache_key: str, flag_name: str, enabled: bool) -> None:
    """Persiste el flag en KeyDB con TTL corto; los fallos de caché nunca bloquean la petición."""
    try:
        redis = get_redis_client()
        await redis.hset(cache_key, flag_name, "1" if enabled else "0")
        await redis.expire(cache_key, FEATURE_CACHE_TTL_SECONDS)
    except Exception:
        return


async def _read_db_feature(tenant_id: uuid.UUID, flag_name: str) -> bool:
    """Consulta el flag en PostgreSQL vía ORM (columna validada contra la lista blanca)."""
    from sqlalchemy import select

    from src.db.session import engine
    from src.models.core import Tenant

    column = getattr(Tenant, flag_name)
    async with engine.connect() as conn:
        result = await conn.execute(select(column).where(Tenant.id == tenant_id))
        row = result.fetchone()
    return bool(row and row[0])


async def resolve_tenant_feature(tenant_id: uuid.UUID, flag_name: str) -> bool:
    """Resuelve un flag por tenant: KeyDB (L2) -> PostgreSQL -> valor por defecto de la especificación."""
    from src.schemas.tenants import TENANT_FEATURE_DEFAULTS

    cache_key = f"rg:{tenant_id}:features"
    cached = await _read_cached_feature(cache_key, flag_name)
    if cached is not None:
        return cached
    try:
        enabled = await _read_db_feature(tenant_id, flag_name)
    except Exception:
        return bool(TENANT_FEATURE_DEFAULTS.get(flag_name, False))
    await _store_cached_feature(cache_key, flag_name, enabled)
    return enabled


def require_feature(flag_name: str) -> Callable[..., Coroutine[Any, Any, bool]]:
    """Validador de Feature Flags por Tenant (HTTP 403 FEATURE_MODULE_DISABLED) con caché L2 en KeyDB."""
    from src.schemas.tenants import TENANT_FEATURE_DEFAULTS

    if flag_name not in TENANT_FEATURE_DEFAULTS:
        raise ValueError(f"Feature flag desconocido: {flag_name}")

    async def _feature_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> bool:
        tid = claims.get("tid")
        if not tid:
            raise feature_disabled_exception(flag_name)
        if not await resolve_tenant_feature(uuid.UUID(str(tid)), flag_name):
            raise feature_disabled_exception(flag_name)
        return True

    return _feature_checker
