<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import { http } from '@/api/httpClient';
import type { WifiProvisioningRuleItem, WifiSsidProfile } from '@/types';

const AVAILABLE_BANDS = [
  '2ghz-ax',
  '5ghz-ax',
  '6ghz-ax',
  '2ghz-ac',
  '5ghz-ac',
  '2ghz-n',
  '5ghz-n',
];

const props = defineProps<{
  show: boolean;
  routerId: string;
  availableConfigs?: WifiSsidProfile[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated'): void;
}>();

const { t } = useI18n();

const rules = ref<WifiProvisioningRuleItem[]>([]);
const isLoading = ref(false);
const errorMsg = ref('');

const showAddForm = ref(false);
const isCreating = ref(false);
const newRule = ref({
  name: 'prov-all-bands',
  action: 'create-dynamic-enabled',
  master_configuration: '',
  slave_configurations_raw: '',
  supported_bands: ['2ghz-ax', '5ghz-ax', '6ghz-ax'] as string[],
  identity_regex: '.*',
  comment: '',
});

function toggleBand(band: string) {
  const idx = newRule.value.supported_bands.indexOf(band);
  if (idx >= 0) {
    newRule.value.supported_bands.splice(idx, 1);
  } else {
    newRule.value.supported_bands.push(band);
  }
}

async function fetchRules() {
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const res = await http.get<WifiProvisioningRuleItem[]>(
      `/api/v1/wifi/capsman/${props.routerId}/provisioning`,
    );
    rules.value = res.data || [];
  } catch (err: any) {
    errorMsg.value =
      err.response?.data?.detail ||
      err.message ||
      t('wifi.fetch_prov_error', 'Error al consultar reglas de aprovisionamiento.');
  } finally {
    isLoading.value = false;
  }
}

async function handleCreateRule() {
  errorMsg.value = '';
  if (!newRule.value.master_configuration.trim()) {
    errorMsg.value = t(
      'wifi.error_master_cfg_required',
      'Debe especificar la configuración maestra (master-configuration).',
    );
    return;
  }

  const slaves = newRule.value.slave_configurations_raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  isCreating.value = true;
  try {
    await http.post(`/api/v1/wifi/capsman/${props.routerId}/provisioning`, {
      name: newRule.value.name.trim() || 'prov-rule',
      action: newRule.value.action,
      master_configuration: newRule.value.master_configuration.trim(),
      slave_configurations: slaves,
      supported_bands: newRule.value.supported_bands,
      identity_regex: newRule.value.identity_regex.trim() || '.*',
      comment: newRule.value.comment.trim() || null,
    });
    showAddForm.value = false;
    newRule.value = {
      name: 'prov-all-bands',
      action: 'create-dynamic-enabled',
      master_configuration: '',
      slave_configurations_raw: '',
      supported_bands: ['2ghz-ax', '5ghz-ax', '6ghz-ax'],
      identity_regex: '.*',
      comment: '',
    };
    await fetchRules();
    emit('updated');
  } catch (err: any) {
    errorMsg.value =
      err.response?.data?.detail ||
      err.message ||
      t('wifi.create_prov_error', 'Error creando regla de aprovisionamiento.');
  } finally {
    isCreating.value = false;
  }
}

async function handleDeleteRule(provId: string) {
  if (!confirm(t('wifi.confirm_delete_prov', '¿Eliminar esta regla de aprovisionamiento?'))) return;
  try {
    await http.delete(
      `/api/v1/wifi/capsman/${props.routerId}/provisioning/${encodeURIComponent(provId)}`,
    );
    await fetchRules();
    emit('updated');
  } catch (err: any) {
    errorMsg.value =
      err.response?.data?.detail ||
      err.message ||
      t('wifi.delete_prov_error', 'Error eliminando regla de aprovisionamiento.');
  }
}

onMounted(() => {
  if (props.show && props.routerId) {
    fetchRules();
  }
});
</script>

