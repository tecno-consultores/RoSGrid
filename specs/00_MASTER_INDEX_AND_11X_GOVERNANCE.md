# 00 — ÍNDICE MAESTRO, GOBERNANZA ARQUITECTÓNICA Y ESTÁNDAR 11X (RoSGrid)

> **[DIRECTIVA DE SISTEMA PARA AGENTES DE IA / ANTIGRAVITY]:** Actúa como un Principal Systems Architect, Staff Backend/Frontend Engineer y Staff QA Automation Engineer. Lee, analiza y aplica de forma estricta e innegociable todas las especificaciones contenidas en esta enciclopedia documental de 31 archivos ubicada en `specs/` para construir **RoSGrid**: Plataforma Centralizada Multi-Tenant de Gestión Técnica y Operativa para Flotas MikroTik RouterOS v7+. Procesa la lógica al máximo nivel de razonamiento técnico y genera todo el código, comentarios, commits y documentación en **Español**.

---

## 1. Identidad del Proyecto y Licencia Legal

* **Nombre Oficial del Sistema:** `RoSGrid`
* **Propósito:** Consola web centralizada Multi-Tenant de alta seguridad que permite administrar, diagnosticar, auditar, respaldar y operar flotas de routers MikroTik con **RouterOS v7.1+** exclusivamente a través de su **REST API nativa sobre HTTPS (`/rest/*`)**, replicando la capacidad técnica de WebFig/WinBox sin almacenar métricas históricas en base de datos ni incluir módulos de facturación, e incorporando un conector **MCP Protegido (`/api/v1/mcp`)** para agentes IA (`Hermes Agent`, `Claude`).
* **Licencia Obligatoria:** **GNU General Public License v3.0 (`GPL-3.0-only`)**.
  * Todo archivo de código fuente (`.py`, `.ts`, `.vue`, `.sh`, `Dockerfile`) DEBE incluir el encabezado SPDX estándar en sus primeras líneas:
    ~~~text
    # SPDX-License-Identifier: GPL-3.0-only
    # Copyright (C) 2026 RoSGrid Contributors
    ~~~
  * Debe existir un archivo `LICENSE` en la raíz del repositorio con el texto íntegro de la licencia GPLv3.

---

## 2. Leyes Innegociables de Infraestructura y Calidad (Estándar 11X)

Antigravity tiene **estrictamente prohibido** violar cualquiera de los siguientes 10 mandamientos arquitectónicos:

1. **Imágenes Oficiales Inmutables en QA y Empaquetado Multi-Stage de Producción:**
   * Queda prohibido usar la directiva `build:` dentro de `fastapi/docker-compose.qa.yml` y `vue3/docker-compose.qa.yml`.
   * Toda ejecución de desarrollo y pruebas QA DEBE consumir las imágenes oficiales inmutables `sinfallas/base-python-uv:3.15` (Backend FastAPI) y `sinfallas/base-node-ionic:26` + `nginx:alpine` (Frontend Vue 3), junto con los sidecars oficiales (`postgres:17-alpine`, `eqalpha/keydb:alpine` Multi-Hilo por defecto o `DragonflyDB` en alta escala, `sinfallas/karatelabs:latest`, `owasp/zap2docker-stable:latest`, `gaiaadm/pumba:latest`, `prom/prometheus:latest`, `sinfallas/remote-graphify:latest`).
   * Para distribución en producción hacia Docker Hub, se utilizan `fastapi/Dockerfile`, `vue3/Dockerfile`, `docker-compose.prod.yml` y `build.sh` generando `sinfallas/rosgrid-backend:latest` y `sinfallas/rosgrid-frontend:latest` con usuario sin privilegios (`non-root`).
2. **Cero Instalaciones en el Host:**
   * Prohibido ejecutar `pip install`, `uv sync`, `npm install` o `pnpm install` directamente en el sistema operativo anfitrión. Todo se ejecuta de manera efímera dentro de contenedores usando las metas de los `Makefile` (`make qa-lint`, `make qa-unit`, `make qa-mutation`, `make qa-all`) y volúmenes nombrados de caché (`uv-cache` y `pnpm-store`).
