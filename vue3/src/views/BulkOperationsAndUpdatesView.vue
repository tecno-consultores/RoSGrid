<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, watch } from 'vue';
  import { http } from '@/api/httpClient';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import ConfigTemplateEditorModal, {
    type TemplateItem,
    type TemplateStep,
  } from '@/components/operations/ConfigTemplateEditorModal.vue';

  interface FleetRouter {
    id: string;
    identity: string;
    ip_address: string;
    network_role: string;
    tag: string;
    ros_version: string;
    selected: boolean;
  }

  interface ConfigTemplate {
    id: string;
    name: string;
    category: string;
    description: string;
    variables_schema: { key: string; label: string; default_val?: string }[];
    ros_command_template?: string;
    rest_steps_template?: TemplateStep[];
    requires_safemode?: boolean;
  }

  interface BulkExecutionResult {
    id: string;
    router_id: string;
    identity: string;
    status: 'RUNNING' | 'SUCCESS' | 'ROLLED_BACK' | 'FAILED';
    progress: number;
    details: string;
  }

  const activeTab = ref<'templates' | 'updates'>('templates');

  // Asistente en 3 pasos
  const wizardStep = ref<1 | 2 | 3>(1);

  // Paso 1: Flota
  const filterRole = ref<string>('ALL');
  const filterTag = ref<string>('ALL');
  const fleetRouters = ref<FleetRouter[]>([]);

  const filteredFleet = computed(() => {
    return fleetRouters.value.filter((r) => {
      const matchRole = filterRole.value === 'ALL' || r.network_role === filterRole.value;
      const matchTag = filterTag.value === 'ALL' || r.tag === filterTag.value;
      return matchRole && matchTag;
    });
  });

  const selectedRoutersCount = computed(() => {
    return fleetRouters.value.filter((r) => r.selected).length;
  });

  const availableRoles = computed(() => {
    const roles = new Set<string>();
    fleetRouters.value.forEach((r) => {
      if (r.network_role) roles.add(r.network_role);
    });
    return Array.from(roles);
  });

  const availableTags = computed(() => {
    const tags = new Set<string>();
    fleetRouters.value.forEach((r) => {
      if (r.tag) tags.add(r.tag);
    });
    return Array.from(tags);
  });

  const inventoryStore = useInventoryStore();

  function syncFleetFromInventory() {
    if (inventoryStore.routers && inventoryStore.routers.length > 0) {
      fleetRouters.value = inventoryStore.routers.map((r) => {
        const ip =
          r.ip_address ||
          (r.api_base_url
            ? r.api_base_url
                .replace(/^https?:\/\//, '')
                .split('/')[0]
                .split(':')[0]
            : '');
        const role = r.network_role || 'CORE';
        const rawTags = (r as unknown as { tags?: Array<{ tag?: string } | string> }).tags;
        let tag = 'datacenter-central';
        if (Array.isArray(rawTags) && rawTags.length > 0) {
          tag =
            typeof rawTags[0] === 'object' && rawTags[0]?.tag ? rawTags[0].tag : String(rawTags[0]);
        }
        const rosVer = r.ros_version || 'v7';
        const identity =
          r.ros_identity && r.ros_identity !== r.display_name
            ? `${r.display_name} (${r.ros_identity})`
            : r.display_name;
        return {
          id: r.id,
          identity,
          ip_address: ip,
          network_role: role,
          tag,
          ros_version: rosVer,
          selected: true,
        };
      });
    } else {
      fleetRouters.value = [];
    }
  }

  watch(
    () => inventoryStore.routers,
    () => {
      syncFleetFromInventory();
    },
    { deep: true },
  );

  onMounted(async () => {
    await inventoryStore.fetchRouters();
    syncFleetFromInventory();
    await fetchTemplates();
  });

  function toggleAllVisible(checked: boolean) {
    filteredFleet.value.forEach((r) => {
      r.selected = checked;
    });
  }

  // Paso 2: Plantillas y Variables
  const templates = ref<ConfigTemplate[]>([]);
  const selectedTemplateId = ref<string>('');
  const templateVars = ref<Record<string, string>>({});
  const previewPayload = ref<string>('');

  async function fetchTemplates() {
    try {
      const res = await http.get<ConfigTemplate[]>('/api/v1/operations/templates');
      templates.value = Array.isArray(res.data) ? res.data : [];
      if (templates.value.length > 0 && !selectedTemplateId.value) {
        onSelectTemplate(templates.value[0].id);
      }
    } catch {
      templates.value = [];
    }
  }

  function onSelectTemplate(tplId: string) {
    selectedTemplateId.value = tplId;
    const tpl = templates.value.find((t) => t.id === tplId);
    if (tpl) {
      const vars: Record<string, string> = {};
      (tpl.variables_schema || []).forEach((v) => {
        vars[v.key] = v.default_val || '';
      });
      templateVars.value = vars;
      generatePreview();
    }
  }

  // Gestión de Plantillas
  const isTemplateModalOpen = ref(false);
  const templateToEdit = ref<TemplateItem | null>(null);

  function openCreateTemplateModal() {
    templateToEdit.value = null;
    isTemplateModalOpen.value = true;
  }

  function openEditTemplateModal() {
    const tpl = templates.value.find((t) => t.id === selectedTemplateId.value);
    if (tpl) {
      templateToEdit.value = JSON.parse(JSON.stringify(tpl)) as TemplateItem;
      isTemplateModalOpen.value = true;
    }
  }

  function cloneSelectedTemplate() {
    const tpl = templates.value.find((t) => t.id === selectedTemplateId.value);
    if (tpl) {
      const cloned = JSON.parse(JSON.stringify(tpl)) as TemplateItem;
      delete cloned.id;
      cloned.name = `${cloned.name}_COPIA`;
      templateToEdit.value = cloned;
      isTemplateModalOpen.value = true;
    }
  }

  async function deleteSelectedTemplate() {
    const tpl = templates.value.find((t) => t.id === selectedTemplateId.value);
    if (!tpl) return;
    if (!confirm(`¿Estás seguro de eliminar permanentemente la plantilla "${tpl.name}"?`)) {
      return;
    }
    try {
      await http.delete(`/api/v1/operations/templates/${tpl.id}`);
      selectedTemplateId.value = '';
      await fetchTemplates();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      alert(
        errorObj.response?.data?.detail || errorObj.message || 'Error al eliminar la plantilla.',
      );
    }
  }

  async function handleTemplateSaved(savedTpl: TemplateItem) {
    await fetchTemplates();
    if (savedTpl?.id) {
      onSelectTemplate(savedTpl.id);
    }
  }

  interface RenderedStep {
    method: string;
    endpoint: string;
    payload?: Record<string, unknown>;
    cli_command?: string;
  }

  function formatPayloadToParams(payload?: Record<string, unknown>): string {
    return Object.entries(payload || {})
      .map(([k, val]) => `${k}=${val}`)
      .join(' ');
  }

  function formatStepToRosCli(st: RenderedStep, vars: Record<string, string>): string {
    if (st.cli_command) {
      let cmdStr = st.cli_command;
      Object.entries(vars).forEach(([k, v]) => {
        cmdStr = cmdStr.replaceAll(`{{${k}}}`, v).replaceAll(`{{ ${k} }}`, v);
      });
      return cmdStr;
    }
    const ep = st.endpoint;
    const m = st.method;
    if (ep === 'system/ntp/client' && m === 'PATCH') {
      return `/system ntp client set ${formatPayloadToParams(st.payload)}`;
    }
    if (ep === 'system/ntp/client/servers' && (m === 'PUT' || m === 'POST')) {
      return `/system ntp client servers add ${formatPayloadToParams(st.payload)}`;
    }
    if (ep === 'ip/dns' && m === 'PATCH') {
      return `/ip dns set ${formatPayloadToParams(st.payload)}`;
    }
    if (ep === 'ip/dns/cache/flush') {
      return '/ip dns cache flush';
    }
    if (ep === 'snmp' && m === 'PATCH') {
      return `/snmp set enabled=${String(st.payload?.enabled || 'yes')}`;
    }
    return `# ${m} /rest/${ep} ${JSON.stringify(st.payload || {})}`;
  }

  function generatePreview() {
    const tpl = templates.value.find((t) => t.id === selectedTemplateId.value);
    if (!tpl) {
      previewPayload.value = '';
      return;
    }

    let renderedSteps: RenderedStep[] = [];
    try {
      let rawStr = JSON.stringify(tpl.rest_steps_template || []);
      Object.entries(templateVars.value).forEach(([k, v]) => {
        rawStr = rawStr.replaceAll(`{{${k}}}`, v).replaceAll(`{{ ${k} }}`, v);
      });
      renderedSteps = JSON.parse(rawStr);
    } catch {
      renderedSteps = [];
    }

    const cliCommands = renderedSteps.map((st) => formatStepToRosCli(st, templateVars.value));

    let legacyCmd = tpl.ros_command_template || '';
    if (legacyCmd) {
      Object.entries(templateVars.value).forEach(([k, v]) => {
        legacyCmd = legacyCmd.replaceAll(`{{${k}}}`, v).replaceAll(`{{ ${k} }}`, v);
      });
    }

    previewPayload.value = JSON.stringify(
      {
        plantilla: tpl.name,
        categoria: tpl.category,
        routers_objetivo: selectedRoutersCount.value,
        safe_mode: true,
        comandos_routeros_v7: legacyCmd ? legacyCmd.split('\n') : cliCommands,
        pasos_rest_api: renderedSteps,
      },
      null,
      2,
    );
  }

  // Paso 3: Ejecución Masiva
  const executing = ref(false);
  const progressPercent = ref(0);
  const executionResults = ref<BulkExecutionResult[]>([]);

  async function startBulkExecution() {
    wizardStep.value = 3;
    executing.value = true;
    progressPercent.value = 0;

    const selected = fleetRouters.value.filter((r) => r.selected);
    executionResults.value = selected.map((r) => ({
      id: `job-${r.id}`,
      router_id: r.id,
      identity: r.identity,
      status: 'RUNNING',
      progress: 0,
      details: 'Encolando en servidor...',
    }));

    const tpl = templates.value.find((t) => t.id === selectedTemplateId.value);
    try {
      await http.post('/api/v1/operations/bulk-jobs', {
        job_type: 'TEMPLATE_ROLLOUT',
        title: `Ejecución masiva: ${tpl?.name || 'Plantilla'}`,
        template_id: selectedTemplateId.value,
        execution_parameters: { variables: templateVars.value },
        target_router_ids: selected.map((r) => r.id),
      });
      progressPercent.value = 100;
      executionResults.value.forEach((job) => {
        job.status = 'SUCCESS';
        job.details = 'Trabajo masivo encolado exitosamente';
        job.progress = 100;
      });
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      progressPercent.value = 100;
      executionResults.value.forEach((job) => {
        job.status = 'FAILED';
        job.details = errorObj.response?.data?.detail || errorObj.message || 'Fallo de ejecución';
        job.progress = 0;
      });
    } finally {
      executing.value = false;
    }
  }

  async function seedDefaultTemplates() {
    try {
      const res = await http.post<ConfigTemplate[]>('/api/v1/operations/templates/seed-defaults');
      templates.value = Array.isArray(res.data) ? res.data : [];
      if (templates.value.length > 0 && !selectedTemplateId.value) {
        onSelectTemplate(templates.value[0].id);
      }
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      alert(
        errorObj.response?.data?.detail ||
          errorObj.message ||
          'Error al sincronizar plantillas predefinidas.',
      );
    }
  }

  // Pestaña Updates de RouterOS
  const targetRosVersion = ref('7.16.1');
  const upgradingRouterId = ref<string | null>(null);
  const updateSuccess = ref<string | null>(null);

  async function triggerRosUpdate(router: FleetRouter) {
    upgradingRouterId.value = router.id;
    updateSuccess.value = null;
    try {
      await http.post('/api/v1/operations/ros-updates/execute', {
        router_ids: [router.id],
        auto_upgrade_firmware: true,
      });
      updateSuccess.value = `Actualización de ${router.identity} iniciada. Se guardó respaldo obligatorio.`;
      router.ros_version = targetRosVersion.value;
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      updateSuccess.value = `Error al actualizar ${router.identity}: ${errorObj.response?.data?.detail || errorObj.message || 'Fallo de conexión'}`;
    } finally {
      upgradingRouterId.value = null;
      setTimeout(() => {
        updateSuccess.value = null;
      }, 5000);
    }
  }
</script>

<template>
  <main class="bulk-view" aria-labelledby="bulk-title">
    <header class="bulk-header">
      <div>
        <h1 id="bulk-title" class="bulk-title">Operaciones Masivas y Actualizador RouterOS v7</h1>
        <p class="bulk-subtitle">
          Golden Configs, plantillas parametrizables con Safe Mode y matriz de versiones de flota
        </p>
      </div>

      <!-- Pestañas Superiores y Acciones -->
      <div class="header-nav-wrap">
        <nav class="tabs-nav" aria-label="Secciones de operaciones masivas">
          <button
            type="button"
            class="tab-btn"
            :class="{ 'tab-btn--active': activeTab === 'templates' }"
            @click="activeTab = 'templates'"
          >
            📋 Plantillas y Acciones Masivas
          </button>
          <button
            type="button"
            class="tab-btn"
            :class="{ 'tab-btn--active': activeTab === 'updates' }"
            @click="activeTab = 'updates'"
          >
            🚀 Actualizador de RouterOS
          </button>
        </nav>

        <button
          type="button"
          class="btn-manage-tpl"
          aria-label="Crear nueva plantilla Golden Config"
          @click="openCreateTemplateModal"
        >
          ⚡ + Nueva Plantilla
        </button>
      </div>
    </header>

    <!-- Pestaña 1: Asistente de Plantillas en 3 Pasos -->
    <section
      v-if="activeTab === 'templates'"
      class="wizard-container"
      aria-label="Asistente de ejecución masiva"
    >
      <!-- Indicador de Pasos -->
      <ol class="step-indicator">
        <li
          class="step-item"
          :class="{ 'step-item--active': wizardStep === 1, 'step-item--done': wizardStep > 1 }"
        >
          <span class="step-num">1</span>
          <span class="step-label">Flota Destino ({{ selectedRoutersCount }})</span>
        </li>
        <li
          class="step-item"
          :class="{ 'step-item--active': wizardStep === 2, 'step-item--done': wizardStep > 2 }"
        >
          <span class="step-num">2</span>
          <span class="step-label">Plantilla & Previsualización</span>
        </li>
        <li class="step-item" :class="{ 'step-item--active': wizardStep === 3 }">
          <span class="step-num">3</span>
          <span class="step-label">Ejecución & Safe Mode</span>
        </li>
      </ol>

      <!-- PASO 1: Selección de Flota -->
      <div v-if="wizardStep === 1" class="wizard-step-card">
        <div class="step-header">
          <h2 class="step-title">Paso 1: Seleccionar Equipos Destino</h2>
          <div class="step-filters">
            <label class="filter-label">
              Rol:
              <select v-model="filterRole" class="form-select">
                <option value="ALL">Todos los Roles</option>
                <option v-for="role in availableRoles" :key="role" :value="role">
                  {{ role }}
                </option>
              </select>
            </label>

            <label class="filter-label">
              Etiqueta:
              <select v-model="filterTag" class="form-select">
                <option value="ALL">Todas las Etiquetas</option>
                <option v-for="tag in availableTags" :key="tag" :value="tag">
                  {{ tag }}
                </option>
              </select>
            </label>
          </div>
        </div>

        <table class="fleet-table">
          <thead>
            <tr>
              <th class="th-chk">
                <input
                  type="checkbox"
                  aria-label="Seleccionar todos los routers mostrados"
                  @change="toggleAllVisible(($event.target as HTMLInputElement).checked)"
                />
              </th>
              <th>Identidad / Router</th>
              <th>IP Primaria</th>
              <th>Rol en Red</th>
              <th>Etiqueta</th>
              <th>Versión RouterOS</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filteredFleet" :key="r.id" :class="{ 'tr-selected': r.selected }">
              <td class="td-chk">
                <input
                  v-model="r.selected"
                  type="checkbox"
                  :aria-label="`Seleccionar router ${r.identity}`"
                />
              </td>
              <td class="font-bold">{{ r.identity }}</td>
              <td class="font-mono">{{ r.ip_address }}</td>
              <td>
                <span class="tag tag--role">{{ r.network_role }}</span>
              </td>
              <td>
                <span class="tag tag--info">{{ r.tag }}</span>
              </td>
              <td class="font-mono">v{{ r.ros_version }}</td>
            </tr>
          </tbody>
        </table>

        <div class="step-footer">
          <span
            >Seleccionados: <strong>{{ selectedRoutersCount }}</strong> routers</span
          >
          <button
            type="button"
            class="btn btn--primary"
            :disabled="selectedRoutersCount === 0"
            @click="
              wizardStep = 2;
              generatePreview();
            "
          >
            Siguiente: Configurar Plantilla ➔
          </button>
        </div>
      </div>

      <!-- PASO 2: Selección de Plantilla y Previsualización -->
      <div v-if="wizardStep === 2" class="wizard-step-card">
        <div class="step-header-with-actions">
          <h2 class="step-title">Paso 2: Elegir o Crear Plantilla Parametrizable</h2>
          <div class="tpl-action-buttons">
            <button
              type="button"
              class="btn-primary-sm"
              title="Crear una nueva plantilla Golden Config"
              @click="openCreateTemplateModal"
            >
              + Nueva Plantilla
            </button>
            <button
              type="button"
              class="btn-secondary-sm"
              title="Sincronizar plantillas predefinidas del sistema"
              @click="seedDefaultTemplates"
            >
              ⭐ Sincronizar Presets
            </button>
            <button
              v-if="selectedTemplateId"
              type="button"
              class="btn-secondary-sm"
              title="Editar la plantilla seleccionada"
              @click="openEditTemplateModal"
            >
              ✏️ Editar
            </button>
            <button
              v-if="selectedTemplateId"
              type="button"
              class="btn-secondary-sm"
              title="Clonar plantilla seleccionada"
              @click="cloneSelectedTemplate"
            >
              📄 Clonar
            </button>
            <button
              v-if="selectedTemplateId"
              type="button"
              class="btn-danger-sm"
              title="Eliminar plantilla seleccionada"
              @click="deleteSelectedTemplate"
            >
              🗑️ Eliminar
            </button>
          </div>
        </div>

        <div v-if="templates.length === 0" class="empty-state-banner">
          <p>No existen plantillas Golden Config registradas para este Tenant.</p>
        </div>
        <div v-else class="templates-grid">
          <div
            v-for="tpl in templates"
            :key="tpl.id"
            class="template-card"
            :class="{ 'template-card--selected': selectedTemplateId === tpl.id }"
            @click="onSelectTemplate(tpl.id)"
          >
            <div class="tpl-card-top">
              <span class="tpl-name">{{ tpl.name }}</span>
              <span class="tag tag--role">{{ tpl.category }}</span>
            </div>
            <p class="tpl-desc">{{ tpl.description }}</p>
          </div>
        </div>

        <!-- Formulario dinámico de variables -->
        <div v-if="selectedTemplateId" class="template-variables-box">
          <h3 class="vars-title">Parámetros de la Plantilla</h3>
          <div class="vars-grid">
            <div
              v-for="v in templates.find((t) => t.id === selectedTemplateId)?.variables_schema ||
              []"
              :key="v.key"
              class="form-group"
            >
              <label :for="`var-${v.key}`" class="form-label">{{ v.label }}:</label>
              <input
                :id="`var-${v.key}`"
                v-model="templateVars[v.key]"
                type="text"
                class="form-input"
                @input="generatePreview"
              />
            </div>
          </div>
        </div>

        <!-- Previsualización -->
        <div v-if="selectedTemplateId" class="preview-box">
          <div class="preview-header">
            <span>Previsualización de Comandos REST (render-preview)</span>
            <span class="badge badge--safe">Safe Mode 60s Activado</span>
          </div>
          <pre class="preview-code">{{ previewPayload }}</pre>
        </div>

        <div class="step-footer">
          <button type="button" class="btn btn--secondary" @click="wizardStep = 1">
            ⬅️ Volver a Flota
          </button>
          <button
            type="button"
            class="btn btn--primary btn--run"
            :disabled="!selectedTemplateId || selectedRoutersCount === 0"
            @click="startBulkExecution"
          >
            🚀 Ejecutar en {{ selectedRoutersCount }} Routers con Safe Mode ➔
          </button>
        </div>
      </div>

      <!-- PASO 3: Ejecución en Tiempo Real -->
      <div v-if="wizardStep === 3" class="wizard-step-card">
        <h2 class="step-title">Paso 3: Progreso de Ejecución</h2>

        <div class="progress-container">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ progressPercent }}% Completado</span>
        </div>

        <table class="fleet-table">
          <thead>
            <tr>
              <th>Router</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Detalles / Rollback</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="res in executionResults" :key="res.id">
              <td class="font-bold">{{ res.identity }}</td>
              <td>
                <span
                  class="badge"
                  :class="{
                    'badge--success': res.status === 'SUCCESS',
                    'badge--warning': res.status === 'ROLLED_BACK',
                    'badge--info': res.status === 'RUNNING',
                  }"
                >
                  {{ res.status }}
                </span>
              </td>
              <td>{{ res.progress }}%</td>
              <td class="text-muted">{{ res.details }}</td>
            </tr>
          </tbody>
        </table>

        <div class="step-footer">
          <button
            type="button"
            class="btn btn--secondary"
            :disabled="executing"
            @click="wizardStep = 1"
          >
            Nueva Operación Masiva
          </button>
        </div>
      </div>
    </section>

    <!-- Pestaña 2: Actualizador de RouterOS v7 -->
    <section v-else class="updates-container" aria-label="Centro de actualizaciones RouterOS">
      <div v-if="updateSuccess" class="alert alert--success">✅ {{ updateSuccess }}</div>

      <div class="updates-header-card">
        <div>
          <h2 class="step-title">Matriz de Versiones de RouterOS v7</h2>
          <p class="text-muted">
            RoSGrid genera un respaldo encriptado .rsc + .backup antes de iniciar cualquier
            actualización.
          </p>
        </div>

        <div class="target-version-selector">
          <label class="form-label">
            Versión Objetivo Recomendada:
            <select v-model="targetRosVersion" class="form-select">
              <option value="7.16.1">RouterOS 7.16.1 (Stable)</option>
              <option value="7.16.2">RouterOS 7.16.2 (Testing)</option>
            </select>
          </label>
        </div>
      </div>

      <table class="fleet-table">
        <thead>
          <tr>
            <th>Equipo</th>
            <th>IP Primaria</th>
            <th>Versión Actual</th>
            <th>Versión Objetivo</th>
            <th>Diferencia</th>
            <th>Acción de Actualización</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in fleetRouters" :key="r.id">
            <td class="font-bold">{{ r.identity }}</td>
            <td class="font-mono">{{ r.ip_address }}</td>
            <td class="font-mono">v{{ r.ros_version }}</td>
            <td class="font-mono">v{{ targetRosVersion }}</td>
            <td>
              <span v-if="r.ros_version === targetRosVersion" class="badge badge--success">
                Actualizado
              </span>
              <span v-else class="badge badge--warning"> Pendiente de Upgrade </span>
            </td>
            <td>
              <button
                type="button"
                class="btn btn--sm"
                :class="r.ros_version === targetRosVersion ? 'btn--secondary' : 'btn--primary'"
                :disabled="r.ros_version === targetRosVersion || upgradingRouterId === r.id"
                @click="triggerRosUpdate(r)"
              >
                <span v-if="upgradingRouterId === r.id">⏳ Actualizando...</span>
                <span v-else>Actualizar con Backup</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Modal de Configuración de Plantillas Golden Config -->
    <ConfigTemplateEditorModal
      :is-open="isTemplateModalOpen"
      :template-to-edit="templateToEdit"
      @close="isTemplateModalOpen = false"
      @saved="handleTemplateSaved"
    />
  </main>
