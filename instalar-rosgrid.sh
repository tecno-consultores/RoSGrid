#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Script de Instalación No-Root para RoSGrid v1.0.0 (Soporte Local y Remoto vía curl)

set -euo pipefail

# 1. Validación estricta de permisos de usuario (Regla corporativa 11X)
if [[ "$EUID" -eq 0 ]]; then
    echo -e "\e[31m[ERROR] Este script NUNCA debe ejecutarse como root.\e[0m"
    echo "Ejecútalo con tu usuario habitual que pertenezca al grupo 'docker'."
    exit 1
fi

# Validar pertenencia al grupo docker
if ! groups | grep -qw docker; then
    echo -e "\e[31m[ERROR] Tu usuario actual no forma parte del grupo 'docker'.\e[0m"
    echo "Agrega tu usuario con: sudo usermod -aG docker \$USER y reinicia sesión."
    exit 1
fi

# Función para leer entrada interactiva compatible con tuberías (curl ... | bash)
leer_entrada() {
    local prompt="$1"
    local var_name="$2"
    local valor_defecto="${3:-}"
    local respuesta=""

    if [[ -t 0 ]]; then
        read -r -p "$prompt" respuesta || true
    elif [[ -c /dev/tty ]] && read -r -p "$prompt" respuesta < /dev/tty 2>/dev/null; then
        :
    else
        respuesta="$valor_defecto"
    fi
    respuesta="${respuesta:-$valor_defecto}"
    printf -v "$var_name" '%s' "$respuesta"
}

clear 2>/dev/null || true
echo "=============================================================================="
echo "          🚀 Asistente de Instalación No-Root de RoSGrid v1.0.0              "
echo "=============================================================================="

# 2. Verificación de herramientas prerrequisito
echo -e "\n[1/5] Verificando dependencias en el host..."

# Verificar comandos base individuales
for cmd in docker openssl curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "\e[31m[ERROR] El comando requerido '$cmd' no está instalado en el sistema.\e[0m"
        exit 1
    fi
done

# Verificar específicamente que Docker Compose (plugin v2) funcione correctamente
if ! docker compose version &> /dev/null; then
    echo -e "\e[31m[ERROR] El plugin de 'docker compose' no está disponible o no está instalado en Docker.\e[0m"
    exit 1
fi

echo "✔ Docker, Docker Compose y dependencias locales verificadas."

# 3. Detección de Modo Dual: Local (repo clonado) vs Remoto Standalone (curl | bash)
RAW_BASE_URL="${RAW_BASE_URL:-https://raw.githubusercontent.com/tecno-consultores/RoSGrid/main}"
IS_REMOTE=false

if [[ ! -f .env.example || ! -f docker-compose.prod.yml ]]; then
    IS_REMOTE=true
fi

# Comprobación de variables de entorno (.env):
# - Modo Local: Busca un archivo .env y lo carga si existe; si no se encuentra, usa valores por defecto.
# - Modo Remoto (curl | bash): Como no estará el .env inicialmente, se usan los valores por defecto del sistema.
if [[ "$IS_REMOTE" == "false" ]]; then
    if [[ -f .env ]]; then
        echo -e "\n[INFO] Modo local: Archivo '.env' encontrado. Cargando variables de configuración..."
        set -a
        # shellcheck source=/dev/null
        source .env
        set +a
        echo "✔ Configuración local cargada desde .env."
    else
        echo -e "\n[INFO] Modo local: No se encontró archivo '.env' previo. Se emplearán los valores por defecto."
    fi
else
    echo -e "\n[INFO] Modo de instalación remota standalone detectado."
    echo "[INFO] No se dispone de archivo .env previo; se utilizarán los valores por defecto del sistema."
fi

