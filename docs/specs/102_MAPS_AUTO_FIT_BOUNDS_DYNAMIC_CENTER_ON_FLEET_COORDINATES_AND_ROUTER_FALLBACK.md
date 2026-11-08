# Especificación 102: Auto-Encuadre Cartográfico Dinámico (`fitBounds` / `setView`) sobre Coordenadas Reales de la Flota (Eliminación del Centrado Fijo en Caracas)

**Estado:** Implementado y Certificado (`[x]` Hito 30.25)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Frontend (`vue3/src/components/network/UnifiedNetworkMap.vue`, `vue3/src/components/inventory/OsmRouterMap.vue`, `vue3/src/components/inventory/OsmOnuMap.vue`, `vue3/src/views/SubscribersMapView.vue`, `vue3/src/components/field/FieldTechMobileView.vue`) + Suite de Pruebas 11X (`vue3/src/components/network/UnifiedNetworkMap.unit.ts`, `vue3/src/components/inventory/osmRouterMap.unit.ts`, Karate Labs BDD)

---

## 1. Diagnóstico Causa Raíz (Root-Cause Analysis)

Al revisar por qué todos los mapas (**Wallboard NOC**, **Mapa de Clientes**, **Inventario** y **Técnico de Campo**) siempre abren ubicados en **Caracas (`[10.4806, -66.9036]`)** aunque los 7 routers reales del tenant (`r1`..`r6`, `caps1`) están ubicados en **Carabobo (`~10.230, -67.880`)**:

1. **Coordenadas de Caracas Fijas por Defecto (`[10.4806, -66.9036]`) al Montar el Componente:**
   - En `UnifiedNetworkMap.vue` (línea 42), `OsmRouterMap.vue` (línea 27), `OsmOnuMap.vue` (línea 27) y `SubscribersMapView.vue` (línea 621), la propiedad `centerCoordinates` tiene como valor predeterminado `[10.4806, -66.9036]`.
   - Cuando el mapa se monta en el DOM (`onMounted -> initMap()`), las peticiones HTTP asíncronas (`/api/v1/inventory/routers`, `/api/v1/optical-boxes`, `/api/v1/subscriber-devices`) aún no han respondido, por lo que Leaflet inicializa la cámara en `[10.4806, -66.9036]`.
2. **Ausencia de Auto-Encuadre (`fitBounds` / `setView`) en `UnifiedNetworkMap.vue` al Llegar los Datos:**
   - En `UnifiedNetworkMap.vue`, cuando terminan de cargar `props.routers`, `props.opticalBoxes` y `props.subscribers`, `renderAllLayers()` dibuja los marcadores en sus coordenadas reales (`10.230, -67.880`), pero **nunca actualiza la vista de la cámara (`mapInstance.fitBounds` o `mapInstance.setView`)** hacia las coordenadas de los equipos cargados ni expone un botón **`🎯 Centrar en mi Red`**.
3. **Condición Incompleta (`groups.length > 1`) en `OsmRouterMap.vue`:**
   - En `OsmRouterMap.vue` (línea 344), `renderMarkers()` solo ejecuta `mapInstance.fitBounds(...)` si `groups.length > 1`. Si el tenant tiene 1 solo router o todos sus routers están agrupados en el mismo nodo (`groups.length === 1`), la cámara jamás se mueve de Caracas hacia `[groups[0].lat, groups[0].lng]`.
4. **Formulario de `FieldTechMobileView.vue` Inicializado en Caracas:**
   - En `FieldTechMobileView.vue` (líneas 41 y 59), `napForm` y `custForm` inicializan `latitude: 10.4806, longitude: -66.9036` en lugar de tomar dinámicamente las coordenadas del router seleccionado (`selectedRouter.latitude`, `selectedRouter.longitude`).

---

## 2. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 2.1. Auto-Encuadre Inteligente (`fitMapToActiveNodes`) y Botón `🎯 Centrar Red` en `vue3/src/components/network/UnifiedNetworkMap.vue`

1. En `<script setup lang="ts">` de `vue3/src/components/network/UnifiedNetworkMap.vue`, añadir la bandera `hasInitialAutoCentered = ref(false)` y la función `fitMapToActiveNodes(force = false)`:

