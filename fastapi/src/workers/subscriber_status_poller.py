# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller) de Clientes y Dispositivos.

Consulta periódicamente las tablas nativas de sesiones de RouterOS v7 (/ip/dhcp-server/lease o /ppp/active)
aplicando jitter temporal entre routers para erradicar picos de CPU, filtrado delta de escritura cero en DB,
y notificación reactiva de eventos DEVICE_STATUS_CHANGED vía Pub/Sub a WebSockets.
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from src.api.v1.webfig_common import _create_client_from_vault
from src.core.config import settings
from src.db.session import async_session_maker
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.redis_layer.client import get_redis_client

logger = logging.getLogger("rosgrid-subscriber-poller")

DEFAULT_POLL_INTERVAL_SECONDS: int = 180
MIN_INTER_ROUTER_JITTER_SECONDS: float = 2.0


async def _poll_single_router_sessions(
    session: Any,
    tenant_id: uuid.UUID,
    router: Router,
    is_isp_mode: bool,
) -> int:
    """Consulta pasiva compacta de las tablas de sesiones en RouterOS v7 con filtro delta en base de datos."""
    redis = get_redis_client()

    # 1. Comprobación rápida de Circuit Breaker en KeyDB
    cb_key = f"rg:{tenant_id}:diag:circuit:router:{router.id}"
    cb_state = await redis.get(cb_key)
    if cb_state and (cb_state == "OPEN" or cb_state == b"OPEN"):
        logger.debug(f"Router {router.display_name} en Circuit Breaker abierto. Omitiendo sondeo pasivo.")
        return 0

    client = None
    try:
        client = _create_client_from_vault(router, tenant_id)
    except Exception as exc:
        logger.debug(f"No se pudo crear cliente para router {router.display_name}: {exc}")
        return 0

    active_identifiers: set[str] = set()

    try:
        async with client:
            if is_isp_mode:
                raw_active = await asyncio.wait_for(client.get("/ppp/active"), timeout=8.0)
                if isinstance(raw_active, list):
                    for item in raw_active:
                        if isinstance(item, dict):
                            name = str(item.get("name") or "").strip()
                            addr = str(item.get("address") or "").strip()
                            if name:
                                active_identifiers.add(name.lower())
                            if addr:
                                active_identifiers.add(addr)
            else:
                raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
                if isinstance(raw_leases, list):
                    for item in raw_leases:
                        if isinstance(item, dict):
                            st = str(item.get("status") or "").lower()
                            if st in ("bound", "active"):
                                addr = str(item.get("address") or "").strip()
                                mac = str(item.get("mac-address") or "").replace(":", "").replace("-", "").upper()
                                if addr:
                                    active_identifiers.add(addr)
                                if mac:
                                    active_identifiers.add(mac)
    except Exception as exc:
        logger.warning(f"Error consultando tablas de sesiones en router {router.display_name}: {exc}")
        return 0

    # 2. Consultar los dispositivos registrados para este router
    stmt_devs = select(SubscriberDevice).where(
        SubscriberDevice.tenant_id == tenant_id,
        SubscriberDevice.router_id == router.id,
    )
    devices = list((await session.execute(stmt_devs)).scalars().all())
    if not devices:
        return 0

    changed_count = 0
    now_utc = datetime.now(UTC)
    pubsub_channel = f"rg:pubsub:events:{tenant_id}"

    for dev in devices:
        # Evaluar presencia en el set de activos
        ip = str(dev.assigned_ipv4 or "").strip()
        mac = str(dev.onu_mac_address or "").replace(":", "").replace("-", "").upper()
        pppoe = str(dev.pppoe_username or "").strip().lower()

        is_present = False
        if ip and ip in active_identifiers:
            is_present = True
        elif mac and mac in active_identifiers:
            is_present = True
        elif pppoe and pppoe in active_identifiers:
            is_present = True

        new_status = "ONLINE" if is_present else "OFFLINE"

        # 3. Filtro Delta (Zero-Write DB): Solo actualiza y emite si hay cambio de estado
        if new_status != dev.last_reachability_status:
            dev.last_reachability_status = new_status
            dev.last_seen_at = now_utc
            changed_count += 1

            # Emitir evento reactivo a WebSocket
            event_payload = {
                "event_name": "DEVICE_STATUS_CHANGED",
                "payload": {
                    "device_id": str(dev.id),
                    "status": new_status,
                    "router_id": str(router.id),
                    "endpoint_identifier": dev.endpoint_identifier,
                    "last_seen_at": now_utc.isoformat(),
                },
            }
            try:
                await redis.publish(pubsub_channel, json.dumps(event_payload))
            except Exception as e:
                logger.debug(f"Aviso publicando evento DEVICE_STATUS_CHANGED: {e}")

    if changed_count > 0:
        await session.commit()
        logger.info(
            f"[Poller Delta] Router {router.display_name}: {changed_count} dispositivos cambiaron de estado."
        )

    return changed_count


async def poll_tenant_subscribers_cycle(tenant_id: uuid.UUID, is_isp_mode: bool) -> None:
    """Ejecuta el ciclo de sondeo pasivo escalonado para todos los routers de un tenant."""
    async with async_session_maker() as session:
        stmt_routers = (
            select(Router)
            .where(
                Router.tenant_id == tenant_id,
                Router.admin_state != RouterAdminStateEnum.RETIRED,
                Router.is_reachable.is_(True),
            )
            .order_by(Router.display_name.asc())
        )
        routers = list((await session.execute(stmt_routers)).scalars().all())
        if not routers:
            return

        interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)
        base_delay = max(MIN_INTER_ROUTER_JITTER_SECONDS, interval / max(1, len(routers)))

        for r in routers:
            await _poll_single_router_sessions(session, tenant_id, r, is_isp_mode)
            # Jitter dinámico entre routers para aplanar la curva de carga
            jitter = random.uniform(0.1, 0.8)
            await asyncio.sleep(base_delay + jitter)


async def subscriber_status_poller_worker_loop() -> None:
    """Loop principal del Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller)."""
    logger.info("=== Iniciando Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller) ===")
    interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)

    while True:
        try:
            async with async_session_maker() as session:
                stmt_t = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
                tenants = list((await session.execute(stmt_t)).scalars().all())

            for t in tenants:
                is_isp = bool(getattr(t, "isp_module_enabled", False))
                try:
                    await poll_tenant_subscribers_cycle(t.id, is_isp)
                except Exception as e:
                    logger.warning(f"Error en ciclo de sondeo para tenant {t.name}: {e}")

        except asyncio.CancelledError:
            logger.info("Worker StaggeredSessionPoller cancelado.")
            break
        except Exception as exc:
            logger.error(f"Excepción en ciclo de StaggeredSessionPoller: {exc}", exc_info=True)

        await asyncio.sleep(interval)
