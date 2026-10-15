# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import secrets
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import jwt
import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.core.config import settings
from src.core.crypto import (
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    verify_password,
)
from src.core.csrf import generate_csrf_token
from src.db.session import get_db_session, set_tenant_context
from src.models.core import Tenant, TenantStatusEnum, User
from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import (
    create_session,
    kill_session,
    rotate_refresh_token,
)
from src.schemas.auth import (
    AuthSessionResponse,
    LoginStep1Request,
    LoginStep1Response,
    UserProfileResponse,
    Verify2FARequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_create_jwt_access_token__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_create_jwt_access_token__mutmut)
def create_jwt_access_token(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_orig(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_1(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = None
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_2(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(None)
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_3(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = None
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_4(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "XXsubXX": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_5(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "SUB": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_6(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "XXtidXX": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_7(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "TID": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_8(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "XXtslugXX": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_9(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "TSLUG": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_10(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "XXsidXX": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_11(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "SID": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_12(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "XXrolXX": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_13(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "ROL": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_14(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "XXall_rXX": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_15(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "ALL_R": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_16(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "XXiatXX": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_17(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "IAT": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_18(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "XXexpXX": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_19(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "EXP": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_20(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now - 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_21(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 601,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_22(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(None, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_23(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, None, algorithm="HS256")


def x_create_jwt_access_token__mutmut_24(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm=None)


def x_create_jwt_access_token__mutmut_25(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")


def x_create_jwt_access_token__mutmut_26(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, algorithm="HS256")


def x_create_jwt_access_token__mutmut_27(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, )


def x_create_jwt_access_token__mutmut_28(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="XXHS256XX")


def x_create_jwt_access_token__mutmut_29(
    user_id: str,
    tenant_id: str,
    tenant_slug: str,
    session_id: str,
    role: str,
    all_routers: bool,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": role,
        "all_r": all_routers,
        "iat": now,
        "exp": now + 600,  # 10 minutos
    }
    return jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="hs256")

mutants_x_create_jwt_access_token__mutmut['_mutmut_orig'] = x_create_jwt_access_token__mutmut_orig # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_1'] = x_create_jwt_access_token__mutmut_1 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_2'] = x_create_jwt_access_token__mutmut_2 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_3'] = x_create_jwt_access_token__mutmut_3 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_4'] = x_create_jwt_access_token__mutmut_4 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_5'] = x_create_jwt_access_token__mutmut_5 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_6'] = x_create_jwt_access_token__mutmut_6 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_7'] = x_create_jwt_access_token__mutmut_7 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_8'] = x_create_jwt_access_token__mutmut_8 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_9'] = x_create_jwt_access_token__mutmut_9 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_10'] = x_create_jwt_access_token__mutmut_10 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_11'] = x_create_jwt_access_token__mutmut_11 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_12'] = x_create_jwt_access_token__mutmut_12 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_13'] = x_create_jwt_access_token__mutmut_13 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_14'] = x_create_jwt_access_token__mutmut_14 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_15'] = x_create_jwt_access_token__mutmut_15 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_16'] = x_create_jwt_access_token__mutmut_16 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_17'] = x_create_jwt_access_token__mutmut_17 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_18'] = x_create_jwt_access_token__mutmut_18 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_19'] = x_create_jwt_access_token__mutmut_19 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_20'] = x_create_jwt_access_token__mutmut_20 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_21'] = x_create_jwt_access_token__mutmut_21 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_22'] = x_create_jwt_access_token__mutmut_22 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_23'] = x_create_jwt_access_token__mutmut_23 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_24'] = x_create_jwt_access_token__mutmut_24 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_25'] = x_create_jwt_access_token__mutmut_25 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_26'] = x_create_jwt_access_token__mutmut_26 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_27'] = x_create_jwt_access_token__mutmut_27 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_28'] = x_create_jwt_access_token__mutmut_28 # type: ignore # mutmut generated
mutants_x_create_jwt_access_token__mutmut['x_create_jwt_access_token__mutmut_29'] = x_create_jwt_access_token__mutmut_29 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_set_auth_cookies__mutmut)
def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_orig(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_1(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = True,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_2(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = None
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_3(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if (is_secure) and False else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_4(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if (is_secure) or True else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_5(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "XX__Host-rg_atXX" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_6(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_7(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__HOST-RG_AT" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_8(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "XXrg_atXX"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_9(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "RG_AT"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_10(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = None

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_11(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if (is_secure) and False else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_12(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if (is_secure) or True else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_13(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "XX__Host-rg_rtXX" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_14(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_15(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__HOST-RG_RT" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_16(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "XXrg_rtXX"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_17(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "RG_RT"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_18(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=None,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_19(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=None,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_20(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=None,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_21(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=None,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_22(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=None,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_23(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite=None,
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_24(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path=None,
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_25(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_26(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_27(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_28(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_29(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_30(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_31(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_32(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=601,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_33(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_34(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="XXstrictXX",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_35(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="STRICT",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_36(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="XX/XX",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_37(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=None,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_38(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=None,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_39(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=None,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_40(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=None,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_41(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=None,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_42(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite=None,
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_43(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path=None,
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_44(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_45(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_46(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_47(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_48(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_49(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_50(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_51(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28801,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_52(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_53(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="XXstrictXX",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_54(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="STRICT",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_55(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="XX/api/v1/auth/refreshXX",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_56(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/API/V1/AUTH/REFRESH",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_57(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key=None,
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_58(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=None,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_59(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=None,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_60(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=None,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_61(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=None,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_62(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite=None,
        path="/",
    )


def x_set_auth_cookies__mutmut_63(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path=None,
    )


def x_set_auth_cookies__mutmut_64(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_65(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_66(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_67(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_68(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_69(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        path="/",
    )


def x_set_auth_cookies__mutmut_70(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        )


def x_set_auth_cookies__mutmut_71(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="XXrg_csrfXX",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_72(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="RG_CSRF",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_73(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28801,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_74(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def x_set_auth_cookies__mutmut_75(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="XXstrictXX",
        path="/",
    )


def x_set_auth_cookies__mutmut_76(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="STRICT",
        path="/",
    )


def x_set_auth_cookies__mutmut_77(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    is_secure: bool = False,
) -> None:
    at_name = "__Host-rg_at" if is_secure else "rg_at"
    rt_name = "__Host-rg_rt" if is_secure else "rg_rt"

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        path="XX/XX",
    )

mutants_x_set_auth_cookies__mutmut['_mutmut_orig'] = x_set_auth_cookies__mutmut_orig # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_1'] = x_set_auth_cookies__mutmut_1 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_2'] = x_set_auth_cookies__mutmut_2 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_3'] = x_set_auth_cookies__mutmut_3 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_4'] = x_set_auth_cookies__mutmut_4 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_5'] = x_set_auth_cookies__mutmut_5 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_6'] = x_set_auth_cookies__mutmut_6 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_7'] = x_set_auth_cookies__mutmut_7 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_8'] = x_set_auth_cookies__mutmut_8 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_9'] = x_set_auth_cookies__mutmut_9 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_10'] = x_set_auth_cookies__mutmut_10 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_11'] = x_set_auth_cookies__mutmut_11 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_12'] = x_set_auth_cookies__mutmut_12 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_13'] = x_set_auth_cookies__mutmut_13 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_14'] = x_set_auth_cookies__mutmut_14 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_15'] = x_set_auth_cookies__mutmut_15 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_16'] = x_set_auth_cookies__mutmut_16 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_17'] = x_set_auth_cookies__mutmut_17 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_18'] = x_set_auth_cookies__mutmut_18 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_19'] = x_set_auth_cookies__mutmut_19 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_20'] = x_set_auth_cookies__mutmut_20 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_21'] = x_set_auth_cookies__mutmut_21 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_22'] = x_set_auth_cookies__mutmut_22 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_23'] = x_set_auth_cookies__mutmut_23 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_24'] = x_set_auth_cookies__mutmut_24 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_25'] = x_set_auth_cookies__mutmut_25 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_26'] = x_set_auth_cookies__mutmut_26 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_27'] = x_set_auth_cookies__mutmut_27 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_28'] = x_set_auth_cookies__mutmut_28 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_29'] = x_set_auth_cookies__mutmut_29 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_30'] = x_set_auth_cookies__mutmut_30 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_31'] = x_set_auth_cookies__mutmut_31 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_32'] = x_set_auth_cookies__mutmut_32 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_33'] = x_set_auth_cookies__mutmut_33 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_34'] = x_set_auth_cookies__mutmut_34 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_35'] = x_set_auth_cookies__mutmut_35 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_36'] = x_set_auth_cookies__mutmut_36 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_37'] = x_set_auth_cookies__mutmut_37 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_38'] = x_set_auth_cookies__mutmut_38 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_39'] = x_set_auth_cookies__mutmut_39 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_40'] = x_set_auth_cookies__mutmut_40 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_41'] = x_set_auth_cookies__mutmut_41 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_42'] = x_set_auth_cookies__mutmut_42 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_43'] = x_set_auth_cookies__mutmut_43 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_44'] = x_set_auth_cookies__mutmut_44 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_45'] = x_set_auth_cookies__mutmut_45 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_46'] = x_set_auth_cookies__mutmut_46 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_47'] = x_set_auth_cookies__mutmut_47 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_48'] = x_set_auth_cookies__mutmut_48 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_49'] = x_set_auth_cookies__mutmut_49 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_50'] = x_set_auth_cookies__mutmut_50 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_51'] = x_set_auth_cookies__mutmut_51 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_52'] = x_set_auth_cookies__mutmut_52 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_53'] = x_set_auth_cookies__mutmut_53 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_54'] = x_set_auth_cookies__mutmut_54 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_55'] = x_set_auth_cookies__mutmut_55 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_56'] = x_set_auth_cookies__mutmut_56 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_57'] = x_set_auth_cookies__mutmut_57 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_58'] = x_set_auth_cookies__mutmut_58 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_59'] = x_set_auth_cookies__mutmut_59 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_60'] = x_set_auth_cookies__mutmut_60 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_61'] = x_set_auth_cookies__mutmut_61 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_62'] = x_set_auth_cookies__mutmut_62 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_63'] = x_set_auth_cookies__mutmut_63 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_64'] = x_set_auth_cookies__mutmut_64 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_65'] = x_set_auth_cookies__mutmut_65 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_66'] = x_set_auth_cookies__mutmut_66 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_67'] = x_set_auth_cookies__mutmut_67 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_68'] = x_set_auth_cookies__mutmut_68 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_69'] = x_set_auth_cookies__mutmut_69 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_70'] = x_set_auth_cookies__mutmut_70 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_71'] = x_set_auth_cookies__mutmut_71 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_72'] = x_set_auth_cookies__mutmut_72 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_73'] = x_set_auth_cookies__mutmut_73 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_74'] = x_set_auth_cookies__mutmut_74 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_75'] = x_set_auth_cookies__mutmut_75 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_76'] = x_set_auth_cookies__mutmut_76 # type: ignore # mutmut generated
mutants_x_set_auth_cookies__mutmut['x_set_auth_cookies__mutmut_77'] = x_set_auth_cookies__mutmut_77 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_active_tenant__mutmut)
async def _get_active_tenant(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_orig(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_1(db: AsyncSession, slug: str) -> Tenant:
    stmt = None
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_2(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(None, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_3(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, None)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_4(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_5(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, )
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_6(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(None).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_7(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug != slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_8(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status != TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_9(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = None
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_10(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(None)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_11(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = None
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_12(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_13(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=None, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_14(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail=None)
    return tenant


async def x__get_active_tenant__mutmut_15(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_16(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, )
    return tenant


async def x__get_active_tenant__mutmut_17(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=402, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_18(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="XXCredenciales inválidas o empresa no encontradaXX")
    return tenant


async def x__get_active_tenant__mutmut_19(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="credenciales inválidas o empresa no encontrada")
    return tenant


async def x__get_active_tenant__mutmut_20(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="CREDENCIALES INVÁLIDAS O EMPRESA NO ENCONTRADA")
    return tenant

mutants_x__get_active_tenant__mutmut['_mutmut_orig'] = x__get_active_tenant__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_1'] = x__get_active_tenant__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_2'] = x__get_active_tenant__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_3'] = x__get_active_tenant__mutmut_3 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_4'] = x__get_active_tenant__mutmut_4 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_5'] = x__get_active_tenant__mutmut_5 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_6'] = x__get_active_tenant__mutmut_6 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_7'] = x__get_active_tenant__mutmut_7 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_8'] = x__get_active_tenant__mutmut_8 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_9'] = x__get_active_tenant__mutmut_9 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_10'] = x__get_active_tenant__mutmut_10 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_11'] = x__get_active_tenant__mutmut_11 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_12'] = x__get_active_tenant__mutmut_12 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_13'] = x__get_active_tenant__mutmut_13 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_14'] = x__get_active_tenant__mutmut_14 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_15'] = x__get_active_tenant__mutmut_15 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_16'] = x__get_active_tenant__mutmut_16 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_17'] = x__get_active_tenant__mutmut_17 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_18'] = x__get_active_tenant__mutmut_18 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_19'] = x__get_active_tenant__mutmut_19 # type: ignore # mutmut generated
mutants_x__get_active_tenant__mutmut['x__get_active_tenant__mutmut_20'] = x__get_active_tenant__mutmut_20 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__validate_user_lock__mutmut)
def _validate_user_lock(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_orig(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_1(user: User) -> None:
    now_utc = None
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_2(user: User) -> None:
    now_utc = datetime.now(None)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_3(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until or user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_4(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked or user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_5(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until >= now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_6(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=None,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_7(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail=None,
        )


def x__validate_user_lock__mutmut_8(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_9(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            )


def x__validate_user_lock__mutmut_10(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=424,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_11(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="XXCuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.XX",
        )


def x__validate_user_lock__mutmut_12(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="cuenta bloqueada temporalmente por múltiples intentos fallidos. intenta en 15 minutos.",
        )


def x__validate_user_lock__mutmut_13(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="CUENTA BLOQUEADA TEMPORALMENTE POR MÚLTIPLES INTENTOS FALLIDOS. INTENTA EN 15 MINUTOS.",
        )

mutants_x__validate_user_lock__mutmut['_mutmut_orig'] = x__validate_user_lock__mutmut_orig # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_1'] = x__validate_user_lock__mutmut_1 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_2'] = x__validate_user_lock__mutmut_2 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_3'] = x__validate_user_lock__mutmut_3 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_4'] = x__validate_user_lock__mutmut_4 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_5'] = x__validate_user_lock__mutmut_5 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_6'] = x__validate_user_lock__mutmut_6 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_7'] = x__validate_user_lock__mutmut_7 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_8'] = x__validate_user_lock__mutmut_8 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_9'] = x__validate_user_lock__mutmut_9 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_10'] = x__validate_user_lock__mutmut_10 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_11'] = x__validate_user_lock__mutmut_11 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_12'] = x__validate_user_lock__mutmut_12 # type: ignore # mutmut generated
mutants_x__validate_user_lock__mutmut['x__validate_user_lock__mutmut_13'] = x__validate_user_lock__mutmut_13 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__verify_user_credentials__mutmut)
async def _verify_user_credentials(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_orig(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_1(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(None)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_2(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_3(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(None, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_4(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, None):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_5(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_6(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, ):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_7(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts = 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_8(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts -= 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_9(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 2
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_10(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts > 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_11(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 6:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_12(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = None
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_13(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = False
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_14(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = None
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_15(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(None, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_16(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, None)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_17(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_18(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, )
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_19(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() - 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_20(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 901, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_21(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=None, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_22(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail=None)
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_23(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_24(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, )
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_25(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=402, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_26(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="XXCredenciales inválidas o empresa no encontradaXX")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_27(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_28(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="CREDENCIALES INVÁLIDAS O EMPRESA NO ENCONTRADA")
    user.failed_login_attempts = 0
    await db.commit()


async def x__verify_user_credentials__mutmut_29(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = None
    await db.commit()


async def x__verify_user_credentials__mutmut_30(db: AsyncSession, user: User, password: str) -> None:
    _validate_user_lock(user)
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    user.failed_login_attempts = 1
    await db.commit()

mutants_x__verify_user_credentials__mutmut['_mutmut_orig'] = x__verify_user_credentials__mutmut_orig # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_1'] = x__verify_user_credentials__mutmut_1 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_2'] = x__verify_user_credentials__mutmut_2 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_3'] = x__verify_user_credentials__mutmut_3 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_4'] = x__verify_user_credentials__mutmut_4 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_5'] = x__verify_user_credentials__mutmut_5 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_6'] = x__verify_user_credentials__mutmut_6 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_7'] = x__verify_user_credentials__mutmut_7 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_8'] = x__verify_user_credentials__mutmut_8 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_9'] = x__verify_user_credentials__mutmut_9 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_10'] = x__verify_user_credentials__mutmut_10 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_11'] = x__verify_user_credentials__mutmut_11 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_12'] = x__verify_user_credentials__mutmut_12 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_13'] = x__verify_user_credentials__mutmut_13 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_14'] = x__verify_user_credentials__mutmut_14 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_15'] = x__verify_user_credentials__mutmut_15 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_16'] = x__verify_user_credentials__mutmut_16 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_17'] = x__verify_user_credentials__mutmut_17 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_18'] = x__verify_user_credentials__mutmut_18 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_19'] = x__verify_user_credentials__mutmut_19 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_20'] = x__verify_user_credentials__mutmut_20 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_21'] = x__verify_user_credentials__mutmut_21 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_22'] = x__verify_user_credentials__mutmut_22 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_23'] = x__verify_user_credentials__mutmut_23 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_24'] = x__verify_user_credentials__mutmut_24 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_25'] = x__verify_user_credentials__mutmut_25 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_26'] = x__verify_user_credentials__mutmut_26 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_27'] = x__verify_user_credentials__mutmut_27 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_28'] = x__verify_user_credentials__mutmut_28 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_29'] = x__verify_user_credentials__mutmut_29 # type: ignore # mutmut generated
mutants_x__verify_user_credentials__mutmut['x__verify_user_credentials__mutmut_30'] = x__verify_user_credentials__mutmut_30 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__dispatch_preauth_challenge__mutmut)
async def _dispatch_preauth_challenge(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_orig(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_1(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = None
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_2(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(None)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_3(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(17)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_4(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = None

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_5(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_6(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = None
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_7(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = None
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_8(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "XXuser_idXX": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_9(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "USER_ID": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_10(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(None),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_11(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "XXtenant_idXX": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_12(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "TENANT_ID": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_13(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(None),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_14(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "XXtenant_slugXX": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_15(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "TENANT_SLUG": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_16(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "XXstatusXX": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_17(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "STATUS": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_18(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "XXENROLL_2FA_REQUIREDXX",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_19(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "enroll_2fa_required",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_20(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "XXtemp_totp_secretXX": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_21(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "TEMP_TOTP_SECRET": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_22(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(None, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_23(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=None)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_24(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_25(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, )
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_26(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(None, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_27(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, None)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_28(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_29(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, )
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_30(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 181)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_31(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = None
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_32(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=None, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_33(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=None)
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_34(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_35(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, )
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_36(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(None).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_37(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="XXRoSGridXX")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_38(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="rosgrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_39(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="ROSGRID")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_40(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=None,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_41(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=None,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_42(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step=None,
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_43(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=None,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_44(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=None,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_45(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_46(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_47(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_48(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_49(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_50(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="XXENROLL_2FA_REQUIREDXX",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_51(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="enroll_2fa_required",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_52(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=181,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_53(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = None
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_54(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "XXuser_idXX": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_55(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "USER_ID": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_56(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(None),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_57(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "XXtenant_idXX": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_58(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "TENANT_ID": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_59(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(None),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_60(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "XXtenant_slugXX": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_61(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "TENANT_SLUG": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_62(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "XXstatusXX": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_63(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "STATUS": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_64(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "XXVERIFY_2FA_TOTPXX",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_65(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "verify_2fa_totp",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_66(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(None, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_67(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=None)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_68(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_69(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, )
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_70(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(None, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_71(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, None)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_72(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_73(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, )
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_74(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 181)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_75(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=None,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_76(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=None,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_77(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step=None,
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_78(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=None,
    )


async def x__dispatch_preauth_challenge__mutmut_79(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_80(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_81(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_82(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_83(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        )


async def x__dispatch_preauth_challenge__mutmut_84(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="XXVERIFY_2FA_TOTPXX",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_85(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="verify_2fa_totp",
        totp_provisioning_uri=None,
        expires_in_seconds=180,
    )


async def x__dispatch_preauth_challenge__mutmut_86(redis: Any, tenant: Tenant, user: User) -> LoginStep1Response:
    challenge_id = secrets.token_hex(16)
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"

    if not user.totp_enabled:
        secret = pyotp.random_base32()
        mapping: dict[str, Any] = {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "status": "ENROLL_2FA_REQUIRED",
            "temp_totp_secret": secret,
        }
        await redis.hset(preauth_key, mapping=mapping)
        await redis.expire(preauth_key, 180)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="RoSGrid")
        return LoginStep1Response(
            challenge_id=challenge_id,
            tenant_slug=tenant.slug,
            next_step="ENROLL_2FA_REQUIRED",
            totp_provisioning_uri=uri,
            expires_in_seconds=180,
        )

    verify_mapping: dict[str, Any] = {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=verify_mapping)
    await redis.expire(preauth_key, 180)
    return LoginStep1Response(
        challenge_id=challenge_id,
        tenant_slug=tenant.slug,
        next_step="VERIFY_2FA_TOTP",
        totp_provisioning_uri=None,
        expires_in_seconds=181,
    )

mutants_x__dispatch_preauth_challenge__mutmut['_mutmut_orig'] = x__dispatch_preauth_challenge__mutmut_orig # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_1'] = x__dispatch_preauth_challenge__mutmut_1 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_2'] = x__dispatch_preauth_challenge__mutmut_2 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_3'] = x__dispatch_preauth_challenge__mutmut_3 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_4'] = x__dispatch_preauth_challenge__mutmut_4 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_5'] = x__dispatch_preauth_challenge__mutmut_5 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_6'] = x__dispatch_preauth_challenge__mutmut_6 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_7'] = x__dispatch_preauth_challenge__mutmut_7 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_8'] = x__dispatch_preauth_challenge__mutmut_8 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_9'] = x__dispatch_preauth_challenge__mutmut_9 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_10'] = x__dispatch_preauth_challenge__mutmut_10 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_11'] = x__dispatch_preauth_challenge__mutmut_11 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_12'] = x__dispatch_preauth_challenge__mutmut_12 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_13'] = x__dispatch_preauth_challenge__mutmut_13 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_14'] = x__dispatch_preauth_challenge__mutmut_14 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_15'] = x__dispatch_preauth_challenge__mutmut_15 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_16'] = x__dispatch_preauth_challenge__mutmut_16 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_17'] = x__dispatch_preauth_challenge__mutmut_17 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_18'] = x__dispatch_preauth_challenge__mutmut_18 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_19'] = x__dispatch_preauth_challenge__mutmut_19 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_20'] = x__dispatch_preauth_challenge__mutmut_20 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_21'] = x__dispatch_preauth_challenge__mutmut_21 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_22'] = x__dispatch_preauth_challenge__mutmut_22 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_23'] = x__dispatch_preauth_challenge__mutmut_23 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_24'] = x__dispatch_preauth_challenge__mutmut_24 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_25'] = x__dispatch_preauth_challenge__mutmut_25 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_26'] = x__dispatch_preauth_challenge__mutmut_26 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_27'] = x__dispatch_preauth_challenge__mutmut_27 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_28'] = x__dispatch_preauth_challenge__mutmut_28 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_29'] = x__dispatch_preauth_challenge__mutmut_29 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_30'] = x__dispatch_preauth_challenge__mutmut_30 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_31'] = x__dispatch_preauth_challenge__mutmut_31 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_32'] = x__dispatch_preauth_challenge__mutmut_32 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_33'] = x__dispatch_preauth_challenge__mutmut_33 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_34'] = x__dispatch_preauth_challenge__mutmut_34 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_35'] = x__dispatch_preauth_challenge__mutmut_35 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_36'] = x__dispatch_preauth_challenge__mutmut_36 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_37'] = x__dispatch_preauth_challenge__mutmut_37 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_38'] = x__dispatch_preauth_challenge__mutmut_38 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_39'] = x__dispatch_preauth_challenge__mutmut_39 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_40'] = x__dispatch_preauth_challenge__mutmut_40 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_41'] = x__dispatch_preauth_challenge__mutmut_41 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_42'] = x__dispatch_preauth_challenge__mutmut_42 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_43'] = x__dispatch_preauth_challenge__mutmut_43 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_44'] = x__dispatch_preauth_challenge__mutmut_44 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_45'] = x__dispatch_preauth_challenge__mutmut_45 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_46'] = x__dispatch_preauth_challenge__mutmut_46 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_47'] = x__dispatch_preauth_challenge__mutmut_47 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_48'] = x__dispatch_preauth_challenge__mutmut_48 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_49'] = x__dispatch_preauth_challenge__mutmut_49 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_50'] = x__dispatch_preauth_challenge__mutmut_50 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_51'] = x__dispatch_preauth_challenge__mutmut_51 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_52'] = x__dispatch_preauth_challenge__mutmut_52 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_53'] = x__dispatch_preauth_challenge__mutmut_53 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_54'] = x__dispatch_preauth_challenge__mutmut_54 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_55'] = x__dispatch_preauth_challenge__mutmut_55 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_56'] = x__dispatch_preauth_challenge__mutmut_56 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_57'] = x__dispatch_preauth_challenge__mutmut_57 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_58'] = x__dispatch_preauth_challenge__mutmut_58 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_59'] = x__dispatch_preauth_challenge__mutmut_59 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_60'] = x__dispatch_preauth_challenge__mutmut_60 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_61'] = x__dispatch_preauth_challenge__mutmut_61 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_62'] = x__dispatch_preauth_challenge__mutmut_62 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_63'] = x__dispatch_preauth_challenge__mutmut_63 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_64'] = x__dispatch_preauth_challenge__mutmut_64 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_65'] = x__dispatch_preauth_challenge__mutmut_65 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_66'] = x__dispatch_preauth_challenge__mutmut_66 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_67'] = x__dispatch_preauth_challenge__mutmut_67 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_68'] = x__dispatch_preauth_challenge__mutmut_68 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_69'] = x__dispatch_preauth_challenge__mutmut_69 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_70'] = x__dispatch_preauth_challenge__mutmut_70 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_71'] = x__dispatch_preauth_challenge__mutmut_71 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_72'] = x__dispatch_preauth_challenge__mutmut_72 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_73'] = x__dispatch_preauth_challenge__mutmut_73 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_74'] = x__dispatch_preauth_challenge__mutmut_74 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_75'] = x__dispatch_preauth_challenge__mutmut_75 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_76'] = x__dispatch_preauth_challenge__mutmut_76 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_77'] = x__dispatch_preauth_challenge__mutmut_77 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_78'] = x__dispatch_preauth_challenge__mutmut_78 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_79'] = x__dispatch_preauth_challenge__mutmut_79 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_80'] = x__dispatch_preauth_challenge__mutmut_80 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_81'] = x__dispatch_preauth_challenge__mutmut_81 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_82'] = x__dispatch_preauth_challenge__mutmut_82 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_83'] = x__dispatch_preauth_challenge__mutmut_83 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_84'] = x__dispatch_preauth_challenge__mutmut_84 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_85'] = x__dispatch_preauth_challenge__mutmut_85 # type: ignore # mutmut generated
mutants_x__dispatch_preauth_challenge__mutmut['x__dispatch_preauth_challenge__mutmut_86'] = x__dispatch_preauth_challenge__mutmut_86 # type: ignore # mutmut generated


@router.post("/login", response_model=LoginStep1Response)
async def login_step1(
    body: LoginStep1Request,
    db: AsyncSession = Depends(get_db_session),
) -> LoginStep1Response:
    tenant = await _get_active_tenant(db, body.tenant_slug)
    await set_tenant_context(db, tenant.id, is_superadmin=False)

    stmt_user = select(User).where(User.tenant_id == tenant.id, User.email == body.email)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")

    await _verify_user_credentials(db, user, body.password)
    redis = get_redis_client()
    return await _dispatch_preauth_challenge(redis, tenant, user)
mutants_x__fetch_preauth_state__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__fetch_preauth_state__mutmut)
async def _fetch_preauth_state(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_orig(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_1(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = None
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_2(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(None)
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_3(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_4(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=None, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_5(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail=None)
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_6(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_7(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, )
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_8(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=402, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_9(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="XXDesafío 2FA inválido o expiradoXX")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_10(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="desafío 2fa inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_11(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="DESAFÍO 2FA INVÁLIDO O EXPIRADO")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_12(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = None
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_13(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(None)
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_14(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[1])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_15(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = None
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_16(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(None)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_17(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_18(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=None, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_19(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail=None)
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_20(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_21(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, )
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_22(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=402, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_23(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="XXDesafío 2FA inválido o expiradoXX")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_24(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="desafío 2fa inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_25(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="DESAFÍO 2FA INVÁLIDO O EXPIRADO")
    return key, {str(k): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_26(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(None): str(v) for k, v in data.items()}


async def x__fetch_preauth_state__mutmut_27(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(None) for k, v in data.items()}

mutants_x__fetch_preauth_state__mutmut['_mutmut_orig'] = x__fetch_preauth_state__mutmut_orig # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_1'] = x__fetch_preauth_state__mutmut_1 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_2'] = x__fetch_preauth_state__mutmut_2 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_3'] = x__fetch_preauth_state__mutmut_3 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_4'] = x__fetch_preauth_state__mutmut_4 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_5'] = x__fetch_preauth_state__mutmut_5 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_6'] = x__fetch_preauth_state__mutmut_6 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_7'] = x__fetch_preauth_state__mutmut_7 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_8'] = x__fetch_preauth_state__mutmut_8 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_9'] = x__fetch_preauth_state__mutmut_9 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_10'] = x__fetch_preauth_state__mutmut_10 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_11'] = x__fetch_preauth_state__mutmut_11 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_12'] = x__fetch_preauth_state__mutmut_12 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_13'] = x__fetch_preauth_state__mutmut_13 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_14'] = x__fetch_preauth_state__mutmut_14 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_15'] = x__fetch_preauth_state__mutmut_15 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_16'] = x__fetch_preauth_state__mutmut_16 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_17'] = x__fetch_preauth_state__mutmut_17 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_18'] = x__fetch_preauth_state__mutmut_18 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_19'] = x__fetch_preauth_state__mutmut_19 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_20'] = x__fetch_preauth_state__mutmut_20 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_21'] = x__fetch_preauth_state__mutmut_21 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_22'] = x__fetch_preauth_state__mutmut_22 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_23'] = x__fetch_preauth_state__mutmut_23 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_24'] = x__fetch_preauth_state__mutmut_24 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_25'] = x__fetch_preauth_state__mutmut_25 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_26'] = x__fetch_preauth_state__mutmut_26 # type: ignore # mutmut generated
mutants_x__fetch_preauth_state__mutmut['x__fetch_preauth_state__mutmut_27'] = x__fetch_preauth_state__mutmut_27 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__execute_2fa_enrollment__mutmut)
async def _execute_2fa_enrollment(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_orig(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_1(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_2(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(None, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_3(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=None):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_4(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_5(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, ):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_6(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(None).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_7(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=2):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_8(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=None, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_9(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail=None)
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_10(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_11(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, )
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_12(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=402, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_13(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="XXCódigo 2FA inválidoXX")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_14(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="código 2fa inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_15(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="CÓDIGO 2FA INVÁLIDO")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_16(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = None
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_17(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(None, aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_18(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), None)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_19(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_20(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), )
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_21(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode(None), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_22(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("XXutf-8XX"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_23(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("UTF-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_24(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = None
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_25(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = None
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_26(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = None
    user.totp_enabled = True
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_27(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = None
    await db.commit()


async def x__execute_2fa_enrollment__mutmut_28(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = False
    await db.commit()

mutants_x__execute_2fa_enrollment__mutmut['_mutmut_orig'] = x__execute_2fa_enrollment__mutmut_orig # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_1'] = x__execute_2fa_enrollment__mutmut_1 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_2'] = x__execute_2fa_enrollment__mutmut_2 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_3'] = x__execute_2fa_enrollment__mutmut_3 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_4'] = x__execute_2fa_enrollment__mutmut_4 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_5'] = x__execute_2fa_enrollment__mutmut_5 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_6'] = x__execute_2fa_enrollment__mutmut_6 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_7'] = x__execute_2fa_enrollment__mutmut_7 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_8'] = x__execute_2fa_enrollment__mutmut_8 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_9'] = x__execute_2fa_enrollment__mutmut_9 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_10'] = x__execute_2fa_enrollment__mutmut_10 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_11'] = x__execute_2fa_enrollment__mutmut_11 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_12'] = x__execute_2fa_enrollment__mutmut_12 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_13'] = x__execute_2fa_enrollment__mutmut_13 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_14'] = x__execute_2fa_enrollment__mutmut_14 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_15'] = x__execute_2fa_enrollment__mutmut_15 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_16'] = x__execute_2fa_enrollment__mutmut_16 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_17'] = x__execute_2fa_enrollment__mutmut_17 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_18'] = x__execute_2fa_enrollment__mutmut_18 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_19'] = x__execute_2fa_enrollment__mutmut_19 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_20'] = x__execute_2fa_enrollment__mutmut_20 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_21'] = x__execute_2fa_enrollment__mutmut_21 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_22'] = x__execute_2fa_enrollment__mutmut_22 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_23'] = x__execute_2fa_enrollment__mutmut_23 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_24'] = x__execute_2fa_enrollment__mutmut_24 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_25'] = x__execute_2fa_enrollment__mutmut_25 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_26'] = x__execute_2fa_enrollment__mutmut_26 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_27'] = x__execute_2fa_enrollment__mutmut_27 # type: ignore # mutmut generated
mutants_x__execute_2fa_enrollment__mutmut['x__execute_2fa_enrollment__mutmut_28'] = x__execute_2fa_enrollment__mutmut_28 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__execute_2fa_verification__mutmut)
def _execute_2fa_verification(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_orig(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_1(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv and not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_2(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext and not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_3(user: User, code: str, aad: bytes) -> None:
    if user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_4(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_5(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_6(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=None, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_7(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail=None)
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_8(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_9(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, )
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_10(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=402, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_11(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="XXConfiguración 2FA corruptaXX")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_12(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="configuración 2fa corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_13(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="CONFIGURACIÓN 2FA CORRUPTA")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_14(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = None
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_15(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(None, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_16(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, None, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_17(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, None, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_18(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, None)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_19(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_20(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_21(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_22(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, )
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_23(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = None
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_24(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode(None)
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_25(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("XXutf-8XX")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_26(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("UTF-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_27(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_28(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(None, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_29(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=None):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_30(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_31(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, ):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_32(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(None).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_33(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=2):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_34(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=None, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_35(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail=None)


def x__execute_2fa_verification__mutmut_36(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_37(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, )


def x__execute_2fa_verification__mutmut_38(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=402, detail="Código 2FA incorrecto")


def x__execute_2fa_verification__mutmut_39(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="XXCódigo 2FA incorrectoXX")


def x__execute_2fa_verification__mutmut_40(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="código 2fa incorrecto")


def x__execute_2fa_verification__mutmut_41(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="CÓDIGO 2FA INCORRECTO")

mutants_x__execute_2fa_verification__mutmut['_mutmut_orig'] = x__execute_2fa_verification__mutmut_orig # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_1'] = x__execute_2fa_verification__mutmut_1 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_2'] = x__execute_2fa_verification__mutmut_2 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_3'] = x__execute_2fa_verification__mutmut_3 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_4'] = x__execute_2fa_verification__mutmut_4 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_5'] = x__execute_2fa_verification__mutmut_5 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_6'] = x__execute_2fa_verification__mutmut_6 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_7'] = x__execute_2fa_verification__mutmut_7 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_8'] = x__execute_2fa_verification__mutmut_8 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_9'] = x__execute_2fa_verification__mutmut_9 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_10'] = x__execute_2fa_verification__mutmut_10 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_11'] = x__execute_2fa_verification__mutmut_11 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_12'] = x__execute_2fa_verification__mutmut_12 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_13'] = x__execute_2fa_verification__mutmut_13 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_14'] = x__execute_2fa_verification__mutmut_14 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_15'] = x__execute_2fa_verification__mutmut_15 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_16'] = x__execute_2fa_verification__mutmut_16 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_17'] = x__execute_2fa_verification__mutmut_17 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_18'] = x__execute_2fa_verification__mutmut_18 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_19'] = x__execute_2fa_verification__mutmut_19 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_20'] = x__execute_2fa_verification__mutmut_20 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_21'] = x__execute_2fa_verification__mutmut_21 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_22'] = x__execute_2fa_verification__mutmut_22 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_23'] = x__execute_2fa_verification__mutmut_23 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_24'] = x__execute_2fa_verification__mutmut_24 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_25'] = x__execute_2fa_verification__mutmut_25 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_26'] = x__execute_2fa_verification__mutmut_26 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_27'] = x__execute_2fa_verification__mutmut_27 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_28'] = x__execute_2fa_verification__mutmut_28 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_29'] = x__execute_2fa_verification__mutmut_29 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_30'] = x__execute_2fa_verification__mutmut_30 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_31'] = x__execute_2fa_verification__mutmut_31 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_32'] = x__execute_2fa_verification__mutmut_32 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_33'] = x__execute_2fa_verification__mutmut_33 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_34'] = x__execute_2fa_verification__mutmut_34 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_35'] = x__execute_2fa_verification__mutmut_35 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_36'] = x__execute_2fa_verification__mutmut_36 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_37'] = x__execute_2fa_verification__mutmut_37 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_38'] = x__execute_2fa_verification__mutmut_38 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_39'] = x__execute_2fa_verification__mutmut_39 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_40'] = x__execute_2fa_verification__mutmut_40 # type: ignore # mutmut generated
mutants_x__execute_2fa_verification__mutmut['x__execute_2fa_verification__mutmut_41'] = x__execute_2fa_verification__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_auth_session_response__mutmut)
async def _build_auth_session_response(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_orig(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_1(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = None
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_2(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if (request.client) and False else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_3(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if (request.client) or True else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_4(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "XX127.0.0.1XX"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_5(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = None

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_6(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get(None, "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_7(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", None)

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_8(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_9(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", )

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_10(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("XXUser-AgentXX", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_11(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_12(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("USER-AGENT", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_13(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "XXUnknownXX")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_14(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_15(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "UNKNOWN")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_16(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = None
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_17(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        None,
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_18(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        None,
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_19(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        None,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_20(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        None,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_21(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        None,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_22(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        None,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_23(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        None,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_24(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_25(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_26(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_27(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_28(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_29(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_30(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_31(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(None),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_32(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(None),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_33(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = None
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_34(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        None,
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_35(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        None,
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_36(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        None,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_37(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        None,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_38(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        None,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_39(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        None,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_40(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_41(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_42(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_43(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_44(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_45(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_46(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(None),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_47(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(None),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_48(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = None
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_49(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(None, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_50(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, None)
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_51(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_52(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, )
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_53(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(None))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_54(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(None, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_55(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, None, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_56(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, None, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_57(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, None, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_58(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=None)

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_59(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_60(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_61(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_62(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_63(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, )

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_64(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme != "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_65(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "XXhttpsXX"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_66(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "HTTPS"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_67(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=None,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_68(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=None,
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_69(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=None,
    )


async def x__build_auth_session_response__mutmut_70(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_71(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_72(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        )


async def x__build_auth_session_response__mutmut_73(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=None,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_74(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=None,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_75(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=None,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_76(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=None,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_77(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=None,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_78(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=None,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_79(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=None,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_80(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=None,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_81(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=None,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_82(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_83(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_84(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_85(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_86(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_87(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_88(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_89(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            has_all_routers_access=user.has_all_routers_access,
        ),
        csrf_token=csrf_token,
    )


async def x__build_auth_session_response__mutmut_90(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    session_id, _family_id, initial_rt = await create_session(
        str(tenant_id),
        str(user.id),
        user.username,
        user.full_name,
        user.role.value,
        ip_addr,
        ua,
    )
    access_token = create_jwt_access_token(
        str(user.id),
        str(tenant_id),
        tenant_slug,
        session_id,
        user.role.value,
        user.has_all_routers_access,
    )
    csrf_token = generate_csrf_token(session_id, str(tenant_id))
    set_auth_cookies(response, access_token, initial_rt, csrf_token, is_secure=(request.url.scheme == "https"))

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            ),
        csrf_token=csrf_token,
    )

mutants_x__build_auth_session_response__mutmut['_mutmut_orig'] = x__build_auth_session_response__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_1'] = x__build_auth_session_response__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_2'] = x__build_auth_session_response__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_3'] = x__build_auth_session_response__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_4'] = x__build_auth_session_response__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_5'] = x__build_auth_session_response__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_6'] = x__build_auth_session_response__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_7'] = x__build_auth_session_response__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_8'] = x__build_auth_session_response__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_9'] = x__build_auth_session_response__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_10'] = x__build_auth_session_response__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_11'] = x__build_auth_session_response__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_12'] = x__build_auth_session_response__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_13'] = x__build_auth_session_response__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_14'] = x__build_auth_session_response__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_15'] = x__build_auth_session_response__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_16'] = x__build_auth_session_response__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_17'] = x__build_auth_session_response__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_18'] = x__build_auth_session_response__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_19'] = x__build_auth_session_response__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_20'] = x__build_auth_session_response__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_21'] = x__build_auth_session_response__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_22'] = x__build_auth_session_response__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_23'] = x__build_auth_session_response__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_24'] = x__build_auth_session_response__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_25'] = x__build_auth_session_response__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_26'] = x__build_auth_session_response__mutmut_26 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_27'] = x__build_auth_session_response__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_28'] = x__build_auth_session_response__mutmut_28 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_29'] = x__build_auth_session_response__mutmut_29 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_30'] = x__build_auth_session_response__mutmut_30 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_31'] = x__build_auth_session_response__mutmut_31 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_32'] = x__build_auth_session_response__mutmut_32 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_33'] = x__build_auth_session_response__mutmut_33 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_34'] = x__build_auth_session_response__mutmut_34 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_35'] = x__build_auth_session_response__mutmut_35 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_36'] = x__build_auth_session_response__mutmut_36 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_37'] = x__build_auth_session_response__mutmut_37 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_38'] = x__build_auth_session_response__mutmut_38 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_39'] = x__build_auth_session_response__mutmut_39 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_40'] = x__build_auth_session_response__mutmut_40 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_41'] = x__build_auth_session_response__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_42'] = x__build_auth_session_response__mutmut_42 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_43'] = x__build_auth_session_response__mutmut_43 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_44'] = x__build_auth_session_response__mutmut_44 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_45'] = x__build_auth_session_response__mutmut_45 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_46'] = x__build_auth_session_response__mutmut_46 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_47'] = x__build_auth_session_response__mutmut_47 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_48'] = x__build_auth_session_response__mutmut_48 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_49'] = x__build_auth_session_response__mutmut_49 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_50'] = x__build_auth_session_response__mutmut_50 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_51'] = x__build_auth_session_response__mutmut_51 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_52'] = x__build_auth_session_response__mutmut_52 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_53'] = x__build_auth_session_response__mutmut_53 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_54'] = x__build_auth_session_response__mutmut_54 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_55'] = x__build_auth_session_response__mutmut_55 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_56'] = x__build_auth_session_response__mutmut_56 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_57'] = x__build_auth_session_response__mutmut_57 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_58'] = x__build_auth_session_response__mutmut_58 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_59'] = x__build_auth_session_response__mutmut_59 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_60'] = x__build_auth_session_response__mutmut_60 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_61'] = x__build_auth_session_response__mutmut_61 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_62'] = x__build_auth_session_response__mutmut_62 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_63'] = x__build_auth_session_response__mutmut_63 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_64'] = x__build_auth_session_response__mutmut_64 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_65'] = x__build_auth_session_response__mutmut_65 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_66'] = x__build_auth_session_response__mutmut_66 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_67'] = x__build_auth_session_response__mutmut_67 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_68'] = x__build_auth_session_response__mutmut_68 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_69'] = x__build_auth_session_response__mutmut_69 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_70'] = x__build_auth_session_response__mutmut_70 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_71'] = x__build_auth_session_response__mutmut_71 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_72'] = x__build_auth_session_response__mutmut_72 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_73'] = x__build_auth_session_response__mutmut_73 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_74'] = x__build_auth_session_response__mutmut_74 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_75'] = x__build_auth_session_response__mutmut_75 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_76'] = x__build_auth_session_response__mutmut_76 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_77'] = x__build_auth_session_response__mutmut_77 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_78'] = x__build_auth_session_response__mutmut_78 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_79'] = x__build_auth_session_response__mutmut_79 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_80'] = x__build_auth_session_response__mutmut_80 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_81'] = x__build_auth_session_response__mutmut_81 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_82'] = x__build_auth_session_response__mutmut_82 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_83'] = x__build_auth_session_response__mutmut_83 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_84'] = x__build_auth_session_response__mutmut_84 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_85'] = x__build_auth_session_response__mutmut_85 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_86'] = x__build_auth_session_response__mutmut_86 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_87'] = x__build_auth_session_response__mutmut_87 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_88'] = x__build_auth_session_response__mutmut_88 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_89'] = x__build_auth_session_response__mutmut_89 # type: ignore # mutmut generated
mutants_x__build_auth_session_response__mutmut['x__build_auth_session_response__mutmut_90'] = x__build_auth_session_response__mutmut_90 # type: ignore # mutmut generated


@router.post("/2fa/verify", response_model=AuthSessionResponse)
async def verify_2fa(
    body: Verify2FARequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    redis = get_redis_client()
    preauth_key, preauth_data = await _fetch_preauth_state(redis, body.challenge_id)

    user_id = uuid.UUID(str(preauth_data["user_id"]))
    tenant_id = uuid.UUID(str(preauth_data["tenant_id"]))

    await set_tenant_context(db, tenant_id)
    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    aad = f"{tenant_id}:{user.id}".encode()
    if preauth_data.get("status") == "ENROLL_2FA_REQUIRED":
        secret = str(preauth_data.get("temp_totp_secret", ""))
        await _execute_2fa_enrollment(db, user, body.totp_code, secret, aad)
    else:
        _execute_2fa_verification(user, body.totp_code, aad)

    await redis.delete(preauth_key)

    stmt_t = select(Tenant).where(Tenant.id == tenant_id)
    t_res = await db.execute(stmt_t)
    tenant_obj = t_res.scalar_one()

    return await _build_auth_session_response(request, response, tenant_id, tenant_obj.slug, tenant_obj.name, user)
mutants_x__extract_refresh_cookies__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__extract_refresh_cookies__mutmut)
def _extract_refresh_cookies(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_orig(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_1(request: Request) -> tuple[str, str]:
    rt = None
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_2(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") and request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_3(request: Request) -> tuple[str, str]:
    rt = request.cookies.get(None) or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_4(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("XX__Host-rg_rtXX") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_5(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_6(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__HOST-RG_RT") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_7(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get(None)
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_8(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("XXrg_rtXX")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_9(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("RG_RT")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_10(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_11(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=None, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_12(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail=None)
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_13(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_14(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, )
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_15(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=402, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_16(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="XXCookie de Refresh Token ausenteXX")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_17(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="cookie de refresh token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_18(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="COOKIE DE REFRESH TOKEN AUSENTE")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_19(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = None
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_20(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") and request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_21(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get(None) or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_22(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("XX__Host-rg_atXX") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_23(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_24(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__HOST-RG_AT") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_25(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get(None)
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_26(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("XXrg_atXX")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_27(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("RG_AT")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_28(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_29(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=None, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_30(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail=None)
    return rt, token


def x__extract_refresh_cookies__mutmut_31(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_32(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, )
    return rt, token


def x__extract_refresh_cookies__mutmut_33(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=402, detail="Sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_34(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="XXSesión no encontradaXX")
    return rt, token


def x__extract_refresh_cookies__mutmut_35(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="sesión no encontrada")
    return rt, token


def x__extract_refresh_cookies__mutmut_36(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="SESIÓN NO ENCONTRADA")
    return rt, token

mutants_x__extract_refresh_cookies__mutmut['_mutmut_orig'] = x__extract_refresh_cookies__mutmut_orig # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_1'] = x__extract_refresh_cookies__mutmut_1 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_2'] = x__extract_refresh_cookies__mutmut_2 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_3'] = x__extract_refresh_cookies__mutmut_3 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_4'] = x__extract_refresh_cookies__mutmut_4 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_5'] = x__extract_refresh_cookies__mutmut_5 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_6'] = x__extract_refresh_cookies__mutmut_6 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_7'] = x__extract_refresh_cookies__mutmut_7 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_8'] = x__extract_refresh_cookies__mutmut_8 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_9'] = x__extract_refresh_cookies__mutmut_9 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_10'] = x__extract_refresh_cookies__mutmut_10 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_11'] = x__extract_refresh_cookies__mutmut_11 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_12'] = x__extract_refresh_cookies__mutmut_12 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_13'] = x__extract_refresh_cookies__mutmut_13 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_14'] = x__extract_refresh_cookies__mutmut_14 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_15'] = x__extract_refresh_cookies__mutmut_15 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_16'] = x__extract_refresh_cookies__mutmut_16 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_17'] = x__extract_refresh_cookies__mutmut_17 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_18'] = x__extract_refresh_cookies__mutmut_18 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_19'] = x__extract_refresh_cookies__mutmut_19 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_20'] = x__extract_refresh_cookies__mutmut_20 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_21'] = x__extract_refresh_cookies__mutmut_21 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_22'] = x__extract_refresh_cookies__mutmut_22 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_23'] = x__extract_refresh_cookies__mutmut_23 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_24'] = x__extract_refresh_cookies__mutmut_24 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_25'] = x__extract_refresh_cookies__mutmut_25 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_26'] = x__extract_refresh_cookies__mutmut_26 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_27'] = x__extract_refresh_cookies__mutmut_27 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_28'] = x__extract_refresh_cookies__mutmut_28 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_29'] = x__extract_refresh_cookies__mutmut_29 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_30'] = x__extract_refresh_cookies__mutmut_30 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_31'] = x__extract_refresh_cookies__mutmut_31 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_32'] = x__extract_refresh_cookies__mutmut_32 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_33'] = x__extract_refresh_cookies__mutmut_33 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_34'] = x__extract_refresh_cookies__mutmut_34 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_35'] = x__extract_refresh_cookies__mutmut_35 # type: ignore # mutmut generated
mutants_x__extract_refresh_cookies__mutmut['x__extract_refresh_cookies__mutmut_36'] = x__extract_refresh_cookies__mutmut_36 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__decode_refresh_claims__mutmut)
def _decode_refresh_claims(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_orig(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_1(token: str) -> dict[str, Any]:
    try:
        return dict(
            None
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_2(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(None, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_3(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, None, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_4(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=None, options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_5(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options=None)
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_6(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_7(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_8(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_9(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], )
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_10(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["XXHS256XX"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_11(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["hs256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_12(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"XXverify_expXX": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_13(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"VERIFY_EXP": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_14(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_15(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=None, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_16(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=None) from exc


def x__decode_refresh_claims__mutmut_17(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_18(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, ) from exc


def x__decode_refresh_claims__mutmut_19(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=402, detail="Token inválido") from exc


def x__decode_refresh_claims__mutmut_20(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="XXToken inválidoXX") from exc


def x__decode_refresh_claims__mutmut_21(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="token inválido") from exc


def x__decode_refresh_claims__mutmut_22(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="TOKEN INVÁLIDO") from exc

mutants_x__decode_refresh_claims__mutmut['_mutmut_orig'] = x__decode_refresh_claims__mutmut_orig # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_1'] = x__decode_refresh_claims__mutmut_1 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_2'] = x__decode_refresh_claims__mutmut_2 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_3'] = x__decode_refresh_claims__mutmut_3 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_4'] = x__decode_refresh_claims__mutmut_4 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_5'] = x__decode_refresh_claims__mutmut_5 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_6'] = x__decode_refresh_claims__mutmut_6 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_7'] = x__decode_refresh_claims__mutmut_7 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_8'] = x__decode_refresh_claims__mutmut_8 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_9'] = x__decode_refresh_claims__mutmut_9 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_10'] = x__decode_refresh_claims__mutmut_10 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_11'] = x__decode_refresh_claims__mutmut_11 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_12'] = x__decode_refresh_claims__mutmut_12 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_13'] = x__decode_refresh_claims__mutmut_13 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_14'] = x__decode_refresh_claims__mutmut_14 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_15'] = x__decode_refresh_claims__mutmut_15 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_16'] = x__decode_refresh_claims__mutmut_16 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_17'] = x__decode_refresh_claims__mutmut_17 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_18'] = x__decode_refresh_claims__mutmut_18 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_19'] = x__decode_refresh_claims__mutmut_19 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_20'] = x__decode_refresh_claims__mutmut_20 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_21'] = x__decode_refresh_claims__mutmut_21 # type: ignore # mutmut generated
mutants_x__decode_refresh_claims__mutmut['x__decode_refresh_claims__mutmut_22'] = x__decode_refresh_claims__mutmut_22 # type: ignore # mutmut generated


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    rt, token = _extract_refresh_cookies(request)
    claims = _decode_refresh_claims(token)

    tenant_id = claims["tid"]
    session_id = claims["sid"]
    user_id = claims["sub"]
    role = claims["rol"]
    tslug = claims["tslug"]
    all_r = claims.get("all_r", False)

    redis = get_redis_client()
    sess_data = await redis.hgetall(f"rg:{tenant_id}:sess:{session_id}")
    if not sess_data:
        raise HTTPException(status_code=401, detail="Sesión revocada o finalizada")

    family_id = str(sess_data.get("refresh_family_id", ""))
    ok, error_code, new_rt = await rotate_refresh_token(tenant_id, family_id, rt)
    if not ok or not new_rt:
        raise HTTPException(status_code=401, detail=f"Fallo de rotación de sesión: {error_code}")

    new_at = create_jwt_access_token(user_id, tenant_id, tslug, session_id, role, all_r)
    new_csrf = generate_csrf_token(session_id, tenant_id)
    set_auth_cookies(response, new_at, new_rt, new_csrf, is_secure=(request.url.scheme == "https"))
    return {"status": "refreshed", "csrf_token": new_csrf}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = claims["tid"]
    session_id = claims["sid"]
    await kill_session(tenant_id, session_id, killed_by="USER_LOGOUT", reason="Cierre voluntario")

    response.delete_cookie("__Host-rg_at", path="/")
    response.delete_cookie("rg_at", path="/")
    response.delete_cookie("__Host-rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_csrf", path="/")


@router.get("/me")
async def get_me(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
    return claims
