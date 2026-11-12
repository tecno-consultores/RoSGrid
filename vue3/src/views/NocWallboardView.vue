<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import UnifiedNetworkMap from '@/components/network/UnifiedNetworkMap.vue';
  import L2TopologyView from '@/views/L2TopologyView.vue';
  import type { RouterItem, OpticalBoxItem, SubscriberDeviceItem } from '@/types';
  import { http } from '@/api/httpClient';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useI18n } from '@/composables/useI18n';
  import { formatEventAction, formatEventMessage, isRawUuid } from '@/utils/eventFormatter';

  const router = useRouter();
  const nocEventsStore = useNocEventsStore();
  const { t } = useI18n();

  interface NocEvent {
    id: string;
    timestamp: string;
    type: 'ROUTER_DOWN' | 'ROUTER_UP' | 'HIGH_CPU' | 'SSL_MISMATCH' | 'MAINTENANCE' | 'BACKUP' | 'OPERATION';
    router_identity: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
  }

  const isFullscreen = ref(false);
  const showLogicalL2Graph = ref(false);
  const wallboardContainer = ref<HTMLElement | null>(null);

  // Infraestructura real obtenida de la API
  const routers = ref<RouterItem[]>([]);
  const opticalBoxes = ref<OpticalBoxItem[]>([]);
  const subscribers = ref<SubscriberDeviceItem[]>([]);
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
  const isEventsHudCollapsed = ref<boolean>(false);

  // Alerta de Caída Masiva (Mass Outage) — docs/specs/32 §5.3
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
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
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

  let autoRefreshTimer: ReturnType<typeof setInterval> | null = null;
  const isRefreshing = ref(false);

  async function performAutoRefresh(forceProbe = false) {
    if (isRefreshing.value) return;
    isRefreshing.value = true;
    try {
      await Promise.allSettled([
        loadRouters(forceProbe),
        loadOpticalBoxes(),
        loadSubscribers(),
        loadEvents(),
      ]);
    } finally {
      isRefreshing.value = false;
    }
  }

  function determineEventType(name: string, category?: string): NocEvent['type'] {
    const upper = (name || '').toUpperCase();
    if (upper.includes('DOWN') || upper.includes('OUTAGE')) return 'ROUTER_DOWN';
    if (upper.includes('MAINTENANCE')) return 'MAINTENANCE';
    if (upper.includes('BACKUP')) return 'BACKUP';
    if (upper.includes('SSL') || upper.includes('TOFU')) return 'SSL_MISMATCH';
    if (upper.includes('CPU')) return 'HIGH_CPU';
    if (upper.includes('UP') || category === 'AUTH') return 'ROUTER_UP';
    return 'OPERATION';
  }

  function determineSeverity(sev: string): 'critical' | 'warning' | 'info' {
    const s = sev.toLowerCase();
    if (s === 'critical') return 'critical';
    if (s === 'warning') return 'warning';
    return 'info';
  }

  function createLiveEvent(latest: {
    id: string;
    timestampIso: string;
    eventName: string;
    routerDisplayName?: string;
    message?: string;
    severity: string;
  }): NocEvent {
    const actionDesc = formatEventAction(latest.eventName);
    return {
      id: latest.id,
      timestamp: new Date(latest.timestampIso).toLocaleTimeString(),
      type: determineEventType(latest.eventName),
      router_identity: latest.routerDisplayName || 'Sistema',
      message: latest.message ? formatEventMessage(latest.message, latest.routerDisplayName) : actionDesc,
      severity: determineSeverity(latest.severity),
    };
  }

  watch(
    () => nocEventsStore.recentEvents,
    (events) => {
      if (!events || events.length === 0) return;
      const latest = events[0];
      const newEvt = createLiveEvent(latest);
      liveEvents.value = [newEvt, ...liveEvents.value.slice(0, 19)];
      if (latest.severity === 'CRITICAL' && !massOutageAlert.value.active) {
        playTacticalChime();
      }
    },
    { deep: true },
  );

  async function loadRouters(forceProbe = false) {
    try {
      const url = forceProbe ? '/api/v1/inventory/routers?refresh=true' : '/api/v1/inventory/routers';
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>(url);
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      if (raw.length > 0) {
        routers.value = (raw as unknown as Record<string, unknown>[]).map((item) => ({
          ...(item as unknown as RouterItem),
          latitude:
            item.latitude !== null && item.latitude !== undefined && item.latitude !== ''
              ? Number(item.latitude)
              : undefined,
          longitude:
            item.longitude !== null && item.longitude !== undefined && item.longitude !== ''
              ? Number(item.longitude)
              : undefined,
          ip_address:
            (item.ip_address as string) ||
            ((item.api_base_url as string)
              ? (item.api_base_url as string)
                  .replace(/^https?:\/\//, '')
                  .split('/')[0]
                  .split(':')[0]
              : ''),
          ros_version: (item.ros_version as string) || 'v7',
          is_reachable: Boolean(item.is_reachable || item.syslog_active || item.operational_status === 'ONLINE'),
          operational_status: (item.operational_status as string) || (item.is_reachable || item.syslog_active ? 'ONLINE' : 'OFFLINE'),
          syslog_active: Boolean(item.syslog_active),
        }));
      }

      if (offlineRouters.value >= 10 && !massOutageAlert.value.active) {
        triggerMassOutage(offlineRouters.value, 'INFRAESTRUCTURA', 'CORE/ROUTERS');
      }
    } catch {
      // Mantiene muestra inicial
    }
  }

  async function loadOpticalBoxes() {
    try {
      const res = await http.get<OpticalBoxItem[] | { items: OpticalBoxItem[] }>('/api/v1/optical-boxes');
      const raw = Array.isArray(res.data) ? res.data : (res.data as { items?: OpticalBoxItem[] })?.items || [];
      opticalBoxes.value = raw;
    } catch {
      // Preservar estado previo en memoria ante fallo transitorio
    }
  }

  async function loadSubscribers() {
    try {
      const res = await http.get<SubscriberDeviceItem[] | { items: SubscriberDeviceItem[] }>('/api/v1/subscriber-devices');
      const raw = Array.isArray(res.data) ? res.data : (res.data as { items?: SubscriberDeviceItem[] })?.items || [];
      subscribers.value = raw;
    } catch {
      // Preservar estado previo en memoria ante fallo transitorio
    }
  }

  async function loadEvents() {
    try {
      const res = await http.get<{ items: Record<string, unknown>[] }>('/api/v1/audit/logs');
      const items = res.data?.items || [];

      // Detección de caída masiva en eventos de auditoría recientes
      const outageLog = items.find(
        (log) =>
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED',
      );
      if (outageLog && !massOutageAlert.value.active) {
        const after = (outageLog.after_state as Record<string, unknown>) || {};
        triggerMassOutage(
          Number(after.affected_onus_count || 10),
          after.pon_port as string | undefined,
          after.optical_box as string | undefined,
        );
      }

      liveEvents.value = items.slice(0, 20).map((log) => {
        const rawRouterName = (log.router_display_name as string) || '';
        const rawActor = (log.actor_username as string) || '';
        const cleanIdentity =
          rawRouterName && !isRawUuid(rawRouterName)
            ? rawRouterName
            : rawActor && !isRawUuid(rawActor)
              ? rawActor
              : 'Sistema';
        return {
          id: String(log.id),
          timestamp: log.created_at
            ? new Date(log.created_at as string).toLocaleTimeString()
            : new Date().toLocaleTimeString(),
          type: determineEventType(log.event_action as string, log.event_category as string),
          router_identity: cleanIdentity,
          message: formatEventMessage(log.event_action as string, rawActor),
          severity:
            log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
            log.event_action === 'MASS_OUTAGE_DETECTED'
              ? 'critical'
              : Number(log.status_code || 0) >= 400
                ? 'critical'
                : String(log.event_action || '').includes('MAINTENANCE')
                  ? 'warning'
                  : 'info',
        };
      });
    } catch {
      // Preservar estado previo en memoria ante fallo transitorio
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

  function getBadgeLabel(type: string): string {
    switch (type) {
      case 'ROUTER_DOWN':
        return 'CAÍDA';
      case 'ROUTER_UP':
        return 'OPERATIVO';
      case 'HIGH_CPU':
        return 'CARGA ALTA';
      case 'SSL_MISMATCH':
        return 'ALERTA SSL';
      case 'MAINTENANCE':
        return 'MANTENIMIENTO';
      case 'BACKUP':
        return 'RESPALDO';
      case 'OPERATION':
        return 'OPERACIÓN';
      default:
        return formatEventAction(type);
    }
  }

  onMounted(() => {
    loadRouters();
    loadOpticalBoxes();
    loadSubscribers();
    loadEvents();

    // Auto-refresco autónomo cada 15 segundos sin intervención de usuario
    autoRefreshTimer = setInterval(() => {
      performAutoRefresh();
    }, 15000);

    // Conectar WebSocket de eventos en vivo
    nocEventsStore.connectEventsWebSocket();

    document.addEventListener('fullscreenchange', handleFullscreenChange);
  });

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
    }
  });
