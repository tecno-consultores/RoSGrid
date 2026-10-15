# 🗺️ ROADMAP GRANULAR DE EJECUCIÓN (30 SPECS) — RoSGrid

## 📍 Punto de Control Actual (Checkpoint)
- **Hito Actual en Curso:** Hito 8 — Endpoints WebFig Capa 1 (Partes B y C) — Firewall, BGP/OSPF, PPPoE, Queues, System y Tools
- **Último Archivo de `specs/` Procesado:** `specs/12_BACKEND_ENDPOINTS_WEBFIG_L1_INTERFACES_AND_IP.md`
- **Último Módulo de Código Creado:** `fastapi/src/api/v1/webfig_ip.py` (Hito 7 completado)
- **Siguiente Paso Inmediato:** Sub-tarea **8.1** — Endpoints de Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, `Connections` en `src/api/v1/webfig_firewall.py` — `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md`)

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

## ✅ HITO 2: Capa Redis 7 — Idempotencia, Sesiones Kill-Switch, Pub/Sub y Monitor Zero-Metrics
> **Archivo Guía:** `specs/05_REDIS_KEYS_IDEMPOTENCY_AND_ZERO_METRICS.md`
- [x] **2.1** Cliente y pool de conexión Redis 7 (`src/redis_layer/client.py`).
- [x] **2.2** Middleware y gestor de Idempotencia HTTP (`Idempotency-Key` UUIDv7 con estados `IN_PROGRESS` / `COMPLETED` y hash SHA-256 del body en `src/redis_layer/idempotency.py`).
- [x] **2.3** Gestor de familias de Refresh Tokens (*Reuse Detection*), registro de sesiones activas e invocación del **Kill-Switch** (`src/redis_layer/sessions.py`).
- [x] **2.4** Máquina de Estados Efímera *Zero-Metrics Storage* (~200 bytes/router en Redis para transiciones `ONLINE`/`OFFLINE`/`DEGRADED_HIGH_LOAD` en `src/redis_layer/zero_metrics_monitor.py`).

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

## 🛡️ HITO 8: Endpoints WebFig Capa 1 (Partes B y C) — Firewall, BGP/OSPF, PPPoE, Queues, System y Tools
> **Archivos Guía:** `specs/13_BACKEND_ENDPOINTS_WEBFIG_L1_FIREWALL_AND_ROUTING.md` y `specs/14_BACKEND_ENDPOINTS_WEBFIG_L1_PPP_QUEUES_SYSTEM_TOOLS.md`
- [ ] **8.1** Endpoints de Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, `Connections`) y endpoint de reordenamiento (`move`) protegido por Safe Mode (`src/api/v1/webfig_firewall.py` — `specs/13`).
- [ ] **8.2** Endpoints de Routing v7: sesiones/peers `BGP`, prefijos anunciados, `OSPF`, `Routing Tables`, `Routing Rules`, `BFD` y `Filters` (`src/api/v1/webfig_routing.py` — `specs/13`).
- [ ] **8.3** Endpoints de PPPoE Active (con corte/reconexión para Soporte N1), PPP Secrets, Profiles y Servidores PPPoE (`src/api/v1/webfig_ppp.py` — `specs/14`).
- [ ] **8.4** Endpoints de Control de Ancho de Banda: `Simple Queues` (con `move`) y `Queue Tree` (`src/api/v1/webfig_queues.py` — `specs/14`).
- [ ] **8.5** Endpoints de System (`Identity`, `Users`, `Scripts`, `Scheduler` con ocultamiento de `rosgrid_safemode_*`, `Packages`, `Reboot`) y Tools de diagnóstico en vivo (`Ping`, `Traceroute`, `Torch`, `Log`) (`src/api/v1/webfig_system_tools.py` — `specs/14`).

---

## ⚙️ HITO 9: Motor Universal WebFig Capa 2, Maker-Checker, Backups Diff Git y Acciones Masivas
> **Archivos Guía:** `specs/15_BACKEND_ENDPOINTS_WEBFIG_L2_UNIVERSAL