if [[ "$IS_REMOTE" == "true" ]]; then
    INSTALL_DIR="${ROSGRID_INSTALL_DIR:-/opt/rosgrid}"
    echo "Directorio de destino: $INSTALL_DIR"

    if [[ ! -d "$INSTALL_DIR" ]]; then
        PARENT_DIR="$(dirname "$INSTALL_DIR")"
        if [[ -w "$PARENT_DIR" ]]; then
            mkdir -p "$INSTALL_DIR"
        else
            echo -e "\e[33m[INFO] Se requieren privilegios sudo únicamente para crear y asignar '$INSTALL_DIR' a tu usuario ($USER)...\e[0m"
            if command -v sudo &>/dev/null; then
                sudo mkdir -p "$INSTALL_DIR"
                sudo chown -R "$USER:$(id -gn)" "$INSTALL_DIR"
            else
                echo -e "\e[31m[ERROR] El directorio '$INSTALL_DIR' no existe y 'sudo' no está disponible.\e[0m"
                exit 1
            fi
        fi
    fi

    cd "$INSTALL_DIR"

    echo "Descargando manifiestos de despliegue desde GitHub ($RAW_BASE_URL)..."
    curl -fsSL "${RAW_BASE_URL}/.env.example" -o .env.example
    curl -fsSL "${RAW_BASE_URL}/docker-compose.prod.yml" -o docker-compose.prod.yml
    echo "✔ Manifiestos de despliegue descargados en $INSTALL_DIR."

    echo "Descargando Skill oficial para Agentes IA (rosgrid-noc-operator)..."
    mkdir -p skills/rosgrid-noc-operator/references skills/rosgrid-noc-operator/configs
    curl -fsSL "${RAW_BASE_URL}/.agents/skills/rosgrid-noc-operator/SKILL.md" -o skills/rosgrid-noc-operator/SKILL.md || true
    curl -fsSL "${RAW_BASE_URL}/.agents/skills/rosgrid-noc-operator/references/mcp_tools.md" -o skills/rosgrid-noc-operator/references/mcp_tools.md || true
    curl -fsSL "${RAW_BASE_URL}/.agents/skills/rosgrid-noc-operator/references/routeros_flags.md" -o skills/rosgrid-noc-operator/references/routeros_flags.md || true
    curl -fsSL "${RAW_BASE_URL}/.agents/skills/rosgrid-noc-operator/configs/claude_desktop.json" -o skills/rosgrid-noc-operator/configs/claude_desktop.json || true
    curl -fsSL "${RAW_BASE_URL}/.agents/skills/rosgrid-noc-operator/configs/hermes_agent.yaml" -o skills/rosgrid-noc-operator/configs/hermes_agent.yaml || true
    echo "✔ Skill oficial rosgrid-noc-operator descargada en $INSTALL_DIR/skills/rosgrid-noc-operator."
fi

# 4. Configuración del archivo de variables de entorno (.env) y manejo de volúmenes
echo -e "\n[2/5] Configurando variables de entorno y secretos criptográficos..."
GENERAR_SECRETOS=true
RECREAR_VOLUMENES=false

if [[ -f .env ]]; then
    respuesta=""
    leer_entrada $'\e[33m[AVISO] Ya existe un archivo .env en el directorio. ¿Deseas sobrescribirlo y limpiar la BD? (s/N): \e[0m' respuesta "N"
    if [[ "$respuesta" =~ ^[sS]$ ]]; then
        cp .env.example .env
        RECREAR_VOLUMENES=true
        echo "✔ Archivo .env reiniciado desde la plantilla y programada limpieza de volúmenes."
    else
        GENERAR_SECRETOS=false
        echo "✔ Conservando el archivo .env y los secretos existentes."
    fi
else
    cp .env.example .env
    # Si es una instalación nueva pero ya existía un volumen viejo, prevenimos conflictos de credenciales
    if docker volume inspect rosgrid_pg_data &>/dev/null; then
        echo -e "\e[33m[AVISO] Se detectó un volumen de PostgreSQL previo ('rosgrid_pg_data').\e[0m"
        purgar=""
        leer_entrada "¿Deseas purgar el volumen anterior para evitar conflictos de contraseña? (S/n): " purgar "S"
        if [[ "$purgar" =~ ^[sS]$ ]]; then
            RECREAR_VOLUMENES=true
        fi
    fi
    echo "✔ Archivo .env creado desde la plantilla base."
