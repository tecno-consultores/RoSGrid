#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

LC_ALL=C
set -euo pipefail

if [[ "${ROSGRID_IMAGE_PREBUILT:-0}" != "1" ]]; then
    echo "[RoSGrid] Sincronizando dependencias con uv.lock (--frozen)..."
    uv sync --frozen
else
    echo "[RoSGrid] Imagen de produccion precompilada detectada. Omitiendo uv sync en runtime."
fi

echo "[RoSGrid] Verificando disponibilidad de PostgreSQL y ejecutando migraciones con pg_advisory_lock..."
python3 - << 'PYEOF'
import os
import sys
import time
import subprocess
import psycopg

DB_DSN = os.environ.get("ROSGRID_SYNC_DATABASE_URL", "")
ADVISORY_LOCK_ID = 948271605  # Identificador unico de bloqueo para migraciones de RoSGrid

if not DB_DSN:
    print("[ERROR] Variable ROSGRID_SYNC_DATABASE_URL no definida.", file=sys.stderr)
    sys.exit(1)

for attempt in range(1, 31):
    try:
        with psycopg.connect(DB_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                print("[RoSGrid] Adquiriendo pg_advisory_lock para migraciones Alembic...")
                cur.execute("SELECT pg_advisory_lock(%s);", (ADVISORY_LOCK_ID,))
                try:
                    result = subprocess.run(["alembic", "upgrade", "head"], check=False)
                    if result.returncode != 0:
                        sys.exit(result.returncode)
                    print("[RoSGrid] Migraciones aplicadas exitosamente (head).")
                finally:
                    cur.execute("SELECT pg_advisory_unlock(%s);", (ADVISORY_LOCK_ID,))
        break
    except psycopg.OperationalError as exc:
        print(f"[RoSGrid] Esperando a PostgreSQL (intento {attempt}/30): {exc}")
        time.sleep(2)
else:
    print("[ERROR] No se pudo conectar a PostgreSQL tras 30 intentos.", file=sys.stderr)
    sys.exit(1)
PYEOF

echo "[RoSGrid] Iniciando servidor ASGI Uvicorn..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --loop uvloop \
    --http httptools \
    --proxy-headers \
    --forwarded-allow-ips="*"
