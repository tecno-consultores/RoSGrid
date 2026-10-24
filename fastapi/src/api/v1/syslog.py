# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.core.config import settings
from src.db.session import get_tenant_db_session
from src.models.core import Tenant
from src.models.inventory import Router
from src.schemas.syslog import RouterSyslogResponse, SyslogTemplateResponse
from src.workers.syslog_collector import get_router_syslog_events

router = APIRouter(prefix="/routers", tags=["Router Syslog"])

ROUTEROS_SYSLOG_TEMPLATE = """# ==============================================================================
# RoSGrid: Plantilla de Enrolamiento Syslog Remoto Efímero (RouterOS v7)
# Variables requeridas: {{ROSGRID_SERVER_IP}}, {{ROSGRID_SYSLOG_PORT}}
# ==============================================================================

/system logging action
remove [find name="rosgridsyslog"]
add name="rosgridsyslog" target=remote remote={{ROSGRID_SERVER_IP}} remote-port={{ROSGRID_SYSLOG_PORT}} remote-log-format=syslog syslog-facility=daemon

/system logging
remove [find action="rosgridsyslog"]
add topics=interface,warning,critical action="rosgridsyslog"
add topics=route,bgp,warning action="rosgridsyslog"
add topics=route,ospf,warning action="rosgridsyslog"
add topics=system,error,critical action="rosgridsyslog"
add topics=dhcp,critical action="rosgridsyslog"
add topics=firewall,warning action="rosgridsyslog"
"""


def _check_syslog_feature(tenant: Tenant) -> None:
    if not getattr(tenant, "syslog_collector_enabled", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_MODULE_DISABLED",
                "message": "El receptor centralizado de Syslog no está habilitado para esta organización.",
            },
        )


@router.get("/syslog/template", response_model=SyslogTemplateResponse)
async def get_syslog_provisioning_template(
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> SyslogTemplateResponse:
    """Retorna la plantilla RouterOS v7 para configurar el envío de Syslog remoto hacia RoSGrid."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_syslog_feature(tenant)

    return SyslogTemplateResponse(
        template_content=ROUTEROS_SYSLOG_TEMPLATE,
        default_port=getattr(settings, "ROSGRID_SYSLOG_PORT", 5514),
        protocol="UDP",
        instructions=(
            "Copy and paste this script into RouterOS v7 terminal or apply it "
            "using Bulk Operations under Safe Mode."
        ),
        instructions_es=(
            "Copie y ejecute este script en la terminal de RouterOS v7 o aplíquelo "
            "de forma masiva mediante el módulo de Operaciones Masivas (Bulk Ops) bajo Safe Mode."
        ),
    )


@router.get("/{router_id}/syslog", response_model=RouterSyslogResponse)
async def get_router_syslog(
    router_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=500, description="Cantidad máxima de eventos recientes"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterSyslogResponse:
    """Recupera los últimos N eventos Syslog registrados en la memoria volátil de KeyDB para el router."""
    tenant_id = uuid.UUID(claims["tid"])
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    _check_syslog_feature(tenant)

    query = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ROUTER_NOT_FOUND", "message": "El router especificado no existe."},
        )

    events = await get_router_syslog_events(tenant_id, router_id, limit=limit)
    crit_count = sum(1 for e in events if e.is_critical)

    return RouterSyslogResponse(
        router_id=router_id,
        total_in_buffer=len(events),
        total_events=len(events),
        critical_count=crit_count,
        events=events,
    )
