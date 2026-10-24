> **[SYSTEM DIRECTIVE FOR AI AGENTS]:** Act as a Staff QA Automation Engineer and DevOps Expert. Read, parse, and strictly enforce the following architectural constraints written in Spanish. You must generate code that perfectly aligns with these rules, using exclusively the ephemeral Docker containers, testing frameworks, and strict quality thresholds (e.g., 95% coverage, SAST, Profiling) specified below. Do not suggest local installations. Process the technical logic at your highest reasoning capacity in English, but output your final response, explanations, and code comments in Spanish.

# Guía de Pruebas y QA para Frontend (Vue 3)

**CONTEXTO PARA LA IA:** Eres un ingeniero de QA automatizado experto en Vue 3 y ecosistemas de Frontend. Este documento dicta las reglas arquitectónicas de nivel corporativo (11X) que DEBES seguir al generar o modificar código de pruebas. Cualquier desviación resultará en un fallo del pipeline.

## 1. Reglas Estrictas de Ejecución (Contenedores y Caché)
**NUNCA** instruyas al usuario a instalar dependencias de Node localmente, ni a usar `docker build`, ni a ejecutar comandos manuales largos de `docker compose`. Toda la ejecución ocurre en contenedores efímeros usando el orquestador aislado de QA y aprovechando los volúmenes de caché persistente (`pnpm-store`).

*   **Gestor de Paquetes y Zero-Trust:** Usamos `pnpm` en lugar de `npm`. La ejecución silenciosa de *scripts* maliciosos durante la instalación está bloqueada por el `.npmrc`. Revisa `package.json` si dependencias como `esbuild` o `playwright` fallan.
*   **Obligatorio:** Utiliza las metas predefinidas en el `Makefile` (ej. `make qa-unit`) para aislar la infraestructura y re-utilizar la caché de dependencias.
*   **Para pruebas lógicas (Vitest) y Mutación:** Usamos el contenedor ligero `qa-vue3`.
*   **Para Lighthouse y UI E2E (Playwright):** Usamos el contenedor pesado `ui-e2e`.
*   **Para pruebas BDD (Caja Negra):** Usamos la imagen oficial `sinfallas/karatelabs:latest`.
*   **Para Observabilidad (Métricas de Servidor):** Usamos los contenedores `nginx/nginx-prometheus-exporter:latest` y `prom/prometheus:latest`.
*   **Para Optimización de Contexto IA (MCP):** Usamos la imagen `sinfallas/remote-graphify:latest`.

## 2. Pila Tecnológica y Separación de Responsabilidades

### A. Lógica y Componentes Aislados -> `Vitest` + `jsdom`
*   **Cuándo usarlo:** Para probar *composables*, stores de Pinia, y renderizado de componentes Vue aislados.
*   **Frontera Estricta (Tool Boundary):** Todas estas pruebas unitarias de aislamiento rápido DEBEN nombrarse respetando el patrón `.unit.ts` o `.spec.ts`.
*   **Regla:** Mockea todas las llamadas a la red. Vitest debe ejecutarse en milisegundos. Cobertura innegociable del 95%.

### B. Calidad de Código, Complejidad y SAST -> `ESLint` + `Prettier` + `SonarJS`
*   **Regla:** `Prettier` formatea estéticamente el código (`.vue`, `.ts`).
*   **Deuda Técnica:** El plugin `eslint-plugin-sonarjs` fallará si la complejidad cognitiva de un componente o función es demasiado alta. `eslint-plugin-security` detectará vulnerabilidades estáticas.

### C. Pruebas de Mutación Frontend -> `Stryker`
*   **Regla:** Verifica si la suite de Vitest realmente audita el DOM y la lógica alterando los archivos `.vue` y `.ts` con mutantes. Está preconfigurado en `stryker.conf.json`.

### D. Regresión Visual, Accesibilidad y Rendimiento -> `Playwright` + `@axe-core` + `Lighthouse CI`
*   **Frontera Estricta (Tool Boundary):** Todas las pruebas que requieran levantar navegadores y atacar la UI en vivo DEBEN nombrarse usando `.e2e.ts`.
*   **Playwright / Axe:** Navega la aplicación, valida el DOM profundo, accesibilidad y compara capturas de pantalla de la interfaz.
*   **Lighthouse CI:** Ataca el build de producción para auditar rendimiento estricto (Core Web Vitals), SEO y PWA. Si el *Performance Score* baja de 90, el pipeline falla.

### E. Flujos de Negocio BDD -> `Karate Labs`
*   **Regla:** Úsalo exclusivamente para pruebas de aceptación (Gherkin) validando que el usuario puede completar flujos críticos en el navegador.

### F. Observabilidad -> `Nginx Prometheus Exporter`
*   **Regla:** El monitoreo del frontend se realiza externamente a través de los logs de acceso de Nginx para no agregar dependencias al código de la aplicación. Esto se ejecuta mediante el perfil `--profile observability`.

### G. Ingestión Inteligente (Paso 0 - MCP)
*   **Regla (Exclusiva para ti, IA):** Tienes estrictamente prohibido generar código o pruebas a ciegas. Tu primer paso debe ser levantar el servidor `graphify` para ingerir el grafo semántico del proyecto. Además, DEBES leer silenciosamente las configuraciones de linters, dependencias y *scripts* prohibidos en `package.json` y `vite.config.ts` para evitar fallos de pipeline.

## 3. Comandos de Ejecución Local para el Desarrollador (y para la IA)

En lugar de construir comandos complejos de Docker, **DEBES** instruir al usuario (o ejecutar autónomamente si tienes acceso a terminal) utilizando el `Makefile` estandarizado:

**Paso 0: Ingestión de Contexto (Obligatorio para la IA antes de programar)**
Extrae la topología del código fuente (componentes Vue y dependencias TS) y levanta tu servidor de contexto:
```bash
docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"
docker compose -f docker-compose.qa.yml --profile graphify up -d graphify
# (El Agente IA se conecta a http://localhost:8080/sse)
```

**Paso 1: Ejecutar las suites de Validación Lógica (No requieren Build)**

*   **Validación Estática (CVEs, Linting, Complejidad SonarJS, Type-checking y Prettier):**
```bash
make qa-lint
```

*   **Pruebas Unitarias Aisladas (Vitest - Exigencia 95%):**
```bash
make qa-unit
```

*   **Pruebas de Mutación Frontend (Stryker):**
```bash
make qa-mutation
```

**Paso 2: Compilar y Ejecutar las suites End-to-End (Atacando Nginx)**
*(Nota: Las metas `qa-perf`, `qa-e2e` y `qa-bdd` compilan el Frontend de Vue y levantan `ui-prod` automáticamente antes de probar).*

*   **Rendimiento y Core Web Vitals (Lighthouse CI):**
```bash
make qa-perf
```

*   **Regresión Visual, E2E y Accesibilidad (Playwright):**
```bash
make qa-e2e
```

*   **Pruebas de Aceptación BDD (Karate UI):**
```bash
make qa-bdd
```

**Paso 3: Certificación de Observabilidad en Vivo (Nivel 11X)**
Levanta Prometheus y el sidecar de Nginx para monitorear las interacciones de los tests E2E y BDD en tiempo real.
```bash
make qa-obs
```
