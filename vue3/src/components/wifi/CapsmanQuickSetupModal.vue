<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->
<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from '@/composables/useI18n';
import { http } from '@/api/httpClient';
import type { WifiQuickSetupPayload } from '@/types';

const props = defineProps<{
  show: boolean;
  routerId: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const { t } = useI18n();

const form = ref<WifiQuickSetupPayload>({
  corporate_ssid: 'RoSGrid-Corporate',
  corporate_passphrase: '',
  guest_ssid_enabled: true,
  guest_ssid: 'RoSGrid-Guests',
  guest_passphrase: '',
  guest_vlan_id: 200,
  bridge_name: 'bridge',
});

const isSubmitting = ref(false);
const errorMsg = ref('');

function validateForm(): boolean {
  errorMsg.value = '';
  if (!form.value.corporate_ssid.trim()) {
    errorMsg.value = t('wifi.error_ssid_required', 'El SSID Corporativo es obligatorio.');
    return false;
  }
  if (!form.value.corporate_passphrase || form.value.corporate_passphrase.length < 8) {
    errorMsg.value = t('wifi.error_passphrase_len', 'La contraseña corporativa debe tener al menos 8 caracteres.');
    return false;
  }
  if (form.value.guest_ssid_enabled) {
    if (!form.value.guest_ssid?.trim()) {
      errorMsg.value = t('wifi.error_guest_ssid_required', 'El SSID de Invitados es obligatorio.');
      return false;
    }
    if (!form.value.guest_passphrase || form.value.guest_passphrase.length < 8) {
      errorMsg.value = t('wifi.error_guest_passphrase_len', 'La contraseña de invitados debe tener al menos 8 caracteres.');
      return false;
    }
    const vlan = Number(form.value.guest_vlan_id);
    if (isNaN(vlan) || vlan < 1 || vlan > 4094) {
      errorMsg.value = t('wifi.error_vlan_range', 'La VLAN de invitados debe estar entre 1 y 4094.');
      return false;
    }
  }
  return true;
}

async function handleDeploy() {
  if (!validateForm()) return;
  isSubmitting.value = true;
  errorMsg.value = '';
  try {
    await http.post(`/api/v1/wifi/capsman/${props.routerId}/quick-setup`, form.value);
    emit('saved');
    emit('close');
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || err.message || t('wifi.deploy_error', 'Error al desplegar asistente Wi-Fi.');
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div v-if="show" class="rg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="quick-setup-title">
    <div class="rg-modal-card">
      <header class="rg-modal-header">
        <h3 id="quick-setup-title" class="rg-modal-title">
          ⚡ {{ t('wifi.quick_setup_title', 'Asistente Wi-Fi Rápido en 1 Clic (CAPsMAN v7)') }}
        </h3>
        <button
          type="button"
          class="rg-btn-close"
          :aria-label="t('common.close', 'Cerrar')"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="rg-modal-body">
        <div class="rg-safe-mode-badge" role="status">
          🛡️ {{ t('wifi.safe_mode_note', 'Protegido por Safe Mode de 60 segundos con rollback automático.') }}
        </div>

        <div v-if="errorMsg" class="rg-alert-danger" role="alert">
          {{ errorMsg }}
        </div>

        <fieldset class="rg-fieldset">
          <legend class="rg-legend">{{ t('wifi.corporate_network_legend', 'Red Corporativa (Principal)') }}</legend>
          <div class="rg-field-row">
            <label for="corp-ssid" class="rg-label">{{ t('wifi.label_ssid', 'SSID (Nombre Red):') }}</label>
            <input
              id="corp-ssid"
              v-model="form.corporate_ssid"
              type="text"
              class="rg-input"
              required
            />
          </div>
          <div class="rg-field-row">
            <label for="corp-pass" class="rg-label">{{ t('wifi.label_passphrase', 'Contraseña (WPA2/WPA3):') }}</label>
            <input
              id="corp-pass"
              v-model="form.corporate_passphrase"
              type="password"
              class="rg-input"
              placeholder="Mínimo 8 caracteres"
              required
            />
          </div>
        </fieldset>

        <fieldset class="rg-fieldset">
          <legend class="rg-legend">
            <label class="rg-checkbox-label">
              <input
                id="enable-guest-toggle"
                v-model="form.guest_ssid_enabled"
                type="checkbox"
                class="rg-checkbox"
              />
              {{ t('wifi.guest_network_legend', 'Habilitar Red de Invitados Aislada') }}
            </label>
          </legend>

          <template v-if="form.guest_ssid_enabled">
            <div class="rg-field-row">
              <label for="guest-ssid" class="rg-label">{{ t('wifi.label_guest_ssid', 'SSID Invitados:') }}</label>
              <input
                id="guest-ssid"
                v-model="form.guest_ssid"
                type="text"
                class="rg-input"
                required
              />
            </div>
            <div class="rg-field-row">
              <label for="guest-pass" class="rg-label">{{ t('wifi.label_guest_passphrase', 'Contraseña Invitados:') }}</label>
              <input
                id="guest-pass"
                v-model="form.guest_passphrase"
                type="password"
                class="rg-input"
                placeholder="Mínimo 8 caracteres"
                required
              />
            </div>
            <div class="rg-field-row">
              <label for="guest-vlan" class="rg-label">{{ t('wifi.label_guest_vlan', 'ID de VLAN (Datapath):') }}</label>
              <input
                id="guest-vlan"
                v-model.number="form.guest_vlan_id"
                type="number"
                min="1"
                max="4094"
                class="rg-input"
                required
              />
            </div>
          </template>
        </fieldset>
      </div>

      <footer class="rg-modal-footer">
        <button
          type="button"
          class="rg-btn-secondary"
          :disabled="isSubmitting"
          @click="emit('close')"
        >
          {{ t('common.cancel', 'Cancelar') }}
        </button>
        <button
          id="btn-deploy-wizard"
          type="button"
          class="rg-btn-primary"
          :disabled="isSubmitting"
          @click="handleDeploy"
        >
          <span v-if="isSubmitting">{{ t('common.deploying', 'Desplegando...') }}</span>
          <span v-else>🚀 {{ t('wifi.btn_deploy_quick', 'Desplegar Redes Ahora') }}</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.rg-modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.rg-modal-card {
  background: #0f172a;
  border: 1px solid #00d2ff;
  border-radius: 8px;
  width: 90%;
  max-width: 520px;
  box-shadow: 0 10px 25px -5px rgba(0, 210, 255, 0.25);
  color: #f8fafc;
  display: flex;
  flex-direction: column;
}
.rg-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1e293b;
}
.rg-modal-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #00d2ff;
}
.rg-btn-close {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
}
.rg-modal-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 70vh;
  overflow-y: auto;
}
.rg-safe-mode-badge {
  background: rgba(0, 210, 255, 0.1);
  border: 1px solid rgba(0, 210, 255, 0.3);
  color: #a5f3fc;
  font-size: 0.825rem;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}
.rg-alert-danger {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}
.rg-fieldset {
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.rg-legend {
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
  padding: 0 0.4rem;
}
.rg-field-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.rg-label {
  font-size: 0.8rem;
  color: #94a3b8;
}
.rg-input {
  background: #1e293b;
  border: 1px solid #475569;
  color: #f8fafc;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
}
.rg-input:focus {
  outline: none;
  border-color: #00d2ff;
  box-shadow: 0 0 0 1px #00d2ff;
}
.rg-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
.rg-checkbox {
  accent-color: #00d2ff;
}
.rg-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #1e293b;
}
.rg-btn-secondary {
  background: #334155;
  border: 1px solid #475569;
  color: #f8fafc;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}
.rg-btn-primary {
  background: #0284c7;
  border: 1px solid #00d2ff;
  color: #ffffff;
  padding: 0.5rem 1.25rem;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.875rem;
}
.rg-btn-primary:hover:not(:disabled) {
  background: #00d2ff;
  color: #0f172a;
}
.rg-btn-primary:disabled,
.rg-btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
