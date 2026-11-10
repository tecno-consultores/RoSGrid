# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import logging
import uuid
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.audit import serialize_audit_log_record
from src.core.audit import audit_actor_from_claims, write_audit_log
from src.core.crypto import hash_password
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.models.inventory import Router
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


async def _load_tenant_or_404(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    await set_tenant_context(db, None, is_superadmin=True)
    res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


async def _populate_tenant_counts(db: AsyncSession, tenants: list[Tenant]) -> None:
    """Enriquece cada Tenant con el conteo real de routers y usuarios activos (CC = 4)."""
    if not tenants or not isinstance(db, AsyncSession):
        return
    try:
        r_res = await db.execute(select(Router.tenant_id, func.count(Router.id)).group_by(Router.tenant_id))
        r_counts = {row[0]: int(row[1]) for row in r_res.all()}
        u_res = await db.execute(select(User.tenant_id, func.count(User.id)).group_by(User.tenant_id))
        u_counts = {row[0]: int(row[1]) for row in u_res.all()}
        for t in tenants:
            t.active_routers_count = r_counts.get(t.id, 0)  # type: ignore[attr-defined]
            t.active_users_count = u_counts.get(t.id, 0)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.debug("Conteo de cuotas de tenant omitido: %s", exc)


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TenantResponse]:
    user_role = claims.get("rol")
    if user_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        await set_tenant_context(db, None, is_superadmin=True)
        stmt = select(Tenant).order_by(Tenant.created_at.desc(), Tenant.id.desc())  # seq_num aplica a AuditLog WORM
    else:
        user_tid = claims.get("tid")
        if not user_tid:
            raise HTTPException(status_code=403, detail="Contexto de empresa no disponible")
        await set_tenant_context(db, uuid.UUID(str(user_tid)), is_superadmin=False)
        stmt = select(Tenant).where(Tenant.id == uuid.UUID(str(user_tid)))
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    await _populate_tenant_counts(db, items)
    return [TenantResponse.model_validate(t) for t in items]


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

    tenant = await _load_tenant_or_404(db, tenant_id)
    await _populate_tenant_counts(db, [tenant])
    return TenantResponse.model_validate(tenant)


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
    if not features_dict.get("onboarding_completed"):
        try:
            redis = get_redis_client()
            onb_val = await redis.get(f"rg:{tenant_id}:onboarding_completed")
            if onb_val:
                is_done = (onb_val.decode() if isinstance(onb_val, bytes) else str(onb_val)).lower() == "true"
                features_dict["onboarding_completed"] = is_done
                if is_done and not getattr(tenant, "onboarding_completed", False):
                    tenant.onboarding_completed = True
                    await db.commit()
        except Exception as exc:
            logger.debug("Error leyendo onboarding_completed de KeyDB: %s", exc)
    return TenantFeaturesResponse.model_validate(features_dict)


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
@router.put("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    tenant = await _load_tenant_or_404(db, tenant_id)

    is_superadmin = user_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    is_initial_tenant_onboarding = (
        user_role == SystemRoleEnum.TENANT_ADMIN.value
        and str(user_tid) == str(tenant_id)
        and not bool(getattr(tenant, "onboarding_completed", False))
        and body.onboarding_completed is True
    )
    if not is_superadmin and not is_initial_tenant_onboarding:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol SUPERADMIN_GLOBAL pueden modificar los módulos y licencias de las empresas.",
        )

    before_state = extract_tenant_features(tenant)

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)

    # Persistencia duradera de onboarding_completed en PostgreSQL (Spec 69) + espejo en KeyDB
    onboarding_completed_val: bool = bool(update_data.get("onboarding_completed", True))
    update_data["onboarding_completed"] = onboarding_completed_val
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
    response_dict["onboarding_completed"] = bool(getattr(tenant, "onboarding_completed", onboarding_completed_val))
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
        .order_by(desc(AuditLog.seq_num), desc(AuditLog.created_at), desc(AuditLog.id))
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [serialize_audit_log_record(r) for r in records]


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
    tenant.onboarding_completed = True
    await db.commit()
    await db.refresh(tenant)
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
    hq_lat = body.hq_latitude if body.hq_latitude is not None else 10.480600
    hq_lng = body.hq_longitude if body.hq_longitude is not None else -66.903600
    new_tenant = Tenant(
        slug=body.slug,
        name=body.name,
        status=TenantStatusEnum.ACTIVE,
        tax_id=body.tax_id,
        max_routers_quota=body.max_routers_quota,
        max_users_quota=body.max_users_quota,
        require_2fa_all_users=body.require_2fa_all_users,
        default_safemode_seconds=body.default_safemode_seconds,
        hq_latitude=hq_lat,
        hq_longitude=hq_lng,
    )
    db.add(new_tenant)
    await db.flush()

    # 3. Crear Administrador Inicial del Tenant
    admin_user = User(
        tenant_id=new_tenant.id,
        username=body.admin_username,
        email=body.admin_email,
        full_name=body.admin_full_name or body.admin_username,
        password_hash=hash_password(body.admin_password),
        role=SystemRoleEnum.TENANT_ADMIN,
        has_all_routers_access=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(new_tenant)

    return TenantResponse.model_validate(new_tenant)


async def _validate_unique_tenant_slug(db: AsyncSession, tenant: Tenant, new_slug: str) -> str:
    """Verifica que el nuevo slug no esté asignado a otra organización (CC = 4)."""
    clean_slug = new_slug.strip().lower()
    if clean_slug == tenant.slug:
        return clean_slug
    res = await db.execute(select(Tenant).where(Tenant.slug == clean_slug, Tenant.id != tenant.id))
    conflict = res.scalar_one_or_none()
    if conflict and conflict.id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una organización con el slug '{clean_slug}'",
        )
    return clean_slug


def _normalize_tenant_audit_value(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, Enum):
        return val.value
    return val


async def _apply_tenant_updates(db: AsyncSession, tenant: Tenant, update_data: dict[str, Any]) -> dict[str, Any]:
    """Aplica las modificaciones de metadatos/cuotas sobre el Tenant y retorna before_state (CC = 3)."""
    before_state = {field: _normalize_tenant_audit_value(getattr(tenant, field, None)) for field in update_data}
    if update_data.get("slug"):
        update_data["slug"] = await _validate_unique_tenant_slug(db, tenant, str(update_data["slug"]))
    for field, value in update_data.items():
        setattr(tenant, field, value)
    return before_state


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: UpdateTenantRequest,
    request: Request = None,  # type: ignore[assignment]
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    tenant = await _load_tenant_or_404(db, tenant_id)
    update_data = body.model_dump(exclude_unset=True)
    before_state = await _apply_tenant_updates(db, tenant, update_data)

    actor = audit_actor_from_claims(claims, request)
    actor["tenant_id"] = tenant.id
    await write_audit_log(
        session=db,
        **actor,
        event_category="GOVERNANCE",
        event_action="TENANT_UPDATED",
        before_state=before_state,
        after_state=update_data,
    )
    await db.commit()
    await db.refresh(tenant)
    await invalidate_tenant_features_cache(tenant_id)
    await _populate_tenant_counts(db, [tenant])
    return TenantResponse.model_validate(tenant)
