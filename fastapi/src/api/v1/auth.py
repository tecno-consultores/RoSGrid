# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import json
import logging
import secrets
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import jwt
import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import extract_token_from_request, get_current_user_claims
from src.core.audit import write_audit_log
from src.core.config import settings
from src.core.crypto import (
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    hash_password,
    verify_password,
)
from src.core.csrf import generate_csrf_token
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import (
    CLOSING_GRACE_PERIOD_SECONDS,
    create_session,
    kill_all_user_sessions,
    kill_session,
    mark_session_closing,
    rotate_refresh_token,
)
from src.schemas.auth import (
    AuthSessionResponse,
    BootstrapInitRequest,
    BootstrapInitResponse,
    BootstrapStatusResponse,
    LoginStep1Request,
    LoginStep1Response,
    RegisterUserRequest,
    RegisterUserResponse,
    SessionClosingRequest,
    SessionClosingResponse,
    SwitchTenantRequest,
    UserProfileResponse,
    Verify2FARequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


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
    samesite: Literal["lax", "strict", "none"]
    if settings.ROSGRID_CROSS_ORIGIN_COOKIES:
        at_name = "rg_at"
        rt_name = "rg_rt"
        samesite = "none"
        secure_cookie = True
    else:
        at_name = "__Host-rg_at" if is_secure else "rg_at"
        rt_name = "__Host-rg_rt" if is_secure else "rg_rt"
        samesite = "strict"
        secure_cookie = is_secure

    response.set_cookie(
        key=at_name,
        value=access_token,
        max_age=28800,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        path="/",
    )
    response.set_cookie(
        key=rt_name,
        value=refresh_token,
        max_age=28800,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="rg_csrf",
        value=csrf_token,
        max_age=28800,
        httponly=False,
        secure=secure_cookie,
        samesite=samesite,
        path="/",
    )


async def _get_active_tenant(db: AsyncSession, slug: str) -> Tenant:
    clean_slug = slug.strip().lower()
    stmt = select(Tenant).where(Tenant.slug == clean_slug, Tenant.status == TenantStatusEnum.ACTIVE)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        # Intentar coincidencia por nombre de la empresa
        stmt_name = select(Tenant).where(
            func.lower(Tenant.name) == clean_slug, Tenant.status == TenantStatusEnum.ACTIVE
        )
        res_name = await db.execute(stmt_name)
        tenant = res_name.scalar_one_or_none()
    if not tenant:
        # Si sólo existe 1 tenant activo en la plataforma, resolver a ese tenant
        active_count = (
            await db.scalar(select(func.count(Tenant.id)).where(Tenant.status == TenantStatusEnum.ACTIVE)) or 0
        )
        if active_count == 1:
            stmt_single = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
            res_single = await db.execute(stmt_single)
            tenant = res_single.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
    return tenant


async def _log_login_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    actor_username: str,
    actor_role: SystemRoleEnum,
    event_action: str,
    status_code: int,
    request: Request | None = None,
    actor_user_id: uuid.UUID | None = None,
    error_message: str | None = None,
    extra_details: dict[str, Any] | None = None,
) -> None:
    ip_addr = request.client.host if (request and request.client) else "127.0.0.1"
    ua = request.headers.get("User-Agent") if request else None
    try:
        await write_audit_log(
            session=db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            actor_username=actor_username[:64],
            actor_role=actor_role,
            actor_ip=ip_addr,
            actor_user_agent=ua,
            event_category="AUTHENTICATION",
            event_action=event_action,
            status_code=status_code,
            error_message=error_message,
            after_state=extra_details,
        )
        await db.commit()
    except Exception as exc:
        logger.warning("No se pudo registrar log de auditoría de autenticación: %s", exc)


def _validate_user_lock(user: User) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )


