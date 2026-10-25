# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import audit_actor_from_claims, write_audit_log
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.models.operations import AuditLog
from src.redis_layer.client import get_redis_client
from src.schemas.audit import AuditLogResponse
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
    features_dict = extract_tenant_features(tenant)
    try:
        redis = get_redis_client()
        onb_val = await redis.get(f"rg:{tenant_id}:onboarding_completed")
        if onb_val:
            features_dict["onboarding_completed"] = (
                onb_val.decode() if isinstance(onb_val, bytes) else str(onb_val)
            ).lower() == "true"
    except Exception as exc:
        logger.debug("Error leyendo onboarding_completed de KeyDB: %s", exc)
    return TenantFeaturesResponse.model_validate(features_dict)


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
@router.put("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol SUPERADMIN_GLOBAL pueden modificar los módulos y licencias de las empresas.",
        )

    tenant = await _load_tenant_or_404(db, tenant_id)
    before_state = extract_tenant_features(tenant)

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)

    # Manejo de flag efímero de onboarding_completed en KeyDB
    onboarding_completed_val: bool | None = None
    if "onboarding_completed" in update_data:
        onboarding_completed_val = bool(update_data.pop("onboarding_completed"))
        try:
            redis = get_redis_client()
            await redis.set(f"rg:{tenant_id}:onboarding_completed", "true" if onboarding_completed_val else "false")
        except Exception as exc:
            logger.debug("Error guardando onboarding_completed en KeyDB: %s", exc)

    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    actor = audit_actor_from_claims(claims, request)
    actor["tenant_id"] = tenant.id
    await write_audit_log(
        session=db,
        **actor,
        event_category="GOVERNANCE",
        event_action="TENANT_FEATURE_FLAGS_UPDATED",
        before_state={key: before_state[key] for key in update_data if key in before_state},
        after_state=update_data,
    )
    await db.commit()
    await db.refresh(tenant)
    await invalidate_tenant_features_cache(tenant_id)

    response_dict = extract_tenant_features(tenant)
    if onboarding_completed_val is not None:
        response_dict["onboarding_completed"] = onboarding_completed_val
    else:
        try:
            redis = get_redis_client()
            onb_check = await redis.get(f"rg:{tenant_id}:onboarding_completed")
            if onb_check:
                response_dict["onboarding_completed"] = (
                    onb_check.decode() if isinstance(onb_check, bytes) else str(onb_check)
                ).lower() == "true"
        except Exception:
            pass
    return TenantFeaturesResponse.model_validate(response_dict)


@router.get("/{tenant_id}/features/audit", response_model=list[AuditLogResponse])
async def get_tenant_features_audit(
    tenant_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[AuditLogResponse]:
    """Consulta el historial WORM de modificaciones de feature flags para una empresa."""
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value and str(user_tid) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para consultar la auditoría de esta empresa",
        )

    await set_tenant_context(db, tenant_id, is_superadmin=True)
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.event_action == "TENANT_FEATURE_FLAGS_UPDATED",
        )
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        AuditLogResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            created_at=r.created_at,
            actor_user_id=r.actor_user_id,
            actor_username=r.actor_username,
            actor_role=r.actor_role,
            actor_ip=r.actor_ip,
            actor_user_agent=getattr(r, "actor_user_agent", None),
            event_category=r.event_category,
            event_action=r.event_action,
            router_id=r.router_id,
            router_display_name=r.router_display_name,
            ros_rest_method=getattr(r, "ros_rest_method", None),
            ros_rest_endpoint=getattr(r, "ros_rest_endpoint", None),
            idempotency_key=getattr(r, "idempotency_key", None),
            status_code=r.status_code,
            before_state=r.before_state,
            after_state=r.after_state,
            error_message=getattr(r, "error_message", None),
            record_sha256_hash=r.record_sha256_hash,
            prev_record_hash=getattr(r, "prev_record_hash", None) or "GENESIS",
        )
        for r in records
    ]


@router.post("/{tenant_id}/onboarding-complete", response_model=TenantFeaturesResponse)
async def complete_tenant_onboarding(
    tenant_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    """Marca la configuración inicial (Onboarding Wizard) del tenant como completada."""
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value and str(user_tid) != str(tenant_id):
        raise HTTPException(status_code=403, detail="No autorizado para configurar esta empresa")

    tenant = await _load_tenant_or_404(db, tenant_id)
    try:
        redis = get_redis_client()
        await redis.set(f"rg:{tenant_id}:onboarding_completed", "true")
    except Exception as exc:
        logger.debug("Error persistiendo onboarding_completed: %s", exc)

    features = extract_tenant_features(tenant)
    features["onboarding_completed"] = True
    return TenantFeaturesResponse.model_validate(features)


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
