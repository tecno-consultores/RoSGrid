<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

<script setup lang="ts">
  /* eslint-disable security/detect-object-injection, sonarjs/no-duplicate-string */
  import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
  import { useLiveTelemetryStore } from '@/stores/useLiveTelemetryStore';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import {
    useTelemetryRingBuffer,
    type TelemetryWindowKey,
    WINDOW_POINTS_MAP,
  } from '@/composables/useTelemetryRingBuffer';
  import type { TelemetryPoint, RouterItem } from '@/types';

  const liveStore = useLiveTelemetryStore();
  const ringBuffer = useTelemetryRingBuffer();
  const webFigStore = useWebFigStore();
  const inventoryStore = useInventoryStore();

  const cpuCanvasRef = ref<HTMLCanvasElement | null>(null);
  const trafficCanvasRef = ref<HTMLCanvasElement | null>(null);

  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const { t } = useI18n();

  const selectedIface = ref('all-interfaces');
  const availableInterfaces = ref<string[]>(['all-interfaces']);

  async function loadRealInterfaces() {
    if (!routerId.value) return;
    try {
      const res = await http.get<{ name?: string }[] | { items: { name?: string }[] }>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces`,
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      const names = raw.map((i) => i.name).filter(Boolean) as string[];
      if (names.length > 0) {
        availableInterfaces.value = ['all-interfaces', ...names];
      }
    } catch {
      // Mantiene solo 'all-interfaces' sin inventar interfaces simuladas
    }
  }

  let animationFrameId: number | null = null;
  const isDeterministic = typeof navigator !== 'undefined' && Boolean(navigator.webdriver);

  // Sincronizar puntos entrantes del store global al RingBuffer local
  watch(
    () => liveStore.latestPoint,
    (newPoint) => {
      if (newPoint) {
        ringBuffer.addPoint(newPoint);
        if (isDeterministic) {
          drawCanvasCharts();
        }
      }
    },
    { immediate: true },
  );

  const WINDOW_AXIS_LABELS: Record<TelemetryWindowKey, [string, string, string]> = {
    '2m': ['-2m', '-1m', 'Ahora'],
    '15m': ['-15m', '-7m 30s', 'Ahora'],
    '1h': ['-1h', '-30m', 'Ahora'],
    '3h': ['-3h', '-1h 30m', 'Ahora'],
  };

  const currentWindow = computed(() => ringBuffer.selectedWindow.value);
  const currentWindowCapacity = computed(
    () => WINDOW_POINTS_MAP[currentWindow.value] || 450,
  );
  const currentTrafficScaleLabel = ref('1.00 kbps');

  function handleSelectWindow(w: TelemetryWindowKey) {
    ringBuffer.setWindow(w);
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    drawCanvasCharts();
  }

  function drawCanvasCharts() {
    const pts = ringBuffer.windowPoints.value;
    const windowKey = currentWindow.value;
    const windowCapacity = WINDOW_POINTS_MAP[windowKey] || 450;

    // 1. Gráfica de CPU
    if (cpuCanvasRef.value) {
      const canvas = cpuCanvasRef.value;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawAreaChart(
          ctx,
          canvas.width,
          canvas.height,
          pts,
          'cpuLoadPct',
          '#22D3EE',
          'rgba(34, 211, 238, 0.18)',
          100,
          windowCapacity,
          windowKey,
        );
      }
    }

    // 2. Gráfica de Tráfico de Red (RX / TX)
    if (trafficCanvasRef.value) {
      const canvas = trafficCanvasRef.value;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawTrafficChart(ctx, canvas.width, canvas.height, pts, windowCapacity, windowKey);
      }
    }

    if (!isDeterministic) {
      animationFrameId = requestAnimationFrame(drawCanvasCharts);
    }
  }

  function getThemeToken(tokenName: string, fallback: string): string {
    if (typeof document === 'undefined' || typeof getComputedStyle !== 'function') {
      return fallback;
    }
    const val = getComputedStyle(document.documentElement).getPropertyValue(tokenName).trim();
    return val || fallback;
  }

  function drawChartGridAndAxes(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    windowKey: TelemetryWindowKey,
    topYLabel: string,
    midYLabel: string,
    bottomYLabel: string,
  ) {
    ctx.strokeStyle = getThemeToken('--rg-border-grid', '#1E293B');
    ctx.lineWidth = 1;
    for (let y = 0; y <= height; y += height / 4) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    for (let x = 0; x <= width; x += width / 4) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    ctx.fillStyle = getThemeToken('--rg-text-muted', '#64748B');
    ctx.font = '10px monospace';
    ctx.fillText(topYLabel, 6, 12);
    ctx.fillText(midYLabel, 6, Math.round(height / 2) - 4);
    ctx.fillText(bottomYLabel, 6, height - 18);

    const [startLbl, midLbl, endLbl] = WINDOW_AXIS_LABELS[windowKey] || ['-15m', '-7m 30s', 'Ahora'];
    ctx.fillText(startLbl, 6, height - 4);
    ctx.fillText(midLbl, Math.max(6, Math.round(width / 2) - 20), height - 4);
    ctx.fillText(endLbl, Math.max(6, width - 38), height - 4);
  }

  function drawAreaChart(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    points: TelemetryPoint[],
    key: 'cpuLoadPct' | 'freeMemoryPct',
    strokeColor: string,
    fillColor: string,
    maxY: number,
    windowCapacity = 450,
    windowKey: TelemetryWindowKey = '15m',
  ) {
    ctx.clearRect(0, 0, width, height);
    drawChartGridAndAxes(ctx, width, height, windowKey, `${maxY}%`, `${Math.round(maxY / 2)}%`, '0%');

    if (points.length < 2) {
      ctx.fillStyle = getThemeToken('--rg-text-muted', '#64748B');
      ctx.font = '12px monospace';
      ctx.fillText('Esperando telemetría en vivo...', width / 2 - 80, height / 2);
      return;
    }

    const effectiveCapacity = Math.max(2, windowCapacity, points.length);
    const stepX = width / (effectiveCapacity - 1);
    const startSlot = Math.max(0, effectiveCapacity - points.length);
    const firstX = startSlot * stepX;
    const lastX = (startSlot + points.length - 1) * stepX;

    ctx.beginPath();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';

    points.forEach((pt, index) => {
      const val = pt[key] || 0;
      const x = (startSlot + index) * stepX;
      const y = height - (val / maxY) * height;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Relleno translúcido inferior acotado a la porción temporal ocupada en la ventana
    ctx.lineTo(lastX, height);
    ctx.lineTo(firstX, height);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
  }

  function drawTrafficChart(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    points: TelemetryPoint[],
    windowCapacity = 450,
    windowKey: TelemetryWindowKey = '15m',
  ) {
    ctx.clearRect(0, 0, width, height);

    const peakRx = points.length > 0 ? Math.max(...points.map((p) => p.rxBps || 0), 0) : 0;
    const peakTx = points.length > 0 ? Math.max(...points.map((p) => p.txBps || 0), 0) : 0;
    const maxVal = Math.max(peakRx, peakTx, 1000);
    currentTrafficScaleLabel.value = formatBps(maxVal);

    drawChartGridAndAxes(
      ctx,
      width,
      height,
      windowKey,
      formatBps(maxVal),
      formatBps(Math.round(maxVal / 2)),
      '0 bps',
    );

    if (points.length < 2) return;

    const effectiveCapacity = Math.max(2, windowCapacity, points.length);
    const stepX = width / (effectiveCapacity - 1);
    const startSlot = Math.max(0, effectiveCapacity - points.length);

    // RX (Cian #06B6D4)
    ctx.beginPath();
    ctx.strokeStyle = '#06B6D4';
    ctx.lineWidth = 2;
    points.forEach((pt, i) => {
      const x = (startSlot + i) * stepX;
      const y = height - ((pt.rxBps || 0) / maxVal) * height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // TX (Esmeralda #10B981)
    ctx.beginPath();
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2;
    points.forEach((pt, i) => {
      const x = (startSlot + i) * stepX;
      const y = height - ((pt.txBps || 0) / maxVal) * height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function formatBps(bps?: number): string {
    if (!bps) return '0 bps';
    if (bps >= 1000000000) return `${(bps / 1000000000).toFixed(2)} Gbps`;
    if (bps >= 1000000) return `${(bps / 1000000).toFixed(2)} Mbps`;
    if (bps >= 1000) return `${(bps / 1000).toFixed(2)} kbps`;
    return `${bps} bps`;
  }

  onMounted(() => {
    // Sincronizar historial de puntos previo desde el store global
    if (liveStore.telemetryPoints && liveStore.telemetryPoints.length > 0) {
      liveStore.telemetryPoints.forEach((pt) => ringBuffer.addPoint(pt));
    }

    // Inicializar canvas si existen
    if (cpuCanvasRef.value) {
      cpuCanvasRef.value.width = cpuCanvasRef.value.parentElement?.clientWidth || 600;
      cpuCanvasRef.value.height = 200;
    }
    if (trafficCanvasRef.value) {
      trafficCanvasRef.value.width = trafficCanvasRef.value.parentElement?.clientWidth || 600;
      trafficCanvasRef.value.height = 200;
    }
    loadRealInterfaces();
    drawCanvasCharts();
  });

  onBeforeUnmount(() => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  });

  // Modales de Identidad y Reinicio (Spec 60 & Spec 67)
  const isChangingIdentity = ref(false);
  const isSyncingDiscovery = ref(false);
  const isRebooting = ref(false);
  const isIdentityModalOpen = ref(false);
  const newIdentityName = ref('');
  const syncDisplayName = ref(true);
  const actionBannerMsg = ref('');
  const actionBannerError = ref('');
  const isSubmittingIdentity = computed(() => isChangingIdentity.value);

  function getActiveRouterSnapshot(): RouterItem | null {
    return (
      (webFigStore.currentRouter && webFigStore.currentRouter.id === routerId.value
        ? webFigStore.currentRouter
        : null) ||
      inventoryStore.routers.find((r) => r.id === routerId.value) ||
      webFigStore.currentRouter ||
      null
    );
  }

  function openIdentityModal(): void {
    const cur = getActiveRouterSnapshot();
    newIdentityName.value = cur?.ros_identity || cur?.display_name || '';
    syncDisplayName.value = true;
    actionBannerError.value = '';
    isIdentityModalOpen.value = true;
  }

  async function handleChangeIdentity(): Promise<void> {
    const trimmed = newIdentityName.value.trim();
    if (!trimmed) return;
    isChangingIdentity.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      const res = await http.patch<{
        name?: string;
        ros_identity?: string;
        display_name?: string;
      }>(`/api/v1/routers/${routerId.value}/webfig/system/identity`, {
        name: trimmed,
        sync_display_name: syncDisplayName.value,
      });
      const updatedIdentity = res.data?.ros_identity || res.data?.name || trimmed;
      const cur = getActiveRouterSnapshot();
      const updatedDisplayName =
        res.data?.display_name ||
        (syncDisplayName.value ? updatedIdentity : cur?.display_name || updatedIdentity);

      if (cur) {
        const updatedRouter: RouterItem = {
          ...cur,
          ros_identity: updatedIdentity,
          display_name: updatedDisplayName,
        };
        webFigStore.setCurrentRouter(updatedRouter);
        inventoryStore.updateRouter(updatedRouter);
      } else {
        try {
          const fresh = await http.get<RouterItem>(`/api/v1/inventory/routers/${routerId.value}`);
          if (fresh.data) {
            webFigStore.setCurrentRouter(fresh.data);
            inventoryStore.updateRouter(fresh.data);
          }
        } catch {
          // Ignorar fallo secundario de refresco
        }
      }

      actionBannerMsg.value = `Identidad del router actualizada a "${updatedIdentity}".`;
      isIdentityModalOpen.value = false;
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al actualizar identidad.';
    } finally {
      isChangingIdentity.value = false;
    }
  }

  async function handleSyncDiscovery(): Promise<void> {
    isSyncingDiscovery.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      const res = await http.post<RouterItem>(
        `/api/v1/inventory/routers/${routerId.value}/sync-discovery`,
      );
      if (res.data && typeof res.data === 'object' && 'id' in res.data) {
        webFigStore.setCurrentRouter(res.data);
        inventoryStore.updateRouter(res.data);
      }
      actionBannerMsg.value = 'Sincronización de descubrimiento (Hardware/RouterOS) completada.';
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al sincronizar hardware.';
    } finally {
      isSyncingDiscovery.value = false;
    }
  }

  async function handleRebootRouter(): Promise<void> {
    if (
      !confirm(
        '⚠️ ¿Confirmas el reinicio inmediato del router MikroTik? Se interrumpirá el tráfico de red durante el ciclo de booteo.',
      )
    ) {
      return;
    }
    if (!confirm('⚠️ CONFIRMACIÓN FINAL: ¿Reiniciar ahora?')) {
      return;
    }
    isRebooting.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      const res = await http.post(`/api/v1/routers/${routerId.value}/webfig/system/reboot`, {
        reason: 'Reinicio manual desde Dashboard WebFig Live',
      });
      if (res.status === 202 || (res.data as { status?: string })?.status === 'INTERCEPTED_FOR_APPROVAL') {
        webFigStore.handleMutationResponse(res, 60);
        actionBannerMsg.value =
          (res.data as { detail?: string })?.detail ||
          'Solicitud de reinicio enviada a la bandeja de aprobación Maker-Checker.';
      } else {
        actionBannerMsg.value = 'Orden de reinicio enviada exitosamente al router MikroTik.';
      }
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al enviar comando de reinicio.';
    } finally {
      isRebooting.value = false;
    }
  }
</script>

<template>
  <div class="live-dashboard">
    <header class="dashboard-header">
      <div class="header-titles">
        <h2 class="dashboard-title">{{ t('webfig.live_dashboard_title') }}</h2>
        <p class="dashboard-subtitle">
          {{
            t('webfig.live_dashboard_subtitle', {
              count: ringBuffer.rawPoints.value.length,
            })
          }}
        </p>
      </div>

      <!-- Selectores de Ventana Temporal (2m, 15m, 1h, 3h) & Acciones Rápidas -->
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <div
          class="window-selectors"
          role="group"
          aria-label="Selector de ventana temporal de telemetría"
        >
          <button
            v-for="(pts, key) in WINDOW_POINTS_MAP"
            :key="key"
            type="button"
            class="btn-window"
            :class="{ 'btn-window--active': currentWindow === key }"
            :aria-pressed="currentWindow === key"
            @click="handleSelectWindow(key as TelemetryWindowKey)"
          >
            {{ key }} ({{ pts }} pts)
          </button>
        </div>

        <div class="dashboard-quick-actions" style="display: flex; gap: 6px;">
          <button
            id="btn-change-identity"
            type="button"
            class="btn-rg btn-rg--secondary btn-sm"
            title="Cambiar identidad del router en RouterOS"
            @click="openIdentityModal"
          >
            ✏️ Identidad
          </button>
          <button
            id="btn-sync-discovery"
            type="button"
            class="btn-rg btn-rg--cyan btn-sm"
            :disabled="isSyncingDiscovery"
            title="Sincronizar paquetes y recursos del router"
            @click="handleSyncDiscovery"
          >
            {{ isSyncingDiscovery ? 'Sincronizando...' : '🔄 Sincronizar Datos' }}
          </button>
          <button
            id="btn-reboot-router"
            type="button"
            class="btn-rg btn-rg--red btn-sm"
            :disabled="isRebooting"
            title="Reiniciar router MikroTik"
            @click="handleRebootRouter"
          >
            {{ isRebooting ? 'Reiniciando...' : '⚠️ Reiniciar Router' }}
          </button>
        </div>
      </div>
    </header>

    <div v-if="actionBannerMsg" id="banner-identity-success" class="banner banner--success" role="status" style="margin-bottom: 12px;">
      {{ actionBannerMsg }}
    </div>
    <div v-if="actionBannerError" id="banner-identity-error" class="banner banner--error" role="alert" style="margin-bottom: 12px;">
      {{ actionBannerError }}
    </div>

    <!-- Resumen de Tarjetas Métricas Rápidas -->
    <section class="kpi-grid font-tabular" aria-label="Métricas del sistema">
      <div class="kpi-card">
        <span class="kpi-title">{{ t('webfig.kpi_cpu_load') }}</span>
        <div class="kpi-value text-cyan">
          {{ Math.round(ringBuffer.latestPoint.value?.cpuLoadPct ?? 0) }}%
        </div>
        <span class="kpi-sub">{{ t('webfig.kpi_multicore') }}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">{{ t('webfig.kpi_ram_free') }}</span>
        <div class="kpi-value text-emerald">
          {{ Math.round(ringBuffer.latestPoint.value?.freeMemoryPct ?? 0) }}%
        </div>
        <span class="kpi-sub">{{ t('webfig.kpi_system_memory') }}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">{{ t('webfig.kpi_rx_traffic') }}</span>
        <div class="kpi-value text-cyan">{{ formatBps(ringBuffer.latestPoint.value?.rxBps) }}</div>
        <span class="kpi-sub">{{ t('webfig.kpi_download_iface') }}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">{{ t('webfig.kpi_tx_traffic') }}</span>
        <div class="kpi-value text-emerald">
          {{ formatBps(ringBuffer.latestPoint.value?.txBps) }}
        </div>
        <span class="kpi-sub">{{ t('webfig.kpi_upload_iface') }}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">{{ t('webfig.kpi_temperature') }}</span>
        <div class="kpi-value text-amber">
          {{ ringBuffer.latestPoint.value?.temperatureC ?? 40 }}°C
        </div>
        <span class="kpi-sub">{{ t('webfig.kpi_thermal_health') }}</span>
      </div>
    </section>

    <!-- Sección de Gráficas Canvas 2D Aceleradas -->
    <div class="charts-grid">
      <!-- Gráfica 1: Carga de CPU -->
      <div class="chart-panel">
        <div class="panel-header">
          <h3 class="panel-title">{{ t('webfig.chart_cpu_history') }}</h3>
          <span id="cpu-chart-scale-tag" class="panel-tag font-tabular">
            {{ t('webfig.chart_window_tag', { w: currentWindow }) }} · {{ ringBuffer.windowPoints.value.length }}/{{ currentWindowCapacity }} pts · 0–100%
          </span>
        </div>
        <div class="canvas-container">
          <canvas
            ref="cpuCanvasRef"
            class="telemetry-canvas"
            aria-label="Gráfica de tiempo real de carga de CPU"
            role="img"
          ></canvas>
        </div>
      </div>

      <!-- Gráfica 2: Tráfico RX / TX por Interfaz -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="traffic-title-group">
            <h3 class="panel-title">{{ t('webfig.chart_traffic_history') }}</h3>
            <div class="traffic-legend font-tabular">
              <span class="legend-rx">■ RX</span>
              <span class="legend-tx">■ TX</span>
              <span id="traffic-chart-scale-tag" class="panel-tag">
                Escala: {{ currentWindow }} ({{ currentTrafficScaleLabel }})
              </span>
            </div>
          </div>

          <!-- Selector de Interfaz para superponer -->
          <div class="iface-selector">
            <label for="chart-iface-select" class="sr-only">Interfaz:</label>
            <select id="chart-iface-select" v-model="selectedIface" class="select-iface">
              <option v-for="iface in availableInterfaces" :key="iface" :value="iface">
                {{ iface }}
              </option>
            </select>
          </div>
        </div>
        <div class="canvas-container">
          <canvas
            ref="trafficCanvasRef"
            class="telemetry-canvas"
            aria-label="Gráfica de tiempo real de tráfico RX y TX"
            role="img"
          ></canvas>
        </div>
      </div>
    </div>

    <!-- Modal Táctico: Cambio de Identidad del Router (Spec 60 & Spec 67) -->
    <div
      v-if="isIdentityModalOpen"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="identity-modal-title"
      @click.self="isIdentityModalOpen = false"
    >
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="identity-modal-title" class="modal-title">🏷️ Cambiar Identidad del Router</h3>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isIdentityModalOpen = false">
            ✕
          </button>
        </header>
        <form class="modal-form" @submit.prevent="handleChangeIdentity">
          <div class="modal-body">
            <div class="form-group">
              <label for="input-router-identity">Nuevo nombre de Identity (/system/identity):</label>
              <input
                id="input-router-identity"
                v-model="newIdentityName"
                type="text"
                class="form-control font-tabular"
                placeholder="Ej: CCR2004-Borde-Norte"
                maxlength="128"
                required
              />
            </div>
            <div class="form-group checkbox-row">
              <input
                id="chk-sync-display-name"
                v-model="syncDisplayName"
                type="checkbox"
              />
              <label for="chk-sync-display-name">
                Sincronizar también el nombre visible en el Inventario RoSGrid
              </label>
            </div>
          </div>
          <footer class="modal-footer">
            <button
              type="button"
              class="btn-secondary"
              @click="isIdentityModalOpen = false"
            >
              Cancelar
            </button>
            <button
              id="btn-confirm-identity"
              type="submit"
              class="btn-primary"
              :disabled="isSubmittingIdentity || !newIdentityName.trim()"
              @click="handleChangeIdentity"
            >
              {{ isSubmittingIdentity ? '⏳ Guardando...' : '💾 Guardar Identity' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .live-dashboard {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .dashboard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .dashboard-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .dashboard-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  /* Refactoring UI: Segmented Control con Radios Concéntricos (8px ext - 3px pad = 5px int) */
  .window-selectors {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: var(--rg-radius-lg, 8px);
    box-shadow: var(--rg-inset-well);
  }

  .btn-window {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 4px 10px;
    font-size: var(--rg-text-xs, 0.75rem);
    border-radius: var(--rg-radius-concentric, 5px);
    cursor: pointer;
    font-family: var(--rg-font-mono);
    transition: all 0.15s ease;
  }

  .btn-window--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
    box-shadow: var(--rg-inset-highlight), var(--rg-shadow-sm);
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: var(--rg-space-3, 12px);
  }

  /* Refactoring UI: Lighter surface reads raised on dark mode ("Depth without shadows") */
  .kpi-card {
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
    border-radius: var(--rg-radius-lg, 8px);
    padding: var(--rg-space-3, 12px);
    box-shadow: var(--rg-inset-highlight);
    display: flex;
    flex-direction: column;
    gap: var(--rg-space-1, 4px);
  }

  .kpi-title {
    font-size: 0.75rem;
    color: var(--rg-text-muted);
    text-transform: uppercase;
    font-weight: 600;
  }

  .kpi-value {
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .kpi-sub {
    font-size: 0.7rem;
    color: var(--rg-text-muted);
  }

  .text-cyan {
    color: var(--rg-accent-cyan);
  }

  .text-emerald {
    color: #10b981;
  }

  .text-amber {
    color: #f59e0b;
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
    gap: 16px;
  }

  .chart-panel {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 0;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .panel-title {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--rg-text-primary);
  }

  .panel-tag {
    font-size: 0.72rem;
    color: var(--rg-text-muted);
    background: var(--rg-bg-elevated);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .traffic-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .traffic-legend {
    display: flex;
    gap: 8px;
    font-size: 0.75rem;
  }

  .legend-rx {
    color: #06b6d4;
  }

  .legend-tx {
    color: #10b981;
  }

  .select-iface {
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 4px;
    color: var(--rg-text-primary);
    font-size: 0.75rem;
    padding: 2px 6px;
  }

  .canvas-container {
    width: 100%;
    min-height: 200px;
    background: #060911;
    border-radius: 6px;
    overflow: hidden;
  }

  .telemetry-canvas {
    width: 100%;
    height: 200px;
    display: block;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 640px) {
    .charts-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Modal Táctico NOC */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(3, 7, 18, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-card {
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-lg, 8px);
    width: 90%;
    max-width: 480px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    background: var(--rg-bg-elevated, #1e293b);
  }

  .modal-header h2 {
    margin: 0;
    font-size: 0.95rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.1rem;
    cursor: pointer;
  }

  .modal-form {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-control {
    background: var(--rg-bg-canvas, #090d16);
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .form-hint {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
  }

  .btn-secondary {
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-primary {
    background: #00bcd4;
    border: 1px solid #00acc1;
    color: #030712;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .checkbox-row {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid var(--status-online, #10b981);
    color: var(--status-online, #10b981);
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.14);
    border: 1px solid var(--status-offline, #ef4444);
    color: var(--status-offline, #ef4444);
  }
</style>
