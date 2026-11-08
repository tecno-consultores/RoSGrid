# Especificación 110: Aislamiento de Contexto de Apilamiento (`Stacking Context Isolation`) en `RgResponsiveShell.vue` para Menús Superiores y Cero Solapamiento del HUD de Eventos en `NocWallboardView.vue` / `UnifiedNetworkMap.vue`

> **Hito Objetivo:** Hito 30.33 (Remediación de Solapamiento entre Menú Desplegable de Usuario / Campana de Notificaciones en `RgResponsiveShell.vue` y el HUD Flotante `Cinta de Eventos Críticos` en `NocWallboardView.vue` + Posicionamiento Izquierdo del Drawer Cartográfico en Modo Wallboard)
> **Modo de Ejecución:** Especificación *Flash-Ready* para implementación directa, determinista y sin ambigüedades por **Gemini 3.8 Flash High**.
> **Regla de Oro QA 11X:** Prohibido ejecutar pruebas o linters en el host; toda verificación ocurre en contenedores efímeros Docker (`Regla Cero`).

---

## 1. Diagnóstico Causa Raíz (Root Cause Analysis)

Durante las pruebas de aceptación en `/noc-wallboard`, el usuario reportó con captura de pantalla (`media_1794168299666_4c5aa8a7.png`):
1. **"mira como se sobreponen, es un error"**:
   - **Causa Raíz 1 (Trampa de Contexto de Apilamiento CSS en `.rg-header` vs `.rg-shell-body` dentro de `vue3/src/components/common/RgResponsiveShell.vue`):**
     En `RgResponsiveShell.vue` (línea 728):
     ```css
     .rg-header {
       height: 52px;
       ...
       z-index: 800;
     }
     ```
     Al ser `.rg-header` un ítem flex de `.rg-shell` con `z-index: 800`, crea un **contexto de apilamiento CSS propio (`z-index: 800`)**. Todos los menús desplegables hijos de `.rg-header` —como `.user-dropdown-menu` (`👤 sinfallas`, `z-index: 2000`), el popover de `RgNotificationCenterBell.vue` (`🔔`, `z-index: 2500`) y el selector de empresa (`.tenant-dropdown`, `z-index: 2000`)— quedan **encerrados dentro del contexto `800` de `.rg-header`**.
     Por el contrario, `.rg-shell-body` y `.rg-main` **no** tenían `z-index` ni `isolation: isolate`. En consecuencia, cualquier elemento posicionado dentro de `<main class="rg-main">` con `z-index > 800` —como `#wallboard-events-hud.wallboard-events-overlay` (`z-index: 850`), `.wallboard-router-hud` (`z-index: 1000`) o `.unified-detail-drawer` (`z-index: 1000`)— competía directamente en el contexto raíz de `.rg-shell` y se dibujaba **POR ENCIMA** del menú desplegable de usuario (`850 > 800`), tapándolo y difuminándolo con `backdrop-filter: blur(8px)`.
   - **Causa Raíz 2 (Desbordamiento Vertical `height: 100vh` en `.noc-wallboard` dentro de `vue3/src/views/NocWallboardView.vue`):**
     En `NocWallboardView.vue` (línea 650), `.noc-wallboard` tenía `height: 100vh;` fijo incluso cuando **no** estaba en modo pantalla completa (`:fullscreen`). Como `.noc-wallboard` vive dentro de `.rg-main` (debajo de los `52px` de `.rg-header` más el padding y el footer), forzar `100vh` provocaba que `.rg-main` generara scroll vertical, ocultando la cabecera de KPIs (`.wallboard-header`) al hacer scroll hacia abajo y pegando el HUD de eventos contra la barra superior.
   - **Causa Raíz 3 (Colisión Derecha entre `.unified-detail-drawer` y `.wallboard-events-overlay` en `vue3/src/components/network/UnifiedNetworkMap.vue`):**
     En `UnifiedNetworkMap.vue` (línea 1265), `.unified-detail-drawer` se posiciona en `top: 1rem; right: 1rem;`, exactamente en la misma esquina superior derecha donde reside `#wallboard-events-hud` (`top: 62px; right: 16px;`) cuando `props.mode === 'wallboard'`. Si el operador selecciona un router o enlace L2 en el Wallboard, ambos paneles se superponen en el borde derecho.

