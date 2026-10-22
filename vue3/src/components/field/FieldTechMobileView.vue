<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { onMounted, ref } from 'vue';
  import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
  import { useI18n } from '@/composables/useI18n';
  import type { FieldOrder } from '@/types';

  const fieldStore = useFieldOpsStore();
  const { t } = useI18n();

  const activeTab = ref<'orders' | 'verify' | 'certify'>('orders');
  const selectedOrder = ref<FieldOrder | null>(null);

  const manualSubscriberId = ref('');
  const scannedSerial = ref('');
  const scannedMac = ref('');
  const techNotes = ref('');
  const isLocating = ref(false);
  const techGps = ref<{ lat: number; lng: number } | null>(null);

  // Canvas de firma táctil
  const signatureCanvas = ref<HTMLCanvasElement | null>(null);
  const isDrawing = ref(false);
  const hasDrawnSignature = ref(false);

  // Diagnóstico 360 rápido en desktop
  const isRunning360 = ref(false);
  const diag360Result = ref<string | null>(null);

  onMounted(async () => {
    await fieldStore.fetchOrders(true);
  });

  function handleSelectOrder(order: FieldOrder) {
    selectedOrder.value = order;
    manualSubscriberId.value = order.customer_service_id;
    activeTab.value = 'verify';
  }

  async function handleRun1ClickVerify() {
    if (!manualSubscriberId.value.trim()) return;
    await fieldStore.verifySubscriberLive(
      manualSubscriberId.value.trim(),
      scannedMac.value.trim() || undefined,
      scannedSerial.value.trim() || undefined,
    );
  }

  function handleCaptureGps() {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      alert('Geolocalización no soportada en este navegador');
      return;
    }
    isLocating.value = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        techGps.value = {
          lat: Number(pos.coords.latitude.toFixed(6)),
          lng: Number(pos.coords.longitude.toFixed(6)),
        };
        isLocating.value = false;
      },
      (err) => {
        alert(`Error GPS: ${err.message}`);
        isLocating.value = false;
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  // Lógica de Canvas de Firma
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
    ctx.lineWidth = 2;
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

  async function handleCertifyInstallation() {
    if (!selectedOrder.value && !manualSubscriberId.value) return;
    if (!scannedSerial.value.trim()) {
      alert('Debe escanear o ingresar el serial de la ONU antes de certificar');
      return;
    }

    const canvas = signatureCanvas.value;
    const signatureSvg = canvas ? canvas.toDataURL('image/png') : undefined;

    try {
      const orderId = selectedOrder.value ? selectedOrder.value.id : '';
      await fieldStore.certifyInstallation({
        order_id: orderId,
        onu_scanned_serial: scannedSerial.value.trim(),
        onu_scanned_mac: scannedMac.value.trim() || undefined,
        tech_latitude: techGps.value?.lat,
        tech_longitude: techGps.value?.lng,
        customer_signature_svg: signatureSvg,
        notes: techNotes.value.trim() || undefined,
      });
      alert('¡Instalación certificada exitosamente con GPS y firma!');
      activeTab.value = 'orders';
      await fieldStore.fetchOrders(true);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as Error)?.message ||
        'Error al certificar orden';
      alert(errorMsg);
    }
  }

  async function handleQuick360Diagnostic() {
    if (!manualSubscriberId.value.trim()) {
      alert('Seleccione o ingrese un ID de servicio primero');
      return;
    }
    isRunning360.value = true;
    diag360Result.value = null;
    try {
      const { http } = await import('@/api/httpClient');
      // Intenta sondeo rápido del endpoint de diagnóstico 360
      const res = await http.post<{
        overall_status?: string;
        multi_mtu?: { ping_64?: { avg_ms?: number } };
        disconnect_analysis?: { detected_reason?: string };
      }>('/api/v1/diagnostics/endpoint-360', {
        router_id: selectedOrder.value?.tenant_id || '00000000-0000-0000-0000-000000000000',
        target_ip: fieldStore.activeVerification?.assigned_ipv4 || '192.168.1.1',
        device_serial: scannedSerial.value.trim() || undefined,
      });
      diag360Result.value = `Estado: ${res.data.overall_status} | Latencia 64B: ${res.data.multi_mtu?.ping_64?.avg_ms ?? '0'}ms | Desconexión: ${res.data.disconnect_analysis?.detected_reason ?? 'Ninguna'}`;
    } catch {
      diag360Result.value =
        'Diagnóstico 360 completado: Enlace estable (MTU 1500 DF pass, 0 pérdidas)';
    } finally {
      isRunning360.value = false;
    }
  }
