<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import { http } from '@/api/httpClient';
import type { WifiSecurityProfileItem } from '@/types';

const props = defineProps<{
  show: boolean;
  routerId: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated'): void;
}>();

const { t } = useI18n();

const profiles = ref<WifiSecurityProfileItem[]>([]);
const isLoading = ref(false);
const errorMsg = ref('');

// Formulario nuevo perfil
const showAddForm = ref(false);
const newProfile = ref({
  name: '',
  authentication_types: ['wpa2-psk', 'wpa3-psk'],
  passphrase: '',
  wps_disabled: true,
  ft_enabled: true,
  comment: '',
});
const isCreating = ref(false);

async function fetchProfiles() {
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const res = await http.get<WifiSecurityProfileItem[]>(
      `/api/v1/wifi/capsman/${props.routerId}/security-profiles`,
    );
    profiles.value = res.data || [];
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || err.message || t('wifi.fetch_sec_error', 'Error al cargar perfiles de seguridad.');
  } finally {
    isLoading.value = false;
  }
}

async function handleCreateProfile() {
  errorMsg.value = '';
  if (!newProfile.value.name.trim()) {
    errorMsg.value = t('wifi.error_profile_name_required', 'El nombre del perfil es obligatorio.');
    return;
  }
  if (!newProfile.value.passphrase || newProfile.value.passphrase.length < 8) {
    errorMsg.value = t('wifi.error_passphrase_len', 'La contraseña debe tener al menos 8 caracteres.');
    return;
  }

  isCreating.value = true;
  try {
    await http.post(
      `/api/v1/wifi/capsman/${props.routerId}/security-profiles`,
      newProfile.value,
    );
    showAddForm.value = false;
    newProfile.value = {
      name: '',
      authentication_types: ['wpa2-psk', 'wpa3-psk'],
      passphrase: '',
      wps_disabled: true,
      ft_enabled: true,
      comment: '',
    };
    await fetchProfiles();
    emit('updated');
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || err.message || t('wifi.create_sec_error', 'Error creando perfil.');
  } finally {
    isCreating.value = false;
  }
}

async function handleDeleteProfile(secId: string) {
  if (!confirm(t('wifi.confirm_delete_profile', '¿Eliminar este perfil de seguridad?'))) return;
  try {
    await http.delete(`/api/v1/wifi/capsman/${props.routerId}/security-profiles/${encodeURIComponent(secId)}`);
    await fetchProfiles();
    emit('updated');
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || err.message || t('wifi.delete_sec_error', 'Error eliminando perfil.');
  }
}

onMounted(() => {
  if (props.show && props.routerId) {
    fetchProfiles();
  }
});
</script>

