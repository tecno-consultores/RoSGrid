# Especificación 107: Estabilidad Geométrica (`Zero Layout Shift`) en la Cabecera y Pestañas de `FirewallRulesView.vue` al Seleccionar `NAT` y Sincronización Bidireccional de `?proto=` en la URL

**Estado:** COMPLETADO y Certificado al 100% (`[x]` Hito 30.30)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Frontend (`vue3/src/views/FirewallRulesView.vue`, `vue3/src/views/webfigViews.unit.ts`) + Karate Labs BDD (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`)

---

## 1. Diagnóstico Forense de Causa Raíz

Al navegar a **Firewall (`FirewallRulesView.vue`)** en modo `IPv4 (/ip/firewall)` y hacer clic en la sub-pestaña **`NAT`**, toda la barra de sub-pestañas (`Filter Rules | NAT | Mangle | RAW | Address Lists | Connections`) salta bruscamente desde el extremo derecho de la segunda fila hacia el extremo izquierdo de una tercera fila inferior (*Cumulative Layout Shift*).

### ¿Por qué ocurre este salto geométrico?
1. En `vue3/src/views/FirewallRulesView.vue` (líneas 510–614 y 816–822), `<header class="view-header">` estaba definido como un único contenedor `display: flex; justify-content: space-between; flex-wrap: wrap;` con **4 hijos directos**:
   - `<div>` (Título + Subtítulo)
   - `<div class="proto-switcher">` (`IPv4` | `IPv6`)
   - `<div class="header-actions">` (`🔄 Refrescar`, `+ Nueva Regla`, `🔄 Reset Contadores` y, solo cuando `activeTab === 'nat' && activeProto === 'ip'`, los botones `🧙‍♂️ Masquerade` y `🧙‍♂️ Port Forwarding`)
   - `<nav class="subtabs-bar">` (`Filter Rules | NAT | Mangle | RAW | Address Lists | Connections`)
2. Cuando está activa `Filter Rules`, `.header-actions` tiene 3 botones y comparte la fila con `.subtabs-bar` (quedando `.subtabs-bar` a la derecha).
3. En el instante en que el usuario hace clic en **`NAT`**, se insertan 2 botones adicionales (`🧙‍♂️ Masquerade` y `🧙‍♂️ Port Forwarding`) dentro de `.header-actions` (a la izquierda de `.subtabs-bar`). Al ensancharse `.header-actions`, `.subtabs-bar` ya no cabe en la misma línea y `flex-wrap: wrap` la empuja a una tercera fila a la izquierda, moviendo las pestañas fuera del cursor del usuario.
4. Adicionalmente, `setProto(proto)` (línea 24) actualizaba `activeProto.value = proto` pero no sincronizaba `router.replace({ query: ... })`, dejando `?proto=ipv6` pegado en la barra de direcciones del navegador aun después de haber conmutado a `IPv4 (/ip/firewall)`.

---

## 2. Cambios Exactos Requeridos en Frontend (`vue3/src/views/FirewallRulesView.vue`)

### 2.1. Estructura Fija de 2 Filas (`.header-top-row` y `.header-controls-row`) con `.subtabs-bar` Anclada a la Izquierda

En `vue3/src/views/FirewallRulesView.vue` (líneas 510–614):
Reorganizar `<header class="view-header">` en **dos filas explícitas (`flex-direction: column`)**:
- **Fila 1 (`.header-top-row`):** Título/Subtítulo a la izquierda y `.proto-switcher` (`IPv4 (/ip/firewall)` | `IPv6 (/ipv6/firewall)`) a la derecha.
- **Fila 2 (`.header-controls-row`):**
  - **A la izquierda (posición fija invariable):** `<nav class="subtabs-bar">` (`Filter Rules | NAT | Mangle | RAW | Address Lists | Connections`). Al estar primera a la izquierda, jamás se desplaza ni salta de línea cuando aparecen o desaparecen los botones `🧙‍♂️ Masquerade` y `🧙‍♂️ Port Forwarding` a su derecha.
  - **A la derecha:** `<div class="header-actions">` con los botones de acción (`🧙‍♂️ Masquerade`, `🧙‍♂️ Port Forwarding`, `🔄 Refrescar`, `🔄 Reset Contadores` y el botón primario `+ Nueva Regla` al extremo derecho siguiendo Refactoring UI).

```html
    <header class="view-header">
      <div class="header-top-row">
        <div>
          <h2 class="view-title">
            Firewall RouterOS v7 & Filtrado de Paquetes ({{ activeProto === 'ipv6' ? 'IPv6' : 'IPv4' }})
          </h2>
          <p class="view-subtitle">
            Reglas ordenadas con protección Safe Mode (60s Rollback) y barras de tráfico en vivo
          </p>
        </div>

        <!-- Conmutador de Pila IPv4 / IPv6 -->
        <div class="proto-switcher" role="group" aria-label="Pila de protocolo de Firewall">
          <button
            id="btn-fw-proto-ip"
            type="button"
            class="btn-proto font-tabular"
            :class="{ 'btn-proto--active': activeProto === 'ip' }"
            :aria-pressed="activeProto === 'ip'"
            @click="setProto('ip')"
          >
            🌐 IPv4 (/ip/firewall)
          </button>
          <button
            id="btn-fw-proto-ipv6"
            type="button"
            class="btn-proto font-tabular"
            :class="{ 'btn-proto--active': activeProto === 'ipv6' }"
            :aria-pressed="activeProto === 'ipv6'"
            @click="setProto('ipv6')"
          >
            🌐 IPv6 (/ipv6/firewall)
          </button>
        </div>
      </div>

      <div class="header-controls-row">
        <!-- Pestañas de Tablas de Firewall (Fijas a la izquierda — Zero CLS) -->
        <nav class="subtabs-bar" role="tablist" aria-label="Tablas de Firewall">
          <button
            v-for="tab in [
              { id: 'filter', label: 'Filter Rules' },
              { id: 'nat', label: 'NAT' },
              { id: 'mangle', label: 'Mangle' },
              { id: 'raw', label: 'RAW' },
              { id: 'address-list', label: 'Address Lists' },
              { id: 'connections', label: 'Connections' },
            ]"
            :key="tab.id"
            type="button"
            class="btn-subtab"
            :class="{ 'btn-subtab--active': activeTab === tab.id }"
            role="tab"
            :aria-selected="activeTab === tab.id"
            @click="
              activeTab = tab.id as any;
              loadFirewallRules();
            "
          >
            {{ tab.label }}
          </button>
        </nav>

        <div class="header-actions">
          <button
            v-if="activeTab === 'nat' && activeProto === 'ip'"
            type="button"
            class="btn-wizard-action"
            @click="isMasqueradeWizardOpen = true"
          >
            🧙‍♂️ Masquerade
          </button>
          <button
            v-if="activeTab === 'nat' && activeProto === 'ip'"
            type="button"
            class="btn-wizard-action"
            @click="isPortForwardWizardOpen = true"
          >
            🧙‍♂️ Port Forwarding
          </button>
          <button
            id="btn-webfig-refresh"
            type="button"
            class="btn-secondary-action font-tabular"
            :disabled="isLoading"
            aria-label="Refrescar datos directamente desde el router MikroTik"
            @click="loadFirewallRules(true)"
          >
            {{ isLoading ? '🔄 Refrescando...' : '🔄 Refrescar' }}
          </button>
          <button
            type="button"
            class="btn-secondary-action"
            :disabled="isResetting"
            @click="handleResetCounters"
          >
            🔄 Reset Contadores
          </button>
          <button
            v-if="activeTab === 'filter' || activeTab === 'nat' || activeTab === 'mangle' || activeTab === 'raw' || activeTab === 'address-list'"
            type="button"
            class="btn-primary-action"
            @click="openCreateRuleModal"
          >
            {{ activeTab === 'address-list' ? '+ Agregar a Address-List' : '+ Nueva Regla' }}
          </button>
        </div>
      </div>
    </header>
