<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
import type { FieldOrder } from '@/types';

const fieldStore = useFieldOpsStore();

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
  if (!navigator.geolocation) {
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
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || 'Error al certificar orden');
  }
}
</script>

<template>
  <div class="field-mobile-view">
    <!-- Header Móvil Táctico -->
    <header class="mobile-header">
      <div class="tech-info">
        <span class="tech-icon" aria-hidden="true">🛠️</span>
        <div>
          <h1 class="tech-title">TÉCNICO DE CAMPO</h1>
          <span class="tech-sub">Toolkit de Certificación & Diagnóstico</span>
        </div>
      </div>
      <span class="orders-count">{{ fieldStore.orders.length }} Órdenes</span>
    </header>

    <!-- Pestañas Móviles Táctiles -->
    <nav class="mobile-nav" aria-label="Secciones de técnico de campo">
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'orders' }]"
        @click="activeTab = 'orders'"
      >
        📋 Órdenes
      </button>
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'verify' }]"
        @click="activeTab = 'verify'"
      >
        ⚡ Test 1-Click
      </button>
      <button
        type="button"
        :class="['nav-tab', { active: activeTab === 'certify' }]"
        @click="activeTab = 'certify'"
      >
        ✍️ Certificar
      </button>
    </nav>

    <!-- Tab 1: Órdenes Asignadas -->
    <section v-if="activeTab === 'orders'" class="tab-content">
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
          @click="handleSelectOrder(order)"
        >
          <div class="order-card-header">
            <span class="order-id">ORD-{{ order.id.slice(0, 8) }}</span>
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

    <!-- Tab 2: Verificación en Vivo (1-Click Field Test) -->
    <section v-if="activeTab === 'verify'" class="tab-content">
      <div class="verify-form">
        <label for="sub-id">ID de Servicio o Cédula / Código del Abonado</label>
        <input
          id="sub-id"
          v-model="manualSubscriberId"
          type="text"
          class="rg-input-touch"
          placeholder="Pegar ID o escanear QR..."
        />

        <div class="form-row-touch">
          <input
            v-model="scannedMac"
            type="text"
            class="rg-input-touch flex-1"
            placeholder="MAC ONU (ej: 48:8F:5A:11:22:33)"
          />
          <input
            v-model="scannedSerial"
            type="text"
            class="rg-input-touch flex-1"
            placeholder="Serial ONU (ej: ZTEGC1234567)"
          />
        </div>

        <button
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
            {{ fieldStore.activeVerification.session_active ? '● EN LÍNEA EN ROUTEROS' : '● SIN SESIÓN ACTIVA' }}
          </span>
          <span class="result-mode-tag">
            Modo ONU: <strong>{{ fieldStore.activeVerification.detected_mode }}</strong>
          </span>
        </header>

        <div class="metrics-grid">
          <div class="metric-box">
            <span class="metric-label">Latencia (Ping)</span>
            <span class="metric-val text-green">{{ fieldStore.activeVerification.ping_avg_ms || '0' }} ms</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">Pérdida Paquetes</span>
            <span class="metric-val text-cyan">{{ fieldStore.activeVerification.ping_loss_pct }}%</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">Tráfico Rx</span>
            <span class="metric-val">{{ fieldStore.activeVerification.traffic_rx_kbps }} kbps</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">Tráfico Tx</span>
            <span class="metric-val">{{ fieldStore.activeVerification.traffic_tx_kbps }} kbps</span>
          </div>
        </div>

        <div class="result-details">
          <p><strong>IPv4 Asignada:</strong> {{ fieldStore.activeVerification.assigned_ipv4 || 'Dinámica' }}</p>
          <p v-if="fieldStore.activeVerification.assigned_ipv6_prefix">
            <strong>Prefijo IPv6 /56:</strong> {{ fieldStore.activeVerification.assigned_ipv6_prefix }}
          </p>
          <p><strong>MAC Detectada:</strong> {{ fieldStore.activeVerification.detected_mac || 'Desconocida' }}</p>
          <p class="summary-line">{{ fieldStore.activeVerification.status_summary }}</p>
        </div>

        <button type="button" class="btn-touch btn-touch--green" @click="activeTab = 'certify'">
          Continuar a Certificación y Firma →
        </button>
      </div>
    </section>

    <!-- Tab 3: Certificación y Firma Digital -->
    <section v-if="activeTab === 'certify'" class="tab-content">
      <div class="certify-box">
        <h3>✍️ Certificación Digital de Instalación</h3>

        <div class="gps-capture-box">
          <button
            type="button"
            class="btn-touch-sm btn-touch--cyan"
            :disabled="isLocating"
            @click="handleCaptureGps"
          >
            {{ isLocating ? 'Capturando GPS...' : '📍 Capturar Coordenadas GPS' }}
          </button>
          <div v-if="techGps" class="gps-coords">
            Lat: {{ techGps.lat }} | Lng: {{ techGps.lng }}
          </div>
        </div>

        <div class="form-group-touch">
          <label for="cert-serial">Serial de la ONU Definitivo</label>
          <input
            id="cert-serial"
            v-model="scannedSerial"
            type="text"
            class="rg-input-touch"
            placeholder="Escanear serial ONU..."
            required
          />
        </div>

        <div class="form-group-touch">
          <label for="cert-notes">Observaciones del Técnico</label>
          <textarea
            id="cert-notes"
            v-model="techNotes"
            rows="2"
            class="rg-input-touch"
            placeholder="Detalles del cableado, niveles de potencia óptica, etc."
          />
        </div>

        <!-- Canvas de Firma Digital -->
        <div class="signature-wrapper">
          <label class="signature-label">Firma de Conformidad del Cliente:</label>
          <canvas
            ref="signatureCanvas"
            width="340"
            height="140"
            class="signature-pad"
            @mousedown="startDrawing"
            @mousemove="draw"
            @mouseup="stopDrawing"
            @touchstart.prevent="startDrawing"
            @touchmove.prevent="draw"
            @touchend.prevent="stopDrawing"
          />
          <button type="button" class="btn-clear-sig" @click="clearSignature">
            Borrar Firma
          </button>
        </div>

        <button type="button" class="btn-touch btn-touch--purple" @click="handleCertifyInstallation">
          🚀 Finalizar & Certificar Instalación
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.field-mobile-view {
  max-width: 480px;
  margin: 0 auto;
  background: #090e17;
  color: #fff;
  min-height: 100vh;
  padding: 1rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(0, 243, 255, 0.2);
  margin-bottom: 1rem;
}

