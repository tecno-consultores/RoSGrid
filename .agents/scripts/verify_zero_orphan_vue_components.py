#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""
verify_zero_orphan_vue_components.py — Invariante de Cero Componentes Vue Huérfanos.

Audita que cada archivo .vue en vue3/src posea su correspondiente suite .unit.ts
dedicada o esté directamente testeado en una suite unitaria activa.
"""

import os
import sys

def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    vue_src = os.path.join(repo_root, "vue3", "src")
    
    if not os.path.exists(vue_src):
        print(f"❌ Error: Directorio no encontrado: {vue_src}")
        return 1

    vue_files = []
    for root, _, files in os.walk(vue_src):
        for f in files:
            if f.endswith(".vue"):
                vue_files.append(os.path.join(root, f))

    unit_files = []
    for root, _, files in os.walk(vue_src):
        for f in files:
            if f.endswith(".unit.ts"):
                unit_files.append(os.path.join(root, f))

    orphans = []
    for vf in sorted(vue_files):
        rel_vf = os.path.relpath(vf, repo_root)
        base = os.path.basename(vf)
        name = base[:-4]
        
        # 1. Comprobación directa: <Component>.unit.ts o variaciones de capitalización
        direct = vf[:-4] + ".unit.ts"
        lower_direct = os.path.join(os.path.dirname(vf), name[0].lower() + name[1:] + ".unit.ts")
        upper_direct = os.path.join(os.path.dirname(vf), name[0].upper() + name[1:] + ".unit.ts")
        
        if os.path.exists(direct) or os.path.exists(lower_direct) or os.path.exists(upper_direct):
            continue
            
        # 2. Comprobación de inclusión/montaje en alguna suite .unit.ts
        found = False
        for uf in unit_files:
            try:
                with open(uf, "r", encoding="utf-8") as ufile:
                    content = ufile.read()
                    if base in content or f"'{name}'" in content or f'"{name}"' in content or f" {name} " in content:
                        found = True
                        break
            except Exception:
                continue

        if not found:
            orphans.append(rel_vf)

    print(f"📊 Componentes Vue auditados: {len(vue_files)}")
    print(f"📊 Suites de pruebas .unit.ts: {len(unit_files)}")

    if orphans:
        print(f"\n❌ Se detectaron {len(orphans)} componente(s) .vue huérfano(s) sin pruebas unitarias:")
        for o in orphans:
            print(f"   - {o}")
        print("\nDirectiva Incumplida: Invariante de Cero Componentes Vue Huérfanos (.agents/rules/mandatory_qa_pyramid_and_doc_sync.md)")
        return 1

    print("✔ Cero componentes .vue huérfanos. 100% de componentes y vistas cuentan con pruebas unitarias.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
