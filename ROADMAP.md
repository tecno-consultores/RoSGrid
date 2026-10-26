# 🗺️ ROADMAP GRANULAR DE EJECUCIÓN (42 SPECS) — RoSGrid

## 📍 Punto de Control Actual (Checkpoint)

- **Hito Actual en Curso:** Hito 27 (En Planificación) — Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`scripts/build.sh`).
- **Hito General del Sistema:** Hitos 0 al 26 COMPLETADOS (100%).
- **Hito 26 (Gobernanza Táctica de Módulos B2B — DAG Hard Lock, Blindaje RBAC, Modo Contingencia y Auditoría Forense con Rollback):** COMPLETADO al 100% y certificado en Docker. Especificación formal `docs/specs/45_TACTICAL_FEATURE_FLAGS_GOVERNANCE_DAG_AND_AUDIT_ROLLBACK.md`. Grafo DAG activo en `RgFeatureFlagsGrid.vue` con bloqueo en cascada y tooltips (`[ 🔒 Requiere activar previamente: Módulo ISP ]`), blindaje RBAC fail-closed en `fastapi/src/api/v1/tenants.py` restringiendo licenciamiento exclusivamente a `SUPERADMIN_GLOBAL` con `HTTP 403 Forbidden`, arquetipo rápido en 1 clic `[ ⚡ Modo Contingencia / Bajo Consumo ]` suspendiendo colectores intensivos ante saturación de red con banner táctico reactivo, y pestaña táctica `[ 📜 Historial de Modificaciones ]` en `TenantModulesStudioView.vue` respaldada por `TenantModulesAuditTab.vue` con consulta WORM SHA-256 de `audit_logs` y reversión rollback en 1 clic. 544 tests backend Pytest (100% éxito), 412 tests frontend en 56 suites Vitest (100% éxito), 97 escenarios BDD Karate Labs API, 46 escenarios BDD Karate Labs UI, y validación visual interactiva en navegador con `browser_subagent`.
- **Internacionalización Integral (i18n) en Inglés y Español de 16 Vistas/Módulos Críticos:** COMPLETADO al 100% y certificado en Docker. Cobertura simétrica total en `vue3/src/locales/es.json` y `vue3/src/locales/en.json` para las 16 áreas clave: Maker-Checker, IPAM, Mapa Unificado de Clientes/ONUs, Desplegables de Técnico de Campo, Topología L2 PoE, Comparador Diff de Respaldos Git, Operaciones Masivas & Golden Config, Gestión de Usuarios y Roles RBAC, Administración de Empresas Multi-Tenant & Módulos Studio, CIS Hardening, Matriz CVE, Auditoría Forense WORM, SD-WAN WireGuard, Seguridad L2 & Rogue DHCP, Telemetría de SLA y Canales de Notificación Multicanal. 405 tests en 55 suites Vitest pasando al 100%, 45 escenarios BDD en Karate Labs UI (incorporado Escenario 45 de conmutación interactiva), 543 tests backend en Pytest pasando al 100%, validación estática limpia con `vue-tsc --noEmit`, `ruff check` y `mypy`, y 0 hallazgos en auditoría de secretos.
- **Hito 25 (Conmutador Rápido de Contexto de Tenants, Ergonomía de Pie de Página In-Flow y Gestión Táctica de Feature Flags por Empresa):** COMPLETADO al 100% y certificado en Docker. Especificación formal `docs/specs/44_TENANT_SWITCHER_INFLOW_FOOTER_AND_MODULAR_FEATURE_FLAGS.md`. Conmutador rápido de tenants exclusivo para `SUPERADMIN_GLOBAL` en cabecera (`RgTenantSwitcher.vue`), respaldado por `POST /api/v1/auth/switch-tenant` con re-keying atómico de sesión en KeyDB y auditoría WORM. Estabilización de conmutación sin auto-deslogueo por WebSocket kill-switch (25.11). Supresión de la barra flotante de 32px y reubicación del footer in-flow dentro de `.rg-main` con `margin-top: auto` (100% de espacio vertical recuperado). Sub-pantalla dedicada `/admin/tenants/:id/modules` con 4 cuadrantes tácticos, 4 presets rápidos y diálogo modal de confirmación de radio de impacto. 5 pruebas unitarias Pytest aprobadas al 100%, 55 suites Vitest con 402/402 tests aprobados, compilación Vite limpia en 4.14s y smoke tests de flota real multi-dominio 100% aprobados.
- **Hito 24 (Marco Universal de Fixtures Trimodales Ground-Truth, Invariantes Negativas y Smoke Tests de Flota Real - 8 Dominios):** COMPLETADO al 100% y certificado en Docker. Especificación formal `docs/specs/43_REAL_FLEET_SMOKE_TESTS_GROUND_TRUTH_FIXTURES_AND_DETERMINISTIC_SENSING.md`, regla de gobernanza institucional `.agents/rules/ground_truth_fixtures_and_negative_invariants.md` y actualización en `AGENTS.md`. Erradicación de la ceguera de mocks (Mock Blindness) en los 8 dominios (Syslog, CIS Hardening, Topología L2, IPAM DHCP, PoE, Rogue DHCP, CAPsMAN WiFi 6 y Config Drift) mediante ternas de fixtures crudos de MikroTik RouterOS v7. Detección canónica estricta con doble candado en Syslog (`rosgridsyslog`), eliminación de métricas inventadas en CAPsMAN (`wifi.py`), aserciones negativas obligatorias para routers de fábrica (`r4, r5, r6`), suite unitaria en Pytest (`test_ground_truth_trimodal_fixtures.unit.py` y `test_inventory_syslog_detection.unit.py` 18/18 tests pasando al 100%) y guardrail de Smoke Test de Flota Real multi-dominio (`scripts/validar-flota-real.py` / `make smoke-fleet`) evaluando los 6 routers físicos reales en laboratorio.
- **Hito 23.28 (Guardrail Anti-Regresión, Detección de Datagramas UDP y Sincronización Syslog en Inventario):** COMPLETADO al 100% y certificado en Docker. Regla `.agents/rules/anti_regression_and_side_effects_guardrail.md` y actualización en `AGENTS.md`. Mapeo bimodal de puertos UDP 514 y 5514 en `docker-compose.prod.local.yml`, resolución heurística en `SyslogUdpProtocol` resiliente a Docker NAT (`172.18.0.1`), inspección flexible de acciones RouterOS v7 (`inspect_router_syslog_config`), refresco activo bajo demanda `?refresh=true` con endpoint `/sync-syslog`, y principio de "No Destructive Catch" en Pinia (`useInventoryStore.ts`). 390 pruebas unitarias Vitest aprobadas (100% éxito en 52 archivos), `vue-tsc` limpio y 0 hallazgos en auditoría de secretos.
- **Hito 23.27 (Cierre de Pestaña/Navegador, Coordinación Multi-Pestaña y Grace Period en KeyDB):** COMPLETADO al 100% y certificado en Docker. Especificación formal `docs/specs/41_TAB_CLOSE_DETECTION_AND_EPHEMERAL_GRACE_PERIOD_SESSION_CLEANUP.md`. Coordinación `BroadcastChannel` multi-pestaña, `sendBeacon` en `pagehide`, endpoint `/session-closing` con período de gracia de 35s en KeyDB, worker de ciclo de vida `session_lifecycle_worker`, cancelación reactiva ante F5/reconexión, eliminación de elementos redundantes en barra lateral (`RgResponsiveShell.vue`) y corrección integral de baldosas de navegación en `DashboardHomeView.vue`. 514 tests unitarios backend (92% de cobertura), 383 tests frontend en 51 archivos Vitest (100% pasando), 89 escenarios BDD API y 41 escenarios BDD UI en Karate Labs, y 26 contratos Front-Back aprobados en Docker.
- **Hito 23.26 (Auditoría Preventiva Shift-Left, Makefile Canónico y Compuerta de Seguridad):** COMPLETADO al 100% y certificado en Docker. Especificación formal `docs/specs/40_LOCAL_VULNERABILITY_AUDIT_AND_SHIFT_LEFT_SECURITY.md`, creación de `Makefile` con comandos canónicos (`make audit`, `make test`, `make lint`, `make certify`), actualización del script de certificación de 5 etapas `.agents/scripts/certify_task_completion.sh` con Trivy IaC + FS en contenedor efímero de solo lectura, remediación inmediata de `brotli v1.2.1` (`GHSA-9v8h-qqgm-4m35`) en `uv.lock`, 4 pruebas unitarias de gate en `test_vulnerability_audit_gate.unit.py` (506 tests unitarios backend en total, 377 frontend Vitest en 50 suites, 88 escenarios BDD API y 40 escenarios BDD UI en Karate Labs), y 0 vulnerabilidades CRITICAL/HIGH detectadas en local antes de Git Push.
- **Hito 23.25 (Componente Unificado de Mapa, 3 Toggles de Capas, Causa Raíz RCA y Locks en KeyDB):** COMPLETADO al 100% y certificado en Docker.
- **Hito 23 (Automatización de Flota, Topología L2, Syslog Efímero, Exportador Prometheus, Seguridad CVE y Disponibilidad API):** COMPLETADO al 100% y certificado en Docker. Especificaciones `docs/specs/35`, `docs/specs/03`, `docs/specs/11`, `docs/specs/18`, `docs/specs/19` y `docs/specs/36`, manuales `docs/12`, `docs/04` y `docs/06`, migraciones Alembic 0007 y 0008 (`tenant_custom_roles` y `routers.network_role` VARCHAR(64)), colector Syslog UDP 5514 activo en Worker con RingBuffer en KeyDB y badge de presencia en inventario con detección continua de configuración, motor de Topología L2 con Pan/Zoom Canvas 2D a 60 FPS, Matriz CVE con cruce local semver, auto-sincronización diaria con caché táctico de 24 horas y forzado manual, orquestador PoE-aware con Safety Stop (1%), exportador Prometheus `/api/v1/metrics/fleet`, indicador táctico de presencia y disponibilidad de API (Heartbeat/Ping) en barra superior y login con popover diagnóstico y caché anti-Thundering Herd de 5s en `/health`, 22 herramientas MCP en la Skill `rosgrid-noc-operator` con grounding oficial de RouterOS v7, 485 tests backend (95.1% cobertura), 361 tests frontend (100% pasando en 49 archivos Vitest), 76/76 escenarios BDD API en Karate Labs, 30/30 escenarios BDD UI en Karate Labs y 26/26 contratos Front-Back validados en Docker (`validar_comunicacion_front_back.py`).
- **Hito 22.15 (Skill Oficial de Operaciones NOC para Agentes IA):** COMPLETADO al 100% y certificado en Docker. Arquitectura portable en `.agents/skills/rosgrid-noc-operator/SKILL.md` y global en `~/.gemini/config/skills/`, 5 Playbooks SOP (Diagnóstico 360°, cortes de fibra PON, inestabilidad BGP/OSPF, auditoría CIS y drift, aislamiento preventivo), catálogo de 14 herramientas MCP, referencias de flags RouterOS v7, configs para Claude Desktop y Hermes Agent, distribución remota en `instalar-rosgrid.sh` (`/opt/rosgrid/skills/`), botones de descarga/copiado en `RgMcpTokenModal.vue` y endpoint público `GET /api/v1/mcp/skill`.
- **Hito 22.14 (Generador de Tokens MCP, Supervisión de Sesiones IA y Panel de Notificaciones):** COMPLETADO al 100% y certificado en Docker. Emisión visual de Bearer Tokens MCP en `RgMcpTokenModal.vue`, Kill-Switch de agentes IA en `ActiveSessionsKillSwitchView.vue`, paridad frontend total con `NotificationChannelsPanel.vue` (Telegram, SMTP, Webhooks) y 406 tests backend / 278 tests frontend aprobados.
- **Hito 22.13 (Consolidación de Calidad, Resolución de Diagnósticos y Robustecimiento DevOps):** COMPLETADO al 100% y certificado en Docker. Normalización con markdownlint-cli, modernización a Mermaid flowchart, Type Narrowing en escapeHtml, eliminación de tests/ huérfana en vue3, script verificar-secretos.sh para Lefthook con ShellCheck y backend con 404 tests unitarios y 95.07% de cobertura.
- **Hito 22.12 (Auditoría Integral de Ciberseguridad y Mitigación de Vulnerabilidades):** COMPLETADO al 100% y certificado en Docker. Mitigaciones CSRF, XSS en Leaflet, SSRF en routers, concurrencia en refresh tokens y aislamiento de idempotencia implementados.
- **Hito 22.11 (Migración Integral de Runtime a Python 3.15 y Node.js 26 LTS):** COMPLETADO al 100% y certificado en Docker. Registro histórico integral de hitos consolidado en `TESTING.md`.
- **Hito 21 (Servidor MCP Ampliado para Agentes IA y Certificación QA 11X Final):** COMPLETADO al 100% y certificado en Docker:
  - Servidor Model Context Protocol (MCP) Integrado en FastAPI (`POST /api/v1/mcp`) ampliado a 16 herramientas semánticas con esquemas Pydantic v2 y validación JSON-RPC 2.0 *Streamable HTTP*.
  - 8 nuevas herramientas semánticas operativas para agentes inteligentes (Hermes Agent, Claude Code / Desktop, NOC Autónomo):
    1. `rosgrid_run_360_diagnostics`: Suite diagnóstica 360° (Ping multi-MTU con DF-bit, análisis de logs de desconexión y muestreo Torch).
    2. `rosgrid_isolate_subscriber`: Aislamiento técnico idempotente de servicios de red en firewall `AISLADOS_TECNICO` o cola 64k.
    3. `rosgrid_restore_subscriber`: Restauración técnica idempotente y reanudación de perfiles nominales.
    4. `rosgrid_change_rate_limit` (alias: `rosgrid_change_subscriber_rate_limit`): Conmutación en caliente de perfiles QoS / Simple Queue sin desconexión física.
    5. `rosgrid_query_bgp_looking_glass`: Consulta no interactiva de tablas de rutas BGP v7 y prefijos anunciados a peers.
    6. `rosgrid_check_config_drift`: Comparación y detección semántica de desviación contra Golden Baseline Templates.
    7. `rosgrid_run_cis_audit`: Auditoría automatizada de directivas críticas CIS Benchmark con Security Score (0-100).
    8. `rosgrid_detect_mass_outage`: Motor de correlación de cortes de fibra óptica y caídas masivas en ramas PON y cajas.
  - Sincronización completa de la documentación técnica en `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`.
  - Certificación QA: Backend con 389 pruebas unitarias aprobadas, 95.0% de cobertura en `src/`, 99.0% en `src/api/v1/mcp.py` y complejidad ciclomática Radon Grado A (promedio 2.9, máxima CC <= 5 por función); Frontend con 240 pruebas unitarias aprobadas, 0 errores en `vue-tsc`, 0 errores en `eslint`, formato Prettier verificado y bundle de producción generado en 4.02s.
- **Hito 20 (Suite Corporativa — Config Drift, CIS Hardening, SD-WAN, Rogue DHCP, SLA y CAPsMAN):** COMPLETADO al 100% y certificado en Docker:
  - Detección de Desviación de Configuración (*Config Drift Detection*): Comparador semántico contra Plantilla Maestra (*Golden Baseline*), visor Git Diff unificado interactivo y reversión atómica en 1 clic (*Auto-Revert*) bajo Safe Mode (60s) con registro de auditoría WORM HMAC-SHA256.
  - Orquestador SD-WAN WireGuard Hub & Spoke: Aprovisionamiento dinámico con direccionamiento de interconexión `/31` o `/30`, inserción de peers y failover Multi-WAN recursivo mediante netwatch scripts en RouterOS v7.
  - Auditoría de Seguridad & Endurecimiento CIS Benchmark: Evaluación de las 10 directivas críticas para RouterOS, cálculo de Security Score (0-100), determinación de grado de cumplimiento (A-F) y auto-endurecimiento (*Auto-Hardening*) preventivo.
  - Seguridad L2 & Detección de Rogue DHCP: Inspección de DHCP Snooping en bridges MikroTik, mapeo de puertos de confianza/desconfianza, alertas de servidores rogue con MAC y aislamiento de puerto en 1 clic bajo Safe Mode.
  - Monitor de Cumplimiento de SLA para Enlaces Dedicados: Sondeos de latencia mínima/promedio/máxima/p95/p99, cálculo de jitter RFC 3550, evaluación de umbral SLA contractual y exportador de informes auditables para reclamos de penalización a carriers.
  - Gestión Centralizada de Wi-Fi Corporativo (CAPsMAN / WiFiWave2): Visión general de radios y APs gestionados, orquestación de perfiles SSID (WPA3-Enterprise 802.1X, Invitados, IoT) y telemetría de clientes en tiempo real (RSSI, SNR, fast roaming 802.11r/k/v).
  - Certificación QA: Backend con 381 pruebas unitarias aprobadas y 95.0% de cobertura en `src/`; Frontend con 240 pruebas unitarias aprobadas, 0 errores en `vue-tsc`, 0 errores en `eslint`, 0 advertencias de formato y compilación de producción validada.
