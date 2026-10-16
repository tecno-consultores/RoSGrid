<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
  import { useLiveTelemetryStore } from '@/stores/useLiveTelemetryStore';
  import {
    useTelemetryRingBuffer,
    type TelemetryWindowKey,
    WINDOW_POINTS_MAP,
  } from '@/composables/useTelemetryRingBuffer';
  import type { TelemetryPoint } from '@/types';

  const liveStore = useLiveTelemetryStore();
  const ringBuffer = useTelemetryRingBuffer();

  const cpuCanvasRef = ref<HTMLCanvasElement | null>(null);
  const trafficCanvasRef = ref<HTMLCanvasElement | null>(null);

  const selectedIface = ref('all-interfaces');
  const availableInterfaces = ref([
    'all-interfaces',
    'ether1-WAN',
    'ether2-LAN',
    'sfp-plus1-Trunk',
  ]);

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

  const currentWindow = computed(() => ringBuffer.selectedWindow.value);

  function handleSelectWindow(w: TelemetryWindowKey) {
    ringBuffer.setWindow(w);
    if (isDeterministic) {
      drawCanvasCharts();
    }
  }

  function drawCanvasCharts() {
    const pts = ringBuffer.windowPoints.value;

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
        );
      }
    }

    // 2. Gráfica de Tráfico de Red (RX / TX)
    if (trafficCanvasRef.value) {
      const canvas = trafficCanvasRef.value;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawTrafficChart(ctx, canvas.width, canvas.height, pts);
      }
    }

    if (!isDeterministic) {
      animationFrameId = requestAnimationFrame(drawCanvasCharts);
    }
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
  ) {
    ctx.clearRect(0, 0, width, height);

    // Cuadrícula táctica estilo WinBox
    ctx.strokeStyle = '#1E293B';
    ctx.lineWidth = 1;
    for (let y = 0; y <= height; y += height / 4) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (points.length < 2) {
      ctx.fillStyle = '#64748B';
      ctx.font = '12px monospace';
      ctx.fillText('Esperando telemetría en vivo...', width / 2 - 80, height / 2);
      return;
    }

    ctx.beginPath();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';

    const stepX = width / Math.max(1, points.length - 1);

    points.forEach((pt, index) => {
      const val = pt[key] || 0;
      const x = index * stepX;
      const y = height - (val / maxY) * height;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Relleno translúcido inferior
    ctx.lineTo((points.length - 1) * stepX, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
  }

  function drawTrafficChart(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    points: TelemetryPoint[],
  ) {
    ctx.clearRect(0, 0, width, height);

    // Cuadrícula de fondo
    ctx.strokeStyle = '#1E293B';
    ctx.lineWidth = 1;
    for (let y = 0; y <= height; y += height / 4) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (points.length < 2) return;

    const maxRx = Math.max(...points.map((p) => p.rxBps || 0), 1000000);
    const maxTx = Math.max(...points.map((p) => p.txBps || 0), 1000000);
    const maxVal = Math.max(maxRx, maxTx, 1);

    const stepX = width / Math.max(1, points.length - 1);

    // RX (Cian #06B6D4)
    ctx.beginPath();
    ctx.strokeStyle = '#06B6D4';
    ctx.lineWidth = 2;
    points.forEach((pt, i) => {
      const x = i * stepX;
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
      const x = i * stepX;
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
    drawCanvasCharts();
  });

  onBeforeUnmount(() => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  });
</script>

<template>
  <div class="live-dashboard">
    <header class="dashboard-header">
      <div class="header-titles">
        <h2 class="dashboard-title">Dashboard & Telemetría en Vivo</h2>
        <p class="dashboard-subtitle">
          Telemetría en memoria RAM (RingBuffer {{ ringBuffer.rawPoints.value.length }} / 5400
          puntos) estilo WinBox
        </p>
      </div>

      <!-- Selectores de Ventana Temporal (2m, 15m, 1h, 3h) -->
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
    </header>

    <!-- Resumen de Tarjetas Métricas Rápidas -->
    <section class="kpi-grid font-tabular" aria-label="Métricas del sistema">
      <div class="kpi-card">
        <span class="kpi-title">Carga CPU</span>
        <div class="kpi-value text-cyan">{{ ringBuffer.latestPoint.value?.cpuLoadPct ?? 0 }}%</div>
        <span class="kpi-sub">Multi-Core</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">RAM Libre</span>
        <div class="kpi-value text-emerald">
          {{ ringBuffer.latestPoint.value?.freeMemoryPct ?? 0 }}%
        </div>
        <span class="kpi-sub">Memoria del Sistema</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">Tráfico RX</span>
        <div class="kpi-value text-cyan">{{ formatBps(ringBuffer.latestPoint.value?.rxBps) }}</div>
        <span class="kpi-sub">Descarga en interfaz</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">Tráfico TX</span>
        <div class="kpi-value text-emerald">
          {{ formatBps(ringBuffer.latestPoint.value?.txBps) }}
        </div>
        <span class="kpi-sub">Subida en interfaz</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-title">Temperatura</span>
        <div class="kpi-value text-amber">
          {{ ringBuffer.latestPoint.value?.temperatureC ?? 40 }}°C
        </div>
        <span class="kpi-sub">Salud Térmica</span>
      </div>
    </section>

    <!-- Sección de Gráficas Canvas 2D Aceleradas -->
    <div class="charts-grid">
      <!-- Gráfica 1: Carga de CPU -->
      <div class="chart-panel">
        <div class="panel-header">
          <h3 class="panel-title">📈 Historial de Carga CPU (%)</h3>
          <span class="panel-tag font-tabular">Ventana: {{ currentWindow }}</span>
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
            <h3 class="panel-title">📊 Tráfico en Vivo RX / TX</h3>
            <div class="traffic-legend font-tabular">
              <span class="legend-rx">■ RX</span>
              <span class="legend-tx">■ TX</span>
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

  .window-selectors {
    display: flex;
    gap: 6px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .btn-window {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 4px 10px;
    font-size: 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    transition: all 0.15s ease;
  }

  .btn-window--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
  }

  .kpi-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
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
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
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
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
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
</style>
