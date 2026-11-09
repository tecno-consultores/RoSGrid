# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory QA Pyramid & Autonomous Documentation Sync Directive

> **SUPREME DIRECTIVE FOR AI AGENTS & CONTRIBUTORS:**
> Never conclude a task, suggest commits, or finish execution turns without proactively fulfilling the following three non-negotiable requirements whenever code is created or modified. Do not wait for user prompting.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Mandatory 11X Test Creation (Using `docs/examples/` as Blueprints)

Any modification, addition, or bugfix in source code (`fastapi/src/` or `vue3/src/`) MUST be accompanied by corresponding tests across the full 11X test pyramid. The AI agent MUST consult and strictly replicate the blueprints, configurations, and test designs provided in `docs/examples/`:

- **Backend Blueprints (`docs/examples/fastapi/`):**
  - Unit & mocking standards (`pytest`, `pytest-cov`, `pytest-mock` in `fastapi/tests/**/*.unit.py` with `>= 95%` coverage).
  - API black-box behavioral scenarios (`Karate Labs` `.feature` in `docs/examples/fastapi/test/api_test.feature`).
  - SAST & complexity auditing (`bandit`, `radon`, `mypy --strict`, `ruff`).
  - Contract & Fuzzing testing (`schemathesis`, `OWASP ZAP` baseline).
  - Chaos engineering & Prometheus observability (`Pumba`, `Locust`, `prometheus_fastapi_instrumentator`).
- **Frontend Blueprints (`docs/examples/vue3/`):**
  - Isolated unit tests (`Vitest` + `jsdom` in `vue3/src/**/*.unit.ts` with `>= 95%` coverage).
  - UI Business Flow BDD (`Karate Labs` in `docs/examples/vue3/test/ui_business_flow.feature`).
  - E2E & Accessibility (`Playwright` + `@axe-core/playwright` in `docs/examples/vue3/e2e/accessibility.spec.ts`).
  - Cognitive complexity and static security (`eslint-plugin-sonarjs`, `eslint-plugin-security`).
  - Frontend mutation testing (`Stryker` preconfigured in `stryker.conf.json.example`).

### 1.1 Complete Multi-Layer Test Pyramid

