# Domain-Specific Governance Rules (rosgrid)

# SPDX-License-Identifier: GPL-3.0-only

# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)


# Terminal ↔ Frontend Parity & UI Invariants

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers working on RoSGrid.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---


# SPDX-License-Identifier: GPL-3.0-only

# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)


## 1. The Mock Blindness Anti-Pattern

Synthetic unit test mocks created ad-hoc by developers invariably introduce **Mock Blindness**:
- The test writer models only the happy path based on idealized assumptions.
- Factory-default states, inert firmware configurations, missing hardware chips, and unconfigured menus return unexpected payloads in real life (e.g. `remote="0.0.0.0"`, empty lists `[]`, or HTTP 404/400).
- Synthetically passing tests give false confidence while the real frontend reports false positives on unconfigured lab or production equipment.

---


## 3. Subsystem Coverage Catalog (The 8 Protected Domains)

The trimodal fixture standard and negative invariant validation MUST be enforced across all 8 domains:

1. **Syslog Telemetry (`/system/logging`, `/system/logging/action`):**
   - Factory default has action `remote` with `0.0.0.0`. Strict signature requires action `rosgridsyslog` with valid remote IP and active rule.
2. **CIS Benchmark / Hardening (`/ip/service`, `/user`, `/ip/dns`, `/ip/neighbor/discovery-settings`):**
   - Factory default has Telnet/FTP active, admin without password, remote DNS open, L2 discovery on all interfaces. Security score MUST be low (< 35). RoSGrid hardened profile MUST score >= 90.
3. **L2 Topology & Neighbors (`/ip/neighbor`, MNDP/LLDP):**
   - Factory default or isolated router returns empty list or third-party devices. Topology engine MUST NOT hallucinate links or crash on foreign MACs.
4. **IPAM, DHCP Pools & Leases (`/ip/pool`, `/ip/dhcp-server`, `/ip/dhcp-server/lease`):**
   - Factory default may have default subnet `192.168.88.0/24` or disabled pool. Sync engine must isolate tenant ranges and distinguish active leases from reserved pools.
5. **PoE Orchestrator (`/interface/ethernet/poe`):**
   - CHR or non-PoE hardware returns 404 or empty. System MUST report `NO_POE_CAPABLE` instead of "all ports down".
6. **Rogue DHCP & DHCP Snooping (`/interface/bridge`, `/interface/bridge/port`):**
   - Factory default has `dhcp-snooping=no`. System MUST NOT emit rogue DHCP alerts when snooping is inactive.
7. **CAPsMAN & Wi-Fi 6 (`/interface/wifi` or `/caps-man`):**
   - Core routers (CCR2004, RB5009) lack wireless chips. Must report `NO_WIRELESS_INTERFACES` without failing health monitor.
8. **Config Drift Detection (`/export` vs Golden Baseline):**
   - Factory default compared to Golden Template MUST report 100% drift with explicit diff, never "in-sync".

---


## 4. Real-Fleet Smoke Test Enforcement (`make smoke-fleet`)

Unit tests with fixtures are necessary but insufficient alone. Before concluding any milestone:
1. The real-fleet smoke test script (`scripts/validar-flota-real.py`) MUST execute against the running Docker stack with live lab routers (`r1` to `r6`):
   - Configured lab routers (`r1, r2, r3`): Positively assert all enabled features.
   - Factory lab routers (`r4, r5, r6`): Negatively assert all unconfigured features.
2. **Fail-Closed Rule:** If any factory router (`r4, r5, r6`) returns a false positive for any configured service, test suite aborts with exit code 1. Git commit and push are strictly blocked.


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
- Verify and auto-provision all 10 canonical logging topics (`system,info`, `account`, `firewall,info`, `pppoe,ppp,info,warning,error`, etc.) to prevent administrative changes in WinBox/WebFig from going undetected.
- Parse legacy BSD datagrams cleanly in the UDP Syslog collector (`514`/`5514`), stripping duplicate identities and dynamically inferring topics when missing.


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


# SPDX-License-Identifier: GPL-3.0-only

# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)


# Mandatory Directive: Security-by-Design, Anti-Regression & Multi-Layer Testing (QA 11X)

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers modifying or extending RoSGrid. No task is complete if any requirement here is unmet.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---


## 1. Multi-Layer Testing, Anti-Mock Blindness & Blast-Radius Governance

