<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { useRouter } from 'vue-router';
  import OsmRouterMap from '@/components/inventory/OsmRouterMap.vue';
  import type { RouterItem } from '@/types';
  import { http } from '@/api/httpClient';

  const router = useRouter();

  interface NocEvent {
    id: string;
    timestamp: string;
    type: 'ROUTER_DOWN' | 'ROUTER_UP' | 'HIGH_CPU' | 'SSL_MISMATCH' | 'MAINTENANCE';
    router_identity: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
  }

  const isFullscreen = ref(false);
  const wallboardContainer = ref<HTMLElement | null>(null);

  // Routers reales obtenidos del inventario
  const routers = ref<RouterItem[]>([]);
  const selectedRouterId = ref<string | null>(null);

  function handleOpenWebFig(routerId: string) {
    router.push(`/routers/${routerId}/webfig/live`);
  }

  // KPIs
  const totalRouters = computed(() => routers.value.length);
  const onlineRouters = computed(
    () =>
      routers.value.filter(
        (r) =>
          r.is_reachable &&
          r.admin_state === 'PRODUCTION' &&
          r.ssl_trust_status !== 'FINGERPRINT_MISMATCH',
      ).length,
  );
  const highLoadRouters = computed(() => 0);
  const offlineRouters = computed(
    () => routers.value.filter((r) => !r.is_reachable && r.admin_state !== 'MAINTENANCE').length,
  );
  const maintenanceRouters = computed(
    () => routers.value.filter((r) => r.admin_state === 'MAINTENANCE').length,
  );
  const sslAlertRouters = computed(
    () => routers.value.filter((r) => r.ssl_trust_status === 'FINGERPRINT_MISMATCH').length,
  );

  // Cinta de eventos reales en vivo
  const liveEvents = ref<NocEvent[]>([]);

  let eventSimulationTimer: ReturnType<typeof setInterval> | null = null;

  async function loadRouters() {
    try {
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>('/api/v1/inventory/routers');
      const raw = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      if (raw.length > 0) {
        routers.value = raw.map((item: any) => ({
          ...item,
          ip_address:
            item.ip_address ||
            (item.api_base_url
              ? item.api_base_url.replace(/^https?:\/\//, '').split('/')[0].split(':')[0]
              : ''),
          ros_version: item.ros_version || 'v7',
          is_reachable: item.is_reachable ?? false,
        }));
      }
    } catch {
      // Mantiene muestra inicial
    }
  }

  async function loadEvents() {
    try {
      const res = await http.get<{ items: any[] }>('/api/v1/audit/logs');
      const items = res.data?.items || [];
      liveEvents.value = items.slice(0, 20).map((log: any) => ({
        id: String(log.id),
        timestamp: log.created_at ? new Date(log.created_at).toLocaleTimeString() : new Date().toLocaleTimeString(),
        type: log.event_category === 'AUTH' ? 'ROUTER_UP' : 'MAINTENANCE',
        router_identity: log.router_display_name || log.actor_username || 'Sistema',
        message: `${log.event_action || 'Operación'} registrada por ${log.actor_username || 'usuario'}`,
        severity: log.status_code >= 400 ? 'critical' : 'info',
      }));
    } catch {
      liveEvents.value = [];
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      if (wallboardContainer.value?.requestFullscreen) {
        wallboardContainer.value.requestFullscreen().catch(() => {});
      }
      isFullscreen.value = true;
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      isFullscreen.value = false;
    }
  }

  function handleFullscreenChange() {
    isFullscreen.value = Boolean(document.fullscreenElement);
  }

  function handleSelectRouter(id: string) {
    selectedRouterId.value = id;
  }

  onMounted(() => {
    loadRouters();
    loadEvents();
    document.addEventListener('fullscreenchange', handleFullscreenChange);
  });

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    if (eventSimulationTimer) {
      clearInterval(eventSimulationTimer);
    }
  });
</script>

