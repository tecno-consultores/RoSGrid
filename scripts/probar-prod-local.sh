#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Pipeline Integral de Validación y Pruebas Locales de Imágenes de Producción a Petición del Usuario

LC_ALL=C
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Configuración y Parámetros por Defecto
KEEP_ALIVE=false
SKIP_BUILD=false
RUN_AUDIT=false
CLEAN_WIZARD=false
UI_PORT="${ROSGRID_HTTP_PORT:-8085}"
COMPOSE_FILE="docker-compose.prod.local.yml"

# Mostrar Ayuda de Uso
mostrar_ayuda() {
    cat << EOF
==============================================================================
  🚀 Pipeline de Pruebas Locales de Producción RoSGrid (QA 11X)
==============================================================================
Uso: ./scripts/probar-prod-local.sh [OPCIONES]

Opciones disponibles:
  -h, --help           Muestra esta ayuda y termina.
  -k, --keep-alive     Mantiene los contenedores y servicios corriendo al finalizar
                       las pruebas para inspección interactiva manual en el navegador.
  -w, --wizard         Modo Asistente Inicial: Omite la creación de admin_local y mantiene
                       el sistema activo en estado is_bootstrapped: false para registrarse
                       manualmente desde el navegador (incluye --keep-alive implícito).
  -s, --skip-build     Omite la fase de compilación local si las imágenes ya fueron
                       construidas previamente en la caché Docker.
  -a, --audit          Ejecuta la auditoría estática de seguridad de infraestructura
                       (./scripts/auditar-infra.sh: Trivy IaC, CVEs y secretos) antes del despliegue.
  -d, --down, --stop   Apaga y desmantela el entorno local de pruebas (contenedores, redes y volúmenes).
  -p, --port PUERTO    Especifica el puerto del host para acceder al Frontend Nginx
                       (Predeterminado: 8085 o variable ROSGRID_HTTP_PORT).

Fases del Pipeline de Validación:
  [1/6] Auditoría y Preparación de Imágenes de Producción (Trivy / Docker build)
  [2/6] Despliegue en Aislamiento Sintético con docker-compose.prod.local.yml
  [3/6] Estabilización y Verificación de Healthchecks (PostgreSQL, KeyDB, FastAPI, Worker)
  [4/6] Pruebas Sintéticas HTTP, Hardening y Proxy Nginx (/health, /metrics, proxy, 404 docs, 401 unauth)
  [5/6] Aprovisionamiento E2E, Token MCP, Invocación JSON-RPC y Suite Front-Back (24 Contratos)
  [6/6] Inspección de Logs (API y Worker), Aislamiento de Red y Cierre Limpio

Ejemplos:
  ./scripts/probar-prod-local.sh                     # Ejecución completa estándar automatizada
  ./scripts/probar-prod-local.sh --keep-alive        # Valida y deja el sistema levantado para probar en navegador
  ./scripts/probar-prod-local.sh --down              # Apaga el stack activo y libera todos los recursos
  ./scripts/probar-prod-local.sh --skip-build        # Revalida el stack rápidamente sin recompilar imágenes
  ./scripts/probar-prod-local.sh -a -k -p 8090       # Auditoría previa, levanta en puerto 8090 y mantiene activo
==============================================================================
EOF
}

# Procesar Argumentos de Línea de Comandos
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            mostrar_ayuda
            exit 0
            ;;
        -d|--down|--stop)
            echo -e "\n🧹 Deteniendo y desmantelando el stack de pruebas de producción (${COMPOSE_FILE})..."
            docker compose -f "$COMPOSE_FILE" down -v
            echo -e "\e[32m✔ Stack local de producción apagado y volúmenes efímeros liberados exitosamente.\e[0m"
            exit 0
            ;;
        -k|--keep-alive)
            KEEP_ALIVE=true
            shift
            ;;
        -w|--wizard)
            CLEAN_WIZARD=true
            KEEP_ALIVE=true
            shift
            ;;
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -a|--audit)
            RUN_AUDIT=true
            shift
            ;;
        -p|--port)
            if [ -z "${2:-}" ]; then
                echo -e "\e[31m[ERROR] Debe especificar un número de puerto tras $1.\e[0m" >&2
                exit 1
            fi
            UI_PORT="$2"
            shift 2
            ;;
        *)
            echo -e "\e[31m[ERROR] Opción desconocida: $1\e[0m" >&2
            mostrar_ayuda
            exit 1
            ;;
    esac
