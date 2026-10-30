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
  const isEditBridgeModalOpen = ref(false);
  const editingBridgeId = ref('');
  const editBridgeForm = ref({
    name: '',
    vlan_filtering: false,
    protocol_mode: 'rstp',
    mtu: 1500,
    disabled: false,
    comment: '',
  });

  const isCreatePortModalOpen = ref(false);
  const isEditPortModalOpen = ref(false);
  const editingPortId = ref('');
  const editPortForm = ref({
    interface: '',
    bridge: '',
    pvid: 1,
    frame_types: 'admit-all',
    hw: true,
    trusted: false,
    disabled: false,
    comment: '',
  });

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

  const isCreateVlanModalOpen = ref(false);
  const isEditVlanModalOpen = ref(false);
  const editingVlanId = ref('');
  const editVlanForm = ref({
    bridge: '',
    vlan_ids: '',
    tagged: '',
    untagged: '',
    comment: '',
    disabled: false,
  });
  const newVlan = ref({
    bridge: '',
    vlan_ids: '10',
    tagged: '',
    untagged: '',
    comment: '',
    disabled: false,
  });

  const isCreateInterfaceVlanModalOpen = ref(false);
  const newInterfaceVlan = ref({
    name: 'vlan10',
    vlan_id: 10,
    interface: '',
    mtu: 1500,
    comment: '',
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
    { key: 'actions', label: 'Acciones', align: 'center' },
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
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  const vlanColumns: TableColumn<BridgeVlanRow>[] = [
    { key: 'bridge', label: 'Bridge', sortable: true },
    { key: 'vlan_ids', label: 'VLAN IDs', sortable: true },
    { key: 'tagged', label: 'Tagged' },
    { key: 'untagged', label: 'Untagged' },
    { key: 'current_tagged', label: 'Current Tagged' },
    { key: 'current_untagged', label: 'Current Untagged' },
    { key: 'actions', label: 'Acciones', align: 'center' },
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
        const res = await http.get<any>(
          `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
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
        const res = await http.get<any>(
          `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        portsList.value = items.map((p: any) => ({
          ...p,
          id: p.id || p['.id'] || `${p.bridge}-${p.interface}`,
          pvid: p.pvid ? Number(p.pvid) : 1,
          frame_types: p.frame_types || p['frame-types'] || 'admit-all',
          ingress_filtering: p.ingress_filtering ?? p['ingress-filtering'] === 'true',
          disabled: p.disabled === 'true' || p.disabled === true,
        }));
      } else if (activeTab.value === 'vlans') {
        const res = await http.get<any>(
          `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/vlans`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        vlansList.value = items.map((v: any) => ({
          ...v,
          id: v.id || v['.id'] || `${v.bridge}-${v.vlan_ids || v['vlan-ids']}`,
          vlan_ids: v.vlan_ids || v['vlan-ids'] || '',
          current_tagged: v.current_tagged || v['current-tagged'] || '',
          current_untagged: v.current_untagged || v['current-untagged'] || '',
        }));
      } else if (activeTab.value === 'hosts') {
        const res = await http.get<any>(
          `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/hosts`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
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
      errorMessage.value =
        error.detail || error.message || 'Error al cargar datos del módulo Bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateBridge() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge`,
        newBridge.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de Bridge en espera de aprobación humana en Maker-Checker.'
        : `Bridge "${newBridge.value.name}" creado exitosamente bajo Safe Mode.`;
      isCreateBridgeModalOpen.value = false;
      newBridge.value = {
        name: `bridge${bridgesList.value.length + 1}`,
        vlan_filtering: false,
        protocol_mode: 'rstp',
        comment: '',
      };
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear el bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreatePort() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports`,
        newPort.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de puerto Bridge en espera de aprobación humana en Maker-Checker.'
        : `Puerto agregado al Bridge "${newPort.value.bridge}" exitosamente.`;
      isCreatePortModalOpen.value = false;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al agregar el puerto al bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  function openEditBridgeModal(bridge: BridgeRow) {
    editingBridgeId.value = bridge.id;
    editBridgeForm.value = {
      name: bridge.name,
      vlan_filtering: Boolean(bridge.vlan_filtering),
      protocol_mode: bridge.protocol_mode || 'rstp',
      mtu: Number(bridge.mtu || 1500),
      disabled: Boolean(bridge.disabled),
      comment: String(bridge.comment || ''),
    };
    isEditBridgeModalOpen.value = true;
  }

  async function handleUpdateBridge() {
    if (!editingBridgeId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/${encodeURIComponent(editingBridgeId.value)}`,
        editBridgeForm.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Modificación de Bridge en espera de aprobación en Maker-Checker.'
        : `Bridge "${editBridgeForm.value.name}" actualizado exitosamente bajo Safe Mode.`;
      isEditBridgeModalOpen.value = false;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al actualizar el bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleDeleteBridge(bridge: BridgeRow) {
    if (!confirm(`¿Eliminar el Bridge "${bridge.name}"?`)) {
      return;
    }
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/${encodeURIComponent(bridge.id)}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Eliminación de Bridge en espera de aprobación en Maker-Checker.'
        : `Bridge "${bridge.name}" eliminado exitosamente bajo Safe Mode.`;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al eliminar el bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  function openEditPortModal(port: BridgePortRow) {
    editingPortId.value = port.id;
    editPortForm.value = {
      interface: port.interface,
      bridge: port.bridge,
      pvid: Number(port.pvid || 1),
      frame_types: port.frame_types || 'admit-all',
      hw: port.hw !== false && port.hw !== 'false',
      trusted: port.trusted === true || port.trusted === 'true',
      disabled: Boolean(port.disabled),
      comment: String(port.comment || ''),
    };
    isEditPortModalOpen.value = true;
  }

  async function handleUpdatePort() {
    if (!editingPortId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports/${encodeURIComponent(editingPortId.value)}`,
        editPortForm.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Modificación de puerto Bridge en espera de aprobación en Maker-Checker.'
        : `Puerto "${editPortForm.value.interface}" actualizado en Bridge "${editPortForm.value.bridge}".`;
      isEditPortModalOpen.value = false;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al actualizar el puerto del bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleDeletePort(port: BridgePortRow) {
    if (!confirm(`¿Sacar la interfaz "${port.interface}" del Bridge "${port.bridge}"?`)) {
      return;
    }
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/ports/${encodeURIComponent(port.id)}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud para sacar puerto del Bridge en espera de aprobación en Maker-Checker.'
        : `Puerto "${port.interface}" liberado del Bridge "${port.bridge}" exitosamente.`;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al sacar el puerto del bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  function openEditVlanModal(vlan: BridgeVlanRow) {
    editingVlanId.value = vlan.id;
    editVlanForm.value = {
      bridge: vlan.bridge,
      vlan_ids: String(vlan.vlan_ids || ''),
      tagged: String(vlan.tagged || ''),
      untagged: String(vlan.untagged || ''),
      comment: String(vlan.comment || ''),
      disabled: Boolean(vlan.disabled),
    };
    isEditVlanModalOpen.value = true;
  }

  async function handleUpdateVlan() {
    if (!editingVlanId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/vlans/${encodeURIComponent(editingVlanId.value)}`,
        editVlanForm.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Modificación de VLAN Bridge en espera de aprobación en Maker-Checker.'
        : `VLAN "${editVlanForm.value.vlan_ids}" actualizada exitosamente.`;
      isEditVlanModalOpen.value = false;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al actualizar la VLAN del bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  function openCreateVlanModal() {
    if (bridgesList.value.length > 0 && !newVlan.value.bridge) {
      newVlan.value.bridge = bridgesList.value[0].name;
    }
    isCreateVlanModalOpen.value = true;
  }

  function openCreateInterfaceVlanModal() {
    if (bridgesList.value.length > 0 && !newInterfaceVlan.value.interface) {
      newInterfaceVlan.value.interface = bridgesList.value[0].name;
    }
    isCreateInterfaceVlanModalOpen.value = true;
  }

  async function handleCreateVlan() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/vlans`,
        newVlan.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de Bridge VLAN en espera de aprobación humana en Maker-Checker.'
        : `VLAN(s) "${newVlan.value.vlan_ids}" agregada(s) al Bridge "${newVlan.value.bridge}" bajo Safe Mode.`;
      isCreateVlanModalOpen.value = false;
      newVlan.value = {
        bridge: bridgesList.value[0]?.name || 'bridge',
        vlan_ids: '',
        tagged: '',
        untagged: '',
        comment: '',
        disabled: false,
      };
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || 'Error al crear la VLAN en el bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleDeleteVlan(vlan: BridgeVlanRow) {
    if (!confirm(`¿Eliminar la entrada de VLAN "${vlan.vlan_ids}" del Bridge "${vlan.bridge}"?`)) {
      return;
    }
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/bridge/vlans/${vlan.id}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de eliminación en espera de aprobación humana en Maker-Checker.'
        : `VLAN "${vlan.vlan_ids}" eliminada del Bridge con éxito.`;
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || 'Error al eliminar la VLAN del bridge.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateInterfaceVlan() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/vlan`,
        newInterfaceVlan.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de subinterfaz VLAN en espera de aprobación humana en Maker-Checker.'
        : `Subinterfaz VLAN "${newInterfaceVlan.value.name}" (ID ${newInterfaceVlan.value.vlan_id}) creada exitosamente bajo Safe Mode.`;
      isCreateInterfaceVlanModalOpen.value = false;
      newInterfaceVlan.value = {
        name: `vlan${Number(newInterfaceVlan.value.vlan_id) + 10}`,
        vlan_id: Number(newInterfaceVlan.value.vlan_id) + 10,
        interface: bridgesList.value[0]?.name || 'bridge',
        mtu: 1500,
        comment: '',
      };
      loadData();
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || 'Error al crear la subinterfaz VLAN.';
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
          Configuración de Bridges MikroTik v7, Puertos STP/RSTP, Tabla VLAN Filtering y FDB MAC
          Hosts.
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
          v-if="activeTab === 'vlans'"
          type="button"
          class="btn-primary"
          @click="openCreateVlanModal"
        >
          + Definir VLAN en Bridge
        </button>
        <button
          v-if="activeTab === 'vlans'"
          type="button"
          class="btn-secondary"
          @click="openCreateInterfaceVlanModal"
        >
          + Subinterfaz 802.1Q
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
        🌉 Bridges
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'ports' }"
        @click="setTab('ports')"
      >
        🔌 Puertos Miembro
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'vlans' }"
        @click="setTab('vlans')"
      >
        🏷️ Tabla VLANs
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'hosts' }"
        @click="setTab('hosts')"
      >
        💻 Hosts / FDB MAC
      </button>
    </nav>

    <!-- Contenido según pestaña activa -->
    <div class="tab-content">
      <div v-if="activeTab === 'bridges'">
        <RgDataTable
          :columns="bridgeColumns as any"
          :rows="bridgesList"
          caption="Interfaces Bridge RouterOS"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions">
              <button
                type="button"
                class="btn-table-action"
                title="Editar Bridge"
                aria-label="Editar Bridge"
                @click="openEditBridgeModal(row as BridgeRow)"
              >
                ✏️ Editar
              </button>
              <button
                type="button"
                class="btn-table-action btn-table-action--delete"
                title="Eliminar Bridge"
                aria-label="Eliminar Bridge"
                @click="handleDeleteBridge(row as BridgeRow)"
              >
                🗑️
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <div v-else-if="activeTab === 'ports'">
        <RgDataTable
          :columns="portColumns as any"
          :rows="portsList"
          caption="Puertos Miembros Bridge"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions">
              <button
                type="button"
                class="btn-table-action"
                title="Editar parámetros de puerto en Bridge"
                aria-label="Editar puerto de Bridge"
                @click="openEditPortModal(row as BridgePortRow)"
              >
                ✏️ Editar
              </button>
              <button
                type="button"
                class="btn-table-action btn-table-action--delete"
                title="Sacar interfaz de este Bridge"
                aria-label="Sacar puerto del Bridge"
                @click="handleDeletePort(row as BridgePortRow)"
              >
                ⏏ Sacar del Bridge
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <div v-else-if="activeTab === 'vlans'">
        <RgDataTable
          :columns="vlanColumns as any"
          :rows="vlansList"
          caption="Tabla VLAN Switching"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions">
              <button
                type="button"
                class="btn-table-action"
                title="Editar regla de VLAN del Bridge"
                aria-label="Editar regla de VLAN del Bridge"
                @click="openEditVlanModal(row as BridgeVlanRow)"
              >
                ✏️ Editar
              </button>
              <button
                type="button"
                class="btn-table-action btn-table-action--delete"
                title="Eliminar regla de VLAN del Bridge"
                aria-label="Eliminar regla de VLAN del Bridge"
                @click="handleDeleteVlan(row as BridgeVlanRow)"
              >
                🗑️
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <div v-else-if="activeTab === 'hosts'">
        <RgDataTable
          :columns="hostColumns as any"
          :rows="hostsList"
          caption="Tabla de Direcciones MAC Hosts (FDB)"
          row-key="id"
        />
      </div>
    </div>

    <!-- Modal Crear Bridge -->
    <div
      v-if="isCreateBridgeModalOpen"
      class="modal-backdrop"
      @click.self="isCreateBridgeModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-bridge-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-bridge-title">Crear Nuevo Bridge MikroTik</h2>
          <button type="button" class="btn-close" @click="isCreateBridgeModalOpen = false">
            ✕
          </button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateBridge">
          <div class="form-group">
            <label for="bridge-name">Nombre del Bridge:</label>
            <input
              id="bridge-name"
              v-model="newBridge.name"
              required
              placeholder="ej. bridge-lan"
            />
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
            <input
              id="bridge-comment"
              v-model="newBridge.comment"
              placeholder="ej. Bridge Anillo de Distribución"
            />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateBridgeModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Crear con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Agregar Puerto -->
    <div
      v-if="isCreatePortModalOpen"
      class="modal-backdrop"
      @click.self="isCreatePortModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-port-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-port-title">Agregar Puerto al Bridge</h2>
          <button type="button" class="btn-close" @click="isCreatePortModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreatePort">
          <div class="form-group">
            <label for="port-iface">Interfaz Física:</label>
            <input
              id="port-iface"
              v-model="newPort.interface"
              required
              placeholder="ej. ether2 o sfp-sfpplus1"
            />
          </div>
          <div class="form-group">
            <label for="port-bridge">Bridge Destino:</label>
            <input
              id="port-bridge"
              v-model="newPort.bridge"
              required
              placeholder="ej. bridge-lan"
            />
          </div>
          <div class="form-group">
            <label for="port-pvid">PVID (Port VLAN ID):</label>
            <input
              id="port-pvid"
              v-model.number="newPort.pvid"
              type="number"
              min="1"
              max="4094"
              required
            />
          </div>
          <div class="form-group">
            <label for="port-frame-types">Frame Types:</label>
            <select id="port-frame-types" v-model="newPort.frame_types">
              <option value="admit-all">Admit All (Tagged y Untagged)</option>
              <option value="admit-only-untagged-and-priority-tagged">
                Solo Untagged (Acceso)
              </option>
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
            <button type="button" class="btn-secondary" @click="isCreatePortModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Asignar con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Definir VLAN en Bridge (/interface/bridge/vlan) -->
    <div
      v-if="isCreateVlanModalOpen"
      class="modal-backdrop"
      @click.self="isCreateVlanModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-vlan-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-vlan-title">Definir VLAN en Bridge (/interface/bridge/vlan)</h2>
          <button type="button" class="btn-close" @click="isCreateVlanModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateVlan">
          <div class="form-group">
            <label for="vlan-bridge">Bridge Destino:</label>
            <select id="vlan-bridge" v-model="newVlan.bridge" required>
              <option v-for="b in bridgesList" :key="b.name" :value="b.name">
                {{ b.name }}
              </option>
              <option v-if="bridgesList.length === 0" value="bridge">bridge</option>
            </select>
          </div>
          <div class="form-group">
            <label for="vlan-ids">VLAN IDs (Rango o Lista):</label>
            <input
              id="vlan-ids"
              v-model="newVlan.vlan_ids"
              required
              placeholder="ej. 10 o 10-20 o 10,20,30"
            />
            <small class="form-help">Identificador 802.1Q de la VLAN (1-4094 o rango).</small>
          </div>
          <div class="form-group">
            <label for="vlan-tagged">Puertos Tagged (Troncales / Trunk):</label>
            <input
              id="vlan-tagged"
              v-model="newVlan.tagged"
              placeholder="ej. ether1,sfp-sfpplus1,bridge"
            />
            <small class="form-help">Interfaces que transportan tráfico etiquetado separadas por coma.</small>
          </div>
          <div class="form-group">
            <label for="vlan-untagged">Puertos Untagged (Acceso / Access):</label>
            <input
              id="vlan-untagged"
              v-model="newVlan.untagged"
              placeholder="ej. ether2,ether3"
            />
            <small class="form-help">Interfaces de acceso sin etiqueta para esta VLAN.</small>
          </div>
          <div class="form-group">
            <label for="vlan-comment">Comentario:</label>
            <input id="vlan-comment" v-model="newVlan.comment" placeholder="ej. VLAN Clientes Residenciales" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateVlanModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Definir con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Crear Subinterfaz VLAN 802.1Q (/interface/vlan) -->
    <div
      v-if="isCreateInterfaceVlanModalOpen"
      class="modal-backdrop"
      @click.self="isCreateInterfaceVlanModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-iface-vlan-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-iface-vlan-title">Crear Subinterfaz VLAN (/interface/vlan)</h2>
          <button type="button" class="btn-close" @click="isCreateInterfaceVlanModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateInterfaceVlan">
          <div class="form-group">
            <label for="iface-vlan-name">Nombre de la Subinterfaz:</label>
            <input
              id="iface-vlan-name"
              v-model="newInterfaceVlan.name"
              required
              placeholder="ej. vlan10-mgmt"
            />
          </div>
          <div class="form-group">
            <label for="iface-vlan-id">VLAN ID (Tag 802.1Q):</label>
            <input
              id="iface-vlan-id"
              v-model.number="newInterfaceVlan.vlan_id"
              type="number"
              min="1"
              max="4094"
              required
            />
          </div>
          <div class="form-group">
            <label for="iface-vlan-parent">Interfaz Base (Padre):</label>
            <input
              id="iface-vlan-parent"
              v-model="newInterfaceVlan.interface"
              required
              placeholder="ej. bridge o ether1"
            />
          </div>
          <div class="form-group">
            <label for="iface-vlan-mtu">MTU:</label>
            <input
              id="iface-vlan-mtu"
              v-model.number="newInterfaceVlan.mtu"
              type="number"
              min="68"
              max="65535"
              placeholder="1500"
            />
          </div>
          <div class="form-group">
            <label for="iface-vlan-comment">Comentario:</label>
            <input id="iface-vlan-comment" v-model="newInterfaceVlan.comment" placeholder="ej. Subinterfaz Gateway para IP" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateInterfaceVlanModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Crear con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar Bridge -->
    <div
      v-if="isEditBridgeModalOpen"
      class="modal-backdrop"
      @click.self="isEditBridgeModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-bridge-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-bridge-title">Editar Bridge ({{ editBridgeForm.name }})</h2>
          <button type="button" class="btn-close" @click="isEditBridgeModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdateBridge">
          <div class="form-group">
            <label for="edit-bridge-name">Nombre del Bridge:</label>
            <input id="edit-bridge-name" v-model="editBridgeForm.name" required />
          </div>
          <div class="form-group">
            <label for="edit-bridge-protocol">Protocolo Spanning Tree (STP):</label>
            <select id="edit-bridge-protocol" v-model="editBridgeForm.protocol_mode">
              <option value="rstp">RSTP (Rapid STP)</option>
              <option value="stp">STP Estándar</option>
              <option value="mstp">MSTP</option>
              <option value="none">Sin STP (None)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="edit-bridge-mtu">MTU:</label>
            <input id="edit-bridge-mtu" v-model.number="editBridgeForm.mtu" type="number" min="68" max="65535" />
          </div>
          <div class="form-group form-group--checkbox">
            <label>
              <input v-model="editBridgeForm.vlan_filtering" type="checkbox" />
              Activar VLAN Filtering (v7 Hardware Offload)
            </label>
          </div>
          <div class="form-group form-group--checkbox">
            <label>
              <input v-model="editBridgeForm.disabled" type="checkbox" />
              Deshabilitado (Disabled)
            </label>
          </div>
          <div class="form-group">
            <label for="edit-bridge-comment">Comentario:</label>
            <input id="edit-bridge-comment" v-model="editBridgeForm.comment" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditBridgeModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar Puerto de Bridge -->
    <div
      v-if="isEditPortModalOpen"
      class="modal-backdrop"
      @click.self="isEditPortModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-port-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-port-title">Editar Puerto de Bridge ({{ editPortForm.interface }})</h2>
          <button type="button" class="btn-close" @click="isEditPortModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdatePort">
          <div class="form-group">
            <label for="edit-port-iface">Interfaz Física:</label>
            <input id="edit-port-iface" v-model="editPortForm.interface" required />
          </div>
          <div class="form-group">
            <label for="edit-port-bridge">Bridge Destino:</label>
            <input id="edit-port-bridge" v-model="editPortForm.bridge" required />
          </div>
          <div class="form-group">
            <label for="edit-port-pvid">PVID (Port VLAN ID):</label>
            <input id="edit-port-pvid" v-model.number="editPortForm.pvid" type="number" min="1" max="4094" required />
          </div>
          <div class="form-group">
            <label for="edit-port-frame-types">Frame Types:</label>
            <select id="edit-port-frame-types" v-model="editPortForm.frame_types">
              <option value="admit-all">Admit All (Tagged y Untagged)</option>
              <option value="admit-only-untagged-and-priority-tagged">Solo Untagged (Acceso)</option>
              <option value="admit-only-vlan-tagged">Solo Tagged (Trunk)</option>
            </select>
          </div>
          <div class="form-group form-group--checkbox">
            <label>
              <input v-model="editPortForm.hw" type="checkbox" />
              Hardware Offload (L2 Switch Chip)
            </label>
          </div>
          <div class="form-group">
            <label for="edit-port-comment">Comentario:</label>
            <input id="edit-port-comment" v-model="editPortForm.comment" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditPortModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar VLAN de Bridge -->
    <div
      v-if="isEditVlanModalOpen"
      class="modal-backdrop"
      @click.self="isEditVlanModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-vlan-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-vlan-title">Editar VLAN en Bridge</h2>
          <button type="button" class="btn-close" @click="isEditVlanModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdateVlan">
          <div class="form-group">
            <label for="edit-vlan-ids">VLAN IDs:</label>
            <input id="edit-vlan-ids" v-model="editVlanForm.vlan_ids" required />
          </div>
          <div class="form-group">
            <label for="edit-vlan-tagged">Puertos Tagged:</label>
            <input id="edit-vlan-tagged" v-model="editVlanForm.tagged" />
          </div>
          <div class="form-group">
            <label for="edit-vlan-untagged">Puertos Untagged:</label>
            <input id="edit-vlan-untagged" v-model="editVlanForm.untagged" />
          </div>
          <div class="form-group">
            <label for="edit-vlan-comment">Comentario:</label>
            <input id="edit-vlan-comment" v-model="editVlanForm.comment" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditVlanModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
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
