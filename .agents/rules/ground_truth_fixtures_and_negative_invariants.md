# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory Directive: Ground-Truth Fixtures & Negative Invariants Governance

> **CORE GOVERNANCE DIRECTIVE — ZERO MOCK BLINDNESS:**
> Applies to all AI agents and developers creating or testing integrations with MikroTik RouterOS v7, KeyDB, or hardware network telemetry.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. The Mock Blindness Anti-Pattern

Synthetic unit test mocks created ad-hoc by developers invariably introduce **Mock Blindness**:
- The test writer models only the happy path based on idealized assumptions.
- Factory-default states, inert firmware configurations, missing hardware chips, and unconfigured menus return unexpected payloads in real life (e.g. `remote="0.0.0.0"`, empty lists `[]`, or HTTP 404/400).
- Synthetically passing tests give false confidence while the real frontend reports false positives on unconfigured lab or production equipment.

---

## 2. Universal Trimodal Ground-Truth Fixture Matrix

For **EVERY** component, service, or worker interacting with MikroTik RouterOS v7 REST API (`/rest/*`), the test suite MUST include and validate against the following three raw JSON fixtures captured from physical or containerized RouterOS v7 hardware under `fastapi/tests/fixtures/mikrotik/`:

| Fixture Type | Canonical Description | Mandatory Assertion (Negative Invariant) |
| :--- | :--- | :--- |
| **Fixture A: Factory Default (Virgin)** | Raw JSON from unconfigured RouterOS v7 out-of-the-box (`system reset-configuration`). | **MUST assert negative:** `active=False`, `status="NOT_CONFIGURED"`, `score=LOW`, `items=[]`. Any positive detection is a critical failure. |
| **Fixture B: Nominal RoSGrid Configured** | Raw JSON from router provisioned with official RoSGrid templates & services. | **MUST assert positive:** `active=True`, `status="ONLINE"`, expected operational telemetry. |
| **Fixture C: Degraded / Unsupported / Disabled** | Raw JSON with services disabled (`disabled=true`) or missing hardware subsystem (e.g. PoE on CHR, WiFi on CCR2004). | **MUST assert graceful handling:** No unhandled exceptions (`500`), explicit state `UNSUPPORTED` or `DISABLED`, zero CPU/KeyDB leak. |

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
