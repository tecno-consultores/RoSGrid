# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

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
        # Claves de sorted set: rg:{tenant_id}:closing_sessions_zset
        zset_keys = await redis.keys("rg:*:closing_sessions_zset")
        for key_raw in zset_keys:
            key_str = key_raw.decode("utf-8") if isinstance(key_raw, bytes) else str(key_raw)
            parts = key_str.split(":")
            if len(parts) >= 3:
                tenant_id = parts[1]
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
