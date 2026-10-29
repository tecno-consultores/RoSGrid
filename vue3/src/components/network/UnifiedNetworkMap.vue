<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type { OpticalBoxItem, RouterItem, SubscriberDeviceItem, OperationalStatusResponse } from '@/types';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useI18n } from '@/composables/useI18n';
  import { escapeHtml } from '@/utils/security';

  const { t } = useI18n();

  const props = withDefaults(
    defineProps<{
      mode?: 'subscribers' | 'inventory' | 'wallboard';
      allowWebfig?: boolean;
      routers?: RouterItem[];
      opticalBoxes?: OpticalBoxItem[];
      subscribers?: SubscriberDeviceItem[];
      selectedId?: string | null;
      centerCoordinates?: [number, number];
      zoomLevel?: number;
    }>(),
    {
      mode: 'subscribers',
      allowWebfig: true,
      routers: () => [],
      opticalBoxes: () => [],
      subscribers: () => [],
      selectedId: null,
      centerCoordinates: () => [10.4806, -66.9036], // Caracas por defecto
      zoomLevel: 13,
    },
  );

  const emit = defineEmits<{
    (e: 'select-router', routerId: string): void;
    (e: 'select-box', boxId: string): void;
    (e: 'select-subscriber', subscriberId: string): void;
    (e: 'diagnose-subscriber', subscriber: SubscriberDeviceItem): void;
  }>();

  const authStore = useAuthStore();
  const fieldOpsStore = useFieldOpsStore();
  const nocEventsStore = useNocEventsStore();

  const isHeadlessTest = computed(
    () =>
      typeof navigator !== 'undefined' &&
      Boolean('webdriver' in navigator && (navigator as { webdriver?: boolean }).webdriver),
  );

  const isIspMode = computed<boolean>(() => Boolean(authStore.tenantFeatures?.isp_module_enabled));

  // Control RBAC: Si allowWebfig es false (modo técnico de campo), WebFig está terminantemente prohibido
  const canAccessWebFig = computed<boolean>(() => {
    if (!props.allowWebfig) return false;
    const role = authStore.currentRole || authStore.user?.role || '';
    const privileged = ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'];
    return privileged.includes(role);
  });

  // Semáforo de salud de Routers: Verde (Online), Naranja (Mantenimiento/Provisión), Rojo (Caído)
  function getRouterHealth(r: RouterItem): { color: string; label: string; badgeClass: string; pulseClass: string } {
    if (!r.is_reachable || r.admin_state === 'DECOMMISSIONED') {
      return {
        color: '#EF4444', // Rojo
        label: 'CAÍDO / SIN ALCANCE',
        badgeClass: 'badge-offline',
        pulseClass: 'router-pulse-danger',
      };
    }
    if (r.admin_state === 'MAINTENANCE' || r.admin_state === 'PROVISIONING') {
      return {
        color: '#F59E0B', // Naranja
        label: 'EN MANTENIMIENTO / PROVISIÓN',
        badgeClass: 'badge-warning',
        pulseClass: 'router-pulse-warning',
      };
    }
    return {
      color: '#10B981', // Verde
      label: 'ONLINE / OPERATIVO',
      badgeClass: 'badge-online',
      pulseClass: '',
    };
  }

  // Estado de los 3 Toggles de Capa Independientes
  const showRouters = ref<boolean>(props.mode === 'inventory' || props.mode === 'wallboard');
  const showBoxes = ref<boolean>(isIspMode.value && props.mode === 'subscribers');
  const showSubscribers = ref<boolean>(props.mode === 'subscribers');

  // Filtro de estado
  const statusFilter = ref<'ALL' | 'ONLINE' | 'OFFLINE'>('ALL');

  // Interfaz para sitios o nodos con múltiples routers co-ubicados
  export interface LocationGroup {
    lat: number;
    lng: number;
    routers: RouterItem[];
  }

  // Elementos seleccionados para el drawer lateral
  const activeRouter = ref<RouterItem | null>(null);
  const activeLocationGroup = ref<LocationGroup | null>(null);
  const activeBox = ref<OpticalBoxItem | null>(null);
  const activeSubscriber = ref<SubscriberDeviceItem | null>(null);
  const operationalLock = ref<OperationalStatusResponse | null>(null);

  // Alerta de Causa Raíz (RCA)
  const showRcaBanner = ref<boolean>(true);

  const downRouters = computed<RouterItem[]>(() => {
    return props.routers.filter(
      (r) => !r.is_reachable || r.admin_state === 'DECOMMISSIONED' || r.admin_state === 'MAINTENANCE',
    );
  });

  const affectedSubscribers = computed<SubscriberDeviceItem[]>(() => {
    if (downRouters.value.length === 0) return [];
    const downIds = new Set(downRouters.value.map((r) => r.id));
    return props.subscribers.filter((s) => s.router_id && downIds.has(s.router_id));
  });

  // Instancias de Leaflet
  const mapContainer = ref<HTMLDivElement | null>(null);
  let mapInstance: L.Map | null = null;
  let routersLayer: L.LayerGroup | null = null;
  let spiderLayer: L.LayerGroup | null = null;
  let boxesLayer: L.LayerGroup | null = null;
  let subscribersLayer: L.LayerGroup | null = null;
  let linesLayer: L.LayerGroup | null = null;
  let resizeObserver: ResizeObserver | null = null;

  function clearSpiderLayer(): void {
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

  function buildLocationGroups(routers: RouterItem[]): LocationGroup[] {
    const groups: LocationGroup[] = [];
    for (const r of routers) {
      if (
        r.latitude === undefined ||
        r.latitude === null ||
        (r.latitude as unknown) === '' ||
        r.longitude === undefined ||
        r.longitude === null ||
        (r.longitude as unknown) === ''
      ) {
        continue;
      }
      const lat = Number(r.latitude);
      const lng = Number(r.longitude);
      if (Number.isNaN(lat) || Number.isNaN(lng) || (lat === 0 && lng === 0)) {
        continue;
      }
      const match = groups.find((g) => getDistanceMeters(g.lat, g.lng, lat, lng) <= 25);
      if (match) {
        match.routers.push(r);
      } else {
        groups.push({ lat, lng, routers: [r] });
      }
    }
    return groups;
  }

  function getGroupStatus(routers: RouterItem[]): { color: string; label: string; badgeClass: string; pulseClass: string } {
    if (routers.some((r) => !r.is_reachable || r.admin_state === 'DECOMMISSIONED')) {
      return {
        color: '#EF4444',
        label: 'ALERTAS / SIN ALCANCE',
        badgeClass: 'badge-offline',
        pulseClass: 'router-pulse-danger',
      };
    }
    if (routers.some((r) => r.admin_state === 'MAINTENANCE' || r.admin_state === 'PROVISIONING')) {
      return {
        color: '#F59E0B',
        label: 'MANTENIMIENTO / PROVISIÓN',
        badgeClass: 'badge-warning',
        pulseClass: 'router-pulse-warning',
      };
    }
    return {
      color: '#10B981',
      label: 'ONLINE / OPERATIVO',
      badgeClass: 'badge-online',
      pulseClass: '',
    };
  }

  function getSpiderfiedPositions(center: L.LatLng, count: number): L.LatLng[] {
    if (!mapInstance) return new Array(count).fill(center);
    if (count <= 1) return [center];

    const centerPoint = mapInstance.latLngToLayerPoint(center);
    const radius = Math.min(75, 45 + count * 5);
    const positions: L.LatLng[] = [];

    const angleStep = (2 * Math.PI) / count;
    const startAngle = -Math.PI / 2;

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

  function spiderfyGroup(grp: LocationGroup): void {
    if (!mapInstance || !spiderLayer) return;
    spiderLayer.clearLayers();

    const center = L.latLng(grp.lat, grp.lng);
    const count = grp.routers.length;
    const positions = getSpiderfiedPositions(center, count);

    for (let i = 0; i < count; i++) {
      const r = grp.routers[i];
      const pos = positions[i];
      const health = getRouterHealth(r);

      try {
        const leg = L.polyline([center, pos], {
          color: '#00F0FF',
          weight: 1.5,
          opacity: 0.8,
          dashArray: '3, 4',
        });
        spiderLayer.addLayer(leg);
      } catch {
        // Ignorar en JSDOM/entornos headless sin motor SVG
      }

      const icon = L.divIcon({
        className: 'rg-map-pin-container',
        html: `
          <div class="rg-map-pin" style="--pin-color: ${health.color};" role="button" tabindex="0" title="${escapeHtml(r.display_name)} (${health.label})">
            <div class="pin-pulse ${health.pulseClass}"></div>
            <div class="pin-dot"></div>
            <span class="pin-router-label">${escapeHtml(r.display_name)}</span>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker(pos, { icon });
      marker.on('click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        activeRouter.value = r;
        activeLocationGroup.value = null;
        activeBox.value = null;
        activeSubscriber.value = null;
        emit('select-router', r.id);
      });
      spiderLayer.addLayer(marker);
    }
  }

  function selectRouterFromGroup(r: RouterItem): void {
    activeRouter.value = r;
    activeLocationGroup.value = null;
    emit('select-router', r.id);
  }

  function initMap(): void {
    if (!mapContainer.value) return;

    if (isHeadlessTest.value) {
      return;
    }

    try {
      mapInstance = L.map(mapContainer.value, {
        zoomControl: false,
        attributionControl: false,
      }).setView(props.centerCoordinates, props.zoomLevel);

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
      }).addTo(mapInstance);

      routersLayer = L.layerGroup().addTo(mapInstance);
      spiderLayer = L.layerGroup().addTo(mapInstance);
      boxesLayer = L.layerGroup().addTo(mapInstance);
      subscribersLayer = L.layerGroup().addTo(mapInstance);
      linesLayer = L.layerGroup().addTo(mapInstance);

      renderAllLayers();

      mapInstance.on('zoomstart', () => {
        clearSpiderLayer();
      });
      mapInstance.on('click', () => {
        clearSpiderLayer();
      });

      resizeObserver = new ResizeObserver(() => {
        if (mapInstance) {
          mapInstance.invalidateSize();
        }
      });
      resizeObserver.observe(mapContainer.value);
    } catch {
      // Manejo seguro en entornos sin soporte gráfico completo
    }
  }

  function getSubscriberColor(sub: SubscriberDeviceItem): string {
    if (sub.last_reachability_status === 'OFFLINE' || sub.status === 'SUSPENDED') {
      return '#EF4444'; // Rojo
    }
    const lat = sub.ping_latency_ms;
    const loss = sub.packet_loss_pct;
    if ((lat !== undefined && lat !== null && lat >= 40) || (loss !== undefined && loss !== null && loss >= 1)) {
      return '#F97316'; // Naranja
    }
    return '#00F0FF'; // Tactical Cyan / Verde
  }

  function renderAllLayers(): void {
    if (!mapInstance || isHeadlessTest.value) return;

    routersLayer?.clearLayers();
    spiderLayer?.clearLayers();
    boxesLayer?.clearLayers();
    subscribersLayer?.clearLayers();
    linesLayer?.clearLayers();

    // 1. Capa de Routers de Red (con soporte para Sitios Compartidos / Co-ubicados)
    if (showRouters.value && routersLayer) {
      const groups = buildLocationGroups(props.routers);

      groups.forEach((grp) => {
        if (grp.routers.length === 1) {
          const r = grp.routers[0];
          const health = getRouterHealth(r);
          const color = health.color;
          const pulseClass = health.pulseClass;

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin" style="--pin-color: ${color};" role="button" tabindex="0" title="${escapeHtml(r.display_name)} (${health.label})">
                <div class="pin-pulse ${pulseClass}"></div>
                <div class="pin-dot"></div>
                <span class="pin-router-label">${escapeHtml(r.display_name)}</span>
              </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            clearSpiderLayer();
            activeRouter.value = r;
            activeLocationGroup.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            emit('select-router', r.id);
          });
          routersLayer?.addLayer(marker);
        } else {
          // Múltiples routers co-ubicados (ej. 5 equipos en Guacara)
          const groupHealth = getGroupStatus(grp.routers);
          const count = grp.routers.length;
          const names = grp.routers.map((r) => r.display_name).join(', ');

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin rg-map-pin--multi" style="--pin-color: ${groupHealth.color};" role="button" tabindex="0" title="Sitio con ${count} routers: ${escapeHtml(names)}">
                <div class="pin-pulse pin-pulse--multi ${groupHealth.pulseClass}"></div>
                <div class="pin-dot pin-dot--multi">
                  <span class="pin-count-badge">${count}</span>
                </div>
                <span class="pin-router-label pin-router-label--multi">${count} Equipos (${escapeHtml(grp.routers[0].display_name)}+)</span>
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            activeLocationGroup.value = grp;
            activeRouter.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            spiderfyGroup(grp);
            if (grp.routers.length > 0) {
              emit('select-router', grp.routers[0].id);
            }
          });
          routersLayer?.addLayer(marker);
        }
      });
    }

    // 2. Capa de Cajas NAP FTTH (Solo en modo ISP)
    if (isIspMode.value && showBoxes.value && boxesLayer) {
      props.opticalBoxes.forEach((b) => {
        const lat = Number(b.latitude);
        const lng = Number(b.longitude);
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

        const occ = b.occupied_ports_count || 0;
        const cap = b.capacity_ports || 16;
        const isFull = occ >= cap;
        const color = isFull ? '#EF4444' : '#10B981';

        const icon = L.divIcon({
          className: 'rg-box-marker-container',
          html: `
            <div class="rg-box-marker" style="--box-color: ${color};" title="Caja NAP ${escapeHtml(b.box_code)}">
              <span class="box-icon">📦</span>
              <span class="box-badge">${occ}/${cap}</span>
            </div>
          `,
          iconSize: [36, 36],
          iconAnchor: [18, 18],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', () => {
          activeBox.value = b;
          activeRouter.value = null;
          activeSubscriber.value = null;
          emit('select-box', b.id);
        });
        boxesLayer?.addLayer(marker);
      });
    }

    // 3. Capa de Clientes / Dispositivos
    if (showSubscribers.value && subscribersLayer) {
      props.subscribers.forEach((s) => {
        const lat = Number(s.latitude);
        const lng = Number(s.longitude);
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

        // Filtrado rápido por estado
        if (statusFilter.value === 'ONLINE' && s.last_reachability_status === 'OFFLINE') return;
        if (statusFilter.value === 'OFFLINE' && s.last_reachability_status !== 'OFFLINE') return;

        const color = getSubscriberColor(s);
        const isDownByRouter = downRouters.value.some((r) => r.id === s.router_id);

        const icon = L.divIcon({
          className: 'rg-sub-marker-container',
          html: `
            <div class="rg-sub-marker ${isDownByRouter ? 'sub-rca-pulse' : ''}" style="--sub-color: ${color};" title="${escapeHtml(s.endpoint_identifier)}">
              <span class="sub-dot"></span>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', async () => {
          activeSubscriber.value = s;
          activeRouter.value = null;
          activeBox.value = null;
          emit('select-subscriber', s.id);
          // Consultar lock operativo y causa raíz en vivo
          operationalLock.value = await fieldOpsStore.fetchOperationalStatus(s.id);
        });
        subscribersLayer?.addLayer(marker);
      });
    }
  }

  function focusAffectedZone(): void {
    if (!mapInstance || affectedSubscribers.value.length === 0) return;
    const lats = affectedSubscribers.value.map((s) => Number(s.latitude)).filter((n) => !isNaN(n) && n !== 0);
    const lngs = affectedSubscribers.value.map((s) => Number(s.longitude)).filter((n) => !isNaN(n) && n !== 0);
    if (lats.length > 0 && lngs.length > 0) {
      const avgLat = lats.reduce((a, b) => a + b, 0) / lats.length;
      const avgLng = lngs.reduce((a, b) => a + b, 0) / lngs.length;
      mapInstance.flyTo([avgLat, avgLng], 15, { animate: true });
    }
  }

  watch([showRouters, showBoxes, showSubscribers, statusFilter, () => props.routers, () => props.opticalBoxes, () => props.subscribers], () => {
    renderAllLayers();
  }, { deep: true });

  // Escuchar eventos reactivos de cambio de estado en vivo emitidos por el Worker vía WebSocket
  watch(
    () => nocEventsStore.lastDeviceStatusEvent,
    (ev) => {
      if (!ev) return;
      const target = props.subscribers.find((s) => s.id === ev.deviceId);
      if (target) {
        target.last_reachability_status = ev.status;
        renderAllLayers();
      }
    },
    { deep: true },
  );

  watch(
    () => props.selectedId,
    (newId) => {
      if (!newId) return;
      const target = props.routers.find((r) => r.id === newId);
      if (target) {
        activeRouter.value = target;
        activeLocationGroup.value = null;
      }
    },
    { immediate: true },
  );

  defineExpose({
    activeRouter,
    activeLocationGroup,
    buildLocationGroups,
    getDistanceMeters,
    getGroupStatus,
    renderAllLayers,
    spiderfyGroup,
    clearSpiderLayer,
  });

  onMounted(() => {
    initMap();
  });

  onBeforeUnmount(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
    }
    if (mapInstance) {
      mapInstance.remove();
      mapInstance = null;
    }
  });
