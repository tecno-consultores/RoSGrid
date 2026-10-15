# 🗺️ ROADMAP Y CONTROL DE PROGRESO — RoSGrid (Estándar QA 11X)

## 📍 Punto de Control Actual (Checkpoint)
- **Fecha / Hora:** 2026-10-14 21:07 (UTC-4)
- **Hito en Curso:** Hito 1 — Núcleo Backend, Base de Datos RLS, Redis y Seguridad
- **Último Módulo Completado:** Sub-etapa 1.7 (Suite de Pruebas Unitarias Aisladas del Hito 1 con 10 archivos de prueba y 95 casos de prueba unitarios aislados).
- **Siguiente Acción Inmediata:** Completar la ejecución de Gate 1 dentro de Docker (`qa-unit` con cobertura >= 95% y `qa-mutation` con Mutmut) para cerrar formalmente el Hito 1 y esperar autorización explícita antes del Hito 2.
- **Estado de Pruebas (Gate 11X):**
  - `qa-lint` en Docker: **100% APROBADO (Exit Code 0)** — Ruff (0 errores), Ruff Format (0 errores), Mypy Strict (0 errores en 36 archivos), Radon CC (< C, CC <= 5 por función), Radon MI (MI Grade A en todos los archivos), Bandit SAST (0 vulnerabilidades), Pip-Audit CVE (0 vulnerabilidades conocidas).
  - `qa-unit` en Docker: **En ejecución** (93/95 tests pasando, cerrando configuración Pydantic `from_attributes=True`).
  - `qa-mutation` en Docker: **Pendiente de ejecución tras qa-unit**.

---

## ✅ Hito 0: Preparación del Monorepo, Licencia GPLv3 y Fusión Quirúrgica 11X (`specs/00`, `01`, `29`)
- [x] **0.1** Estructura de directorios (`fastapi/`, `vue3/`, `specs/`, `examples/`, `docs/`).
- [x] **0.2** Archivos raíz (`LICENSE` GPL-3.0-only, `.env.example`, `docker-compose.yml`, `.gitignore`, hooks Lefthook/Commitlint y `auditar-infra.sh`).
- [x] **0.3** Fusión quirúrgica en `./fastapi/` (`pyproject.toml`, `tox.ini`, `Makefile`, `docker-compose.qa.yml`, `limpieza.sh`, `locustfile.py`, `scripts/entrypoint.sh`).
- [x] **0.4** Fusión quirúrgica en `./vue3/` (`package.json`, `.npmrc`, `vitest.config.ts`, `stryker.conf.json`, `playwright.config.ts`, `lighthouserc.js`, `Makefile`, `docker-compose.qa.yml`, `nginx/default.conf`).
- [x] **0.5** Gate 0 superado (`./auditar-infra.sh` con Trivy IaC + FS).

---

## 🚧 Hito 1: Núcleo Backend, PostgreSQL RLS, Redis y Seguridad (`specs/02` al `07`, `09`, `10`, `25`)
- [x] **1.1** Configuración Alembic (`alembic.ini`, `migrations/env.py`) y las 3 migraciones DDL completas (`0001_core_tenants_users_rls.py`, `0002_inventory_vault_maintenance.py`, `0003_operations_backups_immutable_audit.py` con RLS y trigger WORM).
- [x] **1.2** Modelos declarativos SQLAlchemy 2.0 (`src/models/base.py`, `core.py`, `inventory.py`, `operations.py`) y sesión async con contexto RLS (`src/db/session.py`).
- [x] **1.3** Núcleo de seguridad y criptografía (`src/core/config.py`, `crypto.py` AES-256-GCM + Argon2id, `csrf.py` HMAC-SHA256, `security_headers.py`, `audit.py` Hash-Chain WORM).
- [x] **1.4** Capa Redis 7 (`src/redis_layer/client.py`, `idempotency.py`, `sessions.py` Kill-Switch + Reuse Detection, `zero_metrics_monitor.py`).
- [x] **1.5** Motor RBAC de 11 roles y clasificador de 7 acciones críticas Maker-Checker (`src/rbac/`).
- [x] **1.6** Aplicación principal (`src/main.py` con `/metrics`, `/health`, `/users/me`) y Endpoints V1 de Auth Multi-Tenant + 2FA TOTP, Tenants, Usuarios, Permisos por Router y Sesiones Activas (`src/api/v1/` y `src/schemas/`).
- [x] **1.7** Suite de Pruebas Unitarias Aisladas del Hito 1 (`fastapi/tests/` con `pytest-mock` sin red ni DB real).
- [ ] **1.8** Gate 1 superado en Docker (`make qa-lint && make qa-unit && make qa-mutation` con cobertura >= 95%, Radon CC < C / MI == A y 0 mutantes sobrevivientes).

---

