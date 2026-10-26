<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import RgSafeModeBanner from '@/components/common/RgSafeModeBanner.vue';

  const route = useRoute();
  const webFigStore = useWebFigStore();

  const routerId = computed(() => String(route.params.routerId || ''));

  // Pestaña activa principal
  type MainTab = 'addresses' | 'dhcp-server' | 'dhcp-client' | 'pools' | 'dns' | 'arp';
  const activeTab = ref<MainTab>('addresses');

  // Subpestaña de DHCP Server
  type DhcpServerSubtab = 'leases' | 'servers' | 'networks';
  const activeDhcpSubtab = ref<DhcpServerSubtab>('leases');

  // Estados de datos
  const isLoading = ref(false);
  const errorMessage = ref('');
  const actionMessage = ref('');

  // Colecciones
  const ipAddresses = ref<any[]>([]);
  const dhcpLeases = ref<any[]>([]);
  const dhcpServers = ref<any[]>([]);
  const dhcpNetworks = ref<any[]>([]);
  const dhcpClients = ref<any[]>([]);
  const ipPools = ref<any[]>([]);
  const arpEntries = ref<any[]>([]);
  const dnsConfig = ref<any>({ servers: '', allow_remote_requests: false });
  const dnsStatics = ref<any[]>([]);

  // Modales
  const isAddressModalOpen = ref(false);
  const newAddress = ref({ address: '', interface: 'ether1', comment: '', disabled: false });

  const isServerModalOpen = ref(false);
  const newServer = ref({ name: 'dhcp-lan', interface: 'bridge1', address_pool: '', lease_time: '12h', disabled: false });

  const isNetworkModalOpen = ref(false);
  const newNetwork = ref({ address: '192.168.88.0/24', gateway: '192.168.88.1', dns_server: '8.8.8.8,1.1.1.1', domain: '', comment: '' });

  const isClientModalOpen = ref(false);
  const newClient = ref({ interface: 'ether1', add_default_route: true, use_peer_dns: true, use_peer_ntp: true, comment: '' });

  const isPoolModalOpen = ref(false);
  const newPool = ref({ name: 'pool-lan', ranges: '192.168.88.10-192.168.88.254' });

  // Wizard DHCP Setup en 3 pasos
  const isDhcpWizardOpen = ref(false);
  const dhcpWizard = ref({
    interface: 'bridge1',
    address: '192.168.88.1/24',
    network: '192.168.88.0/24',
    gateway: '192.168.88.1',
    poolRanges: '192.168.88.10-192.168.88.254',
    dnsServers: '8.8.8.8,1.1.1.1',
    leaseTime: '12h',
  });

  async function loadData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      if (activeTab.value === 'addresses') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/addresses`);
        ipAddresses.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'dhcp-server') {
        if (activeDhcpSubtab.value === 'leases') {
          const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/leases`);
          dhcpLeases.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
        } else if (activeDhcpSubtab.value === 'servers') {
          const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-servers`);
          dhcpServers.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
        } else {
          const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/networks`);
          dhcpNetworks.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
        }
      } else if (activeTab.value === 'dhcp-client') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-clients`);
        dhcpClients.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'pools') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/pools`);
        ipPools.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'dns') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dns`);
        dnsConfig.value = res.data?.config || {};
        dnsStatics.value = res.data?.static_records || [];
      } else if (activeTab.value === 'arp') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/arp`);
        arpEntries.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      }
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al cargar datos IP.';
    } finally {
      isLoading.value = false;
    }
  }

  function setTab(tab: MainTab) {
    activeTab.value = tab;
    loadData();
  }

  function setDhcpSubtab(sub: DhcpServerSubtab) {
    activeDhcpSubtab.value = sub;
    loadData();
  }

  // --- Acciones de Direcciones IP ---
  async function handleCreateAddress() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/addresses`, newAddress.value);
      actionMessage.value = `Dirección IP ${newAddress.value.address} asignada a ${newAddress.value.interface}.`;
      isAddressModalOpen.value = false;
      newAddress.value = { address: '', interface: 'ether1', comment: '', disabled: false };
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al asignar IP.';
    }
  }

  async function handleDeleteAddress(item: any) {
    if (!confirm(`¿Eliminar la dirección IP ${item.address}?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/addresses/${item.id || item['.id']}`);
      actionMessage.value = `Dirección ${item.address} eliminada.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar IP.';
    }
  }

  // --- Acciones DHCP Leases ---
  async function handleMakeLeaseStatic(lease: any) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/leases/${lease.id || lease['.id']}/make-static`);
      actionMessage.value = `Concesión ${lease.address} (${lease['mac-address'] || lease.mac_address}) fijada como estática.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al fijar concesión estática.';
    }
  }

  async function handleDeleteLease(lease: any) {
    if (!confirm(`¿Eliminar o expulsar la concesión ${lease.address}?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/leases/${lease.id || lease['.id']}`);
      actionMessage.value = `Concesión ${lease.address} eliminada.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar concesión.';
    }
  }

  // --- Acciones DHCP Servers & Networks ---
  async function handleCreateServer() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-servers`, newServer.value);
      actionMessage.value = `Servidor DHCP "${newServer.value.name}" creado.`;
      isServerModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear servidor DHCP.';
    }
  }

  async function handleDeleteServer(item: any) {
    if (!confirm(`¿Eliminar el servidor DHCP "${item.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-servers/${item.id || item['.id']}`);
      actionMessage.value = `Servidor DHCP eliminado.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar servidor DHCP.';
    }
  }

  async function handleCreateNetwork() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/networks`, newNetwork.value);
      actionMessage.value = `Red DHCP ${newNetwork.value.address} creada.`;
      isNetworkModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear red DHCP.';
    }
  }

  async function handleDeleteNetwork(item: any) {
    if (!confirm(`¿Eliminar la red DHCP ${item.address}?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/networks/${item.id || item['.id']}`);
      actionMessage.value = `Red DHCP eliminada.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar red DHCP.';
    }
  }

  // --- Asistente DHCP Setup Completo ---
  async function handleExecuteDhcpWizard() {
    webFigStore.startSafeModeCountdown(60);
    try {
      // 1. Crear IP Pool
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/pools`, {
        name: `pool-${dhcpWizard.value.interface}`,
        ranges: dhcpWizard.value.poolRanges,
      });
      // 2. Crear Network
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/networks`, {
        address: dhcpWizard.value.network,
        gateway: dhcpWizard.value.gateway,
        dns_server: dhcpWizard.value.dnsServers,
      });
      // 3. Crear Server
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-servers`, {
        name: `dhcp-${dhcpWizard.value.interface}`,
        interface: dhcpWizard.value.interface,
        address_pool: `pool-${dhcpWizard.value.interface}`,
        lease_time: dhcpWizard.value.leaseTime,
        disabled: false,
      });
      actionMessage.value = `Asistente completado: Servidor DHCP configurado en ${dhcpWizard.value.interface}.`;
      isDhcpWizardOpen.value = false;
      setDhcpSubtab('servers');
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al ejecutar el asistente DHCP.';
    }
  }

  // --- Acciones Clientes DHCP WAN ---
  async function handleCreateClient() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-clients`, newClient.value);
      actionMessage.value = `Cliente DHCP creado en ${newClient.value.interface}.`;
      isClientModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear cliente DHCP.';
    }
  }

  async function handleRenewClient(item: any) {
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-clients/${item.id || item['.id']}/renew`);
      actionMessage.value = `Solicitud de renovación DHCP enviada para ${item.interface}.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al renovar concesión.';
    }
  }

  async function handleReleaseClient(item: any) {
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-clients/${item.id || item['.id']}/release`);
      actionMessage.value = `Concesión DHCP liberada en ${item.interface}.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al liberar concesión.';
    }
  }

  async function handleDeleteClient(item: any) {
    if (!confirm(`¿Eliminar cliente DHCP en ${item.interface}?`)) return;
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-clients/${item.id || item['.id']}`);
      actionMessage.value = `Cliente DHCP eliminado.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar cliente DHCP.';
    }
  }

  // --- Acciones Pools & DNS ---
  async function handleCreatePool() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/pools`, newPool.value);
      actionMessage.value = `Pool de IPs "${newPool.value.name}" creado.`;
      isPoolModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear pool.';
    }
  }

  async function handleFlushDnsCache() {
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dns/flush-cache`);
      actionMessage.value = 'Caché DNS vaciada con éxito.';
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al vaciar caché DNS.';
    }
  }

  // --- Acciones ARP ---
  async function handleMakeArpStatic(arp: any) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/arp`, {
        address: arp.address,
        mac_address: arp['mac-address'] || arp.mac_address,
        interface: arp.interface,
        comment: 'Fijado desde WebFig',
      });
      actionMessage.value = `Entrada ARP ${arp.address} fijada como estática.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al fijar ARP.';
    }
  }

  onMounted(() => {
    loadData();
  });
</script>

<template>
  <div class="webfig-ip-view">
    <RgSafeModeBanner />

    <header class="view-header">
      <div class="header-titles">
        <h1 class="view-title">🔢 Módulo IP & Servicios DHCP (Layer 3)</h1>
        <p class="view-subtitle">
          Direccionamiento IPv4, servidor y clientes DHCP, pools, DNS y tabla ARP en RouterOS v7.
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'addresses'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isAddressModalOpen = true"
        >
          + Asignar Dirección IP
        </button>

        <button
          v-else-if="activeTab === 'dhcp-server' && activeDhcpSubtab === 'servers'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isDhcpWizardOpen = true"
        >
          ⚡ Asistente DHCP Setup
        </button>

        <button
          v-else-if="activeTab === 'dhcp-server' && activeDhcpSubtab === 'networks'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isNetworkModalOpen = true"
        >
          + Crear Red DHCP
        </button>

        <button
          v-else-if="activeTab === 'dhcp-client'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isClientModalOpen = true"
        >
          + Añadir Cliente DHCP
        </button>

        <button
          v-else-if="activeTab === 'pools'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isPoolModalOpen = true"
        >
          + Crear Pool de Direcciones
        </button>

        <button
          v-else-if="activeTab === 'dns'"
          type="button"
          class="btn-tactical btn-warning"
          @click="handleFlushDnsCache"
        >
          🧹 Vaciar Caché DNS
        </button>

        <button
          type="button"
          class="btn-tactical btn-outline"
          :disabled="isLoading"
          @click="loadData"
        >
          🔄 Actualizar
        </button>
      </div>
    </header>

    <!-- Alertas -->
    <div v-if="actionMessage" class="alert-box alert-success" role="status">
      <span>✔ {{ actionMessage }}</span>
    </div>
    <div v-if="errorMessage" class="alert-box alert-danger" role="alert">
      <span>⚠ {{ errorMessage }}</span>
    </div>

    <!-- Navegación de Pestañas Principales -->
    <nav class="nav-tabs" aria-label="Secciones del Módulo IP">
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'addresses' }"
        @click="setTab('addresses')"
      >
        Direcciones IP
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'dhcp-server' }"
        @click="setTab('dhcp-server')"
      >
        Servidor DHCP
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'dhcp-client' }"
        @click="setTab('dhcp-client')"
      >
        Cliente DHCP (WAN)
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'pools' }"
        @click="setTab('pools')"
      >
        Pools de Direcciones
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'dns' }"
        @click="setTab('dns')"
      >
        DNS & Registros
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'arp' }"
        @click="setTab('arp')"
      >
        Tabla ARP
      </button>
    </nav>

    <!-- Subpestañas para DHCP Server -->
    <div v-if="activeTab === 'dhcp-server'" class="subtabs-bar">
      <button
        type="button"
        class="subtab-btn"
        :class="{ 'subtab-btn--active': activeDhcpSubtab === 'leases' }"
        @click="setDhcpSubtab('leases')"
      >
        Concesiones Activas (Leases)
      </button>
      <button
        type="button"
        class="subtab-btn"
        :class="{ 'subtab-btn--active': activeDhcpSubtab === 'servers' }"
        @click="setDhcpSubtab('servers')"
      >
        Servidores DHCP
      </button>
      <button
        type="button"
        class="subtab-btn"
        :class="{ 'subtab-btn--active': activeDhcpSubtab === 'networks' }"
        @click="setDhcpSubtab('networks')"
      >
        Redes & Opciones
      </button>
    </div>

    <!-- TAB 1: DIRECCIONES IP -->
    <section v-if="activeTab === 'addresses'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Dirección CIDR</th>
              <th>Red</th>
              <th>Interfaz</th>
              <th>Comentario</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipAddresses.length === 0">
              <td colspan="6" class="empty-cell">No hay direcciones IP configuradas.</td>
            </tr>
            <tr v-for="addr in ipAddresses" :key="addr.id || addr['.id']">
              <td class="font-mono font-bold text-cyan">{{ addr.address }}</td>
              <td class="font-mono text-muted">{{ addr.network || '—' }}</td>
              <td><span class="badge-interface">{{ addr.interface }}</span></td>
              <td class="text-muted">{{ addr.comment || '—' }}</td>
              <td>
                <span :class="addr.disabled === 'true' || addr.disabled === true ? 'status-down' : 'status-up'">
                  {{ addr.disabled === 'true' || addr.disabled === true ? 'Deshabilitada' : 'Activa' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Dirección IP"
                  @click="handleDeleteAddress(addr)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 2: SERVIDOR DHCP (LEASES, SERVERS, NETWORKS) -->
    <section v-else-if="activeTab === 'dhcp-server'" class="tab-panel">
      <!-- LEASES -->
      <div v-if="activeDhcpSubtab === 'leases'" class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Dirección IP</th>
              <th>Dirección MAC</th>
              <th>Hostname del Cliente</th>
              <th>Servidor</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpLeases.length === 0">
              <td colspan="6" class="empty-cell">No hay concesiones DHCP activas actualmente.</td>
            </tr>
            <tr v-for="lease in dhcpLeases" :key="lease.id || lease['.id']">
              <td class="font-mono font-bold text-cyan">{{ lease.address }}</td>
              <td class="font-mono">{{ lease['mac-address'] || lease.mac_address || '—' }}</td>
              <td>{{ lease['host-name'] || lease.host_name || 'Desconocido' }}</td>
              <td><span class="badge-server">{{ lease.server || 'default' }}</span></td>
              <td>
                <span class="badge-status" :class="lease.dynamic === 'false' || lease.dynamic === false ? 'badge-static' : 'badge-dynamic'">
                  {{ lease.dynamic === 'false' || lease.dynamic === false ? 'Estática' : 'Dinámica' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  v-if="lease.dynamic !== 'false' && lease.dynamic !== false"
                  type="button"
                  class="btn-icon btn-cyan"
                  title="Convertir a Reservación Estática"
                  @click="handleMakeLeaseStatic(lease)"
                >
                  📌
                </button>
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Concesión"
                  @click="handleDeleteLease(lease)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- SERVERS -->
      <div v-else-if="activeDhcpSubtab === 'servers'" class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Interfaz</th>
              <th>Pool de Direcciones</th>
              <th>Tiempo de Concesión</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpServers.length === 0">
              <td colspan="6" class="empty-cell">No hay instancias de Servidor DHCP configuradas.</td>
            </tr>
            <tr v-for="srv in dhcpServers" :key="srv.id || srv['.id']">
              <td class="font-bold text-cyan">{{ srv.name }}</td>
              <td><span class="badge-interface">{{ srv.interface }}</span></td>
              <td class="font-mono">{{ srv['address-pool'] || srv.address_pool }}</td>
              <td class="font-mono">{{ srv['lease-time'] || srv.lease_time }}</td>
              <td>
                <span :class="srv.disabled === 'true' || srv.disabled === true ? 'status-down' : 'status-up'">
                  {{ srv.disabled === 'true' || srv.disabled === true ? 'Deshabilitado' : 'Activo' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Servidor"
                  @click="handleDeleteServer(srv)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- NETWORKS -->
      <div v-else class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Subred / CIDR</th>
              <th>Puerta de Enlace (Gateway)</th>
              <th>Servidores DNS</th>
              <th>Dominio</th>
              <th>Comentario</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpNetworks.length === 0">
              <td colspan="6" class="empty-cell">No hay redes DHCP configuradas.</td>
            </tr>
            <tr v-for="net in dhcpNetworks" :key="net.id || net['.id']">
              <td class="font-mono font-bold text-cyan">{{ net.address }}</td>
              <td class="font-mono">{{ net.gateway || '—' }}</td>
              <td class="font-mono text-muted">{{ net['dns-server'] || net.dns_server || '—' }}</td>
              <td>{{ net.domain || '—' }}</td>
              <td class="text-muted">{{ net.comment || '—' }}</td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Red"
                  @click="handleDeleteNetwork(net)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: CLIENTES DHCP (WAN) -->
    <section v-else-if="activeTab === 'dhcp-client'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Interfaz</th>
              <th>IP Asignada (WAN)</th>
              <th>Puerta de Enlace</th>
              <th>Ruta por Defecto</th>
              <th>DNS del Peer</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpClients.length === 0">
              <td colspan="7" class="empty-cell">No hay clientes DHCP configurados en interfaces.</td>
            </tr>
            <tr v-for="cli in dhcpClients" :key="cli.id || cli['.id']">
              <td class="font-bold"><span class="badge-interface">{{ cli.interface }}</span></td>
              <td class="font-mono text-cyan">{{ cli.address || 'Buscando...' }}</td>
              <td class="font-mono">{{ cli.gateway || '—' }}</td>
              <td>{{ cli['add-default-route'] || 'yes' }}</td>
              <td>{{ cli['use-peer-dns'] || 'yes' }}</td>
              <td>
                <span class="badge-status" :class="cli.status === 'bound' ? 'badge-static' : 'badge-dynamic'">
                  {{ cli.status || 'searching' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-cyan"
                  title="Renovar Concesión (Renew)"
                  @click="handleRenewClient(cli)"
                >
                  🔄
                </button>
                <button
                  type="button"
                  class="btn-icon btn-warning"
                  title="Liberar Concesión (Release)"
                  @click="handleReleaseClient(cli)"
                >
                  ❌
                </button>
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Cliente"
                  @click="handleDeleteClient(cli)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 4: POOLS DE DIRECCIONES -->
    <section v-else-if="activeTab === 'pools'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Nombre del Pool</th>
              <th>Rangos de Direcciones</th>
              <th>Siguiente Pool (Next Pool)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipPools.length === 0">
              <td colspan="3" class="empty-cell">No hay pools de direcciones definidos.</td>
            </tr>
            <tr v-for="pool in ipPools" :key="pool.id || pool['.id']">
              <td class="font-bold text-cyan">{{ pool.name }}</td>
              <td class="font-mono">{{ pool.ranges }}</td>
              <td class="text-muted">{{ pool['next-pool'] || pool.next_pool || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 5: DNS -->
    <section v-else-if="activeTab === 'dns'" class="tab-panel">
      <div class="dns-dashboard">
        <div class="dns-card">
          <h2 class="card-title">Configuración de Servidores DNS</h2>
          <div class="dns-row">
            <span class="dns-label">Servidores Upstream:</span>
            <span class="font-mono text-cyan">{{ dnsConfig.servers || 'Sin configurar' }}</span>
          </div>
          <div class="dns-row">
            <span class="dns-label">Permitir Peticiones Remotas:</span>
            <span>{{ dnsConfig['allow-remote-requests'] === 'yes' ? 'Sí' : 'No' }}</span>
          </div>
        </div>

        <div class="table-container">
          <h2 class="card-title">Registros DNS Estáticos</h2>
          <table class="tactical-table">
            <thead>
              <tr>
                <th>Nombre de Dominio</th>
                <th>Dirección IP</th>
                <th>TTL</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="dnsStatics.length === 0">
                <td colspan="3" class="empty-cell">No hay registros DNS estáticos configurados.</td>
              </tr>
              <tr v-for="rec in dnsStatics" :key="rec.id || rec['.id']">
                <td class="font-bold text-cyan">{{ rec.name }}</td>
                <td class="font-mono">{{ rec.address }}</td>
                <td class="font-mono text-muted">{{ rec.ttl || '1d' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 6: TABLA ARP -->
    <section v-else-if="activeTab === 'arp'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Dirección IP</th>
              <th>Dirección MAC</th>
              <th>Interfaz</th>
              <th>Tipo</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="arpEntries.length === 0">
              <td colspan="5" class="empty-cell">Tabla ARP vacía.</td>
            </tr>
            <tr v-for="arp in arpEntries" :key="arp.id || arp['.id']">
              <td class="font-mono font-bold text-cyan">{{ arp.address }}</td>
              <td class="font-mono">{{ arp['mac-address'] || arp.mac_address || '—' }}</td>
              <td><span class="badge-interface">{{ arp.interface }}</span></td>
              <td>
                <span class="badge-status" :class="arp.dynamic === 'false' || arp.dynamic === false ? 'badge-static' : 'badge-dynamic'">
                  {{ arp.dynamic === 'false' || arp.dynamic === false ? 'Estática' : 'Dinámica' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  v-if="arp.dynamic !== 'false' && arp.dynamic !== false"
                  type="button"
                  class="btn-icon btn-cyan"
                  title="Fijar Entrada ARP como Estática"
                  @click="handleMakeArpStatic(arp)"
                >
                  📌
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- MODAL: ASIGNAR DIRECCIÓN IP -->
    <div v-if="isAddressModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Asignar Dirección IP a Interfaz</h2>
        <form @submit.prevent="handleCreateAddress">
          <div class="form-group">
            <label for="addr-val">Dirección IP con Máscara CIDR</label>
            <input
              id="addr-val"
              v-model="newAddress.address"
              type="text"
              class="form-input font-mono"
              placeholder="192.168.88.1/24"
              required
            />
          </div>
          <div class="form-group">
            <label for="addr-iface">Interfaz</label>
            <input
              id="addr-iface"
              v-model="newAddress.interface"
              type="text"
              class="form-input"
              placeholder="ether1 o bridge1"
              required
            />
          </div>
          <div class="form-group">
            <label for="addr-comment">Comentario</label>
            <input
              id="addr-comment"
              v-model="newAddress.comment"
              type="text"
              class="form-input"
              placeholder="LAN Principal"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isAddressModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar bajo Safe Mode</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: ASISTENTE DHCP SETUP -->
    <div v-if="isDhcpWizardOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">⚡ Asistente de Configuración DHCP en 3 Pasos</h2>
        <p class="modal-desc text-muted">
          Configura automáticamente el Pool de IPs, la Subred y el Servidor DHCP en una sola transacción protegida.
        </p>
        <form @submit.prevent="handleExecuteDhcpWizard">
          <div class="form-group">
            <label for="wiz-iface">Interfaz Servidor</label>
            <input id="wiz-iface" v-model="dhcpWizard.interface" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="wiz-net">Subred de Clientes</label>
            <input id="wiz-net" v-model="dhcpWizard.network" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="wiz-gw">Puerta de Enlace (Gateway)</label>
            <input id="wiz-gw" v-model="dhcpWizard.gateway" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="wiz-pool">Rango de Concesiones (Pool)</label>
            <input id="wiz-pool" v-model="dhcpWizard.poolRanges" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="wiz-dns">Servidores DNS</label>
            <input id="wiz-dns" v-model="dhcpWizard.dnsServers" type="text" class="form-input font-mono" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isDhcpWizardOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Ejecutar Asistente</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR SERVIDOR DHCP INDIVIDUAL -->
    <div v-if="isServerModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Servidor DHCP</h2>
        <form @submit.prevent="handleCreateServer">
          <div class="form-group">
            <label for="srv-name">Nombre del Servidor</label>
            <input id="srv-name" v-model="newServer.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="srv-iface">Interfaz</label>
            <input id="srv-iface" v-model="newServer.interface" type="text" class="form-input" placeholder="bridge1" required />
          </div>
          <div class="form-group">
            <label for="srv-pool">Pool de Direcciones</label>
            <input id="srv-pool" v-model="newServer.address_pool" type="text" class="form-input" placeholder="pool-lan" required />
          </div>
          <div class="form-group">
            <label for="srv-lease">Tiempo de Concesión</label>
            <input id="srv-lease" v-model="newServer.lease_time" type="text" class="form-input font-mono" placeholder="12h" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isServerModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Servidor</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR POOL -->
    <div v-if="isPoolModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Pool de Direcciones IP</h2>
        <form @submit.prevent="handleCreatePool">
          <div class="form-group">
            <label for="pool-name">Nombre del Pool</label>
            <input id="pool-name" v-model="newPool.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="pool-ranges">Rangos IP</label>
            <input id="pool-ranges" v-model="newPool.ranges" type="text" class="form-input font-mono" placeholder="192.168.88.10-192.168.88.254" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isPoolModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Pool</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR RED DHCP -->
    <div v-if="isNetworkModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Red DHCP</h2>
        <form @submit.prevent="handleCreateNetwork">
          <div class="form-group">
            <label for="net-addr">Subred / CIDR</label>
            <input id="net-addr" v-model="newNetwork.address" type="text" class="form-input font-mono" placeholder="192.168.88.0/24" required />
          </div>
          <div class="form-group">
            <label for="net-gw">Gateway</label>
            <input id="net-gw" v-model="newNetwork.gateway" type="text" class="form-input font-mono" placeholder="192.168.88.1" />
          </div>
          <div class="form-group">
            <label for="net-dns">Servidores DNS</label>
            <input id="net-dns" v-model="newNetwork.dns_server" type="text" class="form-input font-mono" placeholder="8.8.8.8,1.1.1.1" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isNetworkModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Red</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR CLIENTE DHCP WAN -->
    <div v-if="isClientModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Añadir Cliente DHCP WAN</h2>
        <form @submit.prevent="handleCreateClient">
          <div class="form-group">
            <label for="cli-iface">Interfaz WAN</label>
            <input id="cli-iface" v-model="newClient.interface" type="text" class="form-input" placeholder="ether1" required />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newClient.add_default_route" type="checkbox" />
              Añadir Ruta por Defecto (0.0.0.0/0)
            </label>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newClient.use_peer_dns" type="checkbox" />
              Usar DNS del Proveedor
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isClientModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Cliente</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .webfig-ip-view {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 1.5rem;
    background-color: var(--color-bg-primary, #0f172a);
    color: var(--color-text-primary, #f8fafc);
    min-height: calc(100vh - 4rem);
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .view-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--color-cyan-400, #38bdf8);
    margin: 0;
  }

  .view-subtitle {
    font-size: 0.85rem;
    color: var(--color-text-secondary, #94a3b8);
    margin-top: 0.25rem;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .nav-tabs {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid var(--color-border, #334155);
    padding-bottom: 0.25rem;
    overflow-x: auto;
  }

  .tab-btn {
    background: none;
    border: none;
    color: var(--color-text-secondary, #94a3b8);
    font-weight: 600;
    padding: 0.6rem 1rem;
    cursor: pointer;
    border-radius: 6px 6px 0 0;
    transition: all 0.2s ease;
  }

  .tab-btn:hover {
    color: var(--color-text-primary, #f8fafc);
    background-color: rgba(255, 255, 255, 0.05);
  }

  .tab-btn--active {
    color: var(--color-cyan-400, #38bdf8);
    border-bottom: 2px solid var(--color-cyan-400, #38bdf8);
    background-color: rgba(56, 189, 248, 0.1);
  }

  .subtabs-bar {
    display: flex;
    gap: 0.5rem;
    margin-top: -0.5rem;
  }

  .subtab-btn {
    background: #1e293b;
    border: 1px solid #334155;
    color: #94a3b8;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .subtab-btn--active {
    background: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
  }

  .table-container {
    background: var(--color-bg-secondary, #1e293b);
    border: 1px solid var(--color-border, #334155);
    border-radius: 8px;
    overflow-x: auto;
  }

  .tactical-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .tactical-table th {
    background-color: rgba(15, 23, 42, 0.8);
    color: #94a3b8;
    padding: 0.75rem 1rem;
    font-weight: 600;
    border-bottom: 1px solid #334155;
  }

  .tactical-table td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid #1e293b;
  }

  .tactical-table tr:hover {
    background-color: rgba(255, 255, 255, 0.02);
  }

  .empty-cell {
    text-align: center;
    padding: 2rem;
    color: #64748b;
  }

  .actions-col {
    text-align: right;
    white-space: nowrap;
  }

  .btn-tactical {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    border: none;
    transition: opacity 0.2s;
  }

  .btn-tactical:hover {
    opacity: 0.9;
  }

  .btn-cyan {
    background-color: #0284c7;
    color: #ffffff;
  }

  .btn-warning {
    background-color: #d97706;
    color: #ffffff;
  }

  .btn-outline {
    background: transparent;
    border: 1px solid #475569;
    color: #f8fafc;
  }

  .btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.3rem 0.5rem;
    font-size: 1rem;
    border-radius: 4px;
    transition: background 0.2s;
  }

  .btn-icon:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .badge-interface {
    background: #334155;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.8rem;
  }

  .badge-status {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .badge-static {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
  }

  .badge-dynamic {
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
  }

  .status-up {
    color: #34d399;
  }

  .status-down {
    color: #f87171;
  }

  .dns-dashboard {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .dns-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1.25rem;
  }

  .card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #38bdf8;
    margin-bottom: 0.75rem;
  }

  .dns-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .dns-label {
    color: #94a3b8;
    width: 220px;
  }

  .alert-box {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .alert-success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #059669;
    color: #6ee7b7;
  }

  .alert-danger {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #dc2626;
    color: #fca5a5;
  }

  /* Modales */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-window {
    background: #1e293b;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    padding: 1.5rem;
    width: 90%;
    max-width: 520px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-title {
    margin-top: 0;
    font-size: 1.2rem;
    color: #38bdf8;
  }

  .modal-desc {
    font-size: 0.8rem;
    margin-bottom: 1rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 1rem;
  }

  .form-group label {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .form-input {
    background: #0f172a;
    border: 1px solid #334155;
    color: #f8fafc;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .form-input:focus {
    border-color: #38bdf8;
    outline: none;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }

  .font-mono {
    font-family: monospace;
  }

  .font-bold {
    font-weight: 700;
  }

  .text-cyan {
    color: #38bdf8;
  }

  .text-muted {
    color: #94a3b8;
  }
</style>
