# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller) de Clientes y Dispositivos FTTH.

Consulta periódicamente las tablas nativas de sesiones de RouterOS v7 (/ppp/active + /ip/dhcp-server/lease)
y verifica alcanzabilidad ICMP ligera cuando procede, aplicando contexto RLS por tenant, precarga ansiosa
selectinload(Router.vault, SubscriberDevice.ipv4_address), filtro delta de escritura cero en DB y emisión
reactiva de eventos DEVICE_STATUS_CHANGED vía Pub/Sub hacia WebSockets.
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.webfig_common import _create_client_from_vault
from src.core.config import settings
from src.db.session import async_session_maker, set_tenant_context
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.redis_layer.client import get_redis_client

logger = logging.getLogger("rosgrid-subscriber-poller")

DEFAULT_POLL_INTERVAL_SECONDS: int = 180
MIN_INTER_ROUTER_JITTER_SECONDS: float = 2.0


def _clean_mac_hex(raw_mac: Any) -> str:
    """Normaliza una dirección MAC eliminando separadores para cruce rápido en memoria."""
    if not raw_mac:
        return ""
    return "".join(ch for ch in str(raw_mac).strip().upper() if ch in "0123456789ABCDEF")


def _extract_ppp_single_item(item: dict[str, Any], active_identifiers: set[str]) -> None:
    name = str(item.get("name") or "").strip().lower()
    addr = str(item.get("address") or "").strip()
    caller_mac = _clean_mac_hex(item.get("caller-id"))
    if name:
        active_identifiers.add(name)
    if addr:
        active_identifiers.add(addr)
    if caller_mac:
        active_identifiers.add(caller_mac)


def _extract_ppp_active_identifiers(raw_active: Any, active_identifiers: set[str]) -> None:
    """Extrae usernames, direcciones IP y caller-id MAC de /ppp/active."""
    if not isinstance(raw_active, list):
        return
    for item in raw_active:
        if isinstance(item, dict):
            _extract_ppp_single_item(item, active_identifiers)


def _extract_dhcp_single_lease(item: dict[str, Any], active_identifiers: set[str]) -> None:
    st = str(item.get("status") or "").lower()
    if st not in ("bound", "active"):
        return
    addr = str(item.get("address") or item.get("active-address") or "").strip()
    mac = _clean_mac_hex(item.get("mac-address") or item.get("active-mac-address"))
    if addr:
        active_identifiers.add(addr)
    if mac:
        active_identifiers.add(mac)


def _extract_dhcp_lease_identifiers(raw_leases: Any, active_identifiers: set[str]) -> None:
    """Extrae direcciones IPv4 y MACs con estado bound/active desde /ip/dhcp-server/lease."""
    if not isinstance(raw_leases, list):
        return
    for item in raw_leases:
        if isinstance(item, dict):
            _extract_dhcp_single_lease(item, active_identifiers)


def _is_device_matched(dev: SubscriberDevice, active_identifiers: set[str]) -> bool:
    """Evalúa si un abonado aparece en el conjunto de sesiones/leases activos del router."""
    ip = str(getattr(dev, "assigned_ipv4", "") or "").strip()
    if ip and ip in active_identifiers:
        return True
    mac = _clean_mac_hex(getattr(dev, "onu_mac_address", ""))
    if mac and mac in active_identifiers:
        return True
    pppoe = str(getattr(dev, "pppoe_username", "") or getattr(dev, "endpoint_identifier", "") or "").strip().lower()
    return bool(pppoe and pppoe in active_identifiers)


def _parse_single_ping_packet(pkt: dict[str, Any]) -> bool | None:
    received = pkt.get("received")
    if received is not None:
        return int(received) > 0
    if pkt.get("status") in ("echo reply", None) and pkt.get("time"):
        return True
    if pkt.get("status") in ("timeout", "host unreachable", "net unreachable"):
        return False
    return None


