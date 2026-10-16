# 🗺️ ROADMAP GRANULAR DE EJECUCIÓN (31 SPECS) — RoSGrid

## 📍 Punto de Control Actual (Checkpoint)
- **Hito Actual en Curso:** Hito 15 (Ejecución de Pruebas y Certificación Estándar QA 11X)
- **Último Archivo de `specs/` Procesado:** Hito 14 completo (`docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` a `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`, sincronización de gobernanza raíz y especificaciones AST)
- **Último Módulo de Código Creado:** Hito 14 completo: Enciclopedia documental en `docs/` (7 manuales oficiales completos con diagramas Mermaid, tablas técnicas, especificación exhaustiva de API REST/WebSockets y guía de integración IA MCP para Hermes Agent y Claude), más gobernanza raíz actualizada (`README.md`, `INSTALL.md`, `SECURITY.md`, `RESOURCES.md`, `FAQ.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`).
- **Siguiente Paso Inmediato:** Hito 15 (Certificación dinámica, BDD, DAST, Caos y E2E/A11y Frontend bajo orden explícita del usuario).

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
- [x] **10.5** **Dockerfile Multi-Stage de Producción Backend (`fastapi/Dockerfile`):** Crear `fastapi/Dockerfile` basado en `sinfallas/base-python-uv:3.13` con soporte `ARG BUILD_DATE`, dependencias `--no-dev`, usuario sin privilegios (`non-root`) y `scripts/entrypoint.sh` (`specs/01`).
- [x] **10.6** **Paquete de Optimización de Alto Rendimiento Backend, DB y KeyDB Multi-Hilo:**
  * Sustituir `redis:7-alpine` por `eqalpha/keydb:alpine` (`keydb-server --server-threads 2` y healthcheck `keydb-cli`) en `docker-compose.yml`, `fastapi/docker-compose.qa.yml` y `specs/01` (documentando `DragonflyDB` como perfil de alta escala).
  * Configurar `ORJSONResponse` como `default_response_class` en `fastapi/src/main.py`, serialización `orjson` en frames WebSocket, desactivación estricta de Swagger/ReDoc/OpenAPI cuando `ROSGRID_ENV == "production"` y activar `--loop uvloop --http httptools` en `fastapi/scripts/entrypoint.sh`.
  * Implementar reutilización de pool `Keep-Alive` TLS (`limits=httpx.Limits(max_keepalive_connections=20, keepalive_expiry=60.0)`) en `src/mikrotik/client.py` y ejecución por lotes con `pipeline()` hacia KeyDB en `src/redis_layer/zero_metrics_monitor.py`.
  * Añadir índice `BRIN` (`ix_audit_logs_created_at_brin` con `postgresql_using='brin'`) sobre `audit_logs(created_at)` en `0003_operations_backups_immutable_audit.py` y re-validar `make qa-lint && make qa-unit`.

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
  * Implementar `fastapi/src/schemas/mcp.py` y `fastapi/src/api/v1/mcp.py` conforme a `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md`, controlado por `ROSGRID_MCP_ENABLED` (`false` por defecto) y `ROSGRID_MCP_RATE_LIMIT_PER_MIN` (`30` req/min en KeyDB), restringido exclusivamente al rol `SERVICE_ACCOUNT` con validación de lista blanca CIDR.
  * Exponer las 8 Tools semánticas de diagnóstico y operación (`rosgrid_list_inventory`, `rosgrid_get_router_health`, `rosgrid_check_sfp_optical_ddm`, `rosgrid_inspect_routing_bgp_ospf`, `rosgrid_run_live_diagnostic`, `rosgrid_compare_config_diff`, `rosgrid_reconnect_pppoe_client` y `rosgrid_propose_network_change` con intercepción obligatoria **Maker-Checker** + **Safe Mode 60s** y registro en **WORM**).
  * Crear suite unitaria `fastapi/tests/test_mcp_endpoint.unit.py` (`make qa-lint && make qa-unit` >= 95% de cobertura) y actualizar `fastapi/graphify-out/GRAPH_REPORT.md` con Graphify en Docker antes del Hito 14.

