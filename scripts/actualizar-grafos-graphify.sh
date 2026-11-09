#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)
# Propósito: Extracción y actualización canónica de grafos semánticos AST (Graphify) para Backend y Frontend.
# Cumple estrictamente con la Regla Cero (ejecución en contenedor Docker efímero).

LC_ALL=C
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

TARGET_STACK="${1:-all}"

# 2. Descargar o asegurar imagen Graphify
echo -e "\n📦 Verificando imagen Docker: ${IMAGE_NAME}..."
if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  docker pull "${IMAGE_NAME}"
fi

# 3. Procesar Backend (FastAPI)
if [[ "${TARGET_STACK}" == "all" || "${TARGET_STACK}" == "backend" || "${TARGET_STACK}" == "fastapi" ]]; then
  echo -e "\n⚙️ [1/2] Extrayendo y agrupando grafo semántico de Backend (fastapi/)..."
  docker compose -f "${REPO_ROOT}/fastapi/docker-compose.qa.yml" --profile graphify run --rm graphify graphify extract . --code-only
  docker compose -f "${REPO_ROOT}/fastapi/docker-compose.qa.yml" --profile graphify run --rm graphify graphify cluster-only .
fi

# 4. Procesar Frontend (Vue 3)
if [[ "${TARGET_STACK}" == "all" || "${TARGET_STACK}" == "frontend" || "${TARGET_STACK}" == "vue3" ]]; then
  echo -e "\n🎨 [2/2] Extrayendo y agrupando grafo semántico de Frontend (vue3/)..."
  docker compose -f "${REPO_ROOT}/vue3/docker-compose.qa.yml" --profile graphify run --rm graphify graphify extract . --code-only
  docker compose -f "${REPO_ROOT}/vue3/docker-compose.qa.yml" --profile graphify run --rm graphify graphify cluster-only .
fi

# 5. Normalizar permisos para el usuario del host
echo -e "\n🔒 Normalizando permisos de salida (UID $(id -u):$(id -g))..."
docker run --rm -v "${REPO_ROOT}:/work" "${IMAGE_NAME}" chown -R "$(id -u):$(id -g)" /work/fastapi/graphify-out /work/vue3/graphify-out

# Sincronizar copia en graphify-out/ raíz para herramientas MCP (certify_11x_gate / inspect_ast_blast_radius)
mkdir -p "${REPO_ROOT}/graphify-out"
if [ -f "${REPO_ROOT}/fastapi/graphify-out/graph.json" ]; then
  cp "${REPO_ROOT}/fastapi/graphify-out/graph.json" "${REPO_ROOT}/graphify-out/graph.json"
  cp "${REPO_ROOT}/fastapi/graphify-out/GRAPH_REPORT.md" "${REPO_ROOT}/graphify-out/GRAPH_REPORT.md" 2>/dev/null || true
fi
if [ -f "${REPO_ROOT}/vue3/graphify-out/graph.json" ]; then
  cp "${REPO_ROOT}/vue3/graphify-out/graph.json" "${REPO_ROOT}/graphify-out/graph-vue3.json"
  cp "${REPO_ROOT}/vue3/graphify-out/GRAPH_REPORT.md" "${REPO_ROOT}/graphify-out/GRAPH_REPORT_VUE3.md" 2>/dev/null || true
fi

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
