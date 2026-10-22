# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import audit_actor_from_claims, write_audit_log
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.redis_layer.client import get_redis_client
from src.schemas.tenants import (
    CreateTenantRequest,
    TenantFeaturesResponse,
    TenantResponse,
    UpdateTenantFeaturesRequest,
    UpdateTenantRequest,
    extract_tenant_features,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TenantResponse]:
    user_role = claims.get("rol")
    if user_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        await set_tenant_context(db, None, is_superadmin=True)
        stmt = select(Tenant).order_by(Tenant.created_at.desc())
        result = await db.execute(stmt)
        return [TenantResponse.model_validate(t) for t in result.scalars().all()]
    else:
        user_tid = claims.get("tid")
        if not user_tid:
            raise HTTPException(status_code=403, detail="Contexto de empresa no disponible")
        await set_tenant_context(db, uuid.UUID(str(user_tid)), is_superadmin=False)
        stmt = select(Tenant).where(Tenant.id == uuid.UUID(str(user_tid)))
        result = await db.execute(stmt)
        return [TenantResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value and str(user_tid) != str(tenant_id):
        raise HTTPException(status_code=403, detail="No autorizado para consultar esta empresa")

    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return TenantResponse.model_validate(tenant)


async def _load_tenant_or_404(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    await set_tenant_context(db, None, is_superadmin=True)
    res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


async def invalidate_tenant_features_cache(tenant_id: uuid.UUID) -> None:
    """Invalida la caché L2 de flags en KeyDB para propagación inmediata a todas las sesiones."""
    try:
        await get_redis_client().delete(f"rg:{tenant_id}:features")
    except Exception:
        logger.warning("No se pudo invalidar la caché de features del tenant %s", tenant_id)


@router.get("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def get_tenant_features(
    tenant_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value and str(user_tid) != str(tenant_id):
        raise HTTPException(status_code=403, detail="No autorizado para consultar configuración de esta empresa")

    tenant = await _load_tenant_or_404(db, tenant_id)
    return TenantFeaturesResponse.model_validate(tenant)


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value and str(user_tid) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para modificar la configuración de otra empresa",
        )

    tenant = await _load_tenant_or_404(db, tenant_id)
    before_state = extract_tenant_features(tenant)

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    actor = audit_actor_from_claims(claims, request)
    actor["tenant_id"] = tenant.id
    await write_audit_log(
        session=db,
        **actor,
        event_category="GOVERNANCE",
        event_action="TENANT_FEATURE_FLAGS_UPDATED",
        before_state={key: before_state[key] for key in update_data},
        after_state=update_data,
    )
    await db.commit()
    await db.refresh(tenant)
    await invalidate_tenant_features_cache(tenant_id)

    return TenantFeaturesResponse.model_validate(tenant)


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

    # Invalidar caché de features en KeyDB
    redis = get_redis_client()
    try:
        await redis.delete(f"rg:{tenant_id}:features")
    except Exception as ex:
        logger.warning(f"Error al invalidar caché de features en redis: {ex}")

    return TenantResponse.model_validate(tenant)
