# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.db.session import get_tenant_db_session
from src.models.core import Tenant
from src.models.inventory import Router
from src.redis_layer.client import get_redis_client
from src.schemas.cve import CveSyncResponse, FleetCveSummary, RouterCveEvaluation
from src.services.cve_matcher import (
    evaluate_fleet_cves,
    evaluate_router_cves,
    sync_cve_catalog,
)

logger = logging.getLogger(__name__)

CVE_SYNC_META_KEY = "rg:cve:sync_meta"
CVE_CACHE_TTL_SECONDS = 86400  # 24 horas de vigencia de caché

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
    """Descarga y sincroniza manualmente el catálogo de firmas CVE, renovando la vigencia del caché de 24 horas."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_cve_feature(tenant)

    sync_res = await sync_cve_catalog()

    # Renovar validez del caché de 24 horas en KeyDB
    try:
        redis = get_redis_client()
        meta = {
            "last_sync": sync_res.updated_at.isoformat(),
            "total_cves": sync_res.total_cves,
            "source_url": sync_res.source_url,
        }
        await redis.set(CVE_SYNC_META_KEY, json.dumps(meta), ex=CVE_CACHE_TTL_SECONDS)
    except Exception as exc:
        logger.warning("Fallo al actualizar TTL de KeyDB en sync manual: %s", exc)

    return sync_res


@router.get("", response_model=FleetCveSummary)
async def get_fleet_cves_summary(
    auto_sync: bool = Query(True, description="Sincronizar automáticamente si el caché de 24 horas ha expirado"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> FleetCveSummary:
    """Evalúa la totalidad de routers adoptados contra el catálogo local de CVEs con caché de 24 horas en KeyDB."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_cve_feature(tenant)

    # 1. Comprobar vigencia del caché de sincronización en KeyDB (24 horas)
    cache_raw = None
    ttl_remaining: int | None = None
    try:
        redis = get_redis_client()
        cache_raw = await redis.get(CVE_SYNC_META_KEY)
        if cache_raw:
            raw_ttl = await redis.ttl(CVE_SYNC_META_KEY)
            ttl_remaining = max(0, raw_ttl) if raw_ttl is not None and raw_ttl >= 0 else None
    except Exception as exc:
        logger.warning("Fallo al consultar KeyDB para caché CVE: %s", exc)

    now_utc = datetime.now(timezone.utc)
    auto_synced = False
    last_synced_at: datetime | None = None
    cache_expires_at: datetime | None = None

    if (not cache_raw or ttl_remaining is None or ttl_remaining <= 0) and auto_sync:
        # Primera vez en el día o caché expirado (> 24 horas): sincronización automática
        logger.info("Caché de CVE inexistente o expirado. Ejecutando sincronización automática...")
        sync_res = await sync_cve_catalog()
        auto_synced = True
        last_synced_at = sync_res.updated_at
        cache_expires_at = last_synced_at + timedelta(seconds=CVE_CACHE_TTL_SECONDS)
        ttl_remaining = CVE_CACHE_TTL_SECONDS
        try:
            redis = get_redis_client()
            meta = {
                "last_sync": last_synced_at.isoformat(),
                "total_cves": sync_res.total_cves,
                "source_url": sync_res.source_url,
            }
            await redis.set(CVE_SYNC_META_KEY, json.dumps(meta), ex=CVE_CACHE_TTL_SECONDS)
        except Exception as exc:
            logger.warning("Fallo al persistir caché CVE en KeyDB tras autosync: %s", exc)
    elif cache_raw:
        # Caché vigente: se reutiliza sin descargas remotas
        try:
            meta = json.loads(cache_raw)
            sync_str = meta.get("last_sync")
            if sync_str:
                last_synced_at = datetime.fromisoformat(sync_str)
                cache_expires_at = last_synced_at + timedelta(seconds=CVE_CACHE_TTL_SECONDS)
        except Exception as exc:
            logger.warning("Error al deserializar metadatos de caché CVE: %s", exc)
            last_synced_at = now_utc
            cache_expires_at = now_utc + timedelta(seconds=CVE_CACHE_TTL_SECONDS)

    query = select(Router.id, Router.display_name, Router.ros_version).where(Router.tenant_id == tenant_id)
    result = await db.execute(query)
    rows = result.all()

    routers_data = [{"id": row[0], "display_name": row[1], "ros_version": row[2]} for row in rows]

    return evaluate_fleet_cves(
        routers_data=routers_data,
        last_synced_at=last_synced_at,
        cache_expires_at=cache_expires_at,
        cache_ttl_seconds=ttl_remaining,
        is_cache_fresh=(cache_raw is not None or auto_synced),
        auto_synced=auto_synced,
    )


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
