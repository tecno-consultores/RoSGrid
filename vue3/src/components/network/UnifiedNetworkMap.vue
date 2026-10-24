<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type { OpticalBoxItem, RouterItem, SubscriberDeviceItem, OperationalStatusResponse } from '@/types';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
  import { escapeHtml } from '@/utils/security';

  const props = withDefaults(
    defineProps<{
      mode?: 'subscribers' | 'inventory' | 'wallboard';
      routers?: RouterItem[];
      opticalBoxes?: OpticalBoxItem[];
      subscribers?: SubscriberDeviceItem[];
      selectedId?: string | null;
      centerCoordinates?: [number, number];
      zoomLevel?: number;
    }>(),
    {
      mode: 'subscribers',
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

  const isHeadlessTest = computed(
    () =>
      typeof navigator !== 'undefined' &&
      Boolean('webdriver' in navigator && (navigator as { webdriver?: boolean }).webdriver),
  );

  const isIspMode = computed<boolean>(() => Boolean(authStore.tenantFeatures?.isp_module_enabled));

  // Control RBAC: Solo ingenieros de NOC y administradores pueden acceder a WebFig
  const canAccessWebFig = computed<boolean>(() => {
    const role = authStore.currentRole || authStore.user?.role || '';
    const privileged = ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'NETWORK_ADMIN', 'SUPPORT_L2'];
    return privileged.includes(role);
  });

  // Estado de los 3 Toggles de Capa Independientes
  const showRouters = ref<boolean>(props.mode === 'inventory' || props.mode === 'wallboard');
  const showBoxes = ref<boolean>(isIspMode.value && props.mode === 'subscribers');
  const showSubscribers = ref<boolean>(props.mode === 'subscribers');

  // Filtro de estado
  const statusFilter = ref<'ALL' | 'ONLINE' | 'OFFLINE'>('ALL');

  // Elementos seleccionados para el drawer lateral
  const activeRouter = ref<RouterItem | null>(null);
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
  let boxesLayer: L.LayerGroup | null = null;
  let subscribersLayer: L.LayerGroup | null = null;
  let linesLayer: L.LayerGroup | null = null;
  let resizeObserver: ResizeObserver | null = null;

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
      boxesLayer = L.layerGroup().addTo(mapInstance);
      subscribersLayer = L.layerGroup().addTo(mapInstance);
      linesLayer = L.layerGroup().addTo(mapInstance);

      renderAllLayers();

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
    boxesLayer?.clearLayers();
    subscribersLayer?.clearLayers();
    linesLayer?.clearLayers();

    // 1. Capa de Routers de Red
    if (showRouters.value && routersLayer) {
      props.routers.forEach((r) => {
        if (r.latitude === undefined || r.longitude === undefined) return;
        const lat = Number(r.latitude);
        const lng = Number(r.longitude);
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

        const isOnline = r.is_reachable && r.admin_state === 'PRODUCTION';
        const color = isOnline ? '#00F0FF' : '#EF4444';
        const pulseClass = isOnline ? '' : 'router-pulse-danger';

        const icon = L.divIcon({
          className: 'rg-router-marker-container',
          html: `
            <div class="rg-router-marker ${pulseClass}" style="--marker-color: ${color};" title="${escapeHtml(r.display_name)}">
              <span class="router-icon">🏢</span>
              <span class="router-badge">${escapeHtml(r.display_name)}</span>
            </div>
          `,
          iconSize: [44, 44],
          iconAnchor: [22, 22],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', () => {
          activeRouter.value = r;
          activeBox.value = null;
          activeSubscriber.value = null;
          emit('select-router', r.id);
        });
        routersLayer?.addLayer(marker);
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
          @click="showRouters = !showRouters"
          :aria-pressed="showRouters ? 'true' : 'false'"
        >
          <span class="icon">🏢</span>
          <span class="label">Routers de Red</span>
          <span class="counter">({{ routers.length }})</span>
        </button>

        <button
          v-if="isIspMode"
          type="button"
          class="btn-layer-toggle btn-layer-boxes"
          :class="{ 'btn-layer-toggle--active': showBoxes }"
          @click="showBoxes = !showBoxes"
          :aria-pressed="showBoxes ? 'true' : 'false'"
        >
          <span class="icon">📦</span>
          <span class="label">Cajas NAP</span>
          <span class="counter">({{ opticalBoxes.length }})</span>
        </button>

        <button
          type="button"
          class="btn-layer-toggle btn-layer-subs"
          :class="{ 'btn-layer-toggle--active': showSubscribers }"
          @click="showSubscribers = !showSubscribers"
          :aria-pressed="showSubscribers ? 'true' : 'false'"
        >
          <span class="icon">💻</span>
          <span class="label">{{ isIspMode ? 'Abonados FTTH' : 'Dispositivos DHCP' }}</span>
          <span class="counter">({{ subscribers.length }})</span>
        </button>
      </div>

      <div class="filter-controls-group">
        <select v-model="statusFilter" class="rg-select-filter" aria-label="Filtrar por estado">
          <option value="ALL">Todos los Estados</option>
          <option value="ONLINE">🟢 Solo Online</option>
          <option value="OFFLINE">🔴 Solo Alertas/Offline</option>
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
          <strong>ALERTA DE CABECERA:</strong>
          <span>El router <strong>{{ downRouters[0].display_name }}</strong> se encuentra inalcanzable.</span>
          <span class="rca-affected">({{ affectedSubscribers.length }} abonados dependientes afectados por esta contingencia).</span>
        </div>
      </div>
      <div class="rca-actions">
        <button type="button" class="btn-rca-focus" @click="focusAffectedZone">
          🎯 Enfocar Zona Afectada
        </button>
        <button
          type="button"
          class="btn-rca-close"
          @click="showRcaBanner = false"
          aria-label="Descartar aviso de cabecera"
        >
          ✖️
        </button>
      </div>
    </aside>

    <!-- Contenedor del Mapa Cartográfico -->
    <main class="map-view-body">
      <div ref="mapContainer" class="unified-leaflet-container" tabindex="0" aria-label="Mapa de Red Unificado"></div>

      <!-- Drawer Lateral de Detalle con Gobernanza RBAC y Prevención de Colisiones -->
      <aside v-if="activeRouter || activeBox || activeSubscriber" class="unified-detail-drawer" aria-label="Panel de Información">
        <!-- Detalle de Router -->
        <div v-if="activeRouter" class="drawer-card router-detail-card">
          <div class="card-header">
            <h3>🏢 {{ activeRouter.display_name }}</h3>
            <button type="button" class="btn-close-card" @click="activeRouter = null">✖</button>
          </div>
          <div class="card-body">
            <p><strong>IP de Gestión:</strong> {{ activeRouter.ip_address }}</p>
            <p><strong>Rol de Red:</strong> {{ activeRouter.network_role || 'DISTRIBUTION' }}</p>
            <p><strong>Identidad ROS:</strong> {{ activeRouter.ros_identity || activeRouter.board_name || 'MikroTik Router' }}</p>
            <p>
              <strong>Estado de Enlace:</strong>
              <span :class="activeRouter.is_reachable ? 'badge-online' : 'badge-offline'">
                {{ activeRouter.is_reachable ? 'ONLINE' : 'CAÍDO / SIN ALCANCE' }}
              </span>
            </p>

            <!-- Gobernanza RBAC: Campo NO tiene acceso a WebFig -->
            <div class="webfig-access-section">
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
  max-width: calc(100vw - 2rem);
  background: rgba(15, 23, 42, 0.96);
  border: 1px solid rgba(0, 240, 255, 0.4);
  border-radius: 6px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.7);
  z-index: 1000;
  backdrop-filter: blur(8px);
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

.badge-offline {
  color: #EF4444;
  font-weight: 600;
}
</style>
