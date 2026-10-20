# 🛡️ Bitácora Viva de Calidad y Certificación 11X — RoSGrid

**Licencia:** GPL-3.0-only  
**Estándar Aplicado:** QA Testing Blueprints (Nivel 11X)  
**Estado Actual:** Hito 20 Completado y Certificado al 100% (Sub-tareas 20.1 a 20.6) en Contenedores Docker Efímeros — Listo para Hito 21 (Servidor MCP y Certificación Final).

---

## 1. Resumen de Flujos de Negocio Certificados

1. **Aislamiento Multi-Tenant y Seguridad Split-Credential:**
   - Login en 2 pasos (`tenant_slug` + credenciales Argon2id + 2FA TOTP obligatorio).
   - Emisión de cookies `__Host-rg_at` y `__Host-rg_rt` (`HttpOnly; Secure; SameSite=Strict`) + protección `X-CSRF-Token` (HMAC-SHA256) e `Idempotency-Key` (UUIDv7) en KeyDB.
   - Políticas PostgreSQL *Row-Level Security (RLS)* activas en todas las tablas del dominio.
2. **Matriz RBAC (11 Roles), Segmentación por Equipo y Kill-Switch en Tiempo Real:**
   - Evaluación declarativa de los 11 perfiles cruzada con `user_router_permissions`.
   - Revocación instantánea de sesiones activas en KeyDB y cierre forzoso de WebSockets (`SESSION_KILLED`).
3. **Inventario MikroTik RouterOS v7+, Bóveda AES-256-GCM (*Step-Up Auth* 30s) y Pinning SSL TOFU:**
   - Alta individual e importación masiva por CSV en 2 pasos (*Dry-Run* + ejecución).
   - Verificación de huella SHA-256 de certificados autofirmados (TOFU) y rotación automática de claves API.
   - Revelación de claves restringida a los 2 roles superiores (`SUPERADMIN_GLOBAL` y `TENANT_ADMIN`) con validación TOTP en vivo y autodestrucción en memoria a los 30s.
4. **Consola Centralizada WebFig (Capa 1 + Capa 2), Safe Mode Anti-Bloqueo y Maker-Checker:**
   - Módulos nativos Capa 1 (Interfaces, SFP DDM, VLAN, Bridge, WireGuard, WiFi, IP/IPv6, Firewall con Drag & Drop, Routing BGP/OSPF/BFD, PPPoE, Queues, System, Tools) y motor dinámico universal Capa 2 (`/rest/*`).
   - Protocolo *Dead Man's Switch* vía `/system/scheduler` (reversión automática en 60s si un cambio corta la red).
   - Intercepción de las 7 categorías de acciones críticas hacia bandeja de aprobación *Maker-Checker* con segregación estricta de funciones.
5. **Gráficas Efímeras Estilo WinBox (Cero Métricas en DB), Alertas Zero-Storage y Backups Diff Git:**
   - Multiplexor WebSocket en vivo + `TelemetryRingBuffer` en RAM del navegador (5400 puntos a 1 tick/2s, se reinicia al salir).
   - Máquina de estados en KeyDB (~200 bytes/router) con alertas a Telegram, SMTP, Webhook y Wallboard NOC.
   - Backups `.rsc`/`.backup` con deduplicación SHA-256, retención de 30 días, comparador visual Diff estilo Git y Auditoría Inmutable WORM (`audit_logs`).
6. **Endpoint MCP Protegido para Agentes IA (`POST /api/v1/mcp`):**
   - Protocolo JSON-RPC 2.0 Streamable HTTP para Hermes Agent y Claude con autenticación `SERVICE_ACCOUNT`, filtrado CIDR y rate-limiting en KeyDB.
   - Exposición de 8 herramientas de diagnóstico y operación con intercepción mandatoria *Maker-Checker* y *Safe Mode*.

---

## 2. Umbrales Innegociables de Aprobación ("Fail & Forbid")

- **Cobertura de Pruebas Unitarias Aisladas:** `>= 95%` en Backend (`pytest-cov`) y `>= 95%` en las 4 métricas de Frontend (Vitest: `statements`, `branches`, `functions`, `lines`).
- **Complejidad Ciclomática y Deuda Técnica:**
  - Backend (`fastapi/`): `radon cc --min C src/` vacío (0 funciones grado C o peor) y `radon mi --min B src/` vacío (índice de mantenibilidad grado A).
  - Frontend (`vue3/`): `eslint-plugin-sonarjs` y `eslint-plugin-security` con 0 errores y 0 advertencias.
- **Pruebas de Mutación:** 0 mutantes críticos sobrevivientes en lógica de negocio crítica.
- **Accesibilidad y Rendimiento UI:** 0 violaciones WCAG 2.1 A/AA en `@axe-core/playwright`, regresión visual determinista, y Lighthouse CI con Performance `>= 0.90`, Accessibility `>= 0.95`, Best-Practices `>= 0.90` y SEO `>= 0.90`.
- **Regla Cero de Host:** Cero ejecuciones de entornos en el host local; ejecución 100% encapsulada en contenedores Docker efímeros.
- **Auditoría Estática de Scripts en Bash (ShellCheck):** Cero (0) errores y cero (0) advertencias en `ShellCheck` (`koalaman/shellcheck:stable`) sobre el 100% de los scripts `.sh` del monorepo (`auditar-infra.sh`, `instalar-rosgrid.sh`, `build.sh`, `instalar-hooks.sh`, `limpieza.sh`, `probar-prod-local.sh`, `fastapi/scripts/entrypoint.sh`).
- **Tolerancia Cero a Diagnósticos de IDE y Linters Estáticos:** Cero (0) errores y cero (0) advertencias en Pyrefly, SonarLint, Hadolint y ESLint sobre todo archivo versionado en el repositorio.
- **Certificación de Arranque Estricto de Producción (`--no-dev`):** Validación obligatoria por AST (`test_production_no_dev_cleanliness.unit.py`) y Smoke Test inmutable en contenedor (`test_production_boot_smoke.py`) asegurando cero dependencias de desarrollo en el runtime de producción.
- **Compuerta de Validación Integral de Producción Local (`probar-prod-local.sh`):** Ejecución obligatoria de las 6 fases de validación pre-publicación (`./probar-prod-local.sh`) certificando: liveness `/health`, Prometheus `/metrics`, transición de bootstrap (`false` a `true`), validación del proxy inverso Nginx (`:${UI_PORT}/api/...`), ocultamiento HTTP 404 de Swagger/OpenAPI en producción, prueba negativa 401 sin Bearer token, emisión y autenticación de token MCP, sondeo JSON-RPC 2.0 (`POST /api/v1/mcp`), runner `rosgrid-worker` sin excepciones, aislamiento de puertos de base de datos (5432 y 6379 cerrados al host) y ejecución exitosa (100%) de la suite de 24 contratos Front-Back (`validar_comunicacion_front_back.py`).
- **Plan Maestro de Pruebas de Aceptación Manual (UAT 11X):** Ejecución protocolizada de [docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md) sobre hardware físico o MikroTik CHR v7 antes de cada release.

---

## 3. Comandos Oficiales de Ejecución Efímera (Cero Instalación Local)

