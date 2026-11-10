# 🛡️ Bitácora Viva de Calidad y Certificación 11X — RoSGrid

**Licencia:** GPL-3.0-only  
**Estándar Aplicado:** QA Testing Blueprints (Nivel 11X)  
**Estado Actual:** Hitos 0 al 30 (incluyendo Subhitos `30.1` al `30.38` — `Spec 114`) COMPLETADOS y Certificados al 100% en Contenedores Docker Efímeros.
> **Archivo Histórico de Certificación (`Hitos 15 al 29`):** Consulta los reportes históricos detallados en [`docs/archive/TESTING_HISTORICO.md`](docs/archive/TESTING_HISTORICO.md).

---

## 1. Resumen de Flujos de Negocio Certificados

1. **Aislamiento Multi-Tenant y Seguridad Split-Credential:**
   - Login en 2 pasos (`tenant_slug` vía `fn_resolve_tenant_by_slug` `SECURITY DEFINER` + credenciales Argon2id + 2FA TOTP obligatorio).
   - Emisión de cookies `__Host-rg_at` y `__Host-rg_rt` (`HttpOnly; Secure; SameSite=Strict`) + protección `X-CSRF-Token` (HMAC-SHA256) e `Idempotency-Key` (UUIDv7) en KeyDB con liberación Lua atómica.
   - Políticas PostgreSQL *Row-Level Security (RLS)* activas en todas las tablas del dominio con rol `rosgrid_app` (`NOSUPERUSER NOBYPASSRLS`) y listener `after_begin` multi-transacción.
2. **Matriz RBAC (11 Roles), Segmentación por Equipo y Kill-Switch en Tiempo Real:**
   - Evaluación declarativa de los 11 perfiles cruzada con `user_router_permissions` y defensa contra escalación vertical/horizontal en `PATCH /api/v1/users/{id}`.
   - Revocación instantánea de sesiones activas en KeyDB y cierre forzoso de WebSockets (`SESSION_KILLED`).
3. **Inventario MikroTik RouterOS v7.13+, Bóveda AES-256-GCM (*Step-Up Auth* 30s) y Pinning SSL TOFU:**
   - Alta individual e importación masiva por CSV en 2 pasos (*Dry-Run* + ejecución) con defensa anti-SSRF.
   - Verificación de huella SHA-256 de certificados autofirmados (TOFU), rotación automática de claves API y pool TCP reutilizable en `MikrotikRestClient`.
   - Revelación de claves restringida a los 2 roles superiores (`SUPERADMIN_GLOBAL` y `TENANT_ADMIN`) con validación TOTP en vivo y autodestrucción en memoria a los 30s.
4. **Consola Centralizada WebFig (Capa 1 + Capa 2), Safe Mode Anti-Bloqueo y Maker-Checker:**
   - Módulos nativos Capa 1 (Interfaces, SFP DDM, VLAN, Bridge, WireGuard, WiFi, IP/IPv6, Firewall Dual-Stack con Drag & Drop, Routing BGP/OSPF/BFD, PPPoE, Queues, System, Tools) y motor dinámico universal Capa 2 (`/rest/*`).
   - Protocolo *Dead Man's Switch* vía `/system/scheduler` (reversión automática en 60s si un cambio corta la red).
   - Intercepción de las 7 categorías de acciones críticas hacia bandeja de aprobación *Maker-Checker* con segregación estricta de funciones y aislamiento por tenant.
5. **Gráficas Efímeras Estilo WinBox (Cero Métricas en DB), Alertas Zero-Storage y Backups Diff Git:**
   - Multiplexor WebSocket en vivo + `TelemetryRingBuffer` en RAM del navegador (5400 puntos a 1 tick/2s, se reinicia al salir).
   - Máquina de estados en KeyDB (~200 bytes/router) con alertas a Telegram, SMTP, Webhook y Wallboard NOC.
   - Backups `.rsc`/`.backup` con deduplicación SHA-256, retención de 30 días, comparador visual Diff estilo Git y Auditoría Inmutable WORM (`audit_logs` con secuencia monotónica `audit_logs_worm_seq` y `pg_advisory_xact_lock`).
6. **Endpoint MCP Protegido para Agentes IA (`POST /api/v1/mcp`):**
   - Protocolo JSON-RPC 2.0 Streamable HTTP para Hermes Agent y Claude con autenticación exclusiva `SERVICE_ACCOUNT` (`mcp_only`), filtrado CIDR obligatorio y rate-limiting en KeyDB.
   - Exposición de 22 herramientas semánticas de diagnóstico y operación y 8 Playbooks SOP (`GET /api/v1/mcp/skill`) con intercepción mandatoria *Maker-Checker* en las 6 herramientas de mutación Nivel 3 y *Safe Mode* de 60s.

---

## 2. Umbrales Innegociables de Aprobación ("Fail & Forbid")

