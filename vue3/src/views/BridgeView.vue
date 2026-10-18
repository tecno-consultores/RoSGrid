<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  interface BridgeRow extends Record<string, unknown> {
    id: string;
    name: string;
    mtu?: number;
    mac_address?: string;
    fast_forward?: boolean;
    vlan_filtering?: boolean;
    protocol_mode?: string;
    running?: boolean;
    disabled?: boolean;
    comment?: string;
  }

  interface BridgePortRow extends Record<string, unknown> {
    id: string;
    interface: string;
    bridge: string;
    priority?: number;
    path_cost?: number;
    pvid?: number;
    frame_types?: string;
    ingress_filtering?: boolean;
    disabled?: boolean;
  }

  interface BridgeVlanRow extends Record<string, unknown> {
    id: string;
    bridge: string;
    vlan_ids?: string;
    tagged?: string;
    untagged?: string;
    current_tagged?: string;
    current_untagged?: string;
    disabled?: boolean;
  }

  interface BridgeHostRow extends Record<string, unknown> {
    id: string;
    mac_address: string;
    vid?: number;
    interface?: string;
    bridge?: string;
    age?: string;
    dynamic?: boolean;
    local?: boolean;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<'bridges' | 'ports' | 'vlans' | 'hosts'>('bridges');
  const isLoading = ref(false);
  const statusMessage = ref('');
  const errorMessage = ref('');

  const bridgesList = ref<BridgeRow[]>([]);
  const portsList = ref<BridgePortRow[]>([]);
  const vlansList = ref<BridgeVlanRow[]>([]);
  const hostsList = ref<BridgeHostRow[]>([]);

  // Modals
  const isCreateBridgeModalOpen = ref(false);
  const isCreatePortModalOpen = ref(false);
  const newBridge = ref({
    name: 'bridge1',
    vlan_filtering: false,
    protocol_mode: 'rstp',
    comment: '',
  });
  const newPort = ref({
    interface: '',
    bridge: '',
    pvid: 1,
    frame_types: 'admit-all',
    ingress_filtering: false,
  });

  const bridgeColumns: TableColumn<BridgeRow>[] = [
    { key: 'name', label: 'Nombre Bridge', sortable: true },
    { key: 'mac_address', label: 'Dirección MAC' },
    { key: 'protocol_mode', label: 'Modo STP', align: 'center' },
    {
      key: 'vlan_filtering',
      label: 'VLAN Filtering',
      align: 'center',
      formatter: (row) => (row.vlan_filtering ? '✅ Activo' : '❌ Inactivo'),
    },
    { key: 'mtu', label: 'MTU', align: 'right' },
    { key: 'comment', label: 'Comentario' },
  ];

  const portColumns: TableColumn<BridgePortRow>[] = [
    { key: 'interface', label: 'Interfaz Puerto', sortable: true },
    { key: 'bridge', label: 'Bridge Destino', sortable: true },
    { key: 'pvid', label: 'PVID', align: 'center' },
    { key: 'frame_types', label: 'Frame Types', align: 'center' },
    {
      key: 'ingress_filtering',
      label: 'Ingress Filtering',
      align: 'center',
      formatter: (row) => (row.ingress_filtering ? 'Sí' : 'No'),
    },
    { key: 'priority', label: 'Prioridad', align: 'right' },
  ];

  const vlanColumns: TableColumn<BridgeVlanRow>[] = [
    { key: 'bridge', label: 'Bridge', sortable: true },
    { key: 'vlan_ids', label: 'VLAN IDs', sortable: true },
    { key: 'tagged', label: 'Tagged' },
    { key: 'untagged', label: 'Untagged' },
    { key: 'current_tagged', label: 'Current Tagged' },
    { key: 'current_untagged', label: 'Current Untagged' },
  ];

  const hostColumns: TableColumn<BridgeHostRow>[] = [
    { key: 'mac_address', label: 'Dirección MAC', sortable: true },
    { key: 'vid', label: 'VID', align: 'center' },
    { key: 'interface', label: 'Interfaz', sortable: true },
    { key: 'bridge', label: 'Bridge', sortable: true },
    { key: 'age', label: 'Age', align: 'right' },
  ];

  async function loadData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      if (activeTab.value === 'bridges') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        bridgesList.value = items.map((b: any) => ({
          ...b,
          id: b.id || b['.id'] || b.name,
          mac_address: b.mac_address || b['mac-address'] || '',
          vlan_filtering: b.vlan_filtering ?? b['vlan-filtering'] === 'true' ?? false,
          protocol_mode: b.protocol_mode || b['protocol-mode'] || 'none',
          running: b.running !== 'false' && b.running !== false,
          disabled: b.disabled === 'true' || b.disabled === true,
        }));
      } else if (activeTab.value === 'ports') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        portsList.value = items.map((p: any) => ({
          ...p,
          id: p.id || p['.id'] || `${p.bridge}-${p.interface}`,
          pvid: p.pvid ? Number(p.pvid) : 1,
          frame_types: p.frame_types || p['frame-types'] || 'admit-all',
          ingress_filtering: p.ingress_filtering ?? p['ingress-filtering'] === 'true',
          disabled: p.disabled === 'true' || p.disabled === true,
        }));
      } else if (activeTab.value === 'vlans') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/vlans`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        vlansList.value = items.map((v: any) => ({
          ...v,
          id: v.id || v['.id'] || `${v.bridge}-${v.vlan_ids || v['vlan-ids']}`,
          vlan_ids: v.vlan_ids || v['vlan-ids'] || '',
          current_tagged: v.current_tagged || v['current-tagged'] || '',
          current_untagged: v.current_untagged || v['current-untagged'] || '',
        }));
      } else if (activeTab.value === 'hosts') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/hosts`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        hostsList.value = items.map((h: any) => ({
          ...h,
          id: h.id || h['.id'] || `${h.bridge}-${h.mac_address || h['mac-address']}`,
          mac_address: h.mac_address || h['mac-address'] || '',
          vid: h.vid ? Number(h.vid) : undefined,
          dynamic: h.dynamic === 'true' || h.dynamic === true,
          local: h.local === 'true' || h.local === true,
        }));
      }
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar datos del módulo Bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateBridge() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge`, newBridge.value);
      statusMessage.value = `Bridge "${newBridge.value.name}" creado exitosamente bajo Safe Mode.`;
      isCreateBridgeModalOpen.value = false;
      newBridge.value = { name: `bridge${bridgesList.value.length + 1}`, vlan_filtering: false, protocol_mode: 'rstp', comment: '' };
      loadData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear el bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreatePort() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports`, newPort.value);
      statusMessage.value = `Puerto agregado al Bridge "${newPort.value.bridge}" exitosamente.`;
      isCreatePortModalOpen.value = false;
      loadData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al agregar el puerto al bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  function setTab(tab: 'bridges' | 'ports' | 'vlans' | 'hosts') {
    activeTab.value = tab;
    loadData();
  }

  onMounted(() => {
    loadData();
  });
