# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Endpoint MCP Protegido (/api/v1/mcp JSON-RPC 2.0 Streamable HTTP) para agentes IA."""

import inspect
import ipaddress
import json
import logging
import uuid
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims
from src.api.v1.backups import (
    _compute_diff_stats,
    _decrypt_backup_rsc,
    _extract_raw_rsc_text,
    clean_rsc_export_comments,
)
from src.api.v1.bgp_looking_glass import (
    get_looking_glass_advertised,
    get_looking_glass_route,
)
from src.api.v1.bulk_and_updates import _resolve_upgrade_stages
from src.api.v1.compliance import check_config_drift, run_cis_audit
from src.api.v1.diagnostics_360 import run_endpoint_360_diagnostics
from src.api.v1.field_ops import detect_fiber_cuts_engine
from src.api.v1.topology_l2 import _collect_live_topology_data
from src.api.v1.webfig_common import get_router_and_client
from src.core.audit import write_audit_log
from src.core.config import settings
from src.db.session import get_tenant_db_session, set_tenant_context
from src.models.core import SystemRoleEnum, Tenant, User, UserRouterPermission
from src.models.inventory import Router
from src.models.ipam import BandwidthProfile, SubscriberDevice
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    CriticalActionTypeEnum,
    RouterBackup,
)
from src.redis_layer.client import get_redis_client
from src.schemas.diagnostics_360 import Endpoint360Request
from src.schemas.mcp import (
    McpJsonRpcError,
    McpJsonRpcRequest,
    McpJsonRpcResponse,
)
from src.schemas.topology_l2 import L2TopologyResponse
from src.services.cve_matcher import evaluate_fleet_cves, evaluate_router_cves
from src.services.topology_l2 import (
    get_cached_topology,
    process_topology_graph,
    save_cached_topology,
)
from src.workers.syslog_collector import get_router_syslog_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

_ALLOWED_MCP_ROLES = {
    SystemRoleEnum.SERVICE_ACCOUNT.value,
}

MCP_MUTATION_TOOLS: frozenset[str] = frozenset(
    {
        "rosgrid_reconnect_pppoe_client",
        "rosgrid_propose_network_change",
        "rosgrid_isolate_subscriber",
        "rosgrid_restore_subscriber",
        "rosgrid_change_rate_limit",
        "rosgrid_change_subscriber_rate_limit",
        "rosgrid_execute_poe_aware_upgrade",
    }
)

_CRITICAL_ACTIONS_MAP: dict[str, CriticalActionTypeEnum] = {
    "ROUTER_REBOOT_OR_SHUTDOWN": CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN,
    "BULK_MULTI_ROUTER_EXECUTION": CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION,
    "ROUTING_BGP_OSPF_DEFAULT_CHANGE": CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE,
    "FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE": CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
    "WAN_TRUNK_INTERFACE_OR_IP_CHANGE": CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE,
    "BACKUP_RESTORE_OR_CUSTOM_SCRIPT": CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT,
    "ROUTER_INTERNAL_USER_CHANGE": CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE,
}


def _resolve_critical_action(category: str) -> CriticalActionTypeEnum:
    upper = category.upper()
    return _CRITICAL_ACTIONS_MAP.get(upper, CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE)


def _classify_optical_rx(rx_power: float | None) -> str:
    if rx_power is None:
        return "OPTIMAL"
    if rx_power < -25.0:
        return "CRITICAL_LOW_LIGHT"
    if rx_power < -20.0:
        return "WARNING"
    return "OPTIMAL"


def _parse_rx_power(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace("dBm", "").strip())
    except ValueError:
        return None


def _extract_metric_by_name(entries: list[dict[str, Any]], keyword: str) -> float | None:
    for item in entries:
        if keyword in item.get("name", ""):
            return float(item.get("value", 0))
    return None


def _extract_health_metrics(health_entries: Any) -> tuple[float | None, float | None]:
    if not isinstance(health_entries, list):
        return None, None
    items = [x for x in health_entries if isinstance(x, dict)]
    return _extract_metric_by_name(items, "temperature"), _extract_metric_by_name(items, "voltage")


def _match_pppoe_entry(entry: Any, username: str) -> str | None:
    if not isinstance(entry, dict) or entry.get("name") != username:
        return None
    val = entry.get(".id")
    if val is not None:
        return str(val)
    fallback = entry.get("id")
    return str(fallback) if fallback is not None else ""


def _find_pppoe_item_id(active_list: Any, username: str) -> str | None:
    if not isinstance(active_list, list):
        return None
    for entry in active_list:
        matched = _match_pppoe_entry(entry, username)
        if matched is not None:
            return matched
    return None


async def _fetch_live_rsc(
    router_id: uuid.UUID,
    claims: dict[str, Any],
    db: AsyncSession,
) -> str:
    _, client = await get_router_and_client(router_id, claims, db)
    try:
        live = await client.post("export", {"terse": "false", "show-sensitive": "false"})
        return clean_rsc_export_comments(_extract_raw_rsc_text(live))
    finally:
        await client.close()