- **Hito 19 (Mapas Separados, Telemetría Efímera, Responsive e i18n):** COMPLETADO al 100% y certificado en Docker:
  - Mapa Exclusivo de Clientes/ONUs (`OsmOnuMap.vue` en `/subscribers/map`): Totalmente desacoplado del mapa de infraestructura de routers, con telemetría efímera Zero-Metrics (🟢 < 40ms, 🟠 40-120ms, 🔴 > 20% o timeout), agrupación por caja de empalme / coordenadas coincidentes y spiderfier interactivo.
  - Detección de Caída Masiva (Mass Outage Alert): Monitoreo de umbral dinámico (`tenant.mass_outage_threshold`), alerta visual y sonora reactiva en el Wallboard NOC mediante WebSockets y registro de auditoría WORM inmutable con hash encadenado HMAC-SHA256.
  - Interfaz Responsive Táctica de Campo (`FieldTechMobileView.vue`): Eliminación de la restricción rígida de 480px, layout fluido adaptable a móvil (<768px), tablet (2 columnas) y desktop/laptop (3 columnas con diagnóstico 360° integrado), captura GPS prominente con georreferenciación en la activación de ONUs y canvas de firma digital.
  - Arquitectura Modular de Internacionalización (i18n): Composable `useI18n()` reactivo con diccionarios `es.json` y `en.json`, persistencia en localStorage y botón conmutador táctico en la barra superior del shell.
  - Certificación QA: Backend con 370 pruebas unitarias aprobadas y 95.16% de cobertura; Frontend con 234 pruebas unitarias aprobadas, 0 errores en `vue-tsc`, 0 errores en `eslint` y compilación de producción validada.

---

## ✅ HITO 0: Gobernanza 11X, Infraestructura Docker Inmutable y Fusión Base

