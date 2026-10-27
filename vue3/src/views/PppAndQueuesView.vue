<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, PppActiveSessionItem, SimpleQueueItem } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import RgSimpleQueueModal from '@/components/webfig/RgSimpleQueueModal.vue';

  interface PppSecretItem extends Record<string, unknown> {
    id: string;
    name: string;
    service?: string;
    profile?: string;
    local_address?: string;
    remote_address?: string;
    disabled?: boolean;
    comment?: string;
  }

  interface PppProfileItem extends Record<string, unknown> {
    id: string;
    name: string;
    local_address?: string;
    remote_address?: string;
    rate_limit?: string;
    dns_server?: string;
    only_one?: string;
  }

  interface PppoeServerItem extends Record<string, unknown> {
    id: string;
    service_name: string;
    interface: string;
    default_profile?: string;
    max_mtu?: number;
    max_sessions?: number;
    disabled?: boolean;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<
    'pppoe-active' | 'ppp-secrets' | 'ppp-profiles' | 'pppoe-servers' | 'simple-queues'
  >('pppoe-active');
  const isLoading = ref(false);
  const pppSearchQuery = ref('');
  const actionMessage = ref('');
  const errorMessage = ref('');

  const pppSessions = ref<PppActiveSessionItem[]>([]);
  const pppSecrets = ref<PppSecretItem[]>([]);
  const pppProfiles = ref<PppProfileItem[]>([]);
  const pppoeServers = ref<PppoeServerItem[]>([]);
  const simpleQueues = ref<SimpleQueueItem[]>([]);

  // Modals
  const isCreateSecretModalOpen = ref(false);
  const isCreateProfileModalOpen = ref(false);
  const isCreateServerModalOpen = ref(false);
  const isCreateQueueModalOpen = ref(false);
  const isEditingQueue = ref(false);
  const selectedQueue = ref<SimpleQueueItem | null>(null);

  const newSecret = ref({
    name: '',
    password: '',
    service: 'any',
    profile: 'default',
    local_address: '',
    remote_address: '',
    comment: '',
  });

  const newProfile = ref({
    name: '',
    local_address: '',
    remote_address: '',
    rate_limit: '10M/10M',
    dns_server: '8.8.8.8,1.1.1.1',
    only_one: 'yes',
  });

  const newServer = ref({
    service_name: 'pppoe-service',
    interface: 'bridge1',
    default_profile: 'default',
    max_mtu: 1492,
    max_mru: 1492,
    one_session_per_host: true,
  });

  const pppColumns: TableColumn<PppActiveSessionItem>[] = [
    { key: 'name', label: 'Usuario PPPoE', sortable: true },
    { key: 'address', label: 'Dirección IP' },
    { key: 'caller_id', label: 'MAC / Caller-ID' },
    { key: 'uptime', label: 'Uptime', align: 'right' },
    { key: 'service', label: 'Servicio', align: 'center' },
  ];

  const secretColumns: TableColumn<PppSecretItem>[] = [
    { key: 'name', label: 'Usuario (Name)', sortable: true },
    { key: 'service', label: 'Servicio', align: 'center' },
    { key: 'profile', label: 'Perfil Asignado', sortable: true },
    { key: 'local_address', label: 'IP Local (Gateway)' },
    { key: 'remote_address', label: 'IP Remota (Cliente)' },
    {
      key: 'disabled',
      label: 'Estado',
      align: 'center',
      formatter: (row) => (row.disabled ? '🔴 Deshabilitado' : '🟢 Activo'),
    },
    { key: 'comment', label: 'Comentario' },
  ];

  const profileColumns: TableColumn<PppProfileItem>[] = [
    { key: 'name', label: 'Nombre Perfil', sortable: true },
    { key: 'local_address', label: 'Pool / IP Local' },
    { key: 'remote_address', label: 'Pool / IP Remota' },
    { key: 'rate_limit', label: 'Rate Limit (Límite Ancho de Banda)', align: 'center' },
    { key: 'dns_server', label: 'Servidores DNS' },
    { key: 'only_one', label: 'Sesión Única', align: 'center' },
  ];

  const serverColumns: TableColumn<PppoeServerItem>[] = [
    { key: 'service_name', label: 'Nombre Servicio', sortable: true },
    { key: 'interface', label: 'Interfaz Escucha', sortable: true },
    { key: 'default_profile', label: 'Perfil Predeterminado' },
    { key: 'max_mtu', label: 'Max MTU', align: 'center' },
    {
      key: 'disabled',
      label: 'Estado',
      align: 'center',
      formatter: (row) => (row.disabled ? '🔴 Inactivo' : '🟢 Activo'),
    },
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
    errorMessage.value = '';
    try {
      if (activeTab.value === 'pppoe-active') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ppp/active`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppSessions.value = items.map((s: any) => ({
          ...s,
          id: s.id || s['.id'] || s.name,
          caller_id: s.caller_id || s['caller-id'] || '',
        }));
      } else if (activeTab.value === 'ppp-secrets') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ppp/secrets`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppSecrets.value = items.map((sec: any) => ({
          ...sec,
          id: sec.id || sec['.id'] || sec.name,
          local_address: sec.local_address || sec['local-address'] || '',
          remote_address: sec.remote_address || sec['remote-address'] || '',
          disabled: sec.disabled === 'true' || sec.disabled === true,
        }));
      } else if (activeTab.value === 'ppp-profiles') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ppp/profiles`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppProfiles.value = items.map((prof: any) => ({
          ...prof,
          id: prof.id || prof['.id'] || prof.name,
          local_address: prof.local_address || prof['local-address'] || '',
          remote_address: prof.remote_address || prof['remote-address'] || '',
          rate_limit: prof.rate_limit || prof['rate-limit'] || '',
          dns_server: prof.dns_server || prof['dns-server'] || '',
          only_one: prof.only_one || prof['only-one'] || '',
        }));
      } else if (activeTab.value === 'pppoe-servers') {
        const res = await http.get<any>(
          `/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppoeServers.value = items.map((srv: any) => ({
          ...srv,
          id: srv.id || srv['.id'] || `${srv.interface}-${srv.service_name || srv['service-name']}`,
          service_name: srv.service_name || srv['service-name'] || '',
          default_profile: srv.default_profile || srv['default-profile'] || '',
          max_mtu: srv.max_mtu ? Number(srv.max_mtu) : Number(srv['max-mtu'] || 1492),
          disabled: srv.disabled === 'true' || srv.disabled === true,
        }));
      } else {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/queues/simple`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        simpleQueues.value = items.map((q: any) => ({
          ...q,
          id: q.id || q['.id'] || q.name,
          bytes_in: Number(q.bytes_in || 0),
          bytes_out: Number(q.bytes_out || 0),
        }));
      }
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar datos del módulo PPP.';
      if (activeTab.value === 'pppoe-active') pppSessions.value = [];
      else if (activeTab.value === 'ppp-secrets') pppSecrets.value = [];
      else if (activeTab.value === 'ppp-profiles') pppProfiles.value = [];
      else if (activeTab.value === 'pppoe-servers') pppoeServers.value = [];
      else simpleQueues.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function handleReconnectPpp(session: PppActiveSessionItem) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/active/${session.id}`);
      actionMessage.value = `Sesión de ${session.name} reiniciada con éxito.`;
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
      loadPppData();
    } catch (err: any) {
      actionMessage.value = err?.detail || err?.message || 'Error al reiniciar sesión';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    }
  }

  async function handleCreateSecret() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ppp/secrets`, newSecret.value);
      actionMessage.value = `Usuario PPP "${newSecret.value.name}" creado exitosamente bajo Safe Mode.`;
      isCreateSecretModalOpen.value = false;
      newSecret.value = {
        name: '',
        password: '',
        service: 'any',
        profile: 'default',
        local_address: '',
        remote_address: '',
        comment: '',
      };
      loadPppData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear el secreto PPP.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateProfile() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/ppp/profiles`, newProfile.value);
      actionMessage.value = `Perfil PPP "${newProfile.value.name}" creado exitosamente.`;
      isCreateProfileModalOpen.value = false;
      newProfile.value = {
        name: '',
        local_address: '',
        remote_address: '',
        rate_limit: '10M/10M',
        dns_server: '8.8.8.8,1.1.1.1',
        only_one: 'yes',
      };
      loadPppData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear el perfil PPP.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleCreateServer() {
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.post(
        `/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers`,
        newServer.value,
      );
      actionMessage.value = `Servidor PPPoE "${newServer.value.service_name}" activado en ${newServer.value.interface}.`;
      isCreateServerModalOpen.value = false;
      loadPppData();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear el servidor PPPoE.';
    } finally {
      isLoading.value = false;
    }
  }

  function openCreateQueueModal() {
    isEditingQueue.value = false;
    selectedQueue.value = null;
    isCreateQueueModalOpen.value = true;
  }

  function openEditQueueModal(queue: SimpleQueueItem) {
    isEditingQueue.value = true;
    selectedQueue.value = queue;
    isCreateQueueModalOpen.value = true;
  }

  async function handleSaveQueue(payload: Record<string, any>) {
    webFigStore.startSafeModeCountdown(60);
    errorMessage.value = '';
    try {
      if (isEditingQueue.value && selectedQueue.value?.id) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/queues/simple/${selectedQueue.value.id}`,
          payload,
        );
        actionMessage.value = 'Cola simple modificada exitosamente.';
      } else {
        await http.post(`/api/v1/routers/${routerId.value}/webfig/queues/simple`, payload);
        actionMessage.value = 'Nueva cola simple creada bajo Safe Mode.';
      }
      isCreateQueueModalOpen.value = false;
      loadPppData();
    } catch (err: any) {
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al persistir cola simple.';
    }
  }

  async function handleToggleQueue(queue: SimpleQueueItem) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/queues/simple/${queue.id}`,
        { disabled: !queue.disabled },
      );
      loadPppData();
    } catch (err: any) {
      errorMessage.value = err?.response?.data?.detail || 'Error al conmutar cola.';
    }
  }

  async function handleDeleteQueue(queue: SimpleQueueItem) {
    if (!confirm(`¿Eliminar la cola simple "${queue.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/queues/simple/${queue.id}`);
      actionMessage.value = `Cola "${queue.name}" eliminada.`;
      loadPppData();
    } catch (err: any) {
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar cola simple.';
    }
  }

  async function handleToggleSecret(secret: PppSecretItem) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ppp/secrets/${secret.id}`,
        { disabled: !secret.disabled },
      );
      loadPppData();
    } catch (err: any) {
      errorMessage.value = err?.response?.data?.detail || 'Error al conmutar usuario PPP.';
    }
  }

  async function handleDeleteSecret(secret: PppSecretItem) {
    if (!confirm(`¿Eliminar el usuario PPP "${secret.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/secrets/${secret.id}`);
      actionMessage.value = `Usuario "${secret.name}" eliminado.`;
      loadPppData();
    } catch (err: any) {
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar usuario PPP.';
    }
  }

  async function handleDeleteProfile(profile: PppProfileItem) {
    if (!confirm(`¿Eliminar el perfil PPP "${profile.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/profiles/${profile.id}`);
      actionMessage.value = `Perfil "${profile.name}" eliminado.`;
      loadPppData();
    } catch (err: any) {
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar perfil PPP.';
    }
  }

  function setTab(tab: typeof activeTab.value) {
    activeTab.value = tab;
    loadPppData();
  }

  onMounted(() => {
    loadPppData();
  });