fi

# 5. Generación de entropía y secretos criptográficos automáticos de 256 bits
echo -e "\n[3/5] Verificando llaves criptográficas de alta seguridad..."
if [[ "$GENERAR_SECRETOS" == "true" ]]; then
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
    sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24)|" .env
    sed -i "s|ROSGRID_MASTER_VAULT_KEY=.*|ROSGRID_MASTER_VAULT_KEY=$(openssl rand -base64 32)|" .env
    sed -i "s|ROSGRID_JWT_SECRET_KEY=.*|ROSGRID_JWT_SECRET_KEY=$(openssl rand -base64 48)|" .env
    sed -i "s|ROSGRID_CSRF_HMAC_SECRET=.*|ROSGRID_CSRF_HMAC_SECRET=$(openssl rand -base64 48)|" .env
    echo "✔ Nuevos secretos generados e inyectados en .env."
else
    echo "✔ Se mantienen las llaves criptográficas actuales de .env."
fi

# Asegurar permisos estrictos de lectura exclusiva para el propietario
chmod 600 .env
echo "✔ Permisos 600 verificados sobre .env."

# Cargar/recargar las variables finales de .env para que el script use los valores consolidados
set -a
# shellcheck source=/dev/null
source .env
set +a

# Purgar volúmenes antiguos si se solicitó por incompatibilidad de credenciales
if [[ "$RECREAR_VOLUMENES" == "true" ]]; then
    echo -e "\e[33m[INFO] Purgando contenedores y volúmenes antiguos de base de datos...\e[0m"
    docker compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
    echo "✔ Volúmenes anteriores purgados exitosamente."
fi

# 6. Ejecución del auditor de infraestructura (Trivy IaC si existe localmente)
if [[ -f ./auditar-infra.sh ]]; then
    echo -e "\n[4/5] Ejecutando auditoría de seguridad IaC (Trivy)..."
    chmod +x ./auditar-infra.sh
    if ./auditar-infra.sh; then
        echo "✔ Auditoría de infraestructura superada sin vulnerabilidades CRITICAL/HIGH."
    else
        echo -e "\e[31m[ERROR] La auditoría de seguridad detectó fallos. Revisa la salida superior.\e[0m"
        exit 1
    fi
else
    echo -e "\n[4/5] Omitiendo auditoría Trivy (script auditar-infra.sh no encontrado en el entorno)."
fi

# 7. Despliegue de contenedores utilizando Docker Compose
API_CONTAINER="rosgrid_api"
option="1"

if [[ "$IS_REMOTE" == "true" ]]; then
    echo -e "\n[5/5] Desplegando el stack de contenedores RoSGrid (Producción Oficial Docker Hub)..."
    docker compose -f docker-compose.prod.yml pull
    docker compose -f docker-compose.prod.yml up -d