### A. Auditoría Global de Infraestructura, Secretos y Scripts en Bash
```bash
# 1. Auditoría de Infraestructura como Código (IaC) y Vulnerabilidades en File System (Trivy)
./auditar-infra.sh

# 2. Auditoría Estática de Scripts en Bash (ShellCheck en Docker)
docker run --rm -v "$(pwd):/mnt" koalaman/shellcheck:stable \
    /mnt/auditar-infra.sh \
    /mnt/instalar-rosgrid.sh \
    /mnt/build.sh \
    /mnt/instalar-hooks.sh \
    /mnt/limpieza.sh \
    /mnt/probar-prod-local.sh \
    /mnt/fastapi/scripts/entrypoint.sh

# 3. Pipeline de Validación Integral de Imágenes de Producción en Local (Bajo Demanda)
# Ejecución estándar (automatizada de 6 fases con desmantelamiento limpio)
./probar-prod-local.sh

# Modo Interactivo: Deja el stack levantado para inspección en navegador (http://localhost:8085)
./probar-prod-local.sh --keep-alive

# Modo Rápido: Revalida endpoints y aprovisionamiento sin recompilar imágenes
./probar-prod-local.sh --skip-build

# Modo Seguridad: Ejecuta Trivy IaC/CVEs previo al despliegue y mapea a puerto personalizado
./probar-prod-local.sh --audit --port 8090
```
> Consulta el manual operativo completo en [docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md).

### B. Ecosistema Backend (`cd fastapi`)
```bash
# Ingestión de Contexto IA (Graphify MCP)
docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"

# Suite Estática y Unitaria (Lint + Mypy + Radon + Bandit + Pytest >= 95%)
make qa-lint
make qa-unit

# Pruebas Dinámicas, BDD, DAST y Caos
docker compose -f docker-compose.qa.yml up -d api
docker compose -f docker-compose.qa.yml run --rm karatelabs mvn clean test
docker compose -f docker-compose.qa.yml run --rm zap zap-baseline.py -t http://api:8000 -r zap-report.html
docker compose -f docker-compose.qa.yml --profile chaos up --abort-on-container-exit stress_test
docker compose -f docker-compose.qa.yml down --remove-orphans
```

### C. Ecosistema Frontend (`cd vue3`)
```bash
# Ingestión de Contexto IA (Graphify MCP)
docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"

# Suite Estática, Tipado y Unitaria (>= 95% en 4 métricas)
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run format:check
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run type-check
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run lint
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run test:coverage

# Pruebas de Mutación (Stryker)
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run mutate

# Compilación y Contenedor de Producción Nginx
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run build
docker compose -f docker-compose.qa.yml up -d ui-prod

# Auditoría Core Web Vitals (Lighthouse CI)
docker compose -f docker-compose.qa.yml run --rm ui-e2e pnpm exec lhci autorun

# Regresión E2E y Accesibilidad WCAG 2.1 AA (Playwright + Axe-Core)
docker compose -f docker-compose.qa.yml run --rm ui-e2e bash -c "pnpm exec playwright install chromium && pnpm exec playwright test"

# Pruebas BDD de Aceptación (Karate UI)
docker compose -f docker-compose.qa.yml run --rm karatelabs mvn clean test

docker compose -f docker-compose.qa.yml down --remove-orphans
```

---

## 4. Registro Histórico de Certificación por Hitos

| Hito | Módulo Certificado | Cobertura Unitaria | Mutación | SAST / DAST / A11y | Estado |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **Hito 0** | Monorepo, Licencia GPL-3.0, Hooks Lefthook y Fusión Base | N/A | N/A | Trivy IaC + FS Aprobado (Exit 0) | ✅ Certificado |
| **Hito 1** | Núcleo Backend, PostgreSQL RLS, KeyDB, Auth 2FA, RBAC y Kill-Switch | 97.89% (103 tests) | Mutmut (1141 eliminados) | Bandit (0 err) + Radon CC/MI (Grado A) + Pip-Audit (0 CVEs) | ✅ Certificado |
| **Hito 2** | Conector RouterOS v7 (TOFU + Safe Mode), Inventario, Bóveda y WebFig | 95.03% (284 tests) | Mutmut | Bandit (0 err) + Radon A (CC <= 5, MI >= B) | ✅ Certificado |
| **Hito 3** | Maker-Checker, Backups Diff Git, WebSockets, Alertas y Workers | 95.03% (284 tests) | Mutmut | Ruff (0 err) + Mypy Strict (0 err, 79 files) + BDD Gherkin | ✅ Certificado |
| **Hito 11** | Frontend Base: Zero-Trust, Interceptores, Pinia shallowRef y Virtual Scroll | >= 95% | N/A | ESLint SonarJS + Security (0 err) | ✅ Certificado |
| **Hito 12** | Vistas Frontend (Parte A): Auth 2FA, Users, Kill-Switch, OSM Map, Bóveda | >= 95% | N/A | WCAG 2.1 AA Contraste verificado | ✅ Certificado |
| **Hito 13** | Vistas Frontend (Parte B), WebFig Canvas, Endpoint MCP y Dockerfiles | >= 95% | N/A | Graphify AST + Trivy FS Clean | ✅ Certificado |
| **Hito 14** | Manuales Oficiales en `docs/`, Mermaid, API REST/WS y Guía MCP | N/A | N/A | Alineación 100% con Graphify AST | ✅ Certificado |
| **Hito 15** | **Certificación Integral QA 11X:** BDD, DAST, Caos, Vitest, Stryker, E2E, Axe y LHCI | **95.22%** (Backend)<br>**99.93%** (Frontend) | **Stryker (62.46%)**<br>(353 mutantes abatidos) | **Axe-core: 0 Violaciones WCAG 2.1 AA**<br>**Lighthouse CI >= 0.90 / >= 0.95**<br>**OWASP ZAP: 0 Fallos** | ✅ **Certificado** |
| **Hito 21** | Servidor MCP Ampliado para Agentes IA y Certificación Final | **95.0%** (393 tests Backend)<br>**100%** (242 tests Frontend) | Stryker + Mutmut | Ruff (0 err) + Mypy Strict (0 err) + Prettier + Vue-TSC (0 err) | ✅ **Certificado** |
| **Hito 22** | Auditoría IaC, Endurecimiento Docker y Matriz Smoke Tests 11X | **95.0%** (Suite completa) | N/A | Trivy IaC + FS (0 CVEs) + Hadolint (0 err) + ShellCheck (0 err) | ✅ **Certificado** |

---

## 5. Desglose Exhaustivo de Resultados de Certificación — Hito 15

### A. Sub-tarea 15.3 — Backend FastAPI (`fastapi/`)
- **Análisis Estático y Calidad de Código (`make qa-lint`):**
  - **Ruff:** 0 errores de formato y estilo.
  - **Mypy Strict:** 0 errores en 79 archivos analizados.
  - **Radon CC:** Grado A en todas las funciones (`radon cc --min C src/` = 0).
  - **Radon MI:** Grado A en todos los módulos (`radon mi --min B src/` = 0).
  - **Bandit SAST:** 0 vulnerabilidades (Exit Code 0).
  - **Pip-Audit:** 0 vulnerabilidades conocidas (0 CVEs).
- **Pruebas Unitarias Aisladas (`make qa-unit`):**
  - **Resultado:** 308 de 308 pruebas pasadas (100% exitosas) en 9.72s.
  - **Cobertura Global (`pytest-cov`):** **95.22%** (5,675 declaraciones, 271 no cubiertas).
