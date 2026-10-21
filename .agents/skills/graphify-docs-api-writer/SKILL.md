---
name: graphify-docs-api-writer
description: >-
  Technical authoring for operations manuals, Mermaid architecture diagrams, security ADRs, complete
  REST/WebSockets API specifications, and AI MCP integration guides (Hermes Agent and Claude) inside docs/,
  grounded in Graphify AST graphs (GRAPH_REPORT.md). Applies to RoSGrid Milestone 14.
---

# Technical Documentation, API Reference & AI MCP Authoring (Graphify AST-Grounded)

This skill guides the execution of **Milestone 14 (`14.1` to `14.8`)**, using `fastapi/graphify-out/GRAPH_REPORT.md`, `vue3/graphify-out/GRAPH_REPORT.md`, and `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md` as sources of truth.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Formatting Rules & Architectural Fidelity

1. **Semantic Grounding (`GRAPH_REPORT.md`):**
   - Before drafting documentation in `docs/`, inspect `fastapi/graphify-out/GRAPH_REPORT.md` and `vue3/graphify-out/GRAPH_REPORT.md` to accurately reference module names, Pydantic v2 schemas (`src/schemas/mcp.py`), Pinia stores, Vue 3 components, and actual backend routes.
2. **Clean Markdown Format:**
   - **Language Directive:** Write all deliverables in `docs/` in clear, professional technical Spanish.
   - Use `mermaid` blocks to illustrate architecture flows (Split-Credential, 60s Safe Mode, Maker-Checker, KeyDB WebSocket multiplexer, WORM chain, and AI MCP tool invocation flow).
   - Avoid unnecessary escaping (`\_`, `\{`) or raw citation markers.

---

## 2. Mandatory Deliverables in `docs/` (`Sub-tasks 14.1 to 14.7`)

1. **`docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` (`14.1`):**
   - Hardware/network requirements, `.env` secret generation with `openssl` (including `ROSGRID_MCP_ENABLED` and `ROSGRID_MCP_RATE_LIMIT_PER_MIN`), default **Multi-Threaded KeyDB** vs optional **DragonflyDB High-Performance Profile**, deployment via `docker-compose.yml` and `docker-compose.prod.yml`, auto-migration with `pg_advisory_lock`, and `./build.sh` usage.
2. **`docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md` (`14.2`):**
   - RouterOS v7.1+ CLI commands for TOFU self-signed TLS certificate generation, enabling `/ip/service/www-ssl`, disabling plaintext HTTP, API service user creation, and detailed explanation of *Safe Mode (Dead Man's Switch)* via `/system/scheduler`.
3. **`docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md` (`14.3`):**
   - Tenant RLS isolation, complete matrix of the **11 RBAC roles** (including `SERVICE_ACCOUNT` with CIDR whitelisting for M2M/MCP integrations), router technician assignment matrix, Vault secret revelation via *Step-Up Auth* (30s TTL autodestruction), and real-time *Kill-Switch* usage.
4. **`docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md` (`14.4`):**
   - WebFig Layer 1 and Layer 2 daily operations, WinBox-style tab bar with `<KeepAlive :max="5">`, adaptive dual density (`32px`/`44px`) with *Virtual Scrolling*, ephemeral `TelemetryRingBuffer` charts on HTML5 2D `<canvas>`, *Maker-Checker* approval queue, Git-style `.rsc` Diff viewer, 2-step CSV onboarding wizard, and **NOC Wallboard** mode.
5. **`docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md` (`14.5`):**
   - `AUDITOR` role manual, mathematical verification of the immutable WORM chain (`audit_logs` with `BRIN` index, including `MCP_AI_TOOL_CALL` events), **formal ADR detailing the 5 security reasons why RoSGrid intentionally omits an unconstrained interactive CLI/SSH terminal**, and Mermaid architecture diagrams extracted from `GRAPH_REPORT.md`.
6. **`docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` (`14.6`):**
   - Since Swagger (`/docs`), ReDoc (`/redoc`), and OpenAPI (`/openapi.json`) are suppressed in production (`ROSGRID_ENV=production`), this document provides exhaustive coverage of all `/api/v1/*` endpoints (including `POST /api/v1/mcp`) and `/ws/v1/*` WebSocket channels:
     * HTTP method, exact path, allowed RBAC roles, and *Maker-Checker* interception status.
     * Required headers (`Cookie: __Host-rg_at`, `X-CSRF-Token`, `Idempotency-Key` UUIDv7, or `Authorization: Bearer` with CIDR validation for `SERVICE_ACCOUNT`).
     * JSON request/response schemas, HTTP status codes (`200`, `201`, `202 Accepted`, `401`, `403`, `404`, `409`, `422`, `429`), and WebSocket frame structure (`TELEMETRY_TICK`, `SESSION_KILLED`, NOC alerts).
7. **`docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md` (`14.7`):**
   - Technical manual for integrating AI agents (**Hermes Agent**, **Claude Desktop / Claude Code**, and compliant MCP clients) with the **Protected MCP Endpoint (`POST /api/v1/mcp`)**:
     * **Architecture & Security:** Activation via `ROSGRID_MCP_ENABLED=true`, `SERVICE_ACCOUNT` creation, CIDR whitelisting, router assignment, KeyDB rate-limiting (`ROSGRID_MCP_RATE_LIMIT_PER_MIN`), and *Split-Credential* isolation (zero access to `AES-256-GCM` Vault keys).
     * **JSON-RPC 2.0 Streamable HTTP Protocol:** Request and response payloads for `initialize`, `ping`, `tools/list`, and `tools/call`.
     * **MCP Tool Catalog:** Detailed specifications, input schemas, and execution examples for all tools (`rosgrid_list_inventory`, `rosgrid_get_router_health`, `rosgrid_check_sfp_optical_ddm`, `rosgrid_inspect_routing_bgp_ospf`, `rosgrid_run_live_diagnostic`, `rosgrid_compare_config_diff`, `rosgrid_reconnect_pppoe_client`, `rosgrid_propose_network_change`).
     * **Client Configurations:** Ready-to-use registration blocks for Hermes Agent (`hermes_agent.yaml`) and Claude Desktop (`claude_desktop_config.json`).
     * **Autonomous 24/7 NOC Workflow (Webhooks + Maker-Checker):** Mermaid workflow showing HMAC-SHA256 webhooks alerting Hermes Agent on optical/BGP anomalies, root cause diagnosis with `.rsc` Diff, and proposed mitigations held in `AWAITING_APPROVAL` with **60s Safe Mode**.

---

## 3. Governance Sync in Root Files (`Sub-task 14.8`)

- Upon finalizing all manuals in `docs/`, verify that root governance files (`README.md`, `INSTALL.md`, `SECURITY.md`, `RESOURCES.md`, `FAQ.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`) are 100% aligned with implementation.
