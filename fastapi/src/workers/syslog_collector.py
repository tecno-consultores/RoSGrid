# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone

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


def parse_syslog_message(raw_text: str) -> SyslogEvent:
    """Parsea un mensaje Syslog estilo BSD emitido por MikroTik RouterOS v7."""
    clean = raw_text.strip()
    match = re.match(r"^<(\d+)>?(.*)$", clean)
    pri = int(match.group(1)) if match else 13
    rest = match.group(2).strip() if match else clean

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

    topics = ""
    message = rest
    parts = rest.split(" ", 3)
    if len(parts) >= 4 and ("," in parts[2] or parts[2].startswith("system")):
        topics = parts[2]
        message = parts[3]

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
        payload = event.model_dump_json()

        pipeline = redis.pipeline()
        pipeline.lpush(key, payload)
        pipeline.ltrim(key, 0, SYSLOG_RINGBUFFER_MAXLEN - 1)
        pipeline.expire(key, SYSLOG_KEY_TTL_SECONDS)

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

    def __init__(self, ip_router_map: dict[str, tuple[uuid.UUID, uuid.UUID]]) -> None:
        self.ip_router_map = ip_router_map

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        src_ip = addr[0]
        mapping = self.ip_router_map.get(src_ip)
        if not mapping:
            # Descarte silencioso anti-spoofing para IPs no enroladas en el tenant
            return

        tenant_id, router_id = mapping
        try:
            text = data.decode("utf-8", errors="replace")
            event = parse_syslog_message(text)
            asyncio.create_task(push_event_to_ringbuffer(tenant_id, router_id, event))
        except Exception as exc:
            logger.debug("Error procesando datagrama Syslog de %s: %s", src_ip, exc)