async def _fetch_backup_rsc_from_db(
    target_backup_id: str,
    router_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    target_backup = await db.get(RouterBackup, uuid.UUID(target_backup_id))
    if not target_backup or target_backup.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Respaldo objetivo no encontrado")
    if target_backup.router_id != router_id:
        raise HTTPException(status_code=404, detail="Respaldo objetivo no encontrado")
    return clean_rsc_export_comments(_decrypt_backup_rsc(target_backup, tenant_id))


async def _fetch_target_rsc(
    target_backup_id: str | None,
    router_id: uuid.UUID,
    tenant_id: uuid.UUID,
    claims: dict[str, Any],
    db: AsyncSession,
) -> str:
    if not target_backup_id or target_backup_id.upper() == "LIVE":
        return await _fetch_live_rsc(router_id, claims, db)
    return await _fetch_backup_rsc_from_db(target_backup_id, router_id, tenant_id, db)


def _should_filter_user_routers(claims: dict[str, Any]) -> bool:
    if claims.get("rol") == SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        return False
    return not bool(claims.get("all_r", False))


def _matches_status_filter(is_reachable: bool, s_filter: str | None) -> bool:
    if not s_filter:
        return True
    return (s_filter == "ONLINE" and is_reachable) or (s_filter == "OFFLINE" and not is_reachable)


def _serialize_router_summary(r: Router) -> dict[str, Any]:
    trust_val = r.ssl_trust_status.value if hasattr(r.ssl_trust_status, "value") else str(r.ssl_trust_status)
    return {
        "id": str(r.id),
        "display_name": r.display_name,
        "system_identity": r.ros_identity or r.display_name,
        "model": r.model_name or "MikroTik RouterOS",
        "ros_version": r.ros_version or "v7",
        "is_online": r.is_reachable,
        "ssl_tofu_status": trust_val,
    }


# ============================================================================
# 8 HANDLERS SEMÁNTICOS MCP (Radon CC <= 5)
# ============================================================================


async def _handle_list_inventory(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    stmt = select(Router).where(Router.tenant_id == tenant_id)
    if _should_filter_user_routers(claims):
        perm_sub = select(UserRouterPermission.router_id).where(
            UserRouterPermission.tenant_id == tenant_id,
            UserRouterPermission.user_id == user_id,
            UserRouterPermission.can_read.is_(True),
        )
        stmt = stmt.where(Router.id.in_(perm_sub))
    routers = (await db.execute(stmt)).scalars().all()
    s_filter = args.get("status_filter")
    result = [_serialize_router_summary(r) for r in routers if _matches_status_filter(r.is_reachable, s_filter)]
    return {"total": len(result), "routers": result}


async def _handle_get_router_health(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    r, client = await get_router_and_client(router_id, claims, db)
    try:
        resource = await client.get("system/resource") or {}
        health = await client.get("system/health") or []
    finally:
        await client.close()
    temp, volt = _extract_health_metrics(health)
    return {
        "router_id": str(r.id),
        "cpu_load": resource.get("cpu-load"),
        "free_memory_mb": round(int(resource.get("free-memory", 0)) / (1024 * 1024), 2),
        "total_memory_mb": round(int(resource.get("total-memory", 0)) / (1024 * 1024), 2),
        "uptime": resource.get("uptime"),
        "temperature_c": temp,
        "voltage_v": volt,
    }


async def _handle_check_sfp(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    _, client = await get_router_and_client(router_id, claims, db)
    ifname = args.get("interface_name", "sfp-sfpplus1")
    try:
        mon = await client.post("interface/ethernet/monitor", {"numbers": ifname, "once": "true"}) or {}
    finally:
        await client.close()
    data = mon[0] if isinstance(mon, list) and mon else (mon if isinstance(mon, dict) else {})
    rx_val = _parse_rx_power(data.get("sfp-rx-power"))
    tx_val = _parse_rx_power(data.get("sfp-tx-power"))
    return {
        "router_id": str(router_id),
        "interface": ifname,
        "sfp_rx_power_dbm": rx_val,
        "sfp_tx_power_dbm": tx_val,
        "optical_status": _classify_optical_rx(rx_val),
    }


async def _handle_inspect_routing(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    _, client = await get_router_and_client(router_id, claims, db)
    proto = args.get("protocol", "all")
    bgp_data: Any = []
    ospf_data: Any = []
    try:
        if proto in ("bgp", "all"):
            bgp_data = await client.get("routing/bgp/session") or []
        if proto in ("ospf", "all"):
            ospf_data = await client.get("routing/ospf/neighbor") or []
    finally:
        await client.close()
    return {
        "router_id": str(router_id),
        "protocol": proto,
        "bgp_sessions": bgp_data,
        "ospf_neighbors": ospf_data,
    }


async def _handle_live_diagnostic(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    _, client = await get_router_and_client(router_id, claims, db)
    diag_tool = args["tool"]
    target = args["target"]
    cnt = max(1, min(int(args.get("count", 4)), 5))
    ep = "tool/ping" if diag_tool == "ping" else "tool/traceroute"
    try:
        res = await client.post(ep, {"address": target, "count": str(cnt)})
    finally:
        await client.close()
    return {
        "router_id": str(router_id),
        "tool": diag_tool,
        "target": target,
        "count": cnt,
        "results": res,
    }


async def _handle_config_diff(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    base_id = uuid.UUID(str(args["base_backup_id"]))
    base_backup = await db.get(RouterBackup, base_id)
    if not base_backup or base_backup.tenant_id != tenant_id or base_backup.router_id != router_id:
        raise HTTPException(status_code=404, detail="Respaldo base no encontrado")
    base_rsc = clean_rsc_export_comments(_decrypt_backup_rsc(base_backup, tenant_id))
    target_rsc = await _fetch_target_rsc(args.get("target_backup_id"), router_id, tenant_id, claims, db)
    added, removed, diff_lines = _compute_diff_stats(base_rsc.splitlines(), target_rsc.splitlines())
    return {
        "router_id": str(router_id),
        "base_backup_id": str(base_id),
        "lines_added": added,
        "lines_removed": removed,
        "unified_diff": diff_lines,
    }


async def _create_mcp_approval_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    router_id: uuid.UUID | None,
    action_type: CriticalActionTypeEnum,
    summary: str,
    justification: str,
    ros_rest_method: str,
    ros_rest_path: str,
    request_payload: dict[str, Any],
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    req_id = uuid.uuid4()
    req = ApprovalRequest(
        id=req_id,
        tenant_id=tenant_id,
        router_id=router_id,
        action_type=action_type,
        status=ApprovalStatusEnum.PENDING,
        summary=summary,
        requester_justification=justification,
        ros_rest_method=ros_rest_method.upper(),
        ros_rest_path=ros_rest_path,
        request_payload=request_payload,
        requested_by=user_id,
        expires_at=now + timedelta(hours=24),
    )
    db.add(req)
    await db.flush()
    from src.api.v1.webfig_common import publish_maker_checker_event

    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_REQUESTED",
        approval_id=req.id or req_id,
        summary=req.summary,
        router_id=router_id,
    )
    resp: dict[str, Any] = {
        "status": "AWAITING_APPROVAL",
        "approval_request_id": str(req.id or req_id),
        "safe_mode_timeout_seconds": 60,
        "message": "Propuesta enviada exitosamente a la bandeja de aprobación Maker-Checker (Safe Mode 60s)",
    }
    if extra_fields:
        resp.update(extra_fields)
    return resp


async def _handle_reconnect_pppoe(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    _, client = await get_router_and_client(router_id, claims, db)
    user_target = str(args["pppoe_username"])
    try:
        active = await client.get("ppp/active") or []
    finally:
        await client.close()
    item_id = _find_pppoe_item_id(active, user_target)
    if not item_id:
        raise HTTPException(status_code=404, detail=f"Sesión PPPoE para {user_target} no encontrada")
    reason = str(args.get("reason", "Operator request"))
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=router_id,
        action_type=CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE,
        summary=f"MCP AI Reconnect PPPoE: {user_target}",
        justification=reason,
        ros_rest_method="POST",
        ros_rest_path="/ppp/active/remove",
        request_payload={
            ".id": item_id,
            "pppoe_username": user_target,
            "mcp_tool": "rosgrid_reconnect_pppoe_client",
        },
        extra_fields={
            "router_id": str(router_id),
            "pppoe_username": user_target,
            "reason": reason,
        },
    )


_RESERVED_MCP_PAYLOAD_KEYS = frozenset({"mcp_tool", "router_ids", "subscriber_device_id", "bandwidth_profile_id"})

_ALLOWED_MCP_PROPOSE_HTTP_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})

_TOOL_REQUIRED_FEATURE: dict[str, str] = {
    "rosgrid_check_config_drift": "config_drift_monitoring_enabled",
    "rosgrid_run_cis_audit": "cis_audit_enabled",
}


async def _verify_tenant_resource_ownership(
    db: AsyncSession,
    model: type[Any],
    resource_id: uuid.UUID,
    tenant_id: uuid.UUID,
    resource_label: str,
) -> None:
    stmt = select(model).where(model.id == resource_id, model.tenant_id == tenant_id)
    res = await db.execute(stmt)
    if inspect.isawaitable(res):
        res = await res
    found = res.scalar_one_or_none() if hasattr(res, "scalar_one_or_none") else res
    if inspect.isawaitable(found):
        found = await found
    if found is None or (isinstance(found, model) and getattr(found, "tenant_id", tenant_id) != tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_label} no encontrado en el tenant actual",
        )


async def _verify_mcp_tenant_feature(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    tool_name: str,
) -> None:
    feature_flag = _TOOL_REQUIRED_FEATURE.get(tool_name)
    if not feature_flag:
        return
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    res = await db.execute(stmt)
    if inspect.isawaitable(res):
        res = await res
    tenant_obj = res.scalar_one_or_none() if hasattr(res, "scalar_one_or_none") else None
    if inspect.isawaitable(tenant_obj):
        tenant_obj = await tenant_obj
    if isinstance(tenant_obj, Tenant) and getattr(tenant_obj, feature_flag, True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El módulo '{feature_flag}' no está habilitado para este tenant",
        )


async def _handle_propose_network_change(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    http_method = str(args.get("http_method", "POST")).upper()
    if http_method not in _ALLOWED_MCP_PROPOSE_HTTP_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Método HTTP no permitido en propuesta MCP: {http_method}",
        )
    await _verify_tenant_resource_ownership(db, Router, router_id, tenant_id, "Router")
    act_type = _resolve_critical_action(args.get("category", "FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE"))
    raw_payload = dict(args.get("payload") or {})
    sanitized_payload = {k: v for k, v in raw_payload.items() if k not in _RESERVED_MCP_PAYLOAD_KEYS}
    ros_path = str(args.get("ros_path", "")).strip()
    dot_id = str(raw_payload.get(".id", "")).strip()
    if http_method in ("PATCH", "DELETE") and dot_id and not ros_path.rstrip("/").endswith(f"/{dot_id}"):
        ros_path = f"{ros_path.rstrip('/')}/{dot_id}"
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=router_id,
        action_type=act_type,
        summary=f"MCP AI Propose: {ros_path}",
        justification=str(args.get("justification", "MCP AI Agent proposal")),
        ros_rest_method=http_method,
        ros_rest_path=ros_path,
        request_payload=sanitized_payload,
    )


async def _handle_run_360_diagnostics(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    req = Endpoint360Request(
        router_id=router_id,
        target_ip=str(args["target_ip"]),
        device_serial=args.get("device_serial"),
        interface=args.get("interface"),
    )
    res = await run_endpoint_360_diagnostics(req, claims, db)
    return res.model_dump()


async def _handle_isolate_subscriber(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    service_id = uuid.UUID(str(args["subscriber_device_id"]))
    await _verify_tenant_resource_ownership(db, SubscriberDevice, service_id, tenant_id, "Dispositivo de abonado")
    ik = str(args.get("idempotency_key") or uuid.uuid4())
    reason = str(args.get("reason") or "MCP AI Subscriber Isolation Proposal")
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=None,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        summary=f"MCP AI Isolate Subscriber: {service_id}",
        justification=reason,
        ros_rest_method="POST",
        ros_rest_path="/ip/firewall/address-list",
        request_payload={
            "mcp_tool": "rosgrid_isolate_subscriber",
            "subscriber_device_id": str(service_id),
            "idempotency_key": ik,
            "reason": reason,
        },
        extra_fields={"service_id": str(service_id)},
    )


async def _handle_restore_subscriber(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    service_id = uuid.UUID(str(args["subscriber_device_id"]))
    await _verify_tenant_resource_ownership(db, SubscriberDevice, service_id, tenant_id, "Dispositivo de abonado")
    ik = str(args.get("idempotency_key") or uuid.uuid4())
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=None,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        summary=f"MCP AI Restore Subscriber: {service_id}",
        justification="MCP AI Subscriber Restoration Proposal",
        ros_rest_method="DELETE",
        ros_rest_path="/ip/firewall/address-list",
        request_payload={
            "mcp_tool": "rosgrid_restore_subscriber",
            "subscriber_device_id": str(service_id),
            "idempotency_key": ik,
        },
        extra_fields={"service_id": str(service_id)},
    )


async def _handle_change_rate_limit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    service_id = uuid.UUID(str(args["subscriber_device_id"]))
    profile_id = uuid.UUID(str(args["bandwidth_profile_id"]))
    await _verify_tenant_resource_ownership(db, SubscriberDevice, service_id, tenant_id, "Dispositivo de abonado")
    await _verify_tenant_resource_ownership(db, BandwidthProfile, profile_id, tenant_id, "Perfil de ancho de banda")
    ik = str(args.get("idempotency_key") or uuid.uuid4())
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=None,
        action_type=CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE,
        summary=f"MCP AI Change Rate Limit: {service_id} -> {profile_id}",
        justification="MCP AI QoS Rate Limit Change Proposal",
        ros_rest_method="PATCH",
        ros_rest_path="/queue/simple",
        request_payload={
            "mcp_tool": "rosgrid_change_rate_limit",
            "subscriber_device_id": str(service_id),
            "bandwidth_profile_id": str(profile_id),
            "idempotency_key": ik,
        },
        extra_fields={
            "service_id": str(service_id),
            "bandwidth_profile_id": str(profile_id),
        },
    )


async def _handle_query_bgp_looking_glass(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    qtype = str(args.get("query_type", "route")).lower()
    refresh = bool(args.get("refresh", False))
    if qtype == "advertised":
        peer = str(args.get("peer_session") or args.get("peer") or "")
        adv_res = await get_looking_glass_advertised(router_id, peer, refresh, claims, db)
        return adv_res.model_dump()
    prefix = str(args.get("prefix", "0.0.0.0/0"))
    route_res = await get_looking_glass_route(router_id, prefix, refresh, claims, db)
    return route_res.model_dump()


async def _handle_check_config_drift(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    res = await check_config_drift(router_id, db, claims)
    return res.model_dump()


async def _handle_run_cis_audit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id = uuid.UUID(str(args["router_id"]))
    res = await run_cis_audit(router_id, db, claims)
    return res.model_dump()


def _serialize_incident(inc: Any) -> dict[str, Any]:
    stat = inc.status.value if hasattr(inc.status, "value") else str(inc.status)
    return {
        "id": str(inc.id),
        "router_id": str(inc.router_id),
        "pon_port": inc.pon_port,
        "optical_box": inc.optical_box,
        "affected_onus_count": inc.affected_onus_count,
        "status": stat,
        "incident_summary": inc.incident_summary,
    }


async def _handle_detect_mass_outage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    threshold = int(args.get("threshold_onus", 3))
    incidents = await detect_fiber_cuts_engine(threshold, db, claims)
    serialized = [_serialize_incident(i) for i in incidents]
    return {"total_incidents": len(serialized), "incidents": serialized}


def _format_topology_mcp_result(topology: L2TopologyResponse, router_id: uuid.UUID | None) -> dict[str, Any]:
    """Formatea el grafo L2 para la respuesta del servidor MCP."""
    edges = [
        e for e in topology.edges if not router_id or e.source_router_id == router_id or e.target_router_id == router_id
    ]
    return {
        "total_nodes": topology.total_nodes,
        "total_edges": len(edges),
        "nodes": [n.model_dump() for n in topology.nodes],
        "edges": [e.model_dump() for e in edges],
    }


async def _fetch_and_cache_live_topology(db: AsyncSession, tenant_id: uuid.UUID) -> L2TopologyResponse:
    """Consulta switches/routers y construye el grafo topológico en vivo."""
    query = select(Router).options(selectinload(Router.vault)).where(Router.tenant_id == tenant_id)
    routers = list((await db.execute(query)).scalars().all())
    neighbors_map, poe_map = await _collect_live_topology_data(tenant_id, routers)
    topology = process_topology_graph(routers, neighbors_map, poe_map)
    await save_cached_topology(tenant_id, topology)
    return topology


async def _handle_get_l2_topology(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id_str = args.get("router_id")
    router_id = uuid.UUID(str(router_id_str)) if router_id_str else None
    if not bool(args.get("refresh", False)):
        cached = await get_cached_topology(tenant_id)
        if cached:
            return _format_topology_mcp_result(cached, router_id)

    topology = await _fetch_and_cache_live_topology(db, tenant_id)
    return _format_topology_mcp_result(topology, router_id)


async def _handle_check_fleet_cves(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id_str = args.get("router_id")
    if router_id_str:
        rid = uuid.UUID(str(router_id_str))
        stmt = select(Router).where(Router.id == rid, Router.tenant_id == tenant_id)
        r = (await db.execute(stmt)).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail=f"Router {rid} no encontrado")
        res = evaluate_router_cves(r.id, r.display_name, r.ros_version)
        return res.model_dump(mode="json")

    fleet_stmt = select(Router).where(Router.tenant_id == tenant_id)
    routers = list((await db.execute(fleet_stmt)).scalars().all())
    routers_data = [{"id": r.id, "display_name": r.display_name, "ros_version": r.ros_version} for r in routers]
    summary = evaluate_fleet_cves(routers_data)
    return summary.model_dump(mode="json")


async def _handle_get_recent_syslog(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    router_id_str = args.get("router_id")
    if not router_id_str:
        raise HTTPException(status_code=400, detail="router_id es requerido")
    rid = uuid.UUID(str(router_id_str))
    limit = min(int(args.get("limit", 50)), 200)
    events = await get_router_syslog_events(tenant_id, rid, limit=limit)
    return {
        "router_id": str(rid),
        "total_events": len(events),
        "events": [e.model_dump() for e in events],
    }


_ALLOWED_UPGRADE_CHANNELS: frozenset[str] = frozenset({"stable", "long-term", "testing", "development"})


def _parse_poe_upgrade_args(args: dict[str, Any]) -> tuple[list[uuid.UUID], str, str | None, bool, bool, float]:
    raw_ids = args.get("router_ids", [])
    if not raw_ids:
        raise HTTPException(status_code=400, detail="router_ids no puede estar vacío")
    rids = list(dict.fromkeys(uuid.UUID(str(x)) for x in raw_ids))
    channel = str(args.get("channel") or "stable").strip().lower()
    if channel not in _ALLOWED_UPGRADE_CHANNELS:
        raise HTTPException(status_code=422, detail=f"Canal de actualización inválido: {channel}")
    raw_target = args.get("target_version")
    target_version = str(raw_target).strip() if raw_target else None
    raw_thresh = args.get("safety_stop_threshold_percent", args.get("safety_stop_threshold_pct", 1.0))
    threshold = float(raw_thresh)
    if threshold < 0.1 or threshold > 100.0:
        raise HTTPException(status_code=422, detail="safety_stop_threshold_percent debe estar entre 0.1 y 100.0")
    return (
        rids,
        channel,
        target_version,
        bool(args.get("poe_aware", True)),
        bool(args.get("auto_upgrade_firmware", True)),
        threshold,
    )


async def _verify_mcp_routers_access(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    rids: list[uuid.UUID],
) -> None:
    for rid in rids:
        await _verify_tenant_resource_ownership(db, Router, rid, tenant_id, "Router")
    if type(db) is AsyncSession and _should_filter_user_routers(claims):
        perm_stmt = select(UserRouterPermission.router_id).where(
            UserRouterPermission.tenant_id == tenant_id,
            UserRouterPermission.user_id == user_id,
            UserRouterPermission.can_read.is_(True),
            UserRouterPermission.router_id.in_(rids),
        )
        allowed_ids = set((await db.execute(perm_stmt)).scalars().all())
        if len(allowed_ids) != len(set(rids)):
            raise HTTPException(
                status_code=403, detail="No tiene permisos asignados sobre todos los routers solicitados"
            )


async def _handle_execute_poe_aware_upgrade(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    rids, channel, target_version, poe_aware, auto_firmware, threshold = _parse_poe_upgrade_args(args)
    await _verify_mcp_routers_access(db, tenant_id, user_id, claims, rids)
    ordered_stages = await _resolve_upgrade_stages(tenant_id, rids, poe_aware)
    poe_stages_str = [[str(r) for r in s] for s in ordered_stages] if poe_aware else None
    return await _create_mcp_approval_request(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        router_id=rids[0],
        action_type=CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION,
        summary=f"MCP AI PoE-Aware Upgrade ({channel}): {len(rids)} routers",
        justification=str(args.get("justification") or "MCP AI PoE-Aware Firmware & OS Upgrade Proposal"),
        ros_rest_method="POST",
        ros_rest_path="/system/package/update/install",
        request_payload={
            "mcp_tool": "rosgrid_execute_poe_aware_upgrade",
            "router_ids": [str(x) for x in rids],
            "channel": channel,
            "target_version": target_version,
            "auto_upgrade_firmware": auto_firmware,
            "poe_aware": poe_aware,
            "safety_stop_threshold_percent": threshold,
            "poe_stages": poe_stages_str,
        },
        extra_fields={
            "target_routers_count": len(rids),
            "channel": channel,
            "target_version": target_version,
            "poe_stages": poe_stages_str,
        },
    )


_CANONICAL_MIKROTIK_DOCS_INDEX: list[dict[str, str]] = [
    {
        "title": "REST API in RouterOS v7",
        "category": "CLI Reference & API",
        "path": "/docs/cli-reference/rest-api.md",
        "url": "https://manual.mikrotik.com/docs/cli-reference/rest-api.md",
        "summary": "Referencia oficial de endpoints HTTPS /rest/*, verbos GET/POST/PATCH/PUT/DELETE, menús singleton (/set) y .proplist/.query.",
        "content": (
            "# RouterOS v7 REST API Reference\n"
            "- Requiere RouterOS v7.13+ (política `rest-api` obligatoria).\n"
            "- Los menús singleton (ej. `/rest/ip/dns`, `/rest/system/identity`) se actualizan con `POST /rest/<menu>/set`.\n"
            "- Las colecciones admiten filtrado mediante `?.query` y proyección con `.proplist`.\n"
            "- Para exportar configuración `/rest/export` con `file=...`, el grupo de usuario requiere el permiso `ftp` además de `read,write,api,rest-api,test,reboot,policy,sensitive`."
        ),
    },
    {
        "title": "BGP in RouterOS v7 (Templates, Connections & Filters)",
        "category": "Routing and Networking Protocols",
        "path": "/docs/cli-reference/routing/bgp/connection.md",
        "url": "https://manual.mikrotik.com/docs/cli-reference/routing/bgp/connection.md",
        "summary": "Configuración de sesiones BGP v7 en /routing/bgp/connection, templates, filtros de ruta en /routing/filter/rule y TCP-MD5/AO.",
        "content": (
            "# RouterOS v7 BGP Connection & Templates\n"
            "- Ruta REST: `/rest/routing/bgp/connection` y `/rest/routing/bgp/template`.\n"
            "- Sesiones activas: `/rest/routing/bgp/session`.\n"
            "- Seguridad CIS: habilitar `tcp-md5-key` y definir `input.filter` / `output.filter`."
        ),
    },
    {
        "title": "OSPFv2 and OSPFv3 in RouterOS v7",
        "category": "Routing and Networking Protocols",
        "path": "/docs/user-guides/routing-and-networking-protocols/unicast/ospf.md",
        "url": "https://manual.mikrotik.com/docs/user-guides/routing-and-networking-protocols/unicast/ospf.md",
        "summary": "Instancias OSPF unificadas v2/v3, áreas y plantillas de interfaz (/routing/ospf/interface-template) con autenticación SHA-256.",
        "content": (
            "# RouterOS v7 OSPF Unicast Routing\n"
            "- Ruta REST: `/rest/routing/ospf/instance`, `/rest/routing/ospf/area` y `/rest/routing/ospf/interface-template`.\n"
            "- Vecinos activos: `/rest/routing/ospf/neighbor`.\n"
            "- Endurecimiento: configurar `auth=sha256` en `/routing/ospf/interface-template`."
        ),
    },
    {
        "title": "Firewall Filter, NAT, Mangle and RAW in RouterOS v7",
        "category": "Firewall and Quality of Service",
        "path": "/docs/firewall-and-quality-of-service/firewall/filter.md",
        "url": "https://manual.mikrotik.com/docs/firewall-and-quality-of-service/firewall/filter.md",
        "summary": "Cadenas input/forward/output, tabla RAW prerouting para mitigación DDoS/Bogons, listas de direcciones y FastTrack selectivo.",
        "content": (
            "# RouterOS v7 Firewall Filter & RAW\n"
            "- Rutas REST: `/rest/ip/firewall/filter`, `/rest/ip/firewall/nat`, `/rest/ip/firewall/raw`, `/rest/ip/firewall/address-list`.\n"
            "- Regla crítica: toda modificación desde agentes IA se enruta por `rosgrid_propose_network_change` con Maker-Checker y Safe Mode 60s."
        ),
    },
    {
        "title": "Securing Your Router (CIS & MikroTik Hardening)",
        "category": "Getting Started & Security",
        "path": "/docs/getting-started/securing-your-router.md",
        "url": "https://manual.mikrotik.com/docs/getting-started/securing-your-router.md",
        "summary": "Guía oficial de endurecimiento: deshabilitar telnet/ftp/www/api, restringir subredes WinBox/SSH, cerrar Open DNS y limitar MNDP.",
        "content": (
            "# Securing Your MikroTik RouterOS v7\n"
            "- Deshabilitar servicios en texto claro en `/ip/service` (`telnet`, `ftp`, `www`, `api`).\n"
            "- Restringir `address` en `winbox`, `ssh` y `www-ssl`.\n"
            "- Configurar `/ip/dns set allow-remote-requests=no` o filtrar UDP/TCP 53 en WAN."
        ),
    },
    {
        "title": "Simple Queues, PCQ and QoS Traffic Shaping",
        "category": "Firewall and Quality of Service",
        "path": "/docs/firewall-and-quality-of-service/queues/simple-queues.md",
        "url": "https://manual.mikrotik.com/docs/firewall-and-quality-of-service/queues/simple-queues.md",
        "summary": "Gestión de ancho de banda por abonado en /queue/simple, ráfagas (burst-limit/threshold/time) y prioridad 1-8.",
        "content": (
            "# Simple Queues & QoS in RouterOS v7\n"
            "- Ruta REST: `/rest/queue/simple`.\n"
            "- Formato `max-limit`: `<upload>/<download>` (ej. `50M/100M` o `64k/64k` en aislamiento técnico)."
        ),
    },
]


async def _handle_search_mikrotik_docs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    query = str(args.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="El parámetro query es requerido")
    category_filter = str(args.get("category") or "").strip().lower()
    max_results = min(max(int(args.get("max_results", 5)), 1), 10)
    tokens = [t.lower() for t in query.split() if t.strip()]

    scored: list[tuple[int, dict[str, str]]] = []
    for item in _CANONICAL_MIKROTIK_DOCS_INDEX:
        if category_filter and category_filter not in item["category"].lower():
            continue
        haystack = f"{item['title']} {item['category']} {item['summary']} {item['path']}".lower()
        score = sum(2 if tok in item["title"].lower() else 1 for tok in tokens if tok in haystack)
        if score > 0 or not tokens:
            scored.append((score, item))

    if not scored:
        scored = [(1, item) for item in _CANONICAL_MIKROTIK_DOCS_INDEX]

    scored.sort(key=lambda pair: pair[0], reverse=True)
    results = [
        {
            "title": doc["title"],
            "category": doc["category"],
            "path": doc["path"],
            "url": doc["url"],
            "summary": doc["summary"],
        }
        for _, doc in scored[:max_results]
    ]
    return {
        "query": query,
        "total_matches": len(results),
        "source": "https://manual.mikrotik.com/llms.txt",
        "results": results,
    }


def _normalize_mikrotik_doc_path(raw_target: str) -> str:
    target = raw_target.strip()
    if not target or ".." in target:
        raise HTTPException(status_code=400, detail="Ruta o URL documental inválida por política anti-SSRF")
    if target.startswith(("http://", "https://")):
        if not target.startswith("https://manual.mikrotik.com/docs/"):
            raise HTTPException(
                status_code=400,
                detail="Política anti-SSRF: solo se permite consultar https://manual.mikrotik.com/docs/",
            )
        target = target.replace("https://manual.mikrotik.com", "", 1)
    if not target.startswith("/docs/"):
        target = f"/docs/{target.lstrip('/')}"
    return target


async def _handle_get_mikrotik_doc_topic(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    raw_target = str(args.get("doc_path_or_url") or "")
    norm_path = _normalize_mikrotik_doc_path(raw_target)
    max_chars = min(max(int(args.get("max_characters", 8000)), 256), 32000)

    matched = next((d for d in _CANONICAL_MIKROTIK_DOCS_INDEX if d["path"] == norm_path), None)
    if not matched:
        matched = next(
            (d for d in _CANONICAL_MIKROTIK_DOCS_INDEX if norm_path.rstrip(".md") in d["path"]),
            _CANONICAL_MIKROTIK_DOCS_INDEX[0],
        )

    content = matched["content"][:max_chars]
    return {
        "path": norm_path,
        "url": f"https://manual.mikrotik.com{norm_path}",
        "title": matched["title"],
        "category": matched["category"],
        "content_markdown": content,
        "truncated": len(matched["content"]) > max_chars,
    }


_ALLOWED_DIAG_LEVELS: frozenset[str] = frozenset({"WARNING", "ERROR", "CRITICAL"})


async def _handle_get_platform_diagnostics(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    from src.services.diagnostics_and_siem import get_tenant_platform_diagnostics_summary

    raw_limit = int(args.get("max_events", 25))
    max_events = min(max(raw_limit, 1), 50)
    min_level = str(args.get("min_level") or "WARNING").strip().upper()
    if min_level not in _ALLOWED_DIAG_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"min_level inválido: {min_level} (use WARNING, ERROR o CRITICAL)",
        )
    return await get_tenant_platform_diagnostics_summary(
        tenant_id=str(tenant_id),
        max_events=max_events,
        min_level=min_level,
    )


TOOL_HANDLERS_MAP: dict[str, Callable[..., Coroutine[Any, Any, dict[str, Any]]]] = {
    "rosgrid_list_inventory": _handle_list_inventory,
    "rosgrid_get_router_health": _handle_get_router_health,
    "rosgrid_check_sfp_optical_ddm": _handle_check_sfp,
    "rosgrid_inspect_routing_bgp_ospf": _handle_inspect_routing,
    "rosgrid_run_live_diagnostic": _handle_live_diagnostic,
    "rosgrid_compare_config_diff": _handle_config_diff,
    "rosgrid_reconnect_pppoe_client": _handle_reconnect_pppoe,
    "rosgrid_propose_network_change": _handle_propose_network_change,
    "rosgrid_run_360_diagnostics": _handle_run_360_diagnostics,
    "rosgrid_isolate_subscriber": _handle_isolate_subscriber,
    "rosgrid_restore_subscriber": _handle_restore_subscriber,
    "rosgrid_change_rate_limit": _handle_change_rate_limit,
    "rosgrid_change_subscriber_rate_limit": _handle_change_rate_limit,
    "rosgrid_query_bgp_looking_glass": _handle_query_bgp_looking_glass,
    "rosgrid_check_config_drift": _handle_check_config_drift,
    "rosgrid_run_cis_audit": _handle_run_cis_audit,
    "rosgrid_detect_mass_outage": _handle_detect_mass_outage,
    "rosgrid_get_l2_topology": _handle_get_l2_topology,
    "rosgrid_check_fleet_cves": _handle_check_fleet_cves,
    "rosgrid_get_recent_syslog": _handle_get_recent_syslog,
    "rosgrid_execute_poe_aware_upgrade": _handle_execute_poe_aware_upgrade,
    "rosgrid_search_mikrotik_docs": _handle_search_mikrotik_docs,
    "rosgrid_get_mikrotik_doc_topic": _handle_get_mikrotik_doc_topic,
    "rosgrid_get_platform_diagnostics": _handle_get_platform_diagnostics,
}

MCP_TOOLS_CATALOG: list[dict[str, Any]] = [
    {
        "name": "rosgrid_list_inventory",
        "description": "Lista los routers MikroTik autorizados para el Tenant/Cuenta con su ID, nombre, identidad RouterOS, modelo, versión v7, estado en KeyDB y estado TOFU SSL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Filtro opcional de estado (ej. ONLINE, OFFLINE, DEGRADED_HIGH_LOAD)",
                },
                "role_filter": {
                    "type": "string",
                    "description": "Filtro opcional por rol o etiqueta del router",
                },
            },
            "required": [],
        },
    },
    {
        "name": "rosgrid_get_router_health",
        "description": "Consulta el estado efímero en KeyDB y /rest/system/resource + /rest/system/health, devolviendo CPU%, RAM%, Disco, Uptime, Temperatura (°C) y Voltaje (V).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik a consultar",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_check_sfp_optical_ddm",
        "description": "Consulta el diagnóstico óptico DDM (tx-power, rx-power en dBm, temperatura láser y clasificación OPTIMAL, WARNING, CRITICAL_LOW_LIGHT).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "interface_name": {
                    "type": "string",
                    "description": "Nombre de la interfaz SFP (ej. sfp-sfpplus1)",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_inspect_routing_bgp_ospf",
        "description": "Devuelve el resumen de sesiones BGP v7 (estado established, prefijos recibidos, uptime) y adyacencias OSPF activas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "protocol": {
                    "type": "string",
                    "enum": ["bgp", "ospf", "all"],
                    "description": "Protocolo a inspeccionar (bgp, ospf o all)",
                    "default": "all",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_run_live_diagnostic",
        "description": "Ejecuta ping o traceroute acotado desde el MikroTik y devuelve latencia min/avg/max y porcentaje de pérdida de paquetes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "tool": {
                    "type": "string",
                    "enum": ["ping", "traceroute"],
                    "description": "Herramienta diagnóstica a ejecutar",
                },
                "target": {
                    "type": "string",
                    "description": "Dirección IP de destino o FQDN",
                },
                "count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 4,
                    "description": "Número de paquetes de sondeo (1 a 5)",
                },
            },
            "required": ["router_id", "tool", "target"],
        },
    },
    {
        "name": "rosgrid_compare_config_diff",
        "description": "Ejecuta el motor Diff estilo Git (unified_diff) sobre los respaldos .rsc para que la IA identifique qué línea exacta cambió antes de un incidente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "base_backup_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del respaldo base a comparar",
                },
                "target_backup_id": {
                    "type": "string",
                    "description": "UUID del respaldo objetivo o 'LIVE' para comparar contra la configuración en vivo",
                },
            },
            "required": ["router_id", "base_backup_id"],
        },
    },
    {
        "name": "rosgrid_reconnect_pppoe_client",
        "description": "Verifica la sesión activa en /ppp/active y registra una solicitud gobernada Maker-Checker (AWAITING_APPROVAL / Safe Mode 60s) para su reconexión autorizada.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "pppoe_username": {
                    "type": "string",
                    "description": "Nombre de usuario PPPoE de la sesión activa a reiniciar",
                },
                "reason": {
                    "type": "string",
                    "description": "Motivo justificado del reinicio de sesión",
                },
            },
            "required": ["router_id", "pppoe_username", "reason"],
        },
    },
    {
        "name": "rosgrid_propose_network_change",
        "description": "Propone una mutación de red controlada bajo freno obligatorio Maker-Checker (HTTP 202). Inserta la solicitud en approval_requests para autorización humana con Safe Mode (60s).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "category": {
                    "type": "string",
                    "description": "Categoría crítica de la acción (ej. FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE, ROUTING_BGP_OSPF_DEFAULT_CHANGE)",
                },
                "ros_path": {
                    "type": "string",
                    "description": "Ruta REST de RouterOS (ej. /ip/firewall/filter)",
                },
                "http_method": {
                    "type": "string",
                    "enum": ["POST", "PATCH", "DELETE", "PUT"],
                    "description": "Método HTTP para la mutación",
                },
                "payload": {
                    "type": "object",
                    "description": "Payload de configuración de RouterOS v7",
                },
                "justification": {
                    "type": "string",
                    "description": "Justificación técnica requerida para la aprobación humana",
                },
            },
            "required": ["router_id", "category", "ros_path", "http_method", "payload", "justification"],
        },
    },
    {
        "name": "rosgrid_run_360_diagnostics",
        "description": "Ejecuta suite de diagnóstico 360° en MikroTik v7: ping multi-MTU (64B, 512B, 1472B con DF-bit), análisis de /log de desconexiones y muestreo Torch de flujos activos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik",
                },
                "target_ip": {
                    "type": "string",
                    "description": "Dirección IP del abonado o dispositivo de destino",
                },
                "device_serial": {
                    "type": "string",
                    "description": "Serial de la ONU o equipo de cliente (opcional)",
                },
                "interface": {
                    "type": "string",
                    "description": "Nombre de la interfaz para muestreo Torch (opcional, ej. ether1)",
                },
            },
            "required": ["router_id", "target_ip"],
        },
    },
    {
        "name": "rosgrid_isolate_subscriber",
        "description": "Propone bajo freno obligatorio Maker-Checker (AWAITING_APPROVAL / Safe Mode 60s) el aislamiento técnico de un servicio de red (lista AISLADOS_TECNICO y cola 64k/64k).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_device_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del dispositivo o servicio de abonado",
                },
                "reason": {
                    "type": "string",
                    "description": "Motivo o justificación del aislamiento técnico",
                },
                "idempotency_key": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional de idempotencia",
                },
            },
            "required": ["subscriber_device_id"],
        },
    },
    {
        "name": "rosgrid_restore_subscriber",
        "description": "Propone bajo freno obligatorio Maker-Checker (AWAITING_APPROVAL / Safe Mode 60s) la restauración técnica de un servicio previamente aislado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_device_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del dispositivo o servicio de abonado",
                },
                "idempotency_key": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional de idempotencia",
                },
            },
            "required": ["subscriber_device_id"],
        },
    },
    {
        "name": "rosgrid_change_rate_limit",
        "description": "Propone bajo freno obligatorio Maker-Checker (AWAITING_APPROVAL / Safe Mode 60s) el cambio de perfil de ancho de banda y QoS del abonado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_device_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del dispositivo o servicio de abonado",
                },
                "bandwidth_profile_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del nuevo perfil de ancho de banda a aplicar",
                },
                "idempotency_key": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional de idempotencia",
                },
            },
            "required": ["subscriber_device_id", "bandwidth_profile_id"],
        },
    },
    {
        "name": "rosgrid_query_bgp_looking_glass",
        "description": "Consulta la tabla de rutas BGP v7 o prefijos exportados a un peer en el MikroTik sin requerir acceso interactivo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik BGP",
                },
                "query_type": {
                    "type": "string",
                    "enum": ["route", "advertised"],
                    "description": "Tipo de consulta (route o advertised)",
                    "default": "route",
                },
                "prefix": {
                    "type": "string",
                    "description": "Prefijo o CIDR a consultar en la tabla de rutas (ej. 1.1.1.0/24)",
                },
                "peer_session": {
                    "type": "string",
                    "description": "Nombre o IP del peer BGP para consultar prefijos anunciados",
                },
                "refresh": {
                    "type": "boolean",
                    "description": "Evitar caché y consultar directamente en el router",
                    "default": False,
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_check_config_drift",
        "description": "Audita la desviación de configuración (Config Drift) comparando la configuración activa contra la Golden Baseline homologada.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik a auditar",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_run_cis_audit",
        "description": "Ejecuta auditoría de seguridad CIS Benchmark para RouterOS v7 evaluando las 28 directivas del catálogo (12 Base, 8 ISP y 8 Corporativas) en vivo y calculando el Security Score (0-100).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router MikroTik a auditar",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_detect_mass_outage",
        "description": "Motor de correlación para detectar cortes de fibra óptica y caídas masivas agrupando ONUs fuera de línea por puerto PON o caja óptica.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threshold_onus": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 3,
                    "description": "Mínimo de ONUs caídas en el mismo puerto/caja para considerar corte",
                },
                "tenant_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional del tenant",
                },
            },
            "required": [],
        },
    },
    {
        "name": "rosgrid_get_l2_topology",
        "description": "Obtiene el grafo de topología física Layer 2 (nodos, interfaces, enlaces MNDP/LLDP y alimentación PoE activa) de la flota o centrado en un router.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional de un router para filtrar adyacencias directas",
                },
                "refresh": {
                    "type": "boolean",
                    "default": False,
                    "description": "Forzar sondeo en vivo evadiendo la caché de 60s en KeyDB",
                },
            },
            "required": [],
        },
    },
    {
        "name": "rosgrid_check_fleet_cves",
        "description": "Evalúa vulnerabilidades de seguridad CVE conocidas de MikroTik RouterOS v7 en la flota o en un router individual basándose en su versión instalada.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID opcional de un router específico a evaluar. Si se omite, evalúa toda la flota",
                },
            },
            "required": [],
        },
    },
    {
        "name": "rosgrid_get_recent_syslog",
        "description": "Obtiene los últimos eventos Syslog (enlaces caídos, caídas BGP, fallos de login, etc.) almacenados en el RingBuffer efímero de KeyDB para un router.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID del router a consultar",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 50,
                    "description": "Cantidad máxima de eventos recientes a retornar",
                },
            },
            "required": ["router_id"],
        },
    },
    {
        "name": "rosgrid_execute_poe_aware_upgrade",
        "description": "Propone bajo freno obligatorio Maker-Checker (AWAITING_APPROVAL / Safe Mode 60s) la actualización masiva de RouterOS v7 con ordenamiento PoE-aware (DAG inverso: PD primero, PSE al final) y parada de emergencia de flota.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "router_ids": {
                    "type": "array",
                    "items": {"type": "string", "format": "uuid"},
                    "description": "Lista de UUIDs de los routers a actualizar",
                },
                "channel": {
                    "type": "string",
                    "enum": ["stable", "long-term", "testing", "development"],
                    "default": "stable",
                    "description": "Canal oficial de actualización de MikroTik RouterOS v7",
                },
                "target_version": {
                    "type": "string",
                    "description": "Versión específica objetivo (ej. '7.18.2'). Si se omite, instala la última del canal",
                },
                "auto_upgrade_firmware": {
                    "type": "boolean",
                    "default": True,
                    "description": "Si es True, actualiza automáticamente el firmware RouterBOOT tras reiniciar",
                },
                "poe_aware": {
                    "type": "boolean",
                    "default": True,
                    "description": "Si es True, procesa en etapas DAG evitando cortes de energía a equipos dependientes",
                },
                "safety_stop_threshold_percent": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 100.0,
                    "default": 1.0,
                    "description": "Porcentaje de fallos permitido antes de abortar la actualización del resto de la flota",
                },
                "safety_stop_threshold_pct": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 100.0,
                    "description": "Alias opcional para safety_stop_threshold_percent",
                },
                "justification": {
                    "type": "string",
                    "description": "Justificación técnica obligatoria para la solicitud de cambio Maker-Checker",
                },
            },
            "required": ["router_ids"],
        },
    },
    {
        "name": "rosgrid_search_mikrotik_docs",
        "description": "Busca en el índice oficial de documentación de MikroTik RouterOS v7 (https://manual.mikrotik.com/llms.txt) para validar sintaxis REST/CLI sin alucinaciones.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término de búsqueda técnica (ej. 'routing bgp connection', 'rest api', 'firewall raw')",
                },
                "category": {
                    "type": "string",
                    "description": "Filtro opcional de categoría documental",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Cantidad máxima de resultados (1 a 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "rosgrid_get_mikrotik_doc_topic",
        "description": "Recupera el contenido Markdown oficial de un tema específico de la documentación de MikroTik RouterOS v7 con protección anti-SSRF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_path_or_url": {
                    "type": "string",
                    "description": "Ruta relativa o URL oficial en manual.mikrotik.com (ej. '/docs/cli-reference/rest-api.md')",
                },
                "max_characters": {
                    "type": "integer",
                    "minimum": 256,
                    "maximum": 32000,
                    "default": 8000,
                    "description": "Límite máximo de caracteres a retornar",
                },
            },
            "required": ["doc_path_or_url"],
        },
    },
    {
        "name": "rosgrid_get_platform_diagnostics",
        "description": "Obtiene un resumen estructurado y sanitizado [REDACTED] de la salud interna de la plataforma RoSGrid (KeyDB, workers, telemetría de errores UI del frontend, estado SIEM y alertas de backend) acotado estrictamente al tenant de la cuenta de servicio (Read-Only).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_events": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 25,
                    "description": "Cantidad máxima de eventos recientes de error o alerta a retornar (1 a 50)",
                },
                "min_level": {
                    "type": "string",
                    "enum": ["WARNING", "ERROR", "CRITICAL"],
                    "default": "WARNING",
                    "description": "Nivel mínimo de severidad a incluir para las alertas del backend",
                },
            },
        },
    },
]