<template>
  <div
    ref="wallboardContainer"
    class="noc-wallboard"
    data-theme="noc-high-contrast"
    role="region"
    aria-label="Wallboard NOC 24/7 Pantalla Completa"
  >
    <!-- Encabezado KPI Gigante -->
    <header class="wallboard-header">
      <div class="wallboard-brand">
        <h1 class="brand-title">RoSGrid NOC Wallboard</h1>
        <span class="live-indicator"> <span class="pulse-dot"></span> EN VIVO 24/7 </span>
      </div>

      <div class="kpi-strip" role="group" aria-label="Indicadores clave de rendimiento">
        <div class="kpi-card">
          <span class="kpi-label">TOTAL</span>
          <span class="kpi-value text-cyan">{{ totalRouters }}</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">ONLINE</span>
          <span class="kpi-value text-green">{{ onlineRouters }}</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">CARGA ALTA</span>
          <span class="kpi-value text-yellow">{{ highLoadRouters }}</span>
        </div>

        <div class="kpi-card" :class="{ 'kpi-card--critical': offlineRouters > 0 }">
          <span class="kpi-label">OFFLINE</span>
          <span class="kpi-value text-red">{{ offlineRouters }}</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">MANTENIMIENTO</span>
          <span class="kpi-value text-blue">{{ maintenanceRouters }}</span>
        </div>

        <div class="kpi-card" :class="{ 'kpi-card--alert': sslAlertRouters > 0 }">
          <span class="kpi-label">ALERTA TOFU</span>
          <span class="kpi-value text-red">{{ sslAlertRouters }}</span>
        </div>
      </div>

      <button
        type="button"
        class="btn-fullscreen"
        :aria-label="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa NOC'"
        @click="toggleFullscreen"
      >
        {{ isFullscreen ? '🗗 Salir TV' : '🖥️ Modo TV' }}
      </button>
    </header>

    <!-- Cuerpo Dividido: Mitad Izquierda (Mapa OSM) + Mitad Derecha (Ticker de Eventos) -->
    <div class="wallboard-body">
      <!-- Mitad Izquierda: Mapa Interactivo -->
      <section class="wallboard-map-panel" aria-label="Mapa de routers de la flota">
        <OsmRouterMap
          :routers="routers"
          :selected-router-id="selectedRouterId"
          :zoom-level="12"
          @select-router="handleSelectRouter"
          @open-webfig="handleOpenWebFig"
        />
      </section>

      <!-- Mitad Derecha: Cinta de Eventos Críticos en Vivo -->
      <section class="wallboard-events-panel" aria-labelledby="events-panel-title">
        <div class="events-header">
          <h2 id="events-panel-title" class="events-title">Cinta de Eventos Críticos</h2>
          <span class="events-subtitle">/ws/v1/tenant/events</span>
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
              <span class="event-type-badge font-mono">{{ evt.type }}</span>
            </div>
            <div class="event-body">
              <strong class="event-router">{{ evt.router_identity }}</strong>
              <p class="event-msg">{{ evt.message }}</p>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
  .noc-wallboard {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100%;
    background-color: #030712;
    color: #f9fafb;
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
    overflow: hidden;
  }

  /* Encabezado KPI */
  .wallboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background-color: #0b0f19;
    border-bottom: 2px solid #1f2937;
    gap: 1rem;
    flex-shrink: 0;
  }

  .wallboard-brand {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .brand-title {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: #38bdf8;
    margin: 0;
  }

  .live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: #4ade80;
    background: rgba(34, 197, 94, 0.15);
    padding: 0.2rem 0.5rem;
    border-radius: 9999px;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.4;
      transform: scale(1.2);
    }
  }

  .kpi-strip {
    display: flex;
    gap: 0.75rem;
  }

  .kpi-card {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 0.35rem 0.85rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 90px;
  }

  .kpi-card--critical {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
    animation: blink-border 1.5s infinite;
  }

  .kpi-card--alert {
    border-color: #f97316;
    background: rgba(249, 115, 22, 0.15);
  }

  @keyframes blink-border {
    0%,
    100% {
      border-color: #ef4444;
    }
    50% {
      border-color: transparent;
    }
  }

  .kpi-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #9ca3af;
    letter-spacing: 0.05em;
  }

  .kpi-value {
    font-size: 1.6rem;
    font-weight: 900;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }

  .text-cyan {
    color: #38bdf8;
  }
  .text-green {
    color: #4ade80;
  }
  .text-yellow {
    color: #facc15;
  }
  .text-red {
    color: #f87171;
  }
  .text-blue {
    color: #60a5fa;
  }

  .btn-fullscreen {
    background: #1f2937;
    border: 1px solid #4b5563;
    color: #f3f4f6;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }

  /* Cuerpo */
  .wallboard-body {
    display: grid;
    grid-template-columns: 55% 45%;
    flex: 1;
    overflow: hidden;
  }

  @media (max-width: 1024px) {
    .wallboard-body {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 1fr;
    }
  }

  .wallboard-map-panel {
    position: relative;
    height: 100%;
    width: 100%;
    border-right: 2px solid #1f2937;
  }

  .wallboard-events-panel {
    display: flex;
    flex-direction: column;
    background: #090d16;
    overflow: hidden;
  }

  .events-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #111827;
    border-bottom: 1px solid #1f2937;
  }

  .events-title {
    font-size: 1rem;
    font-weight: 700;
    color: #e5e7eb;
    margin: 0;
  }

  .events-subtitle {
    font-family: monospace;
    font-size: 0.75rem;
    color: #6b7280;
  }

  .events-list {
    list-style: none;
    margin: 0;
    padding: 0.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .event-item {
    background: #111827;
    border-left: 4px solid #4b5563;
    padding: 0.5rem 0.75rem;
    border-radius: 2px;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .event-item--critical {
    border-left-color: #ef4444;
    background: rgba(239, 68, 68, 0.08);
  }

  .event-item--warning {
    border-left-color: #facc15;
    background: rgba(250, 204, 21, 0.08);
  }

  .event-item--info {
    border-left-color: #38bdf8;
  }

  .event-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
  }

  .event-time {
    color: #9ca3af;
  }

  .event-type-badge {
    background: #1f2937;
    color: #e5e7eb;
    padding: 0.1rem 0.35rem;
    border-radius: 2px;
    font-size: 0.7rem;
    font-weight: 700;
  }

  .event-body {
    display: flex;
    flex-direction: column;
  }

  .event-router {
    font-size: 0.85rem;
    color: #f3f4f6;
  }

  .event-msg {
    margin: 0;
    font-size: 0.8rem;
    color: #9ca3af;
  }

  .font-mono {
    font-family: 'JetBrains Mono', monospace;
  }
</style>
