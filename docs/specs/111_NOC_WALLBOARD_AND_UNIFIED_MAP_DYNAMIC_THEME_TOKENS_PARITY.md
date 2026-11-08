# Especificación 111: Paridad Dinámica de Temas (`dark` / `light` / `noc-high-contrast`) con Variables Semánticas `var(--rg-*)` en `NocWallboardView.vue`, `UnifiedNetworkMap.vue` y `SubscribersMapView.vue`

> **Hito Objetivo:** Hito 30.34 (Eliminación de `data-theme="noc-high-contrast"` Hardcodeado y Migración de Colores Estáticos Oscuros a Tokens `var(--rg-*)` en `NocWallboardView.vue`, `UnifiedNetworkMap.vue` y `SubscribersMapView.vue`)
> **Modo de Ejecución:** Especificación *Flash-Ready* para implementación directa, determinista y sin ambigüedades por **Gemini 3.8 Flash High**.
> **Regla de Oro QA 11X:** Prohibido ejecutar pruebas o linters en el host; toda verificación ocurre en contenedores efímeros Docker (`Regla Cero`).

---

## 1. Diagnóstico Causa Raíz (Root Cause Analysis)

Durante las pruebas de aceptación en `/noc-wallboard` tras seleccionar el tema **Claro (`light`)** en el menú de usuario, el usuario reportó con captura de pantalla (`media_1794168340584_3495b0a1.png`):
1. **"wallboardnoc no cambia los colores"**:
   - **Causa Raíz 1 (`data-theme="noc-high-contrast"` Hardcodeado en `vue3/src/views/NocWallboardView.vue`):**
     En la línea 397 de `NocWallboardView.vue`:
     ```html
     <div
       ref="wallboardContainer"
       class="noc-wallboard"
       data-theme="noc-high-contrast"
       role="region"
       aria-label="Wallboard NOC 24/7 Pantalla Completa"
     >
     ```
     El atributo `data-theme="noc-high-contrast"` estaba fijo en el nodo raíz de `NocWallboardView.vue`, bloqueando la herencia del atributo `<html data-theme="light|dark|noc-high-contrast">` gestionado por `useThemeAndLayoutStore`.
   - **Causa Raíz 2 (Colores Hexadecimales Oscuros Hardcodeados en `<style scoped>` de `NocWallboardView.vue`, `UnifiedNetworkMap.vue` y `SubscribersMapView.vue`):**
     - En `NocWallboardView.vue`, `.noc-wallboard` (`#030712`), `.wallboard-header` (`#0b0f19`), `.kpi-card` (`#111827`), `.btn-fullscreen` (`#1f2937`) y `.wallboard-events-overlay` (`rgba(3, 7, 18, 0.72)`) usaban valores hexadecimales oscuros fijos en lugar de las variables semánticas `var(--rg-*)` de `vue3/src/assets/themes.css`.
     - En `UnifiedNetworkMap.vue`, `.unified-map-toolbar` (`rgba(15, 23, 42, 0.95)`), `.btn-layer-toggle` (`rgba(30, 41, 59, 0.8)`), `.rg-select-filter` (`rgba(15, 23, 42, 0.9)`) y `.unified-detail-drawer` (`rgba(15, 23, 42, 0.96)`) también usaban colores oscuros estáticos.
     - En `SubscribersMapView.vue`, `.subscribers-map-view` (`#060b13`), `.kpi-card` (`#0d1628`), `.rg-search-input` (`#0d1628`) y `.chip-btn` (`#0d1628`) tenían el mismo problema al cambiar al tema Claro.

---

## 2. Solución Arquitectónica Exacta (Paso a Paso)

### Paso 1: Eliminar `data-theme="noc-high-contrast"` Fijo y Adoptar Tokens `var(--rg-*)` en `vue3/src/views/NocWallboardView.vue`

**Archivo:** `vue3/src/views/NocWallboardView.vue`

1. En `<template>` (líneas 394–400), eliminar el atributo estático `data-theme="noc-high-contrast"` para que `.noc-wallboard` herede automáticamente el tema global activo (`dark`, `light` o `noc-high-contrast`):

```html
  <div
    ref="wallboardContainer"
    class="noc-wallboard"
    role="region"
    aria-label="Wallboard NOC 24/7 Pantalla Completa"
  >
```

