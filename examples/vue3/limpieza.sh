#!/usr/bin/env bash
# Licencia: MIT
LC_ALL=C

if [[ "$EUID" != "0" ]]; then
        echo "ERROR: debe ser root. Ejecuta con sudo ./limpieza.sh"
        exit 1
fi

clear
echo "Iniciando purga profunda del entorno de QA de Vue 3 (Nivel 11X)..."

rm -rf node_modules
rm -rf dist
rm -rf .nuxt

rm -rf test-results/
rm -rf playwright-report/
rm -rf blob-report/
rm -rf target/
rm -rf test/target/
rm -rf coverage/
rm -rf .stryker-tmp/
rm -rf lhci-reports/
rm -rf .lhcache/
rm -rf graphify-out/
rm -rf prometheus_data/
rm -f *.html
rm -f *.log

chown -R $USER:$USER . 2>/dev/null || true

# Apagar infraestructuras de perfiles ocultos para forzar purga de la caché de pnpm (pnpm-store)
docker compose -f docker-compose.qa.yml down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile observability down -v 2>/dev/null || true
docker compose -f docker-compose.qa.yml --profile graphify down -v 2>/dev/null || true
docker system prune -af --volumes

echo "Limpieza de caché, builds, reportes y contenedores finalizada."
exit 0