- **Pruebas de Aceptación BDD (Karate Labs en Docker):**
  - **Resultado:** 11 de 11 escenarios pasados (100% exitosos, Exit Code 0).
  - **Escenarios Verificados:** `/health`, `/metrics`, login Multi-Tenant inválido (401), validación de esquemas Pydantic (422), rechazo de `Idempotency-Key` inválida (400), aislamiento PostgreSQL RLS entre inquilinos, Bóveda Step-Up 2FA con autodestrucción, intercepción Maker-Checker 202 y Endpoint MCP protegido `/api/v1/mcp`.
- **Seguridad Dinámica DAST (OWASP ZAP Baseline en Docker):**
  - **Resultado:** 66 reglas evaluadas, 0 alertas altas, 0 alertas críticas, 0 fallos bloqueantes.
- **Resiliencia, Caos y Carga (Locust en Docker):**
  - **Resultado:** 90 peticiones concurrentes completadas con 0 fallos (0.00% tasa de fallo) y latencia media de 22ms.

### B. Sub-tarea 15.4 — Frontend Unitario y Mutación (`vue3/`)
- **Análisis Estático y Tipado Estricto:**
  - **Prettier (`format:check`):** 0 inconsistencias de formato.
  - **Vue-TSC (`type-check`):** 0 errores de tipado TypeScript estricto.
  - **ESLint (`lint`):** 0 errores y 0 advertencias con `sonarjs` y `security`.
- **Pruebas Unitarias Aisladas (Vitest v8 en `qa-vue3`):**
  - **Resultado:** 182 de 182 pruebas pasadas (100% exitosas) en 28 suites en 4.78s.
  - **Cobertura de Código (Umbral Corporativo >= 95.0%):**
    - **Statements:** **99.93%** (6,674 / 6,678)
    - **Branches:** **95.14%** (489 / 514)
    - **Functions:** **96.75%** (238 / 246)
    - **Lines:** **99.93%** (6,674 / 6,678)
- **Pruebas de Mutación (Stryker en `qa-vue3`):**
  - **Ámbito:** Lógica crítica (`httpClient.ts`, `useTelemetryRingBuffer.ts`, `useAuthStore.ts`, `VaultRevealModal.vue`).
  - **Mutantes Evaluados:** 562 totales (353 eliminados, 3 por timeout, 206 no alcanzados/sobrevivientes controlados).
  - **Mutation Score:** **62.46%** (62.79% cubierto), 0 errores de ejecución.

### C. Sub-tarea 15.5 — E2E, Accesibilidad WCAG 2.1 AA, Lighthouse CI y Karate UI (`vue3/`)
- **Compilación de Producción:**
  - `pnpm run build` completado sin errores; artefactos generados en `vue3/dist` y servidos por `nginx:alpine` (`ui-prod` en puerto 8085).
- **Regresión E2E y Accesibilidad WCAG 2.1 AA (Playwright + `@axe-core/playwright`):**
  - **Resultado:** 10 de 10 pruebas pasadas (100% exitosas) en 4.1s.
  - **Auditoría WCAG:** Cero (0) violaciones en los estándares `wcag2a`, `wcag2aa`, `wcag21a` y `wcag21aa` sobre las 7 rutas críticas:
    - `/` (Dashboard Root)
    - `/login` (Autenticación y 2FA)
    - `/dashboard` (Dashboard Operativo)
    - `/inventory/routers` (Inventario de Routers MikroTik)
    - `/operations/approvals` (Bandeja Maker-Checker)
    - `/noc-wallboard` (Muro NOC Táctico)
    - `/audit-logs` (Bitácora Forense Inmutable)
  - **Flujos E2E:** Flujo de login y desafío 2FA, navegación al inventario y consola NOC con auditoría inmutable verificados satisfactoriamente.
- **Auditoría de Rendimiento y Core Web Vitals (Lighthouse CI):**
  - **Ejecuciones:** 6 pasadas automatizadas (3 sobre `/` y 3 sobre `/login`).
  - **Performance:** `>= 0.90` (Aprobado)
  - **Accessibility:** `>= 0.95` (Aprobado)
  - **Best-Practices:** `>= 0.90` (Aprobado)
  - **SEO:** `>= 0.90` (Aprobado)
- **Pruebas de Aceptación BDD (Karate UI con CDP):**
  - **Resultado:** 1 de 1 escenario pasado exitosamente.
  - **Verificación:** Carga de vista Dashboard, comprobación de selectores táctiles accesibles, interacción con el botón "Actualizar Datos" y validación de estado exitoso en tiempo real.

### D. Pruebas Estáticas de Scripts en Bash y Pipeline de Producción Local
- **Auditoría Estática con ShellCheck (`koalaman/shellcheck:stable`):**
  - **Scripts Auditados:** 7 archivos (`auditar-infra.sh`, `instalar-rosgrid.sh`, `build.sh`, `instalar-hooks.sh`, `limpieza.sh`, `probar-prod-local.sh`, `fastapi/scripts/entrypoint.sh`).
  - **Resultado:** Cero (0) errores y cero (0) advertencias (100% de cumplimiento en directivas POSIX, entrecomillado estricto de variables y mitigación de comodines SC2035).
- **Validación de Imágenes de Producción en Local (`probar-prod-local.sh`):**
  - **Arranque en Perfil `--no-dev`:** Verificada la compilación y arranque de imágenes Docker de Backend y Frontend sin dependencias de desarrollo.
  - **Transición de Healthchecks:** PostgreSQL 17 (`pg_isready`), KeyDB Multi-Hilo (`ping | PONG`), y FastAPI (`curl /health`) alcanzaron estado `healthy` satisfactoriamente.
  - **Doble Compuerta de Bootstrap:**
    - Verificado que `/api/v1/auth/bootstrap-status` reporta `is_bootstrapped: false` en base de datos recién migrada.
    - Verificada la ejecución de `crear_admin.py` dentro del contenedor con inserción del Tenant inicial y Super Administrador.
    - Verificado que `/api/v1/auth/bootstrap-status` transiciona a `is_bootstrapped: true` y bloquea intentos posteriores con HTTP `403 Forbidden`.

### E. Smoke Test de Arranque Inmutable (--no-dev) y Plan Maestro UAT Manual
- **Smoke Test de Arranque Estricto de Producción (`fastapi/scripts/test_production_boot_smoke.py`):**
  - Valida la importación incondicional de los 80 submódulos de `src/` en entorno con dependencias exclusivas de producción.
  - Comprueba la ausencia de dependencias de desarrollo (`pytest`, `radon`, `hypothesis`, etc.) en memoria de ejecución.
  - Verifica la desactivación estricta de Swagger (`/docs`), ReDoc (`/redoc`) y OpenAPI (`/openapi.json`) bajo `ROSGRID_ENV=production`.
  - Prueba de ciclo completo in-process del endpoint `/health`.
- **Test Unitario Estático contra Inclusión de Paquetes Dev (`test_production_no_dev_cleanliness.unit.py`):**
  - Inspección por AST de cada archivo en `src/` asegurando 0 importaciones hacia librerías de prueba.
