<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue';
  import { useIpamStore } from '@/stores/useIpamStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useI18n } from '@/composables/useI18n';
  import IpamPrefixTable from '@/components/ipam/IpamPrefixTable.vue';
  import IpamIpGridModal from '@/components/ipam/IpamIpGridModal.vue';
  import CorporateIpv6ManagerModal from '@/components/ipam/CorporateIpv6ManagerModal.vue';
  import FiberCutAlertBanner from '@/components/operations/FiberCutAlertBanner.vue';
  import type { CustomerService, IPAMPrefix } from '@/types';
  import { http } from '@/api/httpClient';

  const { t } = useI18n();

  const ipamStore = useIpamStore();
  const inventoryStore = useInventoryStore();

  interface BandwidthProfileItem {
    id: string;
    name: string;
    rate_down_kbps: number;
    rate_up_kbps: number;
    burst_down_kbps?: number;
    burst_up_kbps?: number;
    burst_threshold_down_kbps?: number;
    burst_threshold_up_kbps?: number;
    burst_time_seconds?: number;
    priority?: number;
    queue_type?: string;
    created_at?: string;
  }

  const activeSubTab = ref<'prefixes' | 'subscribers' | 'sync' | 'bandwidth'>('prefixes');
  const selectedGridPrefix = ref<IPAMPrefix | null>(null);
  const corporateModalOpen = ref(false);

  const isSimulatingDhcp = ref(false);
  const bandwidthProfiles = ref<BandwidthProfileItem[]>([]);
  const isLoadingBandwidth = ref(false);
  const isBandwidthModalOpen = ref(false);
  const editingProfileId = ref<string | null>(null);
  const bandwidthForm = ref({
    name: '',
    rate_down_kbps: 10240,
    rate_up_kbps: 5120,
    burst_down_kbps: 0,
    burst_up_kbps: 0,
    burst_threshold_down_kbps: 0,
    burst_threshold_up_kbps: 0,
    burst_time_seconds: 8,
    priority: 8,
    queue_type: 'pcq-download-default',
  });

  const isScriptModalOpen = ref(false);
  const scriptTitle = ref('');
  const generatedScript = ref('');

  function copyGeneratedScript() {
    if (typeof window !== 'undefined' && window.navigator?.clipboard) {
      window.navigator.clipboard.writeText(generatedScript.value);
      window.alert('Script copiado al portapapeles');
    }
  }

  const isChangeRateLimitModalOpen = ref(false);
  const selectedServiceForRateLimit = ref<CustomerService | null>(null);
  const targetProfileIdForRateLimit = ref('');
  const isSubmittingRateLimit = ref(false);

  const selectedSyncRouterId = ref('');
  const isSyncing = ref(false);
  const syncResult = ref<{ synced_prefixes: number; synced_ips: number; message: string } | null>(
    null,
  );

  // Modal Nuevo Abonado
  const newSubscriberModalOpen = ref(false);
  const newSubscriber = ref<Partial<CustomerService>>({
    router_id: '',
    customer_name: '',
    customer_code: '',
    service_type: 'DHCP',
    auth_backend: 'LOCAL_SECRET',
    pppoe_username: '',
    assigned_ipv4: '',
    onu_mode: 'ROUTER',
    onu_mac_address: '',
    onu_serial_number: '',
    pon_port: 'gpon-olt1/1/1',
    optical_box: 'NAP-01',
  });

  // Modal Emparejar Red de Abonado (DHCP / PPPoE / IPAM)
  const pairModalOpen = ref(false);
  const selectedSubForPair = ref<CustomerService | null>(null);
  const isLoadingCandidates = ref(false);
  const isSavingPair = ref(false);
  const pairErrorMsg = ref('');
  const pairSuccessMsg = ref('');
  const liveCandidates = ref<import('@/types').SubscriberLiveCandidatesResponse | null>(null);
  const selectedDhcpLeaseIp = ref('');
  const selectedPppoeSessionName = ref('');
  const pairForm = ref({
    bng_router_id: '',
    provision_on_router: true,
    service_type: 'DHCP' as 'DHCP' | 'PPPOE' | 'STATIC',
    onu_mode: 'ROUTER' as 'ROUTER' | 'BRIDGE',
    pppoe_username: '',
    pppoe_password: '',
    onu_mac_address: '',
    assigned_ipv4: '',
  });

  async function loadLiveCandidatesForPair(subId: string, bngRouterId?: string) {
    isLoadingCandidates.value = true;
    pairErrorMsg.value = '';
    try {
      const candidates = bngRouterId
        ? await ipamStore.fetchSubscriberLiveCandidates(subId, bngRouterId)
        : await ipamStore.fetchSubscriberLiveCandidates(subId);
      liveCandidates.value = candidates;
      if (candidates.router_id) {
        pairForm.value.bng_router_id = candidates.router_id;
      }
      if (candidates.matched_ipv4 && !pairForm.value.assigned_ipv4) {
        pairForm.value.assigned_ipv4 = candidates.matched_ipv4;
        selectedDhcpLeaseIp.value = candidates.matched_ipv4;
      }
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'No se pudieron consultar sesiones en vivo del router.');
    } finally {
      isLoadingCandidates.value = false;
    }
  }

  async function openPairSubscriberModal(sub: CustomerService) {
    selectedSubForPair.value = sub;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    selectedDhcpLeaseIp.value = '';
    selectedPppoeSessionName.value = '';
    pairForm.value = {
      bng_router_id: sub.router_id || '',
      provision_on_router: true,
      service_type: (sub.service_type as 'DHCP' | 'PPPOE' | 'STATIC') || 'DHCP',
      onu_mode: (sub.onu_mode === 'BRIDGE' ? 'BRIDGE' : 'ROUTER'),
      pppoe_username: sub.pppoe_username || sub.endpoint_identifier || '',
      pppoe_password: '',
      onu_mac_address: sub.onu_mac_address || '',
      assigned_ipv4: sub.assigned_ipv4 || '',
    };
    pairModalOpen.value = true;
    await loadLiveCandidatesForPair(sub.id);
  }

  async function handleChangeBngRouter() {
    if (!selectedSubForPair.value || !pairForm.value.bng_router_id) return;
    await loadLiveCandidatesForPair(selectedSubForPair.value.id, pairForm.value.bng_router_id);
  }

  function handleSelectDhcpCandidate(address: string) {
    selectedDhcpLeaseIp.value = address;
    const found = liveCandidates.value?.dhcp_leases.find((l) => l.address === address);
    if (found) {
      pairForm.value.assigned_ipv4 = found.address;
      if (found.mac_address) {
        pairForm.value.onu_mac_address = found.mac_address;
      }
    }
  }

  function handleSelectPppoeCandidate(name: string) {
    selectedPppoeSessionName.value = name;
    const found = liveCandidates.value?.pppoe_sessions.find((p) => p.name === name);
    if (found) {
      pairForm.value.pppoe_username = found.name;
      if (found.address) {
        pairForm.value.assigned_ipv4 = found.address;
      }
      if (found.caller_id) {
        pairForm.value.onu_mac_address = found.caller_id;
      }
    }
  }

  async function handleSavePairSubscriber() {
    if (!selectedSubForPair.value) return;
    isSavingPair.value = true;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    try {
      await ipamStore.pairSubscriberNetwork(selectedSubForPair.value.id, {
        bng_router_id: pairForm.value.bng_router_id || undefined,
        provision_on_router: pairForm.value.provision_on_router,
        service_type: pairForm.value.service_type,
        onu_mode: pairForm.value.onu_mode,
        endpoint_identifier:
          pairForm.value.service_type === 'PPPOE' && pairForm.value.pppoe_username.trim()
            ? pairForm.value.pppoe_username.trim()
            : selectedSubForPair.value.endpoint_identifier || selectedSubForPair.value.customer_name,
        pppoe_password:
          pairForm.value.service_type === 'PPPOE' && pairForm.value.pppoe_password.trim()
            ? pairForm.value.pppoe_password.trim()
            : undefined,
        onu_mac_address: pairForm.value.onu_mac_address.trim() || undefined,
        assigned_ipv4: pairForm.value.assigned_ipv4.trim() || undefined,
      });
      pairSuccessMsg.value = pairForm.value.provision_on_router
        ? 'Abonado emparejado y aprovisionado en MikroTik exitosamente. Diagnóstico Ping listo.'
        : 'Abonado emparejado en IPAM exitosamente.';
      await ipamStore.fetchCustomerServices();
      setTimeout(() => {
        pairModalOpen.value = false;
      }, 900);
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'Error al emparejar red del abonado.');
    } finally {
      isSavingPair.value = false;
    }
  }

  onMounted(async () => {
    await ipamStore.fetchVrfs();
    await ipamStore.fetchPrefixes();
    await ipamStore.fetchCustomerServices();
    await inventoryStore.fetchRouters();
    fetchBandwidthProfiles();
    if (inventoryStore.routers.length > 0) {
      selectedSyncRouterId.value = inventoryStore.routers[0].id;
      newSubscriber.value.router_id = inventoryStore.routers[0].id;
    }
  });

  async function fetchBandwidthProfiles() {
    isLoadingBandwidth.value = true;
    try {
      const res = await http.get<BandwidthProfileItem[]>('/api/v1/bandwidth-profiles');
      bandwidthProfiles.value = res.data;
    } catch (err: unknown) {
      console.error('Error al cargar perfiles QoS:', err);
    } finally {
      isLoadingBandwidth.value = false;
    }
  }

  async function handleSimulateFromDhcp() {
    if (!confirm('¿Importar y simular abonados automáticamente a partir de los leases DHCP de la flota?')) {
      return;
    }
    isSimulatingDhcp.value = true;
    try {
      const res = await http.post<{ total_simulated: number; subscribers_created: number; message: string }>(
        '/api/v1/subscriber-devices/simulate-from-dhcp?reset_existing=false',
      );
      alert(res.data.message || `Simulación completada: ${res.data.total_simulated} leases procesados.`);
      await ipamStore.fetchCustomerServices();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al simular clientes desde DHCP'));
    } finally {
      isSimulatingDhcp.value = false;
    }
  }

  async function handleIsolateService(sub: CustomerService) {
    if (!confirm(`¿Suspender técnicamente el servicio de ${sub.customer_name}?`)) return;
    try {
      const res = await http.post<{ status: string; message: string }>(
        `/api/v1/network-services/${sub.id}/isolate`,
      );
      alert(res.data.message || 'Servicio aislado exitosamente');
      await ipamStore.fetchCustomerServices();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al aislar servicio'));
    }
  }

  async function handleRestoreService(sub: CustomerService) {
    if (!confirm(`¿Reconectar y restaurar servicio de ${sub.customer_name}?`)) return;
    try {
      const res = await http.post<{ status: string; message: string }>(
        `/api/v1/network-services/${sub.id}/restore`,
      );
      alert(res.data.message || 'Servicio restaurado exitosamente');
      await ipamStore.fetchCustomerServices();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al restaurar servicio'));
    }
  }

  function openChangeRateLimitModal(sub: CustomerService) {
    selectedServiceForRateLimit.value = sub;
    targetProfileIdForRateLimit.value = bandwidthProfiles.value[0]?.id || '';
    isChangeRateLimitModalOpen.value = true;
    if (bandwidthProfiles.value.length === 0) {
      fetchBandwidthProfiles();
    }
  }

  async function submitChangeRateLimit() {
    if (!selectedServiceForRateLimit.value || !targetProfileIdForRateLimit.value) return;
    isSubmittingRateLimit.value = true;
    try {
      const res = await http.post<{ status: string; message: string }>(
        `/api/v1/network-services/${selectedServiceForRateLimit.value.id}/change-rate-limit`,
        { bandwidth_profile_id: targetProfileIdForRateLimit.value },
      );
      alert(res.data.message || 'Límite de ancho de banda modificado en caliente');
      isChangeRateLimitModalOpen.value = false;
      await ipamStore.fetchCustomerServices();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al cambiar plan'));
    } finally {
      isSubmittingRateLimit.value = false;
    }
  }

  async function handleShowSubscriberQueueScript(sub: CustomerService) {
    try {
      const res = await http.get<{ script: string }>(
        `/api/v1/subscriber-devices/${sub.id}/mikrotik-queue-script`,
      );
      scriptTitle.value = `Script RouterOS Queue: ${sub.customer_name}`;
      generatedScript.value = res.data.script || '# Sin script generado';
      isScriptModalOpen.value = true;
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al generar script de cola'));
    }
  }

  async function handleShowBandwidthProfileScript(profile: BandwidthProfileItem) {
    try {
      const res = await http.get<{ script: string; profile_name: string }>(
        `/api/v1/bandwidth-profiles/${profile.id}/mikrotik-script`,
      );
      scriptTitle.value = `Script MikroTik QoS: ${profile.name}`;
      generatedScript.value = res.data.script || '# Sin script';
      isScriptModalOpen.value = true;
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al consultar script MikroTik'));
    }
  }

  function openCreateBandwidthModal() {
    editingProfileId.value = null;
    bandwidthForm.value = {
      name: '',
      rate_down_kbps: 10240,
      rate_up_kbps: 5120,
      burst_down_kbps: 0,
      burst_up_kbps: 0,
      burst_threshold_down_kbps: 0,
      burst_threshold_up_kbps: 0,
      burst_time_seconds: 8,
      priority: 8,
      queue_type: 'pcq-download-default',
    };
    isBandwidthModalOpen.value = true;
  }

  function openEditBandwidthModal(profile: BandwidthProfileItem) {
    editingProfileId.value = profile.id;
    bandwidthForm.value = {
      name: profile.name,
      rate_down_kbps: profile.rate_down_kbps,
      rate_up_kbps: profile.rate_up_kbps,
      burst_down_kbps: profile.burst_down_kbps || 0,
      burst_up_kbps: profile.burst_up_kbps || 0,
      burst_threshold_down_kbps: profile.burst_threshold_down_kbps || 0,
      burst_threshold_up_kbps: profile.burst_threshold_up_kbps || 0,
      burst_time_seconds: profile.burst_time_seconds || 8,
      priority: profile.priority || 8,
      queue_type: profile.queue_type || 'pcq-download-default',
    };
    isBandwidthModalOpen.value = true;
  }

  async function handleSaveBandwidthProfile() {
    if (!bandwidthForm.value.name) return;
    try {
      if (editingProfileId.value) {
        await http.patch(`/api/v1/bandwidth-profiles/${editingProfileId.value}`, bandwidthForm.value);
      } else {
        await http.post('/api/v1/bandwidth-profiles', bandwidthForm.value);
      }
      isBandwidthModalOpen.value = false;
      await fetchBandwidthProfiles();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al guardar perfil de ancho de banda'));
    }
  }

  async function handleDeleteBandwidthProfile(profile: BandwidthProfileItem) {
    if (!confirm(`¿Eliminar el perfil QoS "${profile.name}"?`)) return;
    try {
      await http.delete(`/api/v1/bandwidth-profiles/${profile.id}`);
      await fetchBandwidthProfiles();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al eliminar perfil'));
    }
  }

  const totalSubscribersCount = computed(() => ipamStore.customerServices.length);
  const activeSubscribersCount = computed(
    () => ipamStore.customerServices.filter((s) => s.last_reachability_status === 'ONLINE').length,
  );

  function getErrorMessage(err: unknown, defaultMsg: string): string {
    if (err && typeof err === 'object') {
      const resData = (err as { response?: { data?: { detail?: string } } }).response?.data;
      if (resData?.detail) return resData.detail;
      const msg = (err as { message?: string }).message;
      if (msg) return msg;
    }
    return defaultMsg;
  }

  async function handleSyncMikrotik() {
    if (!selectedSyncRouterId.value) return;
    isSyncing.value = true;
    syncResult.value = null;
    try {
      syncResult.value = await ipamStore.syncMikrotikIpam(selectedSyncRouterId.value);
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error durante la sincronización'));
    } finally {
      isSyncing.value = false;
    }
  }

  async function handleSyncAllMikrotik() {
    isSyncing.value = true;
    syncResult.value = null;
    try {
      syncResult.value = await ipamStore.syncAllMikrotikIpam();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error durante la sincronización de la flota'));
    } finally {
      isSyncing.value = false;
    }
  }

  async function handleCreateSubscriber() {
    if (!newSubscriber.value.customer_name || !newSubscriber.value.router_id) return;
    try {
      await ipamStore.createCustomerService(newSubscriber.value);
      newSubscriberModalOpen.value = false;
      alert('Abonado registrado exitosamente');
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al registrar abonado'));
    }
  }

  // Modal de Ubicación de Cliente
  const locationModalOpen = ref(false);
  const selectedSubForLocation = ref<CustomerService | null>(null);
  const editLocation = ref<{ latitude: number | null; longitude: number | null }>({
    latitude: null,
    longitude: null,
  });
  const isSavingLocation = ref(false);
  const isLocatingGps = ref(false);
  const locationSuccessMsg = ref('');
  const locationErrorMsg = ref('');

  function openLocationModal(sub: CustomerService) {
    selectedSubForLocation.value = sub;
    editLocation.value = {
      latitude: sub.latitude ?? null,
      longitude: sub.longitude ?? null,
    };
    locationSuccessMsg.value = '';
    locationErrorMsg.value = '';
    locationModalOpen.value = true;
  }

  function getCurrentGpsLocation() {
    if (!navigator.geolocation) {
      locationErrorMsg.value = 'Geolocalización no soportada por su navegador.';
      return;
    }
    isLocatingGps.value = true;
    locationErrorMsg.value = '';
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        editLocation.value.latitude = Number(pos.coords.latitude.toFixed(6));
        editLocation.value.longitude = Number(pos.coords.longitude.toFixed(6));
        isLocatingGps.value = false;
      },
      (err) => {
        isLocatingGps.value = false;
        locationErrorMsg.value = `Error GPS: ${err.message}`;
      },
      { timeout: 10000, enableHighAccuracy: true },
    );
  }

  function inheritHeadendLocation() {
    if (!selectedSubForLocation.value) return;
    const router = inventoryStore.routers.find(
      (r) => r.id === selectedSubForLocation.value?.router_id,
    );
    if (router && router.latitude && router.longitude) {
      editLocation.value.latitude = Number(router.latitude);
      editLocation.value.longitude = Number(router.longitude);
      locationSuccessMsg.value = `Ubicación heredada del router ${router.display_name}.`;
    } else {
      locationErrorMsg.value = 'El router asociado no tiene coordenadas geográficas registradas.';
    }
  }

  async function handleSaveLocation() {
    if (!selectedSubForLocation.value) return;
    isSavingLocation.value = true;
    locationErrorMsg.value = '';
    locationSuccessMsg.value = '';
    try {
      await http.patch(`/api/v1/subscriber-devices/${selectedSubForLocation.value.id}`, {
        latitude: editLocation.value.latitude,
        longitude: editLocation.value.longitude,
      });
      // Actualizar en el estado local de Pinia
      selectedSubForLocation.value.latitude = editLocation.value.latitude ?? undefined;
      selectedSubForLocation.value.longitude = editLocation.value.longitude ?? undefined;
      locationSuccessMsg.value = 'Ubicación actualizada correctamente.';
      setTimeout(() => {
        locationModalOpen.value = false;
      }, 1200);
    } catch (err: unknown) {
      locationErrorMsg.value = getErrorMessage(err, 'Error al guardar ubicación del cliente.');
    } finally {
      isSavingLocation.value = false;
    }
  }
