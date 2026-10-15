# 00 — ÍNDICE MAESTRO, GOBERNANZA ARQUITECTÓNICA Y ESTÁNDAR 11X (RoSGrid)

> **[DIRECTIVA DE SISTEMA PARA AGENTES DE IA / ANTIGRAVITY]:** Actúa como un Principal Systems Architect, Staff Backend/Frontend Engineer y Staff QA Automation Engineer. Lee, analiza y aplica de forma estricta e innegociable todas las especificaciones contenidas en esta enciclopedia documental de 30 archivos ubicada en `specs/` para construir **RoSGrid**: Plataforma Centralizada Multi-Tenant de Gestión Técnica y Operativa para Flotas MikroTik RouterOS v7+. Procesa la lógica al máximo nivel de razonamiento técnico y genera todo el código, comentarios, commits y documentación en **Español**.

---

## 1. Identidad del Proyecto y Licencia Legal

* **Nombre Oficial del Sistema:** `RoSGrid`
* **Propósito:** Consola web centralizada Multi-Tenant de alta seguridad que permite administrar, diagnosticar, auditar, respaldar y operar flotas de routers MikroTik con **RouterOS v7.1+** exclusivamente a través de su **REST API nativa sobre HTTPS (`/rest/*`)**, replicando la capacidad técnica de WebFig/WinBox sin almacenar métricas históricas en base de datos ni incluir módulos de facturación.
* **Licencia Obligatoria:** **GNU General Public License v3.0 (`GPL-3.0-only`)**.
  * Todo archivo de código fuente (`.py`, `.ts`, `.vue`, `.sh`) DEBE incluir el encabezado SPDX estándar en sus primeras líneas:
    ```text
    # SPDX-License-Identifier: GPL-3.0-only
    # Copyright (C) 2026 RoSGrid Contributors
    ```
  * Debe existir un archivo `LICENSE` en la raíz del repositorio con el texto íntegro de la licencia GPLv3.

---

## 2. Leyes Innegociables de Infraestructura y Calidad (Estándar 11X)

AntiGravity tiene **estrictamente prohibido** violar cualquiera de los siguientes 10 mandamientos arquitectónicos:

1. **Cero Compilaciones Locales (`No Dockerfile` / `No docker build`):**
   * Queda prohibido crear archivos `Dockerfile` personalizados o usar la directiva `build:` en ningún archivo `docker-compose*.yml`.
   * Toda ejecución de desarrollo, producción y pruebas DEBE consumir las imágenes oficiales inmutables `sinfallas/base-python-uv:3.13` (Backend FastAPI) y `sinfallas/base-node-ionic:22` / `node:20-bookworm-slim` + `nginx:alpine` (Frontend Vue 3), junto con los sidecars oficiales (`postgres:17-alpine`, `redis:7-alpine`, `sinfallas/karatelabs:latest`, `owasp/zap2docker-stable:latest`, `gaiaadm/pumba:latest`, `prom/prometheus:latest`, `sinfallas/remote-graphify:latest`).
2. **Cero Instalaciones en el Host:**
   * Prohibido ejecutar `pip install`, `uv sync`, `npm install` o `pnpm install` directamente en el sistema operativo anfitrión. Todo se ejecuta de manera efímera dentro de contenedores usando las metas de los `Makefile` (`make qa-lint`, `make qa-unit`, `make qa-mutation`, `make qa-all`) y volúmenes nombrados de caché (`uv-cache` y `pnpm-store`).
3. **Cero Almacenamiento de Métricas Históricas en Base de Datos (Zero-Metrics Storage):**
   * PostgreSQL **JAMÁS** almacenará series temporales de CPU, RAM, temperatura, voltaje ni tráfico de interfaces.
   * Las gráficas de recursos y tráfico funcionan **100% en vivo y en memoria RAM** (estilo WinBox): mientras un operador tiene abierta la pestaña del navegador en un router, FastAPI hace streaming por WebSocket y Vue 3 acumula los puntos en un `RingBuffer` en memoria de la pestaña. Al cerrar o refrescar la vista, las gráficas se reinician.
   * El monitoreo en segundo plano para alertas utiliza una **Máquina de Estados Efímera en Redis** (~200 bytes por router) que solo evalúa transiciones de estado (`ONLINE` <-> `OFFLINE` o umbral sostenido) sin escribir historial en disco.