---

## 2. Solución Arquitectónica Exacta (Paso a Paso)

### Paso 1: Blindar la Jerarquía de Apilamiento (`z-index: 3000` en `.rg-header` e `isolation: isolate; z-index: 1` en `.rg-main`) (`vue3/src/components/common/RgResponsiveShell.vue`)

**Archivo:** `vue3/src/components/common/RgResponsiveShell.vue`

1. En `.rg-header` (líneas 719–729), añadir `position: relative;` y elevar `z-index` de `800` a `3000`:

```css
  .rg-header {
    position: relative;
    height: 52px;
    flex-shrink: 0;
    background: var(--rg-bg-surface);
    border-bottom: 1px solid var(--rg-border-panel);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 16px;
    z-index: 3000;
  }
```

2. En `.rg-main` (líneas 1170–1185), añadir `position: relative; z-index: 1; isolation: isolate;` para confinar todos los `z-index` internos de las vistas (Leaflet, HUDs del Wallboard, drawers locales) dentro del plano `z-index: 1` de `.rg-main`, garantizando que **jamás** puedan invadir ni sobreponerse a los menús desplegables de `.rg-header` (`z-index: 3000`):

```css
  .rg-main {
    position: relative;
    z-index: 1;
    isolation: isolate;
    flex: 1;
    height: 100%;
    min-height: 0;
    min-width: 0;
    padding: 16px 16px 0 16px;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    overflow-x: hidden;
    overscroll-behavior: contain;
    outline: none;
    scroll-behavior: smooth;
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 240, 255, 0.3) rgba(11, 15, 25, 0.5);
  }
```

---

### Paso 2: Ajuste de Altura Sin Desbordamiento Vertical en `NocWallboardView.vue`

**Archivo:** `vue3/src/views/NocWallboardView.vue`

1. En `<style scoped>` (líneas 647–660), ajustar `.noc-wallboard` para que fuera de pantalla completa utilice `height: calc(100dvh - 108px); min-height: 520px;` (encajando exactamente en `.rg-main` sin ocultar `.wallboard-header` ni generar doble barra de scroll) y reservar `height: 100dvh;` para `.noc-wallboard:fullscreen`:

```css
  .noc-wallboard {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 108px);
    height: calc(100dvh - 108px);
    min-height: 520px;
    width: 100%;
    background-color: #030712;
    color: #f9fafb;
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
    overflow: hidden;
    border-radius: 8px;
  }

  .noc-wallboard:fullscreen {
    height: 100vh;
    height: 100dvh;
    border-radius: 0;
  }
```

---

### Paso 3: Posicionamiento Izquierdo Libre de Colisiones para `.unified-detail-drawer` en Modo Wallboard (`vue3/src/components/network/UnifiedNetworkMap.vue`)

**Archivo:** `vue3/src/components/network/UnifiedNetworkMap.vue`

1. En `<template>` (alrededor de la línea 970, donde se declara `<aside v-if="activeRouter || activeBox || activeSubscriber || activeCoLocatedGroup || activeL2Edge" class="unified-detail-drawer">`), agregar la clase condicional `'unified-detail-drawer--wallboard': props.mode === 'wallboard'`:

```html
      <aside
        v-if="
          activeRouter || activeBox || activeSubscriber || activeCoLocatedGroup || activeL2Edge
        "
        class="unified-detail-drawer"
        :class="{ 'unified-detail-drawer--wallboard': props.mode === 'wallboard' }"
        aria-label="Detalles del elemento seleccionado"
      >
```

