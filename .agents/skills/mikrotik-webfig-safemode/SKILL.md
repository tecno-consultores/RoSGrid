---
name: mikrotik-webfig-safemode
description: >-
  MikroTik RouterOS v7.13+ REST API domain rules (/rest/*), native flags ([D]/[X]/[I]/[R]),
  in-memory <KeepAlive :max="5"> workspace cache, ephemeral RingBuffer telemetry, 60s Safe Mode,
  HTTP 202 Maker-Checker interception, and 30s Step-Up Auth Vault.
---

# MikroTik RouterOS v7.13+ Domain, Dual-Layer WebFig & Operational Safety

This skill governs the integration between Vue 3 (`vue3/`) and FastAPI endpoints for operating MikroTik **RouterOS v7.13+** fleets over HTTPS REST API (`/rest/*`).
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. RouterOS v7.13+ (`/rest/*`) UI Particulars

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
   - Consume `GET /api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}` with `/rest/console/inspect` schema fallback for empty tables, server-side `.query`/`.proplist` projection, contextual RPC actions (`RgLayer2RpcActionModal.vue`), bulk mutations under a single 60s Safe Mode window, and `.rsc` submenu export/diff (`RgLayer2RscExportDiffModal.vue`).
   - If `is_singleton === false`, generate `RgDataTable.vue` from `columns_schema` and modal CRUD mapping `string`, `integer`, and `boolean_ros`.
   - If `is_singleton === true`, render the configuration form dispatching `POST <endpoint>/set` with **Safe Mode (60s)** enabled by default.

---

## 2. In-Memory Workspace Cache (`KeepAlive`) & Ephemeral Telemetry (`TelemetryRingBuffer`)

1. **In-Memory Cache (`KeepAlive`) Without Redundant Tab Bar:**
   - `RouterWebFigLayout.vue` maintains `<keep-alive :max="5">` in RAM so switching between submodules of the same router via `RouterSidebarMenu.vue` preserves filters, sorting, and diagnostic state (`Ping`, `Traceroute`, `Torch`) without rendering a redundant top tab bar.
2. **Strict Telemetry Lifecycle (`TelemetryRingBuffer`):**
   - Exact memory capacity: `MAX_POINTS = 5400` points in RAM (3 hours at 1 tick every 2 seconds, $O(1)$ ring buffer insertion) with window selectors (`2m`, `15m`, `1h`, `3h`).
   - The `/ws/v1/routers/{router_id}/live-telemetry` WebSocket lives in parent `RouterWebFigLayout.vue` so it remains uninterrupted when switching submodules.
   - Upon **leaving the router** (`onBeforeUnmount` in `RouterWebFigLayout.vue`) or changing `router_id`, immediately close the WebSocket (triggering backend polling stop if `SCARD == 0` in KeyDB) and call `liveTelemetryStore.resetChartsBuffer()` and `webFigStore.clearRouterWorkspace()`. Never persist metrics in `localStorage` or `IndexedDB`.

---

## 3. Security Interceptors, Safe Mode (60s), Maker-Checker & Vault (30s)

1. **Zero-Trust HTTP Client (`vue3/src/api/httpClient.ts`):**
   - Forbid storing JWT tokens in `localStorage` or `sessionStorage`. Use `fetch` with `credentials: "include"`.
   - Attach `X-CSRF-Token` and `Idempotency-Key` (UUIDv7 generated via `crypto.getRandomValues`, preserved across `502`/`503`/`504` retries) to all mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
   - Seamless token rotation on `401` using a shared singleton promise (`refreshPromiseSingleton`) towards `/api/v1/auth/refresh`.
2. **`HTTP 202 Accepted` Interception (*Maker-Checker*):**
   - When an operation returns `202 Accepted` with `status === "INTERCEPTED_FOR_APPROVAL"` (or `AWAITING_APPROVAL` in MCP), do NOT throw: dispatch an informative toast with the request ID and update the visual form state.
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

### Key RouterOS v7.13+ REST Invariants:
1. **Required Group Policies (`rosgrid-api-group`):**
   - RouterOS v7.13+ requires `policy=api,rest-api,read,write,ftp,test,reboot,policy,sensitive` (`rest-api` for `/rest/*`, `ftp` for `/export file=...` while `/ip service ftp` remains disabled, and `sensitive` for reading secrets/certificates).
2. **Singleton Settings Menus (`/snmp`, `/system/ntp/client`, `/ip/dns`, `/system/clock`):**
   - RouterOS v7 rejects root-level `PATCH` requests on singleton configuration menus with `HTTP 500` or identifier errors. Always dispatch property modifications via `POST <endpoint>/set`.
3. **Identifier & Action Name Constraints:**
   - Resource names such as `/system/logging/action` require strict alphanumeric identifiers (`letters and digits only`, e.g. `rosgridsyslog`).
