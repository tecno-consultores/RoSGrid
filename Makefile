# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Makefile canónico para desarrollo local, automatización y gobernanza Level-11X

.PHONY: help audit test test-backend test-frontend lint certify graphify build clean

help:
	@echo "Comandos canónicos de desarrollo y gobernanza para RoSGrid:"
	@echo "  make audit         - Ejecuta escaneo preventivo de seguridad (Trivy IaC & Vulnerabilidades en Docker)"
	@echo "  make test          - Ejecuta todas las pruebas unitarias (Backend y Frontend en Docker)"
	@echo "  make test-backend  - Ejecuta pruebas unitarias de FastAPI en Docker"
	@echo "  make test-frontend - Ejecuta pruebas unitarias Vitest en Docker"
	@echo "  make lint          - Ejecuta linters y chequeo de tipos (ruff, mypy, vue-tsc)"
	@echo "  make certify       - Ejecuta el gate de certificación 11X (.agents/scripts/certify_task_completion.sh)"
	@echo "  make graphify      - Extrae y actualiza los grafos AST de Graphify (Backend y Frontend en Docker)"
	@echo "  make build         - Reconstruye imágenes locales de Docker (rosgrid-api, rosgrid-ui)"
	@echo "  make clean         - Limpia artefactos temporales y contenedores de prueba"

audit:
	@echo "🔒 [Audit] Iniciando escaneo preventivo de vulnerabilidades y seguridad (Shift-Left)..."
	@./scripts/auditar-infra.sh

test-backend:
	@echo "🧪 [Test Backend] Ejecutando pytest en contenedor efímero..."
	@docker run --rm --entrypoint uv -u $$(id -u):$$(id -g) -e UV_CACHE_DIR=/tmp/uv-cache -e PYTHONPATH=/app/src -v $$(pwd)/fastapi:/app -v $$(pwd):/workspace:ro -w /app sinfallas/rosgrid-backend:local-test run pytest -o addopts="" --import-mode=importlib --no-cov tests/

test-frontend:
	@echo "🧪 [Test Frontend] Ejecutando vitest en contenedor efímero..."
	@docker run --rm -v $$(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vitest run

smoke-fleet:
	@echo "🔍 [Smoke Fleet] Ejecutando Smoke Test de Flota Real (Negative Invariants) en Docker..."
	@docker cp scripts/validar-flota-real.py rosgrid_api_local:/app/scripts/validar-flota-real.py && docker exec -e ROSGRID_API_URL=http://localhost:8000 rosgrid_api_local python /app/scripts/validar-flota-real.py

test: test-backend test-frontend smoke-fleet

lint:
	@echo "🔍 [Lint] Ejecutando ruff, mypy y vue-tsc..."
	@docker run --rm --entrypoint ruff -v $$(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test check --no-cache src/
	@docker run --rm --entrypoint mypy -v $$(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test --cache-dir=/tmp/mypy src/
	@docker run --rm -v $$(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vue-tsc --noEmit

certify:
	@./.agents/scripts/certify_task_completion.sh

graphify:
	@./scripts/actualizar-grafos-graphify.sh

build:
	@./scripts/build.sh

clean:
	@./scripts/limpieza.sh
