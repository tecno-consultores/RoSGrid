#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Pipeline de Validación Integral y Pruebas Locales de Imágenes de Producción (Sin Docker Hub)

LC_ALL=C
set -euo pipefail

echo "=============================================================================="
echo "      🚀 Pipeline de Pruebas Locales de Producción RoSGrid (QA 11X)         "
echo "=============================================================================="

# 1. Comprobar herramientas
for cmd in docker curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "\e[31m[ERROR] Comando requerido no encontrado: $cmd\e[0m"
        exit 1
    fi
done

echo -e "\n[1/6] Construyendo imágenes de producción locales..."
docker build -f fastapi/Dockerfile -t sinfallas/rosgrid-backend:local-test fastapi
docker build -f vue3/Dockerfile -t sinfallas/rosgrid-frontend:local-test vue3

echo -e "\n[2/6] Levantando stack de producción local con docker-compose.prod.local.yml..."
docker compose -f docker-compose.prod.local.yml down -v --remove-orphans 2>/dev/null || true
docker compose -f docker-compose.prod.local.yml up -d

echo -e "\n[3/6] Esperando estabilización y healthchecks de contenedores..."
MAX_ATTEMPTS=40
ATTEMPT=0

until [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; do
    DB_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_db_local 2>/dev/null || echo '"unknown"')
    REDIS_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_redis_local 2>/dev/null || echo '"unknown"')
    API_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_api_local 2>/dev/null || echo '"unknown"')

    if [ "$DB_STATUS" = '"healthy"' ] && [ "$REDIS_STATUS" = '"healthy"' ] && [ "$API_STATUS" = '"healthy"' ]; then
        echo "✔ Base de Datos, KeyDB y API alcanzaron estado 'healthy'."
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "Esperando servicios... (intento $ATTEMPT/$MAX_ATTEMPTS) [DB: $DB_STATUS, KeyDB: $REDIS_STATUS, API: $API_STATUS]"
    sleep 3
done

if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
    echo -e "\e[31m[ERROR] Tiempo de espera agotado para el inicio saludable de los contenedores.\e[0m"
    docker compose -f docker-compose.prod.local.yml logs
    docker compose -f docker-compose.prod.local.yml down -v
    exit 1
fi

echo -e "\n[4/6] Ejecutando pruebas sintéticas de endpoints de producción..."
# Prueba 1: Endpoint de Salud
curl -fsS http://127.0.0.1:8000/health > /dev/null
echo "✔ Endpoint /health respondiendo HTTP 200 (healthy)."

# Prueba 2: Instrumentación de Métricas Prometheus
curl -fsS http://127.0.0.1:8000/metrics | grep -q "http_request"
echo "✔ Endpoint /metrics exportando métricas Prometheus correctamente."

# Prueba 3: Consulta de Estado Bootstrap inicial (debe ser false)
BOOTSTRAP_STATUS=$(curl -fsS http://127.0.0.1:8000/api/v1/auth/bootstrap-status)
echo "Estado inicial de bootstrap: $BOOTSTRAP_STATUS"
echo "$BOOTSTRAP_STATUS" | grep -q '"is_bootstrapped":false'
echo "✔ Endpoint /api/v1/auth/bootstrap-status reporta correctamente que el sistema requiere inicio."

# Prueba 4: Servidor Web Nginx Frontend
UI_PORT="${ROSGRID_HTTP_PORT:-8085}"
curl -fsS "http://127.0.0.1:${UI_PORT}/" | grep -q "RoSGrid"
echo "✔ Servidor Nginx (UI) entregando el bundle compilado de producción en puerto ${UI_PORT}."

echo -e "\n[5/6] Probando aprovisionamiento del Super Administrador con crear_admin.py..."
docker exec rosgrid_api_local python3 /app/scripts/crear_admin.py \
    --tenant-name "ISP Test Local" \
    --tenant-slug "isp-local" \
    --username "admin_local" \
    --email "admin@isp-local.test" \
    --password "ClaveSegura123!" \
    --full-name "Administrador de Pruebas"

# Verificar que ahora el bootstrap-status responde is_bootstrapped: true
BOOTSTRAP_STATUS_AFTER=$(curl -fsS http://127.0.0.1:8000/api/v1/auth/bootstrap-status)
echo "Estado posterior de bootstrap: $BOOTSTRAP_STATUS_AFTER"
echo "$BOOTSTRAP_STATUS_AFTER" | grep -q '"is_bootstrapped":true'
echo "✔ Verificado que el sistema transiciona a 'is_bootstrapped: true' tras ejecutar crear_admin.py."

echo -e "\n[6/6] Desmantelando entorno de prueba y limpiando volúmenes efímeros..."
docker compose -f docker-compose.prod.local.yml down -v

echo "=============================================================================="
echo -e "\e[32m  🎉 ¡Todas las pruebas locales de producción fueron superadas al 100%!  \e[0m"
echo "=============================================================================="
exit 0