<template>
  <div
    v-if="show"
    class="rg-modal-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="prov-rules-title"
  >
    <div class="rg-modal-card">
      <header class="rg-modal-header">
        <h3 id="prov-rules-title" class="rg-modal-title">
          📡 {{ t('wifi.prov_rules_title', 'Reglas de Aprovisionamiento de Radios (CAPsMAN v7)') }}
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
            id="btn-toggle-add-prov"
            type="button"
            class="rg-btn-primary"
            @click="showAddForm = !showAddForm"
          >
            {{
              showAddForm
                ? t('common.cancel', 'Cancelar')
                : `+ ${t('wifi.btn_add_prov_rule', 'Nueva Regla')}`
            }}
          </button>
          <button
            id="btn-refresh-prov-rules"
            type="button"
            class="rg-btn-secondary"
            :disabled="isLoading"
            @click="fetchRules"
          >
            🔄 {{ t('common.refresh', 'Refrescar') }}
          </button>
        </div>

        <!-- Formulario nueva regla -->
        <div v-if="showAddForm" class="rg-add-form">
          <h4 class="rg-subheading">
            {{ t('wifi.create_prov_heading', 'Nueva Regla /interface/wifi/provisioning') }}
          </h4>
          <div class="rg-grid-2">
            <div class="rg-field-row">
              <label for="prov-name" class="rg-label">{{ t('wifi.label_name', 'Nombre Regla:') }}</label>
              <input
                id="prov-name"
                v-model="newRule.name"
                type="text"
                class="rg-input"
                placeholder="prov-all-bands"
              />
            </div>

            <div class="rg-field-row">
              <label for="prov-action" class="rg-label">{{ t('wifi.label_action', 'Acción:') }}</label>
              <select id="prov-action" v-model="newRule.action" class="rg-input">
                <option value="create-dynamic-enabled">create-dynamic-enabled</option>
                <option value="create-enabled">create-enabled</option>
                <option value="none">none</option>
              </select>
            </div>

            <div class="rg-field-row">
              <label for="prov-master" class="rg-label">
                {{ t('wifi.label_master_cfg', 'Configuración Maestra (Master SSID):') }}
              </label>
              <input
                id="prov-master"
                v-model="newRule.master_configuration"
                type="text"
                list="available-wifi-configs"
                class="rg-input"
                placeholder="cfg-corporate"
              />
              <datalist id="available-wifi-configs">
                <option v-for="cfg in availableConfigs || []" :key="cfg.id" :value="cfg.name">
                  {{ cfg.ssid }}
                </option>
              </datalist>
            </div>

            <div class="rg-field-row">
              <label for="prov-slaves" class="rg-label">
                {{ t('wifi.label_slave_cfgs', 'Configuraciones Esclavas (separadas por coma):') }}
              </label>
              <input
                id="prov-slaves"
                v-model="newRule.slave_configurations_raw"
                type="text"
                class="rg-input"
                placeholder="cfg-guest, cfg-iot"
              />
            </div>

            <div class="rg-field-row">
              <label for="prov-regex" class="rg-label">
                {{ t('wifi.label_identity_regex', 'Filtro Identity RegExp:') }}
              </label>
              <input
                id="prov-regex"
                v-model="newRule.identity_regex"
                type="text"
                class="rg-input"
                placeholder=".*"
              />
            </div>

            <div class="rg-field-row">
              <label for="prov-comment" class="rg-label">{{ t('common.comment', 'Comentario:') }}</label>
              <input
                id="prov-comment"
                v-model="newRule.comment"
                type="text"
                class="rg-input"
                placeholder="Flota Wi-Fi 6 Corporativa"
              />
            </div>
          </div>

          <div class="rg-field-row">
            <span class="rg-label">{{ t('wifi.label_supported_bands', 'Bandas Soportadas:') }}</span>
            <div class="rg-bands-row">
              <label v-for="band in AVAILABLE_BANDS" :key="band" class="rg-checkbox-label">
                <input
                  type="checkbox"
                  class="rg-checkbox"
                  :checked="newRule.supported_bands.includes(band)"
                  @change="toggleBand(band)"
                />
                <span>{{ band }}</span>
              </label>
            </div>
          </div>

          <button
            id="btn-save-prov-rule"
            type="button"
            class="rg-btn-primary"
            :disabled="isCreating"
            @click="handleCreateRule"
          >
            {{ isCreating ? t('common.saving', 'Guardando...') : t('common.save', 'Guardar Regla') }}
          </button>
        </div>

        <!-- Tabla de reglas de aprovisionamiento -->
        <div class="rg-table-container">
          <table class="rg-table" :aria-label="t('wifi.prov_rules_table_aria', 'Reglas de aprovisionamiento')">
            <thead>
              <tr>
                <th scope="col">{{ t('wifi.th_name', 'Nombre') }}</th>
                <th scope="col">{{ t('wifi.th_master_cfg', 'Master Config') }}</th>
                <th scope="col">{{ t('wifi.th_slaves', 'Slaves') }}</th>
                <th scope="col">{{ t('wifi.th_bands', 'Bandas') }}</th>
                <th scope="col">{{ t('wifi.th_regex', 'Identity RegExp') }}</th>
                <th scope="col">{{ t('wifi.th_actions', 'Acciones') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rules" :key="r.id" class="rg-tr">
                <td class="font-bold text-cyan">{{ r.name }}</td>
                <td>{{ r.master_configuration }}</td>
                <td>{{ r.slave_configurations.length ? r.slave_configurations.join(', ') : '—' }}</td>
                <td>{{ r.supported_bands.length ? r.supported_bands.join(', ') : 'Todas' }}</td>
                <td><code>{{ r.identity_regex }}</code></td>
                <td>
                  <button
                    type="button"
                    class="rg-btn-danger-sm"
                    :aria-label="`${t('common.delete', 'Eliminar')} ${r.name}`"
                    @click="handleDeleteRule(r.id)"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
              <tr v-if="rules.length === 0 && !isLoading">
                <td colspan="6" class="text-center text-subtle">
                  {{ t('wifi.no_prov_rules', 'No hay reglas de aprovisionamiento configuradas.') }}
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
  width: 92%;
  max-width: 740px;
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
  font-size: 1.05rem;
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
  max-height: 74vh;
  overflow-y: auto;
}
.rg-toolbar {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
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
  font-size: 0.92rem;
  color: #00d2ff;
}
.rg-grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
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
  padding: 0.45rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
}
.rg-bands-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding-top: 0.25rem;
}
.rg-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
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
  font-size: 0.82rem;
}
.rg-table th,
.rg-table td {
  padding: 0.55rem 0.7rem;
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
  font-size: 0.85rem;
}
.rg-btn-primary {
  background: #0284c7;
  border: 1px solid #00d2ff;
  color: #ffffff;
  padding: 0.5rem 1.2rem;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
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
