# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import cast

from src.redis_layer.client import get_redis_client
from src.schemas.syslog import SyslogEvent

logger = logging.getLogger(__name__)

SYSLOG_RINGBUFFER_MAXLEN = 500
SYSLOG_KEY_TTL_SECONDS = 86400  # 24 horas de auto-limpieza en RAM ante inactividad

CRITICAL_PATTERNS = [
    re.compile(r"interface,warning.*link down", re.IGNORECASE),
    re.compile(r"route,bgp,warning.*state changed", re.IGNORECASE),
    re.compile(r"system,error,critical.*login failure", re.IGNORECASE),
    re.compile(r"dhcp,critical.*exhausted", re.IGNORECASE),
    re.compile(r"system,critical.*out of memory", re.IGNORECASE),
]


BSD_SYSLOG_PATTERN = re.compile(
    r"^(?:<(?P<pri>\d+)>)?\s*"
    r"(?:(?P<bsd_time>[A-Z][a-z]{2}\s+\d+\s+\d+:\d+:\d+)\s+)?"
    r"(?:(?P<host>[^\s:,]+)\s+)?"
    r"(?:(?P<topics>[a-zA-Z0-9_\-]+(?:,[a-zA-Z0-9_\-]+)+)[:\s]+)?"
    r"(?P<msg>.*)$"
)


def parse_syslog_message(raw_text: str) -> SyslogEvent:
    """Parsea un mensaje Syslog estilo BSD emitido por MikroTik RouterOS v7."""
    clean = raw_text.strip()
    m = BSD_SYSLOG_PATTERN.match(clean)
    if m:
        pri = int(m.group("pri")) if m.group("pri") else 13
        topics = m.group("topics") or ""
        message = m.group("msg") or clean
    else:
        match_pri = re.match(r"^<(\d+)>?(.*)$", clean)
        pri = int(match_pri.group(1)) if match_pri else 13
        message = match_pri.group(2).strip() if match_pri else clean
        topics = ""

    severity_code = pri & 0x07
    facility_code = pri >> 3

    severity_map = {
        0: "emergency",
        1: "alert",
        2: "critical",
        3: "error",
        4: "warning",
        5: "notice",
        6: "info",
        7: "debug",
    }
    severity = severity_map.get(severity_code, "info")

    if not topics:
        msg_lower = message.lower()
        if "logged in" in msg_lower or "logged out" in msg_lower:
            topics = "system,info,account"
        elif "filter rule" in msg_lower or "firewall" in msg_lower:
            topics = "system,info"
        elif "link down" in msg_lower or "link up" in msg_lower:
            topics = "interface,warning"
        elif "bgp" in msg_lower:
            topics = "route,bgp"
        elif "ospf" in msg_lower:
            topics = "route,ospf"
        elif "dhcp" in msg_lower:
            topics = "dhcp"

    is_critical = any(p.search(clean) for p in CRITICAL_PATTERNS) or severity_code <= 2

    return SyslogEvent(
        timestamp=datetime.now(timezone.utc),
        facility=f"local{facility_code}" if facility_code >= 16 else "daemon",
        severity=severity,
        topics=topics,
        message=message,
        is_critical=is_critical,
        raw=clean,
    )


async def push_event_to_ringbuffer(
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    event: SyslogEvent,
) -> None:
    """Inserta el evento en el RingBuffer en memoria de KeyDB con límite estricto de 500 elementos."""
    try:
        redis = get_redis_client()
        key = f"rg:{tenant_id}:router:{router_id}:syslog:ring"
        active_key = f"rg:{tenant_id}:router:{router_id}:syslog:active"
        conf_key = f"rg:{tenant_id}:router:{router_id}:syslog:configured"
        payload = event.model_dump_json()

        pipeline = redis.pipeline()
        pipeline.lpush(key, payload)
        pipeline.ltrim(key, 0, SYSLOG_RINGBUFFER_MAXLEN - 1)
        pipeline.expire(key, SYSLOG_KEY_TTL_SECONDS)
        pipeline.set(active_key, "1", ex=3600)
        pipeline.set(conf_key, "1", ex=86400)

        if event.is_critical:
            alert_payload = json.dumps(
                {
                    "type": "SYSLOG_CRITICAL_EVENT",
                    "tenant_id": str(tenant_id),
                    "router_id": str(router_id),
                    "severity": event.severity,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat(),
                }
            )
            pipeline.publish("rosgrid:channel:alerts", alert_payload)

        await pipeline.execute()
    except Exception as exc:
        logger.warning("Fallo al escribir Syslog en RingBuffer KeyDB: %s", exc)


async def get_router_syslog_events(
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    limit: int = 30,
) -> list[SyslogEvent]:
    """Recupera los últimos N eventos Syslog almacenados en el RingBuffer de KeyDB."""
    try:
        redis = get_redis_client()
        key = f"rg:{tenant_id}:router:{router_id}:syslog:ring"
        raw_items = await redis.lrange(key, 0, max(0, limit - 1))
        return [SyslogEvent.model_validate_json(item) for item in raw_items]
    except Exception as exc:
        logger.warning("Fallo al consultar Syslog RingBuffer de KeyDB: %s", exc)
        return []