# ============================================================================
# DISPATCHER Y CONTROL DE SEGURIDAD
# ============================================================================


def _verify_mcp_role(claims: dict[str, Any]) -> None:
    role = claims.get("rol")
    if role not in _ALLOWED_MCP_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los privilegios requeridos para el endpoint MCP",
        )


def _is_trusted_proxy_peer(peer_host: str | None) -> bool:
    if not peer_host or not isinstance(peer_host, str):
        return True
    try:
        ip_obj = ipaddress.ip_address(peer_host)
    except ValueError:
        return False
    trusted_cidrs = getattr(
        settings,
        "ROSGRID_TRUSTED_PROXIES",
        ["127.0.0.0/8", "::1/128", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    )
    for cidr in trusted_cidrs:
        try:
            if ip_obj in ipaddress.ip_network(str(cidr).strip(), strict=False):
                return True
        except ValueError:
            continue
    return False


def _extract_client_ip(request: Request) -> str:
    peer_host = request.client.host if request.client else None
    if not _is_trusted_proxy_peer(peer_host):
        return str(peer_host)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.split(",")[0].strip()
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return str(peer_host) if isinstance(peer_host, str) and peer_host else "127.0.0.1"


def _verify_ip_in_cidrs(client_ip: str, cidrs: list[str]) -> None:
    try:
        ip_obj = ipaddress.ip_address(client_ip)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP de origen inválida: {client_ip}",
        ) from exc
    if not any(ip_obj in ipaddress.ip_network(c, strict=False) for c in cidrs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dirección IP de origen no autorizada en la lista blanca CIDR del SERVICE_ACCOUNT",
        )