## ⏳ Hito 2: Conector RouterOS v7 (TOFU + Safe Mode), Inventario, Bóveda y WebFig L1/L2 (`specs/08`, `11` al `15`, `25`)
- [ ] **2.1** Conector RouterOS v7 (`src/mikrotik/ssl_tofu.py`, `client.py`, `safemode.py` Dead Man's Switch `/system/scheduler`, `normalizers.py`).
- [ ] **2.2** Endpoints de Inventario, Autodescubrimiento, Importador CSV en 2 pasos (`dry-run` / `commit`), Bóveda *Step-Up Auth* (30s para los 2 roles altos), Rotación de Claves y Ventanas de Mantenimiento (`specs/11`).
- [ ] **2.3** Endpoints WebFig Capa 1 — Parte A: Interfaces, SFP DDM, VLAN, Bridge, WireGuard, WiFi e IP/IPv6 con protección anti-suicidio `www-ssl` (`specs/12`).
- [ ] **2.4** Endpoints WebFig Capa 1 — Parte B: Firewall (`Filter`, `NAT`, `Mangle`, `RAW`, `Address-Lists`, reordenamiento Drag & Drop) y Routing v7 (`BGP`, `OSPF`, `BFD`) (`specs/13`).
- [ ] **2.5** Endpoints WebFig Capa 1 — Parte C: PPPoE/VPNs, Simple Queues/Queue Tree, System y Tools en vivo (`Ping`, `Traceroute`, `Torch`, `Log`) (`specs/14`).
- [ ] **2.6** Motor Dinámico Universal WebFig Capa 2 (`/webfig/layer2/*`) con lista negra de rutas prohibidas (`specs/15`).
- [ ] **2.7** Suite de Pruebas Unitarias Aisladas del Hito 2 (`fastapi/tests/` usando `routeros_v7_payloads.py`).
- [ ] **2.8** Gate 2 superado en Docker (`make qa-lint && make qa-unit && make qa-mutation`).

---

## ⏳ Hito 3: Maker-Checker, Backups Diff Git, WebSockets, Workers y Certificación Backend (`specs/16`, `17`, `26`)
- [ ] **3.1** Endpoints de Bandeja Maker-Checker, Backups `.rsc`/`.backup` (deduplicación SHA-256, 30 días), Comparador Diff estilo Git, Plantillas (*Golden Configs*), Acciones Masivas y Actualizador RouterOS v7 (`specs/16`).
- [ ] **3.2** Endpoints de Consola Forense de Auditoría Inmutable y verificación criptográfica de cadena WORM (`specs/16`).
- [ ] **3.3** Multiplexor WebSocket para gráficas efímeras (`/ws/v1/routers/{id}/live-telemetry`), bus de eventos (`/ws/v1/tenant/events`) y los 4 Workers en segundo plano (Monitor Zero-Storage, Alertas Telegram/SMTP/Webhook/NOC, Backups y Rotación) (`specs/17`).
- [ ] **3.4** Suite de Pruebas Unitarias del Hito 3, escenarios BDD (`fastapi/test/api_test.feature`) y carga (`locustfile.py`).
- [ ] **3.5** Gate 3 superado en Docker (`make qa-all`, `Schemathesis`, `Karate Labs`, `OWASP ZAP Baseline` y `--profile chaos` con `Pumba + Locust + Prometheus`).

---

## ⏳ Hito 4: Frontend Vue 3, Diseño WCAG/Lighthouse, Mapa OSM, WebFig RingBuffer y NOC (`specs/18` al `23`, `27`, `28`)
- [ ] **4.1** Cliente HTTP seguro (`httpClient.ts` con interceptores CSRF, `Idempotency-Key` UUIDv7, Refresh Token y `202 Accepted`), los 6 Stores Pinia, `TelemetryRingBuffer<T>` (5400 puntos en RAM) y Guards RBAC en Vue Router (`specs/18`, `22`).
- [ ] **4.2** Sistema de Diseño (`themes.css` Dark/Light/NOC con contraste WCAG 2.1 AA) y componentes base (`RgDataTable.vue` con Drag & Drop accesible, `RgCommandPalette.vue` Ctrl+K, `RgSafeModeBanner.vue`, `RgStepUp2FAModal.vue`, `RgResponsiveShell.vue` PWA Móvil/Tablet/PC) (`specs/19`).
- [ ] **4.3** Vistas de Login Multi-Tenant + 2FA QR, Tenants, Usuarios, Matriz de Permisos por Router y Panel de Sesiones Activas con *Kill-Switch* (`specs/20`).
- [ ] **4.4** Vistas de Inventario, Mapa Interactivo **Leaflet + OpenStreetMap (`OsmRouterMap.vue`)**, Asistente CSV en 2 pasos, Modal Bóveda *Step-Up* (autodestrucción 30s) y Ventanas de Mantenimiento (`specs/21`).
- [ ] **4.5** Consola WebFig del Router: Dashboard de Gráficas Efímeras estilo WinBox (`RingBuffer`), Vistas Capa 1 y Renderizador Universal Capa 2 (`specs/22`).
- [ ] **4.6** Vistas de Bandeja Maker-Checker, Comparador Visual Diff Git (`.rsc`), Acciones Masivas/Updates, **Wallboard NOC** y Consola del **Auditor** (`specs/23`).
- [ ] **4.7** Suite Unitaria Frontend (`*.unit.ts` en Vitest >= 95%), Mutación (`Stryker`), E2E + Accesibilidad (`vue3/e2e/accessibility.e2e.ts` y `rosgrid_workflows.e2e.ts`) y BDD (`vue3/test/ui_business_flow.feature`) (`specs/27`, `28`).
- [ ] **4.8** Gate 4 superado en Docker (`make qa-lint`, `make qa-unit`, `make qa-mutation`, `make qa-perf` Lighthouse >= 90/95, `make qa-e2e` Axe 0 violaciones y `make qa-bdd`) + Documentación final en `docs/`.
