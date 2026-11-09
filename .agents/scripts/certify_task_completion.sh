#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

LC_ALL=C
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
STRICT_MODE=false
if [[ "${1:-}" == "--strict" ]]; then
  STRICT_MODE=true
fi

run_py_in_docker() {
  docker run --rm --entrypoint python3 \
    -v "${REPO_ROOT}:/workspace:ro" \
    -w /workspace \
    sinfallas/rosgrid-backend:local-test "$@"
}

echo "══════════════════════════════════════════════════════════════════════"
echo "   🤖 RoSGrid Agent Certification Gate (Regla Cero & QA 11X)        "
echo "══════════════════════════════════════════════════════════════════════"

# 1. Auditoría de Secretos
echo -e "\n🔒 [1/9] Verificando que no existan secretos expuestos en Git..."
"${REPO_ROOT}/scripts/verificar-secretos.sh"
echo "✔ Cero secretos detectados."

# 2. Auditoría Preventiva de Vulnerabilidades y Misconfiguraciones IaC (Trivy)
echo -e "\n🛡️ [2/9] Ejecutando escaneo preventivo de vulnerabilidades y seguridad (Trivy)..."
"${REPO_ROOT}/scripts/auditar-infra.sh"
echo "✔ Cero vulnerabilidades críticas o de alto impacto detectadas."

# 3. Integridad de Diccionarios i18n (Anti-Colisión de Claves JSON)
echo -e "\n🌐 [3/9] Verificando integridad de diccionarios i18n (anti-colisión de claves)..."
run_py_in_docker .agents/scripts/verify_json_no_duplicate_keys.py
echo "✔ Diccionarios i18n validados sin claves duplicadas."

# 4. Invariante de Cero Componentes Vue Huérfanos y Calidad Anti-Silo (3 Fases + 0 Mocks Ciegos)
echo -e "\n🧩 [4/9] Verificando cobertura de componentes Vue y calidad Anti-Silo de pruebas..."
run_py_in_docker .agents/scripts/verify_zero_orphan_vue_components.py
run_py_in_docker .agents/scripts/verify_anti_silo_test_quality.py
echo "✔ Todos los componentes Vue y suites Anti-Silo (0 mocks ciegos / 3 fases temporales) verificados."

# 5. Salud Topológica y Límites de Capas (Graphify AST)
echo -e "\n🧠 [5/9] Auditando salud topológica y límites de capas arquitectónicas (Graphify AST)..."
run_py_in_docker .agents/scripts/verify_topological_health.py
echo "✔ Salud topológica y límites de capas certificados (0 acoplamientos indebidos)."

# 6. Invariante de Cero Endpoints de API Huérfanos
echo -e "\n🔗 [6/9] Verificando paridad de endpoints API e invariante cero huérfanos..."
run_py_in_docker .agents/scripts/verify_no_orphan_api_endpoints.py
echo "✔ Paridad bidireccional API certificada (0 llamadas 404/405)."

# 7. Paridad ORM vs Alembic en Docker
echo -e "\n🗄️ [7/9] Verificando paridad entre modelos ORM y migraciones Alembic..."
if docker ps --format '{{.Names}}' | grep -q "^rosgrid_api_local$"; then
    docker cp "${REPO_ROOT}/.agents/scripts/verify_alembic_orm_parity.py" rosgrid_api_local:/app/scripts/verify_alembic_orm_parity.py
    docker exec -t rosgrid_api_local python scripts/verify_alembic_orm_parity.py
else
    echo "ℹ️ Contenedor rosgrid_api_local inactivo (stack apagado); omitiendo verificación en vivo de ORM."
fi

