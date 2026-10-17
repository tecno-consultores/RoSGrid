<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useLiveTelemetryStore } from '@/stores/useLiveTelemetryStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { http } from '@/api/httpClient';
  import type { RouterItem, TelemetryPoint } from '@/types';
  import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
  import RouterWorkspaceTabsBar from '@/components/webfig/RouterWorkspaceTabsBar.vue';
  import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const liveTelemetryStore = useLiveTelemetryStore();
  const inventoryStore = useInventoryStore();

  const isMobileSidebarOpen = ref(false);
  const routerId = computed(() => String(route.params.routerId || ''));

  let wsInstance: WebSocket | null = null;

  const currentRouter = computed<RouterItem | null>(() => {
    return (
      inventoryStore.routers.find((r) => r.id === routerId.value) ||
      webFigStore.currentRouter ||
      null
    );
  });

  async function loadRouterData() {
    if (!routerId.value) return;
    try {
      const res = await http.get<RouterItem>(`/api/v1/inventory/routers/${routerId.value}`);
      webFigStore.setCurrentRouter(res.data);
    } catch {
      // Si falla la consulta, no se inyectan datos simulados
    }
  }

  function connectTelemetryWebSocket() {
    disconnectTelemetryWebSocket();
    if (!routerId.value) return;

    if (typeof window !== 'undefined' && 'WebSocket' in window) {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsInstance = new WebSocket(
          `${protocol}//${host}/ws/v1/routers/${routerId.value}/live-telemetry`,
        );

        wsInstance.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data && (data.type === 'TELEMETRY_TICK' || data.cpuLoadPct !== undefined || data.system !== undefined)) {
              let totalRx = 0;
              let totalTx = 0;
              if (Array.isArray(data.interfaces)) {
                for (const iface of data.interfaces) {
                  totalRx += Number(iface.rx_bps || iface.rxBps || 0);
                  totalTx += Number(iface.tx_bps || iface.txBps || 0);
                }
              }
              const memUsedPct = Number(data.system?.memory_used_pct ?? data.memoryUsedPct ?? 0);
              const freeMemPct = Number(data.freeMemoryPct ?? (100 - memUsedPct));
              const normalizedPoint: TelemetryPoint = {
                timestampEpoch: Date.now(),
                timestampIso: data.timestamp_iso || data.timestampIso || new Date().toISOString(),
                cpuLoadPct: Number(data.system?.cpu_load_pct ?? data.cpuLoadPct ?? 0),
                freeMemoryPct: Math.max(0, Math.min(100, freeMemPct)),
                rxBps: data.rxBps !== undefined ? Number(data.rxBps) : totalRx,
                txBps: data.txBps !== undefined ? Number(data.txBps) : totalTx,
                temperatureC: data.system?.temperature_c !== undefined ? Number(data.system.temperature_c) : data.temperatureC,
              };
              liveTelemetryStore.pushTelemetryPoint(normalizedPoint);
            }
          } catch {
            // Ignorar errores de deserialización
          }
        };

        wsInstance.onerror = () => {
          // Error de conexión WS
        };

        wsInstance.onclose = () => {
          // Desconexión limpia
        };
      } catch {
        // Excepción de constructor WebSocket
      }
    }
  }

  function disconnectTelemetryWebSocket() {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
  }

  function handleToggleSafeMode() {
    if (webFigStore.isSafeModeActive) {
      webFigStore.stopSafeMode();
    } else {
      webFigStore.startSafeModeCountdown(60);
    }
  }

  watch(
    routerId,
    (newId, oldId) => {
      if (newId && newId !== oldId) {
        liveTelemetryStore.resetChartsBuffer();
        webFigStore.clearRouterWorkspace();
        loadRouterData();
        connectTelemetryWebSocket();
      }
    },
    { immediate: true },
  );

  onMounted(() => {
    connectTelemetryWebSocket();
  });

  onBeforeUnmount(() => {
    disconnectTelemetryWebSocket();
    liveTelemetryStore.resetChartsBuffer();
    webFigStore.clearRouterWorkspace();
  });
</script>

<template>
  <div class="webfig-console-layout">
    <!-- Cabecera de contexto del router -->
    <RouterContextHeader
      :router="currentRouter"
      :latest-telemetry="liveTelemetryStore.latestPoint"
      @toggle-safemode="handleToggleSafeMode"
    />

    <!-- Barra de pestañas con persistencia en RAM (KeepAlive) -->
    <RouterWorkspaceTabsBar
      :router-id="routerId"
      @toggle-sidebar="isMobileSidebarOpen = !isMobileSidebarOpen"
    />

    <!-- Contenido principal: Menú lateral + Router View con KeepAlive -->
    <div class="console-body">
      <RouterSidebarMenu
        :router-id="routerId"
        :is-open-mobile="isMobileSidebarOpen"
        @close-mobile="isMobileSidebarOpen = false"
      />

      <main
        id="webfig-main-view"
        class="console-view-container"
        role="main"
        aria-label="Módulo WebFig activo"
      >
        <router-view v-slot="{ Component }">
          <keep-alive :max="5">
            <component :is="Component" :key="route.name" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
  .webfig-console-layout {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: calc(100vh - 80px);
    width: 100%;
  }

  .console-body {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    flex: 1;
    min-width: 0;
  }

  .console-view-container {
    flex: 1;
    min-width: 0;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  @media (max-width: 1024px) {
    .console-body {
      flex-direction: column;
    }

    .console-view-container {
      padding: 12px;
      width: 100%;
    }
  }
</style>
