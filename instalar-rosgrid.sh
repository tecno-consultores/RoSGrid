#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Script de Instalación No-Root para RoSGrid v1.0.0

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

clear
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

# 3. Configuración del archivo de variables de entorno (.env)
echo -e "\n[2/5] Configurando variables de entorno y secretos criptográficos..."
if [[ -f .env ]]; then
    echo -e "\e[33m[AVISO] Ya existe un archivo .env en la raíz. ¿Deseas sobrescribirlo? (s/N)\e[0m"
    read -r respuesta
    if [[ "$respuesta" =~ ^[sS]$ ]]; then
        cp .env.example .env
        echo "✔ Archivo .env reiniciado desde la plantilla."
    else
        echo "✔ Conservando el archivo .env existente."
    fi
else
    cp .env.example .env
    echo "✔ Archivo .env creado desde la plantilla base."
fi

# 4. Generación de entropía y secretos criptográficos automáticos de 256 bits
echo -e "\n[3/5] Generando llaves criptográficas de alta seguridad..."
sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|ROSGRID_MASTER_VAULT_KEY=.*|ROSGRID_MASTER_VAULT_KEY=$(openssl rand -base64 32)|" .env
sed -i "s|ROSGRID_JWT_SECRET_KEY=.*|ROSGRID_JWT_SECRET_KEY=$(openssl rand -base64 48)|" .env
sed -i "s|ROSGRID_CSRF_HMAC_SECRET=.*|ROSGRID_CSRF_HMAC_SECRET=$(openssl rand -base64 48)|" .env

# Asegurar permisos estrictos de lectura exclusiva para el propietario
chmod 600 .env
echo "✔ Secretos generados e inyectados en .env (Permisos 600 aplicados)."

# 5. Ejecución del auditor de infraestructura (Trivy IaC)
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
    echo -e "\n[4/5] Omitiendo auditoría Trivy (script auditar-infra.sh no encontrado)."
fi

# 6. Despliegue de contenedores utilizando Docker Compose (Modo Producción o Local)
echo -e "\n[5/5] Desplegando el stack de contenedores RoSGrid..."
echo "Selecciona el modo de despliegue:"
echo "  1) Producción (Docker Hub: imágenes precompiladas inmutables) [Recomendado]"
echo "  2) Local / Laboratorio (Montaje de código fuente sobre imágenes base)"
read -option -p "Ingresa tu opción (1 o 2) [1]: "
option="${option:-1}"

if [[ "$option" == "1" ]]; then
    echo "Desplegando con docker-compose.prod.yml..."
    docker compose -f docker-compose.prod.yml pull
    docker compose -f docker-compose.prod.yml up -d
else
    echo "Desplegando con docker-compose.yml (Local)..."
    docker compose pull rosgrid-db rosgrid-redis rosgrid-api rosgrid-worker rosgrid-ui
    docker compose up -d
fi

echo -e "\n=============================================================================="
echo -e "\e[32m       🎉 ¡Instalación de RoSGrid completada exitosamente sin root!       \e[0m"
echo "=============================================================================="
echo "Accede a la consola web en: http://localhost:8080 (o el puerto configurado)"
echo "Para verificar el estado de las migraciones automáticas ejecuta:"
echo "  docker logs -f rosgrid_api"
echo "=============================================================================="
exit 0