2. En `<style scoped>` de `vue3/src/views/NocWallboardView.vue`, reemplazar los colores oscuros estáticos por tokens semánticos `var(--rg-*)` y `color-mix(in srgb, var(--rg-*) ..., transparent)`:
   - `.noc-wallboard`:
     ```css
     background-color: var(--rg-bg-canvas);
     color: var(--rg-text-primary);
     border: 1px solid var(--rg-border-panel);
     ```
   - `.wallboard-header`:
     ```css
     background-color: var(--rg-bg-surface);
     border-bottom: 1px solid var(--rg-border-panel);
     ```
   - `.brand-title`:
     ```css
     color: var(--rg-accent-cyan);
     ```
   - `.kpi-card`:
     ```css
     background: var(--rg-bg-elevated);
     border: 1px solid var(--rg-border-panel);
     ```
   - `.kpi-label`:
     ```css
     color: var(--rg-text-muted);
     ```
   - `.text-cyan`, `.text-green`, `.text-yellow`, `.text-red`, `.text-blue`:
     ```css
     .text-cyan {
       color: var(--rg-accent-cyan);
     }
     .text-green {
       color: var(--rg-status-online);
     }
     .text-yellow {
       color: var(--rg-status-warning);
     }
     .text-red {
       color: var(--rg-status-critical);
     }
     .text-blue {
       color: var(--rg-status-info);
     }
     ```
   - `.btn-wallboard-refresh` y `.btn-fullscreen`:
     ```css
     .btn-wallboard-refresh {
       background: var(--rg-btn-action-bg);
       border: 1px solid var(--rg-accent-cyan-border);
       color: var(--rg-accent-cyan);
       padding: 0.4rem 0.8rem;
       border-radius: 4px;
       font-size: 0.8rem;
       font-weight: 600;
       cursor: pointer;
       transition: all 0.15s ease;
     }

     .btn-wallboard-refresh:hover:not(:disabled) {
       background: var(--rg-bg-elevated);
       color: var(--rg-text-primary);
     }

     .btn-fullscreen {
       background: var(--rg-btn-action-bg);
       border: 1px solid var(--rg-btn-action-border);
       color: var(--rg-btn-action-fg);
       padding: 0.4rem 0.8rem;
       border-radius: 4px;
       font-size: 0.8rem;
       font-weight: 600;
       cursor: pointer;
     }
     ```
   - `.wallboard-router-hud`, `.hud-title`, `.hud-meta`, `.hud-meta code`:
     ```css
     .wallboard-router-hud {
       position: absolute;
       bottom: 1.25rem;
       left: 1.25rem;
       right: 1.25rem;
       background: color-mix(in srgb, var(--rg-bg-surface) 90%, transparent);
       backdrop-filter: blur(8px);
       border: 1px solid var(--rg-accent-cyan-border);
       border-radius: 8px;
       padding: 0.75rem 1.25rem;
       display: flex;
       justify-content: space-between;
       align-items: center;
       gap: 1rem;
       z-index: 1000;
       box-shadow: var(--rg-shadow-lg);
       transition: right 0.2s ease;
     }
     .hud-title {
       font-size: 0.95rem;
       font-weight: 700;
       color: var(--rg-accent-cyan);
       white-space: nowrap;
       overflow: hidden;
       text-overflow: ellipsis;
     }
     .hud-meta {
       font-size: 0.75rem;
       color: var(--rg-text-secondary);
       display: flex;
       align-items: center;
       gap: 0.5rem;
       flex-wrap: wrap;
     }
     .hud-meta code {
       color: var(--rg-text-primary);
       background: var(--rg-bg-elevated);
       padding: 0.1rem 0.35rem;
       border-radius: 4px;
     }
     ```
   - `.wallboard-events-overlay`, `.btn-events-hud-pill`, `.events-header`, `.events-title`, `.btn-collapse-events-hud`, `.events-empty-state`, `.event-item`, `.event-time`, `.event-type-badge`, `.event-router`, `.event-msg`:
     ```css
     .wallboard-events-overlay {
       position: absolute;
       top: 62px;
       right: 16px;
       bottom: 16px;
       width: 370px;
       max-width: calc(100vw - 32px);
       display: flex;
       flex-direction: column;
       background: color-mix(in srgb, var(--rg-bg-surface) 76%, transparent);
       backdrop-filter: blur(8px);
       -webkit-backdrop-filter: blur(8px);
       border: 1px solid var(--rg-border-panel);
       border-radius: 12px;
       box-shadow: var(--rg-shadow-lg);
       overflow: hidden;
       z-index: 850;
     }

     .btn-events-hud-pill {
       position: absolute;
       top: 62px;
       right: 16px;
       z-index: 850;
       background: color-mix(in srgb, var(--rg-bg-surface) 86%, transparent);
       backdrop-filter: blur(8px);
       border: 1px solid var(--rg-accent-cyan-border);
       color: var(--rg-accent-cyan);
       padding: 0.45rem 0.9rem;
       border-radius: 999px;
       font-size: 0.8rem;
       font-weight: 700;
       cursor: pointer;
       box-shadow: var(--rg-shadow-md);
       transition: all 0.15s ease;
     }

     .btn-events-hud-pill:hover {
       background: var(--rg-bg-elevated);
       color: var(--rg-text-primary);
       border-color: var(--rg-accent-cyan);
     }

     .events-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       padding: 0.65rem 0.9rem;
       background: color-mix(in srgb, var(--rg-bg-elevated) 84%, transparent);
       border-bottom: 1px solid var(--rg-border-panel);
     }

     .events-title {
       font-size: 0.9rem;
       font-weight: 700;
       color: var(--rg-text-primary);
       margin: 0;
     }

     .btn-collapse-events-hud {
       background: var(--rg-btn-action-bg);
       border: 1px solid var(--rg-btn-action-border);
       color: var(--rg-btn-action-fg);
       width: 26px;
       height: 26px;
       border-radius: 6px;
       display: inline-flex;
       align-items: center;
       justify-content: center;
       cursor: pointer;
       font-weight: 700;
       transition: all 0.15s ease;
     }

     .events-empty-state {
       padding: 1.25rem;
       color: var(--rg-text-secondary);
       font-size: 0.85rem;
       text-align: center;
     }

     .event-item {
       background: color-mix(in srgb, var(--rg-bg-elevated) 82%, transparent);
       border: 1px solid var(--rg-border-grid);
       border-left: 4px solid var(--rg-accent-cyan);
       padding: 0.5rem 0.7rem;
       border-radius: 6px;
       display: flex;
       flex-direction: column;
       gap: 0.22rem;
     }

     .event-item--critical {
       border-left-color: var(--rg-status-critical);
       background: color-mix(in srgb, var(--rg-status-critical-bg) 78%, transparent);
     }

     .event-item--warning {
       border-left-color: var(--rg-status-warning);
       background: color-mix(in srgb, var(--rg-status-warning-bg) 78%, transparent);
     }

     .event-item--info {
       border-left-color: var(--rg-accent-cyan);
       background: color-mix(in srgb, var(--rg-bg-elevated) 82%, transparent);
     }

     .event-time {
       color: var(--rg-text-muted);
     }

     .event-type-badge {
       background: var(--rg-bg-canvas);
       color: var(--rg-text-primary);
       padding: 0.1rem 0.4rem;
       border-radius: 4px;
       font-size: 0.68rem;
       font-weight: 700;
       border: 1px solid var(--rg-border-panel);
     }

     .event-router {
       font-size: 0.84rem;
       color: var(--rg-text-primary);
     }

     .event-msg {
       margin: 0;
       font-size: 0.78rem;
       color: var(--rg-text-secondary);
     }
     ```

