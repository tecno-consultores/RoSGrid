---
name: graphify-docs-api-writer
description: >-
  Technical authoring and maintenance for operations manuals, Mermaid architecture diagrams,
  security ADRs, complete REST/WebSockets API specifications, and AI MCP integration guides
  (Hermes Agent and Claude) inside docs/, grounded in Graphify AST graphs (GRAPH_REPORT.md).
---

# Technical Documentation, API Reference & AI MCP Authoring (Graphify AST-Grounded)

This skill governs the authoring and continuous maintenance of all technical manuals in `docs/`, using `fastapi/graphify-out/GRAPH_REPORT.md` and `vue3/graphify-out/GRAPH_REPORT.md` as sources of truth.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Formatting Rules & Architectural Fidelity

1. **Semantic Grounding (`GRAPH_REPORT.md`):**
   - Before drafting or updating documentation in `docs/`, inspect `fastapi/graphify-out/GRAPH_REPORT.md` and `vue3/graphify-out/GRAPH_REPORT.md` to accurately reference module names, Pydantic v2 schemas (`src/schemas/`), Pinia stores, Vue 3 components, and actual backend routes.
2. **Clean Markdown Format:**
   - **Language Directive:** Write all deliverables in `docs/` in clear, professional technical Spanish.
   - Use `mermaid` blocks to illustrate architecture flows (Split-Credential, 60s Safe Mode, Maker-Checker, KeyDB WebSocket multiplexer, WORM chain, and AI MCP tool invocation flow).
   - Avoid unnecessary escaping (`\_`, `\{`) or raw citation markers.

---

## 2. Canonical Manuals Catalog in `docs/`

1. **`docs/MANUAL_ADMINISTRADOR_E_INSTALADOR.md` & `docs/MANUAL_USUARIO_Y_OPERADOR_NOC.md`:**
   - Master PDF-ready guides with Mermaid diagrams covering installation, Multi-Tenant governance (19 Feature Flags, 30 granular user flags, 10 router flags), 11 RBAC roles, 2FA Vault, MCP, and daily WebFig v7 NOC operations.
2. **`docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md`:**
   - Hardware/network requirements, `.env` secret generation with `openssl` (including `ROSGRID_MCP_ENABLED`, `ROSGRID_MCP_RATE_LIMIT_PER_MIN`, and opt-in `ROSGRID_TELEMETRY_BEACON_ENABLED=false`), default **Multi-Threaded KeyDB** vs optional **DragonflyDB**, deployment via `docker-compose.yml` and `docker-compose.prod.yml`, auto-migration with `pg_advisory_lock`, and `./scripts/build.sh` usage for official releases.
3. **`docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md`:**
   - **RouterOS v7.13+** CLI commands for TOFU self-signed TLS certificate generation, enabling `/ip/service/www-ssl` (port 443), disabling legacy services (`www,api,api-ssl,telnet,ftp`), creating `rosgrid-api-group` with `policy=api,rest-api,read,write,ftp,test,reboot,policy,sensitive` (explaining `ftp` policy is required by RouterOS `/export file=...` while `/ip service ftp` stays disabled), and *Safe Mode (Dead Man's Switch)* via `/system/scheduler`.
4. **`docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md`:**
   - Tenant RLS isolation, complete matrix of the **11 RBAC roles** (including `SERVICE_ACCOUNT` with mandatory non-empty `allowed_cidr_list` for MCP), router technician assignment matrix, Vault secret revelation via *Step-Up Auth* (30s TTL autodestruction), and real-time *Kill-Switch* usage.
5. **`docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md`:**
   - WebFig Layer 1 and Layer 2 daily operations, `<KeepAlive :max="5">` in-memory cache, adaptive dual density (`32px`/`44px`) with *Virtual Scrolling*, ephemeral `TelemetryRingBuffer` charts on HTML5 2D `<canvas>`, *Maker-Checker* approval queue, Git-style `.rsc` Diff viewer, 2-step CSV onboarding wizard, and **NOC Wallboard** mode.
6. **`docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md`:**
   - `AUDITOR` role manual, mathematical verification of the immutable WORM chain (`audit_logs` with `BRIN` index, including `MCP_AI_TOOL_CALL` events), **formal ADR detailing the 5 security reasons why RoSGrid intentionally omits an unconstrained interactive CLI/SSH terminal**, and Mermaid architecture diagrams.
7. **`docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`:**
   - Exhaustive specification of all `/api/v1/*` endpoints (including `POST /api/v1/mcp`) and `/ws/v1/*` WebSocket channels, since Swagger/ReDoc/OpenAPI are suppressed in production (`ROSGRID_ENV=production`).
8. **`docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`:**
   - Integration manual for AI agents (**Hermes Agent**, **Claude Desktop / Claude Code**, **Cursor**) with `POST /api/v1/mcp`:
     * **Zero-Trust Security:** Exclusive to `SERVICE_ACCOUNT` with mandatory non-empty `allowed_cidr_list`, KeyDB rate-limiting (`30 req/min`), and *Split-Credential* isolation.
     * **22 Semantic MCP Tools:** 16 read/diagnostic/grounding tools and **6 Level-3 mutation tools** (`rosgrid_reconnect_pppoe_client`, `rosgrid_propose_network_change`, `rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit`, `rosgrid_execute_poe_aware_upgrade`), all strictly governed by **Maker-Checker (`AWAITING_APPROVAL` + 60s Safe Mode)**, plus **28 live CIS Benchmark directives** in `rosgrid_run_cis_audit`.
9. **`docs/08` to `docs/12` & Root Guides (`INSTALL.md`, `FAQ.md`, `RESOURCES.md`):**
   - Local production validation pipeline (`08`), UAT master plan (`09`), Python 3.15 (`10`) and Node 26 (`11`) reports, and L2 topology / ephemeral Syslog UDP `514`/`5514` / dual Prometheus observability (`12`).

---

## 3. Operational Refresh Workflow (One-Click)

Whenever code changes modify the AST structure, refresh both graphs in ephemeral Docker using the canonical script:

```bash
./scripts/actualizar-grafos-graphify.sh
```

This updates `GRAPH_REPORT.md`, `graph.json`, and `graph.html` under `fastapi/graphify-out/` and `vue3/graphify-out/` (`--code-only`).