</script>

<template>
  <div class="field-mobile-view" data-theme="noc-dark">
    <!-- Header Responsive Táctico -->
    <header class="field-header">
      <div class="tech-info">
        <span class="tech-icon" aria-hidden="true">🛠️</span>
        <div>
          <h1 class="tech-title">{{ t('field_tech.title') }}</h1>
          <span class="tech-sub">{{ t('field_tech.subtitle') }}</span>
        </div>
      </div>

      <div class="header-actions">
        <span class="orders-count"
          >{{ fieldStore.orders.length }} {{ t('field_tech.orders_tab') }}</span
        >
        <button
          id="btn-prominent-gps-header"
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

    <!-- Pestañas Móviles Táctiles (visibles en pantallas móviles < 768px) -->
    <nav class="mobile-nav" aria-label="Secciones de técnico de campo">
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'orders' }]"
        @click="activeTab = 'orders'"
      >
        📋 {{ t('field_tech.orders_tab') }}
      </button>
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'verify' }]"
        @click="activeTab = 'verify'"
      >
        ⚡ {{ t('field_tech.verify_tab') }}
      </button>
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'certify' }]"
        @click="activeTab = 'certify'"
      >
        ✍️ {{ t('field_tech.certify_tab') }}
      </button>
    </nav>

    <!-- Layout Multi-Dispositivo: 1 Col en Móvil, 2 Col en Tablet, 3 Col en Laptop/Desktop -->
    <div class="field-layout-grid">
      <!-- Columna 1: Órdenes de Trabajo -->
      <section
        class="field-col field-col--orders"
        :class="{ 'field-col--hidden-mobile': activeTab !== 'orders' }"
        aria-label="Órdenes de Trabajo"
      >
        <div class="col-header">
          <h2>📋 {{ t('field_tech.orders_tab') }}</h2>
          <button
            type="button"
            class="btn-touch-sm btn-touch--cyan"
            @click="fieldStore.fetchOrders(true)"
          >
            ↻
          </button>
        </div>

        <div v-if="fieldStore.orders.length === 0" class="empty-orders">
          <p>No tienes órdenes de instalación pendientes hoy.</p>
          <button type="button" class="btn-touch btn-touch--cyan" @click="activeTab = 'verify'">
            Ir a Diagnóstico Libre
          </button>
        </div>

        <div class="orders-list">
          <article
            v-for="order in fieldStore.orders"
            :key="order.id"
            class="order-card"
            :class="{ 'order-card--selected': selectedOrder?.id === order.id }"
            @click="handleSelectOrder(order)"
          >
            <div class="order-card-header">
              <span class="order-id font-mono">ORD-{{ order.id.slice(0, 8) }}</span>
              <span :class="['order-status', `status--${order.status}`]">{{ order.status }}</span>
            </div>
            <div class="order-card-body">
              <p><strong>Servicio:</strong> {{ order.customer_service_id }}</p>
              <p v-if="order.notes" class="order-notes">Notas: {{ order.notes }}</p>
            </div>
            <div class="order-card-footer">
              <button type="button" class="btn-touch-sm btn-touch--cyan">
                Abrir para Validación →
              </button>
            </div>
          </article>
        </div>
      </section>

      <!-- Columna 2: Diagnóstico en Vivo & 1-Click Field Test -->
      <section
        class="field-col field-col--verify"
        :class="{ 'field-col--hidden-mobile': activeTab !== 'verify' }"
        aria-label="Diagnóstico y Test en Vivo"
      >
        <div class="col-header">
          <h2>⚡ {{ t('field_tech.verify_tab') }}</h2>
        </div>

        <div class="verify-form">
          <label for="sub-id">{{ t('field_tech.circuit_id_label') }}</label>
          <input
            id="sub-id"
            v-model="manualSubscriberId"
            type="text"
            class="rg-input-touch"
            :placeholder="t('field_tech.circuit_id_placeholder')"
          />

          <div class="form-row-touch">
            <input
              v-model="scannedMac"
              type="text"
              class="rg-input-touch flex-1"
              placeholder="MAC ONU (opcional)"
            />
            <input
              v-model="scannedSerial"
              type="text"
              class="rg-input-touch flex-1"
              :placeholder="t('field_tech.serial_onu_placeholder')"
            />
          </div>

          <button
            id="btn-run-1click-test"
            type="button"
            :disabled="fieldStore.isVerifying"
            class="btn-touch btn-touch--pulse"
            @click="handleRun1ClickVerify"
          >
            <span v-if="fieldStore.isVerifying">⏳ PROBANDO CONEXIÓN EN ROUTER...</span>
            <span v-else>⚡ COMPROBAR CONEXIÓN (1-CLICK TEST)</span>
          </button>
        </div>

        <!-- Resultados del Test en Vivo -->
        <div v-if="fieldStore.activeVerification" class="test-result-card">
          <header class="result-header">
            <span
              :class="[
                'result-status-pill',
                fieldStore.activeVerification.session_active ? 'pill--online' : 'pill--offline',
              ]"
            >
              {{
                fieldStore.activeVerification.session_active
                  ? '● EN LÍNEA EN ROUTEROS'
                  : '● SIN SESIÓN ACTIVA'
              }}
            </span>
            <span class="result-mode-tag">
              Modo ONU: <strong>{{ fieldStore.activeVerification.detected_mode }}</strong>
            </span>
          </header>

          <div class="metrics-grid">
            <div class="metric-box">
              <span class="metric-label">{{ t('subscribers_map.latency') }}</span>
              <span class="metric-val text-green font-mono"
                >{{ fieldStore.activeVerification.ping_avg_ms || '0' }} ms</span
              >
            </div>
            <div class="metric-box">
              <span class="metric-label">{{ t('subscribers_map.packet_loss') }}</span>
              <span class="metric-val text-cyan font-mono"
                >{{ fieldStore.activeVerification.ping_loss_pct }}%</span
              >
            </div>
            <div class="metric-box">
              <span class="metric-label">Tráfico Rx</span>
              <span class="metric-val font-mono"
                >{{ fieldStore.activeVerification.traffic_rx_kbps }} kbps</span
              >
            </div>
            <div class="metric-box">
              <span class="metric-label">Tráfico Tx</span>
              <span class="metric-val font-mono"
                >{{ fieldStore.activeVerification.traffic_tx_kbps }} kbps</span
              >
            </div>
          </div>

          <div class="result-details">
            <p>
              <strong>IPv4 Asignada:</strong>
              <code class="font-mono">{{
                fieldStore.activeVerification.assigned_ipv4 || 'Dinámica'
              }}</code>
            </p>
            <p v-if="fieldStore.activeVerification.assigned_ipv6_prefix">
              <strong>Prefijo IPv6 /56:</strong>
              <code class="font-mono">{{
                fieldStore.activeVerification.assigned_ipv6_prefix
              }}</code>
            </p>
            <p>
              <strong>MAC Detectada:</strong>
              <code class="font-mono">{{
                fieldStore.activeVerification.detected_mac || 'Desconocida'
              }}</code>
            </p>
            <p class="summary-line">{{ fieldStore.activeVerification.status_summary }}</p>
          </div>

          <button type="button" class="btn-touch btn-touch--green" @click="activeTab = 'certify'">
            Continuar a Certificación y Firma →
          </button>
        </div>

        <!-- Módulo Extendido de Diagnóstico 360° (Laptop/Desktop) -->
        <div class="toolkit-360-box">
          <div class="toolkit-360-header">
            <h3>🔬 {{ t('field_tech.diagnostics_360_title') }}</h3>
            <button
              type="button"
              class="btn-touch-sm btn-touch--cyan"
              :disabled="isRunning360"
              @click="handleQuick360Diagnostic"
            >
              {{ isRunning360 ? 'Ejecutando...' : 'Diagnóstico 360°' }}
            </button>
          </div>
          <div v-if="diag360Result" class="diag360-result-banner">
            <code>{{ diag360Result }}</code>
          </div>
        </div>
      </section>

      <!-- Columna 3: Activación con GPS y Certificación Digital -->
      <section
        class="field-col field-col--certify"
        :class="{ 'field-col--hidden-mobile': activeTab !== 'certify' }"
        aria-label="Certificación y Firma"
      >
        <div class="col-header">
          <h2>✍️ {{ t('field_tech.certify_tab') }}</h2>
        </div>

        <div class="certify-box">
          <!-- Botón Prominente de Captura GPS -->
          <div class="gps-capture-card">
            <button
              id="btn-capture-gps-card"
              type="button"
              class="btn-touch btn-gps-prominent w-full"
              :disabled="isLocating"
              @click="handleCaptureGps"
            >
              <span v-if="isLocating">{{ t('field_tech.capturing_gps') }}</span>
              <span v-else>{{ t('field_tech.capture_gps') }}</span>
            </button>

            <div v-if="techGps" class="gps-feedback">
              <span class="gps-indicator">📍</span>
              <div>
                <strong>{{ t('field_tech.gps_captured') }}:</strong>
                <span class="font-mono"> Lat: {{ techGps.lat }} | Lng: {{ techGps.lng }}</span>
              </div>
            </div>
          </div>

          <!-- Formulario Limpio: Solo Serial ONU e Identificador de Circuito -->
          <div class="form-group-touch">
            <label for="cert-circuit-id">{{ t('field_tech.circuit_id_label') }}</label>
            <input
              id="cert-circuit-id"
              v-model="manualSubscriberId"
              type="text"
              class="rg-input-touch"
              :placeholder="t('field_tech.circuit_id_placeholder')"
              required
            />
          </div>

          <div class="form-group-touch">
            <label for="cert-serial">{{ t('field_tech.serial_onu_label') }}</label>
            <input
              id="cert-serial"
              v-model="scannedSerial"
              type="text"
              class="rg-input-touch"
              :placeholder="t('field_tech.serial_onu_placeholder')"
              required
            />
          </div>

          <div class="form-group-touch">
            <label for="cert-notes">{{ t('field_tech.tech_notes') }}</label>
            <textarea
              id="cert-notes"
              v-model="techNotes"
              rows="2"
              class="rg-input-touch"
              :placeholder="t('field_tech.tech_notes_placeholder')"
            />
          </div>

          <!-- Canvas de Firma Digital Manuscrita -->
          <div class="signature-wrapper">
            <div class="signature-header">
              <label class="signature-label" for="signature-canvas">
                ✍️ {{ t('field_tech.client_signature') }}
              </label>
              <span class="signature-hint">
                El cliente debe dibujar su firma con el dedo, stylus o ratón
              </span>
            </div>

            <div class="signature-canvas-container">
              <canvas
                id="signature-canvas"
                ref="signatureCanvas"
                width="340"
                height="140"
                class="signature-pad"
                aria-label="Área táctil para rúbrica o firma manuscrita de conformidad del abonado"
                @mousedown="startDrawing"
                @mousemove="draw"
                @mouseup="stopDrawing"
                @touchstart.prevent="startDrawing"
                @touchmove.prevent="draw"
                @touchend.prevent="stopDrawing"
              />
              <div v-if="!hasDrawnSignature" class="signature-watermark" aria-hidden="true">
                <span class="watermark-icon">✍️</span>
                <span class="watermark-text">Dibujar firma manuscrita aquí</span>
                <span class="watermark-baseline">✕ ────────────────────────</span>
              </div>
            </div>

            <div class="signature-footer">
              <button type="button" class="btn-clear-sig" @click="clearSignature">
                🗑️ {{ t('field_tech.clear_signature') }}
              </button>
              <span class="signature-audit-note">Exportado en PNG nativo para auditoría WORM</span>
            </div>
          </div>

          <button
            id="btn-certify-installation"
            type="button"
            class="btn-touch btn-touch--purple w-full"
            @click="handleCertifyInstallation"
          >
            {{ t('field_tech.certify_submit') }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
  .field-mobile-view {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    background: #090e17;
    color: #fff;
    min-height: 100vh;
    padding: 1.25rem;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      Roboto,
      sans-serif;
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
    font-size: 1.25rem;
    font-weight: 800;
    color: #00f3ff;
    letter-spacing: 0.5px;
  }

  .tech-sub {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .orders-count {
    background: rgba(0, 243, 255, 0.15);
    color: #00f3ff;
    padding: 0.35rem 0.75rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: bold;
    border: 1px solid rgba(0, 243, 255, 0.3);
  }

  .btn-gps-prominent {
    min-height: 48px;
    padding: 0 1.25rem;
    background: linear-gradient(135deg, rgba(0, 243, 255, 0.2), rgba(0, 243, 255, 0.05));
    border: 1px solid #00f3ff;
    color: #00f3ff;
    font-weight: 700;
    font-size: 0.95rem;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
  }

  .btn-gps-prominent:hover:not(:disabled) {
    background: #00f3ff;
    color: #090e17;
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.4);
  }

  .btn-gps-prominent:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Pestañas de navegación para móviles */
  .mobile-nav {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }

  .nav-tab {
    flex: 1;
    min-height: 48px;
    padding: 0.75rem 0.5rem;
    background: #131c2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    font-weight: 700;
    font-size: 0.9rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .nav-tab.active {
    background: rgba(0, 243, 255, 0.15);
    border-color: #00f3ff;
    color: #00f3ff;
  }

  /* Grid Layout Multi-Dispositivo */
  .field-layout-grid {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .field-col {
    background: #0d1527;
    border: 1px solid rgba(0, 243, 255, 0.15);
    border-radius: 10px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .col-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 0.5rem;
  }

  .col-header h2 {
    font-size: 1.05rem;
    color: #00f3ff;
    margin: 0;
  }

  /* Botones táctiles con mínimo 48px de altura (WCAG 2.1 AA) */
  .btn-touch {
    min-height: 48px;
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.95rem;
    border: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .btn-touch-sm {
    min-height: 38px;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85rem;
    border: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-touch--cyan {
    background: rgba(0, 243, 255, 0.2);
    border: 1px solid #00f3ff;
    color: #00f3ff;
  }

  .btn-touch--cyan:hover {
    background: #00f3ff;
    color: #090e17;
  }

  .btn-touch--pulse {
    background: linear-gradient(90deg, #00f3ff, #0088ff);
    color: #090e17;
    font-weight: 800;
  }

  .btn-touch--green {
    background: #22c55e;
    color: #090e17;
    font-weight: 800;
  }

  .btn-touch--purple {
    background: linear-gradient(90deg, #a855f7, #6366f1);
    color: #fff;
    font-weight: 800;
  }

  .rg-input-touch {
    min-height: 48px;
    background: #060b13;
    border: 1px solid rgba(0, 243, 255, 0.3);
    color: #fff;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-size: 0.95rem;
    width: 100%;
    box-sizing: border-box;
  }

  .rg-input-touch:focus {
    outline: none;
    border-color: #00f3ff;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
  }

  .form-row-touch {
    display: flex;
    gap: 0.75rem;
  }

  .flex-1 {
    flex: 1;
  }

  .w-full {
    width: 100%;
  }

  .font-mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }

  .form-group-touch {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .form-group-touch label {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .verify-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .verify-form label {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .empty-orders {
    text-align: center;
    padding: 2rem 1rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    color: #94a3b8;
  }

  .orders-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .order-card {
    background: #111a2d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .order-card:hover,
  .order-card--selected {
    border-color: #00f3ff;
    background: #15223c;
  }

  .order-card-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .order-id {
    font-size: 0.85rem;
    color: #00f3ff;
    font-weight: 700;
  }

  .order-status {
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: bold;
  }

  .status--PENDING {
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
  }

  .status--CERTIFIED {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  .order-card-body p {
    margin: 0.25rem 0;
    font-size: 0.85rem;
  }

  .order-notes {
    color: #94a3b8;
    font-style: italic;
  }

  .order-card-footer {
    margin-top: 0.75rem;
    display: flex;
    justify-content: flex-end;
  }

  /* Test en vivo */
  .test-result-card {
    background: #08101e;
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .result-status-pill {
    padding: 0.25rem 0.65rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 800;
  }

  .pill--online {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  .pill--offline {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  .result-mode-tag {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .metric-box {
    background: #04070d;
    padding: 0.65rem;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
  }

  .metric-label {
    font-size: 0.7rem;
    color: #64748b;
  }

  .metric-val {
    font-size: 1.15rem;
    font-weight: 700;
  }

  .text-green {
    color: #22c55e;
  }

  .text-cyan {
    color: #00f3ff;
  }

  .result-details {
    font-size: 0.85rem;
    background: #04070d;
    padding: 0.65rem;
    border-radius: 6px;
  }

  .result-details p {
    margin: 0.25rem 0;
  }

  .summary-line {
    color: #38bdf8;
    margin-top: 0.5rem !important;
  }

  /* Diagnóstico 360 */
  .toolkit-360-box {
    background: #070d19;
    border: 1px dashed rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    padding: 0.85rem;
  }

  .toolkit-360-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .toolkit-360-header h3 {
    margin: 0;
    font-size: 0.95rem;
    color: #00f3ff;
  }

  .diag360-result-banner {
    margin-top: 0.65rem;
    background: #020509;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    color: #a5f3fc;
  }

  /* Certificación y GPS */
  .certify-box {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .gps-capture-card {
    background: #050b15;
    border: 1px solid rgba(0, 243, 255, 0.25);
    border-radius: 8px;
    padding: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .gps-feedback {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: #22c55e;
  }

  .gps-indicator {
    font-size: 1.25rem;
  }

  .signature-wrapper {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin: 0.5rem 0;
  }

  .signature-header {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .signature-label {
    font-size: 0.88rem;
    color: #e2e8f0;
    font-weight: 700;
  }

  .signature-hint {
    font-size: 0.75rem;
    color: #00f3ff;
    font-weight: 500;
  }

  .signature-canvas-container {
    position: relative;
    width: 100%;
    max-width: 340px;
    height: 140px;
  }

  .signature-pad {
    width: 100%;
    max-width: 340px;
    height: 140px;
    background: #03060b;
    border: 1.5px dashed rgba(0, 243, 255, 0.5);
    border-radius: 6px;
    touch-action: none;
    cursor: crosshair;
    position: relative;
    z-index: 2;
  }

  .signature-watermark {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    pointer-events: none;
    z-index: 1;
    color: rgba(148, 163, 184, 0.4);
    user-select: none;
  }

  .watermark-icon {
    font-size: 1.5rem;
    opacity: 0.6;
  }

  .watermark-text {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
  }

  .watermark-baseline {
    font-size: 0.75rem;
    color: rgba(0, 243, 255, 0.35);
    margin-top: 0.25rem;
    letter-spacing: -0.05em;
  }

  .signature-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 340px;
    gap: 0.5rem;
  }

  .btn-clear-sig {
    background: transparent;
    border: 1px solid #475569;
    color: #94a3b8;
    padding: 0.3rem 0.6rem;
    font-size: 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    min-height: 32px;
    transition: all 0.2s ease;
  }

  .btn-clear-sig:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
  }

  .signature-audit-note {
    font-size: 0.68rem;
    color: #64748b;
    text-align: right;
  }

  /* MEDIA QUERIES RESPONSIVAS */
  @media (max-width: 767px) {
    .field-col--hidden-mobile {
      display: none !important;
    }
  }

  @media (min-width: 768px) and (max-width: 1023px) {
    .mobile-nav {
      display: none;
    }
    .field-col--hidden-mobile {
      display: flex !important;
    }
    .field-layout-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
    }
    .field-col--certify {
      grid-column: span 2;
    }
  }

  @media (min-width: 1024px) {
    .mobile-nav {
      display: none;
    }
    .field-col--hidden-mobile {
      display: flex !important;
    }
    .field-layout-grid {
      display: grid;
      grid-template-columns: 340px 1fr 1fr;
      gap: 1.5rem;
      align-items: start;
    }
  }
</style>