4. **Cero Gestión de Conectividad de Red Subyacente:**
   * RoSGrid asume que el administrador de infraestructura ya garantizó la alcanzabilidad IP/enrutamiento entre el contenedor del backend y la IP/URL de la API REST de cada MikroTik. RoSGrid no administra VPNs del servidor host.
5. **Paso 0 Obligatorio con Graphify (MCP) y Lectura Proactiva de Configuraciones:**
   * Antes de escribir o refactorizar código en `fastapi/` o `vue3/`, el agente DEBE levantar el perfil `--profile graphify`, extraer el grafo semántico (`uvx graphifyy extract`) y leer los archivos locales de reglas (`pyproject.toml`, `tox.ini`, `package.json`, `.npmrc`, `tsconfig.json`, `vitest.config.ts`, `playwright.config.ts`) para cumplir el estándar en el primer intento.
6. **Protocolo de Inicialización y Fusión Quirúrgica No Destructiva desde `examples/`:**
   * En las carpetas `examples/fastapi/` y `examples/vue3/` residen las plantillas originales y archivos `.example` del Estándar 11X. **Trátalos como referencia de solo lectura (no los modifiques ni los elimines).**
   * Al inicializar los directorios reales `./fastapi/` y `./vue3/` en la raíz del proyecto:
     1. Lee obligatoriamente `specs/qa-11x/AI_MASTER_PROMPT.md`, `examples/fastapi/README.md` y `examples/vue3/README.md`.
     2. Copia hacia `./fastapi/` y `./vue3/` los orquestadores `docker-compose.qa.yml` y scripts `limpieza.sh`.
     3. Realiza la **Fusión Quirúrgica No Destructiva** de los archivos `.example` (`pyproject.toml.example`, `package.json.example`, `gitignore.example`, `Makefile.example`, `tox.ini.example`, `npmrc.example`, `stryker.conf.json.example`, `vitest.config.ts.example`, `playwright.config.ts.example`, `lighthouserc.js.example`, `locustfile.py.example`) generando los archivos definitivos sin el sufijo `.example` en `./fastapi/` y `./vue3/`, uniendo las herramientas de QA 11X con las dependencias de negocio de RoSGrid.
7. **Umbrales de Rechazo Automático ("Fail & Forbid"):**
   * **Cobertura Unitaria:** Mínimo **95%** obligatorio tanto en Backend (`pytest-cov --cov-fail-under=95`) como en Frontend (`Vitest v8` con 95% en `lines`, `functions`, `branches` y `statements`).
   * **Complejidad Ciclomática y Deuda Técnica:** En Python (`radon cc --min C` debe dar vacío y `radon mi --min B` debe ser grado `A`); en Vue 3/TS (`eslint-plugin-sonarjs` sin funciones cognitivamente complejas). Ninguna función o método debe superar una complejidad ciclomática de 10 (Grado B máximo, idealmente Grado A <= 5).
   * **Pruebas de Mutación:** `mutmut` (Backend) y `Stryker` (Frontend) deben ejecutarse sin mutantes sobrevivientes en lógica crítica.
   * **Rendimiento y Accesibilidad UI:** Lighthouse CI (`performance >= 0.90`, `accessibility >= 0.95`, `best-practices >= 0.90`, `seo >= 0.90`) y `@axe-core/playwright` con **0 violaciones WCAG 2.1 A/AA**.
8. **Fronteras Estrictas de Archivos de Prueba (Tool Boundaries):**
   * Pruebas unitarias Backend: `fastapi/tests/**/*.unit.py` o `fastapi/tests/**/*.spec.py` (100% aisladas con `pytest-mock`, prohibido tocar red, Postgres, Redis o MikroTik real).
   * Pruebas unitarias Frontend: `vue3/src/**/*.unit.ts` o `vue3/src/**/*.spec.ts` (100% aisladas en `jsdom` con mocks).
   * Pruebas E2E y Accesibilidad Frontend: `vue3/e2e/**/*.e2e.ts` (ejecutadas exclusivamente por Playwright contra `http://ui-prod:80`). Nota: el archivo de referencia `examples/vue3/accessibility.spec.ts` DEBE ubicarse y renombrarse como `vue3/e2e/accessibility.e2e.ts` para respetar el `testMatch: '**/*.e2e.ts'` de `playwright.config.ts`.
   * Pruebas BDD Caja Negra: `fastapi/test/*.feature` y `vue3/test/*.feature` (ejecutadas por `sinfallas/karatelabs:latest`).
