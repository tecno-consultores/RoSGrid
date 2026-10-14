#!/usr/bin/env bash
# Licencia: MIT
# Propósito: Auditoría efímera de Infraestructura como Código (IaC) usando Trivy.

LC_ALL=C
set -e

echo "🛡️ Iniciando Auditoría de Seguridad de Infraestructura (Trivy IaC)..."

# Ejecuta el escáner de misconfiguraciones mapeando la carpeta actual al contenedor.
# Usamos ":ro" (Read-Only) para garantizar que Trivy no pueda alterar el código fuente.
docker run --rm \
  -v "${PWD}:/app:ro" \
  -w /app \
  aquasec/trivy:latest config . \
  --severity HIGH,CRITICAL \
  --exit-code 1

# Si el comando anterior no arroja Exit Code 1, pasamos a escanear vulnerabilidades (CVEs)
# en los manifiestos de dependencias expuestos en el file system.
echo "✅ IaC validado. Escaneando vulnerabilidades (CVEs) en el File System..."

docker run --rm \
  -v "${PWD}:/app:ro" \
  -w /app \
  aquasec/trivy:latest fs . \
  --severity CRITICAL \
  --exit-code 1

echo "✅ Auditoría de Infraestructura superada. Entorno seguro."
exit 0
