<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  interface WireGuardIfaceRow extends Record<string, unknown> {
    id: string;
    name: string;
    listen_port: number;
    mtu?: number;
    public_key?: string;
    running?: boolean;
    disabled?: boolean;
    comment?: string;
  }

  interface WireGuardPeerRow extends Record<string, unknown> {
    id: string;
    interface: string;
    public_key: string;
    endpoint_address?: string;
    endpoint_port?: number;
    allowed_address?: string;
    current_endpoint_address?: string;
    last_handshake?: string;
    rx?: number;
    tx?: number;
    disabled?: boolean;
    comment?: string;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<'interfaces' | 'peers'>('interfaces');
  const isLoading = ref(false);
  const statusMessage = ref('');
  const errorMessage = ref('');

  const ifacesList = ref<WireGuardIfaceRow[]>([]);
  const peersList = ref<WireGuardPeerRow[]>([]);

  // Modals
  const isCreateIfaceModalOpen = ref(false);
  const isCreatePeerModalOpen = ref(false);

  const newIface = ref({
    name: 'wg0',
    listen_port: 13231,
    mtu: 1420,
    comment: '',
  });

  const newPeer = ref({
    interface: 'wg0',
    public_key: '',
    endpoint_address: '',
    endpoint_port: 13231,
    allowed_address: '10.250.0.2/32',
    persistent_keepalive: 25,
    comment: '',
  });

  const ifaceColumns: TableColumn<WireGuardIfaceRow>[] = [
    { key: 'name', label: 'Interfaz Túnel', sortable: true },
    { key: 'listen_port', label: 'Puerto de Escucha (UDP)', align: 'center' },
    { key: 'mtu', label: 'MTU', align: 'center' },
    { key: 'public_key', label: 'Clave Pública (Public Key)' },
    {
      key: 'running',
      label: 'Estado',
      align: 'center',
      formatter: (row) => (row.running ? '🟢 En Servicio' : '⚪ Detenida'),
    },
    { key: 'comment', label: 'Comentario' },
  ];

  const peerColumns: TableColumn<WireGuardPeerRow>[] = [
    { key: 'interface', label: 'Interfaz', sortable: true },
    { key: 'public_key', label: 'Clave Pública del Peer' },
    { key: 'allowed_address', label: 'Allowed IPs (Rutas VPN)', sortable: true },
    { key: 'endpoint_address', label: 'Endpoint Remoto' },
    { key: 'endpoint_port', label: 'Puerto', align: 'center' },
    { key: 'last_handshake', label: 'Último Handshake', align: 'right' },
    { key: 'comment', label: 'Comentario' },
  ];

  async function loadData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      if (activeTab.value === 'interfaces') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        ifacesList.value = items.map((i: any) => ({
          ...i,
          id: i.id || i['.id'] || i.name,
          listen_port: i.listen_port ? Number(i.listen_port) : Number(i['listen-port'] || 13231),
          public_key: i.public_key || i['public-key'] || '',
          running: i.running !== 'false' && i.running !== false,
          disabled: i.disabled === 'true' || i.disabled === true,
        }));
      } else {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard/peers`);
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        peersList.value = items.map((p: any) => ({
          ...p,
          id: p.id || p['.id'] || `${p.interface}-${p.public_key || p['public-key']}`,
          public_key: p.public_key || p['public-key'] || '',
          allowed_address: p.allowed_address || p['allowed-address'] || '',
          endpoint_address: p.endpoint_address || p['endpoint-address'] || '',
          endpoint_port: p.endpoint_port ? Number(p.endpoint_port) : Number(p['endpoint-port'] || 0),
          last_handshake: p.last_handshake || p['last-handshake'] || 'Nunca',
          disabled: p.disabled === 'true' || p.disabled === true,
        }));
      }
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar recursos WireGuard.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateIface() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard`, newIface.value);
      statusMessage.value = `Interfaz WireGuard "${newIface.value.name}" creada exitosamente bajo Safe Mode.`;
      isCreateIfaceModalOpen.value = false;
      newIface.value = { name: `wg${ifacesList.value.length + 1}`, listen_port: 13231 + ifacesList.value.length, mtu: 1420, comment: '' };
      loadData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear la interfaz WireGuard.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreatePeer() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard/peers`, newPeer.value);
      statusMessage.value = `Peer WireGuard registrado exitosamente bajo Safe Mode.`;
      isCreatePeerModalOpen.value = false;
      newPeer.value = { interface: ifacesList.value[0]?.name || 'wg0', public_key: '', endpoint_address: '', endpoint_port: 13231, allowed_address: '10.250.0.3/32', persistent_keepalive: 25, comment: '' };
      loadData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al agregar el Peer WireGuard.';
    } finally {
      isLoading.value = false;
    }
  }

  function setTab(tab: 'interfaces' | 'peers') {
    activeTab.value = tab;
    loadData();
  }

  onMounted(() => {
    loadData();
  });
</script>

<template>
  <div class="wireguard-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">VPN Moderna WireGuard (RouterOS v7)</h1>
        <p class="view-subtitle">
          Administración de interfaces de túnel WireGuard de alto rendimiento y gestión de Peers criptográficos.
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'interfaces'"
          type="button"
          class="btn-primary"
          @click="isCreateIfaceModalOpen = true"
        >
          + Crear Interfaz WireGuard
        </button>
        <button
          v-if="activeTab === 'peers'"
          type="button"
          class="btn-primary"
          @click="isCreatePeerModalOpen = true"
        >
          + Agregar Peer WireGuard
        </button>
        <button
          type="button"
          class="btn-refresh"
          :disabled="isLoading"
          aria-label="Refrescar datos WireGuard"
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

    <!-- Pestañas -->
    <nav class="tabs-nav" aria-label="Pestañas de WireGuard">
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'interfaces' }"
        @click="setTab('interfaces')"
      >
        🛡️ Interfaces de Túnel ({{ ifacesList.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'peers' }"
        @click="setTab('peers')"
      >
        👥 Peers & Claves Públicas ({{ peersList.length }})
      </button>
    </nav>

    <!-- Contenido -->
    <div class="tab-content">
      <div v-if="activeTab === 'interfaces'">
        <RgDataTable
          :columns="(ifaceColumns as any)"
          :rows="ifacesList"
          caption="Túneles WireGuard Configurados"
          row-key="id"
        />
      </div>

      <div v-else-if="activeTab === 'peers'">
        <RgDataTable
          :columns="(peerColumns as any)"
          :rows="peersList"
          caption="Peers Criptográficos WireGuard"
          row-key="id"
        />
      </div>
    </div>

    <!-- Modal Crear Interfaz WireGuard -->
    <div v-if="isCreateIfaceModalOpen" class="modal-backdrop" @click.self="isCreateIfaceModalOpen = false">
      <div class="modal-card" role="dialog" aria-labelledby="modal-wg-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-wg-title">Crear Interfaz WireGuard</h2>
          <button type="button" class="btn-close" @click="isCreateIfaceModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateIface">
          <div class="form-group">
            <label for="wg-name">Nombre de Interfaz:</label>
            <input id="wg-name" v-model="newIface.name" required placeholder="ej. wg0 o wg-hq" />
          </div>
          <div class="form-group">
            <label for="wg-port">Puerto de Escucha UDP (Listen Port):</label>
            <input id="wg-port" v-model.number="newIface.listen_port" type="number" min="1024" max="65535" required />
          </div>
          <div class="form-group">
            <label for="wg-mtu">MTU:</label>
            <input id="wg-mtu" v-model.number="newIface.mtu" type="number" min="1280" max="1500" required />
          </div>
          <div class="form-group">
            <label for="wg-comment">Comentario:</label>
            <input id="wg-comment" v-model="newIface.comment" placeholder="ej. Túnel VPN Sucursales" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateIfaceModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Crear con Safe Mode</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Agregar Peer WireGuard -->
    <div v-if="isCreatePeerModalOpen" class="modal-backdrop" @click.self="isCreatePeerModalOpen = false">
      <div class="modal-card" role="dialog" aria-labelledby="modal-peer-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-peer-title">Agregar Peer Criptográfico WireGuard</h2>
          <button type="button" class="btn-close" @click="isCreatePeerModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreatePeer">
          <div class="form-group">
            <label for="peer-iface">Interfaz WireGuard Local:</label>
            <input id="peer-iface" v-model="newPeer.interface" required placeholder="ej. wg0" />
          </div>
          <div class="form-group">
            <label for="peer-pubkey">Clave Pública (Base64):</label>
            <input id="peer-pubkey" v-model="newPeer.public_key" required placeholder="44 caracteres Base64..." />
          </div>
          <div class="form-group">
            <label for="peer-allowed">Allowed IPs (Redes Enrutadas):</label>
            <input id="peer-allowed" v-model="newPeer.allowed_address" required placeholder="ej. 10.250.0.2/32 o 0.0.0.0/0" />
          </div>
          <div class="form-group">
            <label for="peer-endpoint">Endpoint Remoto (IP o FQDN):</label>
            <input id="peer-endpoint" v-model="newPeer.endpoint_address" placeholder="ej. vpn.empresa.com o IP pública" />
          </div>
          <div class="form-group">
            <label for="peer-eport">Puerto Endpoint:</label>
            <input id="peer-eport" v-model.number="newPeer.endpoint_port" type="number" min="1" max="65535" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreatePeerModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Registrar Peer con Safe Mode</button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .wireguard-view {
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
  .form-group input {
    background: var(--rg-bg-input, #0f172a);
    color: var(--rg-text-primary, #f8fafc);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 8px 12px;
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
