<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import RgSafeModeBanner from '@/components/common/RgSafeModeBanner.vue';

  const route = useRoute();
  const router = useRouter();
  const webFigStore = useWebFigStore();

  const routerId = computed(() => String(route.params.routerId || ''));

  type Ipv6Tab = 'addresses' | 'dhcp-client' | 'dhcp-server' | 'pools' | 'ndp';
  const activeTab = ref<Ipv6Tab>('addresses');

  const isLoading = ref(false);
  const errorMessage = ref('');
  const actionMessage = ref('');

  // Colecciones de datos
  const ipv6Addresses = ref<any[]>([]);
  const dhcpv6Clients = ref<any[]>([]);
  const dhcpv6Servers = ref<any[]>([]);
  const ipv6Pools = ref<any[]>([]);
  const ipv6Neighbors = ref<any[]>([]);
  const ndSettings = ref<any[]>([]);

  // Modales
  const isAddressModalOpen = ref(false);
  const newAddress = ref({ address: '', interface: 'ether2', advertise: true, eui_64: false, comment: '', disabled: false });

  const isClientModalOpen = ref(false);
  const newClient = ref({ interface: 'ether1', request: 'prefix', pool_name: 'pool-v6-delegated', pool_prefix_length: 64, add_default_route: true, comment: '' });

  const isServerModalOpen = ref(false);
  const newServer = ref({ name: 'dhcp6-lan', interface: 'bridge1', address_pool: 'pool-v6-delegated', lease_time: '24h', disabled: false });

  const isPoolModalOpen = ref(false);
  const newPool = ref({ name: 'pool-v6-static', prefix: '2001:db8:cafe::/48', prefix_length: 64 });

  async function loadData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      if (activeTab.value === 'addresses') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/addresses`);
        ipv6Addresses.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'dhcp-client') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-clients`);
        dhcpv6Clients.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'dhcp-server') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-servers`);
        dhcpv6Servers.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'pools') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/pools`);
        ipv6Pools.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'ndp') {
        const resNeigh = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/neighbors`);
        ipv6Neighbors.value = Array.isArray(resNeigh.data) ? resNeigh.data : resNeigh.data?.items || [];
        const resNd = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ipv6/nd`);
        ndSettings.value = Array.isArray(resNd.data) ? resNd.data : resNd.data?.items || [];
      }
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al cargar datos IPv6.';
    } finally {
      isLoading.value = false;
    }
  }

  function setTab(tab: Ipv6Tab) {
    activeTab.value = tab;
    loadData();
  }

  function goToFirewall() {
    router.push(`/routers/${routerId.value}/webfig/firewall`);
  }

  // --- Operaciones Direcciones IPv6 ---
  async function handleCreateAddress() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ipv6/addresses`, newAddress.value);
      actionMessage.value = `Dirección IPv6 ${newAddress.value.address} asignada a ${newAddress.value.interface}.`;
      isAddressModalOpen.value = false;
      newAddress.value = { address: '', interface: 'ether2', advertise: true, eui_64: false, comment: '', disabled: false };
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al asignar IPv6.';
    }
  }

  async function handleDeleteAddress(item: any) {
    if (!confirm(`¿Eliminar la dirección IPv6 ${item.address}?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ipv6/addresses/${item.id || item['.id']}`);
      actionMessage.value = `Dirección IPv6 ${item.address} eliminada.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar IPv6.';
    }
  }

  // --- Operaciones DHCPv6 Client & PD ---
  async function handleCreateDhcpClient() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-clients`, newClient.value);
      actionMessage.value = `Cliente DHCPv6 solicitando prefijo en ${newClient.value.interface}.`;
      isClientModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear cliente DHCPv6.';
    }
  }

  async function handleDeleteDhcpClient(item: any) {
    if (!confirm(`¿Eliminar cliente DHCPv6 en ${item.interface}?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-clients/${item.id || item['.id']}`);
      actionMessage.value = `Cliente DHCPv6 eliminado.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar cliente DHCPv6.';
    }
  }

  // --- Operaciones DHCPv6 Server ---
  async function handleCreateDhcpServer() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-servers`, newServer.value);
      actionMessage.value = `Servidor DHCPv6 "${newServer.value.name}" activado en ${newServer.value.interface}.`;
      isServerModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear servidor DHCPv6.';
    }
  }

  async function handleDeleteDhcpServer(item: any) {
    if (!confirm(`¿Eliminar servidor DHCPv6 "${item.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ipv6/dhcp-servers/${item.id || item['.id']}`);
      actionMessage.value = `Servidor DHCPv6 eliminado.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar servidor DHCPv6.';
    }
  }

  // --- Operaciones Pools IPv6 ---
  async function handleCreatePool() {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ipv6/pools`, newPool.value);
      actionMessage.value = `Pool IPv6 "${newPool.value.name}" creado.`;
      isPoolModalOpen.value = false;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al crear pool IPv6.';
    }
  }

  async function handleDeletePool(item: any) {
    if (!confirm(`¿Eliminar pool IPv6 "${item.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ipv6/pools/${item.id || item['.id']}`);
      actionMessage.value = `Pool IPv6 eliminado.`;
      loadData();
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al eliminar pool IPv6.';
    }
  }

  onMounted(() => {
    loadData();
  });
