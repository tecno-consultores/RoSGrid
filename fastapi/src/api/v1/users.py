# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import secrets
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, User, UserRouterPermission
from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import kill_all_user_sessions
from src.schemas.users import (
    AssignUserRoutersRequest,
    CreateUserRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


class Reset2FARequest(BaseModel):
    admin_totp_code: str


class ToggleRegistrationRequest(BaseModel):
    enabled: bool


class ApproveUserRequest(BaseModel):
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

    stmt_user = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    u_res = await db.execute(stmt_user)
    target_user = u_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_user.has_all_routers_access = body.has_all_routers_access

    # Limpiar asignaciones previas y crear nuevas
    stmt_del = delete(UserRouterPermission).where(
        UserRouterPermission.tenant_id == tenant_id, UserRouterPermission.user_id == user_id
    )
    await db.execute(stmt_del)

    admin_uuid = uuid.UUID(claims["sub"])
    for item in body.router_assignments:
        perm = UserRouterPermission(
            tenant_id=tenant_id,
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
