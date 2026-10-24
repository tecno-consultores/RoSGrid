# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker 1: Monitor de Salud Zero-Storage (cada 30s) con detección de transiciones en Redis."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.inventory_helpers import discover_hardware
from src.api.v1.webfig_common import _create_client_from_vault
from src.db.session import async_session_maker
from src.mikrotik.client import MikrotikRestClient
from src.models.inventory import MaintenanceWindow, Router, RouterAdminStateEnum, SSLTrustStatusEnum
from src.redis_layer.client import get_redis_client
from src.redis_layer.zero_metrics_monitor import (
    evaluate_router_monitoring_cycle,
    write_monitoring_state_pipeline,
)

logger = logging.getLogger(__name__)


async def _check_router_in_maintenance(session: Any, tenant_id: uuid.UUID, router_id: uuid.UUID) -> bool:
    now_utc = datetime.now(UTC)
    stmt = select(MaintenanceWindow).where(
        MaintenanceWindow.tenant_id == tenant_id,
        MaintenanceWindow.router_id == router_id,
        MaintenanceWindow.is_cancelled.is_(False),
        MaintenanceWindow.starts_at <= now_utc,
        MaintenanceWindow.ends_at >= now_utc,
    )
    window = (await session.execute(stmt)).scalar_one_or_none()
    return window is not None


async def _ping_router_resource(client: MikrotikRestClient) -> tuple[bool, int, int]:
    try:
        res = await asyncio.wait_for(client.get("system/resource"), timeout=5.0)
        if isinstance(res, dict) and "cpu-load" in res:
            cpu = int(res.get("cpu-load", 0))
            tot_mem = int(res.get("total-memory", 1))
            free_mem = int(res.get("free-memory", 0))
            pct_free = int((free_mem / tot_mem) * 100) if tot_mem > 0 else 100
            return True, cpu, pct_free
    except Exception as exc:
        logger.debug("Fallo en sondeo de salud del router: %s", exc)
    return False, 0, 0


async def _publish_alert_and_event(
    redis: Any,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    router_name: str,
    alert_name: str,
    new_status: str,
) -> None:
    now_iso = datetime.now(UTC).isoformat()
    payload = {
        "event_name": alert_name,
        "router_id": str(router_id),
        "router_display_name": router_name,
        "operational_status": new_status,
        "timestamp_iso": now_iso,
    }
    await redis.publish(f"rg:pubsub:alerts:{tenant_id}", json.dumps(payload))
    await redis.publish(
        f"rg:pubsub:events:{tenant_id}",
        json.dumps(
            {
                "type": "ROUTER_STATE_CHANGED",
                "tenant_id": str(tenant_id),
                "timestamp_iso": now_iso,
                "event_name": alert_name,
                "payload": payload,
            }
        ),
    )


async def _evaluate_single_router(session: Any, redis: Any, r: Router) -> None:
    in_maint = await _check_router_in_maintenance(session, r.tenant_id, r.id)
    state_key = f"rg:{r.tenant_id}:mon_state:{r.id}"
    cur_state = await redis.hgetall(state_key)

    is_reachable = False
    cpu, free_pct = 0, 100
    if r.vault:
        client = _create_client_from_vault(r, r.tenant_id)
        is_reachable, cpu, free_pct = await _ping_router_resource(client)
        if is_reachable:
            if r.ssl_trust_status == SSLTrustStatusEnum.PENDING_TOFU or not r.ssl_sha256_fingerprint:
                fp = getattr(client, "_observed_fingerprint", None)
                if not fp and hasattr(client, "ensure_ssl_verified"):
                    try:
                        fp = await client.ensure_ssl_verified()
                    except Exception as ssl_err:
                        logger.debug("Error extrayendo huella SSL en health monitor para %s: %s", r.display_name, ssl_err)
                if fp:
                    r.ssl_sha256_fingerprint = fp
                    r.ssl_trust_status = SSLTrustStatusEnum.TRUSTED_PINNED
                    r.ssl_pinned_at = datetime.now(UTC)
                    logger.info("Auto-pinning TOFU exitoso en monitor de salud para router %s: %s", r.display_name, fp)
            if not r.ros_version or not r.ros_identity:
                try:
                    await discover_hardware(client, r)
                    r.last_discovery_sync_at = datetime.now(UTC)
                except Exception as d_exc:
                    logger.debug("Fallo en autodescubrimiento durante monitor de salud para %s: %s", r.display_name, d_exc)
        await client.close()

    new_status, alert, updated_state = evaluate_router_monitoring_cycle(
        current_state=cur_state,
        is_reachable=is_reachable,
        cpu_load_pct=cpu,
        free_memory_pct=free_pct,
        in_maintenance=in_maint,
    )

    await write_monitoring_state_pipeline(redis, r.tenant_id, r.id, updated_state)
    r.is_reachable = is_reachable
    if is_reachable:
        r.last_seen_at = datetime.now(UTC)

    if alert and not in_maint:
        await _publish_alert_and_event(redis, r.tenant_id, r.id, r.display_name, alert, new_status)


async def run_health_monitor_cycle() -> None:
    """Ejecuta una ronda de sondeo de salud sobre todos los routers en producción."""
    redis = get_redis_client()
    async with async_session_maker() as session:
        stmt = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.admin_state == RouterAdminStateEnum.PRODUCTION)
        )
        routers = (await session.execute(stmt)).scalars().all()
        for r in routers:
            try:
                await _evaluate_single_router(session, redis, r)
            except Exception as exc:
                logger.error("Error al monitorear router %s: %s", r.id, exc)
        await session.commit()


async def health_monitor_worker_loop() -> None:
    """Bucle infinito del worker de salud cada 30 segundos."""
    logger.info("Iniciando Worker 1: Monitor de Salud Zero-Storage...")
    while True:
        try:
            await run_health_monitor_cycle()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Excepción en ciclo de salud: %s", exc)
        await asyncio.sleep(30.0)