done

export ROSGRID_HTTP_PORT="$UI_PORT"

echo "=============================================================================="
echo "      🚀 Pipeline de Pruebas Locales de Producción RoSGrid (QA 11X)         "
echo "=============================================================================="
echo "  • Puerto Frontend UI:   http://127.0.0.1:${UI_PORT}"
echo "  • Endpoint API Backend: http://127.0.0.1:8000"
echo "  • Recompilar Imágenes:  $([ "$SKIP_BUILD" = true ] && echo "NO (usando caché local)" || echo "SÍ")"
echo "  • Auditoría Trivy IaC:  $([ "$RUN_AUDIT" = true ] && echo "SÍ (auditar-infra.sh)" || echo "Omitida")"
echo "  • Modo Keep-Alive:      $([ "$KEEP_ALIVE" = true ] && echo "ACTIVO (no se apagará al terminar)" || echo "DESACTIVADO (desmantelamiento automático)")"
echo "------------------------------------------------------------------------------"

# 1. Comprobar herramientas CLI
for cmd in docker curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "\e[31m[ERROR] Comando requerido no encontrado en el sistema: $cmd\e[0m" >&2
        exit 1
    fi
done

# Función de captura de errores para desmantelamiento seguro si algo falla
# shellcheck disable=SC2329
limpiar_en_fallo() {
    local exit_code=$?
    if [ "$exit_code" -ne 0 ]; then
        echo -e "\n\e[31m[FALLO] El pipeline de validación encontró un error (código de salida: $exit_code).\e[0m" >&2
        echo "Extrayendo logs de diagnóstico de los contenedores..." >&2
        docker compose -f "$COMPOSE_FILE" logs --tail=40 || true
        echo "Desmantelando entorno de prueba tras fallo..." >&2
        docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
    fi
}
trap limpiar_en_fallo EXIT

# Fase 1: Auditoría y Preparación de Imágenes
echo -e "\n[1/6] Auditoría y Preparación de Imágenes de Producción..."
if [ "$RUN_AUDIT" = true ]; then
    echo "Ejecutando auditoría de infraestructura y seguridad (Trivy)..."
    "${SCRIPT_DIR}/auditar-infra.sh"
fi

if [ "$SKIP_BUILD" = false ]; then
    echo "Construyendo imagen de producción del Backend (sinfallas/rosgrid-backend:local-test)..."
    docker build -f fastapi/Dockerfile -t sinfallas/rosgrid-backend:local-test fastapi
    echo "Construyendo imagen de producción del Frontend (sinfallas/rosgrid-frontend:local-test)..."
    docker build -f vue3/Dockerfile -t sinfallas/rosgrid-frontend:local-test vue3
else
    echo "Omitiendo compilación de imágenes según argumento --skip-build."
fi

# Fase 2: Despliegue en Aislamiento Sintético
echo -e "\n[2/6] Levantando stack de producción local con ${COMPOSE_FILE}..."
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" up -d

# Fase 3: Estabilización y Verificación de Healthchecks
echo -e "\n[3/6] Esperando estabilización y healthchecks de contenedores..."
MAX_ATTEMPTS=45
ATTEMPT=0

