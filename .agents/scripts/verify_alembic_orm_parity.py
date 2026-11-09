#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Script de auditoría para prevenir modelos ORM huérfanos sin migración de Alembic.

Inspecciona Base.metadata en src/models/ y valida que todas las tablas existan
en las migraciones de Alembic en fastapi/migrations/versions/.
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

if (REPO_ROOT / "fastapi").exists():
    FASTAPI_DIR = REPO_ROOT / "fastapi"
elif Path("/app/src/models").exists():
    FASTAPI_DIR = Path("/app")
else:
    FASTAPI_DIR = REPO_ROOT

MIGRATIONS_DIR = FASTAPI_DIR / "migrations" / "versions"
MODELS_DIR = FASTAPI_DIR / "src" / "models"


def get_orm_tables() -> set[str]:
    """Extrae nombres de tablas a partir de __tablename__ en src/models/."""
    tables = set()
    table_pattern = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
    for py_file in MODELS_DIR.glob("*.py"):
        if py_file.name == "__init__.py" or py_file.name == "base.py":
            continue
        content = py_file.read_text(encoding="utf-8")
        for match in table_pattern.finditer(content):
            tables.add(match.group(1))
    return tables


def get_migrated_tables() -> set[str]:
    """Extrae nombres de tablas creadas o renombradas en las migraciones de Alembic."""
    migrated = set()
    create_pattern = re.compile(r'op\.create_table\(\s*["\']([^"\']+)["\']')
    rename_pattern = re.compile(r'op\.rename_table\(\s*["\'][^"\']+["\']\s*,\s*["\']([^"\']+)["\']\)')

    for mig_file in MIGRATIONS_DIR.glob("*.py"):
        content = mig_file.read_text(encoding="utf-8")
        for match in create_pattern.finditer(content):
            migrated.add(match.group(1))
        for match in rename_pattern.finditer(content):
            migrated.add(match.group(1))
    return migrated


def verify_revision_id_lengths() -> list[tuple[str, str, int]]:
    """Valida que ningún revision ID supere los 32 caracteres de alembic_version.version_num."""
    rev_pattern = re.compile(r'^\s*revision(?:\s*:\s*str)?\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    violations: list[tuple[str, str, int]] = []
    for mig_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        content = mig_file.read_text(encoding="utf-8")
        match = rev_pattern.search(content)
        if match:
            rev_id = match.group(1)
            if len(rev_id) > 32:
                violations.append((mig_file.name, rev_id, len(rev_id)))
    return violations


def verify_dropped_columns_not_in_orm() -> list[tuple[str, str]]:
    """Detecta columnas eliminadas vía op.drop_column que siguen declaradas en los modelos ORM sin migración de restauración."""
    drop_re = re.compile(r'op\.drop_column\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)')
    add_re = re.compile(
        r'op\.add_column\(\s*["\']([^"\']+)["\']\s*,\s*sa\.Column\(\s*["\']([^"\']+)["\']'
    )
    sql_add_re = re.compile(
        r'ALTER\s+TABLE\s+([a-zA-Z0-9_]+)\s*(?:["\']\s*["\']|\s+)?ADD\s+COLUMN(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-zA-Z0-9_]+)',
        re.IGNORECASE,
    )
    rename_table_re = re.compile(
        r'op\.rename_table\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'
    )

    dropped_cols: set[tuple[str, str]] = set()
    for mig_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        content = mig_file.read_text(encoding="utf-8")
        # Extraer solo el cuerpo de upgrade() antes de def downgrade()
        upgrade_body = content.split("def downgrade")[0]
        for m in drop_re.finditer(upgrade_body):
            dropped_cols.add((m.group(1), m.group(2)))
        for m in rename_table_re.finditer(upgrade_body):
            old_t, new_t = m.group(1), m.group(2)
            for t, c in list(dropped_cols):
                if t == old_t:
                    dropped_cols.add((new_t, c))
        for m in add_re.finditer(upgrade_body):
            dropped_cols.discard((m.group(1), m.group(2)))
        for m in sql_add_re.finditer(upgrade_body):
            dropped_cols.discard((m.group(1), m.group(2)))

    # Verificar si alguna columna en dropped_cols sigue definida como mapped_column en el ORM
    violations: list[tuple[str, str]] = []
    class_split_re = re.compile(r"(?=^class\s+\w+\()", re.MULTILINE)
    tname_re = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
    for py_file in MODELS_DIR.glob("*.py"):
        if py_file.name in ("__init__.py", "base.py"):
            continue
        content = py_file.read_text(encoding="utf-8")
        for block in class_split_re.split(content):
            tm = tname_re.search(block)
            if not tm:
                continue
            table_name = tm.group(1)
            for t, col_name in sorted(dropped_cols):
                if t == table_name and re.search(rf"^\s*{re.escape(col_name)}\s*:\s*Mapped\[", block, re.MULTILINE):
                    violations.append((table_name, col_name))
    return violations


def main() -> int:
    print("🔍 [RoSGrid QA] Verificando paridad entre modelos SQLAlchemy ORM y migraciones Alembic...")
    orm_tables = get_orm_tables()
    migrated_tables = get_migrated_tables()

    missing = orm_tables - migrated_tables
    if missing:
        print("\n❌ ERROR: Se detectaron modelos ORM huérfanos sin migración de Alembic:")
        for t in sorted(missing):
            print(f"   - Tabla: '{t}' definida en src/models/ pero NO creada en fastapi/migrations/versions/")
        print("\n💡 Solución: Crea una migración de Alembic (ej. alembic revision -m 'add_<tabla>')")
        return 1

    rev_violations = verify_revision_id_lengths()
    if rev_violations:
        print("\n❌ ERROR: Se detectaron identificadores 'revision' en Alembic que exceden VARCHAR(32) en PostgreSQL:")
        for fname, rev_id, length in rev_violations:
            print(f"   - Archivo: {fname} -> revision='{rev_id}' ({length} caracteres > máximo 32)")
        print("\n💡 Solución: Acorta el identificador 'revision' a <= 32 caracteres.")
        return 1

    col_violations = verify_dropped_columns_not_in_orm()
    if col_violations:
        print(
            "\n❌ ERROR: Se detectaron columnas eliminadas en Alembic (op.drop_column) que siguen declaradas en modelos ORM:"
        )
        for tname, col_name in col_violations:
            print(f"   - Tabla '{tname}', Columna '{col_name}': eliminada en migraciones pero aún declarada en src/models/")
        print("\n💡 Solución: Restaura la columna con una migración (op.execute / op.add_column) o elimínala del modelo ORM.")
        return 1

    print(
        f"✅ ÉXITO: Las {len(orm_tables)} tablas ORM y sus columnas cuentan con su correspondiente migración de Alembic y revision IDs <= 32 chars."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