.tech-info {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.tech-icon {
  font-size: 1.75rem;
}

.tech-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: #00f3ff;
  letter-spacing: 0.5px;
}

.tech-sub {
  font-size: 0.7rem;
  color: #94a3b8;
}

.orders-count {
  background: rgba(0, 243, 255, 0.15);
  color: #00f3ff;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
}

.mobile-nav {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.nav-tab {
  flex: 1;
  padding: 0.65rem 0.5rem;
  background: #131c2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  font-weight: 700;
  font-size: 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-tab.active {
  background: rgba(0, 243, 255, 0.15);
  border-color: #00f3ff;
  color: #00f3ff;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.order-card {
  background: #111a2d;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s;
}

.order-card:hover {
  border-color: #00f3ff;
  transform: translateY(-2px);
}

.order-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.order-id {
  font-family: monospace;
  font-weight: bold;
  color: #00f3ff;
}

.order-status {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: bold;
}
.status--ASSIGNED { background: rgba(0, 150, 255, 0.2); color: #60a5fa; }
.status--CERTIFIED { background: rgba(0, 255, 136, 0.2); color: #00ff88; }

.verify-form, .certify-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-row-touch {
  display: flex;
  gap: 0.5rem;
}

.rg-input-touch {
  width: 100%;
  padding: 0.75rem 0.85rem;
  background: #131d31;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  color: #fff;
  font-size: 0.95rem;
  box-sizing: border-box;
}

.rg-input-touch:focus {
  border-color: #00f3ff;
  outline: none;
}

.btn-touch {
  width: 100%;
  min-height: 48px;
  padding: 0.85rem;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 800;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-touch-sm {
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  border: none;
  cursor: pointer;
}

.btn-touch--cyan {
  background: #00f3ff;
  color: #000;
}

.btn-touch--pulse {
  background: linear-gradient(90deg, #00f3ff, #0088ff);
  color: #000;
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
}

.btn-touch--green {
  background: #00ff88;
  color: #000;
}

.btn-touch--purple {
  background: #8a2be2;
  color: #fff;
}

.test-result-card {
  margin-top: 1rem;
  background: #111a2e;
  border: 1px solid #00f3ff;
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
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
}
.pill--online { background: rgba(0, 255, 136, 0.2); color: #00ff88; }
.pill--offline { background: rgba(255, 51, 102, 0.2); color: #ff3366; }

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
  background: #090e17;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-label {
  display: block;
  font-size: 0.65rem;
  color: #64748b;
}

.metric-val {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 800;
}
.text-green { color: #00ff88; }
.text-cyan { color: #00f3ff; }

.result-details {
  font-size: 0.8rem;
  color: #cbd5e1;
  background: rgba(0, 0, 0, 0.2);
  padding: 0.5rem;
  border-radius: 4px;
}

.signature-wrapper {
  margin: 0.75rem 0;
}

.signature-pad {
  background: #050811;
  border: 1px dashed rgba(0, 243, 255, 0.5);
  border-radius: 6px;
  width: 100%;
  height: 140px;
  touch-action: none;
}

.btn-clear-sig {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.75rem;
  text-decoration: underline;
  cursor: pointer;
  margin-top: 0.25rem;
}
</style>