> **Archivos Guía:** `docs/specs/00_MASTER_INDEX_AND_11X_GOVERNANCE.md` y `docs/specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **0.1** Estructura del monorepo (`fastapi/`, `vue3/`, `docs/specs/`, `docs/examples/`, `docs/`).
- [x] **0.2** Archivos raíz (`LICENSE` GPL-3.0-only, `.env.example`, `docker-compose.yml`, `.gitignore`, `lefthook.yml`, `commitlint.config.js`, `instalar-hooks.sh`, `auditar-infra.sh`).
- [x] **0.3** Fusión quirúrgica inicial en `fastapi/` (`pyproject.toml`, `tox.ini`, `Makefile`, `docker-compose.qa.yml`, `limpieza.sh`, `locustfile.py`, `scripts/entrypoint.sh`).
- [x] **0.4** Fusión quirúrgica inicial en `vue3/` (`package.json`, `.npmrc`, `vitest.config.ts`, `stryker.conf.json`, `playwright.config.ts`, `lighthouserc.js`, `Makefile`, `docker-compose.qa.yml`, `nginx/default.conf`).

---

## ✅ HITO 1: Esquema PostgreSQL 17, Multi-Tenant RLS, Bóveda y Auditoría WORM

> **Archivos Guía:** `docs/specs/02_DB_SCHEMA_CORE_TENANTS_AND_RLS.md`, `docs/specs/03_DB_SCHEMA_INVENTORY_VAULT_AND_MAINTENANCE.md` y `docs/specs/04_DB_SCHEMA_OPERATIONS_BACKUPS_AND_IMMUTABLE_AUDIT.md`

- [x] **1.1** Configuración de Alembic (`fastapi/alembic.ini`, `fastapi/migrations/env.py`, `script.py.mako`).
- [x] **1.2** Migración `0001_core_tenants_users_rls.py` (Tablas `tenants`, `users`, `user_router_permissions`, los 11 roles y políticas `FORCE ROW LEVEL SECURITY` — `docs/specs/02`).
- [x] **1.3** Migración `0002_inventory_vault_maintenance.py` (Tablas `routers`, `router_tags`, `router_credentials_vault` AES-256-GCM y `maintenance_windows` — `docs/specs/03`).
- [x] **1.4** Migración `0003_operations_backups_immutable_audit.py` (Tablas `approval_requests`, `router_backups`, `config_templates`, `bulk_jobs`, `bulk_job_items`, `notification_channels` y `audit_logs` con trigger WORM `trg_immutable_audit_logs` — `docs/specs/04`).
- [x] **1.5** Modelos SQLAlchemy 2.0 (`src/models/base.py`, `core.py`, `inventory.py`, `operations.py`) y motor de sesión async con inyección de `app.current_tenant_id` (`src/db/session.py`).

---

## ✅ HITO 2: Capa KeyDB Multi-Hilo (Compatible RESP) — Idempotencia, Sesiones Kill-Switch, Pub/Sub y Monitor Zero-Metrics

> **Archivo Guía:** `docs/specs/05_REDIS_KEYS_IDEMPOTENCY_AND_ZERO_METRICS.md`

- [x] **2.1** Cliente y pool de conexión asíncrono compatible con KeyDB / DragonflyDB (`src/redis_layer/client.py`).
- [x] **2.2** Middleware y gestor de Idempotencia HTTP (`Idempotency-Key` UUIDv7 con estados `IN_PROGRESS` / `COMPLETED` y hash SHA-256 del body en `src/redis_layer/idempotency.py`).
- [x] **2.3** Gestor de familias de Refresh Tokens (*Reuse Detection*), registro de sesiones activas e invocación del **Kill-Switch** (`src/redis_layer/sessions.py`).
- [x] **2.4** Máquina de Estados Efímera *Zero-Metrics Storage* (~200 bytes/router en memoria para transiciones `ONLINE`/`OFFLINE`/`DEGRADED_HIGH_LOAD` en `src/redis_layer/zero_metrics_monitor.py`).

---

## ✅ HITO 3: Seguridad Split-Credential, 2FA TOTP, Step-Up Auth y Matriz RBAC (11 Roles)

> **Archivos Guía:** `docs/specs/06_SECURITY_SPLIT_CREDENTIAL_2FA_AND_STEPUP.md` y `docs/specs/07_RBAC_11_ROLES_MATRIX_AND_MAKER_CHECKER.md`

- [x] **3.1** Configuración central tipada (`src/core/config.py`).
- [x] **3.2** Motor criptográfico `Argon2id`, `AES-256-GCM` con `AAD` (`tenant_id|router_id`) y generador TOTP RFC 6238 (`src/core/crypto.py`).
- [x] **3.3** Generación/verificación de cookies `__Host-rg_at` / `__Host-rg_rt` y protección `X-CSRF-Token` firmada con HMAC-SHA256 (`src/core/csrf.py`).
- [x] **3.4** Middleware de cabeceras de seguridad estrictas para cumplimiento OWASP ZAP (`src/core/security_headers.py`).
- [x] **3.5** Servicio de Auditoría Inmutable con cadena hash SHA-256 (`prev_record_hash`) y sanitización `[REDACTED]` (`src/core/audit.py`).
- [x] **3.6** Matriz declarativa de los **11 Roles** + filtro de permisos por router (`src/rbac/policy_matrix.py` — `docs/specs/07`).
- [x] **3.7** Clasificador e interceptor de las 7 categorías críticas **Maker-Checker** (`src/rbac/checker.py` — `docs/specs/07`).

---

## ✅ HITO 4: Conector Asíncrono RouterOS v7 (`/rest/*`), Pinning SSL TOFU y Motor Safe Mode

> **Archivo Guía:** `docs/specs/08_MIKROTIK_REST_V7_CLIENT_TOFU_AND_SAFEMODE.md`

- [x] **4.1** Verificador de huella TLS `SHA-256` (*Trust On First Use* — `PENDING_TOFU`, `TRUSTED_PINNED`, `FINGERPRINT_MISMATCH` en `src/mikrotik/ssl_tofu.py`) con auto-pinning reactivo continuo y autodescubrimiento desatendido de hardware al detectar router running en el monitor de salud (`health_monitor_worker.py`) o al abrir la consola WebFig (`webfig_common.py`).
- [x] **4.2** Cliente HTTP asíncrono `httpx` para RouterOS v7 (`/rest/*`) con soporte de fallback transaccional a `previous_password` (`src/mikrotik/client.py`).
- [x] **4.3** Motor **Safe Mode (*Dead Man's Switch*)** mediante inyección y limpieza de `/rest/system/scheduler` a 60s (`src/mikrotik/safemode.py`).
- [x] **4.4** Normalizadores de tipos de RouterOS v7 (booleanos `"true"`/`"false"`, tiempos y unidades a tipos nativos en `src/mikrotik/normalizers.py`).

---

## ✅ HITO 5: Esqueleto FastAPI, Observabilidad `/metrics` y Endpoints Auth, Usuarios y Kill-Switch

> **Archivos Guía:** `docs/specs/09_BACKEND_PHASE_1_SKELETON_OBSERVABILITY_AND_MIGRATIONS.md` y `docs/specs/10_BACKEND_ENDPOINTS_AUTH_TENANTS_USERS_KILLSWITCH.md`

- [x] **5.1** Aplicación principal `src/main.py` con `prometheus-fastapi-instrumentator` (`/metrics`), `/health`, `/users/me` y registro de middlewares.
- [x] **5.2** Dependencias de inyección (`src/api/deps.py`) y esquemas Pydantic v2 de Autenticación, Tenants, Usuarios y Sesiones (`src/schemas/auth.py`, `users.py`).
- [x] **5.3** Endpoints de Login Multi-Tenant en 2 etapas, enrolamiento/verificación 2FA TOTP, Refresh y Logout (`src/api/v1/auth.py` — `docs/specs/10`).
- [x] **5.4** Endpoints de gestión de Empresas (`src/api/v1/tenants.py`), Usuarios de los 11 roles y matriz de asignación de routers por técnico (`src/api/v1/users.py` — `docs/specs/10`).
- [x] **5.5** Endpoints de Sesiones Activas en tiempo real y ejecución del **Kill-Switch** individual o masivo (`src/api/v1/sessions.py` — `docs/specs/10`).

---

## ✅ HITO 6: Endpoints de Inventario MikroTik, Importador CSV, Bóveda Step-Up (30s) y Rotación

> **Archivo Guía:** `docs/specs/11_BACKEND_ENDPOINTS_INVENTORY_CSV_VAULT_AND_ROTATION.md`

- [x] **6.1** Esquemas Pydantic v2 de Inventario, CSV, Bóveda y Ventanas de Mantenimiento (`src/schemas/inventory.py`).
- [x] **6.2** Endpoints CRUD de Routers MikroTik con autodescubrimiento (`/rest/system/resource`, `routerboard`, `identity`, `package`) y coordenadas OpenStreetMap (`src/api/v1/inventory.py`).
- [x] **6.3** Importador Masivo por CSV en 2 pasos: validación `/import-csv/dry-run` y ejecución `/import-csv/commit`.
- [x] **6.4** Endpoints de Bóveda Criptográfica: revelación con **Step-Up Auth (2FA TOTP en vivo, exclusivo para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`)**, rotación transaccional de clave API y Re-Pin SSL TOFU (`src/api/v1/vault.py`).
- [x] **6.5** Endpoints de Ventanas de Mantenimiento Programadas (`src/api/v1/maintenance.py`).

---

## ✅ HITO 7: Endpoints WebFig Capa 1 (Parte A) — Interfaces, Óptica SFP DDM, VLAN, WireGuard e IP

> **Archivo Guía:** `docs/specs/12_BACKEND_ENDPOINTS_WEBFIG_L1_INTERFACES_AND_IP.md`

- [x] **7.1** Esquemas Pydantic v2 para Interfaces e IP/IPv6 (`src/schemas/webfig_l1_net.py`).
- [x] **7.2** Endpoints de Interfaces generales, Ethernet, test de cable TDR y diagnóstico óptico **SFP/SFP+ DDM** (`tx-power`, `rx-power` dBm y clasificación de salud óptica) (`src/api/v1/webfig_interfaces.py`).
- [x] **7.3** Endpoints de VLAN 802.1Q, Bridges + Ports, WireGuard (Peers + llave pública) y tabla de registro WiFi/Wireless.
- [x] **7.4** Endpoints de IPv4/IPv6 Addresses, Routes (incluyendo balanceo ECMP), ARP, Pools, DHCP Server Leases (con conversión a estático), DNS, IP Neighbors y `/ip/service` (con protección anti-suicidio del puerto `www-ssl`) (`src/api/v1/webfig_ip.py`).

---

## ✅ HITO 8: Endpoints WebFig Capa 1 (Partes B y C) — Firewall, BGP/OSPF, PPPoE, Queues, System y Tools

> **Archivos Guía:** `docs/specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md` y `docs/specs/14_BACKEND_ENDPOINTS_WEBFIG_L1_PPP_QUEUES_SYSTEM_TOOLS.md`

- [x] **8.1** Endpoints de Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, `Connections`) y endpoint de reordenamiento (`move`) protegido por Safe Mode (`src/api/v1/webfig_firewall.py` — `docs/specs/13`).
- [x] **8.2** Endpoints de Routing v7: sesiones/peers `BGP`, prefijos anunciados, `OSPF`, `Routing Tables`, `Routing Rules`, `BFD` y `Filters` (`src/api/v1/webfig_routing.py` — `docs/specs/13`).
- [x] **8.3** Endpoints de PPPoE Active (con corte/reconexión para Soporte N1), PPP Secrets, Profiles y Servidores PPPoE (`src/api/v1/webfig_ppp.py` — `docs/specs/14`).
- [x] **8.4** Endpoints de Control de Ancho de Banda: `Simple Queues` (con `move`) y `Queue Tree` (`src/api/v1/webfig_queues.py` — `docs/specs/14`).
- [x] **8.5** Endpoints de System (`Identity`, `Users`, `Scripts`, `Scheduler` con ocultamiento de `rosgrid_safemode_*`, `Packages`, `Reboot`) y Tools de diagnóstico en vivo (`Ping`, `Traceroute`, `Torch`, `Log`) (`src/api/v1/webfig_system_tools.py` — `docs/specs/14`).

---

## ✅ HITO 9: Motor Universal WebFig Capa 2, Maker-Checker, Backups Diff Git y Acciones Masivas

> **Archivos Guía:** `docs/specs/15_BACKEND_ENDPOINTS_WEBFIG_L2_UNIVERSAL_ENGINE.md` y `docs/specs/16_BACKEND_ENDPOINTS_MAKER_CHECKER_BACKUPS_BULK_UPDATES.md`

- [x] **9.1** Motor Dinámico Universal WebFig Capa 2 (`/webfig/layer2/catalog`, inspector de esquema dinámico, CRUD genérico y bloqueo de rutas prohibidas `FORBIDDEN_L2_PATHS`) (`src/api/v1/webfig_layer2.py` — `docs/specs/15`).
- [x] **9.2** Endpoints de Bandeja de Aprobación **Maker-Checker** (listar, aprobar ejecutando cambio diferido con Safe Mode y rechazar, impidiendo auto-aprobación) (`src/api/v1/approvals.py` — `docs/specs/16`).
- [x] **9.3** Motor de Backups `.rsc`/`.backup` con deduplicación SHA-256, retención de 30 días y comparador **Diff estilo Git (`unified_diff`)** entre backups o contra el estado `LIVE` (`src/api/v1/backups.py` — `docs/specs/16`).
- [x] **9.4** Endpoints de Plantillas (*Golden Configs*), Acciones Masivas Multi-Router (`bulk-jobs`) y Actualizador Centralizado de RouterOS v7 con pre-backup obligatorio (`src/api/v1/bulk_and_updates.py` — `docs/specs/16`).
- [x] **9.5** Endpoints de Consola Forense de Auditoría Inmutable y verificador criptográfico de integridad WORM (`src/api/v1/audit.py` — `docs/specs/16`).

---

## ✅ HITO 10: Multiplexor WebSocket, Workers, Dockerfile, Graphify y Optimización de Alto Rendimiento Backend

> **Archivos Guía:** `docs/specs/17_BACKEND_WEBSOCKETS_LIVE_CHARTS_AND_ALERT_WORKERS.md` y `docs/specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **10.1** Multiplexor WebSocket `/ws/v1/routers/{router_id}/live-telemetry` (activa el poller cuando hay >= 1 operador viendo el router y se detiene al instante cuando `SCARD == 0`).
- [x] **10.2** WebSocket global del Tenant `/ws/v1/tenant/events` (eventos NOC, progreso de trabajos masivos y orden `SESSION_KILLED`).
- [x] **10.3** Los 4 Workers en segundo plano (`src/workers/`): Monitor *Zero-Storage*, Despachador de Alertas Multi-Canal (Telegram Bot, Correo SMTP, Webhook HMAC-SHA256 y NOC), Worker de Backups Nocturnos y Worker de Rotación Automática de Bóveda.
- [x] **10.4** **Cierre de Arquitectura Backend con Graphify (En Docker):** Ejecutar `docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify` dentro de `./fastapi/` para generar `fastapi/graphify-out/GRAPH_REPORT.md` y el grafo AST completo del Backend (`docs/specs/09`, `29`).
- [x] **10.5** **Dockerfile Multi-Stage de Producción Backend (`fastapi/Dockerfile`):** Crear `fastapi/Dockerfile` basado en `sinfallas/base-python-uv:3.15` con soporte `ARG BUILD_DATE`, dependencias `--no-dev`, usuario sin privilegios (`non-root`) y `scripts/entrypoint.sh` (`docs/specs/01`).
- [x] **10.6** **Paquete de Optimización de Alto Rendimiento Backend, DB y KeyDB Multi-Hilo:**
  - Sustituir `redis:7-alpine` por `eqalpha/keydb:alpine` (`keydb-server --server-threads 2` y healthcheck `keydb-cli`) en `docker-compose.yml`, `fastapi/docker-compose.qa.yml` y `docs/specs/01` (documentando `DragonflyDB` como perfil de alta escala).
  - Configurar `ORJSONResponse` como `default_response_class` en `fastapi/src/main.py`, serialización `orjson` en frames WebSocket, desactivación estricta de Swagger/ReDoc/OpenAPI cuando `ROSGRID_ENV == "production"` y activar `--loop uvloop --http httptools` en `fastapi/scripts/entrypoint.sh`.
  - Implementar reutilización de pool `Keep-Alive` TLS (`limits=httpx.Limits(max_keepalive_connections=20, keepalive_expiry=60.0)`) en `src/mikrotik/client.py` y ejecución por lotes con `pipeline()` hacia KeyDB en `src/redis_layer/zero_metrics_monitor.py`.
  - Añadir índice `BRIN` (`ix_audit_logs_created_at_brin` con `postgresql_using='brin'`) sobre `audit_logs(created_at)` en `0003_operations_backups_immutable_audit.py` y re-validar `make qa-lint && make qa-unit`.

---

## ✅ HITO 11: Frontend Vue 3 Base — Zero-Trust, Interceptores, Stores Pinia (`shallowRef`) y Sistema de Diseño WCAG (`Virtual Scroll`)

> **Archivos Guía:** `docs/specs/18_FRONTEND_PHASE_1_SETUP_ZERO_TRUST_AND_INTERCEPTORS.md` y `docs/specs/19_FRONTEND_DESIGN_SYSTEM_ACCESSIBILITY_AND_PERFORMANCE.md`

- [x] **11.1** Configuración base de Vite, TypeScript (`tsconfig.json`), `index.html` y `public/manifest.webmanifest` PWA (`docs/specs/18`, `19`).
- [x] **11.2** Cliente HTTP seguro (`vue3/src/api/httpClient.ts`) con los 4 interceptores: `X-CSRF-Token`, `Idempotency-Key` (`UUIDv7`), rotación transparente de Refresh Token y captura de `202 Accepted` (*Maker-Checker*) (`docs/specs/18`).
- [x] **11.3** Los 6 Stores en Pinia (`useAuthStore`, `useThemeAndLayoutStore` con densidad dual adaptativa `auto`/`compact`/`comfortable`, `useInventoryStore`, `useWebFigStore` con cola de hasta 5 pestañas en RAM `openRouterTabs`, `useLiveTelemetryStore`, `useNocEventsStore`) usando **`shallowRef` para colecciones masivas y buffers de telemetría**, más Vue Router con Guards RBAC para los 11 roles (`docs/specs/18`).
- [x] **11.4** Sistema de diseño de alta densidad (`themes.css` con tema predeterminado `dark` *Tactical NOC Cyan* `#0B0F19`/`#06B6D4`/`#22D3EE`, `light` y `noc-high-contrast` cumpliendo contraste WCAG 2.1 AA y fuentes nativas `tabular-nums`) (`docs/specs/19`).
- [x] **11.5** Los 5 componentes base reutilizables: `RgDataTable.vue` (Densidad Dual `32px` WinBox en PC / `44px` táctil en móvil con **Virtual Scrolling nativo para tablas > 100 filas**, insignias `[D]`/`[X]`/`[I]`/`[R]`, conmutador rápido y Drag & Drop + teclado accesible), `RgCommandPalette.vue` (`Ctrl+K`), `RgSafeModeBanner.vue`, `RgStepUp2FAModal.vue` y `RgResponsiveShell.vue` (Doble contexto + Barra Inferior Fija en Móvil) (`docs/specs/19`).

---

## ✅ HITO 12: Vistas Frontend (Parte A) — Login 2FA, Usuarios/Matriz, Kill-Switch, Inventario OSM y Bóveda

> **Archivos Guía:** `docs/specs/20_FRONTEND_VIEWS_AUTH_USERS_PERMISSIONS_AND_SESSIONS.md` y `docs/specs/21_FRONTEND_VIEWS_INVENTORY_OSM_MAP_CSV_AND_VAULT.md`

- [x] **12.1** Vista `LoginView.vue` en 2 etapas (`tenant_slug` + credenciales -> QR de enrolamiento local o desafío 2FA TOTP) (`docs/specs/20`).
- [x] **12.2** Vistas de Administración de Tenants (`TenantsManagementView.vue`), Gestión de Usuarios de los 11 roles (`UsersAndPermissionsView.vue`) y Modal de Matriz de Asignación de Routers por Técnico (`UserRouterMatrixModal.vue`) (`docs/specs/20`).
- [x] **12.3** Panel en vivo de Sesiones Activas y botón de expulsión **Kill-Switch** (`ActiveSessionsKillSwitchView.vue`) (`docs/specs/20`).
- [x] **12.4** Vista de Inventario MikroTik (`RouterInventoryView.vue`) y componente de Mapa Interactivo 100% gratuito con **Leaflet + OpenStreetMap (`OsmRouterMap.vue`)** (`docs/specs/21`).
- [x] **12.5** Asistente de Importación Masiva CSV en 2 pasos (`CsvOnboardingWizardModal.vue`), Modal de **Bóveda con Step-Up Auth y autodestrucción en memoria a los 30s (`VaultRevealModal.vue`)** y vista de Ventanas de Mantenimiento (`docs/specs/21`).

---

## ✅ HITO 13: Vistas Frontend (Parte B), Endpoint MCP Protegido para IA (`Hermes`/`Claude`), Dockerfiles y Graphify

> **Archivos Guía:** `docs/specs/22_FRONTEND_VIEWS_WEBFIG_CONSOLE_RINGBUFFER_AND_LAYERS.md`, `docs/specs/23_FRONTEND_VIEWS_APPROVALS_DIFF_BULK_NOC_AND_AUDITOR.md`, `docs/specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md` y `docs/specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`

- [x] **13.1** Clase `TelemetryRingBuffer<T>` en memoria RAM (`MAX_POINTS = 5400` para 3 horas a 1 tick/2s con reactividad superficial `shallowRef` y limpieza total en `onBeforeUnmount` al salir del router) (`docs/specs/22`).
- [x] **13.2** Layout de Consola WebFig (`RouterWebFigLayout.vue`), Barra de Pestañas de Trabajo con `<KeepAlive :max="5">` (`RouterWorkspaceTabsBar.vue`) y Dashboard de Gráficas Efímeras estilo WinBox (`RouterLiveDashboardView.vue`) renderizadas sobre **`<canvas>` 2D acelerado con `requestAnimationFrame`** (`docs/specs/22`).
- [x] **13.3** Vistas especializadas de WebFig Capa 1 (`InterfacesAndSfpView.vue`, `FirewallRulesView.vue` con Drag & Drop + Safe Mode, `RoutingBgpOspfView.vue`, `PppAndQueuesView.vue`, `LiveToolsDiagnosticsView.vue`) y Renderizador Universal de Capa 2 (`DynamicLayer2ResourceView.vue`) (`docs/specs/22`).
- [x] **13.4** Bandeja de Aprobaciones Maker-Checker (`ApprovalsInboxView.vue`), Historial de Backups (30 días) y Comparador Visual Lado a Lado estilo Git (`RscGitDiffViewer.vue`) (`docs/specs/23`).
- [x] **13.5** Asistente de Plantillas, Acciones Masivas y Updates de RouterOS (`BulkOperationsAndUpdatesView.vue`), Pantalla Completa **Wallboard NOC (`NocWallboardView.vue`)** con telemetría limpia (depuración de textos redundantes y formateo descriptivo de eventos en español vía `eventFormatter.ts`), Reloj Global Táctico persistente en la Barra Superior (`RgResponsiveShell.vue`) y Consola Forense del **Auditor (`ImmutableAuditLogsView.vue`)** (`docs/specs/23`).
- [x] **13.6** **Cierre de Arquitectura Frontend con Graphify (En Docker):** Ejecutar `docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify` dentro de `./vue3/` para generar `vue3/graphify-out/GRAPH_REPORT.md` y el grafo de componentes/stores del Frontend (`docs/specs/18`, `29`).
- [x] **13.7** **Dockerfile Multi-Stage de Producción Frontend (`vue3/Dockerfile`), `docker-compose.prod.yml` (con KeyDB Multi-Hilo) y Script `build.sh`:** Crear `vue3/Dockerfile` (builder `pnpm build` + runtime `nginx:1.27-alpine` no-root con `ARG BUILD_DATE` y `vue3/nginx/default.conf`), `docker-compose.prod.yml` (usando `eqalpha/keydb:alpine` por defecto y bloque comentado de `DragonflyDB` para alto rendimiento) y el script `build.sh` en la raíz con `docker buildx` (`container-builder`, `tonistiigi/binfmt` y limpieza `prune -af`) (`docs/specs/01`).
- [x] **13.8** **Endpoint MCP Protegido (`POST /api/v1/mcp` JSON-RPC 2.0 Streamable HTTP) para Agentes IA (`Hermes Agent`, `Claude`):**
  - Implementar `fastapi/src/schemas/mcp.py` y `fastapi/src/api/v1/mcp.py` conforme a `docs/specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`, controlado por `ROSGRID_MCP_ENABLED` (`false` por defecto) y `ROSGRID_MCP_RATE_LIMIT_PER_MIN` (`30` req/min en KeyDB), restringido exclusivamente al rol `SERVICE_ACCOUNT` con validación de lista blanca CIDR.
  - Exponer las 8 Tools semánticas de diagnóstico y operación (`rosgrid_list_inventory`, `rosgrid_get_router_health`, `rosgrid_check_sfp_optical_ddm`, `rosgrid_inspect_routing_bgp_ospf`, `rosgrid_run_live_diagnostic`, `rosgrid_compare_config_diff`, `rosgrid_reconnect_pppoe_client` y `rosgrid_propose_network_change` con intercepción obligatoria **Maker-Checker** + **Safe Mode 60s** y registro en **WORM**).
  - Crear suite unitaria `fastapi/tests/test_mcp_endpoint.unit.py` (`make qa-lint && make qa-unit` >= 95% de cobertura) y actualizar `fastapi/graphify-out/GRAPH_REPORT.md` con Graphify en Docker antes del Hito 14.

---

## ✅ HITO 14: Documentación Oficial en `docs/`, Referencia de API, Guía de Integración IA (MCP) y Gobernanza Raíz (Basada en `GRAPH_REPORT.md`)

> **Propósito:** Generar la documentación técnica, operativa, de despliegue, la especificación completa de la API y la guía detallada de integración del servidor MCP para agentes IA (`Hermes`, `Claude`) dentro de `docs/`, más la sincronización de los archivos de gobernanza de la raíz tomando como referencia `fastapi/graphify-out/GRAPH_REPORT.md` y `vue3/graphify-out/GRAPH_REPORT.md`.

- [x] **14.1** `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md`: Requisitos de infraestructura, configuración de variables `.env` (incluyendo `ROSGRID_MCP_ENABLED`, `ROSGRID_INSTALL_DIR`, `POSTGRES_HOST`, `REDIS_HOST`, parámetros CORS y variables de tiempo/retención), generación de llaves criptográficas (`AES-256-GCM`, `JWT`, `CSRF`), arquitectura en memoria con **KeyDB Multi-Hilo por defecto** y guía de activación del **Perfil de Alto Rendimiento con DragonflyDB** para grandes flotas ISP, despliegue con `docker-compose.yml` / `docker-compose.prod.yml`, uso de `build.sh` y auto-migración con `pg_advisory_lock`.
- [x] **14.2** `docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md`: Guía paso a paso con comandos CLI de RouterOS v7.1+ para habilitar `/ip/service/www-ssl`, generar certificado autofirmado para pinning TOFU, permisos mínimos del usuario API y explicación del mecanismo *Safe Mode (Dead Man's Switch)* vía `/system/scheduler`.
- [x] **14.3** `docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md`: Administración de empresas (Tenants), detalle de los **11 roles RBAC**, uso de la matriz de asignación de routers por técnico, consulta de la Bóveda con *Step-Up Auth* (30s) y operación del *Kill-Switch* de sesiones en vivo.
- [x] **14.4** `docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md`: Uso diario de la consola WebFig (Capa 1 y Capa 2 con pestañas `KeepAlive` y densidad adaptativa), gráficas efímeras en vivo estilo WinBox (`RingBuffer`), flujo de aprobaciones *Maker-Checker*, comparador Diff estilo Git de respaldos `.rsc`, importación masiva por CSV, ventanas de mantenimiento y modo **Wallboard NOC**.
- [x] **14.5** `docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md`: Guía exclusiva para el rol **Auditor**, verificación criptográfica de la cadena de custodia inmutable WORM (`audit_logs`), registro de decisión de arquitectura (ADR) sobre la exclusión deliberada de terminal CLI/SSH interactiva libre y diagramas de arquitectura en formato Mermaid extraídos de `graphify-out/GRAPH_REPORT.md`.
- [x] **14.6** `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`: Documentación exhaustiva de todos los endpoints REST (`/api/v1/*`, incluyendo `/api/v1/mcp`) y canales WebSocket (`/ws/v1/*`) de RoSGrid (métodos HTTP, rutas, cabeceras obligatorias `X-CSRF-Token` / `Idempotency-Key`, esquemas JSON de entrada/salida, códigos de estado `200`/`202 Maker-Checker`/`401`/`403`/`409`/`422` y uso con `SERVICE_ACCOUNT`), reemplazando a Swagger/ReDoc que permanecen desactivados en producción (`ROSGRID_ENV=production`).
- [x] **14.7** `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`: Documentación técnica detallada del **Servidor MCP Protegido (`/api/v1/mcp`)** para conectar agentes autónomos e interactivos (**Hermes Agent**, **Claude Desktop / Claude Code** y clientes MCP compatibles): activación mediante `ROSGRID_MCP_ENABLED=true`, provisión de credenciales `SERVICE_ACCOUNT` con restricción CIDR y alcances por router, catálogo completo de las 8 Tools MCP con sus esquemas JSON-RPC 2.0 de entrada/salida, configuración paso a paso en Hermes Agent y Claude, recepción de Webhooks firmados (`HMAC-SHA256`) para diagnóstico NOC 24/7 y gobierno humano de cambios mediante *Maker-Checker* + *Safe Mode*.
- [x] **14.8** **Sincronización de Archivos de Gobernanza en la Raíz:** Revisar y actualizar (asegurando que reflejen KeyDB por defecto, DragonflyDB como perfil opcional de alto rendimiento, el conector MCP protegido y las optimizaciones implementadas) los archivos `README.md`, `INSTALL.md`, `SECURITY.md`, `RESOURCES.md`, `FAQ.md`, `CONTRIBUTING.md` y `CODE_OF_CONDUCT.md`.

---

## ✅ HITO 15: Ejecución de Pruebas y Certificación Estándar QA 11X (Bajo Orden Explícita del Usuario)

> **Archivos Guía:** `docs/specs/24`, `docs/specs/25`, `docs/specs/26`, `docs/specs/27`, `docs/specs/28`, `docs/specs/29` + `fastapi/graphify-out/GRAPH_REPORT.md` + `vue3/graphify-out/GRAPH_REPORT.md`

- [x] **15.1** Catálogo de Mocks RouterOS v7 (`routeros_v7_payloads.py`) y Suite Unitaria Backend completa (`fastapi/tests/**/*.unit.py` con cobertura >= 95% alcanzando 95.03% con 284 tests) (`docs/specs/24`, `25`).
- [x] **15.2** Certificación Estática y Unitaria Backend en Docker (`make qa-lint` con `Ruff`, `Mypy strict`, `Radon` Grado A `CC <= 5` / `MI >= B`, `Bandit`, `Pip-Audit` y `make qa-unit`) (`docs/specs/24`, `25`).
- [x] **15.3** Certificación Dinámica, Contratos, BDD, DAST y Caos Backend en Docker (`Schemathesis`, `Karate Labs`, `OWASP ZAP Baseline`, `py-spy` y `--profile chaos` con `Pumba + Locust + Prometheus`) (`docs/specs/26`).
- [x] **15.4** Suite Unitaria Frontend (`vue3/src/__tests__/*.unit.ts` con Vitest >= 95% en las 4 métricas) y Mutación con `Stryker` en Docker (`make qa-lint`, `make qa-unit`, `make qa-mutation`) (`docs/specs/27`).
- [x] **15.5** Suite E2E, Accesibilidad WCAG 2.1 AA (`@axe-core/playwright` = 0 violaciones + snapshots deterministas), `Lighthouse CI` (`>= 90` / `>= 95` a11y), `Karate UI` en Docker (`make qa-perf`, `make qa-e2e`, `make qa-bdd`) y actualización final de `TESTING.md` (`docs/specs/28`, `29`).

---

## ✅ HITO 15B: Estabilización Operativa en Hardware Real MikroTik RouterOS v7 y Validación Front-Back E2E

> **Validación en Vivo:** CHR QEMU x86_64 / RouterBOARD físico con RouterOS v7.21.5 y suite de 24 contratos automatizados.

- [x] **15B.1** **Diagnóstico de Conectividad y Políticas RouterOS v7.13+:** Corrección del error HTTP 401 provocado por la ausencia de la política `rest-api` en el grupo de usuarios de MikroTik, permitiendo la autenticación efectiva de `rosgrid_agent`.
- [x] **15B.2** **Flujo de Auto-Registro Web de Operadores con Aprobación Maker-Checker:**
  - Implementación de solicitud de acceso web en `LoginView.vue` (`POST /api/v1/auth/register`).
  - Bloqueo 403 preventivo a cuentas no aprobadas.
  - Pestaña de gestión de solicitudes en `UsersAndPermissionsView.vue` con aprobación (`PUT /api/v1/users/{id}/approve`) y asignación de rol por Superadmin.
  - Switch de activación/desactivación en tiempo real en KeyDB (`POST /api/v1/users/registration-toggle`).
- [x] **15B.3** **Resiliencia de Inmutabilidad WORM en Eliminación de Usuarios:** Adaptación de `reject_user` (`DELETE /api/v1/users/{id}/reject`) para aplicar soft-revocación segura si el usuario tiene registros en `audit_logs`, preservando el trigger inmutable de PostgreSQL.
- [x] **15B.4** **Redescubrimiento Dinámico TOFU:** Implementación del botón de redescubrimiento en la grilla de Inventario (`POST /api/v1/inventory/routers/{id}/discover`), detectando en caliente hardware, versión de RouterOS, memoria y huella SSL sin recargar la página.
- [x] **15B.5** **Consola WebFig e Interfaces en Router Real:** Corrección de la lectura de interfaces vivas (10 interfaces detectadas) y telemetría de CPU y memoria desde el endpoint REST real.
- [x] **15B.6** **Visualización Cartográfica OpenStreetMap:** Corrección de directivas CSP en Nginx y dimensionamiento CSS en Leaflet para eliminar el estiramiento vertical infinito.
- [x] **15B.7** **Suite Automatizada de 24 Pruebas de Integración UI-API:** Ejecución dentro del contenedor Docker (`rosgrid_api_local`) de `fastapi/scripts/validar_comunicacion_front_back.py` con 100% de éxito (24 pruebas pasadas | 0 fallidas).

---

## ✅ HITO 16: Gobernanza Modular, Feature Flags y Purga de Datos (Fase 1)

> **Archivos Guía:** `docs/specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md` y `docs/specs/34_TENANT_FEATURE_FLAGS_AND_GOVERNANCE_PANEL.md`

- [x] **16.1** Migración Alembic `0005_tenant_feature_flags_and_technical_qos.py` con atributos booleanos en `tenants` (`isp_module_enabled`, `bgp_looking_glass_enabled`, `sfp_ddm_telemetry_enabled`, `ipfix_analytics_enabled`, `enforce_maker_checker`, `auto_safemode_enforced`, `ai_mcp_integration_enabled`, `nightly_backups_enabled`, `outbound_webhooks_enabled`, `config_drift_monitoring_enabled`, `cis_audit_enabled`, `sdwan_orchestrator_enabled`, `capsman_wifi_enabled`, `sla_tracker_enabled`, `mass_outage_threshold`, `default_locale`).
- [x] **16.2** Refactorización de `subscriber_devices` en PostgreSQL: Purga estricta de nombres, cédulas y datos personales. Identificación técnica exclusiva por `device_serial`, `endpoint_identifier`, router y puerto.
- [x] **16.3** Panel de Feature Flags en Frontend (`TenantsManagementView.vue`): Pestaña táctica *"Módulos & Capacidades"* con switches de alta densidad para conmutación inmediata por tenant por el Superadmin.
- [x] **16.4** Seguridad y Reactividad de Módulos: Dependencia FastAPI `require_feature(flag_name)` que responde HTTP 403 `FEATURE_MODULE_DISABLED`, y adaptación dinámica de `RgResponsiveShell.vue`, `RgCommandPalette.vue` y rutas Vue Router para ocultar módulos inactivos.
- [x] **16.5** Branding Institucional, Footer Global y Enlaces Oficiales:
  - Modificación de `LoginView.vue`: Pie de página discreto y elegante con icono SVG accesible de GitHub enlazando a `https://github.com/tecno-consultores/RoSGrid/`, atribución *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/)"*, versión del sistema y badge de *"Licencia GNU GPLv3"*.
  - Modificación de `RgResponsiveShell.vue`: Pie de página global autenticado en la base del sitio mostrando *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/) • Licencia GNU GPLv3"* e icono de GitHub enlazando al repositorio, en tipografía reducida con ratio de contraste WCAG 2.1 AA.

---

## ✅ HITO 17: QoS Técnico, API de Aprovisionamiento e Idempotencia (Fase 2)

> **Archivo Guía:** `docs/specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md`

- [x] **17.1** Modelo y Endpoints de `BandwidthProfile`: Tasas Up/Down nominales, parámetros de Burst (`burst_down_kbps`, `burst_up_kbps`, `burst_threshold`, `burst_time`), Prioridad (1-8) y colas PCQ / Simple Queues en MikroTik v7.
- [x] **17.2** API de Aprovisionamiento Técnico Idempotente (`Idempotency-Key` UUIDv7 obligatorio):
  - `POST /api/v1/network-services/{id}/isolate` (agrega a lista de firewall `AISLADOS_TECNICO` o conmuta a 64k).
  - `POST /api/v1/network-services/{id}/restore` (retira aislamiento y restaura perfil en caliente).
  - `POST /api/v1/network-services/{id}/change-rate-limit` (modifica límites de cola sin desconectar sesión física).
- [x] **17.3** Despachador de Webhooks Salientes: Worker asíncrono que envía payloads firmados con HMAC-SHA256 ante eventos técnicos de red (`DEVICE_ACTIVATED_GPS`, `DEVICE_ISOLATED`, `DEVICE_RESTORED`, `MASS_OUTAGE_TRIGGERED`).

---

## ✅ HITO 18: Diagnóstico 360°, BGP Looking Glass e IPFIX (Fase 3)

> **Archivos Guía:** `docs/specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md` y `docs/specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md`

- [x] **18.1** Suite de Diagnóstico 360° (`POST /api/v1/diagnostics/endpoint-360`):
  - Ping Multi-MTU (64B, 512B, 1472B) para detección de dispersión de latencia y fragmentación DF-bit.
  - Parser automático de motivos de desconexión en `/log` de RouterOS (`link down`, `peer is not responding`, `user request`, `auth failed`).
  - Muestreo Torch en tiempo real (3 segundos) filtrado por IP/MAC con Top 5 de flujos activos.
- [x] **18.2** Consola BGP Looking Glass Interno: Endpoints `GET /api/v1/bgp/looking-glass/route` y `/advertised` para inspeccionar rutas, AS-Path, comunidades BGP y prefijos exportados a proveedores de tránsito sin dar acceso por SSH.
- [x] **18.3** Detección de Tráfico Anómalo / Flujos IPFIX: Detección de clientes con tasas anormales de PPS o conexiones masivas con botón de mitigación rápida (FastDrop / Blackhole con Safe Mode y auditoría WORM inmutable).

---

## 🗺️ HITO 19: Mapas Separados, Telemetría Efímera, Responsive e i18n (Fase 4)

> **Archivo Guía:** `docs/specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md`

- [x] **19.1** Mapa Exclusivo de Clientes/ONUs (`OsmOnuMap.vue` en `/subscribers/map`): Completamente separado del mapa de routers de infraestructura, con telemetría efímera Zero-Metrics (Verde < 40ms, Naranja 40-120ms o pérdida leve, Rojo timeout).
- [x] **19.2** Alerta de Caída Masiva (Mass Outage Alert): Detección automática en segundo plano de caídas simultáneas > `mass_outage_threshold` (por defecto 10), con alarma visual/sonora en NOC y registro forense en `audit_logs` con hash encadenado HMAC-SHA256.
- [x] **19.3** Corrección de Responsive del Técnico de Calle (`FieldTechMobileView.vue`): Eliminación del contenedor fijo vertical (`max-width: 480px`), maquetación 100% fluida para móvil, tablet y laptop, campo simplificado solo con Serial de ONU, y botón prominente *"📍 Capturar Coordenadas GPS"* al activar.
- [x] **19.4** Arquitectura de Internacionalización (i18n): Base modular con `locales/es.json` y `locales/en.json`, composable `useI18n()` y selector táctico de idioma en barra de herramientas superior.

---

## 🏢 HITO 20: Suite Corporativa — Config Drift, CIS Hardening, SD-WAN, Rogue DHCP, SLA y CAPsMAN

> **Archivo Guía:** `docs/specs/33_ENTERPRISE_FLEET_MANAGEMENT_AND_SECURITY_COMPLIANCE.md`

- [x] **20.1** Detección de Desviación de Configuración (*Config Drift Detection*): Comparador contra Plantilla Maestra (*Golden Baseline Template*), visor de diferencias Git Diff en rojo/verde y botón de remediación en 1 clic (*Auto-Revert*) con Safe Mode y Maker-Checker.
- [x] **20.2** Orquestador SD-WAN WireGuard Hub & Spoke: Generación automática de llaves, direccionamiento `/30` o `/31`, inserción de peers y enrutamiento dinámico OSPF sobre WireGuard con failover multi-WAN recursivo.
- [x] **20.3** Auditoría de Seguridad & Endurecimiento CIS Benchmark para RouterOS: Escaneo de las 10 directivas críticas de ciberseguridad, cálculo de Security Score (0-100) y botón de auto-endurecimiento (*Auto-Hardening*).
- [x] **20.4** Detección de Rogue DHCP & Seguridad de Conmutación: Monitoreo de eventos de DHCP Snooping en switches y bridges MikroTik, alertas al NOC con puerto físico y MAC del intruso, y deshabilitación preventiva de puerto.
- [x] **20.5** Monitor de Cumplimiento de SLA para Enlaces Dedicados: Medición continua de jitter, latencia y pérdida hacia el gateway del carrier con generador de reportes de cumplimiento (PDF/CSV) para reclamos de penalización.
- [x] **20.6** Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2): Orquestación de SSIDs (Corporativo WPA3-Enterprise 802.1X, Invitados aislado y dispositivos IoT) con telemetría de señal RSSI y trazabilidad de roaming 802.11r.

---

## ✅ HITO 21: Servidor MCP Ampliado para Agentes IA y Certificación QA 11X Final

> **Archivos Guía:** `docs/specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`, `docs/specs/24` a `docs/specs/29` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`

- [x] **21.1** Expansión de Tools MCP para Agentes de IA: Nuevas herramientas para sustitución o asistencia técnica autónoma (`rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit`, `rosgrid_run_360_diagnostics`, `rosgrid_query_bgp_looking_glass`, `rosgrid_check_config_drift`, `rosgrid_run_cis_audit`, `rosgrid_detect_mass_outage`).
- [x] **21.2** Actualización de Documentación: Sincronización completa de `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md` con los nuevos contratos.
- [x] **21.3** Certificación Estándar QA 11X en Docker: Cobertura unitaria >= 95% en backend (`sinfallas/base-python-uv:3.15`) y frontend (`sinfallas/base-node-ionic:26`), ejecución de la suite de contratos Front-Back y compilación limpia del bundle de producción.

---

## 📦 HITO 22: Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`build.sh`)

> **Archivo Guía:** `docs/specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **22.1** Auditar los `Dockerfile`, `docker-compose*.yml` e infraestructura con `./scripts/auditar-infra.sh` y escaneo Trivy de imágenes (`CRITICAL,HIGH = 0`).
- [x] **22.2** **Especificación y Endurecimiento de Pruebas Smoke Locales (`probar-prod-local.sh`):** Actualización de especificaciones (`docs/specs/31`), manual operativo (`docs/08`) y bitácora QA 11X (`TESTING.md`) incorporando la ejecución obligatoria de la suite de 24 contratos Front-Back (`validar_comunicacion_front_back.py`), validación del proxy inverso Nginx (`:${UI_PORT}/api/...`), sondeo real JSON-RPC 2.0 MCP (`POST /api/v1/mcp`), supervisión activa de healthchecks y logs de `rosgrid-worker`, verificación de ocultamiento HTTP 404 de Swagger/OpenAPI en producción, pruebas negativas de autenticación (401) y verificación de aislamiento de puertos internos DB/KeyDB.
- [x] **22.5** **Endurecimiento de Seguridad Híbrida (FastAPI + Vue 3) y Protección contra Vectores de Ataque:**
  - Mitigación de Cross-Site WebSocket Hijacking (CSWSH) mediante validación obligatoria de la cabecera `Origin` (`_verify_ws_origin`) previa a la aceptación del WebSocket (`ws.accept()`), rechazando orígenes no autorizados o ausentes en producción con código `4403`.
  - Sanitización de errores `RequestValidationError` (422) de Pydantic en producción, previniendo la enumeración de esquemas, expresiones regulares y nombres internos de columnas.
  - Parametrización segura de contexto de inquilino SQL en el servidor MCP (`set_tenant_context`) con eliminación de cadenas interpoladas crudas.
  - Protección Anti-SSRF en el despachador de webhooks (`is_safe_webhook_url`), bloqueando localhost, redes privadas RFC 1918 y servicios de metadatos de nube (`169.254.169.254`).
  - Límite estricto de carga de archivos (2 MB) en el onboarding CSV para prevenir ataques de agotamiento de memoria RAM.
  - Endurecimiento de CORS en producción con descarte de credenciales ante configuraciones abiertas (`allow_origins=[]`, `allow_credentials=False`).
  - Sincronización de cabeceras de proxy inverso en Nginx para WebSockets (`X-Forwarded-For`, `X-Forwarded-Proto`).
  - Incorporación de plantilla predefinida `Cliente NTP` para configuración masiva automatizada de sincronización horaria en routers MikroTik.
- [x] **22.6** **Asistente de Instalación Standalone Remoto vía curl (`instalar-rosgrid.sh`):** Implementación de modo dual inteligente (local en repositorio vs. remoto standalone en `/opt/rosgrid`), lectura de entrada interactiva desde `/dev/tty` para compatibilidad con tuberías `curl -fsSL ... | bash`, descarga automatizada de `.env.example` y `docker-compose.prod.yml` desde GitHub `main`, generación de secretos criptográficos de 256 bits, permisos 600 y auditoría estática con ShellCheck (0 errores, 0 advertencias).
- [x] **22.7** **Suite de Pruebas BDD E2E Karate Labs para el 100% de la Interfaz Web:** Expansión de `vue3/test/ui_business_flow.feature` a 16 escenarios BDD de extremo a extremo cubriendo la totalidad de vistas y flujos funcionales del sistema (Login & 2FA, Dashboard y Refresco de Flota, Inventario y Búsqueda, WebFig Live y Pestañas KeepAlive, Maker-Checker, Respaldos y Git Diff, Operaciones Masivas y Paquetes, Wallboard NOC, Auditoría Forense WORM, Gestión Multi-Tenant, Matriz RBAC, Kill-Switch de Sesiones, IPAM Dual-Stack, Toolkit de Campo Móvil, Mapa de Abonados/ONUs, y Compliance Corporativo CIS/Drift/SD-WAN), sincronización idéntica en `docs/examples/vue3/test/ui_business_flow.feature` y validación con Vitest (38/38 suites, 262/262 tests) y `vue-tsc` (0 errores).
- [x] **22.8** **Enriquecimiento Visual con Diagramas Mermaid en Toda la Documentación:** Inserción masiva de diagramas de arquitectura, secuencias criptográficas, árboles de decisión y flujos de datos en todos los manuales del sistema (`README.md`, `INSTALL.md`, `SECURITY.md` y `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` hasta `docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md`).
- [x] **22.9** **Investigación Técnica y Hojas de Ruta de Migración a Python 3.15 y Node.js 26 LTS:**
  - `docs/10_REPORTE_INVESTIGACION_PYTHON_3_15.md`: Investigación sobre Free-Threading / No-GIL (PEP 703) Tier-1, Tier-2 JIT, PEP 649 y migración a `sinfallas/base-python-uv:3.15`.
  - `docs/11_REPORTE_INVESTIGACION_NODE_26.md`: Investigación sobre Native Type Stripping, V8 14.x, Temporal API y migración a `sinfallas/base-node-ionic:26`.
- [x] **22.10** **Suite de Pruebas BDD Integral Karate Labs para el 100% de la API REST FastAPI:** Expansión de `fastapi/test/api_test.feature` a 54 escenarios BDD exhaustivos cubriendo todos y cada uno de los 35 submódulos y endpoints de la API REST (Observabilidad, Auth, Multi-Tenant, Usuarios, Sesiones, Inventario, TOFU, Bóveda 2FA, IPAM, QoS, Dispositivos ONU, Servicios de Red, Field Ops, Mantenimiento, WebFig L1/L2, Maker-Checker, Backups, Operaciones Masivas, Notificaciones, WORM, MCP JSON-RPC 2.0, Diagnóstico 360°, BGP Looking Glass, Tráfico IPFIX, Compliance CIS/Drift, SD-WAN, Switching, SLA, WiFi y RBAC), sincronización idéntica en `docs/examples/fastapi/test/api_test.feature` y certificación en `TESTING.md`.
- [x] **22.11** **Migración Integral de Runtime a Python 3.15 y Node.js 26 LTS:** Actualización de `fastapi/Dockerfile` (`sinfallas/base-python-uv:3.15`), `vue3/Dockerfile` (`sinfallas/base-node-ionic:26`), `docker-compose.yml`, `fastapi/docker-compose.qa.yml`, `vue3/docker-compose.qa.yml`, metadatos en `pyproject.toml` (`requires-python = ">=3.15"`) y `package.json` (`engines: { "node": ">=26.0.0" }`), sincronización completa de la bitácora histórica de hitos (Hitos 0 al 22.11) en `TESTING.md`, gobernanza raíz y reportes técnicos `docs/10` y `docs/11`.
- [x] **22.12** **Auditoría Integral de Ciberseguridad y Mitigación de Vulnerabilidades (FastAPI + Vue 3):**
  - Desacoplamiento de `CSRFProtectionMiddleware` para extracción autónoma de JWT desde cookies (`__Host-rg_at` / `rg_at`) y exención de clientes API puros con token Bearer según directrices OWASP.
  - Sanitización estricta anti-XSS mediante `escapeHtml` en popups Leaflet OpenStreetMap (`OsmRouterMap.vue` y `OsmOnuMap.vue`).
  - Validación anti-SSRF integral en el direccionamiento de routers (`validate_router_target_url`) bloqueando loopback, cloud metadata y hostnames de contenedores Docker tanto en la API como en el asistente CSV masivo.
  - Tolerancia a carreras concurrentes (*Grace Period Leeway* de 5 segundos) en rotación de refresh tokens (`rotate_refresh_token`), eliminando falsos positivos de robo por múltiples pestañas.
  - Aislamiento multi-tenant y por operador en `IdempotencyMiddleware` mediante llaves con prefijo `rg:{tenant_id}:{user_id}:idemp:{key}`.
  - Endurecimiento de la expresión regular de CORS en desarrollo a `(localhost|127.0.0.1)`.
- [x] **22.13** **Consolidación de Calidad, Resolución Integral de Diagnósticos y Robustecimiento DevOps:**
  - Normalización y certificación estricta con `markdownlint-cli` (0 errores) y diagramas Mermaid modernos (`flowchart`) en toda la enciclopedia técnica de `docs/specs/` y `docs/`.
  - Tipado estricto en frontend con *Type Narrowing* en `escapeHtml` (`vue3/src/utils/security.ts`) para cumplimiento total de `@typescript-eslint/no-base-to-string` y manejo seguro de objetos con prototipo nulo (`Object.create(null)`).
  - Limpieza arquitectónica en frontend: eliminación de carpeta huérfana de scaffolding `vue3/tests/` consolidando la arquitectura de pruebas unitarias co-localizadas en `src/` (`*.unit.ts`, 38 suites, 267 pruebas unitarias 100% exitosas) y sincronización de scripts en `vue3/package.json`.
  - Extracción de barrera de seguridad de credenciales hardcodeadas al script ejecutable independiente `verificar-secretos.sh` con normalización de sintaxis YAML en `lefthook.yml` y certificación ShellCheck (0 errores, 0 advertencias).
- [x] **22.14** **Generador Visual de Tokens MCP, Supervisión con Kill-Switch y Panel de Canales de Alerta:**
  - Modal interactivo de generación de tokens MCP (`RgMcpTokenModal.vue`) integrado en `UsersAndPermissionsView.vue` para cuentas de servicio (`SERVICE_ACCOUNT`, `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`) con selección de vigencia (30 a 730 días) y snippets para Claude Desktop y Hermes Agent.
  - Supervisión en tiempo real de sesiones de agentes IA en `ActiveSessionsKillSwitchView.vue` con pestañas de filtro, visualización de autoría (`Por: @usuario`), lista blanca CIDR y botón de revocación en caliente (*Kill-Switch*).
  - Endpoint `POST /api/v1/users/{user_id}/mcp-token` con firma criptográfica JWT HS256, registro en KeyDB (`active_sessions`) y auditoría inmutable WORM.
  - Sincronización del script CLI `generar_token_mcp.py` con el registro de sesiones activas.
  - Implementación del componente `NotificationChannelsPanel.vue` integrado como 7ª pestaña en `EnterpriseComplianceView.vue` para administración completa y despacho de pruebas (`POST /{id}/test`) de canales de Telegram, SMTP y Webhooks cifrados en AES-256-GCM.
  - Certificación QA 11X en Docker: 406 pruebas backend aprobadas (95% cobertura), 278 pruebas frontend aprobadas en 40 archivos, 0 errores en ESLint y Vue-TSC.
- [x] **22.15** **Skill Oficial de Operaciones NOC para Agentes IA (`rosgrid-noc-operator`):**
  - Creación de la Skill portable en `.agents/skills/rosgrid-noc-operator/SKILL.md` con 5 Playbooks SOP (Diagnóstico 360°, cortes PON, flapping BGP/OSPF, CIS/drift, aislamiento).
  - Catálogo de herramientas MCP en `references/mcp_tools.md`, banderas de RouterOS v7 en `references/routeros_flags.md` y configuraciones para Claude Desktop y Hermes Agent.
  - Distribución multicanal: descarga remota en `instalar-rosgrid.sh` (`/opt/rosgrid/skills/`), botones en `RgMcpTokenModal.vue` y endpoint público `GET /api/v1/mcp/skill`.

---

## ✅ HITO 23: Automatización de Flota, Topología L2, Syslog Efímero, Exportador Prometheus y Seguridad CVE

> **Archivos Guía:** `docs/specs/35_FLEET_AUTOMATION_TOPOLOGY_L2_SYSLOG_AND_PROMETHEUS.md` y `docs/12_DISENO_TOPOLOGIA_L2_SYSLOG_Y_AUTOMATIZACION.md`

- [x] **23.1** **Especificación Técnica y Arquitectura de Datos (`docs/specs/35` y `docs/12`):**
  - Definición integral de estructuras de datos en memoria, preservando estrictamente la premisa *Zero-Metrics Storage* (cero almacenamiento de series temporales en PostgreSQL 17).
  - Especificación del Grafo Acíclico Dirigido (DAG) para dependencias de energía PoE, ordenamiento inverso de actualización (Hojas PD primero, Raíces PSE al final) y circuito de corte de emergencia *Fleet Safety Stop* (umbral 1% de fallos post-reinicio).
  - Definición del modelo de cruce local de boletines CVE (`cve_catalog_ros.json`) con cero exposición de telemetría a la nube exterior.
  - Diseño del receptor asíncrono Syslog en puerto no privilegiado 5514 (UDP/TCP) con RingBuffer volátil en KeyDB (`MAXLEN 500`) y filtro de eventos críticos en vuelo (*linkDown*, *bgp drop*, *login attack*).
  - Diseño del puente de métricas hacia Prometheus (`GET /api/v1/metrics/fleet`) autenticado por token, habilitando dashboards en Grafana sin saturación de disco local.
- [x] **23.2** **Plantilla Estandarizada para Enrolamiento Masivo de Syslog RouterOS v7:**
  - Creación del script predefinido para `/system/logging/action` y `/system/logging` adaptable con variables `{{rosgrid_server_ip}}` y `{{rosgrid_syslog_port}}` (5514) incorporado como preset oficial `SYSLOG_CENTRALIZADO_ROSGRID` en backend (`_DEFAULT_STARTER_TEMPLATES`) y frontend (`PREDEFINED_TEMPLATES` / `ConfigTemplateEditorModal.vue` / `BulkOperationsAndUpdatesView.vue`) para despliegue masivo y seguro bajo Safe Mode.
- [x] **23.3** **Ampliación del Servidor MCP y Skill Oficial (`rosgrid-noc-operator`):**
  - Incorporación al diseño del servidor MCP de 4 nuevas herramientas semánticas: `rosgrid_get_l2_topology`, `rosgrid_check_fleet_cves`, `rosgrid_get_recent_syslog` y `rosgrid_execute_poe_aware_upgrade` (total 18 herramientas).
  - Actualización de la Skill `.agents/skills/rosgrid-noc-operator/SKILL.md` incorporando SOP-6 (Triaje de caídas de enlace vía Syslog) y SOP-7 (Planificación PoE-Aware con Safety Stop).
  - Sincronización idéntica en el catálogo global de Antigravity (`~/.gemini/config/skills/rosgrid-noc-operator/`).
- [x] **23.4** **Implementación Backend & Modelos:**
  - Migración Alembic `0007_fleet_automation_l2_syslog_flags.py` con 4 feature flags tácticos en `Tenant`.
  - Catálogo local base de CVEs (`cve_catalog_ros.json`) enriquecido a 23 firmas oficiales de RouterOS v7, motor semver `cve_matcher.py` y sincronizador dinámico `POST /api/v1/inventory/cves/sync` contra MikroTik Security Advisories (`https://mikrotik.com/supportsec`) y búsqueda de registros NIST NVD.
  - Colector Syslog efímero UDP/TCP 5514 BSD (`syslog_collector.py`) con RingBuffer KeyDB (500 eventos por router, 0 persistencia en Postgres) y endpoint de plantilla `/api/v1/routers/syslog/template`.
  - Motor de topología física Layer 2 (`topology_l2.py`) con detección canónica de anillo mediante priorización estricta de LLDP punto a punto (IEEE 802.1AB descartando la inundación MNDP en bridges/ether1) y normalización regex de interfaces compuestas de RouterOS (`ether3,bridge-anillo` a `ether3`), detección PoE PSE/PD, endpoint `/api/v1/topology/l2` y caché KeyDB de 60s.
  - Exportador Prometheus OpenMetrics `/api/v1/metrics/fleet` sin almacenamiento en base de datos.
  - Orquestador de actualizaciones masivas PoE-aware en orden topológico inverso con Safety Stop automático del 1%.
  - Expansión del servidor MCP a 20 herramientas (`rosgrid_get_l2_topology`, `rosgrid_check_fleet_cves`, `rosgrid_get_recent_syslog`, `rosgrid_execute_poe_aware_upgrade`).
  - Suite de pruebas de contratos y BDD en Karate Labs (`fastapi/test/api_test.feature` y `docs/examples/fastapi/test/api_test.feature`, Escenarios 55-61) y 23 tests unitarios Pytest en Docker (100% pasando, Grado A Radon CC <= 5, 0 errores Mypy Strict).
- [x] **23.5** **Implementación Frontend (Vue 3 + Pinia):**
  - Vista interactiva de Topología L2 con Canvas 2D táctica (`L2TopologyView.vue`), renderizado a 60 FPS con Pan/Zoom, badges de PoE (Watts), indicadores LED de estado Online/Offline, drawer táctico de detalles y fallback accesible para screen readers (`role="region"`).
  - Matriz de Vulnerabilidades CVE táctica (`FleetCveMatrix.vue`), 4 tarjetas KPI evaluadas (Evaluados, Vulnerables, Críticos, Versión Recomendada), franja táctica prominente de estado de caché 24 horas y gobernanza de boletines con badge dinámico, filtro reactivo por severidad (CRITICAL/HIGH/MEDIUM/LOW), sincronización remota contra MikroTik Security Advisories (`https://mikrotik.com/supportsec`) y NIST NVD con enlaces oficiales accesibles y botón directo a remediación masiva.
  - Insignia y botón de acceso directo `[ 🛡️ Matriz de CVEs ]` en la tabla de inventario (`RouterInventoryView.vue`).
  - Terminal de eventos Syslog en vivo en la consola WebFig del router (`RouterSyslogTerminalView.vue`), lectura de RingBuffer efímero en KeyDB (UDP/TCP 5514), badges tácticos de severidad (CRIT, WARN, INFO), auto-scroll inteligente y modal con script CLI de enrolamiento MikroTik.
  - Asistente de actualización masiva con conmutador *PoE-Aware* y selector de umbral *Safety Stop* (1%, 2%, 5%) (`BulkOperationsAndUpdatesView.vue`).
  - Menú lateral WebFig v7 actualizado con enlace directo a Syslog Live RingBuffer (`RouterSidebarMenu.vue`) y barra de navegación responsive global con Topología L2 y CVEs (`RgResponsiveShell.vue`).
  - Suite de pruebas de contratos y BDD en Karate Labs UI (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`, Escenarios 17-20) y 17 tests unitarios Vitest en Docker (100% pasando, 0 violaciones ESLint/SonarJS, 0 errores TypeScript strict).
- [x] **23.6** **Certificación Integral QA 11X Pre-Lanzamiento y Validación Local de Producción:**
  - Auditoría de Shell Scripts con ShellCheck (0 errores, 0 advertencias en todos los scripts `.sh`).
  - Backend QA (`sinfallas/base-python-uv:3.15`): 463 pruebas unitarias aprobadas al 100% en 29.09s, 95.11% de cobertura de código real (`--cov-fail-under=95`), Ruff check y format sin desviaciones en 159 archivos, Mypy strict (0 errores en 114 archivos), Bandit SAST (0 problemas de seguridad en 19.941 líneas) y pip-audit (0 vulnerabilidades conocidas en dependencias de producción y desarrollo).
  - Frontend QA (`sinfallas/base-node-ionic:26`): 297 pruebas unitarias aprobadas al 100% en 43 suites con Vitest, vue-tsc (0 errores de tipos TypeScript) y compilación de producción con Vite limpia en 3.99s.
  - Validación de Producción Local (`./scripts/probar-prod-local.sh`): 6 fases completadas exitosamente al 100% (construcción de imágenes locales, healthchecks de contenedores en aislamiento, pruebas sintéticas HTTP, endpoints de documentación 404 estricto, fail-closed 401, Bearer token MCP, invocación JSON-RPC 2.0 y 26/26 contratos Front-Back validados con `validar_comunicacion_front_back.py`).
  - Verificación de secretos (`./scripts/verificar-secretos.sh`): Árbol de trabajo auditado con 0 credenciales ni tokens expuestos.
- [x] **23.8** **Refactorización Táctica del Centro de Mando, Menú Desplegable de Usuario y Gestión de Seguridad:**
  - Depuración del Centro de Mando (`DashboardHomeView.vue`): remoción del término anglosajón redundante *"Mission Control"*, erradicación del tag estático *"Tactical NOC v1.0"*, eliminación del indicador superfluo *"NOC EN VIVO"*, simplificación del reloj operativo a una sola lectura y supresión de prefijos de organización redundantes.
  - Despliegue del menú táctico de usuario en `RgResponsiveShell.vue` disparado por el `username` del operador autenticado: selectores en caliente de formato horario (24 Horas vs 12h AM/PM), tema gráfico (Oscuro, Claro, NOC) e idioma (ES/EN); acciones de auto-gestión (Cambio de Clave, Reset 2FA, Token MCP) y botón de cierre de sesión al pie.
  - Enlace del logotipo y marca *"RoSGrid"* directamente al Centro de Mando (`/`).
  - Paridad estricta y no regresión: preservación de accesos en el módulo de Usuarios y RBAC (`/users`), incorporando el modal `ChangePasswordModal.vue` mediante el botón `[ 🔑 Clave ]`.
  - Backend seguro `POST /api/v1/users/change-password` con verificación de contraseña actual mediante `argon2id`, soporte de reseteo administrativo y auditoría inmutable WORM (`USER_SECURITY` / `CHANGE_PASSWORD`).
  - Certificación 11X en Docker efímero: 319 pruebas Vitest aprobadas al 100% en 45 suites, 0 errores en `vue-tsc --noEmit`, 12 pruebas Pytest aprobadas al 100% y bundle de producción generado en 3.69s.
- [x] **23.9** **Refinamiento de Inventario MikroTik, Alineación de Roles, Plantilla CSV y Soporte i18n WebFig:**
  - Depuración de cabeceras de Inventario (`RouterInventoryView.vue` y catálogos `es.json` / `en.json`): eliminación del sufijo redundante *" — Flota MikroTik"*, normalizando el título a *"Inventario de Equipos"* / *"Equipment Inventory"*.
  - Alineación pixel-perfect de campos y botón en el modal de personalización de roles de red (`ManageNetworkRolesModal.vue`): corrección de desfase vertical, estandarización de alturas a 38px, etiquetas de 16px con spacer y reubicación de texto de ayuda.
  - Asistente de importación masiva CSV (`CsvOnboardingWizardModal.vue` y `fastapi/src/api/v1/inventory.py`): resolución de archivo corrupto mediante nuevo endpoint `GET /api/v1/inventory/template-csv` emitiendo MIME `text/csv; charset=utf-8` con BOM UTF-8 y fallback frontend libre de caracteres residuales.
  - Internacionalización completa y reactiva de la Consola WebFig (`RouterSidebarMenu.vue`, `RouterContextHeader.vue`, `RouterWorkspaceTabsBar.vue`, `RouterLiveDashboardView.vue` y locales `es.json` / `en.json`): soporte en caliente de cambio de idioma a inglés sin recargar el navegador ni perder pestañas.
  - Reloj operativo del Centro de Mando sin segundos (solo formato `HH:MM` en 24 Horas o 12h AM/PM reactivo ante cambios de preferencia e idioma).
  - Internacionalización dinámica del menú desplegable de usuario (`user_menu.*`) y enlaces del riel lateral (`nav.l2_topology` / `nav.cve_matrix`).
  - Certificación 11X en Docker: 333 pruebas Vitest aprobadas (100% en 46 suites), 17 pruebas Pytest de inventario/CSV aprobadas (100%), 0 errores en `vue-tsc --noEmit`, 26/26 contratos front-back y validación visual multi-pantalla con navegador.
- [x] **23.10** **Motor de Ejecución en Flota para Aprobaciones Masivas Maker-Checker (`approvals.py`, `bulk_and_updates.py`, `ApprovalsInboxView.vue`):**
  - Despachador masivo en flota `execute_bulk_job_on_fleet` que conecta mediante `MikrotikRestClient` a cada router objetivo empleando credenciales de la bóveda AES-256-GCM.
  - Ejecución diferida automática al aprobar (`approve_request`): si la solicitud es `BULK_MULTI_ROUTER_EXECUTION`, ejecuta la plantilla Golden Config sobre los routers, actualiza `BulkJob` y `BulkJobItem`, e inyecta el `execution_result` estructurado.
  - Manejo de endpoints singulares en RouterOS v7: fallback automático de `PATCH` a `POST <endpoint>/set` para recursos de configuración única (ej. `/system/ntp/client`, `/ip/dns`).
  - Panel visual de resultados en frontend (`ApprovalsInboxView.vue`): despliegue del resumen de ejecución en tiempo real en la pestaña de solicitudes "Aprobadas y Ejecutadas".
- [x] **23.11** **Robustecimiento y Paridad de la Consola WebFig L1 Bridge & Safe Mode (`webfig_interfaces.py`, `webfig_l1_net.py`, `BridgeView.vue`):**
  - Soporte de configuración de Spanning Tree Protocol (`protocol_mode`) y validación de puertos (`ingress_filtering`) en esquemas Pydantic v2 estrictos (`BridgeCreateRequest`, `BridgeUpdateRequest`, `BridgePortCreateRequest`).
  - Mapeo nativo de parámetros de puente a la API REST de RouterOS v7 (`protocol-mode`, `vlan-filtering: "yes"/"no"`).
  - Cierre instantáneo del modal de creación en la consola WebFig y activación transparente del Dead Man's Switch (Safe Mode de 60 segundos).
  - Certificación 11X en Docker: 7/7 pruebas unitarias de endpoints WebFig aprobadas al 100%, 0 errores de tipado `mypy`, 0 errores `ruff` y verificación de creación en vivo en equipos CHR MikroTik.
- [x] **23.12** **Indicador Táctico de Disponibilidad de API (Heartbeat/Ping) y Caché Anti-Thundering Herd:**
  - Caché en memoria de 5.0 segundos con cerrojo `asyncio.Lock` en `GET /health` en producción para absorber ráfagas concurrentes de sondeo sin consultar repetidamente PostgreSQL ni KeyDB, con soporte de parámetro `?force=true`.
  - Interceptor de monitoreo pasivo en `httpClient.ts` emitiendo `rosgrid:api-health-event` con latencia calculada, permitiendo al frontend actualizar el estado sin llamadas HTTP adicionales mientras haya actividad normal.
  - Store `useApiHeartbeatStore.ts` con integración `BroadcastChannel('rosgrid_api_heartbeat')`, pausa automática por `Page Visibility API` (`document.hidden`) y sondeo en reposo a 45s con `AbortController` (timeout 4s).
  - Componente táctico `RgApiHealthBadge.vue` con dot semántico pulsante (`ONLINE`, `OFFLINE`, `DEGRADED`, `CHECKING`), popover interactivo con diagnóstico en vivo de backend/BD/KeyDB y botón de reintento forzado, integrado en la barra superior de `RgResponsiveShell.vue` y en la cabecera de `LoginView.vue`.
  - Corrección de enrutamiento Nginx (`location /health`), alias estandarizado `/api/v1/health` en FastAPI, validación estricta de `Content-Type` JSON y diagnósticos de conectividad claros en español.
  - Cobertura 11X certificada: 3 pruebas unitarias Pytest dedicadas (`test_health_cache.unit.py`), 33 pruebas Vitest en frontend, Escenario 1b en Karate API y Escenario 25 enriquecido en Karate UI, 100% sincronizados con `docs/examples/`.
- [x] **23.13** **Reorganización Estructural del Repositorio y Gobernanza Centralizada:**
  - Centralización de los 7 scripts operativos raíz en el nuevo directorio `scripts/` (`auditar-infra.sh`, `build.sh`, `instalar-hooks.sh`, `instalar-rosgrid.sh`, `limpieza.sh`, `probar-prod-local.sh`, `verificar-secretos.sh`), con rutas internas normalizadas (`SCRIPT_DIR`, `REPO_ROOT`).
  - Consolidación y reubicación de manuales técnicos de la raíz (`INSTALL.md`, `FAQ.md`, `RESOURCES.md`) dentro de `docs/`.
  - Actualización exhaustiva de configuraciones CI/CD (`lefthook.yml`), directivas de IA (`AGENTS.md`, `.agents/rules/`, `.agents/skills/`), manuales (`docs/`), especificaciones arquitectónicas (`docs/specs/`) e índices maestros.
- [x] **23.14** **Integración de Documentación Oficial de MikroTik RouterOS v7 en el Servidor MCP (Grounding IA):**
  - Especificación formal `docs/specs/36_MCP_OFFICIAL_MIKROTIK_DOCS_GROUNDING.md` para ingesta segura y contextual del estándar abierto `https://manual.mikrotik.com/llms.txt` y `docs/*.md`.
  - Diseño de protección anti-SSRF innegociable con whitelist estricta a `manual.mikrotik.com` y límites de tamaño (1 MB por tópico / 2 MB índice).
  - Mecanismo de caché inteligente en KeyDB (`mcp:docs:mikrotik:index` con TTL 24h y `mcp:docs:mikrotik:page:{hash}` con TTL 7d) para cero latencia (< 5ms) y resiliencia offline.
  - Expansión de herramientas MCP a 22 tools: `rosgrid_search_mikrotik_docs` (búsqueda en índice oficial) y `rosgrid_get_mikrotik_doc_topic` (obtención de Markdown limpio) para erradicación de alucinaciones sintácticas v6 vs v7.
  - Actualización de manual `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md` y Skill oficial `.agents/skills/rosgrid-noc-operator/SKILL.md` (nuevo SOP-8 y catálogo ampliado a 22 tools).
- [x] **23.15** **Sintaxis Canónica RouterOS v7 e Idempotencia en Acciones Masivas (`SNMP_V2C_MONITOREO_NOC` y `SYSLOG_CENTRALIZADO_ROSGRID`):**
  - Corrección de endpoint singular de SNMP en RouterOS v7 REST hacia `POST snmp/set` con payload `{"enabled": "yes"}`.
  - Corrección de acción en `/system/logging/action` con nombre alfanumérico estricto `rosgridsyslog` (restringido por RouterOS v7 a letras y números sin guiones) y parámetros oficiales `remote-log-format: syslog` y `syslog-facility: daemon`.
  - Idempotencia en despacho de pasos (`_execute_single_step`): conmutación a `PATCH` ante acciones existentes, tolerancia a direcciones duplicadas en NTP y resolución dinámica de comunidad SNMP default.
  - Sincronización en base de datos PostgreSQL (`config_templates`), pruebas unitarias al 100% en backend (`test_operations_endpoints_full.unit.py`) y frontend (`ConfigTemplateEditorModal.unit.ts`), y nuevos escenarios BDD en Karate Labs: Escenarios 70 y 71 en API y Escenario 27 en UI (`docs/examples/`).
- [x] **23.16** **Auditoría Sintáctica Exhaustiva y Estandarización de Interacciones con MikroTik RouterOS v7:**
  - Auditoría sistemática de cada módulo y función que interactúa con la API REST de RouterOS v7 (`bulk_and_updates.py`, `webfig_*.py`, `health_monitor_worker.py`, `telemetry_multiplexer.py`, `mcp.py`, `templatePresets.ts`).
  - Corrección de endpoints singulares canónicos: `system/ntp/client/set` (POST) y `ip/dns/set` (POST) en plantillas y presets.
  - Verificación en vivo en routers CHR reales: monitoreo de interfaces SFP (`/interface/ethernet/monitor`), reseteo de contadores de firewall (`/reset-counters-all`), vaciado de caché DNS (`/ip/dns/cache/flush`), ejecución de scripts (`/system/script/run`) y optimización de telemetría de interfaces mediante query param `?.proplist=...`.
  - Certificación 11X multi-capa: 8/8 tests backend, 10/10 tests frontend, 0 errores en `vue-tsc`, 0 errores en `ruff`, 26/26 contratos front-back y nuevos escenarios Karate Labs: Escenario 72 en API y Escenario 28 en UI sincronizados en `docs/examples/`.
- [x] **23.17** **Idempotencia en Reglas de Syslog, Detección Continua en Inventario y Consola Syslog Live:**
  - Idempotencia preventiva en `_execute_single_step` de operaciones masivas: consulta previa de reglas en `/system/logging` para evitar duplicar reglas idénticas (misma acción y mismo set de tópicos), erradicando la duplicación en routers MikroTik. Deduplicación y limpieza en vivo realizada en routers de prueba (`r1`, `r2`, `r3`).
  - Detección continua de Syslog en `health_monitor_worker.py`: verificación periódica de presencia de la acción `rosgridsyslog` en el router y persistencia en KeyDB (`rg:{tenant}:router:{id}:syslog:configured`), eliminando el falso negativo `⚪ Sin Syslog` en el inventario para routers que no emiten logs continuos.
  - Corrección de límite de eventos en `syslog.py` (ampliado de 100 a 500) para resolver el error HTTP 422 generado por la petición del frontend (`limit=200`), paridad de contrato con campos `total_events` y `critical_count` en `schemas/syslog.py`, y exposición de puerto `5514/udp` en worker.
  - Certificación 11X multi-capa: 33/33 tests backend en `test_hito23_cve_and_syslog.unit.py`, 5/5 tests frontend en `routerSyslogTerminalView.unit.ts`, 26/26 contratos front-back y nuevos escenarios Karate Labs: Escenarios 73, 74 y 75 en API y Escenario 29 en UI sincronizados en `docs/examples/`.
- [x] **23.18** **Robustecimiento de Scripts de Limpieza, Purga de Residuos `.venv` y Blindaje Global de `.gitignore` y `.dockerignore`:**
  - Actualización integral de `scripts/limpieza.sh` y `docs/examples/fastapi/limpieza.sh` con eliminación de entornos virtuales residuales (`.venv/`, `venv/`), doble capa de purga de bytecode `__pycache__` con contenedor Docker de rescate y depuración de caché intermedia de Graphify (`graphify-out/cache/`).
  - Normalización determinista de permisos de usuario (`chown -R $(id -u):$(id -g)`) al final del ciclo de limpieza, eliminando bloqueos de permisos y candados gráficos en Nautilus sobre archivos versionados como `fastapi/uv.lock`.
  - Actualización exhaustiva de `.gitignore` y estandarización de `fastapi/.dockerignore` y `vue3/.dockerignore` con exclusiones recursivas globales (`**/venv/`, `**/.venv/`, `**/__pycache__/`, `**/.pytest_cache/`, `**/.mypy_cache/`, `**/.ruff_cache/`, `**/.uv/`, `**/.stryker-tmp/`, `**/graphify-out/`, etc.) para agilizar la transferencia del contexto de compilación en Docker.


- [x] **23.19** **Auditoría Integral y Corrección de Rutas en Scripts Bash y Barrera Pre-commit (`scripts/`, `lefthook.yml`):**
  - Corrección de modo dual en `scripts/instalar-rosgrid.sh`: resolución determinista de `REPO_ROOT` con `cd "${REPO_ROOT}"` al detectar `.env.example` y `docker-compose.prod.yml`, eliminando falsos positivos de modo remoto al invocar desde `scripts/`.
  - Detección dual de la Skill `rosgrid-noc-operator` en modo local (`.agents/skills/rosgrid-noc-operator`) y remoto (`skills/rosgrid-noc-operator`).
  - Sincronización de contratos Front-Back en `scripts/probar-prod-local.sh`: actualización de 24 a **26 contratos validados** (`26/26 contratos validados`) tras la incorporación de contratos 25 y 26 en Hito 23.
  - Estandarización de licencias `SPDX-License-Identifier: GPL-3.0-only` y flags `set -euo pipefail` en `scripts/auditar-infra.sh`, `scripts/build.sh` e `scripts/instalar-hooks.sh`.
- [x] **23.20** **Corrección de Sintaxis Canónica RouterOS v7 para Generación y Firma de Certificados SSL TOFU (`README.md`, `docs/INSTALL.md`, `docs/02`):**
  - Incorporación de la creación y autofirma previa de la CA local (`rosgrid-ca` con `key-usage=key-cert-sign,crl-sign`) requerida por RouterOS v7 antes de emitir un certificado de servidor.
  - Firma explícita de `rosgrid-tofu-cert` con `ca="rosgrid-ca"`, erradicando el error `failure: ca not found`.
  - Estandarización unificada de nomenclatura de certificados (`rosgrid-ca`, `rosgrid-tofu-cert`) y usuario canónico de servicio `rosgrid_agent` en toda la documentación y guías de puesta en marcha.
- [x] **23.21** **Sincronización Automática de Boletines CVE con Caché de 24 Horas y Forzado Manual:**
  - Auto-sincronización transparente al ingresar por primera vez en el día a la Matriz de CVEs (`GET /api/v1/inventory/cves`) si no existe o expiró la clave de metadatos en KeyDB (`rg:cve:sync_meta`, TTL 86400s).
  - Reutilización eficiente de caché local en memoria para los siguientes usuarios durante la jornada (`is_cache_fresh: true`, `auto_synced: false`), evitando peticiones remotas redundantes.
  - Forzado de sincronización manual vía `POST /api/v1/inventory/cves/sync` que renueva el TTL a 24 horas y actualiza el catálogo de firmas.
  - Barra táctica en `FleetCveMatrix.vue` con badge de estado de caché (`Caché 24h Vigente (expira en Xh Ym)`), punto luminoso pulsante, fecha de última descarga y notificación contextual al auto-sincronizar.
  - Cobertura 11X certificada: 35 pruebas unitarias Pytest en backend (`test_hito23_cve_and_syslog.unit.py`), 9 pruebas unitarias Vitest en frontend (`fleetCveMatrix.unit.ts`), Escenario 76 en Karate API y Escenario 30 en Karate UI, 100% sincronizados con `docs/examples/`.
- [x] **23.22** **Auto-Descubrimiento y Sincronización Masiva de IPAM Dual-Stack (Pools DHCP, Leases e Interfaces de Flota):**
  - Descubrimiento exhaustivo de tablas `/ip/pool`, `/ip/dhcp-server`, `/ip/dhcp-server/network`, `/ip/dhcp-server/lease` e `/ip/address` mediante cliente MikroTik con credenciales descifradas de la bóveda AES-256-GCM.
  - Auto-descubrimiento automático en primer acceso a `GET /api/v1/ipam/prefixes` cuando no existen prefijos registrados en base de datos.
  - Nuevo endpoint masivo `POST /api/v1/ipam/sync-all` para sincronizar toda la flota en un paso.
  - Coerción robusta en esquemas Pydantic v2 (`IPAMPrefixResponse`, `IPAMAddressResponse`) con `@field_validator(mode="before")` para conversión incondicional de objetos `IPv4Network`/`IPv4Address` INET a cadenas de texto.
  - Visualización táctica prominente de rangos IPv4 en `IpamPrefixTable.vue` con badge `🎯 <rango_inicio> - <rango_fin>`, indicador de utilización porcentual calculado, tag `POOL`, botón `[ 🔄 Sincronizar Flota (DHCP) ]` y botón de flota en `IpamManagementView.vue`.
  - Cobertura 11X certificada: 5 pruebas unitarias backend (`test_ipam_and_field_ops.unit.py`), 5 pruebas unitarias Vitest (`useIpamStore.unit.ts`), 0 errores en `vue-tsc`, ESLint, Ruff y Mypy, Escenario 77 en Karate Labs API y Escenario 31 en Karate Labs UI.
- [x] **23.23** **Arquitectura Bimodal del Mapa de Red, Infraestructura Pasiva (Cajas NAP) y Rediseño Táctico de Operaciones de Campo:**
  - Especificación formal `docs/specs/37_BIMODAL_NETWORK_MAP_AND_FTTH_FIELD_OPS.md` y manual operativo `docs/13_MANUAL_MAPA_RED_BIMODAL_Y_OPERACIONES_CAMPO.md` completados.
  - Modelo de datos e infraestructura pasiva: nueva tabla `optical_boxes` (código, marca, capacidad 8/16/24, splitter ratio, potencia dBm, anclaje, coordenadas) con RLS multi-tenant y relación con `subscriber_devices` (`optical_box_id`, `optical_box_port`, `rx_optical_power_dbm`, `is_custom_coordinates`). Migración Alembic `0010_optical_boxes_ftth.py` aplicada con paridad ORM 100% (26/26 tablas).
  - Motor Dual gobernado por `tenant.isp_module_enabled`:
    - **Modo Empresa (`false`):** Descubrimiento real de leases DHCP en `/ip/dhcp-server/lease`, herencia automática de coordenadas del router MikroTik asignador, preservación de coordenadas manuales del administrador, endpoint de Ping 1-Click desde RouterOS v7 (`POST /ping`), y apagado/ocultamiento total de pantallas y menús de campo `/field-ops`.
    - **Modo ISP (`true`):** Aprovisionamiento formal FTTH, visualización cartográfica de Cajas NAP con badges de ocupación (`ocupados / capacidad`), drawer interactivo con matriz de puertos 1 al 16, clientes conectados y polilíneas de acometida drop.
  - Rediseño táctico de Operaciones de Campo (`FieldTechMobileView.vue`): supresión de la sección de órdenes vacías, incorporación de 3 pestañas directas (1. Registrar Caja NAP con captura GPS, 2. Registrar Nuevo Cliente FTTH con cálculo de potencia $Rx\text{ dBm}$ y semáforo cromático, 3. Diagnósticos y Certificación 1-Click con ping RouterOS y firma táctil WORM) e historial de altas recientes.
  - Cobertura 11X certificada: 6 pruebas unitarias backend (`test_optical_boxes_and_bimodal_ops.unit.py` y `test_subscribers.unit.py`), 12 pruebas unitarias Vitest (`FieldTechMobileView.unit.ts` y `subscribersMapView.unit.ts`), 26 contratos front-back, 82 escenarios BDD API y 33 escenarios BDD UI en Karate Labs. Cero errores en linters y type-checkers.
- [x] **23.24** **Gobernanza Anti-Saturación de Diagnósticos de Red y Clientes (KeyDB Governor & RouterOS Protection):**
  - Servicio `DiagnosticGovernor` (`fastapi/src/services/diagnostic_governor.py`) con 5 capas de protección:
    - *Anti-Thundering Herd & Cooldown (KeyDB 15s):* Retorno ultra-rápido (< 2ms) con `is_cached: true` y `cache_ttl_remaining: N`.
    - *Semáforo Concurrente por Router:* Máximo 3 solicitudes concurrentes por router (`MAX_CONCURRENT_PER_ROUTER = 3`), protegiendo `www-ssl` y CPU MikroTik.
    - *Límite de Tasa por Router:* Máximo 30 diagnósticos por minuto por equipo.
    - *Límite de Tasa por Técnico:* Máximo 60 diagnósticos por minuto por usuario.
    - *Circuit Breaker Táctico por Router:* Umbral de 3 fallos activa estado `CIRCUIT_OPEN` por 30s con respuesta *Fail-Fast* (HTTP 503) sin retener hilos de FastAPI.
  - Exposición en API (`POST /api/v1/subscriber-devices/{id}/ping`) y frontend con badge `⚡ Caché Anti-Saturación (Ns)` en `SubscribersMapView.vue` y `FieldTechMobileView.vue`.
  - Cobertura 11X certificada: 5 pruebas unitarias backend (`test_diagnostic_governor.unit.py`), 0 errores en `vue-tsc`, ESLint, Ruff y Mypy, Escenario 83 en Karate Labs API y Escenario 34 en Karate Labs UI.
- [x] **23.25** **Componente Unificado de Mapa (`UnifiedNetworkMap.vue`), 3 Toggles con Feature Flags, Causa Raíz (RCA), Cerraduras Operativas, IPAM GPS y Remediación CIS Selectiva:**
  - Especificación formal `docs/specs/38_UNIFIED_NETWORK_MAP_ROOT_CAUSE_AND_OPERATIONAL_LOCKING.md` y manual operativo `docs/13_MANUAL_MAPA_RED_BIMODAL_Y_OPERACIONES_CAMPO.md` completados.
  - Consolidación en un solo componente de mapa polimórfico (`UnifiedNetworkMap.vue`) para `/inventory/routers`, `/subscribers/map` y `/wallboard`.
  - Toggles de capas independientes: `[ 🏢 Routers de Red ]`, `[ 📦 Cajas NAP FTTH ]` (gobernado estrictamente por `v-if="isp_module_enabled"`) y `[ 💻 Clientes ]` (estandarización universal para ISPs y empresas privadas).
  - Control de acceso RBAC en el mapa: técnicos de calle y soporte básico visualizan telemetría de salud del router pero tienen bloqueado y oculto el acceso a WebFig.
  - Motor de Análisis de Causa Raíz (RCA estilo Zabbix): supresión automática de pruebas individuales en clientes si el router de cabecera está caído o con Circuit Breaker abierto, con barra superior táctica de alerta y zoom a zona afectada (`ROOT_CAUSE_SUPPRESSED`).
  - Prevención de colisión operativa entre brigadas mediante cerraduras efímeras en KeyDB (`TTL = 600s`) con aviso contextual de trabajo en curso.
  - Acceso directo a Ventanas de Mantenimiento desde `/inventory` con botón superior y acción por fila para alternar `admin_state` en 1 clic.
  - Geolocalización de Clientes en `/ipam` con captura GPS móvil en vivo, herencia de cabecera y visualización de coordenadas.
  - Remediación selectiva individual con Safe Mode en la tabla CIS Benchmark (`/enterprise-compliance`) con botón `[ ⚡ Aplicar ]` por directiva, remediación real de CIS-1.8 (reglas dinámicas en `/ip/firewall/filter` contra fuerza bruta) y re-auditoría reactiva en caliente con persistencia en KeyDB.
  - Cobertura 11X certificada: 19 pruebas unitarias backend (`test_diagnostic_governor.unit.py`, `test_hito20_enterprise_suite.unit.py`), 20 pruebas unitarias Vitest (`UnifiedNetworkMap.unit.ts`, `subscribersMapView.unit.ts`, `enterpriseComplianceView.unit.ts`, `routerInventoryView.unit.ts`), 0 errores en `vue-tsc`, ESLint, Ruff y Mypy, Escenarios 84, 86 y 87 en Karate Labs API y Escenarios 35, 37 y 38 en Karate Labs UI.
- [x] **23.26** **Sondeo Pasivo Escalonado de Fondo (Worker Jitter), Notificación Reactiva WebSocket y Diagnóstico 360° en Toolkit de Campo:**
  - Especificación formal `docs/specs/39_BACKGROUND_SUBSCRIBER_POLLING_AND_REALTIME_STATUS_WEBSOCKET.md` y manual operativo `docs/13_MANUAL_MAPA_RED_BIMODAL_Y_OPERACIONES_CAMPO.md` completados.
  - Motor `StaggeredSessionPoller` en `rosgrid-worker` para lectura periódica de `/ip/dhcp-server/lease` y `/ppp/active` (intervalo 180s con jitter dinámico entre routers de 2 a 5s).
  - Filtro delta de base de datos (*Zero-Write Optimization*): cero escrituras en PostgreSQL si el estado no cambió.
  - Integración con vía rápida de eventos Syslog UDP 5514 ante desconexiones repentinas.
  - Transmisión en tiempo real por canal WebSocket de eventos `DEVICE_STATUS_CHANGED` y actualización cromática en caliente en `UnifiedNetworkMap.vue` y Wallboard NOC.
  - Toolkit de campo (`FieldTechMobileView.vue`): 4ta pestaña de Mapa de Zona integrada (routers visibles sin acceso WebFig), suite de Diagnóstico Integral 360° (Ping cliente, Gateway local, Internet WAN 1.1.1.1, DNS y MTU), y banner de advertencia de cerradura operativa con botón de forzado de prueba para órdenes de NOC.
- [x] **23.27** **Detección de Cierre de Pestaña o Navegador, Coordinación Multi-Pestaña y Liberación Efímera de Sesión con Período de Gracia (Grace Period en KeyDB):**
  - **Especificación Formal:** Aprobada `docs/specs/41_TAB_CLOSE_DETECTION_AND_EPHEMERAL_GRACE_PERIOD_SESSION_CLEANUP.md`.
  - **Frontend (Vue 3 / TypeScript):**
    - Composable `useTabLifecycleCoordinator.ts` con API estándar `BroadcastChannel('rosgrid_tab_lifecycle_bus')` para computar activas en memoria sin colisiones.
    - Intercepción del evento WHATWG `pagehide` para ejecutar `navigator.sendBeacon('/api/v1/auth/session-closing')` (con fallback a `fetch` con `keepalive: true` y `credentials: 'include'`) exclusivamente al cerrar la última pestaña activa del operador.
    - Reconexión transparente sin pérdida de sesión ante F5 / recargas de página.
  - **Backend (FastAPI / KeyDB):**
    - Nuevo endpoint `POST /api/v1/auth/session-closing` que registra clave efímera `rg:{tenant}:sess_closing:{session_id}` con TTL de 35 segundos e inserción en cola `closing_sessions_queue`.
    - Cancelación reactiva incondicional al detectar nueva petición autenticada o apertura de WebSocket en el plazo de gracia (eliminando la clave y preservando el ciclo absoluto de 8 horas).
    - Recolección y cierre desatendido (`kill_session`) con registro WORM `SESSION_CLOSED_ON_DISCONNECT` si el usuario no reconecta tras 35 segundos.
- [x] **23.28** **Políticas CIS Hardening Personalizables por Empresa (ISP / Corporativo), Onboarding de Feature Flags al Primer Inicio y Especificación Formal 42:**
  - **Especificación Formal:** Aprobada `docs/specs/42_ROUTEROS_V7_CIS_HARDENING_PERFORMANCE_AND_BULK_OPS_TEMPLATES.md` documentando directivas de control plane, L2 discovery, mitigación de amplificación DNS, BGP prefix-limits / TCP-AO / MD5, filtrado de bogons RFC 1918/6598, FastTrack selectivo QoS (`packet-mark=!qos-shaped`) y port-knocking dinámico de 3 etapas.
  - **Frontend (Vue 3 / TypeScript):**
    - Supresión estricta de la palabra "Benchmark" en títulos, badges, descripciones y pestañas en favor de la denominación unificada "CIS Hardening".
    - Modal interactivo de bienvenida y despliegue `TenantOnboardingModal.vue` presentado automáticamente al `SUPERADMIN_GLOBAL` o `TENANT_ADMIN` en su primer inicio de sesión para configurar el arquetipo de red (`🏢 Corporativo`, `🌐 ISP` o `⚙️ Personalizado`).
    - Modal de personalización de políticas CIS en `EnterpriseComplianceView.vue` para alternar perfiles base, activar/desactivar directivas, editar ponderaciones numéricas (1 a 50 pts) y personalizar scripts RouterOS de remediación.
  - **Backend (FastAPI / KeyDB):**
    - Endpoints `GET /api/v1/compliance/cis-policies` y `PUT /api/v1/compliance/cis-policies` con almacenamiento en KeyDB (`rg:{tenant}:cis_policies_config`) y auditoría inmutable WORM `COMPLIANCE_CIS`.
    - Ponderación normalizada de seguridad (0-100 pts) calculada dinámicamente sobre las directivas activas configuradas por el tenant.
    - Endpoints de onboarding en tenants (`POST /{id}/onboarding-complete` y `PATCH /{id}/features`) con flag `onboarding_completed`.
  - **Aseguramiento Multi-Capa 11X:** 517 pruebas unitarias backend aprobadas al 100%, 390 pruebas unitarias Vitest aprobadas en 52 archivos, 0 errores en `vue-tsc`, `ruff` y `mypy`, y nuevos escenarios Karate Labs BDD en API (escenarios 90-92 en `api_test.feature`) y UI (escenario 42 en `ui_business_flow.feature`), espejados en `docs/examples/`.
- [x] **23.29** **Corrección de Disponibilidad de Flota (50%), Telemetría Viva Syslog y Consolidación de Alcanzabilidad en Centro de Mando:**
  - **Diagnóstico y Causa Raíz:** El monitor de salud periódico marcaba `is_reachable = False` ante demoras REST, sobreescribiendo el estado a `OFFLINE` e ignorando el tráfico Syslog vivo de `r1`, `r2` y `r3`. En el frontend, las fórmulas de disponibilidad en `DashboardHomeView.vue` y `useInventoryStore.ts` dependían de `r.is_reachable` en Postgres, causando 0% de disponibilidad artificial.
  - **Worker de Monitoreo:** `health_monitor_worker.py` evalúa la existencia de llaves de Syslog activo en KeyDB y calcula `effective_reachable = is_reachable or has_syslog_live`, actualizando PostgreSQL y preservando la flota viva.
  - **Enriquecimiento de Telemetría:** `inventory_helpers.py` consolida `is_effective_reachable` y promueve `operational_status = "ONLINE"` si el router emite datagramas de eventos.
  - **Centro de Mando & Pinia:** `useInventoryStore.ts` y `DashboardHomeView.vue` consideran `is_reachable || operational_status === 'ONLINE' || syslog_active`, y el botón `[Actualizar Datos]` despacha `fetchRouters(true)`. Verificado visualmente en navegador con 3 en línea de 6 (50% disponibilidad).
  - **Aseguramiento Multi-Capa 11X:** 518 pruebas unitarias backend aprobadas al 100%, 392 pruebas unitarias Vitest aprobadas en 52 archivos, 0 errores en `vue-tsc`, `ruff` y `mypy`, y 0 secretos detectados.

---

## 🛡️ HITO 24: Marco Universal de Fixtures Trimodales Ground-Truth, Invariantes Negativas y Smoke Tests de Flota Real

> **Archivos Guía:** `docs/specs/43_REAL_FLEET_SMOKE_TESTS_GROUND_TRUTH_FIXTURES_AND_DETERMINISTIC_SENSING.md` y `.agents/rules/ground_truth_fixtures_and_negative_invariants.md`

### Fase 1: Subsistema de Syslog y Telemetría Viva (Completado y Certificado)
- [x] **24.1** **Redefinición Canónica y Determinista de Detección de Syslog:**
  - Sustituida la búsqueda genérica de `"remote"` en `inspect_router_syslog_config` (`inventory_helpers.py` y `health_monitor_worker.py`) por validación estricta de doble candado: acción con nombre exacto `rosgridsyslog`, parámetro `remote` con IP válida (distinta de `0.0.0.0`) y regla en `/system/logging` con `action="rosgridsyslog"` y `disabled="false"`.
  - Fallback por evidencia física de tráfico en KeyDB (`llen(syslog:ring) > 0`).
  - Retorno estrictamente de `False` ante routers con configuración por defecto de fábrica.
- [x] **24.2** **Fixtures JSON Reales de Syslog MikroTik RouterOS v7:**
  - Capturas crudas bajo `fastapi/tests/fixtures/mikrotik/`: `factory_default_logging.json` (de fábrica), `rosgrid_configured_logging.json` (activo) y `disabled_rosgrid_logging.json` (deshabilitado).
- [x] **24.3** **Saneamiento de Estado en KeyDB y PostgreSQL:**
  - Purgadas claves erróneas de `r4`, `r5` y `r6` en KeyDB (`syslog:active`, `syslog:configured`).
- [x] **24.4** **Guardrail Inicial de Validación de Flota Real (`scripts/validar-flota-real.py`):**
  - Script end-to-end evaluando aserciones positivas (`r1, r2, r3` con Syslog activo) y aserciones negativas obligatorias (`r4, r5, r6` estrictamente inactivos / `⚪ Sin Syslog`).
- [x] **24.5** **Aseguramiento Unitario Multi-Capa con Salidas Reales:**
  - Pruebas Pytest (`test_inventory_syslog_detection.unit.py`) evaluando `inspect_router_syslog_config` contra los fixtures reales (100% aprobadas).
- [x] **24.6** **Inspección Visual y Certificación en Navegador:**
  - Inspección con `browser_subagent` en `/inventory` y `/dashboard` certificando que `r1, r2, r3` muestran `🟢 Activo (3)` y `r4, r5, r6` muestran `⚪ Sin Syslog`.

### Fase 2: Extensión Transversal a los 7 Subsistemas Restantes (Completada y Certificada)
- [x] **24.7** **Auditoría CIS Hardening & Endurecimiento:**
  - Fixtures trimodales: `factory_default_cis.json` (Telnet/FTP activos, admin sin pass, score < 35), `hardened_rosgrid_cis.json` (score >= 90) y `partial_hardened_cis.json`.
  - Aserción negativa obligatoria: Routers vírgenes de fábrica (`r4, r5, r6`) DEBEN reprobar directivas críticas; nunca otorgar puntaje alto a equipos sin endurecer.
- [x] **24.8** **Topología L2 & Vecinos MNDP/LLDP:**
  - Fixtures trimodales: `factory_default_neighbors.json` (lista vacía `[]`), `meshed_neighbors.json` (vecinos MikroTik nominales) y `thirdparty_neighbors.json` (dispositivos extranjeros no-ROS).
  - Aserción negativa obligatoria: Zero alucinación de topología ni fallos ante MACs foráneas cuando la tabla está vacía.
- [x] **24.9** **IPAM, Pools DHCP y Leases:**
  - Fixtures trimodales: `factory_default_dhcp.json` (subnet por defecto `192.168.88.0/24` inerte), `configured_dhcp_pools.json` (pools corporativos RoSGrid) y `disabled_dhcp_server.json` (`invalid=true`).
  - Aserción negativa obligatoria: No asociar leases ajenos ni registrar pools inactivos como operativos en el tenant.
- [x] **24.10** **Orquestador PoE & Tolerancia a Hardware No Compatible:**
  - Fixtures trimodales: `factory_default_poe.json` (routers sin PoE/CHR, HTTP 404/400), `active_poe_netpower.json` (interfaces PoE activas) y `overload_poe.json` (sobrecarga/cortocircuito).
  - Aserción negativa obligatoria: Equipos sin chip PoE retornan `UNSUPPORTED`, nunca "puertos caídos".
- [x] **24.11** **Detección de Rogue DHCP & DHCP Snooping:**
  - Fixtures trimodales: `factory_default_bridge.json` (`dhcp-snooping=no`), `snooping_enabled_bridge.json` (`dhcp-snooping=yes`) y `rogue_server_alert.json`.
  - Aserción negativa obligatoria: Zero alertas espurias de Rogue DHCP si el bridge tiene `dhcp-snooping=no`.
- [x] **24.12** **CAPsMAN & Wi-Fi 6:**
  - Remediación en `wifi.py` erradicando métricas inventadas (4 APs, 8 radios, 36 clientes). Fixtures trimodales: `factory_default_no_wifi.json` (CCR2004/RB5009 sin radio), `active_wifiwave2_capsman.json` y `unregistered_ap.json`.
  - Aserción negativa obligatoria: Reportar `NO_WIRELESS_INTERFACES` sin degradar la salud general del equipo.
- [x] **24.13** **Detección de Config Drift (Desviación):**
  - Fixtures trimodales: `factory_default_export.rsc`, `golden_baseline_export.rsc` y `tampered_export.rsc`.
  - Aserción negativa obligatoria: Configuración de fábrica contra Golden Baseline debe reportar 100% de desviación (drift).
- [x] **24.14** **Suite Unificada de Smoke Tests de Flota Real Multi-Dominio:**
  - Ampliación de `scripts/validar-flota-real.py` (`make smoke-fleet`) evaluando los 8 dominios contra los 6 routers físicos (`r1-r3` nominales vs `r4-r6` fábrica), garantizando la compuerta institucional Level-11X.

---

## 🎛️ HITO 25: Conmutador Rápido de Tenants en Cabecera (SuperAdmin), Ergonomía de Pie de Página In-Flow y Gestión Táctica de Feature Flags por Empresa

> **Archivos Guía:** `docs/specs/44_TENANT_SWITCHER_INFLOW_FOOTER_AND_MODULAR_FEATURE_FLAGS.md`

- [x] **25.1** **API Backend de Conmutación de Contexto de Tenant:**
  - Endpoint `POST /api/v1/auth/switch-tenant` restringido exclusivamente a `SUPERADMIN_GLOBAL`.
  - Validación de estado activo del tenant destino, actualización atómica de sesión en KeyDB y emisión de nuevo JWT token.
  - Registro de auditoría WORM HMAC-SHA256 con acción `SUPERADMIN_TENANT_SWITCHED`.
- [x] **25.2** **Componente Frontend `RgTenantSwitcher.vue` en Barra Superior:**
  - Sustitución del badge estático `div.tenant-badge` en `RgResponsiveShell.vue` por selector interactivo `🏢 {tenantSlug} ▾` para `SUPERADMIN_GLOBAL`.
  - Popover flotante estilo Tactical NOC con buscador (`🔍 Buscar empresa...`), lista de empresas activas y conmutación en caliente de stores de Pinia (`useInventoryStore`, `useNocEventsStore`, `useAuthStore`) sin recargar página.
  - Mantenimiento como badge estático solo de lectura para roles no-SuperAdmin.
- [x] **25.3** **Ergonomía de Pie de Página In-Flow (Recuperación de 32px Verticales):**
  - Eliminación de la barra fija flotante `.rg-global-footer` del layout raíz en `RgResponsiveShell.vue`.
  - Reubicación del pie de página con créditos institucionales y licencia GPLv3 al interior de `.rg-main` tras el `<slot />`, con `margin-top: auto`.
  - Maximización del 100% de la altura de pantalla en todas las vistas (Dashboard, Inventario, Wallboard, Topología).
- [x] **25.4** **Indicadores Visuales de Módulos en Tabla de Empresas:**
  - Inclusión de badges resumen `[ 12/16 Módulos ]` y botón de acción descriptivo `[ ⚙️ Módulos ]` en `TenantsManagementView.vue`.
- [x] **25.5** **Sub-pantalla Táctica de Módulos & Capacidades (`TenantModulesStudioView.vue`):**
  - Vista dedicada en `/admin/tenants/:tenantId/modules` con navegación de miga de pan (`Breadcrumbs`) y botón `[ ⬅ Volver a Empresas ]`.
- [x] **25.6** **Barra de Arquetipos en 1 Clic (Presets Rápidos):**
  - Botones tácticos superiores para alternancia instantánea: `🏢 Modo Corporativo`, `🌐 Modo ISP & WISP`, `⚡ Modo NOC Mínimo` y `⚙️ Personalizado`.
- [x] **25.7** **Cuadrícula Táctica de 4 Cuadrantes (`RgFeatureFlagsGrid.vue` & `RgFeatureCard.vue`):**
  - Organización de las 16 flags en 4 dominios funcionales: *Núcleo ISP*, *Ciberseguridad*, *Telemetría* y *Automatización*.
  - Tarjetas enriquecidas con badges de riesgo (`🟢 Bajo`, `🟡 Operativo`, `🔴 Crítico`), descripción en español, interruptores táctiles y validación de dependencias lógicas (DAG).
- [x] **25.8** **Escudo de Radio de Impacto (*Blast Radius Shield*):**
  - Modal de advertencia de seguridad con cálculo dinámico antes de desactivar flags críticas de gobernanza (`syslog_collector_enabled`, `enforce_maker_checker`, `auto_safemode_enforced`).
- [x] **25.9** **Aseguramiento Unitario Multi-Capa 11X:**
  - Pruebas unitarias backend (FastAPI/Pytest) del endpoint de conmutación y frontend (Vitest) de los componentes `RgTenantSwitcher`, `TenantModulesStudioView` y `RgFeatureFlagsGrid`.
  - 0 errores de tipado estricto en `ruff`, `mypy` y `vue-tsc`.
- [x] **25.10** **Certificación en Docker e Inspección Visual en Navegador Real:**
  - Despliegue en contenedor efímero y validación visual con `browser_subagent` verificando conmutación de tenant, footer in-flow y cuadrícula de módulos.
- [x] **25.11** **Estabilización de Conmutación de Contexto, Doble Candado Fail-Safe y Cobertura 11X Integral (Karate Labs API & UI):**
  - Silenciamiento de broadcast en Pub/Sub (`notify_ws=False`) en `kill_session` al conmutar organizaciones, impidiendo que el WebSocket propio interprete un kill-switch administrativo sobre la sesión activa.
  - Secuencia Fail-Safe en backend extrayendo `features` de forma canónica y asegurando la nueva sesión antes de revocar la anterior.
  - Filtro de exclusión para `SUPERADMIN_TENANT_SWITCH` en `useNocEventsStore.ts` y reconexión reactiva limpia ante el evento `rosgrid:tenant-switched`.
  - Aseguramiento 11X completo: 543 pruebas unitarias backend aprobadas al 100% (añadida validación de payload y `test_kill_session_silent_mode_no_ws_notify`), 404 pruebas frontend en 55 suites Vitest, 94 escenarios BDD Karate Labs API (escenarios 93 y 94 en `api_test.feature`), 44 escenarios BDD Karate Labs UI (escenarios 43 y 44 en `ui_business_flow.feature`) y 26 de 26 contratos Front-Back aprobados en Docker.

---

## 🛡️ HITO 26: Gobernanza Táctica de Módulos B2B — DAG en Cascada (Hard Lock), Blindaje RBAC de Licenciamiento, Modo Contingencia y Auditoría Visual con Rollback

> **Archivos Guía:** `docs/specs/45_TACTICAL_FEATURE_FLAGS_GOVERNANCE_DAG_AND_AUDIT_ROLLBACK.md`

- [x] **26.1** **Grafo de Dependencias Activo (DAG) con Bloqueo Estricto en Cascada (Hard Lock):**
  - Implementación reactiva en `RgFeatureFlagsGrid.vue`: si un módulo padre (ej. `isp_module_enabled`) es apagado, los módulos dependientes (`bgp_looking_glass_enabled`, `sla_tracker_enabled`) se fuerzan a `false` y sus interruptores quedan bloqueados en gris (`disabled`).
  - Tooltips contextuales explicativos en hover (`[ 🔒 Requiere activar Módulo ISP previamente ]`) y badge visual en tarjeta.
- [x] **26.2** **Blindaje RBAC de Licenciamiento Comercial (Solo SuperAdmin):**
  - Refuerzo de validación estricta en endpoints de flags (`fastapi/src/api/v1/tenants.py`): retorno imperativo de `HTTP 403 Forbidden` ante cualquier rol inferior a `SUPERADMIN_GLOBAL`.
  - Documentación de gobernanza comercial: las flags representan licenciamiento contractual B2B inalterable por inquilinos locales.
- [x] **26.3** **Botón Táctico de Modo Contingencia / Emergencia NOC:**
  - Inclusión del botón `[ ⚡ Modo Contingencia / Bajo Consumo ]` con acento visual en la barra de presets de `RgFeatureFlagsGrid.vue` y `TenantModulesStudioView.vue`.
  - Matriz de apagado en 1 clic de colectores de alta frecuencia (`syslog_collector_enabled`, `ipfix_analytics_enabled`, `prometheus_fleet_exporter_enabled`, `sfp_ddm_telemetry_enabled`, `config_drift_monitoring_enabled`, `sdwan_orchestrator_enabled`), preservando intacto el núcleo de control.
  - Banner informativo reactivo en pantalla alertando sobre la suspensión de telemetría intensiva.
- [x] **26.4** **Auditoría Visual en Pantalla y Función de Reversión (Rollback en 1 Clic):**
  - Estructuración bimodal de pestañas en `/admin/tenants/:tenantId/modules`: `[ ⚙️ Matriz de Módulos ]` y `[ 📜 Historial de Modificaciones ]`.
  - Componente de auditoría `TenantModulesAuditTab.vue` que consulta el endpoint `GET /api/v1/tenants/{tenant_id}/features/audit` para listar eventos WORM `TENANT_FEATURE_FLAGS_UPDATED` de esa empresa con hash criptográfico SHA-256.
  - Botón `[ ⤺ Cargar esta versión ]` en cada registro histórico, poblando el formulario reactivo de la Pestaña 1 con el estado previo para guardado consciente y desplegando banner informativo.
- [x] **26.5** **Aseguramiento Unitario Multi-Capa 11X:**
  - Pruebas unitarias frontend en Vitest para la cascada del DAG, el preset de contingencia y la reversión de auditoría (`RgFeatureFlagsGrid.unit.ts`, `TenantModulesAuditTab.unit.ts` y `TenantModulesStudioView.unit.ts`). Total: 412 tests en 56 suites pasando al 100%.
  - Pruebas unitarias backend en Pytest para la restricción 403 de roles no-SuperAdmin y endpoint de auditoría WORM (`test_tenants_features_rbac.unit.py`). Total: 544 tests backend pasando al 100%.
  - 0 errores en `vue-tsc --noEmit` y `ruff check src/`.
  - Escenarios BDD Karate Labs API (95, 96, 97) y UI (46) incorporados y sincronizados en `docs/examples/`.
- [x] **26.6** **Validación en Docker e Inspección Visual en Navegador Real:**
  - Reconstrucción de imágenes locales (`sinfallas/rosgrid-backend:local-test` y `sinfallas/rosgrid-frontend:local-test`), recreación de contenedores y verificación interactiva del bloqueo de switches hijos, el preset de contingencia y el cargado de versiones históricas en `browser_subagent`.
- [x] **26.7** **Integración Integral de Graphify AST en el Proceso de Desarrollo (Fases 1 a 4):**
  - Refresco completo de grafos topológicos (Backend: 3.320 nodos, 12.448 aristas, 171 comunidades; Frontend: 1.816 nodos, 3.235 aristas, 95 comunidades).
  - Script canónico de extracción en 1 clic en Docker efímero con `--code-only` (`scripts/actualizar-grafos-graphify.sh`).
  - Script de validación topológica y límites de capas arquitectónicas (`.agents/scripts/verify_topological_health.py`) integrado en la compuerta de certificación (`[4/7]`).
  - Herramienta de inspección de radio de impacto pre-refactorización (`.agents/scripts/inspect_blast_radius.py`) incorporada en directivas de `.agents/rules/`.
  - Servicio MCP estandarizado (`graphify-mcp`) en puerto 8080 con plantillas para Hermes Agent y Claude Desktop, y habilidad agéntica `.agents/skills/graphify-ast-navigator`.
  - Visualización interactiva en 1 clic (`scripts/ver-mapa-arquitectura.sh` / `make map`).

---

## 📦 HITO 27: Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`scripts/build.sh`)

> **Archivo Guía:** `docs/specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [ ] **27.1** Actualizar `CHANGELOG.md` consolidando los cambios de `[Unreleased]` dentro del lanzamiento oficial `[1.0.0]` con las métricas certificadas en `TESTING.md`.
- [ ] **27.2** Ejecutar `./scripts/build.sh` (como usuario no-root) con `docker buildx` (`container-builder` + `tonistiigi/binfmt`) para construir y publicar `sinfallas/rosgrid-backend:latest` (`:1.0.0`) y `sinfallas/rosgrid-frontend:latest` (`:1.0.0`) en Docker Hub y limpiar cachés con `prune -af`.


