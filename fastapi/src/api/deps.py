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
