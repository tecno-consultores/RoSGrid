# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Mandatory QA Pyramid & Autonomous Documentation Sync Directive

> **SUPREME DIRECTIVE FOR AI AGENTS & CONTRIBUTORS:**
> Never conclude a task, suggest commits, or finish execution turns without proactively fulfilling the following three non-negotiable requirements whenever code is created or modified. Do not wait for user prompting.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Mandatory 11X Test Creation (Using `docs/examples/` as Blueprints)

Any modification, addition, or bugfix in source code (`fastapi/src/` or `vue3/src/`) MUST be accompanied by corresponding tests across the full 11X test pyramid, consulting the canonical blueprints in `docs/examples/fastapi/` and `docs/examples/vue3/`:

| Test Layer | Location | Blueprint Reference | Requirement |
| :--- | :--- | :--- | :--- |
| **1. Backend Unit** | `fastapi/tests/**/*.unit.py` | `docs/examples/fastapi/README.md` | Coverage `>= 95%` (`pytest-cov`). Test nominal, edge, and error branches. |
| **2. Frontend Unit** | `vue3/src/**/*.unit.ts` | `docs/examples/vue3/README.md` | 100% pass rate in Vitest. Test composables, Pinia stores, and form validation. |
| **3. Real DB & Migration** | `fastapi/migrations/versions/` | `docs/specs/02` & `alembic` | **Anti-Mock Invariant:** Never validate ORM changes (`src/models/`) with `AsyncMock` alone. Generate an Alembic migration and verify actual column types (`\d <table>`) and RLS in real PostgreSQL. |
| **4. Front-Back Contracts** | `fastapi/scripts/validar_comunicacion_front_back.py` | `docs/08` | Run inside Docker `rosgrid_api_local`. Send the exact payload used by the UI and verify DB persistence. |
| **5. Karate Labs API BDD** | `fastapi/test/api_test.feature` | `docs/examples/fastapi/test/api_test.feature` | **MANDATORY FOR ALL API CHANGES:** Black-box Gherkin scenarios testing 401 unauth, 422 malformed payloads, and 200/201 success contracts. |
| **6. Karate Labs UI BDD** | `vue3/test/ui_business_flow.feature` | `docs/examples/vue3/test/ui_business_flow.feature` | **MANDATORY FOR ALL UI CHANGES:** Real browser acceptance scenarios with Chrome CDP (button clicks, modal flows, navigation). |
| **7. Visual Geometry** | DOM Hierarchy & Viewport Layout | `docs/examples/vue3/e2e/` | **Anti-JSDOM Blindness:** JSDOM does not render Flexbox/Grid boxes. Test DOM order and inspect viewports in real browser sessions. |
| **8. Trimodal Fixtures & Fleet Smoke** | `fastapi/tests/fixtures/mikrotik/` & `scripts/validar-flota-real.py` | [ground_truth_fixtures_and_negative_invariants.md](ground_truth_fixtures_and_negative_invariants.md) | **Universal Ground-Truth Invariant:** All RouterOS integrations MUST validate against 3 raw JSON fixtures (Factory Default asserting negative, Nominal asserting active, Degraded asserting graceful handling). |

### 1.1 Zero-Orphan Vue Component Invariant

Every `.vue` file located in `vue3/src/` (views, components, modals, widgets) **MUST** possess a co-located or dedicated `.unit.ts` unit test suite verified by `.agents/scripts/verify_zero_orphan_vue_components.py`, maintaining 100% Vitest pass rate and 0 errors in `vue-tsc --noEmit`.

### 1.2 Zero-Blindness Telemetry Invariant

When interacting with RouterOS v7 telemetry or Syslog:
- Verify and auto-provision all 9 canonical logging topics (`system,info`, `account`, `firewall,info`, etc.) to prevent administrative changes in WinBox/WebFig from going undetected.
- Parse legacy BSD datagrams cleanly in the UDP Syslog collector (`514`/`5514`), stripping duplicate identities and dynamically inferring topics when missing.

### 1.3 Anti-Silo Cross-Module State Propagation, 3-Phase Temporal Lifecycle & Semantic Audit Invariant

1. **Cross-Module State Propagation (Zero Boundary Mocks for State Consumers):** Whenever an action in Module A modifies operational state (e.g., `MaintenanceWindow`, router `system/identity`, 60s `Safe Mode`, or FTTH IPAM pairing), tests MUST invoke the read endpoints and UI stores of Module B (`GET /api/v1/inventory/routers`, `DashboardHomeView`, `NocWallboardView`, `UnifiedNetworkMap`, `GET /api/v1/audit/logs`) **without intermediate mocks** and assert effective state propagation.
2. **3-Phase Temporal Lifecycle:** Any entity governed by time windows or TTLs (`starts_at` / `ends_at` in Maintenance Windows, 60s Safe Mode `/system/scheduler`, 30s Vault Step-Up Auth, DHCP Lease expiration) MUST be tested across all **three temporal phases**: Scheduled (`t < starts_at`), Active (`starts_at <= t <= ends_at`), and Expired/Cancelled (`t > ends_at`).
3. **Anti-Raw-UUID & Semantic Badge Audit Invariant:** Do NOT blindly replace `write_audit_log` with an uninspected `AsyncMock` in endpoint tests (enforced by `.agents/scripts/verify_anti_silo_test_quality.py`). Verify that `actor_username` and `router_display_name` resolve to human-readable identifiers (never raw UUID v4 strings).

---

## 2. Mandatory Ephemeral Docker Test Execution (`Rule Zero`)

Execute all tests and linters strictly inside ephemeral Docker containers (as defined in [`Makefile`](../../Makefile)) before concluding any code task:

```bash
# Backend unit tests & linters (Rule Zero)
docker run --rm --entrypoint uv -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_CACHE_DIR=/tmp/uv-cache -e PYTHONPATH=/app/src -v $(pwd)/fastapi:/app -v $(pwd):/workspace:ro -w /app sinfallas/rosgrid-backend:local-test run --with pytest --with pytest-asyncio --with pytest-cov pytest -o addopts="" -o cache_dir=/tmp/pytest-cache --import-mode=importlib tests/
docker run --rm --entrypoint ruff -v $(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test check --no-cache src/ tests/
docker run --rm --entrypoint uv -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_CACHE_DIR=/tmp/uv-cache -v $(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test run --with mypy mypy --cache-dir=/tmp/mypy src/

# Frontend unit tests & type check (Rule Zero)
docker run --rm -v $(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vitest run
docker run --rm -v $(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vue-tsc --noEmit
```

---

## 3. Autonomous & Mandatory Documentation Sync

Whenever code is added, updated, or refactored, update all corresponding documentation files simultaneously:

1. **`docs/` & `docs/specs/`:** Update affected operational manuals (`docs/01` through `docs/12`, `MANUAL_*.md`) and domain specifications (`docs/specs/`).
2. **`CHANGELOG.md` (Concise Release-Level Format):** Document user-facing changes under `## [Unreleased]` (`Added`, `Fixed`, `Changed`) in concise 1–2 line bullets. Never create duplicate version headers or dump verbose internal sub-milestone logs into `CHANGELOG.md`.
3. **`ROADMAP.md`, `TESTING.md` & `README.md`:** Sync milestone checkpoints, test counts, and root documentation.
4. **Canonical Location Invariant for `ACTIVE_TASK.md`:** The agent task diary MUST reside strictly at `.agents/ACTIVE_TASK.md` (never in the repository root) and include `- **Estado:** IN_PROGRESS (XX%)` or `COMPLETED (100%)`.
