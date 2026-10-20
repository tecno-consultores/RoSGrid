<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { http } from '@/api/httpClient';

  export interface TemplateVariable {
    key: string;
    label: string;
    default_val?: string;
    var_type?: string;
  }

  export interface TemplateStep {
    method: 'PATCH' | 'POST' | 'PUT' | 'DELETE' | 'GET';
    endpoint: string;
    payload?: Record<string, string | number | boolean>;
    cli_command?: string;
  }

  export interface TemplateItem {
    id?: string;
    name: string;
    category: string;
    description: string;
    variables_schema: TemplateVariable[];
    rest_steps_template: TemplateStep[];
    requires_safemode: boolean;
  }

  import { PREDEFINED_TEMPLATES } from './templatePresets';

  const props = defineProps<{
    isOpen: boolean;
    templateToEdit?: TemplateItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'saved', template: TemplateItem): void;
  }>();

  const isEditing = computed(() => Boolean(props.templateToEdit?.id));

  // Estado del formulario
  const name = ref('');
  const category = ref('NETWORK');
  const description = ref('');
  const requiresSafemode = ref(true);
  const variables = ref<TemplateVariable[]>([]);
  const steps = ref<TemplateStep[]>([]);
  const rawJsonMode = ref(false);
  const rawJsonText = ref('');
  const selectedPresetKey = ref('');

  // Pestaña activa del modal
  const activeTab = ref<'general' | 'variables' | 'steps' | 'preview'>('general');

  // Estado de envío y feedback
  const isSubmitting = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const dryRunPreview = ref<string>('');

  const categories = [
    { value: 'NETWORK', label: 'Red & Interfaces' },
    { value: 'SYSTEM', label: 'Sistema & Servicios' },
    { value: 'SECURITY', label: 'Seguridad & Firewall' },
    { value: 'ROUTING', label: 'Enrutamiento v7 BGP/OSPF' },
    { value: 'MAINTENANCE', label: 'Mantenimiento & Respaldos' },
    { value: 'CUSTOM', label: 'Personalizada' },
  ];

  function loadPredefinedPreset(presetKey: string) {
    selectedPresetKey.value = presetKey;
    const preset = PREDEFINED_TEMPLATES.find((p) => p.name === presetKey);
    if (!preset) return;

    name.value = preset.name;
    category.value = preset.category;
    description.value = preset.description;
    requiresSafemode.value = preset.requires_safemode;
    variables.value = JSON.parse(JSON.stringify(preset.variables_schema));
    steps.value = JSON.parse(JSON.stringify(preset.rest_steps_template));
    rawJsonText.value = JSON.stringify(steps.value, null, 2);
    errorMessage.value = '';
    successMessage.value = `Plantilla predefinida "${preset.name}" cargada correctamente.`;
    updatePreview();
  }

  function resetForm() {
    selectedPresetKey.value = '';
    if (props.templateToEdit) {
      name.value = props.templateToEdit.name || '';
      category.value = props.templateToEdit.category || 'NETWORK';
      description.value = props.templateToEdit.description || '';
      requiresSafemode.value = props.templateToEdit.requires_safemode ?? true;
      variables.value = JSON.parse(JSON.stringify(props.templateToEdit.variables_schema || []));
      steps.value = JSON.parse(JSON.stringify(props.templateToEdit.rest_steps_template || []));
      rawJsonText.value = JSON.stringify(steps.value, null, 2);
    } else {
      name.value = '';
      category.value = 'NETWORK';
      description.value = '';
      requiresSafemode.value = true;
      variables.value = [
        {
          key: 'param_valor',
          label: 'Parámetro de configuración',
          default_val: '',
          var_type: 'string',
        },
      ];
      steps.value = [
        { method: 'PATCH', endpoint: 'ip/dns', payload: { servers: '{{ param_valor }}' } },
      ];
      rawJsonText.value = JSON.stringify(steps.value, null, 2);
    }
    rawJsonMode.value = false;
    errorMessage.value = '';
    successMessage.value = '';
    activeTab.value = 'general';
    updatePreview();
  }

  watch(
    () => props.isOpen,
    (open) => {
      if (open) resetForm();
    },
    { immediate: true },
  );

  function formatName(val: string) {
    name.value = val
      .toUpperCase()
      .replace(/\s+/g, '_')
      .replace(/[^A-Z0-9_-]/g, '');
  }

  function addVariable() {
    variables.value.push({
      key: `var_${variables.value.length + 1}`,
      label: `Nueva Variable ${variables.value.length + 1}`,
      default_val: '',
      var_type: 'string',
    });
    updatePreview();
  }

  function removeVariable(index: number) {
    variables.value.splice(index, 1);
    updatePreview();
  }

  function addStep() {
    steps.value.push({
      method: 'PATCH',
      endpoint: 'ip/dns',
      payload: {},
    });
    syncStepsToRaw();
    updatePreview();
  }

  function removeStep(index: number) {
    steps.value.splice(index, 1);
    syncStepsToRaw();
    updatePreview();
  }

  function syncStepsToRaw() {
    rawJsonText.value = JSON.stringify(steps.value, null, 2);
  }

  function syncRawToSteps() {
    try {
      const parsed = JSON.parse(rawJsonText.value);
      if (Array.isArray(parsed)) {
        steps.value = parsed;
        errorMessage.value = '';
      } else {
        errorMessage.value = 'El JSON de pasos debe ser un arreglo de objetos.';
      }
    } catch {
      errorMessage.value = 'Sintaxis JSON inválida en los pasos de la plantilla.';
    }
    updatePreview();
  }

  function updatePreview() {
    if (rawJsonMode.value) {
      try {
        syncRawToSteps();
      } catch {
        return;
      }
    }

    const varsMap: Record<string, string> = {};
    variables.value.forEach((v) => {
      varsMap[v.key] = v.default_val || `[VALOR_${v.key.toUpperCase()}]`;
    });

    let renderedStr = JSON.stringify(steps.value, null, 2);
    Object.keys(varsMap).forEach((k) => {
      const val = varsMap[k];
      renderedStr = renderedStr.split(`{{ ${k} }}`).join(val);
      renderedStr = renderedStr.split(`{{${k}}}`).join(val);
    });

    dryRunPreview.value = renderedStr;
  }

  async function handleSave() {
    errorMessage.value = '';
    successMessage.value = '';

    const cleanName = name.value.trim().toUpperCase();
    if (!cleanName) {
      errorMessage.value = 'El nombre de la plantilla es obligatorio.';
      activeTab.value = 'general';
      return;
    }
    if (!description.value.trim()) {
      errorMessage.value = 'La descripción es obligatoria.';
      activeTab.value = 'general';
      return;
    }

    if (rawJsonMode.value) {
      syncRawToSteps();
      if (errorMessage.value) return;
    }

    if (steps.value.length === 0) {
      errorMessage.value = 'La plantilla debe contener al menos un paso de ejecución.';
      activeTab.value = 'steps';
      return;
    }

    const payload = {
      name: cleanName,
      category: category.value,
      description: description.value.trim(),
      variables_schema: variables.value,
      rest_steps_template: steps.value,
      requires_safemode: requiresSafemode.value,
    };

    try {
      isSubmitting.value = true;
      if (isEditing.value && props.templateToEdit?.id) {
        const res = await http.put<TemplateItem>(
          `/api/v1/operations/templates/${props.templateToEdit.id}`,
          payload,
        );
        successMessage.value = 'Plantilla actualizada exitosamente.';
        emit('saved', res.data);
      } else {
        const res = await http.post<TemplateItem>('/api/v1/operations/templates', payload);
        successMessage.value = 'Plantilla creada exitosamente.';
        emit('saved', res.data);
      }
      setTimeout(() => {
        emit('close');
      }, 700);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      errorMessage.value =
        errorObj.response?.data?.detail || errorObj.message || 'Error al guardar la plantilla.';
    } finally {
      isSubmitting.value = false;
    }
  }

  function handleClose() {
    emit('close');
  }