---

## ✅ HITO 14: Documentación Oficial en `docs/`, Referencia de API, Guía de Integración IA (MCP) y Gobernanza Raíz (Basada en `GRAPH_REPORT.md`)
> **Propósito:** Generar la documentación técnica, operativa, de despliegue, la especificación completa de la API y la guía detallada de integración del servidor MCP para agentes IA (`Hermes`, `Claude`) dentro de `docs/`, más la sincronización de los archivos de gobernanza de la raíz tomando como referencia `fastapi/graphify-out/GRAPH_REPORT.md` y `vue3/graphify-out/GRAPH_REPORT.md`.
- [x] **14.1** `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md`: Requisitos de infraestructura, configuración de variables `.env` (incluyendo `ROSGRID_MCP_ENABLED`), generación de llaves criptográficas (`AES-256-GCM`, `JWT`, `CSRF`), arquitectura en memoria con **KeyDB Multi-Hilo por defecto** y guía de activación del **Perfil de Alto Rendimiento con DragonflyDB** para grandes flotas ISP, despliegue con `docker-compose.yml` / `docker-compose.prod.yml`, uso de `build.sh` y auto-migración con `pg_advisory_lock`.
- [x] **14.2** `docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md`: Guía paso a paso con comandos CLI de RouterOS v7.1+ para habilitar `/ip/service/www-ssl`, generar certificado autofirmado para pinning TOFU, permisos mínimos del usuario API y explicación del mecanismo *Safe Mode (Dead Man's Switch)* vía `/system/scheduler`.
- [x] **14.3** `docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md`: Administración de empresas (Tenants), detalle de los **11 roles RBAC**, uso de la matriz de asignación de routers por técnico, consulta de la Bóveda con *Step-Up Auth* (30s) y operación del *Kill-Switch* de sesiones en vivo.
- [x] **14.4** `docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md`: Uso diario de la consola WebFig (Capa 1 y Capa 2 con pestañas `KeepAlive` y densidad adaptativa), gráficas efímeras en vivo estilo WinBox (`RingBuffer`), flujo de aprobaciones *Maker-Checker*, comparador Diff estilo Git de respaldos `.rsc`, importación masiva por CSV, ventanas de mantenimiento y modo **Wallboard NOC**.
- [x] **14.5** `docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md`: Guía exclusiva para el rol **Auditor**, verificación criptográfica de la cadena de custodia inmutable WORM (`audit_logs`), registro de decisión de arquitectura (ADR) sobre la exclusión deliberada de terminal CLI/SSH interactiva libre y diagramas de arquitectura en formato Mermaid extraídos de `graphify-out/GRAPH_REPORT.md`.
- [x] **14.6** `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`: Documentación exhaustiva de todos los endpoints REST (`/api/v1/*`, incluyendo `/api/v1/mcp`) y canales WebSocket (`/ws/v1/*`) de RoSGrid (métodos HTTP, rutas, cabeceras obligatorias `X-CSRF-Token` / `Idempotency-Key`, esquemas JSON de entrada/salida, códigos de estado `200`/`202 Maker-Checker`/`401`/`403`/`409`/`422` y uso con `SERVICE_ACCOUNT`), reemplazando a Swagger/ReDoc que permanecen desactivados en producción (`ROSGRID_ENV=production`).
- [x] **14.7** `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`: Documentación técnica detallada del **Servidor MCP Protegido (`/api/v1/mcp`)** para conectar agentes autónomos e interactivos (**Hermes Agent**, **Claude Desktop / Claude Code** y clientes MCP compatibles): activación mediante `ROSGRID_MCP_ENABLED=true`, provisión de credenciales `SERVICE_ACCOUNT` con restricción CIDR y alcances por router, catálogo completo de las 8 Tools MCP con sus esquemas JSON-RPC 2.0 de entrada/salida, configuración paso a paso en Hermes Agent y Claude, recepción de Webhooks firmados (`HMAC-SHA256`) para diagnóstico NOC 24/7 y gobierno humano de cambios mediante *Maker-Checker* + *Safe Mode*.
- [x] **14.8** **Sincronización de Archivos de Gobernanza en la Raíz:** Revisar y actualizar (asegurando que reflejen KeyDB por defecto, DragonflyDB como perfil opcional de alto rendimiento, el conector MCP protegido y las optimizaciones implementadas) los archivos `README.md`, `INSTALL.md`, `SECURITY.md`, `RESOURCES.md`, `FAQ.md`, `CONTRIBUTING.md` y `CODE_OF_CONDUCT.md`.

---

## 🧪 HITO 15: Ejecución de Pruebas y Certificación Estándar QA 11X (Bajo Orden Explícita del Usuario)
> **Archivos Guía:** `specs/24`, `specs/25`, `specs/26`, `specs/27`, `specs/28`, `specs/29` + `fastapi/graphify-out/GRAPH_REPORT.md` + `vue3/graphify-out/GRAPH_REPORT.md`
- [x] **15.1** Catálogo de Mocks RouterOS v7 (`routeros_v7_payloads.py`) y Suite Unitaria Backend completa (`fastapi/tests/**/*.unit.py` con cobertura >= 95% alcanzando 95.03% con 284 tests) (`specs/24`, `25`).
- [x] **15.2** Certificación Estática y Unitaria Backend en Docker (`make qa-lint` con `Ruff`, `Mypy strict`, `Radon` Grado A `CC <= 5` / `MI >= B`, `Bandit`, `Pip-Audit` y `make qa-unit`) (`specs/24`, `25`).
- [ ] **15.3** Certificación Dinámica, Contratos, BDD, DAST y Caos Backend en Docker (`Schemathesis`, `Karate Labs`, `OWASP ZAP Baseline`, `py-spy` y `--profile chaos` con `Pumba + Locust + Prometheus`) (`specs/26`).
- [ ] **15.4** Suite Unitaria Frontend (`vue3/src/__tests__/*.unit.ts` con Vitest >= 95% en las 4 métricas) y Mutación con `Stryker` en Docker (`make qa-lint`, `make qa-unit`, `make qa-mutation`) (`specs/27`).
- [ ] **15.5** Suite E2E, Accesibilidad WCAG 2.1 AA (`@axe-core/playwright` = 0 violaciones + snapshots deterministas), `Lighthouse CI` (`>= 90` / `>= 95` a11y), `Karate UI` en Docker (`make qa-perf`, `make qa-e2e`, `make qa-bdd`) y actualización final de `TESTING.md` (`specs/28`, `29`).

---

## 📦 HITO 16: Cierre de `CHANGELOG.md`, Auditoría Trivy y Publicación en Docker Hub (`build.sh`)
> **Archivo Guía:** `specs/01_DOCKER_INFRASTRUCTURE_AND_IMMUTABLE_IMAGES.md`
- [ ] **16.1** Auditar los `Dockerfile`, `docker-compose*.yml` e infraestructura con `./auditar-infra.sh` y escaneo Trivy de imágenes (`CRITICAL,HIGH = 0`).
- [ ] **16.2** Actualizar `CHANGELOG.md` consolidando los cambios de `[Unreleased]` dentro del lanzamiento oficial `[1.0.0]` con las métricas certificadas en `TESTING.md`.
- [ ] **16.3** Ejecutar `./build.sh` (como usuario no-root) con `docker buildx` (`container-builder` + `tonistiigi/binfmt`) para construir y publicar `sinfallas/rosgrid-backend:latest` (`:1.0.0`) y `sinfallas/rosgrid-frontend:latest` (`:1.0.0`) en Docker Hub y limpiar cachés con `prune -af`.