async def _verify_user_credentials(
    db: AsyncSession,
    user: User,
    password: str,
    request: Request | None = None,
) -> None:
    now_utc = datetime.now(UTC)
    if user.is_locked and user.locked_until and user.locked_until > now_utc:
        await _log_login_event(
            db=db,
            tenant_id=user.tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_FAILED_ACCOUNT_LOCKED",
            status_code=423,
            error_message="Cuenta bloqueada temporalmente por múltiples intentos fallidos",
            request=request,
        )
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.",
        )

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
        await _log_login_event(
            db=db,
            tenant_id=user.tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_FAILED_INVALID_PASSWORD",
            status_code=401,
            error_message="Credenciales inválidas",
            extra_details={"failed_attempts": user.failed_login_attempts, "locked": user.is_locked},
            request=request,
        )
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        await _log_login_event(
            db=db,
            tenant_id=user.tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_FAILED_USER_INACTIVE",
            status_code=403,
            error_message="Cuenta inactiva pendiente de aprobación",
            request=request,
        )
        raise HTTPException(
            status_code=403,
            detail="Tu cuenta está pendiente de aprobación por el Administrador. No puedes ingresar hasta que sea autorizada y se te asigne un rol.",
        )

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
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> LoginStep1Response:
    tenant = await _get_active_tenant(db, body.tenant_slug)
    await set_tenant_context(db, tenant.id, is_superadmin=False)

    ident = body.identifier
    stmt_user = select(User).where(
        User.tenant_id == tenant.id,
        or_(User.email == ident, User.username == ident),
    )
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    if not user:
        await _log_login_event(
            db=db,
            tenant_id=tenant.id,
            actor_username=ident,
            actor_role=SystemRoleEnum.AUDITOR,
            actor_user_id=None,
            event_action="LOGIN_FAILED_USER_NOT_FOUND",
            status_code=401,
            error_message="Credenciales inválidas o empresa no encontrada",
            request=request,
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")

    await _verify_user_credentials(db, user, body.password, request=request)
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


async def _execute_2fa_verification(db: AsyncSession, user: User, code: str, aad: bytes) -> None:
    clean_code = code.strip().upper()
    code_hash = hashlib.sha256(clean_code.encode("utf-8")).hexdigest()

    # 1. Comprobar si coincide con un código de recuperación de emergencia
    current_hashes = list(user.totp_recovery_codes_hashes or [])
    if code_hash in current_hashes:
        current_hashes.remove(code_hash)
        user.totp_recovery_codes_hashes = current_hashes
        await db.commit()
        return

    # 2. Si no es código de recuperación, verificar token TOTP dinámico
    if not user.totp_secret_ciphertext or not user.totp_secret_iv or not user.totp_secret_tag:
        raise HTTPException(status_code=401, detail="Configuración 2FA corrupta")
    secret_bytes = decrypt_aes_gcm(user.totp_secret_ciphertext, user.totp_secret_iv, user.totp_secret_tag, aad)
    secret = secret_bytes.decode("utf-8")
    if not pyotp.TOTP(secret).verify(clean_code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA o de recuperación incorrecto")


def _extract_tenant_features(tenant: Tenant) -> dict[str, Any]:
    features_dict: dict[str, Any] = {
        "isp_module_enabled": True,
        "bgp_looking_glass_enabled": False,
        "sfp_ddm_telemetry_enabled": True,
        "ipfix_analytics_enabled": False,
        "enforce_maker_checker": True,
        "auto_safemode_enforced": True,
        "ai_mcp_integration_enabled": True,
        "nightly_backups_enabled": True,
        "outbound_webhooks_enabled": True,
        "config_drift_monitoring_enabled": False,
        "cis_audit_enabled": True,
        "sdwan_orchestrator_enabled": False,
        "capsman_wifi_enabled": False,
        "sla_tracker_enabled": False,
        "l2_topology_enabled": True,
        "syslog_collector_enabled": True,
        "cve_scanner_enabled": True,
        "prometheus_fleet_exporter_enabled": True,
        "mass_outage_threshold": 10,
        "default_locale": "es",
    }
    for key in list(features_dict.keys()):
        val = getattr(tenant, key, None)
        if val is not None:
            features_dict[key] = val

    custom_features = getattr(tenant, "features", None)
    if isinstance(custom_features, dict):
        features_dict.update(custom_features)

    return features_dict


async def _build_auth_session_response(
    request: Request,
    response: Response,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    tenant_name: str,
    user: User,
    db: AsyncSession | None = None,
    features: dict[str, Any] | None = None,
) -> AuthSessionResponse:
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent", "Unknown")

    # Política de Sesión Única: revocar cualquier sesión activa previa del usuario
    killed_count = await kill_all_user_sessions(
        str(tenant_id),
        str(user.id),
        killed_by="AUTH_LOGIN",
        reason="Nueva sesión iniciada (política de sesión única)",
    )
    if killed_count > 0 and db is not None:
        await _log_login_event(
            db=db,
            tenant_id=tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="SESSION_KILLED_DUPLICATE_LOGIN",
            status_code=200,
            extra_details={"killed_sessions_count": killed_count},
            request=request,
        )

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

    if db is not None:
        await _log_login_event(
            db=db,
            tenant_id=tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_SUCCESSFUL",
            status_code=200,
            extra_details={"session_id": session_id},
            request=request,
        )

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
            features=features or {},
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
    try:
        if preauth_data.get("status") == "ENROLL_2FA_REQUIRED":
            secret = str(preauth_data.get("temp_totp_secret", ""))
            await _execute_2fa_enrollment(db, user, body.totp_code, secret, aad)
        else:
            await _execute_2fa_verification(db, user, body.totp_code, aad)
    except HTTPException as exc:
        await _log_login_event(
            db=db,
            tenant_id=tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="2FA_VERIFICATION_FAILED",
            status_code=exc.status_code,
            error_message=str(exc.detail),
            request=request,
        )
        raise

    await redis.delete(preauth_key)

    stmt_t = select(Tenant).where(Tenant.id == tenant_id)
    t_res = await db.execute(stmt_t)
    tenant_obj = t_res.scalar_one()

    features = _extract_tenant_features(tenant_obj)

    return await _build_auth_session_response(
        request, response, tenant_id, tenant_obj.slug, tenant_obj.name, user, db=db, features=features
    )


@router.post("/2fa/confirm-enrollment", response_model=AuthSessionResponse)
async def confirm_2fa_enrollment(
    body: Verify2FARequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    """Alias para confirmación de enrolamiento 2FA (mismo flujo de validación y sesión que verify_2fa)."""
    return await verify_2fa(body, request, response, db)


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


@router.post(
    "/session-closing",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SessionClosingResponse,
)
async def session_closing(
    request: Request,
    payload: SessionClosingRequest | None = None,
) -> SessionClosingResponse:
    """Registra una sesión en estado de cierre temporal con período de gracia de 35s.

    Invocado por el frontend ante el cierre de la última pestaña o navegador
    (mediante navigator.sendBeacon o fetch con keepalive).
    """
    sid: str | None = payload.session_id if payload else None
    if not sid:
        try:
            raw_body = await request.body()
            if raw_body:
                body_json = json.loads(raw_body.decode("utf-8"))
                sid = body_json.get("session_id")
        except Exception:
            sid = None

    token = extract_token_from_request(request)
    tenant_id: str | None = None

    if token:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                settings.ROSGRID_JWT_SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            tenant_id = claims.get("tid")
            token_sid = claims.get("sid")
            if sid and token_sid and sid != token_sid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="El ID de sesión no coincide con las credenciales",
                )
            sid = sid or token_sid
        except jwt.PyJWTError:
            pass

    if not sid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere session_id para registrar el cierre",
        )

    redis = get_redis_client()
    if not tenant_id:
        keys = await redis.keys(f"rg:*:sess:{sid}")
        if keys:
            first_key = keys[0]
            matched_key = first_key.decode("utf-8") if isinstance(first_key, bytes) else str(first_key)
            parts = matched_key.split(":")
            if len(parts) >= 4:
                tenant_id = parts[1]

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada o ya finalizada",
        )

    marked = await mark_session_closing(tenant_id, sid, grace_seconds=CLOSING_GRACE_PERIOD_SECONDS)
    if not marked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión no existe en el registro activo",
        )

    return SessionClosingResponse(
        status="GRACE_PERIOD_ACTIVE",
        ttl_seconds=CLOSING_GRACE_PERIOD_SECONDS,
        session_id=sid,
    )


