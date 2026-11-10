# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Motor Safe Mode (Dead Man's Switch) anti-bloqueo para RouterOS v7+ usando /system/script y /system/scheduler."""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from src.mikrotik.client import MikrotikClientError, MikrotikRestClient
from src.mikrotik.normalizers import format_routeros_duration

logger = logging.getLogger(__name__)

_READONLY_ROS_KEYS: frozenset[str] = frozenset(
    {
        ".id",
        "*id",
        "id",
        "running",
        "dynamic",
        "invalid",
        "default",
        "builtin",
        "slave",
        "inactive",
        "rx-byte",
        "tx-byte",
        "rx-packet",
        "tx-packet",
        "rx-drop",
        "tx-drop",
        "rx-error",
        "tx-error",
        "fp-rx-byte",
        "fp-tx-byte",
        "fp-rx-packet",
        "fp-tx-packet",
        "actual-mtu",
        "l2mtu",
        "max-l2mtu",
        "mac-address",
        "orig-mac-address",
        "type",
        "default-name",
        "last-link-up-time",
        "last-link-down-time",
        "link-downs",
        "current-operator",
        "active-address",
        "expires-after",
    }
)


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
    """Formatea valores escalares a representación CLI compatible con RouterOS v7."""
    if isinstance(val, bool):
        return "yes" if val else "no"
    if isinstance(val, str) and val.lower() in {"true", "false"}:
        return "yes" if val.lower() == "true" else "no"
    if isinstance(val, (int, float)):
        return str(val)
    escaped = str(val).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _normalize_ros_key(key: str) -> str:
    return key.replace("_", "-")


def _extract_writable_pairs(
    before_state: dict[str, Any],
    mutated_keys: set[str] | list[str] | None = None,
) -> list[str]:
    """Filtra atributos de solo lectura y restringe a mutated_keys si se definen."""
    allowed_norm = (
        {_normalize_ros_key(k) for k in mutated_keys if k not in _READONLY_ROS_KEYS} if mutated_keys else None
    )
    items: list[str] = []
    for raw_k, v in before_state.items():
        norm_k = _normalize_ros_key(raw_k)
        if norm_k in _READONLY_ROS_KEYS or raw_k in _READONLY_ROS_KEYS or v is None:
            continue
        if allowed_norm is not None and norm_k not in allowed_norm and raw_k not in (mutated_keys or set()):
            continue
        items.append(f"{norm_k}={_format_cli_val(v)}")
    return items


def _build_set_command(
    clean_menu: str,
    item_id: str,
    before_state: dict[str, Any],
    mutated_keys: set[str] | list[str] | None = None,
) -> str:
    items = _extract_writable_pairs(before_state, mutated_keys)
    if not items and mutated_keys:
        for mk in mutated_keys:
            norm_k = _normalize_ros_key(mk)
            if norm_k not in _READONLY_ROS_KEYS:
                prev_val = before_state.get(norm_k, before_state.get(mk, ""))
                items.append(f"{norm_k}={_format_cli_val(prev_val)}")
    params_str = " ".join(items)
    target_selector = f'[find .id="{item_id}"]' if str(item_id).startswith("*") else f'[find name="{item_id}"]'
    return f"/{clean_menu}/set {target_selector} {params_str}".strip()


def _build_create_command(clean_menu: str, item_id: str | None, before_state: dict[str, Any] | None) -> str:
    if item_id:
        return f'/{clean_menu}/remove [find .id="{item_id}"]'
    if before_state:
        name = before_state.get("name")
        if name:
            return f'/{clean_menu}/remove [find name="{name}"]'
        comment = before_state.get("comment")
        if comment:
            return f'/{clean_menu}/remove [find comment="{comment}"]'
    return f"/{clean_menu}/remove [find]"


def _build_delete_command(clean_menu: str, item_id: str, before_state: dict[str, Any] | None = None) -> str:
    if before_state:
        items = _extract_writable_pairs(before_state)
        if items:
            return f"/{clean_menu}/add {' '.join(items)}"
    return f'/{clean_menu}/set [find .id="{item_id}"] disabled=no'


def build_rollback_command(
    menu_path: str,
    action: str,
    item_id: str | None = None,
    before_state: dict[str, Any] | None = None,
    mutated_keys: set[str] | list[str] | None = None,
) -> str:
    """Construye la instrucción CLI de RouterOS para revertir una operación de Safe Mode."""
    clean_menu = menu_path.strip("/")
    act = action.lower()
    if act in {"set", "modify", "patch"} and item_id and before_state is not None:
        return _build_set_command(clean_menu, item_id, before_state, mutated_keys=mutated_keys)
    if act in {"create", "put", "add"}:
        return _build_create_command(clean_menu, item_id, before_state)
    if act in {"delete", "remove"} and item_id:
        return _build_delete_command(clean_menu, item_id, before_state)
    return ":nothing"


def build_script_payload(job_name: str, rollback_cli: str) -> dict[str, Any]:
    """Genera el payload para crear el /system/script de reversión y autolimpieza."""
    source = (
        f":do {{ {rollback_cli} }} on-error={{}}; "
        f':do {{ /system/scheduler/remove [find name="{job_name}"] }} on-error={{}}; '
        f':do {{ /system/script/remove [find name="{job_name}"] }} on-error={{}}'
    )
    return {
        "name": job_name,
        "comment": "ROSGRID_DEADMAN_SWITCH_AUTO_ROLLBACK",
        "source": source,
    }


