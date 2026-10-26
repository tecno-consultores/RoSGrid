#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Apertura rápida en el navegador de los mapas interactivos AST de RoSGrid (Backend y Frontend).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_MAP="${REPO_ROOT}/fastapi/graphify-out/graph.html"
FRONTEND_MAP="${REPO_ROOT}/vue3/graphify-out/graph.html"

echo "══════════════════════════════════════════════════════════════════════"
echo "   🗺️  RoSGrid — Visualizador Interactivo de Arquitectura AST        "
echo "══════════════════════════════════════════════════════════════════════"

if [ ! -f "${BACKEND_MAP}" ] || [ ! -f "${FRONTEND_MAP}" ]; then
  echo "⚠️ Advertencia: No se encontraron los archivos HTML de Graphify."
  echo "  Ejecutando generación inicial con './scripts/actualizar-grafos-graphify.sh'..."
  "${REPO_ROOT}/scripts/actualizar-grafos-graphify.sh"
fi

echo -e "\n📍 Rutas de los Mapas Interactivos:"
echo "  - Backend (FastAPI):  file://${BACKEND_MAP}"
echo "  - Frontend (Vue 3):   file://${FRONTEND_MAP}"

# Intentar abrir en navegador gráfico si hay display disponible
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
  OPEN_CMD=""
  if command -v xdg-open &> /dev/null; then
    OPEN_CMD="xdg-open"
  elif command -v google-chrome &> /dev/null; then
    OPEN_CMD="google-chrome"
  elif command -v firefox &> /dev/null; then
    OPEN_CMD="firefox"
  elif command -v sensible-browser &> /dev/null; then
    OPEN_CMD="sensible-browser"
  fi

  if [ -n "${OPEN_CMD}" ]; then
    echo -e "\n🌐 Abriendo mapas interactivos en tu navegador predeterminado..."
    "${OPEN_CMD}" "${BACKEND_MAP}" >/dev/null 2>&1 &
    "${OPEN_CMD}" "${FRONTEND_MAP}" >/dev/null 2>&1 &
    echo "✔ Pestañas abiertas en el navegador."
    exit 0
  fi
fi

echo -e "\n💡 Para visualizar los mapas, copia y pega cualquiera de las URLs en tu navegador:"
echo "   file://${BACKEND_MAP}"
echo "   file://${FRONTEND_MAP}"
echo "══════════════════════════════════════════════════════════════════════"