until [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; do
    DB_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_db_local 2>/dev/null || echo '"unknown"')
    REDIS_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_redis_local 2>/dev/null || echo '"unknown"')
    API_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_api_local 2>/dev/null || echo '"unknown"')
    WORKER_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' rosgrid_worker_local 2>/dev/null || echo '"unknown"')

    if [ "$DB_STATUS" = '"healthy"' ] && [ "$REDIS_STATUS" = '"healthy"' ] && [ "$API_STATUS" = '"healthy"' ] && [ "$WORKER_STATUS" = '"healthy"' ]; then
        echo "✔ Base de Datos PostgreSQL 17, KeyDB Multi-Hilo, FastAPI y Runner de Workers alcanzaron estado 'healthy'."
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "Esperando servicios... (intento $ATTEMPT/$MAX_ATTEMPTS) [DB: $DB_STATUS, KeyDB: $REDIS_STATUS, API: $API_STATUS, Worker: $WORKER_STATUS]"
    sleep 3
done

if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
    echo -e "\e[31m[ERROR] Tiempo de espera agotado para el inicio saludable de los contenedores.\e[0m" >&2
    exit 1
fi

# Fase 4: Pruebas Sintéticas de Endpoints de Producción
echo -e "\n[4/6] Ejecutando pruebas sintéticas de endpoints de producción..."
# Prueba 0: Smoke Test de Arranque Estricto de Producción (--no-dev)
echo "Ejecutando Smoke Test de arranque estricto (--no-dev) dentro del contenedor de producción..."
docker exec rosgrid_api_local python3 /app/scripts/test_production_boot_smoke.py

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

# Prueba 4: Servidor Web Nginx Frontend y Cabeceras de Seguridad
curl -fsS "http://127.0.0.1:${UI_PORT}/" | grep -q "RoSGrid"
UI_HEADERS=$(curl -sI "http://127.0.0.1:${UI_PORT}/")
echo "$UI_HEADERS" | grep -iq "x-frame-options: DENY"
echo "$UI_HEADERS" | grep -iq "x-content-type-options: nosniff"
echo "✔ Servidor Nginx (UI) entregando bundle compilado y cabeceras de seguridad en puerto ${UI_PORT}."

# Prueba 5: Proxy Inverso Nginx hacia FastAPI (/api/...)
PROXY_BOOTSTRAP=$(curl -fsS "http://127.0.0.1:${UI_PORT}/api/v1/auth/bootstrap-status")
echo "$PROXY_BOOTSTRAP" | grep -q '"is_bootstrapped":false'
echo "✔ Proxy inverso Nginx (http://127.0.0.1:${UI_PORT}/api/...) enrutando correctamente a FastAPI."

# Prueba 6: Ocultamiento Estricto de Documentación en Producción (Hardening Trivy)
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs)
OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/openapi.json)
if [ "$DOCS_CODE" -eq 404 ] && [ "$OPENAPI_CODE" -eq 404 ]; then
    echo "✔ Hardening verificado: Swagger (/docs: HTTP $DOCS_CODE) y OpenAPI (/openapi.json: HTTP $OPENAPI_CODE) devuelven 404."
else
    echo -e "\e[31m[ERROR] Swagger/OpenAPI accesible en producción (Docs: HTTP $DOCS_CODE, OpenAPI: HTTP $OPENAPI_CODE).\e[0m" >&2
    exit 1
fi

# Prueba 7: Comportamiento de Seguridad Fail-Closed (401 sin Bearer Token)
UNAUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/auth/me)
if [ "$UNAUTH_CODE" -eq 401 ]; then
    echo "✔ Comportamiento Fail-Closed verificado: Petición sin credenciales a /api/v1/auth/me rechazada con HTTP 401."
else
    echo -e "\e[31m[ERROR] /api/v1/auth/me no devolvió HTTP 401 sin autenticación (recibido: HTTP $UNAUTH_CODE).\e[0m" >&2
    exit 1
fi

# Fase 5: Aprovisionamiento E2E, Token Bearer MCP y Validación de Contratos
if [ "$CLEAN_WIZARD" = true ]; then
    echo -e "\n[5/6] Modo Asistente de Registro Limpio (--wizard)..."
    echo "✔ Omitiendo creación automática de admin_local."
    echo "✔ Verificado que el sistema requiere inicio (is_bootstrapped: false) para el Wizard."
