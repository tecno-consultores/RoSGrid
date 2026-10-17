# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Multiplexor de Telemetría Efímera en Vivo: Poller bajo demanda gobernado por SCARD en Redis."""

import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.webfig_common import _create_client_from_vault
from src.db.session import async_session_maker
from src.mikrotik.client import MikrotikRestClient
from src.models.inventory import Router
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)

_ACTIVE_POLLERS: dict[str, asyncio.Task[None]] = {}
_LAST_SNAPSHOTS: dict[str, tuple[float, dict[str, dict[str, int]]]] = {}


async def _resolve_router_client(tenant_id: uuid.UUID, router_id: uuid.UUID) -> MikrotikRestClient | None:
    async with async_session_maker() as session:
        stmt = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.id == router_id, Router.tenant_id == tenant_id)
        )
        router_obj = (await session.execute(stmt)).scalar_one_or_none()
        if not router_obj or not router_obj.vault:
            return None
        return _create_client_from_vault(router_obj, tenant_id)


async def _fetch_raw_telemetry(
    client: MikrotikRestClient,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    res_task = client.get("system/resource")
    health_task = client.get("system/health")
    iface_task = client.get("interface?.proplist=.id,name,type,running,disabled,rx-byte,tx-byte,rx-packet,tx-packet")
    results = await asyncio.gather(res_task, health_task, iface_task, return_exceptions=True)
    res_raw: Any = results[0]
    health_raw: Any = results[1]
    iface_raw: Any = results[2]

    res_dict = res_raw if isinstance(res_raw, dict) else {}
    health_dict = health_raw if isinstance(health_raw, dict) else {}
    iface_list = iface_raw if isinstance(iface_raw, list) else []
    return res_dict, health_dict, iface_list


def _compute_iface_delta(cur: dict[str, Any], prev: dict[str, int], dt: float) -> dict[str, Any]:
    rx_cur = int(cur.get("rx-byte", 0))
    tx_cur = int(cur.get("tx-byte", 0))
    rx_p_cur = int(cur.get("rx-packet", 0))
    tx_p_cur = int(cur.get("tx-packet", 0))

    rx_diff = max(0, rx_cur - prev.get("rx", rx_cur))
    tx_diff = max(0, tx_cur - prev.get("tx", tx_cur))
    rx_p_diff = max(0, rx_p_cur - prev.get("rx_p", rx_p_cur))
    tx_p_diff = max(0, tx_p_cur - prev.get("tx_p", tx_p_cur))

    return {
        "name": cur.get("name", "unknown"),
        "running": str(cur.get("running", "false")).lower() in ("true", "yes"),
        "disabled": str(cur.get("disabled", "false")).lower() in ("true", "yes"),
        "rx_bps": int((rx_diff * 8) / dt) if dt > 0 else 0,
        "tx_bps": int((tx_diff * 8) / dt) if dt > 0 else 0,
        "rx_pps": int(rx_p_diff / dt) if dt > 0 else 0,
        "tx_pps": int(tx_p_diff / dt) if dt > 0 else 0,
    }


def _process_interfaces(
    ifaces_raw: list[dict[str, Any]],
    prev_snap: dict[str, dict[str, int]],
    dt: float,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    result: list[dict[str, Any]] = []
    new_snap: dict[str, dict[str, int]] = {}
    for item in ifaces_raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        if not name:
            continue
        prev = prev_snap.get(name, {})
        delta = _compute_iface_delta(item, prev, dt)
        result.append(delta)
        new_snap[name] = {
            "rx": int(item.get("rx-byte", 0)),
            "tx": int(item.get("tx-byte", 0)),
            "rx_p": int(item.get("rx-packet", 0)),
            "tx_p": int(item.get("tx-packet", 0)),
        }
    return result, new_snap


def _build_telemetry_frame(
    router_id: uuid.UUID,
    res: dict[str, Any],
    health: dict[str, Any],
    ifaces: list[dict[str, Any]],
) -> dict[str, Any]:
    total_mem = int(res.get("total-memory", 1))
    free_mem = int(res.get("free-memory", 0))
    used_pct = round(((total_mem - free_mem) / total_mem) * 100) if total_mem > 0 else 0
    free_pct = round((free_mem / total_mem) * 100) if total_mem > 0 else 100

    return {
        "type": "TELEMETRY_TICK",
        "router_id": str(router_id),
        "timestamp_iso": datetime.now(UTC).isoformat(),
        "system": {
            "uptime": res.get("uptime", "unknown"),
            "cpu_load_pct": int(res.get("cpu-load", 0)),
            "cpu_count": int(res.get("cpu-count", 1)),
            "cpu_frequency_mhz": int(res.get("cpu-frequency", 0)) if "cpu-frequency" in res else None,
            "free_memory_bytes": free_mem,
            "total_memory_bytes": total_mem,
            "memory_used_pct": used_pct,
            "free_memory_pct": free_pct,
            "free_hdd_bytes": int(res.get("free-hdd-space", 0)),
            "total_hdd_bytes": int(res.get("total-hdd-space", 0)),
            "temperature_c": float(health.get("temperature", 0.0)) if "temperature" in health else None,
            "voltage_v": float(health.get("voltage", 0.0)) if "voltage" in health else None,
        },
        "interfaces": ifaces,
    }


async def _poll_loop(tenant_id: uuid.UUID, router_id: uuid.UUID) -> None:
    poller_key = f"{tenant_id}:{router_id}"
    redis = get_redis_client()
    subs_key = f"rg:{tenant_id}:ws_subs:{router_id}"
    channel = f"rg:pubsub:telemetry:{tenant_id}:{router_id}"

    client = await _resolve_router_client(tenant_id, router_id)
    if not client:
        logger.warning("No se pudo obtener cliente MikroTik para telemetría: %s", router_id)
        _ACTIVE_POLLERS.pop(poller_key, None)
        return

    try:
        while True:
            subs_count = await redis.scard(subs_key)
            if subs_count <= 0:
                break

            now = time.time()
            prev_time, prev_snap = _LAST_SNAPSHOTS.get(poller_key, (now - 2.0, {}))
            dt = max(0.5, now - prev_time)

            res, health, ifaces_raw = await _fetch_raw_telemetry(client)
            ifaces_metrics, new_snap = _process_interfaces(ifaces_raw, prev_snap, dt)
            _LAST_SNAPSHOTS[poller_key] = (now, new_snap)

            frame = _build_telemetry_frame(router_id, res, health, ifaces_metrics)
            await redis.publish(channel, json.dumps(frame))
            await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.error("Error en bucle de telemetría para router %s: %s", router_id, exc)
    finally:
        _ACTIVE_POLLERS.pop(poller_key, None)
        _LAST_SNAPSHOTS.pop(poller_key, None)
        await client.close()


def ensure_poller_active(tenant_id: uuid.UUID, router_id: uuid.UUID) -> None:
    """Activa el poller bajo demanda si no está ya en ejecución."""
    poller_key = f"{tenant_id}:{router_id}"
    task = _ACTIVE_POLLERS.get(poller_key)
    if task is None or task.done():
        _ACTIVE_POLLERS[poller_key] = asyncio.create_task(_poll_loop(tenant_id, router_id))


def cancel_poller_task(tenant_id: uuid.UUID, router_id: uuid.UUID) -> None:
    """Cancela inmediatamente el poller si ya no hay suscriptores."""
    poller_key = f"{tenant_id}:{router_id}"
    task = _ACTIVE_POLLERS.pop(poller_key, None)
    if task and not task.done():
        task.cancel()