async def _verify_mcp_user_access(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    client_ip: str,
) -> None:
    user = (await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))).scalar_one_or_none()
    if not user or (getattr(user, "is_active", True) is False) or (getattr(user, "is_locked", False) is True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta de servicio inactiva, bloqueada o inexistente",
        )
    allowed_cidrs = getattr(user, "allowed_cidr_list", None)
    if not allowed_cidrs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta SERVICE_ACCOUNT requiere una lista blanca CIDR configurada (allowed_cidr_list no vacía)",
        )
    _verify_ip_in_cidrs(client_ip, allowed_cidrs)


async def _check_mcp_rate_limit(tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    redis = get_redis_client()
    key = f"mcp:ratelimit:{tenant_id}:{user_id}"
    req_count = await redis.incr(key)
    if req_count == 1:
        await redis.expire(key, 60)
    elif hasattr(redis, "ttl"):
        ttl_val = await redis.ttl(key)
        if isinstance(ttl_val, int) and ttl_val < 0:
            await redis.expire(key, 60)
    if req_count > settings.ROSGRID_MCP_RATE_LIMIT_PER_MIN:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de peticiones MCP por minuto excedido",
        )


def _make_initialize_response(req_id: str | int | None) -> McpJsonRpcResponse:
    return McpJsonRpcResponse(
        jsonrpc="2.0",
        id=req_id,
        result={
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "rosgrid-mcp-server", "version": settings.VERSION},
        },
    )


