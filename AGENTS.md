# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# 🤖 AI Agent Directives & Technical Governance — RoSGrid

Welcome to the **RoSGrid** repository. All AI coding assistants (Google Antigravity, Claude, Hermes Agent, Cursor, etc.) and human developers must strictly adhere to the Level-11X corporate quality and security directives defined here and in `.agents/rules/`.

> **OUTPUT LANGUAGE CONSTRAINT:**
> Always interact with the user, provide status updates, explain reasoning, and write commit messages / user-facing documentation in Spanish.
>
> **TOKEN EFFICIENCY & LANGUAGE DESIGN:**
> All directives in `.agents/rules/` and skills in `.agents/skills/` are maintained in concise, high-density technical English to optimize token utilization (~35% reduction in context window) and ensure maximum logical adherence across LLMs. All human-facing documentation (`docs/specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`) remains strictly in Spanish. See [.agents/README.md](.agents/README.md) for full architectural rationale.

---

## 1. Active Rules in `.agents/rules/`

1. [mandatory_qa_pyramid_and_doc_sync.md](.agents/rules/mandatory_qa_pyramid_and_doc_sync.md):
   - **Mandatory 11X Test Creation:** Any code addition or modification MUST include corresponding tests across the 11X quality pyramid (`docs/examples/fastapi/` and `docs/examples/vue3/`): backend unit tests (`fastapi/tests/**/*.unit.py`, `>= 95%` coverage), frontend unit tests (`vue3/src/**/*.unit.ts`, 100% Vitest pass, zero orphan `.vue` components), real PostgreSQL and Alembic schema verification, front-back integration contracts, and **Karate Labs BDD scenarios** for both API (`fastapi/test/api_test.feature`) and UI (`vue3/test/ui_business_flow.feature`), mirrored in `docs/examples/`.
   - **Anti-Silo Cross-Module State Propagation, 3-Phase Temporal Lifecycle & Semantic Audit Invariant:** Secondary state (e.g. `MaintenanceWindow`) affecting primary entities (`Router.admin_state`) MUST be verified end-to-end across modules without intermediate mocks, across all 3 temporal phases (`Scheduled`, `Active`, `Expired`), and with human-readable actor/resource labels (zero raw UUIDs in UI/audit feeds).
   - **Zero-Blindness Telemetry Invariant:** Auto-provision all 10 canonical Syslog topics (`system,info`, `account`, `firewall,info`, `pppoe,ppp,info,warning,error`, etc.) and parse RouterOS v7 BSD datagrams cleanly (`UDP 514/5514`).
   - **Concise `CHANGELOG.md` & Documentation Sync:** Synchronize affected files in `docs/`, `docs/specs/`, `ROADMAP.md`, `TESTING.md`, `README.md`, and `CHANGELOG.md` (concise 1–2 line bullets under `## [Unreleased]`, zero duplicate version headers or verbose sub-milestone dumps). Keep `.agents/ACTIVE_TASK.md` strictly inside `.agents/`.

