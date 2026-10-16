<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import OsmRouterMap from '@/components/inventory/OsmRouterMap.vue';
  import type { RouterItem } from '@/types';
  import { http } from '@/api/httpClient';

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

  // Muestra inicial de routers para el mapa y KPIs
  const routers = ref<RouterItem[]>([
    {
      id: 'r-01',
      tenant_id: 't-default',
      display_name: 'RB5009-Core-01',
      ros_identity: 'RB5009-Core-01',
      ip_address: '192.168.88.1',
      api_port: 443,
      ros_version: '7.16.1',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
      ssl_trust_status: 'TRUSTED_PINNED',
      admin_state: 'PRODUCTION',
      latitude: 10.4806,
      longitude: -66.9036,
    },
    {
      id: 'r-02',
      tenant_id: 't-default',
      display_name: 'CCR2004-Border-02',
      ros_identity: 'CCR2004-Border-02',
      ip_address: '10.0.0.1',
      api_port: 443,
      ros_version: '7.15.2',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
      ssl_trust_status: 'TRUSTED_PINNED',
      admin_state: 'PRODUCTION',
      latitude: 10.495,
      longitude: -66.88,
    },
    {
      id: 'r-03',
      tenant_id: 't-default',
      display_name: 'hAP-ax3-Branch-01',
      ros_identity: 'hAP-ax3-Branch-01',
      ip_address: '172.16.10.1',
      api_port: 443,
      ros_version: '7.15.2',
      is_reachable: false,
      last_seen_at: new Date(Date.now() - 300000).toISOString(),
      ssl_trust_status: 'TRUSTED_PINNED',
      admin_state: 'PRODUCTION',
      latitude: 10.51,
      longitude: -66.92,
    },
    {
      id: 'r-04',
      tenant_id: 't-default',
      display_name: 'NetMetal-Tower-AP',
      ros_identity: 'NetMetal-Tower-AP',
      ip_address: '10.50.0.1',
      api_port: 443,
      ros_version: '7.14.3',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
      ssl_trust_status: 'FINGERPRINT_MISMATCH',
      admin_state: 'PRODUCTION',
      latitude: 10.47,
      longitude: -66.95,
    },
    {
      id: 'r-05',
      tenant_id: 't-default',
      display_name: 'CRS326-Switch-Core',
      ros_identity: 'CRS326-Switch-Core',
      ip_address: '10.100.0.1',
      api_port: 443,
      ros_version: '7.16.1',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
      ssl_trust_status: 'TRUSTED_PINNED',
      admin_state: 'MAINTENANCE',
      latitude: 10.46,
      longitude: -66.89,
    },
  ]);

  const selectedRouterId = ref<string | null>(null);

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
  const highLoadRouters = ref(1); // Simulado de telemetría viva
  const offlineRouters = computed(
    () => routers.value.filter((r) => !r.is_reachable && r.admin_state !== 'MAINTENANCE').length,
  );
  const maintenanceRouters = computed(
    () => routers.value.filter((r) => r.admin_state === 'MAINTENANCE').length,
  );
  const sslAlertRouters = computed(
    () => routers.value.filter((r) => r.ssl_trust_status === 'FINGERPRINT_MISMATCH').length,
  );

  // Cinta de eventos en vivo
  const liveEvents = ref<NocEvent[]>([
    {
      id: 'evt-01',
      timestamp: new Date().toLocaleTimeString(),
      type: 'ROUTER_DOWN',
      router_identity: 'hAP-ax3-Branch-01',
      message: 'Enlace caído o timeout HTTP REST v7 (> 5000ms)',
      severity: 'critical',
    },
    {
      id: 'evt-02',
      timestamp: new Date(Date.now() - 45000).toLocaleTimeString(),
      type: 'SSL_MISMATCH',
      router_identity: 'NetMetal-Tower-AP',
      message: 'Alerta SSL TOFU: Huella SHA-256 no coincide con el registro previo',
      severity: 'critical',
    },
    {
      id: 'evt-03',
      timestamp: new Date(Date.now() - 120000).toLocaleTimeString(),
      type: 'HIGH_CPU',
      router_identity: 'CCR2004-Border-02',
      message: 'CPU al 94% sostenido por convergencia BGP v7',
      severity: 'warning',
    },
    {
      id: 'evt-04',
      timestamp: new Date(Date.now() - 300000).toLocaleTimeString(),
      type: 'MAINTENANCE',
      router_identity: 'CRS326-Switch-Core',
      message: 'Equipo ingresó en ventana de mantenimiento programada',
      severity: 'info',
    },
    {
      id: 'evt-05',
      timestamp: new Date(Date.now() - 600000).toLocaleTimeString(),
      type: 'ROUTER_UP',
      router_identity: 'RB5009-Core-01',
      message: 'Sesión REST HTTPS v7 re-establecida y telemetría activa',
      severity: 'info',
    },
  ]);

  let eventSimulationTimer: ReturnType<typeof setInterval> | null = null;

  async function loadRouters() {
    try {
      const res = await http.get<{ items: RouterItem[] }>('/api/v1/routers');
      if (res.data?.items && res.data.items.length > 0) {
        routers.value = res.data.items;
      }
    } catch {
      // Mantiene muestra inicial
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
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    // Simula llegada de eventos en tiempo real para modo NOC
    eventSimulationTimer = setInterval(() => {
      const now = new Date();
      const mockTypes: NocEvent['type'][] = ['ROUTER_UP', 'HIGH_CPU', 'ROUTER_DOWN'];
      const pickedType = mockTypes[Math.floor(Math.random() * mockTypes.length)];
      liveEvents.value.unshift({
        id: `evt-${Date.now()}`,
        timestamp: now.toLocaleTimeString(),
        type: pickedType,
        router_identity: 'RB5009-Core-01',
        message:
          pickedType === 'ROUTER_UP'
            ? 'Latencia ICMP normalizada (< 4ms)'
            : pickedType === 'HIGH_CPU'
              ? 'Pico transitorio de CPU al 88%'
              : 'Verificación periódica OK',
        severity:
          pickedType === 'ROUTER_DOWN'
            ? 'critical'
            : pickedType === 'HIGH_CPU'
              ? 'warning'
              : 'info',
      });
      if (liveEvents.value.length > 20) {
        liveEvents.value.pop();
      }
    }, 15000);
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
        />
      </section>

      <!-- Mitad Derecha: Cinta de Eventos Críticos en Vivo -->
      <section class="wallboard-events-panel" aria-labelledby="events-panel-title">
        <div class="events-header">
          <h2 id="events-panel-title" class="events-title">Cinta de Eventos Críticos</h2>
          <span class="events-subtitle">/ws/v1/tenant/events</span>
        </div>

        <ul class="events-list" role="log" aria-live="polite">
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
