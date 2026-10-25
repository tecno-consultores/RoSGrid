# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory Directive: Security-by-Design & Multi-Layer Testing (QA 11X)

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers modifying or extending RoSGrid. No task is complete if any requirement here is unmet.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Multi-Layer Testing & Anti-Mock Blindness

Unit isolation with mocks measures quick logical coverage but creates blind spots if disconnected from real infrastructure:

1. **ORM vs PostgreSQL Schema Invariant:**
   - **Zero Schema Drift:** Modifying `src/models/*.py` or column types never alters the database automatically.
   - **Mandatory Alembic Migration:** Any new model, table, constraint (`UniqueConstraint`), or column type change requires an immediate versioned migration in `fastapi/migrations/versions/`.
   - **Real PostgreSQL Verification:** Always verify tables, column types, and indices via `\d <table>` in real PostgreSQL (`rosgrid_db_local`). Never assume `AsyncMock` passing guarantees SQL execution.

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

7. **SuperAdmin Tenant Fast-Switching & Atomic Session Re-keying:**
   - Dynamic context switching via `POST /api/v1/auth/switch-tenant` is strictly restricted to `SUPERADMIN_GLOBAL`.
   - Any request from lower roles (`TENANT_ADMIN`, `OPERATOR`, `FIELD_TECH`) must fail-closed with HTTP `403 Forbidden`.
   - Re-keying of active session in KeyDB must occur atomically, updating tenant claims in JWT without dropping the authenticated user identity, followed by an immediate WORM audit record `SUPERADMIN_TENANT_SWITCHED`.

8. **Feature Flags Governance & Blast Radius Shield (Scoped by Tenant):**
   - In B2B multi-tenancy, feature flags are tenant-level capabilities and licensing attributes. They must be managed strictly from the Tenant administration context (`/tenants`), never from an orphan global sidebar.
   - UI mutators modifying critical governance flags (`syslog_collector_enabled`, `enforce_maker_checker`, `auto_safemode_enforced`) MUST enforce a Blast Radius confirmation shield calculating dynamic impact on fleet and active operators.
   - Flag dependencies must be validated via a Directed Acyclic Graph (DAG) preventing orphan dependent flags (e.g. BGP Looking Glass without ISP Core).

9. **Visual Geometry & In-Flow Ergonomics (Anti-Sticky Footer):**
   - JSDOM does not calculate layout or bounding boxes. Ensure real browser validation for viewport ergonomics.
   - Prohibit fixed floating bottom footers (`position: fixed` or rigid bottom flex containers) that permanently steal vertical pixels.
   - All copyright and legal footers must be placed in-flow inside `<main>` with `margin-top: auto`, reserving 100% of vertical height for dashboards, inventory tables, and network maps.

10. **Critical Execution Gate & Explicit User Authorization:**
    - AI agents MUST NEVER create, edit, or delete code files (in `fastapi/`, `vue3/`, scripts, or migrations) based on IDE timeouts, artifact review notifications, or automatic system 'Auto-proceed' events.
    - All code modifications are strictly prohibited while in the planning phase. The agent must pause and wait until the user explicitly commands to proceed in the chat (e.g. 'procede', 'ejecuta el plan', 'adelante con el código').


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
