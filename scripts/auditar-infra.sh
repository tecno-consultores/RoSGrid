#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)
# Propósito: Auditoría efímera de Infraestructura como Código (IaC) usando Trivy.

LC_ALL=C
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🛡️ Iniciando Auditoría de Seguridad de Infraestructura (Trivy IaC)..."

# Ejecuta el escáner de misconfiguraciones mapeando la carpeta raíz del repositorio al contenedor.
# Usamos ":ro" (Read-Only) para garantizar que Trivy no pueda alterar el código fuente.
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy:0.58.2}"
if ! docker image inspect "${TRIVY_IMAGE}" >/dev/null 2>&1; then
  docker pull "${TRIVY_IMAGE}" >/dev/null 2>&1 || TRIVY_IMAGE="aquasec/trivy:latest"
fi

docker run --rm \
  -v "${REPO_ROOT}:/app:ro" \
  -w /app \
  "${TRIVY_IMAGE}" config . \
  --config /app/.trivy.yaml \
  --severity HIGH,CRITICAL \
  --exit-code 1

# Si el comando anterior no arroja Exit Code 1, pasamos a escanear vulnerabilidades (CVEs)
# en los manifiestos de dependencias expuestos en el file system.
echo "✅ IaC validado. Escaneando vulnerabilidades (CVEs) en el File System..."

docker run --rm \
  -v "${REPO_ROOT}:/app:ro" \
  -w /app \
  "${TRIVY_IMAGE}" fs . \
  --config /app/.trivy.yaml \
  --severity HIGH,CRITICAL \
  --exit-code 1

echo "✅ Auditoría de Infraestructura superada. Entorno seguro."
exit 0
