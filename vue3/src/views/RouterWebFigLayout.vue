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
  let mockTickInterval: ReturnType<typeof setInterval> | null = null;

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
      const res = await http.get<RouterItem>(`/api/v1/routers/${routerId.value}`);
      webFigStore.setCurrentRouter(res.data);
    } catch {
      // Si falla o en modo mock, crear objeto de respaldo
      if (!webFigStore.currentRouter) {
        webFigStore.setCurrentRouter({
          id: routerId.value,
          tenant_id: 't-default',
          display_name: `CCR2004-${routerId.value.substring(0, 5)}`,
          ros_identity: 'Edge-Core-RouterOS',
          model: 'CCR2004-16G-2S+',
          serial_number: 'HE4011ABC123',
          ip_address: '192.168.88.1',
          api_port: 8728,
          ros_version: '7.18',
          admin_state: 'PRODUCTION',
          is_reachable: true,
        });
      }
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
            if (data && (data.type === 'TELEMETRY_TICK' || data.cpuLoadPct !== undefined)) {
              liveTelemetryStore.pushTelemetryPoint(data);
            }
          } catch {
            // Ignorar errores de deserialización
          }
        };

        wsInstance.onerror = () => {
          startMockTelemetry();
        };

        wsInstance.onclose = () => {
          // Desconexión limpia
        };
      } catch {
        startMockTelemetry();
      }
    } else {
      startMockTelemetry();
    }
  }

  function startMockTelemetry() {
    if (mockTickInterval) return;
    let tick = 0;
    mockTickInterval = setInterval(() => {
      tick++;
      const samplePoint: TelemetryPoint = {
        timestampEpoch: Math.floor(Date.now() / 1000),
        timestampIso: new Date().toISOString(),
        cpuLoadPct: 15 + Math.round(Math.sin(tick * 0.3) * 12),
        freeMemoryPct: 65 - Math.round(Math.cos(tick * 0.2) * 8),
        rxBps: Math.max(100000, 10000000 + Math.round(Math.sin(tick * 0.5) * 5000000)),
        txBps: Math.max(80000, 6000000 + Math.round(Math.cos(tick * 0.5) * 3000000)),
        temperatureC: 41 + (tick % 3),
      };
      liveTelemetryStore.pushTelemetryPoint(samplePoint);
    }, 2000);
  }

  function disconnectTelemetryWebSocket() {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
    if (mockTickInterval) {
      clearInterval(mockTickInterval);
      mockTickInterval = null;
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