</script>

<template>
  <div
    ref="wallboardContainer"
    class="noc-wallboard"
    role="region"
    aria-label="Wallboard NOC 24/7 Pantalla Completa"
  >
    <!-- Encabezado KPI Gigante -->
    <header class="wallboard-header">
      <div class="wallboard-brand">
        <img
          src="/favicon.svg"
          alt=""
          class="wallboard-logo"
          width="32"
          height="32"
          aria-hidden="true"
        />
        <h1 class="brand-title">{{ t('wallboard.title') }}</h1>
      </div>

      <div class="kpi-strip" role="group" aria-label="Indicadores clave de rendimiento">
        <div class="kpi-card">
          <span class="kpi-label">{{ t('wallboard.kpi_total') }}</span>
          <span class="kpi-value text-cyan">{{ totalRouters }}</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">{{ t('wallboard.kpi_online') }}</span>
          <span class="kpi-value text-green">{{ onlineRouters }}</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">{{ t('wallboard.kpi_high_load') }}</span>
          <span class="kpi-value text-yellow">{{ highLoadRouters }}</span>
        </div>

        <div class="kpi-card" :class="{ 'kpi-card--critical': offlineRouters > 0 }">
          <span class="kpi-label">{{ t('wallboard.kpi_offline') }}</span>
          <span class="kpi-value text-red">{{ offlineRouters }}</span>
        </div>

        <div class="kpi-card" :class="{ 'kpi-card--maintenance-active': maintenanceRouters > 0 }">
          <span class="kpi-label">{{ t('wallboard.kpi_maintenance') }}</span>
          <span class="kpi-value text-blue">{{ maintenanceRouters }}</span>
        </div>

        <div class="kpi-card" :class="{ 'kpi-card--alert': sslAlertRouters > 0 }">
          <span class="kpi-label">{{ t('wallboard.kpi_ssl_alerts') }}</span>
          <span class="kpi-value text-red">{{ sslAlertRouters }}</span>
        </div>
      </div>

      <div class="wallboard-header-actions">
        <button
          id="btn-wallboard-toggle-l2-view"
          type="button"
          class="btn-wallboard-refresh"
          @click="showLogicalL2Graph = !showLogicalL2Graph"
        >
          {{ showLogicalL2Graph ? t('wallboard.btn_geo_map', '🗺️ Mapa Geográfico') : t('wallboard.btn_l2_graph', '🕸️ Grafo L2 / PoE') }}
        </button>
        <button
          id="btn-wallboard-refresh"
          type="button"
          class="btn-wallboard-refresh"
          :disabled="isRefreshing"
          aria-label="Refrescar estado del Wallboard NOC"
          @click="performAutoRefresh(true)"
        >
          {{ isRefreshing ? '⏳ Refrescando...' : '🔄 Refrescar' }}
        </button>
        <button
          type="button"
          class="btn-fullscreen"
          :aria-label="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa NOC'"
          @click="toggleFullscreen"
        >
          {{ isFullscreen ? t('wallboard.exit_tv') : t('wallboard.mode_tv') }}
        </button>
      </div>
    </header>

    <!-- Banner de Alta Visibilidad de Caída Masiva (docs/specs/32 §5.3) -->
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
            id="btn-ack-mass-outage"
            type="button"
            class="btn-outage-ack"
            @click="acknowledgeOutage"
          >
            {{ t('mass_outage.acknowledge') }}
          </button>
        </div>
      </div>
    </transition>

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
  </div>
