# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import time
from typing import Any

STATUS_ONLINE = "ONLINE"
STATUS_DEGRADED = "DEGRADED_HIGH_LOAD"
STATUS_OFFLINE = "OFFLINE"
STATUS_SSL_MISMATCH = "SSL_MISMATCH"

ALERT_ROUTER_DOWN = "ROUTER_DOWN"
ALERT_ROUTER_UP = "ROUTER_UP"
ALERT_HIGH_CPU = "HIGH_CPU"
ALERT_SSL_MISMATCH = "SSL_MISMATCH"


def get_default_monitor_state(now_epoch: int) -> dict[str, str]:
    return {
        "operational_status": STATUS_ONLINE,
        "consecutive_failures": "0",
        "consecutive_high_cpu": "0",
        "last_cpu_load_pct": "0",
        "last_free_memory_pct": "100",
        "in_maintenance_window": "false",
        "last_state_change_epoch": str(now_epoch),
        "last_check_epoch": str(now_epoch),
    }


def _process_failure(prev_status: str, failures: int, in_maint: bool, now_epoch: int) -> tuple[str, str | None, int]:
    failures += 1
    if failures >= 3 and prev_status != STATUS_OFFLINE:
        alert = None if in_maint else ALERT_ROUTER_DOWN
        return STATUS_OFFLINE, alert, now_epoch
    return prev_status, None, 0


def _process_success_cpu(
    prev_status: str, cpu_load: int, high_cpu_count: int, now_epoch: int
) -> tuple[str, str | None, int, int]:
    if cpu_load >= 90:
        high_cpu_count += 1
        if high_cpu_count >= 4 and prev_status != STATUS_DEGRADED:
            return STATUS_DEGRADED, ALERT_HIGH_CPU, high_cpu_count, now_epoch
        return prev_status, None, high_cpu_count, 0

    # CPU normal
    if prev_status in (STATUS_OFFLINE, STATUS_DEGRADED):
        alert = ALERT_ROUTER_UP if prev_status == STATUS_OFFLINE else None
        return STATUS_ONLINE, alert, 0, now_epoch

    return STATUS_ONLINE, None, 0, 0


def evaluate_router_monitoring_cycle(
    current_state: dict[str, str] | None,
    is_reachable: bool,
    cpu_load_pct: int = 0,
    free_memory_pct: int = 100,
    is_ssl_mismatch: bool = False,
    in_maintenance: bool = False,
    custom_epoch: int | None = None,
) -> tuple[str, str | None, dict[str, str]]:
    now_epoch = custom_epoch if custom_epoch is not None else int(time.time())
    state = dict(current_state or get_default_monitor_state(now_epoch))

    prev_status = state.get("operational_status", STATUS_ONLINE)
    failures = int(state.get("consecutive_failures", "0"))
    high_cpu_count = int(state.get("consecutive_high_cpu", "0"))
    last_change_epoch = int(state.get("last_state_change_epoch", str(now_epoch)))

    if is_ssl_mismatch:
        new_status = STATUS_SSL_MISMATCH
        alert = ALERT_SSL_MISMATCH if prev_status != STATUS_SSL_MISMATCH else None
        last_change_epoch = now_epoch if prev_status != STATUS_SSL_MISMATCH else last_change_epoch
    elif not is_reachable:
        new_status, alert, change_epoch = _process_failure(prev_status, failures, in_maintenance, now_epoch)
        failures += 1
        if change_epoch:
            last_change_epoch = change_epoch
    else:
        failures = 0
        new_status, alert, high_cpu_count, change_epoch = _process_success_cpu(
            prev_status, cpu_load_pct, high_cpu_count, now_epoch
        )
        if change_epoch:
            last_change_epoch = change_epoch

    state.update(
        {
            "operational_status": new_status,
            "consecutive_failures": str(failures),
            "consecutive_high_cpu": str(high_cpu_count),
            "last_cpu_load_pct": str(cpu_load_pct),
            "last_free_memory_pct": str(free_memory_pct),
            "in_maintenance_window": "true" if in_maintenance else "false",
            "last_state_change_epoch": str(last_change_epoch),
            "last_check_epoch": str(now_epoch),
        }
    )
    return new_status, alert, state


async def write_monitoring_state_pipeline(
    redis: Any,
    tenant_id: Any,
    router_id: Any,
    updated_state: dict[str, str],
    ttl_seconds: int = 86400,
) -> None:
    """Escribe el estado del monitor en KeyDB mediante un pipeline atómico de alto rendimiento."""
    state_key = f"rg:{tenant_id}:mon_state:{router_id}"
    try:
        pipe = redis.pipeline(transaction=False)
        if hasattr(pipe, "hset") and callable(getattr(pipe, "hset", None)):
            pipe.hset(state_key, mapping=updated_state)
            pipe.expire(state_key, ttl_seconds)
            await pipe.execute()
            return
    except Exception:  # nosec B110
        pass
    await redis.hset(state_key, mapping=updated_state)
