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

  const selectedRouter = computed(() => {
    if (!selectedRouterId.value) return null;
    return routers.value.find((r) => r.id === selectedRouterId.value) || null;
  });

  function handleOpenWebFig(routerId: string) {
    if (isFullscreen.value && typeof document !== 'undefined' && document.fullscreenElement) {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      isFullscreen.value = false;
    }
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

  // Alerta de Caída Masiva (Mass Outage) — specs/32 §5.3
  interface MassOutageAlertData {
    active: boolean;
    title: string;
    message: string;
    affectedCount: number;
    ponPort?: string;
    opticalBox?: string;
    timestamp?: string;
  }

  const massOutageAlert = ref<MassOutageAlertData>({
    active: false,
    title: 'ALERTA DE CAÍDA MASIVA DETECTADA',
    message: '',
    affectedCount: 0,
  });

  const isAudioSilenced = ref(false);

  function playTacticalChime(): void {
    if (isAudioSilenced.value || typeof window === 'undefined') return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
    } catch {
      // AudioContext protegido o restringido
    }
  }

  function triggerMassOutage(count: number, ponPort?: string, opticalBox?: string): void {
    massOutageAlert.value = {
      active: true,
      title: '🚨 ALERTA DE CAÍDA MASIVA DETECTADA (MASS OUTAGE)',
      message: `Caída simultánea de ${count} equipos superando el umbral técnico. Sector afectado: Puerto ${ponPort || 'PON'} / Caja ${opticalBox || 'NAP'}`,
      affectedCount: count,
      ponPort,
      opticalBox,
      timestamp: new Date().toLocaleTimeString(),
    };
    playTacticalChime();
  }

  function acknowledgeOutage(): void {
    massOutageAlert.value.active = false;
  }

  let eventSimulationTimer: ReturnType<typeof setInterval> | null = null;

  async function loadRouters() {
    try {
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>(
        '/api/v1/inventory/routers',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      if (raw.length > 0) {
        routers.value = raw.map((item: any) => ({
          ...item,
          latitude:
            item.latitude !== null && item.latitude !== undefined && item.latitude !== ''
              ? Number(item.latitude)
              : undefined,
          longitude:
            item.longitude !== null && item.longitude !== undefined && item.longitude !== ''
              ? Number(item.longitude)
              : undefined,
          ip_address:
            item.ip_address ||
            (item.api_base_url
              ? item.api_base_url
                  .replace(/^https?:\/\//, '')
                  .split('/')[0]
                  .split(':')[0]
              : ''),
          ros_version: item.ros_version || 'v7',
          is_reachable: item.is_reachable ?? false,
        }));
      }

      if (offlineRouters.value >= 10 && !massOutageAlert.value.active) {
        triggerMassOutage(offlineRouters.value, 'INFRAESTRUCTURA', 'CORE/ROUTERS');
      }
    } catch {
      // Mantiene muestra inicial
    }
  }

  async function loadEvents() {
    try {
      const res = await http.get<{ items: any[] }>('/api/v1/audit/logs');
      const items = res.data?.items || [];

      // Detección de caída masiva en eventos de auditoría recientes
      const outageLog = items.find(
        (log: any) =>
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED',
      );
      if (outageLog && !massOutageAlert.value.active) {
        const after = outageLog.after_state || {};
        triggerMassOutage(
          Number(after.affected_onus_count || 10),
          after.pon_port,
          after.optical_box,
        );
      }

      liveEvents.value = items.slice(0, 20).map((log: any) => ({
        id: String(log.id),
        timestamp: log.created_at
          ? new Date(log.created_at).toLocaleTimeString()
          : new Date().toLocaleTimeString(),
        type:
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED'
            ? 'ROUTER_DOWN'
            : log.event_category === 'AUTH'
              ? 'ROUTER_UP'
              : 'MAINTENANCE',
        router_identity: log.router_display_name || log.actor_username || 'Sistema',
        message: `${log.event_action || 'Operación'} registrada por ${log.actor_username || 'usuario'}`,
        severity:
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED'
            ? 'critical'
            : log.status_code >= 400
              ? 'critical'
              : 'info',
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

    <!-- Banner de Alta Visibilidad de Caída Masiva (specs/32 §5.3) -->
    <transition name="outage-slide">
      <div
        v-if="massOutageAlert.active"
        class="mass-outage-banner"
        role="alert"
        aria-live="assertive"
      >
        <div class="outage-icon-box">
          <span class="outage-siren">🚨</span>
        </div>
        <div class="outage-text-group">
          <div class="outage-headline">
            <strong>{{ massOutageAlert.title }}</strong>
            <span class="outage-count-tag font-mono"
              >{{ massOutageAlert.affectedCount }} Equipos</span
            >
          </div>
          <div class="outage-description">
            {{ massOutageAlert.message }}
          </div>
        </div>
        <div class="outage-actions">
          <button
            type="button"
            class="btn-outage-silence"
            :aria-label="isAudioSilenced ? 'Activar sirena' : 'Silenciar sirena'"
            @click="isAudioSilenced = !isAudioSilenced"
          >
            {{ isAudioSilenced ? '🔔 Activar Sonido' : '🔇 Silenciar' }}
          </button>
          <button
            type="button"
            class="btn-outage-ack"
            id="btn-ack-mass-outage"
            @click="acknowledgeOutage"
          >
            Reconocer Alarma
          </button>
        </div>
      </div>
    </transition>

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

        <!-- Floating HUD de equipo seleccionado con botón directo a WebFig -->
        <transition name="hud-fade">
          <div
            v-if="selectedRouter"
            class="wallboard-router-hud"
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
                type="button"
                class="btn-hud-webfig"
                id="btn-wallboard-open-webfig"
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

  /* Banner Táctico de Caída Masiva (specs/32 §5.3) */
  .mass-outage-banner {
    background: linear-gradient(90deg, #7f1d1d, #b91c1c, #dc2626);
    color: #fff;
    padding: 0.85rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.25rem;
    box-shadow: 0 0 25px rgba(239, 68, 68, 0.7);
    border-bottom: 2px solid #fca5a5;
    animation: outage-flash 1.6s infinite alternate;
    z-index: 100;
  }

  @keyframes outage-flash {
    from {
      background: linear-gradient(90deg, #7f1d1d, #b91c1c, #dc2626);
      box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
    }
    to {
      background: linear-gradient(90deg, #991b1b, #dc2626, #ef4444);
      box-shadow: 0 0 35px rgba(239, 68, 68, 0.95);
    }
  }

  .outage-icon-box {
    font-size: 2rem;
    animation: siren-swing 1s infinite alternate ease-in-out;
  }

  @keyframes siren-swing {
    from {
      transform: rotate(-10deg) scale(0.95);
    }
    to {
      transform: rotate(10deg) scale(1.1);
    }
  }

  .outage-text-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .outage-headline {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: 0.5px;
  }

  .outage-count-tag {
    background: #000;
    color: #fca5a5;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 800;
    border: 1px solid rgba(254, 202, 202, 0.4);
  }

  .outage-description {
    font-size: 0.85rem;
    color: #fee2e2;
  }

  .outage-actions {
    display: flex;
    gap: 0.65rem;
    align-items: center;
  }

  .btn-outage-silence {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid #fee2e2;
    color: #fff;
    padding: 0.45rem 0.85rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-outage-silence:hover {
    background: rgba(0, 0, 0, 0.8);
  }

  .btn-outage-ack {
    background: #fff;
    color: #991b1b;
    border: none;
    padding: 0.5rem 1.1rem;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.9rem;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    transition: all 0.2s;
  }

  .btn-outage-ack:hover {
    background: #fee2e2;
    transform: translateY(-1px);
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

  /* Floating HUD de Router Seleccionado en Wallboard */
  .wallboard-router-hud {
    position: absolute;
    bottom: 1.25rem;
    left: 1.25rem;
    right: 1.25rem;
    background: rgba(11, 15, 25, 0.95);
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
  }

  .hud-left {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    min-width: 0;
  }

  .hud-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .hud-dot--online {
    background-color: #22c55e;
    box-shadow: 0 0 8px #22c55e;
  }

  .hud-dot--offline {
    background-color: #ef4444;
    box-shadow: 0 0 8px #ef4444;
  }

  .hud-text {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;
  }

  .hud-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #38bdf8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hud-meta {
    font-size: 0.75rem;
    color: #9ca3af;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .hud-meta code {
    color: #e5e7eb;
    background: rgba(255, 255, 255, 0.1);
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
  }

  .badge-role {
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    border: 1px solid rgba(56, 189, 248, 0.4);
  }

  .hud-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .btn-hud-webfig {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #0284c7;
    color: #ffffff;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #38bdf8;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-hud-webfig:hover {
    background: #0369a1;
    transform: translateY(-1px);
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
  }

  .btn-hud-close {
    background: transparent;
    color: #9ca3af;
    border: none;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 0.35rem;
    border-radius: 4px;
    line-height: 1;
    transition: color 0.15s ease;
  }

  .btn-hud-close:hover {
    color: #f3f4f6;
    background: rgba(255, 255, 255, 0.1);
  }

  /* Transición HUD */
  .hud-fade-enter-active,
  .hud-fade-leave-active {
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .hud-fade-enter-from,
  .hud-fade-leave-to {
    opacity: 0;
    transform: translateY(12px);
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