2. [secure_development_and_testing_guidelines.md](.agents/rules/secure_development_and_testing_guidelines.md):
   - **Anti-Mock Blindness, JSONB `Decimal` Serialization & `AsyncSession` `MissingGreenlet` Invariant:** ORM changes (`src/models/`) require immediate versioned Alembic migrations verified in PostgreSQL (`\d <table>`). `MockDbSession.commit()` and `make_asserting_audit_mock` enforce strict `json.dumps()` on `JSONB` columns (`Decimal` $\rightarrow$ `float`). Avoid accessing lazy-loaded relationships in `AsyncSession` (`self.__dict__.get("attr")`) and generate a fresh `Idempotency-Key` UUID per mutation test.
   - **Anti-Regression & Blast-Radius Governance (CLI-First AST Invariant):** Inspect incoming dependency edges via `.agents/scripts/inspect_blast_radius.py` and layer boundaries via `.agents/scripts/verify_topological_health.py` before modifying shared modules. Shell-capable agents MUST run AST queries via CLI scripts (never spawn background Docker MCP daemons on host ports). Preserve canonical ports (`UDP 514/5514`, `:8000`, `:8085`), tolerate Docker NAT/bridge proxy IPs, and never clear frontend stores (`setRouters([])`) in catch blocks.
   - **Security-by-Design, Zero-Trust MCP & Service-Layer RBAC (Specs 113–114):** Forced PostgreSQL RLS per tenant (`rosgrid_app` `NOSUPERUSER NOBYPASSRLS` + `after_begin` multi-transaction listener + deterministic WORM audit chain), anti-SSRF validation (`validate_router_target_url`), `AES-256-GCM` Vault with 30s Step-Up 2FA, HMAC-SHA256 CSRF protection, and SuperAdmin tenant fast-switching (`notify_ws=False`). `POST /api/v1/mcp` is exclusive to `SERVICE_ACCOUNT` with a mandatory non-empty `allowed_cidr_list`; all **6 Level-3 MCP mutation tools** require Maker-Checker approval (`status: "AWAITING_APPROVAL"`, 60s Safe Mode); mutating service functions validate `claims["rol"]` in Python to prevent `Depends(require_roles(...))` bypass; and `run_cis_audit` evaluates all **28 CIS Benchmark directives** live.
   - **Feature Flags, RBAC UI Visibility & Opt-In Telemetry (Specs 55, 64 & 113):** 4-tier permission resolution (`Tenant Flag` $\rightarrow$ `User Override` $\rightarrow$ `Role Matrix 30×11` $\rightarrow$ `Router Permissions 10 Flags`), proactive UI hiding (`v-if="canUseUserFeature(...)"`) with 100% `_READ_ROLES` parity, `ROSGRID_TELEMETRY_BEACON_ENABLED=false` (`Opt-In` by default), and dual Prometheus endpoints (`GET /metrics` vs `GET /api/v1/metrics/fleet`).
   - **Operational Separation & Explicit User Authorization:** Build `local-test` images (`sinfallas/rosgrid-backend:local-test` and `sinfallas/rosgrid-frontend:local-test`) for local testing (`docker-compose.prod.local.yml`); reserve `./scripts/build.sh` strictly for official Docker Hub releases. Never modify code without explicit user authorization in chat.

3. [frontend_parity_and_closure.md](.agents/rules/frontend_parity_and_closure.md):
   - **Terminal ↔ Frontend & Zero-Orphan API Parity (Spec 60):** Every backend endpoint in `fastapi/src/api/v1/` must pair with an actionable Vue 3 interface (`0` broken 404/405 calls, certified by `.agents/scripts/verify_no_orphan_api_endpoints.py`).
   - **WebFig v7 Parity, Layer 2 Next-Gen Engine & Map Ergonomics (Specs 54, 104–113):** Tactical CRUD + 1-click wizards under 60s Safe Mode across all L1/L2 modules; L2 contextual RPC actions, `/rest/console/inspect` fallback, `.query`/`.proplist`, bulk ops, and `.rsc` export/diff; `<= 25m` multi-node map clustering (`rg-map-pin--multi`) and automatic `authStore.tenantHqCoordinates` centering in `FieldTechMobileView.vue` and `UnifiedNetworkMap.vue`.
   - **Refactoring UI, Dynamic Themes, Stacking Context & Notification Center (Specs 53, 79–82, 107–114):** All `var(--rg-*)` tokens defined across all 3 themes (`dark`, `light`, `noc-high-contrast`, zero hardcoded `data-theme` on view roots); `.rg-header` (`z-index: 3000`) isolated above `.rg-main` (`z-index: 1`) and translucent Wallboard HUD (`.wallboard-events-overlay`); safe vertical scroll and baseline-aligned `.form-row-2col` in `LoginView.vue`; contextual help (`helpCatalog.ts`, zero PDF buttons in `RoSGrid`), `X-Robots-Tag: noindex`, 6 MCP client snippets in `RgMcpTokenModal.vue`, and `RgNotificationCenterBell.vue` (`Alt+N`) separating *Read* vs *Resolved* states.

4. [ground_truth_fixtures_and_negative_invariants.md](.agents/rules/ground_truth_fixtures_and_negative_invariants.md):
   - **Universal Trimodal Fixtures & Negative Invariants:** Validate all 8 RouterOS v7 domains (Syslog, CIS Hardening, L2 Topology, IPAM DHCP, PoE, Rogue DHCP, CAPsMAN WiFi, and Config Drift) against three raw JSON fixtures: Factory Default (asserting negative/unconfigured), Nominal RoSGrid (asserting active/online), and Degraded/Unsupported (asserting graceful handling without 500 errors), plus real-fleet smoke testing (`scripts/validar-flota-real.py`).

---

## 2. Rule Zero: Ephemeral Docker Execution

