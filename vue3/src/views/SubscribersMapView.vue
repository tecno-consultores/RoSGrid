<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import OsmOnuMap from '@/components/inventory/OsmOnuMap.vue';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import type { SubscriberDeviceItem } from '@/types';

  const { t } = useI18n();

  const onus = ref<SubscriberDeviceItem[]>([]);
  const isLoading = ref<boolean>(false);
  const selectedOnuId = ref<string | null>(null);
  const searchQuery = ref<string>('');
  const statusFilter = ref<'ALL' | 'OPTIMAL' | 'DEGRADED' | 'DOWN'>('ALL');

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

      // Asignar telemetría efímera Zero-Metrics en memoria (specs/32 §5.2)
      onus.value = items.map((item, index) => {
        // En simulación efímera para demo/test de campo:
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
        const code = (o.customer_code || o.customer_name || '').toLowerCase();
        const box = (o.optical_box || '').toLowerCase();
        const pon = (o.pon_port || '').toLowerCase();
        return serial.includes(q) || code.includes(q) || box.includes(q) || pon.includes(q);
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
    selectedOnuId.value = onuId;
  }

  function handleVerifyOnu(onu: SubscriberDeviceItem) {
    selectedOnuId.value = onu.id;
    alert(
      `⚡ Iniciando verificación 1-Click para ONU: ${onu.onu_serial_number || onu.device_serial}`,
    );
  }

  function handleDiagnoseOnu(onu: SubscriberDeviceItem) {
    selectedOnuId.value = onu.id;
    alert(`🔬 Ejecutando diagnóstico 360° para ONU: ${onu.onu_serial_number || onu.device_serial}`);
  }

  onMounted(() => {
    loadSubscriberDevices();
  });
</script>

<template>
  <main
    class="subscribers-map-view"
    data-theme="noc-dark"
    role="main"
    aria-label="Mapa Exclusivo de Clientes y ONUs"
  >
    <!-- Encabezado Táctico & KPIs Zero-Metrics -->
    <header class="map-view-header">
      <div class="header-titles">
        <h1 class="view-title">🗺️ {{ t('subscribers_map.title') }}</h1>
        <p class="view-subtitle">{{ t('subscribers_map.subtitle') }}</p>
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

    <!-- Barra de Filtros y Búsqueda Rápida -->
    <div class="filter-toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          class="rg-search-input font-mono"
          :placeholder="t('subscribers_map.search_placeholder')"
          aria-label="Buscar ONUs por serial, código o caja"
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
    </div>

    <!-- Contenedor del Mapa y HUD Lateral Flotante -->
    <div class="map-stage">
      <OsmOnuMap
        :onus="filteredOnus"
        :selected-onu-id="selectedOnuId"
        :center-coordinates="[10.4806, -66.9036]"
        :zoom-level="12"
        @select-onu="handleSelectOnu"
        @verify-onu="handleVerifyOnu"
        @diagnose-onu="handleDiagnoseOnu"
      />

      <!-- Drawer Lateral de Detalles del Abonado -->
      <aside v-if="selectedOnu" class="onu-detail-drawer" aria-label="Detalles de la ONU">
        <div class="drawer-header">
          <div class="drawer-title-group">
            <span
              class="status-indicator-dot"
              :class="`dot--${selectedOnu.zero_metrics_state?.toLowerCase()}`"
            ></span>
            <h2 class="drawer-title font-mono">
              {{ selectedOnu.onu_serial_number || selectedOnu.device_serial }}
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
              selectedOnu.customer_name || selectedOnu.customer_code || 'N/A'
            }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.port') }}:</span>
            <span class="detail-val font-mono">{{ selectedOnu.pon_port || 'PON-1' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.box') }}:</span>
            <span class="detail-val font-mono">{{ selectedOnu.optical_box || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('subscribers_map.mode') }}:</span>
            <span class="detail-val">{{ selectedOnu.onu_mode }}</span>
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

          <div class="drawer-actions">
            <button
              type="button"
              class="btn-drawer-action btn--cyan"
              @click="handleVerifyOnu(selectedOnu)"
            >
              ⚡ Test 1-Click
            </button>
            <button
              type="button"
              class="btn-drawer-action btn--purple"
              @click="handleDiagnoseOnu(selectedOnu)"
            >
              🔬 Diagnóstico 360°
            </button>
          </div>
        </div>
      </aside>
    </div>
  </main>
</template>

<style scoped>
  .subscribers-map-view {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 64px);
    background: #060b13;
    color: #fff;
    padding: 1rem 1.5rem;
    box-sizing: border-box;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      Roboto,
      sans-serif;
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
    color: #00f3ff;
  }

  .view-subtitle {
    margin: 0.2rem 0 0;
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .kpi-ribbon {
    display: flex;
    gap: 0.75rem;
  }

  .kpi-card {
    background: #0d1628;
    border: 1px solid rgba(0, 243, 255, 0.2);
    border-radius: 8px;
    padding: 0.5rem 0.85rem;
    display: flex;
    flex-direction: column;
    min-width: 90px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .kpi-card:hover,
  .kpi-card.active {
    border-color: #00f3ff;
    background: #13223f;
  }

  .kpi-label {
    font-size: 0.7rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .kpi-value {
    font-size: 1.25rem;
    font-weight: 800;
    font-family: ui-monospace, SFMono-Regular, monospace;
  }

  .text-cyan {
    color: #00f3ff;
  }

  .text-green {
    color: #22c55e;
  }

  .text-orange {
    color: #f97316;
  }

  .text-red {
    color: #ef4444;
  }

  .filter-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
  }

  .search-box {
    position: relative;
    width: 320px;
  }

  .rg-search-input {
    width: 100%;
    min-height: 40px;
    background: #0d1628;
    border: 1px solid rgba(0, 243, 255, 0.3);
    color: #fff;
    padding: 0.5rem 2rem 0.5rem 0.85rem;
    border-radius: 6px;
    font-size: 0.85rem;
    box-sizing: border-box;
  }

  .rg-search-input:focus {
    outline: none;
    border-color: #00f3ff;
  }

  .btn-clear-search {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .filter-chips {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .chip-btn {
    min-height: 36px;
    background: #0d1628;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .chip-btn.active {
    background: rgba(0, 243, 255, 0.15);
    border-color: #00f3ff;
    color: #00f3ff;
  }

  .chip--green.active {
    border-color: #22c55e;
    color: #22c55e;
    background: rgba(34, 197, 94, 0.15);
  }

  .chip--orange.active {
    border-color: #f97316;
    color: #f97316;
    background: rgba(249, 115, 22, 0.15);
  }

  .chip--red.active {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
  }

  .map-stage {
    position: relative;
    flex: 1;
    min-height: 480px;
    border: 1px solid rgba(0, 243, 255, 0.2);
    border-radius: 8px;
    overflow: hidden;
  }

  /* Drawer Lateral Flotante */
  .onu-detail-drawer {
    position: absolute;
    top: 16px;
    right: 16px;
    bottom: 16px;
    width: 320px;
    background: rgba(9, 14, 23, 0.95);
    border: 1px solid #00f3ff;
    border-radius: 8px;
    z-index: 1000;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    padding: 1rem;
    box-sizing: border-box;
  }

  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .drawer-title-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .drawer-title {
    margin: 0;
    font-size: 1rem;
    color: #00f3ff;
  }

  .status-indicator-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .dot--optimal {
    background: #22c55e;
    box-shadow: 0 0 8px #22c55e;
  }

  .dot--degraded {
    background: #f97316;
    box-shadow: 0 0 8px #f97316;
  }

  .dot--down {
    background: #ef4444;
    box-shadow: 0 0 8px #ef4444;
  }

  .btn-close-drawer {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.1rem;
    cursor: pointer;
  }

  .drawer-content {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    font-size: 0.85rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
    padding-bottom: 0.35rem;
  }

  .detail-label {
    color: #94a3b8;
  }

  .detail-val {
    font-weight: 600;
  }

  .drawer-actions {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .btn-drawer-action {
    min-height: 42px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.85rem;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn--cyan {
    background: #00f3ff;
    color: #090e17;
  }

  .btn--purple {
    background: rgba(168, 85, 247, 0.2);
    border: 1px solid #a855f7;
    color: #c084fc;
  }
</style>
