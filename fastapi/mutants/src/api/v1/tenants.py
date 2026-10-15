# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.schemas.tenants import CreateTenantRequest, TenantResponse, UpdateTenantRequest

router = APIRouter(prefix="/tenants", tags=["Tenants"])


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TenantResponse]:
    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    result = await db.execute(stmt)
    return [TenantResponse.model_validate(t) for t in result.scalars().all()]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: CreateTenantRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    await set_tenant_context(db, None, is_superadmin=True)

    # 1. Verificar slug único
    stmt_check = select(Tenant).where(Tenant.slug == body.slug)
    existing = await db.execute(stmt_check)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una organización con el slug '{body.slug}'",
        )

    # 2. Crear Tenant
    new_tenant = Tenant(
        slug=body.slug,
        name=body.name,
        status=TenantStatusEnum.ACTIVE,
        tax_id=body.tax_id,
        max_routers_quota=body.max_routers_quota,
        max_users_quota=body.max_users_quota,
        require_2fa_all_users=body.require_2fa_all_users,
        default_safemode_seconds=body.default_safemode_seconds,
    )
    db.add(new_tenant)
    await db.flush()

    # 3. Crear Administrador Inicial del Tenant
    admin_user = User(
        tenant_id=new_tenant.id,
        username=body.admin_username,
        email=body.admin_email,
        full_name=body.admin_full_name,
        password_hash=hash_password(body.admin_password),
        role=SystemRoleEnum.TENANT_ADMIN,
        has_all_routers_access=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(new_tenant)

    return TenantResponse.model_validate(new_tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: UpdateTenantRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)
    return TenantResponse.model_validate(tenant)
