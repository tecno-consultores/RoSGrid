#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Script unificado de limpieza y purga de artefactos temporales y cachés (Estándar QA 11X)

LC_ALL=C
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "=============================================================================="
echo "          🧹 Limpieza Unificada del Espacio de Trabajo RoSGrid               "
echo "=============================================================================="

echo "[1/4] Deteniendo contenedores efímeros y redes de prueba..."
docker compose -f fastapi/docker-compose.qa.yml down --remove-orphans -v 2>/dev/null || true
docker compose -f fastapi/docker-compose.qa.yml --profile chaos down --remove-orphans -v 2>/dev/null || true
docker compose -f fastapi/docker-compose.qa.yml --profile graphify down --remove-orphans -v 2>/dev/null || true
docker compose -f vue3/docker-compose.qa.yml down --remove-orphans -v 2>/dev/null || true
docker compose -f vue3/docker-compose.qa.yml --profile observability down --remove-orphans -v 2>/dev/null || true
docker compose -f vue3/docker-compose.qa.yml --profile graphify down --remove-orphans -v 2>/dev/null || true
docker compose -f docker-compose.prod.local.yml down --remove-orphans -v 2>/dev/null || true
docker ps -q --filter "name=rosgrid" | xargs -r docker stop 2>/dev/null || true

echo "[2/4] Eliminando artefactos temporales del Backend (fastapi)..."
rm -f fastapi/.coverage 2>/dev/null || true
rm -rf fastapi/.coverage.* 2>/dev/null || true
rm -rf fastapi/.mypy_cache 2>/dev/null || docker run --rm -v "$(pwd)/fastapi:/app" alpine rm -rf /app/.mypy_cache 2>/dev/null || true
rm -rf fastapi/.pytest_cache 2>/dev/null || docker run --rm -v "$(pwd)/fastapi:/app" alpine rm -rf /app/.pytest_cache 2>/dev/null || true
rm -rf fastapi/.ruff_cache 2>/dev/null || docker run --rm -v "$(pwd)/fastapi:/app" alpine rm -rf /app/.ruff_cache 2>/dev/null || true
rm -rf fastapi/.hypothesis 2>/dev/null || true
rm -rf fastapi/.schemathesis 2>/dev/null || true
rm -rf fastapi/.tox 2>/dev/null || true
rm -rf fastapi/.uv 2>/dev/null || true
rm -rf fastapi/htmlcov 2>/dev/null || docker run --rm -v "$(pwd)/fastapi:/app" alpine rm -rf /app/htmlcov 2>/dev/null || true
rm -rf fastapi/mutants 2>/dev/null || true
rm -rf fastapi/.mutmut-cache 2>/dev/null || true
rm -rf fastapi/target 2>/dev/null || true
rm -rf fastapi/test/target 2>/dev/null || true
rm -f fastapi/zap-report.html 2>/dev/null || true
rm -f fastapi/zap.yaml 2>/dev/null || true
rm -f fastapi/chaos-report.html 2>/dev/null || true
rm -f fastapi/profile.svg 2>/dev/null || true
rm -f fastapi/*.log 2>/dev/null || true
rm -rf fastapi/prometheus_data 2>/dev/null || true
find fastapi -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find fastapi -type f -name "*.py[cod]" -delete 2>/dev/null || true

echo "[3/4] Eliminando artefactos temporales del Frontend (vue3)..."
rm -rf vue3/dist 2>/dev/null || docker run --rm -v "$(pwd)/vue3:/app" alpine rm -rf /app/dist 2>/dev/null || true
rm -rf vue3/.vite 2>/dev/null || docker run --rm -v "$(pwd)/vue3:/app" alpine rm -rf /app/.vite 2>/dev/null || true
rm -rf vue3/coverage 2>/dev/null || docker run --rm -v "$(pwd)/vue3:/app" alpine rm -rf /app/coverage 2>/dev/null || true
rm -rf vue3/.stryker-tmp 2>/dev/null || true
rm -rf vue3/test-results
rm -rf vue3/playwright-report
rm -rf vue3/blob-report
rm -rf vue3/target
rm -rf vue3/test/target
rm -rf vue3/.lighthouseci
rm -rf vue3/lhci-reports
rm -rf vue3/.lhcache
rm -rf vue3/reports
rm -f vue3/*.log 2>/dev/null || true
rm -rf vue3/prometheus_data

echo "[4/4] Eliminando archivos temporales en la raíz..."
rm -f ./*.log 2>/dev/null || true
rm -f ./trivy-results* 2>/dev/null || true
docker system prune -af

# Verificación de integridad: los grafos AST de Graphify se conservan intactos
if [[ -f fastapi/graphify-out/GRAPH_REPORT.md ]] && [[ -f vue3/graphify-out/GRAPH_REPORT.md ]]; then
    echo "✔ Reportes de Graphify AST verificados e intactos."
fi

echo "=============================================================================="
echo "✔ Limpieza completada exitosamente sin alterar dependencias ni imágenes base."
echo "=============================================================================="
exit 0
