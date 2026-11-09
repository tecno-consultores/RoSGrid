# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Terminal ↔ Frontend Parity & UI Invariants

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers working on RoSGrid.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Terminal ↔ Frontend Parity Invariants

1. **Zero Console-Exclusive Actions & Zero Orphan API Endpoints (Spec 60):**
   - Any operational, administrative, or diagnostic capability exposed by the backend (`fastapi/src/api/v1/`) MUST have a matching, actionable Vue 3 interface (`vue3/src/`).
   - Prohibit route and HTTP method mismatches (404/405) between frontend and backend, support singleton menus (`POST .../set` and `PATCH`), and certify 100% bidirectional parity via `.agents/scripts/verify_no_orphan_api_endpoints.py` (step `[6/9]` of `certify_task_completion.sh`).
2. **Bidirectional CLI Session Audit Sync:**
   - Maintenance CLI scripts issuing tokens or altering sessions MUST sync metadata into KeyDB (`issued_by_username: "CLI (Terminal)"`) so they are visible and revocable via `ActiveSessionsKillSwitchView.vue`.
3. **Zero Read-Only Operational Consoles (WebFig v7 Parity):**
   - Every router management table (Firewall, Queues, PPP, DHCPv4, Dual-Stack IPv6, Routing) MUST offer tactical mutation actions (create, edit, toggle enable/disable, delete with confirmation, and 1-click setup wizards) guarded by 60s Safe Mode.
4. **Zero-Overlap Geographic Co-location & Tenant HQ Centering Invariant (Specs 104–113):**
   - Cartographic Leaflet maps (`UnifiedNetworkMap.vue`, `OsmRouterMap.vue`, `OsmOnuMap.vue`) MUST group co-located devices (`<= 25m`) into a distinct cluster marker (`rg-map-pin--multi`) with numeric badge, radial spiderfication, and side-drawer listing.
   - `RgResponsiveShell.vue` and `FieldTechMobileView.vue` MUST hydrate `authStore.fetchTenantFeatures()` on mount and center maps/forms on `authStore.tenantHqCoordinates` when no active nodes override the bounds.
5. **Refactoring UI Hierarchy & Dynamic Theme Token Parity (Specs 53 & 111):**
   - All `var(--rg-*)` tokens MUST be defined across all 3 themes (`dark`, `light`, `noc-high-contrast`) in `vue3/src/assets/themes.css`. Never hardcode `data-theme` on view roots (`NocWallboardView.vue`) or static dark hex colors.
   - Enforce a single primary button per view, neutral-at-rest secondary/row actions, concentric segmented radii (`8px`/`5px`), tactical `RgDataTable` empty states, and geometric Online/Offline indicators for colorblind safety.
6. **Responsive Multi-Viewport, Safe Vertical Scroll & Stacking Context Isolation (Specs 107–112):**
   - Enforce zero horizontal viewport overflow across mobile (`375x667`), tablet (`768x1024`), and desktop (`1440x900`).
   - Isolate `.rg-header` (`z-index: 3000`) above `.rg-main` (`isolation: isolate; z-index: 1`) in `RgResponsiveShell.vue` so header dropdowns never collide with the translucent `NocWallboardView.vue` events HUD overlay (`.wallboard-events-overlay`).
   - In `LoginView.vue`, use safe vertical scroll (`justify-content: flex-start` + `margin: auto`) to prevent logo clipping and keep 2-column form inputs (`.form-row-2col`) baseline-aligned (`margin-top: auto`) with single-line labels.
7. **Contextual Help Boundary, Zero-Trust Anti-Indexing & LLM-Ready MCP Context (Spec 53):**
   - Every global route and WebFig module MUST resolve to a topic in `RgContextualHelpDrawer.vue` (`helpCatalog.ts`, zero PDF buttons inside `RoSGrid`), enforce `X-Robots-Tag: "noindex, nofollow, noarchive, nosnippet"`, persist `rg_theme` and `rg_table_density`, and expose all 6 MCP client snippets + `llms.txt` context in `RgMcpTokenModal.vue`.
8. **WebFig Layer 2 Next-Gen Universal Engine Invariant (Spec 54):**
   - `DynamicLayer2ResourceView.vue` and `webfig_layer2.py` enforce contextual RPC actions (`RgLayer2RpcActionModal.vue`), `/rest/console/inspect` schema discovery for empty tables, server-side `.query` & `.proplist` projection (`RgLayer2QueryBuilder.vue`), multi-row bulk mutations under a single 60s Safe Mode window, `.rsc` submenu export/diff (`RgLayer2RscExportDiffModal.vue`), and persisted column profiles (`useLayer2ColumnProfiles.ts`).
9. **In-App Tactical Notification Center & Real-Time Maker-Checker Reactivity (Specs 79–82):**
   - `RgResponsiveShell.vue` renders `RgBrandLogo.vue`, connects `nocStore.connectEventsWebSocket()` on mount, and exposes `RgNotificationCenterBell.vue` (`Alt+N`) separating *Read State* (`lastReadIso`) from *Action Completion* (`requiresAction`), with 1-click inline triage (`✓ Aprobar 1-Clic` / `👁️ Reconocer (Ack)`), `[×N]` deduplication, session noise filtering, and explicit `[ 🔄 Refrescar ]` triggers on live operational views.

---

## 2. Proactive Vulnerability Audit & Closure Gate

1. **User State, Tenant Context & Anti-XSS:**
   - Ensure inactive/locked accounts cannot generate tokens, every DB query runs within `set_tenant_context`, dynamic HTML is sanitized (`sanitizeHtml` in Leaflet popups, zero raw `v-html`), and mutation endpoints validate CSRF tokens + `Idempotency-Key`.
2. **Unified 9-Step Certification Gate (`certify_task_completion.sh`):**
   - Before committing and pushing (`git push origin <branch>`), run `./.agents/scripts/certify_task_completion.sh` to certify all **9 gates**: (1) zero exposed secrets, (2) Trivy IaC/FS scan = 0 CRITICAL/HIGH, (3) i18n JSON integrity, (4) AST topological health, (5) zero orphan Vue components, (6) zero orphan API endpoints + anti-silo test quality, (7) ORM/Alembic parity, (8) 28 live Front-Back contracts, and (9) documentation + `ROADMAP.md` / `ACTIVE_TASK.md` consistency.