@router.post("/switch-tenant", response_model=AuthSessionResponse)
async def switch_tenant(
    body: SwitchTenantRequest,
    request: Request,
    response: Response,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    """Permite al Super Administrador Global conmutar en caliente entre tenants activos.

    Emite un nuevo JWT token, actualiza la sesión en KeyDB y registra la auditoría WORM.
    """
    current_role = claims.get("rol")
    if current_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo el Super Administrador Global puede conmutar de tenant",
        )

    # 1. Buscar y validar el tenant destino
    query = select(Tenant)
    if body.target_tenant_id:
        query = query.where(Tenant.id == body.target_tenant_id)
    elif body.target_tenant_slug:
        query = query.where(Tenant.slug == body.target_tenant_slug.strip().lower())

    target_tenant = await db.scalar(query)
    if not target_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El tenant destino especificado no existe",
        )

    if target_tenant.status != TenantStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tenant destino especificado no se encuentra activo",
        )

    # 2. Cargar datos del usuario SuperAdmin actual
    current_user_id = uuid.UUID(str(claims["sub"]))
    user = await db.scalar(select(User).where(User.id == current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario Super Administrador no encontrado",
        )

    old_tenant_id = str(claims["tid"])
    old_session_id = str(claims["sid"])

    # 3. Revocar sesión previa en el tenant anterior
    await kill_session(
        old_tenant_id,
        old_session_id,
        killed_by="SUPERADMIN_TENANT_SWITCH",
        reason=f"Conmutación al tenant {target_tenant.slug}",
    )

    # 4. Construir y activar nueva sesión para el tenant destino
    features = _extract_tenant_features(target_tenant)
    session_response = await _build_auth_session_response(
        request=request,
        response=response,
        tenant_id=target_tenant.id,
        tenant_slug=target_tenant.slug,
        tenant_name=target_tenant.name,
        user=user,
        db=db,
        features=features,
    )

    # 5. Registrar evento WORM específico de cambio de tenant
    await _log_login_event(
        db=db,
        tenant_id=target_tenant.id,
        actor_username=user.username,
        actor_role=user.role,
        actor_user_id=user.id,
        event_action="SUPERADMIN_TENANT_SWITCHED",
        status_code=200,
        extra_details={
            "previous_tenant_id": old_tenant_id,
            "target_tenant_id": str(target_tenant.id),
            "target_tenant_slug": target_tenant.slug,
            "new_session_id": session_response.session_id,
        },
        request=request,
    )

    return session_response


@router.get("/me")
async def get_me(claims: dict[str, Any] = Depends(get_current_user_claims)) -> dict[str, Any]:
    return claims


@router.get("/bootstrap-status", response_model=BootstrapStatusResponse)
async def get_bootstrap_status(
    db: AsyncSession = Depends(get_db_session),
) -> BootstrapStatusResponse:
    redis = get_redis_client()
    users_count = await db.scalar(select(func.count(User.id))) or 0
    tenants_count = await db.scalar(select(func.count(Tenant.id))) or 0
    is_bootstrapped = users_count > 0

    reg_enabled_raw = await redis.get("rg:config:public_registration_enabled")
    reg_enabled = True
    if reg_enabled_raw is not None:
        val = reg_enabled_raw.decode("utf-8") if isinstance(reg_enabled_raw, bytes) else str(reg_enabled_raw)
        if val.lower() in ("0", "false", "off", "no"):
            reg_enabled = False

    default_tenant_slug: str | None = None
    default_tenant_name: str | None = None
    if tenants_count == 1:
        single_tenant = (await db.execute(select(Tenant))).scalar_one_or_none()
        if single_tenant:
            default_tenant_slug = single_tenant.slug
            default_tenant_name = single_tenant.name

    return BootstrapStatusResponse(
        is_bootstrapped=is_bootstrapped,
        tenants_count=tenants_count,
        users_count=users_count,
        registration_enabled=reg_enabled,
        default_tenant_slug=default_tenant_slug,
        default_tenant_name=default_tenant_name,
        message="Sistema ya inicializado"
        if is_bootstrapped
        else "Inicialización requerida: No hay usuarios registrados.",
    )


@router.post("/register", response_model=RegisterUserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterUserResponse:
    redis = get_redis_client()
    users_count = await db.scalar(select(func.count(User.id))) or 0
    if users_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El sistema requiere inicialización mediante bootstrap para crear el Super Administrador inicial.",
        )

    # 1. Verificar si el auto-registro está habilitado
    reg_enabled_raw = await redis.get("rg:config:public_registration_enabled")
    if reg_enabled_raw is not None:
        val = reg_enabled_raw.decode("utf-8") if isinstance(reg_enabled_raw, bytes) else str(reg_enabled_raw)
        if val.lower() in ("0", "false", "off", "no"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El auto-registro de usuarios ha sido deshabilitado por el Administrador.",
            )

    # 2. Buscar tenant por slug, nombre o fallback si existe un único tenant
    clean_slug = body.tenant_slug.strip().lower()
    stmt_t = select(Tenant).where(Tenant.slug == clean_slug)
    res_t = await db.execute(stmt_t)
    tenant = res_t.scalar_one_or_none()
    if not tenant:
        stmt_name = select(Tenant).where(func.lower(Tenant.name) == clean_slug)
        res_name = await db.execute(stmt_name)
        tenant = res_name.scalar_one_or_none()
    if not tenant:
        tenants_count = await db.scalar(select(func.count(Tenant.id))) or 0
        if tenants_count == 1:
            stmt_single = select(Tenant)
            res_single = await db.execute(stmt_single)
            tenant = res_single.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La empresa o tenant '{body.tenant_slug}' no existe en RoSGrid. Verifica el identificador de la organización.",
        )

    # 3. Verificar unicidad de username y email
    clean_username = body.username.strip()
    clean_email = body.email.strip().lower()
    stmt_check = select(User).where(
        User.tenant_id == tenant.id,
        (User.username == clean_username) | (User.email == clean_email),
    )
    res_check = await db.execute(stmt_check)
    if res_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este nombre de usuario o correo en la empresa.",
        )

    # 4. Crear usuario en estado PENDIENTE DE APROBACIÓN (is_active = False)
    new_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        username=clean_username,
        email=clean_email,
        full_name=body.full_name.strip(),
        password_hash=hash_password(body.password),
        role=SystemRoleEnum.NOC_MONITOR,
        is_active=False,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=False,
        has_all_routers_access=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RegisterUserResponse(
        status="PENDING_APPROVAL",
        message="Tu cuenta fue creada exitosamente y se encuentra pendiente de aprobación por el Administrador. No podrás ingresar hasta que sea autorizada y se te asigne un rol.",
        user_id=new_user.id,
        username=new_user.username,
        is_active=False,
    )


