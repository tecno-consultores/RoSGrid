# 🗺️ ROADMAP GRANULAR DE EJECUCIÓN (36 SPECS) — RoSGrid

## 📍 Punto de Control Actual (Checkpoint)

- **Hito Actual en Curso:** Hito 24 (Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub)
- **Estado General del Sistema:** Hitos 0 al 23 COMPLETADOS (100%).
- **Hito 23 (Automatización de Flota, Topología L2, Syslog Efímero, Exportador Prometheus y Seguridad CVE):** COMPLETADO al 100% y certificado en Docker. Especificaciones `specs/35`, `specs/03` y `specs/11`, manuales `docs/12` y `docs/06`, migraciones Alembic 0007 y 0008 (`tenant_custom_roles` y `routers.network_role` VARCHAR(64)), colector Syslog UDP 5514 activo en Worker con RingBuffer en KeyDB y badge de presencia en inventario, motor de Topología L2 con Pan/Zoom Canvas 2D a 60 FPS, Matriz CVE con cruce local semver, orquestador PoE-aware con Safety Stop (1%), exportador Prometheus `/api/v1/metrics/fleet`, 20 herramientas MCP en la Skill `rosgrid-noc-operator`, 466 tests backend (95.11% cobertura), 298 tests frontend (100% pasando), 64/64 escenarios BDD API, 22/22 escenarios BDD UI y 26/26 contratos Front-Back validados en Docker (`validar_comunicacion_front_back.py`).
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

