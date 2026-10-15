# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from src.redis_layer.zero_metrics_monitor import (
    ALERT_HIGH_CPU,
    ALERT_ROUTER_DOWN,
    ALERT_ROUTER_UP,
    ALERT_SSL_MISMATCH,
    STATUS_DEGRADED,
    STATUS_OFFLINE,
    STATUS_ONLINE,
    STATUS_SSL_MISMATCH,
    evaluate_router_monitoring_cycle,
    get_default_monitor_state,
)


def test_default_monitor_state() -> None:
    epoch = 1700000000
    state = get_default_monitor_state(epoch)
    assert state["operational_status"] == STATUS_ONLINE
    assert state["consecutive_failures"] == "0"
    assert state["consecutive_high_cpu"] == "0"
    assert state["last_state_change_epoch"] == str(epoch)


def test_boundary_reachability_failures_offline_transition() -> None:
    # Ciclo 0: Estado inicial ONLINE
    state = get_default_monitor_state(1000)

    # Fallo 1: no debe pasar a OFFLINE
    new_status, alert, state = evaluate_router_monitoring_cycle(state, is_reachable=False, custom_epoch=1010)
    assert new_status == STATUS_ONLINE
    assert alert is None
    assert state["consecutive_failures"] == "1"

    # Fallo 2 (Límite inferior exacto: failures=2): debe permanecer ONLINE
    new_status, alert, state = evaluate_router_monitoring_cycle(state, is_reachable=False, custom_epoch=1020)
    assert new_status == STATUS_ONLINE
    assert alert is None
    assert state["consecutive_failures"] == "2"

    # Fallo 3 (Límite de transición exacto: failures=3): debe pasar a OFFLINE con alerta
    new_status, alert, state = evaluate_router_monitoring_cycle(state, is_reachable=False, custom_epoch=1030)
    assert new_status == STATUS_OFFLINE
    assert alert == ALERT_ROUTER_DOWN
    assert state["consecutive_failures"] == "3"
    assert state["last_state_change_epoch"] == "1030"

    # Fallo 4: Sigue en OFFLINE, pero no debe disparar alerta repetida
    new_status, alert, state = evaluate_router_monitoring_cycle(state, is_reachable=False, custom_epoch=1040)
    assert new_status == STATUS_OFFLINE
    assert alert is None
    assert state["consecutive_failures"] == "4"


def test_maintenance_window_suppresses_router_down_alert() -> None:
    state = get_default_monitor_state(1000)

    # 3 fallos consecutivos dentro de ventana de mantenimiento
    _, _, state = evaluate_router_monitoring_cycle(state, is_reachable=False, in_maintenance=True, custom_epoch=1010)
    _, _, state = evaluate_router_monitoring_cycle(state, is_reachable=False, in_maintenance=True, custom_epoch=1020)
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=False, in_maintenance=True, custom_epoch=1030
    )

    assert new_status == STATUS_OFFLINE
    assert alert is None  # Alerta suprimida
    assert state["in_maintenance_window"] == "true"


def test_router_recovery_online_triggers_router_up() -> None:
    # Iniciar en OFFLINE con 3 fallos
    state = get_default_monitor_state(1000)
    state["operational_status"] = STATUS_OFFLINE
    state["consecutive_failures"] = "3"

    # Recuperación exitosa
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, cpu_load_pct=25, custom_epoch=1040
    )

    assert new_status == STATUS_ONLINE
    assert alert == ALERT_ROUTER_UP
    assert state["consecutive_failures"] == "0"
    assert state["last_state_change_epoch"] == "1040"


def test_boundary_cpu_load_degraded_transition() -> None:
    state = get_default_monitor_state(1000)

    # CPU al 89% (Límite < 90%): no incrementa high_cpu_count
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, cpu_load_pct=89, custom_epoch=1010
    )
    assert new_status == STATUS_ONLINE
    assert alert is None
    assert state["consecutive_high_cpu"] == "0"

    # CPU al 90% (Límite exacto de carga alta): Ciclos 1, 2, 3
    for ep in (1020, 1030, 1040):
        new_status, alert, state = evaluate_router_monitoring_cycle(
            state, is_reachable=True, cpu_load_pct=90, custom_epoch=ep
        )
        assert new_status == STATUS_ONLINE
        assert alert is None

    assert state["consecutive_high_cpu"] == "3"

    # Ciclo 4 (Límite de transición exacto: high_cpu_count=4) -> DEGRADED_HIGH_LOAD
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, cpu_load_pct=95, custom_epoch=1050
    )
    assert new_status == STATUS_DEGRADED
    assert alert == ALERT_HIGH_CPU
    assert state["consecutive_high_cpu"] == "4"
    assert state["last_state_change_epoch"] == "1050"

    # Ciclo 5 al 95%: se mantiene DEGRADED, sin repetir alerta
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, cpu_load_pct=95, custom_epoch=1060
    )
    assert new_status == STATUS_DEGRADED
    assert alert is None

    # Reducción de CPU a nivel normal (ej. 40%) -> Regresa a ONLINE sin alerta DOWN/UP
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, cpu_load_pct=40, custom_epoch=1070
    )
    assert new_status == STATUS_ONLINE
    assert alert is None
    assert state["consecutive_high_cpu"] == "0"


def test_ssl_mismatch_transition() -> None:
    state = get_default_monitor_state(1000)

    # Disparo de SSL Mismatch
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, is_ssl_mismatch=True, custom_epoch=1010
    )
    assert new_status == STATUS_SSL_MISMATCH
    assert alert == ALERT_SSL_MISMATCH
    assert state["last_state_change_epoch"] == "1010"

    # Siguiente ciclo con SSL Mismatch repetido -> no repite alerta
    new_status, alert, state = evaluate_router_monitoring_cycle(
        state, is_reachable=True, is_ssl_mismatch=True, custom_epoch=1020
    )
    assert new_status == STATUS_SSL_MISMATCH
    assert alert is None
