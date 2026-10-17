#!/usr/bin/env bash
# Made by Sinfallas <sinfallas@yahoo.com>
# Licence: GPL-3.0-only
# Propósito: Compilación Multi-Arquitectura (amd64, arm64) y Publicación a Docker Hub tras Validación Local

LC_ALL=C
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
	echo -e "\e[00;31mERROR: NO debe ser root.\e[00m" >&2
	exit 1
fi

VERSION="1.0.0"
SKIP_VALIDATION=false

# Procesar argumentos
for arg in "$@"; do
	case "$arg" in
		--skip-validation)
			SKIP_VALIDATION=true
			;;
		-h|--help)
			echo "Uso: ./build.sh [VERSION] [--skip-validation]"
			echo "Ejemplo: ./build.sh 1.2.0"
			exit 0
			;;
		*)
			if [[ ! "$arg" =~ ^-- ]]; then
				VERSION="$arg"
			fi
			;;
	esac
done

CURRENT_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

echo "=============================================================================="
echo "    📦 Publicación Multi-Arquitectura RoSGrid ${VERSION} (amd64, arm64)     "
echo "=============================================================================="

# Validación previa obligatoria antes de publicar en Docker Hub
if [ "$SKIP_VALIDATION" = false ]; then
	echo -e "\n[Paso 0] Ejecutando Pipeline de Validación Local Previo a la Publicación..."
	if ! ./probar-prod-local.sh; then
		echo -e "\n\e[31m[ERROR CRÍTICO] La validación local de imágenes falló.\e[0m" >&2
		echo -e "\e[31mSe cancela la publicación a Docker Hub para proteger el entorno de producción.\e[0m" >&2
		exit 1
	fi
	echo "✔ Validación local superada al 100%. Procediendo con compilación multi-arquitectura..."
else
	echo -e "\n[AVISO] Se ha omitido la validación local (--skip-validation)."
fi

echo -e "\n[Paso 1] Preparando emuladores multi-arquitectura con binfmt y buildx..."
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx rm container-builder 2>/dev/null || true
docker buildx create --name container-builder --driver docker-container --bootstrap --use

echo -e "\n[Paso 2] Construyendo y publicando sinfallas/rosgrid-backend para amd64 y arm64 (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64,linux/arm64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-backend:${VERSION}" \
	-t sinfallas/rosgrid-backend:latest \
	--builder=container-builder \
	-f fastapi/Dockerfile fastapi

echo -e "\n[Paso 3] Construyendo y publicando sinfallas/rosgrid-frontend para amd64 y arm64 (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64,linux/arm64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-frontend:${VERSION}" \
	-t sinfallas/rosgrid-frontend:latest \
	--builder=container-builder \
	-f vue3/Dockerfile vue3

echo -e "\n[Paso 4] Limpieza de constructores y caché temporal..."
docker buildx rm container-builder
docker system prune -af
docker builder prune -af
docker buildx prune -af

echo "=============================================================================="
echo -e "\e[32m  🎉 Publicación exitosa de RoSGrid ${VERSION} en Docker Hub (amd64, arm64) \e[0m"
echo "=============================================================================="
exit 0
