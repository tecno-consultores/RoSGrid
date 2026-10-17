<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import type { TableColumn, SfpOpticalDdmInfo } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  interface InterfaceRow extends Record<string, unknown> {
    id: string;
    name: string;
    type: string;
    mac_address?: string;
    mtu?: number;
    running: boolean;
    disabled: boolean;
    dynamic?: boolean;
    comment?: string;
    rx_bps?: number;
    tx_bps?: number;
    is_sfp?: boolean;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));

  const activeTab = ref<'all' | 'ethernet' | 'sfp' | 'vlan' | 'bridge' | 'wireguard' | 'wifi'>(
    'all',
  );
  const isLoading = ref(false);
  const interfacesList = ref<InterfaceRow[]>([]);
  const selectedSfpDdm = ref<SfpOpticalDdmInfo | null>(null);
  const isDdmModalOpen = ref(false);

  const columns: TableColumn<InterfaceRow>[] = [
    { key: 'name', label: 'Nombre', sortable: true },
    { key: 'type', label: 'Tipo', sortable: true },
    { key: 'mac_address', label: 'Dirección MAC' },
    { key: 'mtu', label: 'MTU', align: 'center' },
    {
      key: 'traffic',
      label: 'Tráfico (RX / TX)',
      align: 'right',
      formatter: (row) => `${formatTraffic(row.rx_bps)} / ${formatTraffic(row.tx_bps)}`,
    },
  ];

  function formatTraffic(bps?: number): string {
    if (!bps) return '0 bps';
    if (bps >= 1000000) return `${(bps / 1000000).toFixed(1)} Mbps`;
    if (bps >= 1000) return `${(bps / 1000).toFixed(0)} kbps`;
    return `${bps} bps`;
  }

  const filteredInterfaces = computed(() => {
    return interfacesList.value.filter((iface) => {
      if (activeTab.value === 'all') return true;
      if (activeTab.value === 'ethernet') return iface.type === 'ether' && !iface.is_sfp;
      if (activeTab.value === 'sfp') return Boolean(iface.is_sfp);
      if (activeTab.value === 'vlan') return iface.type === 'vlan';
      if (activeTab.value === 'bridge') return iface.type === 'bridge';
      if (activeTab.value === 'wireguard') return iface.type === 'wireguard';
      if (activeTab.value === 'wifi') return iface.type === 'wifi' || iface.type === 'wlan';
      return true;
    });
  });

  async function loadInterfaces() {
    isLoading.value = true;
    try {
      const res = await http.get<InterfaceRow[] | { items: InterfaceRow[] }>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces`,
      );
      interfacesList.value = Array.isArray(res.data) ? res.data : (res.data?.items || []);
    } catch {
      interfacesList.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function openSfpDdm(interfaceName: string) {
    try {
      const res = await http.post<SfpOpticalDdmInfo>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/ethernet/${interfaceName}/sfp-monitor`,
      );
      selectedSfpDdm.value = res.data;
      isDdmModalOpen.value = true;
    } catch {
      selectedSfpDdm.value = null;
    }
  }

  function getHealthClass(health: string): string {
    if (health === 'CRITICAL_LOW_LIGHT') return 'health--critical';
    if (health === 'WARNING') return 'health--warning';
    return 'health--optimal';
  }

  onMounted(() => {
    loadInterfaces();
  });
</script>

<template>
  <div class="interfaces-view">
    <header class="view-header">
      <div>
        <h2 class="view-title">Interfaces de Red & Diagnóstico Óptico SFP</h2>
        <p class="view-subtitle">
          Supervisión en vivo de puertos Ethernet, SFP/SFP+ DDM, VLANs y Bridges
        </p>
      </div>

      <!-- Sub-pestañas de interfaces -->
      <nav class="subtabs-bar" role="tablist" aria-label="Tipos de interfaces">
        <button
          v-for="tab in [
            { id: 'all', label: 'Todas' },
            { id: 'ethernet', label: 'Ethernet' },
            { id: 'sfp', label: 'SFP Óptico' },
            { id: 'vlan', label: 'VLAN' },
            { id: 'bridge', label: 'Bridge' },
            { id: 'wireguard', label: 'WireGuard' },
            { id: 'wifi', label: 'WiFi' },
          ]"
          :key="tab.id"
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === tab.id }"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="activeTab = tab.id as any"
        >
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <!-- Tabla Reactiva con Virtual Scrolling e Insignias -->
    <div class="table-card">
      <RgDataTable
        :columns="columns"
        :rows="filteredInterfaces"
        caption="Listado de Interfaces RouterOS"
        row-key="id"
      >
        <template #actions="{ row }">
          <button
            v-if="row.is_sfp"
            type="button"
            class="btn-ddm font-tabular"
            aria-label="Abrir diagnóstico óptico DDM del transceptor"
            @click="openSfpDdm(row.name)"
          >
            🔍 DDM Óptico
          </button>
        </template>
      </RgDataTable>
    </div>

    <!-- Modal Diagnóstico Óptico SFP/SFP+ DDM -->
    <div
      v-if="isDdmModalOpen && selectedSfpDdm"
      class="rg-modal-backdrop"
      @click.self="isDdmModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-ddm-title">
        <header class="modal-header">
          <h3 id="modal-ddm-title" class="modal-title">
            🔬 Diagnóstico Óptico SFP/SFP+ DDM — {{ selectedSfpDdm.interface_name }}
          </h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar diagnóstico DDM"
            @click="isDdmModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="modal-body font-tabular">
          <div class="health-banner" :class="getHealthClass(selectedSfpDdm.optical_health)">
            Salud Óptica: <strong>{{ selectedSfpDdm.optical_health }}</strong>
          </div>

          <div class="ddm-grid">
            <div class="ddm-card">
              <span class="ddm-label">Potencia TX (Láser Salida):</span>
              <strong class="ddm-val text-cyan">{{ selectedSfpDdm.tx_power_dbm }} dBm</strong>
            </div>

            <div class="ddm-card">
              <span class="ddm-label">Potencia RX (Recepción):</span>
              <strong class="ddm-val text-emerald">{{ selectedSfpDdm.rx_power_dbm }} dBm</strong>
            </div>

            <div class="ddm-card">
              <span class="ddm-label">Temperatura Transceptor:</span>
              <strong class="ddm-val text-amber">{{ selectedSfpDdm.temperature_c }} °C</strong>
            </div>

            <div class="ddm-card">
              <span class="ddm-label">Voltaje Suministro:</span>
              <strong class="ddm-val">{{ selectedSfpDdm.voltage_v }} V</strong>
            </div>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-secondary" @click="isDdmModalOpen = false">
            Cerrar
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .interfaces-view {
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

  .btn-ddm {
    padding: 3px 8px;
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid var(--rg-accent-cyan);
    border-radius: 4px;
    color: var(--rg-accent-cyan);
    font-size: 0.75rem;
    cursor: pointer;
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 16px;
  }

  .rg-modal {
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    width: 100%;
    max-width: 520px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .modal-title {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--rg-text-primary);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 1rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .health-banner {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    text-align: center;
  }

  .health--optimal {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #10b981;
  }

  .health--warning {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #f59e0b;
  }

  .health--critical {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #ef4444;
  }

  .ddm-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .ddm-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .ddm-label {
    font-size: 0.72rem;
    color: var(--rg-text-muted);
  }

  .ddm-val {
    font-size: 1.1rem;
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

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    padding: 12px 16px;
    border-top: 1px solid var(--rg-border-grid);
  }

  .btn-secondary {
    padding: 6px 14px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    cursor: pointer;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
