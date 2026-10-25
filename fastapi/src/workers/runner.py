# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Orquestador Principal de Workers en Segundo Plano (rosgrid-worker)."""

import asyncio
import logging
import signal
import sys

from src.redis_layer.client import close_redis_client
from src.workers.alert_dispatcher_worker import alert_dispatcher_worker_loop
from src.workers.health_monitor_worker import health_monitor_worker_loop
from src.workers.nightly_backup_worker import nightly_backup_worker_loop
from src.workers.session_lifecycle_worker import session_lifecycle_worker_loop
from src.workers.subscriber_status_poller import subscriber_status_poller_worker_loop
from src.workers.syslog_collector import syslog_collector_worker_loop
from src.workers.vault_rotation_worker import vault_rotation_worker_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rosgrid-workers")


def _setup_signal_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass


async def main_workers_runner() -> None:
    """Inicia concurrentemente los workers de RoSGrid y gestiona el apagado ordenado."""
    logger.info("=== Iniciando Orquestador de Workers RoSGrid ===")
    stop_event = asyncio.Event()
    _setup_signal_handlers(stop_event)

    tasks = [
        asyncio.create_task(health_monitor_worker_loop(), name="HealthMonitorWorker"),
        asyncio.create_task(alert_dispatcher_worker_loop(), name="AlertDispatcherWorker"),
        asyncio.create_task(nightly_backup_worker_loop(), name="NightlyBackupWorker"),
        asyncio.create_task(vault_rotation_worker_loop(), name="VaultRotationWorker"),
        asyncio.create_task(syslog_collector_worker_loop(), name="SyslogCollectorWorker"),
        asyncio.create_task(subscriber_status_poller_worker_loop(), name="SubscriberStatusPollerWorker"),
        asyncio.create_task(session_lifecycle_worker_loop(), name="SessionLifecycleWorker"),
    ]

    try:
        await stop_event.wait()
        logger.info("Señal de parada recibida. Cancelando workers...")
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await close_redis_client()
        logger.info("=== Todos los workers finalizados ordenadamente ===")


def main() -> None:
    try:
        asyncio.run(main_workers_runner())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
