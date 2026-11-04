# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 75: Eliminación de la Barra de Pestañas Redundante (`RouterWorkspaceTabsBar.vue`) en WebFig v7, Recuperación de Espacio Vertical (~50px) y Reubicación del Toggle Responsivo (`<= 1024px`) (Hito 28.18)

> **Estado:** APROBADO — LISTO PARA EJECUCIÓN POR **GEMINI 3.8 FLASH HIGH** (Blueprint Literal Paso a Paso)  
> **Hito Asociado:** Hito 28 (Subhito `28.18`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Componentes Afectados:**
> - **Frontend (`vue3/`):**
>   - [vue3/src/views/RouterWebFigLayout.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue) — Eliminación de `<RouterWorkspaceTabsBar />`, preservación intacta de `<keep-alive :max="5">` en `<router-view>`, e integración del botón responsivo `.btn-webfig-menu-inline` (`☰ Menú`, visible solo en `<= 1024px`) dentro de `.webfig-module-help-bar`.
>   - `vue3/src/components/webfig/RouterWorkspaceTabsBar.vue` — Eliminación física del archivo del componente (`git rm -f vue3/src/components/webfig/RouterWorkspaceTabsBar.vue`) para erradicar tanto la fila de pestañas en escritorio como la barra flotante inferior `.mobile-bottom-bar` (`position: fixed; bottom: 0`).
> - **Pruebas Unitarias y BDD Level-11X:**
>   - [vue3/src/views/webfigViews.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/webfigViews.unit.ts) — Eliminación del import de `RouterWorkspaceTabsBar.vue` y sustitución del test de pestañas por la prueba del toggle `.btn-webfig-menu-inline` y ausencia de `.webfig-tabs-bar` en `RouterWebFigLayout.vue`.
>   - [vue3/src/views/views.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/views.unit.ts) — Actualización del test en líneas 92–116 para validar `.btn-webfig-menu-inline` y la ausencia de `.webfig-tab` en `RouterWebFigLayout.vue`.
>   - [vue3/test/ui_business_flow.feature](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature) (+ réplicas en `docs/examples/vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature`) — Verificación de ausencia de `.webfig-tabs-bar` y presencia de `.btn-webfig-menu-inline` en `RouterWebFigLayout.vue`.

---

## 1. Diagnóstico Arquitectónico y de Experiencia de Usuario (UX / Refactoring UI)

Durante las pruebas operativas de usuario (UAT) sobre la consola **WebFig v7** (`/routers/:routerId/webfig/*`), se identificó que cada vez que el operador entra a un módulo (ej. `WireGuard VPN & Peers`), se apila una pestaña horizontal en [`RouterWorkspaceTabsBar.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/webfig/RouterWorkspaceTabsBar.vue) (`📊 Dashboard en Vivo | 🛡️ WireGuard VPN & Peers ×`):

1. **Redundancia de Navegación con `RouterSidebarMenu.vue` (`MÓDULOS WEBFIG V7`):**
   - El panel lateral izquierdo (`RouterSidebarMenu.vue`) permanece **siempre visible** en escritorio (`> 1024px`) y ya resalta en color cian (`.nav-item--active`) el módulo activo, permitiendo cambiar entre cualquiera de los módulos de Capa 1 y Capa 2 en un solo clic.
2. **Ruido Visual por Doble Barra de Pestañas:**
   - Casi todos los módulos de Capa 1 (`WireGuard`, `IP & DHCP`, `IPv6`, `Firewall`, `Routing`, `PPPoE & Queues`, `Tools`) cuentan con sus propias **sub-pestañas internas** (ej. `🛡️ Interfaces de Túnel | 👥 Peers & Claves Públicas`). Mantener `RouterWorkspaceTabsBar.vue` arriba genera dos barras de pestañas superpuestas que confunden la jerarquía visual.
3. **Desperdicio de ~50px Verticales + Barra Flotante Inferior en Móvil:**
   - `RouterWorkspaceTabsBar.vue` más el `gap: 12px` de `.webfig-console-layout` consume **~50px de altura útil** a todo lo ancho del viewport en escritorio, y en móvil (`<= 768px`) inyectaba además `.mobile-bottom-bar` (`position: fixed; bottom: 0; height: 56px`), contradiciendo la directiva **Anti-Sticky Footer**.
4. **Caché en Memoria (`<keep-alive :max="5">`) Independiente de la Barra Visual:**
   - En [`RouterWebFigLayout.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue#L201-L205), la retención en memoria RAM de los últimos 5 módulos visitados depende exclusivamente de:
     ```vue
     <router-view v-slot="{ Component }">
       <keep-alive :max="5">
         <component :is="Component" :key="route.name" />
       </keep-alive>
     </router-view>
     ```
   - Por tanto, eliminar `<RouterWorkspaceTabsBar />` **preserva al 100% la velocidad y caché en RAM** al cambiar de módulo desde el menú lateral.
5. **Preservación del Botón Responsivo `.btn-webfig-menu-inline` (`<= 1024px`):**
   - En tablets y móviles (`<= 1024px`), el menú lateral `RouterSidebarMenu.vue` se oculta en modo cajón (*drawer*). El botón `.btn-webfig-menu-inline` (`☰ Menú`) que abre dicho cajón residía dentro de `RouterWorkspaceTabsBar.vue`.
   - Al eliminar `RouterWorkspaceTabsBar.vue`, el botón `.btn-webfig-menu-inline` se reubica limpiamente en el extremo izquierdo de `.webfig-module-help-bar` dentro de [`RouterWebFigLayout.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue), permaneciendo oculto (`display: none`) en escritorio (`> 1024px`) y visible (`display: inline-flex`) en `<= 1024px`, sin ocupar una fila extra y cumpliendo con la invariante del Escenario 63 de Karate Labs UI (`waitFor(".btn-webfig-menu-inline")`).

---

## 2. Instrucciones Literales de Implementación (Paso a Paso para Gemini 3.8 Flash High)

### Paso 1: Actualizar `vue3/src/views/RouterWebFigLayout.vue`

1. En [vue3/src/views/RouterWebFigLayout.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue) (líneas 12–23), eliminar el import de `RouterWorkspaceTabsBar` e importar `useI18n`:

**Target (`vue3/src/views/RouterWebFigLayout.vue`):**
```ts
  import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
  import RouterWorkspaceTabsBar from '@/components/webfig/RouterWorkspaceTabsBar.vue';
  import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';
  import { useContextualHelp } from '@/composables/useContextualHelp';

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const liveTelemetryStore = useLiveTelemetryStore();
  const inventoryStore = useInventoryStore();
  const { openHelp, currentHelpEntry } = useContextualHelp();
```

**Replacement (`vue3/src/views/RouterWebFigLayout.vue`):**
```ts
  import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
  import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';
  import { useContextualHelp } from '@/composables/useContextualHelp';
  import { useI18n } from '@/composables/useI18n';

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const liveTelemetryStore = useLiveTelemetryStore();
  const inventoryStore = useInventoryStore();
  const { openHelp, currentHelpEntry } = useContextualHelp();
  const { t } = useI18n();
```

2. En el `<template>` de [vue3/src/views/RouterWebFigLayout.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue#L159-L209), eliminar `<RouterWorkspaceTabsBar ... />`, añadir la clase compatible `webfig-layout` al contenedor raíz y colocar el botón `.btn-webfig-menu-inline` dentro de `.webfig-module-help-bar`:

> **Nota de compatibilidad con Spec 74:** Si la **Spec 74** ya fue aplicada antes de ejecutar esta Spec, conserva la línea `<RgSafeModeBanner v-if="webFigStore.isSafeModeActive" :router-id="routerId" />` justo debajo de `<RouterContextHeader ... />`.

**Target (`vue3/src/views/RouterWebFigLayout.vue`):**
```vue
<template>
  <div class="webfig-console-layout">
    <!-- Cabecera de contexto del router -->
    <RouterContextHeader
      :router="currentRouter"
      :latest-telemetry="liveTelemetryStore.latestPoint"
      @toggle-safemode="handleToggleSafeMode"
    />

    <!-- Barra de pestañas con persistencia en RAM (KeepAlive) -->
    <RouterWorkspaceTabsBar
      :router-id="routerId"
      @toggle-sidebar="isMobileSidebarOpen = !isMobileSidebarOpen"
    />

    <!-- Contenido principal: Menú lateral + Router View con KeepAlive -->
    <div class="console-body">
      <RouterSidebarMenu
        :router-id="routerId"
        :is-open-mobile="isOpenMobileSidebar"
        @close-mobile="isMobileSidebarOpen = false"
      />
```
*(Nota: En el archivo actual la prop en línea 178 es `:is-open-mobile="isMobileSidebarOpen"` — reemplaza el bloque exacto de líneas 159–200 como se muestra abajo).*

**Target Exacto (`vue3/src/views/RouterWebFigLayout.vue` líneas 159–200):**
```vue
<template>
  <div class="webfig-console-layout">
    <!-- Cabecera de contexto del router -->
    <RouterContextHeader
      :router="currentRouter"
      :latest-telemetry="liveTelemetryStore.latestPoint"
      @toggle-safemode="handleToggleSafeMode"
    />

    <!-- Barra de pestañas con persistencia en RAM (KeepAlive) -->
    <RouterWorkspaceTabsBar
      :router-id="routerId"
      @toggle-sidebar="isMobileSidebarOpen = !isMobileSidebarOpen"
    />

    <!-- Contenido principal: Menú lateral + Router View con KeepAlive -->
    <div class="console-body">
      <RouterSidebarMenu
        :router-id="routerId"
        :is-open-mobile="isMobileSidebarOpen"
        @close-mobile="isMobileSidebarOpen = false"
      />

      <main
        id="webfig-main-view"
        class="console-view-container"
        role="main"
        aria-label="Módulo WebFig activo"
      >
        <div class="webfig-module-help-bar">
          <span class="webfig-module-help-title">{{ currentHelpEntry.title }}</span>
          <button
            id="btn-webfig-module-help"
            type="button"
            class="btn-webfig-module-help"
            aria-label="Abrir guía contextual de este módulo WebFig"
            @click="openHelp()"
          >
            ❓ Guía del Módulo
          </button>
        </div>
```

**Replacement (`vue3/src/views/RouterWebFigLayout.vue`):**
```vue
<template>
  <div class="webfig-console-layout webfig-layout">
    <!-- Cabecera de contexto del router -->
    <RouterContextHeader
      :router="currentRouter"
      :latest-telemetry="liveTelemetryStore.latestPoint"
      @toggle-safemode="handleToggleSafeMode"
    />

    <!-- Contenido principal: Menú lateral siempre visible en Desktop + Router View con KeepAlive -->
    <div class="console-body">
      <RouterSidebarMenu
        :router-id="routerId"
        :is-open-mobile="isMobileSidebarOpen"
        @close-mobile="isMobileSidebarOpen = false"
      />

      <main
        id="webfig-main-view"
        class="console-view-container"
        role="main"
        aria-label="Módulo WebFig activo"
      >
        <div class="webfig-module-help-bar">
          <div class="webfig-module-help-left">
            <button
              id="btn-webfig-menu-inline"
              type="button"
              class="btn-webfig-menu-inline"
              :aria-label="t('webfig.sidebar_title', 'Menú RouterOS')"
              @click="isMobileSidebarOpen = !isMobileSidebarOpen"
            >
              <span aria-hidden="true">☰</span>
              <span class="menu-inline-label">{{ t('webfig.tab_menu_short', 'Menú') }}</span>
            </button>
            <span class="webfig-module-help-title">{{ currentHelpEntry.title }}</span>
          </div>
          <button
            id="btn-webfig-module-help"
            type="button"
            class="btn-webfig-module-help"
            aria-label="Abrir guía contextual de este módulo WebFig"
            @click="openHelp()"
          >
            ❓ Guía del Módulo
          </button>
        </div>
```

3. En la sección `<style scoped>` de [vue3/src/views/RouterWebFigLayout.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue#L241-L285), añadir los estilos de `.webfig-module-help-left` y `.btn-webfig-menu-inline` (oculto en escritorio, visible en `<= 1024px`):

**Target (`vue3/src/views/RouterWebFigLayout.vue`):**
```css
  .webfig-module-help-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px dashed var(--rg-border-grid);
  }

  .webfig-module-help-title {
    font-size: 0.75rem;
    font-family: var(--rg-font-mono);
    color: var(--rg-text-muted);
  }
```

**Replacement (`vue3/src/views/RouterWebFigLayout.vue`):**
```css
  .webfig-module-help-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px dashed var(--rg-border-grid);
  }

  .webfig-module-help-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .btn-webfig-menu-inline {
    display: none;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
    border-radius: 5px;
    color: var(--rg-accent-cyan);
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    flex-shrink: 0;
  }

  @media (max-width: 1024px) {
    .btn-webfig-menu-inline {
      display: inline-flex;
    }
  }

  .webfig-module-help-title {
    font-size: 0.75rem;
    font-family: var(--rg-font-mono);
    color: var(--rg-text-muted);
  }
```

---

### Paso 2: Eliminar el Componente Obsoleto `vue3/src/components/webfig/RouterWorkspaceTabsBar.vue`

Para cumplir con la invariante de cero código muerto y con `.agents/scripts/verify_zero_orphan_vue_components.py`, eliminar el archivo `vue3/src/components/webfig/RouterWorkspaceTabsBar.vue`:

```bash
rm -f vue3/src/components/webfig/RouterWorkspaceTabsBar.vue
```

*(Nota: Los métodos `openOrFocusTab`, `closeTab` y `openRouterTabs` en `vue3/src/stores/useWebFigStore.ts` se conservan intactos como estado ligero del módulo activo para mantener 100% de compatibilidad con `router/index.ts` y `useWebFigStore.unit.ts`).*

---

### Paso 3: Actualizar las Suites Unitarias (`webfigViews.unit.ts` y `views.unit.ts`)

1. En [vue3/src/views/webfigViews.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/webfigViews.unit.ts#L10-L14), eliminar el import de `RouterWorkspaceTabsBar`:

**Target (`vue3/src/views/webfigViews.unit.ts`):**
```ts
import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
import RouterWorkspaceTabsBar from '@/components/webfig/RouterWorkspaceTabsBar.vue';
import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';
import RouterWebFigLayout from './RouterWebFigLayout.vue';
```

**Replacement (`vue3/src/views/webfigViews.unit.ts`):**
```ts
import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';
import RouterWebFigLayout from './RouterWebFigLayout.vue';
```

2. En [vue3/src/views/webfigViews.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/webfigViews.unit.ts#L143-L186), reemplazar el test `RouterWorkspaceTabsBar — cambia, cierra y navega pestañas móviles` por la prueba de ausencia de barra de pestañas y funcionamiento de `.btn-webfig-menu-inline` y `#btn-webfig-module-help` directamente en `RouterWebFigLayout.vue`:

**Target (`vue3/src/views/webfigViews.unit.ts`):**
```ts
  it('RouterWorkspaceTabsBar — cambia, cierra y navega pestañas móviles', async () => {
    const { useWebFigStore } = await import('@/stores/useWebFigStore');
    const store = useWebFigStore();
    store.openOrFocusTab({
      tabId: 'tab-1',
      routeName: 'InterfacesAndSfp',
      label: 'Interfaces & SFP',
      closable: true,
    });
    store.openOrFocusTab({
      tabId: 'tab-2',
      routeName: 'FirewallRules',
      label: 'Firewall Rules',
      closable: true,
    });

    const wrapper = mount(RouterWorkspaceTabsBar, {
      props: { routerId: 'r-01' },
    });

    const tabs = wrapper.findAll('.webfig-tab');
    expect(tabs.length).toBeGreaterThan(0);
    await tabs[0].trigger('click');
    await tabs[0].trigger('keydown.enter');

    // Cerrar pestaña
    const closeBtns = wrapper.findAll('.btn-close-tab');
    if (closeBtns.length > 0) {
      await closeBtns[0].trigger('click');
    }

    // Botones rápidos de móvil
    const mobileBtns = wrapper.findAll('.bottom-bar-btn');
    expect(mobileBtns.length).toBeGreaterThan(0);
    for (const btn of mobileBtns) {
      await btn.trigger('click');
    }

    // Botón inline de módulos WebFig para tablet/móvil (<= 1024px)
    const inlineMenuBtn = wrapper.find('.btn-webfig-menu-inline');
    expect(inlineMenuBtn.exists()).toBe(true);
    await inlineMenuBtn.trigger('click');
    expect(wrapper.emitted('toggle-sidebar')).toBeTruthy();
  });
```

**Replacement (`vue3/src/views/webfigViews.unit.ts`):**
```ts
  it('RouterWebFigLayout — omite barra de pestañas redundante y expone toggle .btn-webfig-menu-inline en cabecera de módulo', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: { id: 'r-01', display_name: 'r111', ros_identity: 'r111' },
      headers: new Headers(),
    });

    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });
    await flushPromises();

    // Verifica que la barra de pestañas redundante fue eliminada
    expect(wrapper.find('.webfig-tabs-bar').exists()).toBe(false);
    expect(wrapper.find('.webfig-tab').exists()).toBe(false);

    // Verifica que el botón inline de menú móvil/tablet (<= 1024px) está integrado en la barra del módulo
    const inlineMenuBtn = wrapper.find('.btn-webfig-menu-inline');
    expect(inlineMenuBtn.exists()).toBe(true);

    const sidebar = wrapper.findComponent(RouterSidebarMenu);
    expect(sidebar.props('isOpenMobile')).toBe(false);

    await inlineMenuBtn.trigger('click');
    expect(sidebar.props('isOpenMobile')).toBe(true);

    // Verifica botón de guía contextual del módulo
    const helpBtn = wrapper.find('#btn-webfig-module-help');
    expect(helpBtn.exists()).toBe(true);
    await helpBtn.trigger('click');
  });
```

3. En [vue3/src/views/views.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/views.unit.ts#L92-L116), reemplazar el test que buscaba `.webfig-tab` por la verificación del layout limpio sin pestañas y del toggle `.btn-webfig-menu-inline`:

**Target (`vue3/src/views/views.unit.ts`):**
```ts
  it('permite hacer click en pestañas y cerrarlas en RouterWebFigLayout', async () => {
    const { useWebFigStore } = await import('@/stores/useWebFigStore');
    const store = useWebFigStore();
    store.openOrFocusTab({
      tabId: 'test-closable-tab',
      routeName: 'InterfacesAndSfp',
      label: 'Interfaces',
      closable: true,
    });

    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });

    const tabs = wrapper.findAll('.webfig-tab');
    expect(tabs.length).toBeGreaterThan(1);
    await tabs[1].trigger('click');

    const closeBtn = wrapper.find('.btn-close-tab');
    if (closeBtn.exists()) {
      await closeBtn.trigger('click');
    }
  });
```

**Replacement (`vue3/src/views/views.unit.ts`):**
```ts
  it('renderiza RouterWebFigLayout sin barra de pestañas redundante y permite alternar el menú móvil inline', async () => {
    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });

    expect(wrapper.find('.webfig-tabs-bar').exists()).toBe(false);
    expect(wrapper.findAll('.webfig-tab').length).toBe(0);

    const inlineMenuBtn = wrapper.find('.btn-webfig-menu-inline');
    expect(inlineMenuBtn.exists()).toBe(true);
    await inlineMenuBtn.trigger('click');
  });
```

---

### Paso 4: Actualizar Escenario 63 en Karate Labs BDD (`vue3/test/ui_business_flow.feature` y réplicas en `docs/examples/`)

En [vue3/test/ui_business_flow.feature](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature#L607-L616) (y sus réplicas idénticas en `docs/examples/vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature`), añadir la aserción `!document.querySelector('.webfig-tabs-bar')` en el Escenario 63:

**Target (`vue3/test/ui_business_flow.feature`):**
```gherkin
  Scenario: 63. Responsive Design 11X — Shell Adaptativo, Tablas Desplazables (.table-wrapper) y Barra WebFig Inline
    Given driver baseUrl + '/inventory'
    And waitFor(".rg-shell")
    And waitFor("header.rg-header")
    And waitFor("nav.rg-rail")
    And waitFor(".rg-table-scroll.table-wrapper")
    When driver baseUrl + '/routers/r-01/webfig/live'
    And waitFor(".webfig-layout")
    And waitFor(".btn-webfig-menu-inline")
```

**Replacement (`vue3/test/ui_business_flow.feature`):**
```gherkin
  Scenario: 63. Responsive Design 11X — Shell Adaptativo, Tablas Desplazables (.table-wrapper) y Barra WebFig Inline
    Given driver baseUrl + '/inventory'
    And waitFor(".rg-shell")
    And waitFor("header.rg-header")
    And waitFor("nav.rg-rail")
    And waitFor(".rg-table-scroll.table-wrapper")
    When driver baseUrl + '/routers/r-01/webfig/live'
    And waitFor(".webfig-layout")
    And waitFor(".btn-webfig-menu-inline")
    And waitUntil("!document.querySelector('.webfig-tabs-bar')")
```

---

## 3. Verificación en Contenedores Efímeros (Regla Cero) y Reconstrucción Local

```bash
# 1. Verificar cero componentes Vue huérfanos y paridad de endpoints
python3 .agents/scripts/verify_zero_orphan_vue_components.py
python3 .agents/scripts/verify_no_orphan_api_endpoints.py

# 2. Ejecutar linter TypeScript y pruebas unitarias Vitest en contenedor efímero
docker compose -f vue3/docker-compose.qa.yml run --rm vue-qa sh -c "pnpm run type-check && npx vitest run src/views/webfigViews.unit.ts src/views/views.unit.ts"

# 3. Reconstruir imagen local-test de frontend y recrear contenedor local
docker build -t sinfallas/rosgrid-frontend:local-test ./vue3
docker compose -f docker-compose.prod.local.yml up -d
```
