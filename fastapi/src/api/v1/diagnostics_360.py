# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de la Suite de Diagnóstico 360° para Soporte Técnico y Técnicos de Campo (Hito 18.1)."""

import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_feature, require_roles
from src.api.v1.webfig_common import get_router_and_client
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.schemas.diagnostics_360 import (
    DisconnectLogAnalysis,
    DisconnectLogItem,
    Endpoint360Request,
    Endpoint360Response,
    MultiMtuPingSummary,
    PingMtuStats,
    TorchTopFlowItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/diagnostics",
    tags=["Diagnostics 360"],
    dependencies=[Depends(require_feature("isp_module_enabled"))],
)

_DIAGNOSTICS_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.FIELD_TECH,
    SystemRoleEnum.NOC_MONITOR,
)

_PING_ENDPOINT = "/ping"


def _parse_rtt_ms(val: Any) -> float | None:
    """Extrae la latencia en milisegundos de salidas textuales o numéricas de RouterOS."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    if not s:
        return None
    try:
        if s.endswith("ms"):
            return float(s[:-2])
        if s.endswith("s"):
            return float(s[:-1]) * 1000.0
        return float(s)
    except (ValueError, TypeError):
        return None


def _extract_received_rtts(items: list[Any]) -> tuple[int, list[float]]:
    """Extrae paquetes recibidos y lista de RTTs válidos."""
    rtts: list[float] = []
    received = 0
    for r in items:
        if not isinstance(r, dict) or r.get("status") not in (None, "ok", 0, "received"):
            continue
        received += 1
        rtt = _parse_rtt_ms(r.get("time", r.get("rtt", r.get("avg-rtt"))))
        if rtt is not None:
            rtts.append(rtt)
    return received, rtts


def _compute_jitter(rtts: list[float]) -> float | None:
    """Calcula jitter medio entre paquetes sucesivos."""
    if len(rtts) <= 1:
        return 0.0 if rtts else None
    diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
    return round(sum(diffs) / len(diffs), 2)


def _calculate_ping_stats(size: int, count: int, raw_results: Any, df_bit: bool = False) -> PingMtuStats:
    """Calcula latencia mínima, media, máxima, jitter y pérdida de paquetes de una ronda de pings."""
    items = raw_results if isinstance(raw_results, list) else []
    received, rtts = _extract_received_rtts(items)

    loss_pct = round(((count - received) / max(1, count)) * 100.0, 2)
    min_rtt = min(rtts) if rtts else None
    max_rtt = max(rtts) if rtts else None
    avg_rtt = round(sum(rtts) / len(rtts), 2) if rtts else None
    jitter = _compute_jitter(rtts)

    return PingMtuStats(
        size=size,
        sent=count,
        received=received,
        packet_loss_pct=loss_pct,
        min_rtt_ms=min_rtt,
        avg_rtt_ms=avg_rtt,
        max_rtt_ms=max_rtt,
        jitter_ms=jitter,
        df_bit=df_bit,
    )


def _classify_log_message(msg: str) -> str | None:
    """Clasifica el motivo de RouterOS ante eventos de desconexión."""
    lowered = msg.lower()
    if "user request" in lowered:
        return "user request"
    if "peer is not responding" in lowered:
        return "peer is not responding"
    if "link down" in lowered:
        return "link down"
    if "auth" in lowered and ("fail" in lowered or "wrong" in lowered):
        return "authentication failed"
    return None


def _is_log_relevant(entry: dict[str, Any], target_ip: str, device_serial: str | None) -> bool:
    """Determina si una entrada de log está vinculada al abonado o interfaz."""
    msg = str(entry.get("message", ""))
    topics = str(entry.get("topics", "")).lower()
    is_relevant_topic = any(k in topics for k in ("ppp", "pppoe", "interface", "link"))
    has_identifier = (target_ip in msg) or (bool(device_serial and device_serial in msg))
    return is_relevant_topic or has_identifier


def _classify_disconnect_reason(
    raw_logs: Any,
    target_ip: str,
    device_serial: str | None = None,
) -> DisconnectLogAnalysis:
    """Analiza los logs de RouterOS para correlacionar y tipificar caídas de sesión."""
    logs_list = raw_logs if isinstance(raw_logs, list) else []
    matched_items: list[DisconnectLogItem] = []
    detected_reason = "none_detected"
    last_time: str | None = None

    for entry in reversed(logs_list):
        if not isinstance(entry, dict) or not _is_log_relevant(entry, target_ip, device_serial):
            continue
        msg = str(entry.get("message", ""))
        topics = str(entry.get("topics", "")).lower()
        t_time = str(entry.get("time", ""))

        matched_items.append(
            DisconnectLogItem(
                time=t_time or None,
                topics=topics or None,
                message=msg,
            )
        )
        reason = _classify_log_message(msg)
        if reason and detected_reason == "none_detected":
            detected_reason = reason
            last_time = t_time

        if len(matched_items) >= 10:
            break

    return DisconnectLogAnalysis(
        detected_reason=detected_reason,
        last_disconnect_time=last_time,
        matched_logs=matched_items,
    )


def _parse_torch_rate(val: Any) -> float:
    """Normaliza tasas de transmisión de Torch a kilobits por segundo (kbps)."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return round(float(val) / 1000.0, 2)
    s = str(val).strip().lower()
    try:
        if s.endswith("mbps"):
            return round(float(s[:-4]) * 1000.0, 2)
        if s.endswith("kbps"):
            return round(float(s[:-4]), 2)
        if s.endswith("bps"):
            return round(float(s[:-3]) / 1000.0, 2)
        return round(float(s) / 1000.0, 2)
    except (ValueError, TypeError):
        return 0.0


