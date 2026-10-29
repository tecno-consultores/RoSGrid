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

  const activeSubTab = ref<'prefixes' | 'subscribers' | 'sync'>('prefixes');
  const selectedGridPrefix = ref<IPAMPrefix | null>(null);
  const corporateModalOpen = ref(false);

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
    service_type: 'PPPOE',
    auth_backend: 'LOCAL_SECRET',
    pppoe_username: '',
    onu_mode: 'ROUTER',
    onu_mac_address: '',
    onu_serial_number: '',
    pon_port: 'gpon-olt1/1/1',
    optical_box: 'NAP-01',
  });

  onMounted(async () => {
    await ipamStore.fetchVrfs();
    await ipamStore.fetchPrefixes();
    await ipamStore.fetchCustomerServices();
    await inventoryStore.fetchRouters();
    if (inventoryStore.routers.length > 0) {
      selectedSyncRouterId.value = inventoryStore.routers[0].id;
      newSubscriber.value.router_id = inventoryStore.routers[0].id;
    }
  });

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
        <button type="button" class="btn-rg btn-rg--cyan" @click="newSubscriberModalOpen = true">
          {{ t('ipam.btn_register_subscriber') }}
        </button>
      </header>

      <div class="table-scroll-wrapper">
        <table class="rg-table">
          <thead>
            <tr>
              <th scope="col">{{ t('ipam.th_customer') }}</th>
              <th scope="col">{{ t('ipam.th_type_proto') }}</th>
              <th scope="col">{{ t('ipam.th_pppoe_user') }}</th>
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
              <td class="font-bold">{{ sub.customer_name }}</td>
              <td>
                <span class="badge-type">{{ sub.service_type }}</span>
              </td>
              <td class="font-mono text-cyan">{{ sub.pppoe_username || '—' }}</td>
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
                <button
                  type="button"
                  class="btn-row-geo"
                  :aria-label="`Cambiar o agregar ubicación GPS de ${sub.customer_name}`"
                  @click="openLocationModal(sub)"
                >
                  {{ t('ipam.btn_location') }}
                </button>
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

    <!-- Modal Registrar Abonado -->
    <div v-if="newSubscriberModalOpen" class="rg-modal-backdrop" role="dialog" aria-modal="true">
      <div class="rg-modal">
        <header class="modal-header">
          <h3>Registrar Nuevo Servicio FTTH</h3>
          <button type="button" class="btn-close" @click="newSubscriberModalOpen = false">✕</button>
        </header>
        <form class="modal-body" @submit.prevent="handleCreateSubscriber">
          <div class="form-group">

            <label for="sub-r">Router de Acceso / BRAS</label>
            <select id="sub-r" v-model="newSubscriber.router_id" class="rg-input" required>
              <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
                {{ r.display_name }} ({{ r.ip_address }})
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-name">Nombre del Cliente</label>
              <input
                id="sub-name"
                v-model="newSubscriber.customer_name"
                class="rg-input"
                required
              />
            </div>
            <div class="form-group w-30">
              <label for="sub-type">Protocolo</label>
              <select id="sub-type" v-model="newSubscriber.service_type" class="rg-input">
                <option value="PPPOE">PPPoE</option>
                <option value="DHCP">DHCP</option>
                <option value="STATIC">Estático</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="sub-user">Usuario PPPoE</label>
              <input id="sub-user" v-model="newSubscriber.pppoe_username" class="rg-input" />
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
  </main>
</template>

<style scoped>
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
  .rg-modal--sm {
    max-width: 480px;
    width: 95%;
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