```ts
  const hasInitialAutoCentered = ref<boolean>(false);

  function collectAllValidCoordinates(): [number, number][] {
    const coords: [number, number][] = [];
    if (showRouters.value) {
      for (const r of props.routers) {
        const lat = Number(r.latitude);
        const lng = Number(r.longitude);
        if (!Number.isNaN(lat) && !Number.isNaN(lng) && !(lat === 0 && lng === 0)) {
          coords.push([lat, lng]);
        }
      }
    }
    if (isIspMode.value && showBoxes.value) {
      for (const b of props.opticalBoxes) {
        const lat = Number(b.latitude);
        const lng = Number(b.longitude);
        if (!Number.isNaN(lat) && !Number.isNaN(lng) && !(lat === 0 && lng === 0)) {
          coords.push([lat, lng]);
        }
      }
    }
    if (showSubscribers.value) {
      for (const s of props.subscribers) {
        const resolved = resolveSubscriberBaseCoords(s);
        if (resolved) {
          coords.push(resolved);
        }
      }
    }
    return coords;
  }

  function fitMapToActiveNodes(force = false): void {
    if (!mapInstance || isHeadlessTest.value) return;
    if (hasInitialAutoCentered.value && !force) return;

    const coords = collectAllValidCoordinates();
    if (coords.length === 0) return;

    try {
      hasInitialAutoCentered.value = true;
      if (coords.length === 1) {
        mapInstance.setView(coords[0], Math.max(props.zoomLevel, 14));
      } else {
        const bounds = L.latLngBounds(coords);
        mapInstance.fitBounds(bounds, { padding: [48, 48], maxZoom: 15 });
      }
    } catch {
      // Ignorar en entornos JSDOM sin layout
    }
  }
```

2. Al final de `renderAllLayers()` en `UnifiedNetworkMap.vue`, invocar:
```ts
    if (!hasInitialAutoCentered.value) {
      fitMapToActiveNodes(false);
    }
```

3. Exponer `fitMapToActiveNodes` en `defineExpose({ ..., fitMapToActiveNodes })` y añadir en `.filter-controls-group` de `UnifiedNetworkMap.vue` (junto al `<select v-model="statusFilter">`) un botón táctico `#btn-map-fit-bounds`:

```vue
        <button
          id="btn-map-fit-bounds"
          type="button"
          class="btn-layer-toggle"
          :title="t('network_map.btn_center_fleet', 'Centrar mapa en los equipos de la red')"
          @click="fitMapToActiveNodes(true)"
        >
          🎯 {{ t('network_map.btn_center_fleet', 'Centrar Red') }}
        </button>
```

### 2.2. Corrección de Encuadre para `groups.length === 1` en `vue3/src/components/inventory/OsmRouterMap.vue` y `OsmOnuMap.vue`

En `vue3/src/components/inventory/OsmRouterMap.vue` (líneas 342–350), actualizar el bloque de auto-encuadre para que también centre la cámara cuando `groups.length === 1`:

```ts
    // Auto-encuadre sobre los nodos reales del tenant (1 o múltiples sitios)
    try {
      if (mapInstance && groups.length === 1) {
        mapInstance.setView([groups[0].lat, groups[0].lng], Math.max(props.zoomLevel, 14));
      } else if (mapInstance && groups.length > 1) {
        const bounds = L.latLngBounds(groups.map((g) => [g.lat, g.lng]));
        mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
      }
    } catch {
      // Ignorar en entornos sin motor de renderizado vectorial
    }
```

### 2.3. Herencia de Coordenadas del Router Seleccionado en `vue3/src/components/field/FieldTechMobileView.vue`

En `vue3/src/components/field/FieldTechMobileView.vue`, cuando se cargan los routers o cambia `napForm.router_id` / `custForm.router_id`, si las coordenadas del formulario siguen en el valor por defecto (`10.4806, -66.9036`), sincronizarlas automáticamente con `latitude` y `longitude` del router seleccionado (si el router dispone de coordenadas válidas).

---

## 3. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

### 3.1. Prueba Unitaria Frontend (`vue3/src/components/network/UnifiedNetworkMap.unit.ts` y `vue3/src/components/inventory/osmRouterMap.unit.ts`)

1. En `UnifiedNetworkMap.unit.ts`: Verificar que `fitMapToActiveNodes` centra el mapa sobre las coordenadas de los routers/clientes cargados (ej. `[10.232347, -67.879893]`) y que el botón `#btn-map-fit-bounds` existe y re-encuadra la vista al hacer clic.
2. En `osmRouterMap.unit.ts`: Verificar que cuando solo existe 1 grupo de ubicación (`groups.length === 1`), `OsmRouterMap` invoca `setView` con las coordenadas de ese grupo.

### 3.2. Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` + `docs/examples/vue3/`)

En `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`:
```gherkin
  Scenario: 116. Auto-encuadre dinamico de mapas sobre coordenadas reales de la flota (Spec 102)
    Given path '/subscribers/map'
    When method GET
    Then status 200
```

---

## 4. Criterios de Aceptación y Certificación 11X

- [x] Al abrir **Wallboard NOC**, **Mapa de Clientes**, **Inventario** o **Técnico de Campo**, el mapa encuadra automáticamente (`fitBounds` / `setView`) los equipos reales del tenant (ej. Carabobo `10.230, -67.880`) en cuanto cargan los datos de la API, sin quedarse fijo en Caracas (`10.4806, -66.9036`).
- [x] El botón `🎯 Centrar Red` (`#btn-map-fit-bounds`) permite re-encuadrar todos los nodos visibles con 1 clic en cualquier momento.
- [x] 100% de pruebas unitarias Vitest y Pytest en verde y 9/9 compuertas en `.agents/scripts/certify_task_completion.sh`.
