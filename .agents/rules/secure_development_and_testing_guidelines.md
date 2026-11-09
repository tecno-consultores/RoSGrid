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