</script>

<template>
  <div class="unified-network-map-wrapper">
    <!-- Barra Táctica Superior: 3 Toggles de Capa Independientes con Feature Flags -->
    <header class="unified-map-toolbar">
      <div class="layers-toggles-group" role="toolbar" aria-label="Controles de Capa del Mapa">
        <button
          type="button"
          class="btn-layer-toggle btn-layer-routers"
          :class="{ 'btn-layer-toggle--active': showRouters }"
          :aria-pressed="showRouters ? 'true' : 'false'"
          @click="showRouters = !showRouters"
        >
          <span class="icon">🏢</span>
          <span class="label">{{ t('network_map.layer_routers') }}</span>
          <span class="counter">({{ routers.length }})</span>
        </button>

        <button
          v-if="isIspMode"
          type="button"
          class="btn-layer-toggle btn-layer-boxes"
          :class="{ 'btn-layer-toggle--active': showBoxes }"
          :aria-pressed="showBoxes ? 'true' : 'false'"
          @click="showBoxes = !showBoxes"
        >
          <span class="icon">📦</span>
          <span class="label">{{ t('network_map.layer_boxes') }}</span>
          <span class="counter">({{ opticalBoxes.length }})</span>
        </button>

        <button
          type="button"
          class="btn-layer-toggle btn-layer-subs"
          :class="{ 'btn-layer-toggle--active': showSubscribers }"
          :aria-pressed="showSubscribers ? 'true' : 'false'"
          @click="showSubscribers = !showSubscribers"
        >
          <span class="icon">💻</span>
          <span class="label">{{ t('network_map.layer_subs') }}</span>
          <span class="counter">({{ subscribers.length }})</span>
        </button>
      </div>

      <div class="filter-controls-group">
        <select v-model="statusFilter" class="rg-select-filter" aria-label="Filtrar por estado">
          <option value="ALL">{{ t('network_map.filter_all') }}</option>
          <option value="ONLINE">{{ t('network_map.filter_online') }}</option>
          <option value="OFFLINE">{{ t('network_map.filter_offline') }}</option>
        </select>
      </div>
    </header>

    <!-- Franja Táctica de Alerta de Cabecera (RCA estilo Zabbix) -->
    <aside
      v-if="downRouters.length > 0 && showRcaBanner"
      class="rca-header-alert-strip"
      role="alert"
      aria-live="polite"
    >
      <div class="rca-alert-content">
        <span class="rca-icon">🚨</span>
        <div class="rca-text">
          <strong>{{ t('network_map.rca_title') }}</strong>
          <span>{{ t('network_map.rca_desc', { name: downRouters[0].display_name }) }}</span>
          <span class="rca-affected">{{ t('network_map.rca_affected', { count: affectedSubscribers.length }) }}</span>
        </div>
      </div>
      <div class="rca-actions">
        <button type="button" class="btn-rca-focus" @click="focusAffectedZone">
          {{ t('network_map.btn_focus_zone') }}
        </button>
        <button
          type="button"
          class="btn-rca-close"
          aria-label="Descartar aviso de cabecera"
          @click="showRcaBanner = false"
        >
          ✖️
        </button>
      </div>
    </aside>

    <!-- Contenedor del Mapa Cartográfico -->
    <main class="map-view-body">
      <div ref="mapContainer" class="unified-leaflet-container" tabindex="0" aria-label="Mapa de Red Unificado"></div>

      <!-- Drawer Lateral de Detalle con Gobernanza RBAC y Prevención de Colisiones -->
      <aside v-if="activeRouter || activeLocationGroup || activeBox || activeSubscriber" class="unified-detail-drawer" aria-label="Panel de Información">
        <!-- Detalle de Sitio / Nodo Co-ubicado con Múltiples Equipos -->
        <div v-if="activeLocationGroup" class="drawer-card location-group-card">
          <div class="card-header">
            <h3>🏢 Sitio Compartido ({{ activeLocationGroup.routers.length }} Equipos)</h3>
            <button type="button" class="btn-close-card" @click="activeLocationGroup = null; clearSpiderLayer()">✖</button>
          </div>
          <div class="card-body">
            <p class="site-location-meta">
              <strong>Ubicación:</strong> <code>{{ Number(activeLocationGroup.lat).toFixed(5) }}, {{ Number(activeLocationGroup.lng).toFixed(5) }}</code>
            </p>
            <div class="group-routers-list">
              <div
                v-for="r in activeLocationGroup.routers"
                :key="r.id"
                class="group-router-item"
              >
                <div class="group-router-header">
                  <span class="router-status-dot" :style="{ backgroundColor: getRouterHealth(r).color }"></span>
                  <strong class="group-router-name">{{ r.display_name }}</strong>
                  <span class="badge-role">{{ r.network_role || 'DISTRIBUTION' }}</span>
                </div>
                <div class="group-router-info">
                  <span>IP: <code>{{ r.ip_address || r.api_base_url || '--' }}</code></span>
                  <span class="group-router-status" :class="getRouterHealth(r).badgeClass">{{ getRouterHealth(r).label }}</span>
                </div>
                <div class="group-router-actions">
                  <button
                    type="button"
                    class="btn-select-group-router"
                    @click="selectRouterFromGroup(r)"
                  >
                    🔍 Seleccionar
                  </button>
                  <RouterLink
                    v-if="allowWebfig && canAccessWebFig"
                    :to="'/routers/' + r.id + '/webfig'"
                    class="btn-webfig-group-router"
                  >
                    ⚡ WebFig
                  </RouterLink>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Detalle de Router -->
        <div v-if="activeRouter" class="drawer-card router-detail-card">
          <div class="card-header">
            <h3>🏢 {{ activeRouter.display_name }}</h3>
            <button type="button" class="btn-close-card" @click="activeRouter = null">✖</button>
          </div>
          <div class="card-body">
            <p><strong>IP / Endpoint:</strong> {{ activeRouter.ip_address || activeRouter.api_base_url || '--' }}</p>
            <p><strong>Rol de Red:</strong> {{ activeRouter.network_role || 'DISTRIBUTION' }}</p>
            <p><strong>Identidad ROS:</strong> {{ activeRouter.ros_identity || activeRouter.board_name || 'MikroTik Router' }}</p>
            <p>
              <strong>Salud del Router:</strong>
              <span class="router-health-pill font-mono" :class="getRouterHealth(activeRouter).badgeClass">
                ● {{ getRouterHealth(activeRouter).label }}
              </span>
            </p>

            <!-- Gobernanza Estricta: En el mapa del técnico NUNCA se muestra el botón de WebFig -->
            <div v-if="allowWebfig" class="webfig-access-section">
              <RouterLink
                v-if="canAccessWebFig"
                :to="'/routers/' + activeRouter.id + '/webfig'"
                class="btn-open-webfig"
              >
                ⚡ Abrir Consola WebFig v7
              </RouterLink>
              <div v-else class="rbac-restricted-box">
                <span class="lock-icon">🔒</span>
                <span>Acceso a configuración WebFig restringido para ingenieros de NOC.</span>
              </div>
            </div>
            <div v-else class="field-view-indicator">
              <span class="field-indicator-dot" :style="{ backgroundColor: getRouterHealth(activeRouter).color }"></span>
              <span class="field-indicator-text">Modo Operaciones de Campo: WebFig estrictamente deshabilitado.</span>
            </div>
          </div>
        </div>

        <!-- Detalle de Caja NAP -->
        <div v-if="activeBox" class="drawer-card box-detail-card">
          <div class="card-header">
            <h3>📦 Caja NAP: {{ activeBox.box_code }}</h3>
            <button type="button" class="btn-close-card" @click="activeBox = null">✖</button>
          </div>
          <div class="card-body">
            <p><strong>Capacidad:</strong> {{ activeBox.occupied_ports_count || 0 }} / {{ activeBox.capacity_ports || 16 }} Puertos</p>
            <p><strong>Splitter:</strong> {{ activeBox.splitter_ratio || '1:16' }}</p>
            <p><strong>Potencia Entrada:</strong> {{ activeBox.input_power_dbm || '--' }} dBm</p>
            <p><strong>Anclaje:</strong> {{ activeBox.installation_type || 'POSTE' }}</p>
          </div>
        </div>

        <!-- Detalle de Dispositivo / Abonado -->
        <div v-if="activeSubscriber" class="drawer-card subscriber-detail-card">
          <div class="card-header">
            <h3>💻 {{ activeSubscriber.endpoint_identifier }}</h3>
            <button type="button" class="btn-close-card" @click="activeSubscriber = null">✖</button>
          </div>
          <div class="card-body">
            <!-- Aviso de Prevención de Colisiones (Lock de otro técnico) -->
            <div v-if="operationalLock?.is_locked_by_other" class="operational-lock-banner">
              <span class="warning-icon">👥</span>
              <div class="lock-text">
                <strong>ATENCIÓN EN CURSO:</strong>
                <span>El técnico <strong>{{ operationalLock.technician_name }}</strong> ya atendió este cliente hace {{ operationalLock.minutes_ago || 0 }}m.</span>
              </div>
            </div>

            <!-- Aviso de Causa Raíz (Router de cabecera caído) -->
            <div v-if="operationalLock?.root_cause" class="rca-suppressed-banner">
              <span class="warning-icon">🚨</span>
              <div class="rca-lock-text">
                <strong>CABECERA CAÍDA:</strong>
                <span>{{ operationalLock.root_cause.message }}</span>
              </div>
            </div>

            <p><strong>IP Asignada:</strong> {{ activeSubscriber.assigned_ipv4 || 'Sin IP' }}</p>
            <p><strong>Estado:</strong> {{ activeSubscriber.last_reachability_status || 'UNKNOWN' }}</p>
            <p v-if="activeSubscriber.optical_box"><strong>Caja NAP:</strong> {{ activeSubscriber.optical_box }} (Puerto: {{ activeSubscriber.optical_box_port || '--' }})</p>

            <button
              type="button"
              class="btn-ping-live"
              :disabled="Boolean(operationalLock?.root_cause)"
              @click="emit('diagnose-subscriber', activeSubscriber)"
            >
              ⚡ {{ operationalLock?.root_cause ? 'Diagnóstico Suprimido (Cabecera Caída)' : 'Ejecutar Diagnóstico 1-Click' }}
            </button>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.unified-network-map-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: var(--color-bg-primary, #0B0F19);
  position: relative;
  overflow: hidden;
}

