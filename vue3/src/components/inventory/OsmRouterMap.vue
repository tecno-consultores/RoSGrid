<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type { RouterItem } from '@/types';

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

  const mapContainer = ref<HTMLDivElement | null>(null);
  let mapInstance: L.Map | null = null;
  let markersLayer: L.LayerGroup | null = null;
  const isDeterministicE2E = typeof navigator !== 'undefined' && Boolean(navigator.webdriver);

  function getStatusColor(router: RouterItem): string {
    if (router.admin_state === 'MAINTENANCE') return '#38BDF8';
    if (!router.is_reachable || router.ssl_trust_status === 'FINGERPRINT_MISMATCH') {
      return '#EF4444';
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

  function renderMarkers() {
    if (!mapInstance || !markersLayer) return;
    markersLayer.clearLayers();

    for (const r of props.routers) {
      if (r.latitude !== undefined && r.longitude !== undefined) {
        const color = getStatusColor(r);
        const icon = createRouterIcon(color, r.display_name);
        const marker = L.marker([r.latitude, r.longitude], { icon });

        // Popup interactivo
        const popupContent = document.createElement('div');
        popupContent.className = 'rg-map-popup';
        popupContent.innerHTML = `
          <div class="popup-title"><strong>${r.display_name}</strong></div>
          <div class="popup-identity">Identity: <code>${r.ros_identity || r.display_name}</code></div>
          <div class="popup-role">Rol: <span class="badge-role">${r.network_role || 'GENERAL'}</span></div>
          <div class="popup-meta">IP: <code>${r.ip_address}</code> | v${r.ros_version}</div>
          <div class="popup-actions">
            <button type="button" class="btn-popup-webfig" data-router-id="${r.id}">
              Abrir WebFig →
            </button>
          </div>
        `;

        const webfigBtn = popupContent.querySelector('.btn-popup-webfig');
        if (webfigBtn) {
          webfigBtn.addEventListener('click', () => {
            emit('open-webfig', r.id);
          });
        }

        marker.bindPopup(popupContent);
        marker.on('click', () => {
          emit('select-router', r.id);
        });

        markersLayer.addLayer(marker);
      }
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

    if (!isDeterministicE2E) {
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      }).addTo(mapInstance);
    }

    markersLayer = L.layerGroup().addTo(mapInstance);
    renderMarkers();

    // Modo selector de coordenadas
    mapInstance.on('click', (e: L.LeafletMouseEvent) => {
      if (props.enableCoordinatePicker) {
        emit('coordinates-selected', { lat: e.latlng.lat, lng: e.latlng.lng });
      }
    });
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
    initMap();
  });

  onBeforeUnmount(() => {
    if (mapInstance) {
      mapInstance.remove();
      mapInstance = null;
    }
  });
</script>

<template>
  <div class="map-wrapper">
    <div
      ref="mapContainer"
      class="osm-map-container"
      :class="{ 'osm-map-container--deterministic': isDeterministicE2E }"
      aria-label="Mapa interactivo de routers MikroTik"
    >
      <!-- En modo E2E Playwright, se muestra un lienzo determinista para snapshot visual -->
      <div v-if="isDeterministicE2E" class="deterministic-grid-placeholder" aria-hidden="true">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E293B" stroke-width="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="#0B0F19" />
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>
    </div>
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
    min-height: 400px;
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--rg-border-grid, #1e293b);
  }

  .osm-map-container {
    width: 100%;
    height: 100%;
    min-height: 400px;
  }

  .deterministic-grid-placeholder {
    width: 100%;
    height: 100%;
    position: absolute;
    inset: 0;
    z-index: 1000;
  }
</style>
