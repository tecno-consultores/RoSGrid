# Registro de Cambios (Changelog) — RoSGrid

Todos los cambios relevantes de este proyecto se documentan en este archivo siguiendo el formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Added
- **Remediación Integral Zero-Trust, RLS Multi-Transacción, Cadena WORM Determinista, Accesibilidad WCAG 2.1 AA y Pipelines CI/CD 11X (`Spec 114` / Hito `30.38`):** Migración Alembic `0016` con rol `rosgrid_app` (`NOSUPERUSER NOBYPASSRLS`), función `SECURITY DEFINER` `fn_resolve_tenant_by_slug`, secuencia determinista `audit_logs_worm_seq` + bloqueo transaccional `pg_advisory_xact_lock`, listener `after_begin` en `AsyncSession`, cierre de escalación de privilegios en `PATCH /api/v1/users/{id}`, bloqueo de token `mcp_only` fuera de `/api/v1/mcp`, pool TCP reutilizable en `MikrotikRestClient`, mitigación XSS/CSRF/Open Redirect en Vue 3, paridad WCAG 2.1 AA e i18n, workflows `.github/workflows/01-backend-qa.yml` y `02-frontend-qa.yml`, y archivado histórico en `docs/archive/`.
- **Catálogo MCP Completo de 22 Herramientas (`fastapi/src/api/v1/mcp.py` — Spec 113):** Implementación de las herramientas de consulta documental oficial de MikroTik `#21 rosgrid_search_mikrotik_docs` y `#22 rosgrid_get_mikrotik_doc_topic` (con validación anti-SSRF sobre `https://manual.mikrotik.com/docs/`).

### Changed
- **Gobernanza Maker-Checker Obligatoria en las 6 Herramientas MCP de Mutación (`fastapi/src/api/v1/mcp.py`, `fastapi/src/api/v1/approvals.py` — Spec 113):** Las 6 herramientas de mutación Nivel 3 (`rosgrid_reconnect_pppoe_client`, `rosgrid_propose_network_change`, `rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit` y `rosgrid_execute_poe_aware_upgrade`) generan un `ApprovalRequest` (`status: "AWAITING_APPROVAL"`, `safe_mode_timeout_seconds: 60`) sin tocar el router hasta que un operador humano (`Checker`) apruebe la operación.
- **Aislamiento Zero-Trust de `/api/v1/mcp` y Defensa RBAC en Capa de Servicio (`fastapi/src/api/v1/mcp.py`, `network_services.py`, `bulk_and_updates.py` — Spec 113):** Restricción exclusiva de `/api/v1/mcp` al rol `SERVICE_ACCOUNT` con lista `allowed_cidr_list` obligatoriamente no vacía; remoción de `NOC_MONITOR` de `_PROVISIONING_ROLES` (manteniéndolo de solo lectura) y validación explícita de rol en Python dentro de las funciones de servicio.
- **Auditoría CIS Viva de 28 Directivas y Telemetría Opt-In (`fastapi/src/api/v1/compliance.py`, `fastapi/src/core/config.py` — Spec 113):** Sondeo en vivo de `/rest/ip/ipsec/profile` (`CIS-1.9`) y `/rest/system/routerboard` (`CIS-1.6`) completando las 28 directivas CIS en `run_cis_audit`, y cambio de `ROSGRID_TELEMETRY_BEACON_ENABLED=false` por defecto (`Opt-In`).
- **Unificación Documental y Depuración de Gobernanza IA (`README.md`, `docs/`, `AGENTS.md`, `.agents/rules/`, `.agents/skills/`, `rosgrid-web` — Spec 113):** Alineación 1:1 entre código y documentación sobre `RouterOS v7.13+`, políticas del grupo `rosgrid_api_group` (`api,rest-api,read,write,ftp,test,reboot,policy,sensitive`), 28 directivas CIS y gobernanza MCP; limpieza de referencias a hitos pasados, comandos obsoletos (`docker-compose.qa.yml`) y enlaces rotos en las skills y reglas de `.agents/`.

### Fixed
- **Centrado Cartográfico en Sede Central para Técnico de Campo (`vue3/src/components/field/FieldTechMobileView.vue`, `RgResponsiveShell.vue`, `UnifiedNetworkMap.vue` — Spec 113):** Sincronización automática de `authStore.tenantHqCoordinates` al montar la consola y centrado reactivo del mapa del Técnico de Campo en las coordenadas de la Oficina Central del tenant.
- **Aprovisionamiento Zero-Trust `SERVICE_ACCOUNT` en Pipeline de Validación y Generador CLI MCP (`fastapi/scripts/generar_token_mcp.py`, `scripts/probar-prod-local.sh`):** Resolución y aprovisionamiento automático de cuenta `SERVICE_ACCOUNT` con lista blanca CIDR (`allowed_cidr_list` incluyendo subredes locales y puente Docker) para garantizar cumplimiento con el aislamiento Zero-Trust de `POST /api/v1/mcp` durante `./scripts/build.sh`.

---

## [1.0.0] - 2026-11-08

### Added
- **Consola WebFig NOC Multi-Tenant para MikroTik RouterOS v7.13+:** Gestión integral de flotas RouterOS v7 mediante API REST (`/rest/*`) con aislamiento Row-Level Security (RLS) en PostgreSQL 18, sesiones y telemetría efímera en KeyDB, y bóveda criptográfica `AES-256-GCM` con desbloqueo Step-Up 2FA (`TOTP` / `WebAuthn`).
- **Gobernanza Operativa Safe Mode 60s y Flujo Maker-Checker:** Protección transaccional contra desconexiones accidentales con reversión automática a los 60 segundos, auditoría forense inmutable WORM y bandeja de aprobaciones en tiempo real vía WebSockets.
- **Motor Universal WebFig Capa 1 y Capa 2:** Operaciones tácticas sobre Interfaces, Bridges, VLANs, IP/IPv6, Firewall, NAT, Colas QoS, PPPoE, DHCP, BGP/OSPF, MPLS, VXLAN, WireGuard y ZeroTier, con exportación y comparador visual de configuraciones `.rsc` (Git-Diff).
- **Operaciones ISP, FTTH GPON y Panel Móvil de Técnico de Campo:** Gestión de suscriptores PPPoE/DHCP, aprovisionamiento en vivo en el BNG, topología de Cajas Ópticas NAP, telemetría de potencia óptica ONU y aplicación móvil responsiva con firma digital y diagnóstico Ping 1-Clic.
- **Cumplimiento CIS Benchmark RouterOS v7 (28 Directivas) y Observabilidad:** Escáner de endurecimiento CIS (`12 Base + 8 ISP + 8 CORP`) con remediación asistida, detector de deriva de configuración (Config Drift), Looking Glass BGP/Traceroute, receptor Syslog UDP (`514`/`5514`) y exportador dual de métricas OpenMetrics/Prometheus (`GET /metrics` y `GET /api/v1/metrics/fleet`).
- **Servidor Model Context Protocol (MCP) Integrado (`/api/v1/mcp`):** Punto de enlace JSON-RPC 2.0 nativo para agentes de IA (Claude Desktop, Hermes Agent, Cursor) con 22 herramientas de diagnóstico, auditoría y operación gobernada.