- **Cobertura de Pruebas Unitarias Aisladas:** `>= 95%` en Backend (`pytest-cov` con `COVERAGE_FILE=/tmp/.coverage`) y `100%` pass rate en las suites unitarias de Frontend (Vitest + `0` componentes `.vue` huérfanos).
- **Complejidad Ciclomática y Deuda Técnica:**
  - Backend (`fastapi/`): `radon cc --min C src/` vacío (0 funciones grado C o peor) y `radon mi --min B src/` vacío (índice de mantenibilidad grado A).
  - Frontend (`vue3/`): `eslint` (`sonarjs` y `security`) y `vue-tsc --noEmit` con 0 errores.
- **Accesibilidad y Rendimiento UI:** 0 violaciones WCAG 2.1 A/AA en `@axe-core/playwright`, un único hito `<main>` por vista, etiquetas `aria-label` y `scope="col"`, y Lighthouse CI con Performance `>= 0.90`, Accessibility `>= 0.95`, Best-Practices `>= 0.90` y SEO `>= 0.90`.
- **Regla Cero de Host:** Cero ejecuciones de entornos en el host local; ejecución 100% encapsulada en contenedores Docker efímeros (`sinfallas/rosgrid-backend:local-test` y `sinfallas/base-node-ionic:26`).
- **Auditoría Estática de Scripts en Bash (ShellCheck):** Cero (0) errores y cero (0) advertencias en `ShellCheck` (`koalaman/shellcheck:stable`) sobre el 100% de los scripts `.sh` del monorepo.
- **Salud Topológica y Límites de Capas (Graphify AST):** Validación obligatoria de 0 violaciones de límites de capas arquitectónicas mediante `.agents/scripts/verify_topological_health.py`.
- **Compuerta de Validación Integral de Producción Local (`probar-prod-local.sh`):** Ejecución obligatoria de las 6 fases de validación pre-publicación (`./scripts/probar-prod-local.sh`) y de [docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md](docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md).

---

## 3. Comandos Oficiales de Ejecución Efímera (Cero Instalación Local)

### A. Auditoría Global de Infraestructura, Secretos, Grafos AST y Scripts en Bash

```bash
# 1. Auditoría de Infraestructura como Código (IaC) y Vulnerabilidades en File System (Trivy)
./scripts/auditar-infra.sh

# 2. Auditoría Estática de Scripts en Bash (ShellCheck en Docker)
docker run --rm -v "$(pwd):/mnt:ro" koalaman/shellcheck:stable \
    /mnt/scripts/auditar-infra.sh \
    /mnt/scripts/instalar-rosgrid.sh \
    /mnt/scripts/build.sh \
    /mnt/scripts/instalar-hooks.sh \
    /mnt/scripts/limpieza.sh \
    /mnt/scripts/probar-prod-local.sh \
    /mnt/scripts/verificar-secretos.sh \
    /mnt/scripts/actualizar-grafos-graphify.sh \
    /mnt/scripts/ver-mapa-arquitectura.sh \
    /mnt/fastapi/scripts/entrypoint.sh

# 3. Actualización Incremental de Grafos de Conocimiento AST (Graphify en Docker)
./scripts/actualizar-grafos-graphify.sh

# 4. Compuerta Integral de Certificación 11X (9 Etapas en Docker Efímero)
./.agents/scripts/certify_task_completion.sh --strict

# 5. Pipeline de Validación Integral de Imágenes de Producción en Local
./scripts/probar-prod-local.sh
```

> Consulta el manual operativo completo en [docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md](docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md).

### B. Ecosistema Backend y Frontend (`Makefile` Canónico — Regla Cero)

```bash
# Ejecutar linters y verificación de tipos en contenedores efímeros (ruff, mypy --strict, vue-tsc, eslint)
make lint

# Ejecutar suite unitaria Backend con cobertura >= 95% en contenedor efímero
make test-backend

# Ejecutar suite unitaria Frontend en contenedor efímero
make test-frontend

# Ejecutar ambas suites unitarias + auditoría Trivy
make test
make audit
```

---

## 4. Registro Histórico de Certificación por Hitos