3. **Cero Almacenamiento de Métricas Históricas en Base de Datos (Zero-Metrics Storage):**
   * PostgreSQL **JAMÁS** almacenará series temporales de CPU, RAM, temperatura, voltaje ni tráfico de interfaces.
   * Las gráficas de recursos y tráfico funcionan **100% en vivo y en memoria RAM** (estilo WinBox): mientras un operador tiene abierta la consola del router, FastAPI hace streaming por WebSocket y Vue 3 acumula los puntos en un `TelemetryRingBuffer` (`shallowRef` + `<canvas>` 2D) en memoria de la pestaña. Al salir del router, las gráficas se reinician.
   * El monitoreo en segundo plano para alertas utiliza una **Máquina de Estados Efímera en KeyDB** (~200 bytes por router actualizados mediante `pipeline()`) que solo evalúa transiciones de estado (`ONLINE` <-> `OFFLINE` o umbral sostenido) sin escribir historial en disco.
4. **Cero Gestión de Conectividad de Red Subyacente y Cero Terminal CLI/SSH Libre:**
   * RoSGrid asume que el administrador de infraestructura ya garantizó la alcanzabilidad IP/enrutamiento entre el contenedor del backend y la IP/URL de la API REST de cada MikroTik.
   * Por diseño de seguridad (ADR), RoSGrid omite deliberadamente terminales interactivas SSH/Telnet/CLI libres para preservar el aislamiento *Split-Credential*, el *Maker-Checker*, el *Safe Mode* y la bitácora inmutable WORM.
5. **Uso de Graphify (En Docker) y Lectura Proactiva de Configuraciones:**
   * Al cerrar la arquitectura de Backend y Frontend, el agente DEBE ejecutar el perfil `--profile graphify` en Docker para generar `fastapi/graphify-out/GRAPH_REPORT.md` y `vue3/graphify-out/GRAPH_REPORT.md`, usándolos como fuente de verdad para la documentación en `docs/` y la certificación QA.
6. **Protocolo de Inicialización y Fusión Quirúrgica No Destructiva desde `examples/`:**
   * En las carpetas `examples/fastapi/` y `examples/vue3/` residen las plantillas originales y archivos `.example` del Estándar 11X. **Trátalos como referencia de solo lectura (no los modifiques ni los elimines).**
   * Al inicializar o auditar los directorios reales `./fastapi/` y `./vue3/` en la raíz del proyecto, une las herramientas de QA 11X con las dependencias de negocio de RoSGrid.
7. **Umbrales de Rechazo Automático ("Fail & Forbid"):**
   * **Cobertura Unitaria:** Mínimo **95%** obligatorio tanto en Backend (`pytest-cov --cov-fail-under=95`) como en Frontend (`Vitest v8` con 95% en `lines`, `functions`, `branches` y `statements`).
   * **Complejidad Ciclomática y Deuda Técnica:** En Python (`radon cc --min C` debe dar vacío y `radon mi --min B` debe ser grado `A`, con funciones `CC <= 5`); en Vue 3/TS (`eslint-plugin-sonarjs` sin funciones cognitivamente complejas).
   * **Pruebas de Mutación:** `mutmut` (Backend) y `Stryker` (Frontend) deben ejecutarse sin mutantes sobrevivientes en lógica crítica.
   * **Rendimiento y Accesibilidad UI:** Lighthouse CI (`performance >= 0.90`, `accessibility >= 0.95`, `best-practices >= 0.90`, `seo >= 0.90`) y `@axe-core/playwright` con **0 violaciones WCAG 2.1 A/AA**.
8. **Fronteras Estrictas de Archivos de Prueba (Tool Boundaries):**
   * Pruebas unitarias Backend: `fastapi/tests/**/*.unit.py` o `fastapi/tests/**/*.spec.py` (100% aisladas con `pytest-mock`, prohibido tocar red, Postgres, KeyDB o MikroTik real).
   * Pruebas unitarias Frontend: `vue3/src/**/*.unit.ts` o `vue3/src/**/*.spec.ts` (100% aisladas en `jsdom` con mocks).
   * Pruebas E2E y Accesibilidad Frontend: `vue3/e2e/**/*.e2e.ts` (ejecutadas exclusivamente por Playwright contra `http://ui-prod:80`).
   * Pruebas BDD Caja Negra: `fastapi/test/*.feature` y `vue3/test/*.feature` (ejecutadas por `sinfallas/karatelabs:latest`).
