# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Worker 7: Gestor de Ciclo de Vida y Liberación Efímera de Sesiones (Hito 23.27).

Monitorea y purga las sesiones que entraron en período de gracia (35 segundos)
ante el cierre de pestaña/navegador y que no recibieron reactivación.
"""

import asyncio
import logging

from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import sweep_expired_closing_sessions

logger = logging.getLogger("session-lifecycle-worker")


async def sweep_all_tenants_closing_sessions() -> int:
    """Explora todas las colas de cierre por tenant en KeyDB y purga las expiradas."""
    redis = get_redis_client()
    total_purged = 0
    try:
        tenant_ids: set[str] = set()
        if hasattr(redis, "smembers"):
            indexed_tenants = await redis.smembers("rg:closing_tenants_set")
            if isinstance(indexed_tenants, (set, list, tuple)):
                for t_raw in indexed_tenants:
                    t_str = t_raw.decode("utf-8") if isinstance(t_raw, bytes) else str(t_raw)
                    if t_str:
                        tenant_ids.add(t_str)
        if not tenant_ids:
            # Fallback para conjuntos creados antes del índice o en pruebas unitarias
            if hasattr(redis, "scan_iter"):
                async for key_raw in redis.scan_iter(match="rg:*:closing_sessions_zset", count=200):
                    key_str = key_raw.decode("utf-8") if isinstance(key_raw, bytes) else str(key_raw)
                    parts = key_str.split(":")
                    if len(parts) >= 3:
                        tenant_ids.add(parts[1])
            elif hasattr(redis, "keys"):
                zset_keys = await redis.keys("rg:*:closing_sessions_zset")
                for key_raw in zset_keys:
                    key_str = key_raw.decode("utf-8") if isinstance(key_raw, bytes) else str(key_raw)
                    parts = key_str.split(":")
                    if len(parts) >= 3:
                        tenant_ids.add(parts[1])
        for tenant_id in sorted(tenant_ids):
            purged = await sweep_expired_closing_sessions(tenant_id)
            if purged:
                total_purged += len(purged)
                logger.info(
                    "Tenant %s: Purga de %d sesiones cerradas por navegador (sesiones: %s)",
                    tenant_id,
                    len(purged),
                    purged,
                )
    except Exception as exc:
        logger.error("Error durante barrido de ciclo de vida de sesiones: %s", exc)

    return total_purged


async def session_lifecycle_worker_loop() -> None:
    """Bucle asíncrono continuo de supervisión de sesiones cerradas por navegador."""
    logger.info("Iniciando Worker de Ciclo de Vida y Cierre Efímero de Sesiones (Hito 23.27)...")
    while True:
        try:
            await sweep_all_tenants_closing_sessions()
        except asyncio.CancelledError:
            logger.info("Worker de Ciclo de Vida de Sesiones cancelado.")
            break
        except Exception as exc:
            logger.error("Error inesperado en loop de sesión: %s", exc)

        await asyncio.sleep(10)
