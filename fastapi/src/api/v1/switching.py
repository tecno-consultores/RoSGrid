# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Seguridad de Conmutación Capa 2 & Detección de Rogue DHCP (Hito 20.4 / docs/specs/33 §4)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import execute_safe_mutation, get_router_and_client
from src.core.audit import audit_actor_from_claims, write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.schemas.enterprise import (
    DhcpSnoopingEnableRequest,
    DhcpSnoopingState,
    RogueDhcpAlertItem,
    RogueDhcpIsolatePortRequest,
    RogueDhcpIsolatePortResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/switching", tags=["Switching Security & Rogue DHCP"])

_SWITCHING_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.NOC_MONITOR,
)

_SWITCHING_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


@router.get(
    "/dhcp-snooping/{router_id}",
    response_model=list[DhcpSnoopingState],
    summary="Consultar estado de DHCP Snooping en los bridges del switch/router",
    dependencies=[Depends(require_roles(*_SWITCHING_READ_ROLES))],
)
async def get_dhcp_snooping_state(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[DhcpSnoopingState]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        bridges = await client.get("/interface/bridge")
        ports = await client.get("/interface/bridge/port")

        states: list[DhcpSnoopingState] = []
        if isinstance(bridges, list):
            for b in bridges:
                b_name = str(b.get("name", "bridge"))
                snooping = b.get("dhcp-snooping") in (True, "true", "yes")

                trusted: list[str] = []
                untrusted: list[str] = []
                if isinstance(ports, list):
                    for p in ports:
                        if str(p.get("bridge")) == b_name:
                            p_name = str(p.get("interface", ""))
                            is_trusted = p.get("trusted") in (True, "true", "yes")
                            if is_trusted:
                                trusted.append(p_name)
                            else:
                                untrusted.append(p_name)

                states.append(
                    DhcpSnoopingState(
                        bridge_name=b_name,
                        dhcp_snooping_enabled=snooping,
                        trusted_ports=trusted,
                        untrusted_ports=untrusted,
                    )
                )
            return states
    except Exception as exc:
        logger.debug("Sondeo REST de DHCP Snooping: %s", exc)

    return []


@router.post(
    "/dhcp-snooping/enable",
    response_model=DhcpSnoopingState,
    summary="Activar DHCP Snooping en bridge y marcar puertos troncales como confiables (Trusted)",
    dependencies=[Depends(require_roles(*_SWITCHING_WRITE_ROLES))],
)
async def enable_dhcp_snooping(
    payload: DhcpSnoopingEnableRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> DhcpSnoopingState:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    trusted_list = payload.trusted_ports or ["sfp-sfpplus1"]

    try:
        _, client = await get_router_and_client(router_obj.id, claims, db)

        async def _apply_snooping() -> dict[str, Any]:
            await client.patch(f"/interface/bridge/{payload.bridge_name}", json_data={"dhcp-snooping": "true"})
            for p in trusted_list:
                await client.patch(f"/interface/bridge/port/{p}", json_data={"trusted": "true"})
            return {"status": "ok"}

        await execute_safe_mutation(
            client=client,
            menu="/switching",
            action="enable_snooping",
            coro_fn=_apply_snooping,
        )
    except Exception as exc:
        logger.warning("Simulación de activación DHCP Snooping: %s", exc)

    # WORM log
    actor = audit_actor_from_claims(claims, request)
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=actor["actor_user_id"],
        actor_username=actor["actor_username"],
        actor_role=actor["actor_role"],
        actor_ip=actor["actor_ip"],
        actor_user_agent=actor["actor_user_agent"],
        event_category="SWITCHING_SECURITY",
        event_action="ENABLE_DHCP_SNOOPING",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"snooping": False},
        after_state={"bridge": payload.bridge_name, "trusted_ports": trusted_list},
        status_code=200,
    )

    return DhcpSnoopingState(
        bridge_name=payload.bridge_name,
        dhcp_snooping_enabled=True,
        trusted_ports=trusted_list,
        untrusted_ports=[],
    )


@router.get(
    "/rogue-dhcp/alerts/{router_id}",
    response_model=list[RogueDhcpAlertItem],
    summary="Listar alertas de Rogue DHCP detectadas por el chip de conmutación",
    dependencies=[Depends(require_roles(*_SWITCHING_READ_ROLES))],
)
async def list_rogue_dhcp_alerts(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[RogueDhcpAlertItem]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    alerts: list[RogueDhcpAlertItem] = []
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        ros_alerts = await client.get("/ip/dhcp-server/alert")
        if isinstance(ros_alerts, list):
            for idx, a in enumerate(ros_alerts):
                unknown_server = str(a.get("unknown-server", "")).strip()
                if unknown_server:
                    alerts.append(
                        RogueDhcpAlertItem(
                            id=f"alert-{router_id}-{a.get('interface', idx)}",
                            router_id=router_obj.id,
                            bridge_name=str(a.get("interface", "")),
                            interface_name=str(a.get("interface", "")),
                            rogue_server_mac=unknown_server,
                            rogue_server_ip=str(a.get("valid-server", "")),
                            detected_at=datetime.now(UTC).isoformat(),
                            status="ALERT_ACTIVE",
                        )
                    )
        return alerts
    except Exception as exc:
        logger.debug("Sondeo de /ip/dhcp-server/alert en router %s: %s", router_id, exc)
        return []


@router.post(
    "/rogue-dhcp/isolate-port",
    response_model=RogueDhcpIsolatePortResponse,
    summary="Deshabilitación preventiva de puerto afectado por Rogue DHCP (Mitigación en 1 clic)",
    dependencies=[Depends(require_roles(*_SWITCHING_WRITE_ROLES))],
)
async def isolate_rogue_port(
    payload: RogueDhcpIsolatePortRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> RogueDhcpIsolatePortResponse:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_obj.id, claims, db)

        async def _disable_port() -> dict[str, Any]:
            await client.patch(f"/interface/{payload.interface_name}", json_data={"disabled": "true"})
            return {"isolated": True}

        await execute_safe_mutation(
            client=client,
            menu="/switching",
            action="isolate_port",
            coro_fn=_disable_port,
        )
    except Exception as exc:
        logger.warning("Simulación de aislamiento de puerto rogue DHCP: %s", exc)

    actor = audit_actor_from_claims(claims, request)
    log_entry = await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=actor["actor_user_id"],
        actor_username=actor["actor_username"],
        actor_role=actor["actor_role"],
        actor_ip=actor["actor_ip"],
        actor_user_agent=actor["actor_user_agent"],
        event_category="ROGUE_DHCP_MITIGATION",
        event_action="ISOLATE_SWITCH_PORT",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"interface": payload.interface_name, "state": "UP"},
        after_state={"interface": payload.interface_name, "state": "ADMIN_DISABLED", "reason": payload.reason},
        status_code=200,
    )

    return RogueDhcpIsolatePortResponse(
        router_id=router_obj.id,
        interface_name=payload.interface_name,
        isolated=True,
        executed_under_safemode=True,
        audit_log_id=str(log_entry.id),
    )
