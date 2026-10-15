.PHONY: qa-lint qa-unit qa-mutation qa-contracts qa-bdd qa-dast qa-chaos qa-all clean-cache

COMPOSE_FILE = docker-compose.qa.yml
SERVICE_NAME = qa-backend

qa-lint:
	@echo "🔍 Ejecutando Ruff, Mypy Strict, Radon (Complejidad < C, MI >= B), Bandit SAST y Auditoría CVE..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "\
		uv sync --all-extras && \
		uv run ruff check src/ tests/ && \
		uv run ruff format --check src/ tests/ && \
		uv run mypy --strict src/ && \
		test -z \"\$$(uv run radon cc --min C src/)\" && \
		test -z \"\$$(uv run radon mi --min B src/)\" && \
		uv run bandit -c pyproject.toml -r src/ && \
		uv run pip-audit"

qa-unit:
	@echo "🧪 Ejecutando Pruebas Unitarias Aisladas y Cobertura Innegociable >= 95% (Pytest)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "\
		uv sync --all-extras && \
		uv run pytest -m 'not integration' --cov=src --cov-fail-under=95 --cov-report=term-missing --cov-report=html"

qa-mutation:
	@echo "👽 Ejecutando Pruebas de Mutación (Mutmut)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "\
		uv sync --all-extras && \
		uv run mutmut run && \
		uv run mutmut results"

qa-all: qa-lint qa-unit qa-mutation
	@echo "✅ Pipeline QA Backend (FastAPI RoSGrid) completado exitosamente."

clean-cache:
	@echo "🧹 Limpiando volúmenes de caché de uv y contenedores efímeros..."
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_FILE) --profile chaos down -v
	docker compose -f $(COMPOSE_FILE) --profile graphify down -v