def build_scheduler_payload(
    job_name: str,
    rollback_cli: str,
    interval_seconds: int = 60,
) -> dict[str, Any]:
    """Genera el payload para crear el /system/scheduler de reversión automática."""
    interval_str = format_routeros_duration(interval_seconds)
    on_event = (
        f':do {{ /system/script/run [find name="{job_name}"] }} on-error={{}}; '
        f":do {{ {rollback_cli} }} on-error={{}}; "
        f':do {{ /system/scheduler/remove [find name="{job_name}"] }} on-error={{}}; '
        f':do {{ /system/script/remove [find name="{job_name}"] }} on-error={{}}'
    )
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
    """Inyecta el script y el scheduler de reversión en el MikroTik previo a ejecutar cambios sensibles."""
    name = job_name or generate_safemode_job_name()
    script_payload = build_script_payload(name, rollback_cli)
    try:
        await client.put("/system/script", json_data=script_payload)
    except Exception as exc:
        logger.debug("Creación opcional de /system/script '%s' omitida: %s", name, exc)

    payload = build_scheduler_payload(name, rollback_cli, interval_seconds)
    await client.put("/system/scheduler", json_data=payload)
    logger.info("SafeMode script+scheduler '%s' inyectado con intervalo %ds", name, interval_seconds)
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


async def _delete_ros_named_items(client: MikrotikRestClient, endpoint: str, job_name: str) -> bool:
    removed = False
    try:
        items = await client.get(endpoint, params={"name": job_name})
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and item.get("name", job_name) == job_name:
                    item_id = item.get(".id") or item.get("id")
                    if item_id:
                        await client.delete(f"{endpoint}/{item_id}")
                        removed = True
    except Exception as exc:
        logger.debug("Error limpiando %s '%s': %s", endpoint, job_name, exc)
    return removed


async def remove_deadmans_switch(
    client: MikrotikRestClient,
    job_name: str,
) -> bool:
    """Elimina el scheduler y el script de reversión una vez confirmados los cambios por el operador."""
    sched_removed = await _delete_ros_named_items(client, "/system/scheduler", job_name)
    await _delete_ros_named_items(client, "/system/script", job_name)
    if sched_removed:
        logger.info("SafeMode scheduler y script '%s' eliminados con éxito", job_name)
    return sched_removed


async def execute_rollback_on_router(
    client: MikrotikRestClient,
    job_name: str,
    menu: str,
    action: str,
    item_id: str | None,
    before_state: dict[str, Any] | None,
    mutated_keys: list[str] | None = None,
) -> bool:
    """Ejecuta la reversión inmediata en RouterOS vía REST/Script y limpia el scheduler/script."""
    reverted = False
    clean_menu = menu.strip("/")
    act = action.lower()
    try:
        if act in {"set", "modify", "patch"} and item_id and before_state:
            restore_payload: dict[str, Any] = {}
            target_keys = mutated_keys or list(before_state.keys())
            for k in target_keys:
                norm_k = _normalize_ros_key(k)
                if norm_k not in _READONLY_ROS_KEYS and (norm_k in before_state or k in before_state):
                    restore_payload[norm_k] = before_state.get(norm_k, before_state.get(k))
            if restore_payload:
                await client.patch(f"/{clean_menu}/{item_id}", json_data=restore_payload)
                reverted = True
        elif act in {"create", "put", "add"} and item_id:
            await client.delete(f"/{clean_menu}/{item_id}")
            reverted = True
        elif act in {"delete", "remove"} and before_state:
            recreate_payload = {
                _normalize_ros_key(k): v
                for k, v in before_state.items()
                if _normalize_ros_key(k) not in _READONLY_ROS_KEYS and v is not None
            }
            if recreate_payload:
                await client.put(f"/{clean_menu}", json_data=recreate_payload)
                reverted = True
    except Exception as exc:
        logger.warning("Fallback a /system/script/run para rollback '%s': %s", job_name, exc)

    if not reverted:
        try:
            await client.post("/system/script/run", json_data={".id": job_name})
            reverted = True
        except Exception as script_exc:
            logger.debug("El script '%s' ya fue ejecutado por el scheduler: %s", job_name, script_exc)

    await remove_deadmans_switch(client, job_name)
    return reverted


async def execute_with_safemode(
    client: MikrotikRestClient,
    rollback_cli: str,
    operation_fn: Callable[[], Awaitable[Any]],
    interval_seconds: int = 60,
    job_name: str | None = None,
    keep_alive_for_confirmation: bool = False,
) -> Any:
    """Aplica el protocolo Dead Man's Switch alrededor de una operación asíncrona."""
    name = await inject_deadmans_switch(
        client=client,
        rollback_cli=rollback_cli,
        interval_seconds=interval_seconds,
        job_name=job_name,
    )

    try:
        result = await operation_fn()
    except Exception:
        await remove_deadmans_switch(client, name)
        raise

    is_alive = await verify_connectivity(client)
    if not is_alive:
        logger.critical("Pérdida de conectividad tras cambio. Dejando expirar scheduler '%s'", name)
        raise SafeModeRollbackTriggeredError(name, interval_seconds)

    if not keep_alive_for_confirmation:
        await remove_deadmans_switch(client, name)
    return result