| Hito | Módulo Certificado | Cobertura Unitaria | SAST / DAST / A11y | Estado |
| :---: | :--- | :---: | :---: | :---: |
| **Hito 0–14** | Monorepo, PostgreSQL RLS, KeyDB, Auth 2FA, WebFig L1/L2, WS, Vue 3 y Docs | >= 95% | Trivy IaC/FS + Ruff + Mypy Strict + Radon A | ✅ Certificado |
| **Hito 15–15B** | Certificación Integral QA 11X y Estabilización en Hardware Real RouterOS v7 | 95.22% Back / 99.93% Front | Axe 0 Violaciones + LHCI >= 0.95 + ZAP 0 Fallos | ✅ Certificado |
| **Hito 16–22** | Feature Flags, Idempotencia, Diagnóstico 360°, Mapas, CIS, MCP y BDD 100% | >= 95% | ShellCheck 0 err + Hadolint 0 err + Karate BDD | ✅ Certificado |
| **Hito 23–27** | Topología L2, Syslog UDP, CVEs, Fixtures Trimodales, DAG B2B y WebFig v7 Total | >= 95% | 6 Routers Reales Evaluados + 28 Directivas CIS | ✅ Certificado |
| **Hito 28** | Estabilización UAT Fase I, Safe Mode 2 Fases, Paridad 0 Huérfanos y STIG V6R5 | >= 95% | STIG V6R5 + OWASP v4.2 + CycloneDX SBOM | ✅ Certificado |
| **Hito 29** | Conector NIST NVD v2.0, Support Bundle 1-Click Sanitizado y Conector SIEM ISP | >= 95% | Zero-Leak Bundle + Multi-Protocol SIEM | ✅ Certificado |
| **Hito 30** | Refinamientos UAT Fase II, Gobernanza MCP Zero-Trust y Remediación Integral (`Spec 114`) | >= 95% | RLS Multi-Tx + WORM Seq + WCAG 2.1 AA + CI/CD SHA | ✅ **Certificado** |

---

## 5. Desglose de Certificación — Hito 30 (`Specs 79 a 114`)

14. **Hito 30.1: Unificación del Isotipo de Alta Definición (`512×512` Mesh + Glow) en `RgBrandLogo.vue` para Cabecera Global y Login (`docs/specs/79`):**
    - **Frontend Vue 3 (`RgBrandLogo.vue`, `RgResponsiveShell.vue`, `RgBrandLogo.unit.ts`):**
      - Reemplazo del SVG simplificado de 15 líneas por el arte vectorial de alta definición `viewBox="0 0 512 512"`.
      - Incorporación del contenedor táctico deep navy redondeado (`rx="96"`, `ry="96"`), retícula táctica de fondo, malla poligonal de constelación `R` (`rgCyberBlue`) y `G` (`rgElectricOrange`), degradados enriquecidos y filtro `rgNeonGlow` con resplandor `drop-shadow(0 0 8px rgba(0, 240, 255, 0.45))`.
      - Ajuste del tamaño del logo en la cabecera global (`RgResponsiveShell.vue`) a `:size="28"` para máxima nitidez y paridad visual con la consola del NOC Wallboard.
      - Cobertura: `RgBrandLogo.unit.ts` ampliado a 2 tests dedicados (100% aprobado).

15. **Hito 30.2: Sincronización Automática de Ventanas de Mantenimiento con `admin_state` del Router, Estado Reactivo `🛠️ En Curso` / `⏳ Programada`, Botón `[ 🔄 Refrescar ]` en Mapas NOC / Clientes, Visibilidad en Centro de Mando y Resolución Humana de Actores/Routers en Cinta de Eventos WORM (`docs/specs/80`):**
    - **Backend FastAPI (`inventory_helpers.py`, `inventory.py`, `audit.py`):**
      - Evaluación dinámica en `resolve_active_maintenance_router_ids` purgando ventanas vencidas y proyectando `admin_state = MAINTENANCE` en `list_routers`, `get_router` y `update_router`.
      - Cancelación automática de ventanas en curso asociadas cuando el operador restablece manualmente `admin_state = PRODUCTION` en `update_router`.
      - Resolución de `User.username` y `Router.display_name` en `write_audit_log` cuando se proporcionan UUIDs crudos o valores omitidos, erradicando filtración de identificadores crudos en auditoría WORM.
      - Cobertura: `test_inventory_and_vault_endpoints_full.unit.py` ampliado con pruebas de 3 fases temporales y resolución de actores.
    - **Frontend Vue 3 (`MaintenanceWindowsView.vue`, `DashboardHomeView.vue`, `eventFormatter.ts`, `NocWallboardView.vue`, `UnifiedNetworkMap.vue`, `SubscribersMapView.vue`):**
      - Reloj reactivo de 15s y helper `getWindowStatusLabel` (`🛠️ En Curso` vs `⏳ Programada`) con sincronización inmediata `inventoryStore.fetchRouters(true)` en `MaintenanceWindowsView.vue`.
      - Cálculo de `maintenanceRouters`, exclusión del pool activo para disponibilidad real, desglose en tarjeta KPI de flota e insignia `🛠️ MANTENIMIENTO` en lista de acceso rápido en `DashboardHomeView.vue`.
      - Filtrado de UUIDs crudos en `formatEventMessage` y catálogo extendido de eventos (`SESSION_TOKEN_RENEWED`, `MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED`) en `eventFormatter.ts`.
      - Clasificación multi-categoría (`CAÍDA`, `MANTENIMIENTO`, `RESPALDO`, `OPERATIVO`, `OPERACIÓN`) y botón táctico `#btn-wallboard-refresh` con `forceProbe` en `NocWallboardView.vue`.
      - Opción `MAINTENANCE` en filtro de estado de mapa, exclusión de falsos positivos en alerta RCA y filtrado de routers en `UnifiedNetworkMap.vue`.
      - Auto-refresco de 30s y botón `#btn-subscribers-map-refresh` (`.btn-refresh-map`) en `SubscribersMapView.vue`.
      - Cobertura: suites unitarias co-localizadas `maintenanceWindowsView.unit.ts`, `DashboardHomeView.unit.ts`, `eventFormatter.unit.ts` y `UnifiedNetworkMap.unit.ts` aprobadas al 100%.