1. **ORM vs PostgreSQL Schema & JSONB Serialization Invariant:**
   - **Zero Schema Drift & Mandatory Alembic Migration:** Any new model, table, constraint, or column type change in `src/models/*.py` requires an immediate versioned migration in `fastapi/migrations/versions/`, verified via `.agents/scripts/verify_alembic_orm_parity.py` and `\d <table>` in real PostgreSQL (`rosgrid_db_local`).
   - **Strict JSONB & `Decimal` Serialization (`MockDbSession` & Audit Mocks — Spec 105):** PostgreSQL `NUMERIC(p, s)` columns hydrate as `decimal.Decimal` in SQLAlchemy, and `JSONB` columns (`AuditLog.before_state`, `AuditLog.after_state`) execute strict `json.dumps(val)` (without `default=str`) on `flush`/`commit`. Every `MockDbSession.commit()` and `make_asserting_audit_mock` MUST execute `json.dumps()` on `JSONB` fields, and `sanitize_sensitive_data` converts `Decimal` $\rightarrow$ `float`.
   - **AsyncSession `MissingGreenlet` Prevention & Idempotency Anti-Replay:** In `AsyncSession`, accessing lazy-loaded relationships or model properties calling un-preloaded relationships triggers `MissingGreenlet`. Always serialize via base dicts or `self.__dict__.get("rel_attr")`, and generate a fresh `Idempotency-Key` (`str(uuid.uuid4())`) per distinct mutation in test suites. Prefer `status.HTTP_422_UNPROCESSABLE_CONTENT` over deprecated `HTTP_422_UNPROCESSABLE_ENTITY`.

2. **Anti-Regression & Blast-Radius Governance (CLI-First AST Invariant):**
   - Zero degradation of pre-existing functionality when introducing changes.
   - Before modifying shared modules, inspect incoming dependency edges via `.agents/scripts/inspect_blast_radius.py` and verify layer boundaries via `.agents/scripts/verify_topological_health.py`.
   - Shell-capable agents (Antigravity, Claude Code CLI) MUST execute AST queries directly via CLI scripts (`inspect_blast_radius.py`) and never spawn background Docker MCP daemons occupying host ports.
   - Preserve canonical Docker Compose ports (UDP `514`/`5514` for Syslog, HTTP `8000`, WebFig `8085`), tolerate Docker NAT/bridge proxy addresses (`172.18.0.1`) via payload/identity fallback, and never clear frontend stores (`setRouters([])`) inside generic network catch blocks.

3. **Visual Geometry & In-Flow Ergonomics (Anti-Sticky Footer):**
   - JSDOM does NOT calculate CSS Flexbox/Grid layouts or bounding boxes. Validate DOM hierarchy in unit tests and inspect real browser viewports.
   - Prohibit fixed floating bottom footers that steal vertical pixels; place footers in-flow inside `<main>` (`margin-top: auto`).

---


## 2. Security-by-Design, Zero-Trust MCP & OWASP / STIG Guidelines

1. **Multi-Tenant Isolation & Row Level Security (RLS):**
   - Every tenant table MUST include `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE` with `ENABLE ROW LEVEL SECURITY;` and `FORCE ROW LEVEL SECURITY;` (`USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)`), accessed via `get_tenant_db_session`.

2. **Strict SSRF Prevention (`validate_router_target_url`):**
   - Any user-supplied or CSV-imported host/IP/URL (`api_base_url`, webhooks, syslog targets, documentation URLs) MUST pass anti-SSRF validation, rejecting loopback, link-local, cloud metadata (`169.254.0.0/16`), and internal Docker container hostnames (`rosgrid-db`, `rosgrid-redis`, `rosgrid-api`, `rosgrid-worker`).

3. **Zero Plaintext Secrets, Vault Cryptography & Hardened Sessions:**
   - Router passwords are encrypted with `AES-256-GCM` using tenant-bound AAD (`f"{tenant_id}:{router_id}"`); decryption is restricted to `SUPERADMIN_GLOBAL` and `TENANT_ADMIN` via live 2FA Step-Up Auth (30s in-memory TTL).
   - User passwords use Argon2id. Session cookies (`__Host-rg_at`, `__Host-rg_rt`) enforce `HttpOnly; Secure; SameSite=Strict; Path=/` with HMAC-SHA256 `X-CSRF-Token` verification.