.unified-map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.625rem 1rem;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 1px solid rgba(0, 240, 255, 0.2);
  z-index: 10;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.layers-toggles-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.btn-layer-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 4px;
  color: #94A3B8;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-layer-toggle:hover {
  background: rgba(51, 65, 85, 0.9);
  color: #F8FAFC;
}

.btn-layer-toggle--active {
  background: rgba(0, 240, 255, 0.15);
  border-color: #00F0FF;
  color: #00F0FF;
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.25);
}

.counter {
  font-size: 0.75rem;
  opacity: 0.8;
}

.rg-select-filter {
  padding: 0.375rem 0.625rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: #E2E8F0;
  border-radius: 4px;
  font-size: 0.8125rem;
}

.rca-header-alert-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  background: rgba(220, 38, 38, 0.9);
  color: #FFFFFF;
  padding: 0.5rem 1rem;
  border-bottom: 2px solid #EF4444;
  z-index: 10;
  animation: pulse-border 2s infinite;
}

.rca-alert-content {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.875rem;
}

.rca-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-rca-focus {
  padding: 0.25rem 0.625rem;
  background: #FFFFFF;
  color: #991B1B;
  border: none;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-rca-close {
  background: transparent;
  border: none;
  color: #FFFFFF;
  cursor: pointer;
}

.map-view-body {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
}

.unified-leaflet-container {
  width: 100%;
  height: 100%;
  background: #090D16;
}

.unified-detail-drawer {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 20rem;
  max-width: calc(100% - 2rem);
  max-height: calc(100% - 2rem);
  overflow-y: auto;
  overscroll-behavior: contain;
  background: rgba(15, 23, 42, 0.96);
  border: 1px solid rgba(0, 240, 255, 0.4);
  border-radius: 6px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.7);
  z-index: 1000;
  backdrop-filter: blur(8px);
}