16. **Hito 30.3 y Hito 30.4: Reactividad en Tiempo Real de la Bandeja Maker-Checker (`/approvals`) y Centro Táctico de Notificaciones In-App (`RgNotificationCenterBell.vue`) (`docs/specs/81` y `docs/specs/82`):**
    - **Backend FastAPI (`webfig_common.py`, `bulk_and_updates.py`, `mcp.py`, `approvals.py`):**
      - Emisión automática de eventos `MAKER_CHECKER_REQUESTED` y `MAKER_CHECKER_RESOLVED` hacia KeyDB Pub/Sub (`rg:{tenant_id}:events`).
    - **Frontend Vue 3 (`RgNotificationCenterBell.vue`, `RgResponsiveShell.vue`, `ApprovalsInboxView.vue`, `useNocEventsStore.ts`, `RgNotificationCenterBell.unit.ts`):**
      - Conexión global del WebSocket de eventos en `RgResponsiveShell.vue`, auto-refresco de 15s y botón `[ 🔄 Refrescar ]` (`#btn-refresh-approvals`) en `ApprovalsInboxView.vue`.
      - Centro Táctico de Notificaciones In-App en barra superior con 4 pestañas, separación de estado leído (`lastReadIso`) vs. acción pendiente (`requiresAction`), triaje en línea en 1 clic (`✓ Aprobar 1-Clic` y `👁️ Reconocer (Ack)`), deduplicación `[×N]` y modo Snooze 30m.

17. **Hito 30.5: Refactorización Sistemática de Suites Preexistentes bajo el Estándar Anti-Silo, Ciclo de Vida Temporal de 3 Fases y Guardrail Estático `verify_anti_silo_test_quality.py` (`docs/specs/83`):**
    - **Backend FastAPI Tests (`conftest.py`, 12 suites `*.unit.py`, `test_safemode_deadman_switch.unit.py`):**
      - Helper global `make_asserting_audit_mock` en `fastapi/tests/conftest.py` validando en tiempo de ejecución la integridad semántica de cada llamada a `write_audit_log` y rechazando UUIDs crudos.
      - Erradicación de los 49 mocks ciegos de `write_audit_log` en los 12 archivos de pruebas existentes (reducción de 49 a **0 mocks ciegos**).
      - Ciclo de vida temporal de 3 fases en `test_reveal_and_rotate_credentials` (30s Step-Up Vault) y `test_safemode_three_phase_temporal_lifecycle_and_rollback` (60s Safe Mode Dead-Man Switch), más propagación cruzada sin mocks intermedios en `test_maintenance_window_endpoints`.
    - **Guardrail Estático e Integración CI/CD (`.agents/scripts/verify_anti_silo_test_quality.py`, `certify_task_completion.sh`):**
      - Validador estático integrado en el paso `[4/9]` de `certify_task_completion.sh`, certificando 0 mocks ciegos y 100% de suites 3-Fases / Anti-Silo, junto con el Escenario 159 de Karate Labs API sincronizado en `docs/examples/`.