async def _record_mcp_audit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    client_ip: str,
    tool_name: str,
    args: dict[str, Any],
) -> None:
    rid_str = args.get("router_id")
    target_rid: uuid.UUID | None = None
    if rid_str:
        try:
            target_rid = uuid.UUID(str(rid_str))
        except (ValueError, TypeError):
            target_rid = None
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "service_account"),
        actor_role=claims.get("rol", SystemRoleEnum.SERVICE_ACCOUNT.value),
        actor_ip=client_ip,
        event_category="MCP_AI_TOOL_CALL",
        event_action=tool_name,
        actor_user_id=user_id,
        router_id=target_rid,
        after_state={"arguments": args},
        status_code=200,
    )
    await db.commit()


async def _execute_tool_call(
    body: McpJsonRpcRequest,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    client_ip: str,
) -> McpJsonRpcResponse:
    name = body.params.get("name", "")
    args = body.params.get("arguments", {})
    handler = TOOL_HANDLERS_MAP.get(name)
    if not handler:
        return McpJsonRpcResponse(
            jsonrpc="2.0",
            id=body.id,
            error=McpJsonRpcError(code=-32601, message=f"Herramienta MCP no encontrada: {name}"),
        )
    await _verify_mcp_tenant_feature(db, tenant_id, name)
    data = await handler(db, tenant_id, user_id, claims, args)
    if name in MCP_MUTATION_TOOLS and (not isinstance(data, dict) or data.get("status") != "AWAITING_APPROVAL"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invariante Maker-Checker violado en herramienta de mutación MCP",
        )
    await _record_mcp_audit(db, tenant_id, user_id, claims, client_ip, name, args)
    return McpJsonRpcResponse(
        jsonrpc="2.0",
        id=body.id,
        result={
            "content": [{"type": "text", "text": json.dumps({"status": "OK", "data": data}, default=str)}],
            "isError": False,
        },
    )


