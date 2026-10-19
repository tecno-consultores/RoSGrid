<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type { SubscriberDeviceItem } from '@/types';

  interface LocationGroup {
    lat: number;
    lng: number;
    onus: SubscriberDeviceItem[];
  }

  const props = withDefaults(
    defineProps<{
      onus: SubscriberDeviceItem[];
      selectedOnuId?: string | null;
      centerCoordinates?: [number, number];
      zoomLevel?: number;
    }>(),
    {
      selectedOnuId: null,
      centerCoordinates: () => [10.4806, -66.9036], // Caracas por defecto
      zoomLevel: 13,
    },
  );

  const emit = defineEmits<{
    (e: 'select-onu', onuId: string): void;
    (e: 'verify-onu', onu: SubscriberDeviceItem): void;
    (e: 'diagnose-onu', onu: SubscriberDeviceItem): void;
  }>();

  const POPUP_CUSTOM_CLASS = 'rg-custom-leaflet-popup';
  const EVENT_SELECT_ONU = 'select-onu';

  const isHeadlessTest = computed(
    () =>
      typeof navigator !== 'undefined' &&
      Boolean('webdriver' in navigator && (navigator as { webdriver?: boolean }).webdriver),
  );
  const mapContainer = ref<HTMLDivElement | null>(null);
  let mapInstance: L.Map | null = null;
  let markersLayer: L.LayerGroup | null = null;
  let spiderLayer: L.LayerGroup | null = null;
  let resizeObserver: ResizeObserver | null = null;

  /**
   * Regla de Oro Zero-Metrics (specs/32 §5.2):
   * 🟢 Verde: Latencia < 40ms, 0% pérdida
   * 🟠 Naranja: Latencia 40-120ms o pérdida 1-20%
   * 🔴 Rojo: Timeout, offline o pérdida > 20%
   */
  function getZeroMetricsColor(onu: SubscriberDeviceItem): string {
    if (
      onu.last_reachability_status === 'OFFLINE' ||
      onu.status === 'SUSPENDED' ||
      (onu.packet_loss_pct !== undefined &&
        onu.packet_loss_pct !== null &&
        onu.packet_loss_pct > 20)
    ) {
      return '#EF4444'; // 🔴 Rojo
    }

    const lat = onu.ping_latency_ms;
    const loss = onu.packet_loss_pct;
    if (
      (lat !== undefined && lat !== null && lat >= 40) ||
      (loss !== undefined && loss !== null && loss >= 1)
    ) {
      return '#F97316'; // 🟠 Naranja
    }

    return '#22C55E'; // 🟢 Verde
  }

  function getGroupStatusColor(onus: SubscriberDeviceItem[]): string {
    if (onus.some((o) => getZeroMetricsColor(o) === '#EF4444')) {
      return '#EF4444';
    }
    if (onus.some((o) => getZeroMetricsColor(o) === '#F97316')) {
      return '#F97316';
    }
    return '#22C55E';
  }

  function createOnuIcon(color: string, label: string): L.DivIcon {
    return L.divIcon({
      className: 'rg-onu-pin-container',
      html: `
        <div class="rg-onu-pin" style="--pin-color: ${color};" role="button" tabindex="0" aria-label="ONU ${label}">
          <div class="pin-pulse"></div>
          <div class="pin-dot"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });
  }

  function createMultiOnuIcon(color: string, count: number, label: string): L.DivIcon {
    return L.divIcon({
      className: 'rg-onu-pin-container',
      html: `
        <div class="rg-onu-pin rg-onu-pin--multi" style="--pin-color: ${color};" role="button" tabindex="0" aria-label="Caja con ${count} ONUs: ${label}">
          <div class="pin-pulse pin-pulse--multi"></div>
          <div class="pin-dot pin-dot--multi">
            <span class="pin-count-badge">${count}</span>
          </div>
        </div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
  }

  function createSingleOnuPopup(onu: SubscriberDeviceItem): HTMLElement {
    const popupContent = document.createElement('div');
    popupContent.className = 'rg-map-popup';
    const serial = onu.onu_serial_number || onu.device_serial || 'Sin Serial';
    const client = onu.customer_name || onu.customer_code || onu.endpoint_identifier || 'Cliente';
    const latMs =
      onu.ping_latency_ms !== undefined && onu.ping_latency_ms !== null
        ? `${onu.ping_latency_ms} ms`
        : 'N/A';
    const lossPct =
      onu.packet_loss_pct !== undefined && onu.packet_loss_pct !== null
        ? `${onu.packet_loss_pct}%`
        : '0%';
    const color = getZeroMetricsColor(onu);
    const colorBadge =
      color === '#22C55E' ? '🟢 Óptimo' : color === '#F97316' ? '🟠 Degradado' : '🔴 Caído';

    popupContent.innerHTML = `
      <div class="popup-title"><strong>${serial}</strong></div>
      <div class="popup-identity">Cliente: <code>${client}</code></div>
      <div class="popup-role">Estado: <span class="badge-status">${colorBadge}</span></div>
      <div class="popup-meta">
        PON: <code>${onu.pon_port || 'N/A'}</code> | Caja: <code>${onu.optical_box || 'N/A'}</code>
      </div>
      <div class="popup-telemetry">
        Ping: <strong>${latMs}</strong> | Pérdida: <strong>${lossPct}</strong>
      </div>
      <div class="popup-actions">
        <button type="button" class="btn-popup-test" data-onu-id="${onu.id}">
          ⚡ Test 1-Click
        </button>
        <button type="button" class="btn-popup-diag360" data-onu-id="${onu.id}">
          🔬 360°
        </button>
      </div>
    `;

    L.DomEvent.disableClickPropagation(popupContent);
    const testBtn = popupContent.querySelector('.btn-popup-test') as HTMLButtonElement | null;
    if (testBtn) {
      L.DomEvent.disableClickPropagation(testBtn);
      L.DomEvent.on(testBtn, 'click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        L.DomEvent.preventDefault(ev);
        emit('verify-onu', onu);
      });
    }

    const diagBtn = popupContent.querySelector('.btn-popup-diag360') as HTMLButtonElement | null;
    if (diagBtn) {
      L.DomEvent.disableClickPropagation(diagBtn);
      L.DomEvent.on(diagBtn, 'click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        L.DomEvent.preventDefault(ev);
        emit('diagnose-onu', onu);
      });
    }

    return popupContent;
  }

  function createMultiOnuPopup(grp: LocationGroup): HTMLElement {
    const popupContent = document.createElement('div');
    popupContent.className = 'rg-map-popup rg-map-popup--multi';

    const itemsHtml = grp.onus
      .map((onu) => {
        const color = getZeroMetricsColor(onu);
        const serial = onu.onu_serial_number || onu.device_serial || 'ONU';
        const client = onu.customer_name || onu.customer_code || 'Cliente';
        const stateText =
          color === '#22C55E' ? 'Óptimo' : color === '#F97316' ? 'Degradado' : 'Caído';

        return `
          <div class="popup-onu-item" data-onu-id="${onu.id}">
            <div class="onu-item-header">
              <span class="onu-status-bullet" style="background: ${color};"></span>
              <strong>${serial}</strong>
              <span class="onu-state-label font-mono">${stateText}</span>
            </div>
            <div class="onu-item-meta">
              <span>${client}</span> |
              <code>${onu.pon_port || 'PON'}</code>
            </div>
          </div>
        `;
      })
      .join('');

    popupContent.innerHTML = `
      <div class="popup-title">
        <strong>Caja / Punto Coincidente</strong>
        <span class="popup-badge font-mono">${grp.onus.length} ONUs</span>
      </div>
      <div class="popup-onus-list">
        ${itemsHtml}
      </div>
    `;

    L.DomEvent.disableClickPropagation(popupContent);
    const itemElements = popupContent.querySelectorAll('.popup-onu-item');
    itemElements.forEach((el) => {
      const onuId = el.getAttribute('data-onu-id');
      if (onuId) {
        L.DomEvent.on(el as HTMLElement, 'click', (ev) => {
          L.DomEvent.stopPropagation(ev);
          emit(EVENT_SELECT_ONU, onuId);
        });
      }
    });

    return popupContent;
  }

  function expandSpiderfier(grp: LocationGroup): void {
    if (!mapInstance || !spiderLayer) return;
    spiderLayer.clearLayers();

    const count = grp.onus.length;
    const centerLatLng = L.latLng(grp.lat, grp.lng);
    const radiusPixels = Math.min(80, 35 + count * 8);

    const centerPoint = mapInstance.latLngToLayerPoint(centerLatLng);

    grp.onus.forEach((onu, idx) => {
      const angle = (2 * Math.PI * idx) / count;
      const targetPoint = L.point(
        centerPoint.x + radiusPixels * Math.cos(angle),
        centerPoint.y + radiusPixels * Math.sin(angle),
      );
      const targetLatLng = mapInstance!.layerPointToLatLng(targetPoint);

      const spiderLeg = L.polyline([centerLatLng, targetLatLng], {
        color: '#00F3FF',
        weight: 1.5,
        opacity: 0.7,
        dashArray: '3, 4',
      });
      spiderLeg.addTo(spiderLayer!);

      const color = getZeroMetricsColor(onu);
      const serial = onu.onu_serial_number || onu.device_serial || 'ONU';
      const marker = L.marker(targetLatLng, {
        icon: createOnuIcon(color, serial),
      });

      marker.bindPopup(createSingleOnuPopup(onu), {
        className: POPUP_CUSTOM_CLASS,
        maxWidth: 280,
      });

      marker.on('click', () => {
        emit(EVENT_SELECT_ONU, onu.id);
      });

      marker.addTo(spiderLayer!);
    });
  }

  function renderMarkers(): void {
    if (!markersLayer || !mapInstance) return;
    markersLayer.clearLayers();
    if (spiderLayer) spiderLayer.clearLayers();

    // Filtrar equipos con coordenadas válidas
    const validOnus = props.onus.filter(
      (o) =>
        o.latitude !== undefined &&
        o.latitude !== null &&
        o.longitude !== undefined &&
        o.longitude !== null &&
        !isNaN(Number(o.latitude)) &&
        !isNaN(Number(o.longitude)) &&
        (Number(o.latitude) !== 0 || Number(o.longitude) !== 0),
    );

    if (validOnus.length === 0) return;

    // Agrupar por coordenadas coincidentes
    const groupsMap = new Map<string, LocationGroup>();
    validOnus.forEach((onu) => {
      const key = `${Number(onu.latitude).toFixed(4)}_${Number(onu.longitude).toFixed(4)}`;
      if (!groupsMap.has(key)) {
        groupsMap.set(key, {
          lat: Number(onu.latitude),
          lng: Number(onu.longitude),
          onus: [],
        });
      }
      groupsMap.get(key)!.onus.push(onu);
    });

    const bounds = L.latLngBounds([]);

    groupsMap.forEach((grp) => {
      const latLng = L.latLng(grp.lat, grp.lng);
      bounds.extend(latLng);

      if (grp.onus.length === 1) {
        const singleOnu = grp.onus[0];
        const color = getZeroMetricsColor(singleOnu);
        const serial = singleOnu.onu_serial_number || singleOnu.device_serial || 'ONU';
        const marker = L.marker(latLng, {
          icon: createOnuIcon(color, serial),
        });

        marker.bindPopup(createSingleOnuPopup(singleOnu), {
          className: POPUP_CUSTOM_CLASS,
          maxWidth: 280,
        });

        marker.on('click', () => {
          emit(EVENT_SELECT_ONU, singleOnu.id);
        });

        marker.addTo(markersLayer!);
      } else {
        const groupColor = getGroupStatusColor(grp.onus);
        const label = grp.onus.map((o) => o.onu_serial_number || o.device_serial).join(', ');
        const marker = L.marker(latLng, {
          icon: createMultiOnuIcon(groupColor, grp.onus.length, label),
        });

        marker.bindPopup(createMultiOnuPopup(grp), {
          className: POPUP_CUSTOM_CLASS,
          maxWidth: 320,
        });

        marker.on('click', () => {
          expandSpiderfier(grp);
        });

        marker.addTo(markersLayer!);
      }
    });

    // Ajustar límites si hay coordenadas válidas
    if (bounds.isValid() && validOnus.length > 1) {
      mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }

  function initMap(): void {
    if (!mapContainer.value) return;

    mapInstance = L.map(mapContainer.value, {
      center: props.centerCoordinates,
      zoom: props.zoomLevel,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(mapInstance);

    markersLayer = L.layerGroup().addTo(mapInstance);
    spiderLayer = L.layerGroup().addTo(mapInstance);

    renderMarkers();

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        if (mapInstance) {
          mapInstance.invalidateSize();
        }
      });
      resizeObserver.observe(mapContainer.value);
    }
  }

  onMounted(() => {
    initMap();
  });

  onBeforeUnmount(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    if (mapInstance) {
      mapInstance.remove();
      mapInstance = null;
    }
  });

  watch(
    () => props.onus,
    () => {
      renderMarkers();
    },
    { deep: true },
  );
