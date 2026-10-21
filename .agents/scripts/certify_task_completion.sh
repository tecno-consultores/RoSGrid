#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "══════════════════════════════════════════════════════════════════════"
echo "   🤖 RoSGrid Agent Certification Gate (Regla Cero & QA 11X)        "
echo "══════════════════════════════════════════════════════════════════════"

# 1. Auditoría de Secretos
echo -e "\n🔒 [1/4] Verificando que no existan secretos expuestos en Git..."
"${REPO_ROOT}/verificar-secretos.sh"
echo "✔ Cero secretos detectados."

# 2. Paridad ORM vs Alembic en Docker
echo -e "\n🗄️ [2/4] Verificando paridad entre modelos ORM y migraciones Alembic..."
docker cp "${REPO_ROOT}/.agents/scripts/verify_alembic_orm_parity.py" rosgrid_api_local:/app/scripts/verify_alembic_orm_parity.py
docker exec -t rosgrid_api_local python scripts/verify_alembic_orm_parity.py

# 3. Contratos de Integración Front-Back
echo -e "\n🧪 [3/4] Ejecutando suite de Contratos Front-Back (25 pruebas)..."
docker cp "${REPO_ROOT}/fastapi/scripts/validar_comunicacion_front_back.py" rosgrid_api_local:/app/scripts/validar_comunicacion_front_back.py
docker exec -t rosgrid_api_local python scripts/validar_comunicacion_front_back.py

# 4. Verificación de Sincronización Documental
echo -e "\n📚 [4/4] Verificando sincronización de documentación obligatoria..."
CODE_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/src|vue3/src)' || true)

if [ -n "${CODE_CHANGES}" ]; then
  echo "Se detectaron cambios en código fuente:"
  while IFS= read -r line; do
    [ -n "${line}" ] && echo "  - ${line}"
  done <<< "${CODE_CHANGES}"

  DOC_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(specs/|docs/|CHANGELOG\.md|ROADMAP\.md|TESTING\.md)' || true)
  if [ -z "${DOC_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código pero NO se han actualizado specs/, docs/, CHANGELOG.md, ROADMAP.md o TESTING.md."
    echo "Recuerda la Directiva Suprema: la documentación debe sincronizarse con cada cambio."
  else
    echo "✔ Documentación actualizada en paralelo:"
    while IFS= read -r doc_line; do
      [ -n "${doc_line}" ] && echo "  - ${doc_line}"
    done <<< "${DOC_CHANGES}"
  fi
else
  echo "✔ No hay cambios pendientes sin commitear en src/."
fi

echo -e "\n══════════════════════════════════════════════════════════════════════"
echo "   ✅ CERTIFICACIÓN EXITOSA: La tarea cumple con el estándar 11X     "
echo "══════════════════════════════════════════════════════════════════════"
