<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, PppActiveSessionItem, SimpleQueueItem } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<'pppoe-active' | 'simple-queues'>('pppoe-active');
  const isLoading = ref(false);
  const pppSearchQuery = ref('');
  const pppSessions = ref<PppActiveSessionItem[]>([]);
  const simpleQueues = ref<SimpleQueueItem[]>([]);
  const actionMessage = ref('');

  const pppColumns: TableColumn<PppActiveSessionItem>[] = [
    { key: 'name', label: 'Usuario PPPoE', sortable: true },
    { key: 'address', label: 'Dirección IP' },
    { key: 'caller_id', label: 'MAC / Caller-ID' },
    { key: 'uptime', label: 'Uptime', align: 'right' },
    { key: 'service', label: 'Servicio', align: 'center' },
  ];

  const queueColumns: TableColumn<SimpleQueueItem>[] = [
    { key: 'name', label: 'Nombre Cola', sortable: true },
    { key: 'target', label: 'Target IP' },
    { key: 'max_limit', label: 'Límite Máximo (Up/Down)', align: 'center' },
    {
      key: 'traffic',
      label: 'Consumo Acumulado',
      align: 'right',
      formatter: (row) => `${formatBytes(row.bytes_in)} / ${formatBytes(row.bytes_out)}`,
    },
  ];

  function formatBytes(b: number): string {
    if (b >= 1000000000) return `${(b / 1000000000).toFixed(1)} GB`;
    if (b >= 1000000) return `${(b / 1000000).toFixed(1)} MB`;
    return `${(b / 1000).toFixed(0)} KB`;
  }

  const filteredPppSessions = computed(() => {
    const q = pppSearchQuery.value.trim().toLowerCase();
    if (!q) return pppSessions.value;
    return pppSessions.value.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.address.toLowerCase().includes(q) ||
        (s.caller_id && s.caller_id.toLowerCase().includes(q)),
    );
  });

  async function loadPppData() {
    isLoading.value = true;
    try {
      if (activeTab.value === 'pppoe-active') {
        const res = await http.get<PppActiveSessionItem[] | { items: PppActiveSessionItem[] }>(
          `/api/v1/routers/${routerId.value}/webfig/ppp/active`,
        );
        pppSessions.value = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      } else {
        const res = await http.get<SimpleQueueItem[] | { items: SimpleQueueItem[] }>(
          `/api/v1/routers/${routerId.value}/webfig/queues/simple`,
        );
        simpleQueues.value = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      }
    } catch {
      pppSessions.value = [];
      simpleQueues.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function handleReconnectPpp(session: PppActiveSessionItem) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/ppp/active/${session.id}`,
      );
      actionMessage.value = `Sesión de ${session.name} reiniciada con éxito.`;
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
      loadPppData();
    } catch (err: any) {
      actionMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al reiniciar sesión';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    }
  }

  onMounted(() => {
    loadPppData();
  });
</script>

<template>
  <div class="ppp-queues-view">
    <header class="view-header">
      <div>
        <h2 class="view-title">PPPoE & Control de Ancho de Banda (Simple Queues)</h2>
        <p class="view-subtitle">
          Supervisión de sesiones de abonados y gestión de límites de velocidad
        </p>
      </div>

      <nav class="subtabs-bar" role="tablist" aria-label="Módulos PPP y Colas">
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'pppoe-active' }"
          role="tab"
          :aria-selected="activeTab === 'pppoe-active'"
          @click="
            activeTab = 'pppoe-active';
            loadPppData();
          "
        >
          PPPoE Active
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'simple-queues' }"
          role="tab"
          :aria-selected="activeTab === 'simple-queues'"
          @click="
            activeTab = 'simple-queues';
            loadPppData();
          "
        >
          Simple Queues
        </button>
      </nav>
    </header>

    <div v-if="actionMessage" class="banner banner--success font-tabular" role="status">
      {{ actionMessage }}
    </div>

    <!-- Pestaña 1: PPPoE Active con Reconexión 1 Clic -->
    <div v-if="activeTab === 'pppoe-active'" class="content-block">
      <div class="search-bar">
        <label for="ppp-search" class="search-label">Buscar Abonado:</label>
        <input
          id="ppp-search"
          v-model="pppSearchQuery"
          type="search"
          placeholder="Filtrar por usuario, IP o MAC..."
          class="search-input font-tabular"
        />
      </div>

      <div class="table-card font-tabular">
        <RgDataTable
          :columns="pppColumns"
          :rows="filteredPppSessions"
          caption="Sesiones PPPoE Activas"
          row-key="id"
        >
          <template #actions="{ row }">
            <button
              type="button"
              class="btn-reconnect"
              :aria-label="`Reconectar sesión PPPoE de ${row.name}`"
              @click="handleReconnectPpp(row)"
            >
              🔄 Reconectar
            </button>
          </template>
        </RgDataTable>
      </div>
    </div>

    <!-- Pestaña 2: Simple Queues -->
    <div v-if="activeTab === 'simple-queues'" class="content-block">
      <div class="table-card font-tabular">
        <RgDataTable
          :columns="queueColumns"
          :rows="simpleQueues"
          caption="Colas Simples de Ancho de Banda"
          row-key="id"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
  .ppp-queues-view {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .view-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .view-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .view-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 5px 12px;
    font-size: 0.78rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-subtab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .banner--success {
    padding: 10px 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #10b981;
    font-size: 0.85rem;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .search-label {
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .search-input {
    flex: 1;
    max-width: 400px;
    padding: 6px 12px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.82rem;
  }

  .btn-reconnect {
    padding: 4px 10px;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    border-radius: 4px;
    color: #f59e0b;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
