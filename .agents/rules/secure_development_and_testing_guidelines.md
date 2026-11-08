# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory Directive: Security-by-Design & Multi-Layer Testing (QA 11X)

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers modifying or extending RoSGrid. No task is complete if any requirement here is unmet.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Multi-Layer Testing & Anti-Mock Blindness

Unit isolation with mocks measures quick logical coverage but creates blind spots if disconnected from real infrastructure:

1. **ORM vs PostgreSQL Schema & JSONB Serialization Invariant:**
   - **Zero Schema Drift:** Modifying `src/models/*.py` or column types never alters the database automatically.
   - **Mandatory Alembic Migration:** Any new model, table, constraint (`UniqueConstraint`), or column type change requires an immediate versioned migration in `fastapi/migrations/versions/`.
   - **Real PostgreSQL Verification:** Always verify tables, column types, and indices via `\d <table>` in real PostgreSQL (`rosgrid_db_local`). Never assume `AsyncMock` passing guarantees SQL execution.
   - **Strict JSONB & `Decimal` Serialization in `MockDbSession` and Audit Mocks (Spec 105):** PostgreSQL `NUMERIC(p, s)` columns hydrate as `decimal.Decimal` in SQLAlchemy, and `JSONB` columns (`AuditLog.before_state`, `AuditLog.after_state`) execute strict `json.dumps(val)` (without `default=str`) on `flush`/`commit`. Every `MockDbSession.commit()` and `make_asserting_audit_mock` MUST execute `json.dumps()` on `JSONB` fields, and test fixtures for `Numeric` columns MUST use `Decimal("...")` to prevent `TypeError: Object of type Decimal is not JSON serializable` from escaping unit tests.

2. **3-Layer Endpoint & Component Verification Pyramid:**
   - **Layer 1: Isolated Unit Tests:**
     - Backend: `fastapi/tests/**/*.unit.py` (Pytest, coverage `>= 95%`).
     - Frontend: `vue3/src/**/*.unit.ts` (Vitest, composables and component logic).
   - **Layer 2: Real Front-Back Integration Contracts:**
     - Update and run `fastapi/scripts/validar_comunicacion_front_back.py` inside Docker `rosgrid_api_local`. Send the exact payload (multipart form or JSON) used by the UI and verify DB persistence.
   - **Layer 3: Black-Box Acceptance BDD (Karate Labs):**
     - Backend: Scenarios in `fastapi/test/api_test.feature` & `docs/examples/` verifying 401 unauth, 422 malformed, and 200/201 success contracts.
     - Frontend: Scenarios in `vue3/test/ui_business_flow.feature` & `docs/examples/` testing interactive UI, modals, and navigation.

3. **Anti-JSDOM Geometry Blindness:**
   - JSDOM does NOT calculate CSS Flexbox/Grid layouts, element coordinates, or viewport bounding boxes.
   - Prevent overlapping elements (e.g. login footer collapsing over form cards or uncentered modals) by asserting DOM hierarchy in unit tests and inspecting real browser viewport visibility/clickability in Karate UI or Playwright.

