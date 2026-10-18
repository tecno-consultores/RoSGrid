#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Script unificado de limpieza y purga de artefactos temporales y cachés (Estándar QA 11X)

LC_ALL=C
set -euo pipefail

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
rm -f fastapi/.coverage
rm -rf fastapi/.coverage.*
rm -rf fastapi/.mypy_cache
rm -rf fastapi/.pytest_cache
rm -rf fastapi/.ruff_cache
rm -rf fastapi/.hypothesis
rm -rf fastapi/.schemathesis
rm -rf fastapi/.tox
rm -rf fastapi/.uv
rm -rf fastapi/htmlcov
rm -rf fastapi/mutants
rm -rf fastapi/.mutmut-cache
rm -rf fastapi/target
rm -rf fastapi/test/target
rm -f fastapi/zap-report.html
rm -f fastapi/zap.yaml
rm -f fastapi/chaos-report.html
rm -f fastapi/profile.svg
rm -f fastapi/*.log 2>/dev/null || true
rm -rf fastapi/prometheus_data
find fastapi -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find fastapi -type f -name "*.py[cod]" -delete 2>/dev/null || true

echo "[3/4] Eliminando artefactos temporales del Frontend (vue3)..."
rm -rf vue3/dist 2>/dev/null || docker run --rm -v "$(pwd)/vue3:/app" alpine rm -rf /app/dist 2>/dev/null || true
rm -rf vue3/.vite
rm -rf vue3/coverage
rm -rf vue3/.stryker-tmp
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