else
    echo -e "\n[5/6] Probando aprovisionamiento del Super Administrador, Servidor MCP y Contratos Front-Back..."
    docker exec rosgrid_api_local python3 /app/scripts/crear_admin.py \
        --tenant-name "ISP Validación Local" \
        --tenant-slug "isp-local" \
        --username "admin_local" \
        --email "admin@isp-local.test" \
        --password "ClaveSegura123!" \
        --full-name "Administrador de Pruebas"

    # Verificar transición de bootstrap-status a true
    BOOTSTRAP_STATUS_AFTER=$(curl -fsS http://127.0.0.1:8000/api/v1/auth/bootstrap-status)
    echo "Estado posterior de bootstrap: $BOOTSTRAP_STATUS_AFTER"
    echo "$BOOTSTRAP_STATUS_AFTER" | grep -q '"is_bootstrapped":true'
    echo "✔ Verificado que el sistema transiciona a 'is_bootstrapped: true' tras ejecutar crear_admin.py."

    # Prueba de Generación y Validación de Token Bearer MCP
    echo "Probando generación de Token MCP con generar_token_mcp.py..."
    TOKEN_MCP=$(docker exec rosgrid_api_local python3 /app/scripts/generar_token_mcp.py \
        --username "admin_local" \
        --tenant-slug "isp-local" \
        --raw-token)

    if [ -z "$TOKEN_MCP" ]; then
        echo -e "\e[31m[ERROR] Falló la generación del token Bearer MCP.\e[0m" >&2
        exit 1
    fi
    echo "✔ Token Bearer MCP generado exitosamente (longitud: ${#TOKEN_MCP} caracteres)."

    # Llamada autenticada con Bearer Token a /api/v1/auth/me
    ME_RESPONSE=$(curl -fsS -H "Authorization: Bearer ${TOKEN_MCP}" http://127.0.0.1:8000/api/v1/auth/me)
    echo "Respuesta de autenticación Bearer /api/v1/auth/me: $ME_RESPONSE"
    echo "$ME_RESPONSE" | grep -q '"tslug":"isp-local"'
    echo "✔ Verificado que el Token Bearer MCP autentica exitosamente contra KeyDB y la API REST."

    # Invocación Real del Servidor MCP JSON-RPC 2.0 (POST /api/v1/mcp)
    echo "Probando invocación al Servidor MCP (POST /api/v1/mcp) con protocolo JSON-RPC 2.0..."
    MCP_RPC_PAYLOAD='{"jsonrpc":"2.0","method":"tools/list","id":1}'
    MCP_RESPONSE=$(curl -fsS -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN_MCP}" \
        -d "$MCP_RPC_PAYLOAD" \
        http://127.0.0.1:8000/api/v1/mcp)
    echo "Respuesta MCP JSON-RPC 2.0: $(echo "$MCP_RESPONSE" | cut -c1-120)..."
    echo "$MCP_RESPONSE" | grep -q '"tools"'
    echo "✔ Endpoint MCP (/api/v1/mcp) respondió JSON-RPC 2.0 con catálogo de Tools semánticas correctamente."

    # Ejecución de la Suite de 24 Contratos Front-Back (validar_comunicacion_front_back.py)
    echo "Ejecutando suite automatizada de 24 contratos Front-Back (validar_comunicacion_front_back.py)..."
    docker exec rosgrid_api_local python3 /app/scripts/validar_comunicacion_front_back.py
    echo "✔ Suite de integración Front-Back superada al 100% (24/24 contratos validados)."

    # Inspección de logs de API y Worker en busca de excepciones no controladas
    echo "Comprobando ausencia de errores críticos y tracebacks en logs de API y Worker..."
    if docker logs rosgrid_api_local 2>&1 | grep -iE "(Traceback \(most recent call last\)|CRITICAL|Unhandled exception)" | grep -v "test_"; then
        echo -e "\e[31m[ADVERTENCIA] Se detectaron errores o tracebacks sospechosos en los logs de la API.\e[0m" >&2
    else
        echo "✔ Logs de rosgrid_api_local limpios sin tracebacks de runtime."
    fi

    if docker logs rosgrid_worker_local 2>&1 | grep -iE "(Traceback \(most recent call last\)|CRITICAL|Unhandled exception)" | grep -v "test_"; then
        echo -e "\e[31m[ADVERTENCIA] Se detectaron errores o tracebacks sospechosos en los logs del Worker.\e[0m" >&2
    else
        echo "✔ Logs de rosgrid_worker_local limpios sin tracebacks de runtime."
    fi
fi

# Fase 6: Desmantelamiento o Modo Interactivo
echo -e "\n[6/6] Finalización del Pipeline..."

# Verificación de Aislamiento de Red Interna (Puertos 5432 y 6379 no expuestos al host)
echo "Verificando aislamiento de red interna (puertos 5432 y 6379 no expuestos al host)..."
if curl -s --connect-timeout 1 http://127.0.0.1:5432 >/dev/null 2>&1 || curl -s --connect-timeout 1 http://127.0.0.1:6379 >/dev/null 2>&1; then
    echo -e "\e[31m[ERROR] Brecha de seguridad detectada: Puerto de base de datos o KeyDB accesible directamente en el host.\e[0m" >&2
    exit 1
fi
echo "✔ Aislamiento de red verificado: Puertos de PostgreSQL y KeyDB protegidos en red interna Docker."

if [ "$CLEAN_WIZARD" = true ]; then
    trap - EXIT
    echo "=============================================================================="
    echo -e "\e[32m  🎉 ¡Stack local de producción listo para registro manual!  \e[0m"
    echo "=============================================================================="
    echo "El stack permanece ACTIVO (--wizard) para tu registro interactivo en el navegador:"
    echo "  • Interfaz Web (NOC):    http://localhost:${UI_PORT}"
    echo "  • API Backend:           http://localhost:8000"
    echo "  • Estado Bootstrap:      is_bootstrapped: false (Registro abierto)"
    echo "------------------------------------------------------------------------------"
    echo "Para apagar el stack y liberar los recursos cuando termines, ejecuta:"
    echo "  ./scripts/probar-prod-local.sh --down"
    echo "  (o alternativamente: docker compose -f ${COMPOSE_FILE} down -v)"
    echo "=============================================================================="
    exit 0
elif [ "$KEEP_ALIVE" = true ]; then
    # Desactivar trampa para evitar desmontaje automático al salir
    trap - EXIT
    echo "=============================================================================="
    echo -e "\e[32m  🎉 ¡Todas las pruebas locales de producción fueron superadas al 100%!  \e[0m"
    echo "=============================================================================="
    echo "El stack permanece ACTIVO (--keep-alive) para tu inspección interactiva:"
    echo "  • Interfaz Web (NOC):    http://localhost:${UI_PORT}"
    echo "  • API Backend:           http://localhost:8000 (Swagger /docs desactivado en producción)"
    echo "  • Endpoint MCP IA:       http://localhost:8000/api/v1/mcp (JSON-RPC 2.0 con Bearer Token)"
    echo "  • Organización (Slug):   isp-local"
    echo "  • Usuario Super Admin:   admin_local"
    echo "  • Contraseña:            ClaveSegura123!"
    echo "------------------------------------------------------------------------------"
    echo "Para apagar el stack y liberar los recursos cuando termines, ejecuta:"
    echo "  ./scripts/probar-prod-local.sh --down"
    echo "  (o alternativamente: docker compose -f ${COMPOSE_FILE} down -v)"
    echo "=============================================================================="
    exit 0
else
    echo "Desmantelando entorno de prueba y limpiando volúmenes efímeros..."
    trap - EXIT
    docker compose -f "$COMPOSE_FILE" down -v
    echo "=============================================================================="
    echo -e "\e[32m  🎉 ¡Todas las pruebas locales de producción fueron superadas al 100%!  \e[0m"
    echo "=============================================================================="
    echo "Las imágenes locales 'sinfallas/rosgrid-backend:local-test' y"
    echo "'sinfallas/rosgrid-frontend:local-test' están certificadas para producción."
    echo "=============================================================================="
    exit 0
fi