> **Archivos Guía:** `specs/00_MASTER_INDEX_AND_11X_GOVERNANCE.md` y `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **0.1** Estructura del monorepo (`fastapi/`, `vue3/`, `specs/`, `examples/`, `docs/`).
- [x] **0.2** Archivos raíz (`LICENSE` GPL-3.0-only, `.env.example`, `docker-compose.yml`, `.gitignore`, `lefthook.yml`, `commitlint.config.js`, `instalar-hooks.sh`, `auditar-infra.sh`).
- [x] **0.3** Fusión quirúrgica inicial en `fastapi/` (`pyproject.toml`, `tox.ini`, `Makefile`, `docker-compose.qa.yml`, `limpieza.sh`, `locustfile.py`, `scripts/entrypoint.sh`).
- [x] **0.4** Fusión quirúrgica inicial en `vue3/` (`package.json`, `.npmrc`, `vitest.config.ts`, `stryker.conf.json`, `playwright.config.ts`, `lighthouserc.js`, `Makefile`, `docker-compose.qa.yml`, `nginx/default.conf`).

---

## ✅ HITO 1: Esquema PostgreSQL 17, Multi-Tenant RLS, Bóveda y Auditoría WORM

> **Archivos Guía:** `specs/02_DB_SCHEMA_CORE_TENANTS_AND_RLS.md`, `specs/03_DB_SCHEMA_INVENTORY_VAULT_AND_MAINTENANCE.md` y `specs/04_DB_SCHEMA_OPERATIONS_BACKUPS_AND_IMMUTABLE_AUDIT.md`

- [x] **1.1** Configuración de Alembic (`fastapi/alembic.ini`, `fastapi/migrations/env.py`, `script.py.mako`).
- [x] **1.2** Migración `0001_core_tenants_users_rls.py` (Tablas `tenants`, `users`, `user_router_permissions`, los 11 roles y políticas `FORCE ROW LEVEL SECURITY` — `specs/02`).
- [x] **1.3** Migración `0002_inventory_vault_maintenance.py` (Tablas `routers`, `router_tags`, `router_credentials_vault` AES-256-GCM y `maintenance_windows` — `specs/03`).
- [x] **1.4** Migración `0003_operations_backups_immutable_audit.py` (Tablas `approval_requests`, `router_backups`, `config_templates`, `bulk_jobs`, `bulk_job_items`, `notification_channels` y `audit_logs` con trigger WORM `trg_immutable_audit_logs` — `specs/04`).
- [x] **1.5** Modelos SQLAlchemy 2.0 (`src/models/base.py`, `core.py`, `inventory.py`, `operations.py`) y motor de sesión async con inyección de `app.current_tenant_id` (`src/db/session.py`).

---

## ✅ HITO 2: Capa KeyDB Multi-Hilo (Compatible RESP) — Idempotencia, Sesiones Kill-Switch, Pub/Sub y Monitor Zero-Metrics

> **Archivo Guía:** `specs/05_REDIS_KEYS_IDEMPOTENCY_AND_ZERO_METRICS.md`

- [x] **2.1** Cliente y pool de conexión asíncrono compatible con KeyDB / DragonflyDB (`src/redis_layer/client.py`).
- [x] **2.2** Middleware y gestor de Idempotencia HTTP (`Idempotency-Key` UUIDv7 con estados `IN_PROGRESS` / `COMPLETED` y hash SHA-256 del body en `src/redis_layer/idempotency.py`).
- [x] **2.3** Gestor de familias de Refresh Tokens (*Reuse Detection*), registro de sesiones activas e invocación del **Kill-Switch** (`src/redis_layer/sessions.py`).
- [x] **2.4** Máquina de Estados Efímera *Zero-Metrics Storage* (~200 bytes/router en memoria para transiciones `ONLINE`/`OFFLINE`/`DEGRADED_HIGH_LOAD` en `src/redis_layer/zero_metrics_monitor.py`).

---

## ✅ HITO 3: Seguridad Split-Credential, 2FA TOTP, Step-Up Auth y Matriz RBAC (11 Roles)

> **Archivos Guía:** `specs/06_SECURITY_SPLIT_CREDENTIAL_2FA_AND_STEPUP.md` y `specs/07_RBAC_11_ROLES_MATRIX_AND_MAKER_CHECKER.md`

- [x] **3.1** Configuración central tipada (`src/core/config.py`).
- [x] **3.2** Motor criptográfico `Argon2id`, `AES-256-GCM` con `AAD` (`tenant_id|router_id`) y generador TOTP RFC 6238 (`src/core/crypto.py`).
- [x] **3.3** Generación/verificación de cookies `__Host-rg_at` / `__Host-rg_rt` y protección `X-CSRF-Token` firmada con HMAC-SHA256 (`src/core/csrf.py`).
- [x] **3.4** Middleware de cabeceras de seguridad estrictas para cumplimiento OWASP ZAP (`src/core/security_headers.py`).
- [x] **3.5** Servicio de Auditoría Inmutable con cadena hash SHA-256 (`prev_record_hash`) y sanitización `[REDACTED]` (`src/core/audit.py`).
- [x] **3.6** Matriz declarativa de los **11 Roles** + filtro de permisos por router (`src/rbac/policy_matrix.py` — `specs/07`).
- [x] **3.7** Clasificador e interceptor de las 7 categorías críticas **Maker-Checker** (`src/rbac/checker.py` — `specs/07`).

---

## ✅ HITO 4: Conector Asíncrono RouterOS v7 (`/rest/*`), Pinning SSL TOFU y Motor Safe Mode

> **Archivo Guía:** `specs/08_MIKROTIK_REST_V7_CLIENT_TOFU_AND_SAFEMODE.md`

- [x] **4.1** Verificador de huella TLS `SHA-256` (*Trust On First Use* — `PENDING_TOFU`, `TRUSTED_PINNED`, `FINGERPRINT_MISMATCH` en `src/mikrotik/ssl_tofu.py`).
- [x] **4.2** Cliente HTTP asíncrono `httpx` para RouterOS v7 (`/rest/*`) con soporte de fallback transaccional a `previous_password` (`src/mikrotik/client.py`).
- [x] **4.3** Motor **Safe Mode (*Dead Man's Switch*)** mediante inyección y limpieza de `/rest/system/scheduler` a 60s (`src/mikrotik/safemode.py`).
- [x] **4.4** Normalizadores de tipos de RouterOS v7 (booleanos `"true"`/`"false"`, tiempos y unidades a tipos nativos en `src/mikrotik/normalizers.py`).

---

## ✅ HITO 5: Esqueleto FastAPI, Observabilidad `/metrics` y Endpoints Auth, Usuarios y Kill-Switch

> **Archivos Guía:** `specs/09_BACKEND_PHASE_1_SKELETON_OBSERVABILITY_AND_MIGRATIONS.md` y `specs/10_BACKEND_ENDPOINTS_AUTH_TENANTS_USERS_KILLSWITCH.md`

- [x] **5.1** Aplicación principal `src/main.py` con `prometheus-fastapi-instrumentator` (`/metrics`), `/health`, `/users/me` y registro de middlewares.
- [x] **5.2** Dependencias de inyección (`src/api/deps.py`) y esquemas Pydantic v2 de Autenticación, Tenants, Usuarios y Sesiones (`src/schemas/auth.py`, `users.py`).
- [x] **5.3** Endpoints de Login Multi-Tenant en 2 etapas, enrolamiento/verificación 2FA TOTP, Refresh y Logout (`src/api/v1/auth.py` — `specs/10`).
- [x] **5.4** Endpoints de gestión de Empresas (`src/api/v1/tenants.py`), Usuarios de los 11 roles y matriz de asignación de routers por técnico (`src/api/v1/users.py` — `specs/10`).
- [x] **5.5** Endpoints de Sesiones Activas en tiempo real y ejecución del **Kill-Switch** individual o masivo (`src/api/v1/sessions.py` — `specs/10`).

---

## ✅ HITO 6: Endpoints de Inventario MikroTik, Importador CSV, Bóveda Step-Up (30s) y Rotación

> **Archivo Guía:** `specs/11_BACKEND_ENDPOINTS_INVENTORY_CSV_VAULT_AND_ROTATION.md`

- [x] **6.1** Esquemas Pydantic v2 de Inventario, CSV, Bóveda y Ventanas de Mantenimiento (`src/schemas/inventory.py`).
- [x] **6.2** Endpoints CRUD de Routers MikroTik con autodescubrimiento (`/rest/system/resource`, `routerboard`, `identity`, `package`) y coordenadas OpenStreetMap (`src/api/v1/inventory.py`).
- [x] **6.3** Importador Masivo por CSV en 2 pasos: validación `/import-csv/dry-run` y ejecución `/import-csv/commit`.
- [x] **6.4** Endpoints de Bóveda Criptográfica: revelación con **Step-Up Auth (2FA TOTP en vivo, exclusivo para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`)**, rotación transaccional de clave API y Re-Pin SSL TOFU (`src/api/v1/vault.py`).
- [x] **6.5** Endpoints de Ventanas de Mantenimiento Programadas (`src/api/v1/maintenance.py`).

---

## ✅ HITO 7: Endpoints WebFig Capa 1 (Parte A) — Interfaces, Óptica SFP DDM, VLAN, WireGuard e IP

> **Archivo Guía:** `specs/12_BACKEND_ENDPOINTS_WEBFIG_L1_INTERFACES_AND_IP.md`

- [x] **7.1** Esquemas Pydantic v2 para Interfaces e IP/IPv6 (`src/schemas/webfig_l1_net.py`).
- [x] **7.2** Endpoints de Interfaces generales, Ethernet, test de cable TDR y diagnóstico óptico **SFP/SFP+ DDM** (`tx-power`, `rx-power` dBm y clasificación de salud óptica) (`src/api/v1/webfig_interfaces.py`).
- [x] **7.3** Endpoints de VLAN 802.1Q, Bridges + Ports, WireGuard (Peers + llave pública) y tabla de registro WiFi/Wireless.
- [x] **7.4** Endpoints de IPv4/IPv6 Addresses, Routes (incluyendo balanceo ECMP), ARP, Pools, DHCP Server Leases (con conversión a estático), DNS, IP Neighbors y `/ip/service` (con protección anti-suicidio del puerto `www-ssl`) (`src/api/v1/webfig_ip.py`).

---

## ✅ HITO 8: Endpoints WebFig Capa 1 (Partes B y C) — Firewall, BGP/OSPF, PPPoE, Queues, System y Tools

> **Archivos Guía:** `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md` y `specs/14_BACKEND_ENDPOINTS_WEBFIG_L1_PPP_QUEUES_SYSTEM_TOOLS.md`

- [x] **8.1** Endpoints de Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, `Connections`) y endpoint de reordenamiento (`move`) protegido por Safe Mode (`src/api/v1/webfig_firewall.py` — `specs/13`).
- [x] **8.2** Endpoints de Routing v7: sesiones/peers `BGP`, prefijos anunciados, `OSPF`, `Routing Tables`, `Routing Rules`, `BFD` y `Filters` (`src/api/v1/webfig_routing.py` — `specs/13`).
- [x] **8.3** Endpoints de PPPoE Active (con corte/reconexión para Soporte N1), PPP Secrets, Profiles y Servidores PPPoE (`src/api/v1/webfig_ppp.py` — `specs/14`).
- [x] **8.4** Endpoints de Control de Ancho de Banda: `Simple Queues` (con `move`) y `Queue Tree` (`src/api/v1/webfig_queues.py` — `specs/14`).
- [x] **8.5** Endpoints de System (`Identity`, `Users`, `Scripts`, `Scheduler` con ocultamiento de `rosgrid_safemode_*`, `Packages`, `Reboot`) y Tools de diagnóstico en vivo (`Ping`, `Traceroute`, `Torch`, `Log`) (`src/api/v1/webfig_system_tools.py` — `specs/14`).

---

## ✅ HITO 9: Motor Universal WebFig Capa 2, Maker-Checker, Backups Diff Git y Acciones Masivas

> **Archivos Guía:** `specs/15_BACKEND_ENDPOINTS_WEBFIG_L2_UNIVERSAL_ENGINE.md` y `specs/16_BACKEND_ENDPOINTS_MAKER_CHECKER_BACKUPS_BULK_UPDATES.md`

- [x] **9.1** Motor Dinámico Universal WebFig Capa 2 (`/webfig/layer2/catalog`, inspector de esquema dinámico, CRUD genérico y bloqueo de rutas prohibidas `FORBIDDEN_L2_PATHS`) (`src/api/v1/webfig_layer2.py` — `specs/15`).
- [x] **9.2** Endpoints de Bandeja de Aprobación **Maker-Checker** (listar, aprobar ejecutando cambio diferido con Safe Mode y rechazar, impidiendo auto-aprobación) (`src/api/v1/approvals.py` — `specs/16`).
- [x] **9.3** Motor de Backups `.rsc`/`.backup` con deduplicación SHA-256, retención de 30 días y comparador **Diff estilo Git (`unified_diff`)** entre backups o contra el estado `LIVE` (`src/api/v1/backups.py` — `specs/16`).
- [x] **9.4** Endpoints de Plantillas (*Golden Configs*), Acciones Masivas Multi-Router (`bulk-jobs`) y Actualizador Centralizado de RouterOS v7 con pre-backup obligatorio (`src/api/v1/bulk_and_updates.py` — `specs/16`).
- [x] **9.5** Endpoints de Consola Forense de Auditoría Inmutable y verificador criptográfico de integridad WORM (`src/api/v1/audit.py` — `specs/16`).

---

## ✅ HITO 10: Multiplexor WebSocket, Workers, Dockerfile, Graphify y Optimización de Alto Rendimiento Backend

> **Archivos Guía:** `specs/17_BACKEND_WEBSOCKETS_LIVE_CHARTS_AND_ALERT_WORKERS.md` y `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **10.1** Multiplexor WebSocket `/ws/v1/routers/{router_id}/live-telemetry` (activa el poller cuando hay >= 1 operador viendo el router y se detiene al instante cuando `SCARD == 0`).
- [x] **10.2** WebSocket global del Tenant `/ws/v1/tenant/events` (eventos NOC, progreso de trabajos masivos y orden `SESSION_KILLED`).
- [x] **10.3** Los 4 Workers en segundo plano (`src/workers/`): Monitor *Zero-Storage*, Despachador de Alertas Multi-Canal (Telegram Bot, Correo SMTP, Webhook HMAC-SHA256 y NOC), Worker de Backups Nocturnos y Worker de Rotación Automática de Bóveda.
- [x] **10.4** **Cierre de Arquitectura Backend con Graphify (En Docker):** Ejecutar `docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify` dentro de `./fastapi/` para generar `fastapi/graphify-out/GRAPH_REPORT.md` y el grafo AST completo del Backend (`specs/09`, `29`).
- [x] **10.5** **Dockerfile Multi-Stage de Producción Backend (`fastapi/Dockerfile`):** Crear `fastapi/Dockerfile` basado en `sinfallas/base-python-uv:3.15` con soporte `ARG BUILD_DATE`, dependencias `--no-dev`, usuario sin privilegios (`non-root`) y `scripts/entrypoint.sh` (`specs/01`).
- [x] **10.6** **Paquete de Optimización de Alto Rendimiento Backend, DB y KeyDB Multi-Hilo:**
  - Sustituir `redis:7-alpine` por `eqalpha/keydb:alpine` (`keydb-server --server-threads 2` y healthcheck `keydb-cli`) en `docker-compose.yml`, `fastapi/docker-compose.qa.yml` y `specs/01` (documentando `DragonflyDB` como perfil de alta escala).
  - Configurar `ORJSONResponse` como `default_response_class` en `fastapi/src/main.py`, serialización `orjson` en frames WebSocket, desactivación estricta de Swagger/ReDoc/OpenAPI cuando `ROSGRID_ENV == "production"` y activar `--loop uvloop --http httptools` en `fastapi/scripts/entrypoint.sh`.
  - Implementar reutilización de pool `Keep-Alive` TLS (`limits=httpx.Limits(max_keepalive_connections=20, keepalive_expiry=60.0)`) en `src/mikrotik/client.py` y ejecución por lotes con `pipeline()` hacia KeyDB en `src/redis_layer/zero_metrics_monitor.py`.
  - Añadir índice `BRIN` (`ix_audit_logs_created_at_brin` con `postgresql_using='brin'`) sobre `audit_logs(created_at)` en `0003_operations_backups_immutable_audit.py` y re-validar `make qa-lint && make qa-unit`.

---

## ✅ HITO 11: Frontend Vue 3 Base — Zero-Trust, Interceptores, Stores Pinia (`shallowRef`) y Sistema de Diseño WCAG (`Virtual Scroll`)

> **Archivos Guía:** `specs/18_FRONTEND_PHASE_1_SETUP_ZERO_TRUST_AND_INTERCEPTORS.md` y `specs/19_FRONTEND_DESIGN_SYSTEM_ACCESSIBILITY_AND_PERFORMANCE.md`

- [x] **11.1** Configuración base de Vite, TypeScript (`tsconfig.json`), `index.html` y `public/manifest.webmanifest` PWA (`specs/18`, `19`).
- [x] **11.2** Cliente HTTP seguro (`vue3/src/api/httpClient.ts`) con los 4 interceptores: `X-CSRF-Token`, `Idempotency-Key` (`UUIDv7`), rotación transparente de Refresh Token y captura de `202 Accepted` (*Maker-Checker*) (`specs/18`).
- [x] **11.3** Los 6 Stores en Pinia (`useAuthStore`, `useThemeAndLayoutStore` con densidad dual adaptativa `auto`/`compact`/`comfortable`, `useInventoryStore`, `useWebFigStore` con cola de hasta 5 pestañas en RAM `openRouterTabs`, `useLiveTelemetryStore`, `useNocEventsStore`) usando **`shallowRef` para colecciones masivas y buffers de telemetría**, más Vue Router con Guards RBAC para los 11 roles (`specs/18`).
- [x] **11.4** Sistema de diseño de alta densidad (`themes.css` con tema predeterminado `dark` *Tactical NOC Cyan* `#0B0F19`/`#06B6D4`/`#22D3EE`, `light` y `noc-high-contrast` cumpliendo contraste WCAG 2.1 AA y fuentes nativas `tabular-nums`) (`specs/19`).
- [x] **11.5** Los 5 componentes base reutilizables: `RgDataTable.vue` (Densidad Dual `32px` WinBox en PC / `44px` táctil en móvil con **Virtual Scrolling nativo para tablas > 100 filas**, insignias `[D]`/`[X]`/`[I]`/`[R]`, conmutador rápido y Drag & Drop + teclado accesible), `RgCommandPalette.vue` (`Ctrl+K`), `RgSafeModeBanner.vue`, `RgStepUp2FAModal.vue` y `RgResponsiveShell.vue` (Doble contexto + Barra Inferior Fija en Móvil) (`specs/19`).

---

## ✅ HITO 12: Vistas Frontend (Parte A) — Login 2FA, Usuarios/Matriz, Kill-Switch, Inventario OSM y Bóveda

> **Archivos Guía:** `specs/20_FRONTEND_VIEWS_AUTH_USERS_PERMISSIONS_AND_SESSIONS.md` y `specs/21_FRONTEND_VIEWS_INVENTORY_OSM_MAP_CSV_AND_VAULT.md`

- [x] **12.1** Vista `LoginView.vue` en 2 etapas (`tenant_slug` + credenciales -> QR de enrolamiento local o desafío 2FA TOTP) (`specs/20`).
- [x] **12.2** Vistas de Administración de Tenants (`TenantsManagementView.vue`), Gestión de Usuarios de los 11 roles (`UsersAndPermissionsView.vue`) y Modal de Matriz de Asignación de Routers por Técnico (`UserRouterMatrixModal.vue`) (`specs/20`).
- [x] **12.3** Panel en vivo de Sesiones Activas y botón de expulsión **Kill-Switch** (`ActiveSessionsKillSwitchView.vue`) (`specs/20`).
- [x] **12.4** Vista de Inventario MikroTik (`RouterInventoryView.vue`) y componente de Mapa Interactivo 100% gratuito con **Leaflet + OpenStreetMap (`OsmRouterMap.vue`)** (`specs/21`).
- [x] **12.5** Asistente de Importación Masiva CSV en 2 pasos (`CsvOnboardingWizardModal.vue`), Modal de **Bóveda con Step-Up Auth y autodestrucción en memoria a los 30s (`VaultRevealModal.vue`)** y vista de Ventanas de Mantenimiento (`specs/21`).

---

## ✅ HITO 13: Vistas Frontend (Parte B), Endpoint MCP Protegido para IA (`Hermes`/`Claude`), Dockerfiles y Graphify

> **Archivos Guía:** `specs/22_FRONTEND_VIEWS_WEBFIG_CONSOLE_RINGBUFFER_AND_LAYERS.md`, `specs/23_FRONTEND_VIEWS_APPROVALS_DIFF_BULK_NOC_AND_AUDITOR.md`, `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md` y `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`

- [x] **13.1** Clase `TelemetryRingBuffer<T>` en memoria RAM (`MAX_POINTS = 5400` para 3 horas a 1 tick/2s con reactividad superficial `shallowRef` y limpieza total en `onBeforeUnmount` al salir del router) (`specs/22`).
- [x] **13.2** Layout de Consola WebFig (`RouterWebFigLayout.vue`), Barra de Pestañas de Trabajo con `<KeepAlive :max="5">` (`RouterWorkspaceTabsBar.vue`) y Dashboard de Gráficas Efímeras estilo WinBox (`RouterLiveDashboardView.vue`) renderizadas sobre **`<canvas>` 2D acelerado con `requestAnimationFrame`** (`specs/22`).
- [x] **13.3** Vistas especializadas de WebFig Capa 1 (`InterfacesAndSfpView.vue`, `FirewallRulesView.vue` con Drag & Drop + Safe Mode, `RoutingBgpOspfView.vue`, `PppAndQueuesView.vue`, `LiveToolsDiagnosticsView.vue`) y Renderizador Universal de Capa 2 (`DynamicLayer2ResourceView.vue`) (`specs/22`).
- [x] **13.4** Bandeja de Aprobaciones Maker-Checker (`ApprovalsInboxView.vue`), Historial de Backups (30 días) y Comparador Visual Lado a Lado estilo Git (`RscGitDiffViewer.vue`) (`specs/23`).
- [x] **13.5** Asistente de Plantillas, Acciones Masivas y Updates de RouterOS (`BulkOperationsAndUpdatesView.vue`), Pantalla Completa **Wallboard NOC (`NocWallboardView.vue`)** y Consola Forense del **Auditor (`ImmutableAuditLogsView.vue`)** (`specs/23`).
- [x] **13.6** **Cierre de Arquitectura Frontend con Graphify (En Docker):** Ejecutar `docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify` dentro de `./vue3/` para generar `vue3/graphify-out/GRAPH_REPORT.md` y el grafo de componentes/stores del Frontend (`specs/18`, `29`).
- [x] **13.7** **Dockerfile Multi-Stage de Producción Frontend (`vue3/Dockerfile`), `docker-compose.prod.yml` (con KeyDB Multi-Hilo) y Script `build.sh`:** Crear `vue3/Dockerfile` (builder `pnpm build` + runtime `nginx:1.27-alpine` no-root con `ARG BUILD_DATE` y `vue3/nginx/default.conf`), `docker-compose.prod.yml` (usando `eqalpha/keydb:alpine` por defecto y bloque comentado de `DragonflyDB` para alto rendimiento) y el script `build.sh` en la raíz con `docker buildx` (`container-builder`, `tonistiigi/binfmt` y limpieza `prune -af`) (`specs/01`).
- [x] **13.8** **Endpoint MCP Protegido (`POST /api/v1/mcp` JSON-RPC 2.0 Streamable HTTP) para Agentes IA (`Hermes Agent`, `Claude`):**
  - Implementar `fastapi/src/schemas/mcp.py` y `fastapi/src/api/v1/mcp.py` conforme a `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`, controlado por `ROSGRID_MCP_ENABLED` (`false` por defecto) y `ROSGRID_MCP_RATE_LIMIT_PER_MIN` (`30` req/min en KeyDB), restringido exclusivamente al rol `SERVICE_ACCOUNT` con validación de lista blanca CIDR.
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

> **Archivos Guía:** `specs/24`, `specs/25`, `specs/26`, `specs/27`, `specs/28`, `specs/29` + `fastapi/graphify-out/GRAPH_REPORT.md` + `vue3/graphify-out/GRAPH_REPORT.md`

- [x] **15.1** Catálogo de Mocks RouterOS v7 (`routeros_v7_payloads.py`) y Suite Unitaria Backend completa (`fastapi/tests/**/*.unit.py` con cobertura >= 95% alcanzando 95.03% con 284 tests) (`specs/24`, `25`).
- [x] **15.2** Certificación Estática y Unitaria Backend en Docker (`make qa-lint` con `Ruff`, `Mypy strict`, `Radon` Grado A `CC <= 5` / `MI >= B`, `Bandit`, `Pip-Audit` y `make qa-unit`) (`specs/24`, `25`).
- [x] **15.3** Certificación Dinámica, Contratos, BDD, DAST y Caos Backend en Docker (`Schemathesis`, `Karate Labs`, `OWASP ZAP Baseline`, `py-spy` y `--profile chaos` con `Pumba + Locust + Prometheus`) (`specs/26`).
- [x] **15.4** Suite Unitaria Frontend (`vue3/src/__tests__/*.unit.ts` con Vitest >= 95% en las 4 métricas) y Mutación con `Stryker` en Docker (`make qa-lint`, `make qa-unit`, `make qa-mutation`) (`specs/27`).
- [x] **15.5** Suite E2E, Accesibilidad WCAG 2.1 AA (`@axe-core/playwright` = 0 violaciones + snapshots deterministas), `Lighthouse CI` (`>= 90` / `>= 95` a11y), `Karate UI` en Docker (`make qa-perf`, `make qa-e2e`, `make qa-bdd`) y actualización final de `TESTING.md` (`specs/28`, `29`).

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

> **Archivos Guía:** `specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md` y `specs/34_TENANT_FEATURE_FLAGS_AND_GOVERNANCE_PANEL.md`

- [x] **16.1** Migración Alembic `0005_tenant_feature_flags_and_technical_qos.py` con atributos booleanos en `tenants` (`isp_module_enabled`, `bgp_looking_glass_enabled`, `sfp_ddm_telemetry_enabled`, `ipfix_analytics_enabled`, `enforce_maker_checker`, `auto_safemode_enforced`, `ai_mcp_integration_enabled`, `nightly_backups_enabled`, `outbound_webhooks_enabled`, `config_drift_monitoring_enabled`, `cis_audit_enabled`, `sdwan_orchestrator_enabled`, `capsman_wifi_enabled`, `sla_tracker_enabled`, `mass_outage_threshold`, `default_locale`).
- [x] **16.2** Refactorización de `subscriber_devices` en PostgreSQL: Purga estricta de nombres, cédulas y datos personales. Identificación técnica exclusiva por `device_serial`, `endpoint_identifier`, router y puerto.
- [x] **16.3** Panel de Feature Flags en Frontend (`TenantsManagementView.vue`): Pestaña táctica *"Módulos & Capacidades"* con switches de alta densidad para conmutación inmediata por tenant por el Superadmin.
- [x] **16.4** Seguridad y Reactividad de Módulos: Dependencia FastAPI `require_feature(flag_name)` que responde HTTP 403 `FEATURE_MODULE_DISABLED`, y adaptación dinámica de `RgResponsiveShell.vue`, `RgCommandPalette.vue` y rutas Vue Router para ocultar módulos inactivos.
- [x] **16.5** Branding Institucional, Footer Global y Enlaces Oficiales:
  - Modificación de `LoginView.vue`: Pie de página discreto y elegante con icono SVG accesible de GitHub enlazando a `https://github.com/tecno-consultores/RoSGrid/`, atribución *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/)"*, versión del sistema y badge de *"Licencia GNU GPLv3"*.
  - Modificación de `RgResponsiveShell.vue`: Pie de página global autenticado en la base del sitio mostrando *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/) • Licencia GNU GPLv3"* e icono de GitHub enlazando al repositorio, en tipografía reducida con ratio de contraste WCAG 2.1 AA.

---

## ✅ HITO 17: QoS Técnico, API de Aprovisionamiento e Idempotencia (Fase 2)

> **Archivo Guía:** `specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md`

- [x] **17.1** Modelo y Endpoints de `BandwidthProfile`: Tasas Up/Down nominales, parámetros de Burst (`burst_down_kbps`, `burst_up_kbps`, `burst_threshold`, `burst_time`), Prioridad (1-8) y colas PCQ / Simple Queues en MikroTik v7.
- [x] **17.2** API de Aprovisionamiento Técnico Idempotente (`Idempotency-Key` UUIDv7 obligatorio):
  - `POST /api/v1/network-services/{id}/isolate` (agrega a lista de firewall `AISLADOS_TECNICO` o conmuta a 64k).
  - `POST /api/v1/network-services/{id}/restore` (retira aislamiento y restaura perfil en caliente).
  - `POST /api/v1/network-services/{id}/change-rate-limit` (modifica límites de cola sin desconectar sesión física).
- [x] **17.3** Despachador de Webhooks Salientes: Worker asíncrono que envía payloads firmados con HMAC-SHA256 ante eventos técnicos de red (`DEVICE_ACTIVATED_GPS`, `DEVICE_ISOLATED`, `DEVICE_RESTORED`, `MASS_OUTAGE_TRIGGERED`).

---

## ✅ HITO 18: Diagnóstico 360°, BGP Looking Glass e IPFIX (Fase 3)

> **Archivos Guía:** `specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md` y `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md`

- [x] **18.1** Suite de Diagnóstico 360° (`POST /api/v1/diagnostics/endpoint-360`):
  - Ping Multi-MTU (64B, 512B, 1472B) para detección de dispersión de latencia y fragmentación DF-bit.
  - Parser automático de motivos de desconexión en `/log` de RouterOS (`link down`, `peer is not responding`, `user request`, `auth failed`).
  - Muestreo Torch en tiempo real (3 segundos) filtrado por IP/MAC con Top 5 de flujos activos.
- [x] **18.2** Consola BGP Looking Glass Interno: Endpoints `GET /api/v1/bgp/looking-glass/route` y `/advertised` para inspeccionar rutas, AS-Path, comunidades BGP y prefijos exportados a proveedores de tránsito sin dar acceso por SSH.
- [x] **18.3** Detección de Tráfico Anómalo / Flujos IPFIX: Detección de clientes con tasas anormales de PPS o conexiones masivas con botón de mitigación rápida (FastDrop / Blackhole con Safe Mode y auditoría WORM inmutable).

---

## 🗺️ HITO 19: Mapas Separados, Telemetría Efímera, Responsive e i18n (Fase 4)

> **Archivo Guía:** `specs/32_ISP_OPERATIONS_TECHNICAL_QOS_AND_FIELD_TOOLKIT.md`

- [x] **19.1** Mapa Exclusivo de Clientes/ONUs (`OsmOnuMap.vue` en `/subscribers/map`): Completamente separado del mapa de routers de infraestructura, con telemetría efímera Zero-Metrics (Verde < 40ms, Naranja 40-120ms o pérdida leve, Rojo timeout).
- [x] **19.2** Alerta de Caída Masiva (Mass Outage Alert): Detección automática en segundo plano de caídas simultáneas > `mass_outage_threshold` (por defecto 10), con alarma visual/sonora en NOC y registro forense en `audit_logs` con hash encadenado HMAC-SHA256.
- [x] **19.3** Corrección de Responsive del Técnico de Calle (`FieldTechMobileView.vue`): Eliminación del contenedor fijo vertical (`max-width: 480px`), maquetación 100% fluida para móvil, tablet y laptop, campo simplificado solo con Serial de ONU, y botón prominente *"📍 Capturar Coordenadas GPS"* al activar.
- [x] **19.4** Arquitectura de Internacionalización (i18n): Base modular con `locales/es.json` y `locales/en.json`, composable `useI18n()` y selector táctico de idioma en barra de herramientas superior.

---

## 🏢 HITO 20: Suite Corporativa — Config Drift, CIS Hardening, SD-WAN, Rogue DHCP, SLA y CAPsMAN

> **Archivo Guía:** `specs/33_ENTERPRISE_FLEET_MANAGEMENT_AND_SECURITY_COMPLIANCE.md`

- [x] **20.1** Detección de Desviación de Configuración (*Config Drift Detection*): Comparador contra Plantilla Maestra (*Golden Baseline Template*), visor de diferencias Git Diff en rojo/verde y botón de remediación en 1 clic (*Auto-Revert*) con Safe Mode y Maker-Checker.
- [x] **20.2** Orquestador SD-WAN WireGuard Hub & Spoke: Generación automática de llaves, direccionamiento `/30` o `/31`, inserción de peers y enrutamiento dinámico OSPF sobre WireGuard con failover multi-WAN recursivo.
- [x] **20.3** Auditoría de Seguridad & Endurecimiento CIS Benchmark para RouterOS: Escaneo de las 10 directivas críticas de ciberseguridad, cálculo de Security Score (0-100) y botón de auto-endurecimiento (*Auto-Hardening*).
- [x] **20.4** Detección de Rogue DHCP & Seguridad de Conmutación: Monitoreo de eventos de DHCP Snooping en switches y bridges MikroTik, alertas al NOC con puerto físico y MAC del intruso, y deshabilitación preventiva de puerto.
- [x] **20.5** Monitor de Cumplimiento de SLA para Enlaces Dedicados: Medición continua de jitter, latencia y pérdida hacia el gateway del carrier con generador de reportes de cumplimiento (PDF/CSV) para reclamos de penalización.
- [x] **20.6** Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2): Orquestación de SSIDs (Corporativo WPA3-Enterprise 802.1X, Invitados aislado y dispositivos IoT) con telemetría de señal RSSI y trazabilidad de roaming 802.11r.

---

## ✅ HITO 21: Servidor MCP Ampliado para Agentes IA y Certificación QA 11X Final

> **Archivos Guía:** `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`, `specs/24` a `specs/29` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`

- [x] **21.1** Expansión de Tools MCP para Agentes de IA: Nuevas herramientas para sustitución o asistencia técnica autónoma (`rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit`, `rosgrid_run_360_diagnostics`, `rosgrid_query_bgp_looking_glass`, `rosgrid_check_config_drift`, `rosgrid_run_cis_audit`, `rosgrid_detect_mass_outage`).
- [x] **21.2** Actualización de Documentación: Sincronización completa de `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md` con los nuevos contratos.
- [x] **21.3** Certificación Estándar QA 11X en Docker: Cobertura unitaria >= 95% en backend (`sinfallas/base-python-uv:3.15`) y frontend (`sinfallas/base-node-ionic:26`), ejecución de la suite de contratos Front-Back y compilación limpia del bundle de producción.

---

## 📦 HITO 22: Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`build.sh`)

> **Archivo Guía:** `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [x] **22.1** Auditar los `Dockerfile`, `docker-compose*.yml` e infraestructura con `./auditar-infra.sh` y escaneo Trivy de imágenes (`CRITICAL,HIGH = 0`).
- [x] **22.2** **Especificación y Endurecimiento de Pruebas Smoke Locales (`probar-prod-local.sh`):** Actualización de especificaciones (`specs/31`), manual operativo (`docs/08`) y bitácora QA 11X (`TESTING.md`) incorporando la ejecución obligatoria de la suite de 24 contratos Front-Back (`validar_comunicacion_front_back.py`), validación del proxy inverso Nginx (`:${UI_PORT}/api/...`), sondeo real JSON-RPC 2.0 MCP (`POST /api/v1/mcp`), supervisión activa de healthchecks y logs de `rosgrid-worker`, verificación de ocultamiento HTTP 404 de Swagger/OpenAPI en producción, pruebas negativas de autenticación (401) y verificación de aislamiento de puertos internos DB/KeyDB.
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
- [x] **22.7** **Suite de Pruebas BDD E2E Karate Labs para el 100% de la Interfaz Web:** Expansión de `vue3/test/ui_business_flow.feature` a 16 escenarios BDD de extremo a extremo cubriendo la totalidad de vistas y flujos funcionales del sistema (Login & 2FA, Dashboard y Refresco de Flota, Inventario y Búsqueda, WebFig Live y Pestañas KeepAlive, Maker-Checker, Respaldos y Git Diff, Operaciones Masivas y Paquetes, Wallboard NOC, Auditoría Forense WORM, Gestión Multi-Tenant, Matriz RBAC, Kill-Switch de Sesiones, IPAM Dual-Stack, Toolkit de Campo Móvil, Mapa de Abonados/ONUs, y Compliance Corporativo CIS/Drift/SD-WAN), sincronización idéntica en `examples/vue3/test/ui_business_flow.feature` y validación con Vitest (38/38 suites, 262/262 tests) y `vue-tsc` (0 errores).
- [x] **22.8** **Enriquecimiento Visual con Diagramas Mermaid en Toda la Documentación:** Inserción masiva de diagramas de arquitectura, secuencias criptográficas, árboles de decisión y flujos de datos en todos los manuales del sistema (`README.md`, `INSTALL.md`, `SECURITY.md` y `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` hasta `docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md`).
- [x] **22.9** **Investigación Técnica y Hojas de Ruta de Migración a Python 3.15 y Node.js 26 LTS:**
  - `docs/10_REPORTE_INVESTIGACION_PYTHON_3_15.md`: Investigación sobre Free-Threading / No-GIL (PEP 703) Tier-1, Tier-2 JIT, PEP 649 y migración a `sinfallas/base-python-uv:3.15`.
  - `docs/11_REPORTE_INVESTIGACION_NODE_26.md`: Investigación sobre Native Type Stripping, V8 14.x, Temporal API y migración a `sinfallas/base-node-ionic:26`.
- [x] **22.10** **Suite de Pruebas BDD Integral Karate Labs para el 100% de la API REST FastAPI:** Expansión de `fastapi/test/api_test.feature` a 54 escenarios BDD exhaustivos cubriendo todos y cada uno de los 35 submódulos y endpoints de la API REST (Observabilidad, Auth, Multi-Tenant, Usuarios, Sesiones, Inventario, TOFU, Bóveda 2FA, IPAM, QoS, Dispositivos ONU, Servicios de Red, Field Ops, Mantenimiento, WebFig L1/L2, Maker-Checker, Backups, Operaciones Masivas, Notificaciones, WORM, MCP JSON-RPC 2.0, Diagnóstico 360°, BGP Looking Glass, Tráfico IPFIX, Compliance CIS/Drift, SD-WAN, Switching, SLA, WiFi y RBAC), sincronización idéntica en `examples/fastapi/test/api_test.feature` y certificación en `TESTING.md`.
- [x] **22.11** **Migración Integral de Runtime a Python 3.15 y Node.js 26 LTS:** Actualización de `fastapi/Dockerfile` (`sinfallas/base-python-uv:3.15`), `vue3/Dockerfile` (`sinfallas/base-node-ionic:26`), `docker-compose.yml`, `fastapi/docker-compose.qa.yml`, `vue3/docker-compose.qa.yml`, metadatos en `pyproject.toml` (`requires-python = ">=3.15"`) y `package.json` (`engines: { "node": ">=26.0.0" }`), sincronización completa de la bitácora histórica de hitos (Hitos 0 al 22.11) en `TESTING.md`, gobernanza raíz y reportes técnicos `docs/10` y `docs/11`.
- [x] **22.12** **Auditoría Integral de Ciberseguridad y Mitigación de Vulnerabilidades (FastAPI + Vue 3):**
  - Desacoplamiento de `CSRFProtectionMiddleware` para extracción autónoma de JWT desde cookies (`__Host-rg_at` / `rg_at`) y exención de clientes API puros con token Bearer según directrices OWASP.
  - Sanitización estricta anti-XSS mediante `escapeHtml` en popups Leaflet OpenStreetMap (`OsmRouterMap.vue` y `OsmOnuMap.vue`).
  - Validación anti-SSRF integral en el direccionamiento de routers (`validate_router_target_url`) bloqueando loopback, cloud metadata y hostnames de contenedores Docker tanto en la API como en el asistente CSV masivo.
  - Tolerancia a carreras concurrentes (*Grace Period Leeway* de 5 segundos) en rotación de refresh tokens (`rotate_refresh_token`), eliminando falsos positivos de robo por múltiples pestañas.
  - Aislamiento multi-tenant y por operador en `IdempotencyMiddleware` mediante llaves con prefijo `rg:{tenant_id}:{user_id}:idemp:{key}`.
  - Endurecimiento de la expresión regular de CORS en desarrollo a `(localhost|127.0.0.1)`.
- [x] **22.13** **Consolidación de Calidad, Resolución Integral de Diagnósticos y Robustecimiento DevOps:**
  - Normalización y certificación estricta con `markdownlint-cli` (0 errores) y diagramas Mermaid modernos (`flowchart`) en toda la enciclopedia técnica de `specs/` y `docs/`.
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

> **Archivos Guía:** `specs/35_FLEET_AUTOMATION_TOPOLOGY_L2_SYSLOG_AND_PROMETHEUS.md` y `docs/12_DISENO_TOPOLOGIA_L2_SYSLOG_Y_AUTOMATIZACION.md`

- [x] **23.1** **Especificación Técnica y Arquitectura de Datos (`specs/35` y `docs/12`):**
  - Definición integral de estructuras de datos en memoria, preservando estrictamente la premisa *Zero-Metrics Storage* (cero almacenamiento de series temporales en PostgreSQL 17).
  - Especificación del Grafo Acíclico Dirigido (DAG) para dependencias de energía PoE, ordenamiento inverso de actualización (Hojas PD primero, Raíces PSE al final) y circuito de corte de emergencia *Fleet Safety Stop* (umbral 1% de fallos post-reinicio).
  - Definición del modelo de cruce local de boletines CVE (`cve_catalog_ros.json`) con cero exposición de telemetría a la nube exterior.
  - Diseño del receptor asíncrono Syslog en puerto no privilegiado 5514 (UDP/TCP) con RingBuffer volátil en KeyDB (`MAXLEN 500`) y filtro de eventos críticos en vuelo (*linkDown*, *bgp drop*, *login attack*).
  - Diseño del puente de métricas hacia Prometheus (`GET /api/v1/metrics/fleet`) autenticado por token, habilitando dashboards en Grafana sin saturación de disco local.
- [x] **23.2** **Plantilla Estandarizada para Enrolamiento Masivo de Syslog RouterOS v7:**
  - Creación del script predefinido para `/system/logging/action` y `/system/logging` adaptable con variables `{{ROSGRID_SERVER_IP}}` y `{{ROSGRID_SYSLOG_PORT}}` para despliegue desatendido mediante *Bulk Ops*.
- [x] **23.3** **Ampliación del Servidor MCP y Skill Oficial (`rosgrid-noc-operator`):**
  - Incorporación al diseño del servidor MCP de 4 nuevas herramientas semánticas: `rosgrid_get_l2_topology`, `rosgrid_check_fleet_cves`, `rosgrid_get_recent_syslog` y `rosgrid_execute_poe_aware_upgrade` (total 18 herramientas).
  - Actualización de la Skill `.agents/skills/rosgrid-noc-operator/SKILL.md` incorporando SOP-6 (Triaje de caídas de enlace vía Syslog) y SOP-7 (Planificación PoE-Aware con Safety Stop).
  - Sincronización idéntica en el catálogo global de Antigravity (`~/.gemini/config/skills/rosgrid-noc-operator/`).
- [x] **23.4** **Implementación Backend & Modelos:**
  - Migración Alembic `0007_fleet_automation_l2_syslog_flags.py` con 4 feature flags tácticos en `Tenant`.
  - Catálogo local base inmutable de CVEs (`cve_catalog_ros.json`) con 6 firmas de RouterOS v7, motor semver `cve_matcher.py` y sincronizador dinámico `POST /api/v1/inventory/cves/sync`.
  - Colector Syslog efímero UDP/TCP 5514 BSD (`syslog_collector.py`) con RingBuffer KeyDB (500 eventos por router, 0 persistencia en Postgres) y endpoint de plantilla `/api/v1/routers/syslog/template`.
  - Motor de topología física Layer 2 (`topology_l2.py`) cruzando MNDP/LLDP y detección de alimentación PoE PSE/PD con endpoint `/api/v1/topology/l2` y caché KeyDB de 60s.
  - Exportador Prometheus OpenMetrics `/api/v1/metrics/fleet` sin almacenamiento en base de datos.
  - Orquestador de actualizaciones masivas PoE-aware en orden topológico inverso con Safety Stop automático del 1%.
  - Expansión del servidor MCP a 20 herramientas (`rosgrid_get_l2_topology`, `rosgrid_check_fleet_cves`, `rosgrid_get_recent_syslog`, `rosgrid_execute_poe_aware_upgrade`).
  - Suite de pruebas de contratos y BDD en Karate Labs (`fastapi/test/api_test.feature` y `examples/fastapi/test/api_test.feature`, Escenarios 55-61) y 23 tests unitarios Pytest en Docker (100% pasando, Grado A Radon CC <= 5, 0 errores Mypy Strict).
- [x] **23.5** **Implementación Frontend (Vue 3 + Pinia):**
  - Vista interactiva de Topología L2 con Canvas 2D táctica (`L2TopologyView.vue`), renderizado a 60 FPS con Pan/Zoom, badges de PoE (Watts), indicadores LED de estado Online/Offline, drawer táctico de detalles y fallback accesible para screen readers (`role="region"`).
  - Matriz de Vulnerabilidades CVE táctica (`FleetCveMatrix.vue`), 4 tarjetas KPI evaluadas (Evaluados, Vulnerables, Críticos, Versión Recomendada), filtro reactivo por severidad (CRITICAL/HIGH/MEDIUM/LOW), sincronización remota contra NIST NVD y botón directo a remediación masiva.
  - Insignia y botón de acceso directo `[ 🛡️ Matriz de CVEs ]` en la tabla de inventario (`RouterInventoryView.vue`).
  - Terminal de eventos Syslog en vivo en la consola WebFig del router (`RouterSyslogTerminalView.vue`), lectura de RingBuffer efímero en KeyDB (UDP/TCP 5514), badges tácticos de severidad (CRIT, WARN, INFO), auto-scroll inteligente y modal con script CLI de enrolamiento MikroTik.
  - Asistente de actualización masiva con conmutador *PoE-Aware* y selector de umbral *Safety Stop* (1%, 2%, 5%) (`BulkOperationsAndUpdatesView.vue`).
  - Menú lateral WebFig v7 actualizado con enlace directo a Syslog Live RingBuffer (`RouterSidebarMenu.vue`) y barra de navegación responsive global con Topología L2 y CVEs (`RgResponsiveShell.vue`).
  - Suite de pruebas de contratos y BDD en Karate Labs UI (`vue3/test/ui_business_flow.feature` y `examples/vue3/test/ui_business_flow.feature`, Escenarios 17-20) y 17 tests unitarios Vitest en Docker (100% pasando, 0 violaciones ESLint/SonarJS, 0 errores TypeScript strict).
- [x] **23.6** **Certificación Integral QA 11X Pre-Lanzamiento y Validación Local de Producción:**
  - Auditoría de Shell Scripts con ShellCheck (0 errores, 0 advertencias en todos los scripts `.sh`).
  - Backend QA (`sinfallas/base-python-uv:3.15`): 463 pruebas unitarias aprobadas al 100% en 29.09s, 95.11% de cobertura de código real (`--cov-fail-under=95`), Ruff check y format sin desviaciones en 159 archivos, Mypy strict (0 errores en 114 archivos), Bandit SAST (0 problemas de seguridad en 19.941 líneas) y pip-audit (0 vulnerabilidades conocidas en dependencias de producción y desarrollo).
  - Frontend QA (`sinfallas/base-node-ionic:26`): 297 pruebas unitarias aprobadas al 100% en 43 suites con Vitest, vue-tsc (0 errores de tipos TypeScript) y compilación de producción con Vite limpia en 3.99s.
  - Validación de Producción Local (`./probar-prod-local.sh`): 6 fases completadas exitosamente al 100% (construcción de imágenes locales, healthchecks de contenedores en aislamiento, pruebas sintéticas HTTP, endpoints de documentación 404 estricto, fail-closed 401, Bearer token MCP, invocación JSON-RPC 2.0 y 24/24 contratos Front-Back validados con `validar_comunicacion_front_back.py`).
  - Verificación de secretos (`./verificar-secretos.sh`): Árbol de trabajo auditado con 0 credenciales ni tokens expuestos.

---

## 📦 HITO 24: Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`build.sh`)

> **Archivo Guía:** `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`

- [ ] **24.1** Actualizar `CHANGELOG.md` consolidando los cambios de `[Unreleased]` dentro del lanzamiento oficial `[1.0.0]` con las métricas certificadas en `TESTING.md`.
- [ ] **24.2** Ejecutar `./build.sh` (como usuario no-root) con `docker buildx` (`container-builder` + `tonistiigi/binfmt`) para construir y publicar `sinfallas/rosgrid-backend:latest` (`:1.0.0`) y `sinfallas/rosgrid-frontend:latest` (`:1.0.0`) en Docker Hub y limpiar cachés con `prune -af`.
