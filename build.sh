#!/usr/bin/env bash
# Made by Sinfallas <sinfallas@yahoo.com>
# Licence: GPL-3.0-only

set -euo pipefail

if [[ "$EUID" = "0" ]]; then
	echo -e "\e[00;31mERROR: NO debe ser root.\e[00m"
	exit 1
fi

clear
CURRENT_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION="${1:-1.0.0}"

echo "[RoSGrid] Preparando entorno multi-arquitectura con binfmt y buildx..."
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx rm container-builder 2>/dev/null || true
docker buildx create --name container-builder --driver docker-container --bootstrap --use

echo "[RoSGrid] Construyendo y publicando sinfallas/rosgrid-backend (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-backend:${VERSION}" \
	-t sinfallas/rosgrid-backend:latest \
	--builder=container-builder \
	-f fastapi/Dockerfile fastapi

echo "[RoSGrid] Construyendo y publicando sinfallas/rosgrid-frontend (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-frontend:${VERSION}" \
	-t sinfallas/rosgrid-frontend:latest \
	--builder=container-builder \
	-f vue3/Dockerfile vue3

docker buildx rm container-builder
docker system prune -af
docker builder prune -af
docker buildx prune -af

echo "finalizado..."
exit 0
