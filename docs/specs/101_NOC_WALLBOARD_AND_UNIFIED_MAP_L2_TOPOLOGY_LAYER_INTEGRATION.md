# Especificación 101: Integración de Topología Física Layer 2 (`━ Enlaces L2`) como Capa en `UnifiedNetworkMap.vue` y Vista Esquemática en `NocWallboardView.vue`

**Estado:** Implementado (`[x]` Hito 30.24)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Frontend (`vue3/src/components/network/UnifiedNetworkMap.vue`, `vue3/src/views/NocWallboardView.vue`, `vue3/src/components/common/RgResponsiveShell.vue`, `vue3/src/locales/es.json`, `vue3/src/locales/en.json`) + Suite de Pruebas 11X (`vue3/src/components/network/UnifiedNetworkMap.unit.ts`, `vue3/src/views/nocWallboardView.unit.ts`, Karate Labs BDD)

---

## 1. Propósito y Justificación Arquitectónica

La vista `Topología L2` (`/topology/l2`) ocupaba un ítem independiente en el menú principal izquierdo únicamente para mostrar las interconexiones MNDP/LLDP/CDP y PoE entre los routers de la flota.
Para optimizar la ergonomía operativa del NOC:
1. **Cuarta Capa Cartográfica `[ ━ Enlaces L2 (N) ]` (`#btn-layer-l2-links`) en `UnifiedNetworkMap.vue`:**
   - Justo al lado de los toggles `● Routers`, `■ Cajas NAP` y `▲ Clientes`, se incorpora el botón de capa **`━ Enlaces L2 (N)`**.
   - En el **Wallboard NOC** (`mode="wallboard"`), la capa `Enlaces L2` se activa **por defecto** (`showL2Links = ref<boolean>(props.mode === 'wallboard')`), dibujando sobre el mapa Leaflet las líneas (`L.polyline`) que interconectan geográficamente a los routers según `/api/v1/topology/l2` (en color dorado `#FACC15` cuando entregan energía PoE `⚡ W` y en cyan `#06B6D4` para enlaces troncales de datos).
   - Al hacer clic sobre un enlace L2 en el mapa, el drawer lateral muestra la tarjeta de detalle del enlace (Router/Interfaz origen ↔ Router/Interfaz destino, protocolo MNDP/LLDP y telemetría PoE-Out).
2. **Conmutador de Vista Esquemática L2 (`#btn-wallboard-toggle-l2-view`) en `NocWallboardView.vue`:**
   - Cuando varios routers están co-ubicados en el mismo rack o torre, el operador puede alternar en la cabecera del Wallboard NOC entre **`🗺️ Mapa Geográfico`** y **`🕸️ Grafo Esquemático L2`** (que renderiza `L2TopologyView` embebido dentro del panel izquierdo del Wallboard NOC sin salir de la pantalla 24/7).
3. **Simplificación del Menú Principal Izquierdo (`RgResponsiveShell.vue`):**
   - Se retira el ítem suelto `Topología L2` de `globalNavItems` en `RgResponsiveShell.vue` (conservando la ruta `/topology/l2` en `vue-router` por retrocompatibilidad).

---

## 2. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 2.1. Cuarto Toggle `#btn-layer-l2-links` y Trazado de Polilíneas L2 en `vue3/src/components/network/UnifiedNetworkMap.vue`

