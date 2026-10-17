<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, FirewallRuleItem } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import RgSafeModeBanner from '@/components/common/RgSafeModeBanner.vue';

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<'filter' | 'nat' | 'mangle' | 'raw' | 'address-list' | 'connections'>(
    'filter',
  );
  const chainFilter = ref<string>('all');
  const isLoading = ref(false);
  const rulesList = ref<FirewallRuleItem[]>([]);
  const isMoving = ref(false);

  const columns: TableColumn<FirewallRuleItem>[] = [
    { key: 'chain', label: 'Cadena', sortable: true },
    { key: 'action', label: 'Acción', sortable: true },
    { key: 'src_address', label: 'Src Address' },
    { key: 'dst_address', label: 'Dst Address' },
    { key: 'protocol', label: 'Proto' },
    { key: 'dst_port', label: 'Dst Port' },
    {
      key: 'traffic',
      label: 'Bytes / Paquetes',
      align: 'right',
      formatter: (row) => `${formatBytes(row.bytes)} (${row.packets} pkts)`,
    },
    { key: 'comment', label: 'Comentario' },
  ];

  function formatBytes(bytes: number): string {
    if (bytes >= 1000000000) return `${(bytes / 1000000000).toFixed(2)} GB`;
    if (bytes >= 1000000) return `${(bytes / 1000000).toFixed(1)} MB`;
    if (bytes >= 1000) return `${(bytes / 1000).toFixed(0)} KB`;
    return `${bytes} B`;
  }

  const filteredRules = computed(() => {
    return rulesList.value.filter((r) => {
      if (chainFilter.value === 'all') return true;
      return r.chain.toLowerCase() === chainFilter.value.toLowerCase();
    });
  });

  async function loadFirewallRules() {
    isLoading.value = true;
    try {
      const res = await http.get<FirewallRuleItem[] | { items: FirewallRuleItem[] }>(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}`,
      );
      const raw = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      rulesList.value = raw.map((item: any) => ({
        ...item,
        id: item.id || item['.id'] || '',
        chain: item.chain || 'forward',
        action: item.action || 'accept',
        src_address: item.src_address || item['src-address'] || '',
        dst_address: item.dst_address || item['dst-address'] || '',
        protocol: item.protocol || '',
        dst_port: item.dst_port || item['dst-port'] || '',
        bytes: Number(item.bytes || 0),
        packets: Number(item.packets || 0),
        comment: item.comment || '',
        disabled: item.disabled === true || item.disabled === 'true',
        dynamic: item.dynamic === true || item.dynamic === 'true',
        invalid: item.invalid === true || item.invalid === 'true',
      }));
    } catch {
      rulesList.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function handleReorder(event: {
    fromIndex: number;
    toIndex: number;
    row: FirewallRuleItem;
  }) {
    isMoving.value = true;
    webFigStore.startSafeModeCountdown(60);

    const moved = rulesList.value.splice(event.fromIndex, 1)[0];
    rulesList.value.splice(event.toIndex, 0, moved);

    try {
      await http.post(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/move`,
        {
          numbers: event.row.id,
          destination: String(event.toIndex),
        },
      );
    } catch {
      // Manejo silencioso en fallo de red
    } finally {
      isMoving.value = false;
    }
  }

  onMounted(() => {
    loadFirewallRules();
  });
</script>

<template>
  <div class="firewall-view">
    <!-- Banner de Safe Mode si está activo -->
    <RgSafeModeBanner
      :is-active="webFigStore.isSafeModeActive"
      :remaining-seconds="webFigStore.safeModeCountdownSeconds"
    />

    <header class="view-header">
      <div>
        <h2 class="view-title">Firewall RouterOS v7 & Filtrado de Paquetes</h2>
        <p class="view-subtitle">
          Reglas ordenadas con protección Safe Mode (60s Rollback) y barras de tráfico en vivo
        </p>
      </div>

      <!-- Pestañas de Tablas de Firewall -->
      <nav class="subtabs-bar" role="tablist" aria-label="Tablas de Firewall">
        <button
          v-for="tab in [
            { id: 'filter', label: 'Filter Rules' },
            { id: 'nat', label: 'NAT' },
            { id: 'mangle', label: 'Mangle' },
            { id: 'raw', label: 'RAW' },
            { id: 'address-list', label: 'Address Lists' },
            { id: 'connections', label: 'Connections' },
          ]"
          :key="tab.id"
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === tab.id }"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="
            activeTab = tab.id as any;
            loadFirewallRules();
          "
        >
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <!-- Filtro rápido por Cadena (Chain) -->
    <div class="filter-toolbar">
      <div class="filter-item">
        <label for="filter-chain-select" class="filter-label">Filtrar por Cadena:</label>
        <select id="filter-chain-select" v-model="chainFilter" class="filter-select font-tabular">
          <option value="all">Todas las Cadenas (All)</option>
          <option value="input">input</option>
          <option value="forward">forward</option>
          <option value="output">output</option>
          <option value="prerouting">prerouting</option>
          <option value="postrouting">postrouting</option>
          <option value="srcnat">srcnat</option>
          <option value="dstnat">dstnat</option>
        </select>
      </div>

      <div class="reorder-info">
        <span class="info-icon">💡</span>
        <span
          >Arrastra filas o usa <strong>Alt + ↑ / Alt + ↓</strong> para reordenar con Safe
          Mode.</span
        >
      </div>
    </div>

    <!-- Tabla de Reglas con Barras de Tráfico Proporcionales -->
    <div class="table-card">
      <RgDataTable
        :columns="columns"
        :rows="filteredRules"
        :sortable-rows="true"
        caption="Reglas de Firewall RouterOS"
        row-key="id"
        @reorder="handleReorder"
      />
    </div>
  </div>
</template>

<style scoped>
  .firewall-view {
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
    overflow-x: auto;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 5px 12px;
    font-size: 0.78rem;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }

  .btn-subtab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .filter-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 14px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .filter-label {
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .filter-select {
    padding: 4px 8px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 4px;
    color: var(--rg-text-primary);
    font-size: 0.8rem;
  }

  .reorder-info {
    font-size: 0.78rem;
    color: var(--rg-text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .traffic-cell {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 130px;
  }

  .traffic-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
  }

  .pkts-label {
    color: var(--rg-text-muted);
    font-size: 0.7rem;
  }

  .traffic-bar-bg {
    width: 100%;
    height: 4px;
    background: var(--rg-bg-elevated);
    border-radius: 2px;
    overflow: hidden;
  }

  .traffic-bar-fill {
    height: 100%;
    background: var(--rg-accent-cyan);
    border-radius: 2px;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