@media (max-width: 640px) {
  .unified-detail-drawer {
    left: 0.5rem;
    right: 0.5rem;
    top: auto;
    bottom: 0.5rem;
    width: auto;
    max-width: calc(100% - 1rem);
    max-height: 60%;
  }
}

.drawer-card {
  padding: 1rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  padding-bottom: 0.5rem;
}

.card-header h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #00F0FF;
  margin: 0;
}

.btn-close-card {
  background: transparent;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-open-webfig {
  display: block;
  text-align: center;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #00F0FF;
  color: #0B0F19;
  font-weight: 700;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.8125rem;
}

.rbac-restricted-box {
  margin-top: 1rem;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #F87171;
  font-size: 0.75rem;
  border-radius: 4px;
  display: flex;
  gap: 0.375rem;
  align-items: center;
}

.operational-lock-banner {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid #F59E0B;
  color: #FBBF24;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.rca-suppressed-banner {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #EF4444;
  color: #F87171;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.btn-ping-live {
  width: 100%;
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: #00F0FF;
  color: #0B0F19;
  border: none;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.8125rem;
  cursor: pointer;
}

.btn-ping-live:disabled {
  background: #475569;
  color: #94A3B8;
  cursor: not-allowed;
}

.badge-online {
  color: #10B981;
  font-weight: 600;
}

.badge-warning {
  color: #F59E0B;
  font-weight: 600;
}

.badge-offline {
  color: #EF4444;
  font-weight: 600;
}

.router-health-pill {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid currentColor;
}

.field-view-indicator {
  margin-top: 1rem;
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.75);
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.field-indicator-text {
  font-size: 0.725rem;
  color: #94A3B8;
}

.router-pulse-warning {
  animation: pulse-orange 1.5s infinite;
}

@keyframes pulse-orange {
  0% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(245, 158, 11, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
  }
}

.site-location-meta {
  font-size: 0.75rem;
  color: #94A3B8;
  margin-bottom: 0.75rem;
}

.site-location-meta code {
  color: #00F0FF;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.group-routers-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 320px;
  overflow-y: auto;
}

.group-router-item {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  transition: border-color 0.2s;
}

.group-router-item:hover {
  border-color: rgba(0, 240, 255, 0.4);
}

.group-router-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.router-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.group-router-name {
  font-size: 0.8125rem;
  color: #F8FAFC;
  flex: 1;
}

.badge-role {
  font-size: 0.625rem;
  background: rgba(0, 240, 255, 0.15);
  color: #00F0FF;
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.group-router-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.6875rem;
  color: #94A3B8;
}

.group-router-info code {
  color: #E2E8F0;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.group-router-actions {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.25rem;
}

.btn-select-group-router {
  flex: 1;
  padding: 0.25rem 0.5rem;
  background: rgba(148, 163, 184, 0.2);
  color: #F8FAFC;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 3px;
  font-size: 0.6875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-select-group-router:hover {
  background: rgba(0, 240, 255, 0.2);
  border-color: #00F0FF;
  color: #00F0FF;
}

.btn-webfig-group-router {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0.5rem;
  background: #00F0FF;
  color: #0B0F19;
  border-radius: 3px;
  font-size: 0.6875rem;
  font-weight: 700;
  text-decoration: none;
  transition: opacity 0.15s;
}

.btn-webfig-group-router:hover {
  opacity: 0.9;
}
</style>

<!-- Clases globales para marcadores inyectados dinámicamente en el DOM de Leaflet (Estilo Wallboard NOC) -->
<style>
.rg-map-pin-container {
  background: transparent !important;
  border: none !important;
}

.rg-map-pin {
  width: 24px;
  height: 24px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.pin-dot {
  width: 14px;
  height: 14px;
  background-color: var(--pin-color, #10B981);
  border-radius: 50%;
  border: 2px solid #0B0F19;
  box-shadow: 0 0 10px var(--pin-color, #10B981);
  z-index: 2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rg-map-pin:hover .pin-dot {
  transform: scale(1.25);
  box-shadow: 0 0 16px var(--pin-color, #10B981);
}

.pin-pulse {
  position: absolute;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--pin-color, #10B981);
  opacity: 0.4;
  animation: pin-pulsate 2s infinite ease-out;
}

.pin-pulse.router-pulse-danger {
  animation: pin-pulsate-danger 1.2s infinite ease-out;
}

.pin-pulse.router-pulse-warning {
  animation: pin-pulsate-warning 1.6s infinite ease-out;
}

.pin-router-label {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 4px;
  background: rgba(11, 15, 25, 0.9);
  color: #F1F5F9;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.7rem;
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.15);
  pointer-events: none;
  z-index: 3;
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
  background-color: var(--pin-color, #00F0FF);
  border: 2px solid #0B0F19;
  box-shadow: 0 0 12px var(--pin-color, #00F0FF);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3;
}

.pin-count-badge {
  font-size: 11px;
  font-weight: 800;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #0B0F19;
  line-height: 1;
  user-select: none;
}

.pin-pulse--multi {
  width: 36px;
  height: 36px;
}

.pin-router-label--multi {
  border-color: rgba(0, 240, 255, 0.4);
  color: #00F0FF;
}

@keyframes pin-pulsate {
  0% {
    transform: scale(0.6);
    opacity: 0.8;
  }
  100% {
    transform: scale(2.2);
    opacity: 0;
  }
}

@keyframes pin-pulsate-danger {
  0% {
    transform: scale(0.6);
    opacity: 0.9;
  }
  100% {
    transform: scale(2.4);
    opacity: 0;
  }
}

@keyframes pin-pulsate-warning {
  0% {
    transform: scale(0.6);
    opacity: 0.8;
  }
  100% {
    transform: scale(2.0);
    opacity: 0;
  }
}
</style>
