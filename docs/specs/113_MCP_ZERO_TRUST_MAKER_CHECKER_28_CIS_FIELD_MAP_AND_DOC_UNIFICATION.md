# Especificación 113: Gobernanza Zero-Trust MCP (Maker-Checker en las 6 Herramientas de Mutación), RBAC en Capa de Servicio, Catálogo de 22 Tools, Auditoría CIS Viva de 28 Directivas, Telemetría Opt-In, Centrado de Mapa de Técnico de Campo y Unificación Documental

## 1. Contexto y Objetivo

A partir de una auditoría técnica externa sobre la versión `1.0.0` de RoSGrid y de pruebas operativas en campo, se identificaron discrepancias entre las garantías documentadas y la implementación en código, así como un defecto de centrado geográfico en el mapa del Técnico de Campo FTTH:

1. **Gobernanza Maker-Checker en Herramientas MCP de Mutación (`fastapi/src/api/v1/mcp.py` y `fastapi/src/api/v1/approvals.py`):**
   - Sólo `rosgrid_propose_network_change` generaba un `ApprovalRequest` (`status: "AWAITING_APPROVAL"`), mientras que las otras 5 herramientas de mutación (`rosgrid_reconnect_pppoe_client`, `rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit` y `rosgrid_execute_poe_aware_upgrade`) ejecutaban cambios directos sobre el router MikroTik.
   - **Solución:** Las 6 herramientas de mutación MCP (`MCP_MUTATION_TOOLS`) pasan obligatoriamente por `_create_mcp_approval_request`, devolviendo `status: "AWAITING_APPROVAL"` y `safe_mode_timeout_seconds: 60` sin tocar el router hasta que un operador humano (`Checker`) apruebe la solicitud en `POST /api/v1/approvals/{request_id}/approve` (`_execute_mcp_deferred_tool`).

2. **Aislamiento Zero-Trust del Endpoint `/api/v1/mcp` y RBAC en Capa de Servicio:**
   - Se restringe `_ALLOWED_MCP_ROLES` exclusivamente a `SystemRoleEnum.SERVICE_ACCOUNT.value` y se exige que `user.allowed_cidr_list` sea una lista no vacía (rechazando `[]` con HTTP 403).
   - Se remueve `NOC_MONITOR` de `_PROVISIONING_ROLES` en `network_services.py` (manteniéndolo únicamente en `_PROVISIONING_READ_ROLES` para lectura) y se añade validación explícita de rol en Python (`_ensure_provisioning_role` y `_ensure_admin_operations_role`) dentro de las funciones de servicio (`isolate_network_service`, `restore_network_service`, `change_network_service_rate_limit` y `_process_upgrade_stages`), impidiendo cualquier bypass de `Depends(require_roles(...))` en llamadas directas.

3. **Catálogo Completo de 22 Herramientas MCP:**
   - Se implementan las herramientas #21 (`rosgrid_search_mikrotik_docs`) y #22 (`rosgrid_get_mikrotik_doc_topic` con validación anti-SSRF sobre `https://manual.mikrotik.com/docs/`) en `TOOL_HANDLERS_MAP` y `MCP_TOOLS_CATALOG`, alcanzando las 22 herramientas documentadas.

4. **Auditoría CIS RouterOS v7 Viva de 28 Directivas (`fastapi/src/api/v1/compliance.py`) y Telemetría Opt-In (`fastapi/src/core/config.py`):**
   - `run_cis_audit` consulta en vivo `/rest/ip/ipsec/profile` (`CIS-1.9`) y `/rest/system/routerboard` (`CIS-1.6`), evaluando las 28 directivas completas de `CIS_CATALOG_BASE` (`12 Base + 8 ISP + 8 CORP`).
   - `ROSGRID_TELEMETRY_BEACON_ENABLED` cambia su valor por defecto a `False` (`Opt-In` estricto).

5. **Centrado Cartográfico en Sede Central para Técnico de Campo (`vue3/`):**
   - `RgResponsiveShell.vue` y `FieldTechMobileView.vue` invocan `authStore.fetchTenantFeatures()` al montar, inicializan los formularios NAP/Abonado con `authStore.tenantHqCoordinates` y enlazan `:center-coordinates="authStore.tenantHqCoordinates"` en `<UnifiedNetworkMap />`.

6. **Unificación Documental y Simplificación de `CHANGELOG.md`:**
   - Se unifican en `RoSGrid` y `rosgrid-web` la versión mínima `RouterOS v7.13+`, las políticas del grupo RouterOS (`api,rest-api,read,write,ftp,test,reboot,policy,sensitive`), las 28 directivas CIS y la gobernanza de las 22 herramientas MCP.
   - Se simplifica `CHANGELOG.md` a un único bloque limpio `## [1.0.0] - 2026-11-08` más `## [Unreleased]`.