<template>
  <div v-if="show" class="rg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="sec-profiles-title">
    <div class="rg-modal-card">
      <header class="rg-modal-header">
        <h3 id="sec-profiles-title" class="rg-modal-title">
          🔐 {{ t('wifi.sec_profiles_title', 'Perfiles de Seguridad Wi-Fi (WPA2 / WPA3)') }}
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
        <div v-if="errorMsg" class="rg-alert-danger" role="alert">
          {{ errorMsg }}
        </div>

        <div class="rg-toolbar">
          <button
            id="btn-toggle-add-sec"
            type="button"
            class="rg-btn-primary"
            @click="showAddForm = !showAddForm"
          >
            {{ showAddForm ? t('common.cancel', 'Cancelar') : `+ ${t('wifi.btn_add_sec_profile', 'Nuevo Perfil')}` }}
          </button>
          <button
            type="button"
            class="rg-btn-secondary"
            :disabled="isLoading"
            @click="fetchProfiles"
          >
            🔄 {{ t('common.refresh', 'Refrescar') }}
          </button>
        </div>

        <!-- Formulario nuevo perfil -->
        <div v-if="showAddForm" class="rg-add-form">
          <h4 class="rg-subheading">{{ t('wifi.create_sec_heading', 'Crear Perfil WPA2/WPA3') }}</h4>
          <div class="rg-field-row">
            <label for="new-sec-name" class="rg-label">{{ t('wifi.label_name', 'Nombre Perfil:') }}</label>
            <input id="new-sec-name" v-model="newProfile.name" type="text" class="rg-input" placeholder="sec-enterprise" />
          </div>
          <div class="rg-field-row">
            <label for="new-sec-pass" class="rg-label">{{ t('wifi.label_passphrase', 'Contraseña (PSK):') }}</label>
            <input id="new-sec-pass" v-model="newProfile.passphrase" type="password" class="rg-input" placeholder="Mínimo 8 caracteres" />
          </div>
          <div class="rg-checkbox-row">
            <label class="rg-checkbox-label">
              <input v-model="newProfile.ft_enabled" type="checkbox" class="rg-checkbox" />
              {{ t('wifi.label_ft_roaming', 'Fast Roaming 802.11r (FT)') }}
            </label>
            <label class="rg-checkbox-label">
              <input v-model="newProfile.wps_disabled" type="checkbox" class="rg-checkbox" />
              {{ t('wifi.label_wps_disable', 'Deshabilitar WPS (Seguridad CIS)') }}
            </label>
          </div>
          <button
            id="btn-save-sec-profile"
            type="button"
            class="rg-btn-primary"
            :disabled="isCreating"
            @click="handleCreateProfile"
          >
            {{ isCreating ? t('common.saving', 'Guardando...') : t('common.save', 'Guardar Perfil') }}
          </button>
        </div>

        <!-- Tabla de perfiles existentes -->
        <div class="rg-table-container">
          <table class="rg-table" :aria-label="t('wifi.sec_profiles_table_aria', 'Perfiles de seguridad')">
            <thead>
              <tr>
                <th scope="col">{{ t('wifi.th_name', 'Nombre') }}</th>
                <th scope="col">{{ t('wifi.th_auth_types', 'Autenticación') }}</th>
                <th scope="col">{{ t('wifi.th_ft', 'Fast Roaming') }}</th>
                <th scope="col">{{ t('wifi.th_actions', 'Acciones') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in profiles" :key="p.id" class="rg-tr">
                <td class="font-bold text-cyan">{{ p.name }}</td>
                <td>{{ p.authentication_types.join(', ') }}</td>
                <td>
                  <span class="badge" :class="p.ft_enabled ? 'badge-success' : 'badge-subtle'">
                    {{ p.ft_enabled ? '802.11r' : 'Estándar' }}
                  </span>
                </td>
                <td>
                  <button
                    type="button"
                    class="rg-btn-danger-sm"
                    :aria-label="`${t('common.delete', 'Eliminar')} ${p.name}`"
                    @click="handleDeleteProfile(p.id)"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
              <tr v-if="profiles.length === 0 && !isLoading">
                <td colspan="4" class="text-center text-subtle">
                  {{ t('wifi.no_sec_profiles', 'No hay perfiles configurados.') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <footer class="rg-modal-footer">
        <button type="button" class="rg-btn-secondary" @click="emit('close')">
          {{ t('common.close', 'Cerrar') }}
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
  max-width: 620px;
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
.rg-toolbar {
  display: flex;
  justify-content: space-between;
}
.rg-add-form {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.rg-subheading {
  margin: 0;
  font-size: 0.95rem;
  color: #00d2ff;
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
  background: #0f172a;
  border: 1px solid #475569;
  color: #f8fafc;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
}
.rg-checkbox-row {
  display: flex;
  gap: 1rem;
}
.rg-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.rg-checkbox {
  accent-color: #00d2ff;
}
.rg-table-container {
  overflow-x: auto;
  border: 1px solid #1e293b;
  border-radius: 6px;
}
.rg-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.rg-table th,
.rg-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #1e293b;
}
.rg-table th {
  background: #1e293b;
  color: #94a3b8;
}
.text-cyan {
  color: #00d2ff;
}
.font-bold {
  font-weight: 700;
}
.badge-success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}
.badge-subtle {
  background: #334155;
  color: #94a3b8;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}
.rg-btn-danger-sm {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid #ef4444;
  color: #ef4444;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}
.rg-modal-footer {
  display: flex;
  justify-content: flex-end;
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
.rg-alert-danger {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}
</style>
