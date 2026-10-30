# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# 🤖 AI Agent Directives & Technical Governance — RoSGrid

Welcome to the **RoSGrid** repository. All AI coding assistants (Google Antigravity, Claude, Hermes Agent, Cursor, etc.) and human developers must strictly adhere to the Level-11X corporate quality and security directives defined here and in `.agents/rules/`.

> **OUTPUT LANGUAGE CONSTRAINT:**
> Always interact with the user, provide status updates, explain reasoning, and write commit messages / user-facing documentation in Spanish.
>
> **TOKEN EFFICIENCY & LANGUAGE DESIGN:**
> All directives in `.agents/rules/` and skills in `.agents/skills/` are maintained in concise, high-density technical English to optimize token utilization (~35% reduction in context window) and ensure maximum logical adherence across LLMs (Google Antigravity, Claude, Hermes Agent, Cursor). All human-facing documentation (`docs/specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`) remains strictly in Spanish. See [.agents/README.md](file:///.agents/README.md) for full architectural rationale.

---

## 1. Active Rules in `.agents/rules/`

1. [mandatory_qa_pyramid_and_doc_sync.md](file:///.agents/rules/mandatory_qa_pyramid_and_doc_sync.md):
   - **Supreme Directive — Mandatory 11X Test Creation:** Any code addition or modification MUST strictly include corresponding test suites across all layers of the 11X quality pyramid, using the canonical blueprints provided in `docs/examples/` (`docs/examples/fastapi/` and `docs/examples/vue3/`). Includes backend unit tests (`fastapi/tests/**/*.unit.py` with `>= 95%` coverage), frontend unit tests (`vue3/src/**/*.unit.ts` Vitest 100% pass), real PostgreSQL and Alembic schema verification, front-back integration contracts, and **ALWAYS Karate Labs BDD scenarios** for both API (`fastapi/test/api_test.feature`) and UI (`vue3/test/ui_business_flow.feature`), synchronized in `docs/examples/`.
   - **Zero-Orphan Vue Component Invariant:** Every `.vue` component or view in `vue3/src/` must have a dedicated, co-located `.unit.ts` suite maintaining 100% pass rate.
   - **Zero-Blindness Telemetry Invariant:** Proactively auto-provision all 9 canonical Syslog topics (`system,info`, `account`, `firewall,info`) and parse RouterOS v7 BSD logs cleanly.
   - **Mandatory Test Execution:** The full test suite MUST be executed and passed inside ephemeral Docker containers (`Rule Zero`) after EACH task modifying code before concluding.
   - **Continuous Mandatory Documentation Sync:** Autonomously and continuously update after any code modification:
     - All affected operational guides and technical manuals in `docs/`.
     - All affected domain architectural specifications in `docs/specs/`.
     - Change history in `CHANGELOG.md` (under `## [Unreleased]`).
     - Milestone and sub-task progress tracking in `ROADMAP.md`.
     - Quality metrics and test counts in `TESTING.md`.
     - Repository root documentation (`README.md`, etc., when applicable) or operational guides in `docs/` (`INSTALL.md`, `FAQ.md`, `RESOURCES.md`).

2. [secure_development_and_testing_guidelines.md](file:///.agents/rules/secure_development_and_testing_guidelines.md):
   - **Anti-Mock Blindness:** ORM changes (`src/models/`) require immediate versioned Alembic migrations verified in PostgreSQL (`\d <table>`).
   - **Security-by-Design:** Forced PostgreSQL RLS per tenant, anti-SSRF URL validation (`validate_router_target_url`), AES-256-GCM Vault cryptography, HMAC-SHA256 CSRF protection, mandatory `Idempotency-Key` headers, and SuperAdmin tenant fast-switching with atomic KeyDB session re-keying, Pub/Sub suppression (`notify_ws=False`) and WORM audit.
   - **Visual Geometry & In-Flow Ergonomics (Anti-Sticky Footer):** JSDOM does not calculate layout or bounding boxes. Validate DOM tree order and inspect viewports in real browser sessions. Prohibit fixed floating bottom footers that steal vertical real estate; enforce in-flow footers inside `<main>` (`margin-top: auto`).
   - **Feature Flags Governance & DAG Hard Lock:** Flags are tenant-scoped commercial capabilities; enforce DAG cascade lock (disabling child flags if parent is off), 1-click Contingency low-power preset, and Blast Radius confirmation shield.
   - **Operational Separation Invariant:** Never run `./scripts/build.sh` for intermediate local testing; build `local-test` images (`sinfallas/rosgrid-backend:local-test` and `sinfallas/rosgrid-frontend:local-test`) and recreate `docker-compose.prod.local.yml`. `build.sh` is reserved strictly for official milestone releases.
   - **Critical Execution Gate:** AI agents must NEVER modify code based on IDE timeouts or 'Auto-proceed' signals; code changes require explicit user authorization in the chat.

3. [frontend_parity_and_closure.md](file:///.agents/rules/frontend_parity_and_closure.md):
   - **Terminal ↔ Frontend Parity:** Zero console-only actions or orphan API endpoints without a matching Vue 3 interface.
   - **Zero Read-Only Operational Consoles (WebFig v7 Parity):** Router management tables (Firewall, Queues, PPP, DHCPv4, Dual-Stack IPv6, Routing) MUST offer tactical mutation actions (create, edit, toggle, delete, 1-click wizards) with 60s Safe Mode; no screen may remain view-only when RouterOS REST API supports mutations.
   - **Zero-Overlap Geographic Co-location Invariant (Anti-Superposición Cartográfica):** Cartographic Leaflet maps (`UnifiedNetworkMap.vue`, `OsmRouterMap.vue`) MUST group co-located network devices (`<= 25m`) into a distinct cluster marker (`rg-map-pin--multi`) with numeric count badges, interactive radial spiderfication, and full side-drawer listing to prevent markers from being obscured by DOM stack order.
   - **Refactoring UI Hierarchy & Zero-Orphan CSS Token Invariant:** All `var(--rg-*)` tokens MUST be declared across all 3 themes in `themes.css` with named spacing/radius/typography scales, 1 primary button per view, neutral-at-rest secondary/row actions, concentric segmented radii (`8px`/`5px`), tactical `RgDataTable` empty states, and geometric Online/Offline indicators for colorblind accessibility.
   - **Responsive Multi-Viewport & Zero Horizontal Overflow Invariant:** Enforce zero horizontal viewport overflow across mobile (`375x667`), tablet (`768x1024`), and desktop (`1440x900`), `100dvh` shells with `overscroll-behavior: contain`, `.table-wrapper` horizontal scroll containment on all tables, decoupled mobile drawer opening (`.rg-rail.rg-rail--collapsed.rg-rail--open`), inline WebFig module drawer toggle (`.btn-webfig-menu-inline`) on `<= 1024px`, and bottom-anchored map drawers on narrow screens.
   - **Contextual Help Boundary, Zero-Trust Anti-Indexing & LLM-Ready MCP Context Invariant:** Every global route and WebFig module must map to a rich topic in `RgContextualHelpDrawer.vue` (`helpCatalog.ts`, zero PDF buttons inside `RoSGrid`), enforce `X-Robots-Tag: "noindex, nofollow, noarchive, nosnippet"` and `<meta name="robots">`, persist `rg_theme` and `rg_table_density` with native `color-scheme` tokens, and expose 6 MCP client tabs + `# Agent Instructions` (`ask`/`goal`) `llms.txt` generator in `RgMcpTokenModal.vue`.
   - **WebFig Layer 2 Next-Gen Universal Engine Invariant (Spec 54):** `DynamicLayer2ResourceView.vue` and `webfig_layer2.py` enforce contextual RPC actions (`L2_RPC_ACTIONS_CATALOG` + `RgLayer2RpcActionModal.vue`), `/rest/console/inspect` schema discovery for empty tables, server-side `.query` & `.proplist` projection (`RgLayer2QueryBuilder.vue`), multi-row bulk mutations under a single 60s Safe Mode window, contextual `.rsc` export & unified Diff (`RgLayer2RscExportDiffModal.vue`), and persisted column profiles (`useLayer2ColumnProfiles.ts`) + 1-click presets (`layer2PresetsCatalog.ts`).
   - **Closure Protocol & Mandatory Git Push:** Test creation and execution in ephemeral Docker, mandatory synchronization of `docs/`, `docs/specs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`, and `README.md`, secret scanning, and automated Git publication (`git add`, `git commit`, and `git push`).


4. [continuous_agent_evolution.md](file:///.agents/rules/continuous_agent_evolution.md):
   - **Autonomous Evolution of `.agents/`:** Proactively update rules, skills, and automation scripts whenever discovering an improvement opportunity, unhandled edge case, procedure automation, or token optimization without waiting for user prompting.

5. [anti_regression_and_side_effects_guardrail.md](file:///.agents/rules/anti_regression_and_side_effects_guardrail.md):
   - **Anti-Regression & Blast-Radius Governance (CLI-First Invariant):** Zero degradation of pre-existing functionality when introducing changes. Mandatory pre-modification impact audit for shared files, Docker Compose ports (canonical UDP 514/5514 must never be dropped), and AST blast radius (`.agents/scripts/inspect_blast_radius.py`). Shell-capable agents (Antigravity) MUST execute AST inspection directly via CLI/scripts and never spawn background Docker MCP daemons or occupy port 8080. MCP (`graphify-mcp`) is reserved exclusively for external non-shell clients (Claude Desktop, Hermes Agent). Docker NAT/bridge proxy tolerance with heuristic payload/identity fallback, strict pre-build static typing/linting (`ruff`, `vue-tsc`), and non-destructive frontend error handling (no `setRouters([])` in generic catch blocks).

6. [ground_truth_fixtures_and_negative_invariants.md](file:///.agents/rules/ground_truth_fixtures_and_negative_invariants.md):
   - **Universal Trimodal Fixtures & Negative Invariants:** Eradicate Mock Blindness across all 8 RouterOS v7 domains (Syslog, CIS Hardening, L2 Topology, IPAM DHCP, PoE, Rogue DHCP, CAPsMAN WiFi, and Config Drift). Every endpoint/integration MUST be tested against three raw JSON fixtures: Factory Default (asserting negative/unconfigured), Nominal RoSGrid (asserting active/online), and Degraded/Unsupported (asserting graceful degradation without 500 errors). Real-fleet smoke testing (`scripts/validar-flota-real.py`) mandatory before concluding tasks.

---

## 2. Rule Zero: Ephemeral Docker Execution

**NEVER** execute tests, migrations, linters, or operational scripts directly on the host machine (`Ubuntu`). All executions must occur inside the project's ephemeral Docker containers (`docker-compose.qa.yml`, `docker-compose.prod.local.yml`, and `Makefile`).

---

## 3. Skills Catalog in `.agents/skills/`

1. `rosgrid-noc-operator`: NOC Operator & Autonomous Diagnostics for MikroTik RouterOS v7 via MCP (`/api/v1/mcp`) with 8 SOP Playbooks and 22 tools.
2. `qa-11x-docker-certifier`: QA 11X Corporate Standard certifier in ephemeral Docker (coverage `>= 95%`, SonarJS, Karate Labs, mutation testing).
3. `mikrotik-webfig-safemode`: RouterOS v7 REST API domain rules, native flags, 60s Safe Mode, and 30s Step-Up Auth Vault.
4. `vue3-wcag-tactical-ui`: WinBox-style high-density Vue 3 + TypeScript architecture (Tactical NOC Cyan), virtual scrolling, and WCAG 2.1 AA compliance.
5. `docker-trivy-keydb-hardening`: Docker container hardening (Trivy HIGH/CRITICAL = 0), Multi-Threaded KeyDB in-memory engine, and backend performance.
6. `graphify-docs-api-writer`: Technical authoring for operations manuals, Mermaid architecture, REST/WebSockets API specs, and AI MCP integration guides.
7. `graphify-ast-navigator`: AST Knowledge Graph navigation, blast-radius pre-audit, layer boundary compliance, CLI-first query protocol for shell agents, and local MCP topology server integration.

---

## 4. Automation Scripts in `.agents/scripts/`

- `verify_alembic_orm_parity.py`: Automated parity validator between SQLAlchemy ORM models and Alembic migrations (detects schema drift).
- `verify_json_no_duplicate_keys.py`: Automated integrity validator detecting duplicate keys in i18n JSON locale files.
- `verify_topological_health.py`: Automated AST architectural validator detecting forbidden cross-layer coupling and layer boundary violations.
- `inspect_blast_radius.py`: Automated pre-refactoring blast radius inspector calculating incoming dependency edges across the codebase.
- `verify_zero_orphan_vue_components.py`: Automated parity validator ensuring 100% of Vue components and views have dedicated or active unit test suites.
- `certify_task_completion.sh`: End-to-end certification gate enforcing secret scanning, ORM parity, front-back contracts, i18n integrity, topological health, zero orphan Vue components, and documentation sync.

---

## 5. Official MikroTik RouterOS v7 Grounding & Technical References

> **CANONICAL GROUNDING DIRECTIVE — ZERO HALLUCINATIONS:**
> To prevent legacy RouterOS v6 syntax hallucinations (e.g. invalid syslog parameters, hyphenated action names, or illegal `PATCH` calls on singleton menus), all AI agents and developers modifying or creating RouterOS REST integrations, Golden Config templates, or CLI workflows MUST consult the official MikroTik documentation:
>
> - **Official MikroTik v7 Documentation Hub:** [https://manual.mikrotik.com/docs/introduction/](https://manual.mikrotik.com/docs/introduction/)
> - **Open LLM Index (Fast Semantic Retrieval):** [https://manual.mikrotik.com/llms.txt](https://manual.mikrotik.com/llms.txt)
> - **Command Line & REST API Reference:** [https://manual.mikrotik.com/docs/cli-reference/](https://manual.mikrotik.com/docs/cli-reference/)
>
> Prior to implementing REST endpoints under `/rest/*` or executing actions in `/bulk-ops` or MCP tools, verify parameter schemas, singleton menu mechanics (`POST <endpoint>/set`), and native property types directly against these official sources.

---

## 6. Mandatory Git Publication Directive & Task Closure Gate

> **NON-NEGOTIABLE:** Following **EACH** task or user request modifying, adding, or fixing source code (`fastapi/`, `vue3/`, scripts, or configurations), the AI agent **MUST** autonomously execute the following 7-step protocol before completing its turn:
>
> 1. **Mandatory 11X Test Creation (ALWAYS Including Karate Labs):** Create or extend unit and integration tests in `fastapi/tests/` and `vue3/src/`, and **ALWAYS incorporate Karate Labs BDD scenarios** in `fastapi/test/api_test.feature` (API) and `vue3/test/ui_business_flow.feature` (UI), strictly replicating them in canonical blueprints under `docs/examples/` (`docs/examples/fastapi/` and `docs/examples/vue3/`).
> 2. **Mandatory Test Execution & Anti-Regression Verification:** Execute the complete test suite in ephemeral Docker containers (`Rule Zero`), certifying `>= 95%` coverage, 100% passed assertions, Karate Labs BDD contract validation, and 0 typing/linting errors (`ruff`, `mypy`, `eslint`, `vue-tsc`), and perform smoke checks on adjacent pre-existing features to guarantee zero regressions.
> 3. **Mandatory Documentation Synchronization:** Unconditionally update all affected files across:
>    - `docs/` (operations manuals, guides, and REST/WebSockets API specifications).
>    - `docs/specs/` (domain architectural specifications).
>    - `CHANGELOG.md` (section `## [Unreleased]`).
>    - `ROADMAP.md` (milestone and sub-task status).
>    - `TESTING.md` (assurance metrics and test counts).
>    - Repository root (`README.md`, etc., when applicable) or `docs/` (`INSTALL.md`, `FAQ.md`, `RESOURCES.md`).
> 4. **Secret Scanning, Local Dependency Audit & ORM Parity:** Run `./scripts/verificar-secretos.sh`, execute local vulnerability and IaC audit via `make audit` (`./scripts/auditar-infra.sh` in ephemeral Docker) certifying 0 CRITICAL/HIGH findings, and certify ORM schema parity against PostgreSQL.
> 5. **Stage Changes:** Register all modifications via `git add .`.
> 6. **Semantic Commit:** Create commit following Conventional Commits strictly in Spanish: `git commit -m "<tipo>(<ámbito>): <descripción_en_español>"`.
> 7. **Immediate Remote Push:** Publish to remote repository via `git push origin <current_branch>`.
>
> **Under no circumstances** may the agent conclude a response with uncommitted changes or outdated documentation in the working tree.