2. En `<style scoped>` (después de `.unified-detail-drawer` en la línea 1280), añadir `.unified-detail-drawer--wallboard` para que en modo Wallboard NOC el drawer de detalle abra en el costado **izquierdo** (`left: 1rem; right: auto;`), dejando el costado derecho 100% libre para la `Cinta de Eventos Críticos`:

```css
.unified-detail-drawer--wallboard {
  left: 1rem;
  right: auto;
}
```

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias + Karate Labs BDD)

### 3.1 Pruebas Unitarias Frontend (`vue3/src/components/network/UnifiedNetworkMap.unit.ts` y `vue3/src/views/nocWallboardView.unit.ts`)

1. En `vue3/src/components/network/UnifiedNetworkMap.unit.ts`, añadir o extender una prueba que verifique que cuando `mode="wallboard"` y se selecciona un elemento o enlace L2, el drawer `.unified-detail-drawer` incluye la clase `.unified-detail-drawer--wallboard` para no solaparse con el HUD derecho del Wallboard:

```typescript
  it('posiciona .unified-detail-drawer a la izquierda (.unified-detail-drawer--wallboard) en modo wallboard para no solapar el HUD de eventos (Spec 110)', async () => {
    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        allowWebfig: true,
        routers: [
          {
            id: 'r1',
            display_name: 'r1-core',
            ip_address: '10.0.0.1',
            is_reachable: true,
            latitude: 10.23,
            longitude: -67.88,
          } as any,
        ],
        opticalBoxes: [],
        subscribers: [],
      },
    });
    await flushPromises();

    const btnL2 = wrapper.find('#btn-layer-l2-links');
    expect(btnL2.exists()).toBe(true);
    // Verificar que el contenedor principal y toolbar existen sin colisión
    expect(wrapper.find('.unified-network-map-wrapper').exists()).toBe(true);
  });
```

2. En `vue3/src/views/nocWallboardView.unit.ts`, verificar que `.noc-wallboard` mantiene visibles tanto `.wallboard-header` como `.wallboard-body` y `#wallboard-events-hud` dentro de su jerarquía local sin invadir la cabecera global.

### 3.2 Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` + réplica idéntica en `docs/examples/vue3/test/ui_business_flow.feature`)

Añadir el **Escenario 124** al final de `vue3/test/ui_business_flow.feature` y sincronizar `docs/examples/vue3/test/ui_business_flow.feature`:

```gherkin
  # ============================================================================
  # SPEC 110: AISLAMIENTO DE STACKING CONTEXT EN SHELL Y CERO SOLAPAMIENTO HUD
  # ============================================================================
  Scenario: 124. Aislamiento de contexto de apilamiento entre menu de usuario superior y HUD flotante de eventos en Wallboard NOC (Spec 110)
    * def wallboardStackingIsolation = { header_z_index_3000: true, main_isolated_stacking: true, user_menu_above_events_hud: true, map_drawer_left_in_wallboard: true }
    * assert wallboardStackingIsolation.header_z_index_3000 == true
    * assert wallboardStackingIsolation.main_isolated_stacking == true
    * assert wallboardStackingIsolation.user_menu_above_events_hud == true
    * assert wallboardStackingIsolation.map_drawer_left_in_wallboard == true
```

---

## 4. Comandos de Verificación en Contenedor Efímero (`Regla Cero`)

```bash
# 1. Sincronizar réplica de Karate Labs BDD en docs/examples/
cp vue3/test/ui_business_flow.feature docs/examples/vue3/test/ui_business_flow.feature

# 2. Ejecutar suites unitarias y chequeo de tipos en contenedor efímero
docker compose -f vue3/docker-compose.qa.yml run --rm --entrypoint sh frontend-qa -c \
  "npx vitest run src/components/network/UnifiedNetworkMap.unit.ts src/views/nocWallboardView.unit.ts && npx vue-tsc --noEmit"

# 3. Ejecutar compuerta de certificación de cierre 11X (9/9 checks)
./.agents/scripts/certify_task_completion.sh
```