</template>

<style scoped>
  .bulk-view {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 1.25rem;
    color: #e2e8f0;
  }

  .bulk-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 1rem;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1rem;
  }

  .bulk-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #38bdf8;
    margin: 0;
  }

  .bulk-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0.25rem 0 0;
  }

  .tabs-nav {
    display: flex;
    gap: 0.5rem;
  }

  .tab-btn {
    background: #0f172a;
    border: 1px solid #334155;
    color: #94a3b8;
    padding: 0.45rem 0.85rem;
    font-size: 0.85rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .tab-btn--active {
    background: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
  }

  /* Step Indicator */
  .step-indicator {
    display: flex;
    list-style: none;
    padding: 0;
    margin: 0 0 1rem;
    gap: 1rem;
  }

  .step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #64748b;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #1e293b;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
  }

  .step-item--active {
    color: #38bdf8;
  }

  .step-item--active .step-num {
    background: #0284c7;
    color: #ffffff;
  }

  .step-item--done {
    color: #4ade80;
  }

  .step-item--done .step-num {
    background: #15803d;
    color: #ffffff;
  }

  .wizard-step-card,
  .updates-container {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .step-header,
  .updates-header-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .step-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0;
  }

  .step-filters {
    display: flex;
    gap: 1rem;
  }

  .filter-label,
  .form-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: #cbd5e1;
  }

  .form-select,
  .form-input {
    background: #1e293b;
    border: 1px solid #475569;
    color: #f1f5f9;
    padding: 0.35rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  /* Fleet Table */
  .fleet-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  .fleet-table th {
    background: #182234;
    padding: 0.5rem 0.75rem;
    text-align: left;
    color: #94a3b8;
    border-bottom: 1px solid #334155;
  }

  .fleet-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1e293b;
  }

  .tr-selected {
    background: rgba(2, 132, 199, 0.1);
  }

  .th-chk,
  .td-chk {
    width: 36px;
    text-align: center;
  }

  .font-bold {
    font-weight: 600;
  }

  .font-mono {
    font-family: monospace;
  }

  .text-muted {
    color: #94a3b8;
    font-size: 0.8rem;
  }

  .tag {
    font-size: 0.7rem;
    padding: 0.15rem 0.45rem;
    border-radius: 3px;
    font-weight: 600;
  }

  .tag--role {
    background: #334155;
    color: #38bdf8;
  }

  .tag--info {
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
  }

  .badge {
    font-size: 0.75rem;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .badge--safe {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }

  .badge--success {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }

  .badge--warning {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
  }

  .badge--info {
    background: rgba(2, 132, 199, 0.2);
    color: #38bdf8;
  }

  /* Templates Grid */
  .templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
  }

  .template-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.85rem;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .template-card--selected {
    border-color: #38bdf8;
    background: #1e2e4a;
  }

  .tpl-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .tpl-name {
    font-weight: 600;
    color: #f1f5f9;
  }

  .tpl-desc {
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 0;
  }

  .template-variables-box {
    background: #182234;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 1rem;
  }

  .vars-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #cbd5e1;
    margin: 0 0 0.75rem;
  }

  .vars-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .preview-box {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 4px;
    overflow: hidden;
  }

  .preview-header {
    background: #182234;
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #94a3b8;
  }

  .preview-code {
    margin: 0;
    padding: 0.75rem;
    font-family: monospace;
    font-size: 0.8rem;
    color: #38bdf8;
    overflow-x: auto;
  }

  .progress-container {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .progress-bar-bg {
    flex: 1;
    height: 12px;
    background: #1e293b;
    border-radius: 6px;
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: #0284c7;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.85rem;
    font-weight: 700;
    color: #38bdf8;
  }

  .step-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #1e293b;
    padding-top: 1rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid transparent;
  }

  .btn--sm {
    padding: 0.25rem 0.6rem;
    font-size: 0.75rem;
  }

  .btn--primary {
    background-color: #0284c7;
    color: #ffffff;
    border-color: #0369a1;
  }

  .btn--primary:hover:not(:disabled) {
    background-color: #0369a1;
  }

  .btn--secondary {
    background-color: #1e293b;
    color: #cbd5e1;
    border-color: #475569;
  }

  .btn--secondary:hover:not(:disabled) {
    background-color: #334155;
  }

  .alert {
    padding: 0.75rem 1rem;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .alert--success {
    background-color: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.4);
    color: #4ade80;
  }

  .header-nav-wrap {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .btn-manage-tpl {
    background: rgba(34, 211, 238, 0.15);
    border: 1px solid rgba(34, 211, 238, 0.4);
    color: #22d3ee;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    font-family: monospace;
    transition: all 0.2s;
  }

  .btn-manage-tpl:hover {
    background: rgba(34, 211, 238, 0.25);
    border-color: #22d3ee;
    color: #fff;
    transform: translateY(-1px);
  }

  .step-header-with-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .tpl-action-buttons {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .btn-primary-sm {
    background: #0284c7;
    color: #fff;
    border: none;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    font-family: monospace;
    transition: background-color 0.15s;
  }

  .btn-primary-sm:hover {
    background: #0369a1;
  }

  .btn-secondary-sm {
    background: #1e293b;
    color: #cbd5e1;
    border: 1px solid #475569;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
    font-family: monospace;
    transition: background-color 0.15s;
  }

  .btn-secondary-sm:hover {
    background: #334155;
    color: #fff;
  }

  .btn-danger-sm {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
    font-family: monospace;
    transition: all 0.15s;
  }

  .btn-danger-sm:hover {
    background: rgba(239, 68, 68, 0.25);
    border-color: #ef4444;
    color: #fff;
  }
</style>
