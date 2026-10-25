#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Validador estricto de integridad para archivos JSON (detector de claves duplicadas).

Verifica que ningún archivo JSON contenga claves colisionadas o duplicadas en el mismo nivel,
evitando sobreescrituras silenciosas en diccionarios de internacionalización (i18n).
"""

import json
import os
import sys
from pathlib import Path


def detect_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    duplicates: list[str] = []
    for key, value in pairs:
        if key in result:
            duplicates.append(key)
        result[key] = value
    if duplicates:
        raise ValueError(f"Claves duplicadas detectadas en el mismo nivel: {sorted(set(duplicates))}")
    return result


def validate_file(filepath: Path) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f, object_pairs_hook=detect_duplicate_keys)
        return True
    except ValueError as ve:
        print(f"❌ ERROR EN {filepath}: {ve}", file=sys.stderr)
        return False
    except json.JSONDecodeError as jde:
        print(f"❌ ERROR SINTÁCTICO EN {filepath}: {jde}", file=sys.stderr)
        return False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    locales_dir = repo_root / "vue3" / "src" / "locales"

    target_files = list(locales_dir.glob("*.json"))
    if not target_files:
        print(f"⚠️ No se encontraron archivos JSON en {locales_dir}", file=sys.stderr)
        return 0

    all_passed = True
    print("🔍 Verificando integridad de diccionarios JSON (anti-colisión de claves)...")
    for f in sorted(target_files):
        rel_path = f.relative_to(repo_root)
        if validate_file(f):
            print(f"  ✔ {rel_path}: Sin claves duplicadas (Válido)")
        else:
            all_passed = False

    if not all_passed:
        print("\n❌ Se detectaron colisiones de claves en archivos de traducción.", file=sys.stderr)
        return 1

    print("✔ 100% de archivos JSON libres de colisiones de claves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
