# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Motor Safe Mode (Dead Man's Switch) anti-bloqueo para RouterOS v7+ usando /system/scheduler."""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from src.mikrotik.client import MikrotikClientError, MikrotikRestClient
from src.mikrotik.normalizers import format_routeros_duration

logger = logging.getLogger(__name__)


class SafeModeError(MikrotikClientError):
    """Excepción base para fallos del motor Safe Mode."""


class SafeModeRollbackTriggeredError(SafeModeError):
    """Lanzada cuando un cambio corta la conectividad y se delega la reversión al scheduler."""

    def __init__(self, job_name: str, interval_seconds: int):
        self.job_name = job_name
        self.interval_seconds = interval_seconds
        super().__init__(
            f"El cambio aplicado interrumpió la conectividad con el MikroTik. "
            f"El scheduler '{job_name}' revertirá la configuración automáticamente en {interval_seconds}s."
        )


def generate_safemode_job_name(operation_id: str | None = None) -> str:
    """Genera un identificador único y determinista para el scheduler de reversión."""
    suffix = operation_id if operation_id else uuid.uuid4().hex[:8]
    return f"rosgrid-safemode-{suffix}"


def _format_cli_val(val: Any) -> str:
    if isinstance(val, bool):
        return "yes" if val else "no"
    if isinstance(val, (int, float)):
        return str(val)
    escaped = str(val).replace('"', '\\"')
    return f'"{escaped}"'


def _build_set_command(clean_menu: str, item_id: str, before_state: dict[str, Any]) -> str:
    items = []
    for k, v in before_state.items():
        if k not in {".id", "*id", "id"}:
            items.append(f"{k}={_format_cli_val(v)}")
    params_str = " ".join(items)
    return f"/{clean_menu}/set [find .id={item_id}] {params_str}".strip()


def _build_create_command(clean_menu: str, item_id: str | None, before_state: dict[str, Any] | None) -> str:
    if item_id:
        return f"/{clean_menu}/remove [find .id={item_id}]"
    comment = before_state.get("comment") if before_state else None
    if comment:
        return f'/{clean_menu}/remove [find comment="{comment}"]'
    return f"/{clean_menu}/remove [find]"


def _build_delete_command(clean_menu: str, item_id: str) -> str:
    return f"/{clean_menu}/set [find .id={item_id}] disabled=no"


def build_rollback_command(
    menu_path: str,
    action: str,
    item_id: str | None = None,
    before_state: dict[str, Any] | None = None,
) -> str:
    """Construye la instrucción CLI de RouterOS para revertir una operación de Safe Mode."""
    clean_menu = menu_path.strip("/")
    act = action.lower()
    if act in {"set", "modify", "patch"} and item_id and before_state:
        return _build_set_command(clean_menu, item_id, before_state)
    if act in {"create", "put", "add"}:
        return _build_create_command(clean_menu, item_id, before_state)
    if act in {"delete", "remove"} and item_id:
        return _build_delete_command(clean_menu, item_id)
    return ":nothing"


def build_scheduler_payload(
    job_name: str,
    rollback_cli: str,
    interval_seconds: int = 60,
) -> dict[str, Any]:
    """Genera el payload para crear el /system/scheduler de reversión automática."""
    interval_str = format_routeros_duration(interval_seconds)
    on_event = f':do {{ {rollback_cli} }} on-error={{}}; /system/scheduler/remove [find name="{job_name}"]'
    return {
        "name": job_name,
        "start-time": "startup",
        "interval": interval_str,
        "comment": "ROSGRID_DEADMAN_SWITCH_AUTO_ROLLBACK",
        "on-event": on_event,
    }


async def inject_deadmans_switch(
    client: MikrotikRestClient,
    rollback_cli: str,
    interval_seconds: int = 60,
    job_name: str | None = None,
) -> str:
    """Inyecta el scheduler de reversión en el MikroTik previo a ejecutar cambios sensibles."""
    name = job_name or generate_safemode_job_name()
    payload = build_scheduler_payload(name, rollback_cli, interval_seconds)
    await client.put("/system/scheduler", json_data=payload)
    logger.info("SafeMode scheduler '%s' inyectado con intervalo %ds", name, interval_seconds)
    return name


async def verify_connectivity(
    client: MikrotikRestClient,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> bool:
    """Verifica la supervivencia de la comunicación con el router tras un cambio sensible."""
    for attempt in range(1, max_retries + 1):
        try:
            res = await client.get("/system/identity")
            if res is not None:
                return True
        except Exception as exc:
            logger.warning("Intento %d/%d de verificación falló: %s", attempt, max_retries, exc)
        if attempt < max_retries:
            await asyncio.sleep(retry_delay)
    return False


async def remove_deadmans_switch(
    client: MikrotikRestClient,
    job_name: str,
) -> bool:
    """Elimina el scheduler de reversión una vez confirmada la supervivencia del router."""
    try:
        schedulers = await client.get("/system/scheduler", params={"name": job_name})
        if isinstance(schedulers, list) and schedulers:
            sched_id = schedulers[0].get(".id")
            if sched_id:
                await client.delete(f"/system/scheduler/{sched_id}")
                logger.info("SafeMode scheduler '%s' eliminado con éxito", job_name)
                return True
    except Exception as exc:
        logger.error("No se pudo eliminar el scheduler '%s': %s", job_name, exc)
    return False


async def execute_with_safemode(
    client: MikrotikRestClient,
    rollback_cli: str,
    operation_fn: Callable[[], Awaitable[Any]],
    interval_seconds: int = 60,
    job_name: str | None = None,
) -> Any:
    """Aplica el protocolo Dead Man's Switch completo alrededor de una operación asíncrona."""
    name = await inject_deadmans_switch(
        client=client,
        rollback_cli=rollback_cli,
        interval_seconds=interval_seconds,
        job_name=job_name,
    )

    result = await operation_fn()

    is_alive = await verify_connectivity(client)
    if not is_alive:
        logger.critical("Pérdida de conectividad tras cambio. Dejando expirar scheduler '%s'", name)
        raise SafeModeRollbackTriggeredError(name, interval_seconds)

    await remove_deadmans_switch(client, name)
    return result