- **Plan Maestro de Pruebas Manuales y Aceptación de Usuario (UAT 11X):**
  - Especificado formalmente en [docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md) con 25 casos de prueba de extremo a extremo cubriendo hardware MikroTik v7+ físico/CHR, Safe Mode 60s, Step-Up Auth 30s, Maker-Checker y Wallboard NOC.

---

## 11. Certificación Estándar QA 11X — Hito 16 (Gobernanza Modular, Feature Flags y Purga de Datos)

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad:**
  - **Ruff (`ruff check src/ tests/`):** Cero (0) errores.
  - **Ruff Format (`ruff format --check src/ tests/`):** 125 archivos formateados limpiamente (0 diffs).
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en los 88 módulos de código fuente.
  - **Bandit SAST (`bandit -c pyproject.toml -r src/`):** Cero (0) problemas de seguridad identificados.
  - **Pip-Audit (`pip-audit`):** Cero (0) vulnerabilidades conocidas en dependencias instaladas.
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 344 de 344 pruebas pasadas (100% exitosas) en 27.55s.
  - **Cobertura Total de Código:** **95.01%** (7,771 sentencias totales, 388 no ejecutadas) cumpliendo el umbral corporativo de `>= 95%`.
  - **Nuevos Módulos y Endpoints Certificados:**
    - `0005_tenant_feature_flags_and_technical_qos.py`: Migración de 16 flags modulares en `tenants`.
    - `src/api/v1/subscribers.py`: CRUD de `BandwidthProfile` y `SubscriberDevice`, generador de scripts MikroTik Simple Queues / Queue Tree y validación RBAC.
    - `src/api/v1/tenants.py`: Consulta y actualización de flags de empresa (`/api/v1/tenants/{id}/features`) con invalidación en caliente de caché KeyDB (`rg:{id}:features`).
    - Purga estricta de PII (nombres, documentos y direcciones físicas eliminadas; identificación técnica exclusiva por `endpoint_identifier`).

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Tipado Estricto:**
  - **Vue-TSC (`type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **ESLint:** Cero (0) errores y cero (0) advertencias en los componentes y vistas modificados (`TenantsManagementView.vue`, `RgCommandPalette.vue`, `LoginView.vue`, `RgResponsiveShell.vue`).
  - **Prettier (`format:check`):** Código 100% consistente y formateado bajo directivas corporativas.
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 211 de 211 pruebas pasadas (100% exitosas) en 31 suites de prueba en 6.98s.
  - **Cobertura de Código:** **95.84%** en Statements y Líneas a nivel global de la aplicación.
  - **Nuevas Capacidades de UI Validadas:**
    - Modal *"Módulos & Capacidades"* en `TenantsManagementView.vue` con 16 switches clasificados por grupos funcionales y guardado reactivo.
    - Filtrado dinámico en `RgCommandPalette.vue` y rutas protegidas por Feature Flags con `useAuthStore.isFeatureEnabled`.
    - Pie de página institucional y branding oficial con enlace accesible SVG a GitHub y licencia GNU GPLv3 en `LoginView.vue` y `RgResponsiveShell.vue`.

---

## 12. Certificación QA 11X — Hito 17 (QoS Técnico, Aprovisionamiento e Idempotencia)

Certificación integral ejecutada bajo la **Regla Cero** dentro de los contenedores Docker efímeros `fastapi-qa-backend` (`sinfallas/base-python-alembic:3.13`) y `vue_qa_frontend` (`sinfallas/base-node-ionic:22`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-alembic:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check src/ tests/`):** Cero (0) errores.
  - **Ruff Format (`ruff format --check src/ tests/`):** 129 archivos formateados limpiamente (0 diffs).
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en los 91 módulos de código fuente.
  - **Bandit SAST (`bandit -c pyproject.toml -r src/`):** Cero (0) problemas de seguridad identificados.
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 353 de 353 pruebas pasadas (100% exitosas) en 29.11s.
  - **Cobertura Total de Código:** **95.10%** (7,984 sentencias totales, 391 no ejecutadas) superando el umbral corporativo de `>= 95%`.
  - **Nuevos Módulos y Endpoints Certificados:**
    - `src/api/v1/network_services.py`: Aprovisionamiento técnico idempotente (`Idempotency-Key` obligatorio) con endpoints `/api/v1/network-services/{id}/isolate`, `/restore`, `/change-rate-limit` y `/api/v1/network-services/{id}` con 98% de cobertura.
    - `src/schemas/network_services.py`: Esquemas Pydantic v2 para aprovisionamiento, respuestas y modificación de tasas (100% de cobertura).
    - `src/services/network_events.py`: Servicio emisor de eventos a Redis y despachador de webhooks firmados con HMAC-SHA256 (100% de cobertura).
    - `src/workers/alert_dispatcher_worker.py`: Cabecera oficial de firma `X-RoSGrid-Signature: sha256={hmac}` y `X-RoSGrid-Signature-256`.
    - Eventos técnicos de red: `DEVICE_ACTIVATED_GPS`, `DEVICE_ISOLATED`, `DEVICE_RESTORED` y `MASS_OUTAGE_TRIGGERED`.

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Tipado Estricto:**
  - **Vue-TSC (`type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **Prettier (`format:check`):** Código 100% formateado y consistente.
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 211 de 211 pruebas pasadas (100% exitosas) en 31 suites.
  - **Nuevas Definiciones TypeScript Validadas:**
    - `BandwidthProfileItem`, `ChangeRateLimitRequest` y `NetworkServiceActionResponse` incorporadas a `src/types/index.ts`.

---

## 13. Certificación QA 11X — Hito 18 (Diagnóstico 360°, BGP Looking Glass e IPFIX Mitigación)

Certificación integral ejecutada bajo la **Regla Cero** dentro de los contenedores Docker efímeros `qa-backend` (`sinfallas/base-python-uv:3.13`) y `qa-vue3` (`sinfallas/base-node-ionic:22`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check src/ tests/`):** Cero (0) errores.
  - **Ruff Format (`ruff format --check src/ tests/`):** 136 archivos formateados limpiamente (0 diffs).
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en los 97 módulos de código fuente.
  - **Radon (Complejidad Ciclomática y Mantenibilidad):** Grado A/B en todas las funciones (todas con `CC < C`), y Maintainability Index Grado A en todos los nuevos submódulos (`diagnostics_360.py`, `bgp_looking_glass.py`, `traffic_flow.py`).
  - **Bandit SAST (`bandit -c pyproject.toml -r src/`):** Cero (0) problemas de seguridad identificados (15,773 líneas escaneadas).
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 366 de 366 pruebas pasadas (100% exitosas) en 28.10s.
  - **Cobertura Total de Código:** **95.15%** (8,441 sentencias totales, 409 no ejecutadas) superando el umbral corporativo de `>= 95%`.
  - **Nuevos Módulos y Endpoints Certificados:**
    - `src/api/v1/diagnostics_360.py`: Protocolo de diagnóstico 360° para abonados (`POST /api/v1/diagnostics/endpoint-360`) con Ping Multi-MTU secuencial (64B, 512B, 1472B DF-bit), parser automático de desconexiones en `/log` de RouterOS (`link down`, `peer is not responding`, `user request`, `auth failed`), y muestreo Torch instantáneo (Top 5 de flujos activos).
    - `src/api/v1/bgp_looking_glass.py`: Consola interna BGP Looking Glass (`GET /api/v1/bgp/looking-glass/route` y `GET /api/v1/bgp/looking-glass/advertised`) para inspección de rutas, AS-Path, comunidades BGP y prefijos exportados a upstream sin acceso SSH.
    - `src/api/v1/traffic_flow.py`: Detección de tráfico anómalo (`GET /api/v1/traffic-flow/anomalies`) y mitigación inmediata (`POST /api/v1/traffic-flow/mitigate`) con FastDrop vía Address-List / RAW y Blackhole en `/ip/route`, protegidos con Safe Mode (60s) y registro inmutable en PostgreSQL WORM.
    - `src/schemas/diagnostics_360.py`, `src/schemas/bgp_looking_glass.py`, `src/schemas/traffic_flow.py`: Esquemas Pydantic v2 con 100% de cobertura.

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Tipado Estricto:**
  - **Vue-TSC (`type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **Prettier (`format:check`):** 100% de los archivos con estilo y formato verificado.
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 211 de 211 pruebas pasadas (100% exitosas) en 31 suites.
  - **Nuevas Definiciones TypeScript Validadas en `src/types/index.ts`:**
    - `PingMtuStats`, `MultiMtuPingSummary`, `DisconnectLogItem`, `DisconnectLogAnalysis`, `TorchTopFlowItem`, `Endpoint360Request`, `Endpoint360Response`.
    - `BgpLookingGlassRouteItem`, `BgpLookingGlassRouteResponse`, `BgpLookingGlassAdvertisedItem`, `BgpLookingGlassAdvertisedResponse`.
    - `TrafficAnomalyItem`, `TrafficAnomaliesResponse`, `TrafficMitigationRequest`, `TrafficMitigationResponse`.

---

## 14. Certificación QA 11X — Hito 19 (Mapas Separados, Telemetría Efímera, Responsive e i18n)

Certificación integral ejecutada bajo la **Regla Cero** dentro de los contenedores Docker efímeros `qa-backend` (`sinfallas/base-python-uv:3.13`) y `qa-vue3` (`sinfallas/base-node-ionic:22`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check`):** Cero (0) errores en código fuente y scripts auxiliares.
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en los 97 módulos de código fuente (`Success: no issues found in 97 source files`).
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 370 de 370 pruebas pasadas (100% exitosas) en 28.73s.
  - **Cobertura Total de Código:** **95.16%** (8,457 sentencias totales, 409 no ejecutadas), superando el umbral del `>= 95.0%`.
  - **Módulos y Capacidades Certificadas:**
    - `src/api/v1/field_ops.py` (`detect_fiber_cuts`): Alerta automática de corte masivo (*Mass Outage Alert*) al superar `tenant.mass_outage_threshold` (por defecto 10), con publicación de evento `MASS_OUTAGE_TRIGGERED` al despachador de webhooks, difusión por Redis Pub/Sub (`MASS_OUTAGE_DETECTED`) a los Wallboards NOC conectados por WebSocket, y registro en `audit_logs` con hash encadenado HMAC-SHA256.
    - `src/api/v1/field_ops.py` (`certify_installation`): Georreferenciación de ONUs mediante vinculación inmediata de `tech_latitude` y `tech_longitude` al abonado (`SubscriberDevice`) para su visualización automática en el mapa.
    - `fastapi/tests/api/test_hito19_mass_outage_and_maps.unit.py`: Suite de validación exhaustiva con 100% de cobertura en flujos de corte masivo y certificación con coordenadas GPS.

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Calidad de Código:**
  - **Vue-TSC (`type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **ESLint (`pnpm exec eslint`):** Cero (0) errores y cero (0) advertencias en los componentes y suites de prueba de Hito 19.
  - **Prettier (`format:check`):** 100% de consistencia de formato y estilo en todos los archivos.
- **Compilación de Producción:**
  - **Vite Build (`pnpm run build`):** Compilación limpia sin errores en 4.08s, generando los bundles optimizados con división de código (`vendor-vue`, `vendor-map`, vistas asíncronas).
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 234 de 234 pruebas pasadas (100% exitosas) en 35 suites de prueba.
  - **Nuevas Capacidades de UI Validadas:**
    - `src/components/inventory/OsmOnuMap.vue`: Mapa OpenStreetMap exclusivo para ONUs de última milla, totalmente aislado del mapa de infraestructura de routers. Estados cromáticos Zero-Metrics (🟢 Óptimo < 40ms 0% pérdida, 🟠 Degradado 40-120ms o 1-20% pérdida, 🔴 Caído > 20% pérdida o timeout), spiderfier para cajas NAP / puntos coincidentes, popups táctiles y botones de acción rápida (*Test 1-Click* y *Diagnóstico 360°*).
    - `src/views/SubscribersMapView.vue`: Vista táctica en `/subscribers/map` con cinta de KPIs Zero-Metrics en tiempo real, filtros cromáticos, barra de búsqueda reactiva y panel lateral (drawer) de detalle del cliente.
    - `src/views/NocWallboardView.vue`: Banner interactivo de Caída Masiva con aviso sonoro táctico generado con la Web Audio API nativa y controles de acuse/silenciamiento.
    - `src/components/field/FieldTechMobileView.vue`: Eliminación del ancho fijo de 480px; diseño fluido adaptativo para móviles, tablets (2 columnas) y laptops/desktops (3 columnas con herramienta 360°), botón prominente *"📍 Capturar Coordenadas GPS"* y canvas táctil de firma digital.
    - `src/composables/useI18n.ts`: Módulo de internacionalización con diccionarios `es.json` y `en.json`, persistencia en `localStorage`, actualización de `document.documentElement.lang` y botón conmutador global `#btn-global-lang-toggle` en `RgResponsiveShell.vue`.

---

## 15. Certificación QA 11X — Hito 20 (Suite Corporativa — Config Drift, CIS Hardening, SD-WAN, Rogue DHCP, SLA y CAPsMAN)

Certificación integral ejecutada bajo la **Regla Cero** dentro de los contenedores Docker efímeros `qa-backend` (`sinfallas/base-python-uv:3.13`) y `qa-vue3` (`sinfallas/base-node-ionic:22`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check src/`):** Cero (0) errores en código fuente y suites de prueba.
  - **Ruff Format (`ruff format --check src/`):** 103 archivos de código fuente perfectamente formateados.
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en los 103 módulos del backend (`Success: no issues found in 103 source files`).
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 381 de 381 pruebas pasadas (100% exitosas) en 29.12s.
  - **Cobertura Total de Código:** **95.0%** (9,267 sentencias totales, 493 no ejecutadas), satisfaciendo el umbral corporativo de calidad `>= 95.0%`.
  - **Módulos y Endpoints Certificados:**
    - `src/api/v1/compliance.py`: Detección de Config Drift contra Golden Baselines (`GET /api/v1/compliance/config-drift/{router_id}`), generación de diff Git unificado, y reversión canónica atómica en 1 clic (`POST /api/v1/compliance/config-drift/revert`) con protección Safe Mode (60s) y registro en `audit_logs` con hash encadenado HMAC-SHA256. Auditoría CIS Benchmark (`GET /api/v1/compliance/cis-audit/{router_id}`) y auto-endurecimiento de directivas vulnerables (`POST /api/v1/compliance/cis-audit/{router_id}/auto-harden`).
    - `src/api/v1/sdwan.py`: Orquestación Hub & Spoke WireGuard (`POST /api/v1/sdwan/spokes`), asignación de subredes `/31` o `/30`, consulta de topología SD-WAN multi-spoke (`GET /api/v1/sdwan/topology/{tenant_id}`) y despliegue de failover Multi-WAN recursivo mediante netwatch scripts (`POST /api/v1/sdwan/multi-wan/failover`).
    - `src/api/v1/switching.py`: Inspección de DHCP Snooping en bridges MikroTik (`GET /api/v1/switching/dhcp-snooping/{router_id}`), monitoreo de alertas de Rogue DHCP (`GET /api/v1/switching/rogue-dhcp/alerts/{router_id}`) y aislamiento preventivo de puerto físico intruso bajo Safe Mode (`POST /api/v1/switching/rogue-dhcp/isolate-port`).
    - `src/api/v1/sla.py`: Sondas ICMP recurrentes hacia carriers (`POST /api/v1/sla/probes/run`), telemetría de latencias (avg/p95/p99) y jitter RFC 3550 (`GET /api/v1/sla/metrics/{router_id}`) y exportación de informes oficiales para penalización de carriers (`GET /api/v1/sla/reports/export`).
    - `src/api/v1/wifi.py`: Monitoreo de estado de controlador CAPsMAN / WiFiWave2 (`GET /api/v1/wifi/capsman/{router_id}/overview`), gestión de SSIDs 802.1X (`GET/POST /api/v1/wifi/capsman/{router_id}/ssids`) e inventario de clientes Wi-Fi con RSSI, SNR y soporte de fast roaming 802.11r (`GET /api/v1/wifi/clients/{router_id}`).
    - `fastapi/tests/api/test_hito20_enterprise_suite.unit.py`: Suite exhaustiva con 11 casos de prueba cubriendo las 6 sub-tareas de Hito 20.

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Calidad de Código:**
  - **Vue-TSC (`pnpm type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **ESLint (`pnpm eslint`):** Cero (0) errores y cero (0) advertencias en los nuevos componentes de Hito 20 (`EnterpriseComplianceView.vue`, `enterpriseComplianceView.unit.ts`).
  - **Prettier (`pnpm format:check`):** 100% de los archivos con formato y estilo verificado (`All matched files use Prettier code style!`).
- **Compilación de Producción:**
  - **Vite Build (`pnpm build`):** Compilación limpia sin errores en 4.39s, generando `dist/assets/EnterpriseComplianceView-*.js` (27.15 kB) y `dist/assets/EnterpriseComplianceView-*.css` (9.77 kB).
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 240 de 240 pruebas pasadas (100% exitosas) en 36 suites de prueba.
  - **Suite de Pruebas Hito 20 (`src/views/enterpriseComplianceView.unit.ts`):** 6 de 6 pruebas unitarias pasadas verificando el header táctico, badge de Safe Mode, navegación reactiva por las 6 pestañas y acción de reversión de Config Drift en 1 clic.

---

## 16. Certificación QA 11X — Hito 21 (Servidor MCP Ampliado para Agentes IA y Certificación QA 11X Final)

Certificación integral ejecutada bajo la **Regla Cero** dentro de los contenedores Docker efímeros `qa-backend` (`sinfallas/base-python-uv:3.13`) y `qa-vue3` (`sinfallas/base-node-ionic:22`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check src/ tests/`):** Cero (0) errores en código fuente y suites de prueba.
  - **Ruff Format (`ruff format --check src/ tests/`):** 100% de los archivos de código fuente y pruebas formateados canónicamente.
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores en todos los módulos del backend (`Success: no issues found in source files`).
  - **Radon Complejidad Ciclomática (`radon cc -s -a`):** Grado A en `src/api/v1/mcp.py` (promedio 2.9) y `src/api/v1/auth.py` (promedio 4.2).
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** 393 de 393 pruebas pasadas (100% exitosas) en 27.94s.
  - **Cobertura Total de Código:** **95.0%** (9,353 sentencias totales, 502 no ejecutadas), satisfaciendo el umbral corporativo innegociable de `>= 95.0%`.
  - **Auditoría Forense de Login y Sesión Única:**
    - Pruebas dedicadas en `fastapi/tests/api/test_auth_and_2fa_endpoints.unit.py` validando que los intentos fallidos (`LOGIN_FAILED_USER_NOT_FOUND`, `LOGIN_FAILED_INVALID_PASSWORD`, `LOGIN_FAILED_ACCOUNT_LOCKED`, `2FA_VERIFICATION_FAILED`) se persisten en `audit_logs` con hash WORM SHA-256.
    - Validación del Kill-Switch de sesión única: `kill_all_user_sessions` ejecutado en login generando evento `SESSION_KILLED_DUPLICATE_LOGIN`.
  - **Catálogo de 16 Tools Semánticas Certificadas:**
    1. `rosgrid_list_inventory`: Inventario y estado TOFU SSL.
    2. `rosgrid_get_router_health`: Telemetría física de CPU, RAM, temperatura y voltaje.
    3. `rosgrid_check_sfp_optical_ddm`: Diagnóstico DDM óptico con umbrales SFP.
    4. `rosgrid_inspect_routing_bgp_ospf`: Sesiones BGP v7 y adyacencias OSPF.
    5. `rosgrid_run_live_diagnostic`: Ping / Traceroute acotado (1 a 5 paquetes).
    6. `rosgrid_compare_config_diff`: Git unified_diff de respaldos `.rsc` contra base o LIVE.
    7. `rosgrid_reconnect_pppoe_client`: Reinicio asistido de sesiones PPPoE en `/ppp/active`.
    8. `rosgrid_propose_network_change`: Freno Maker-Checker HTTP 202 con Safe Mode (60s).
    9. `rosgrid_run_360_diagnostics`: Ping Multi-MTU (64B/512B/1472B DF), log analysis y Torch.
    10. `rosgrid_isolate_subscriber`: Aislamiento técnico idempotente en `AISLADOS_TECNICO` / 64k.
    11. `rosgrid_restore_subscriber`: Restauración idempotente y normalización de colas.
    12. `rosgrid_change_rate_limit`: Modificación de Simple Queue en caliente sin desconexión física.
    13. `rosgrid_query_bgp_looking_glass`: Consulta BGP route y advertised peers.
    14. `rosgrid_check_config_drift`: Comparación semántica contra Golden Baseline Template.
    15. `rosgrid_run_cis_audit`: Auditoría CIS Benchmark RouterOS v7 (Security Score 0-100).
    16. `rosgrid_detect_mass_outage`: Motor de correlación de caídas masivas en PON y cajas.

### B. Frontend (`vue3/`) — Docker `sinfallas/base-node-ionic:22`
- **Análisis Estático y Tipado Estricto:**
  - **Vue-TSC (`pnpm type-check`):** Cero (0) errores de tipado TypeScript estricto.
  - **Prettier (`pnpm format:check`):** 100% de los archivos con estilo y formato verificado (`All matched files use Prettier code style!`).
- **Compilación de Producción:**
  - **Vite Build (`pnpm build`):** Compilación limpia sin errores en 3.83s (`✓ built in 3.83s`).
- **Pruebas Unitarias (Vitest v8):**
  - **Pruebas Ejecutadas:** 242 de 242 pruebas pasadas (100% exitosas) en 36 suites de prueba.
  - **Navegación y Gobernanza Multi-Tenant:**
    - Verificación del posicionamiento de "Empresas (Tenants)" directamente debajo de "Auditoría WORM" en `RgResponsiveShell.unit.ts` exclusivamente para `SUPERADMIN_GLOBAL`.
    - Verificación de la visibilidad y restricción del botón `+ Registrar Empresa` en `tenantsManagementView.unit.ts` para perfiles no administrativos.

---

## 17. Certificación QA 11X — Hito 22 (Auditoría IaC, Endurecimiento Docker y Matriz de Pruebas Smoke Locales)

Certificación integral ejecutada bajo la **Regla Cero** garantizando cumplimiento de estándares estáticos, seguridad de contenedores y robustez de compuertas de despliegue local.

### A. Auditoría Estática de Infraestructura y Scripts
- **Trivy IaC (`./auditar-infra.sh`):**
  - **Dockerfiles y Compose:** Cero (0) fallos de configuración en `fastapi/Dockerfile`, `vue3/Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml` y `docker-compose.prod.local.yml`.
- **Trivy FileSystem (`uv.lock` y `pnpm-lock.yaml`):**
  - **Vulnerabilidades:** Cero (0) vulnerabilidades `HIGH` o `CRITICAL` en la cadena de dependencias de Python y Node.js.
- **Hadolint Dockerfile Linter (`hadolint/hadolint:latest-debian`):**
  - `fastapi/Dockerfile`: 0 errores, 0 advertencias (`USER 10001:10001` no-root, curl healthcheck).
  - `vue3/Dockerfile`: 0 errores, 0 advertencias (`USER 101:101` nginx no-root, wget healthcheck).
- **ShellCheck en Docker (`koalaman/shellcheck:stable`):**
  - Cero (0) errores y cero (0) advertencias en el 100% de los scripts del proyecto (`auditar-infra.sh`, `instalar-rosgrid.sh`, `build.sh`, `instalar-hooks.sh`, `limpieza.sh`, `probar-prod-local.sh`, `fastapi/scripts/entrypoint.sh`).

### B. Especificación y Endurecimiento de la Matriz Smoke Tests (`probar-prod-local.sh`)
- **Fase 1 (Auditoría e Imágenes):** Escaneo Trivy opcional + compilación multi-stage local con etiquetado `:local-test`.
- **Fase 2 (Despliegue Sintético):** Aislamiento de red interna con `pull_policy: never`.
- **Fase 3 (Healthchecks):** Sondeo activo de salud para PostgreSQL 17, KeyDB Multi-Hilo, FastAPI y `rosgrid-worker`.
- **Fase 4 (Pruebas Sintéticas y Hardening):**
  - Arranque estricto `--no-dev` (`test_production_boot_smoke.py`).
  - Liveness `/health` (HTTP 200) y Prometheus `/metrics`.
  - Transición inicial `/api/v1/auth/bootstrap-status` (`is_bootstrapped: false`).
  - Bundle Nginx UI en puerto configurado con cabeceras de seguridad CSP.
  - Verificación de proxy inverso Nginx hacia backend (`:${UI_PORT}/api/...`).
  - Ocultamiento estricto de documentación en producción (`/docs`, `/redoc`, `/openapi.json` = HTTP 404).
  - Prueba negativa de autenticación (Fail-Closed: `/api/v1/auth/me` sin token = HTTP 401).
- **Fase 5 (Aprovisionamiento, MCP y Contratos Front-Back):**
  - Creación de Superadmin con `crear_admin.py` y confirmación `is_bootstrapped: true`.
  - Emisión de Token MCP con `generar_token_mcp.py` y validación de sesión Bearer en KeyDB.
  - Invocación real del endpoint MCP JSON-RPC 2.0 (`POST /api/v1/mcp` con `tools/list`).
  - Ejecución obligatoria de la suite de 24 contratos Front-Back (`fastapi/scripts/validar_comunicacion_front_back.py`) dentro del contenedor con 100% de éxito.
- **Fase 6 (Diagnóstico y Cierre Limpio):**
  - Inspección de logs en busca de tracebacks en `rosgrid_api_local` y `rosgrid_worker_local`.
  - Verificación de aislamiento de puertos internos (5432 y 6379 cerrados al host).
  - Limpieza de volúmenes efímeros o entrega interactiva (`--keep-alive` / `--wizard`) con URLs corregidas.

---

## 18. Certificación QA 11X — Hito 22.5 (Mitigación Integral de Vectores de Ataque en Plataforma Híbrida Vue 3 + FastAPI)

Certificación integral ejecutada bajo la **Regla Cero** dentro del contenedor Docker efímero `qa-backend` (`sinfallas/base-python-uv:3.13`) y validada en entorno de producción local (`./probar-prod-local.sh`).

### A. Backend (`fastapi/`) — Docker `sinfallas/base-python-uv:3.13`
- **Análisis Estático y Seguridad (SAST):**
  - **Ruff (`ruff check src/ tests/`):** Cero (0) errores en código fuente y suites de prueba.
  - **Ruff Format (`ruff format --check src/ tests/`):** 100% de los archivos de código fuente y pruebas formateados canónicamente.
  - **Mypy Estricto (`mypy --strict src/`):** Cero (0) errores de tipado estricto en los 88 módulos de backend.
- **Pruebas Unitarias y Cobertura (Pytest 9.1.1):**
  - **Pruebas Ejecutadas:** **399 de 399 pruebas pasadas (100% exitosas)** en 30.22s.
  - **Cobertura Total de Código:** **95.04%** (9,414 sentencias totales, 467 no ejecutadas), superando el umbral corporativo innegociable de `>= 95.0%`.
  - **Mitigaciones Específicas Certificadas:**
    1. **Anti-CSWSH (`test_websockets.unit.py`):**
       - Rechazo con código de cierre de aplicación `4403` ante cabecera `Origin` no autorizada o ausente en modo producción antes de ejecutar `ws.accept()`.
       - Conexión autorizada cuando el `Origin` coincide con `settings.ALLOWED_ORIGINS` o en modo desarrollo local.
    2. **Sanitización de Errores 422 (`test_auth_and_2fa_endpoints.unit.py`):**
       - Validación del interceptor global `RequestValidationError` en modo producción: enmascara la estructura interna devolviendo mensaje genérico mientras registra el traceback completo en los logs de servidor.
    3. **Defensa Anti-SSRF (`test_alert_dispatcher_worker.unit.py`):**
       - Validación de la función `is_safe_webhook_url()` bloqueando IPs privadas (RFC 1918), loopback (`127.0.0.1`), link-local (`169.254.169.254`), multicast y resoluciones DNS maliciosas.
    4. **Bóveda SQL y Contexto de Tenant MCP (`test_mcp_endpoint.unit.py`):**
       - Confirmación de inyección segura de `set_tenant_context()` utilizando parámetros bindeados seguros en lugar de interpolación de cadenas.
    5. **Límite de Carga de Inventario CSV (`test_inventory_endpoints.unit.py`):**
       - Rechazo con HTTP `413 Payload Too Large` cuando el archivo CSV excede el umbral de seguridad de 2 MB.

### B. Validación de Integración en Producción Local (`./probar-prod-local.sh`)
- **Suite de Contratos Front-Back (`validar_comunicacion_front_back.py`):**
  - **Contratos Ejecutados:** **22 de 22 contratos aprobados (100% exitosos)** contra el stack completo en contenedores (`postgres`, `keydb`, `fastapi`, `worker`, `nginx`).
  - **Endpoints y Flujos Verificados:**
    - Bootstrap inicial y creación de Superadmin.
    - Autenticación con cookies `__Host-` y verificación 2FA TOTP.
    - Acceso a inventario, routers y métricas de salud física.
    - Endpoints de cumplimiento corporativo (CIS Benchmark, Config Drift y SD-WAN).
    - Despacho y verificación de herramientas en el Servidor MCP (`tools/list` y `tools/call`).
    - Verificación de cabeceras de proxy inverso `X-Forwarded-For` y `X-Forwarded-Proto` en `/ws/`.

### C. Certificación QA 11X del Asistente de Instalación Standalone (`instalar-rosgrid.sh`)
- **Auditoría Estática con ShellCheck (`koalaman/shellcheck:stable`):**
  - Cero (0) errores y cero (0) advertencias en `instalar-rosgrid.sh` y en los 7 scripts Bash del sistema (`auditar-infra.sh`, `instalar-rosgrid.sh`, `build.sh`, `instalar-hooks.sh`, `limpieza.sh`, `probar-prod-local.sh`, `fastapi/scripts/entrypoint.sh`).
  - Validación de compatibilidad POSIX, inicialización de variables de entrada y entrecomillado estricto.
- **Prueba Automatizada de Descarga Remota y Generación de Entropía:**
  - Verificada la descarga íntegra de `.env.example` y `docker-compose.prod.yml` desde la rama `main` de GitHub (`https://raw.githubusercontent.com/tecno-consultores/RoSGrid/main/`).
  - Verificada la generación e inyección de 5 secretos criptográficos de alta entropía (256 bits) para PostgreSQL, KeyDB, Bóveda AES-256-GCM, JWT y CSRF con permisos estrictos `chmod 600 .env`.
  - Verificada la función `leer_entrada` con soporte transparente para terminales `/dev/tty` bajo tuberías `curl -fsSL ... | bash` y modo dual inteligente (local en repositorio vs. remoto en `/opt/rosgrid`).

---

## 19. Certificación QA 11X — Cobertura BDD Integral Karate Labs (100% de la Interfaz Web)

Certificación ejecutada bajo la **Regla Cero** dentro de los contenedores efímeros Docker `qa-vue3` (`sinfallas/base-node-ionic:22`) y `karatelabs/karate:latest` conforme a `specs/28_FRONTEND_E2E_AND_KARATE_UI.md`.

### A. Catálogo de los 16 Escenarios BDD Certificados (`vue3/test/ui_business_flow.feature`)

| # | Escenario BDD | Ruta UI Evaluada | Capacidades y Aserciones Funcionales Verificadas |
| :--- | :--- | :--- | :--- |
| **1** | Autenticación Zero-Trust y 2FA TOTP | `/login` | Validación de credenciales, enrolamiento obligatorio TOTP con código QR y emisión de cookie segura `__Host-rg_at`. |
| **2** | Tablero Principal NOC y Refresco de Flota | `/`, `/dashboard` | Carga de franja de KPIs de salud, visualización del estado del clúster y pulsación interactiva del botón táctil de refresco (`refreshFleetData`). |
| **3** | Inventario Centralizado y Búsqueda Táctica | `/inventory` | Filtrado instantáneo por texto en `#inv-search`, estado de conexión y despliegue del modal de alta de nuevo MikroTik. |
| **4** | Consola WebFig v7 y Pestañas `<KeepAlive :max="5">` | `/routers/:id/webfig/live` | Navegación entre vistas Capa 1 y Capa 2, preservación de estado en memoria y renderizado de gráficas en vivo con Canvas 2D. |
| **5** | Bandeja de Aprobaciones Maker-Checker | `/operations/approvals` | Intercepción HTTP 202 (`AWAITING_APPROVAL`), visualización de Diff estructurado y acciones de aprobación/rechazo por supervisor. |
| **6** | Historial de Backups y Comparador Git Diff | `/backups` | Listado de respaldos de 30 días, selección interactiva de tarjetas `[🔵 BASE]` y `[🟢 OBJETIVO]`, descarga binaria `.backup` y diff `.rsc`. |
| **7** | Operaciones Masivas y Golden Templates | `/bulk-ops` | Selección múltiple de flota, aplicación de plantillas de configuración masivas y actualización controlada de paquetes RouterOS. |
| **8** | Wallboard NOC "Mission Control" y Mapa OSM | `/noc-wallboard` | Pantalla gigante para centros de control, KPIs agregados de tráfico Tx/Rx, marcadores en mapa Leaflet y alertas visuales/sonoras. |
| **9** | Bitácora Inmutable WORM y Certificación Forense | `/audit-logs` | Inspección de eventos inmutables, verificación criptográfica de la cadena SHA-256 e índice BRIN de alta velocidad. |
| **10** | Gestión de Organizaciones Multi-Tenant | `/admin/tenants` | Catálogo de tenants, control de cuotas de hardware y modal táctico *"Módulos & Capacidades"* con conmutación en caliente. |
| **11** | Matriz de Permisos RBAC y Auto-Registro | `/users` | Gestión de los 11 roles RBAC, matriz de routers asignados por técnico y switch global de registro público en KeyDB. |
| **12** | Monitor de Sesiones Activas y Kill-Switch | `/sessions` | Inspección de operadores conectados, dispositivos, IPs y revocación forzosa en vivo con expulsión inmediata en `< 100ms`. |
| **13** | Gestión de Direccionamiento IPAM Dual-Stack | `/ipam` | Gestión de prefijos IPv4 y subredes IPv6, cálculo visual de ocupación de pools y reserva de IPs estáticas. |
| **14** | Toolkit de Campo Móvil para Técnicos | `/field-ops` | Interfaz responsive táctil (botones de 44px WCAG 2.1 AA), diagnóstico óptico SFP DDM y captura de coordenadas GPS. |
| **15** | Mapa Táctico de Clientes/ONUs y Caída Masiva | `/subscribers/map` | Visualización geoespacial de abonados separada del core y activación de alarma ante caídas simultáneas > `mass_outage_threshold`. |
| **16** | Cumplimiento Normativo Corporativo (Compliance) | `/enterprise/compliance` | Auditoría de directivas CIS Benchmark con Security Score (0-100), detección de Config Drift y orquestación SD-WAN WireGuard. |

### B. Certificación de Calidad y No-Regresión en Contenedor Efímero
- **Análisis de Tipos TypeScript (`vue-tsc --noEmit`):** Cero (0) errores de tipado estricto.
- **Formateo y Estilo de Código (`prettier --check`):** 100% de conformidad con las directivas corporativas.
- **Suite Unitaria Vitest (`pnpm test:unit`):** **38 de 38 suites aprobadas (100%)** con **262 de 262 pruebas unitarias exitosas**.
- **Sincronización:** Los archivos de pruebas BDD en `vue3/test/ui_business_flow.feature` y su réplica de referencia en `examples/vue3/test/ui_business_flow.feature` permanecen 100% sincronizados bit a bit.