@router.post("/bootstrap", response_model=BootstrapInitResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_initial_admin(
    body: BootstrapInitRequest,
    db: AsyncSession = Depends(get_db_session),
) -> BootstrapInitResponse:
    users_count = await db.scalar(select(func.count(User.id))) or 0
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El sistema ya ha sido inicializado. No es posible crear otro Super Administrador inicial vía bootstrap.",
        )

    # 1. Crear Tenant Principal
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name=body.tenant_name.strip(),
        slug=body.tenant_slug.strip().lower(),
        status=TenantStatusEnum.ACTIVE,
    )
    db.add(tenant)
    await db.flush()

    # 2. Generar secreto 2FA y códigos de respaldo
    totp_secret = pyotp.random_base32()
    totp = pyotp.totp.TOTP(totp_secret)
    totp_uri = totp.provisioning_uri(name=body.admin_email, issuer_name="RoSGrid")
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    backup_hashes = [hashlib.sha256(c.encode("utf-8")).hexdigest() for c in backup_codes]

    # 3. Cifrar secretos con AES-256-GCM
    admin_id = uuid.uuid4()
    aad = f"{tenant.id}:{admin_id}".encode("utf-8")
    ct, iv, tag = encrypt_aes_gcm(totp_secret.encode("utf-8"), aad)

    # 4. Crear Super Administrador Global
    super_admin = User(
        id=admin_id,
        tenant_id=tenant.id,
        username=body.admin_username.strip(),
        email=body.admin_email.strip().lower(),
        full_name=body.admin_full_name.strip(),
        password_hash=hash_password(body.admin_password),
        role=SystemRoleEnum.SUPERADMIN_GLOBAL,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=True,
        totp_secret_ciphertext=ct,
        totp_secret_iv=iv,
        totp_secret_tag=tag,
        totp_recovery_codes_hashes=backup_hashes,
        has_all_routers_access=True,
    )
    db.add(super_admin)
    await db.commit()
    await db.refresh(tenant)
    await db.refresh(super_admin)

    # 5. Generar preauth challenge para enrolar/verificar 2FA en el navegador inmediatamente
    challenge_id = secrets.token_hex(16)
    redis: Any = get_redis_client()
    preauth_key = f"rg:{tenant.id}:preauth:{challenge_id}"
    mapping: dict[str, Any] = {
        "user_id": str(super_admin.id),
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "status": "VERIFY_2FA_TOTP",
    }
    await redis.hset(preauth_key, mapping=mapping)
    await redis.expire(preauth_key, 300)

    return BootstrapInitResponse(
        status="success",
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        admin_id=super_admin.id,
        admin_username=super_admin.username,
        totp_secret=totp_secret,
        totp_provisioning_uri=totp_uri,
        backup_codes=backup_codes,
        challenge_id=challenge_id,
        message="Super Administrador y Tenant Principal creados exitosamente.",
    )
