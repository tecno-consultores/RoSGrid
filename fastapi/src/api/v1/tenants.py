# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import write_audit_log
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
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TenantResponse]:
    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
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

    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    return TenantFeaturesResponse(
        isp_module_enabled=tenant.isp_module_enabled,
        bgp_looking_glass_enabled=tenant.bgp_looking_glass_enabled,
        sfp_ddm_telemetry_enabled=tenant.sfp_ddm_telemetry_enabled,
        ipfix_analytics_enabled=tenant.ipfix_analytics_enabled,
        enforce_maker_checker=tenant.enforce_maker_checker,
        auto_safemode_enforced=tenant.auto_safemode_enforced,
        ai_mcp_integration_enabled=tenant.ai_mcp_integration_enabled,
        nightly_backups_enabled=tenant.nightly_backups_enabled,
        outbound_webhooks_enabled=tenant.outbound_webhooks_enabled,
        config_drift_monitoring_enabled=tenant.config_drift_monitoring_enabled,
        cis_audit_enabled=tenant.cis_audit_enabled,
        sdwan_orchestrator_enabled=tenant.sdwan_orchestrator_enabled,
        capsman_wifi_enabled=tenant.capsman_wifi_enabled,
        sla_tracker_enabled=tenant.sla_tracker_enabled,
        mass_outage_threshold=tenant.mass_outage_threshold,
        default_locale=tenant.default_locale,
    )


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    await set_tenant_context(db, None, is_superadmin=True)
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    # Invalidar caché KeyDB
    redis = get_redis_client()
    try:
        await redis.delete(f"rg:{tenant_id}:features")
    except Exception:
        pass

    # Registro de auditoría WORM
    await write_audit_log(
        db=db,
        tenant_id=tenant.id,
        user_id=uuid.UUID(str(claims.get("sub"))),
        username=str(claims.get("username", "superadmin")),
        action="UPDATE_TENANT_FEATURE_FLAGS",
        resource_type="TENANT",
        resource_id=str(tenant.id),
        details={"updated_fields": list(update_data.keys()), "values": update_data},
    )

    return TenantFeaturesResponse(
        isp_module_enabled=tenant.isp_module_enabled,
        bgp_looking_glass_enabled=tenant.bgp_looking_glass_enabled,
        sfp_ddm_telemetry_enabled=tenant.sfp_ddm_telemetry_enabled,
        ipfix_analytics_enabled=tenant.ipfix_analytics_enabled,
        enforce_maker_checker=tenant.enforce_maker_checker,
        auto_safemode_enforced=tenant.auto_safemode_enforced,
        ai_mcp_integration_enabled=tenant.ai_mcp_integration_enabled,
        nightly_backups_enabled=tenant.nightly_backups_enabled,
        outbound_webhooks_enabled=tenant.outbound_webhooks_enabled,
        config_drift_monitoring_enabled=tenant.config_drift_monitoring_enabled,
        cis_audit_enabled=tenant.cis_audit_enabled,
        sdwan_orchestrator_enabled=tenant.sdwan_orchestrator_enabled,
        capsman_wifi_enabled=tenant.capsman_wifi_enabled,
        sla_tracker_enabled=tenant.sla_tracker_enabled,
        mass_outage_threshold=tenant.mass_outage_threshold,
        default_locale=tenant.default_locale,
    )


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
    except Exception:
        pass

    return TenantResponse.model_validate(tenant)
