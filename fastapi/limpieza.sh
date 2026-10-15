#!/usr/bin/env bash
# Licencia: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
LC_ALL=C

if [[ "$EUID" != "0" ]]; then
	if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
		exec sudo "$0" "$@"
	fi
	echo "Aviso: Ejecutando limpieza sin privilegios directos de superusuario..."
fi

clear
echo "Iniciando purga profunda del entorno de QA de FastAPI (Nivel 11X)..."

rm -f .coverage
rm -rf .mypy_cache
rm -rf .pytest_cache
rm -rf .ruff_cache
rm -rf .tox
rm -rf .uv/
rm -rf dist
rm -rf tests/__pycache__
rm -rf src/*/__pycache__
rm -rf htmlcov/
rm -rf mutants/
rm -rf target/
rm -rf test/target/
rm -f zap-report.html
rm -f chaos-report.html
rm -f profile.svg
rm -f *.log
# rm -rf graphify-out/  # Preservado intacto para documentación y auditoría
rm -rf prometheus_data/

chown -R "$USER:$USER" . 2>/dev/null || true

# Apagar infraestructuras y perfiles ocultos para liberar redes y forzar purga de volúmenes de caché (uv-cache)
docker compose -f docker-compose.qa.yml down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile chaos down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile graphify down -v 2>/dev/null || true

docker system prune -f --volumes 2>/dev/null || true

echo "Limpieza de caché, reportes, imágenes y contenedores finalizada exitosamente."
exit 0