9. **Observabilidad Innegociable desde el Primer Commit:**
   * `fastapi/src/main.py` DEBE exponer `/metrics` usando `prometheus-fastapi-instrumentator`.
   * `vue3/` en Nginx (`ui-prod`) DEBE exponer `/stub_status` para `nginx/nginx-prometheus-exporter`.
10. **Bitácora Viva (`TESTING.md`) y Gobernanza Git (`Lefthook` + `Commitlint` + `Trivy`):**
    * Cada fase completada obliga a actualizar `TESTING.md` en la raíz y en el subproyecto correspondiente.
    * Todo commit debe seguir Conventional Commits en minúscula con los scopes permitidos (`fastapi`, `vue3`, `docs`, `ci`, `global`) y longitud de cabecera `<= 72` caracteres.

---

## 3. Estructura Oficial del Monorepo RoSGrid

Para garantizar compatibilidad exacta con `lefthook.yml`, `commitlint.config.js` y `auditar-infra.sh` del Estándar 11X, manteniendo separadas las especificaciones (`specs/`), las plantillas de referencia (`examples/`) y la documentación del producto (`docs/`), AntiGravity DEBE estructurar el repositorio exactamente con este árbol de directorios:

```text
rosgrid/
├── LICENSE                                  # Texto íntegro GPLv3
├── README.md                                # Documentación general del proyecto RoSGrid
├── TESTING.md                               # Bitácora Viva 11X global (flujos cubiertos y comandos)
├── docker-compose.yml                       # Orquestador de despliegue integrado (Prod/Staging sin build)
├── .env.example                             # Plantilla de variables de entorno (Cero secretos reales)
├── .gitignore                               # Reglas globales de exclusión
├── commitlint.config.js                     # Reglas de Conventional Commits (Estándar 11X)
├── lefthook.yml                             # Barrera Pre-commit, Commit-msg y Pre-push
├── instalar-hooks.sh                        # Instalador de Lefthook
├── auditar-infra.sh                         # Escáner efímero Trivy IaC + FS (CRITICAL/HIGH = Exit 1)
│
├── specs/                                   # PLANOS ARQUITECTÓNICOS Y REGLAS PARA ANTIGRAVITY
│   ├── 00..29_*.md                          # Enciclopedia de 30 archivos de especificación RoSGrid
│   └── qa-11x/                              # Documentación oficial del Blueprint QA 11X
│       ├── AI_MASTER_PROMPT.md
│       ├── ARCHITECTURE_C4.md
│       ├── FAQ.md
│       ├── SECURITY.md
│       ├── ai-integration.md
│       ├── ci-cd-pipelines.md
│       ├── docker-troubleshooting.md
│       └── qa-philosophy.md
│
├── examples/                                # PLANTILLAS BASE 11X (SOLO LECTURA — NO MODIFICAR)
│   ├── fastapi/                             # Archivos .example, README.md y compose base de FastAPI
│   └── vue3/                                # Archivos .example, README.md y compose base de Vue 3
│
├── docs/                                    # RESERVADO EXCLUSIVAMENTE PARA DOCUMENTACIÓN PROPIA DE ROSGRID
│   └── (Manuales de usuario, guías operativas NOC, arquitectura desplegada, etc.)
│
├── fastapi/                                 # ECOSISTEMA BACKEND REAL (Python 3.13 + FastAPI + SQLAlchemy 2.0)
│   ├── docker-compose.qa.yml                # Orquestador efímero 11X para Backend
│   ├── Makefile                             # Comandos: qa-lint, qa-unit, qa-mutation, qa-all, clean-cache
│   ├── limpieza.sh                          # Purga profunda de artefactos y cachés Backend
│   ├── pyproject.toml                       # Dependencias de producción + QA 11X + configuración Ruff/Mypy/Mutmut
│   ├── tox.ini                              # Matriz de validación y Radon (CC < C, MI >= B)
│   ├── alembic.ini                          # Configuración de migraciones PostgreSQL
│   ├── locustfile.py                        # Pruebas de estrés y caos para RoSGrid
│   ├── TESTING.md                           # Bitácora Viva específica del Backend
│   ├── scripts/
│   │   └── entrypoint.sh                    # Arranque con pg_advisory_lock + alembic upgrade head + uvicorn
│   ├── migrations/                          # Versiones de esquema Alembic
│   │   ├── env.py
│   │   └── versions/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                          # App FastAPI + Instrumentator(/metrics) + Middlewares
│   │   ├── core/                            # Config, Seguridad, Criptografía AES-256-GCM, CSRF, TOTP, Auditoría
│   │   ├── db/                              # Engine Async SQLAlchemy, Sesión, Contexto RLS Multi-Tenant
│   │   ├── redis_layer/                     # Cliente Redis, Idempotencia, Sesiones Kill-Switch, Estado Monitor
│   │   ├── models/                          # Modelos declarativos SQLAlchemy 2.0
│   │   ├── schemas/                         # Esquemas Pydantic v2 estrictos
│   │   ├── rbac/                            # Matriz de 11 roles, permisos por router e interceptor Maker-Checker
│   │   ├── mikrotik/                        # Conector REST v7 (httpx), TOFU SSL SHA-256, Safe Mode Scheduler
│   │   ├── api/                             # Routers FastAPI (Auth, Inventory, Vault, WebFig L1/L2, Ops, WS)
│   │   ├── services/                        # Lógica de negocio desacoplada (Complejidad Ciclomática Grado A)
│   │   └── workers/                         # Tareas asíncronas (Backups, Diff, Monitor Cero-Métricas, Alertas)
│   ├── tests/                               # Suite Unitaria Aislada (*.unit.py / *.spec.py)
│   └── test/                                # Suite BDD Caja Negra (Karate Labs *.feature)
│
└── vue3/                                    # ECOSISTEMA FRONTEND REAL (Vue 3 + TypeScript + Vite + Pinia)
    ├── docker-compose.qa.yml                # Orquestador efímero 11X para Frontend
    ├── Makefile                             # Comandos: build-ui, qa-lint, qa-unit, qa-mutation, qa-perf, qa-e2e, qa-bdd, qa-obs, qa-all
    ├── limpieza.sh                          # Purga profunda de artefactos y cachés Frontend
    ├── .npmrc                               # Zero-Trust (ignore-scripts=true, engine-strict=true)
    ├── package.json                         # Dependencias Vue 3, Leaflet, Pinia + Stack QA 11X
    ├── tsconfig.json                        # Tipado estricto TypeScript
    ├── vite.config.ts                       # Configuración de compilación Vite y PWA
    ├── vitest.config.ts                     # Frontera *.unit.ts / *.spec.ts y umbral 95% en las 4 métricas
    ├── stryker.conf.json                    # Configuración de pruebas de mutación Frontend
    ├── playwright.config.ts                 # Frontera *.e2e.ts, snapshots pixel-perfect y timezone America/Caracas
    ├── lighthouserc.js                      # Umbrales obligatorios Lighthouse CI (>= 0.90 / >= 0.95 a11y)
    ├── TESTING.md                           # Bitácora Viva específica del Frontend
    ├── nginx/
    │   └── default.conf                     # Configuración Nginx con soporte SPA, cabeceras seguras y /stub_status
    ├── src/
    │   ├── main.ts
    │   ├── App.vue
    │   ├── api/                             # Cliente HTTP con interceptores CSRF, Idempotency-Key (UUIDv7) y Kill-Switch
    │   ├── stores/                          # Stores Pinia (Auth, Tenant, Inventory, WebFig, RingBuffer Charts, NOC)
    │   ├── router/                          # Vue Router con Guards RBAC de los 11 roles
    │   ├── composables/                     # Lógica reutilizable desacoplada y testeable
    │   ├── components/                      # Componentes UI de alta densidad (Tablas, Drag&Drop, Diff, Mapa OSM, Charts)
    │   ├── views/                           # Vistas por módulo (Login+2FA, Inventario, Vault, WebFig L1/L2, NOC, Auditor)
    │   └── __tests__/                       # Pruebas unitarias (*.unit.ts / *.spec.ts)
    ├── e2e/                                 # Pruebas Playwright + @axe-core (*.e2e.ts)
    └── test/                                # Escenarios BDD Karate UI (*.feature)
```

