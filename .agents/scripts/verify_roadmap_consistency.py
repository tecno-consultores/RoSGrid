#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""verify_roadmap_consistency.py — Validador de Consistencia ROADMAP.md y ACTIVE_TASK.md.

Audita de forma bidireccional y determinista:
1. Coherencia interna en ROADMAP.md:
   - Que cada hito listado en la tabla de resumen superior coincida exactamente
     en estado (Completado vs Pendiente vs En Progreso) y porcentaje con las
     tareas marcadas ([x] vs [ ]) en las secciones detalladas correspondientes.
   - Que un hito con 100% de tareas completadas NO figure como Pendiente / 0%.
   - Que un hito sin tareas completadas NO figure como Completado / 100%.
   - Que el encabezado de sección (## ✅ vs ## ⏳ vs ## 🚧) coincida con el estado.
2. Coherencia operativa en .agents/ACTIVE_TASK.md:
   - Que el archivo exista y declare un estado formal (COMPLETED vs IN_PROGRESS).
   - Que si está marcado como COMPLETED (100%), no contenga casillas pendientes '- [ ]'.
   - Que si está IN_PROGRESS, tenga tareas o fases declaradas.

Ejecución determinista estática en < 1 segundo (sin dependencias externas).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_roadmap_table(content: str) -> List[Dict[str, Any]]:
    """Extrae las filas de la tabla de resumen de hitos en ROADMAP.md."""
    hitos: List[Dict[str, Any]] = []

    # Busca la tabla de resumen (ej. | **Hito 1** | ... | Estado | Progreso |)
    # Patrón flexible que detecta filas de tabla con 'Hito X' o '**Hito X**'
    row_pattern = re.compile(
        r"\|\s*\*{0,2}Hito\s+([0-9]+(?:\.[0-9]+)?)\*{0,2}\s*\|([^|]+)\|([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|",
        re.IGNORECASE,
    )

    for line in content.splitlines():
        line_clean = line.strip()
        if not line_clean.startswith("|"):
            continue
        match = row_pattern.search(line_clean)
        if match:
            hito_num = match.group(1).strip()
            nombre = match.group(2).strip()
            especificacion = match.group(3).strip()
            estado = match.group(4).strip()
            progreso_str = match.group(5).strip().replace("`", "").replace("%", "").strip()

            try:
                progreso_num = int(float(progreso_str))
            except ValueError:
                progreso_num = -1

            hitos.append(
                {
                    "hito_num": hito_num,
                    "nombre": nombre,
                    "spec": especificacion,
                    "estado_raw": estado,
                    "is_completed": "completado" in estado.lower() or "✅" in estado,
                    "is_pending": "pendiente" in estado.lower() or "⏳" in estado,
                    "is_in_progress": "progreso" in estado.lower() or "curso" in estado.lower() or "🚧" in estado,
                    "progreso_pct": progreso_num,
                    "line": line_clean,
                }
            )

    return hitos


def parse_roadmap_sections(content: str) -> Dict[str, Dict[str, Any]]:
    """Extrae las secciones de hitos y cuenta sus casillas [x] y [ ]."""
    sections: Dict[str, Dict[str, Any]] = {}

    # Divide por encabezados de segundo nivel: ## [icon] Hito X: ...
    section_header_pattern = re.compile(
        r"^##\s+([^\w]*?)\s*Hito\s+([0-9]+(?:\.[0-9]+)?)\s*[:—\-]\s*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    lines = content.splitlines()
    current_hito: Optional[str] = None
    current_header_icon: str = ""
    current_title: str = ""
    current_lines: List[str] = []

    for line in lines:
        header_match = section_header_pattern.match(line.strip())
        if header_match:
            if current_hito is not None:
                sections[current_hito] = _analyze_section_tasks(
                    current_hito, current_header_icon, current_title, current_lines
                )
            current_header_icon = header_match.group(1).strip()
            current_hito = header_match.group(2).strip()
            current_title = header_match.group(3).strip()
            current_lines = []
        elif current_hito is not None:
            # Si encontramos otro encabezado ## que no sea Hito, cerramos
            if line.strip().startswith("## ") and not line.strip().startswith("## ---"):
                sections[current_hito] = _analyze_section_tasks(
                    current_hito, current_header_icon, current_title, current_lines
                )
                current_hito = None
                current_lines = []
            else:
                current_lines.append(line)

    if current_hito is not None:
        sections[current_hito] = _analyze_section_tasks(
            current_hito, current_header_icon, current_title, current_lines
        )

    return sections


def _analyze_section_tasks(
    hito_num: str, header_icon: str, title: str, lines: List[str]
) -> Dict[str, Any]:
    """Cuenta casillas de verificación dentro del cuerpo de una sección de hito."""
    total_tasks = 0
    completed_tasks = 0

    for line in lines:
        stripped = line.strip()
        if re.match(r"^-\s*\[x\]", stripped, re.IGNORECASE):
            total_tasks += 1
            completed_tasks += 1
        elif re.match(r"^-\s*\[\s*\]", stripped):
            total_tasks += 1

    pct = 0
    if total_tasks > 0:
        pct = int((completed_tasks / total_tasks) * 100)

    return {
        "hito_num": hito_num,
        "header_icon": header_icon,
        "title": title,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "calculated_pct": pct,
        "is_all_completed": total_tasks > 0 and completed_tasks == total_tasks,
        "is_all_pending": total_tasks > 0 and completed_tasks == 0,
        "is_in_progress": total_tasks > 0 and 0 < completed_tasks < total_tasks,
    }


def validate_roadmap_consistency(roadmap_path: Path) -> List[str]:
    """Comprueba la consistencia entre la tabla de resumen y las secciones de ROADMAP.md."""
    if not roadmap_path.is_file():
        return [f"Archivo no encontrado: {roadmap_path}"]

    content = roadmap_path.read_text(encoding="utf-8")
    table_hitos = parse_roadmap_table(content)
    sections = parse_roadmap_sections(content)

    archive_path = roadmap_path.parent / "docs" / "archive" / "ROADMAP_HITOS_00-29.md"
    if archive_path.is_file():
        archived_sections = parse_roadmap_sections(archive_path.read_text(encoding="utf-8"))
        for k, v in archived_sections.items():
            sections.setdefault(k, v)

    if not table_hitos:
        return []

    errors: List[str] = []

    for t_hito in table_hitos:
        num = t_hito["hito_num"]
        if num not in sections:
            errors.append(
                f"Hito {num} figura en la tabla de resumen pero carece de sección '## Hito {num}:' en el cuerpo."
            )
            continue

        sec = sections[num]
        total = sec["total_tasks"]
        done = sec["completed_tasks"]

        # Si no hay tareas tipo '- [ ]' ni '- [x]', no podemos auditar con precisión de casillas
        if total == 0:
            continue

        # Inconsistencia 1: Todas las tareas completadas pero en la tabla figura como pendiente o < 100%
        if sec["is_all_completed"]:
            if t_hito["is_pending"] or t_hito["progreso_pct"] < 100:
                errors.append(
                    f"Inconsistencia en Hito {num}: La tabla de resumen indica '{t_hito['estado_raw']} | "
                    f"{t_hito['progreso_pct']}%', pero todas sus tareas ({done}/{total}) están completadas [x]. "
                    f"Debe actualizarse la tabla a '✅ Completado | 100%'."
                )
            if sec["header_icon"] in ("⏳", "🚧"):
                errors.append(
                    f"Inconsistencia en Hito {num}: El encabezado de sección tiene icono '{sec['header_icon']}', "
                    f"pero todas las tareas están completadas. Debe llevar '## ✅ Hito {num}:'."
                )

        # Inconsistencia 2: Cero tareas completadas pero en la tabla figura como completado o > 0%
        elif sec["is_all_pending"]:
            if t_hito["is_completed"] or t_hito["progreso_pct"] > 0:
                errors.append(
                    f"Inconsistencia en Hito {num}: La tabla de resumen indica '{t_hito['estado_raw']} | "
                    f"{t_hito['progreso_pct']}%', pero tiene 0 tareas completadas [x] de {total}. "
                    f"Debe actualizarse la tabla a '⏳ Pendiente | 0%'."
                )
            if sec["header_icon"] not in ("⏳", ""):
                errors.append(
                    f"Inconsistencia en Hito {num}: El encabezado de sección tiene icono '{sec['header_icon']}', "
                    f"pero ninguna tarea está completada. Debe llevar '## ⏳ Hito {num}:'."
                )

        # Inconsistencia 3: Tareas parcialmente completadas
        elif sec["is_in_progress"]:
            if t_hito["is_completed"]:
                errors.append(
                    f"Inconsistencia en Hito {num}: La tabla de resumen marca 'Completado', pero solo tiene "
                    f"{done}/{total} tareas completadas ({sec['calculated_pct']}%). Debe figurar '🚧 En Progreso'."
                )
            elif t_hito["is_pending"]:
                errors.append(
                    f"Inconsistencia en Hito {num}: La tabla de resumen marca 'Pendiente', pero ya cuenta con "
                    f"{done}/{total} tareas completadas ({sec['calculated_pct']}%). Debe figurar '🚧 En Progreso'."
                )

    return errors


def validate_active_task(active_task_path: Path) -> List[str]:
    """Valida la estructura y coherencia del archivo .agents/ACTIVE_TASK.md."""
    if not active_task_path.is_file():
        # Si no existe, es opcional en repos sin agentes activos, pero advertimos
        return []

    content = active_task_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    state_match = None
    for line in lines:
        match = re.search(r"\*{0,2}Estado\*{0,2}\s*:\s*(.+)$", line, re.IGNORECASE)
        if match:
            state_match = match.group(1).strip()
            break

    if not state_match:
        return [
            ".agents/ACTIVE_TASK.md carece del campo obligatorio '**Estado:**' (ej. 'IN_PROGRESS (XX%)' o 'COMPLETED (100%)')."
        ]

    is_completed = "completed" in state_match.lower() or "100%" in state_match
    pending_tasks = [
        line.strip() for line in lines if re.match(r"^-\s*\[\s*\]", line.strip())
    ]

    errors: List[str] = []

    if is_completed and pending_tasks:
        errors.append(
            f".agents/ACTIVE_TASK.md figura como '{state_match}', pero aún contiene {len(pending_tasks)} "
            f"casillas pendientes sin marcar '- [ ]'. Debe completarlas o actualizar el estado a IN_PROGRESS."
        )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent

    print("══════════════════════════════════════════════════════════════════════")
    print("   📋 [QA 11X] Auditoría de Consistencia de ROADMAP y ACTIVE_TASK     ")
    print("══════════════════════════════════════════════════════════════════════")

    roadmap_path = repo_root / "ROADMAP.md"
    active_task_path = repo_root / ".agents" / "ACTIVE_TASK.md"

    roadmap_errors: List[str] = []
    if roadmap_path.is_file():
        print(f"\n🔍 Auditando consistencia en {roadmap_path.relative_to(repo_root)}...")
        roadmap_errors = validate_roadmap_consistency(roadmap_path)
    else:
        print("\nℹ️ No se detectó ROADMAP.md; omitiendo comprobación de hoja de ruta.")

    active_task_errors: List[str] = []
    if active_task_path.is_file():
        print(f"🔍 Auditando estado y casillas en {active_task_path.relative_to(repo_root)}...")
        active_task_errors = validate_active_task(active_task_path)
    else:
        print("ℹ️ No se detectó .agents/ACTIVE_TASK.md; omitiendo comprobación de tarea activa.")

    all_errors = roadmap_errors + active_task_errors

    if all_errors:
        print("\n❌ Se detectaron discrepancias de consistencia operativa:")
        for err in all_errors:
            print(f"   - {err}")
        print("\n💡 Directiva: Mantén sincronizadas las tablas de resumen con el desglose granular.")
        return 1

    print("\n✔ ROADMAP.md y ACTIVE_TASK.md verificados en perfecta coherencia y sincronía.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
