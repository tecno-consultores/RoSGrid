# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.db.session import get_tenant_db_session
from src.models.core import Tenant
from src.models.inventory import Router
from src.schemas.cve import CveSyncResponse, FleetCveSummary, RouterCveEvaluation
from src.services.cve_matcher import (
    evaluate_fleet_cves,
    evaluate_router_cves,
    sync_cve_catalog,
)

router = APIRouter(prefix="/inventory/cves", tags=["CVE Vulnerabilities"])


def _check_cve_feature(tenant: Tenant) -> None:
    if not getattr(tenant, "cve_scanner_enabled", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_MODULE_DISABLED",
                "message": "El escáner de vulnerabilidades CVE no está habilitado para esta organización.",
            },
        )


@router.post("/sync", response_model=CveSyncResponse)
async def sync_cve_database(
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> CveSyncResponse:
    """Descarga y sincroniza la última base de datos de firmas CVE para MikroTik RouterOS v7."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_cve_feature(tenant)
    return await sync_cve_catalog()


@router.get("", response_model=FleetCveSummary)
async def get_fleet_cves_summary(
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> FleetCveSummary:
    """Evalúa la totalidad de routers adoptados en la organización contra el catálogo local de CVEs."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_cve_feature(tenant)

    query = select(Router.id, Router.display_name, Router.ros_version).where(Router.tenant_id == tenant_id)
    result = await db.execute(query)
    rows = result.all()

    routers_data = [{"id": row[0], "display_name": row[1], "ros_version": row[2]} for row in rows]

    return evaluate_fleet_cves(routers_data)


@router.get("/routers/{router_id}", response_model=RouterCveEvaluation)
async def get_router_cves(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterCveEvaluation:
    """Evalúa las vulnerabilidades CVE que afectan a un router específico según su versión de RouterOS."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_cve_feature(tenant)

    query = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    result = await db.execute(query)
    target_router = result.scalar_one_or_none()

    if not target_router:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ROUTER_NOT_FOUND", "message": "El router especificado no existe."},
        )

    return evaluate_router_cves(
        router_id=target_router.id,
        display_name=target_router.display_name,
        ros_version=target_router.ros_version,
    )
