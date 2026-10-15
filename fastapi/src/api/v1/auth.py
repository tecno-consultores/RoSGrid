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


async def _get_active_tenant(db: AsyncSession, slug: str) -> Tenant:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


def _validate_user_lock(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


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


async def _fetch_preauth_state(redis: Any, challenge_id: str) -> tuple[str, dict[str, str]]:
    keys = await redis.keys(f"rg:*:preauth:{challenge_id}")
    if not keys:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    key = str(keys[0])
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=401, detail="Desafío 2FA inválido o expirado")
    return key, {str(k): str(v) for k, v in data.items()}


async def _execute_2fa_enrollment(db: AsyncSession, user: User, code: str, secret: str, aad: bytes) -> None:
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA inválido")
    ct, iv, tag = encrypt_aes_gcm(secret.encode("utf-8"), aad)
    user.totp_secret_ciphertext = ct
    user.totp_secret_iv = iv
    user.totp_secret_tag = tag
    user.totp_enabled = True
    await db.commit()


def _execute_2fa_verification(user: User, code: str, aad: bytes) -> None:
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA incorrecto")


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


def _extract_refresh_cookies(request: Request) -> tuple[str, str]:
    rt = request.cookies.get("__Host-rg_rt") or request.cookies.get("rg_rt")
    if not rt:
        raise HTTPException(status_code=401, detail="Cookie de Refresh Token ausente")
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    return rt, token


def _decode_refresh_claims(token: str) -> dict[str, Any]:
    try:
        return dict(
            jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc


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
