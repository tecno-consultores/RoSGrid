# 27 — ESTÁNDAR QA 11X FRONTEND (VUE 3): ORQUESTADOR DOCKER EFÍMERO, VITEST (\>= 95%) Y PRUEBAS DE MUTACIÓN STRYKER (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la infraestructura inmutable de validación Nivel 11X para el ecosistema Frontend (vue3/), la configuración de vitest.config.ts, el catálogo de pruebas unitarias aisladas (\*.unit.ts / \*.spec.ts) y la auditoría anti-falsos-positivos con **Stryker (stryker.conf.json)**. Queda estrictamente prohibido instalar paquetes en la máquina host o usar docker build.




## **1. Especificación de vue3/docker-compose.qa.yml y vue3/Makefile**

### **1.1 Reglas de Orquestación en vue3/docker-compose.qa.yml**

El archivo vue3/docker-compose.qa.yml mantiene intacta la arquitectura efímera del blueprint 11X con los servicios:


- ui-prod (nginx:alpine sirviendo ./dist:/usr/share/nginx/html:ro en puerto 8080:80).

- qa-vue3 (sinfallas/base-node-ionic:26 o node:26-bookworm-slim con PNPM\_HOME: /pnpm y volumen nombrado pnpm-store:/pnpm).

- ui-e2e (Contenedor oficial de Playwright v1.43.0-jammy con pnpm-store:/pnpm).