</script>


<template>
  <main class="ipam-management-view" aria-label="Gestor IPAM y Servicios de Abonados">
    <!-- Banner de Alerta de Corte de Fibra (Si hay ONUs caídas en el mismo puerto PON) -->
    <FiberCutAlertBanner />

    <!-- Métricas Tácticas Superiores -->
    <section class="ipam-kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">{{ t('ipam.total_subscribers') }}</span>
        <span class="kpi-value text-cyan">{{ totalSubscribersCount }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">{{ t('ipam.online_subscribers') }}</span>
        <span class="kpi-value text-green">{{ activeSubscribersCount }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">{{ t('ipam.active_prefixes') }}</span>
        <span class="kpi-value text-purple">{{ ipamStore.prefixes.length }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">{{ t('ipam.routing_vrfs') }}</span>
        <span class="kpi-value text-yellow">{{ ipamStore.vrfs.length }}</span>
      </div>
    </section>

    <!-- Navegación por Pestañas -->
    <nav class="ipam-tabs-nav" aria-label="Secciones IPAM">
      <button
        type="button"
        :class="['tab-btn', { active: activeSubTab === 'prefixes' }]"
        @click="activeSubTab = 'prefixes'"
      >
        {{ t('ipam.tab_prefixes') }}
      </button>
      <button
        type="button"
        :class="['tab-btn', { active: activeSubTab === 'subscribers' }]"
        @click="activeSubTab = 'subscribers'"
      >
        {{ t('ipam.tab_subscribers') }}
      </button>
      <button
        type="button"
        :class="['tab-btn', { active: activeSubTab === 'sync' }]"
        @click="activeSubTab = 'sync'"
      >
        {{ t('ipam.tab_sync') }}
      </button>
      <button
        type="button"
        :class="['tab-btn', { active: activeSubTab === 'bandwidth' }]"
        @click="activeSubTab = 'bandwidth'; fetchBandwidthProfiles()"
      >
        ⚡ {{ t('ipam.tab_bandwidth', 'Planes de Ancho de Banda (QoS)') }}
      </button>
    </nav>

    <!-- Contenido 1: Tabla de Prefijos -->
    <section v-if="activeSubTab === 'prefixes'">
      <IpamPrefixTable
        @open-ip-grid="(pfx) => (selectedGridPrefix = pfx)"
        @open-corporate-modal="corporateModalOpen = true"
      />
    </section>

    <!-- Contenido 2: Abonados FTTH -->
    <section v-if="activeSubTab === 'subscribers'" class="subscribers-section">
      <header class="section-toolbar">
        <h3>{{ t('ipam.subscribers_list_title') }}</h3>
        <div style="display: flex; gap: 8px;">
          <button
            id="btn-simulate-dhcp-subscribers"
            type="button"
            class="btn-rg btn-rg--purple"
            :disabled="isSimulatingDhcp"
            @click="handleSimulateFromDhcp"
          >
            {{ isSimulatingDhcp ? '⏳ Simulando...' : '🔄 Importar / Simular desde DHCP' }}
          </button>
          <button type="button" class="btn-rg btn-rg--cyan" @click="newSubscriberModalOpen = true">
            {{ t('ipam.btn_register_subscriber') }}
          </button>
        </div>
      </header>

      <div class="table-scroll-wrapper">
        <table class="rg-table">
          <thead>
            <tr>
              <th scope="col">{{ t('ipam.th_customer') }} / Serial ONU</th>
              <th scope="col">{{ t('ipam.th_type_proto') }}</th>
              <th scope="col">IPv4 / Sesión Emparejada</th>
              <th scope="col">{{ t('ipam.th_pon_box') }}</th>
              <th scope="col">{{ t('ipam.th_onu_mode') }}</th>
              <th scope="col">{{ t('ipam.th_reachability') }}</th>
              <th scope="col">{{ t('ipam.th_gps') }}</th>
              <th scope="col">{{ t('ipam.th_actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="ipamStore.customerServices.length === 0">
              <td colspan="8" class="empty-state-cell">
                {{ t('ipam.empty_subscribers') }}
              </td>
            </tr>
            <tr v-for="sub in ipamStore.customerServices" :key="sub.id" class="table-row">
              <td>
                <div class="font-bold">{{ sub.customer_name || sub.endpoint_identifier }}</div>
                <div v-if="sub.onu_serial_number || sub.device_serial" class="font-mono text-xs text-cyan">
                  ONU: {{ sub.onu_serial_number || sub.device_serial }}
                </div>
              </td>
              <td>
                <span class="badge-type">{{ sub.service_type }}</span>
              </td>
              <td class="font-mono">
                <div v-if="sub.assigned_ipv4" class="pair-badge pair-badge--ok">
                  🌐 {{ sub.assigned_ipv4 }}
                </div>
                <div v-else class="pair-badge pair-badge--unpaired">
                  ⚠️ Sin IP emparejada
                </div>
                <div v-if="sub.onu_mac_address" class="text-xs text-muted">
                  MAC: {{ sub.onu_mac_address }}
                </div>
              </td>
              <td>{{ sub.pon_port || 'S/N' }} / {{ sub.optical_box || 'S/N' }}</td>
              <td>
                <span
                  :class="[
                    'mode-pill',
                    sub.onu_mode === 'ROUTER' ? 'mode--router' : 'mode--bridge',
                  ]"
                >
                  {{ sub.onu_mode }}
                </span>
              </td>
              <td>
                <span
                  :class="[
                    'status-pill',
                    sub.last_reachability_status === 'ONLINE' ? 'pill--green' : 'pill--red',
                  ]"
                >
                  ● {{ sub.last_reachability_status }}
                </span>
              </td>
              <td>
                <span
                  v-if="sub.latitude && sub.longitude"
                  class="geo-badge geo-badge--ok font-mono"
                  :title="`Lat: ${sub.latitude}, Lng: ${sub.longitude}`"
                >
                  📍 {{ Number(sub.latitude).toFixed(4) }}, {{ Number(sub.longitude).toFixed(4) }}
                </span>
                <span v-else class="geo-badge geo-badge--none font-mono">
                  {{ t('ipam.no_coords') }}
                </span>
              </td>
              <td>
                <div style="display: flex; gap: 4px; align-items: center;">
                  <button
                    :id="`btn-pair-subscriber-${sub.id}`"
                    type="button"
                    class="btn-rg btn-rg--cyan btn-sm"
                    title="Emparejar ONU con Lease DHCP, Sesión PPPoE o IP IPAM"
                    @click="openPairSubscriberModal(sub)"
                  >
                    🔗 Emparejar
                  </button>
                  <button
                    type="button"
                    class="btn-row-geo"
                    :aria-label="`Cambiar o agregar ubicación GPS de ${sub.customer_name}`"
                    @click="openLocationModal(sub)"
                  >
                    📍 {{ t('ipam.btn_location') }}
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--amber btn-sm"
                    title="Suspender servicio en RouterOS"
                    @click="handleIsolateService(sub)"
                  >
                    🔒
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--green btn-sm"
                    title="Restaurar servicio en RouterOS"
                    @click="handleRestoreService(sub)"
                  >
                    🟢
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--cyan btn-sm"
                    title="Cambiar Plan de Ancho de Banda QoS"
                    @click="openChangeRateLimitModal(sub)"
                  >
                    ⚡ Plan
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--purple btn-sm"
                    title="Ver Script de Cola Simple RouterOS"
                    @click="handleShowSubscriberQueueScript(sub)"
                  >
                    📜 Queue
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Contenido 2.5: Planes de Ancho de Banda (QoS) -->
    <section v-if="activeSubTab === 'bandwidth'" class="subscribers-section bandwidth-section">
      <header class="section-toolbar">
        <div>
          <h3>⚡ Planes de Ancho de Banda y Calidad de Servicio (QoS)</h3>
          <p class="section-subtitle">Gestión centralizada de límites de bajada/subida, ráfagas (Burst) y colas PCQ.</p>
        </div>
        <button type="button" class="btn-rg btn-rg--cyan" @click="openCreateBandwidthModal">
          ➕ Nuevo Perfil QoS
        </button>
      </header>

      <div class="table-scroll-wrapper">
        <table class="rg-table font-tabular">
          <thead>
            <tr>
              <th scope="col">Nombre del Plan</th>
              <th scope="col">Bajada (Down)</th>
              <th scope="col">Subida (Up)</th>
              <th scope="col">Ráfaga (Burst Down/Up)</th>
              <th scope="col">Prioridad</th>
              <th scope="col">Tipo de Cola</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoadingBandwidth">
              <td colspan="7" class="empty-state-cell">Cargando perfiles QoS...</td>
            </tr>
            <tr v-else-if="bandwidthProfiles.length === 0">
              <td colspan="7" class="empty-state-cell">No hay perfiles de ancho de banda configurados.</td>
            </tr>
            <tr v-for="prof in bandwidthProfiles" :key="prof.id" class="table-row">
              <td class="font-bold text-cyan">{{ prof.name }}</td>
              <td class="font-mono">{{ (prof.rate_down_kbps / 1024).toFixed(1) }} Mbps</td>
              <td class="font-mono">{{ (prof.rate_up_kbps / 1024).toFixed(1) }} Mbps</td>
              <td class="font-mono text-muted">
                {{ prof.burst_down_kbps ? `${(prof.burst_down_kbps / 1024).toFixed(1)}M` : '—' }} /
                {{ prof.burst_up_kbps ? `${(prof.burst_up_kbps / 1024).toFixed(1)}M` : '—' }}
              </td>
              <td><span class="badge-type">P{{ prof.priority || 8 }}</span></td>
              <td class="font-mono text-xs">{{ prof.queue_type }}</td>
              <td>
                <div style="display: flex; gap: 4px;">
                  <button
                    type="button"
                    class="btn-rg btn-rg--cyan btn-sm"
                    title="Editar perfil"
                    @click="openEditBandwidthModal(prof)"
                  >
                    ✏️ Editar
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--purple btn-sm"
                    title="Ver script RouterOS v7"
                    @click="handleShowBandwidthProfileScript(prof)"
                  >
                    📜 Script
                  </button>
                  <button
                    type="button"
                    class="btn-rg btn-rg--red btn-sm"
                    title="Eliminar perfil"
                    @click="handleDeleteBandwidthProfile(prof)"
                  >
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Contenido 3: Sincronización MikroTik -->
    <section v-if="activeSubTab === 'sync'" class="sync-section">
      <div class="sync-card">
        <h3>{{ t('ipam.sync_title') }}</h3>
        <p class="sync-desc">
          {{ t('ipam.sync_desc') }}
        </p>

        <div class="form-row-sync">
          <select v-model="selectedSyncRouterId" class="rg-select select-lg">
            <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
              {{ r.display_name }} ({{ r.ip_address }}) — {{ r.network_role }}
            </option>
          </select>

          <button
            type="button"
            class="btn-rg btn-rg--cyan btn-lg"
            :disabled="isSyncing || !selectedSyncRouterId"
            @click="handleSyncMikrotik"
          >
            {{ isSyncing ? t('ipam.syncing') : `🚀 ${t('ipam.btn_sync_single')}` }}
          </button>

          <button
            type="button"
            class="btn-rg btn-rg--purple btn-lg"
            :disabled="isSyncing"
            @click="handleSyncAllMikrotik"
          >
            {{ isSyncing ? t('ipam.syncing') : `🌐 ${t('ipam.btn_sync_all')}` }}
          </button>
        </div>


        <div v-if="syncResult" class="sync-result-box">
          <h4>Resultado de la Sincronización:</h4>
          <p>{{ syncResult.message }}</p>
          <div class="result-counters">
            <span
              >Prefijos descubiertos: <strong>{{ syncResult.synced_prefixes }}</strong></span
            >
            <span
              >IPs descubiertas: <strong>{{ syncResult.synced_ips }}</strong></span
            >
          </div>
        </div>
      </div>
    </section>

    <!-- Modales -->
    <IpamIpGridModal
      v-if="selectedGridPrefix"
      :prefix="selectedGridPrefix"
      @close="selectedGridPrefix = null"
    />

    <CorporateIpv6ManagerModal v-if="corporateModalOpen" @close="corporateModalOpen = false" />

    <!-- Modal Emparejar Red de Abonado (DHCP / PPPoE / IPAM) -->
    <div
      v-if="pairModalOpen"
      id="modal-pair-subscriber"
      class="rg-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-pair-subscriber-title"
    >
      <div class="rg-modal">
        <header class="modal-header">
          <h3 id="modal-pair-subscriber-title">
            🔗 Emparejar Red de Abonado FTTH ({{ selectedSubForPair?.customer_name || selectedSubForPair?.endpoint_identifier }})
          </h3>
          <button type="button" class="btn-close" @click="pairModalOpen = false">✕</button>
        </header>

        <form class="modal-body" @submit.prevent="handleSavePairSubscriber">
          <p class="sub-target-info">
            MAC WAN ONU:
            <strong class="font-mono text-cyan">
              {{ selectedSubForPair?.onu_mac_address || pairForm.onu_mac_address || 'S/M' }}
            </strong>
            • Caja NAP:
            <strong class="font-mono">{{ selectedSubForPair?.optical_box || 'S/N' }}</strong>
            <span v-if="liveCandidates?.access_router_name">
              • Nodo Físico L2: <strong>{{ liveCandidates.access_router_name }}</strong>
            </span>
            <span v-if="liveCandidates?.router_name">
              • Cabecera BNG/DHCP:
              <strong class="text-green">{{ liveCandidates.router_name }}</strong>
              <span v-if="liveCandidates.auto_switched_bng" class="badge-type">Auto-detectado</span>
            </span>
          </p>

          <div v-if="pairSuccessMsg" class="banner banner--success mb-3">{{ pairSuccessMsg }}</div>
          <div v-if="pairErrorMsg" class="banner banner--error mb-3">{{ pairErrorMsg }}</div>

          <!-- Selector de Router Cabecera BNG / Servidor DHCP-PPPoE (Soporte Bridge L2 r3 -> BNG r111) -->
          <div class="form-group mb-3">
            <label for="pair-bng-router-select">
              🏢 Router Cabecera BNG / Servidor DHCP-PPPoE (Donde vive el Lease DHCP o Secreto PPPoE)
            </label>
            <select
              id="pair-bng-router-select"
              v-model="pairForm.bng_router_id"
              class="rg-input"
              @change="handleChangeBngRouter"
            >
              <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
                {{ r.display_name }} ({{ r.ip_address }})
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pair-proto-select">Protocolo de Servicio del ISP *</label>
              <select id="pair-proto-select" v-model="pairForm.service_type" class="rg-input">
                <option value="DHCP">DHCP (Reserva Estática por MAC en Servidor DHCP)</option>
                <option value="PPPOE">PPPoE (Secreto PPPoE en BRAS + Caller-ID MAC)</option>
                <option value="STATIC">IP Estática (Asignación Manual / Pool IPAM)</option>
              </select>
            </div>
            <div class="form-group w-30">
              <label for="pair-onu-mode">Modo ONU</label>
              <select id="pair-onu-mode" v-model="pairForm.onu_mode" class="rg-input">
                <option value="ROUTER">ROUTER (NAT)</option>
                <option value="BRIDGE">BRIDGE</option>
              </select>
            </div>
          </div>

          <!-- Selector en vivo para ISPs con DHCP -->
          <div v-if="pairForm.service_type === 'DHCP'" class="form-group mb-3">
            <label for="pair-dhcp-lease-select">
              🔍 Leases DHCP Activos en {{ liveCandidates?.router_name || 'Router BNG' }} ({{ liveCandidates?.dhcp_leases.length || 0 }} detectados)
            </label>
            <select
              id="pair-dhcp-lease-select"
              :value="selectedDhcpLeaseIp"
              class="rg-input font-mono"
              @change="handleSelectDhcpCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione un Lease DHCP activo o elija/escriba IP abajo para crear reserva --</option>
              <option
                v-for="lease in liveCandidates?.dhcp_leases || []"
                :key="`${lease.address}-${lease.mac_address}`"
                :value="lease.address"
              >
                {{ lease.address }} — MAC: {{ lease.mac_address || 'S/M' }} — {{ lease.host_name || lease.comment || lease.status || 'bound' }}
              </option>
            </select>
          </div>

          <!-- Selector en vivo para ISPs con PPPoE -->
          <div v-if="pairForm.service_type === 'PPPOE'" class="form-group mb-3">
            <label for="pair-pppoe-session-select">
              🔍 Sesiones / Secretos PPPoE en {{ liveCandidates?.router_name || 'Router BNG' }} ({{ liveCandidates?.pppoe_sessions.length || 0 }} detectados)
            </label>
            <select
              id="pair-pppoe-session-select"
              :value="selectedPppoeSessionName"
              class="rg-input font-mono"
              @change="handleSelectPppoeCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione una Sesión/Secreto PPPoE existente o cree uno nuevo abajo --</option>
              <option
                v-for="ppp in liveCandidates?.pppoe_sessions || []"
                :key="`${ppp.source}-${ppp.name}`"
                :value="ppp.name"
              >
                [{{ ppp.source === 'active' ? 'ACTIVA' : 'SECRET' }}] {{ ppp.name }} — IP: {{ ppp.address || 'Dinámica' }} — Caller: {{ ppp.caller_id || '—' }}
              </option>
            </select>
          </div>

          <!-- Selector de Pool IPAM (Disponible para DHCP con reserva nueva, PPPoE con IP fija o IP Estática) -->
          <div v-if="liveCandidates?.ipam_addresses?.length" class="form-group mb-3">
            <label for="pair-ipam-address-select">
              🔍 Seleccionar IPv4 del Pool IPAM ({{ liveCandidates.ipam_addresses.length }} registradas)
            </label>
            <select
              id="pair-ipam-address-select"
              v-model="pairForm.assigned_ipv4"
              class="rg-input font-mono"
            >
              <option value="">-- Seleccione una IP del Pool IPAM o escríbala manualmente abajo --</option>
              <option
                v-for="ipItem in liveCandidates.ipam_addresses"
                :key="ipItem.id"
                :value="ipItem.address.split('/')[0]"
              >
                {{ ipItem.address }} ({{ ipItem.status }}) — {{ ipItem.description || 'IPAM' }}
              </option>
            </select>
          </div>

          <div v-if="pairForm.service_type === 'PPPOE'" class="form-row">
            <div class="form-group flex-1">
              <label for="pair-pppoe-user">Usuario PPPoE (Pre-configurado en ONU) *</label>
              <input
                id="pair-pppoe-user"
                v-model="pairForm.pppoe_username"
                class="rg-input font-mono"
                placeholder="Ej: cliente_ftth_01"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-pppoe-password">Contraseña PPPoE (Para crear/actualizar `/ppp/secret`)</label>
              <input
                id="pair-pppoe-password"
                v-model="pairForm.pppoe_password"
                type="password"
                class="rg-input font-mono"
                placeholder="Dejar vacío si el secret ya existe"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pair-assigned-ipv4">Dirección IPv4 Asignada / Reservada *</label>
              <input
                id="pair-assigned-ipv4"
                v-model="pairForm.assigned_ipv4"
                class="rg-input font-mono"
                placeholder="Ej: 10.250.3.55"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-onu-mac">MAC WAN de la ONU (Reserva DHCP / Caller-ID PPPoE) *</label>
              <input
                id="pair-onu-mac"
                v-model="pairForm.onu_mac_address"
                class="rg-input font-mono"
                placeholder="AA:BB:CC:11:22:33"
                required
              />
            </div>
          </div>

          <div class="form-group mt-2 mb-2">
            <label class="checkbox-inline" for="chk-provision-mikrotik">
              <input
                id="chk-provision-mikrotik"
                v-model="pairForm.provision_on_router"
                type="checkbox"
              />
              <span>
                ⚡ Aprovisionar automáticamente en MikroTik (Crear Reserva Estática DHCP o `/ppp/secret` con `caller-id` MAC)
              </span>
            </label>
          </div>

          <footer class="modal-footer">
            <button
              type="button"
              class="btn-rg btn-rg--secondary"
              @click="pairModalOpen = false"
            >
              Cancelar
            </button>
            <button
              id="btn-save-pair-subscriber"
              type="submit"
              class="btn-rg btn-rg--cyan"
              :disabled="isSavingPair"
            >
              {{ isSavingPair ? '⏳ Emparejando...' : '🔗 Guardar Emparejamiento' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Registrar Abonado -->
    <div v-if="newSubscriberModalOpen" class="rg-modal-backdrop" role="dialog" aria-modal="true">
      <div class="rg-modal">
        <header class="modal-header">
          <h3>Registrar Nuevo Servicio FTTH</h3>
          <button type="button" class="btn-close" @click="newSubscriberModalOpen = false">✕</button>
        </header>
        <form class="modal-body" @submit.prevent="handleCreateSubscriber">
          <div class="form-group mb-3">
            <label for="sub-r">Router de Acceso / BRAS</label>
            <select id="sub-r" v-model="newSubscriber.router_id" class="rg-input" required>
              <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
                {{ r.display_name }} ({{ r.ip_address }})
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-name">Identificador / Nombre del Cliente *</label>
              <input
                id="sub-name"
                v-model="newSubscriber.customer_name"
                class="rg-input"
                placeholder="Ej: CLI-008492"
                required
              />
            </div>
            <div class="form-group w-30">
              <label for="sub-type">Protocolo WAN</label>
              <select id="sub-type" v-model="newSubscriber.service_type" class="rg-input">
                <option value="DHCP">DHCP</option>
                <option value="PPPOE">PPPoE</option>
                <option value="STATIC">Estático (IPAM)</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div v-if="newSubscriber.service_type === 'PPPOE'" class="form-group flex-1">
              <label for="sub-user">Usuario PPPoE</label>
              <input
                id="sub-user"
                v-model="newSubscriber.pppoe_username"
                class="rg-input font-mono"
                placeholder="Ej: user_pppoe_01"
              />
            </div>
            <div class="form-group flex-1">
              <label for="sub-ipv4">IPv4 Asignada (DHCP Lease / IP Estática / PPPoE)</label>
              <input
                id="sub-ipv4"
                v-model="newSubscriber.assigned_ipv4"
                class="rg-input font-mono"
                placeholder="Ej: 10.250.3.55"
              />
            </div>
            <div class="form-group w-30">
              <label for="sub-mode">Modo ONU</label>
              <select id="sub-mode" v-model="newSubscriber.onu_mode" class="rg-input">
                <option value="ROUTER">ROUTER (NAT)</option>
                <option value="BRIDGE">BRIDGE</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-serial">Serial GPON de la ONU</label>
              <input
                id="sub-serial"
                v-model="newSubscriber.onu_serial_number"
                class="rg-input font-mono"
                placeholder="Ej: HWTC1234ABCD"
              />
            </div>
            <div class="form-group flex-1">
              <label for="sub-mac">MAC WAN / ONU</label>
              <input
                id="sub-mac"
                v-model="newSubscriber.onu_mac_address"
                class="rg-input font-mono"
                placeholder="AA:BB:CC:11:22:33"
              />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-pon">Puerto PON (OLT)</label>
              <input
                id="sub-pon"
                v-model="newSubscriber.pon_port"
                class="rg-input"
                placeholder="gpon-olt1/1/1"
              />
            </div>
            <div class="form-group flex-1">
              <label for="sub-box">Caja / Manga NAP</label>
              <input
                id="sub-box"
                v-model="newSubscriber.optical_box"
                class="rg-input"
                placeholder="NAP-01"
              />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-lat">Latitud GPS (Opcional)</label>
              <input
                id="sub-lat"
                v-model.number="newSubscriber.latitude"
                type="number"
                step="any"
                class="rg-input"
                placeholder="Ej: 10.480600"
              />
            </div>
            <div class="form-group flex-1">
              <label for="sub-lng">Longitud GPS (Opcional)</label>
              <input
                id="sub-lng"
                v-model.number="newSubscriber.longitude"
                type="number"
                step="any"
                class="rg-input"
                placeholder="Ej: -66.903600"
              />
            </div>
          </div>
          <footer class="modal-footer">
            <button
              type="button"
              class="btn-rg btn-rg--secondary"
              @click="newSubscriberModalOpen = false"
            >
              Cancelar
            </button>
            <button type="submit" class="btn-rg btn-rg--cyan">Registrar Servicio</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Cambiar Ubicación de Cliente -->
    <div v-if="locationModalOpen" class="rg-modal-backdrop" role="dialog" aria-modal="true">
      <div class="rg-modal rg-modal--sm">
        <header class="modal-header">
          <h3>📍 Ubicación Geográfica de Cliente</h3>
          <button type="button" class="btn-close" @click="locationModalOpen = false">✕</button>
        </header>
        <div class="modal-body">
          <p class="sub-target-info">
            Cliente: <strong>{{ selectedSubForLocation?.customer_name }}</strong>
            <span v-if="selectedSubForLocation?.pppoe_username" class="text-cyan font-mono">
              ({{ selectedSubForLocation.pppoe_username }})
            </span>
          </p>

          <div v-if="locationSuccessMsg" class="banner banner--success mb-3">
            {{ locationSuccessMsg }}
          </div>
          <div v-if="locationErrorMsg" class="banner banner--error mb-3">
            {{ locationErrorMsg }}
          </div>

          <div class="geo-actions-helper mb-3">
            <button
              type="button"
              class="btn-rg btn-rg--secondary btn-xs"
              :disabled="isLocatingGps"
              @click="getCurrentGpsLocation"
            >
              {{ isLocatingGps ? '⏳ Obteniendo GPS...' : '🎯 Mi Ubicación GPS Actual' }}
            </button>

            <button
              type="button"
              class="btn-rg btn-rg--secondary btn-xs"
              @click="inheritHeadendLocation"
            >
              🏢 Heredar de Cabecera
            </button>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="geo-lat">Latitud Decimal (-90 a 90)</label>
              <input
                id="geo-lat"
                v-model.number="editLocation.latitude"
                type="number"
                step="any"
                class="rg-input"
                placeholder="Ej: 10.480600"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="geo-lng">Longitud Decimal (-180 a 180)</label>
              <input
                id="geo-lng"
                v-model.number="editLocation.longitude"
                type="number"
                step="any"
                class="rg-input"
                placeholder="Ej: -66.903600"
                required
              />
            </div>
          </div>
        </div>
        <footer class="modal-footer">
          <button
            type="button"
            class="btn-rg btn-rg--secondary"
            @click="locationModalOpen = false"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="btn-rg btn-rg--cyan"
            :disabled="isSavingLocation"
            @click="handleSaveLocation"
          >
            {{ isSavingLocation ? 'Guardando...' : '💾 Guardar Ubicación' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal 1: Crear / Editar Perfil QoS -->
    <div v-if="isBandwidthModalOpen" class="modal-backdrop" role="dialog" aria-modal="true">
      <div class="modal-card">
        <header class="modal-header">
          <h3>{{ editingProfileId ? '✏️ Editar Perfil de Ancho de Banda' : '➕ Nuevo Perfil de Ancho de Banda QoS' }}</h3>
          <button type="button" class="btn-close" @click="isBandwidthModalOpen = false">✕</button>
        </header>
        <div class="modal-body form-grid">
          <label>
            <span>Nombre del Plan *</span>
            <input v-model="bandwidthForm.name" type="text" class="rg-input" placeholder="Ej: Plan Fibra 50M" required />
          </label>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <label>
              <span>Bajada (Kbps) *</span>
              <input v-model.number="bandwidthForm.rate_down_kbps" type="number" class="rg-input font-mono" required />
            </label>
            <label>
              <span>Subida (Kbps) *</span>
              <input v-model.number="bandwidthForm.rate_up_kbps" type="number" class="rg-input font-mono" required />
            </label>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <label>
              <span>Burst Down (Kbps)</span>
              <input v-model.number="bandwidthForm.burst_down_kbps" type="number" class="rg-input font-mono" />
            </label>
            <label>
              <span>Burst Up (Kbps)</span>
              <input v-model.number="bandwidthForm.burst_up_kbps" type="number" class="rg-input font-mono" />
            </label>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <label>
              <span>Prioridad (1-8)</span>
              <input v-model.number="bandwidthForm.priority" type="number" min="1" max="8" class="rg-input" />
            </label>
            <label>
              <span>Tipo de Cola</span>
              <input v-model="bandwidthForm.queue_type" type="text" class="rg-input" placeholder="pcq-download-default" />
            </label>
          </div>
        </div>
        <footer class="modal-footer">
          <button type="button" class="btn-rg btn-rg--secondary" @click="isBandwidthModalOpen = false">Cancelar</button>
          <button type="button" class="btn-rg btn-rg--cyan" @click="handleSaveBandwidthProfile">
            {{ editingProfileId ? '💾 Actualizar Perfil' : '🚀 Crear Perfil' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal 2: Visualizador de Script MikroTik -->
    <div v-if="isScriptModalOpen" class="modal-backdrop" role="dialog" aria-modal="true">
      <div class="modal-card">
        <header class="modal-header">
          <h3>{{ scriptTitle }}</h3>
          <button type="button" class="btn-close" @click="isScriptModalOpen = false">✕</button>
        </header>
        <div class="modal-body">
          <p class="section-subtitle">Comando RouterOS v7 generado para despliegue manual o auditoría:</p>
          <pre class="script-display font-mono">{{ generatedScript }}</pre>
        </div>
        <footer class="modal-footer">
          <button type="button" class="btn-rg btn-rg--secondary" @click="isScriptModalOpen = false">Cerrar</button>
          <button
            type="button"
            class="btn-rg btn-rg--cyan"
            @click="copyGeneratedScript"
          >
            📋 Copiar Script
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal 3: Cambiar Plan de Ancho de Banda (Rate Limit en Caliente) -->
    <div v-if="isChangeRateLimitModalOpen" class="modal-backdrop" role="dialog" aria-modal="true">
      <div class="modal-card">
        <header class="modal-header">
          <h3>⚡ Modificar Plan de Ancho de Banda (En Caliente)</h3>
          <button type="button" class="btn-close" @click="isChangeRateLimitModalOpen = false">✕</button>
        </header>
        <div class="modal-body">
          <p>
            Modificar los límites de velocidad del abonado
            <strong>{{ selectedServiceForRateLimit?.customer_name }}</strong> sin interrumpir la sesión física.
          </p>
          <label style="margin-top: 12px; display: block;">
            <span>Seleccionar Nuevo Plan QoS:</span>
            <select v-model="targetProfileIdForRateLimit" class="rg-select select-lg" style="width: 100%; margin-top: 6px;">
              <option v-for="p in bandwidthProfiles" :key="p.id" :value="p.id">
                {{ p.name }} ({{ (p.rate_down_kbps / 1024).toFixed(0) }}M / {{ (p.rate_up_kbps / 1024).toFixed(0) }}M)
              </option>
            </select>
          </label>
        </div>
        <footer class="modal-footer">
          <button type="button" class="btn-rg btn-rg--secondary" @click="isChangeRateLimitModalOpen = false">Cancelar</button>
          <button
            type="button"
            class="btn-rg btn-rg--cyan"
            :disabled="isSubmittingRateLimit || !targetProfileIdForRateLimit"
            @click="submitChangeRateLimit"
          >
            {{ isSubmittingRateLimit ? 'Aplicando...' : '⚡ Aplicar Cambio de Plan' }}
          </button>
        </footer>
      </div>
    </div>
  </main>
</template>

<style scoped>
  .script-display {
    background: #040812;
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 6px;
    padding: 12px;
    font-size: 0.85rem;
    color: #00e5ff;
    overflow-x: auto;
    white-space: pre-wrap;
    max-height: 240px;
  }

  .ipam-management-view {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 1.5rem;
    background: #080d1a;
    min-height: calc(100vh - 60px);
    min-height: calc(100dvh - 60px);
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .header-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .ipam-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .kpi-card {
    background: #0d1527;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .kpi-label {
    font-size: 0.75rem;
    color: #8da4be;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .kpi-value {
    font-size: 1.85rem;
    font-weight: 800;
    font-family: monospace;
  }
  .text-cyan {
    color: #00f3ff;
  }
  .text-green {
    color: #00ff88;
  }
  .text-purple {
    color: #c084fc;
  }
  .text-yellow {
    color: #ffaa00;
  }

  .ipam-tabs-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    border-bottom: 2px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 0.5rem;
  }

  .tab-btn {
    background: none;
    border: none;
    color: #8da4be;
    font-size: 0.95rem;
    font-weight: 700;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s;
  }

  .tab-btn.active {
    background: rgba(0, 243, 255, 0.15);
    color: #00f3ff;
  }

  .subscribers-section,
  .sync-section {
    background: #0d1527;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 1.25rem;
  }

  .section-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .section-toolbar h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #00f3ff;
  }

  .badge-type {
    background: rgba(255, 255, 255, 0.08);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
  }

  .font-mono {
    font-family: monospace;
  }
  .font-bold {
    font-weight: 700;
  }

  .mode-pill {
    font-size: 0.7rem;
    font-weight: bold;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
  }
  .mode--router {
    background: rgba(0, 243, 255, 0.2);
    color: #00f3ff;
  }
  .mode--bridge {
    background: rgba(255, 170, 0, 0.2);
    color: #ffaa00;
  }

  .status-pill {
    font-size: 0.75rem;
    font-weight: bold;
  }
  .pill--green {
    color: #00ff88;
  }
  .pill--red {
    color: #ff3366;
  }

  .sync-card {
    max-width: 650px;
  }

  .sync-card h3 {
    margin-top: 0;
    color: #00f3ff;
  }

  .sync-desc {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.4;
    margin-bottom: 1.5rem;
  }

  .form-row-sync {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .select-lg {
    flex: 1 1 220px;
    min-width: 0;
    padding: 0.65rem 0.85rem;
    font-size: 0.95rem;
  }

  .btn-lg {
    padding: 0.65rem 1.25rem;
    font-size: 0.95rem;
  }

  .sync-result-box {
    margin-top: 1.5rem;
    background: #060a12;
    border-left: 3px solid #00ff88;
    padding: 1rem;
    border-radius: 4px;
  }

  .sync-result-box h4 {
    margin: 0 0 0.5rem 0;
    color: #00ff88;
  }

  .result-counters {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: #cbd5e1;
  }

  .table-scroll-wrapper {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .rg-table {
    width: 100%;
    min-width: 680px;
    border-collapse: collapse;
    font-size: 0.82rem;
  }

  .rg-table th,
  .rg-table td {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    text-align: left;
  }

  .form-row {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .flex-1 {
    flex: 1;
    min-width: 0;
  }

  .w-30 {
    width: 30%;
    min-width: 120px;
  }

  @media (max-width: 768px) {
    .script-display {
    background: #040812;
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 6px;
    padding: 12px;
    font-size: 0.85rem;
    color: #00e5ff;
    overflow-x: auto;
    white-space: pre-wrap;
    max-height: 240px;
  }

  .ipam-management-view {
      padding: 0.85rem;
    }

    .form-row {
      flex-direction: column;
    }

    .w-30 {
      width: 100%;
    }
  }

  /* Estilos de Ubicación GPS de Clientes */
  .geo-badge {
    font-size: 0.72rem;
    padding: 3px 6px;
    border-radius: 4px;
    display: inline-block;
  }
  .geo-badge--ok {
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.3);
    color: #22d3ee;
  }
  .geo-badge--none {
    background: rgba(148, 163, 184, 0.08);
    border: 1px dashed rgba(148, 163, 184, 0.25);
    color: #64748b;
  }
  .btn-row-geo {
    background: transparent;
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-row-geo:hover {
    background: rgba(56, 189, 248, 0.15);
    color: #fff;
  }
  .pair-badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.74rem;
    font-weight: 700;
  }
  .pair-badge--ok {
    background: rgba(0, 255, 136, 0.14);
    border: 1px solid rgba(0, 255, 136, 0.35);
    color: #00ff88;
  }
  .pair-badge--unpaired {
    background: rgba(255, 170, 0, 0.14);
    border: 1px dashed rgba(255, 170, 0, 0.45);
    color: #ffaa00;
  }
  .rg-modal-backdrop,
  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1200;
    background: rgba(4, 8, 18, 0.82);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .rg-modal,
  .modal-card {
    background: #0d1527;
    border: 1px solid rgba(0, 243, 255, 0.28);
    border-radius: 10px;
    width: 100%;
    max-width: 640px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65);
    color: #f1f5f9;
  }
  .rg-modal--sm {
    max-width: 480px;
    width: 95%;
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .modal-header h3 {
    margin: 0;
    font-size: 1.05rem;
    color: #00f3ff;
  }
  .btn-close {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #94a3b8;
    border-radius: 6px;
    width: 30px;
    height: 30px;
    cursor: pointer;
  }
  .modal-body {
    padding: 1.25rem;
  }
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.65rem;
    padding: 0.9rem 1.25rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .form-group label {
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 600;
  }
  .rg-input,
  .rg-select {
    background: #060b16;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 6px;
    color: #f8fafc;
    padding: 0.55rem 0.75rem;
    font-size: 0.85rem;
    width: 100%;
  }
  .rg-input:focus,
  .rg-select:focus {
    outline: none;
    border-color: #00f3ff;
  }
  .sub-target-info {
    font-size: 0.85rem;
    color: #cbd5e1;
    margin-bottom: 0.75rem;
  }
  .geo-actions-helper {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .btn-xs {
    font-size: 0.75rem;
    padding: 4px 8px;
  }
  .mt-3 {
    margin-top: 0.75rem;
  }
  .mb-3 {
    margin-bottom: 0.75rem;
  }
</style>
