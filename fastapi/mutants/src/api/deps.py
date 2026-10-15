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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_extract_token_from_request__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_extract_token_from_request__mutmut)
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


def x_extract_token_from_request__mutmut_orig(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_1(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = None
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_2(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") and request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_3(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get(None) or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_4(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("XX__Host-rg_atXX") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_5(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_6(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__HOST-RG_AT") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_7(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get(None)
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_8(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("XXrg_atXX")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_9(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("RG_AT")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_10(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = None
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_11(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get(None)
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_12(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("XXAuthorizationXX")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_13(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_14(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("AUTHORIZATION")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_15(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header or auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_16(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith(None):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_17(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("XXBearer XX"):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_18(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("bearer "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_19(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("BEARER "):
        return auth_header[7:].strip()

    return None


def x_extract_token_from_request__mutmut_20(request: Request) -> str | None:
    # 1. Cookie __Host-rg_at o rg_at
    cookie_token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if cookie_token:
        return cookie_token

    # 2. Authorization Bearer
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[8:].strip()

    return None

mutants_x_extract_token_from_request__mutmut['_mutmut_orig'] = x_extract_token_from_request__mutmut_orig # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_1'] = x_extract_token_from_request__mutmut_1 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_2'] = x_extract_token_from_request__mutmut_2 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_3'] = x_extract_token_from_request__mutmut_3 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_4'] = x_extract_token_from_request__mutmut_4 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_5'] = x_extract_token_from_request__mutmut_5 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_6'] = x_extract_token_from_request__mutmut_6 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_7'] = x_extract_token_from_request__mutmut_7 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_8'] = x_extract_token_from_request__mutmut_8 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_9'] = x_extract_token_from_request__mutmut_9 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_10'] = x_extract_token_from_request__mutmut_10 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_11'] = x_extract_token_from_request__mutmut_11 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_12'] = x_extract_token_from_request__mutmut_12 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_13'] = x_extract_token_from_request__mutmut_13 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_14'] = x_extract_token_from_request__mutmut_14 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_15'] = x_extract_token_from_request__mutmut_15 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_16'] = x_extract_token_from_request__mutmut_16 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_17'] = x_extract_token_from_request__mutmut_17 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_18'] = x_extract_token_from_request__mutmut_18 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_19'] = x_extract_token_from_request__mutmut_19 # type: ignore # mutmut generated
mutants_x_extract_token_from_request__mutmut['x_extract_token_from_request__mutmut_20'] = x_extract_token_from_request__mutmut_20 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_current_user_claims__mutmut)
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


async def x_get_current_user_claims__mutmut_orig(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_1(request: Request) -> dict[str, Any]:
    token = None
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


async def x_get_current_user_claims__mutmut_2(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(None)
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


async def x_get_current_user_claims__mutmut_3(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if token:
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


async def x_get_current_user_claims__mutmut_4(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=None,
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


async def x_get_current_user_claims__mutmut_5(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=None,
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


async def x_get_current_user_claims__mutmut_6(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
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


async def x_get_current_user_claims__mutmut_7(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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


async def x_get_current_user_claims__mutmut_8(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="XXNo autenticado (falta token o cookie de sesión)XX",
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


async def x_get_current_user_claims__mutmut_9(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="no autenticado (falta token o cookie de sesión)",
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


async def x_get_current_user_claims__mutmut_10(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NO AUTENTICADO (FALTA TOKEN O COOKIE DE SESIÓN)",
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


async def x_get_current_user_claims__mutmut_11(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = None
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


async def x_get_current_user_claims__mutmut_12(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
            None,
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


async def x_get_current_user_claims__mutmut_13(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            None,
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


async def x_get_current_user_claims__mutmut_14(request: Request) -> dict[str, Any]:
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
            algorithms=None,
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


async def x_get_current_user_claims__mutmut_15(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
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


async def x_get_current_user_claims__mutmut_16(request: Request) -> dict[str, Any]:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado (falta token o cookie de sesión)",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
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


async def x_get_current_user_claims__mutmut_17(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_18(request: Request) -> dict[str, Any]:
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
            algorithms=["XXHS256XX"],
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


async def x_get_current_user_claims__mutmut_19(request: Request) -> dict[str, Any]:
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
            algorithms=["hs256"],
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


async def x_get_current_user_claims__mutmut_20(request: Request) -> dict[str, Any]:
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
            status_code=None,
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


async def x_get_current_user_claims__mutmut_21(request: Request) -> dict[str, Any]:
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
            detail=None,
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


async def x_get_current_user_claims__mutmut_22(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_23(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_24(request: Request) -> dict[str, Any]:
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

    session_id = None
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


async def x_get_current_user_claims__mutmut_25(request: Request) -> dict[str, Any]:
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

    session_id = payload.get(None)
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


async def x_get_current_user_claims__mutmut_26(request: Request) -> dict[str, Any]:
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

    session_id = payload.get("XXsidXX")
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


async def x_get_current_user_claims__mutmut_27(request: Request) -> dict[str, Any]:
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

    session_id = payload.get("SID")
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


async def x_get_current_user_claims__mutmut_28(request: Request) -> dict[str, Any]:
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
    tenant_id = None
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


async def x_get_current_user_claims__mutmut_29(request: Request) -> dict[str, Any]:
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
    tenant_id = payload.get(None)
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


async def x_get_current_user_claims__mutmut_30(request: Request) -> dict[str, Any]:
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
    tenant_id = payload.get("XXtidXX")
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


async def x_get_current_user_claims__mutmut_31(request: Request) -> dict[str, Any]:
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
    tenant_id = payload.get("TID")
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


async def x_get_current_user_claims__mutmut_32(request: Request) -> dict[str, Any]:
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
    user_id = None
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


async def x_get_current_user_claims__mutmut_33(request: Request) -> dict[str, Any]:
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
    user_id = payload.get(None)
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


async def x_get_current_user_claims__mutmut_34(request: Request) -> dict[str, Any]:
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
    user_id = payload.get("XXsubXX")
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


async def x_get_current_user_claims__mutmut_35(request: Request) -> dict[str, Any]:
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
    user_id = payload.get("SUB")
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


async def x_get_current_user_claims__mutmut_36(request: Request) -> dict[str, Any]:
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
    role = None

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


async def x_get_current_user_claims__mutmut_37(request: Request) -> dict[str, Any]:
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
    role = payload.get(None)

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


async def x_get_current_user_claims__mutmut_38(request: Request) -> dict[str, Any]:
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
    role = payload.get("XXrolXX")

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


async def x_get_current_user_claims__mutmut_39(request: Request) -> dict[str, Any]:
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
    role = payload.get("ROL")

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


async def x_get_current_user_claims__mutmut_40(request: Request) -> dict[str, Any]:
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

    if not session_id or not tenant_id and not user_id:
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


async def x_get_current_user_claims__mutmut_41(request: Request) -> dict[str, Any]:
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

    if not session_id and not tenant_id or not user_id:
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


async def x_get_current_user_claims__mutmut_42(request: Request) -> dict[str, Any]:
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

    if session_id or not tenant_id or not user_id:
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


async def x_get_current_user_claims__mutmut_43(request: Request) -> dict[str, Any]:
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

    if not session_id or tenant_id or not user_id:
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


async def x_get_current_user_claims__mutmut_44(request: Request) -> dict[str, Any]:
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

    if not session_id or not tenant_id or user_id:
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


async def x_get_current_user_claims__mutmut_45(request: Request) -> dict[str, Any]:
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
            status_code=None,
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


async def x_get_current_user_claims__mutmut_46(request: Request) -> dict[str, Any]:
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
            detail=None,
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


async def x_get_current_user_claims__mutmut_47(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_48(request: Request) -> dict[str, Any]:
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


async def x_get_current_user_claims__mutmut_49(request: Request) -> dict[str, Any]:
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
            detail="XXToken malformado (claims requeridos faltantes)XX",
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


async def x_get_current_user_claims__mutmut_50(request: Request) -> dict[str, Any]:
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
            detail="token malformado (claims requeridos faltantes)",
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


async def x_get_current_user_claims__mutmut_51(request: Request) -> dict[str, Any]:
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
            detail="TOKEN MALFORMADO (CLAIMS REQUERIDOS FALTANTES)",
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


async def x_get_current_user_claims__mutmut_52(request: Request) -> dict[str, Any]:
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
    redis = None
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


async def x_get_current_user_claims__mutmut_53(request: Request) -> dict[str, Any]:
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
    sess_key = None
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


async def x_get_current_user_claims__mutmut_54(request: Request) -> dict[str, Any]:
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
    session_alive = None
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


async def x_get_current_user_claims__mutmut_55(request: Request) -> dict[str, Any]:
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
    session_alive = await redis.exists(None)
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


async def x_get_current_user_claims__mutmut_56(request: Request) -> dict[str, Any]:
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
    if session_alive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o revocada por Kill-Switch",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_57(request: Request) -> dict[str, Any]:
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
            status_code=None,
            detail="Sesión expirada o revocada por Kill-Switch",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_58(request: Request) -> dict[str, Any]:
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
            detail=None,
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_59(request: Request) -> dict[str, Any]:
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
            detail="Sesión expirada o revocada por Kill-Switch",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_60(request: Request) -> dict[str, Any]:
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
            )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_61(request: Request) -> dict[str, Any]:
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
            detail="XXSesión expirada o revocada por Kill-SwitchXX",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_62(request: Request) -> dict[str, Any]:
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
            detail="sesión expirada o revocada por kill-switch",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_63(request: Request) -> dict[str, Any]:
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
            detail="SESIÓN EXPIRADA O REVOCADA POR KILL-SWITCH",
        )

    request.state.tenant_id = uuid.UUID(str(tenant_id))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_64(request: Request) -> dict[str, Any]:
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

    request.state.tenant_id = None
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_65(request: Request) -> dict[str, Any]:
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

    request.state.tenant_id = uuid.UUID(None)
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_66(request: Request) -> dict[str, Any]:
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

    request.state.tenant_id = uuid.UUID(str(None))
    request.state.session_id = str(session_id)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_67(request: Request) -> dict[str, Any]:
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
    request.state.session_id = None
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_68(request: Request) -> dict[str, Any]:
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
    request.state.session_id = str(None)
    request.state.user_id = uuid.UUID(str(user_id))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_69(request: Request) -> dict[str, Any]:
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
    request.state.user_id = None
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_70(request: Request) -> dict[str, Any]:
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
    request.state.user_id = uuid.UUID(None)
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_71(request: Request) -> dict[str, Any]:
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
    request.state.user_id = uuid.UUID(str(None))
    request.state.is_superadmin_global = role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload


async def x_get_current_user_claims__mutmut_72(request: Request) -> dict[str, Any]:
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
    request.state.is_superadmin_global = None

    return payload


async def x_get_current_user_claims__mutmut_73(request: Request) -> dict[str, Any]:
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
    request.state.is_superadmin_global = role != SystemRoleEnum.SUPERADMIN_GLOBAL.value

    return payload

mutants_x_get_current_user_claims__mutmut['_mutmut_orig'] = x_get_current_user_claims__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_1'] = x_get_current_user_claims__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_2'] = x_get_current_user_claims__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_3'] = x_get_current_user_claims__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_4'] = x_get_current_user_claims__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_5'] = x_get_current_user_claims__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_6'] = x_get_current_user_claims__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_7'] = x_get_current_user_claims__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_8'] = x_get_current_user_claims__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_9'] = x_get_current_user_claims__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_10'] = x_get_current_user_claims__mutmut_10 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_11'] = x_get_current_user_claims__mutmut_11 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_12'] = x_get_current_user_claims__mutmut_12 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_13'] = x_get_current_user_claims__mutmut_13 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_14'] = x_get_current_user_claims__mutmut_14 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_15'] = x_get_current_user_claims__mutmut_15 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_16'] = x_get_current_user_claims__mutmut_16 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_17'] = x_get_current_user_claims__mutmut_17 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_18'] = x_get_current_user_claims__mutmut_18 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_19'] = x_get_current_user_claims__mutmut_19 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_20'] = x_get_current_user_claims__mutmut_20 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_21'] = x_get_current_user_claims__mutmut_21 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_22'] = x_get_current_user_claims__mutmut_22 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_23'] = x_get_current_user_claims__mutmut_23 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_24'] = x_get_current_user_claims__mutmut_24 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_25'] = x_get_current_user_claims__mutmut_25 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_26'] = x_get_current_user_claims__mutmut_26 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_27'] = x_get_current_user_claims__mutmut_27 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_28'] = x_get_current_user_claims__mutmut_28 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_29'] = x_get_current_user_claims__mutmut_29 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_30'] = x_get_current_user_claims__mutmut_30 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_31'] = x_get_current_user_claims__mutmut_31 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_32'] = x_get_current_user_claims__mutmut_32 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_33'] = x_get_current_user_claims__mutmut_33 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_34'] = x_get_current_user_claims__mutmut_34 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_35'] = x_get_current_user_claims__mutmut_35 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_36'] = x_get_current_user_claims__mutmut_36 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_37'] = x_get_current_user_claims__mutmut_37 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_38'] = x_get_current_user_claims__mutmut_38 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_39'] = x_get_current_user_claims__mutmut_39 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_40'] = x_get_current_user_claims__mutmut_40 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_41'] = x_get_current_user_claims__mutmut_41 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_42'] = x_get_current_user_claims__mutmut_42 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_43'] = x_get_current_user_claims__mutmut_43 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_44'] = x_get_current_user_claims__mutmut_44 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_45'] = x_get_current_user_claims__mutmut_45 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_46'] = x_get_current_user_claims__mutmut_46 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_47'] = x_get_current_user_claims__mutmut_47 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_48'] = x_get_current_user_claims__mutmut_48 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_49'] = x_get_current_user_claims__mutmut_49 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_50'] = x_get_current_user_claims__mutmut_50 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_51'] = x_get_current_user_claims__mutmut_51 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_52'] = x_get_current_user_claims__mutmut_52 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_53'] = x_get_current_user_claims__mutmut_53 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_54'] = x_get_current_user_claims__mutmut_54 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_55'] = x_get_current_user_claims__mutmut_55 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_56'] = x_get_current_user_claims__mutmut_56 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_57'] = x_get_current_user_claims__mutmut_57 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_58'] = x_get_current_user_claims__mutmut_58 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_59'] = x_get_current_user_claims__mutmut_59 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_60'] = x_get_current_user_claims__mutmut_60 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_61'] = x_get_current_user_claims__mutmut_61 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_62'] = x_get_current_user_claims__mutmut_62 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_63'] = x_get_current_user_claims__mutmut_63 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_64'] = x_get_current_user_claims__mutmut_64 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_65'] = x_get_current_user_claims__mutmut_65 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_66'] = x_get_current_user_claims__mutmut_66 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_67'] = x_get_current_user_claims__mutmut_67 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_68'] = x_get_current_user_claims__mutmut_68 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_69'] = x_get_current_user_claims__mutmut_69 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_70'] = x_get_current_user_claims__mutmut_70 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_71'] = x_get_current_user_claims__mutmut_71 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_72'] = x_get_current_user_claims__mutmut_72 # type: ignore # mutmut generated
mutants_x_get_current_user_claims__mutmut['x_get_current_user_claims__mutmut_73'] = x_get_current_user_claims__mutmut_73 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_require_roles__mutmut)
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


