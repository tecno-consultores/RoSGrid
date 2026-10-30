# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Terminal ↔ Frontend Parity & Task Closure Protocol

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers working on RoSGrid.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Terminal ↔ Frontend Parity Invariants

1. **Zero Console-Exclusive Actions:** Any administrative, operational, or diagnostics action executable from the terminal (except initial unattended system bootstrap) MUST have an equivalent Vue 3 screen.
2. **Zero Orphan API Endpoints:** Every route defined under `fastapi/src/api/v1/` MUST be paired with a frontend interface enabling visual inspection, parameter configuration, and interactive verification.
3. **Bidirectional Audit Sync:** Maintenance CLI scripts issuing tokens or altering sessions MUST sync metadata into KeyDB/Redis (`issued_by_username: "CLI (Terminal)"`) so they are visible and revocable via `ActiveSessionsKillSwitchView.vue`.
4. **Zero Read-Only Operational Consoles (WebFig v7 Parity):** Every router management table (Firewall, Queues, PPP, DHCPv4, Dual-Stack IPv6, Routing) MUST offer tactical mutation actions (create, edit, toggle enable/disable, delete with confirmation and 1-click setup wizards) guarded by 60s Safe Mode. No screen may be left in view-only state when RouterOS REST API supports mutations.
5. **Zero-Overlap Geographic Co-location Invariant (Anti-Superposición Cartográfica):** Any cartographic or topology map rendering network entities (routers, ONUs, switches) in Leaflet/OpenStreetMap (`UnifiedNetworkMap.vue`, `OsmRouterMap.vue`, `OsmOnuMap.vue`) MUST group co-located items (distance `<= 25m`) into a distinct cluster marker (`rg-map-pin--multi`) with a numeric count badge. It MUST provide radial spiderfication upon click and a detailed side-drawer card listing all co-located items to prevent any device from being hidden or obscured by DOM injection order.
6. **Refactoring UI Hierarchy & Zero-Orphan CSS Token Invariant:** All `var(--rg-*)` CSS custom properties MUST be defined across all 3 themes in `vue3/src/assets/themes.css` (using named spacing, radius, and 7-step typography scales). Views must enforce a single primary button rank, keep secondary header/row actions neutral at rest (illuminating semantic colors on `:hover` / `:focus-visible`), apply concentric border radii (`8px` outer / `5px` inner), provide tactical empty states in `RgDataTable.vue`, and pair status colors with geometric shape differentiation (solid dot vs. hollow ring) for colorblind safety.
7. **Responsive Multi-Viewport & Zero Horizontal Overflow Invariant:** All views, tables, maps, and modals MUST render with zero unintended horizontal viewport overflow (`document.documentElement.scrollWidth <= window.innerWidth`) across mobile (`375x667`), tablet (`768x1024`), and desktop (`1440x900`). Enforce `100dvh` progressive viewport units with `overscroll-behavior: contain` on shells/drawers, wrap all `<table>` elements in `.table-wrapper` / `.table-scroll-wrapper` (`overflow-x: auto; max-width: 100%`), decouple desktop sidebar collapse from mobile/tablet drawer opening (`.rg-rail.rg-rail--collapsed.rg-rail--open`), expose the inline WebFig module toggle (`.btn-webfig-menu-inline`) on `<= 1024px`, and anchor map detail drawers at the bottom within viewport width on narrow screens.
8. **Contextual Help Boundary, Zero-Trust Anti-Indexing & LLM-Ready MCP Context Invariant:** Every global route and WebFig module MUST resolve to a rich operational guide in `RgContextualHelpDrawer.vue` (`helpCatalog.ts`) with `[ 📋 Copiar Guía como Markdown ]` and strictly zero PDF conversion buttons inside `RoSGrid` (PDF generation belongs exclusively to `rosgrid-web`). The private NOC console (`vue3/nginx/default.conf` and `vue3/index.html`) MUST enforce `X-Robots-Tag: "noindex, nofollow, noarchive, nosnippet"` and `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">`, persist `rg_theme` and `rg_table_density` in `localStorage` with native `color-scheme` declarations, and provide 1-click `llms.txt` context (`# Agent Instructions`: `ask` + `goal`) plus config snippets for all 6 MCP clients in `RgMcpTokenModal.vue`.



---

## 2. Proactive Vulnerability Audit

Before exposing new endpoints or frontend views:

1. **User State Checks:** Ensure inactive (`is_active = False`) or locked (`is_locked = True`) accounts cannot generate tokens or trigger protected actions.
2. **Multi-Tenant Context:** Ensure every DB query executes within an active tenant context (`set_tenant_context`).
3. **Automated SAST:** Run Bandit (`bandit -r src/ -ll`) and dependency auditing in ephemeral Docker with 0 High/Medium alerts.
4. **Anti-XSS & Anti-CSRF:** In Vue 3, never bind unescaped dynamic HTML (`v-html`); in FastAPI, mandate CSRF tokens on mutation endpoints and strict SameSite cookies.

---

## 3. Mandatory Task Closure Protocol & Autonomous Git Publication

After **EVERY** task or turn that adds, edits, or removes code or configuration files, the AI agent **MUST** autonomously execute this protocol and publish to Git without waiting for user prompting:

1. **Mandatory 11X Test Creation (Including Karate Labs for API & UI):**
   - For backend mutations: add/update unit tests in `fastapi/tests/**/*.unit.py` AND mandatory BDD scenarios in `fastapi/test/api_test.feature` (mirrored in `docs/examples/fastapi/`).
   - For frontend mutations: add/update unit tests in `vue3/src/**/*.unit.ts` AND mandatory BDD scenarios in `vue3/test/ui_business_flow.feature` (mirrored in `docs/examples/vue3/`).
   - **Karate Labs Invariant:** Every single code change MUST include corresponding Karate Labs API and/or UI scenarios.
2. **Full Ephemeral Docker Test Execution (`Rule Zero`):**
   - Backend: `docker compose -f docker-compose.qa.yml run --rm qa-backend uv run pytest tests/ --cov=src --cov-fail-under=95`
   - Frontend: `docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run test:unit` & `type-check` (100% pass, 0 type errors).
   - Linters: `ruff check`, `mypy --strict`, `eslint`, `prettier`.
3. **Autonomous & Mandatory Multi-Layer Documentation Sync:**
   - Update affected operational and technical manuals in `docs/` (including `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`).
   - Update affected specifications in `docs/specs/`.
   - Update `CHANGELOG.md` under `## [Unreleased]`.
   - Update `ROADMAP.md` task checkpoints and deliverables.
   - Update `TESTING.md` metrics and counts.
   - Update `README.md` and root documentation when user-facing interfaces or architectures change.
4. **Secret, Dependency Vulnerability, i18n & Parity Certification:**
   - Run `./scripts/verificar-secretos.sh` (0 secret leaks).
   - Run `make audit` (or `./scripts/auditar-infra.sh` in ephemeral Docker, certifying 0 CRITICAL/HIGH findings).
   - Run `python3 .agents/scripts/verify_json_no_duplicate_keys.py` (0 duplicate keys in locale files).
   - Run `./.agents/scripts/certify_task_completion.sh` (all 8 gates passed).
5. **Mandatory Git Commit & Push:**
   - Run `git add .`
   - Create a commit following Conventional Commits in Spanish: `git commit -m "<tipo>(<ámbito>): <descripción_en_español>"`
   - Push immediately to remote: `git push origin <current_branch>`
   - **Never leave uncommitted or unpushed code changes** in the workspace at the end of a response.


