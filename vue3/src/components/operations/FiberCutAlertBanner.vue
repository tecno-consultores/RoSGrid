<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';

const fieldStore = useFieldOpsStore();
const isChecking = ref(false);

onMounted(async () => {
  await fieldStore.detectFiberCuts(3);
});

async function handleManualDetection() {
  isChecking.value = true;
  await fieldStore.detectFiberCuts(3);
  isChecking.value = false;
}
</script>

<template>
  <div v-if="fieldStore.incidents.length > 0" class="fiber-cut-alert-wrapper" role="alert" aria-live="assertive">
    <div
      v-for="inc in fieldStore.incidents"
      :key="inc.id"
      class="fiber-cut-banner"
    >
      <div class="banner-icon-container">
        <span class="warning-flashing-icon">⚠️</span>
      </div>

      <div class="banner-content">
        <div class="banner-title-row">
          <span class="banner-tag">ALERTA CRÍTICA GPON / FIBRA</span>
          <span class="banner-timestamp">{{ new Date(inc.detected_at).toLocaleTimeString() }}</span>
        </div>
        <h4 class="banner-headline">{{ inc.incident_summary }}</h4>
        <div class="banner-details">
          <span>Puerto PON: <strong>{{ inc.pon_port }}</strong></span>
          <span v-if="inc.optical_box">Caja / NAP: <strong>{{ inc.optical_box }}</strong></span>
          <span class="badge-affected">Abonados Afectados: {{ inc.affected_onus_count }}</span>
        </div>
      </div>

      <div class="banner-actions">
        <button
          type="button"
          class="btn-banner-action"
          @click="handleManualDetection"
          :disabled="isChecking"
        >
          🔄 Re-verificar
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fiber-cut-alert-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.fiber-cut-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: linear-gradient(90deg, rgba(255, 51, 102, 0.25), rgba(18, 27, 45, 0.9));
  border: 1px solid #ff3366;
  border-left: 5px solid #ff3366;
  border-radius: 8px;
  padding: 0.85rem 1.25rem;
  box-shadow: 0 0 20px rgba(255, 51, 102, 0.3);
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: #ff3366; }
  50% { border-color: #ff99bb; }
}

.banner-icon-container {
  font-size: 2rem;
}

.warning-flashing-icon {
  display: inline-block;
  animation: flash-shake 1s infinite;
}

@keyframes flash-shake {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15) rotate(5deg); }
}

.banner-content {
  flex: 1;
}

.banner-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.banner-tag {
  background: #ff3366;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
  letter-spacing: 0.5px;
}

.banner-timestamp {
  font-size: 0.75rem;
  color: #94a3b8;
}

.banner-headline {
  margin: 0.15rem 0 0.4rem 0;
  font-size: 1rem;
  font-weight: 800;
  color: #fff;
}

.banner-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.8rem;
  color: #cbd5e1;
}

.badge-affected {
  background: rgba(255, 51, 102, 0.2);
  color: #ff6688;
  font-weight: bold;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.banner-actions {
  display: flex;
  align-items: center;
}

.btn-banner-action {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.45rem 0.85rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-banner-action:hover {
  background: #ff3366;
  border-color: #ff3366;
}
</style>
