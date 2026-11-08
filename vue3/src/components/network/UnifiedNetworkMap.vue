<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import L from 'leaflet';
  import type {
    OpticalBoxItem,
    RouterItem,
    SubscriberDeviceItem,
    OperationalStatusResponse,
    TopologyEdge,
    L2TopologyResponse,
  } from '@/types';
  import { http } from '@/api/httpClient';
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

  const isIspMode = computed<boolean>(() => {
    if (authStore.tenantFeatures?.isp_module_enabled === false) return false;
    return (
      authStore.isFeatureEnabled('isp_module_enabled') ||
      Boolean(authStore.tenantFeatures?.isp_module_enabled) ||
      props.opticalBoxes.length > 0
    );
  });

  const canShowBoxesLayer = computed<boolean>(
    () =>
      isIspMode.value ||
      props.opticalBoxes.length > 0 ||
      props.mode === 'subscribers' ||
      props.mode === 'wallboard',
  );

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

  // Estado de los 4 Toggles de Capa Independientes
  const showRouters = ref<boolean>(props.mode === 'inventory' || props.mode === 'wallboard');
  const showBoxes = ref<boolean>(canShowBoxesLayer.value && props.mode === 'subscribers');
  const showSubscribers = ref<boolean>(props.mode === 'subscribers');
  const showL2Links = ref<boolean>(props.mode === 'wallboard');
  const l2Edges = ref<TopologyEdge[]>([]);
  const activeL2Edge = ref<TopologyEdge | null>(null);

  // Filtro de estado
  const statusFilter = ref<'ALL' | 'ONLINE' | 'OFFLINE' | 'MAINTENANCE'>('ALL');

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
      (r) => (!r.is_reachable && r.admin_state !== 'MAINTENANCE') || r.admin_state === 'DECOMMISSIONED',
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
  let l2LinksLayer: L.LayerGroup | null = null;
  let resizeObserver: ResizeObserver | null = null;

  async function loadL2TopologyEdges(): Promise<void> {
    try {
      const res = await http.get<L2TopologyResponse>('/api/v1/topology/l2');
      l2Edges.value = Array.isArray(res.data?.edges) ? res.data.edges : [];
      renderAllLayers();
    } catch {
      l2Edges.value = [];
    }
  }

  async function toggleL2Links(): Promise<void> {
    showL2Links.value = !showL2Links.value;
    if (showL2Links.value && l2Edges.value.length === 0) {
      await loadL2TopologyEdges();
    } else {
      renderAllLayers();
    }
  }

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
      const initialCenter =
        props.centerCoordinates &&
        (props.centerCoordinates[0] !== 10.4806 || props.centerCoordinates[1] !== -66.9036)
          ? props.centerCoordinates
          : authStore.tenantHqCoordinates;

      mapInstance = L.map(mapContainer.value, {
        zoomControl: false,
        attributionControl: false,
      }).setView(initialCenter, props.zoomLevel);

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
      }).addTo(mapInstance);

      routersLayer = L.layerGroup().addTo(mapInstance);
      spiderLayer = L.layerGroup().addTo(mapInstance);
      boxesLayer = L.layerGroup().addTo(mapInstance);
      subscribersLayer = L.layerGroup().addTo(mapInstance);
      linesLayer = L.layerGroup().addTo(mapInstance);
      l2LinksLayer = L.layerGroup().addTo(mapInstance);

      if (showL2Links.value) {
        loadL2TopologyEdges();
      }

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
      return '#EF4444'; // Rojo (Caído / Aislado)
    }
    const lat = sub.ping_latency_ms;
    const loss = sub.packet_loss_pct;
    if (
      sub.status === 'PENDING_INSTALL' ||
      (lat !== undefined && lat !== null && lat >= 40) ||
      (loss !== undefined && loss !== null && loss >= 1)
    ) {
      return '#F59E0B'; // Naranja (Degradado / Pendiente)
    }
    return '#10B981'; // Verde Esmeralda (Online Óptimo)
  }

  function resolveSubscriberBaseCoords(s: SubscriberDeviceItem): [number, number] | null {
    const rawLat = Number(s.latitude);
    const rawLng = Number(s.longitude);
    if (!Number.isNaN(rawLat) && !Number.isNaN(rawLng) && !(rawLat === 0 && rawLng === 0)) {
      return [rawLat, rawLng];
    }
    if (s.optical_box_id || s.optical_box) {
      const parentBox = props.opticalBoxes.find(
        (b) => b.id === s.optical_box_id || b.box_code === s.optical_box,
      );
      if (parentBox) {
        const bLat = Number(parentBox.latitude);
        const bLng = Number(parentBox.longitude);
        if (!Number.isNaN(bLat) && !Number.isNaN(bLng) && !(bLat === 0 && bLng === 0)) {
          return [bLat, bLng];
        }
      }
    }
    if (s.router_id) {
      const parentRouter = props.routers.find((r) => r.id === s.router_id);
      if (parentRouter) {
        const rLat = Number(parentRouter.latitude);
        const rLng = Number(parentRouter.longitude);
        if (!Number.isNaN(rLat) && !Number.isNaN(rLng) && !(rLat === 0 && rLng === 0)) {
          return [rLat, rLng];
        }
      }
    }
    return null;
  }

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
    if (canShowBoxesLayer.value && showBoxes.value) {
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
    if (coords.length === 0) {
      try {
        mapInstance.setView(authStore.tenantHqCoordinates, props.zoomLevel);
      } catch {
        // Ignorar en entornos JSDOM sin layout
      }
      return;
    }

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

  function renderAllLayers(): void {
    if (!mapInstance || isHeadlessTest.value) return;

    routersLayer?.clearLayers();
    spiderLayer?.clearLayers();
    boxesLayer?.clearLayers();
    subscribersLayer?.clearLayers();
    linesLayer?.clearLayers();
    l2LinksLayer?.clearLayers();

    const filteredMapRouters = props.routers.filter((r) => {
      if (statusFilter.value === 'MAINTENANCE') return r.admin_state === 'MAINTENANCE';
      if (statusFilter.value === 'ONLINE') return r.is_reachable && r.admin_state !== 'MAINTENANCE';
      if (statusFilter.value === 'OFFLINE') return !r.is_reachable && r.admin_state !== 'MAINTENANCE';
      return true;
    });
    const groups = buildLocationGroups(filteredMapRouters);

    // 1. Capa de Routers de Red (● Círculos de color con soporte para Sitios Co-ubicados)
    if (showRouters.value && routersLayer) {
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

    // 2. Capa de Cajas NAP FTTH (■ Pequeños cuadrados de colores según ocupación)
    const renderedBoxCoords = new Map<string, [number, number]>();
    if (canShowBoxesLayer.value && showBoxes.value && boxesLayer) {
      props.opticalBoxes.forEach((b, boxIdx) => {
        const baseLat = Number(b.latitude);
        const baseLng = Number(b.longitude);
        if (Number.isNaN(baseLat) || Number.isNaN(baseLng) || (baseLat === 0 && baseLng === 0)) return;

        let lat = baseLat;
        let lng = baseLng;
        const collidesWithRouter = groups.some((g) => getDistanceMeters(g.lat, g.lng, baseLat, baseLng) <= 18);
        if (collidesWithRouter) {
          const angle = Math.PI / 4 + boxIdx * (Math.PI / 3);
          lat = baseLat + 0.00022 * Math.sin(angle);
          lng = baseLng + 0.00022 * Math.cos(angle);
          try {
            const feederLine = L.polyline([[baseLat, baseLng], [lat, lng]], {
              color: '#10B981',
              weight: 1.5,
              opacity: 0.65,
              dashArray: '4, 4',
            });
            linesLayer?.addLayer(feederLine);
          } catch {
            // Ignorar en entorno JSDOM sin motor vectorial
          }
        }
        renderedBoxCoords.set(b.id, [lat, lng]);

        const occ = b.occupied_ports_count || 0;
        const cap = b.capacity_ports || 16;
        const ratio = cap > 0 ? occ / cap : 0;
        const color = occ >= cap ? '#EF4444' : ratio >= 0.8 ? '#F59E0B' : '#10B981';

        const icon = L.divIcon({
          className: 'rg-box-marker-container',
          html: `
            <div class="rg-box-marker" style="--box-color: ${color};" role="button" tabindex="0" title="Caja NAP ${escapeHtml(b.box_code)} (${occ}/${cap} puertos)">
              <div class="box-square"></div>
              <span class="box-badge">${escapeHtml(b.box_code)} · ${occ}/${cap}</span>
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', () => {
          activeBox.value = b;
          activeRouter.value = null;
          activeLocationGroup.value = null;
          activeSubscriber.value = null;
          emit('select-box', b.id);
        });
        boxesLayer?.addLayer(marker);
      });
    }

    // 3. Capa de Clientes / Dispositivos (▲ Pequeños triángulos de colores según estado)
    if (showSubscribers.value && subscribersLayer) {
      const anchorBuckets = new Map<string, number>();

      props.subscribers.forEach((s) => {
        // Filtrado rápido por estado
        if (statusFilter.value === 'MAINTENANCE') return;
        if (statusFilter.value === 'ONLINE' && s.last_reachability_status === 'OFFLINE') return;
        if (statusFilter.value === 'OFFLINE' && s.last_reachability_status !== 'OFFLINE') return;

        const baseCoords = resolveSubscriberBaseCoords(s);
        if (!baseCoords) return;

        let [lat, lng] = baseCoords;
        const anchorKey = `${lat.toFixed(4)},${lng.toFixed(4)}`;
        const subIndexAtAnchor = anchorBuckets.get(anchorKey) || 0;
        anchorBuckets.set(anchorKey, subIndexAtAnchor + 1);

        const collidesWithRouterOrBox =
          subIndexAtAnchor > 0 ||
          groups.some((g) => getDistanceMeters(g.lat, g.lng, lat, lng) <= 20) ||
          props.opticalBoxes.some(
            (b) => getDistanceMeters(Number(b.latitude), Number(b.longitude), lat, lng) <= 20,
          );

        const originLat = lat;
        const originLng = lng;
        if (collidesWithRouterOrBox) {
          const angle = -Math.PI / 3 + subIndexAtAnchor * ((2 * Math.PI) / 8);
          const radiusDeg = 0.00032 + Math.floor(subIndexAtAnchor / 8) * 0.00018;
          lat = originLat + radiusDeg * Math.sin(angle);
          lng = originLng + radiusDeg * Math.cos(angle);

          const parentBoxRendered = s.optical_box_id ? renderedBoxCoords.get(s.optical_box_id) : undefined;
          const lineStart: [number, number] = parentBoxRendered || [originLat, originLng];
          try {
            const dropLine = L.polyline([lineStart, [lat, lng]], {
              color: '#38BDF8',
              weight: 1.2,
              opacity: 0.55,
              dashArray: '2, 4',
            });
            linesLayer?.addLayer(dropLine);
          } catch {
            // Ignorar en entorno JSDOM
          }
        }

        const color = getSubscriberColor(s);
        const isDownByRouter = downRouters.value.some((r) => r.id === s.router_id);
        const labelText = s.customer_name || s.endpoint_identifier;

        const icon = L.divIcon({
          className: 'rg-sub-marker-container',
          html: `
            <div class="rg-sub-marker ${isDownByRouter ? 'sub-rca-pulse' : ''}" style="--sub-color: ${color};" role="button" tabindex="0" title="Cliente: ${escapeHtml(labelText)} (${s.last_reachability_status || 'ONLINE'})">
              <svg class="sub-triangle-svg" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                <polygon points="10,2 19,18 1,18" fill="${color}" stroke="#0B0F19" stroke-width="2.2" stroke-linejoin="round" />
              </svg>
              <span class="sub-dot"></span>
              <span class="sub-label">${escapeHtml(labelText)}</span>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', async () => {
          activeSubscriber.value = s;
          activeRouter.value = null;
          activeLocationGroup.value = null;
          activeBox.value = null;
          emit('select-subscriber', s.id);
          operationalLock.value = await fieldOpsStore.fetchOperationalStatus(s.id);
        });
        subscribersLayer?.addLayer(marker);
      });
    }

    // 4. Capa de Enlaces Físicos L2 / PoE (Polilíneas Leaflet)
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

    if (!hasInitialAutoCentered.value) {
      fitMapToActiveNodes(false);
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

  watch([showRouters, showBoxes, showSubscribers, showL2Links, statusFilter, () => props.routers, () => props.opticalBoxes, () => props.subscribers], () => {
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

  watch(
    () => authStore.tenantHqCoordinates,
    (newHq) => {
      if (!mapInstance || isHeadlessTest.value) return;
      if (collectAllValidCoordinates().length === 0) {
        try {
          mapInstance.setView(newHq, props.zoomLevel);
        } catch {
          // Ignorar en entornos JSDOM
        }
      }
    },
  );

  defineExpose({
    activeRouter,
    activeLocationGroup,
    activeL2Edge,
    showL2Links,
    l2Edges,
    toggleL2Links,
    loadL2TopologyEdges,
    buildLocationGroups,
    getDistanceMeters,
    getGroupStatus,
    renderAllLayers,
    spiderfyGroup,
    clearSpiderLayer,
    resolveSubscriberBaseCoords,
    getSubscriberColor,
    hasInitialAutoCentered,
    collectAllValidCoordinates,
    fitMapToActiveNodes,
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
    <!-- Barra Táctica Superior: 4 Toggles de Capa Independientes con Feature Flags -->
    <header class="unified-map-toolbar">
      <div class="layers-toggles-group" role="toolbar" aria-label="Controles de Capa del Mapa">
        <button
          type="button"
          class="btn-layer-toggle btn-layer-routers"
          :class="{ 'btn-layer-toggle--active': showRouters }"
          :aria-pressed="showRouters ? 'true' : 'false'"
          @click="showRouters = !showRouters"
        >
          <span class="icon shape-legend shape-legend--circle" aria-hidden="true">●</span>
          <span class="label">{{ t('network_map.layer_routers') }}</span>
          <span class="counter">({{ routers.length }})</span>
        </button>

        <button
          v-if="canShowBoxesLayer"
          type="button"
          class="btn-layer-toggle btn-layer-boxes"
          :class="{ 'btn-layer-toggle--active': showBoxes }"
          :aria-pressed="showBoxes ? 'true' : 'false'"
          @click="showBoxes = !showBoxes"
        >
          <span class="icon shape-legend shape-legend--square" aria-hidden="true">■</span>
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
          <span class="icon shape-legend shape-legend--triangle" aria-hidden="true">▲</span>
          <span class="label">{{ t('network_map.layer_subs') }}</span>
          <span class="counter">({{ subscribers.length }})</span>
        </button>

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
      </div>

      <div class="filter-controls-group">
        <select v-model="statusFilter" class="rg-select-filter" aria-label="Filtrar por estado">
          <option value="ALL">{{ t('network_map.filter_all') }}</option>
          <option value="ONLINE">{{ t('network_map.filter_online') }}</option>
          <option value="MAINTENANCE">{{ t('enums.admin_state.MAINTENANCE', 'En Mantenimiento') }}</option>
          <option value="OFFLINE">{{ t('network_map.filter_offline') }}</option>
        </select>
        <button
          id="btn-map-fit-bounds"
          type="button"
          class="btn-layer-toggle"
          :title="t('network_map.btn_center_fleet', 'Centrar mapa en los equipos de la red')"
          @click="fitMapToActiveNodes(true)"
        >
          🎯 {{ t('network_map.btn_center_fleet', 'Centrar Red') }}
        </button>
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
      <aside
        v-if="activeRouter || activeLocationGroup || activeBox || activeSubscriber || activeL2Edge"
        class="unified-detail-drawer"
        :class="{ 'unified-detail-drawer--wallboard': props.mode === 'wallboard' }"
        aria-label="Panel de Información"
      >
        <!-- Detalle de Enlace Físico L2 / PoE -->
        <div v-if="activeL2Edge" class="drawer-card l2-edge-detail-card">
          <div class="card-header">
            <h3>🔗 Enlace Físico Capa 2 ({{ activeL2Edge.protocol }})</h3>
            <button type="button" class="btn-close-card" @click="activeL2Edge = null">✖</button>
          </div>
          <div class="card-body">
            <p><strong>Interfaz Origen:</strong> <code>{{ activeL2Edge.source_interface }}</code></p>
            <p><strong>Interfaz Destino:</strong> <code>{{ activeL2Edge.target_interface }}</code></p>
            <p v-if="activeL2Edge.link_speed"><strong>Velocidad:</strong> {{ activeL2Edge.link_speed }}</p>
            <p>
              <strong>Alimentación PoE:</strong>
              <span v-if="activeL2Edge.is_poe_delivering">⚡ {{ activeL2Edge.poe_power_watts ?? activeL2Edge.poe_watts ?? 0 }}W <template v-if="activeL2Edge.poe_status">({{ activeL2Edge.poe_status }})</template></span>
              <span v-else>Solo Datos</span>
            </p>
          </div>
        </div>

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
  background: var(--rg-bg-canvas);
  position: relative;
  overflow: hidden;
}

.unified-map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.625rem 1rem;
  background: var(--rg-bg-surface);
  border-bottom: 1px solid var(--rg-border-panel);
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
  background: var(--rg-bg-elevated);
  border: 1px solid var(--rg-border-panel);
  border-radius: 4px;
  color: var(--rg-text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-layer-toggle:hover {
  background: var(--rg-btn-action-bg);
  color: var(--rg-text-primary);
}

.btn-layer-toggle--active {
  background: color-mix(in srgb, var(--rg-accent-cyan) 15%, var(--rg-bg-surface));
  border-color: var(--rg-accent-cyan);
  color: var(--rg-accent-cyan);
  box-shadow: var(--rg-cyan-glow);
}

.counter {
  font-size: 0.75rem;
  opacity: 0.8;
}

.filter-controls-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.rg-select-filter {
  padding: 0.375rem 0.625rem;
  background: var(--rg-bg-input);
  border: 1px solid var(--rg-border-panel);
  color: var(--rg-text-primary);
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
  background: color-mix(in srgb, var(--rg-bg-surface) 94%, transparent);
  border: 1px solid var(--rg-border-panel);
  border-radius: 6px;
  box-shadow: var(--rg-shadow-lg);
  color: var(--rg-text-primary);
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.unified-detail-drawer--wallboard {
  left: 1rem;
  right: auto;
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
  border-bottom: 1px solid var(--rg-border-grid);
  padding-bottom: 0.5rem;
}

.card-header h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--rg-accent-cyan);
  margin: 0;
}

.btn-close-card {
  background: transparent;
  border: none;
  color: var(--rg-text-muted);
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

/* Marcadores Geométricos de Cajas NAP (■ Cuadrados de Colores) */
.rg-box-marker-container {
  background: transparent !important;
  border: none !important;
}

.rg-box-marker {
  width: 24px;
  height: 24px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.box-square {
  width: 15px;
  height: 15px;
  background-color: var(--box-color, #10B981);
  border: 2px solid #0B0F19;
  border-radius: 3px;
  box-shadow: 0 0 10px var(--box-color, #10B981);
  z-index: 2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rg-box-marker:hover .box-square {
  transform: scale(1.25);
  box-shadow: 0 0 15px var(--box-color, #10B981);
}

.box-badge {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 3px;
  background: rgba(11, 15, 25, 0.92);
  color: #E2E8F0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid var(--box-color, #10B981);
  pointer-events: none;
  z-index: 3;
}

/* Marcadores Geométricos de Clientes / ONUs (▲ Triángulos de Colores) */
.rg-sub-marker-container {
  background: transparent !important;
  border: none !important;
}

.rg-sub-marker {
  width: 22px;
  height: 22px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.sub-triangle-svg {
  filter: drop-shadow(0 0 6px var(--sub-color, #10B981));
  z-index: 2;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.rg-sub-marker:hover .sub-triangle-svg {
  transform: scale(1.28);
  filter: drop-shadow(0 0 12px var(--sub-color, #10B981));
}

.sub-dot {
  display: none;
}

.sub-label {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 2px;
  background: rgba(11, 15, 25, 0.9);
  color: #F8FAFC;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.64rem;
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.18);
  pointer-events: none;
  z-index: 3;
}

.sub-rca-pulse .sub-triangle-svg {
  animation: pin-pulsate-danger 1.2s infinite ease-out;
}

.shape-legend {
  font-size: 0.95rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
}

.shape-legend--circle {
  color: var(--rg-primary, #00F0FF);
}

.shape-legend--square {
  color: #10B981;
}

.shape-legend--triangle {
  color: #38BDF8;
}

.shape-legend--line {
  color: #06B6D4;
  font-weight: 900;
}

.btn-layer-l2.btn-layer-toggle--active {
  background: rgba(6, 182, 212, 0.18);
  border-color: #06B6D4;
  color: #06B6D4;
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);
}

.l2-edge-detail-card {
  border-left: 3px solid #06B6D4;
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
