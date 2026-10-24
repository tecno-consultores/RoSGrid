---
name: mikrotik-webfig-safemode
description: >-
  MikroTik RouterOS v7 REST API domain rules (/rest/*), native flags ([D]/[X]/[I]/[R]),
  WebFig tabs with <KeepAlive :max="5">, ephemeral RingBuffer telemetry, 60s Safe Mode,
  HTTP 202 Maker-Checker interception, and 30s Step-Up Auth Vault.
  Applies to RoSGrid Milestones 11, 12, and 13.
---

# MikroTik RouterOS v7 Domain, Dual-Layer WebFig & Operational Safety

This skill guides the integration between Vue 3 (`vue3/`) and FastAPI endpoints for operating MikroTik RouterOS v7.1+ fleets.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. RouterOS v7 (`/rest/*`) UI Particulars

1. **Internal Identifiers (`.id`) & Native Flags:**
   - Preserve RouterOS hexadecimal identifiers with asterisks (`*1`, `*1A`, `*1C`) when selecting, modifying, deleting, or reordering rules (`POST .../move`).
   - In `RgDataTable.vue`, render the native RouterOS flag column at the beginning of each row:
     * `[D]` (*Dynamic*) in informative cyan (`#38BDF8`).
     * `[X]` (*Disabled*) applying italics and accessible opacity across the row.
     * `[I]` (*Invalid*) in coral red (`#EF4444`) with tooltip explanation.
     * `[R]` (*Running*) in emerald green (`#10B981`) for active interfaces and sessions.
2. **SFP/SFP+ Optical DDM Diagnostics (`InterfacesAndSfpView.vue`):**
   - Display `tx-power` and `rx-power` laser levels in `dBm`, temperature, and voltage color-coded by optical health (`OPTIMAL`, `WARNING`, `CRITICAL_LOW_LIGHT`).
3. **Universal Layer 2 Dynamic Engine (`DynamicLayer2ResourceView.vue`):**
   - Consume `GET /api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}`.
   - If `is_singleton === false`, generate `RgDataTable.vue` from `columns_schema` and modal CRUD mapping `string`, `integer`, and `boolean_ros`.
   - If `is_singleton === true`, render the configuration form with **Safe Mode (60s)** enabled by default.

---

## 2. Workspace Tabs (`KeepAlive`) & Ephemeral Telemetry (`TelemetryRingBuffer`)

1. **WinBox/IDE Tab Bar (`RouterWorkspaceTabsBar.vue`):**
   - Backed by `useWebFigStore.openRouterTabs` with a strict limit of **5 active tabs in FIFO/LRU order (`MAX_OPEN_TABS = 5`)** wrapped in `<KeepAlive :max="5">`.
   - Preserves filter strings (e.g. `chain=forward`), sorting, and diagnostic tools (`Ping`, `Traceroute`, `Torch`) in RAM when switching between submenus on the same router.
2. **Strict Telemetry Lifecycle (`TelemetryRingBuffer`):**
   - Exact memory capacity: `MAX_POINTS = 5400` points in RAM (3 hours at 1 tick every 2 seconds, $O(1)$ ring buffer insertion) with zoom buttons (`2m`, `15m`, `1h`, `3h`).
   - The `/ws/v1/routers/{router_id}/live-telemetry` WebSocket lives in parent `RouterWebFigLayout.vue` so it remains uninterrupted when switching internal tabs.
   - Upon **leaving the router** (`onBeforeUnmount` in `RouterWebFigLayout.vue`) or changing `router_id`, immediately close the WebSocket (triggering backend polling stop if `SCARD == 0` in KeyDB) and call `liveTelemetryStore.resetChartsBuffer()` and `webFigStore.clearRouterWorkspace()`. Never persist metrics in `localStorage` or `IndexedDB`.

---

## 3. Security Interceptors, Safe Mode (60s), Maker-Checker & Vault (30s)

1. **Zero-Trust HTTP Client (`vue3/src/api/httpClient.ts`):**
   - Forbid storing JWT tokens in `localStorage` or `sessionStorage`. Use `fetch` with `credentials: "include"`.
   - Attach `X-CSRF-Token` and `Idempotency-Key` (UUIDv7 generated via `crypto.getRandomValues`, preserved across `502`/`503`/`504` retries) to all mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
   - Seamless token rotation on `401` using a shared singleton promise (`refreshPromiseSingleton`) towards `/api/v1/auth/refresh`.
2. **`HTTP 202 Accepted` Interception (*Maker-Checker*):**
   - When an operation returns `202 Accepted` with `status === "INTERCEPTED_FOR_APPROVAL"`, do NOT throw: dispatch an informative toast with the request ID and update the visual form state.
3. **Safe Mode Countdown Banner (`RgSafeModeBanner.vue`):**
   - Accessible top banner (`role="status"`, `aria-live="polite"`) displaying a 60-second countdown while backend verifies router survivability and confirms the `rosgrid_safemode_*` scheduler removal.
4. **Step-Up Auth Vault with 30s Auto-Destruction (`VaultRevealModal.vue`):**
   - Restricted to `SUPERADMIN_GLOBAL` and `TENANT_ADMIN`. Requires live 2FA TOTP verification (`RgStepUp2FAModal.vue`), displays a 30-second countdown bar, and automatically purges the plaintext password from memory when reaching `0`.

---

## 4. Official MikroTik Documentation & Zero-Hallucination Grounding

Before introducing new WebFig endpoints, Golden Config templates, or bulk operations, verify syntax directly against official vendor resources:

- **Official MikroTik v7 Documentation Hub:** [https://manual.mikrotik.com/docs/introduction/](https://manual.mikrotik.com/docs/introduction/)
- **Open LLM Index (Fast Semantic Retrieval):** [https://manual.mikrotik.com/llms.txt](https://manual.mikrotik.com/llms.txt)
- **CLI & REST API Reference:** [https://manual.mikrotik.com/docs/cli-reference/](https://manual.mikrotik.com/docs/cli-reference/)

### Key RouterOS v7 REST Invariants:
1. **Singleton Settings Menus (`/snmp`, `/system/ntp/client`, `/ip/dns`):**
   - RouterOS v7 rejects root-level `PATCH` requests on singleton configuration menus with `HTTP 500` or identifier errors.
   - Always dispatch property modifications via `POST <endpoint>/set` (e.g. `POST snmp/set` with `{enabled: "yes"}`).
2. **Identifier & Action Name Constraints:**
   - Resource names such as `/system/logging/action` require strict alphanumeric identifiers (`letters and digits only`). Avoid hyphens (`-`) or special characters that trigger `HTTP 400 failure: action name can contain only letters and numbers`.
3. **Parameter Evolution (v6 vs v7):**
   - Legacy parameters (e.g. `bsd-syslog`, `facility`, `sys-ident`) are discontinued. Modern v7 equivalents must be used (e.g. `remote-log-format: syslog`, `syslog-facility: daemon`).