4. **Zero-Trust MCP Governance & Service-Layer RBAC Defense (Spec 113):**
   - **Exclusive `SERVICE_ACCOUNT` + Non-Empty CIDR:** `POST /api/v1/mcp` is restricted exclusively to `SystemRoleEnum.SERVICE_ACCOUNT` with a mandatory non-empty `allowed_cidr_list` (empty `[]` is rejected with HTTP 403).
   - **Maker-Checker Across All 6 Mutation Tools:** All 6 Level-3 MCP mutation tools (`rosgrid_reconnect_pppoe_client`, `rosgrid_propose_network_change`, `rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit`, `rosgrid_execute_poe_aware_upgrade`) MUST create an `ApprovalRequest` (`status: "AWAITING_APPROVAL"`, `safe_mode_timeout_seconds: 60`) and never modify the router directly until a human `Checker` approves the request.
   - **Service-Layer RBAC Enforcement (Anti-`Depends` Bypass):** FastAPI `Depends(require_roles(...))` only executes on HTTP router calls. Mutating service functions (`isolate_network_service`, `restore_network_service`, `change_network_service_rate_limit`, `_process_upgrade_stages`) MUST explicitly validate `claims["rol"]` in Python, and `NOC_MONITOR` must remain strictly read-only.

5. **SuperAdmin Tenant Fast-Switching & Pub/Sub Suppression:**
   - `POST /api/v1/auth/switch-tenant` is restricted to `SUPERADMIN_GLOBAL` (HTTP 403 for all other roles), atomically re-keys the KeyDB session with `notify_ws=False` (preventing false `forceKillSwitchLogout`), and writes a WORM audit log `SUPERADMIN_TENANT_SWITCHED`.

6. **Feature Flags Governance, Granular User Profile Flags, Opt-In Telemetry & Dual Prometheus (Specs 55 & 113):**
   - Tenant feature flags (`PATCH`/`PUT /features`, restricted to `SUPERADMIN_GLOBAL`) enforce DAG cascade locks, 1-click Contingency mode, and a Blast Radius confirmation shield.
   - Permissions resolve deterministically across 4 tiers: `Tenant Flag` $\rightarrow$ `User Override (users.feature_flags_override)` $\rightarrow$ `Role Policy Matrix (30×11)` $\rightarrow$ `Router Permissions (10 Flags)`.
   - **RBAC UI Visibility Parity (Zero 403 Dead-Ends — Spec 64):** `useAuthStore.ts` resolves `currentRole.value || user.value?.role` and hides restricted views/tabs (`v-if="canUseUserFeature(...)"`), while backend `_READ_ROLES` tuples maintain 100% parity with `POLICY_MATRIX`.
   - **Opt-In Telemetry Beacon & Dual Prometheus:** `ROSGRID_TELEMETRY_BEACON_ENABLED` defaults to `False` (`Opt-In`), is Zero-PII (`HMAC-SHA256`), fail-silent in air-gapped networks, and disabled during `pytest`/`qa` runs. Maintain `GET /metrics` for FastAPI platform telemetry and `GET /api/v1/metrics/fleet` for the 8 MikroTik fleet OpenMetrics gauges/counters served from KeyDB RAM.

7. **DISA ASD STIG V6R5 & OWASP Developer Guide v4.2.0 Compliance (Spec 68):**
   - Enforce lockout after 3 failed login attempts (`15m`), 15-character minimum password complexity without reuse, constant-time Argon2id dummy verification (`verify_dummy_password`), role-based idle timeouts (`10m` privileged / `15m` operator), WORM session lifecycle auditing with `sanitize_log_string()` and `Clear-Site-Data`, OWASP OSHP headers, `ConfigDict(extra="forbid")` on all request schemas, and live evaluation of all **28 CIS Benchmark directives** in `run_cis_audit`.

---


## 3. Operational Separation & Critical Execution Gate

1. **Local Test Images (`local-test`) vs. Official Release (`scripts/build.sh`):**
   - For local testing (`docker-compose.prod.local.yml`), build `sinfallas/rosgrid-backend:local-test` and `sinfallas/rosgrid-frontend:local-test`.
   - **NEVER run `./scripts/build.sh` for intermediate local testing**; `build.sh` is reserved strictly for official release publication to Docker Hub.
2. **Container Ephemeral Coverage Redirection (`Rule Zero`):**
   - When running coverage in read-only ephemeral containers, pass `-e COVERAGE_FILE=/tmp/.coverage` and module dot-notation (`--cov=src...`).
3. **Explicit User Authorization Gate:**
   - Never modify code based on IDE timeouts or automatic signals during planning; wait for explicit user approval.