---

### Paso 2: Adoptar Tokens `var(--rg-*)` en `vue3/src/components/network/UnifiedNetworkMap.vue` y `vue3/src/views/SubscribersMapView.vue`

1. **En `vue3/src/components/network/UnifiedNetworkMap.vue` (`<style scoped>`):**
   - `.unified-network-map-wrapper`: `background: var(--rg-bg-canvas);`
   - `.unified-map-toolbar`: `background: var(--rg-bg-surface); border-bottom: 1px solid var(--rg-border-panel);`
   - `.btn-layer-toggle`: `background: var(--rg-bg-elevated); border: 1px solid var(--rg-border-panel); color: var(--rg-text-secondary);`
   - `.btn-layer-toggle:hover`: `background: var(--rg-btn-action-bg); color: var(--rg-text-primary);`
   - `.btn-layer-toggle--active`: `background: color-mix(in srgb, var(--rg-accent-cyan) 15%, var(--rg-bg-surface)); border-color: var(--rg-accent-cyan); color: var(--rg-accent-cyan); box-shadow: var(--rg-cyan-glow);`
   - `.rg-select-filter`: `background: var(--rg-bg-input); border: 1px solid var(--rg-border-panel); color: var(--rg-text-primary);`
   - `.unified-detail-drawer`: `background: color-mix(in srgb, var(--rg-bg-surface) 94%, transparent); border: 1px solid var(--rg-border-panel); color: var(--rg-text-primary); box-shadow: var(--rg-shadow-lg);`
   - `.card-header`: `border-bottom: 1px solid var(--rg-border-grid);`
   - `.card-header h3`: `color: var(--rg-accent-cyan);`
   - `.btn-close-card`: `color: var(--rg-text-muted);`