</script>

<template>
  <div class="ppp-queues-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">PPPoE & Control de Ancho de Banda (Simple Queues)</h1>
        <p class="view-subtitle">
          Supervisión de sesiones de abonados, usuarios PPP Secrets, perfiles y servidores PPPoE
          MikroTik v7.
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'ppp-secrets'"
          type="button"
          class="btn-primary"
          @click="isCreateSecretModalOpen = true"
        >
          + Crear Secreto PPP
        </button>
        <button
          v-if="activeTab === 'ppp-profiles'"
          type="button"
          class="btn-primary"
          @click="isCreateProfileModalOpen = true"
        >
          + Crear Perfil PPP
        </button>
        <button
          v-if="activeTab === 'pppoe-servers'"
          type="button"
          class="btn-primary"
          @click="isCreateServerModalOpen = true"
        >
          + Activar Servidor PPPoE
        </button>
        <button
          v-if="activeTab === 'simple-queues'"
          type="button"
          class="btn-primary"
          @click="openCreateQueueModal"
        >
          + Crear Cola Simple
        </button>
        <button
          type="button"
          class="btn-refresh"
          :disabled="isLoading"
          aria-label="Refrescar datos PPP"
          @click="loadPppData"
        >
          🔄 Refrescar
        </button>
      </div>
    </header>

    <div v-if="actionMessage" class="banner banner--success font-tabular" role="status">
      {{ actionMessage }}
    </div>
    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>

    <!-- Navegación de Subpestañas -->
    <nav class="subtabs-bar" role="tablist" aria-label="Módulos PPP y Colas">
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'pppoe-active' }"
        role="tab"
        :aria-selected="activeTab === 'pppoe-active'"
        @click="setTab('pppoe-active')"
      >
        🟢 Sesiones Activas
      </button>
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'ppp-secrets' }"
        role="tab"
        :aria-selected="activeTab === 'ppp-secrets'"
        @click="setTab('ppp-secrets')"
      >
        🔑 Secretos / Usuarios
      </button>
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'ppp-profiles' }"
        role="tab"
        :aria-selected="activeTab === 'ppp-profiles'"
        @click="setTab('ppp-profiles')"
      >
        📋 Perfiles
      </button>
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'pppoe-servers' }"
        role="tab"
        :aria-selected="activeTab === 'pppoe-servers'"
        @click="setTab('pppoe-servers')"
      >
        📡 Servidores PPPoE
      </button>
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'simple-queues' }"
        role="tab"
        :aria-selected="activeTab === 'simple-queues'"
        @click="setTab('simple-queues')"
      >
        ⚡ Simple Queues
      </button>
    </nav>

    <!-- Contenidos -->
    <div class="content-block">
      <!-- Pestaña 1: Sesiones Activas -->
      <div v-if="activeTab === 'pppoe-active'">
        <RgDataTable
          :columns="pppColumns as any"
          :rows="filteredPppSessions"
          caption="Sesiones PPPoE Activas"
          row-key="id"
        >
          <template #actions="{ row }">
            <button
              type="button"
              class="btn-row-action btn-row-action--danger"
              :aria-label="`Desconectar sesión PPPoE de ${(row as any).name}`"
              title="Desconectar / Expulsar Abonado (Kick Session)"
              @click="handleReconnectPpp(row as any)"
            >
              ⏏ Desconectar
            </button>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 2: Secretos PPP -->
      <div v-else-if="activeTab === 'ppp-secrets'">
        <RgDataTable
          :columns="secretColumns as any"
          :rows="pppSecrets"
          caption="Secretos y Clientes PPP"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                :title="(row as any).disabled ? 'Habilitar usuario' : 'Deshabilitar usuario'"
                :aria-label="(row as any).disabled ? 'Habilitar usuario' : 'Deshabilitar usuario'"
                @click="handleToggleSecret(row as any)"
              >
                {{ (row as any).disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar usuario"
                :aria-label="`Eliminar usuario ${(row as any).name}`"
                @click="handleDeleteSecret(row as any)"
              >
                🗑
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 3: Perfiles PPP -->
      <div v-else-if="activeTab === 'ppp-profiles'">
        <RgDataTable
          :columns="profileColumns as any"
          :rows="pppProfiles"
          caption="Perfiles de Servicio PPP"
          row-key="id"
        >
          <template #actions="{ row }">
            <button
              type="button"
              class="btn-row-action btn-row-action--danger"
              title="Eliminar perfil"
              :aria-label="`Eliminar perfil ${(row as any).name}`"
              @click="handleDeleteProfile(row as any)"
            >
              🗑
            </button>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 4: Servidores PPPoE -->
      <div v-else-if="activeTab === 'pppoe-servers'">
        <RgDataTable
          :columns="serverColumns as any"
          :rows="pppoeServers"
          caption="Servidores de Autenticación PPPoE"
          row-key="id"
        />
      </div>

      <!-- Pestaña 5: Simple Queues -->
      <div v-else-if="activeTab === 'simple-queues'">
        <RgDataTable
          :columns="queueColumns as any"
          :rows="simpleQueues"
          caption="Colas de Ancho de Banda Simples"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                title="Editar cola simple"
                :aria-label="`Editar cola ${(row as any).name}`"
                @click="openEditQueueModal(row as any)"
              >
                ✏
              </button>
              <button
                type="button"
                class="btn-row-action"
                :title="(row as any).disabled ? 'Habilitar cola' : 'Deshabilitar cola'"
                :aria-label="(row as any).disabled ? 'Habilitar cola' : 'Deshabilitar cola'"
                @click="handleToggleQueue(row as any)"
              >
                {{ (row as any).disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar cola simple"
                :aria-label="`Eliminar cola ${(row as any).name}`"
                @click="handleDeleteQueue(row as any)"
              >
                🗑
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>
    </div>

    <!-- Modal Táctico de Creación/Edición de Cola Simple -->
    <RgSimpleQueueModal
      :is-open="isCreateQueueModalOpen"
      :is-editing="isEditingQueue"
      :initial-queue="selectedQueue"
      @close="isCreateQueueModalOpen = false"
      @save="handleSaveQueue"
    />

    <!-- Modal Crear Secreto PPP -->
    <div
      v-if="isCreateSecretModalOpen"
      class="modal-backdrop"
      @click.self="isCreateSecretModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-secret-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-secret-title">Crear Secreto / Usuario PPP</h2>
          <button type="button" class="btn-close" @click="isCreateSecretModalOpen = false">
            ✕
          </button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateSecret">
          <div class="form-group">
            <label for="sec-name">Nombre de Usuario:</label>
            <input id="sec-name" v-model="newSecret.name" required placeholder="ej. usuario01" />
          </div>
          <div class="form-group">
            <label for="sec-pwd">Contraseña:</label>
            <input
              id="sec-pwd"
              v-model="newSecret.password"
              type="password"
              required
              placeholder="Contraseña segura"
            />
          </div>
          <div class="form-group">
            <label for="sec-svc">Servicio:</label>
            <select id="sec-svc" v-model="newSecret.service">
              <option value="any">Cualquiera (any)</option>
              <option value="pppoe">PPPoE</option>
              <option value="pptp">PPTP</option>
              <option value="l2tp">L2TP</option>
              <option value="ovpn">OpenVPN</option>
            </select>
          </div>
          <div class="form-group">
            <label for="sec-prof">Perfil:</label>
            <input id="sec-prof" v-model="newSecret.profile" placeholder="ej. default" />
          </div>
          <div class="form-group">
            <label for="sec-local">IP Local (Gateway Opcional):</label>
            <input id="sec-local" v-model="newSecret.local_address" placeholder="ej. 10.10.10.1" />
          </div>
          <div class="form-group">
            <label for="sec-remote">IP Remota (Cliente Opcional):</label>
            <input
              id="sec-remote"
              v-model="newSecret.remote_address"
              placeholder="ej. 10.10.10.50"
            />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateSecretModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Crear con Safe Mode
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Crear Perfil PPP -->
    <div
      v-if="isCreateProfileModalOpen"
      class="modal-backdrop"
      @click.self="isCreateProfileModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-profile-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-profile-title">Crear Perfil PPP</h2>
          <button type="button" class="btn-close" @click="isCreateProfileModalOpen = false">
            ✕
          </button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateProfile">
          <div class="form-group">
            <label for="prof-name">Nombre del Perfil:</label>
            <input id="prof-name" v-model="newProfile.name" required placeholder="ej. plan-20m" />
          </div>
          <div class="form-group">
            <label for="prof-rate">Rate Limit (Subida/Bajada):</label>
            <input id="prof-rate" v-model="newProfile.rate_limit" placeholder="ej. 10M/20M" />
          </div>
          <div class="form-group">
            <label for="prof-dns">Servidores DNS:</label>
            <input
              id="prof-dns"
              v-model="newProfile.dns_server"
              placeholder="ej. 1.1.1.1,8.8.8.8"
            />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateProfileModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Crear Perfil</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Crear Servidor PPPoE -->
    <div
      v-if="isCreateServerModalOpen"
      class="modal-backdrop"
      @click.self="isCreateServerModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-server-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-server-title">Activar Servidor PPPoE</h2>
          <button type="button" class="btn-close" @click="isCreateServerModalOpen = false">
            ✕
          </button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateServer">
          <div class="form-group">
            <label for="srv-name">Nombre del Servicio:</label>
            <input
              id="srv-name"
              v-model="newServer.service_name"
              required
              placeholder="ej. pppoe-clientes"
            />
          </div>
          <div class="form-group">
            <label for="srv-iface">Interfaz Física / Bridge:</label>
            <input
              id="srv-iface"
              v-model="newServer.interface"
              required
              placeholder="ej. bridge1 o ether3"
            />
          </div>
          <div class="form-group">
            <label for="srv-prof">Perfil Predeterminado:</label>
            <input id="srv-prof" v-model="newServer.default_profile" placeholder="ej. default" />
          </div>
          <div class="form-group">
            <label for="srv-mtu">Max MTU:</label>
            <input
              id="srv-mtu"
              v-model.number="newServer.max_mtu"
              type="number"
              min="1280"
              max="1500"
            />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateServerModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Activar Servidor
            </button>
          </footer>
        </form>
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
  .subtabs-bar {
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--rg-border-grid);
    padding-bottom: 8px;
    overflow-x: auto;
  }
  .btn-subtab {
    background: transparent;
    color: var(--rg-text-secondary);
    border: 1px solid transparent;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn-subtab--active {
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
  .row-actions-group {
    display: inline-flex;
    gap: 4px;
    align-items: center;
  }
  .btn-row-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 4px;
    color: var(--rg-text-secondary, #94a3b8);
    font-size: 0.8rem;
    padding: 2px 8px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-row-action:hover {
    border-color: var(--rg-accent-cyan, #00d2ff);
    color: var(--rg-accent-cyan, #00d2ff);
    background: rgba(0, 210, 255, 0.1);
  }
  .btn-row-action--danger:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
  }
</style>
