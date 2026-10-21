# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import json
import secrets
import time
import uuid
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.core.audit import write_audit_log
from src.core.config import settings
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, User, UserRouterPermission
from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import kill_all_user_sessions
from src.schemas.users import (
    AssignUserRoutersRequest,
    CreateUserRequest,
    GenerateMcpTokenRequest,
    McpTokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


class Reset2FARequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admin_totp_code: str


class ToggleRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool


class ApproveUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: SystemRoleEnum
    has_all_routers_access: bool = False
    allowed_cidr_list: list[str] = []


@router.get("", response_model=list[UserResponse])
async def list_users(
    role: SystemRoleEnum | None = None,
    is_active: bool | None = None,
    pending_only: bool = False,
    search: str | None = None,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.AUDITOR,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> list[UserResponse]:
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    stmt = select(User).where(User.tenant_id == tenant_id)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if pending_only:
        stmt = stmt.where(User.is_active.is_(False))
    elif is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(User.username.ilike(pattern) | User.email.ilike(pattern))

    result = await db.execute(stmt)
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    if not is_sa and body.role == SystemRoleEnum.SUPERADMIN_GLOBAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un Administrador de Organización no puede asignar el rol SUPERADMIN_GLOBAL.",
        )

    # Comprobar unicidad
    stmt_check = select(User).where(
        User.tenant_id == tenant_id,
        (User.username == body.username) | (User.email == body.email),
    )
    existing = await db.execute(stmt_check)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este username o email en la organización",
        )

    new_user = User(
        tenant_id=tenant_id,
        username=body.username.strip(),
        email=body.email.strip().lower(),
        full_name=body.full_name.strip(),
        password_hash=hash_password(str(body.temporary_password)),
        role=body.role,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=False,
        has_all_routers_access=body.has_all_routers_access,
        allowed_cidr_list=body.allowed_cidr_list or [],
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@router.get("/{user_id}/router-permissions")
async def get_user_router_permissions(
    user_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    stmt_user = select(User).where(User.id == user_id)
    if not is_sa:
        stmt_user = stmt_user.where(User.tenant_id == tenant_id)
    u_res = await db.execute(stmt_user)
    target_user = u_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_tenant_id = target_user.tenant_id

    from sqlalchemy.orm import selectinload

    from src.models.inventory import Router

    stmt_routers = (
        select(Router)
        .options(selectinload(Router.tags))
        .where(Router.tenant_id == target_tenant_id)
        .order_by(Router.display_name.asc())
    )
    routers = (await db.execute(stmt_routers)).scalars().all()

    stmt_perms = select(UserRouterPermission).where(
        UserRouterPermission.tenant_id == target_tenant_id, UserRouterPermission.user_id == user_id
    )
    perms_map = {p.router_id: p for p in (await db.execute(stmt_perms)).scalars().all()}

    res_permissions = []
    for r in routers:
        p = perms_map.get(r.id)
        tag_str = r.tags[0].tag_name if r.tags and len(r.tags) > 0 else ""
        role_str = r.network_role.value if hasattr(r.network_role, "value") else str(r.network_role or "")
        res_permissions.append(
            {
                "router_id": str(r.id),
                "router_name": r.display_name,
                "network_role": role_str,
                "tag": tag_str,
                "can_read": p.can_read if p else False,
                "can_write_layer1": p.can_write_layer1 if p else False,
                "can_write_layer2": p.can_write_layer2 if p else False,
                "can_execute_diagnostics": p.can_execute_diagnostics if p else False,
                "can_trigger_backup": p.can_trigger_backup if p else False,
                "can_reboot": p.can_reboot if p else False,
                "bypass_maker_checker": p.bypass_maker_checker if p else False,
            }
        )

    return {
        "has_all_routers_access": target_user.has_all_routers_access,
        "permissions": res_permissions,
    }


@router.put("/{user_id}/router-permissions")
async def assign_router_permissions(
    user_id: uuid.UUID,
    body: AssignUserRoutersRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    stmt_user = select(User).where(User.id == user_id)
    if not is_sa:
        stmt_user = stmt_user.where(User.tenant_id == tenant_id)
    u_res = await db.execute(stmt_user)
    target_user = u_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_tenant_id = target_user.tenant_id
    target_user.has_all_routers_access = body.has_all_routers_access

    # Limpiar asignaciones previas y crear nuevas
    stmt_del = delete(UserRouterPermission).where(
        UserRouterPermission.tenant_id == target_tenant_id, UserRouterPermission.user_id == user_id
    )
    await db.execute(stmt_del)

    admin_uuid = uuid.UUID(claims["sub"])
    for item in body.router_assignments:
        perm = UserRouterPermission(
            tenant_id=target_tenant_id,
            user_id=user_id,
            router_id=item.router_id,
            can_read=item.can_read,
            can_write_layer1=item.can_write_layer1,
            can_write_layer2=item.can_write_layer2,
            can_execute_diagnostics=item.can_execute_diagnostics,
            can_trigger_backup=item.can_trigger_backup,
            can_reboot=item.can_reboot,
            bypass_maker_checker=item.bypass_maker_checker,
            assigned_by=admin_uuid,
        )
        db.add(perm)

    await db.commit()
    return {"status": "success", "assigned_count": len(body.router_assignments)}


@router.post("/{user_id}/reset-2fa")
async def reset_user_2fa(
    user_id: uuid.UUID,
    body: Reset2FARequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_user.totp_enabled = False
    target_user.totp_secret_ciphertext = None
    target_user.totp_secret_iv = None
    target_user.totp_secret_tag = None
    await db.commit()

    # Expulsión de sesiones activas del usuario por Kill-Switch
    await kill_all_user_sessions(str(tenant_id), str(user_id), killed_by=claims["sub"], reason="Reinicio de 2FA")

    return {"status": "2fa_reset_completed"}


@router.post("/registration-toggle")
async def toggle_registration(
    body: ToggleRegistrationRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> dict[str, Any]:
    """Habilita o deshabilita el auto-registro público de usuarios en la plataforma."""
    redis = get_redis_client()
    val = "true" if body.enabled else "false"
    await redis.set("rg:config:public_registration_enabled", val)
    return {"registration_enabled": body.enabled}


@router.put("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: uuid.UUID,
    body: ApproveUserRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Aprueba un usuario auto-registrado en estado PENDIENTE, activándolo y asignándole un rol."""
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    if not is_sa and body.role == SystemRoleEnum.SUPERADMIN_GLOBAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un Administrador de Organización no puede asignar el rol SUPERADMIN_GLOBAL.",
        )

    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_user.is_active = True
    target_user.role = body.role
    target_user.has_all_routers_access = body.has_all_routers_access
    target_user.allowed_cidr_list = body.allowed_cidr_list
    await db.commit()
    await db.refresh(target_user)

    return UserResponse.model_validate(target_user)


@router.delete("/{user_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_user(
    user_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Rechaza y elimina una solicitud de registro pendiente de aprobación.
    Si ya existen trazas inmutables en audit_logs (donde WORM prohíbe UPDATE),
    bloquea y desactiva el usuario permanentemente."""
    tenant_id = uuid.UUID(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        await db.delete(target_user)
        await db.commit()
    except Exception:
        await db.rollback()
        # Se recarga el usuario para aplicar soft-delete / revocación definitiva
        res_reload = await db.execute(stmt)
        u_reload = res_reload.scalar_one_or_none()
        if u_reload:
            u_reload.is_active = False
            u_reload.is_locked = True
            rnd_suffix = secrets.token_hex(4)
            u_reload.username = f"rejected_{u_reload.username}_{rnd_suffix}"
            u_reload.email = f"rejected_{rnd_suffix}_{u_reload.email}"
            await db.commit()


@router.post("/{user_id}/mcp-token", response_model=McpTokenResponse)
async def generate_user_mcp_token(
    user_id: uuid.UUID,
    body: GenerateMcpTokenRequest | None = None,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> McpTokenResponse:
    """Emite un token Bearer JWT de larga duración para operar el endpoint MCP y registra la sesión en KeyDB."""
    caller_role = claims.get("rol")
    caller_tenant_id = uuid.UUID(claims["tid"])
    caller_username = claims.get("preferred_username") or claims.get("sub") or "admin"
    is_sa = caller_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value

    await set_tenant_context(db, caller_tenant_id, is_superadmin=is_sa)

    if is_sa:
        stmt = select(User).where(User.id == user_id)
    else:
        stmt = select(User).where(User.id == user_id, User.tenant_id == caller_tenant_id)

    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    allowed_mcp_roles = {
        SystemRoleEnum.SERVICE_ACCOUNT,
        SystemRoleEnum.TENANT_ADMIN,
        SystemRoleEnum.SUPERADMIN_GLOBAL,
    }
    if target_user.role not in allowed_mcp_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario con rol '{target_user.role.value}' no tiene permitido operar el endpoint MCP (roles permitidos: SERVICE_ACCOUNT, TENANT_ADMIN, SUPERADMIN_GLOBAL)",
        )

    stmt_t = select(Tenant).where(Tenant.id == target_user.tenant_id)
    res_t = await db.execute(stmt_t)
    tenant = res_t.scalar_one_or_none()
    tenant_slug = tenant.slug if tenant else "default"

    expiry_days = body.expiry_days if body else 365
    session_id = str(uuid.uuid4())
    redis = get_redis_client()
    now = int(time.time())
    ttl_seconds = expiry_days * 86400
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    exp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + ttl_seconds))

    allowed_ip = (
        target_user.allowed_cidr_list[0]
        if (target_user.allowed_cidr_list and len(target_user.allowed_cidr_list) > 0)
        else "127.0.0.1"
    )

    sess_key = f"rg:{target_user.tenant_id}:sess:{session_id}"
    active_sess_key = f"rg:{target_user.tenant_id}:active_sessions"
    user_sess_key = f"rg:{target_user.tenant_id}:user_sessions:{target_user.id}"

    mapping = {
        "session_id": session_id,
        "user_id": str(target_user.id),
        "username": target_user.username,
        "full_name": target_user.full_name or target_user.username,
        "role": target_user.role.value,
        "tenant_id": str(target_user.tenant_id),
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "ip_address": allowed_ip,
        "user_agent": "RoSGrid-MCP-Daemon/1.0",
        "is_service_account": "true",
        "issued_by_username": str(caller_username),
        "allowed_cidr_list": json.dumps(target_user.allowed_cidr_list),
    }

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, ttl_seconds)
    pipe.zadd(active_sess_key, {session_id: float(now)})
    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, ttl_seconds)
    await pipe.execute()

    payload = {
        "sub": str(target_user.id),
        "tid": str(target_user.tenant_id),
        "tslug": tenant_slug,
        "sid": session_id,
        "rol": target_user.role.value,
        "all_r": target_user.has_all_routers_access,
        "preferred_username": target_user.username,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    token = jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")

    await write_audit_log(
        session=db,
        tenant_id=target_user.tenant_id,
        actor_username=str(caller_username),
        actor_role=str(caller_role or "ADMIN"),
        actor_ip=str(claims.get("ip_address") or "127.0.0.1"),
        event_category="MCP_TOKEN_ISSUED",
        event_action="GENERATE_MCP_TOKEN",
        actor_user_id=uuid.UUID(claims["sub"]),
        after_state={
            "target_user_id": str(target_user.id),
            "target_username": target_user.username,
            "role": target_user.role.value,
            "expiry_days": expiry_days,
            "session_id": session_id,
            "allowed_cidr_list": target_user.allowed_cidr_list,
        },
        status_code=200,
    )
    await db.commit()

    return McpTokenResponse(
        token=token,
        token_type="Bearer",
        session_id=session_id,
        expires_at=exp_iso,
        expiry_days=expiry_days,
        user_id=target_user.id,
        username=target_user.username,
        tenant_slug=tenant_slug,
        role=target_user.role.value,
        allowed_cidr_list=target_user.allowed_cidr_list,
        issued_by=str(caller_username),
    )