---

## 4. Índice Maestro de los 30 Archivos de Especificación (Carpeta `specs/`)

AntiGravity DEBE leer y ejecutar los documentos de especificación ubicados en `specs/` siguiendo rigurosamente el orden de los 5 Bloques listados a continuación:

### Bloque 0: Gobernanza, Arquitectura Global y Despliegue Inmutable
* `specs/00_MASTER_INDEX_AND_11X_GOVERNANCE.md` *(Este documento)* — Reglas globales, licencia GPLv3, estructura del monorepo (`specs/`, `examples/`, `docs/`, `fastapi/`, `vue3/`) y mandamientos del Estándar 11X.
* `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md` — Orquestación sin `Dockerfile`, uso de imágenes `sinfallas/*`, redes IPv4, migraciones automáticas con `pg_advisory_lock` y cumplimiento de `Trivy`.

### Bloque 1: Base de Datos (PostgreSQL 17) y Estado Efímero (Redis 7)
* `specs/02_DB_SCHEMA_CORE_TENANTS_AND_RLS.md` — Tablas Multi-Tenant (`tenants`, `users`, `roles`, `user_router_permissions`) y políticas *Row-Level Security (RLS)*.
* `specs/03_DB_SCHEMA_INVENTORY_VAULT_AND_MAINTENANCE.md` — Tablas de inventario MikroTik, bóveda `AES-256-GCM`, rotación de credenciales, TOFU SSL SHA-256 y ventanas de mantenimiento.
* `specs/04_DB_SCHEMA_OPERATIONS_BACKUPS_AND_IMMUTABLE_AUDIT.md` — Tablas de Maker-Checker, backups `.rsc`/`.backup` con deduplicación SHA-256 (30 días), plantillas, trabajos masivos y `audit_logs` inmutable.
* `specs/05_REDIS_KEYS_IDEMPOTENCY_AND_ZERO_METRICS.md` — Estructura de llaves Redis: idempotencia HTTP, familias de Refresh Tokens, *Kill-Switch* de sesiones, Pub/Sub de gráficas en vivo y máquina de estados *Zero-Metrics*.