else
    echo -e "\n[5/5] Desplegando el stack de contenedores RoSGrid..."
    echo "Selecciona el modo de despliegue:"
    echo "  1) Producción Remota (Docker Hub: imágenes precompiladas oficiales)"
    echo "  2) Producción Local (Compilar y ejecutar imágenes de producción localmente sin Docker Hub) [Recomendado para pruebas]"
    echo "  3) Desarrollo / Laboratorio (Montaje de código fuente en vivo)"
    leer_entrada "Ingresa tu opción (1, 2 o 3) [1]: " option "1"

    if [[ "$option" == "1" ]]; then
        echo "Desplegando con docker-compose.prod.yml..."
        docker compose -f docker-compose.prod.yml pull
        docker compose -f docker-compose.prod.yml up -d
    elif [[ "$option" == "2" ]]; then
        echo "Construyendo y desplegando con docker-compose.prod.local.yml..."
        docker build -f fastapi/Dockerfile -t sinfallas/rosgrid-backend:local-test fastapi
        docker build -f vue3/Dockerfile -t sinfallas/rosgrid-frontend:local-test vue3
        docker compose -f docker-compose.prod.local.yml up -d
        API_CONTAINER="rosgrid_api_local"
    elif [[ "$option" == "3" ]]; then
        echo "Desplegando con docker-compose.yml (Desarrollo)..."
        docker compose pull rosgrid-db rosgrid-redis rosgrid-api rosgrid-worker rosgrid-ui
        docker compose up -d
    else
        echo -e "\e[31m[ERROR] Opción no válida: '$option'. Debe ser 1, 2 o 3.\e[0m"
        exit 1
    fi
fi

echo -e "\nEsperando a que la API complete las migraciones de base de datos..."
for _ in {1..30}; do
    if docker exec "$API_CONTAINER" curl -fsS http://127.0.0.1:8000/health &>/dev/null; then
        break
    fi
    sleep 2
done

echo -e "\nVerificando inicialización de cuenta administrativa..."
if docker exec "$API_CONTAINER" python3 /app/scripts/crear_admin.py --check-only &>/dev/null; then
    echo "✔ Ya existen cuentas de usuario registradas en la base de datos."
else
    echo -e "\e[33m[AVISO] No se detectó ningún usuario en la base de datos de RoSGrid.\e[0m"
    echo "Puedes crear el Super Administrador ahora desde la consola o hacerlo a través de la web."
    crear_adm=""
    leer_entrada "¿Deseas ejecutar el asistente de creación del Super Administrador ahora? (S/n): " crear_adm "S"
    if [[ "$crear_adm" =~ ^[sS]$ ]]; then
        if [[ -t 0 ]]; then
            docker exec -it "$API_CONTAINER" python3 /app/scripts/crear_admin.py
        elif [[ -c /dev/tty ]]; then
            docker exec -it "$API_CONTAINER" python3 /app/scripts/crear_admin.py < /dev/tty
        else
            echo "Terminal no interactiva detectada. Puedes crear el Super Administrador luego ejecutando:"
            echo "  docker exec -it $API_CONTAINER python3 /app/scripts/crear_admin.py"
        fi
    fi
fi

echo -e "\n=============================================================================="
echo -e "\e[32m       🎉 ¡Instalación de RoSGrid completada exitosamente sin root!       \e[0m"
echo "=============================================================================="
if [[ "$option" == "2" ]]; then
    PORT_DISPLAY="${ROSGRID_HTTP_PORT:-8085}"
else
    PORT_DISPLAY="${ROSGRID_HTTP_PORT:-8080}"
fi
echo "Accede a la consola web en: http://localhost:${PORT_DISPLAY} (o la IP/puerto configurado)"
echo "Para verificar el estado de los logs ejecuta:"
echo "  docker logs -f $API_CONTAINER"
if [[ "$IS_REMOTE" == "true" ]]; then
    echo -e "\nLos archivos de despliegue y configuración están en: $INSTALL_DIR"
    echo "Comandos útiles desde $INSTALL_DIR:"
    echo "  docker compose -f docker-compose.prod.yml ps"
    echo "  docker compose -f docker-compose.prod.yml down"
    echo "  docker compose -f docker-compose.prod.yml up -d"
fi
if [[ -d skills/rosgrid-noc-operator ]]; then
    echo -e "\n🤖 Skill Oficial para Agentes IA (rosgrid-noc-operator):"
    echo "  Directorio local: $(pwd)/skills/rosgrid-noc-operator"
    echo "  Consulta pública vía API: http://localhost:${PORT_DISPLAY}/api/v1/mcp/skill"
fi
echo "=============================================================================="
exit 0