</template>

<style scoped>
  .noc-wallboard {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 108px);
    height: calc(100dvh - 108px);
    min-height: 520px;
    width: 100%;
    background-color: var(--rg-bg-canvas);
    color: var(--rg-text-primary);
    border: 1px solid var(--rg-border-panel);
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
    overflow: hidden;
    border-radius: 8px;
  }

  .noc-wallboard:fullscreen {
    height: 100vh;
    height: 100dvh;
    border-radius: 0;
  }

  /* Banner Táctico de Caída Masiva (docs/specs/32 §5.3) */
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
    background-color: var(--rg-bg-surface);
    border-bottom: 1px solid var(--rg-border-panel);
    gap: 1rem;
    flex-shrink: 0;
  }

  .wallboard-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .wallboard-logo {
    width: 32px;
    height: 32px;
    object-fit: contain;
    filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5));
  }

  .brand-title {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: var(--rg-accent-cyan);
    margin: 0;
  }

  .kpi-strip {
    display: flex;
    gap: 0.75rem;
  }

  .kpi-card {
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
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

  .kpi-card--maintenance-active {
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.12);
  }

  .kpi-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--rg-text-muted);
    letter-spacing: 0.05em;
  }

  .kpi-value {
    font-size: 1.6rem;
    font-weight: 900;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }

  .text-cyan {
    color: var(--rg-accent-cyan);
  }
  .text-green {
    color: var(--rg-status-online);
  }
  .text-yellow {
    color: var(--rg-status-warning);
  }
  .text-red {
    color: var(--rg-status-critical);
  }
  .text-blue {
    color: var(--rg-status-info);
  }

  .wallboard-header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-wallboard-refresh {
    background: var(--rg-btn-action-bg);
    border: 1px solid var(--rg-accent-cyan-border);
    color: var(--rg-accent-cyan);
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-wallboard-refresh:hover:not(:disabled) {
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
  }

  .btn-wallboard-refresh:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-fullscreen {
    background: var(--rg-btn-action-bg);
    border: 1px solid var(--rg-btn-action-border);
    color: var(--rg-btn-action-fg);
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }

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
    background: var(--rg-hud-glass-header-bg);
    backdrop-filter: blur(5px) saturate(130%);
    -webkit-backdrop-filter: blur(5px) saturate(130%);
    border: 1px solid var(--rg-accent-cyan-border);
    border-radius: 8px;
    padding: 0.75rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    z-index: 1000;
    box-shadow: var(--rg-shadow-lg);
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
    color: var(--rg-accent-cyan);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hud-meta {
    font-size: 0.75rem;
    color: var(--rg-text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .hud-meta code {
    color: var(--rg-text-primary);
    background: var(--rg-bg-elevated);
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

  .wallboard-events-overlay {
    position: absolute;
    top: 62px;
    right: 16px;
    bottom: 16px;
    width: 370px;
    max-width: calc(100vw - 32px);
    display: flex;
    flex-direction: column;
    background: var(--rg-hud-glass-bg);
    backdrop-filter: blur(5px) saturate(130%);
    -webkit-backdrop-filter: blur(5px) saturate(130%);
    border: 1px solid var(--rg-hud-glass-border);
    border-radius: 12px;
    box-shadow: var(--rg-shadow-lg);
    overflow: hidden;
    z-index: 850;
  }

  .btn-events-hud-pill {
    position: absolute;
    top: 62px;
    right: 16px;
    z-index: 850;
    background: var(--rg-hud-glass-header-bg);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border: 1px solid var(--rg-accent-cyan-border);
    color: var(--rg-accent-cyan);
    padding: 0.45rem 0.9rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: var(--rg-shadow-md);
    transition: all 0.15s ease;
  }

  .btn-events-hud-pill:hover {
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
    border-color: var(--rg-accent-cyan);
  }

  .events-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.65rem 0.9rem;
    background: var(--rg-hud-glass-header-bg);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border-bottom: 1px solid var(--rg-border-panel);
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
    color: var(--rg-text-primary);
    margin: 0;
    text-shadow: var(--rg-hud-text-shadow);
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
    background: var(--rg-btn-action-bg);
    border: 1px solid var(--rg-btn-action-border);
    color: var(--rg-btn-action-fg);
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
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
    border-color: var(--rg-accent-cyan);
  }

  .events-empty-state {
    padding: 1.25rem;
    color: var(--rg-text-secondary);
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
    background: var(--rg-hud-glass-card-bg);
    border: 1px solid color-mix(in srgb, var(--rg-border-panel) 55%, transparent);
    border-left: 4px solid var(--rg-accent-cyan);
    padding: 0.5rem 0.7rem;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    gap: 0.22rem;
    transition: background-color 0.15s ease;
  }

  .event-item:hover {
    background: var(--rg-hud-glass-card-hover-bg);
  }

  .event-item--critical {
    border-left-color: var(--rg-status-critical);
    background: color-mix(in srgb, var(--rg-status-critical-bg) 52%, transparent);
  }

  .event-item--warning {
    border-left-color: var(--rg-status-warning);
    background: color-mix(in srgb, var(--rg-status-warning-bg) 52%, transparent);
  }

  .event-item--info {
    border-left-color: var(--rg-accent-cyan);
    background: var(--rg-hud-glass-card-bg);
  }

  .event-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.73rem;
  }

  .event-time {
    color: var(--rg-text-secondary);
    font-weight: 600;
    text-shadow: var(--rg-hud-text-shadow);
  }

  .event-type-badge {
    background: color-mix(in srgb, var(--rg-bg-canvas) 62%, transparent);
    color: var(--rg-text-primary);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 700;
    border: 1px solid var(--rg-border-panel);
  }

  .event-body {
    display: flex;
    flex-direction: column;
  }

  .event-router {
    font-size: 0.84rem;
    color: var(--rg-text-primary);
    text-shadow: var(--rg-hud-text-shadow);
  }

  .event-msg {
    margin: 0;
    font-size: 0.78rem;
    color: var(--rg-text-secondary);
    text-shadow: var(--rg-hud-text-shadow);
  }

  .font-mono {
    font-family: 'JetBrains Mono', monospace;
  }
</style>
