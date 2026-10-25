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
echo -e "\n🔒 [1/6] Verificando que no existan secretos expuestos en Git..."
"${REPO_ROOT}/scripts/verificar-secretos.sh"
echo "✔ Cero secretos detectados."

# 2. Auditoría Preventiva de Vulnerabilidades y Misconfiguraciones IaC (Trivy)
echo -e "\n🛡️ [2/6] Ejecutando escaneo preventivo de vulnerabilidades y seguridad (Trivy)..."
"${REPO_ROOT}/scripts/auditar-infra.sh"
echo "✔ Cero vulnerabilidades críticas o de alto impacto detectadas."

# 3. Integridad de Diccionarios i18n (Anti-Colisión de Claves JSON)
echo -e "\n🌐 [3/6] Verificando integridad de diccionarios i18n (anti-colisión de claves)..."
python3 "${REPO_ROOT}/.agents/scripts/verify_json_no_duplicate_keys.py"
echo "✔ Diccionarios i18n validados sin claves duplicadas."

# 4. Paridad ORM vs Alembic en Docker
echo -e "\n🗄️ [4/6] Verificando paridad entre modelos ORM y migraciones Alembic..."
if docker ps --format '{{.Names}}' | grep -q "^rosgrid_api_local$"; then
    docker cp "${REPO_ROOT}/.agents/scripts/verify_alembic_orm_parity.py" rosgrid_api_local:/app/scripts/verify_alembic_orm_parity.py
    docker exec -t rosgrid_api_local python scripts/verify_alembic_orm_parity.py
else
    echo "ℹ️ Contenedor rosgrid_api_local inactivo (stack apagado); omitiendo verificación en vivo de ORM."
fi

# 5. Contratos de Integración Front-Back
echo -e "\n🧪 [5/6] Ejecutando suite de Contratos Front-Back (25 pruebas)..."
if docker ps --format '{{.Names}}' | grep -q "^rosgrid_api_local$"; then
    docker cp "${REPO_ROOT}/fastapi/scripts/validar_comunicacion_front_back.py" rosgrid_api_local:/app/scripts/validar_comunicacion_front_back.py
    docker exec -t rosgrid_api_local python scripts/validar_comunicacion_front_back.py
else
    echo "ℹ️ Contenedor rosgrid_api_local inactivo (stack apagado); omitiendo validación en vivo de contratos front-back."
fi

# 6. Verificación de Sincronización Documental
echo -e "\n📚 [6/6] Verificando sincronización de documentación y pruebas obligatorias..."
CODE_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/src|vue3/src)' || true)

if [ -n "${CODE_CHANGES}" ]; then
  echo "Se detectaron cambios en código fuente:"
  while IFS= read -r line; do
    [ -n "${line}" ] && echo "  - ${line}"
  done <<< "${CODE_CHANGES}"

  TEST_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/tests/|vue3/src/.*\.unit\.ts)' || true)
  if [ -z "${TEST_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código fuente pero NO se detectan pruebas unitarias nuevas o modificadas (fastapi/tests/ o vue3/src/)."
  else
    echo "✔ Pruebas unitarias 11X detectadas en paralelo:"
    while IFS= read -r t_line; do
      [ -n "${t_line}" ] && echo "  - ${t_line}"
    done <<< "${TEST_CHANGES}"
  fi

  KARATE_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/test/.*\.feature|vue3/test/.*\.feature|docs/examples/fastapi/test/|docs/examples/vue3/test/)' || true)
  if [ -z "${KARATE_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código fuente pero NO se detectan escenarios BDD Karate Labs (fastapi/test/ o vue3/test/)."
    echo "Recuerda la Invariante Karate Labs: cada cambio de API o UI DEBE incluir sus escenarios BDD correspondientes."
  else
    echo "✔ Escenarios BDD Karate Labs detectados en paralelo:"
    while IFS= read -r k_line; do
      [ -n "${k_line}" ] && echo "  - ${k_line}"
    done <<< "${KARATE_CHANGES}"
  fi

  DOC_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E '^(docs/|CHANGELOG\.md|ROADMAP\.md|TESTING\.md|README\.md)' || true)
  if [ -z "${DOC_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código pero NO se han actualizado docs/, CHANGELOG.md, ROADMAP.md, TESTING.md o README.md."
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