18. **Hito 30.6: Seguridad de Sesiones PPPoE, Prevención de Sesiones Fantasma (*"already active"*), `keepalive-timeout=10`, Candado MAC (`caller-id`), Tópico Syslog `pppoe,ppp` y Evicción Híbrida ICMP (`docs/specs/84`):**
    - **Backend FastAPI (`schemas/webfig_ops.py`, `api/v1/webfig_ppp.py`, `api/v1/bulk_and_updates.py`, `api/v1/inventory_helpers.py`, `workers/subscriber_status_poller.py`):**
      - Soporte para `caller_id` (candado MAC WAN) en creación/edición de secretos PPP (`PppSecretCreateRequest`, `PppSecretUpdateRequest`, `_build_secret_create_body`, `_build_secret_patch_data`).
      - Endurecimiento por defecto `only_one="yes"` en perfiles PPP (`PppProfileCreateRequest`), y `one_session_per_host=True` + `keepalive_timeout=10` (10s conforme al estándar MikroTik/EVANGIT) en servidores PPPoE (`PppoeServerCreateRequest`, `PppoeServerUpdateRequest`, `_format_keepalive_timeout`, `_build_pppoe_server_patch_data`).
      - Incorporación de la regla #11 `/system logging add topics=pppoe,ppp,info,warning,error action="rosgridsyslog"` en la plantilla maestra `SYSLOG_CENTRALIZADO_ROSGRID` y en el auto-aprovisionador `discover_and_persist_syslog_status`.
      - Evicción híbrida de sesiones PPPoE fantasma en `_probe_devices_icmp` (`_discard_device_identifiers`) dentro de `subscriber_status_poller.py`, descartando `pppoe_username` y `endpoint_identifier` de `active_identifiers` cuando falla el sondeo ICMP para transicionar abonados fantasma a `OFFLINE`.
      - Cobertura: `test_webfig_crud_and_maintenance_expiry.unit.py`, `test_operations_endpoints_full.unit.py`, `test_compliance_cis_expanded.unit.py` y `test_subscriber_status_poller.unit.py` (`test_poller_icmp_probe_marks_phantom_pppoe_session_offline`) aprobados al 100%.
    - **Frontend Vue 3 (`PppAndQueuesView.vue`, `webfigViews.unit.ts`):**
      - Columna y campos de formulario `caller_id` (`#sec-caller-id`, `#edit-sec-caller-id`) en la pestaña Secretos PPP.
      - Selector `#prof-only-one` con valor predeterminado `yes (Recomendado Anti-Clonación)` en creación de Perfiles PPP.
      - Columnas y campos `keepalive_timeout` (`#srv-keepalive`, `#edit-srv-keepalive`) y `one_session_per_host` (`#srv-one-session`, `#edit-srv-one-session`) en creación y edición de Servidores PPPoE.
      - Cobertura: `webfigViews.unit.ts` ampliado (27/27 tests aprobados al 100%) + Escenario 160 Karate API y Escenario 98 Karate UI sincronizados en `docs/examples/`.

19. **Hito 30.8: Resiliencia de Actualización RouterOS v7 en CHR y RouterBOARD — Timeout Extendido (`180s`), Fallback Directo `/tool/fetch` `.npk`, Tolerancia `/system/routerboard` y Verificación Real por Equipo en UI (`docs/specs/85`):**
    - **Backend FastAPI (`mikrotik/client.py`, `api/v1/bulk_and_updates.py`, `api/v1/webfig_system_tools.py`):**
      - Soporte de `timeout: float | None = None` por petición en `MikrotikRestClient` (`30.0s` para `check-for-updates`, `180.0s` para `system/package/update/install` y descargas `/tool/fetch` de paquetes `.npk`).
      - Limpieza automática de paquetes `.npk` truncados de `0 bytes` (`_cleanup_corrupted_npk_downloads`), consulta HTTP directa a `upgrade.mikrotik.com/routeros/NEWESTa7.<channel>` (`_fetch_latest_version_via_http_fallback`) y descarga e instalación vía `/tool/fetch` + `/system/reboot` (`_install_routeros_via_fetch_fallback`) ante el bug `ERROR: bad HTTP response` de RouterOS `7.25`.
      - Tolerancia a `HTTP 400: no such command or directory (routerboard)` en equipos CHR mediante `_probe_routerboard_safe` (`bulk_and_updates.py`) y `_fetch_system_routerboard` (`webfig_system_tools.py`).
      - Cobertura: `test_rest_client_v7.unit.py` y `test_smart_os_firmware_update_chr.unit.py` ampliados y aprobados al 100%.
    - **Frontend Vue 3 (`BulkOperationsAndUpdatesView.vue`, `operationsViews.unit.ts`):**
      - Verificación estricta de `res.data.results[]` en `triggerRosUpdate` y `triggerFleetPoeUpdate`, presentando alerta `.alert--error` y evitando marcar `upgraded_in_session = true` cuando el router reporta `FAILED`.
      - Cobertura: `operationsViews.unit.ts` ampliado + Escenario 161 Karate API, Escenario 99 Karate UI y fase `[SMOKE TEST 5/5]` en `scripts/validar-flota-real.py`.

