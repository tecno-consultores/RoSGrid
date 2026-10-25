# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias de detección determinista de Syslog RouterOS v7 basadas en fixtures reales (Hito 24)."""

import json
from pathlib import Path

from src.api.v1.inventory_helpers import inspect_router_syslog_config

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "mikrotik"


def test_factory_default_routeros_must_evaluate_false() -> None:
    """Verifica que un router con la configuración de fábrica de RouterOS v7 NO se marque con Syslog activo."""
    fixture_path = FIXTURES_DIR / "factory_default_logging.json"
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    # De fábrica existe la acción 'remote' con 0.0.0.0, pero NO es de RoSGrid ni tiene regla activa
    result = inspect_router_syslog_config(data["actions"], data["rules"])
    assert result is False, "Un router de fábrica no debe reportar Syslog activo jamás"


def test_rosgrid_configured_routeros_must_evaluate_true() -> None:
    """Verifica que un router con la acción canónica 'rosgridsyslog' y regla activa se marque con Syslog activo."""
    fixture_path = FIXTURES_DIR / "rosgrid_configured_logging.json"
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    result = inspect_router_syslog_config(data["actions"], data["rules"])
    assert result is True, "Un router enrolado con la plantilla canónica debe reportar Syslog activo"


def test_disabled_rosgrid_rule_must_evaluate_false() -> None:
    """Verifica que si la regla de RoSGrid existe pero está deshabilitada (disabled=true), retorne False."""
    fixture_path = FIXTURES_DIR / "disabled_rosgrid_logging.json"
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    result = inspect_router_syslog_config(data["actions"], data["rules"])
    assert result is False, "Una regla deshabilitada no debe reportar Syslog activo"


def test_edge_cases_empty_or_invalid_inputs() -> None:
    """Verifica la robustez de inspect_router_syslog_config ante entradas nulas, vacías o malformadas."""
    assert inspect_router_syslog_config([], []) is False
    assert inspect_router_syslog_config(None, None) is False
    assert inspect_router_syslog_config([{"name": "rosgridsyslog", "target": "remote", "remote": "0.0.0.0"}], []) is False
    assert inspect_router_syslog_config([{"name": "rosgridsyslog", "target": "remote", "remote": ""}], []) is False
    assert inspect_router_syslog_config(
        [{"name": "rosgridsyslog", "target": "remote", "remote": "10.0.0.1"}],
        [{"action": "rosgridsyslog", "disabled": "true"}],
    ) is False