9. **Observabilidad y Hardening de Producción desde el Primer Commit:**
   * `fastapi/src/main.py` DEBE exponer `/metrics` usando `prometheus-fastapi-instrumentator`, usar `ORJSONResponse` por defecto y desactivar Swagger/ReDoc/OpenAPI cuando `ROSGRID_ENV == "production"`.
   * `vue3/` en Nginx (`ui-prod`) DEBE exponer `/stub_status` para `nginx/nginx-prometheus-exporter`.
10. **Bitácora Viva (`TESTING.md`) y Gobernanza Git (`Lefthook` + `Commitlint` + `Trivy`):**
    * Cada fase de certificación actualiza `TESTING.md`.
    * Todo commit debe seguir Conventional Commits en minúscula con longitud de cabecera `<= 72` caracteres.

---

## 3. Estructura Oficial del Monorepo RoSGrid

~~~text
rosgrid/
├── LICENSE                                  # Texto íntegro GPLv3
├── README.md                                # Documentación general del proyecto RoSGrid y ADR de seguridad
├── INSTALL.md                               # Guía paso a paso de instalación, KeyDB vs DragonflyDB y MikroTik
├── SECURITY.md                              # Política de seguridad, criptografía y reporte de vulnerabilidades
├── RESOURCES.md                             # Catálogo de recursos, imágenes Docker y RFCs
├── FAQ.md                                   # Preguntas frecuentes técnicas y operativas
├── CONTRIBUTING.md                          # Guía de contribución y umbrales del estándar QA 11X
├── CODE_OF_CONDUCT.md                       # Código de conducta (Contributor Covenant v2.1)
├── CHANGELOG.md                             # Historial de versiones (Keep a Changelog / SemVer)
├── ROADMAP.md                               # Hoja de ruta granular de los Hitos 0 al 16
├── TESTING.md                               # Bitácora Viva 11X global (flujos cubiertos y comandos)
├── docker-compose.yml                       # Orquestador local / laboratorio EVE-NG (con KeyDB Multi-Hilo)
├── docker-compose.prod.yml                  # Orquestador de producción (Imágenes oficiales en Docker Hub)
├── build.sh                                 # Script multi-arquitectura buildx para publicación en Docker Hub
├── .env.example                             # Plantilla de variables de entorno (Cero secretos reales)
├── .gitignore                               # Reglas globales de exclusión
├── commitlint.config.js                     # Reglas de Conventional Commits (Estándar 11X)
├── lefthook.yml                             # Barrera Pre-commit, Commit-msg y Pre-push
├── instalar-hooks.sh                        # Instalador de Lefthook
├── auditar-infra.sh                         # Escáner efímero Trivy IaC + FS (CRITICAL/HIGH = Exit 1)
│
├── specs/                                   # PLANOS ARQUITECTÓNICOS Y REGLAS PARA ANTIGRAVITY
│   ├── 00..30_*.md                          # Enciclopedia de 31 archivos de especificación RoSGrid
│   └── qa-11x/                              # Documentación oficial del Blueprint QA 11X
│
├── examples/                                # PLANTILLAS BASE 11X (SOLO LECTURA — NO MODIFICAR)
│   ├── fastapi/                             # Archivos .example, README.md y compose base de FastAPI
│   └── vue3/                                # Archivos .example, README.md y compose base de Vue 3
│
├── docs/                                    # DOCUMENTACIÓN OFICIAL DE ROSGRID (HITO 14)
│   ├── 01_GUIA_DESPLIEGUE_Y_ENTORNO.md
│   ├── 02_PREPARACION_MIKROTIK_ROUTEROS_V7.md
│   ├── 03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md
│   ├── 04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md
│   ├── 05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md
│   ├── 06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md
│   └── 07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md
│
├── fastapi/                                 # ECOSISTEMA BACKEND REAL (Python 3.13 + FastAPI + SQLAlchemy 2.0)
│   ├── Dockerfile                           # Imagen multi-stage no-root para sinfallas/rosgrid-backend
│   ├── docker-compose.qa.yml                # Orquestador efímero 11X para Backend (con KeyDB)
│   ├── Makefile                             # Comandos: qa-lint, qa-unit, qa-mutation, qa-all, clean-cache
│   ├── limpieza.sh                          # Purga profunda de artefactos y cachés Backend
│   ├── pyproject.toml                       # Dependencias de producción (orjson, uvloop) + QA 11X
│   ├── tox.ini                              # Matriz de validación y Radon (CC < C, MI >= B)
│   ├── alembic.ini                          # Configuración de migraciones PostgreSQL
│   ├── locustfile.py                        # Pruebas de estrés y caos para RoSGrid
│   ├── scripts/
│   │   └── entrypoint.sh                    # Arranque con pg_advisory_lock + alembic upgrade head + uvicorn (uvloop)
│   ├── migrations/                          # Versiones de esquema Alembic (RLS + WORM + BRIN)
│   ├── src/
│   │   ├── main.py                          # App FastAPI (ORJSONResponse) + /metrics + Swagger Off en prod
│   │   ├── core/                            # Config, Seguridad, Criptografía AES-256-GCM, CSRF, TOTP, Auditoría
│   │   ├── db/                              # Engine Async SQLAlchemy, Sesión, Contexto RLS Multi-Tenant
│   │   ├── redis_layer/                     # Cliente KeyDB/RESP, Idempotencia, Sesiones Kill-Switch, Pipelines Monitor
│   │   ├── models/                          # Modelos declarativos SQLAlchemy 2.0
│   │   ├── schemas/                         # Esquemas Pydantic v2 estrictos (incluyendo mcp.py JSON-RPC 2.0)
│   │   ├── rbac/                            # Matriz de 11 roles, permisos por router e interceptor Maker-Checker
│   │   ├── mikrotik/                        # Conector REST v7 (httpx Keep-Alive TLS), TOFU SSL, Safe Mode Scheduler
│   │   ├── api/                             # Routers FastAPI (Auth, Inventory, Vault, WebFig L1/L2, Ops, WS, MCP)
│   │   └── workers/                         # Tareas asíncronas (Backups, Diff, Monitor Cero-Métricas, Alertas)
│   ├── tests/                               # Suite Unitaria Aislada (*.unit.py)
│   └── test/                                # Suite BDD Caja Negra (Karate Labs *.feature)
│
└── vue3/                                    # ECOSISTEMA FRONTEND REAL (Vue 3 + TypeScript + Vite + Pinia)
    ├── Dockerfile                           # Imagen multi-stage no-root para sinfallas/rosgrid-frontend
    ├── docker-compose.qa.yml                # Orquestador efímero 11X para Frontend (sinfallas/base-node-ionic:26)
    ├── Makefile                             # Comandos: build-ui, qa-lint, qa-unit, qa-mutation, qa-perf, qa-e2e, qa-bdd
    ├── limpieza.sh                          # Purga profunda de artefactos y cachés Frontend
    ├── .npmrc                               # Zero-Trust (ignore-scripts=true, engine-strict=true)
    ├── package.json                         # Dependencias Vue 3, Leaflet, Pinia + Stack QA 11X
    ├── tsconfig.json                        # Tipado estricto TypeScript
    ├── vite.config.ts                       # Configuración de compilación Vite, chunks y PWA
    ├── vitest.config.ts                     # Frontera *.unit.ts / *.spec.ts y umbral 95% en las 4 métricas
    ├── stryker.conf.json                    # Configuración de pruebas de mutación Frontend
    ├── playwright.config.ts                 # Frontera *.e2e.ts, snapshots pixel-perfect y timezone America/Caracas
    ├── lighthouserc.js                      # Umbrales obligatorios Lighthouse CI (>= 0.90 / >= 0.95 a11y)
    ├── nginx/
    │   └── default.conf                     # Configuración Nginx con soporte SPA, cabeceras seguras y /stub_status
    ├── src/                                 # Código fuente Vue 3 (shallowRef, Virtual Scroll, Canvas 2D, KeepAlive)
    ├── e2e/                                 # Pruebas Playwright + @axe-core (*.e2e.ts)
    └── test/                                # Escenarios BDD Karate UI (*.feature)