24. **Hito 30.14: Eliminación del Falso Positivo `0.0.0.0` en Detección de Anomalías de Tráfico, Paridad de Columnas en UI y Sondeo Real `/rest/ping` en Telemetría SLA (`docs/specs/91`):**
    - **Backend FastAPI (`api/v1/traffic_flow.py`, `api/v1/sla.py`):**
      - Validador `_is_valid_anomaly_source_ip` mediante `ipaddress` descartando `0.0.0.0`, broadcast `255.255.255.255`, loopback, link-local, multicast, reservadas e IPs propias del router (`local_router_ips` de `/ip/address`).
      - Desacople de falsos positivos de `HIGH_PPS_BURST` en `_aggregate_connection_stats` y `_analyze_connections` ante sesiones únicas acumulativas históricas (`_extract_item_pps`, CC <= 5 Radon Grado A).
      - Guardrail `HTTP 422 Unprocessable Content` en `mitigate_traffic_anomaly` ante direcciones no enrutables.
      - Acotación de sondeo ICMP a `actual_count = min(count, 5)` en `run_sla_probe` para `/rest/ping` y tolerancia a `time`/`avg-rtt`.
      - Cobertura: `fastapi/tests/api/test_traffic_flow.unit.py` (11 pruebas) y `fastapi/tests/api/test_sla_tracker.unit.py` (6 pruebas) pasando al 100% (746 pruebas backend totales).
    - **Frontend Vue 3 (`EnterpriseComplianceView.vue`, `enterpriseComplianceView.unit.ts`):**
      - Paridad de columnas `connection_count` y `estimated_pps` en la tabla de anomalías de SLA.
      - Deshabilitación reactiva del botón `#btn-mitigate-traffic-anomaly` ante ausencia de anomalías y validación defensiva en `handleMitigateAnomaly`.
      - Cobertura: `enterpriseComplianceView.unit.ts` ampliado (18/18 pruebas aprobadas al 100%, 571 pruebas frontend totales).
      - Escenario 167 Karate API y Escenario 105 Karate UI sincronizados en `docs/examples/`.

25. **Hito 30.15: Despacho Real de Prueba y Alertas en Canales de Notificación (SMTP `to_emails`/`from_email`/TLS/SSL, Telegram y Webhook) y Edición Interactiva de Canales (`✏️ Editar`) (`docs/specs/92`):**
    - **Backend FastAPI (`workers/alert_dispatcher_worker.py`, `schemas/notifications.py`, `api/v1/notification_channels.py`):**
      - `_resolve_smtp_recipients` resolviendo `to_emails` (lista o string delimitado por comas), `to_addresses` y fallback resiliente a `from_email`/`smtp_user`.
      - Soporte dual de `smtplib.SMTP_SSL` en puerto 465 y `smtplib.SMTP` con `starttls()` en puerto 587, saneamiento de contraseñas de Google con espacios intermedios, personalización de asunto/cuerpo con `custom_message` y soporte de cabecera `Authorization` en webhooks.
      - Despacho real en `POST /api/v1/operations/notification-channels/{channel_id}/test` invocando el canal correspondiente con reporte estructurado de fallos (`status="FAILED"` explicativo) ante credenciales o red inalcanzable.
      - `config_summary` sanitizado en `NotificationChannelResponse` y fusión de secretos previos en `PATCH /{channel_id}` preservando tokens/contraseñas existentes.
      - Cobertura: `fastapi/tests/workers/test_workers_full.unit.py`, `fastapi/tests/api/test_operations_endpoints_full.unit.py` y `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` pasando al 100% (746 pruebas backend totales).
    - **Frontend Vue 3 (`NotificationChannelsPanel.vue`, `types/index.ts`, `NotificationChannelsPanel.unit.ts`):**
      - Botón `✏️ Editar` (`#btn-edit-channel-<id>`) en tarjetas de canal, precarga de datos y eventos desde `config_summary`, y modal dual Crear/Editar despachando `PATCH` o `POST`.
      - Cobertura: `NotificationChannelsPanel.unit.ts` ampliado (5 pruebas aprobadas al 100%, 572 pruebas frontend totales en 83 suites).
      - Escenario 168 Karate API y Escenario 106 Karate UI sincronizados en `docs/examples/`.

26. **Hito 30.16: Paridad Total de Internacionalización (i18n Español / Inglés) en CIS Hardening, Seguridad L2 & Rogue DHCP, Telemetría SLA, Canales de Alerta y Diagnóstico & SIEM (`docs/specs/93`):**
    - **Frontend Vue 3 (`locales/es.json`, `locales/en.json`, `EnterpriseComplianceView.vue`, `NotificationChannelsPanel.vue`, `DiagnosticsAndSiemPanel.vue`):**
      - Extensión exhaustiva de más de 60 claves técnicas en diccionarios `es.json` y `en.json` (CIS directivas con `finding_passed`/`finding_failed`, `notifications_channels.*`, `diagnostics_siem.*`). Integridad validada con `verify_json_no_duplicate_keys.py`.
      - Proyección dinámica de estados y hallazgos en CIS Benchmark mediante helper `getDirectiveFinding(d)`.
      - Internacionalización de DHCP Snooping, Option 82, modal `#modal-dhcp-snooping-config`, grupos de servidores SLA y anomalías FastDrop.
      - Reactividad bilingüe con `computed` en `availableEvents` y `getEventLabel`, insignias traducidas de canal y soporte bilingüe en paquete de diagnóstico y SIEM.
      - Cobertura: `enterpriseComplianceView.unit.ts`, `NotificationChannelsPanel.unit.ts` y `DiagnosticsAndSiemPanel.unit.ts` ampliados con pruebas de conmutación `setLocale('en')` (575 pruebas frontend Vitest en 83 suites aprobadas al 100%).
      - Escenario 107 Karate UI sincronizados en `docs/examples/`.

    > **Nota de Trazabilidad (Hitos 30.17 al 30.36):** Los detalles granulares de aseguramiento de calidad de los sub-hitos `30.17` a `30.36` (Specs `94` a `112`: motor WebFig Layer 2 Next-Gen, caché `<KeepAlive>`, agrupación cartográfica `<= 25m`, ayuda contextual, centro de notificaciones `Alt+N`, temas dinámicos `var(--rg-*)`, alineación `.form-row-2col` y auditoría STIG/OWASP de cierre `v1.0.0`) se encuentran documentados en `ROADMAP.md` (sección Hito 30) y en `docs/archive/TESTING_HISTORICO.md`.

