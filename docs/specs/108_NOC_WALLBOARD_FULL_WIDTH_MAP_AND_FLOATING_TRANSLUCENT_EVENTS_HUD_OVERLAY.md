# Especificación 108: Mapa / Grafo L2 al 100% del Lienzo y Cinta de Eventos Críticos como HUD Flotante Semitransparente (*Stream Overlay*) en `NocWallboardView.vue`

**Estado:** Completado (`[x]` Hito 30.31)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Frontend (`vue3/src/views/NocWallboardView.vue`, `vue3/src/views/nocWallboardView.unit.ts`, `vue3/src/views/views.unit.ts`) + Karate Labs BDD (`vue3/test/ui_business_flow.feature` Escenario 122 y `docs/examples/vue3/ui_business_flow.feature.example`)

---

## 1. Propósito y Justificación Arquitectónica

En **`NocWallboardView.vue` (`/wallboard`)**, el cuerpo principal (`.wallboard-body`) dividía la pantalla en dos columnas rígidas (`grid-template-columns: 55% 45%`), haciendo que la lista de eventos ocupara casi la mitad del televisor o monitor con un fondo negro opaco (`#090d16`), y reduciendo el Mapa Geográfico / Grafo L2 a solo el `55%` del espacio disponible.

Siguiendo el patrón de **HUD Flotante Semitransparente (*Stream Overlay*)**:
1. **Lienzo al 100% (`width: 100%; height: 100%`):** El Mapa Geográfico (`UnifiedNetworkMap.vue`) o el Grafo L2 (`L2TopologyView.vue`) pasa a ocupar el **100% del ancho y alto** de `.wallboard-body`.
2. **Cinta de Eventos Críticos Flotante a la Derecha con Fondo Semitransparente Oscuro (`.wallboard-events-overlay`):**
   - Flota sobre el costado derecho del mapa (`position: absolute; top: 62px; right: 16px; bottom: 16px; width: 370px; z-index: 850;`), justo debajo de la barra superior de controles del mapa (`Todos los Estados` / `🎯 Centrar Red`) para no tapar ningún botón de filtro.
   - Utiliza un fondo oscuro **semitransparente** (no completamente transparente): `background: rgba(3, 7, 18, 0.72)` con `backdrop-filter: blur(8px)`, y cada evento individual (`.event-item`) utiliza una cápsula semitransparente (`background: rgba(15, 23, 42, 0.78)`) con textos blancos/cian de alto contraste (`#f8fafc` / `#e2e8f0`) para preservar legibilidad WCAG 2.1 AA mientras deja ver el mapa detrás.
3. **Control Táctico para Minimizar / Expandir el HUD (`#btn-wallboard-toggle-events-hud` / `#btn-wallboard-expand-events-hud`):**
   - Permite contraer el HUD flotante en una píldora compacta (`📡 Eventos en Vivo (N)`) en la esquina superior derecha cuando el operador desea despejar por completo el extremo derecho del mapa, o volver a desplegarlo con 1 clic.

---

## 2. Cambios Exactos Requeridos en `vue3/src/views/NocWallboardView.vue`

### 2.1. Estado Reactivo `isEventsHudCollapsed` en `<script setup lang="ts">`

En `vue3/src/views/NocWallboardView.vue`:
- Declarar:
```ts
  const isEventsHudCollapsed = ref<boolean>(false);
```

### 2.2. Template de `.wallboard-body` y HUD Flotante Semitransparente (`.wallboard-events-overlay`)

En `vue3/src/views/NocWallboardView.vue` (líneas 519–609), actualizar `.wallboard-body` para que `.wallboard-map-panel` ocupe el 100% del área y `.wallboard-events-panel` flote sobre el costado derecho con soporte de minimizado/expandido:

```html
    <!-- Lienzo 100% (Mapa OSM / Grafo L2) + HUD Flotante Semitransparente de Eventos a la Derecha -->
    <div class="wallboard-body">
      <section class="wallboard-map-panel" aria-label="Mapa de routers de la flota">
        <L2TopologyView v-if="showLogicalL2Graph" />
        <UnifiedNetworkMap
          v-else
          :mode="'wallboard'"
          :allow-webfig="true"
          :routers="routers"
          :optical-boxes="opticalBoxes"
          :subscribers="subscribers"
          :selected-id="selectedRouterId"
          :zoom-level="12"
          @select-router="handleSelectRouter"
        />

        <!-- Floating HUD de equipo seleccionado con botón directo a WebFig -->
        <transition name="hud-fade">
          <div
            v-if="selectedRouter"
            class="wallboard-router-hud"
            :class="{ 'wallboard-router-hud--shifted': !isEventsHudCollapsed }"
            role="region"
            aria-label="Detalle de router seleccionado"
          >
            <div class="hud-left">
              <span
                class="hud-dot"
                :class="selectedRouter.is_reachable ? 'hud-dot--online' : 'hud-dot--offline'"
              ></span>
              <div class="hud-text">
                <div class="hud-title font-mono">{{ selectedRouter.display_name }}</div>
                <div class="hud-meta">
                  <code>{{ selectedRouter.ip_address }}</code> |
                  <span class="badge-role">{{ selectedRouter.network_role || 'GENERAL' }}</span> |
                  <span>v{{ selectedRouter.ros_version }}</span>
                </div>
              </div>
            </div>
            <div class="hud-actions">
              <button
                id="btn-wallboard-open-webfig"
                type="button"
                class="btn-hud-webfig"
                @click="handleOpenWebFig(selectedRouter.id)"
              >
                📊 Abrir WebFig →
              </button>
              <button
                type="button"
                class="btn-hud-close"
                title="Cerrar detalle"
                aria-label="Cerrar detalle"
                @click="selectedRouterId = null"
              >
                ✕
              </button>
            </div>
          </div>
        </transition>
      </section>

      <!-- Píldora Flotante cuando el HUD de Eventos está minimizado -->
      <button
        v-if="isEventsHudCollapsed"
        id="btn-wallboard-expand-events-hud"
        type="button"
        class="btn-events-hud-pill font-mono"
        aria-label="Mostrar cinta de eventos críticos"
        @click="isEventsHudCollapsed = false"
      >
        📡 Eventos en Vivo ({{ liveEvents.length }})
      </button>

      <!-- HUD Flotante Semitransparente Derecha: Cinta de Eventos Críticos en Vivo -->
      <section
        v-else
        id="wallboard-events-hud"
        class="wallboard-events-panel wallboard-events-overlay"
        aria-labelledby="events-panel-title"
      >
        <div class="events-header">
          <div class="events-header-left">
            <span class="events-live-dot" aria-hidden="true"></span>
            <h2 id="events-panel-title" class="events-title">
              Cinta de Eventos Críticos
            </h2>
            <span class="events-count-pill font-mono">{{ liveEvents.length }}</span>
          </div>
          <button
            id="btn-wallboard-toggle-events-hud"
            type="button"
            class="btn-collapse-events-hud"
            title="Minimizar panel de eventos"
            aria-label="Minimizar panel de eventos"
            @click="isEventsHudCollapsed = true"
          >
            ─
          </button>
        </div>

        <div v-if="liveEvents.length === 0" class="events-empty-state">
          <p>No se registran eventos críticos recientes en la flota.</p>
        </div>
        <ul v-else class="events-list" role="log" aria-live="polite">
          <li
            v-for="evt in liveEvents"
            :key="evt.id"
            class="event-item"
            :class="`event-item--${evt.severity}`"
          >
            <div class="event-meta">
              <span class="event-time font-mono">{{ evt.timestamp }}</span>
              <span class="event-type-badge font-mono">{{ getBadgeLabel(evt.type) }}</span>
            </div>
            <div class="event-body">
              <strong class="event-router">{{ evt.router_identity }}</strong>
              <p class="event-msg">{{ evt.message }}</p>
            </div>
          </li>
        </ul>
      </section>
    </div>
```

### 2.3. Estilos CSS Semitransparentes Calibrados (`vue3/src/views/NocWallboardView.vue`)

Reemplazar los estilos de `.wallboard-body`, `.wallboard-map-panel`, `.wallboard-router-hud` y `.wallboard-events-panel` (líneas 882–1140) por:

```css
  /* Cuerpo 100% Lienzo con HUD Flotante */
  .wallboard-body {
    position: relative;
    display: flex;
    flex: 1;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .wallboard-map-panel {
    position: relative;
    flex: 1;
    height: 100%;
    width: 100%;
  }

  /* Floating HUD de Router Seleccionado en Wallboard */
  .wallboard-router-hud {
    position: absolute;
    bottom: 1.25rem;
    left: 1.25rem;
    right: 1.25rem;
    background: rgba(11, 15, 25, 0.92);
    backdrop-filter: blur(8px);
    border: 1px solid #0284c7;
    border-radius: 8px;
    padding: 0.75rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    z-index: 1000;
    box-shadow:
      0 10px 25px -5px rgba(0, 0, 0, 0.7),
      0 0 15px rgba(2, 132, 199, 0.3);
    transition: right 0.2s ease;
  }

  .wallboard-router-hud--shifted {
    right: 400px;
  }

  @media (max-width: 1024px) {
    .wallboard-router-hud--shifted {
      right: 1.25rem;
    }
  }

  .wallboard-events-overlay {
    position: absolute;
    top: 62px;
    right: 16px;
    bottom: 16px;
    width: 370px;
    max-width: calc(100vw - 32px);
    display: flex;
    flex-direction: column;
    background: rgba(3, 7, 18, 0.72);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 12px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.65);
    overflow: hidden;
    z-index: 850;
  }

  .btn-events-hud-pill {
    position: absolute;
    top: 62px;
    right: 16px;
    z-index: 850;
    background: rgba(3, 7, 18, 0.82);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(56, 189, 248, 0.45);
    color: #38bdf8;
    padding: 0.45rem 0.9rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.55);
    transition: all 0.15s ease;
  }

  .btn-events-hud-pill:hover {
    background: rgba(15, 23, 42, 0.92);
    color: #ffffff;
    border-color: #38bdf8;
  }

  .events-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.65rem 0.9rem;
    background: rgba(15, 23, 42, 0.78);
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
  }

  .events-header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .events-live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
    box-shadow: 0 0 8px #ef4444;
  }

  .events-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
  }

  .events-count-pill {
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 999px;
    padding: 0.05rem 0.45rem;
    font-size: 0.72rem;
    font-weight: 700;
  }

  .btn-collapse-events-hud {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #cbd5e1;
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

  .btn-collapse-events-hud:hover {
    background: rgba(56, 189, 248, 0.2);
    color: #ffffff;
    border-color: #38bdf8;
  }

  .events-empty-state {
    padding: 1.25rem;
    color: #cbd5e1;
    font-size: 0.85rem;
    text-align: center;
  }

  .events-list {
    list-style: none;
    margin: 0;
    padding: 0.55rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    flex: 1;
  }

  .event-item {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: 4px solid #38bdf8;
    padding: 0.5rem 0.7rem;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    gap: 0.22rem;
  }

  .event-item--critical {
    border-left-color: #ef4444;
    background: rgba(69, 10, 10, 0.76);
  }

  .event-item--warning {
    border-left-color: #facc15;
    background: rgba(66, 32, 6, 0.76);
  }

  .event-item--info {
    border-left-color: #38bdf8;
    background: rgba(15, 23, 42, 0.78);
  }

  .event-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.73rem;
  }

  .event-time {
    color: #cbd5e1;
  }

  .event-type-badge {
    background: rgba(3, 7, 18, 0.75);
    color: #f8fafc;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .event-body {
    display: flex;
    flex-direction: column;
  }

  .event-router {
    font-size: 0.84rem;
    color: #ffffff;
  }

  .event-msg {
    margin: 0;
    font-size: 0.78rem;
    color: #e2e8f0;
  }
```

---

## 3. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

1. **Prueba Unitaria Frontend (`vue3/src/views/nocWallboardView.unit.ts`):**
   - Verificar que `#wallboard-events-hud` tiene la clase `.wallboard-events-overlay` flotando sobre `.wallboard-body`, que al hacer clic en `#btn-wallboard-toggle-events-hud` se contrae mostrando la píldora `#btn-wallboard-expand-events-hud`, y que al pulsar la píldora vuelve a desplegarse `#wallboard-events-hud`.
2. **Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` Escenario 122 + `docs/examples/vue3/ui_business_flow.feature.example`):**
   - Añadir el **`Scenario: 122`** validando el contrato del HUD flotante semitransparente (`.wallboard-events-overlay`, `#btn-wallboard-toggle-events-hud` y `#btn-wallboard-expand-events-hud`) sobre el lienzo al 100% en `NocWallboardView.vue`.

---

## 4. Criterios de Aceptación y Compuerta de Cierre (Level-11X Gate)

1. En `NocWallboardView.vue`, el mapa (`UnifiedNetworkMap.vue`) y el grafo L2 (`L2TopologyView.vue`) ocupan el 100% del ancho de `.wallboard-body`.
2. La Cinta de Eventos Críticos flota en el lado derecho (`.wallboard-events-overlay`) con fondo semitransparente oscuro (`rgba(3, 7, 18, 0.72)` + `backdrop-filter: blur(8px)`) y cápsulas semitransparentes legibles (`rgba(15, 23, 42, 0.78)`), pudiendo minimizarse y restaurarse con 1 clic.
3. Todas las suites unitarias y Karate Labs BDD pasan al 100% en contenedores efímeros (`Regla Cero`) y `./.agents/scripts/certify_task_completion.sh` aprueba las 9/9 compuertas.