~~~

---

## 4. Índice Maestro de los 31 Archivos de Especificación (Carpeta `specs/`)

Antigravity DEBE leer y ejecutar los documentos de especificación ubicados en `specs/` siguiendo rigurosamente el orden de los 5 Bloques listados a continuación:

### Bloque 0: Gobernanza, Arquitectura Global y Despliegue Inmutable
* `specs/00_MASTER_INDEX_AND_11X_GOVERNANCE.md` *(Este documento)* — Reglas globales, licencia GPLv3, estructura del monorepo y mandamientos del Estándar 11X.
* `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md` — Orquestación con imágenes `sinfallas/*`, KeyDB Multi-Hilo por defecto y perfil DragonflyDB, redes IPv4, migraciones automáticas con `pg_advisory_lock`, `Dockerfile` de producción, `build.sh` y cumplimiento de `Trivy`.

### Bloque 1: Base de Datos (PostgreSQL 17) y Estado Efímero (KeyDB Multi-Hilo)
* `specs/02_DB_SCHEMA_CORE_TENANTS_AND_RLS.md` — Tablas Multi-Tenant (`tenants`, `users`, `roles`, `user_router_permissions`) y políticas *Row-Level Security (RLS)*.
* `specs/03_DB_SCHEMA_INVENTORY_VAULT_AND_MAINTENANCE.md` — Tablas de inventario MikroTik, bóveda `AES-256-GCM`, rotación de credenciales, TOFU SSL SHA-256 y ventanas de mantenimiento.
* `specs/04_DB_SCHEMA_OPERATIONS_BACKUPS_AND_IMMUTABLE_AUDIT.md` — Tablas de Maker-Checker, backups `.rsc`/`.backup` con deduplicación SHA-256 (30 días), plantillas, trabajos masivos y `audit_logs` inmutable con índice `BRIN`.
* `specs/05_REDIS_KEYS_IDEMPOTENCY_AND_ZERO_METRICS.md` — Estructura de llaves KeyDB/RESP: idempotencia HTTP, familias de Refresh Tokens, *Kill-Switch* de sesiones, Pub/Sub de gráficas en vivo y máquina de estados *Zero-Metrics* con `pipeline()`.