1. En `<script setup lang="ts">` de `vue3/src/components/network/UnifiedNetworkMap.vue`:
   - Importar `TopologyEdge`, `L2TopologyResponse` desde `@/types` y `http` desde `@/api/httpClient`.
   - Añadir el estado reactivo de la capa L2:
     ```ts
     const showL2Links = ref<boolean>(props.mode === 'wallboard');
     const l2Edges = ref<TopologyEdge[]>([]);
     const activeL2Edge = ref<TopologyEdge | null>(null);
     let l2LinksLayer: L.LayerGroup | null = null;

     async function loadL2TopologyEdges(): Promise<void> {
       try {
         const res = await http.get<L2TopologyResponse>('/api/v1/topology/l2');
         l2Edges.value = Array.isArray(res.data?.edges) ? res.data.edges : [];
         renderAllLayers();
       } catch {
         l2Edges.value = [];
       }
     }
     ```
   - En `initMap()`, inicializar `l2LinksLayer = L.layerGroup().addTo(mapInstance);` y llamar a `if (showL2Links.value) { loadL2TopologyEdges(); }`.
   - Añadir la función `toggleL2Links()`:
     ```ts
     async function toggleL2Links(): Promise<void> {
       showL2Links.value = !showL2Links.value;
       if (showL2Links.value && l2Edges.value.length === 0) {
         await loadL2TopologyEdges();
       } else {
         renderAllLayers();
       }
     }
     ```
   - En `renderAllLayers()`, limpiar `l2LinksLayer?.clearLayers()` y, cuando `showL2Links.value` sea `true`, trazar un `L.polyline` por cada `edge` en `l2Edges.value` cuyos routers origen y destino tengan coordenadas válidas:
     ```ts
     if (showL2Links.value && l2LinksLayer) {
       for (const edge of l2Edges.value) {
         const srcRouter = props.routers.find((r) => r.id === edge.source_router_id);
         const dstRouter = props.routers.find((r) => r.id === edge.target_router_id);
         if (!srcRouter || !dstRouter) continue;
         const lat1 = Number(srcRouter.latitude);
         const lng1 = Number(srcRouter.longitude);
         const lat2 = Number(dstRouter.latitude);
         const lng2 = Number(dstRouter.longitude);
         if (isNaN(lat1) || isNaN(lng1) || isNaN(lat2) || isNaN(lng2)) continue;

         const lineColor = edge.is_poe_delivering ? '#FACC15' : '#06B6D4';
         const poly = L.polyline(
           [
             [lat1, lng1],
             [lat2, lng2],
           ],
           {
             color: lineColor,
             weight: edge.is_poe_delivering ? 4 : 3,
             opacity: 0.9,
             dashArray: edge.is_poe_delivering ? undefined : '6, 6',
           },
         );
         poly.on('click', () => {
           activeL2Edge.value = edge;
           activeRouter.value = null;
           activeLocationGroup.value = null;
           activeBox.value = null;
           activeSubscriber.value = null;
         });
         l2LinksLayer.addLayer(poly);
       }
     }
     ```

2. En `<template>` de `vue3/src/components/network/UnifiedNetworkMap.vue` (dentro de `.layers-toggles-group`, líneas 689–726), añadir el cuarto botón `#btn-layer-l2-links`:

```vue
        <button
          id="btn-layer-l2-links"
          type="button"
          class="btn-layer-toggle btn-layer-l2"
          :class="{ 'btn-layer-toggle--active': showL2Links }"
          :aria-pressed="showL2Links ? 'true' : 'false'"
          @click="toggleL2Links"
        >
          <span class="icon shape-legend shape-legend--line" aria-hidden="true">━</span>
          <span class="label">{{ t('network_map.layer_l2_links', 'Enlaces L2') }}</span>
          <span class="counter">({{ l2Edges.length }})</span>
        </button>
```

3. En el drawer lateral `.unified-detail-drawer` (`v-if="activeRouter || activeLocationGroup || activeBox || activeSubscriber || activeL2Edge"`), añadir la tarjeta de detalle para `activeL2Edge`:

