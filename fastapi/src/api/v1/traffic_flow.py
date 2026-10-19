# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Detección de Tráfico Anómalo y Mitigación Rápida con Safe Mode (Hito 18.3)."""

import collections
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_feature, require_roles
from src.api.v1.webfig_common import execute_safe_mutation, get_router_and_client
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.schemas.traffic_flow import (
    TrafficAnomaliesResponse,
    TrafficAnomalyItem,
    TrafficMitigationRequest,
    TrafficMitigationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/traffic-flow",
    tags=["Traffic Flow & Anomalies"],
    dependencies=[Depends(require_feature("ipfix_analytics_enabled"))],
)

_TRAFFIC_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.NOC_MONITOR,
)

_TRAFFIC_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L3,
)


def _extract_ip_from_address(addr_str: str) -> str:
    """Extrae la dirección IP pura eliminando puertos y máscaras."""
    clean = addr_str.strip()
    if ":" in clean and "." in clean:
        clean = clean.split(":")[0]
    return clean


def _evaluate_anomaly_severity(cnt: int, pps: int, threshold_pps: int, protocols: list[str]) -> tuple[str, str]:
    """Determina tipo y severidad del patrón anómalo detectado."""
    if cnt > 1000 or pps > (threshold_pps * 2):
        atype = "POSSIBLE_SYN_FLOOD" if "tcp" in protocols else "HIGH_PPS_BURST"
        return atype, "CRITICAL"
    if pps >= threshold_pps:
        return "HIGH_PPS_BURST", "HIGH"
    return "HIGH_CONNECTION_COUNT", "HIGH"


def _aggregate_connection_stats(conns_list: list[Any]) -> dict[str, dict[str, Any]]:
    """Agrupa conexiones por dirección IP de origen."""
    ip_stats: dict[str, dict[str, Any]] = collections.defaultdict(lambda: {"count": 0, "pps": 0, "protocols": set()})
    for item in conns_list:
        if not isinstance(item, dict):
            continue
        src = str(item.get("src-address", ""))
        if not src:
            continue
        ip = _extract_ip_from_address(src)
        proto = str(item.get("protocol", "tcp")).lower()
        raw_pkts = item.get("orig-packets") or item.get("packets") or 1
        try:
            orig_packets = int(raw_pkts)
        except (ValueError, TypeError):
            orig_packets = 1

        stats = ip_stats[ip]
        stats["count"] += 1
        stats["pps"] += max(1, orig_packets // 10)
        stats["protocols"].add(proto)
    return ip_stats


def _analyze_connections(
    raw_conns: Any,
    threshold_pps: int,
    threshold_conns: int,
) -> list[TrafficAnomalyItem]:
    """Agrupa conexiones de Firewall / IPFIX y detecta patrones de abuso o DDoS."""
    conns_list = raw_conns if isinstance(raw_conns, list) else []
    ip_stats = _aggregate_connection_stats(conns_list)

    anomalies: list[TrafficAnomalyItem] = []
    for ip, data in ip_stats.items():
        cnt = data["count"]
        pps = data["pps"]
        if cnt < threshold_conns and pps < threshold_pps:
            continue
        protocols = sorted(list(data["protocols"]))
        atype, severity = _evaluate_anomaly_severity(cnt, pps, threshold_pps, protocols)
        anomalies.append(
            TrafficAnomalyItem(
                ip_address=ip,
                connection_count=cnt,
                estimated_pps=pps,
                protocols=protocols,
                anomaly_type=atype,
                severity=severity,
            )
        )

    anomalies.sort(key=lambda a: (a.connection_count, a.estimated_pps), reverse=True)
    return anomalies


@router.get("/anomalies", response_model=TrafficAnomaliesResponse)
async def detect_traffic_anomalies(
    router_id: uuid.UUID = Query(..., description="ID del router a escanear"),
    threshold_pps: int = Query(default=1000, ge=100, le=1000000, description="Umbral de paquetes por segundo"),
    threshold_conns: int = Query(default=500, ge=50, le=100000, description="Umbral de conexiones concurrentes"),
    claims: dict[str, Any] = Depends(require_roles(*_TRAFFIC_READ_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> TrafficAnomaliesResponse:
    """Escanea la tabla de conexiones de RouterOS para identificar hosts maliciosos o saturación."""
    _, client = await get_router_and_client(router_id, claims, db)

    async with client:
        raw_conns = await client.get("/ip/firewall/connection")

    items = _analyze_connections(raw_conns, threshold_pps, threshold_conns)
    return TrafficAnomaliesResponse(
        router_id=router_id,
        threshold_pps=threshold_pps,
        threshold_conns=threshold_conns,
        anomalies_detected=len(items),
        items=items,
    )


@router.post("/mitigate", response_model=TrafficMitigationResponse, status_code=status.HTTP_200_OK)
async def mitigate_traffic_anomaly(
    payload: TrafficMitigationRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_TRAFFIC_WRITE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> TrafficMitigationResponse:
    """Aplica mitigación FastDrop o Blackhole en el MikroTik bajo Safe Mode con auditoría inmutable."""
    router_obj, client = await get_router_and_client(payload.router_id, claims, db)
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    actor_username = claims.get("username", claims.get("sub", ""))
    actor_role = claims.get("rol", SystemRoleEnum.SUPPORT_L2)
    actor_ip = request.client.host if request.client else "127.0.0.1"

    rule_id = f"mitig-{uuid.uuid4().hex[:8]}"

    async with client:
        if payload.action == "fast_drop":
            body = {
                "list": "BLACKHOLE_MITIGATION",
                "address": payload.target_ip,
                "timeout": f"{payload.duration_seconds}s",
                "comment": payload.comment,
            }
            await execute_safe_mutation(
                client=client,
                menu="ip/firewall/address-list",
                action="create",
                before_state=body,
                coro_fn=lambda: client.put("/ip/firewall/address-list", json_data=body),
            )
        else:
            # Blackhole route en /ip/route
            route_body = {
                "dst-address": f"{payload.target_ip}/32",
                "type": "blackhole",
                "comment": payload.comment,
            }
            await execute_safe_mutation(
                client=client,
                menu="ip/route",
                action="create",
                before_state=route_body,
                coro_fn=lambda: client.put("/ip/route", json_data=route_body),
            )

    # Registro forense inmutable en PostgreSQL WORM
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=actor_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        actor_user_agent=request.headers.get("User-Agent"),
        event_category="SECURITY",
        event_action="TRAFFIC_ANOMALY_MITIGATED",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"target_ip": payload.target_ip, "action": payload.action},
        after_state={"status": "APPLIED", "rule_id": rule_id, "duration": payload.duration_seconds},
    )
    await db.commit()

    return TrafficMitigationResponse(
        status="MITIGATED",
        router_id=payload.router_id,
        target_ip=payload.target_ip,
        action_taken=payload.action,
        rule_or_list_id=rule_id,
        safemode_applied=True,
        audit_event="TRAFFIC_ANOMALY_MITIGATED",
    )