def x_require_roles__mutmut_orig(
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


def x_require_roles__mutmut_1(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = None

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_2(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = None
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_3(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get(None)
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_4(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("XXrolXX")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_5(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("ROL")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_6(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values or user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_7(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_8(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_9(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=None,
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_10(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=None,
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_11(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                detail="No tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_12(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                )
        return claims

    return _role_checker


def x_require_roles__mutmut_13(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="XXNo tienes los privilegios requeridos para ejecutar esta acciónXX",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_14(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no tienes los privilegios requeridos para ejecutar esta acción",
            )
        return claims

    return _role_checker


def x_require_roles__mutmut_15(
    *allowed_roles: SystemRoleEnum,
) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
    role_values = {r.value for r in allowed_roles}

    async def _role_checker(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
        user_role = claims.get("rol")
        if user_role not in role_values and user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="NO TIENES LOS PRIVILEGIOS REQUERIDOS PARA EJECUTAR ESTA ACCIÓN",
            )
        return claims

    return _role_checker

mutants_x_require_roles__mutmut['_mutmut_orig'] = x_require_roles__mutmut_orig # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_1'] = x_require_roles__mutmut_1 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_2'] = x_require_roles__mutmut_2 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_3'] = x_require_roles__mutmut_3 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_4'] = x_require_roles__mutmut_4 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_5'] = x_require_roles__mutmut_5 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_6'] = x_require_roles__mutmut_6 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_7'] = x_require_roles__mutmut_7 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_8'] = x_require_roles__mutmut_8 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_9'] = x_require_roles__mutmut_9 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_10'] = x_require_roles__mutmut_10 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_11'] = x_require_roles__mutmut_11 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_12'] = x_require_roles__mutmut_12 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_13'] = x_require_roles__mutmut_13 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_14'] = x_require_roles__mutmut_14 # type: ignore # mutmut generated
mutants_x_require_roles__mutmut['x_require_roles__mutmut_15'] = x_require_roles__mutmut_15 # type: ignore # mutmut generated