</script>

<template>
  <div class="webfig-ipv6-view">
    <RgSafeModeBanner />

    <header class="view-header">
      <div class="header-titles">
        <h1 class="view-title">🌐 Pila Dual IPv6 & Delegación de Prefijos (PD)</h1>
        <p class="view-subtitle">
          Direccionamiento nativo IPv6, cliente DHCPv6-PD, delegación LAN, pools y tabla de vecinos NDP en RouterOS v7.
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'addresses'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isAddressModalOpen = true"
        >
          + Asignar Dirección IPv6
        </button>

        <button
          v-else-if="activeTab === 'dhcp-client'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isClientModalOpen = true"
        >
          + Solicitar Prefijo WAN (PD)
        </button>

        <button
          v-else-if="activeTab === 'dhcp-server'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isServerModalOpen = true"
        >
          + Crear Servidor DHCPv6
        </button>

        <button
          v-else-if="activeTab === 'pools'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isPoolModalOpen = true"
        >
          + Crear Pool IPv6
        </button>

        <button
          type="button"
          class="btn-tactical btn-outline"
          @click="goToFirewall"
        >
          🛡️ Firewall IPv6
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
    <nav class="nav-tabs" aria-label="Secciones de IPv6">
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'addresses' }"
        @click="setTab('addresses')"
      >
        Direcciones IPv6
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'dhcp-client' }"
        @click="setTab('dhcp-client')"
      >
        DHCPv6 Client & PD (WAN)
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'dhcp-server' }"
        @click="setTab('dhcp-server')"
      >
        DHCPv6 Server (LAN)
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'pools' }"
        @click="setTab('pools')"
      >
        Pools de Prefijos IPv6
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'ndp' }"
        @click="setTab('ndp')"
      >
        Vecinos NDP & Anuncios RA
      </button>
    </nav>

    <!-- TAB 1: DIRECCIONES IPv6 -->
    <section v-if="activeTab === 'addresses'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Prefijo / Dirección IPv6</th>
              <th>Interfaz</th>
              <th>Advertise (SLAAC)</th>
              <th>EUI-64</th>
              <th>Comentario</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipv6Addresses.length === 0">
              <td colspan="7" class="empty-cell">No hay direcciones IPv6 configuradas.</td>
            </tr>
            <tr v-for="addr in ipv6Addresses" :key="addr.id || addr['.id']">
              <td class="font-mono font-bold text-cyan">{{ addr.address }}</td>
              <td><span class="badge-interface">{{ addr.interface }}</span></td>
              <td>
                <span class="badge-status" :class="addr.advertise === 'true' || addr.advertise === true ? 'badge-static' : 'badge-dynamic'">
                  {{ addr.advertise === 'true' || addr.advertise === true ? 'Sí' : 'No' }}
                </span>
              </td>
              <td>{{ addr['eui-64'] === 'true' || addr['eui-64'] === true ? 'Sí' : 'No' }}</td>
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
                  title="Eliminar Dirección IPv6"
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

    <!-- TAB 2: DHCPv6 CLIENT & PREFIX DELEGATION -->
    <section v-else-if="activeTab === 'dhcp-client'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Interfaz WAN</th>
              <th>Solicitud</th>
              <th>Pool de Destino</th>
              <th>Longitud Delegada</th>
              <th>Prefijo Delegado Recibido</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpv6Clients.length === 0">
              <td colspan="7" class="empty-cell">No hay clientes DHCPv6 configurados.</td>
            </tr>
            <tr v-for="cli in dhcpv6Clients" :key="cli.id || cli['.id']">
              <td class="font-bold"><span class="badge-interface">{{ cli.interface }}</span></td>
              <td>{{ cli.request || 'prefix' }}</td>
              <td class="font-mono text-cyan">{{ cli['pool-name'] || cli.pool_name || '—' }}</td>
              <td class="font-mono">/{{ cli['pool-prefix-length'] || cli.pool_prefix_length || 64 }}</td>
              <td class="font-mono font-bold text-cyan">{{ cli.prefix || 'Buscando...' }}</td>
              <td>
                <span class="badge-status" :class="cli.status === 'bound' ? 'badge-static' : 'badge-dynamic'">
                  {{ cli.status || 'searching' }}
                </span>
              </td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Cliente DHCPv6"
                  @click="handleDeleteDhcpClient(cli)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: DHCPv6 SERVER -->
    <section v-else-if="activeTab === 'dhcp-server'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Nombre del Servidor</th>
              <th>Interfaz</th>
              <th>Pool de Prefijos Delegable</th>
              <th>Tiempo de Concesión</th>
              <th>Estado</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="dhcpv6Servers.length === 0">
              <td colspan="6" class="empty-cell">No hay servidores DHCPv6 activos.</td>
            </tr>
            <tr v-for="srv in dhcpv6Servers" :key="srv.id || srv['.id']">
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
                  title="Eliminar Servidor DHCPv6"
                  @click="handleDeleteDhcpServer(srv)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 4: POOLS IPv6 -->
    <section v-else-if="activeTab === 'pools'" class="tab-panel">
      <div class="table-container">
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Nombre del Pool</th>
              <th>Prefijo Base IPv6</th>
              <th>Longitud de Prefijo de Clientes</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipv6Pools.length === 0">
              <td colspan="4" class="empty-cell">No hay pools de prefijos IPv6 configurados.</td>
            </tr>
            <tr v-for="pool in ipv6Pools" :key="pool.id || pool['.id']">
              <td class="font-bold text-cyan">{{ pool.name }}</td>
              <td class="font-mono">{{ pool.prefix }}</td>
              <td class="font-mono">/{{ pool['prefix-length'] || pool.prefix_length || 64 }}</td>
              <td class="actions-col">
                <button
                  type="button"
                  class="btn-icon btn-danger"
                  title="Eliminar Pool IPv6"
                  @click="handleDeletePool(pool)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 5: VECINOS NDP -->
    <section v-else-if="activeTab === 'ndp'" class="tab-panel">
      <div class="table-container">
        <h2 class="section-title">Tabla de Descubrimiento de Vecinos (NDP)</h2>
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Dirección IPv6</th>
              <th>Dirección MAC Física</th>
              <th>Interfaz</th>
              <th>Estado / Tipo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipv6Neighbors.length === 0">
              <td colspan="4" class="empty-cell">No hay vecinos IPv6 descubiertos en los enlaces.</td>
            </tr>
            <tr v-for="neigh in ipv6Neighbors" :key="neigh.id || neigh['.id']">
              <td class="font-mono font-bold text-cyan">{{ neigh.address }}</td>
              <td class="font-mono">{{ neigh['mac-address'] || neigh.mac_address || '—' }}</td>
              <td><span class="badge-interface">{{ neigh.interface }}</span></td>
              <td>
                <span class="badge-status badge-static">{{ neigh.status || 'reachable' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- MODAL: ASIGNAR DIRECCIÓN IPv6 -->
    <div v-if="isAddressModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Asignar Dirección IPv6 a Interfaz</h2>
        <form @submit.prevent="handleCreateAddress">
          <div class="form-group">
            <label for="v6-addr">Dirección IPv6 con Prefijo</label>
            <input
              id="v6-addr"
              v-model="newAddress.address"
              type="text"
              class="form-input font-mono"
              placeholder="2001:db8:acad::1/64"
              required
            />
          </div>
          <div class="form-group">
            <label for="v6-iface">Interfaz</label>
            <input id="v6-iface" v-model="newAddress.interface" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newAddress.advertise" type="checkbox" />
              Publicar Prefijo a Clientes (SLAAC / Router Advertisement)
            </label>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newAddress.eui_64" type="checkbox" />
              Autogenerar Identificador de Interfaz EUI-64
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isAddressModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar bajo Safe Mode</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CLIENTE DHCPv6 (PD) -->
    <div v-if="isClientModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Configurar Cliente DHCPv6 WAN (Prefix Delegation)</h2>
        <form @submit.prevent="handleCreateDhcpClient">
          <div class="form-group">
            <label for="v6-cli-iface">Interfaz WAN Hacia el Proveedor</label>
            <input id="v6-cli-iface" v-model="newClient.interface" type="text" class="form-input" placeholder="ether1" required />
          </div>
          <div class="form-group">
            <label for="v6-cli-pool">Nombre del Pool de Inyección Local</label>
            <input id="v6-cli-pool" v-model="newClient.pool_name" type="text" class="form-input" placeholder="pool-v6-delegated" required />
          </div>
          <div class="form-group">
            <label for="v6-cli-len">Longitud del Sub-Prefijo Delegable</label>
            <input id="v6-cli-len" v-model="newClient.pool_prefix_length" type="number" class="form-input" min="48" max="64" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isClientModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Solicitar Prefijo</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: SERVIDOR DHCPv6 -->
    <div v-if="isServerModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Servidor DHCPv6</h2>
        <form @submit.prevent="handleCreateDhcpServer">
          <div class="form-group">
            <label for="v6-srv-name">Nombre del Servidor</label>
            <input id="v6-srv-name" v-model="newServer.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="v6-srv-iface">Interfaz de Distribución (LAN)</label>
            <input id="v6-srv-iface" v-model="newServer.interface" type="text" class="form-input" placeholder="bridge1" required />
          </div>
          <div class="form-group">
            <label for="v6-srv-pool">Pool de Prefijos IPv6</label>
            <input id="v6-srv-pool" v-model="newServer.address_pool" type="text" class="form-input" placeholder="pool-v6-delegated" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isServerModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Servidor</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: POOL IPv6 -->
    <div v-if="isPoolModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Pool de Prefijos IPv6</h2>
        <form @submit.prevent="handleCreatePool">
          <div class="form-group">
            <label for="v6-p-name">Nombre del Pool</label>
            <input id="v6-p-name" v-model="newPool.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="v6-p-prefix">Prefijo Base IPv6</label>
            <input id="v6-p-prefix" v-model="newPool.prefix" type="text" class="form-input font-mono" placeholder="2001:db8:cafe::/48" required />
          </div>
          <div class="form-group">
            <label for="v6-p-len">Longitud de Delegación a Clientes</label>
            <input id="v6-p-len" v-model="newPool.prefix_length" type="number" class="form-input" min="48" max="64" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isPoolModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Pool</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .webfig-ipv6-view {
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

  .table-container {
    background: var(--color-bg-secondary, #1e293b);
    border: 1px solid var(--color-border, #334155);
    border-radius: 8px;
    overflow-x: auto;
    padding: 1rem;
  }

  .section-title {
    font-size: 1rem;
    color: #38bdf8;
    margin-top: 0;
    margin-bottom: 1rem;
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

  .btn-cyan {
    background-color: #0284c7;
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
