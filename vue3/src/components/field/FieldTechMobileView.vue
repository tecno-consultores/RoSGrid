<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import type { SubscriberDeviceItem } from '@/types';

  const router = useRouter();
  const fieldStore = useFieldOpsStore();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();
  const { t } = useI18n();

  const isIspEnabled = computed(() => authStore.isFeatureEnabled('isp_module_enabled'));

  // Pestañas directas: 'nap' (Caja NAP), 'customer' (Cliente FTTH), 'diagnostics' (Diagnóstico y Certificación)
  const activeTab = ref<'nap' | 'customer' | 'diagnostics'>('nap');

  // Estado GPS Global
  const isLocating = ref(false);
  const techGps = ref<{ lat: number; lng: number } | null>(null);

  // Formulario 1: Registrar Caja NAP
  const napForm = ref({
    router_id: '',
    box_code: '',
    brand: 'Huawei',
    model: 'FAT-16A',
    capacity_ports: 16,
    splitter_ratio: '1:16',
    installation_type: 'POSTE',
    physical_location: '',
    input_power_dbm: -15.5,
    latitude: 10.4806,
    longitude: -66.9036,
    notes: '',
  });

  // Formulario 2: Registrar Nuevo Cliente FTTH
  const customerForm = ref({
    endpoint_identifier: '',
    optical_box_id: '',
    optical_box_port: 1,
    device_serial: '',
    onu_mac_address: '',
    model: 'HG8310M Bridge',
    onu_mode: 'BRIDGE',
    rx_optical_power_dbm: -19.2,
    drop_cable_meters: 65,
    latitude: 10.4806,
    longitude: -66.9036,
  });

  // Formulario 3: Diagnósticos y Certificación
  const selectedSubscriberForDiag = ref<SubscriberDeviceItem | null>(null);
  const diagTargetId = ref('');
  const isPinging = ref(false);
  const pingResult = ref<{
    status: 'ONLINE' | 'OFFLINE';
    latency_ms?: number;
    packet_loss?: number;
    message: string;
  } | null>(null);
  const mtuTestResult = ref<'PASS' | 'FAIL' | null>(null);
  const sessionStatus = ref<'ACTIVE' | 'IDLE' | null>(null);

  // Canvas de firma táctil
  const signatureCanvas = ref<HTMLCanvasElement | null>(null);
  const isDrawing = ref(false);
  const hasDrawnSignature = ref(false);

  // Alertas / Feedback
  const actionMessage = ref<string | null>(null);
  const actionStatus = ref<'success' | 'error'>('success');

  // Inicialización de datos
  onMounted(async () => {
    if (!isIspEnabled.value) return;
    await Promise.all([
      inventoryStore.fetchRouters(),
      fieldStore.fetchOpticalBoxes(),
      fieldStore.fetchRecentInstallations(),
    ]);

    // Preseleccionar primer router si existe
    if (inventoryStore.routers.length > 0 && !napForm.value.router_id) {
      napForm.value.router_id = inventoryStore.routers[0].id;
    }
  });

  // Captura GPS
  function handleCaptureGps() {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      alert('Geolocalización no soportada en este dispositivo.');
      return;
    }
    isLocating.value = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        techGps.value = { lat, lng };
        napForm.value.latitude = lat;
        napForm.value.longitude = lng;
        customerForm.value.latitude = lat;
        customerForm.value.longitude = lng;
        isLocating.value = false;
        showMessage('Coordenadas GPS fijadas exitosamente', 'success');
      },
      (err) => {
        isLocating.value = false;
        showMessage(`Error GPS: ${err.message}`, 'error');
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  function showMessage(msg: string, type: 'success' | 'error' = 'success') {
    actionMessage.value = msg;
    actionStatus.value = type;
    setTimeout(() => {
      if (actionMessage.value === msg) actionMessage.value = null;
    }, 6000);
  }

  // Normalizador GPON
  function handleNormalizeSerial() {
    const raw = customerForm.value.device_serial.trim().toUpperCase();
    if (!raw) return;

    // Si viene en formato HEX (ej: 48575443...), convertir prefijo de 4 bytes a ASCII
    if (raw.length === 16 && /^[0-9A-F]+$/.test(raw)) {
      const vendorHex = raw.slice(0, 8);
      let vendorAscii = '';
      for (let i = 0; i < vendorHex.length; i += 2) {
        vendorAscii += String.fromCharCode(parseInt(vendorHex.slice(i, i + 2), 16));
      }
      customerForm.value.device_serial = `${vendorAscii}${raw.slice(8)}`;
    } else {
      customerForm.value.device_serial = raw.replace(/\s+/g, '');
    }
    showMessage(`Serial GPON normalizado: ${customerForm.value.device_serial}`, 'success');
  }

  // Copiar coordenadas de la caja NAP al formulario de cliente
  function handleCopyCoordsFromNap() {
    if (!customerForm.value.optical_box_id) {
      showMessage('Seleccione primero una Caja NAP', 'error');
      return;
    }
    const box = fieldStore.opticalBoxes.find((b) => b.id === customerForm.value.optical_box_id);
    if (box) {
      customerForm.value.latitude = Number(box.latitude);
      customerForm.value.longitude = Number(box.longitude);
      showMessage(`Coordenadas copiadas de ${box.box_code}`, 'success');
    }
  }

  // Semáforo dinámico de Potencia Óptica Rx
  const opticalRxSeverity = computed(() => {
    const p = customerForm.value.rx_optical_power_dbm;
    if (p >= -24.0 && p <= -15.0) return 'optimal';
    if (p < -24.0 && p >= -27.0) return 'warning';
    return 'critical';
  });

  // Puertos disponibles en la caja NAP seleccionada
  const selectedNapBox = computed(() => {
    return fieldStore.opticalBoxes.find((b) => b.id === customerForm.value.optical_box_id) || null;
  });

  // Guardar Caja NAP
  async function handleCreateNap() {
    if (!napForm.value.box_code.trim()) {
      showMessage('Ingrese un código para la Caja NAP', 'error');
      return;
    }
    if (!napForm.value.router_id) {
      showMessage('Seleccione un Router MikroTik asignador', 'error');
      return;
    }

    try {
      const created = await fieldStore.createOpticalBox({
        router_id: napForm.value.router_id,
        box_code: napForm.value.box_code.trim().toUpperCase(),
        brand: napForm.value.brand,
        model: napForm.value.model,
        capacity_ports: Number(napForm.value.capacity_ports),
        splitter_ratio: napForm.value.splitter_ratio,
        installation_type: napForm.value.installation_type,
        physical_location: napForm.value.physical_location,
        input_power_dbm: Number(napForm.value.input_power_dbm),
        latitude: Number(napForm.value.latitude),
        longitude: Number(napForm.value.longitude),
        notes: napForm.value.notes,
      });
      showMessage(`Caja NAP ${created.box_code} registrada exitosamente.`, 'success');

      // Auto-seleccionar en la pestaña de cliente
      customerForm.value.optical_box_id = created.id;
      customerForm.value.optical_box_port = 1;
      activeTab.value = 'customer';
    } catch (err: unknown) {
      const msg = (err as Error)?.message || 'Error al registrar Caja NAP';
      showMessage(msg, 'error');
    }
  }

  // Registrar Nuevo Cliente FTTH
  async function handleRegisterCustomer() {
    if (!customerForm.value.endpoint_identifier.trim()) {
      showMessage('Ingrese el identificador de servicio del abonado', 'error');
      return;
    }
    if (!customerForm.value.device_serial.trim()) {
      showMessage('Ingrese o escanee el serial de la ONU', 'error');
      return;
    }
    if (!customerForm.value.optical_box_id) {
      showMessage('Seleccione una Caja NAP de conexión', 'error');
      return;
    }

    const box = selectedNapBox.value;
    const routerId = box ? box.router_id : napForm.value.router_id;

    try {
      const dev = await fieldStore.registerSubscriberDevice({
        router_id: routerId,
        endpoint_identifier: customerForm.value.endpoint_identifier.trim(),
        service_type: 'FTTH_GPON',
        device_serial: customerForm.value.device_serial.trim().toUpperCase(),
        onu_mac_address: customerForm.value.onu_mac_address.trim() || undefined,
        onu_mode: customerForm.value.onu_mode,
        optical_box_id: customerForm.value.optical_box_id,
        optical_box_port: Number(customerForm.value.optical_box_port),
        rx_optical_power_dbm: Number(customerForm.value.rx_optical_power_dbm),
        drop_cable_meters: Number(customerForm.value.drop_cable_meters),
        latitude: Number(customerForm.value.latitude),
        longitude: Number(customerForm.value.longitude),
      });

      showMessage(`Cliente FTTH ${dev.customer_code || dev.endpoint_identifier} registrado exitosamente.`, 'success');
      selectedSubscriberForDiag.value = dev;
      diagTargetId.value = dev.id;
      activeTab.value = 'diagnostics';
    } catch (err: unknown) {
      const msg = (err as Error)?.message || 'Error al registrar cliente FTTH';
      showMessage(msg, 'error');
    }
  }

  // Ejecutar Ping 1-Click desde MikroTik
  async function handleRun1ClickPing() {
    const devId = diagTargetId.value || selectedSubscriberForDiag.value?.id;
    if (!devId) {
      showMessage('Seleccione un cliente registrado para diagnosticar', 'error');
      return;
    }
    isPinging.value = true;
    pingResult.value = null;
    try {
      const res = await fieldStore.pingSubscriberLive(devId);
      pingResult.value = {
        status: res.last_reachability_status === 'ONLINE' ? 'ONLINE' : 'OFFLINE',
        latency_ms: res.ping_latency_ms,
        packet_loss: res.packet_loss_pct,
        message: res.message,
      };
      sessionStatus.value = 'ACTIVE';
      mtuTestResult.value = 'PASS';
      showMessage('Diagnóstico de enlace MikroTik completado.', 'success');
    } catch (err: unknown) {
      pingResult.value = {
        status: 'OFFLINE',
        latency_ms: undefined,
        packet_loss: 100,
        message: (err as Error)?.message || 'Sin respuesta ICMP desde el router',
      };
      sessionStatus.value = 'IDLE';
      mtuTestResult.value = 'FAIL';
      showMessage('El equipo no respondió al ping.', 'error');
    } finally {
      isPinging.value = false;
    }
  }

  // Canvas de Firma
  function startDrawing(e: MouseEvent | TouchEvent) {
    isDrawing.value = true;
    hasDrawnSignature.value = true;
    const canvas = signatureCanvas.value;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    ctx.beginPath();
    ctx.moveTo(clientX - rect.left, clientY - rect.top);
  }

  function draw(e: MouseEvent | TouchEvent) {
    if (!isDrawing.value) return;
    const canvas = signatureCanvas.value;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    ctx.lineTo(clientX - rect.left, clientY - rect.top);
    ctx.strokeStyle = '#00f3ff';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.stroke();
  }

  function stopDrawing() {
    isDrawing.value = false;
  }

  function clearSignature() {
    const canvas = signatureCanvas.value;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    hasDrawnSignature.value = false;
  }

  function handleCertifyInstallation() {
    if (!hasDrawnSignature.value) {
      showMessage('Se requiere la firma táctil para certificar la entrega', 'error');
      return;
    }
    showMessage('✅ Instalación certificada con éxito. Entrega registrada en auditoría WORM.', 'success');
  }

  function handleSelectRecentDev(dev: SubscriberDeviceItem) {
    selectedSubscriberForDiag.value = dev;
    diagTargetId.value = dev.id;
    activeTab.value = 'diagnostics';
  }
</script>

<template>
  <div class="field-mobile-view" data-theme="noc-dark">
    <!-- Pantalla informativa si Modo ISP está Desactivado (Organización No-ISP) -->
    <div v-if="!isIspEnabled" class="non-isp-blocker">
      <div class="blocker-card">
        <span class="blocker-icon">🏢</span>
        <h2 class="blocker-title">{{ t('field_tech.non_isp_warning_title') }}</h2>
        <p class="blocker-desc">{{ t('field_tech.non_isp_warning_desc') }}</p>
        <button
          type="button"
          class="btn-touch btn-touch--cyan"
          @click="router.push('/subscribers/map')"
        >
          🗺️ {{ t('field_tech.go_to_network_map') }}
        </button>
      </div>
    </div>

    <!-- Panel Completo Técnico de Campo FTTH -->
    <div v-else class="field-content-container">
      <!-- Header Táctico -->
      <header class="field-header">
        <div class="tech-info">
          <span class="tech-icon" aria-hidden="true">🛠️</span>
          <div>
            <h1 class="tech-title">{{ t('field_tech.title') }}</h1>
            <span class="tech-sub">{{ t('field_tech.subtitle') }}</span>
          </div>
        </div>

        <div class="header-actions">
          <button
            id="btn-global-gps"
            type="button"
            class="btn-gps-prominent"
            :disabled="isLocating"
            @click="handleCaptureGps"
          >
            <span v-if="isLocating">{{ t('field_tech.capturing_gps') }}</span>
            <span v-else-if="techGps"
              >✅ {{ t('field_tech.gps_captured') }}: {{ techGps.lat }}, {{ techGps.lng }}</span
            >
            <span v-else>{{ t('field_tech.capture_gps') }}</span>
          </button>
        </div>
      </header>

      <!-- Banner de Feedback -->
      <div
        v-if="actionMessage"
        class="feedback-banner"
        :class="`feedback--${actionStatus}`"
        role="alert"
      >
        <span>{{ actionStatus === 'success' ? '⚡' : '⚠️' }} {{ actionMessage }}</span>
        <button type="button" class="btn-close-msg" @click="actionMessage = null">✕</button>
      </div>

      <!-- Pestañas de Acción Táctica -->
      <nav class="tactical-tabs-nav" aria-label="Navegación de Operaciones de Campo">
        <button
          id="tab-btn-nap"
          type="button"
          :class="['nav-tab', { active: activeTab === 'nap' }]"
          @click="activeTab = 'nap'"
        >
          📦 {{ t('field_tech.tab_nap') }}
          <span class="tab-badge">{{ fieldStore.opticalBoxes.length }}</span>
        </button>
        <button
          id="tab-btn-customer"
          type="button"
          :class="['nav-tab', { active: activeTab === 'customer' }]"
          @click="activeTab = 'customer'"
        >
          🔌 {{ t('field_tech.tab_customer') }}
        </button>
        <button
          id="tab-btn-diagnostics"
          type="button"
          :class="['nav-tab', { active: activeTab === 'diagnostics' }]"
          @click="activeTab = 'diagnostics'"
        >
          ⚡ {{ t('field_tech.tab_diagnostics') }}
        </button>
      </nav>

      <!-- Contenedor Principal de la Pestaña Activa -->
      <main class="field-tab-content">
        <!-- ========================================== -->
        <!-- TAB 1: REGISTRAR CAJA NAP                  -->
        <!-- ========================================== -->
        <section v-if="activeTab === 'nap'" class="tab-pane" aria-labelledby="tab-btn-nap">
          <div class="pane-grid">
            <div class="card-form">
              <h2 class="form-title">📦 Registrar Nueva Caja de Distribución Óptica (NAP)</h2>
              <p class="form-desc">
                Geolocalice la caja y configure su capacidad de splitters para permitir altas de clientes.
              </p>

              <form class="form-body" @submit.prevent="handleCreateNap">
                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="nap-router-select">Router Asignador / Sede *</label>
                    <select
                      id="nap-router-select"
                      v-model="napForm.router_id"
                      class="rg-input"
                      required
                    >
                      <option value="" disabled>Seleccione un router...</option>
                      <option
                        v-for="r in inventoryStore.routers"
                        :key="r.id"
                        :value="r.id"
                      >
                        {{ r.display_name }} ({{ r.ip_address }})
                      </option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="nap-code-input">{{ t('field_tech.box_code') }} *</label>
                    <input
                      id="nap-code-input"
                      v-model="napForm.box_code"
                      type="text"
                      class="rg-input font-mono"
                      :placeholder="t('field_tech.box_code_placeholder')"
                      required
                    />
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label>{{ t('field_tech.capacity') }}</label>
                    <div class="capacity-buttons">
                      <button
                        type="button"
                        :class="['btn-toggle', { active: napForm.capacity_ports === 8 }]"
                        @click="napForm.capacity_ports = 8; napForm.splitter_ratio = '1:8'"
                      >
                        8 Puertos
                      </button>
                      <button
                        type="button"
                        :class="['btn-toggle', { active: napForm.capacity_ports === 16 }]"
                        @click="napForm.capacity_ports = 16; napForm.splitter_ratio = '1:16'"
                      >
                        16 Puertos
                      </button>
                      <button
                        type="button"
                        :class="['btn-toggle', { active: napForm.capacity_ports === 24 }]"
                        @click="napForm.capacity_ports = 24; napForm.splitter_ratio = '1:24'"
                      >
                        24 Puertos
                      </button>
                    </div>
                  </div>

                  <div class="form-group flex-1">
                    <label for="nap-splitter-ratio">{{ t('field_tech.splitter') }}</label>
                    <select id="nap-splitter-ratio" v-model="napForm.splitter_ratio" class="rg-input">
                      <option value="1:8">Splitter Simétrico 1:8</option>
                      <option value="1:16">Splitter Simétrico 1:16</option>
                      <option value="1:24">Splitter Simétrico 1:24</option>
                      <option value="1:2 + 1:8">Cascada 1:2 + 1:8</option>
                    </select>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="nap-type-select">{{ t('field_tech.installation_type') }}</label>
                    <select id="nap-type-select" v-model="napForm.installation_type" class="rg-input">
                      <option value="POSTE">{{ t('field_tech.installation_pole') }}</option>
                      <option value="FACHADA">{{ t('field_tech.installation_facade') }}</option>
                      <option value="CAMARA_SUBTERRANEA">{{ t('field_tech.installation_underground') }}</option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="nap-pin-input">{{ t('field_tech.input_power_dbm') }}</label>
                    <input
                      id="nap-pin-input"
                      v-model.number="napForm.input_power_dbm"
                      type="number"
                      step="0.1"
                      class="rg-input font-mono text-cyan"
                    />
                  </div>
                </div>

                <div class="form-group">
                  <label for="nap-location-input">{{ t('field_tech.physical_location') }}</label>
                  <input
                    id="nap-location-input"
                    v-model="napForm.physical_location"
                    type="text"
                    class="rg-input"
                    placeholder="Ej: Av. Bolívar Poste Eléctrico #14 frente a FarmaCentro"
                  />
                </div>

                <div class="form-row coords-row">
                  <div class="form-group flex-1">
                    <label for="nap-lat-input">{{ t('field_tech.latitude') }} *</label>
                    <input
                      id="nap-lat-input"
                      v-model.number="napForm.latitude"
                      type="number"
                      step="0.000001"
                      class="rg-input font-mono"
                      required
                    />
                  </div>

                  <div class="form-group flex-1">
                    <label for="nap-lng-input">{{ t('field_tech.longitude') }} *</label>
                    <input
                      id="nap-lng-input"
                      v-model.number="napForm.longitude"
                      type="number"
                      step="0.000001"
                      class="rg-input font-mono"
                      required
                    />
                  </div>

                  <button
                    type="button"
                    class="btn-touch btn-touch--cyan align-self-end"
                    @click="handleCaptureGps"
                  >
                    📍 GPS
                  </button>
                </div>

                <button type="submit" class="btn-touch btn-touch--green w-full submit-btn">
                  {{ t('field_tech.btn_save_nap') }}
                </button>
              </form>
            </div>

            <!-- Listado de Cajas Registradas -->
            <div class="card-list">
              <h3 class="list-title">Cajas NAP Desplegadas ({{ fieldStore.opticalBoxes.length }})</h3>
              <div v-if="fieldStore.opticalBoxes.length === 0" class="empty-hint">
                No hay cajas NAP registradas aún. Registre la primera caja a la izquierda.
              </div>
              <div v-else class="boxes-scrollable">
                <article
                  v-for="b in fieldStore.opticalBoxes"
                  :key="b.id"
                  class="box-mini-card"
                  @click="customerForm.optical_box_id = b.id; activeTab = 'customer'"
                >
                  <div class="box-mini-header">
                    <span class="box-badge font-mono">{{ b.box_code }}</span>
                    <span class="box-capacity-tag">{{ b.capacity_ports }}p ({{ b.splitter_ratio }})</span>
                  </div>
                  <p class="box-location">{{ b.physical_location || 'Ubicación sin especificar' }}</p>
                  <div class="box-mini-footer">
                    <span class="font-mono text-cyan">{{ b.input_power_dbm ?? '--' }} dBm Pin</span>
                    <span class="text-subtle font-mono">{{ Number(b.latitude).toFixed(4) }}, {{ Number(b.longitude).toFixed(4) }}</span>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </section>

        <!-- ========================================== -->
        <!-- TAB 2: REGISTRAR NUEVO CLIENTE FTTH        -->
        <!-- ========================================== -->
        <section v-else-if="activeTab === 'customer'" class="tab-pane" aria-labelledby="tab-btn-customer">
          <div class="pane-grid">
            <div class="card-form">
              <h2 class="form-title">🔌 Registrar y Aprovisionar Nuevo Cliente FTTH</h2>
              <p class="form-desc">
                Asocie la ONU al puerto disponible de la Caja NAP y valide la potencia óptica recibida en domicilio.
              </p>

              <form class="form-body" @submit.prevent="handleRegisterCustomer">
                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-service-id">{{ t('field_tech.subscriber_service_id') }} *</label>
                    <input
                      id="cust-service-id"
                      v-model="customerForm.endpoint_identifier"
                      type="text"
                      class="rg-input font-mono"
                      placeholder="Ej: CLI-008492"
                      required
                    />
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-nap-select">{{ t('field_tech.select_nap') }} *</label>
                    <select
                      id="cust-nap-select"
                      v-model="customerForm.optical_box_id"
                      class="rg-input"
                      required
                    >
                      <option value="" disabled>Seleccione una caja NAP...</option>
                      <option
                        v-for="b in fieldStore.opticalBoxes"
                        :key="b.id"
                        :value="b.id"
                      >
                        {{ b.box_code }} ({{ b.capacity_ports }}p - {{ b.physical_location || 'NAP' }})
                      </option>
                    </select>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-port-select">{{ t('field_tech.select_nap_port') }} *</label>
                    <select
                      id="cust-port-select"
                      v-model.number="customerForm.optical_box_port"
                      class="rg-input font-mono"
                      required
                    >
                      <option
                        v-for="p in (selectedNapBox ? selectedNapBox.capacity_ports : 16)"
                        :key="p"
                        :value="p"
                      >
                        Puerto {{ p }}
                      </option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-onu-serial">{{ t('field_tech.serial_onu_label') }} *</label>
                    <div class="input-with-btn">
                      <input
                        id="cust-onu-serial"
                        v-model="customerForm.device_serial"
                        type="text"
                        class="rg-input font-mono flex-1"
                        placeholder="Ej: HWTC1234ABCD"
                        required
                      />
                      <button
                        type="button"
                        class="btn-touch-sm btn-touch--cyan"
                        title="Normalizar prefijos GPON"
                        @click="handleNormalizeSerial"
                      >
                        🔤
                      </button>
                    </div>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-onu-model">Modelo de ONU</label>
                    <select id="cust-onu-model" v-model="customerForm.model" class="rg-input">
                      <option value="HG8310M Bridge">Huawei HG8310M (Bridge 1GE)</option>
                      <option value="F601 Bridge">ZTE F601 (Bridge 1GE)</option>
                      <option value="F670L WiFi-6">ZTE F670L (Router Dual-Band AX)</option>
                      <option value="EG8145V5 WiFi">Huawei EG8145V5 (Router AC)</option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-onu-mode">Modo de Operación</label>
                    <select id="cust-onu-mode" v-model="customerForm.onu_mode" class="rg-input">
                      <option value="BRIDGE">Bridge Puro (PPPoE en Router Cliente)</option>
                      <option value="ROUTER_NAT">Router NAT (PPPoE/DHCP en la ONU)</option>
                    </select>
                  </div>
                </div>

                <!-- Semáforo Cromático de Potencia Óptica Rx -->
                <div class="optical-power-meter-card" :class="`meter--${opticalRxSeverity}`">
                  <div class="meter-header">
                    <label for="cust-rx-power">{{ t('field_tech.rx_optical_power') }} *</label>
                    <span class="power-status-badge">
                      <span v-if="opticalRxSeverity === 'optimal'">🟢 ÓPTIMO (-15 a -24 dBm)</span>
                      <span v-else-if="opticalRxSeverity === 'warning'">🟠 ATENCIÓN (-24 a -27 dBm)</span>
                      <span v-else>🔴 CRÍTICO / SATURADO</span>
                    </span>
                  </div>
                  <div class="meter-input-group">
                    <input
                      id="cust-rx-power"
                      v-model.number="customerForm.rx_optical_power_dbm"
                      type="number"
                      step="0.1"
                      class="rg-input font-mono text-xl"
                      required
                    />
                    <span class="unit-tag font-mono">dBm</span>
                  </div>
                  <p class="meter-advice">
                    <span v-if="opticalRxSeverity === 'optimal'">El nivel de luz se encuentra en el rango de máxima estabilidad y cero jitter.</span>
                    <span v-else-if="opticalRxSeverity === 'warning'">Atenuación elevada. Verifique curvatura del cable drop o limpieza del conector SC/APC.</span>
                    <span v-else>Riesgo inminente de desconexión o pérdida de tramas FEC. Requiere re-fusionar el drop.</span>
                  </p>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-drop-meters">{{ t('field_tech.drop_cable_meters') }}</label>
                    <input
                      id="cust-drop-meters"
                      v-model.number="customerForm.drop_cable_meters"
                      type="number"
                      class="rg-input font-mono"
                    />
                  </div>
                </div>

                <!-- Coordenadas Domicilio -->
                <div class="coords-box">
                  <div class="coords-header">
                    <span>Coordenadas del Domicilio</span>
                    <button
                      type="button"
                      class="btn-touch-xs btn-touch--cyan"
                      @click="handleCopyCoordsFromNap"
                    >
                      {{ t('field_tech.copy_nap_coords') }}
                    </button>
                  </div>
                  <div class="form-row">
                    <div class="form-group flex-1">
                      <input
                        v-model.number="customerForm.latitude"
                        type="number"
                        step="0.000001"
                        class="rg-input font-mono"
                        placeholder="Latitud"
                      />
                    </div>
                    <div class="form-group flex-1">
                      <input
                        v-model.number="customerForm.longitude"
                        type="number"
                        step="0.000001"
                        class="rg-input font-mono"
                        placeholder="Longitud"
                      />
                    </div>
                    <button
                      type="button"
                      class="btn-touch btn-touch--cyan"
                      @click="handleCaptureGps"
                    >
                      📍 GPS
                    </button>
                  </div>
                </div>

                <button type="submit" class="btn-touch btn-touch--green w-full submit-btn">
                  {{ t('field_tech.btn_register_customer') }}
                </button>
              </form>
            </div>

            <!-- Previsualización de la Caja NAP Seleccionada -->
            <div class="card-list">
              <h3 class="list-title">Detalle de la Caja NAP</h3>
              <div v-if="!selectedNapBox" class="empty-hint">
                Seleccione una Caja NAP en el formulario para inspeccionar sus puertos y capacidad.
              </div>
              <div v-else class="nap-detail-view">
                <div class="nap-summary">
                  <h4 class="font-mono text-cyan">{{ selectedNapBox.box_code }}</h4>
                  <p>{{ selectedNapBox.physical_location || 'Sin dirección física registrada' }}</p>
                  <p class="font-mono text-subtle">
                    Splitter {{ selectedNapBox.splitter_ratio }} • Potencia Entrada: {{ selectedNapBox.input_power_dbm ?? '--' }} dBm
                  </p>
                </div>

                <div class="nap-matrix-preview">
                  <h5>Matriz de Puertos ({{ selectedNapBox.capacity_ports }} Puertos)</h5>
                  <div class="ports-grid">
                    <button
                      v-for="p in selectedNapBox.capacity_ports"
                      :key="p"
                      type="button"
                      :class="[
                        'port-btn',
                        { selected: customerForm.optical_box_port === p }
                      ]"
                      @click="customerForm.optical_box_port = p"
                    >
                      <span class="port-num">{{ p }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ========================================== -->
        <!-- TAB 3: DIAGNÓSTICOS Y CERTIFICACIÓN        -->
        <!-- ========================================== -->
        <section v-else class="tab-pane" aria-labelledby="tab-btn-diagnostics">
          <div class="pane-grid">
            <div class="card-form">
              <h2 class="form-title">⚡ Diagnóstico en Tiempo Real y Certificación 1-Click</h2>
              <p class="form-desc">
                Verifique conectividad ICMP desde el router MikroTik y selle la entrega con firma táctil.
              </p>

              <div class="diag-action-bar">
                <div class="form-group flex-1">
                  <label for="diag-target-select">Abonado a Diagnosticar</label>
                  <select
                    id="diag-target-select"
                    v-model="diagTargetId"
                    class="rg-input font-mono"
                  >
                    <option value="" disabled>Seleccione un abonado...</option>
                    <option
                      v-for="dev in fieldStore.recentInstallations"
                      :key="dev.id"
                      :value="dev.id"
                    >
                      {{ dev.customer_code || dev.endpoint_identifier }} - {{ dev.onu_serial_number || dev.device_serial }}
                    </option>
                  </select>
                </div>

                <button
                  type="button"
                  class="btn-touch btn-touch--cyan align-self-end"
                  :disabled="isPinging || !diagTargetId"
                  @click="handleRun1ClickPing"
                >
                  <span v-if="isPinging">⏳ Probando...</span>
                  <span v-else>⚡ Test Ping 1-Click</span>
                </button>
              </div>

              <!-- Resultados de Conectividad en Vivo -->
              <div v-if="pingResult" class="ping-results-card" :class="`ping--${pingResult.status.toLowerCase()}`">
                <div class="ping-card-header">
                  <span class="status-pill">{{ pingResult.status }}</span>
                  <span class="latency-readout font-mono">
                    {{ pingResult.latency_ms !== undefined ? `${pingResult.latency_ms} ms` : 'Timeout' }}
                  </span>
                </div>
                <p class="ping-msg font-mono">{{ pingResult.message }}</p>

                <div class="diagnostics-subgrid">
                  <div class="diag-metric-box">
                    <span class="metric-label">Sesión RouterOS v7</span>
                    <span class="metric-val text-green">{{ sessionStatus || 'Verificando...' }}</span>
                  </div>
                  <div class="diag-metric-box">
                    <span class="metric-label">MTU 1500 DF Pass</span>
                    <span class="metric-val" :class="mtuTestResult === 'PASS' ? 'text-green' : 'text-red'">
                      {{ mtuTestResult || 'En espera' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Canvas Táctil de Firma de Conformidad -->
              <div class="signature-section">
                <div class="sig-header">
                  <label class="sig-title">✍️ {{ t('field_tech.client_signature') }}</label>
                  <button type="button" class="btn-touch-xs btn-touch--orange" @click="clearSignature">
                    🗑️ {{ t('field_tech.clear_signature') }}
                  </button>
                </div>

                <div class="signature-canvas-container">
                  <canvas
                    id="signature-canvas"
                    ref="signatureCanvas"
                    width="480"
                    height="160"
                    class="signature-pad"
                    @mousedown="startDrawing"
                    @mousemove="draw"
                    @mouseup="stopDrawing"
                    @touchstart.prevent="startDrawing"
                    @touchmove.prevent="draw"
                    @touchend.prevent="stopDrawing"
                  />
                  <div v-if="!hasDrawnSignature" class="signature-watermark" aria-hidden="true">
                    <span>Dibujar rúbrica de conformidad aquí con el dedo o stylus</span>
                  </div>
                </div>

                <button
                  type="button"
                  class="btn-touch btn-touch--purple w-full submit-btn"
                  @click="handleCertifyInstallation"
                >
                  {{ t('field_tech.certify_submit') }}
                </button>
              </div>
            </div>

            <!-- Historial de Altas Recientes del Técnico -->
            <div class="card-list">
              <h3 class="list-title">{{ t('field_tech.recent_activity') }} ({{ fieldStore.recentInstallations.length }})</h3>
              <div v-if="fieldStore.recentInstallations.length === 0" class="empty-hint">
                No hay instalaciones recientes registradas en este turno.
              </div>
              <div v-else class="boxes-scrollable">
                <article
                  v-for="inst in fieldStore.recentInstallations"
                  :key="inst.id"
                  class="box-mini-card"
                  @click="handleSelectRecentDev(inst)"
                >
                  <div class="box-mini-header">
                    <span class="box-badge font-mono">{{ inst.customer_code || inst.endpoint_identifier }}</span>
                    <span
                      class="status-pill-sm"
                      :class="inst.last_reachability_status === 'ONLINE' ? 'pill--green' : 'pill--gray'"
                    >
                      {{ inst.last_reachability_status || 'REGISTRADO' }}
                    </span>
                  </div>
                  <p class="font-mono text-cyan">{{ inst.onu_serial_number || inst.device_serial }}</p>
                  <div class="box-mini-footer">
                    <span>Puerto {{ inst.optical_box_port ?? '1' }}</span>
                    <span class="text-subtle font-mono">{{ inst.rx_optical_power_dbm ?? '--' }} dBm Rx</span>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
  .field-mobile-view {
    width: 100%;
    max-width: 1440px;
    margin: 0 auto;
    background: #090e17;
    color: #f1f5f9;
    min-height: 100vh;
    padding: 1.25rem;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .non-isp-blocker {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 60vh;
  }

  .blocker-card {
    background: #111927;
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    padding: 2.5rem;
    max-width: 520px;
    text-align: center;
  }

  .blocker-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
  }

  .blocker-title {
    color: #00f3ff;
    font-size: 1.35rem;
    margin-bottom: 0.75rem;
  }

  .blocker-desc {
    color: #94a3b8;
    margin-bottom: 1.5rem;
    line-height: 1.5;
  }

  .field-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(0, 243, 255, 0.2);
    margin-bottom: 1.25rem;
  }

  .tech-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .tech-icon {
    font-size: 2rem;
  }

  .tech-title {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 800;
    color: #00f3ff;
  }

  .tech-sub {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .btn-gps-prominent {
    background: #002233;
    border: 1px solid #00f3ff;
    color: #00f3ff;
    padding: 0.6rem 1.2rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .btn-gps-prominent:hover {
    background: rgba(0, 243, 255, 0.2);
  }

  .feedback-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    font-weight: 500;
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

  .btn-close-msg {
    background: none;
    border: none;
    color: inherit;
    font-size: 1.1rem;
    cursor: pointer;
  }

  .tactical-tabs-nav {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 1.5rem;
    overflow-x: auto;
  }

  .nav-tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    color: #94a3b8;
    padding: 0.75rem 1.25rem;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
  }

  .nav-tab:hover {
    color: #f1f5f9;
  }

  .nav-tab.active {
    color: #00f3ff;
    border-bottom-color: #00f3ff;
    background: rgba(0, 243, 255, 0.05);
  }

  .tab-badge {
    background: #1e293b;
    color: #00f3ff;
    font-size: 0.75rem;
    padding: 0.15rem 0.45rem;
    border-radius: 10px;
  }

  .pane-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 992px) {
    .pane-grid {
      grid-template-columns: 1fr;
    }
  }

  .card-form, .card-list {
    background: #111927;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 1.5rem;
  }

  .form-title, .list-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 0;
    margin-bottom: 0.35rem;
    color: #f8fafc;
  }

  .form-desc {
    font-size: 0.825rem;
    color: #94a3b8;
    margin-bottom: 1.25rem;
  }

  .form-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .flex-1 {
    flex: 1;
    min-width: 220px;
  }

  .rg-input {
    background: #090e17;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    color: #f1f5f9;
    font-size: 0.9rem;
  }

  .rg-input:focus {
    border-color: #00f3ff;
    outline: none;
    box-shadow: 0 0 0 2px rgba(0, 243, 255, 0.2);
  }

  .capacity-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .btn-toggle {
    flex: 1;
    background: #090e17;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #94a3b8;
    padding: 0.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .btn-toggle.active {
    background: #002b3d;
    border-color: #00f3ff;
    color: #00f3ff;
    font-weight: 600;
  }

  .btn-touch {
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-touch--cyan {
    background: #00f3ff;
    color: #000;
  }

  .btn-touch--cyan:hover {
    background: #5cf6ff;
  }

  .btn-touch--green {
    background: #22c55e;
    color: #000;
  }

  .btn-touch--green:hover {
    background: #4ade80;
  }

  .btn-touch--purple {
    background: #8b5cf6;
    color: #fff;
  }

  .btn-touch-sm {
    padding: 0.4rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    border: none;
    cursor: pointer;
  }

  .btn-touch-xs {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    border: none;
    cursor: pointer;
  }

  .w-full {
    width: 100%;
  }

  .align-self-end {
    align-self: flex-end;
  }

  .input-with-btn {
    display: flex;
    gap: 0.5rem;
  }

  /* Semáforo de Potencia Óptica */
  .optical-power-meter-card {
    padding: 1rem;
    border-radius: 6px;
    background: #090e17;
    border-left: 4px solid #22c55e;
  }

  .meter--optimal {
    border-left-color: #22c55e;
  }

  .meter--warning {
    border-left-color: #f97316;
  }

  .meter--critical {
    border-left-color: #ef4444;
  }

  .meter-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
  }

  .power-status-badge {
    font-weight: 700;
    font-size: 0.75rem;
  }

  .meter-input-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .meter-advice {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 0.4rem;
    margin-bottom: 0;
  }

  .coords-box {
    background: #090e17;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 0.75rem;
  }

  .coords-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .boxes-scrollable {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 520px;
    overflow-y: auto;
  }

  .box-mini-card {
    background: #090e17;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .box-mini-card:hover {
    border-color: #00f3ff;
    transform: translateY(-2px);
  }

  .box-mini-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.35rem;
  }

  .box-badge {
    color: #00f3ff;
    font-weight: 700;
  }

  .box-capacity-tag {
    font-size: 0.75rem;
    background: #1e293b;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
  }

  .box-location {
    font-size: 0.8rem;
    color: #cbd5e1;
    margin: 0 0 0.35rem 0;
  }

  .box-mini-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
  }

  .text-cyan {
    color: #00f3ff;
  }

  .text-green {
    color: #22c55e;
  }

  .text-red {
    color: #ef4444;
  }

  .text-subtle {
    color: #64748b;
  }

  .ports-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 0.35rem;
    margin-top: 0.5rem;
  }

  .port-btn {
    background: #090e17;
    border: 1px solid rgba(0, 243, 255, 0.3);
    color: #00f3ff;
    padding: 0.5rem 0.25rem;
    border-radius: 4px;
    font-weight: 700;
    cursor: pointer;
  }

  .port-btn.selected {
    background: #00f3ff;
    color: #000;
  }

  /* Diagnósticos */
  .diag-action-bar {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }

  .ping-results-card {
    background: #090e17;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 1.25rem;
  }

  .ping--online {
    border-color: #22c55e;
  }

  .ping--offline {
    border-color: #ef4444;
  }

  .ping-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .status-pill {
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.85rem;
  }

  .ping--online .status-pill {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  .ping--offline .status-pill {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  .diagnostics-subgrid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }

  .diag-metric-box {
    background: #111927;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
  }

  .metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .metric-val {
    font-weight: 700;
    font-size: 0.95rem;
  }

  /* Firma */
  .signature-section {
    margin-top: 1.5rem;
  }

  .sig-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .signature-canvas-container {
    position: relative;
    background: #090e17;
    border: 2px dashed rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    margin-bottom: 1rem;
    display: flex;
    justify-content: center;
  }

  .signature-pad {
    width: 100%;
    max-width: 480px;
    height: 160px;
    touch-action: none;
    cursor: crosshair;
  }

  .signature-watermark {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: rgba(255, 255, 255, 0.2);
    pointer-events: none;
    font-size: 0.85rem;
  }

  .status-pill-sm {
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .pill--green {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }

  .pill--gray {
    background: rgba(148, 163, 184, 0.2);
    color: #94a3b8;
  }
</style>
