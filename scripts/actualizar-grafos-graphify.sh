#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Extracción y actualización canónica de grafos semánticos AST (Graphify) para Backend y Frontend.
# Cumple estrictamente con la Regla Cero (ejecución en contenedor Docker efímero).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="sinfallas/remote-graphify:latest"

echo "══════════════════════════════════════════════════════════════════════"
echo "   🧠 RoSGrid — Extracción y Actualización de Grafos AST Graphify    "
echo "══════════════════════════════════════════════════════════════════════"

# 1. Verificar disponibilidad de Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Error: Docker no está instalado o no se encuentra en el PATH." >&2
  exit 1
fi

# 2. Descargar o asegurar imagen Graphify
echo -e "\n📦 Verificando imagen Docker: ${IMAGE_NAME}..."
docker pull "${IMAGE_NAME}"

# 3. Procesar Backend (FastAPI)
echo -e "\n⚙️ [1/2] Extrayendo y agrupando grafo semántico de Backend (fastapi/)..."
docker compose -f "${REPO_ROOT}/fastapi/docker-compose.qa.yml" --profile graphify run --rm graphify graphify extract . --code-only
docker compose -f "${REPO_ROOT}/fastapi/docker-compose.qa.yml" --profile graphify run --rm graphify graphify cluster-only .

# 4. Procesar Frontend (Vue 3)
echo -e "\n🎨 [2/2] Extrayendo y agrupando grafo semántico de Frontend (vue3/)..."
docker compose -f "${REPO_ROOT}/vue3/docker-compose.qa.yml" --profile graphify run --rm graphify graphify extract . --code-only
docker compose -f "${REPO_ROOT}/vue3/docker-compose.qa.yml" --profile graphify run --rm graphify graphify cluster-only .

# 5. Normalizar permisos para el usuario del host
echo -e "\n🔒 Normalizando permisos de salida (UID $(id -u):$(id -g))..."
docker run --rm -v "${REPO_ROOT}:/work" "${IMAGE_NAME}" chown -R "$(id -u):$(id -g)" /work/fastapi/graphify-out /work/vue3/graphify-out

# 6. Mostrar resumen
echo -e "\n✅ Extracción completada exitosamente. Resumen de grafos generados:"
if [ -f "${REPO_ROOT}/fastapi/graphify-out/GRAPH_REPORT.md" ]; then
  echo "  - Backend:  $(grep -m 1 "Summary" -A 1 "${REPO_ROOT}/fastapi/graphify-out/GRAPH_REPORT.md" | tail -n 1)"
fi
if [ -f "${REPO_ROOT}/vue3/graphify-out/GRAPH_REPORT.md" ]; then
  echo "  - Frontend: $(grep -m 1 "Summary" -A 1 "${REPO_ROOT}/vue3/graphify-out/GRAPH_REPORT.md" | tail -n 1)"
fi

echo -e "\n📁 Artefactos disponibles:"
echo "  - Backend:  fastapi/graphify-out/ (GRAPH_REPORT.md, graph.html, graph.json)"
echo "  - Frontend: vue3/graphify-out/ (GRAPH_REPORT.md, graph.html, graph.json)"
echo "══════════════════════════════════════════════════════════════════════"
