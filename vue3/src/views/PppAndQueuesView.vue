<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  /* eslint-disable sonarjs/cognitive-complexity, sonarjs/no-duplicate-string */
  import type { WebFigDynamic } from '@/types';
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
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
    caller_id?: string;
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
    max_mru?: number;
    max_sessions?: number;
    one_session_per_host?: boolean;
    'one-session-per-host'?: string;
    keepalive_timeout?: number;
    disabled?: boolean;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<
    'pppoe-active' | 'ppp-secrets' | 'ppp-profiles' | 'pppoe-servers' | 'simple-queues' | 'queue-tree'
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
  const queueTrees = ref<WebFigDynamic[]>([]);
  const queueTypes = ref<WebFigDynamic[]>([]);

  // Modals Queue Tree
  const isCreateTreeModalOpen = ref(false);
  const newTreeForm = ref({
    name: 'queue-htb-1',
    parent: 'global',
    packet_mark: 'no-mark',
    limit_at: '1M',
    max_limit: '10M',
    priority: 8,
  });

  // Modals
  const isCreateSecretModalOpen = ref(false);
  const isEditSecretModalOpen = ref(false);
  const editingSecretId = ref('');
  const editSecretForm = ref({
    name: '',
    password: '',
    service: 'any',
    profile: 'default',
    local_address: '',
    remote_address: '',
    caller_id: '',
    comment: '',
    disabled: false,
  });

  const isCreateProfileModalOpen = ref(false);
  const isEditProfileModalOpen = ref(false);
  const editingProfileId = ref('');
  const editProfileForm = ref({
    name: '',
    local_address: '',
    remote_address: '',
    rate_limit: '',
    dns_server: '',
    only_one: 'default',
  });

  const isCreateServerModalOpen = ref(false);
  const isEditServerModalOpen = ref(false);
  const editingServerId = ref('');
  const editServerForm = ref({
    service_name: '',
    interface: '',
    default_profile: 'default',
    max_mtu: 1492,
    max_mru: 1492,
    one_session_per_host: true,
    keepalive_timeout: 10,
    disabled: false,
  });

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
    caller_id: '',
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
    keepalive_timeout: 10,
  });

  const pppColumns: TableColumn<PppActiveSessionItem>[] = [
    { key: 'name', label: 'Usuario PPPoE', sortable: true },
    { key: 'address', label: 'Dirección IP' },
    { key: 'caller_id', label: 'MAC / Caller-ID' },
    { key: 'uptime', label: 'Uptime', align: 'right' },
    { key: 'service', label: 'Servicio', align: 'center' },
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  const secretColumns: TableColumn<PppSecretItem>[] = [
    { key: 'name', label: 'Usuario (Name)', sortable: true },
    { key: 'service', label: 'Servicio', align: 'center' },
    { key: 'profile', label: 'Perfil Asignado', sortable: true },
    { key: 'local_address', label: 'IP Local (Gateway)' },
    { key: 'remote_address', label: 'IP Remota (Cliente)' },
    { key: 'caller_id', label: 'Candado MAC (Caller-ID)', align: 'center' },
    {
      key: 'disabled',
      label: 'Estado',
      align: 'center',
      formatter: (row) => (row.disabled ? '🔴 Deshabilitado' : '🟢 Activo'),
    },
    { key: 'comment', label: 'Comentario' },
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  const profileColumns: TableColumn<PppProfileItem>[] = [
    { key: 'name', label: 'Nombre Perfil', sortable: true },
    { key: 'local_address', label: 'Pool / IP Local' },
    { key: 'remote_address', label: 'Pool / IP Remota' },
    { key: 'rate_limit', label: 'Rate Limit (Límite Ancho de Banda)', align: 'center' },
    { key: 'dns_server', label: 'Servidores DNS' },
    { key: 'only_one', label: 'Sesión Única', align: 'center' },
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  const serverColumns: TableColumn<PppoeServerItem>[] = [
    { key: 'service_name', label: 'Nombre Servicio', sortable: true },
    { key: 'interface', label: 'Interfaz Escucha', sortable: true },
    { key: 'default_profile', label: 'Perfil Predeterminado' },
    { key: 'max_mtu', label: 'Max MTU', align: 'center' },
    {
      key: 'one_session_per_host',
      label: '1 Sesión/MAC',
      align: 'center',
      formatter: (row) => (row.one_session_per_host !== false ? '🟢 Sí' : '⚠️ No'),
    },
    {
      key: 'keepalive_timeout',
      label: 'Keepalive (s)',
      align: 'center',
      formatter: (row) =>
        row.keepalive_timeout && row.keepalive_timeout > 0
          ? `${row.keepalive_timeout}s`
          : '⚠️ Deshabilitado',
    },
    {
      key: 'disabled',
      label: 'Estado',
      align: 'center',
      formatter: (row) => (row.disabled ? '🔴 Inactivo' : '🟢 Activo'),
    },
    { key: 'actions', label: 'Acciones', align: 'center' },
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
    { key: 'actions', label: 'Acciones', align: 'center' },
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

  async function loadPppData(forceRefresh = false) {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const query = forceRefresh ? '?refresh=true' : '';
      if (activeTab.value === 'pppoe-active') {
        const res = await http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/ppp/active${query}`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppSessions.value = items.map((s: WebFigDynamic) => ({
          ...s,
          id: s.id || s['.id'] || s.name,
          caller_id: s.caller_id || s['caller-id'] || '',
        }));
      } else if (activeTab.value === 'ppp-secrets') {
        const res = await http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/ppp/secrets${query}`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppSecrets.value = items.map((sec: WebFigDynamic) => ({
          ...sec,
          id: sec.id || sec['.id'] || sec.name,
          local_address: sec.local_address || sec['local-address'] || '',
          remote_address: sec.remote_address || sec['remote-address'] || '',
          caller_id: sec.caller_id || sec['caller-id'] || '',
          disabled: sec.disabled === 'true' || sec.disabled === true,
        }));
      } else if (activeTab.value === 'ppp-profiles') {
        const res = await http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/ppp/profiles${query}`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppProfiles.value = items.map((prof: WebFigDynamic) => ({
          ...prof,
          id: prof.id || prof['.id'] || prof.name,
          local_address: prof.local_address || prof['local-address'] || '',
          remote_address: prof.remote_address || prof['remote-address'] || '',
          rate_limit: prof.rate_limit || prof['rate-limit'] || '',
          dns_server: prof.dns_server || prof['dns-server'] || '',
          only_one: prof.only_one || prof['only-one'] || '',
        }));
      } else if (activeTab.value === 'pppoe-servers') {
        const res = await http.get<WebFigDynamic>(
          `/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers${query}`,
        );
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        pppoeServers.value = items.map((srv: WebFigDynamic) => {
          const rawKa = srv.keepalive_timeout ?? srv['keepalive-timeout'];
          const parsedKa =
            rawKa === 'disabled' || rawKa === 0 || rawKa === '0'
              ? 0
              : rawKa !== undefined && rawKa !== null && rawKa !== ''
                ? Number(rawKa) || 10
                : 10;
          return {
            ...srv,
            id: srv.id || srv['.id'] || `${srv.interface}-${srv.service_name || srv['service-name']}`,
            service_name: srv.service_name || srv['service-name'] || '',
            default_profile: srv.default_profile || srv['default-profile'] || '',
            max_mtu: srv.max_mtu ? Number(srv.max_mtu) : Number(srv['max-mtu'] || 1492),
            one_session_per_host:
              srv.one_session_per_host !== false &&
              srv['one-session-per-host'] !== 'no' &&
              srv['one-session-per-host'] !== 'false',
            keepalive_timeout: parsedKa,
            disabled: srv.disabled === 'true' || srv.disabled === true,
          };
        });
      } else if (activeTab.value === 'queue-tree') {
        const [treesRes, typesRes] = await Promise.all([
          http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/queues/tree${query}`).catch(() => ({ data: [] })),
          http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/queues/types${query}`).catch(() => ({ data: [] })),
        ]);
        queueTrees.value = Array.isArray(treesRes.data) ? treesRes.data : treesRes.data?.items || [];
        queueTypes.value = Array.isArray(typesRes.data) ? typesRes.data : typesRes.data?.items || [];
      } else {
        const res = await http.get<WebFigDynamic>(`/api/v1/routers/${routerId.value}/webfig/queues/simple${query}`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        simpleQueues.value = items.map((q: WebFigDynamic) => ({
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
      else if (activeTab.value === 'queue-tree') queueTrees.value = [];
      else simpleQueues.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function handleMoveSimpleQueue(event: WebFigDynamic) {
    try {
      const body = {
        numbers: event.numbers || event.id || event.from,
        destination: event.destination || event.to || '0',
      };
      await http.post(`/api/v1/routers/${routerId.value}/webfig/queues/simple/move`, body);
      actionMessage.value = 'Cola reordenada exitosamente en RouterOS.';
      await loadPppData(true);
    } catch {
      errorMessage.value = 'Error al reordenar cola simple';
    }
  }

  async function handleCreateQueueTree() {
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/queues/tree`, newTreeForm.value);
      isCreateTreeModalOpen.value = false;
      actionMessage.value = 'Cola Tree creada exitosamente.';
      await loadPppData(true);
    } catch (err: unknown) {
      errorMessage.value = 'Error al crear cola Tree';
    }
  }

  async function handleDeleteQueueTree(tree: WebFigDynamic) {
    if (!confirm(`¿Eliminar la cola Tree ${tree.name || tree.id}?`)) return;
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/queues/tree/${tree.id || tree['.id'] || tree.name}`);
      actionMessage.value = 'Cola Tree eliminada exitosamente.';
      await loadPppData(true);
    } catch {
      errorMessage.value = 'Error al eliminar cola Tree';
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
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
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
        caller_id: '',
        comment: '',
      };
      loadPppData(true);
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
      loadPppData(true);
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
      loadPppData(true);
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

  async function handleSaveQueue(payload: Record<string, WebFigDynamic>) {
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
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
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
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al conmutar cola.';
    }
  }

  async function handleDeleteQueue(queue: SimpleQueueItem) {
    if (!confirm(`¿Eliminar la cola simple "${queue.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/queues/simple/${queue.id}`);
      actionMessage.value = `Cola "${queue.name}" eliminada.`;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
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
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al conmutar usuario PPP.';
    }
  }

  async function handleDeleteSecret(secret: PppSecretItem) {
    if (!confirm(`¿Eliminar el usuario PPP "${secret.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/secrets/${secret.id}`);
      actionMessage.value = `Usuario "${secret.name}" eliminado.`;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar usuario PPP.';
    }
  }

  function openEditSecretModal(secret: PppSecretItem) {
    editingSecretId.value = secret.id;
    editSecretForm.value = {
      name: secret.name,
      password: '',
      service: String(secret.service || 'any'),
      profile: String(secret.profile || 'default'),
      local_address: String(secret.local_address || ''),
      remote_address: String(secret.remote_address || ''),
      caller_id: String(secret.caller_id || ''),
      comment: String(secret.comment || ''),
      disabled: Boolean(secret.disabled),
    };
    isEditSecretModalOpen.value = true;
  }

  async function handleUpdateSecret() {
    if (!editingSecretId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      const payload: Record<string, WebFigDynamic> = {
        name: editSecretForm.value.name,
        service: editSecretForm.value.service,
        profile: editSecretForm.value.profile,
        local_address: editSecretForm.value.local_address,
        remote_address: editSecretForm.value.remote_address,
        caller_id: editSecretForm.value.caller_id,
        comment: editSecretForm.value.comment,
        disabled: editSecretForm.value.disabled,
      };
      if (editSecretForm.value.password.trim()) {
        payload.password = editSecretForm.value.password;
      }
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ppp/secrets/${encodeURIComponent(editingSecretId.value)}`,
        payload,
      );
      actionMessage.value = `Usuario PPP "${editSecretForm.value.name}" actualizado exitosamente.`;
      isEditSecretModalOpen.value = false;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || err?.detail || 'Error al actualizar usuario PPP.';
    } finally {
      isLoading.value = false;
    }
  }

  function openEditProfileModal(profile: PppProfileItem) {
    editingProfileId.value = profile.id;
    editProfileForm.value = {
      name: profile.name,
      local_address: String(profile.local_address || ''),
      remote_address: String(profile.remote_address || ''),
      rate_limit: String(profile.rate_limit || ''),
      dns_server: String(profile.dns_server || ''),
      only_one: String(profile.only_one || 'default'),
    };
    isEditProfileModalOpen.value = true;
  }

  async function handleUpdateProfile() {
    if (!editingProfileId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ppp/profiles/${encodeURIComponent(editingProfileId.value)}`,
        editProfileForm.value,
      );
      actionMessage.value = `Perfil PPP "${editProfileForm.value.name}" actualizado exitosamente.`;
      isEditProfileModalOpen.value = false;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || err?.detail || 'Error al actualizar perfil PPP.';
    } finally {
      isLoading.value = false;
    }
  }

  function openEditServerModal(srv: PppoeServerItem) {
    editingServerId.value = srv.id;
    editServerForm.value = {
      service_name: srv.service_name,
      interface: srv.interface,
      default_profile: String(srv.default_profile || 'default'),
      max_mtu: Number(srv.max_mtu || 1492),
      max_mru: Number(srv.max_mru || srv.max_mtu || 1492),
      one_session_per_host:
        srv['one-session-per-host'] !== 'no' && srv.one_session_per_host !== false,
      keepalive_timeout:
        srv.keepalive_timeout !== undefined && srv.keepalive_timeout !== null
          ? Number(srv.keepalive_timeout)
          : 10,
      disabled: Boolean(srv.disabled),
    };
    isEditServerModalOpen.value = true;
  }

  async function handleUpdateServer() {
    if (!editingServerId.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers/${encodeURIComponent(editingServerId.value)}`,
        editServerForm.value,
      );
      actionMessage.value = `Servidor PPPoE "${editServerForm.value.service_name}" actualizado exitosamente.`;
      isEditServerModalOpen.value = false;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || err?.detail || 'Error al actualizar servidor PPPoE.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleToggleServer(srv: PppoeServerItem) {
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers/${encodeURIComponent(srv.id)}`,
        { disabled: !srv.disabled },
      );
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al conmutar servidor PPPoE.';
    }
  }

  async function handleDeleteServer(srv: PppoeServerItem) {
    if (!confirm(`¿Eliminar el servidor PPPoE "${srv.service_name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/pppoe-servers/${encodeURIComponent(srv.id)}`);
      actionMessage.value = `Servidor PPPoE "${srv.service_name}" eliminado.`;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar servidor PPPoE.';
    }
  }

  async function handleDeleteProfile(profile: PppProfileItem) {
    if (!confirm(`¿Eliminar el perfil PPP "${profile.name}"?`)) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(`/api/v1/routers/${routerId.value}/webfig/ppp/profiles/${profile.id}`);
      actionMessage.value = `Perfil "${profile.name}" eliminado.`;
      loadPppData(true);
    } catch (rawErr: unknown) {
      const err = rawErr as { detail?: string; message?: string; status?: number; response?: { status?: number; data?: { detail?: string; message?: string } } };
      errorMessage.value = err?.response?.data?.detail || 'Error al eliminar perfil PPP.';
    }
  }

  function setTab(tab: typeof activeTab.value) {
    activeTab.value = tab;
    loadPppData();
  }

  function handleWebFigRefresh() {
    loadPppData(true);
  }

  onMounted(() => {
    loadPppData();
    window.addEventListener('rosgrid:webfig-refresh', handleWebFigRefresh);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('rosgrid:webfig-refresh', handleWebFigRefresh);
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
          v-if="activeTab === 'queue-tree'"
          type="button"
          class="btn-primary"
          @click="isCreateTreeModalOpen = true"
        >
          + Nueva Cola Tree (HTB)
        </button>
        <button
          id="btn-webfig-refresh"
          type="button"
          class="btn-refresh font-tabular"
          :disabled="isLoading"
          aria-label="Refrescar datos PPP"
          @click="loadPppData(true)"
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
      <button
        type="button"
        class="btn-subtab"
        :class="{ 'btn-subtab--active': activeTab === 'queue-tree' }"
        role="tab"
        :aria-selected="activeTab === 'queue-tree'"
        @click="setTab('queue-tree')"
      >
        🌳 Queue Tree & Tipos
      </button>
    </nav>

    <!-- Contenidos -->
    <div class="content-block">
      <!-- Pestaña 1: Sesiones Activas -->
      <div v-if="activeTab === 'pppoe-active'">
        <RgDataTable
          :columns="pppColumns"
          :rows="filteredPppSessions"
          caption="Sesiones PPPoE Activas"
          row-key="id"
        >
          <template #actions="{ row }">
            <button
              type="button"
              class="btn-row-action btn-row-action--danger"
              :aria-label="`Desconectar sesión PPPoE de ${row.name}`"
              title="Desconectar / Expulsar Abonado (Kick Session)"
              @click="handleReconnectPpp(row)"
            >
              ⏏ Desconectar
            </button>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 2: Secretos PPP -->
      <div v-else-if="activeTab === 'ppp-secrets'">
        <RgDataTable
          :columns="secretColumns"
          :rows="pppSecrets"
          caption="Secretos y Clientes PPP"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                title="Editar usuario PPP"
                :aria-label="`Editar usuario ${row.name}`"
                @click="openEditSecretModal(row)"
              >
                ✏
              </button>
              <button
                type="button"
                class="btn-row-action"
                :title="row.disabled ? 'Habilitar usuario' : 'Deshabilitar usuario'"
                :aria-label="row.disabled ? 'Habilitar usuario' : 'Deshabilitar usuario'"
                @click="handleToggleSecret(row)"
              >
                {{ row.disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar usuario"
                :aria-label="`Eliminar usuario ${row.name}`"
                @click="handleDeleteSecret(row)"
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
          :columns="profileColumns"
          :rows="pppProfiles"
          caption="Perfiles de Servicio PPP"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                title="Editar perfil PPP"
                :aria-label="`Editar perfil ${row.name}`"
                @click="openEditProfileModal(row)"
              >
                ✏
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar perfil"
                :aria-label="`Eliminar perfil ${row.name}`"
                @click="handleDeleteProfile(row)"
              >
                🗑
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 4: Servidores PPPoE -->
      <div v-else-if="activeTab === 'pppoe-servers'">
        <RgDataTable
          :columns="serverColumns"
          :rows="pppoeServers"
          caption="Servidores de Autenticación PPPoE"
          row-key="id"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                title="Editar servidor PPPoE"
                :aria-label="`Editar servidor PPPoE ${row.service_name}`"
                @click="openEditServerModal(row)"
              >
                ✏
              </button>
              <button
                type="button"
                class="btn-row-action"
                :title="row.disabled ? 'Habilitar servidor PPPoE' : 'Deshabilitar servidor PPPoE'"
                :aria-label="row.disabled ? 'Habilitar servidor PPPoE' : 'Deshabilitar servidor PPPoE'"
                @click="handleToggleServer(row)"
              >
                {{ row.disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar servidor PPPoE"
                :aria-label="`Eliminar servidor PPPoE ${row.service_name}`"
                @click="handleDeleteServer(row)"
              >
                🗑
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 5: Simple Queues -->
      <div v-else-if="activeTab === 'simple-queues'">
        <RgDataTable
          :columns="queueColumns"
          :rows="simpleQueues"
          caption="Colas de Ancho de Banda Simples"
          row-key="id"
          :sortable-rows="true"
          @move-row="handleMoveSimpleQueue"
        >
          <template #actions="{ row }">
            <div class="row-actions-group">
              <button
                type="button"
                class="btn-row-action"
                title="Editar cola simple"
                :aria-label="`Editar cola ${row.name}`"
                @click="openEditQueueModal(row)"
              >
                ✏
              </button>
              <button
                type="button"
                class="btn-row-action"
                :title="row.disabled ? 'Habilitar cola' : 'Deshabilitar cola'"
                :aria-label="row.disabled ? 'Habilitar cola' : 'Deshabilitar cola'"
                @click="handleToggleQueue(row)"
              >
                {{ row.disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-row-action btn-row-action--danger"
                title="Eliminar cola simple"
                :aria-label="`Eliminar cola ${row.name}`"
                @click="handleDeleteQueue(row)"
              >
                🗑
              </button>
            </div>
          </template>
        </RgDataTable>
      </div>

      <!-- Pestaña 6: Queue Tree (HTB) & Tipos -->
      <div v-else-if="activeTab === 'queue-tree'" class="font-tabular">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <div>
            <h3 style="margin: 0; color: #00e5ff;">🌳 Árbol de Colas Jerárquicas HTB (/queue/tree)</h3>
            <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #94a3b8;">Asignación de prioridades y límites de ancho de banda por marcas de paquetes (packet-mark).</p>
          </div>
          <button type="button" class="btn-primary" @click="isCreateTreeModalOpen = true">
            + Nueva Cola Tree
          </button>
        </div>

        <table class="rg-table font-tabular" style="width: 100%;">
          <thead>
            <tr>
              <th scope="col">Nombre</th>
              <th scope="col">Padre (Parent)</th>
              <th scope="col">Marca de Paquete</th>
              <th scope="col">Limit At (Garantizado)</th>
              <th scope="col">Max Limit (Tope)</th>
              <th scope="col">Prioridad</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="queueTrees.length === 0">
              <td colspan="7" class="text-center" style="padding: 1rem; color: #64748b;">No hay colas de árbol HTB configuradas en el router.</td>
            </tr>
            <tr v-for="t in queueTrees" :key="t.name || t['.id']">
              <td class="font-bold text-cyan font-mono">{{ t.name }}</td>
              <td class="font-mono">{{ t.parent }}</td>
              <td class="font-mono text-emerald">{{ t['packet-mark'] || t.packet_mark || 'no-mark' }}</td>
              <td class="font-mono">{{ t['limit-at'] || t.limit_at || '0' }}</td>
              <td class="font-mono font-bold">{{ t['max-limit'] || t.max_limit || '0' }}</td>
              <td><span class="badge-type">P{{ t.priority || 8 }}</span></td>
              <td>
                <button
                  type="button"
                  class="btn-row-action btn-row-action--danger"
                  title="Eliminar cola Tree"
                  @click="handleDeleteQueueTree(t)"
                >
                  🗑
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Visualizador de Queue Types -->
        <div style="margin-top: 1.5rem; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 1rem;">
          <h4 style="margin: 0 0 8px 0; color: #cbd5e1;">📋 Tipos de Colas Disponibles (/queue/type) ({{ queueTypes.length }})</h4>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span
              v-for="qt in queueTypes"
              :key="qt.name || qt['.id']"
              class="badge-type font-mono"
              :title="`Kind: ${qt.kind || 'default'}`"
            >
              {{ qt.name }} ({{ qt.kind || 'pcq' }})
            </span>
          </div>
        </div>
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
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isCreateSecretModalOpen = false">
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
          <div class="form-group">
            <label for="sec-caller-id">Candado MAC / Caller-ID (Opcional):</label>
            <input
              id="sec-caller-id"
              v-model="newSecret.caller_id"
              placeholder="ej. AA:BB:CC:11:22:33"
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
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isCreateProfileModalOpen = false">
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
          <div class="form-group">
            <label for="prof-only-one">Sesión Única (Only One — Anti-Duplicidad):</label>
            <select id="prof-only-one" v-model="newProfile.only_one">
              <option value="yes">yes (Recomendado ISP)</option>
              <option value="default">default</option>
              <option value="no">no</option>
            </select>
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
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isCreateServerModalOpen = false">
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
          <div class="form-group">
            <label for="srv-keepalive">Keepalive Timeout (s) — Anti-Sesión Fantasma:</label>
            <input
              id="srv-keepalive"
              v-model.number="newServer.keepalive_timeout"
              type="number"
              min="1"
              max="3600"
            />
          </div>
          <div class="form-group">
            <label for="srv-one-session" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
              <input
                id="srv-one-session"
                v-model="newServer.one_session_per_host"
                type="checkbox"
              />
              Una sesión por MAC (one-session-per-host = yes)
            </label>
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

    <!-- Modal Editar Secreto PPP -->
    <div
      v-if="isEditSecretModalOpen"
      class="modal-backdrop"
      @click.self="isEditSecretModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-secret-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-secret-title">Editar Usuario / Secreto PPP ({{ editSecretForm.name }})</h2>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isEditSecretModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdateSecret">
          <div class="form-group">
            <label for="edit-sec-name">Nombre de Usuario:</label>
            <input id="edit-sec-name" v-model="editSecretForm.name" required />
          </div>
          <div class="form-group">
            <label for="edit-sec-pwd">Nueva Contraseña (dejar en blanco para conservar):</label>
            <input id="edit-sec-pwd" v-model="editSecretForm.password" type="password" placeholder="Sin cambios" />
          </div>
          <div class="form-group">
            <label for="edit-sec-svc">Servicio:</label>
            <select id="edit-sec-svc" v-model="editSecretForm.service">
              <option value="any">Cualquiera (any)</option>
              <option value="pppoe">PPPoE</option>
              <option value="pptp">PPTP</option>
              <option value="l2tp">L2TP</option>
              <option value="ovpn">OpenVPN</option>
            </select>
          </div>
          <div class="form-group">
            <label for="edit-sec-prof">Perfil:</label>
            <input id="edit-sec-prof" v-model="editSecretForm.profile" />
          </div>
          <div class="form-group">
            <label for="edit-sec-local">IP Local (Gateway):</label>
            <input id="edit-sec-local" v-model="editSecretForm.local_address" />
          </div>
          <div class="form-group">
            <label for="edit-sec-remote">IP Remota (Cliente):</label>
            <input id="edit-sec-remote" v-model="editSecretForm.remote_address" />
          </div>
          <div class="form-group">
            <label for="edit-sec-caller-id">Candado MAC / Caller-ID (dejar vacío para liberar):</label>
            <input id="edit-sec-caller-id" v-model="editSecretForm.caller_id" placeholder="ej. AA:BB:CC:11:22:33" />
          </div>
          <div class="form-group">
            <label for="edit-sec-comment">Comentario:</label>
            <input id="edit-sec-comment" v-model="editSecretForm.comment" />
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditSecretModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar Perfil PPP -->
    <div
      v-if="isEditProfileModalOpen"
      class="modal-backdrop"
      @click.self="isEditProfileModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-profile-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-profile-title">Editar Perfil PPP ({{ editProfileForm.name }})</h2>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isEditProfileModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdateProfile">
          <div class="form-group">
            <label for="edit-prof-name">Nombre del Perfil:</label>
            <input id="edit-prof-name" v-model="editProfileForm.name" required />
          </div>
          <div class="form-group">
            <label for="edit-prof-local">Pool / IP Local:</label>
            <input id="edit-prof-local" v-model="editProfileForm.local_address" />
          </div>
          <div class="form-group">
            <label for="edit-prof-remote">Pool / IP Remota:</label>
            <input id="edit-prof-remote" v-model="editProfileForm.remote_address" />
          </div>
          <div class="form-group">
            <label for="edit-prof-rate">Rate Limit (Subida/Bajada):</label>
            <input id="edit-prof-rate" v-model="editProfileForm.rate_limit" placeholder="ej. 10M/20M" />
          </div>
          <div class="form-group">
            <label for="edit-prof-dns">Servidores DNS:</label>
            <input id="edit-prof-dns" v-model="editProfileForm.dns_server" />
          </div>
          <div class="form-group">
            <label for="edit-prof-only-one">Sesión Única (Only One):</label>
            <select id="edit-prof-only-one" v-model="editProfileForm.only_one">
              <option value="default">default</option>
              <option value="yes">yes</option>
              <option value="no">no</option>
            </select>
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditProfileModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Editar Servidor PPPoE -->
    <div
      v-if="isEditServerModalOpen"
      class="modal-backdrop"
      @click.self="isEditServerModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-edit-server-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-edit-server-title">Editar Servidor PPPoE ({{ editServerForm.service_name }})</h2>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isEditServerModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleUpdateServer">
          <div class="form-group">
            <label for="edit-srv-name">Nombre del Servicio:</label>
            <input id="edit-srv-name" v-model="editServerForm.service_name" required />
          </div>
          <div class="form-group">
            <label for="edit-srv-iface">Interfaz Física / Bridge:</label>
            <input id="edit-srv-iface" v-model="editServerForm.interface" required />
          </div>
          <div class="form-group">
            <label for="edit-srv-prof">Perfil Predeterminado:</label>
            <input id="edit-srv-prof" v-model="editServerForm.default_profile" />
          </div>
          <div class="form-group">
            <label for="edit-srv-mtu">Max MTU:</label>
            <input id="edit-srv-mtu" v-model.number="editServerForm.max_mtu" type="number" min="1280" max="1500" />
          </div>
          <div class="form-group">
            <label for="edit-srv-keepalive">Keepalive Timeout (s) — Anti-Sesión Fantasma:</label>
            <input
              id="edit-srv-keepalive"
              v-model.number="editServerForm.keepalive_timeout"
              type="number"
              min="1"
              max="3600"
            />
          </div>
          <div class="form-group">
            <label for="edit-srv-one-session" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
              <input
                id="edit-srv-one-session"
                v-model="editServerForm.one_session_per_host"
                type="checkbox"
              />
              Una sesión por MAC (one-session-per-host = yes)
            </label>
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isEditServerModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="isLoading">
              Guardar Cambios
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Crear Queue Tree -->
    <div
      v-if="isCreateTreeModalOpen"
      class="modal-backdrop"
      @click.self="isCreateTreeModalOpen = false"
    >
      <div class="modal-card" role="dialog" aria-labelledby="modal-tree-title" aria-modal="true">
        <header class="modal-header">
          <h2 id="modal-tree-title">➕ Nueva Cola HTB (Queue Tree)</h2>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="isCreateTreeModalOpen = false">✕</button>
        </header>
        <form class="modal-form" @submit.prevent="handleCreateQueueTree">
          <div class="form-group">
            <label for="tree-name">Nombre de la Cola *</label>
            <input id="tree-name" v-model="newTreeForm.name" required placeholder="ej. queue-streaming" />
          </div>
          <div class="form-group">
            <label for="tree-parent">Padre (Parent) *</label>
            <input id="tree-parent" v-model="newTreeForm.parent" required placeholder="global / ether1" />
          </div>
          <div class="form-group">
            <label for="tree-pmark">Marca de Paquete (Packet Mark):</label>
            <input id="tree-pmark" v-model="newTreeForm.packet_mark" placeholder="no-mark / streaming_pkts" />
          </div>
          <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div class="form-group">
              <label for="tree-limit">Limit At (Garantizado):</label>
              <input id="tree-limit" v-model="newTreeForm.limit_at" placeholder="1M" />
            </div>
            <div class="form-group">
              <label for="tree-max">Max Limit (Tope):</label>
              <input id="tree-max" v-model="newTreeForm.max_limit" placeholder="10M" />
            </div>
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isCreateTreeModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="isLoading">Crear Cola Tree</button>
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
    background: rgba(15, 23, 42, 0.75);
    color: var(--rg-text-secondary, #cbd5e1);
    border: 1px solid var(--rg-border-panel, #334155);
    padding: 8px 14px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-secondary:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
  }
  .btn-refresh:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }
  .row-actions-group {
    display: inline-flex;
    gap: 6px;
    align-items: center;
    justify-content: flex-end;
  }
  .btn-row-action {
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
  .btn-row-action:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
    box-shadow: 0 0 8px rgba(34, 211, 238, 0.15);
  }
  .btn-row-action--danger {
    border-color: rgba(239, 68, 68, 0.35);
    color: #fca5a5;
  }
  .btn-row-action--danger:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.2);
  }
</style>