4. **Trimodal Ground-Truth Fixtures & Negative Invariants:**
   - Synthetic mocks that assume ideal network responses create critical blind spots (e.g. factory routers reporting active sensors).
   - In accordance with [ground_truth_fixtures_and_negative_invariants.md](file:///.agents/rules/ground_truth_fixtures_and_negative_invariants.md), every integration with RouterOS v7 must test:
     1. **Fixture A (Factory Default):** Must assert negative states (`active=False`, `items=[]`, `score=LOW`).
     2. **Fixture B (Nominal RoSGrid):** Must assert nominal active operation.
     3. **Fixture C (Disabled/Degraded):** Must assert graceful error handling without 500 crashes.
   - Real-fleet smoke testing (`scripts/validar-flota-real.py`) mandatory against running lab equipment (`r1-r6`).

---

## 2. Security-by-Design & OWASP Guidelines

Apply these non-negotiable security directives before writing any code:

1. **Multi-Tenant Isolation & Row Level Security (RLS):**
   - Every tenant table MUST include `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`.
   - Alembic migrations MUST execute:
     `ENABLE ROW LEVEL SECURITY;` and `FORCE ROW LEVEL SECURITY;`
     along with isolation policy: `USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)`.
   - Backend DB sessions MUST use `get_tenant_db_session` to ensure `app.current_tenant_id` is set.

2. **Strict SSRF Prevention:**
   - Any user-supplied or CSV-imported host/IP/URL (`api_base_url`, webhooks, syslog targets) MUST pass through `validate_router_target_url`.
   - Strictly reject: `127.0.0.0/8`, `::1`, `localhost`, link-local, cloud metadata (`169.254.0.0/16`, `fe80::/10`), and internal Docker container hostnames (`rosgrid-db`, `rosgrid-redis`, `rosgrid-api`, `rosgrid-worker`).

3. **Zero Plaintext Secrets & Vault Cryptography:**
   - Router passwords are NEVER stored in plaintext. Encrypt with AES-256-GCM using tenant-bound AAD (`f"{tenant_id}:{router_id}"`).
   - User passwords must use Argon2id. TOTP secret keys must be encrypted symmetrically.
   - Router password decryption is restricted to `SUPERADMIN_GLOBAL` and `TENANT_ADMIN` via TOTP Step-Up Auth with 30s ephemeral in-memory TTL.

4. **Idempotency for Mutating Operations:**
   - All critical `POST`, `PUT`, `DELETE` operations (router creation, CSV onboarding, config mutations, Maker-Checker approvals) MUST require an `Idempotency-Key` (UUIDv7) header, processed via KeyDB/Redis idempotency manager.

5. **CSRF & Hardened Session Cookies:**
   - Session cookies: `__Host-rg_at` and `__Host-rg_rt` with `HttpOnly; Secure; SameSite=Strict; Path=/`.
   - All browser mutation requests require `X-CSRF-Token` HMAC-SHA256 signature verification.

6. **Anti-Regression & Real Network Environment Invariant:**
   - See [anti_regression_and_side_effects_guardrail.md](file:///.agents/rules/anti_regression_and_side_effects_guardrail.md).
   - Inbound network traffic handlers (Syslog, SNMP, WebSockets) must tolerate Docker NAT proxying (`172.18.0.1`) and never rely on raw `addr[0]` alone.
   - Frontend stores must never destroy previously populated in-memory state on network catch blocks.

7. **SuperAdmin Tenant Fast-Switching, Atomic Session Re-keying & Pub/Sub Suppression:**
   - Dynamic context switching via `POST /api/v1/auth/switch-tenant` is strictly restricted to `SUPERADMIN_GLOBAL`.
   - Any request from lower roles (`TENANT_ADMIN`, `OPERATOR`, `FIELD_TECH`) must fail-closed with HTTP `403 Forbidden`.
   - Re-keying of active session in KeyDB must occur atomically, updating tenant claims in JWT without dropping the authenticated user identity, followed by an immediate WORM audit record `SUPERADMIN_TENANT_SWITCHED`.
   - **Pub/Sub Suppression (`notify_ws=False`):** Calling `kill_session` on the old tenant context MUST suppress websocket publication to avoid kicking out the active browser session (`forceKillSwitchLogout`). The frontend store MUST ignore `SUPERADMIN_TENANT_SWITCH` and seamlessly reconnect WebSockets upon `rosgrid:tenant-switched`.

8. **Feature Flags Governance, DAG Hard Lock, Granular User Profile Flags & Contingency Mode:**
   - In B2B multi-tenancy, tenant feature flags represent commercial licensing entitlements. Endpoints `PATCH` and `PUT` `/features` are strictly restricted to `SUPERADMIN_GLOBAL` (fail-closed HTTP 403 to local tenant admins).
   - **Active DAG (Hard Lock):** Dependent flags (e.g. `bgp_looking_glass_enabled`, `sla_tracker_enabled`) MUST be locked (`disabled`) with visual badge and tooltip when the parent module (`isp_module_enabled`) is off, and forced off in cascade.
   - **Granular User Profile Flags (Spec 55 — 4-Tier Resolution):** Every platform capability and submodule MUST have a corresponding toggle flag across the 30-action `POLICY_MATRIX`, 10 router-scoped flags in `UserRouterPermission`, and per-user overrides (`users.feature_flags_override`), evaluated deterministically (`Tenant Flag` -> `User Override` -> `Role Matrix` -> `Router Permission`).
   - **Privacy-Preserving Telemetry Beacon & Dual Prometheus Observability (Spec 55):** Anonymous active-instance heartbeats to `rosgrid-web` MUST be strictly Zero-PII (`HMAC-SHA256` `instance_id`), fail-silent in air-gapped networks, and respect `ROSGRID_TELEMETRY_BEACON_ENABLED`. Prometheus documentation and endpoints MUST clearly distinguish platform metrics (`GET /metrics` via FastAPI Instrumentator) from MikroTik fleet metrics (`GET /api/v1/metrics/fleet`). Fleet metrics MUST serve the 8 canonical OpenMetrics gauges/counters (`rosgrid_router_status`, `rosgrid_router_cpu_percent`, `rosgrid_router_memory_usage_ratio`, `rosgrid_router_uptime_seconds`, `rosgrid_router_temperature_celsius`, `rosgrid_router_voltage_volts`, `rosgrid_router_active_cves_count`, `rosgrid_router_syslog_critical_events_total`) from KeyDB in microseconds without querying PostgreSQL or invoking live HTTP on routers, strictly filter by `Tenant.prometheus_fleet_exporter_enabled`, include `{tenant_id, router_id, identity, model, ros_version}` labels, maintain Radon `CC <= 5`, and provide official Grafana dashboard JSON and Alertmanager rules in `docs/examples/`.
   - **Contingency Mode NOC in 1-Click:** Provide a low-power preset that immediately suspends heavy telemetry collectors (Syslog, IPFIX, Prometheus, SFP, Drift, SD-WAN) during network congestion while preserving the core router control and governance.
   - UI mutators modifying critical governance flags MUST enforce a Blast Radius confirmation shield calculating dynamic impact on fleet and active operators.

9. **Visual Geometry & In-Flow Ergonomics (Anti-Sticky Footer):**
   - JSDOM does not calculate layout or bounding boxes. Ensure real browser validation for viewport ergonomics.
   - Prohibit fixed floating bottom footers (`position: fixed` or rigid bottom flex containers) that permanently steal vertical pixels.
   - All copyright and legal footers must be placed in-flow inside `<main>` with `margin-top: auto`, reserving 100% of vertical height for dashboards, inventory tables, and network maps.

10. **Critical Execution Gate & Explicit User Authorization:**
    - AI agents MUST NEVER create, edit, or delete code files (in `fastapi/`, `vue3/`, scripts, or migrations) based on IDE timeouts, artifact review notifications, or automatic system 'Auto-proceed' events.
    - All code modifications are strictly prohibited while in the planning phase. The agent must pause and wait until the user explicitly commands to proceed in the chat (e.g. 'procede', 'ejecuta el plan', 'adelante con el código').

11. **Operational Separation: Local Test Environment (`local-test`) vs. Official Production Release (`scripts/build.sh`):**
    - **Local Testing Environment:** When testing production images locally (`docker-compose.prod.local.yml`), AI agents MUST build the local test images:
      ```bash
      docker build -f fastapi/Dockerfile -t sinfallas/rosgrid-backend:local-test fastapi
      docker build -f vue3/Dockerfile -t sinfallas/rosgrid-frontend:local-test vue3
      docker compose -f docker-compose.prod.local.yml up -d --force-recreate rosgrid-api rosgrid-ui
      ```
    - **NEVER execute `./scripts/build.sh` for intermediate local testing.** `scripts/build.sh` is reserved strictly for official milestone releases (Milestone 27) that publish `:latest` and `:1.0.0` tags to remote Docker Hub and trigger `docker builder prune -af`. Mixing these environments confuses workflows and burns unnecessary network and CPU resources.

12. **Privacy-Preserving Telemetry Beacon & Dual Observability (Spec 55):**
    - **Zero-PII Invariant:** Heartbeat payloads (`fastapi/src/workers/telemetry_beacon_worker.py`) must never transmit tenant names, router IPs, credentials, or sensitive topology. `instance_id` must be irreversibly hashed via `HMAC-SHA256`.
    - **Fail-Silent & Air-Gapped Resilient:** All outbound requests to `https://rosgrid.net/api/telemetry/heartbeat` must catch network exceptions and timeout within 5.0s without blocking or crashing the application.
    - **Pytest Lifespan Guard:** Never initiate an infinite worker loop during testing (`ROSGRID_ENV.startswith("qa") or ROSGRID_ENV == "test"`).
    - **Dual Observability:** Maintain `GET /metrics` strictly for FastAPI platform telemetry and `GET /api/v1/metrics/fleet` strictly for MikroTik fleet metrics served from KeyDB in RAM.

13. **Idempotency Key Anti-Replay in Test Suites, AsyncSession MissingGreenlet Prevention & Status 422:**
    - **Test Suite Idempotency Isolation:** When writing Pytest suites that execute sequential mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) within the same test function (e.g. testing duplicate detections or port collisions), NEVER reuse the exact same headers dictionary containing a static `Idempotency-Key`. The idempotency middleware will intercept subsequent calls with `HTTP 422 ("Conflicto de Idempotency-Key")`. Always generate a fresh UUID (`"Idempotency-Key": str(uuid.uuid4())`) per distinct mutation.
    - **AsyncSession MissingGreenlet Invariant:** In async SQLAlchemy sessions (`AsyncSession`), accessing lazy-loaded relationships or model properties calling relationship attributes triggers `MissingGreenlet`. Never invoke `ChildResponse.model_validate(orm_obj)` if child relationships are not explicitly loaded via `selectinload()`. Always serialize via `BaseResponse.model_validate(orm_obj).model_dump()` or access attributes defensively via `self.__dict__.get("rel_attr")`.
    - **Modern FastAPI HTTP Status Constants:** In FastAPI/Starlette, prefer `status.HTTP_422_UNPROCESSABLE_CONTENT` over deprecated `HTTP_422_UNPROCESSABLE_ENTITY` to avoid deprecation warnings.

14. **RBAC UI Visibility & Read Roles Parity Invariant (Zero 403 Dead-Ends — Spec 64):**
    - **Defensive Role Resolution in Pinia:** In `useAuthStore.ts`, always evaluate `currentRole.value || user.value?.role` so permission checks in `canUseUserFeature` remain fully functional regardless of whether the store was initialized with `setAuth()` or direct `user` object assignment.
    - **Read Roles Backend Parity:** All endpoints with role-based read restrictions (`_READ_ROLES`) MUST maintain strict parity with `POLICY_MATRIX` (including `SUPPORT_L1`, `FIELD_TECH` and `AUDITOR` where read operations are permitted).
    - **Proactive Navigation & Control Guarding:** UI components and navigation shells MUST evaluate `canUseUserFeature(actionKey)` with `v-if` to conceal unauthorized views, tabs, and mutation controls before unauthorized API calls trigger HTTP 403 errors.
    - **Defensive Asynchronous Collection Access:** Nested view components (such as `FleetCveMatrix.vue`) MUST use optional chaining (`cveSummary.value?.vulnerable_routers?.length`) and safe fallbacks to prevent `TypeError: Cannot read properties of undefined` during initial render cycles before API responses resolve.

15. **DISA ASD STIG V6R5 (XCCDF) & OWASP Developer Guide v4.2.0 Compliance Hardening (Spec 68):**
    - **Account Lockout (`V-222432` CAT I / OWASP 4.3.7 A-15):** Enforce lockout after `ROSGRID_MAX_LOGIN_ATTEMPTS = 3` consecutive failed logon attempts within a 15-minute window (`ROSGRID_LOGIN_LOCKOUT_SECONDS = 900`).
    - **Password Policy & No-Reuse (`V-222536..V-222545` CAT I/II / OWASP 4.3.7 P-4, SM-8):** Enforce 15-character minimum password length on Bootstrap/STIG profiles (`V-222536`), complexity (`validate_stig_password_complexity`), prohibit reusing the current password on `/users/change-password` (`V-222545`), update `password_changed_at` (`V-222543`), and revoke active sessions upon administrative password change (`OWASP 4.3.7 SM-8`).
    - **Constant-Time Anti-Enumeration (`OWASP 4.3.7 A-20` / `V-222551`):** Always execute `verify_dummy_password(password)` against a precomputed Argon2id hash when a username/email is not found during login so valid vs. invalid accounts exhibit indistinguishable response times.
    - **Role-Based Session Idle Timeouts (`V-222389`, `V-222390` / OWASP 4.3.7 SM-7):** Enforce 10-minute (`600s`) idle timeout for privileged roles (`SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`) and 15-minute (`900s`) idle timeout for non-privileged operator roles (`get_role_idle_timeout_seconds`).
    - **Session Lifecycle WORM Auditing, `Clear-Site-Data` & Log Injection Sanitization (`V-222441..V-222444`, `V-222388`, `V-222392`, `V-222437` / OWASP 4.3.10 SL-4):** Generate WORM audit records on login (`LOGIN_SUCCESSFUL` with `previous_login_at`/`previous_login_ip`), token rotation (`SESSION_TOKEN_RENEWED`), and logout (`USER_LOGOUT` with `Clear-Site-Data: "cache", "cookies", "storage"`), and sanitize all audit strings via `sanitize_log_string()` to strip CRLF/control characters.
    - **OWASP OSHP Headers & CycloneDX SBOM (`V-222658` / OWASP 5.3.4 & 5.4.4):** Emit `X-Permitted-Cross-Domain-Policies: none` and `Cross-Origin-Opener-Policy: same-origin` in `SecurityHeadersMiddleware`, and generate CycloneDX SBOMs in ephemeral Docker (`scripts/generar-sbom-cyclonedx.sh`).

16. **Container Ephemeral Coverage & Test Isolation Invariant (Rule Zero):**
    - **Coverage File Redirection:** When executing `pytest` inside ephemeral Docker containers mounted read-only (`:ro`) or running with non-root service accounts (`rosgrid`), always redirect coverage output using `-e COVERAGE_FILE=/tmp/.coverage` and `-w /tmp`. This eliminates `PermissionError: [Errno 13] Permission denied: '/app/.coverage'`.
    - **Python Module Dot-Notation for Coverage:** Always declare coverage targets as Python modules (`--cov=src.services.diagnostics_and_siem`) rather than filesystem paths (`--cov=/app/src/...`) when `PYTHONPATH=/app/src`.
    - **Root-Owned Residue Cleanup Fallback:** Clean any container-generated residue files with Docker container fallback (via `scripts/limpieza.sh` or MCP `clean_workspace_11x`) to prevent host-level `Permission denied` errors.

---

## 3. Pre-Commit 11X Checklist

Before declaring a task done or creating a commit/PR:
- [ ] New/modified ORM models? -> Alembic migration applied and verified in PostgreSQL (`\d <table>`).
- [ ] Ports preserved in Docker Compose? (e.g. standard UDP 514/5514 for Syslog, HTTP 8000, WebFig 8085).
- [ ] Zero missing imports verified via static analysis (`ruff check src/`, `vue-tsc --noEmit`)?
- [ ] Endpoints verified with real payloads using `validar_comunicacion_front_back.py`?
- [ ] Added scenarios in Karate Labs API (`api_test.feature`) and Karate Labs UI (`ui_business_flow.feature`)?
- [ ] Executed `./scripts/verificar-secretos.sh` and ShellCheck clean?
- [ ] Synchronized `docs/specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, and `TESTING.md`?