</script>

<template>
  <div
    class="rg-onu-map-wrapper"
    role="region"
    aria-label="Mapa Exclusivo de Clientes y ONUs (Zero-Metrics)"
  >
    <div ref="mapContainer" class="rg-leaflet-container" />

    <!-- Overlay Táctico Informativo Zero-Metrics -->
    <div class="map-zero-metrics-badge" aria-hidden="true">
      <span class="zero-dot">●</span> Telemetría Efímera RAM (Zero-Metrics)
    </div>

    <!-- Leyenda Cromática Rápida -->
    <div class="map-chromatic-legend" aria-label="Leyenda de estados cromáticos">
      <span class="legend-item"><span class="badge-dot dot--green"></span> &lt; 40ms / 0%</span>
      <span class="legend-item"><span class="badge-dot dot--orange"></span> 40-120ms / 1-20%</span>
      <span class="legend-item"><span class="badge-dot dot--red"></span> Offline / &gt; 20%</span>
    </div>

    <!-- Indicador de Pruebas Headless -->
    <div v-if="isHeadlessTest" class="rg-headless-status" style="display: none">
      Headless Leaflet Ready
    </div>
  </div>
</template>

<style scoped>
  .rg-onu-map-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 480px;
    background: #090e17;
    border-radius: 8px;
    overflow: hidden;
  }

  .rg-leaflet-container {
    width: 100%;
    height: 100%;
    min-height: 480px;
  }

  .map-zero-metrics-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 1000;
    background: rgba(9, 14, 23, 0.85);
    border: 1px solid rgba(0, 243, 255, 0.4);
    color: #00f3ff;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.3rem 0.65rem;
    border-radius: 6px;
    backdrop-filter: blur(4px);
    pointer-events: none;
  }

  .zero-dot {
    color: #22c55e;
    animation: blink-pulse 2s infinite;
  }

  .map-chromatic-legend {
    position: absolute;
    bottom: 16px;
    left: 16px;
    z-index: 1000;
    background: rgba(9, 14, 23, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 0.4rem 0.75rem;
    display: flex;
    gap: 0.85rem;
    font-size: 0.75rem;
    color: #cbd5e1;
    backdrop-filter: blur(4px);
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .dot--green {
    background: #22c55e;
    box-shadow: 0 0 6px #22c55e;
  }

  .dot--orange {
    background: #f97316;
    box-shadow: 0 0 6px #f97316;
  }

  .dot--red {
    background: #ef4444;
    box-shadow: 0 0 6px #ef4444;
  }

  @keyframes blink-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }
</style>

<style>
  /* Clases globales de Leaflet para Pines y Popups */
  .rg-onu-pin-container {
    background: transparent;
    border: none;
  }

  .rg-onu-pin {
    width: 22px;
    height: 22px;
    position: relative;
    cursor: pointer;
  }

  .rg-onu-pin .pin-dot {
    width: 14px;
    height: 14px;
    background: var(--pin-color, #22c55e);
    border-radius: 50%;
    position: absolute;
    top: 4px;
    left: 4px;
    border: 2px solid #090e17;
    box-shadow: 0 0 8px var(--pin-color, #22c55e);
  }

  .rg-onu-pin .pin-pulse {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--pin-color, #22c55e);
    opacity: 0.35;
    position: absolute;
    top: 0;
    left: 0;
    animation: onu-pulse 2s infinite ease-out;
  }

  .rg-onu-pin--multi .pin-dot--multi {
    width: 20px;
    height: 20px;
    top: 3px;
    left: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pin-count-badge {
    color: #fff;
    font-size: 10px;
    font-weight: 800;
  }

  @keyframes onu-pulse {
    0% {
      transform: scale(0.8);
      opacity: 0.6;
    }
    100% {
      transform: scale(2);
      opacity: 0;
    }
  }

  /* Popups de Leaflet Oscuros */
  .rg-custom-leaflet-popup .leaflet-popup-content-wrapper {
    background: #090e17 !important;
    border: 1px solid rgba(0, 243, 255, 0.4) !important;
    color: #fff !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6) !important;
    padding: 0 !important;
  }

  .rg-custom-leaflet-popup .leaflet-popup-tip {
    background: #090e17 !important;
    border: 1px solid rgba(0, 243, 255, 0.4) !important;
  }

  .rg-map-popup {
    padding: 0.85rem;
    font-size: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .popup-title {
    color: #00f3ff;
    font-size: 0.95rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.25rem;
  }

  .popup-identity {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .popup-role {
    font-size: 0.8rem;
  }

  .popup-meta,
  .popup-telemetry {
    font-size: 0.75rem;
    color: #cbd5e1;
  }

  .popup-actions {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.5rem;
  }

  .btn-popup-test,
  .btn-popup-diag360 {
    flex: 1;
    min-height: 32px;
    padding: 0.3rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 4px;
    cursor: pointer;
    border: none;
  }

  .btn-popup-test {
    background: #00f3ff;
    color: #090e17;
  }

  .btn-popup-diag360 {
    background: rgba(168, 85, 247, 0.2);
    border: 1px solid #a855f7;
    color: #c084fc;
  }

  .popup-onus-list {
    max-height: 180px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-top: 0.35rem;
  }

  .popup-onu-item {
    background: #111a2e;
    padding: 0.4rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .popup-onu-item:hover {
    background: #192744;
  }

  .onu-item-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .onu-status-bullet {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .onu-state-label {
    font-size: 0.7rem;
    color: #94a3b8;
    margin-left: auto;
  }

  .onu-item-meta {
    font-size: 0.7rem;
    color: #64748b;
  }
</style>