### Bloque 2: Seguridad, Matriz RBAC (11 Roles) y Conector RouterOS v7
* `specs/06_SECURITY_SPLIT_CREDENTIAL_2FA_AND_STEPUP.md` — Patrón *Split-Credential* con cookies `__Host-`, CSRF firmado, 2FA TOTP, *Step-Up Auth* de 30s para revelar claves y cabeceras HTTP para OWASP ZAP.
* `specs/07_RBAC_11_ROLES_MATRIX_AND_MAKER_CHECKER.md` — Permisos granulares de los 11 roles y catálogo de acciones críticas sujetas a aprobación *Maker-Checker*.
* `specs/08_MIKROTIK_REST_V7_CLIENT_TOFU_AND_SAFEMODE.md` — Conector asíncrono `httpx` con pool TLS `Keep-Alive` para RouterOS v7 (`/rest/*`), pinning SSL TOFU y motor *Dead Man's Switch (Safe Mode)* mediante `/system/scheduler`.

### Bloque 3: Fases de Construcción, Catálogo de Endpoints y Servidor MCP del Backend (`fastapi/`)
* `specs/09_BACKEND_PHASE_1_SKELETON_OBSERVABILITY_AND_MIGRATIONS.md` — Fase 1 Backend: fusión 11X desde `examples/fastapi/`, `/metrics`, `ORJSONResponse`, auto-migración Alembic, middlewares e inyección de dependencias.
* `specs/10_BACKEND_ENDPOINTS_AUTH_TENANTS_USERS_KILLSWITCH.md` — Endpoints de Login Multi-Tenant, 2FA, gestión de usuarios, permisos por equipo y expulsión de sesiones en vivo.
* `specs/11_BACKEND_ENDPOINTS_INVENTORY_CSV_VAULT_AND_ROTATION.md` — Endpoints de inventario, autodescubrimiento, importación masiva CSV en 2 pasos, Bóveda *Step-Up Auth*, rotación de claves y mantenimiento.
* `specs/12_BACKEND_ENDPOINTS_WEBFIG_L1_INTERFACES_AND_IP.md` — Endpoints WebFig Capa 1: Interfaces (Ethernet, SFP DDM, VLAN, Bridge, WireGuard, WiFi) e IP/IPv6 (Addresses, Routes, ARP, DHCP, DNS, Services).
* `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md` — Endpoints WebFig Capa 1: Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, reordenamiento, `Conntrack`) y Routing v7 (`BGP`, `OSPF`, `BFD`).
* `specs/14_BACKEND_ENDPOINTS_WEBFIG_L1_PPP_QUEUES_SYSTEM_TOOLS.md` — Endpoints WebFig Capa 1: PPPoE/VPNs, Queues, System (Users, Scripts, Scheduler, Packages, Reboot) y Tools (`Ping`, `Traceroute`, `Torch`, `Log`).
* `specs/15_BACKEND_ENDPOINTS_WEBFIG_L2_UNIVERSAL_ENGINE.md` — Motor dinámico universal para el 100% restante de menús `/rest/*` de RouterOS v7.
* `specs/16_BACKEND_ENDPOINTS_MAKER_CHECKER_BACKUPS_BULK_UPDATES.md` — Endpoints de aprobaciones Maker-Checker, Backups y Diff Git de `.rsc`, Plantillas/Snippets, Acciones Masivas y Actualizador de RouterOS v7.
* `specs/17_BACKEND_WEBSOCKETS_LIVE_CHARTS_AND_ALERT_WORKERS.md` — Multiplexor WebSocket para gráficas efímeras estilo WinBox y workers de alerta (Telegram, SMTP, Webhook, NOC).
* `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md` — Endpoint MCP Protegido (`POST /api/v1/mcp` JSON-RPC 2.0 Streamable HTTP) para agentes IA (`Hermes Agent`, `Claude`) con cuenta `SERVICE_ACCOUNT` + CIDR, Rate-Limit en KeyDB, 8 Tools semánticas y freno obligatorio *Maker-Checker*.