### Bloque 2: Seguridad, Matriz RBAC (11 Roles) y Conector RouterOS v7
* `specs/06_SECURITY_SPLIT_CREDENTIAL_2FA_AND_STEPUP.md` — Patrón *Split-Credential* con cookies `__Host-`, CSRF firmado, 2FA TOTP, *Step-Up Auth* de 30s para revelar claves y cabeceras HTTP para OWASP ZAP.
* `specs/07_RBAC_11_ROLES_MATRIX_AND_MAKER_CHECKER.md` — Permisos granulares de los 11 roles y catálogo de acciones críticas sujetas a aprobación *Maker-Checker*.
* `specs/08_MIKROTIK_REST_V7_CLIENT_TOFU_AND_SAFEMODE.md` — Conector asíncrono `httpx` para RouterOS v7 (`/rest/*`), pinning SSL TOFU y motor *Dead Man's Switch (Safe Mode)* mediante `/system/scheduler`.

### Bloque 3: Fases de Construcción y Catálogo de Endpoints del Backend (`fastapi/`)
* `specs/09_BACKEND_PHASE_1_SKELETON_OBSERVABILITY_AND_MIGRATIONS.md` — Fase 1 Backend: fusión 11X desde `examples/fastapi/`, `/metrics`, auto-migración Alembic, middlewares e inyección de dependencias.
* `specs/10_BACKEND_ENDPOINTS_AUTH_TENANTS_USERS_KILLSWITCH.md` — Endpoints de Login Multi-Tenant, 2FA, gestión de usuarios, permisos por equipo y expulsión de sesiones en vivo.
* `specs/11_BACKEND_ENDPOINTS_INVENTORY_CSV_VAULT_AND_ROTATION.md` — Endpoints de inventario, autodescubrimiento, importación masiva CSV en 2 pasos, Bóveda *Step-Up Auth*, rotación de claves y mantenimiento.
* `specs/12_BACKEND_ENDPOINTS_WEBFIG_L1_INTERFACES_AND_IP.md` — Endpoints WebFig Capa 1: Interfaces (Ethernet, SFP DDM, VLAN, Bridge, WireGuard, WiFi) e IP/IPv6 (Addresses, Routes, ARP, DHCP, DNS, Services).
* `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md` — Endpoints WebFig Capa 1: Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, reordenamiento, `Conntrack`) y Routing v7 (`BGP`, `OSPF`, `BFD`).
* `specs/14_BACKEND_ENDPOINTS_WEBFIG_L1_PPP_QUEUES_SYSTEM_TOOLS.md` — Endpoints WebFig Capa 1: PPPoE/VPNs, Queues, System (Users, Scripts, Scheduler, Packages, Reboot) y Tools (`Ping`, `Traceroute`, `Torch`, `Log`).
* `specs/15_BACKEND_ENDPOINTS_WEBFIG_L2_UNIVERSAL_ENGINE.md` — Motor dinámico universal para el 100% restante de menús `/rest/*` de RouterOS v7.
* `specs/16_BACKEND_ENDPOINTS_MAKER_CHECKER_BACKUPS_BULK_UPDATES.md` — Endpoints de aprobaciones Maker-Checker, Backups y Diff Git de `.rsc`, Plantillas/Snippets, Acciones Masivas y Actualizador de RouterOS v7.
* `specs/17_BACKEND_WEBSOCKETS_LIVE_CHARTS_AND_ALERT_WORKERS.md` — Multiplexor WebSocket para gráficas efímeras estilo WinBox y workers de alerta (Telegram, SMTP, Webhook, NOC).

