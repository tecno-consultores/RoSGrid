# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)
# Makefile canónico para desarrollo local, automatización y gobernanza Level-11X

.PHONY: help audit test test-backend test-frontend smoke-fleet lint certify graphify map build build-local release clean

help:
	@echo "Comandos canónicos de desarrollo y gobernanza para RoSGrid:"
	@echo "  make audit         - Ejecuta escaneo preventivo de seguridad (Trivy IaC & Vulnerabilidades en Docker)"
	@echo "  make test          - Ejecuta todas las pruebas unitarias (Backend >=95% y Frontend en Docker)"
	@echo "  make test-backend  - Ejecuta pruebas unitarias de FastAPI con cobertura >=95% en Docker"
	@echo "  make test-frontend - Ejecuta pruebas unitarias Vitest en Docker"
	@echo "  make smoke-fleet   - Ejecuta Smoke Test de Flota Real (Negative Invariants) en Docker"
	@echo "  make lint          - Ejecuta linters y chequeo de tipos (ruff, mypy, vue-tsc, eslint)"
	@echo "  make certify       - Ejecuta el gate de certificación 11X (.agents/scripts/certify_task_completion.sh)"
	@echo "  make graphify      - Extrae y actualiza los grafos AST de Graphify (Backend y Frontend en Docker)"
	@echo "  make map           - Abre los mapas interactivos AST de arquitectura en el navegador"
	@echo "  make build-local   - Construye imágenes locales de prueba (sinfallas/rosgrid-*:local-test)"
	@echo "  make release       - Publica imágenes multi-arquitectura oficiales en Docker Hub (./scripts/build.sh)"
	@echo "  make clean         - Limpia artefactos temporales y contenedores de prueba"

audit:
	@echo "🔒 [Audit] Iniciando escaneo preventivo de vulnerabilidades y seguridad (Shift-Left)..."
	@./scripts/auditar-infra.sh

test-backend:
	@echo "🧪 [Test Backend] Ejecutando pytest (>=95% cobertura) en contenedor efímero..."
	@docker run --rm --entrypoint uv -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_CACHE_DIR=/tmp/uv-cache -e COVERAGE_FILE=/tmp/.coverage -e PYTHONPATH=/app/src -v $$(pwd)/fastapi:/app -v $$(pwd):/workspace:ro -w /app sinfallas/rosgrid-backend:local-test run --with pytest --with pytest-asyncio --with pytest-cov pytest -o addopts="" -o cache_dir=/tmp/pytest-cache --import-mode=importlib --cov=src --cov-fail-under=95 tests/

test-frontend:
	@echo "🧪 [Test Frontend] Ejecutando vitest en contenedor efímero..."
	@docker run --rm -v $$(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vitest run

smoke-fleet:
	@echo "🔍 [Smoke Fleet] Ejecutando Smoke Test de Flota Real (Negative Invariants) en Docker..."
	@docker cp scripts/validar-flota-real.py rosgrid_api_local:/app/scripts/validar-flota-real.py && docker exec -e ROSGRID_API_URL=http://localhost:8000 rosgrid_api_local python /app/scripts/validar-flota-real.py

test: test-backend test-frontend

lint:
	@echo "🔍 [Lint] Ejecutando ruff, mypy, vue-tsc y eslint..."
	@docker run --rm --entrypoint ruff -v $$(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test check --no-cache src/ tests/
	@docker run --rm --entrypoint uv -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_CACHE_DIR=/tmp/uv-cache -v $$(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test run --with mypy mypy --cache-dir=/tmp/mypy src/
	@docker run --rm -v $$(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 sh -c "npx vue-tsc --noEmit && npx eslint src --ext .ts,.vue"

certify:
	@./.agents/scripts/certify_task_completion.sh

graphify:
	@./scripts/actualizar-grafos-graphify.sh

map:
	@./scripts/ver-mapa-arquitectura.sh

build-local:
	@echo "🐳 [Build Local] Construyendo imágenes locales de prueba (local-test)..."
	@docker build -t sinfallas/rosgrid-backend:local-test ./fastapi
	@docker build -t sinfallas/rosgrid-frontend:local-test ./vue3

build: build-local

release:
	@./scripts/build.sh

clean:
	@./scripts/limpieza.sh