```vue
        <div v-if="activeL2Edge" class="drawer-card l2-edge-detail-card">
          <div class="card-header">
            <h3>🔗 Enlace Físico Capa 2 ({{ activeL2Edge.protocol }})</h3>
            <button type="button" class="btn-close-card" @click="activeL2Edge = null">✖</button>
          </div>
          <div class="card-body">
            <p><strong>Interfaz Origen:</strong> <code>{{ activeL2Edge.source_interface }}</code></p>
            <p><strong>Interfaz Destino:</strong> <code>{{ activeL2Edge.target_interface }}</code></p>
            <p>
              <strong>Alimentación PoE:</strong>
              <span v-if="activeL2Edge.is_poe_delivering">⚡ {{ activeL2Edge.poe_watts }}W ({{ activeL2Edge.poe_status }})</span>
              <span v-else>Solo Datos</span>
            </p>
          </div>
        </div>
```

### 2.2. Conmutador `🗺️ Mapa Geográfico` | `🕸️ Grafo L2 Esquemático` en `vue3/src/views/NocWallboardView.vue`

1. En `vue3/src/views/NocWallboardView.vue`, importar `L2TopologyView` desde `@/views/L2TopologyView.vue` y añadir `const showLogicalL2Graph = ref(false);`.
2. En `.wallboard-header-actions` (junto a `#btn-wallboard-refresh`), añadir el botón `#btn-wallboard-toggle-l2-view`:

```vue
        <button
          id="btn-wallboard-toggle-l2-view"
          type="button"
          class="btn-wallboard-refresh"
          @click="showLogicalL2Graph = !showLogicalL2Graph"
        >
          {{ showLogicalL2Graph ? t('wallboard.btn_geo_map', '🗺️ Mapa Geográfico') : t('wallboard.btn_l2_graph', '🕸️ Grafo L2 / PoE') }}
        </button>
```

3. En `<section class="wallboard-map-panel">`, alternar entre `<L2TopologyView v-if="showLogicalL2Graph" />` y `<UnifiedNetworkMap v-else ... />`.

### 2.3. Retiro del Ítem Suelto `Topología L2` del Menú Lateral en `vue3/src/components/common/RgResponsiveShell.vue`

En `vue3/src/components/common/RgResponsiveShell.vue` (líneas 231–238), retirar el bloque que inserta `name: 'L2Topology'` en `globalNavItems`, ya que la Topología L2 ahora vive integrada dentro del **Wallboard NOC** y como capa en `UnifiedNetworkMap.vue`.

---

## 3. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

### 3.1. Pruebas Unitarias Frontend (`vue3/src/components/network/UnifiedNetworkMap.unit.ts` y `vue3/src/views/nocWallboardView.unit.ts`)

1. En `UnifiedNetworkMap.unit.ts`: Verificar que `#btn-layer-l2-links` existe, que al activarlo consulta `/api/v1/topology/l2` y actualiza el contador de enlaces L2.
2. En `nocWallboardView.unit.ts`: Verificar que `#btn-wallboard-toggle-l2-view` alterna entre el mapa geográfico con capa L2 y el grafo esquemático L2 (`L2TopologyView`).

### 3.2. Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` + `docs/examples/vue3/`)

En `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`:
```gherkin
  Scenario: 115. Capa de Enlaces L2 integrada en el Mapa Unificado y Wallboard NOC (Spec 101)
    Given path '/noc-wallboard'
    When method GET
    Then status 200
```

---

## 4. Criterios de Aceptación y Certificación 11X

- [x] `UnifiedNetworkMap.vue` expone el cuarto botón de capa `#btn-layer-l2-links` (`━ Enlaces L2 (N)`), traza las polilíneas L2/PoE entre routers y abre el detalle del enlace al hacer clic.
- [x] `NocWallboardView.vue` activa la capa L2 por defecto y permite conmutar con `#btn-wallboard-toggle-l2-view` hacia el grafo esquemático L2/PoE sin salir del Wallboard.
- [x] El menú lateral principal (`RgResponsiveShell.vue`) ya no muestra `Topología L2` como sección separada.
- [x] 100% de suites Vitest y Pytest en verde y 9/9 compuertas en `.agents/scripts/certify_task_completion.sh`.