async def _probe_device_icmp_alive(client: Any, target_ip: str) -> bool | None:
    """Realiza un sondeo ICMP rápido (count=1) cuando el cliente soporta POST /ping."""
    post_fn = getattr(client, "post", None)
    if post_fn is None:
        return None
    try:
        res = await asyncio.wait_for(
            post_fn("/ping", json_data={"address": target_ip, "count": 1, "interval": "200ms"}),
            timeout=3.0,
        )
        if not isinstance(res, list) or not res:
            return None
        for pkt in res:
            if isinstance(pkt, dict):
                parsed = _parse_single_ping_packet(pkt)
                if parsed is not None:
                    return parsed
    except Exception:
        return None
    return None


def _discard_device_identifiers(dev: SubscriberDevice, ip: str, active_identifiers: set[str]) -> None:
    """Purga todos los identificadores de sesión de un abonado (IP, MAC y usuario PPPoE) cuando falla ICMP."""
    active_identifiers.discard(ip)
    mac = _clean_mac_hex(getattr(dev, "onu_mac_address", ""))
    if mac:
        active_identifiers.discard(mac)
    for attr in ("pppoe_username", "endpoint_identifier"):
        val = str(getattr(dev, attr, "") or "").strip().lower()
        if val:
            active_identifiers.discard(val)


async def _probe_devices_icmp(
    client: Any,
    devices: list[SubscriberDevice],
    active_identifiers: set[str],
) -> None:
    for dev in devices:
        ip = str(getattr(dev, "assigned_ipv4", "") or "").strip()
        if not ip:
            continue
        icmp_alive = await _probe_device_icmp_alive(client, ip)
        if icmp_alive is True:
            active_identifiers.add(ip)
        elif icmp_alive is False:
            _discard_device_identifiers(dev, ip, active_identifiers)


async def _collect_router_active_identifiers(
    client: Any,
    is_isp_mode: bool,
    devices: list[SubscriberDevice],
    verify_icmp: bool = False,
) -> set[str]:
    """Consulta las tablas de sesiones de RouterOS (/ppp/active y /ip/dhcp-server/lease) y verifica ICMP."""
    active_identifiers: set[str] = set()
    if is_isp_mode:
        raw_active = await asyncio.wait_for(client.get("/ppp/active"), timeout=8.0)
        _extract_ppp_active_identifiers(raw_active, active_identifiers)
        # Si existen abonados no encontrados en /ppp/active, consultar también DHCP leases
        if any(not _is_device_matched(d, active_identifiers) for d in devices):
            try:
                raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
                _extract_dhcp_lease_identifiers(raw_leases, active_identifiers)
            except Exception:
                pass
    else:
        raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
        _extract_dhcp_lease_identifiers(raw_leases, active_identifiers)

    if verify_icmp:
        await _probe_devices_icmp(client, devices, active_identifiers)

    return active_identifiers


async def _publish_device_status_change(
    redis: Any,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    dev: SubscriberDevice,
    new_status: str,
    now_utc: datetime,
) -> None:
    """Publica el evento DEVICE_STATUS_CHANGED en el canal Pub/Sub del tenant."""
    pubsub_channel = f"rg:pubsub:events:{tenant_id}"
    event_payload = {
        "event_name": "DEVICE_STATUS_CHANGED",
        "payload": {
            "device_id": str(dev.id),
            "status": new_status,
            "router_id": str(router_id),
            "endpoint_identifier": dev.endpoint_identifier,
            "last_seen_at": now_utc.isoformat(),
        },
    }
    try:
        await redis.publish(pubsub_channel, json.dumps(event_payload))
    except Exception as e:
        logger.debug(f"Aviso publicando evento DEVICE_STATUS_CHANGED: {e}")


async def _is_router_cb_open(redis: Any, tenant_id: uuid.UUID, router_id: uuid.UUID) -> bool:
    cb_key = f"rg:{tenant_id}:diag:circuit:router:{router_id}"
    cb_state = await redis.get(cb_key)
    return bool(cb_state and cb_state in ("OPEN", b"OPEN"))