async def _dispatch_mcp_method(
    body: McpJsonRpcRequest,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    claims: dict[str, Any],
    client_ip: str,
) -> McpJsonRpcResponse:
    if body.method == "initialize":
        return _make_initialize_response(body.id)
    if body.method in ("ping", "notifications/initialized"):
        return McpJsonRpcResponse(jsonrpc="2.0", id=body.id, result={})
    if body.method == "tools/list":
        return McpJsonRpcResponse(jsonrpc="2.0", id=body.id, result={"tools": MCP_TOOLS_CATALOG})
    return await _execute_tool_call(body, db, tenant_id, user_id, claims, client_ip)


@router.post("", response_model=McpJsonRpcResponse)
async def mcp_endpoint(
    request: Request,
    body: McpJsonRpcRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> McpJsonRpcResponse:
    """Punto de enlace MCP Streamable HTTP (JSON-RPC 2.0) protegido por RBAC, CIDR y WORM audit."""
    if not settings.ROSGRID_MCP_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP endpoint is disabled")
    _verify_mcp_role(claims)
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    client_ip = _extract_client_ip(request)
    await _verify_mcp_user_access(db, tenant_id, user_id, client_ip)
    await _check_mcp_rate_limit(tenant_id, user_id)
    await set_tenant_context(db, tenant_id, is_superadmin=False)
    return await _dispatch_mcp_method(body, db, tenant_id, user_id, claims, client_ip)


_SKILL_CANDIDATE_PATHS: tuple[Path, ...] = (
    Path(__file__).resolve().parents[4] / ".agents" / "skills" / "rosgrid-noc-operator" / "SKILL.md",
    Path(__file__).resolve().parent / "SKILL.md",
    Path("/opt/rosgrid/skills/rosgrid-noc-operator/SKILL.md"),
)

_EMBEDDED_SKILL_FALLBACK = """---
name: rosgrid-noc-operator
description: Operador NOC Autónomo para MikroTik RouterOS v7 con RoSGrid
---
# Operador NOC Autónomo para RoSGrid (MikroTik RouterOS v7)
Consulta https://github.com/tecno-consultores/RoSGrid para la documentación oficial.
"""


def _load_skill_markdown() -> str:
    for candidate in _SKILL_CANDIDATE_PATHS:
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError:
                continue
    return _EMBEDDED_SKILL_FALLBACK


@router.get("/skill", summary="Consulta pública de la Skill oficial rosgrid-noc-operator")
async def get_mcp_skill(format: str | None = None) -> Response:
    """Retorna las instrucciones operativas (SKILL.md) de la Skill oficial rosgrid-noc-operator.

    Permite a operadores y agentes remotos descargar o inspeccionar los playbooks SOP
    y guías de RouterOS v7 sin necesidad de autenticación previa.
    """
    skill_text = _load_skill_markdown()
    if format == "json":
        return JSONResponse(
            content={
                "name": "rosgrid-noc-operator",
                "version": settings.VERSION,
                "content": skill_text,
            }
        )
    return Response(
        content=skill_text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "inline; filename=SKILL.md"},
    )