# 8. Contratos de Integración Front-Back
echo -e "\n🧪 [8/9] Ejecutando suite de Contratos Front-Back (28 contratos)..."
if docker ps --format '{{.Names}}' | grep -q "^rosgrid_api_local$"; then
    if curl -fsS http://127.0.0.1:8000/api/v1/auth/bootstrap-status 2>/dev/null | grep -q '"is_bootstrapped":false'; then
        echo "ℹ️ Contenedor rosgrid_api_local en modo Wizard limpio (is_bootstrapped: false); omitiendo validación autenticada para preservar estado virgen."
    else
        docker cp "${REPO_ROOT}/fastapi/scripts/validar_comunicacion_front_back.py" rosgrid_api_local:/app/scripts/validar_comunicacion_front_back.py
        docker exec -t rosgrid_api_local python scripts/validar_comunicacion_front_back.py
    fi
else
    echo "ℹ️ Contenedor rosgrid_api_local inactivo (stack apagado); omitiendo validación en vivo de contratos front-back."
fi

# 9. Verificación de Sincronización Documental
echo -e "\n📚 [9/9] Verificando sincronización de documentación y pruebas obligatorias..."
CODE_CHANGES=$(git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/src|vue3/src)' || true)

if [ -n "${CODE_CHANGES}" ]; then
  echo "Se detectaron cambios en código fuente:"
  while IFS= read -r line; do
    [ -n "${line}" ] && echo "  - ${line}"
  done <<< "${CODE_CHANGES}"

  TEST_CHANGES=$({ git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null; git -C "${REPO_ROOT}" ls-files --others --exclude-standard; } | grep -E '^(fastapi/tests/|vue3/src/.*\.unit\.ts)' | sort -u || true)
  if [ -z "${TEST_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código fuente pero NO se detectan pruebas unitarias nuevas o modificadas (fastapi/tests/ o vue3/src/)."
    [ "${STRICT_MODE}" = true ] && exit 1
  else
    echo "✔ Pruebas unitarias 11X detectadas en paralelo:"
    while IFS= read -r t_line; do
      [ -n "${t_line}" ] && echo "  - ${t_line}"
    done <<< "${TEST_CHANGES}"
  fi

  KARATE_CHANGES=$(git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null | grep -E '^(fastapi/test/.*\.feature|vue3/test/.*\.feature|docs/examples/fastapi/test/|docs/examples/vue3/test/)' || true)
  if [ -z "${KARATE_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código fuente pero NO se detectan escenarios BDD Karate Labs (fastapi/test/ o vue3/test/)."
    echo "Recuerda la Invariante Karate Labs: cada cambio de API o UI DEBE incluir sus escenarios BDD correspondientes."
    [ "${STRICT_MODE}" = true ] && exit 1
  else
    echo "✔ Escenarios BDD Karate Labs detectadas en paralelo:"
    while IFS= read -r k_line; do
      [ -n "${k_line}" ] && echo "  - ${k_line}"
    done <<< "${KARATE_CHANGES}"
  fi

  DOC_CHANGES=$(git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null | grep -E '^(docs/|CHANGELOG\.md|ROADMAP\.md|TESTING\.md|README\.md)' || true)
  if [ -z "${DOC_CHANGES}" ]; then
    echo "⚠️ ADVERTENCIA: Se modificó código pero NO se han actualizado docs/, CHANGELOG.md, ROADMAP.md, TESTING.md o README.md."
    echo "Recuerda la Directiva Suprema: la documentación debe sincronizarse con cada cambio."
    [ "${STRICT_MODE}" = true ] && exit 1
  else
    echo "✔ Documentación actualizada en paralelo:"
    while IFS= read -r doc_line; do
      [ -n "${doc_line}" ] && echo "  - ${doc_line}"
    done <<< "${DOC_CHANGES}"
  fi
else
  echo "✔ No hay cambios pendientes sin commitear en src/."
fi

echo -e "\n🗺️  Verificando consistencia entre ROADMAP.md y .agents/ACTIVE_TASK.md..."
run_py_in_docker .agents/scripts/verify_roadmap_consistency.py

echo -e "\n══════════════════════════════════════════════════════════════════════"
echo "   ✅ CERTIFICACIÓN EXITOSA: La tarea cumple con el estándar 11X     "
echo "══════════════════════════════════════════════════════════════════════"