**NEVER** execute tests, migrations, linters, or operational scripts directly on the host machine (`Ubuntu`). All executions must occur inside ephemeral Docker containers as defined in [`Makefile`](Makefile) (`sinfallas/rosgrid-backend:local-test`, `sinfallas/base-node-ionic:26`, and `docker-compose.prod.local.yml`).

---

## 3. Skills Catalog

### Project Domain Skills (`.agents/skills/`):
1. [`rosgrid-noc-operator`](.agents/skills/rosgrid-noc-operator/SKILL.md): NOC Operator & Autonomous Diagnostics for MikroTik RouterOS v7.13+ via MCP (`/api/v1/mcp`) with 8 SOP Playbooks, 22 tools, and Maker-Checker governance across all 6 mutation tools.
2. [`mikrotik-webfig-safemode`](.agents/skills/mikrotik-webfig-safemode/SKILL.md): RouterOS v7.13+ REST API domain rules (`policy=api,rest-api,read,write,ftp,test,reboot,policy,sensitive`), native flags, `<KeepAlive :max="5">`, 60s Safe Mode, and 30s Step-Up Auth Vault.
3. [`vue3-wcag-tactical-ui`](.agents/skills/vue3-wcag-tactical-ui/SKILL.md): WinBox-style high-density Vue 3 + TypeScript architecture (Tactical NOC Cyan), `shallowRef`, virtual scrolling, and WCAG 2.1 AA compliance.
4. [`graphify-docs-api-writer`](.agents/skills/graphify-docs-api-writer/SKILL.md): Technical authoring and maintenance for operations manuals, Mermaid architecture, REST/WebSockets API specs, and AI MCP integration guides grounded in `GRAPH_REPORT.md`.

### Global QA 11X & Infrastructure Skills (`~/.gemini/config/skills/`):
- `qa-11x-architect` & `qa-11x-docker-certifier`: Master QA 11X & DevSecOps architecture, ephemeral Docker execution, coverage `>= 95%`, Karate Labs BDD, and STIG/OWASP compliance.
- `refactoring-ui`: Visual hierarchy, spacing, typography, color tokens, and WCAG 2.1 AA polish.
- `docker-trivy-keydb-hardening`: Container hardening (Trivy HIGH/CRITICAL = 0) and Multi-Threaded KeyDB performance.
- `graphify-ast-navigator`: AST Knowledge Graph navigation, blast-radius pre-audit, and layer boundary compliance.

---

## 4. Automation Scripts in `.agents/scripts/`

- `verify_alembic_orm_parity.py`: Validates parity between SQLAlchemy ORM models and Alembic migrations.
- `verify_json_no_duplicate_keys.py`: Detects duplicate keys in i18n JSON locale files.
- `verify_topological_health.py`: Detects forbidden cross-layer coupling and AST layer boundary violations.
- `inspect_blast_radius.py`: Calculates incoming dependency edges across the codebase prior to refactoring.
- `verify_zero_orphan_vue_components.py`: Certifies 100% of Vue components and views have unit test suites.
- `verify_no_orphan_api_endpoints.py`: Certifies 100% bidirectional parity between FastAPI endpoints and Vue 3 HTTP calls.
- `verify_anti_silo_test_quality.py`: Prohibits blind `write_audit_log` mocks and enforces anti-UUID semantic audit verification.
- `verify_roadmap_consistency.py`: Validates consistency between `ROADMAP.md` and `.agents/ACTIVE_TASK.md`.
- `certify_task_completion.sh`: End-to-end 9-step certification gate.

---

## 5. Official MikroTik RouterOS v7.13+ Grounding & Technical References