</script>

<template>
  <div class="bridge-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Gestor Bridge & VLAN Switching (Capa 2)</h1>
        <p class="view-subtitle">
          Configuración de Bridges MikroTik v7, Puertos STP/RSTP, Tabla VLAN Filtering y FDB MAC Hosts.
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'bridges'"
          type="button"
          class="btn-primary"
          @click="isCreateBridgeModalOpen = true"
        >
          + Crear Bridge
        </button>
        <button
          v-if="activeTab === 'ports'"
          type="button"
          class="btn-primary"
          @click="isCreatePortModalOpen = true"
        >
          + Agregar Puerto
        </button>
        <button
          type="button"
          class="btn-refresh"
          :disabled="isLoading"
          aria-label="Refrescar datos"
          @click="loadData"
        >
          🔄 Refrescar
        </button>
      </div>
    </header>

    <div v-if="statusMessage" class="banner banner--success" role="status">
      {{ statusMessage }}
    </div>
    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>

    <!-- Navegación por pestañas -->
    <nav class="tabs-nav" aria-label="Pestañas de configuración Bridge">
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'bridges' }"
        @click="setTab('bridges')"
      >
        🌉 Bridges ({{ bridgesList.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'ports' }"
        @click="setTab('ports')"
      >
        🔌 Puertos Miembro ({{ portsList.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'vlans' }"
        @click="setTab('vlans')"
      >
        🏷️ Tabla VLANs ({{ vlansList.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'hosts' }"
        @click="setTab('hosts')"
      >
        💻 Hosts / FDB MAC ({{ hostsList.length }})
      </button>
    </nav>

    <!-- Contenido según pestaña activa -->
    <div class="tab-content">
      <div v-if="activeTab === 'bridges'">
        <RgDataTable
          :columns="(bridgeColumns as any)"
          :rows="bridgesList"
          caption="Interfaces Bridge RouterOS"
          row-key="id"
        />
      </div>

      <div v-else-if="activeTab === 'ports'">
        <RgDataTable
          :columns="(portColumns as any)"
          :rows="portsList"
          caption="Puertos Miembros Bridge"
          row-key="id"
        />
      </div>

      <div v-else-if="activeTab === 'vlans'">
        <RgDataTable
          :columns="(vlanColumns as any)"
          :rows="vlansList"
          caption="Tabla VLAN Switching"
          row-key="id"
        />
      </div>

      <div v-else-if="activeTab === 'hosts'">
        <RgDataTable
          :columns="(hostColumns as any)"
          :rows="hostsList"
          caption="Tabla de Direcciones MAC Hosts (FDB)"
          row-key="id"
        />
      </div>
    </div>

    <!-- Modal Crear Bridge -->
    <div v-if="isCreateBridgeModalOpen" class="modal-backdrop" @click.self="isCreateBridgeModalOpen = false">
      <div class="modal-card" role="dialog" aria-labelledby="modal-bridge-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-bridge-title">Crear Nuevo Bridge MikroTik</h2>
          <button type="button" class="btn-close" @click="isCreateBridgeModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateBridge">
          <div class="form-group">
            <label for="bridge-name">Nombre del Bridge:</label>
            <input id="bridge-name" v-model="newBridge.name" required placeholder="ej. bridge-lan" />
          </div>
          <div class="form-group">
            <label for="bridge-protocol">Protocolo Spanning Tree (STP):</label>
            <select id="bridge-protocol" v-model="newBridge.protocol_mode">
              <option value="rstp">RSTP (Rapid STP - Predeterminado)</option>
              <option value="stp">STP Estándar</option>
              <option value="mstp">MSTP (Multiple STP)</option>
              <option value="none">Sin STP (None)</option>
            </select>
          </div>
          <div class="form-group form-group--checkbox">
            <label>
              <input v-model="newBridge.vlan_filtering" type="checkbox" />
              Activar VLAN Filtering (v7 Hardware Offload)
            </label>
          </div>
          <div class="form-group">
            <label for="bridge-comment">Comentario:</label>
            <input id="bridge-comment" v-model="newBridge.comment" placeholder="ej. Bridge Anillo de Distribución" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateBridgeModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Crear con Safe Mode</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Agregar Puerto -->
    <div v-if="isCreatePortModalOpen" class="modal-backdrop" @click.self="isCreatePortModalOpen = false">
      <div class="modal-card" role="dialog" aria-labelledby="modal-port-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-port-title">Agregar Puerto al Bridge</h2>
          <button type="button" class="btn-close" @click="isCreatePortModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreatePort">
          <div class="form-group">
            <label for="port-iface">Interfaz Física:</label>
            <input id="port-iface" v-model="newPort.interface" required placeholder="ej. ether2 o sfp-sfpplus1" />
          </div>
          <div class="form-group">
            <label for="port-bridge">Bridge Destino:</label>
            <input id="port-bridge" v-model="newPort.bridge" required placeholder="ej. bridge-lan" />
          </div>
          <div class="form-group">
            <label for="port-pvid">PVID (Port VLAN ID):</label>
            <input id="port-pvid" v-model.number="newPort.pvid" type="number" min="1" max="4094" required />
          </div>
          <div class="form-group">
            <label for="port-frame-types">Frame Types:</label>
            <select id="port-frame-types" v-model="newPort.frame_types">
              <option value="admit-all">Admit All (Tagged y Untagged)</option>
              <option value="admit-only-untagged-and-priority-tagged">Solo Untagged (Acceso)</option>
              <option value="admit-only-vlan-tagged">Solo Tagged (Trunk)</option>
            </select>
          </div>
          <div class="form-group form-group--checkbox">
            <label>
              <input v-model="newPort.ingress_filtering" type="checkbox" />
              Ingress Filtering (Descartar VLANs no registradas)
            </label>
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreatePortModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Asignar con Safe Mode</button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .bridge-view {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }
  .view-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--rg-text-primary);
    margin: 0;
  }
  .view-subtitle {
    font-size: 0.875rem;
    color: var(--rg-text-secondary);
    margin: 4px 0 0 0;
  }
  .header-actions {
    display: flex;
    gap: 8px;
  }
  .btn-primary {
    background: var(--rg-accent-cyan, #06b6d4);
    color: #0f172a;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
  }
  .btn-primary:hover {
    background: #0891b2;
  }
  .btn-refresh {
    background: var(--rg-bg-surface);
    color: var(--rg-text-primary);
    border: 1px solid var(--rg-border-grid);
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
  }
  .tabs-nav {
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--rg-border-grid);
    padding-bottom: 8px;
  }
  .tab-btn {
    background: transparent;
    color: var(--rg-text-secondary);
    border: 1px solid transparent;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
  }
  .tab-btn--active {
    background: var(--rg-bg-surface);
    color: var(--rg-accent-cyan, #06b6d4);
    border-color: var(--rg-border-grid);
    font-weight: 600;
  }
  .banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.875rem;
  }
  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-card {
    background: var(--rg-bg-surface, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 8px;
    width: 100%;
    max-width: 520px;
    padding: 20px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    font-size: 1.2rem;
    cursor: pointer;
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 14px;
  }
  .form-group label {
    font-size: 0.875rem;
    color: var(--rg-text-secondary);
  }
  .form-group input,
  .form-group select {
    background: var(--rg-bg-input, #0f172a);
    color: var(--rg-text-primary, #f8fafc);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 8px 12px;
  }
  .form-group--checkbox label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
  }
  .btn-secondary {
    background: transparent;
    color: var(--rg-text-secondary);
    border: 1px solid var(--rg-border-grid);
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