### Bloque 4: Fases de Construcción y Especificación del Frontend (`vue3/`)
* `specs/18_FRONTEND_PHASE_1_SETUP_ZERO_TRUST_AND_INTERCEPTORS.md` — Fase 1 Frontend: fusión `.npmrc` Zero-Trust, stores Pinia con `shallowRef`, interceptores de seguridad/idempotencia/Kill-Switch y arquitectura PWA Mobile/Tablet.
* `specs/19_FRONTEND_DESIGN_SYSTEM_ACCESSIBILITY_AND_PERFORMANCE.md` — Sistema de diseño *Tactical NOC Cyan*, Densidad Dual (`32px`/`44px`), *Virtual Scrolling* nativo, buscador `Ctrl+K`, cumplimiento WCAG 2.1 AA (`@axe-core`) y Lighthouse >= 90.
* `specs/20_FRONTEND_VIEWS_AUTH_USERS_PERMISSIONS_AND_SESSIONS.md` — Pantallas de Login Multi-Tenant + 2FA, gestión de usuarios, asignación de routers y panel de sesiones activas en tiempo real.
* `specs/21_FRONTEND_VIEWS_INVENTORY_OSM_MAP_CSV_AND_VAULT.md` — Pantallas de inventario, mapa **Leaflet + OpenStreetMap**, asistente CSV, modal de Bóveda con temporizador de 30s y ventanas de mantenimiento.
* `specs/22_FRONTEND_VIEWS_WEBFIG_CONSOLE_RINGBUFFER_AND_LAYERS.md` — Consola WebFig: pestañas con memoria `<KeepAlive :max="5">`, gráficas efímeras en RAM (`TelemetryRingBuffer` sobre `<canvas>` 2D), módulos Capa 1 y motor universal Capa 2.
* `specs/23_FRONTEND_VIEWS_APPROVALS_DIFF_BULK_NOC_AND_AUDITOR.md` — Vistas de Maker-Checker, visor Diff de `.rsc`, asistente de Acciones Masivas/Updates, modo **Wallboard NOC** y consola del rol **Auditor**.

### Bloque 5: Suite de Pruebas y Certificación del Estándar 11X
* `specs/24_QA_11X_FASTAPI_INFRA_MAKEFILE_AND_CONFIGS.md` — Orquestador `fastapi/docker-compose.qa.yml`, `Makefile`, `pyproject.toml` y `tox.ini`.
* `specs/25_QA_11X_FASTAPI_UNIT_MUTATION_AND_MOCK_CATALOG.md` — Pruebas unitarias `.unit.py` (>= 95%), pruebas de mutación `mutmut` y catálogo de mocks para RouterOS v7.
* `specs/26_QA_11X_FASTAPI_CONTRACTS_BDD_DAST_AND_CHAOS.md` — Contratos `Schemathesis`, BDD `Karate Labs`, `OWASP ZAP`, profiling `py-spy` y caos con `Pumba + Locust + Prometheus`.
* `specs/27_QA_11X_VUE3_INFRA_UNIT_AND_STRYKER_MUTATION.md` — Orquestador `vue3/docker-compose.qa.yml`, `Makefile`, pruebas unitarias `Vitest` (>= 95%) y mutación con `Stryker`.
* `specs/28_QA_11X_VUE3_PLAYWRIGHT_AXE_LIGHTHOUSE_AND_KARATE.md` — Pruebas E2E `Playwright + @axe-core`, snapshots visuales deterministas, `Lighthouse CI`, `Karate UI` y observabilidad Nginx.
* `specs/29_ANTIGRAVITY_MASTER_EXECUTION_PLAYBOOK_AND_TESTING_MD.md` — Playbook secuencial de construcción, validación y plantilla obligatoria de `TESTING.md`.
* `specs/31_PRODUCTION_BOOTSTRAP_LOCAL_TESTING_AND_DISTRIBUTED_OPS.md` — Procedimiento de bootstrap en DB virgen, arquitectura distribuida Cross-Origin Direct y pipeline de validación local `./probar-prod-local.sh`.

