<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type { RouterItem } from '@/types';

  interface LocationGroup {
    lat: number;
    lng: number;
    routers: RouterItem[];
  }

  const props = withDefaults(
    defineProps<{
      routers: RouterItem[];
      selectedRouterId?: string | null;
      enableCoordinatePicker?: boolean;
      centerCoordinates?: [number, number];
      zoomLevel?: number;
    }>(),
    {
      selectedRouterId: null,
      enableCoordinatePicker: false,
      centerCoordinates: () => [10.4806, -66.9036], // Caracas por defecto
      zoomLevel: 12,
    },
  );

  const emit = defineEmits<{
    (e: 'select-router', routerId: string): void;
    (e: 'open-webfig', routerId: string): void;
    (e: 'coordinates-selected', coords: { lat: number; lng: number }): void;
  }>();

  const isHeadlessTest = computed(() => typeof navigator !== 'undefined' && Boolean((navigator as any).webdriver));
  const mapContainer = ref<HTMLDivElement | null>(null);
  let mapInstance: L.Map | null = null;
  let markersLayer: L.LayerGroup | null = null;
  let spiderLayer: L.LayerGroup | null = null;
  let resizeObserver: ResizeObserver | null = null;

  function getStatusColor(router: RouterItem): string {
    if (router.admin_state === 'MAINTENANCE') return '#38BDF8';
    if (!router.is_reachable || router.ssl_trust_status === 'FINGERPRINT_MISMATCH') {
      return '#EF4444';
    }
    return '#22C55E';
  }

  function getGroupStatusColor(routers: RouterItem[]): string {
    if (routers.some((r) => !r.is_reachable || r.ssl_trust_status === 'FINGERPRINT_MISMATCH')) {
      return '#EF4444';
    }
    if (routers.some((r) => r.admin_state === 'MAINTENANCE')) {
      return '#38BDF8';
    }
    return '#22C55E';
  }

  function createRouterIcon(color: string, label: string): L.DivIcon {
    return L.divIcon({
      className: 'rg-map-pin-container',
      html: `
        <div class="rg-map-pin" style="--pin-color: ${color};" role="button" tabindex="0" aria-label="Router ${label}">
          <div class="pin-pulse"></div>
          <div class="pin-dot"></div>
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });
  }

  function createMultiRouterIcon(color: string, routers: RouterItem[]): L.DivIcon {
    const count = routers.length;
    const label = routers.map((r) => r.display_name).join(', ');
    return L.divIcon({
      className: 'rg-map-pin-container',
      html: `
        <div class="rg-map-pin rg-map-pin--multi" style="--pin-color: ${color};" role="button" tabindex="0" aria-label="Sitio con ${count} routers: ${label}">
          <div class="pin-pulse pin-pulse--multi"></div>
          <div class="pin-dot pin-dot--multi">
            <span class="pin-count-badge">${count}</span>
          </div>
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
  }

  function createSingleRouterPopup(r: RouterItem): HTMLElement {
    const popupContent = document.createElement('div');
    popupContent.className = 'rg-map-popup';
    popupContent.innerHTML = `
      <div class="popup-title"><strong>${r.display_name}</strong></div>
      <div class="popup-identity">Identity: <code>${r.ros_identity || r.display_name}</code></div>
      <div class="popup-role">Rol: <span class="badge-role">${r.network_role || 'GENERAL'}</span></div>
      <div class="popup-meta">IP: <code>${r.ip_address}</code> | v${r.ros_version || '7.x'}</div>
      <div class="popup-actions">
        <button type="button" class="btn-popup-webfig" data-router-id="${r.id}">
          Abrir WebFig →
        </button>
      </div>
    `;

    L.DomEvent.disableClickPropagation(popupContent);
    const webfigBtn = popupContent.querySelector('.btn-popup-webfig') as HTMLButtonElement | null;
    if (webfigBtn) {
      L.DomEvent.disableClickPropagation(webfigBtn);
      L.DomEvent.on(webfigBtn, 'click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        L.DomEvent.preventDefault(ev);
        emit('open-webfig', r.id);
      });
    }

    return popupContent;
  }

  function createMultiRouterPopup(grp: LocationGroup): HTMLElement {
    const popupContent = document.createElement('div');
    popupContent.className = 'rg-map-popup rg-map-popup--multi';

    const itemsHtml = grp.routers
      .map((r) => {
        const color = getStatusColor(r);
        const stateText = !r.is_reachable
          ? 'Desconectado'
          : r.admin_state === 'MAINTENANCE'
            ? 'Mantenimiento'
            : 'Operativo';

        return `
          <div class="popup-router-item" data-router-id="${r.id}">
            <div class="router-item-header">
              <span class="status-indicator" style="background-color: ${color};" title="${stateText}"></span>
              <strong class="router-item-name" title="${r.display_name}">${r.display_name}</strong>
              <span class="badge-role">${r.network_role || 'GENERAL'}</span>
            </div>
            <div class="router-item-details">
              <div>Identity: <code>${r.ros_identity || r.display_name}</code></div>
              <div>IP: <code>${r.ip_address}</code> | v${r.ros_version || '7.x'}</div>
            </div>
            <div class="router-item-actions">
              <button type="button" class="btn-popup-select" data-router-id="${r.id}">
                🔍 Seleccionar
              </button>
              <button type="button" class="btn-popup-webfig" data-router-id="${r.id}">
                ⚡ WebFig →
              </button>
            </div>
          </div>
        `;
      })
      .join('');

    popupContent.innerHTML = `
      <div class="popup-site-header">
        <div class="site-badge">🏢 SITIO / NODO COMPARTIDO</div>
        <div class="site-title">${grp.routers.length} Routers en la misma ubicación</div>
        <div class="site-coords"><code>${Number(grp.lat).toFixed(5)}, ${Number(grp.lng).toFixed(5)}</code></div>
      </div>
      <div class="popup-routers-list">
        ${itemsHtml}
      </div>
    `;

    L.DomEvent.disableClickPropagation(popupContent);
    return popupContent;
  }

  function getSpiderfiedPositions(center: L.LatLng, count: number): L.LatLng[] {
    if (!mapInstance) return Array(count).fill(center);
    if (count <= 1) return [center];

    const centerPoint = mapInstance.latLngToLayerPoint(center);
    // Radio en píxeles ajustado dinámicamente según cantidad de equipos (36px a 56px)
    const radius = Math.min(56, 36 + count * 4);
    const positions: L.LatLng[] = [];

    const angleStep = (2 * Math.PI) / count;
    const startAngle = -Math.PI / 2; // Inicia arriba a las 12:00

    for (let i = 0; i < count; i++) {
      const angle = startAngle + i * angleStep;
      const pt = L.point(
        centerPoint.x + radius * Math.cos(angle),
        centerPoint.y + radius * Math.sin(angle),
      );
      positions.push(mapInstance.layerPointToLatLng(pt));
    }

    return positions;
  }

  function spiderfyGroup(grp: LocationGroup) {
    if (!mapInstance || !spiderLayer) return;
    spiderLayer.clearLayers();

    const center = L.latLng(grp.lat, grp.lng);
    const count = grp.routers.length;
    const positions = getSpiderfiedPositions(center, count);

    for (let i = 0; i < count; i++) {
      const r = grp.routers[i];
      const pos = positions[i];
      const color = getStatusColor(r);

      // Línea conectora gráfica (spider leg) desde el centro del sitio
      try {
        const leg = L.polyline([center, pos], {
          color: '#22d3ee',
          weight: 1.5,
          opacity: 0.7,
          dashArray: '3, 4',
        });
        spiderLayer.addLayer(leg);
      } catch {
        // Fallback seguro para entornos de prueba JSDOM sin renderizador vectorial SVG/Canvas
      }

      // Marcador individual separado radialmente
      const icon = createRouterIcon(color, r.display_name);
      const marker = L.marker(pos, { icon });
      marker.bindPopup(createSingleRouterPopup(r));
      marker.on('click', () => {
        emit('select-router', r.id);
      });
      spiderLayer.addLayer(marker);
    }
  }

  function clearSpiderLayer() {
    if (spiderLayer) {
      spiderLayer.clearLayers();
    }
  }

  function getDistanceMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371000;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function renderMarkers() {
    if (!mapInstance || !markersLayer) return;
    markersLayer.clearLayers();
    clearSpiderLayer();

    // Agrupar routers co-ubicados (mismo sitio, POP o coordenadas compartidas <= 25 metros)
    const groups: LocationGroup[] = [];

    for (const r of props.routers) {
      if (
        r.latitude !== undefined &&
        r.latitude !== null &&
        (r.latitude as unknown) !== '' &&
        r.longitude !== undefined &&
        r.longitude !== null &&
        (r.longitude as unknown) !== ''
      ) {
        const lat = Number(r.latitude);
        const lng = Number(r.longitude);
        if (!isNaN(lat) && !isNaN(lng)) {
          const match = groups.find((g) => getDistanceMeters(g.lat, g.lng, lat, lng) <= 25);
          if (match) {
            match.routers.push(r);
          } else {
            groups.push({ lat, lng, routers: [r] });
          }
        }
      }
    }

    for (const grp of groups) {
      if (grp.routers.length === 1) {
        // Un solo router en esta ubicación
        const r = grp.routers[0];
        const color = getStatusColor(r);
        const icon = createRouterIcon(color, r.display_name);
        const marker = L.marker([grp.lat, grp.lng], { icon });

        marker.bindPopup(createSingleRouterPopup(r));
        marker.on('click', () => {
          clearSpiderLayer();
          emit('select-router', r.id);
        });

        markersLayer.addLayer(marker);
      } else {
        // 2 o más routers en la MISMA ubicación: Agrupamiento con Badge y Spiderfy
        const groupColor = getGroupStatusColor(grp.routers);
        const icon = createMultiRouterIcon(groupColor, grp.routers);
        const clusterMarker = L.marker([grp.lat, grp.lng], { icon });

        clusterMarker.bindPopup(createMultiRouterPopup(grp));

        clusterMarker.on('click', () => {
          if (grp.routers.length > 0) {
            emit('select-router', grp.routers[0].id);
          }
          spiderfyGroup(grp);
        });

        markersLayer.addLayer(clusterMarker);
      }
    }

    // Auto-encuadre si hay múltiples nodos en el territorio
    try {
      if (mapInstance && groups.length > 1) {
        const bounds = L.latLngBounds(groups.map((g) => [g.lat, g.lng]));
        mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
      }
    } catch {
      // Ignorar en entornos sin motor de renderizado vectorial
    }
  }

  function initMap() {
    if (!mapContainer.value) return;

    mapInstance = L.map(mapContainer.value, {
      center: props.centerCoordinates,
      zoom: props.zoomLevel,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    }).addTo(mapInstance);

    markersLayer = L.layerGroup().addTo(mapInstance);
    spiderLayer = L.layerGroup().addTo(mapInstance);
    renderMarkers();

    // Limpiar spiderfy al hacer zoom para recalcular posiciones
    mapInstance.on('zoomstart', clearSpiderLayer);

    // Asegurar que cualquier popup abierto maneje correctamente los clics
    mapInstance.on('popupopen', (e: L.PopupEvent) => {
      const popupEl = e.popup.getElement();
      if (!popupEl) return;
      L.DomEvent.disableClickPropagation(popupEl);

      const webfigBtns = popupEl.querySelectorAll<HTMLButtonElement>('.btn-popup-webfig');
      webfigBtns.forEach((btn) => {
        L.DomEvent.disableClickPropagation(btn);
        btn.onclick = (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          const rId = btn.getAttribute('data-router-id');
          if (rId) emit('open-webfig', rId);
        };
      });

      const selectBtns = popupEl.querySelectorAll<HTMLButtonElement>('.btn-popup-select');
      selectBtns.forEach((btn) => {
        L.DomEvent.disableClickPropagation(btn);
        btn.onclick = (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          const rId = btn.getAttribute('data-router-id');
          if (rId) emit('select-router', rId);
        };
      });
    });

    // Modo selector de coordenadas
    mapInstance.on('click', (e: L.LeafletMouseEvent) => {
      clearSpiderLayer();
      if (props.enableCoordinatePicker) {
        emit('coordinates-selected', { lat: e.latlng.lat, lng: e.latlng.lng });
      }
    });
  }

  function handleContainerClick(ev: MouseEvent) {
    const target = ev.target as HTMLElement | null;
    if (!target) return;

    const webfigBtn = target.closest('.btn-popup-webfig') as HTMLElement | null;
    if (webfigBtn) {
      ev.preventDefault();
      ev.stopPropagation();
      const rId = webfigBtn.getAttribute('data-router-id');
      if (rId) {
        emit('open-webfig', rId);
      }
      return;
    }

    const selectBtn = target.closest('.btn-popup-select') as HTMLElement | null;
    if (selectBtn) {
      ev.preventDefault();
      ev.stopPropagation();
      const rId = selectBtn.getAttribute('data-router-id');
      if (rId) {
        emit('select-router', rId);
      }
      return;
    }
  }

  watch(
    () => props.routers,
    () => {
      renderMarkers();
    },
    { deep: true },
  );

  watch(
    () => props.selectedRouterId,
    (id) => {
      if (!id || !mapInstance) return;
      const target = props.routers.find((r) => r.id === id);
      if (target && target.latitude !== undefined && target.longitude !== undefined) {
        mapInstance.flyTo([target.latitude, target.longitude], 15, { duration: 1 });
      }
    },
  );

  onMounted(() => {
    if (isHeadlessTest.value) return;
    initMap();
    if (mapContainer.value) {
      mapContainer.value.addEventListener('click', handleContainerClick, true);
    }
    if (typeof ResizeObserver !== 'undefined' && mapContainer.value) {
      resizeObserver = new ResizeObserver(() => {
        if (mapInstance) {
          mapInstance.invalidateSize();
        }
      });
      resizeObserver.observe(mapContainer.value);
    }
    setTimeout(() => {
      if (mapInstance) {
        mapInstance.invalidateSize();
      }
    }, 150);
    setTimeout(() => {
      if (mapInstance) {
        mapInstance.invalidateSize();
      }
    }, 500);
  });

  onBeforeUnmount(() => {
    if (mapContainer.value) {
      mapContainer.value.removeEventListener('click', handleContainerClick, true);
    }
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    clearSpiderLayer();
    if (markersLayer) {
      markersLayer.clearLayers();
      markersLayer = null;
    }
    if (spiderLayer) {
      spiderLayer.clearLayers();
      spiderLayer = null;
    }
    if (mapInstance) {
      mapInstance.remove();
      mapInstance = null;
    }
  });
</script>

<template>
  <div class="map-wrapper">
    <div
      v-if="isHeadlessTest"
      class="deterministic-grid-placeholder"
      aria-label="Vista determinista de mapa para pruebas"
    >
      <div v-for="r in routers" :key="r.id" class="deterministic-pin">
        {{ r.display_name }} ({{ r.latitude }}, {{ r.longitude }})
      </div>
    </div>
    <div
      v-else
      ref="mapContainer"
      class="osm-map-container"
      aria-label="Mapa interactivo de routers MikroTik"
    ></div>
  </div>
</template>

<style>
  /* Clases globales de Leaflet para estilizado táctico */
  .rg-map-pin-container {
    background: transparent;
    border: none;
  }

  .rg-map-pin {
    width: 20px;
    height: 20px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .pin-dot {
    width: 12px;
    height: 12px;
    background-color: var(--pin-color, #22d3ee);
    border-radius: 50%;
    border: 2px solid #0b0f19;
    box-shadow: 0 0 8px var(--pin-color, #22d3ee);
    z-index: 2;
  }

  .pin-pulse {
    position: absolute;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background-color: var(--pin-color, #22d3ee);
    opacity: 0.35;
    animation: pin-pulsate 2s infinite ease-out;
  }

  /* Pin para Múltiples Equipos en la Misma Ubicación (Co-ubicados) */
  .rg-map-pin--multi {
    width: 28px;
    height: 28px;
  }

  .pin-dot--multi {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background-color: var(--pin-color, #22d3ee);
    border: 2px solid #0b0f19;
    box-shadow: 0 0 10px var(--pin-color, #22d3ee);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 3;
  }

  .pin-count-badge {
    font-size: 11px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace, sans-serif;
    color: #0b0f19;
    line-height: 1;
    user-select: none;
  }

  .pin-pulse--multi {
    width: 34px;
    height: 34px;
  }

  @keyframes pin-pulsate {
    0% {
      transform: scale(0.6);
      opacity: 0.6;
    }
    100% {
      transform: scale(1.6);
      opacity: 0;
    }
  }

  .leaflet-popup-content-wrapper {
    background: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid #1e293b;
    border-radius: 6px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  }

  .leaflet-popup-tip {
    background: #111827 !important;
  }

  .rg-map-popup {
    font-size: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 180px;
  }

  .popup-title {
    font-size: 0.95rem;
    color: #22d3ee;
  }

  .popup-identity code,
  .popup-meta code {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: #cbd5e1;
  }

  .btn-popup-webfig {
    margin-top: 6px;
    background: #22d3ee;
    color: #0b0f19;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.75rem;
    cursor: pointer;
    width: 100%;
    transition: opacity 0.15s ease;
  }

  .btn-popup-webfig:hover {
    opacity: 0.9;
  }

  /* Popup para Múltiples Equipos Co-ubicados */
  .rg-map-popup--multi {
    max-height: 360px;
    overflow-y: auto;
    width: 280px;
    gap: 8px;
    padding: 2px;
  }

  .popup-site-header {
    border-bottom: 1px solid #1e293b;
    padding-bottom: 6px;
    margin-bottom: 4px;
  }

  .site-badge {
    font-size: 0.68rem;
    font-weight: 700;
    color: #22d3ee;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .site-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #f8fafc;
  }

  .site-coords {
    font-size: 0.72rem;
    color: #94a3b8;
  }

  .popup-routers-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .popup-router-item {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: border-color 0.15s ease;
  }

  .popup-router-item:hover {
    border-color: #334155;
    background: rgba(15, 23, 42, 0.85);
  }

  .router-item-header {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .router-item-name {
    font-size: 0.82rem;
    color: #f8fafc;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .badge-role {
    font-size: 0.65rem;
    background: rgba(34, 211, 238, 0.12);
    color: #22d3ee;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .router-item-details {
    font-size: 0.72rem;
    color: #cbd5e1;
    line-height: 1.3;
  }

  .router-item-details code {
    font-family: 'JetBrains Mono', monospace;
    color: #38bdf8;
  }

  .router-item-actions {
    display: flex;
    gap: 6px;
    margin-top: 4px;
  }

  .btn-popup-select {
    flex: 1;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid #334155;
    color: #cbd5e1;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-popup-select:hover {
    background: rgba(34, 211, 238, 0.15);
    border-color: #22d3ee;
    color: #22d3ee;
  }

  /* Filtro de bajo encandilamiento para temas dark y noc-high-contrast */
  [data-theme='dark'] .leaflet-tile-pane,
  [data-theme='noc-high-contrast'] .leaflet-tile-pane {
    filter: brightness(0.82) contrast(1.15) saturate(0.8);
  }
</style>

<style scoped>
  .map-wrapper {
    width: 100%;
    height: 100%;
    min-height: 480px;
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--rg-border-grid, #1e293b);
  }

  .osm-map-container {
    width: 100%;
    height: 100%;
    min-height: 480px;
  }

  .deterministic-grid-placeholder {
    width: 100%;
    height: 100%;
    position: absolute;
    inset: 0;
    z-index: 1000;
  }
</style>