27. **Hito 30.37: Gobernanza Zero-Trust MCP (Maker-Checker en las 6 Herramientas de Mutación), Defensa RBAC en Capa de Servicio, Catálogo de 22 Tools, Auditoría CIS Viva de 28 Directivas, Telemetría Opt-In y Centrado Cartográfico de Técnico de Campo (`docs/specs/113`):**
    - **Backend FastAPI (`mcp.py`, `approvals.py`, `network_services.py`, `bulk_and_updates.py`, `compliance.py`, `config.py`):**
      - Freno Maker-Checker (`status: "AWAITING_APPROVAL"`, `safe_mode_timeout_seconds: 60`) en las 6 herramientas de mutación Nivel 3 y ejecución diferida en `_execute_mcp_deferred_tool` al aprobar el `Checker`.
      - Restricción exclusiva de `/api/v1/mcp` a `SERVICE_ACCOUNT` con `allowed_cidr_list` no vacía, remoción de `NOC_MONITOR` de `_PROVISIONING_ROLES` y validación explícita de rol en Python en las funciones de servicio.
      - Incorporación de `#21 rosgrid_search_mikrotik_docs` y `#22 rosgrid_get_mikrotik_doc_topic` (22 tools MCP), sondeo en vivo de `CIS-1.9` y `CIS-1.6` (28 directivas CIS) y `ROSGRID_TELEMETRY_BEACON_ENABLED=false` por defecto.
    - **Frontend Vue 3 (`RgResponsiveShell.vue`, `FieldTechMobileView.vue`, `UnifiedNetworkMap.vue`):**
      - Sincronización de `authStore.tenantHqCoordinates` al montar y centrado reactivo en `FieldTechMobileView.vue`.
      - Escenario 180 Karate API y Escenario 128 Karate UI sincronizados en `docs/examples/`.

28. **Hito 30.38: Remediación Integral de Seguridad Zero-Trust, Aislamiento RLS Multi-Transacción, Cadena WORM Determinista, Accesibilidad WCAG 2.1 AA e Infraestructura 11X (`docs/specs/114`):**
    - **Backend FastAPI (`users.py`, `auth.py`, `approvals.py`, `mcp.py`, `deps.py`, `db/session.py`, `core/audit.py`, `mikrotik/client.py`, `redis_layer/idempotency.py`, `migrations/versions/0016_rls_worm_seq_and_fk_idx.py`):**
      - Migración Alembic `0016` con rol `rosgrid_app` (`NOSUPERUSER NOBYPASSRLS`), función `SECURITY DEFINER` `fn_resolve_tenant_by_slug`, secuencia monotónica `audit_logs_worm_seq` + bloqueo transaccional `pg_advisory_xact_lock`, e índice compuesto `ix_users_tenant_role_active`.
      - Listener SQLAlchemy `after_begin` en `AsyncSession` que re-aplica `app.current_tenant_id` y `app.is_superadmin_global` automáticamente tras cada `await db.commit()` intermedio.
      - Bloqueo de escalación vertical/horizontal en `PATCH /api/v1/users/{id}`, aislamiento de tokens `mcp_only` en `deps.py`, filtro por `tenant_id` en `approvals.py` y pool TCP compartido `httpx.AsyncClient` en `MikrotikRestClient`.
    - **Frontend Vue 3, Nginx e Infraestructura CI/CD (`vue3/src/`, `vue3/nginx/default.conf`, `.github/workflows/01-backend-qa.yml`, `02-frontend-qa.yml`, `Makefile`):**
      - Mitigación de XSS en `OsmRouterMap.vue` y `UnifiedNetworkMap.vue`, validación de origen en `httpClient.ts` y `LoginView.vue`, remediación de `<main>` anidados, atributos WCAG 2.1 AA (`aria-label`, `role="button"`, `scope="col"`), paridad i18n (`es.json`/`en.json`), y workflows CI/CD con acciones ancladas por SHA.
      - Escenario 181 Karate API y Escenario 129 Karate UI sincronizados en `docs/examples/`.

