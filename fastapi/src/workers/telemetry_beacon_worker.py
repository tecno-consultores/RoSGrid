# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Worker de Telemetría Anónima de Instancias Activas (Spec 55 / Hito 27.18).

Envía latidos anónimos periódicos (Zero-PII) hacia https://rosgrid.net/api/telemetry/heartbeat
de forma estrictamente fail-silent para censar el número de instalaciones activas en el mundo.
"""

import asyncio
import hashlib
import hmac
import logging
import time
from typing import Any

import httpx
from sqlalchemy import func, select

from src.core.config import settings
from src.db.session import async_session_maker, set_tenant_context
from src.models.inventory import Router, RouterAdminStateEnum
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)

BEACON_STATE_KEY = "rg:system:telemetry_beacon_state"
BEACON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RoSGrid-Beacon/1.0; +https://rosgrid.net)",
    "Accept": "application/json",
}


def compute_anonymous_instance_id(seed: str) -> str:
    """Genera un identificador anónimo irreversible SHA-256 de 64 caracteres hex (CC = 1)."""
    normalized_seed = (seed or "rosgrid-default-seed").strip()
    return hmac.new(b"rosgrid-anonymous-beacon-v1", normalized_seed.encode("utf-8"), hashlib.sha256).hexdigest()


def resolve_fleet_bucket(router_count: int) -> str:
    """Clasifica el tamaño de la flota en un rango anónimo sin revelar el número exacto (CC = 4)."""
    if router_count <= 0:
        return "0"
    if router_count <= 10:
        return "1-10"
    if router_count <= 50:
        return "11-50"
    return "51-250" if router_count <= 250 else "250+"


async def _count_active_routers_safe() -> int:
    """Cuenta routers activos globalmente (bypass RLS SuperAdmin) de forma fail-silent (CC = 2)."""
    try:
        async with async_session_maker() as session:
            await set_tenant_context(session, None, is_superadmin=True)
            stmt = select(func.count(Router.id)).where(Router.admin_state == RouterAdminStateEnum.PRODUCTION)
            res = await session.execute(stmt)
            count = res.scalar() or 0
            return int(count)
    except Exception as exc:
        logger.debug("Fallo no bloqueante al contar routers para beacon: %s", exc)
        return 0


async def _persist_beacon_state(
    instance_id: str,
    now_iso: str,
    status_str: str,
    fleet_bucket: str = "0",
    router_count: int = 0,
) -> None:
    """Guarda el último estado del latido en KeyDB sin fallar si KeyDB está mockeado (CC = 2)."""
    try:
        redis = get_redis_client()
        await redis.hset(
            BEACON_STATE_KEY,
            mapping={
                "instance_id": instance_id,
                "last_sent_at": now_iso,
                "last_status": status_str,
                "fleet_bucket": fleet_bucket,
                "router_count": str(router_count),
                "beacon_url": settings.ROSGRID_TELEMETRY_BEACON_URL,
            },
        )
    except Exception as exc:
        logger.debug("Persistencia de beacon en KeyDB omitida: %s", exc)


def _decode_redis_str(val: Any, default: str | None = None) -> str | None:
    """Decodifica un valor de KeyDB (bytes o str) de forma segura (CC = 3)."""
    if val is None:
        return default
    return val.decode() if isinstance(val, bytes) else str(val)


async def get_telemetry_beacon_status() -> dict[str, Any]:
    """Obtiene el estado actual del latido de telemetría para diagnósticos locales (CC = 4)."""
    instance_id = compute_anonymous_instance_id(settings.ROSGRID_JWT_SECRET_KEY[:16])
    last_sent_at: str | None = None
    last_status = "untriggered"
    fleet_bucket: str | None = None
    router_count = await _count_active_routers_safe()

    try:
        redis = get_redis_client()
        raw_state = await redis.hgetall(BEACON_STATE_KEY)
        if raw_state:
            instance_id = _decode_redis_str(raw_state.get("instance_id"), instance_id) or instance_id
            last_sent_at = _decode_redis_str(raw_state.get("last_sent_at"), None)
            last_status = _decode_redis_str(raw_state.get("last_status"), "untriggered") or "untriggered"
            fleet_bucket = _decode_redis_str(raw_state.get("fleet_bucket"), None)
    except Exception as exc:
        logger.debug("Lectura de estado de beacon en KeyDB omitida: %s", exc)

    resolved_bucket = fleet_bucket or resolve_fleet_bucket(router_count)
    return {
        "enabled": settings.ROSGRID_TELEMETRY_BEACON_ENABLED,
        "instance_id": instance_id,
        "beacon_url": settings.ROSGRID_TELEMETRY_BEACON_URL,
        "interval_seconds": settings.ROSGRID_TELEMETRY_BEACON_INTERVAL_SECONDS,
        "last_sent_at": last_sent_at,
        "last_heartbeat_at": last_sent_at,
        "last_status": last_status,
        "fleet_bucket": resolved_bucket,
        "router_count": router_count,
    }


async def _dispatch_beacon_http(payload: dict[str, Any]) -> int:
    """Envía el latido vía POST con fallback automático a GET ante reglas WAF 403/405 (CC = 3)."""
    async with httpx.AsyncClient(timeout=5.0, headers=BEACON_HEADERS) as client:
        resp = await client.post(settings.ROSGRID_TELEMETRY_BEACON_URL, json=payload)
        if resp.status_code in (403, 405):
            query_params = {k: str(v) for k, v in payload.items()}
            resp = await client.get(settings.ROSGRID_TELEMETRY_BEACON_URL, params=query_params)
        return int(resp.status_code)


async def send_telemetry_heartbeat_once(router_count: int | None = None) -> dict[str, Any]:
    """Envía un único latido anónimo Zero-PII hacia rosgrid-web de forma fail-silent (CC = 4)."""
    instance_id = compute_anonymous_instance_id(settings.ROSGRID_JWT_SECRET_KEY[:16])
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if router_count is None:
        router_count = await _count_active_routers_safe()

    payload = {
        "schema_version": 1,
        "instance_id": instance_id,
        "version": "1.0.0",
        "fleet_bucket": resolve_fleet_bucket(router_count),
        "timestamp": now_iso,
    }

    if not settings.ROSGRID_TELEMETRY_BEACON_ENABLED:
        return {
            "enabled": False,
            "instance_id": instance_id,
            "last_status": "disabled",
            "fleet_bucket": payload["fleet_bucket"],
            "router_count": router_count,
        }

    status_str = "sent"
    try:
        code = await _dispatch_beacon_http(payload)
        status_str = f"http_{code}"
    except Exception as exc:
        logger.debug("Telemetry beacon fail-silent: %s", exc)
        status_str = "offline_skipped"

    await _persist_beacon_state(
        instance_id,
        now_iso,
        status_str,
        fleet_bucket=str(payload["fleet_bucket"]),
        router_count=router_count,
    )
    return {
        "enabled": True,
        "instance_id": instance_id,
        "last_sent_at": now_iso,
        "last_heartbeat_at": now_iso,
        "last_status": status_str,
        "fleet_bucket": payload["fleet_bucket"],
        "router_count": router_count,
    }


async def _beacon_sleep_interval(stop_event: asyncio.Event | None, interval: int) -> bool:
    """Espera el intervalo del beacon o retorna True si se activa stop_event (CC = 3)."""
    if not stop_event:
        await asyncio.sleep(interval)
        return False
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=float(interval))
        return True
    except (asyncio.TimeoutError, TimeoutError):
        return False


async def _execute_beacon_tick() -> None:
    """Ejecuta un ciclo de latido de telemetría de forma segura (CC = 2)."""
    try:
        await send_telemetry_heartbeat_once()
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.debug("Fallo en ejecución periódica de telemetry beacon: %s", exc)


async def telemetry_beacon_worker_loop(stop_event: asyncio.Event | None = None) -> None:
    """Ciclo en segundo plano para envío periódico del latido de telemetría anónima (CC = 4)."""
    if not settings.ROSGRID_TELEMETRY_BEACON_ENABLED:
        logger.info("TelemetryBeaconWorker desactivado por configuración (ROSGRID_TELEMETRY_BEACON_ENABLED=false).")
        return

    logger.info(
        "Iniciando TelemetryBeaconWorker (intervalo: %ds)...", settings.ROSGRID_TELEMETRY_BEACON_INTERVAL_SECONDS
    )
    await asyncio.sleep(5)
    interval = max(60, settings.ROSGRID_TELEMETRY_BEACON_INTERVAL_SECONDS)

    while not (stop_event and stop_event.is_set()):
        await _execute_beacon_tick()
        should_stop = await _beacon_sleep_interval(stop_event, interval)
        if should_stop:
            break
