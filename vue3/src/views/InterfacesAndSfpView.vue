<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

<script setup lang="ts">
  import type { WebFigDynamic } from '@/types';
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
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
    { key: 'comment', label: 'Comentario' },
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  function formatTraffic(bps?: number): string {
    if (!bps) return '0 bps';
    if (bps >= 1000000) return `${(bps / 1000000).toFixed(1)} Mbps`;
    if (bps >= 1000) return `${(bps / 1000).toFixed(0)} kbps`;
    return `${bps} bps`;
  }

  function isWireGuardType(type?: string): boolean {
    const normalized = String(type || '').toLowerCase();
    return normalized === 'wireguard' || normalized === 'wg';
  }

  const filteredInterfaces = computed(() => {
    return interfacesList.value.filter((iface) => {
      if (activeTab.value === 'all') return true;
      if (activeTab.value === 'ethernet') return iface.type === 'ether' && !iface.is_sfp;
      if (activeTab.value === 'sfp') return Boolean(iface.is_sfp);
      if (activeTab.value === 'vlan') return iface.type === 'vlan';
      if (activeTab.value === 'bridge') return iface.type === 'bridge';
      if (activeTab.value === 'wireguard') return isWireGuardType(iface.type);
      if (activeTab.value === 'wifi') {
        return iface.type === 'wifi' || iface.type === 'wlan' || iface.type === 'cap';
      }
      return true;
    });
  });

  async function loadInterfaces(forceRefresh = false) {
    isLoading.value = true;
    try {
      const query = forceRefresh ? '?refresh=true' : '';
      const res = await http.get<InterfaceRow[] | { items: InterfaceRow[] }>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces${query}`,
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      interfacesList.value = raw.map((item: WebFigDynamic) => ({
        ...item,
        id: item.id || item['.id'] || item.name,
        mac_address: item.mac_address || item['mac-address'] || '',
        mtu: Number(item.mtu || item['actual-mtu'] || 1500),
        running: item.running === true || item.running === 'true',
        disabled: item.disabled === true || item.disabled === 'true',
        dynamic: item.dynamic === true || item.dynamic === 'true',
        is_sfp: Boolean(
          item.is_sfp ||
          String(item.name).toLowerCase().includes('sfp') ||
          String(item['default-name'] || '')
            .toLowerCase()
            .includes('sfp'),
        ),
      }));
    } catch {
      interfacesList.value = [];
    } finally {
      isLoading.value = false;
      if (activeTab.value === 'wifi') {
        loadWifiRegistrationTable();
      }
    }
  }

  const selectedCableTest = ref<WebFigDynamic>(null);
  const isCableTestModalOpen = ref(false);
  const isRunningCableTest = ref(false);

  async function openCableTest(interfaceName: string) {
    isRunningCableTest.value = true;
    selectedCableTest.value = null;
    try {
      const res = await http.post<WebFigDynamic>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/ethernet/${encodeURIComponent(interfaceName)}/cable-test`,
      );
      selectedCableTest.value = res.data;
      isCableTestModalOpen.value = true;
    } catch {
      errorMessage.value = 'Error al ejecutar cable test TDR en ' + interfaceName;
    } finally {
      isRunningCableTest.value = false;
    }
  }

  const wifiRegistrationList = ref<WebFigDynamic[]>([]);

  async function loadWifiRegistrationTable() {
    try {
      const res = await http.get<WebFigDynamic>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/wifi/registration-table`,
      );
      wifiRegistrationList.value = Array.isArray(res.data) ? res.data : (res.data?.items || []);
    } catch {
      wifiRegistrationList.value = [];
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

  import { useWebFigStore } from '@/stores/useWebFigStore';

  const webFigStore = useWebFigStore();
  const statusMessage = ref('');
  const errorMessage = ref('');
  const isCreateVlanModalOpen = ref(false);
  const isEditIfaceModalOpen = ref(false);
  const editingIface = ref<InterfaceRow | null>(null);
  const editIfaceForm = ref({
    name: '',
    mtu: 1500,
    vlan_id: 10,
    interface: '',
    comment: '',
    disabled: false,
  });

  function openEditIfaceModal(iface: InterfaceRow) {
    editingIface.value = iface;
    editIfaceForm.value = {
      name: iface.name,
      mtu: Number(iface.mtu || 1500),
      vlan_id: Number((iface as WebFigDynamic).vlan_id || (iface as WebFigDynamic)['vlan-id'] || 10),
      interface: String((iface as WebFigDynamic).interface || ''),
      comment: String(iface.comment || ''),
      disabled: Boolean(iface.disabled),
    };
    isEditIfaceModalOpen.value = true;
  }

  async function handleUpdateIface() {
    if (!editingIface.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const isVlan = editingIface.value.type === 'vlan';
      const isWg = isWireGuardType(editingIface.value.type);
      const endpoint = isVlan
        ? `/api/v1/routers/${routerId.value}/webfig/interfaces/vlan/${encodeURIComponent(editingIface.value.id)}`
        : isWg
          ? `/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard/${encodeURIComponent(editingIface.value.id)}`
          : `/api/v1/routers/${routerId.value}/webfig/interfaces/${encodeURIComponent(editingIface.value.id)}`;
      const payload = isVlan
        ? {
            name: editIfaceForm.value.name,
            vlan_id: Number(editIfaceForm.value.vlan_id),
            interface: editIfaceForm.value.interface || undefined,
            mtu: Number(editIfaceForm.value.mtu),
            comment: editIfaceForm.value.comment,
            disabled: editIfaceForm.value.disabled,
          }
        : {
            name: editIfaceForm.value.name,
            mtu: Number(editIfaceForm.value.mtu),
            comment: editIfaceForm.value.comment,
            disabled: editIfaceForm.value.disabled,
          };
      const res = await http.patch(endpoint, payload);
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as { detail?: string })?.detail || 'Modificación de interfaz en espera de aprobación en Maker-Checker.'
        : `Interfaz "${editIfaceForm.value.name}" actualizada exitosamente bajo Safe Mode.`;
      isEditIfaceModalOpen.value = false;
      loadInterfaces(true);
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || 'Error al actualizar la interfaz.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleToggleIface(iface: InterfaceRow) {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/${encodeURIComponent(iface.id)}`,
        { disabled: !iface.disabled },
      );
      webFigStore.handleMutationResponse(res, 60);
      loadInterfaces(true);
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cambiar estado de la interfaz.';
    } finally {
      isLoading.value = false;
    }
  }
  const newVlan = ref({
    name: 'vlan10',
    vlan_id: 10,
    interface: '',
    mtu: 1500,
    comment: '',
  });

  function openCreateVlanModal() {
    if (interfacesList.value.length > 0 && !newVlan.value.interface) {
      newVlan.value.interface = interfacesList.value[0].name;
    }
    isCreateVlanModalOpen.value = true;
  }

  async function handleCreateVlan() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/vlan`,
        newVlan.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as { detail?: string })?.detail || 'Solicitud de VLAN en espera de aprobación humana en la bandeja Maker-Checker.'
        : `Interfaz VLAN "${newVlan.value.name}" (ID ${newVlan.value.vlan_id}) creada exitosamente bajo Safe Mode.`;
      isCreateVlanModalOpen.value = false;
      newVlan.value = {
        name: `vlan${Number(newVlan.value.vlan_id) + 10}`,
        vlan_id: Number(newVlan.value.vlan_id) + 10,
        interface: interfacesList.value[0]?.name || 'ether1',
        mtu: 1500,
        comment: '',
      };
      loadInterfaces(true);
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || 'Error al crear la interfaz VLAN.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleDeleteVlan(iface: InterfaceRow) {
    const isWg = isWireGuardType(iface.type);
    const label = isWg ? 'WireGuard' : 'VLAN';
    if (!confirm(`¿Eliminar la interfaz ${label} "${iface.name}"?`)) {
      return;
    }
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const subPath = isWg ? 'wireguard' : 'vlan';
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/interfaces/${subPath}/${encodeURIComponent(iface.id)}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      statusMessage.value = intercepted
        ? (res.data as { detail?: string })?.detail || 'Solicitud de eliminación en espera de aprobación humana en Maker-Checker.'
        : `Interfaz ${label} "${iface.name}" eliminada exitosamente.`;
      loadInterfaces(true);
    } catch (err: unknown) {
      webFigStore.stopSafeMode?.();
      const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
      errorMessage.value =
        error.response?.data?.detail || error.detail || error.message || `Error al eliminar la interfaz ${label}.`;
    } finally {
      isLoading.value = false;
    }
  }

  const handleWebFigRefresh = (ev: Event) => {
    const detail = (ev as CustomEvent)?.detail;
    loadInterfaces(Boolean(detail?.forceRefresh ?? true));
  };

  onMounted(() => {
    loadInterfaces();
    window.addEventListener('rosgrid:webfig-refresh', handleWebFigRefresh);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('rosgrid:webfig-refresh', handleWebFigRefresh);
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

      <div class="view-header-actions">
        <button
          id="btn-webfig-refresh"
          type="button"
          class="btn-refresh font-tabular"
          :disabled="isLoading"
          aria-label="Refrescar datos directamente desde el router MikroTik"
          @click="loadInterfaces(true)"
        >
          {{ isLoading ? '🔄 Refrescando...' : '🔄 Refrescar' }}
        </button>
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
          @click="activeTab = tab.id as typeof activeTab"
        >
          {{ tab.label }}
        </button>
      </nav>

      <button
        v-if="activeTab === 'vlan' || activeTab === 'all'"
        type="button"
        class="btn-primary font-tabular"
        @click="openCreateVlanModal"
      >
        + Crear Subinterfaz VLAN
      </button>
    </header>

    <div v-if="statusMessage" class="banner banner--success" role="status">
      {{ statusMessage }}
    </div>
    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>

    <!-- Tabla Reactiva con Virtual Scrolling e Insignias -->
    <div class="table-card">
      <RgDataTable
        :columns="columns"
        :rows="filteredInterfaces"
        caption="Listado de Interfaces RouterOS"
        row-key="id"
      >
        <template #actions="{ row }">
          <div class="row-actions-group">
            <button
              v-if="row.is_sfp"
              type="button"
              class="btn-ddm font-tabular"
              aria-label="Abrir diagnóstico óptico DDM del transceptor"
              @click="openSfpDdm(row.name)"
            >
              🔍 DDM Óptico
            </button>
            <button
              type="button"
              class="btn-table-action"
              title="Editar parámetros de interfaz"
              aria-label="Editar interfaz"
              @click="openEditIfaceModal(row as InterfaceRow)"
            >
              ✏️
            </button>
            <button
              type="button"
              class="btn-table-action"
              :title="row.disabled ? 'Habilitar interfaz' : 'Deshabilitar interfaz'"
              :aria-label="row.disabled ? 'Habilitar interfaz' : 'Deshabilitar interfaz'"
              @click="handleToggleIface(row as InterfaceRow)"
            >
              {{ row.disabled ? '▶' : '⏸' }}
            </button>
            <button
              v-if="row.type === 'ether' && !row.is_sfp"
              type="button"
              class="btn-table-action"
              title="Diagnóstico TDR de pares de cobre (Cable Test)"
              aria-label="Cable test TDR"
              @click="openCableTest(row.name)"
            >
              🔌 Cable Test
            </button>
            <button
              v-if="row.type === 'vlan' || isWireGuardType(row.type)"
              type="button"
              class="btn-table-action btn-table-action--delete"
              :title="isWireGuardType(row.type) ? 'Eliminar interfaz WireGuard' : 'Eliminar interfaz VLAN'"
              :aria-label="isWireGuardType(row.type) ? 'Eliminar interfaz WireGuard' : 'Eliminar interfaz VLAN'"
              @click="handleDeleteVlan(row as InterfaceRow)"
            >
              🗑️
            </button>
          </div>
        </template>
      </RgDataTable>

      <!-- Tabla de Clientes Wi-Fi Registrados cuando la pestaña Wi-Fi está activa -->
      <div v-if="activeTab === 'wifi'" style="margin-top: 1.5rem; background: rgba(14, 23, 42, 0.7); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 8px; padding: 1.25rem;">
        <header style="margin-bottom: 0.75rem;">
          <h3 style="margin: 0; color: #00e5ff;">📶 Clientes Wi-Fi Registrados (/interface/wifi/registration-table)</h3>
          <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #94a3b8;">Estaciones inalámbricas asociadas a radios locales o virtuales de este router.</p>
        </header>

        <table class="rg-table font-tabular" style="width: 100%;">
          <thead>
            <tr>
              <th scope="col">Dirección MAC</th>
              <th scope="col">Interfaz Radio / SSID</th>
              <th scope="col">Señal (Signal dBm)</th>
              <th scope="col">Tasa TX / RX</th>
              <th scope="col">Uptime</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="wifiRegistrationList.length === 0">
              <td colspan="5" class="text-center" style="padding: 1rem; color: #64748b;">No hay clientes Wi-Fi asociados en este momento.</td>
            </tr>
            <tr v-for="c in wifiRegistrationList" :key="c.mac_address || c['mac-address'] || c['.id']">
              <td class="font-mono text-cyan font-bold">{{ c.mac_address || c['mac-address'] }}</td>
              <td class="font-mono">{{ c.interface || c.ssid || 'wifi1' }}</td>
              <td class="font-mono text-emerald">{{ c.signal || c['signal-strength'] || '-55 dBm' }}</td>
              <td class="font-mono">{{ c.tx_rate || c['tx-rate'] || '—' }} / {{ c.rx_rate || c['rx-rate'] || '—' }}</td>
              <td class="font-mono text-muted">{{ c.uptime || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
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

    <!-- Modal Crear Subinterfaz VLAN 802.1Q (/interface/vlan) -->
    <div
      v-if="isCreateVlanModalOpen"
      class="rg-modal-backdrop"
      @click.self="isCreateVlanModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-vlan-create-title">
        <header class="modal-header">
          <h3 id="modal-vlan-create-title" class="modal-title">
            🏷️ Crear Subinterfaz VLAN 802.1Q (/interface/vlan)
          </h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isCreateVlanModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleCreateVlan">
          <div class="form-group">
            <label for="vlan-create-name">Nombre de la Interfaz:</label>
            <input
              id="vlan-create-name"
              v-model="newVlan.name"
              required
              placeholder="ej. vlan10-clientes"
            />
          </div>

          <div class="form-group">
            <label for="vlan-create-id">VLAN ID (Tag 802.1Q):</label>
            <input
              id="vlan-create-id"
              v-model.number="newVlan.vlan_id"
              type="number"
              min="1"
              max="4094"
              required
            />
          </div>

          <div class="form-group">
            <label for="vlan-create-parent">Interfaz Base (Padre):</label>
            <input
              id="vlan-create-parent"
              v-model="newVlan.interface"
              required
              placeholder="ej. bridge o ether1"
            />
          </div>

          <div class="form-group">
            <label for="vlan-create-mtu">MTU:</label>
            <input
              id="vlan-create-mtu"
              v-model.number="newVlan.mtu"
              type="number"
              min="68"
              max="65535"
              placeholder="1500"
            />
          </div>

          <div class="form-group">
            <label for="vlan-create-comment">Comentario:</label>
            <input id="vlan-create-comment" v-model="newVlan.comment" placeholder="ej. Subinterfaz para Troncal de Acceso" />
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateVlanModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Crear con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar Interfaz -->
    <div
      v-if="isEditIfaceModalOpen && editingIface"
      class="rg-modal-backdrop"
      @click.self="isEditIfaceModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-iface-edit-title">
        <header class="modal-header">
          <h3 id="modal-iface-edit-title" class="modal-title">
            ✏️ Editar Interfaz — {{ editingIface.name }}
          </h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isEditIfaceModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleUpdateIface">
          <div class="form-group">
            <label for="iface-edit-name">Nombre de la Interfaz:</label>
            <input id="iface-edit-name" v-model="editIfaceForm.name" required />
          </div>

          <div v-if="editingIface.type === 'vlan'" class="form-group">
            <label for="iface-edit-vlan-id">VLAN ID (Tag 802.1Q):</label>
            <input
              id="iface-edit-vlan-id"
              v-model.number="editIfaceForm.vlan_id"
              type="number"
              min="1"
              max="4094"
              required
            />
          </div>

          <div class="form-group">
            <label for="iface-edit-mtu">MTU:</label>
            <input
              id="iface-edit-mtu"
              v-model.number="editIfaceForm.mtu"
              type="number"
              min="68"
              max="65535"
              required
            />
          </div>

          <div class="form-group">
            <label for="iface-edit-comment">Comentario:</label>
            <input id="iface-edit-comment" v-model="editIfaceForm.comment" />
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditIfaceModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Diagnóstico TDR Cable Test -->
    <div
      v-if="isCableTestModalOpen && selectedCableTest"
      class="rg-modal-backdrop"
      @click.self="isCableTestModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-cabletest-title">
        <header class="modal-header">
          <h3 id="modal-cabletest-title" class="modal-title">
            🔌 Diagnóstico TDR de Cable Ethernet (Cable Test)
          </h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar diagnóstico"
            @click="isCableTestModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="modal-body font-tabular">
          <div style="background: rgba(14, 23, 42, 0.6); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 6px; padding: 12px; margin-bottom: 12px;">
            <div>Estado General: <strong :style="{ color: selectedCableTest.status === 'ok' || selectedCableTest.status === 'connected' ? '#10b981' : '#f59e0b' }">{{ selectedCableTest.status?.toUpperCase() || 'COMPLETADO' }}</strong></div>
            <div v-if="selectedCableTest['cable-pairs'] || selectedCableTest.cable_pairs" style="margin-top: 6px; font-size: 0.85rem; color: #94a3b8;">
              Pares: {{ selectedCableTest['cable-pairs'] || selectedCableTest.cable_pairs }}
            </div>
          </div>
          <pre class="font-mono" style="background: #030712; padding: 10px; border-radius: 6px; color: #a5f3fc; font-size: 0.8rem; overflow-x: auto; max-height: 200px;">{{ JSON.stringify(selectedCableTest, null, 2) }}</pre>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-secondary" @click="isCableTestModalOpen = false">Cerrar</button>
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
    gap: 10px;
    padding: 12px 16px;
    border-top: 1px solid var(--rg-border-grid);
  }

  .btn-primary {
    background: var(--rg-accent-cyan, #06b6d4);
    color: #0f172a;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    border: none;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-primary:hover {
    background: #0891b2;
  }

  .btn-secondary {
    padding: 7px 14px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 6px;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-secondary:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
  }

  .row-actions-group {
    display: inline-flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
  }

  .btn-table-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 4px;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.75rem;
    font-weight: 500;
    padding: 3px 8px;
    cursor: pointer;
    transition: all 0.15s ease;
    line-height: 1.2;
  }

  .btn-table-action:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
    box-shadow: 0 0 8px rgba(34, 211, 238, 0.15);
  }

  .btn-table-action--delete {
    border-color: rgba(239, 68, 68, 0.35);
    color: #fca5a5;
  }

  .btn-table-action--delete:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.2);
  }

  .banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
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

  .modal-form {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .form-group label {
    font-size: 0.82rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .form-group input,
  .form-group select {
    background: var(--rg-bg-input, #0f172a);
    color: var(--rg-text-primary, #f8fafc);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.85rem;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .view-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-refresh {
    background: var(--rg-bg-surface);
    color: var(--rg-text-primary);
    border: 1px solid var(--rg-border-grid);
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  .btn-refresh:hover:not(:disabled) {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-refresh:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  @media (max-width: 640px) {
    .ddm-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