### Bloque 4: Fases de Construcción y Especificación del Frontend (`vue3/`)
* `specs/18_FRONTEND_PHASE_1_SETUP_ZERO_TRUST_AND_INTERCEPTORS.md` — Fase 1 Frontend: fusión `.npmrc` Zero-Trust desde `examples/vue3/`, stores Pinia, interceptores de seguridad/idempotencia/Kill-Switch y arquitectura PWA Mobile/Tablet.
* `specs/19_FRONTEND_DESIGN_SYSTEM_ACCESSIBILITY_AND_PERFORMANCE.md` — Sistema de diseño de alta densidad (Claro/Oscuro/NOC), buscador `Ctrl+K`, cumplimiento WCAG 2.1 AA (`@axe-core`) y Lighthouse >= 90.
* `specs/20_FRONTEND_VIEWS_AUTH_USERS_PERMISSIONS_AND_SESSIONS.md` — Pantallas de Login Multi-Tenant + 2FA, gestión de usuarios, asignación de routers y panel de sesiones activas en tiempo real.
* `specs/21_FRONTEND_VIEWS_INVENTORY_OSM_MAP_CSV_AND_VAULT.md` — Pantallas de inventario, mapa **Leaflet + OpenStreetMap**, asistente CSV, modal de Bóveda con temporizador de 30s y ventanas de mantenimiento.
* `specs/22_FRONTEND_VIEWS_WEBFIG_CONSOLE_RINGBUFFER_AND_LAYERS.md` — Consola WebFig: gráficas efímeras en RAM (`RingBuffer`), módulos Capa 1 (con Drag & Drop accesible) y formulario/tabla universal Capa 2.
* `specs/23_FRONTEND_VIEWS_APPROVALS_DIFF_BULK_NOC_AND_AUDITOR.md` — Vistas de Maker-Checker, visor Diff de `.rsc`, asistente de Acciones Masivas/Updates, modo **Wallboard NOC** y consola del rol **Auditor**.

### Bloque 5: Suite de Pruebas y Certificación del Estándar 11X
* `specs/24_QA_11X_FASTAPI_INFRA_MAKEFILE_AND_CONFIGS.md` — Orquestador `fastapi/docker-compose.qa.yml`, `Makefile`, `pyproject.toml` y `tox.ini`.
* `specs/25_QA_11X_FASTAPI_UNIT_MUTATION_AND_MOCK_CATALOG.md` — Pruebas unitarias `.unit.py` (>= 95%), pruebas de mutación `mutmut` y catálogo de mocks para RouterOS v7.
* `specs/26_QA_11X_FASTAPI_CONTRACTS_BDD_DAST_AND_CHAOS.md` — Contratos `Schemathesis`, BDD `Karate Labs`, `OWASP ZAP`, profiling `py-spy` y caos con `Pumba + Locust + Prometheus`.
* `specs/27_QA_11X_VUE3_INFRA_UNIT_AND_STRYKER_MUTATION.md` — Orquestador `vue3/docker-compose.qa.yml`, `Makefile`, pruebas unitarias `Vitest` (>= 95%) y mutación con `Stryker`.
* `specs/28_QA_11X_VUE3_PLAYWRIGHT_AXE_LIGHTHOUSE_AND_KARATE.md` — Pruebas E2E `Playwright + @axe-core`, snapshots visuales deterministas, `Lighthouse CI`, `Karate UI` y observabilidad Nginx.
* `specs/29_ANTIGRAVITY_MASTER_EXECUTION_PLAYBOOK_AND_TESTING_MD.md` — Playbook secuencial de construcción, validación y plantilla obligatoria de `TESTING.md`.