</script>

<template>
  <div
    v-if="isOpen"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="template-editor-title"
    @click.self="handleClose"
  >
    <div class="modal-card">
      <header class="modal-header">
        <h2 id="template-editor-title" class="modal-title">
          <span class="icon" aria-hidden="true">⚡</span>
          {{ isEditing ? 'Editar Plantilla Golden Config' : 'Nueva Plantilla Golden Config' }}
        </h2>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar configurador de plantillas"
          @click="handleClose"
        >
          ✕
        </button>
      </header>

      <!-- Pestañas de Navegación del Editor -->
      <nav class="modal-tabs" aria-label="Secciones del editor de plantilla">
        <button
          type="button"
          class="tab-btn"
          :class="{ 'tab-btn--active': activeTab === 'general' }"
          @click="activeTab = 'general'"
        >
          1. Metadatos & Categoría
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ 'tab-btn--active': activeTab === 'variables' }"
          @click="activeTab = 'variables'"
        >
          2. Variables Dinámicas ({{ variables.length }})
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ 'tab-btn--active': activeTab === 'steps' }"
          @click="activeTab = 'steps'"
        >
          3. Pasos de Ejecución ({{ steps.length }})
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ 'tab-btn--active': activeTab === 'preview' }"
          @click="
            () => {
              activeTab = 'preview';
              updatePreview();
            }
          "
        >
          4. Dry-Run / Previsualizador
        </button>
      </nav>

      <div class="modal-body">
        <!-- Feedback -->
        <div v-if="errorMessage" class="alert alert--error" role="alert">
          <span class="alert-icon" aria-hidden="true">⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>
        <div v-if="successMessage" class="alert alert--success" role="status">
          <span class="alert-icon" aria-hidden="true">✅</span>
          <span>{{ successMessage }}</span>
        </div>

        <!-- Pestaña 1: General -->
        <div v-show="activeTab === 'general'" class="tab-pane">
          <!-- Selector de Plantilla Predefinida del Sistema -->
          <div class="preset-card">
            <div class="preset-card-header">
              <span class="preset-badge">⚡ PLANTILLA PREDEFINIDA</span>
              <span class="preset-hint"
                >Puedes autocompletar con una plantilla estándar de RouterOS v7</span
              >
            </div>
            <div class="preset-selector-row">
              <label for="preset-select" class="form-label mb-0 font-bold">Cargar Preset:</label>
              <select
                id="preset-select"
                v-model="selectedPresetKey"
                class="form-control form-select-preset"
                aria-label="Cargar plantilla predefinida"
                @change="loadPredefinedPreset(($event.target as HTMLSelectElement).value)"
              >
                <option value="">-- Seleccionar plantilla predefinida recomendada --</option>
                <option value="CLIENTE_NTP">🕒 Cliente NTP (/system ntp client) [SYSTEM]</option>
                <option value="DNS_CORPORATIVO_RESILIENTE">
                  🌐 DNS Corporativo Resiliente [NETWORK]
                </option>
                <option value="SNMP_V2C_MONITOREO_NOC">🛡️ SNMP v2c Monitoreo NOC [SECURITY]</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="tpl-name" class="form-label">
              Identificador de la Plantilla: <span class="required">*</span>
            </label>
            <input
              id="tpl-name"
              v-model="name"
              type="text"
              class="form-control"
              placeholder="Ej. DNS_CORPORATIVO_EMERGENCIA"
              maxlength="120"
              @input="formatName(($event.target as HTMLInputElement).value)"
            />
            <span class="help-text">Se normaliza en MAYÚSCULAS_CON_GUIONES_BAJOS</span>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="tpl-category" class="form-label">Categoría:</label>
              <select id="tpl-category" v-model="category" class="form-control">
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">
                  {{ cat.label }}
                </option>
              </select>
            </div>

            <div class="form-group flex-1 checkbox-group">
              <label class="checkbox-label">
                <input v-model="requiresSafemode" type="checkbox" class="form-checkbox" />
                <span class="checkbox-text">
                  <strong>Safe Mode de 60s Obligatorio</strong> (Reversión automática si se pierde
                  conectividad)
                </span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label for="tpl-desc" class="form-label">
              Descripción & Propósito Operativo: <span class="required">*</span>
            </label>
            <textarea
              id="tpl-desc"
              v-model="description"
              class="form-control textarea"
              rows="3"
              placeholder="Explica qué hace esta plantilla, su impacto en la flota y cuándo debe ser aplicada."
            ></textarea>
          </div>
        </div>

        <!-- Pestaña 2: Variables -->
        <div v-show="activeTab === 'variables'" class="tab-pane">
          <div class="pane-header-row">
            <div>
              <h3 class="pane-title">Variables Parametrizables</h3>
              <p class="pane-subtitle">
                Estas variables serán solicitadas al operador antes de ejecutar la acción sobre la
                flota.
              </p>
            </div>
            <button type="button" class="btn-secondary-sm" @click="addVariable">
              + Agregar Variable
            </button>
          </div>

          <div class="variables-list">
            <div v-for="(v, idx) in variables" :key="idx" class="var-item-card">
              <div class="var-field flex-2">
                <label :for="'var-key-' + idx" class="var-label"
                  >Clave &#123;&#123; {{ v.key }} &#125;&#125;:</label
                >
                <input
                  :id="'var-key-' + idx"
                  v-model="v.key"
                  type="text"
                  class="form-control form-control--mono"
                  placeholder="ej. dns_primario"
                  @input="updatePreview"
                />
              </div>

              <div class="var-field flex-3">
                <label :for="'var-label-' + idx" class="var-label">Etiqueta Descriptiva:</label>
                <input
                  :id="'var-label-' + idx"
                  v-model="v.label"
                  type="text"
                  class="form-control"
                  placeholder="ej. Servidor DNS Primario"
                />
              </div>

              <div class="var-field flex-2">
                <label :for="'var-def-' + idx" class="var-label">Valor por Defecto:</label>
                <input
                  :id="'var-def-' + idx"
                  v-model="v.default_val"
                  type="text"
                  class="form-control form-control--mono"
                  placeholder="ej. 1.1.1.1"
                  @input="updatePreview"
                />
              </div>

              <button
                type="button"
                class="btn-icon-danger"
                title="Eliminar variable"
                aria-label="Eliminar variable"
                @click="removeVariable(idx)"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>

        <!-- Pestaña 3: Pasos de Ejecución -->
        <div v-show="activeTab === 'steps'" class="tab-pane">
          <div class="pane-header-row">
            <div>
              <h3 class="pane-title">Pasos REST / Comandos RouterOS</h3>
              <p class="pane-subtitle">
                Secuencia de comandos que ejecutará cada router de forma transaccional.
              </p>
            </div>
            <div class="pane-actions">
              <button
                type="button"
                class="btn-toggle-mode"
                @click="
                  rawJsonMode = !rawJsonMode;
                  if (!rawJsonMode) syncRawToSteps();
                  else syncStepsToRaw();
                "
              >
                {{ rawJsonMode ? 'Visual' : '{ } JSON' }}
              </button>
              <button v-if="!rawJsonMode" type="button" class="btn-secondary-sm" @click="addStep">
                + Agregar Paso
              </button>
            </div>
          </div>

          <!-- Modo JSON Crudo -->
          <div v-if="rawJsonMode" class="raw-json-container">
            <textarea
              v-model="rawJsonText"
              class="form-control textarea mono-editor"
              rows="10"
              placeholder="[ { 'method': 'PATCH', 'endpoint': 'ip/dns', 'payload': { ... } } ]"
              @input="updatePreview"
            ></textarea>
            <span class="help-text"
              >Edita directamente la estructura JSON de pasos REST RouterOS v7.</span
            >
          </div>

          <!-- Modo Estructurado Visual -->
          <div v-else class="steps-list">
            <div v-for="(st, idx) in steps" :key="idx" class="step-card">
              <div class="step-card-header">
                <span class="step-number">Paso #{{ idx + 1 }}</span>
                <button
                  type="button"
                  class="btn-icon-danger"
                  title="Eliminar paso"
                  aria-label="Eliminar paso"
                  @click="removeStep(idx)"
                >
                  🗑️
                </button>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label class="form-label">Método REST:</label>
                  <select
                    v-model="st.method"
                    class="form-control form-control--mono"
                    @change="updatePreview"
                  >
                    <option value="PATCH">PATCH (Actualizar propiedad)</option>
                    <option value="POST">POST (Crear recurso / Ejecutar script)</option>
                    <option value="PUT">PUT (Reemplazar configuración)</option>
                    <option value="DELETE">DELETE (Remover elemento)</option>
                  </select>
                </div>

                <div class="form-group flex-2">
                  <label class="form-label">Endpoint RouterOS (/rest/...):</label>
                  <input
                    v-model="st.endpoint"
                    type="text"
                    class="form-control form-control--mono"
                    placeholder="ej. ip/dns, system/ntp/client, snmp"
                    @input="updatePreview"
                  />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Payload JSON (parámetros y variables):</label>
                <textarea
                  :value="
                    typeof st.payload === 'object'
                      ? JSON.stringify(st.payload, null, 2)
                      : String(st.payload || '')
                  "
                  class="form-control textarea mono-editor-sm"
                  rows="3"
                  placeholder="{ 'servers': '{{ dns_servers }}' }"
                  @input="
                    (e) => {
                      try {
                        st.payload = JSON.parse((e.target as HTMLTextAreaElement).value);
                      } catch {
                        // Se mantiene como texto provisional
                      }
                      updatePreview();
                    }
                  "
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Pestaña 4: Dry-Run Previsualizador -->
        <div v-show="activeTab === 'preview'" class="tab-pane">
          <div class="pane-header-row">
            <div>
              <h3 class="pane-title">Previsualización de Renderizado en Pre-Vuelo</h3>
              <p class="pane-subtitle">
                Así se construirá la carga útil final para cada router con las variables
                sustituidas.
              </p>
            </div>
            <button type="button" class="btn-secondary-sm" @click="updatePreview">
              🔄 Actualizar Renderizado
            </button>
          </div>

          <pre class="preview-box"><code>{{ dryRunPreview }}</code></pre>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn-secondary" :disabled="isSubmitting" @click="handleClose">
          Cancelar
        </button>

        <button type="button" class="btn-primary" :disabled="isSubmitting" @click="handleSave">
          {{ isSubmitting ? 'Guardando...' : isEditing ? 'Guardar Cambios' : '+ Crear Plantilla' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(2, 6, 23, 0.82);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1250;
    padding: 1rem;
  }

  .modal-card {
    background: #0f172a;
    border: 1px solid rgba(0, 240, 255, 0.3);
    border-radius: 8px;
    width: 100%;
    max-width: 820px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow:
      0 16px 40px rgba(0, 0, 0, 0.7),
      0 0 25px rgba(0, 240, 255, 0.15);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    background: rgba(15, 23, 42, 0.95);
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #00f0ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: monospace;
    letter-spacing: 0.5px;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.25rem;
    cursor: pointer;
    line-height: 1;
    padding: 0.25rem;
    border-radius: 4px;
    transition:
      color 0.15s,
      background-color 0.15s;
  }

  .btn-close:hover {
    color: #fff;
    background: rgba(239, 68, 68, 0.2);
  }

  .modal-tabs {
    display: flex;
    gap: 2px;
    background: rgba(15, 23, 42, 0.8);
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    padding: 0 1rem;
    overflow-x: auto;
  }

  .tab-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #94a3b8;
    font-size: 0.82rem;
    font-weight: 600;
    font-family: monospace;
    padding: 0.75rem 0.85rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }

  .tab-btn:hover {
    color: #e2e8f0;
  }

  .tab-btn--active {
    color: #00f0ff;
    border-bottom-color: #00f0ff;
    background: rgba(0, 240, 255, 0.05);
  }

  .modal-body {
    padding: 1.25rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .tab-pane {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .pane-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .pane-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0;
    font-family: monospace;
  }

  .pane-subtitle {
    font-size: 0.78rem;
    color: #94a3b8;
    margin: 2px 0 0 0;
  }

  .pane-actions {
    display: flex;
    gap: 0.5rem;
  }

  .alert {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 0.85rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .alert--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .alert--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .form-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
    flex-wrap: wrap;
  }

  .flex-1 {
    flex: 1;
    min-width: 160px;
  }
  .flex-2 {
    flex: 2;
    min-width: 180px;
  }
  .flex-3 {
    flex: 3;
    min-width: 200px;
  }

  .form-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #cbd5e1;
    font-family: monospace;
    text-transform: uppercase;
  }

  .required {
    color: #ef4444;
  }

  .form-control {
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 4px;
    padding: 0.45rem 0.75rem;
    color: #f8fafc;
    font-size: 0.85rem;
    font-family: inherit;
  }

  .form-control--mono {
    font-family: monospace;
  }

  .form-control:focus {
    outline: none;
    border-color: #00f0ff;
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.3);
  }

  .textarea {
    resize: vertical;
    font-family: inherit;
  }

  .mono-editor {
    font-family: monospace;
    font-size: 0.8rem;
    line-height: 1.4;
  }

  .mono-editor-sm {
    font-family: monospace;
    font-size: 0.78rem;
    line-height: 1.35;
  }

  .help-text {
    font-size: 0.7rem;
    color: #64748b;
  }

  .checkbox-group {
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .form-checkbox {
    accent-color: #00f0ff;
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .checkbox-text {
    font-size: 0.78rem;
    color: #cbd5e1;
  }

  .variables-list,
  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .var-item-card {
    background: rgba(30, 41, 59, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 6px;
    padding: 0.75rem;
    display: flex;
    align-items: flex-end;
    gap: 0.65rem;
    flex-wrap: wrap;
  }

  .var-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .var-label {
    font-size: 0.7rem;
    font-family: monospace;
    color: #94a3b8;
  }

  .step-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 6px;
    padding: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .step-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    padding-bottom: 0.4rem;
  }

  .step-number {
    font-family: monospace;
    font-size: 0.8rem;
    font-weight: 700;
    color: #00f0ff;
  }

  .btn-icon-danger {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 0.9rem;
    padding: 0.25rem;
    opacity: 0.75;
    transition: opacity 0.15s;
  }

  .btn-icon-danger:hover {
    opacity: 1;
    transform: scale(1.1);
  }

  .preview-box {
    background: #020617;
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 6px;
    padding: 1rem;
    font-family: monospace;
    font-size: 0.8rem;
    color: #38bdf8;
    overflow-x: auto;
    max-height: 380px;
  }

  .modal-footer {
    padding: 0.85rem 1.25rem;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    background: rgba(15, 23, 42, 0.95);
  }

  .btn-primary {
    background: #00f0ff;
    color: #020617;
    border: none;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0.5rem 1.2rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: monospace;
    transition:
      background-color 0.15s,
      transform 0.1s;
  }

  .btn-primary:hover:not(:disabled) {
    background: #38bdf8;
    transform: translateY(-1px);
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: #334155;
    color: #e2e8f0;
    border: none;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: monospace;
  }

  .btn-secondary:hover {
    background: #475569;
  }

  .btn-secondary-sm {
    background: rgba(14, 165, 233, 0.15);
    border: 1px solid rgba(14, 165, 233, 0.4);
    color: #38bdf8;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    font-family: monospace;
    transition: all 0.15s;
  }

  .btn-secondary-sm:hover {
    background: rgba(14, 165, 233, 0.25);
    border-color: #38bdf8;
    color: #fff;
  }

  .btn-toggle-mode {
    background: transparent;
    border: 1px solid rgba(148, 163, 184, 0.3);
    color: #cbd5e1;
    padding: 0.35rem 0.65rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: monospace;
    cursor: pointer;
  }

  .btn-toggle-mode:hover {
    border-color: #00f0ff;
    color: #00f0ff;
  }

  .preset-card {
    background: rgba(14, 165, 233, 0.08);
    border: 1px solid rgba(14, 165, 233, 0.35);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 1.25rem;
  }

  .preset-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.65rem;
  }

  .preset-badge {
    background: rgba(14, 165, 233, 0.25);
    color: #38bdf8;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    letter-spacing: 0.05em;
  }

  .preset-hint {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .preset-selector-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .form-select-preset {
    flex: 1;
    background: #0f172a;
    border: 1px solid rgba(14, 165, 233, 0.4);
    color: #f8fafc;
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
    font-family: monospace;
  }

  .form-select-preset:focus {
    border-color: #38bdf8;
    outline: none;
    box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.25);
  }
</style>
