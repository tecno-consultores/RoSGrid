# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory Directive: Anti-Regression & Side-Effects Guardrail

> **SUPREME GOVERNANCE INVARIANT:**
> No code change or refactoring may degrade, break, or disable an existing, previously validated feature. Whenever modifying shared modules, network configurations, or state stores, all agents and developers must proactively enforce the anti-regression safeguards defined herein.

---

## 1. Pre-Modification Impact & Blast-Radius Analysis

Before altering any shared code, service definition, or configuration:
1. **Shared Configuration & Port Invariants (`docker-compose*.yml`):**
   - **Never delete or overwrite canonical protocol ports** when adding or exposing alternative ports.
   - For Syslog, both the standard RFC 3164 / MikroTik port (`514:5514/udp`) and the unprivileged alternative (`5514:5514/udp`) must remain exposed simultaneously.
   - For WebFig, API, and WebSocket endpoints, verify that base HTTP/HTTPS/WSS bindings remain reachable.
2. **Dependency & Shared Worker Audit:**
   - When modifying worker loops (`health_monitor_worker`, `syslog_collector`, `subscriber_poller`), audit all downstream KeyDB keys and consumers to ensure existing TTLs, channel subscriptions, and key structures (`rg:{tid}:router:{rid}:*`) are preserved.

---

## 2. Real-World Network & Docker NAT Tolerance (Anti-Localhost Blindness)

1. **Docker Userland-Proxy & Gateway NAT Tolerance:**
   - In containerized environments, inbound UDP/TCP traffic mapped through host ports is rewritten with the bridge gateway address (e.g. `172.18.0.1` or `127.0.0.1`).
   - Never rely exclusively on socket `addr[0]` to map incoming traffic to a database entity.
   - Implement heuristic cascade resolution:
     - 1st: Exact match on source IP (`ip_router_map`).
     - 2nd: Payload scan for registered router IP addresses.
     - 3rd: Header token match for `display_name` or `ros_identity`.
2. **Canonical MikroTik RouterOS v7 Naming:**
   - Never hardcode proprietary names (e.g. `"rosgridsyslog"`) as the sole condition to detect a remote service.
   - Always accept standard RouterOS defaults (`name="remote"`, `target="remote"`, explicit `remote` IP/host destination, or active rules in `/system/logging`).

---

## 3. Strict Pre-Build Static Analysis (Zero Missing Imports)

1. **Mandatory Immediate Linting:**
   - Before executing `docker build`, restarting containers, or concluding a turn, verify syntactic integrity using:
     - Backend: `docker run --rm --entrypoint ruff -v $(pwd)/fastapi:/app -w /app sinfallas/rosgrid-backend:local-test check --no-cache src/`
     - Frontend: `docker run --rm -v $(pwd)/vue3:/app -w /app sinfallas/base-node-ionic:26 npx vue-tsc --noEmit`
2. **Zero Runtime Exceptions:**
   - Missing imports (e.g. `asyncio`, `uuid`, `logging`) or unhandled type mutations must be detected during static check, never discovered through runtime container failure or blank screens.

---

## 4. Frontend Anti-Degradation (No Destructive Catch)

1. **Preserve Valid Known State on Network Error:**
   - Pinia stores must never reset populated arrays or objects to empty primitives (e.g. `setRouters([])`) inside generic `catch` blocks if valid data already exists in memory.
   - Maintain the last known good state and set an explicit error/stale status flag to inform the operator without destroying rendered views.
2. **Explicit User Feedback:**
   - Action buttons (such as `[Actualizar Datos]`) must always report success, in-flight progress, or failure feedback reactively.

---

## 5. Cross-Functional Smoke Verification Checklist

Prior to submitting any task touching shared domains:
- [ ] Are all standard ports preserved in Docker configurations?
- [ ] Does `ruff check src/` and `vue-tsc --noEmit` pass with zero errors?
- [ ] Did the modification break any adjacent feature in the same view or API group?
- [ ] Were existing tests re-executed and confirmed passing (Vitest 100%, Pytest 100%)?
