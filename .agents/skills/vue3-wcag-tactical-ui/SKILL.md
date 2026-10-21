---
name: vue3-wcag-tactical-ui
description: >-
  High-density WinBox-style Vue 3 + TypeScript architecture (Tactical NOC Cyan),
  optimized with shallowRef, native Virtual Scrolling, and Canvas 2D to pass @axe-core/playwright
  (0 WCAG 2.1 AA violations) and Lighthouse CI (>= 90 / >= 95 A11y) on the first pass.
  Applies to RoSGrid Milestones 11, 12, and 13.
---

# Vue 3 WCAG 2.1 AA & Tactical NOC UI (Standard 11X)

This skill governs all stores, composables, components, and views inside `vue3/` during **Milestones 11, 12, and 13**.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Design System: Tactical NOC Cyan Palette & Tabular Typography

1. **Native CSS Variables (`vue3/src/assets/themes.css`):**
   - **Default Theme (`data-theme="dark"` — Tactical NOC Cyan):**
     * `--rg-bg-canvas`: `#0B0F19` | `--rg-bg-surface`: `#111827` | `--rg-bg-elevated`: `#1E293B` | `--rg-border-grid`: `#1E293B` / `#334155`.
     * `--rg-accent-cyan`: `#22D3EE` for interactive text and icons over dark backgrounds (**10.8:1** contrast ratio, exceeding WCAG 2.1 AA) and `#06B6D4` for active borders and glow effects `--rg-cyan-glow: 0 0 12px rgba(6, 182, 212, 0.28)`.
     * `--rg-text-primary`: `#F8FAFC` | `--rg-text-secondary`: `#CBD5E1` | `--rg-text-muted`: `#94A3B8` (forbid grays with ratio `< 4.5:1`).
   - **Light Theme (`data-theme="light"`):** Background `#F8FAFC`/`#FFFFFF`, dark cyan accent `#0E7490` (ratio `>= 5.2:1`), text `#0F172A`/`#334155`.
   - **NOC Wallboard Theme (`data-theme="noc-high-contrast"`):** Pure `#000000` background, scaled typography `1.15rem`, and `2px` borders for readability at 5 meters.
2. **Zero External Fonts & Mandatory `tabular-nums`:**
   - **Strictly forbidden** to load fonts from Google Fonts or external CDNs.
   - All IP/MAC addresses, byte/packet counters, SFP optical powers (`dBm`), uptimes, and timers MUST use the system monospace stack (`'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace`) with `font-variant-numeric: tabular-nums`.

---

## 2. Extreme Vue 3 Performance (`shallowRef`, Virtual Scroll & 2D `<canvas>`)

1. **Mandatory `shallowRef` in Pinia (`vue3/src/stores/`):**
   - In `useInventoryStore`, `useWebFigStore`, and `useLiveTelemetryStore`, all large RouterOS v7 collections (interfaces, firewall rules, PPPoE sessions, BGP routes) and the `TelemetryRingBuffer` MUST use `shallowRef()` (triggering updates with `triggerRef()`) rather than deep `ref()`, eliminating nested proxy overhead.
2. **Adaptive Dual Density + Native Virtual Scrolling in `RgDataTable.vue`:**
   - **`compact` Mode (Desktop `>= 1024px`):** Exact row height `32px`, `1px solid var(--rg-border-grid)` WinBox-style grid borders.
   - **`comfortable` Mode (Mobile/Tablet `< 1024px`):** Minimum row height and touch targets `44px`, first column pinned (`position: sticky; left: 0; z-index: 2`), and `+ View details` drawer button.
   - **Native Virtual Scrolling:** When `rows.length > 100`, `RgDataTable.vue` calculates `startIndex` and `endIndex` (`overscan = 10`) using fixed row height (`32px` or `44px`) and only renders the ~30 visible rows in the DOM.
3. **HTML5 2D `<canvas>` Charts with `requestAnimationFrame` & E2E Deterministic Mode:**
   - `TelemetryRingBuffer` curves (up to 5,400 points) in `RouterLiveDashboardView.vue` render on 2D `<canvas>` via `requestAnimationFrame`.
   - When `navigator.webdriver === true` (Playwright E2E), disable continuous animations and draw a static deterministic frame with fixed `min-height` to pass `toHaveScreenshot` (`maxDiffPixelRatio <= 0.01`).
4. **Code-Splitting in Vite & Vue Router:**
   - Configure `manualChunks` in `vite.config.ts` separating `vendor-vue` (`vue`, `vue-router`, `pinia`) and `vendor-map` (`leaflet`). Use dynamic imports `() => import(...)` for non-critical views.

---

## 3. Strict Accessibility Directives (`@axe-core/playwright` = 0 Violations)

1. **HTML5 Semantic Landmarks in `RgResponsiveShell.vue`:**
   - Provide `<header>`, `<nav aria-label="Navegación principal">`, `<main id="main-content">` (with *Skip to main content* link on `Tab`), and `<aside aria-label="Estado de sesión y alertas">`.
   - On mobile (`< 768px`), activate the fixed bottom bar with 5 targets of `44x44px`.
2. **Form & Table Controls:**
   - Every `<input>`, `<select>`, or `<textarea>` MUST have an explicit `<label :for="id">` or descriptive `aria-label`.
3. **Icon Buttons & Keyboard Drag-and-Drop:**
   - Every icon button MUST have an `aria-label="..."` and the inner SVG MUST declare `aria-hidden="true"`.
   - Reorderable rows in `RgDataTable.vue` MUST provide keyboard shortcuts (`Alt + ArrowUp` / `Alt + ArrowDown` with `aria-label="Mover regla *1C hacia arriba"`) to fulfill **WCAG 2.1.1**.
4. **Heading Hierarchy & Document Title:**
   - Exactly one `<h1>` per view, followed by consecutive `<h2>`/`<h3>` headings without skipping levels. Dynamically update `document.title` in `router.beforeEach`.