- **Official MikroTik v7 Documentation Hub:** [https://manual.mikrotik.com/docs/introduction/](https://manual.mikrotik.com/docs/introduction/)
- **Open LLM Index (Fast Semantic Retrieval):** [https://manual.mikrotik.com/llms.txt](https://manual.mikrotik.com/llms.txt)
- **Command Line & REST API Reference:** [https://manual.mikrotik.com/docs/cli-reference/](https://manual.mikrotik.com/docs/cli-reference/)

---

<!-- QA_11X_MCP_CONNECTOR_START -->
## 🤖 Central QA 11X Skill & MCP Server Connector (`@sinfallas/mcp-qa-11x`)

> **OUTPUT LANGUAGE & HIGH-IQ TOKEN ECONOMY:** Interact, explain reasoning, and write commits/docs strictly in **Spanish**. Apply *3-Tier Progressive Disclosure* (read `.agents/rules/*.md` and `references/*.md` on-demand only), *AST/Grep-First & Windowed-Read-Second* (`StartLine`/`EndLine` 40–80 lines; never read full files `>150` lines blindly), *Zero Redundant Re-Read*, *Parallel Tool Batching*, and *Subagent Context Isolation* (`<=20` line summary return).

This project (`RoSGrid`) enforces the **Level-11X Quality & DevSecOps Standard** (stacks: `python`, `vue3`).

1. **3-Path Proportional Execution (`DOCS_ONLY` vs. `MICRO_CHANGE` vs. `CODE_CHANGE` / `FULL_11X`):**
   - **`DOCS_ONLY` Fast-Path (ONLY `*.md` / `docs/` changed):** DO NOT run test suites (`run_ephemeral_qa`) and DO NOT rebuild AST graphs (`./scripts/actualizar-grafos-graphify.sh`). Only sync docs/`CHANGELOG.md`, run `certify_11x_gate`, and push to `git`.
   - **`MICRO_CHANGE` Surgical-Path (`<= 3` files, 0 new API/ORM changes, `LOW` AST Blast Radius `< 5` callers):** Use an inline 3-line plan, run `inspect_ast_blast_radius`, execute affected stack `run_ephemeral_qa` in Docker (**Rule Zero**), update stack AST graph, sync `CHANGELOG.md`, run `certify_11x_gate`, and `git push`.
   - **`CODE_CHANGE` (`FULL_11X`) Architectural-Path (`> 3` files, new API/UI, ORM migrations, security, or `MED`/`HIGH` Blast Radius):** Execute all 11 steps below inside ephemeral Docker (**Rule Zero** — never run `pytest`, `vitest`, `npm`, `pnpm`, `uv`, or linters on host OS).
2. **Skills & MCP Tools (`@sinfallas/mcp-qa-11x`):** Load `qa-11x-architect` (backend/QA/DevSecOps) and `refactoring-ui` (UI/CSS). Use `inspect_project_config`, `audit_test_pyramid_gaps`, `inspect_ast_blast_radius`, `audit_security_stig_owasp`, `run_ephemeral_qa` (`skip_if_docs_only: true` supported), `certify_11x_gate`, `clean_workspace_11x`, `reconcile_agents_governance`, and `propose_skill_evolution_pr` (on QA-escape bug fixes, proactively include `💡 Oportunidad de Mejora Detectada para el Estándar QA 11X` and invoke `propose_skill_evolution_pr`).
3. **Mandatory 11-Step Execution & Closure Workflow (Non-Negotiable for Architectural Code Changes):**
   - **Step 1 (Plan):** Invoke `/plan` or plan artifact before modifying code.
   - **Step 2 (Active Task):** Track real-time progress (`- [ ]` -> `- [x]`) in `.agents/ACTIVE_TASK.md` (compact `<= 40 lines`).
   - **Step 3 (Pre-Change AST Graph):** Check blast radius (`inspect_ast_blast_radius`); if `graphify-out/graph.json` is missing, create it first via `./scripts/actualizar-grafos-graphify.sh`.
   - **Step 4 (Governance & Cleanup):** Sync `AGENTS.md`, `.agents/`, `scripts/limpieza.sh`, and `.gitignore`.
   - **Step 5 (11X Tests + Karate Labs):** Create unit (`>= 95%` coverage), integration, and **Karate Labs BDD (`.feature`)** tests.
   - **Step 6 (Full Suite Execution):** Run all suites in ephemeral Docker (`Rule Zero` / `run_ephemeral_qa`, 0 warnings).
   - **Step 7–9 (Docs, Changelog & Roadmap):** Sync `docs/specs/`, `README.md`, `TESTING.md`, `CHANGELOG.md`, and `ROADMAP.md`.
   - **Step 10 (Post-Change AST Graph):** Run `./scripts/actualizar-grafos-graphify.sh` (incremental per modified stack).
   - **Step 11 (Certify & Push):** Run `./.agents/scripts/certify_task_completion.sh`, `certify_11x_gate`, and `clean_workspace_11x`, mark `.agents/ACTIVE_TASK.md` `COMPLETED (100%)` (suggest `/compact`), and `git push`.
<!-- QA_11X_MCP_CONNECTOR_END -->