def _parse_torch_flows(raw_torch: Any) -> list[TorchTopFlowItem]:
    """Extrae y ordena el Top 5 de flujos activos medidos con Torch."""
    items = raw_torch if isinstance(raw_torch, list) else []
    flows: list[TorchTopFlowItem] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        proto = str(item.get("protocol", item.get("proto", "ip")))
        port_raw = item.get("port", item.get("dst-port", item.get("src-port")))
        try:
            port = int(port_raw) if port_raw is not None else None
        except (ValueError, TypeError):
            port = None

        tx = _parse_torch_rate(item.get("tx-rate", item.get("tx", 0)))
        rx = _parse_torch_rate(item.get("rx-rate", item.get("rx", 0)))
        src = str(item.get("src-address", "")) or None
        dst = str(item.get("dst-address", "")) or None

        flows.append(
            TorchTopFlowItem(
                protocol=proto,
                port=port,
                src_address=src,
                dst_address=dst,
                tx_rate_kbps=tx,
                rx_rate_kbps=rx,
            )
        )

    flows.sort(key=lambda f: f.tx_rate_kbps + f.rx_rate_kbps, reverse=True)
    return flows[:5]


def _evaluate_overall_status(
    p64: PingMtuStats,
    p512: PingMtuStats,
    p1472: PingMtuStats,
    dispersion: bool,
) -> str:
    """Evalúa la salud general del abonado según pérdidas, latencia y dispersión MTU."""
    if p64.packet_loss_pct >= 100.0 and p512.packet_loss_pct >= 100.0:
        return "DOWN"
    has_loss = (p64.packet_loss_pct > 0.0) or (p512.packet_loss_pct > 0.0) or (p1472.packet_loss_pct > 0.0)
    high_latency = bool(p64.avg_rtt_ms and p64.avg_rtt_ms > 80.0)
    if has_loss or high_latency or dispersion or not p1472.received:
        return "DEGRADED"
    return "OPTIMAL"


@router.post("/endpoint-360", response_model=Endpoint360Response)
async def run_endpoint_360_diagnostics(
    payload: Endpoint360Request,
    claims: dict[str, Any] = Depends(require_roles(*_DIAGNOSTICS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Endpoint360Response:
    """Ejecuta el protocolo de diagnóstico 360° en MikroTik v7: Ping Multi-MTU, Parseo de /log y Torch."""
    _, client = await get_router_and_client(payload.router_id, claims, db)

    async with client:
        # 1. Ping Multi-MTU Secuencial
        raw_64 = await client.post(
            _PING_ENDPOINT,
            json_data={"address": payload.target_ip, "count": 3, "size": 64},
        )
        raw_512 = await client.post(
            _PING_ENDPOINT,
            json_data={"address": payload.target_ip, "count": 3, "size": 512},
        )
        raw_1472 = await client.post(
            _PING_ENDPOINT,
            json_data={
                "address": payload.target_ip,
                "count": 3,
                "size": 1472,
                "do-not-fragment": True,
            },
        )

        p64 = _calculate_ping_stats(64, 3, raw_64, df_bit=False)
        p512 = _calculate_ping_stats(512, 3, raw_512, df_bit=False)
        p1472 = _calculate_ping_stats(1472, 3, raw_1472, df_bit=True)

        dispersion = False
        if p64.avg_rtt_ms is not None and p1472.avg_rtt_ms is not None:
            if (p1472.avg_rtt_ms - p64.avg_rtt_ms) > 40.0:
                dispersion = True
        pass_1500 = p1472.received > 0 or p64.received == 0

        multi_mtu = MultiMtuPingSummary(
            ping_64=p64,
            ping_512=p512,
            ping_1472=p1472,
            mtu_dispersion_detected=dispersion,
            mtu_pass_1500=pass_1500,
        )

        # 2. Parseo de Desconexiones en /log
        raw_logs = await client.get("/log")
        disconnect_analysis = _classify_disconnect_reason(
            raw_logs=raw_logs,
            target_ip=payload.target_ip,
            device_serial=payload.device_serial,
        )

        # 3. Muestreo Torch Instantáneo
        torch_body: dict[str, Any] = {
            "interface": payload.interface or "ether1",
            "duration": 3,
            "src-address": payload.target_ip,
        }
        try:
            raw_torch = await client.post("/tool/torch", json_data=torch_body)
        except Exception as exc:
            logger.debug("Torch sampling falló de forma no crítica: %s", exc)
            raw_torch = []

        torch_flows = _parse_torch_flows(raw_torch)

    overall_status = _evaluate_overall_status(p64, p512, p1472, dispersion)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return Endpoint360Response(
        router_id=payload.router_id,
        target_ip=payload.target_ip,
        device_serial=payload.device_serial,
        interface=payload.interface,
        overall_status=overall_status,
        multi_mtu=multi_mtu,
        disconnect_analysis=disconnect_analysis,
        torch_top_flows=torch_flows,
        diagnostic_timestamp=now_iso,
        raw_details={
            "raw_64_count": len(raw_64) if isinstance(raw_64, list) else 0,
            "raw_logs_inspected": len(raw_logs) if isinstance(raw_logs, list) else 0,
        },
    )