class SyslogUdpProtocol(asyncio.DatagramProtocol):
    """Protocolo UDP asíncrono para ingesta de eventos Syslog en puerto no privilegiado."""

    def __init__(
        self,
        ip_router_map: dict[str, tuple[uuid.UUID, uuid.UUID]],
        name_router_map: dict[str, tuple[uuid.UUID, uuid.UUID]] | None = None,
    ) -> None:
        self.ip_router_map = ip_router_map
        self.name_router_map = name_router_map or {}
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        src_ip = addr[0]
        mapping = self.ip_router_map.get(src_ip)

        text = data.decode("utf-8", errors="replace")
        clean = text.strip()

        # Si el datagrama viene vía Docker NAT/bridge (ej: 172.18.0.1, 127.0.0.1) o VPN/túnel
        if not mapping:
            # 1. Comprobar si alguna de las IPs registradas aparece en el mensaje Syslog
            for registered_ip, target in self.ip_router_map.items():
                if registered_ip in clean:
                    mapping = target
                    break

        # 2. Comprobar si el display_name o ros_identity del router aparece en el encabezado BSD
        if not mapping and self.name_router_map:
            tokens = re.findall(r"[a-zA-Z0-9_\-\.]+", clean[:150])
            for token in tokens:
                t_lower = token.lower()
                if t_lower in self.name_router_map:
                    mapping = self.name_router_map[t_lower]
                    break

        if not mapping:
            logger.debug("Descarte Syslog: no se encontró mapeo para origen %s ni en texto: %s", src_ip, clean[:80])
            return

        tenant_id, router_id = mapping
        try:
            event = parse_syslog_message(clean)
            asyncio.create_task(push_event_to_ringbuffer(tenant_id, router_id, event))
        except Exception as exc:
            logger.debug("Error procesando datagrama Syslog de %s: %s", src_ip, exc)


async def load_router_syslog_maps() -> tuple[
    dict[str, tuple[uuid.UUID, uuid.UUID]],
    dict[str, tuple[uuid.UUID, uuid.UUID]],
]:
    """Consulta la base de datos para mapear IPs y nombres de routers activos a (tenant_id, router_id)."""
    from sqlalchemy import select

    from src.db.session import async_session_maker
    from src.models.inventory import Router, RouterAdminStateEnum

    ip_map: dict[str, tuple[uuid.UUID, uuid.UUID]] = {}
    name_map: dict[str, tuple[uuid.UUID, uuid.UUID]] = {}
    try:
        async with async_session_maker() as session:
            stmt = select(
                Router.id,
                Router.tenant_id,
                Router.api_base_url,
                Router.display_name,
                Router.ros_identity,
            ).where(Router.admin_state != RouterAdminStateEnum.RETIRED)
            rows = (await session.execute(stmt)).all()
            for row in rows:
                if len(row) >= 5:
                    r_id, t_id, base_url, d_name, r_ident = row[0], row[1], row[2], row[3], row[4]
                elif len(row) >= 3:
                    r_id, t_id, base_url = row[0], row[1], row[2]
                    d_name, r_ident = None, None
                else:
                    continue
                if base_url:
                    clean = (
                        base_url.replace("https://", "")
                        .replace("http://", "")
                        .split("/")[0]
                        .split(":")[0]
                        .strip()
                    )
                    if clean:
                        ip_map[clean] = (t_id, r_id)
                if d_name:
                    name_map[d_name.strip().lower()] = (t_id, r_id)
                if r_ident:
                    name_map[r_ident.strip().lower()] = (t_id, r_id)
    except Exception as exc:
        logger.warning("Fallo al sincronizar mapas de routers para Syslog: %s", exc)
    return ip_map, name_map


async def load_ip_router_map() -> dict[str, tuple[uuid.UUID, uuid.UUID]]:
    """Mantiene compatibilidad con suites de pruebas unitarias existentes."""
    ip_map, _ = await load_router_syslog_maps()
    return ip_map


async def syslog_collector_worker_loop() -> None:
    """Worker en segundo plano que escucha datagramas UDP 5514 y refresca el mapa de enrutadores."""
    from src.core.config import settings

    port = getattr(settings, "ROSGRID_SYSLOG_PORT", 5514)
    logger.info("=== Iniciando Colector Syslog UDP en 0.0.0.0:%d ===", port)

    ip_map, name_map = await load_router_syslog_maps()
    loop = asyncio.get_running_loop()

    transport = None
    protocol = None
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SyslogUdpProtocol(ip_map, name_map),
            local_addr=("0.0.0.0", port),
        )
        logger.info(
            "Colector Syslog escuchando en UDP 0.0.0.0:%d con %d IP(s) y %d nombre(s) mapeado(s).",
            port,
            len(ip_map),
            len(name_map),
        )
    except Exception as exc:
        logger.error("Error al enlazar socket UDP 0.0.0.0:%d para Syslog: %s", port, exc)
        return

    try:
        while True:
            await asyncio.sleep(60)
            new_ip_map, new_name_map = await load_router_syslog_maps()
            if protocol and hasattr(protocol, "ip_router_map"):
                protocol.ip_router_map.clear()
                protocol.ip_router_map.update(new_ip_map)
                if hasattr(protocol, "name_router_map"):
                    protocol.name_router_map.clear()
                    protocol.name_router_map.update(new_name_map)
                logger.debug(
                    "Mapas Syslog refrescados: %d IPs, %d nombres.",
                    len(new_ip_map),
                    len(new_name_map),
                )
    except asyncio.CancelledError:
        logger.info("Cerrando listener Syslog UDP 0.0.0.0:%d...", port)
    finally:
        if transport and not transport.is_closing():
            transport.close()