- karatelabs (sinfallas/karatelabs:latest apuntando a UI\_BASE\_URL=http://ui-prod:80).

- nginx-exporter y prometheus bajo --profile observability.

- graphify (sinfallas/remote-graphify:latest) bajo --profile graphify.

- Red default con driver: bridge estrictamente IPv4 (prohibido enable\_ipv6: true).

### **1.2 Especificación de vue3/Makefile**

.PHONY: qa-lint qa-unit qa-mutation qa-perf qa-e2e qa-bdd qa-obs qa-all build-ui clean-cache


COMPOSE\_FILE = docker-compose.qa.yml


SERVICE\_NAME = qa-vue3


E2E\_SERVICE = ui-e2e


build-ui:


	@echo "🏗️ Compilando la aplicación RoSGrid (Vue 3 / Vite) para entorno E2E/Producción..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "pnpm install && pnpm run build"


	docker compose -f $(COMPOSE\_FILE) up -d ui-prod


qa-lint:


	@echo "🔍 Ejecutando Auditoría de CVEs, ESLint (SonarJS + Security), Vue-TSC y Prettier..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "pnpm install && pnpm run audit:deps && pnpm run type-check && pnpm run format:check && pnpm lint"


qa-unit:


	@echo "🧪 Ejecutando Pruebas Unitarias Aisladas (Vitest \>= 95% en las 4 métricas)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "pnpm install && pnpm run test:coverage"


qa-mutation:


	@echo "👽 Ejecutando Pruebas de Mutación Frontend (Stryker)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "pnpm install && pnpm run mutate"


qa-perf: build-ui


	@echo "⚡ Ejecutando Auditoría de Rendimiento (Lighthouse CI \>= 90 / \>= 95 a11y)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(E2E\_SERVICE) bash -c "pnpm install && pnpm run test:perf"


qa-e2e: build-ui


	@echo "🎭 Ejecutando Regresión Visual, E2E y Accesibilidad WCAG 2.1 AA (Playwright + Axe)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(E2E\_SERVICE) bash -c "pnpm install && pnpm exec playwright test"


qa-bdd: build-ui


	@echo "📚 Ejecutando Pruebas de Aceptación BDD (Karate UI)..."


	docker compose -f $(COMPOSE\_FILE) run --rm karatelabs mvn clean test


qa-obs: build-ui


	@echo "📊 Levantando Stack de Observabilidad Frontend (Nginx Exporter + Prometheus)..."


	docker compose -f $(COMPOSE\_FILE) --profile observability up -d prometheus nginx-exporter


qa-all: qa-lint qa-unit qa-mutation qa-perf qa-e2e qa-bdd


	@echo "✅ Pipeline QA Frontend (Vue 3 RoSGrid) completado."


clean-cache:


	@echo "🧹 Limpiando volúmenes de caché de pnpm y apagando redes..."


	docker compose -f $(COMPOSE\_FILE) down -v


	docker compose -f $(COMPOSE\_FILE) --profile observability down -v


	docker compose -f $(COMPOSE\_FILE) --profile graphify down -v




## **2. Configuración Estricta de vue3/vitest.config.ts (Umbral 95% en las 4 Métricas)**

// SPDX-License-Identifier: GPL-3.0-only


// Copyright (C) 2026 RoSGrid Contributors


import \{ defineConfig \} from 'vite';


import vue from '@vitejs/plugin-vue';


export default defineConfig(\{


  plugins: \[vue()\],


  test: \{


    globals: true,


    environment: 'jsdom',


    // FRONTERA ESTRICTA (TOOL BOUNDARY): Vitest solo ejecuta pruebas unitarias rápidas.


    include: \['src/\*\*/\*.unit.\{ts,tsx\}', 'src/\*\*/\*.spec.\{ts,tsx\}'\],


    coverage: \{


      provider: 'v8',


      reporter: \['text', 'html'\],


      thresholds: \{


        lines: 95,


        functions: 95,


        branches: 95,


        statements: 95,


      \},


      exclude: \[


        'coverage/\*\*',


        'dist/\*\*',


        'playwright-report/\*\*',


        'lhci-reports/\*\*',


        '.stryker-tmp/\*\*',


        'e2e/\*\*',


        'test/\*\*',


        '\*\*/\*.d.ts',


        '\*.config.ts',


        '\*.config.js',


        'src/main.ts',


      \],


    \},


  \},


\});




## **3. Catálogo Obligatorio de Pruebas Unitarias Frontend (vue3/src/\_\_tests\_\_/)**

Todas las pruebas unitarias deben ejecutarse en milisegundos dentro de jsdom, interceptando fetch y WebSocket mediante vi.fn() / vi.spyOn() sin salir jamás a la red:


1. **httpClient.unit.ts:**

   - Verifica que en POST, PUT, PATCH y DELETE se inyecten automáticamente las cabeceras X-CSRF-Token e Idempotency-Key (UUIDv7).

   - Verifica que ante un fallo de red y reintento explícito se conserve exactamente la misma Idempotency-Key.

   - Verifica el flujo de rotación silenciosa ante HTTP 401 (refreshPromiseSingleton) y la redirección a /login?reason=session\_expired cuando el refresh devuelve 401.

   - Verifica que HTTP 202 Accepted (*Maker-Checker*) dispare la notificación de aprobación pendiente sin lanzar error fatal.

2. **useTelemetryRingBuffer.unit.ts:**

   - Verifica la inserción circular hasta MAX\_POINTS = 5400 (3 horas de datos cada 2 segundos).

   - Verifica que al insertar el punto 5401 se sobrescriba el punto más antiguo sin fugas de memoria.

   - Verifica los recortes de ventana temporal (60, 450, 1800 y 5400 puntos).

   - Verifica que clearBuffer() vacíe el arreglo al 100% cuando el técnico sale de la vista del MikroTik (igual que en WinBox).

3. **useAuthStore.unit.ts y rbacGuards.unit.ts:**

   - Prueba parametrizada (it.each) validando los **11 roles** contra los guards de rutas y el método forceKillSwitchLogout al recibir el evento SESSION\_KILLED por WebSocket.

4. **VaultRevealModal.unit.ts:**

   - Verifica con vi.useFakeTimers() que al revelarse la contraseña con *Step-Up Auth*, el contador inicie en 30 segundos, descuente segundo a segundo y en el segundo 30 (o al desmontar el componente unmount()) borre de memoria current\_password y previous\_password.

5. **RgDataTableDragDrop.unit.ts y RscGitDiffViewer.unit.ts:**

   - Verifica el reordenamiento de reglas de Firewall tanto por evento Drag & Drop como por atajos de teclado accesibles (Alt + ArrowUp / Alt + ArrowDown).

   - Verifica el renderizado de hunks añadidos (+), eliminados (-) y modificados en el comparador estilo Git de .rsc.




## **4. Configuración y Reglas para Aprobar Stryker (vue3/stryker.conf.json)**

\{


  "$schema": "./node\_modules/@stryker-mutator/core/schema/stryker-schema.json",


  "packageManager": "npm",


  "reporters": \["html", "clear-text", "progress"\],


  "testRunner": "vitest",


  "coverageAnalysis": "perTest",


  "mutate": \[


    "src/\*\*/\*.ts",


    "src/\*\*/\*.vue",


    "!src/main.ts",


    "!src/\*\*/\*.unit.ts",


    "!src/\*\*/\*.spec.ts",


    "!src/\*\*/\*.test.ts"


  \]


\}


- **Regla Anti-Mutantes en Componentes Vue y Stores:**

  - En cada test con @vue/test-utils, no te limites a verificar expect(wrapper.exists()).toBe(true). Audita el texto exacto renderizado, los atributos disabled / aria-label, las clases semánticas de estado (status-online, status-offline) y los payloads exactos emitidos con wrapper.emitted().