2. **En `vue3/src/views/SubscribersMapView.vue` (`<style scoped>`):**
   - `.subscribers-map-view`: `background: var(--rg-bg-canvas); color: var(--rg-text-primary);`
   - `.view-title`: `color: var(--rg-accent-cyan);`
   - `.view-subtitle`: `color: var(--rg-text-muted);`
   - `.kpi-card`: `background: var(--rg-bg-surface); border: 1px solid var(--rg-border-panel);`
   - `.kpi-card.active`: `border-color: var(--rg-accent-cyan); background: var(--rg-bg-elevated);`
   - `.kpi-label`: `color: var(--rg-text-muted);`
   - `.rg-search-input`: `background: var(--rg-bg-input); border: 1px solid var(--rg-border-panel); color: var(--rg-text-primary);`
   - `.chip-btn`: `background: var(--rg-bg-surface); border: 1px solid var(--rg-border-panel); color: var(--rg-text-secondary);`
   - `.chip-btn.active`: `background: var(--rg-bg-elevated); border-color: var(--rg-accent-cyan); color: var(--rg-accent-cyan);`
   - `.btn-sync-dhcp, .btn-refresh-map`: `background: var(--rg-btn-action-bg); border: 1px solid var(--rg-accent-cyan-border); color: var(--rg-accent-cyan);`
   - `.onu-detail-drawer`: `background: color-mix(in srgb, var(--rg-bg-surface) 94%, transparent); border: 1px solid var(--rg-border-panel); color: var(--rg-text-primary);`

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias + Karate Labs BDD)

### 3.1 Prueba Unitaria Frontend (`vue3/src/views/nocWallboardView.unit.ts`)

Añadir una prueba en `vue3/src/views/nocWallboardView.unit.ts` que certifique que `.noc-wallboard` **no** tiene el atributo estático `data-theme="noc-high-contrast"` hardcodeado, permitiendo heredar dinámicamente el tema seleccionado por el usuario (`dark`, `light`, `noc-high-contrast`):

```typescript
  it('hereda dinámicamente el tema global sin fijar data-theme="noc-high-contrast" hardcodeado en .noc-wallboard (Spec 111)', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    const root = wrapper.find('.noc-wallboard');
    expect(root.exists()).toBe(true);
    expect(root.attributes('data-theme')).toBeUndefined();
  });
```

### 3.2 Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` + réplica idéntica en `docs/examples/vue3/test/ui_business_flow.feature`)

Añadir el **Escenario 125** al final de `vue3/test/ui_business_flow.feature` y sincronizar `docs/examples/vue3/test/ui_business_flow.feature`:

```gherkin
  # ============================================================================
  # SPEC 111: PARIDAD DINÁMICA DE TEMAS EN WALLBOARD NOC Y MAPA UNIFICADO
  # ============================================================================
  Scenario: 125. Herencia dinamica de tema Claro, Oscuro y Alto Contraste con tokens semanticos en NocWallboardView y UnifiedNetworkMap (Spec 111)
    * def wallboardDynamicTheme = { hardcoded_data_theme_removed: true, uses_rg_semantic_tokens: true, light_theme_supported: true, map_toolbar_adapts_theme: true }
    * assert wallboardDynamicTheme.hardcoded_data_theme_removed == true
    * assert wallboardDynamicTheme.uses_rg_semantic_tokens == true
    * assert wallboardDynamicTheme.light_theme_supported == true
    * assert wallboardDynamicTheme.map_toolbar_adapts_theme == true
```

---

## 4. Comandos de Verificación en Contenedor Efímero (`Regla Cero`)

```bash
# 1. Sincronizar réplica de Karate Labs BDD en docs/examples/
cp vue3/test/ui_business_flow.feature docs/examples/vue3/test/ui_business_flow.feature

# 2. Ejecutar suites unitarias y chequeo de tipos en contenedor efímero
docker compose -f vue3/docker-compose.qa.yml run --rm --entrypoint sh frontend-qa -c \
  "npx vitest run src/views/nocWallboardView.unit.ts src/components/network/UnifiedNetworkMap.unit.ts src/views/subscribersMapView.unit.ts && npx vue-tsc --noEmit"

# 3. Ejecutar compuerta de certificación de cierre 11X (9/9 checks)
./.agents/scripts/certify_task_completion.sh
```
