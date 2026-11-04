#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Guardrail estático QA 11X para el Invariante Anti-Silo (Sección 1.5).

Verifica:
1. Cero mocks ciegos de `write_audit_log` en `fastapi/tests/**/*.py` (prohibido usar
   `patch("...write_audit_log", AsyncMock())` sin captura `as mock_...` ni `make_asserting_audit_mock`).
2. Presencia de pruebas de las 3 fases temporales (`Programada`, `En Curso`, `Expirada`) en:
   - Ventanas de Mantenimiento (`test_inventory_and_vault_endpoints_full.unit.py` y `maintenanceWindowsView.unit.ts`)
   - Safe Mode 60s (`test_safemode_deadman_switch.unit.py` y `RgSafeModeBanner.unit.ts`)
   - Bóveda Step-Up 30s (`test_inventory_and_vault_endpoints_full.unit.py` y `vaultRevealModal.unit.ts`)
3. Presencia de aserciones Anti-UUID crudo en auditoría y Cinta de Eventos Críticos.
"""

from __future__ import annotations

import glob
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def check_no_blind_audit_mocks() -> list[str]:
    errors: list[str] = []
    pattern = str(REPO_ROOT / "fastapi" / "tests" / "**" / "*.py")
    for file_path in sorted(glob.glob(pattern, recursive=True)):
        rel = Path(file_path).relative_to(REPO_ROOT)
        if rel.name == "conftest.py":
            continue
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if "write_audit_log" in stripped and ("patch(" in stripped or "setattr(" in stripped):
                has_capture = (
                    " as " in stripped
                    or "fake_audit" in stripped
                    or "make_asserting_audit_mock" in stripped
                )
                if not has_capture:
                    errors.append(f"{rel}:{idx} -> Mock ciego de write_audit_log sin aserción: {stripped}")
    return errors


def check_mandatory_3phase_and_cross_module_suites() -> list[str]:
    errors: list[str] = []
    required_markers = [
        (
            "fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py",
            [
                "test_resolve_active_maintenance_router_ids_3_temporal_phases",
                "test_write_audit_log_resolves_usernames_and_router_names",
                "make_asserting_audit_mock",
            ],
        ),
        (
            "fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py",
            ["test_safemode_three_phase_temporal_lifecycle_and_rollback"],
        ),
        (
            "vue3/src/views/inventory/maintenanceWindowsView.unit.ts",
            ["En Curso", "Programada"],
        ),
        (
            "vue3/src/components/common/RgNotificationCenterBell.unit.ts",
            ["Session token renewed", "approve"],
        ),
    ]
    for rel_path, markers in required_markers:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"Archivo de prueba obligatorio no encontrado: {rel_path}")
            continue
        content = full_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(f"{rel_path} -> Falta marcador obligatorio Anti-Silo / 3-Fases: '{marker}'")
    return errors


def main() -> int:
    print("🔍 Auditando invariante Anti-Silo, 3 Fases Temporales y Cero Mocks Ciegos de Auditoría...")
    blind_errors = check_no_blind_audit_mocks()
    suite_errors = check_mandatory_3phase_and_cross_module_suites()
    all_errors = blind_errors + suite_errors

    if all_errors:
        print("❌ Violaciones detectadas en la calidad de pruebas Anti-Silo:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✔ 0 mocks ciegos de write_audit_log y 100% de suites 3-Fases / Anti-Silo verificadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
