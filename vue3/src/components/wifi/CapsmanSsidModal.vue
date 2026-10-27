<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from '@/composables/useI18n';
import { http } from '@/api/httpClient';
import type { WifiSsidProfile } from '@/types';

const props = defineProps<{
  show: boolean;
  routerId: string;
  editItem?: WifiSsidProfile | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const { t } = useI18n();

const form = ref({
  name: '',
  ssid: '',
  security_profile: '',
  vlan_id: null as number | null,
  client_isolation: true,
  hide_ssid: false,
  disabled: false,
  comment: '',
});

const isSubmitting = ref(false);
const errorMsg = ref('');

watch(
  () => props.editItem,
  (item) => {
    if (item) {
      form.value = {
        name: item.name || '',
        ssid: item.ssid || '',
        security_profile: item.security_profile || item.security_type || '',
        vlan_id: item.vlan_id ?? null,
        client_isolation: Boolean(item.client_isolation),
        hide_ssid: Boolean(item.hide_ssid),
        disabled: Boolean(item.disabled),
        comment: item.comment || '',
      };
    } else {
      form.value = {
        name: '',
        ssid: '',
        security_profile: '',
        vlan_id: null,
        client_isolation: true,
        hide_ssid: false,
        disabled: false,
        comment: '',
      };
    }
  },
  { immediate: true },
);

async function handleSave() {
  errorMsg.value = '';
  if (!form.value.name.trim()) {
    errorMsg.value = t('wifi.error_name_required', 'El nombre de la configuración es obligatorio.');
    return;
  }
  if (!form.value.ssid.trim()) {
    errorMsg.value = t('wifi.error_ssid_required', 'El SSID a emitir es obligatorio.');
    return;
  }

  isSubmitting.value = true;
  try {
    if (props.editItem) {
      await http.patch(
        `/api/v1/wifi/capsman/${props.routerId}/configurations/${encodeURIComponent(props.editItem.id)}`,
        {
          ssid: form.value.ssid,
          security_profile: form.value.security_profile || undefined,
          vlan_id: form.value.vlan_id ?? undefined,
          client_isolation: form.value.client_isolation,
          hide_ssid: form.value.hide_ssid,
          disabled: form.value.disabled,
          comment: form.value.comment,
        },
      );
    } else {
      await http.post(
        `/api/v1/wifi/capsman/${props.routerId}/configurations`,
        form.value,
      );
    }
    emit('saved');
    emit('close');
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || err.message || t('wifi.save_error', 'Error al guardar configuración SSID.');
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div v-if="show" class="rg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ssid-modal-title">
    <div class="rg-modal-card">
      <header class="rg-modal-header">
        <h3 id="ssid-modal-title" class="rg-modal-title">
          📶 {{ editItem ? t('wifi.edit_ssid_title', 'Modificar Configuración SSID') : t('wifi.new_ssid_title', 'Nueva Configuración SSID') }}
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

        <div class="rg-field-row">
          <label for="ssid-cfg-name" class="rg-label">{{ t('wifi.label_cfg_name', 'Nombre de Configuración:') }}</label>
          <input
            id="ssid-cfg-name"
            v-model="form.name"
            type="text"
            class="rg-input"
            placeholder="cfg-corporate-vlan20"
            :disabled="Boolean(editItem)"
            required
          />
        </div>

        <div class="rg-field-row">
          <label for="ssid-name" class="rg-label">{{ t('wifi.label_ssid', 'SSID Emitido (Nombre WiFi):') }}</label>
          <input
            id="ssid-name"
            v-model="form.ssid"
            type="text"
            class="rg-input"
            placeholder="RoSGrid-Secure"
            required
          />
        </div>

        <div class="rg-field-row">
          <label for="ssid-sec-profile" class="rg-label">{{ t('wifi.label_sec_profile', 'Perfil de Seguridad:') }}</label>
          <input
            id="ssid-sec-profile"
            v-model="form.security_profile"
            type="text"
            class="rg-input"
            placeholder="sec-corporate"
          />
        </div>

        <div class="rg-field-row">
          <label for="ssid-vlan-id" class="rg-label">{{ t('wifi.label_vlan_id', 'VLAN ID (Datapath Tagging):') }}</label>
          <input
            id="ssid-vlan-id"
            v-model.number="form.vlan_id"
            type="number"
            min="1"
            max="4094"
            class="rg-input"
            placeholder="Dejar vacío para VLAN nativa"
          />
        </div>

        <div class="rg-checkbox-col">
          <label class="rg-checkbox-label">
            <input
              id="ssid-client-iso"
              v-model="form.client_isolation"
              type="checkbox"
              class="rg-checkbox"
            />
            {{ t('wifi.label_client_iso', 'Aislamiento de Clientes (Client Isolation / No peer-to-peer)') }}
          </label>
          <label class="rg-checkbox-label">
            <input
              id="ssid-hide"
              v-model="form.hide_ssid"
              type="checkbox"
              class="rg-checkbox"
            />
            {{ t('wifi.label_hide_ssid', 'Ocultar SSID (Hide SSID broadcast)') }}
          </label>
          <label class="rg-checkbox-label">
            <input
              id="ssid-disabled"
              v-model="form.disabled"
              type="checkbox"
              class="rg-checkbox"
            />
            {{ t('wifi.label_disabled', 'Deshabilitar SSID temporalmente') }}
          </label>
        </div>
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
          id="btn-save-ssid"
          type="button"
          class="rg-btn-primary"
          :disabled="isSubmitting"
          @click="handleSave"
        >
          {{ isSubmitting ? t('common.saving', 'Guardando...') : (editItem ? t('common.save_changes', 'Guardar Cambios') : t('common.create', 'Crear Configuración')) }}
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
.rg-checkbox-col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.rg-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
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
