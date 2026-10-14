#!/usr/bin/env bash
# Licencia: MIT
LC_ALL=C

if [[ "$EUID" != "0" ]]; then
        echo "ERROR: debe ser root. Ejecuta con sudo ./limpieza.sh"
        exit 1
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
rm -rf target/
rm -rf test/target/
rm -f zap-report.html
rm -f chaos-report.html
rm -f profile.svg
rm -f *.log
rm -rf graphify-out/
rm -rf prometheus_data/

chown -R $USER:$USER . 2>/dev/null || true

# Apagar infraestructuras y perfiles ocultos para liberar redes y forzar purga de volúmenes de caché (uv-cache)
docker compose -f docker-compose.qa.yml down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile chaos down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile graphify down -v 2>/dev/null || true

docker system prune -af --volumes

echo "Limpieza de caché, reportes, imágenes y contenedores finalizada exitosamente."
exit 0