async def _apply_device_status_deltas(
    session: Any,
    redis: Any,
    tenant_id: uuid.UUID,
    router: Router,
    devices: list[SubscriberDevice],
    active_identifiers: set[str],
) -> int:
    changed_count = 0
    now_utc = datetime.now(UTC)
    for dev in devices:
        new_status = "ONLINE" if _is_device_matched(dev, active_identifiers) else "OFFLINE"
        if new_status != dev.last_reachability_status:
            dev.last_reachability_status = new_status
            dev.last_seen_at = now_utc
            changed_count += 1
            await _publish_device_status_change(redis, tenant_id, router.id, dev, new_status, now_utc)

    if changed_count > 0:
        await session.commit()
        logger.info(
            f"[Poller Delta] Router {router.display_name}: {changed_count} dispositivos cambiaron de estado."
        )
    return changed_count


async def _poll_single_router_sessions(
    session: Any,
    tenant_id: uuid.UUID,
    router: Router,
    is_isp_mode: bool,
    verify_icmp: bool = False,
) -> int:
    """Consulta híbrida de las tablas de sesiones en RouterOS v7 con filtro delta en base de datos."""
    redis = get_redis_client()
    if await _is_router_cb_open(redis, tenant_id, router.id):
        logger.debug(f"Router {router.display_name} en Circuit Breaker abierto. Omitiendo sondeo pasivo.")
        return 0

    try:
        client = _create_client_from_vault(router, tenant_id)
    except Exception as exc:
        logger.debug(f"No se pudo crear cliente para router {router.display_name}: {exc}")
        return 0

    stmt_devs = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.ipv4_address))
        .where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.router_id == router.id,
        )
    )
    devices = list((await session.execute(stmt_devs)).scalars().all())
    if not devices:
        return 0

    try:
        async with client:
            active_identifiers = await _collect_router_active_identifiers(
                client=client,
                is_isp_mode=is_isp_mode,
                devices=devices,
                verify_icmp=verify_icmp,
            )
    except Exception as exc:
        logger.warning(f"Error consultando tablas de sesiones en router {router.display_name}: {exc}")
        return 0

    return await _apply_device_status_deltas(
        session=session,
        redis=redis,
        tenant_id=tenant_id,
        router=router,
        devices=devices,
        active_identifiers=active_identifiers,
    )


async def poll_tenant_subscribers_cycle(tenant_id: uuid.UUID, is_isp_mode: bool) -> None:
    """Ejecuta el ciclo de sondeo híbrido escalonado para todos los routers de un tenant."""
    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin=False)
        stmt_routers = (
            select(Router)
            .options(selectinload(Router.vault))
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
        verify_icmp = bool(getattr(settings, "ROSGRID_SUBSCRIBER_ICMP_PROBE_ENABLED", True))
        base_delay = max(MIN_INTER_ROUTER_JITTER_SECONDS, interval / max(1, len(routers)))

        for r in routers:
            await _poll_single_router_sessions(
                session=session,
                tenant_id=tenant_id,
                router=r,
                is_isp_mode=is_isp_mode,
                verify_icmp=verify_icmp,
            )
            jitter = random.uniform(0.1, 0.8)
            await asyncio.sleep(base_delay + jitter)


async def _run_single_poller_cycle() -> None:
    async with async_session_maker() as session:
        await set_tenant_context(session, None, is_superadmin=True)
        stmt_t = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
        tenants = list((await session.execute(stmt_t)).scalars().all())

    for t in tenants:
        is_isp = bool(getattr(t, "isp_module_enabled", False))
        try:
            await poll_tenant_subscribers_cycle(t.id, is_isp)
        except Exception as e:
            logger.warning(f"Error en ciclo de sondeo para tenant {t.name}: {e}")


async def subscriber_status_poller_worker_loop() -> None:
    """Loop principal del Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller)."""
    logger.info("=== Iniciando Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller) ===")
    interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)

    while True:
        try:
            await _run_single_poller_cycle()
        except asyncio.CancelledError:
            logger.info("Worker StaggeredSessionPoller cancelado.")
            break
        except Exception as exc:
            logger.error(f"Excepción en ciclo de StaggeredSessionPoller: {exc}", exc_info=True)

        await asyncio.sleep(interval)
