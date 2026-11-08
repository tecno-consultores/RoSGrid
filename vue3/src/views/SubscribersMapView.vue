<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
  import UnifiedNetworkMap from '@/components/network/UnifiedNetworkMap.vue';
  import { useI18n } from '@/composables/useI18n';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
  import { http } from '@/api/httpClient';
  import type { OpticalBoxDetailItem, SubscriberDeviceItem, RouterItem } from '@/types';

  const { t } = useI18n();
  const authStore = useAuthStore();
  const fieldStore = useFieldOpsStore();

  const isIspMode = computed(() => authStore.isFeatureEnabled('isp_module_enabled'));

  const routers = ref<RouterItem[]>([]);
  const onus = ref<SubscriberDeviceItem[]>([]);
  const isLoading = ref<boolean>(false);
  const isSyncingDhcp = ref<boolean>(false);
  const feedbackMessage = ref<string>('');
  const feedbackType = ref<'success' | 'error'>('success');
  const selectedOnuId = ref<string | null>(null);
  const selectedBoxId = ref<string | null>(null);
  const selectedRouterId = ref<string | null>(null);
  const selectedBoxDetail = ref<OpticalBoxDetailItem | null>(null);
  const isLoadingBoxDetail = ref<boolean>(false);
  const searchQuery = ref<string>('');
  const statusFilter = ref<'ALL' | 'OPTIMAL' | 'DEGRADED' | 'DOWN'>('ALL');

  const dynamicCenterCoordinates = computed<[number, number]>(() => {
    for (const r of routers.value) {
      const lat = Number(r.latitude);
      const lng = Number(r.longitude);
      if (!Number.isNaN(lat) && !Number.isNaN(lng) && !(lat === 0 && lng === 0)) {
        return [lat, lng];
      }
    }
    return authStore.tenantHqCoordinates;
  });

  // Coordenadas en edición
  const editLat = ref<number | undefined>(undefined);
  const editLng = ref<number | undefined>(undefined);
  const isSavingCoords = ref(false);

  // Ping en vivo
  const isPinging = ref(false);
  const livePingResult = ref<{
    status: string;
    latency_ms?: number;
    msg: string;
    is_cached?: boolean;
    cache_ttl_remaining?: number;
    rca_device?: string | null;
    is_rca_suppressed?: boolean;
    lock_tech?: string;
  } | null>(null);

  async function loadRouters() {
    try {
      const res = await http.get<RouterItem[]>('/api/v1/inventory/routers');
      routers.value = Array.isArray(res.data) ? res.data : [];
    } catch {
      routers.value = [];
    }
  }

  // Sincronización real de leases DHCP desde MikroTik (Modo Empresa y Modo ISP)
  async function handleSyncDhcpClients() {
    try {
      isSyncingDhcp.value = true;
      feedbackMessage.value = '';
      const res = await http.post<{
        message: string;
        routers_polled: number;
        leases_found: number;
        created_count: number;
        updated_count: number;
      }>('/api/v1/subscriber-devices/sync-dhcp');
      feedbackType.value = 'success';
      feedbackMessage.value = res.data.message || t('subscribers_map.sync_success');
      await loadSubscriberDevices();
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value = err instanceof Error ? err.message : 'Error al sincronizar clientes DHCP';
    } finally {
      isSyncingDhcp.value = false;
    }
  }

  function calculateZeroMetrics(onu: SubscriberDeviceItem): 'OPTIMAL' | 'DEGRADED' | 'DOWN' {
    if (
      onu.last_reachability_status === 'OFFLINE' ||
      onu.status === 'SUSPENDED' ||
      (onu.packet_loss_pct !== undefined &&
        onu.packet_loss_pct !== null &&
        onu.packet_loss_pct > 20)
    ) {
      return 'DOWN';
    }

    const lat = onu.ping_latency_ms;
    const loss = onu.packet_loss_pct;
    if (
      (lat !== undefined && lat !== null && lat >= 40) ||
      (loss !== undefined && loss !== null && loss >= 1)
    ) {
      return 'DEGRADED';
    }

    return 'OPTIMAL';
  }

  async function loadSubscriberDevices() {
    try {
      isLoading.value = true;
      const res = await http.get<SubscriberDeviceItem[]>('/api/v1/subscriber-devices');
      const items = Array.isArray(res.data) ? res.data : [];

      onus.value = items.map((item, index) => {
        const simulatedLat =
          item.ping_latency_ms ??
          (item.last_reachability_status === 'OFFLINE' ? null : index % 4 === 1 ? 55 : 22);
        const simulatedLoss =
          item.packet_loss_pct ??
          (item.last_reachability_status === 'OFFLINE' ? 100 : index % 4 === 1 ? 5 : 0);

        const dev: SubscriberDeviceItem = {
          ...item,
          latitude:
            item.latitude !== undefined && item.latitude !== null
              ? Number(item.latitude)
              : undefined,
          longitude:
            item.longitude !== undefined && item.longitude !== null
              ? Number(item.longitude)
              : undefined,
          ping_latency_ms: simulatedLat,
          packet_loss_pct: simulatedLoss,
        };
        dev.zero_metrics_state = calculateZeroMetrics(dev);
        return dev;
      });
    } catch {
      onus.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  const filteredOnus = computed(() => {
    let list = onus.value;

    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase().trim();
      list = list.filter((o) => {
        const serial = (o.onu_serial_number || o.device_serial || '').toLowerCase();
        const code = (o.customer_code || o.customer_name || o.endpoint_identifier || '').toLowerCase();
        const ip = (o.assigned_ipv4 || '').toLowerCase();
        const box = (o.optical_box || '').toLowerCase();
        const pon = (o.pon_port || '').toLowerCase();
        return (
          serial.includes(q) ||
          code.includes(q) ||
          ip.includes(q) ||
          box.includes(q) ||
          pon.includes(q)
        );
      });
    }

    if (statusFilter.value !== 'ALL') {
      list = list.filter((o) => o.zero_metrics_state === statusFilter.value);
    }

    return list;
  });

  const selectedOnu = computed(() => {
    if (!selectedOnuId.value) return null;
    return onus.value.find((o) => o.id === selectedOnuId.value) || null;
  });

  watch(selectedOnu, (onu) => {
    if (onu) {
      editLat.value =
        onu.latitude !== null && onu.latitude !== undefined
          ? Number(onu.latitude)
          : undefined;
      editLng.value =
        onu.longitude !== null && onu.longitude !== undefined
          ? Number(onu.longitude)
          : undefined;
      livePingResult.value = null;
    }
  });

  // KPIs
  const totalCount = computed(() => onus.value.length);
  const optimalCount = computed(
    () => onus.value.filter((o) => o.zero_metrics_state === 'OPTIMAL').length,
  );
  const degradedCount = computed(
    () => onus.value.filter((o) => o.zero_metrics_state === 'DEGRADED').length,
  );
  const downCount = computed(
    () => onus.value.filter((o) => o.zero_metrics_state === 'DOWN').length,
  );

  function handleSelectOnu(onuId: string) {
    selectedBoxId.value = null;
    selectedBoxDetail.value = null;
    selectedRouterId.value = null;
    selectedOnuId.value = onuId;
  }

  function handleSelectRouter(routerId: string) {
    selectedOnuId.value = null;
    selectedBoxId.value = null;
    selectedBoxDetail.value = null;
    selectedRouterId.value = routerId;
  }

  async function handleSelectBox(boxId: string) {
    selectedOnuId.value = null;
    selectedBoxId.value = boxId;
    isLoadingBoxDetail.value = true;
    try {
      selectedBoxDetail.value = await fieldStore.fetchOpticalBoxDetail(boxId);
    } catch {
      feedbackMessage.value = 'Error al cargar detalles de la Caja NAP';
      feedbackType.value = 'error';
    } finally {
      isLoadingBoxDetail.value = false;
    }
  }

  async function handleLivePingTest(onu: SubscriberDeviceItem) {
    isPinging.value = true;
    livePingResult.value = null;
    try {
      const res = await http.post<{
        device_id: string;
        last_reachability_status: string;
        ping_latency_ms?: number;
        packet_loss_pct?: number;
        message: string;
        is_cached?: boolean;
        cache_ttl_remaining?: number;
        status?: string;
        root_cause_device_name?: string | null;
        operational_lock?: { technician_name?: string; minutes_ago?: number; is_locked_by_other?: boolean } | null;
      }>(`/api/v1/subscriber-devices/${onu.id}/ping`);

      livePingResult.value = {
        status: res.data.last_reachability_status,
        latency_ms: res.data.ping_latency_ms,
        msg: res.data.message,
        is_cached: res.data.is_cached,
        cache_ttl_remaining: res.data.cache_ttl_remaining,
        rca_device: res.data.root_cause_device_name,
        is_rca_suppressed: res.data.status === 'ROOT_CAUSE_SUPPRESSED',
        lock_tech: res.data.operational_lock?.technician_name,
      };
      onu.last_reachability_status = res.data.last_reachability_status;
      onu.ping_latency_ms = res.data.ping_latency_ms;
      onu.packet_loss_pct = res.data.packet_loss_pct;
      onu.zero_metrics_state = calculateZeroMetrics(onu);
    } catch (err: unknown) {
      livePingResult.value = {
        status: 'OFFLINE',
        latency_ms: undefined,
        msg: (err as Error)?.message || 'Sin respuesta ICMP desde MikroTik',
      };
    } finally {
      isPinging.value = false;
    }
  }


  async function handleSaveCoordinates() {
    if (!selectedOnu.value || editLat.value === undefined || editLng.value === undefined) return;
    isSavingCoords.value = true;
    try {
      await http.patch(`/api/v1/subscriber-devices/${selectedOnu.value.id}`, {
        latitude: editLat.value,
        longitude: editLng.value,
      });
      selectedOnu.value.latitude = editLat.value;
      selectedOnu.value.longitude = editLng.value;
      selectedOnu.value.is_custom_coordinates = true;
      feedbackMessage.value = 'Coordenadas personalizadas guardadas con éxito.';
      feedbackType.value = 'success';
      await loadSubscriberDevices();
    } catch (err: unknown) {
      feedbackMessage.value = (err as Error)?.message || 'Error al guardar coordenadas';
      feedbackType.value = 'error';
    } finally {
      isSavingCoords.value = false;
    }
  }

  async function handleResetToRouterCoords() {
    if (!selectedOnu.value) return;
    isSavingCoords.value = true;
    try {
      const res = await http.patch<SubscriberDeviceItem>(
        `/api/v1/subscriber-devices/${selectedOnu.value.id}`,
        { reset_to_router_coordinates: true },
      );
      selectedOnu.value.latitude = res.data.latitude;
      selectedOnu.value.longitude = res.data.longitude;
      selectedOnu.value.is_custom_coordinates = false;
      editLat.value =
        res.data.latitude !== null && res.data.latitude !== undefined
          ? Number(res.data.latitude)
          : undefined;
      editLng.value =
        res.data.longitude !== null && res.data.longitude !== undefined
          ? Number(res.data.longitude)
          : undefined;
      feedbackMessage.value = 'Coordenadas restablecidas a las de la sede/router asignador.';
      feedbackType.value = 'success';
      await loadSubscriberDevices();
    } catch (err: unknown) {
      feedbackMessage.value = (err as Error)?.message || 'Error al restablecer coordenadas';
      feedbackType.value = 'error';
    } finally {
      isSavingCoords.value = false;
    }
  }

  const isRefreshingMap = ref<boolean>(false);
  let mapAutoRefreshTimer: ReturnType<typeof setInterval> | null = null;

  async function handleRefreshSubscribersMap(): Promise<void> {
    if (isRefreshingMap.value) return;
    isRefreshingMap.value = true;
    try {
      await Promise.allSettled([
        loadSubscriberDevices(),
        loadRouters(),
        fieldStore.fetchOpticalBoxes(),
      ]);
    } finally {
      isRefreshingMap.value = false;
    }
  }

  // Control RBAC y estado para importación masiva de abonados por CSV (Spec 100)
  const canManageBulkSubscribers = computed(() => {
    const role = authStore.currentRole || authStore.user?.role || '';
    return role === 'SUPERADMIN_GLOBAL' || role === 'TENANT_ADMIN';
  });

  const isCsvModalOpen = ref(false);
  const selectedCsvFile = ref<File | null>(null);
  const isCsvDryRunLoading = ref(false);
  const isCsvCommitLoading = ref(false);
  const csvDryRunResult = ref<{
    total_rows: number;
    valid_rows_count: number;
    invalid_rows_count: number;
    can_proceed: boolean;
    rows: Array<{
      row_number: number;
      endpoint_identifier: string;
      onu_serial_number?: string | null;
      assigned_ipv4?: string | null;
      router_name: string;
      optical_box_name?: string | null;
      will_auto_create_box?: boolean;
      is_valid: boolean;
      errors: string[];
    }>;
  } | null>(null);

  const isBoxesCsvModalOpen = ref(false);
  const selectedBoxesCsvFile = ref<File | null>(null);
  const isBoxesCsvDryRunLoading = ref(false);
  const isBoxesCsvCommitLoading = ref(false);
  const boxesCsvDryRunResult = ref<{
    total_rows: number;
    valid_rows_count: number;
    invalid_rows_count: number;
    can_proceed: boolean;
    rows: Array<{
      row_number: number;
      box_code: string;
      router_name: string;
      capacity_ports: number;
      splitter_ratio: string;
      installation_type: string;
      input_power_dbm?: number | null;
      latitude: number;
      longitude: number;
      physical_location?: string | null;
      is_update: boolean;
      is_valid: boolean;
      errors: string[];
    }>;
  } | null>(null);

  async function handleDownloadSubscribersTemplate() {
    try {
      const res = await http.get<string>('/api/v1/subscriber-devices/template-csv');
      const blob = new Blob([String(res.data)], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'rosgrid-clientes-plantilla.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      feedbackType.value = 'error';
      feedbackMessage.value = 'Error al descargar la plantilla CSV de clientes.';
    }
  }

  function handleCsvFileSelected(ev: Event) {
    const input = ev.target as HTMLInputElement;
    selectedCsvFile.value = input.files?.[0] || null;
    csvDryRunResult.value = null;
  }

  async function handleRunSubscribersDryRun() {
    if (!selectedCsvFile.value) return;
    isCsvDryRunLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', selectedCsvFile.value);
      const res = await http.post<NonNullable<typeof csvDryRunResult.value>>(
        '/api/v1/subscriber-devices/import-csv/dry-run',
        formData,
      );
      csvDryRunResult.value = res.data;
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value =
        err instanceof Error ? err.message : 'Error al validar el archivo CSV.';
    } finally {
      isCsvDryRunLoading.value = false;
    }
  }

  async function handleCommitSubscribersCsv() {
    if (!csvDryRunResult.value || !csvDryRunResult.value.can_proceed) return;
    isCsvCommitLoading.value = true;
    try {
      const res = await http.post<{ imported_count: number; message: string }>(
        '/api/v1/subscriber-devices/import-csv/commit',
        { rows: csvDryRunResult.value.rows },
      );
      feedbackType.value = 'success';
      feedbackMessage.value = res.data.message;
      isCsvModalOpen.value = false;
      csvDryRunResult.value = null;
      selectedCsvFile.value = null;
      await loadSubscriberDevices();
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value =
        err instanceof Error ? err.message : 'Error al importar clientes por CSV.';
    } finally {
      isCsvCommitLoading.value = false;
    }
  }

  async function handleDownloadBoxesTemplate() {
    try {
      const res = await http.get<string>('/api/v1/optical-boxes/template-csv');
      const blob = new Blob([String(res.data)], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'rosgrid-cajas-nap-plantilla.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      feedbackType.value = 'error';
      feedbackMessage.value = 'Error al descargar la plantilla CSV de Cajas NAP.';
    }
  }

  function handleBoxesCsvFileSelected(ev: Event) {
    const input = ev.target as HTMLInputElement;
    selectedBoxesCsvFile.value = input.files?.[0] || null;
    boxesCsvDryRunResult.value = null;
  }

  async function handleRunBoxesDryRun() {
    if (!selectedBoxesCsvFile.value) return;
    isBoxesCsvDryRunLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', selectedBoxesCsvFile.value);
      const res = await http.post<NonNullable<typeof boxesCsvDryRunResult.value>>(
        '/api/v1/optical-boxes/import-csv/dry-run',
        formData,
      );
      boxesCsvDryRunResult.value = res.data;
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value =
        err instanceof Error ? err.message : 'Error al validar el archivo CSV de Cajas NAP.';
    } finally {
      isBoxesCsvDryRunLoading.value = false;
    }
  }

  async function handleCommitBoxesCsv() {
    if (!boxesCsvDryRunResult.value || !boxesCsvDryRunResult.value.can_proceed) return;
    isBoxesCsvCommitLoading.value = true;
    try {
      const res = await http.post<{ imported_count: number; updated_count?: number; message: string }>(
        '/api/v1/optical-boxes/import-csv/commit',
        { rows: boxesCsvDryRunResult.value.rows },
      );
      feedbackType.value = 'success';
      feedbackMessage.value = res.data.message;
      isBoxesCsvModalOpen.value = false;
      boxesCsvDryRunResult.value = null;
      selectedBoxesCsvFile.value = null;
      await Promise.all([
        fieldStore.fetchOpticalBoxes(),
        loadSubscriberDevices(),
      ]);
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value =
        err instanceof Error ? err.message : 'Error al importar Cajas NAP por CSV.';
    } finally {
      isBoxesCsvCommitLoading.value = false;
    }
  }

  onMounted(async () => {
    await handleRefreshSubscribersMap();
    mapAutoRefreshTimer = setInterval(() => {
      void handleRefreshSubscribersMap();
    }, 30000);
  });

  onUnmounted(() => {
    if (mapAutoRefreshTimer !== null) {
      clearInterval(mapAutoRefreshTimer);
      mapAutoRefreshTimer = null;
    }
  });
</script>

<template>
  <main
    class="subscribers-map-view"
    data-theme="noc-dark"
    role="main"
    :aria-label="isIspMode ? t('subscribers_map.title_isp') : t('subscribers_map.title_enterprise')"
  >
    <!-- Encabezado Táctico & KPIs Zero-Metrics (Bimodal) -->
    <header class="map-view-header">
      <div class="header-titles">
        <h1 class="view-title">
          🗺️ {{ isIspMode ? t('subscribers_map.title_isp') : t('subscribers_map.title_enterprise') }}
        </h1>
        <p class="view-subtitle">
          {{ isIspMode ? t('subscribers_map.subtitle_isp') : t('subscribers_map.subtitle_enterprise') }}
        </p>
      </div>

      <div class="kpi-ribbon" role="region" aria-label="Indicadores Zero-Metrics">
        <div class="kpi-card" @click="statusFilter = 'ALL'">
          <span class="kpi-label">{{ t('subscribers_map.total_onus') }}</span>
          <span class="kpi-value text-cyan">{{ totalCount }}</span>
        </div>
        <div
          class="kpi-card"
          :class="{ active: statusFilter === 'OPTIMAL' }"
          @click="statusFilter = 'OPTIMAL'"
        >
          <span class="kpi-label">🟢 {{ t('subscribers_map.optimal_count') }}</span>
          <span class="kpi-value text-green">{{ optimalCount }}</span>
        </div>
        <div
          class="kpi-card"
          :class="{ active: statusFilter === 'DEGRADED' }"
          @click="statusFilter = 'DEGRADED'"
        >
          <span class="kpi-label">🟠 {{ t('subscribers_map.degraded_count') }}</span>
          <span class="kpi-value text-orange">{{ degradedCount }}</span>
        </div>
        <div
          class="kpi-card"
          :class="{ active: statusFilter === 'DOWN' }"
          @click="statusFilter = 'DOWN'"
        >
          <span class="kpi-label">🔴 {{ t('subscribers_map.down_count') }}</span>
          <span class="kpi-value text-red">{{ downCount }}</span>
        </div>
      </div>
    </header>

    <!-- Banner de Notificación Táctica -->
    <div
      v-if="feedbackMessage"
      class="tactical-feedback-banner font-mono"
      :class="`feedback--${feedbackType}`"
      role="alert"
    >
      <span>{{ feedbackType === 'success' ? '⚡' : '⚠️' }} {{ feedbackMessage }}</span>
      <button
        type="button"
        class="btn-close-feedback"
        aria-label="Cerrar notificación"
        @click="feedbackMessage = ''"
      >
        ✕
      </button>
    </div>

    <!-- Barra de Filtros, Búsqueda Rápida y Acciones Bimodales -->
    <div class="filter-toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          class="rg-search-input font-mono"
          :placeholder="t('subscribers_map.search_placeholder')"
          aria-label="Buscar por serial, código o IP"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="btn-clear-search"
          aria-label="Limpiar búsqueda"
          @click="searchQuery = ''"
        >
          ✕
        </button>
      </div>

      <div class="filter-chips">
        <button
          type="button"
          class="chip-btn"
          :class="{ active: statusFilter === 'ALL' }"
          @click="statusFilter = 'ALL'"
        >
          {{ t('subscribers_map.filter_all') }}
        </button>
        <button
          type="button"
          class="chip-btn chip--green"
          :class="{ active: statusFilter === 'OPTIMAL' }"
          @click="statusFilter = 'OPTIMAL'"
        >
          {{ t('subscribers_map.filter_optimal') }}
        </button>
        <button
          type="button"
          class="chip-btn chip--orange"
          :class="{ active: statusFilter === 'DEGRADED' }"
          @click="statusFilter = 'DEGRADED'"
        >
          {{ t('subscribers_map.filter_degraded') }}
        </button>
        <button
          type="button"
          class="chip-btn chip--red"
          :class="{ active: statusFilter === 'DOWN' }"
          @click="statusFilter = 'DOWN'"
        >
          {{ t('subscribers_map.filter_down') }}
        </button>
      </div>

      <!-- Acciones de Sincronización Bimodal -->
      <div class="sync-actions">
        <button
          id="btn-subscribers-map-refresh"
          type="button"
          class="btn-refresh-map"
          :disabled="isRefreshingMap"
          aria-label="Refrescar datos del mapa"
          @click="handleRefreshSubscribersMap"
        >
          <span v-if="isRefreshingMap">⏳</span>
          <span v-else>🔄</span>
          {{ isRefreshingMap ? 'Refrescando...' : 'Refrescar' }}
        </button>
        <!-- Botón Modo Empresa / Común: Sincronizar leases DHCP reales desde MikroTik -->
        <button
          id="btn-sync-dhcp-clients"
          type="button"
          class="btn-sync-dhcp"
          :disabled="isSyncingDhcp"
          aria-label="Sincronizar Dispositivos DHCP"
          @click="handleSyncDhcpClients"
        >
          <span v-if="isSyncingDhcp">⏳ {{ t('subscribers_map.syncing_dhcp') }}</span>
          <span v-else>{{ t('subscribers_map.btn_sync_dhcp') }}</span>
        </button>
        <!-- Botón Carga Masiva CSV Clientes (Solo SUPERADMIN_GLOBAL y TENANT_ADMIN) -->
        <button
          v-if="canManageBulkSubscribers"
          id="btn-import-subscribers-csv"
          type="button"
          class="btn-sync-dhcp"
          aria-label="Importar Clientes CSV"
          @click="isCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_csv', '📂 Importar Clientes CSV') }}
        </button>
        <!-- Botón Carga Masiva CSV Cajas NAP (Hito 30.26 / Spec 103 & Spec 106) -->
        <button
          v-if="canManageBulkSubscribers"
          id="btn-import-optical-boxes-csv"
          type="button"
          class="btn-sync-dhcp"
          aria-label="Importar Cajas NAP CSV"
          @click="isBoxesCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_boxes_csv', '📦 Importar Cajas NAP CSV') }}
        </button>
      </div>
    </div>

    <!-- Contenedor del Mapa Cartográfico Unificado Multicapa (Routers, Cajas NAP y Clientes) -->
    <div class="map-stage">
      <UnifiedNetworkMap
        :mode="'subscribers'"
        :routers="routers"
        :optical-boxes="fieldStore.opticalBoxes"
        :subscribers="filteredOnus"
        :selected-id="selectedOnuId"
        :center-coordinates="dynamicCenterCoordinates"
        :zoom-level="12"
        @select-subscriber="handleSelectOnu"
        @select-box="handleSelectBox"
        @select-router="handleSelectRouter"
        @diagnose-subscriber="handleLivePingTest"
      />

      <!-- Drawer Lateral 1: Detalles del Dispositivo Seleccionado (Cliente FTTH o PC DHCP) -->
      <aside v-if="selectedOnu" class="onu-detail-drawer" aria-label="Detalles del Dispositivo">
        <div class="drawer-header">
          <div class="drawer-title-group">
            <span
              class="status-indicator-dot"
              :class="`dot--${selectedOnu.zero_metrics_state?.toLowerCase()}`"
            ></span>
            <h2 class="drawer-title font-mono">
              {{ selectedOnu.onu_serial_number || selectedOnu.device_serial || selectedOnu.assigned_ipv4 }}
            </h2>
          </div>
          <button
            type="button"
            class="btn-close-drawer"
            aria-label="Cerrar detalles"
            @click="selectedOnuId = null"
          >
            ✕
          </button>
        </div>

        <div class="drawer-content">
          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.client') }}:</span>
            <span class="detail-val">{{
              selectedOnu.customer_name || selectedOnu.customer_code || selectedOnu.endpoint_identifier || 'N/A'
            }}</span>
          </div>

          <div v-if="selectedOnu.assigned_ipv4" class="detail-row">
            <span class="detail-label">IPv4 Asignada:</span>
            <span class="detail-val font-mono text-cyan">{{ selectedOnu.assigned_ipv4 }}</span>
          </div>

          <div v-if="selectedOnu.onu_mac_address" class="detail-row">
            <span class="detail-label">MAC Address:</span>
            <span class="detail-val font-mono">{{ selectedOnu.onu_mac_address }}</span>
          </div>

          <div v-if="isIspMode" class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.port') }}:</span>
            <span class="detail-val font-mono">{{ selectedOnu.pon_port || 'PON-1' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ isIspMode ? t('subscribers_map.box') : 'Sede / Router' }}:</span>
            <span class="detail-val font-mono">{{ selectedOnu.optical_box || 'N/A' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.latency') }}:</span>
            <span class="detail-val font-mono text-cyan"
              >{{ selectedOnu.ping_latency_ms ?? 'N/A' }} ms</span
            >
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.packet_loss') }}:</span>
            <span class="detail-val font-mono text-orange"
              >{{ selectedOnu.packet_loss_pct ?? '0' }}%</span
            >
          </div>

          <!-- Ping 1-Click desde MikroTik -->
          <div class="drawer-ping-section">
            <button
              type="button"
              class="btn-drawer-action btn--cyan w-full"
              :disabled="isPinging"
              @click="handleLivePingTest(selectedOnu)"
            >
              <span v-if="isPinging">{{ t('subscribers_map.pinging') }}</span>
              <span v-else>{{ t('subscribers_map.btn_ping_1click') }}</span>
            </button>
            <div v-if="livePingResult" class="ping-feedback-box font-mono" :class="`live--${livePingResult.status.toLowerCase()}`">
              <span>{{ livePingResult.status }}: {{ livePingResult.latency_ms !== undefined ? `${livePingResult.latency_ms}ms` : 'Timeout' }}</span>
              <span v-if="livePingResult.is_cached" class="tag--custom">⚡ Caché ({{ livePingResult.cache_ttl_remaining }}s)</span>
              <small>{{ livePingResult.msg }}</small>
            </div>
          </div>

          <!-- Gestión y Edición de Coordenadas Geográficas -->
          <div class="drawer-coords-section">
            <div class="coords-status-badge">
              <span v-if="selectedOnu.is_custom_coordinates" class="tag--custom">📍 {{ t('subscribers_map.custom_coordinates') }}</span>
              <span v-else class="tag--inherited">🏢 {{ t('subscribers_map.inherited_from_router') }}</span>
            </div>

            <div class="coords-inputs-row">
              <div class="coord-field">
                <label>Lat:</label>
                <input v-model.number="editLat" type="number" step="0.000001" class="rg-coord-input font-mono" />
              </div>
              <div class="coord-field">
                <label>Lng:</label>
                <input v-model.number="editLng" type="number" step="0.000001" class="rg-coord-input font-mono" />
              </div>
            </div>

            <div class="coords-buttons">
              <button
                type="button"
                class="btn-coords-action btn--save"
                :disabled="isSavingCoords"
                @click="handleSaveCoordinates"
              >
                {{ t('subscribers_map.btn_save_coords') }}
              </button>
              <button
                type="button"
                class="btn-coords-action btn--reset"
                :disabled="isSavingCoords"
                @click="handleResetToRouterCoords"
              >
                {{ t('subscribers_map.btn_copy_router_coords') }}
              </button>
            </div>
          </div>
        </div>
      </aside>

      <!-- Drawer Lateral 2: Detalles de la Caja NAP Seleccionada (Modo ISP) -->
      <aside v-if="selectedBoxId && selectedBoxDetail" class="onu-detail-drawer" aria-label="Detalles de la Caja NAP">
        <div class="drawer-header">
          <div class="drawer-title-group">
            <span class="status-indicator-dot dot--optimal"></span>
            <h2 class="drawer-title font-mono">📦 {{ selectedBoxDetail.box_code }}</h2>
          </div>
          <button
            type="button"
            class="btn-close-drawer"
            aria-label="Cerrar detalles"
            @click="selectedBoxId = null; selectedBoxDetail = null"
          >
            ✕
          </button>
        </div>

        <div class="drawer-content">
          <div class="detail-row">
            <span class="detail-label">Ubicación:</span>
            <span class="detail-val">{{ selectedBoxDetail.physical_location || 'Sin especificar' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.ports_capacity') }}:</span>
            <span class="detail-val font-mono">{{ selectedBoxDetail.capacity_ports }} Puertos</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.splitter_ratio') }}:</span>
            <span class="detail-val font-mono">{{ selectedBoxDetail.splitter_ratio }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.input_power') }}:</span>
            <span class="detail-val font-mono text-cyan">{{ selectedBoxDetail.input_power_dbm ?? '--' }} dBm Pin</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Ocupación:</span>
            <span class="detail-val font-mono text-green">
              {{ selectedBoxDetail.occupied_ports_count }} / {{ selectedBoxDetail.capacity_ports }} ({{ selectedBoxDetail.available_ports_count }} libres)
            </span>
          </div>

          <!-- Matriz de Puertos 1 a Capacidad -->
          <div class="nap-ports-matrix-section">
            <h4 class="matrix-title">Matriz de Puertos</h4>
            <div class="ports-matrix-grid">
              <div
                v-for="port in selectedBoxDetail.ports"
                :key="port.port_number"
                class="matrix-port-badge"
                :class="port.is_occupied ? 'port--occupied' : 'port--free'"
                :title="port.is_occupied ? `Ocupado por ${port.subscriber_identifier || port.subscriber_id}` : 'Puerto Libre'"
              >
                <span class="p-num">{{ port.port_number }}</span>
                <span class="p-status">{{ port.is_occupied ? '●' : '○' }}</span>
              </div>
            </div>
          </div>

          <!-- Lista de Clientes Conectados a esta Caja -->
          <div class="nap-subscribers-list">
            <h4 class="matrix-title">Clientes Conectados ({{ selectedBoxDetail.subscribers.length }})</h4>
            <div v-if="selectedBoxDetail.subscribers.length === 0" class="empty-connected">
              No hay clientes asociados a esta caja aún.
            </div>
            <div v-else class="connected-items-scroll">
              <div
                v-for="sub in selectedBoxDetail.subscribers"
                :key="sub.id"
                class="connected-sub-item font-mono"
                @click="handleSelectOnu(sub.id)"
              >
                <span>Puerto {{ sub.optical_box_port ?? '1' }}: {{ sub.onu_serial_number || sub.device_serial }}</span>
                <span class="text-cyan">{{ sub.customer_code || sub.endpoint_identifier }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Modal Asistente de Carga Masiva CSV de Clientes (Spec 100) -->
    <div
      v-if="isCsvModalOpen"
      id="modal-import-subscribers-csv"
      class="rg-modal-backdrop"
      @click.self="isCsvModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="csv-modal-title">
        <header class="modal-header">
          <div>
            <h2 id="csv-modal-title" class="modal-title">
              {{ t('subscribers_map.modal_csv_title', '📂 Carga Masiva de Clientes / Abonados (CSV)') }}
            </h2>
            <p class="modal-subtitle">
              {{ t('subscribers_map.modal_csv_subtitle', 'Migre su cartera de clientes FTTH/DHCP validando formato, router y coordenadas GPS en seco antes de guardar.') }}
            </p>
          </div>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal de importación"
            @click="isCsvModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="modal-body">
          <div class="csv-actions-bar">
            <button
              id="btn-download-subscribers-csv-template"
              type="button"
              class="btn-secondary"
              @click="handleDownloadSubscribersTemplate"
            >
              {{ t('subscribers_map.btn_download_template', '⬇️ Descargar Plantilla CSV') }}
            </button>
            <div class="file-picker-wrapper">
              <input
                id="input-subscribers-csv-file"
                type="file"
                accept=".csv,text/csv"
                @change="handleCsvFileSelected"
              />
            </div>
            <button
              id="btn-run-subscribers-dry-run"
              type="button"
              class="btn-primary"
              :disabled="!selectedCsvFile || isCsvDryRunLoading"
              @click="handleRunSubscribersDryRun"
            >
              {{ isCsvDryRunLoading ? 'Validando...' : t('subscribers_map.btn_validate_dry_run', '🔍 Validar Archivo (Dry-Run)') }}
            </button>
          </div>

          <!-- Previsualización de Resultados Dry-Run -->
          <div v-if="csvDryRunResult" class="csv-preview-container">
            <div class="csv-summary-badges">
              <span class="summary-badge badge--total">
                Total: {{ csvDryRunResult.total_rows }}
              </span>
              <span class="summary-badge badge--valid">
                Válidas: {{ csvDryRunResult.valid_rows_count }}
              </span>
              <span class="summary-badge badge--invalid">
                Inválidas: {{ csvDryRunResult.invalid_rows_count }}
              </span>
            </div>

            <div class="csv-table-wrapper">
              <table class="csv-preview-table">
                <thead>
                  <tr>
                    <th>Fila</th>
                    <th>Endpoint / Código</th>
                    <th>Serial ONU</th>
                    <th>IPv4</th>
                    <th>Router</th>
                    <th>Caja NAP</th>
                    <th>Estado / Errores</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in csvDryRunResult.rows"
                    :key="row.row_number"
                    :class="{ 'row--invalid': !row.is_valid, 'row--valid': row.is_valid }"
                  >
                    <td>#{{ row.row_number }}</td>
                    <td class="font-mono">{{ row.endpoint_identifier }}</td>
                    <td class="font-mono">{{ row.onu_serial_number || '—' }}</td>
                    <td class="font-mono">{{ row.assigned_ipv4 || '—' }}</td>
                    <td>{{ row.router_name }}</td>
                    <td>
                      {{ row.optical_box_name || '—' }}
                      <span
                        v-if="row.is_valid && row.will_auto_create_box"
                        class="badge-auto-create-box"
                        :title="t('subscribers_map.badge_auto_create_box_hint', 'Esta Caja NAP no existe aún y se auto-creará automáticamente en PostgreSQL')"
                      >
                        ✨ {{ t('subscribers_map.badge_auto_create_box', 'Auto-creará Caja NAP') }}
                      </span>
                    </td>
                    <td>
                      <span v-if="row.is_valid" class="text-green">✓ Válido</span>
                      <span v-else class="text-red">✕ {{ row.errors.join('; ') }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="modal-footer">
              <button
                v-if="csvDryRunResult.can_proceed"
                id="btn-commit-subscribers-csv"
                type="button"
                class="btn-primary"
                :disabled="isCsvCommitLoading"
                @click="handleCommitSubscribersCsv"
              >
                {{ isCsvCommitLoading ? 'Importando...' : t('subscribers_map.btn_commit_import', { count: csvDryRunResult.valid_rows_count }) }}
              </button>
              <span v-else class="text-red font-semibold">
                ⚠️ Corrija los errores indicados en las filas en rojo para habilitar la importación.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Asistente de Carga Masiva CSV de Cajas NAP (Spec 103) -->
    <div
      v-if="isBoxesCsvModalOpen"
      id="modal-import-optical-boxes-csv"
      class="rg-modal-backdrop"
      @click.self="isBoxesCsvModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="boxes-csv-modal-title">
        <header class="modal-header">
          <div>
            <h2 id="boxes-csv-modal-title" class="modal-title">
              {{ t('subscribers_map.modal_boxes_csv_title', '📦 Carga Masiva de Cajas NAP (CSV Upsert)') }}
            </h2>
            <p class="modal-subtitle">
              {{ t('subscribers_map.modal_boxes_csv_subtitle', 'Cargue o actualice masivamente cajas de distribución óptica NAP validando router, splitter y coordenadas GPS con soporte Upsert.') }}
            </p>
          </div>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal de importación de cajas NAP"
            @click="isBoxesCsvModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="modal-body">
          <div class="csv-actions-bar">
            <button
              id="btn-download-optical-boxes-csv-template"
              type="button"
              class="btn-secondary"
              @click="handleDownloadBoxesTemplate"
            >
              {{ t('subscribers_map.btn_download_boxes_template', '⬇️ Descargar Plantilla Cajas NAP CSV') }}
            </button>
            <div class="file-picker-wrapper">
              <input
                id="input-optical-boxes-csv-file"
                type="file"
                accept=".csv,text/csv"
                @change="handleBoxesCsvFileSelected"
              />
            </div>
            <button
              id="btn-run-optical-boxes-dry-run"
              type="button"
              class="btn-primary"
              :disabled="!selectedBoxesCsvFile || isBoxesCsvDryRunLoading"
              @click="handleRunBoxesDryRun"
            >
              {{ isBoxesCsvDryRunLoading ? 'Validando...' : t('subscribers_map.btn_validate_boxes_dry_run', '🔍 Validar Cajas (Dry-Run)') }}
            </button>
          </div>

          <!-- Previsualización de Resultados Dry-Run Cajas NAP -->
          <div v-if="boxesCsvDryRunResult" class="csv-preview-container">
            <div class="csv-summary-badges">
              <span class="summary-badge badge--total">
                Total: {{ boxesCsvDryRunResult.total_rows }}
              </span>
              <span class="summary-badge badge--valid">
                Válidas: {{ boxesCsvDryRunResult.valid_rows_count }}
              </span>
              <span class="summary-badge badge--invalid">
                Inválidas: {{ boxesCsvDryRunResult.invalid_rows_count }}
              </span>
              <span class="summary-badge badge--upsert">
                {{ t('subscribers_map.summary_updates', { count: boxesCsvDryRunResult.rows.filter(r => r.is_update && r.is_valid).length }) }}
              </span>
            </div>

            <div class="csv-table-wrapper">
              <table class="csv-preview-table">
                <thead>
                  <tr>
                    <th>Fila</th>
                    <th>Código Caja</th>
                    <th>Router</th>
                    <th>Puertos / Splitter</th>
                    <th>Coordenadas GPS</th>
                    <th>Tipo / Ubicación</th>
                    <th>Acción / Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in boxesCsvDryRunResult.rows"
                    :key="row.row_number"
                    :class="{ 'row--invalid': !row.is_valid, 'row--valid': row.is_valid }"
                  >
                    <td>#{{ row.row_number }}</td>
                    <td class="font-mono">{{ row.box_code }}</td>
                    <td>{{ row.router_name }}</td>
                    <td>{{ row.capacity_ports }}p ({{ row.splitter_ratio }})</td>
                    <td class="font-mono text-xs">{{ row.latitude }}, {{ row.longitude }}</td>
                    <td>{{ row.installation_type }} {{ row.physical_location ? `• ${row.physical_location}` : '' }}</td>
                    <td>
                      <template v-if="row.is_valid">
                        <span v-if="row.is_update" class="badge-upsert">
                          🔄 {{ t('subscribers_map.badge_box_update', 'Actualizará') }}
                        </span>
                        <span v-else class="badge-create">
                          ✨ {{ t('subscribers_map.badge_box_create', 'Nueva') }}
                        </span>
                      </template>
                      <span v-else class="text-red">✕ {{ row.errors.join('; ') }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="modal-footer">
              <button
                v-if="boxesCsvDryRunResult.can_proceed"
                id="btn-commit-optical-boxes-csv"
                type="button"
                class="btn-primary"
                :disabled="isBoxesCsvCommitLoading"
                @click="handleCommitBoxesCsv"
              >
                {{ isBoxesCsvCommitLoading ? 'Importando...' : t('subscribers_map.btn_commit_boxes_import', { count: boxesCsvDryRunResult.valid_rows_count }) }}
              </button>
              <span v-else class="text-red font-semibold">
                ⚠️ Corrija los errores indicados en las filas en rojo para habilitar la importación.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
  .subscribers-map-view {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 64px);
    height: calc(100dvh - 64px);
    background: var(--rg-bg-canvas);
    color: var(--rg-text-primary);
    padding: 1rem 1.5rem;
    box-sizing: border-box;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .map-view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 0.85rem;
  }

  .header-titles {
    display: flex;
    flex-direction: column;
  }

  .view-title {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--rg-accent-cyan);
  }

  .view-subtitle {
    margin: 0.2rem 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .kpi-ribbon {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .kpi-card {
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    min-width: 90px;
  }

  .kpi-card.active {
    border-color: var(--rg-accent-cyan);
    background: var(--rg-bg-elevated);
  }

  .kpi-label {
    font-size: 0.7rem;
    color: var(--rg-text-muted);
  }

  .kpi-value {
    font-size: 1.25rem;
    font-weight: 800;
  }

  .tactical-feedback-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
  }

  .feedback--success {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #4ade80;
  }

  .feedback--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .btn-close-feedback {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
  }

  .filter-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 0.85rem;
  }

  .search-box {
    position: relative;
    flex: 1;
    max-width: 380px;
  }

  .rg-search-input {
    width: 100%;
    background: var(--rg-bg-input);
    border: 1px solid var(--rg-border-panel);
    border-radius: 6px;
    padding: 0.5rem 2rem 0.5rem 0.75rem;
    color: var(--rg-text-primary);
    font-size: 0.85rem;
  }

  .btn-clear-search {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--rg-text-muted);
    cursor: pointer;
  }

  .filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .chip-btn {
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-secondary);
    border-radius: 20px;
    padding: 0.35rem 0.75rem;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .chip-btn.active {
    background: var(--rg-bg-elevated);
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
  }

  .sync-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-sync-dhcp,
  .btn-refresh-map {
    background: var(--rg-btn-action-bg);
    border: 1px solid var(--rg-accent-cyan-border);
    color: var(--rg-accent-cyan);
    border-radius: 6px;
    padding: 0.45rem 0.85rem;
    font-size: 0.8rem;
    cursor: pointer;
    font-weight: 600;
  }

  .btn-simulate-dhcp {
    background: #1e1b4b;
    border: 1px solid #818cf8;
    color: #a5b4fc;
    border-radius: 6px;
    padding: 0.45rem 0.85rem;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .map-stage {
    position: relative;
    flex: 1;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--rg-border-panel);
  }

  /* Drawer Lateral */
  .onu-detail-drawer {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 320px;
    max-width: calc(100% - 20px);
    max-height: calc(100% - 20px);
    background: color-mix(in srgb, var(--rg-bg-surface) 94%, transparent);
    backdrop-filter: blur(8px);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-primary);
    border-radius: 8px;
    z-index: 1000;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 1rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  }

  @media (max-width: 768px) {
    .subscribers-map-view {
      height: auto;
      min-height: calc(100dvh - 110px);
      padding: 0.75rem;
    }

    .kpi-ribbon {
      width: 100%;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
    }

    .search-box {
      flex: 1 1 100%;
      max-width: 100%;
    }

    .map-stage {
      min-height: 400px;
    }

    .onu-detail-drawer {
      left: 8px;
      right: 8px;
      top: auto;
      bottom: 8px;
      width: auto;
      max-height: 65%;
    }
  }

  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
    margin-bottom: 0.75rem;
  }

  .drawer-title-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .status-indicator-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .dot--optimal { background: #22c55e; }
  .dot--degraded { background: #f97316; }
  .dot--down { background: #ef4444; }

  .drawer-title {
    font-size: 0.95rem;
    margin: 0;
    color: #00f3ff;
  }

  .btn-close-drawer {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    padding: 0.3rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .detail-label {
    color: #94a3b8;
  }

  .detail-val {
    font-weight: 600;
  }

  .drawer-ping-section {
    margin-top: 1rem;
  }

  .btn-drawer-action {
    padding: 0.5rem;
    border-radius: 4px;
    font-weight: 700;
    cursor: pointer;
    border: none;
  }

  .btn--cyan {
    background: #00f3ff;
    color: #000;
  }

  .ping-feedback-box {
    margin-top: 0.5rem;
    padding: 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
    display: flex;
    flex-direction: column;
  }

  .live--online {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid #22c55e;
  }

  .live--offline {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid #ef4444;
  }

  .drawer-coords-section {
    margin-top: 1.25rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .coords-status-badge {
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
  }

  .tag--custom { color: #00f3ff; font-weight: 700; }
  .tag--inherited { color: #94a3b8; }

  .coords-inputs-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .coord-field {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
  }

  .rg-coord-input {
    width: 100%;
    background: var(--rg-bg-input);
    border: 1px solid var(--rg-border-panel);
    border-radius: 4px;
    color: var(--rg-text-primary);
    padding: 0.25rem 0.4rem;
    font-size: 0.75rem;
  }

  .coords-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .btn-coords-action {
    flex: 1;
    padding: 0.35rem;
    border-radius: 4px;
    font-size: 0.7rem;
    cursor: pointer;
    border: none;
    font-weight: 600;
  }

  .btn--save {
    background: #22c55e;
    color: #000;
  }

  .btn--reset {
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  /* Matriz NAP */
  .nap-ports-matrix-section {
    margin-top: 1rem;
  }

  .matrix-title {
    font-size: 0.8rem;
    color: #00f3ff;
    margin-bottom: 0.4rem;
  }

  .ports-matrix-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.35rem;
  }

  .matrix-port-badge {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0.45rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: monospace;
  }

  .port--free {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #4ade80;
  }

  .port--occupied {
    background: rgba(0, 243, 255, 0.15);
    border: 1px solid #00f3ff;
    color: #00f3ff;
  }

  .nap-subscribers-list {
    margin-top: 1rem;
  }

  .connected-items-scroll {
    max-height: 140px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .connected-sub-item {
    background: #090e17;
    padding: 0.35rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
  }

  .connected-sub-item:hover {
    border: 1px solid #00f3ff;
  }

  .empty-connected {
    font-size: 0.75rem;
    color: #64748b;
  }

  .text-cyan { color: #00f3ff; }
  .text-green { color: #22c55e; }
  .text-orange { color: #f97316; }
  .text-red { color: #ef4444; }
  .w-full { width: 100%; }

  /* Modal de Importación Masiva CSV (Spec 100) */
  .rg-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(3, 7, 18, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 1rem;
    box-sizing: border-box;
  }

  .rg-modal {
    background: #090e17;
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    width: 100%;
    max-width: 860px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 243, 255, 0.1);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background: #0d1522;
  }

  .modal-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #00f3ff;
    margin: 0 0 0.25rem 0;
  }

  .modal-subtitle {
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 0;
  }

  .modal-body {
    padding: 1.25rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .csv-actions-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    background: var(--rg-bg-canvas);
    padding: 0.75rem 1rem;
    border: 1px dashed var(--rg-border-panel);
    border-radius: 6px;
  }

  .file-picker-wrapper input[type='file'] {
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .btn-primary {
    background: var(--rg-accent-cyan);
    color: var(--rg-bg-canvas);
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.82rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .btn-primary:hover:not(:disabled) {
    background: #38bdf8;
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 0.5rem 0.85rem;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #334155;
  }

  .csv-summary-badges {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
  }

  .summary-badge {
    padding: 0.25rem 0.65rem;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: monospace;
  }

  .badge--total {
    background: rgba(148, 163, 184, 0.15);
    border: 1px solid #64748b;
    color: #cbd5e1;
  }

  .badge--valid {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #4ade80;
  }

  .badge--invalid {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .csv-table-wrapper {
    max-height: 280px;
    overflow-y: auto;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    background: var(--rg-bg-canvas);
  }

  .csv-preview-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.75rem;
    text-align: left;
  }

  .csv-preview-table th {
    background: var(--rg-bg-elevated);
    padding: 0.5rem 0.65rem;
    color: var(--rg-text-primary);
    position: sticky;
    top: 0;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .csv-preview-table td {
    padding: 0.45rem 0.65rem;
    border-bottom: 1px solid var(--rg-border-grid);
    color: var(--rg-text-secondary);
  }

  .row--invalid {
    background: rgba(239, 68, 68, 0.08);
  }

  .row--valid {
    background: rgba(34, 197, 94, 0.04);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 1rem;
    padding-top: 0.5rem;
  }

  .badge--upsert {
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid #38bdf8;
    color: #38bdf8;
  }

  .badge-auto-create-box {
    display: inline-block;
    font-size: 0.65rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    background: rgba(168, 85, 247, 0.2);
    border: 1px solid rgba(168, 85, 247, 0.5);
    color: #c084fc;
    margin-left: 0.4rem;
    font-weight: 500;
  }

  .badge-upsert {
    display: inline-block;
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.2);
    border: 1px solid rgba(56, 189, 248, 0.5);
    color: #38bdf8;
    font-weight: 500;
  }

  .badge-create {
    display: inline-block;
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    background: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.5);
    color: #4ade80;
    font-weight: 500;
  }
</style>