```

### 2.2. Estilos CSS para `.view-header`, `.header-top-row` y `.header-controls-row`

En `vue3/src/views/FirewallRulesView.vue` (líneas 816–867):
```css
  .view-header {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .header-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .header-controls-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }

  .header-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-left: auto;
  }
```

### 2.3. Sincronización del Query Param `?proto=` en `setProto` (`vue3/src/views/FirewallRulesView.vue`)

En `vue3/src/views/FirewallRulesView.vue`:
1. Importar `useRouter` junto a `useRoute` desde `'vue-router'`, e inicializar `const router = useRouter();`.
2. En `setProto(proto: 'ip' | 'ipv6')`:
```ts
  function setProto(proto: 'ip' | 'ipv6') {
    if (activeProto.value === proto) return;
    activeProto.value = proto;
    try {
      const nextQuery = { ...((route as any)?.query || {}) };
      if (proto === 'ipv6') {
        nextQuery.proto = 'ipv6';
      } else {
        delete nextQuery.proto;
      }
      router?.replace?.({ query: nextQuery });
    } catch {
      // Ignorar en entornos de prueba sin router completo
    }
    loadFirewallRules();
  }
```

---

## 3. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

1. **Prueba Unitaria Frontend (`vue3/src/views/webfigViews.unit.ts`):**
   - Verificar que `.view-header` en `FirewallRulesView.vue` contiene `.header-top-row` y `.header-controls-row`, que `.subtabs-bar` precede a `.header-actions` dentro de `.header-controls-row` (garantizando posición fija a la izquierda al alternar entre `Filter Rules` y `NAT`), y que al conmutar `setProto('ip')` tras entrar con `?proto=ipv6` se limpia el query param `proto`.
2. **Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` Escenario 121 + `docs/examples/vue3/ui_business_flow.feature.example`):**
   - Añadir el **`Scenario: 121`** validando la estructura fija de 2 filas (`.header-top-row` + `.header-controls-row` con `.subtabs-bar` fija a la izquierda) en `FirewallRulesView.vue` y la sincronización de `?proto=` en la URL.

---

## 4. Criterios de Aceptación y Compuerta de Cierre (Level-11X Gate)

1. Al alternar entre `Filter Rules`, `NAT`, `Mangle`, `RAW`, `Address Lists` y `Connections` en `FirewallRulesView.vue`, la barra `.subtabs-bar` permanece anclada a la izquierda de `.header-controls-row` sin saltar de fila.
2. Al pulsar `🌐 IPv4 (/ip/firewall)` o `🌐 IPv6 (/ipv6/firewall)`, el query param `?proto=` de la URL se sincroniza inmediatamente.
3. Todas las suites unitarias y Karate Labs BDD pasan al 100% en contenedores efímeros (`Regla Cero`) y `./.agents/scripts/certify_task_completion.sh` aprueba las 9/9 compuertas.
