.PHONY: qa-lint qa-unit qa-mutation qa-perf qa-e2e qa-bdd qa-obs qa-all build-ui clean-cache

COMPOSE_FILE = docker-compose.qa.yml
SERVICE_NAME = qa-vue3
E2E_SERVICE = ui-e2e

build-ui:
	@echo "🏗️ Compilando la aplicación RoSGrid (Vue 3 / Vite) para entorno E2E/Producción..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "pnpm install && pnpm run build"
	docker compose -f $(COMPOSE_FILE) up -d ui-prod

qa-lint:
	@echo "🔍 Ejecutando Auditoría de CVEs, ESLint (SonarJS + Security), Vue-TSC y Prettier..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "pnpm install && pnpm run audit:deps && pnpm run type-check && pnpm run format:check && pnpm lint"

qa-unit:
	@echo "🧪 Ejecutando Pruebas Unitarias Aisladas (Vitest >= 95% en las 4 métricas)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "pnpm install && pnpm run test:coverage"

qa-mutation:
	@echo "👽 Ejecutando Pruebas de Mutación Frontend (Stryker)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE_NAME) bash -c "pnpm install && pnpm run mutate"

qa-perf: build-ui
	@echo "⚡ Ejecutando Auditoría de Rendimiento (Lighthouse CI >= 90 / >= 95 a11y)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(E2E_SERVICE) bash -c "pnpm install && pnpm run test:perf"

qa-e2e: build-ui
	@echo "🎭 Ejecutando Regresión Visual, E2E y Accesibilidad WCAG 2.1 AA (Playwright + Axe)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(E2E_SERVICE) bash -c "pnpm install && pnpm exec playwright test"

qa-bdd: build-ui
	@echo "📚 Ejecutando Pruebas de Aceptación BDD (Karate UI)..."
	docker compose -f $(COMPOSE_FILE) run --rm karatelabs mvn clean test

qa-obs: build-ui
	@echo "📊 Levantando Stack de Observabilidad Frontend (Nginx Exporter + Prometheus)..."
	docker compose -f $(COMPOSE_FILE) --profile observability up -d prometheus nginx-exporter

qa-all: qa-lint qa-unit qa-mutation qa-perf qa-e2e qa-bdd
	@echo "✅ Pipeline QA Frontend (Vue 3 RoSGrid) completado."

clean-cache:
	@echo "🧹 Limpiando volúmenes de caché de pnpm y apagando redes..."
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_FILE) --profile observability down -v
	docker compose -f $(COMPOSE_FILE) --profile graphify down -v