29. **Hito 30.39: Remediación Integral de Auditoría de Repositorio v1.1.0 — Homologación RLS 25 Tablas (`0017`), Validador Anti-SSRF Unificado (`ssrf.py`), Canon de 10 Tópicos Syslog, Aislamiento `<keep-alive>` WebFig por Router, Reconexión WS y Pirámide QA 11X:**
    - **Backend FastAPI (`migrations/versions/0016_*.py`, `0017_homologate_rls_policies.py`, `core/ssrf.py`, `core/config.py`, `api/v1/approvals.py`, `api/v1/mcp.py`, `api/v1/syslog.py`, `redis_layer/sessions.py`, `workers/runner.py`):**
      - Homologación de las 25 tablas multi-tenant reales con `ENABLE/FORCE ROW LEVEL SECURITY` y bypass `app.is_superadmin_global = 'true'` en `0016` y `0017`.
      - Validador centralizado `src/core/ssrf.py` (con `ROSGRID_OUTBOUND_ALLOWED_CIDRS` y `is_safe_smtp_target`), sufijo `/{inferred_id}` para `PATCH`/`DELETE` diferidos y persistencia de `EXPIRED` en `approvals.py`, guardias de feature flags y ownership en `mcp.py`, índices secundarios en KeyDB (`rg:sess_idx:*` y `rg:closing_tenants_set`) y latido `/tmp/worker_heartbeat`.
    - **Frontend Vue 3 y Suites QA 11X (`RouterWebFigLayout.vue`, `router/index.ts`, `templatePresets.ts`, `themes.css`, `UnifiedNetworkMap.vue`, `test_postgres_rls_and_alembic.unit.py`, `test_spec114_security_and_rls.unit.py`):**
      - Aislamiento `<keep-alive>` con `:key="`${routerId}:${String(route.name)}`"` y reconexión exponencial WS en `RouterWebFigLayout.vue`, preservación de estado previo en errores de sondeo en 7 vistas, 10 tópicos Syslog canónicos en `templatePresets.ts`, 20 alias `--rg-*` en `themes.css`, eliminación del componente muerto `OsmOnuMap.vue`, y nueva suite `@pytest.mark.integration` contra PostgreSQL 17.
      - **Métricas Vigentes Certificadas (v1.2.0 / Hito 30.40):** **784 pruebas unitarias Backend Pytest** (`>= 95%` cobertura) + **1 suite de integración PostgreSQL/Alembic/RLS**, **608 pruebas unitarias Frontend Vitest** en **83 suites** (`100% pass`), **28 bloques contractuales Front-Back (77 aserciones HTTP)**, y **185 escenarios BDD Karate API** + **132 escenarios BDD Karate UI** espejados en `docs/examples/`.

30. **Hito 30.40: Corrección del Flujo de Creación de Super Administrador Inicial (`Bootstrap`) y Confirmación 2FA TOTP en Tiempo Real, Supresión de Tormenta `401` en Pre-Auth y Tolerancia CSWSH de Proxy Inverso Nginx:**
    - **Backend FastAPI (`api/v1/auth.py`, `redis_layer/idempotency.py`, `core/csrf.py`, `api/v1/websockets.py`):**
      - Corrección de `rg:preauth_idx:{challenge_id}` en `bootstrap_initial_admin` almacenando `str(tenant.id)` y normalización defensiva en `_fetch_preauth_state`, eliminando el error `HTTP 401 ("Desafío 2FA inválido o expirado")` al confirmar el QR TOTP del administrador inicial.
      - Inclusión de `/api/v1/auth/2fa/confirm-enrollment` en `_EXCLUDED_PATHS` de `IdempotencyMiddleware` y `CSRFProtectionMiddleware`, y tolerancia de puertos de proxy inverso en `_verify_ws_origin` con captura limpia de `WebSocketDisconnect`.
    - **Frontend Vue 3 y Proxy Nginx (`api/httpClient.ts`, `composables/useDiagnosticsCollector.ts`, `views/LoginView.vue`, `vue3/nginx/default.conf`):**
      - Inclusión de `/api/v1/auth/2fa/confirm-enrollment`, `/api/v1/auth/bootstrap`, `/api/v1/auth/register` y `/api/v1/system/diagnostics/ui-error` en `isAuthEndpoint`, omisión de reportes `ui-error` ante errores `401`, purga de sesión residual cuando `is_bootstrapped === false`, y uso de `proxy_set_header Host $http_host;` en Nginx.
      - Escenario 183 Karate API y Escenario 131 Karate UI sincronizados en `docs/examples/`.