### Bloque 6: Operaciones ISP, Gestión Corporativa de Flotas y Gobernanza Modular
* `specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md` — Módulo ISP técnico: QoS con Burst/PCQ, API de aprovisionamiento externa (Isolate/Restore/Rate-limit) con idempotencia, diagnóstico 360°, mapa de ONUs con telemetría efímera, alerta masiva, toolkit de campo responsive con GPS y arquitectura i18n.
* `specs/33_ENTERPRISE_FLEET_MANAGEMENT_AND_SECURITY_COMPLIANCE.md` — Módulo Corporativo / Enterprise: Detección de Desviación de Configuración (Config Drift vs Golden Baseline), Orquestador SD-WAN y Malla WireGuard Hub & Spoke, Auditoría CIS Benchmark (Score 0-100), Detección de Rogue DHCP / Seguridad LAN, Monitor de Cumplimiento de SLA y Gestión Centralizada WiFi (CAPsMAN / WiFiWave2).
* `specs/34_TENANT_FEATURE_FLAGS_AND_GOVERNANCE_PANEL.md` — Panel de Gobernanza de Feature Flags por Empresa: Modelo de datos en `tenants`, control de acceso por SuperAdmin, guardias de API y conmutación dinámica de la interfaz para operar como ISP, Entorno Corporativo o Mixto.

---

## 5. Políticas Complementarias de Gobernanza 11X (Linters, Smoke Test --no-dev y UAT)

1. **Política Innegociable de Cero Diagnósticos de IDE y Linters Estáticos:**
   - Todo archivo versionado en el repositorio debe mantener 0 errores y 0 advertencias en:
     - **Pyrefly / IDE:** Analizador estático tipado de Python con búsqueda configurada en `pyrefly.toml`.
     - **SonarLint / Radon:** Complejidad cognitiva máxima de 15 por función y complejidad ciclomática Grado A (`< 5`).
     - **Hadolint / Docker Linter:** Prohibición de comodines (*globs*) en instrucciones `COPY` (ej. `COPY uv.lock*`) para prevenir fugas de ficheros no previstos.
     - **ShellCheck (`koalaman/shellcheck:stable`):** Cero advertencias y cero errores en la totalidad de scripts `.sh` del monorepo.

2. **Protocolo de Dependencias Inmutables y Validación de Arranque en Producción (`--no-dev`):**
   - El contenedor de producción instala estrictamente mediante `uv sync --frozen --no-dev --compile-bytecode` en `/app/.venv`.
   - Se prohíbe terminantemente la presencia de paquetes de prueba o desarrollo (`pytest`, `radon`, `freezegun`, `unittest.mock`) en el código fuente de `src/`.
   - **Compuertas de Verificación:**
     - Test unitario AST [test_production_no_dev_cleanliness.unit.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/core/test_production_no_dev_cleanliness.unit.py) ejecutado en la suite de `pytest`.
     - Smoke test inmutable [test_production_boot_smoke.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/scripts/test_production_boot_smoke.py) ejecutado dentro del contenedor de producción verificando 80 submódulos sin paquetes dev.

3. **Plan Maestro de Pruebas Manuales y Aceptación de Usuario (UAT 11X):**
   - Antes de cada pase a producción o liberación de release con `./build.sh`, es requisito mandatorio ejecutar y registrar la bitácora de aceptación formal definida en [docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md), evaluando el comportamiento en hardware MikroTik v7+ físico o CHR.