| Test Layer | Location | Blueprint Reference | Requirement |
| :--- | :--- | :--- | :--- |
| **1. Backend Unit** | `fastapi/tests/**/*.unit.py` | `docs/examples/fastapi/README.md` | Coverage `>= 95%` (`pytest-cov`). Test nominal, edge, and error branches. |
| **2. Frontend Unit** | `vue3/src/**/*.unit.ts` | `docs/examples/vue3/README.md` | 100% pass rate in Vitest. Test composables, Pinia stores, and form validation. |
| **3. Real DB & Migration** | `fastapi/migrations/versions/` | `docs/specs/02` & `alembic` | **Anti-Mock Invariant:** Never validate ORM changes (`src/models/`) with `AsyncMock` alone. Generate an Alembic migration and verify actual column types (`\d <table>`) and RLS in real PostgreSQL. |
| **4. Front-Back Contracts** | `fastapi/scripts/validar_comunicacion_front_back.py` | `docs/08` | Run inside Docker `rosgrid_api_local`. Send the exact payload (multipart form or JSON) used by the UI and verify DB persistence. |
| **5. Karate Labs API BDD** | `fastapi/test/api_test.feature` | `docs/examples/fastapi/test/api_test.feature` | **MANDATORY FOR ALL API CHANGES:** Black-box Gherkin scenarios testing 401 unauth, 422 malformed payloads, and 200/201 success contracts. Always include. |
| **6. Karate Labs UI BDD** | `vue3/test/ui_business_flow.feature` | `docs/examples/vue3/test/ui_business_flow.feature` | **MANDATORY FOR ALL UI CHANGES:** Real browser acceptance scenarios with Chrome CDP (button clicks, modal flows, navigation, critical links). Always include. |
| **7. Visual Geometry** | DOM Hierarchy & Viewport Layout | `docs/examples/vue3/e2e/` | **Anti-JSDOM Blindness:** JSDOM does not render Flexbox/Grid boxes. Test DOM order and inspect viewports in real browser sessions to ensure modals and sticky footers never overlap content. |
| **8. Trimodal Fixtures & Fleet Smoke** | `fastapi/tests/fixtures/mikrotik/` & `scripts/validar-flota-real.py` | [ground_truth_fixtures_and_negative_invariants.md](file:///.agents/rules/ground_truth_fixtures_and_negative_invariants.md) | **Universal Ground-Truth Invariant:** All RouterOS integrations MUST validate against 3 raw JSON fixtures (Factory Default asserting negative, Nominal asserting active, Degraded asserting graceful handling). Real-fleet smoke test (`make smoke-fleet`) mandatory against lab routers (`r1-r6`). |

### 1.2 Mandatory Inclusion of Karate Labs Scenarios for All Changes

**ZERO EXCEPTIONS INVARIANT:** Every single task or turn that adds, modifies, or fixes code MUST include Karate Labs scenarios:
1. **API Changes (Endpoints, Schemas, Logic):** MUST add or update black-box BDD scenarios in `fastapi/test/api_test.feature` AND mirror them identically in `docs/examples/fastapi/test/api_test.feature`.
2. **Frontend Changes (Views, Modals, Buttons, Links, Tables):** MUST add or update interactive BDD scenarios in `vue3/test/ui_business_flow.feature` AND mirror them identically in `docs/examples/vue3/test/ui_business_flow.feature`.
3. An AI agent or developer MUST NEVER consider a task completed without verifying that both Karate Labs feature files have been updated with scenarios covering the newly introduced functionality.

### 1.3 Invariante de Cero Componentes Vue Huérfanos (Zero-Orphan Vue Component Invariant)

Every `.vue` file located in `vue3/src/` (views, components, modals, widgets) **MUST** possess a co-located `.unit.ts` unit test suite.
- Zero orphaned components permitted: 100% of `.vue` components must be tested for mounting, empty/loading/error states, reactivity, and user interaction.
- Vitest pass rate must strictly remain 100% across all suites.
- Type integrity verified via `vue-tsc --noEmit` with 0 type errors.

### 1.4 Invariante de Telemetría Auto-Sincronizada e Inferencia BSD (Zero-Blindness Telemetry Invariant)

When interacting with RouterOS v7 telemetry or Syslog:
- The system must verify and auto-provision all 9 canonical logging topics (`system,info`, `account`, `firewall,info`, etc.) to prevent administrative changes in WinBox/WebFig from going undetected.
- The UDP Syslog collector must parse legacy BSD datagrams, strip duplicate identities, and dynamically infer topics if missing in the payload body.

### 1.5 Anti-Silo Cross-Module State Propagation, 3-Phase Temporal Lifecycle & Semantic Audit Invariant

High code coverage (`>= 95%`) alone does NOT prevent cross-module disconnects if unit tests rely on isolated mocks at module boundaries (*Silo Mock Blindness*) or tautological assertions. Every test suite across Backend (`pytest`) and Frontend (`Vitest` / `Playwright` / `Karate Labs`) MUST strictly enforce the following three invariants:

1. **Cross-Module State Propagation Invariant (Zero Boundary Mocks for State Consumers):**
   - Never consider a mutation test complete by asserting only the mutating endpoint's `HTTP 200/201` response while mocking or ignoring downstream consumers.
   - Whenever an action in Module A modifies operational state (e.g., creating/cancelling a `MaintenanceWindow`, updating a router's `system/identity`, triggering a 60s `Safe Mode` window, or pairing an FTTH subscriber in IPAM), the test MUST immediately invoke the read endpoints and UI stores of Module B (`GET /api/v1/inventory/routers`, `DashboardHomeView`, `NocWallboardView`, `UnifiedNetworkMap`, `GET /api/v1/audit/logs`) **without intermediate mocks** and assert that the effective state (`admin_state`, counters, badges, map pins) reflects the mutation across all views.
2. **3-Phase Temporal Lifecycle Invariant:**
   - Any entity governed by time windows or TTLs (`starts_at` / `ends_at` in Maintenance Windows, 60s Safe Mode `/system/scheduler`, 30s Vault Step-Up Auth, DHCP Lease expiration) MUST be tested across all **three temporal phases**:
     - **Phase 1 (`t < starts_at`):** Scheduled / Pending state (`⏳ Programada`).
     - **Phase 2 (`starts_at <= t <= ends_at`):** Active / In-Progress state (`🛠️ En Curso`, projecting effective `admin_state = MAINTENANCE` to all consumers).
     - **Phase 3 (`t > ends_at` or Cancelled):** Expired / Purged / Rolled-back state (restoring nominal `PRODUCTION` state and writing WORM audit trail).
3. **Anti-Raw-UUID & Semantic Badge Audit Invariant:**
   - Do NOT blindly replace `write_audit_log` with an uninspected `AsyncMock` in endpoint tests. Tests MUST verify that `actor_username` and `router_display_name` resolve to human-readable identifiers (never raw UUID v4 strings like `claims["sub"]`) and that UI event tickers (`NocWallboardView.vue`, `DashboardHomeView.vue`) classify event badges (`CAÍDA`, `MANTENIMIENTO`, `RESPALDO`, `OPERATIVO`, `OPERACIÓN`) by their true semantic action rather than falling back to a single misleading default label.

---

## 2. Mandatory Test Execution Upon Task Completion

It is **STRICTLY MANDATORY** to execute all relevant tests in ephemeral Docker containers (`Rule Zero`) before finishing any task that touches code:

```bash
# Backend unit tests & coverage (>= 95%)
docker compose -f docker-compose.qa.yml run --rm qa-backend uv run pytest tests/ --cov=src --cov-fail-under=95

# Frontend unit tests & type check (100% pass, 0 type errors)
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run test:unit
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run type-check

# Linters & Static Analysis
docker compose -f docker-compose.qa.yml run --rm qa-backend uv run ruff check .
docker compose -f docker-compose.qa.yml run --rm qa-backend uv run mypy src/ --strict
docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run lint
```

Never conclude a task if any test fails, coverage drops below 95%, or linters report errors.

---

## 3. Autonomous & Mandatory Documentation Sync

Whenever code is added, updated, or refactored, the AI agent **MUST OBLIGATORILY** update all corresponding documentation files simultaneously:

1. **`docs/` Directory:**
   - Update operational manuals (`docs/01` through `docs/05`, `docs/12`).
   - Update complete REST/WebSockets reference in `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` whenever endpoints, query params, or schemas change.
   - Update AI integration guides (`docs/07`) when MCP tools change.
2. **`docs/specs/` Directory:**
   - Update all affected domain and functional specifications (`docs/specs/01` through `docs/specs/51`).
3. **Monorepo Root:**
   - **`CHANGELOG.md` (Concise Release-Level Format):** Document user-facing changes under `## [Unreleased]` (`Added`, `Fixed`, `Changed`) in concise 1–2 line bullets. Never create duplicate version headers or dump verbose internal sub-milestone logs into `CHANGELOG.md`.
   - **`ROADMAP.md`:** Update milestone checkpoints, sub-task statuses, and deliverables.
   - **`TESTING.md`:** Update test metrics, coverage percentages, and scenario counts.
   - **`README.md` & Root Docs:** Update user-facing features, installation guidelines, architecture descriptions, or table of contents whenever applicable.
4. **`.agents/` Directory:**
   - Proactively update directives, skills, and automation scripts upon identifying improvement opportunities, unhandled edge cases, or automation potential (see [continuous_agent_evolution.md](file:///.agents/rules/continuous_agent_evolution.md)).
   - **Canonical Location Invariant for `ACTIVE_TASK.md`:** The agent task diary (`ACTIVE_TASK.md`) MUST reside strictly and exclusively within `.agents/ACTIVE_TASK.md`. Creating, moving, or committing `ACTIVE_TASK.md` in the project root directory is strictly prohibited across all workspaces.

---

## 4. Pre-Commit Verification Gate

Before concluding any task and proceeding to Git publication:
```bash
./scripts/verificar-secretos.sh
./.agents/scripts/certify_task_completion.sh
```
Verify zero secret leaks, zero type errors, clean git tree, and all Docker containers healthy.
