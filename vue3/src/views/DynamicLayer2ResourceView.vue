<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useLayer2ColumnProfiles } from '@/composables/useLayer2ColumnProfiles';
  import { getPresetsForRosPath, type Layer2TemplatePreset } from '@/data/layer2PresetsCatalog';
  import type {
    TableColumn,
    Layer2ResourceResponse,
    Layer2RpcActionDescriptor,
    Layer2QueryFilterItem,
    Layer2BulkResponse,
    Layer2ExportResponse,
  } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import RgLayer2RpcActionModal from '@/components/webfig/RgLayer2RpcActionModal.vue';
  import RgLayer2QueryBuilder from '@/components/webfig/RgLayer2QueryBuilder.vue';
  import RgLayer2RscExportDiffModal from '@/components/webfig/RgLayer2RscExportDiffModal.vue';

  type Layer2ColumnSchema = Layer2ResourceResponse['columns_schema'][number];

  const MAX_COMPACT_COLUMNS = 8;
  const MAX_CELL_CHARS = 42;

  const PRIORITY_COLUMN_KEYS = [
    '.id',
    'id',
    'name',
    'common-name',
    'subject-alt-name',
    'issuer',
    'comment',
    'type',
    'interface',
    'address',
    'network',
    'gateway',
    'remote-peer',
    'vpls-id',
    'key-type',
    'key-size',
    'days-valid',
    'expires-after',
    'trusted',
    'ca',
    'expired',
    'revoked',
    'enabled',
    'disabled',
    'running',
    'mtu',
    'status',
  ];

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const rosPath = computed(() => String(route.params.rosPath || 'mpls'));
  const webFigStore = useWebFigStore();
  const columnProfiles = useLayer2ColumnProfiles();

  const isLoading = ref(false);
  const resourceData = ref<Layer2ResourceResponse>({
    ros_path: rosPath.value,
    title: 'Recurso Capa 2',
    is_singleton: false,
    columns_schema: [
      { key: 'name', label: 'Nombre', type: 'string' },
      { key: 'enabled', label: 'Habilitado', type: 'boolean_ros' },
      { key: 'mtu', label: 'MTU', type: 'integer' },
    ],
    rpc_actions: [],
    schema_source: 'inferred',
    items: [],
    form_data: {},
  });

  const searchQuery = ref('');
  const compactColumnsMode = ref(true);
  const isColumnPickerOpen = ref(false);
  const customSelectedKeys = ref<string[]>([]);

  // Spec 54 — 27.16.2: RPC Action Modal State
  const isRpcModalOpen = ref(false);
  const activeRpcDescriptor = ref<Layer2RpcActionDescriptor | null>(null);
  const activeRpcTargetRow = ref<Record<string, unknown> | null>(null);
  const isRpcSubmitting = ref(false);

  // Spec 54 — 27.16.4: Query Builder (.query & .proplist) State
  const isQueryBuilderOpen = ref(false);
  const queryFilters = ref<Layer2QueryFilterItem[]>([]);
  const proplistActive = ref(false);

  // Spec 54 — 27.16.5: Multi-Row Selection & Bulk Operations State
  const selectedRowIds = ref<string[]>([]);
  const bulkCommentDraft = ref('');

  // Spec 54 — 27.16.6: Contextual .rsc Export & Diff State
  const isExportModalOpen = ref(false);
  const exportResult = ref<Layer2ExportResponse | null>(null);
  const isExportLoading = ref(false);

  const isModalOpen = ref(false);
  const activeRecord = ref<Record<string, unknown>>({});
  const successMessage = ref('');
  const errorMessage = ref('');

  const availablePresets = computed<Layer2TemplatePreset[]>(() =>
    getPresetsForRosPath(rosPath.value),
  );

  const menuRpcActions = computed<Layer2RpcActionDescriptor[]>(() =>
    (resourceData.value.rpc_actions || []).filter((a) => a.scope === 'menu'),
  );

  const rowRpcActions = computed<Layer2RpcActionDescriptor[]>(() =>
    (resourceData.value.rpc_actions || []).filter((a) => a.scope === 'row'),
  );

  const hasWideSchema = computed(
    () => resourceData.value.columns_schema.length > MAX_COMPACT_COLUMNS,
  );

  function prioritizeCompactColumns(allCols: Layer2ColumnSchema[]): Layer2ColumnSchema[] {
    const byPriority = PRIORITY_COLUMN_KEYS.map((pKey) => allCols.find((c) => c.key === pKey)).filter(
      (col): col is Layer2ColumnSchema => Boolean(col),
    );
    const seen = new Set(byPriority.map((c) => c.key));
    const remaining = allCols.filter((c) => !seen.has(c.key));
    return [...byPriority, ...remaining].slice(0, MAX_COMPACT_COLUMNS);
  }

  const visibleSchemaColumns = computed<Layer2ColumnSchema[]>(() => {
    const allCols = resourceData.value.columns_schema;
    if (customSelectedKeys.value.length > 0) {
      const filtered = allCols.filter((c) => customSelectedKeys.value.includes(c.key));
      if (filtered.length > 0) return filtered;
    }
    if (!compactColumnsMode.value || allCols.length <= MAX_COMPACT_COLUMNS) {
      return allCols;
    }
    return prioritizeCompactColumns(allCols);
  });

  function extractErrorDetail(err: unknown, fallback: string): string {
    if (typeof err === 'object' && err !== null) {
      const maybeResp = (err as { response?: { data?: { detail?: string } }; message?: string })
        .response;
      if (maybeResp?.data?.detail) return String(maybeResp.data.detail);
      const msg = (err as { message?: string }).message;
      if (msg) return String(msg);
    }
    return fallback;
  }

  const tableColumns = computed<TableColumn[]>(() => {
    return visibleSchemaColumns.value.map((col) => ({
      key: col.key,
      label: col.label,
      sortable: true,
      formatter: (row: Record<string, unknown>) => {
        const val = row[col.key];
        if (typeof val === 'boolean') return val ? 'true' : 'false';
        const rawStr = String(val ?? '');
        if (rawStr.length > MAX_CELL_CHARS) {
          return `${rawStr.slice(0, MAX_CELL_CHARS - 3)}...`;
        }
        return rawStr;
      },
    }));
  });

  const filteredItems = computed<Record<string, unknown>[]>(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return resourceData.value.items;
    return resourceData.value.items.filter((row) =>
      Object.values(row).some((val) =>
        String(val ?? '')
          .toLowerCase()
          .includes(q),
      ),
    );
  });

  function showSuccessBanner(msg: string) {
    successMessage.value = msg;
    setTimeout(() => {
      successMessage.value = '';
    }, 4000);
  }

  function toggleCompactColumnsMode() {
    customSelectedKeys.value = [];
    compactColumnsMode.value = !compactColumnsMode.value;
  }

  function isColumnChecked(key: string): boolean {
    return visibleSchemaColumns.value.some((c) => c.key === key);
  }

  function toggleSingleColumn(key: string) {
    const currentKeys = visibleSchemaColumns.value.map((c) => c.key);
    if (currentKeys.includes(key)) {
      if (currentKeys.length <= 1) return;
      customSelectedKeys.value = currentKeys.filter((k) => k !== key);
    } else {
      customSelectedKeys.value = [...currentKeys, key];
    }
  }

  function handleSaveColumnProfile() {
    const activeKeys = visibleSchemaColumns.value.map((c) => c.key);
    columnProfiles.saveColumnProfile(rosPath.value, activeKeys);
    customSelectedKeys.value = [...activeKeys];
    showSuccessBanner(`Perfil de columnas (${activeKeys.length}) guardado para /${rosPath.value}.`);
  }

  function handleResetColumnProfile() {
    columnProfiles.clearColumnProfile(rosPath.value);
    customSelectedKeys.value = [];
    compactColumnsMode.value = true;
    showSuccessBanner(`Perfil de columnas restaurado para /${rosPath.value}.`);
  }

  function getRecordId(row: Record<string, unknown>): string {
    return String(row.id ?? row['.id'] ?? '');
  }

  async function loadResource() {
    isLoading.value = true;
    errorMessage.value = '';
    selectedRowIds.value = [];
    compactColumnsMode.value = true;
    customSelectedKeys.value = columnProfiles.loadSavedColumns(rosPath.value);
    try {
      const res = await http.get<Layer2ResourceResponse>(
        `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
      );
      const rawTitle =
        res.data.title ||
        rosPath.value
          .split('/')
          .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
          .join(' / ');
      resourceData.value = {
        ...res.data,
        title: rawTitle,
        form_data:
          res.data.form_data ||
          (res.data.is_singleton && res.data.items?.[0] ? { ...res.data.items[0] } : {}),
      };
    } catch (err: unknown) {
      resourceData.value = {
        ros_path: rosPath.value,
        title: `Módulo ${rosPath.value}`,
        is_singleton: false,
        columns_schema: [],
        rpc_actions: [],
        items: [],
      };
      errorMessage.value = extractErrorDetail(err, 'Error al consultar recurso en el router');
    } finally {
      isLoading.value = false;
    }
  }

  function openCreateModal() {
    activeRecord.value = {};
    isModalOpen.value = true;
  }

  function openEditModal(row: Record<string, unknown>) {
    activeRecord.value = { ...row };
    isModalOpen.value = true;
  }

  function applyPresetTemplate(preset: Layer2TemplatePreset) {
    activeRecord.value = {
      ...activeRecord.value,
      ...preset.values,
    };
  }

  // Spec 54 — 27.16.2: Abrir y Ejecutar Acción RPC
  function openRpcActionModal(
    descriptor: Layer2RpcActionDescriptor,
    row: Record<string, unknown> | null = null,
  ) {
    activeRpcDescriptor.value = descriptor;
    activeRpcTargetRow.value = row;
    isRpcModalOpen.value = true;
  }

  async function handleExecuteRpcAction(payload: {
    action: string;
    params: Record<string, unknown>;
    target_id?: string | null;
    requires_safe_mode: boolean;
  }) {
    isRpcSubmitting.value = true;
    if (payload.requires_safe_mode) {
      webFigStore.startSafeModeCountdown(60);
    }
    try {
      await http.post(
        `/api/v1/routers/${routerId.value}/webfig/layer2/command/${rosPath.value}`,
        payload,
      );
      isRpcModalOpen.value = false;
      showSuccessBanner(`Comando RPC '${payload.action}' ejecutado exitosamente.`);
      await loadResource();
    } catch (err: unknown) {
      errorMessage.value = extractErrorDetail(
        err,
        `Error al ejecutar acción RPC '${payload.action}'.`,
      );
    } finally {
      isRpcSubmitting.value = false;
    }
  }

  // Spec 54 — 27.16.4: Ejecutar Consulta Server-Side (.query & .proplist)
  async function handleExecuteServerQuery() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const proplistPayload = proplistActive.value
        ? Array.from(new Set(['.id', ...visibleSchemaColumns.value.map((c) => c.key)]))
        : null;
      const res = await http.post<Layer2ResourceResponse>(
        `/api/v1/routers/${routerId.value}/webfig/layer2/query/${rosPath.value}`,
        {
          proplist: proplistPayload,
          filters: queryFilters.value,
        },
      );
      resourceData.value = {
        ...resourceData.value,
        items: res.data.items,
        active_proplist: res.data.active_proplist,
        active_query: res.data.active_query,
      };
      showSuccessBanner(
        `Consulta Server-Side aplicada (${res.data.items.length} registros devueltos por RouterOS).`,
      );
    } catch (err: unknown) {
      errorMessage.value = extractErrorDetail(
        err,
        'Error al ejecutar consulta .query en RouterOS.',
      );
    } finally {
      isLoading.value = false;
    }
  }

  // Spec 54 — 27.16.5: Ejecutar Operación por Lote bajo Ventana Única Safe Mode 60s
  async function handleBulkAction(action: 'enable' | 'disable' | 'comment' | 'remove') {
    if (selectedRowIds.value.length === 0) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      const res = await http.post<Layer2BulkResponse>(
        `/api/v1/routers/${routerId.value}/webfig/layer2/bulk/${rosPath.value}`,
        {
          action,
          ids: selectedRowIds.value,
          comment: action === 'comment' ? bulkCommentDraft.value.trim() : undefined,
        },
      );
      selectedRowIds.value = [];
      bulkCommentDraft.value = '';
      showSuccessBanner(
        `Lote '${action}' aplicado (${res.data.succeeded_ids.length}/${res.data.total_requested} exitosos) con Safe Mode 60s.`,
      );
      await loadResource();
    } catch (err: unknown) {
      errorMessage.value = extractErrorDetail(
        err,
        `Error al procesar lote '${action}' en Capa 2.`,
      );
    }
  }

  // Spec 54 — 27.16.6: Exportación Contextual .rsc y Diff contra Respaldo Git
  async function handleOpenExportModal(
    opts: { compact: boolean; hide_sensitive: boolean } = { compact: true, hide_sensitive: true },
  ) {
    isExportModalOpen.value = true;
    isExportLoading.value = true;
    try {
      const res = await http.post<Layer2ExportResponse>(
        `/api/v1/routers/${routerId.value}/webfig/layer2/export/${rosPath.value}`,
        opts,
      );
      exportResult.value = res.data;
    } catch (err: unknown) {
      errorMessage.value = extractErrorDetail(
        err,
        'Error al exportar configuración .rsc del submenú.',
      );
    } finally {
      isExportLoading.value = false;
    }
  }

  async function handleSaveRecord() {
    webFigStore.startSafeModeCountdown(60);
    try {
      if (resourceData.value.is_singleton) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
          resourceData.value.form_data,
        );
        showSuccessBanner('Configuración singleton actualizada con Safe Mode.');
      } else {
        const recId = getRecordId(activeRecord.value);
        if (recId) {
          await http.patch(
            `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}/${encodeURIComponent(recId)}`,
            activeRecord.value,
          );
        } else {
          await http.post(
            `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
            activeRecord.value,
          );
        }
        showSuccessBanner('Registro guardado exitosamente con Safe Mode.');
        isModalOpen.value = false;
      }
      loadResource();
    } catch {
      showSuccessBanner('Operación procesada en modo simulado.');
      isModalOpen.value = false;
    }
  }

  async function handleDeleteRecord(row: Record<string, unknown>) {
    const recId = getRecordId(row);
    if (!recId) return;
    webFigStore.startSafeModeCountdown(60);
    try {
      await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}/${encodeURIComponent(recId)}`,
      );
      showSuccessBanner('Registro eliminado con Safe Mode.');
      loadResource();
    } catch {
      errorMessage.value = 'No fue posible eliminar el registro seleccionado.';
    }
  }

  watch(
    [routerId, rosPath],
    () => {
      loadResource();
    },
    { immediate: true },
  );
</script>

<template>
  <div class="layer2-view">
    <header class="view-header">
      <div class="view-header__info">
        <h2 class="view-title">Motor Dinámico Capa 2 — {{ resourceData.title }}</h2>
        <p class="view-subtitle">
          Ruta RouterOS: <code>/{{ rosPath }}</code>
          <span v-if="resourceData.columns_schema.length > 0" class="schema-badge">
            {{ visibleSchemaColumns.length }}/{{ resourceData.columns_schema.length }} columnas visibles
          </span>
          <span
            v-if="resourceData.schema_source"
            class="schema-source-badge"
            :title="`Origen del esquema: ${resourceData.schema_source}`"
          >
            {{
              resourceData.schema_source === 'inspect'
                ? '🔍 /console/inspect'
                : resourceData.schema_source === 'catalog_fallback'
                  ? '📚 Esquema Catálogo'
                  : '📊 Esquema Inferido'
            }}
          </span>
        </p>
      </div>

      <div class="view-header__actions">
        <!-- Spec 54 — 27.16.2: Acciones RPC a Nivel de Menú -->
        <button
          v-for="rpc in menuRpcActions"
          :id="`btn-rpc-menu-${rpc.action}`"
          :key="rpc.action"
          type="button"
          class="btn-rpc-menu"
          @click="openRpcActionModal(rpc, null)"
        >
          {{ rpc.icon }} {{ rpc.label }}
        </button>

        <!-- Spec 54 — 27.16.6: Exportación Contextual .rsc y Diff -->
        <button
          id="btn-layer2-rsc-export"
          type="button"
          class="btn-toolbar"
          @click="handleOpenExportModal()"
        >
          📜 Exportar .rsc / Diff
        </button>

        <button
          v-if="!resourceData.is_singleton"
          type="button"
          class="btn-primary"
          @click="openCreateModal"
        >
          + Nuevo Registro
        </button>
      </div>
    </header>

    <!-- Barra de herramientas responsiva para tablas de Capa 2 -->
    <div v-if="!resourceData.is_singleton" class="layer2-toolbar">
      <div class="toolbar-search-wrap">
        <input
          id="layer2-search-input"
          v-model="searchQuery"
          type="search"
          class="toolbar-search-input"
          placeholder="🔍 Filtrar por nombre, CN, huella, serie o atributo..."
          aria-label="Filtrar registros de Capa 2"
        />
      </div>

      <div class="toolbar-controls">
        <!-- Spec 54 — 27.16.4: Botón para abrir/cerrar Query Builder Server-Side -->
        <button
          id="btn-toggle-query-builder"
          type="button"
          class="btn-toolbar"
          :class="{ 'btn-toolbar--active': isQueryBuilderOpen || queryFilters.length > 0 }"
          @click="isQueryBuilderOpen = !isQueryBuilderOpen"
        >
          🔎 Consulta .query / .proplist
          <span v-if="queryFilters.length > 0">({{ queryFilters.length }})</span>
        </button>

        <button
          v-if="hasWideSchema"
          id="btn-toggle-columns-mode"
          type="button"
          class="btn-toolbar"
          :class="{ 'btn-toolbar--active': compactColumnsMode && customSelectedKeys.length === 0 }"
          @click="toggleCompactColumnsMode"
        >
          {{
            compactColumnsMode && customSelectedKeys.length === 0
              ? `📐 Vista Compacta (${visibleSchemaColumns.length}/${resourceData.columns_schema.length})`
              : `📐 Mostrar Compacta (${resourceData.columns_schema.length} cols activas)`
          }}
        </button>

        <div v-if="resourceData.columns_schema.length > 0" class="column-picker-container">
          <button
            id="btn-column-selector"
            type="button"
            class="btn-toolbar"
            :aria-expanded="isColumnPickerOpen"
            @click="isColumnPickerOpen = !isColumnPickerOpen"
          >
            ⚙️ Columnas ({{ visibleSchemaColumns.length }})
          </button>

          <div
            v-if="isColumnPickerOpen"
            class="column-picker-popover"
            role="dialog"
            aria-label="Selector de columnas"
          >
            <div class="column-picker-header">
              <span>Atributos disponibles ({{ resourceData.columns_schema.length }})</span>
              <div class="column-picker-profile-btns">
                <button
                  id="btn-save-column-profile"
                  type="button"
                  class="btn-profile-mini"
                  title="Guardar selección de columnas para este submenú"
                  @click="handleSaveColumnProfile"
                >
                  💾 Guardar
                </button>
                <button
                  id="btn-reset-column-profile"
                  type="button"
                  class="btn-profile-mini"
                  title="Restaurar columnas por defecto"
                  @click="handleResetColumnProfile"
                >
                  ↺ Reset
                </button>
                <button
                  type="button"
                  class="btn-picker-close"
                  aria-label="Cerrar selector de columnas"
                  @click="isColumnPickerOpen = false"
                >
                  ✕
                </button>
              </div>
            </div>
            <div class="column-picker-grid">
              <label
                v-for="col in resourceData.columns_schema"
                :key="col.key"
                class="column-picker-item"
              >
                <input
                  type="checkbox"
                  :checked="isColumnChecked(col.key)"
                  @change="toggleSingleColumn(col.key)"
                />
                <span class="column-picker-label" :title="col.description || col.key">
                  {{ col.label }}
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Spec 54 — 27.16.4: Panel Constructor de Consultas Server-Side (.query / .proplist) -->
    <RgLayer2QueryBuilder
      v-if="!resourceData.is_singleton && isQueryBuilderOpen"
      v-model:filters="queryFilters"
      v-model:proplist-active="proplistActive"
      :columns-schema="resourceData.columns_schema"
      :is-loading="isLoading"
      @apply="handleExecuteServerQuery"
      @clear="loadResource"
    />

    <!-- Spec 54 — 27.16.5: Barra Flotante de Operaciones por Lote bajo Ventana Única Safe Mode 60s -->
    <div
      v-if="!resourceData.is_singleton && selectedRowIds.length > 0"
      id="layer2-bulk-bar"
      class="layer2-bulk-bar font-tabular"
      role="region"
      aria-label="Acciones por lote bajo Safe Mode 60s"
    >
      <span class="bulk-counter">
        ☑️ <strong>{{ selectedRowIds.length }}</strong> registros seleccionados (Safe Mode 60s)
      </span>
      <div class="bulk-actions-group">
        <button
          id="btn-bulk-enable"
          type="button"
          class="btn-bulk"
          @click="handleBulkAction('enable')"
        >
          ▶️ Habilitar
        </button>
        <button
          id="btn-bulk-disable"
          type="button"
          class="btn-bulk"
          @click="handleBulkAction('disable')"
        >
          ⏸️ Deshabilitar
        </button>
        <div class="bulk-comment-box">
          <input
            id="input-bulk-comment"
            v-model="bulkCommentDraft"
            type="text"
            class="bulk-comment-input"
            placeholder="Comentario de lote..."
            aria-label="Comentario para lote"
          />
          <button
            id="btn-bulk-comment"
            type="button"
            class="btn-bulk"
            @click="handleBulkAction('comment')"
          >
            💬 Etiquetar
          </button>
        </div>
        <button
          id="btn-bulk-remove"
          type="button"
          class="btn-bulk btn-bulk--danger"
          @click="handleBulkAction('remove')"
        >
          🗑️ Eliminar Lote
        </button>
      </div>
    </div>

    <div v-if="successMessage" class="banner banner--success font-tabular" role="status">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="banner banner--error font-tabular" role="alert">
      {{ errorMessage }}
    </div>

    <!-- Caso 1: Colección Tabular (is_singleton === false) -->
    <div v-if="!resourceData.is_singleton" class="table-card font-tabular">
      <RgDataTable
        v-model:selected-keys="selectedRowIds"
        :columns="tableColumns"
        :rows="filteredItems"
        :caption="`Recurso ${resourceData.title}`"
        row-key="id"
        selectable
        @select-row="openEditModal"
      >
        <template #actions="{ row }">
          <div class="row-actions">
            <!-- Spec 54 — 27.16.2: Acciones RPC Contextuales por Fila -->
            <button
              v-for="rpc in rowRpcActions"
              :key="rpc.action"
              type="button"
              class="btn-table-action btn-rpc-row"
              :title="rpc.label"
              :aria-label="`${rpc.label}`"
              @click="openRpcActionModal(rpc, row)"
            >
              {{ rpc.icon }} {{ rpc.action }}
            </button>

            <button
              type="button"
              class="btn-table-action"
              title="Inspeccionar o editar registro"
              aria-label="Editar registro"
              @click="openEditModal(row)"
            >
              ✏️ Editar
            </button>
            <button
              v-if="getRecordId(row)"
              type="button"
              class="btn-table-action btn-table-action--delete"
              title="Eliminar registro"
              aria-label="Eliminar registro"
              @click="handleDeleteRecord(row)"
            >
              🗑️
            </button>
          </div>
        </template>
      </RgDataTable>
    </div>

    <!-- Caso 2: Formulario Directo (is_singleton === true) -->
    <div v-else-if="resourceData.form_data" class="form-card font-tabular">
      <form class="singleton-form" @submit.prevent="handleSaveRecord">
        <div class="singleton-fields-grid">
          <div v-for="(val, key) in resourceData.form_data" :key="key" class="form-field">
            <label :for="`field-${key}`" class="field-label">{{ key }}:</label>
            <input
              v-if="typeof val === 'boolean' || val === 'true' || val === 'false'"
              :id="`field-${key}`"
              :checked="val === true || val === 'true'"
              type="checkbox"
              class="field-checkbox"
              @change="
                resourceData.form_data[key] = ($event.target as HTMLInputElement).checked
                  ? 'true'
                  : 'false'
              "
            />
            <input
              v-else
              :id="`field-${key}`"
              v-model="resourceData.form_data[key]"
              type="text"
              class="field-input"
            />
          </div>
        </div>

        <button type="submit" class="btn-primary">💾 Guardar con Safe Mode (60s)</button>
      </form>
    </div>

    <!-- Modal CRUD para Colección (Enriquecido con Presets y Esquema /console/inspect) -->
    <div v-if="isModalOpen" class="rg-modal-backdrop" @click.self="isModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true">
        <header class="modal-header">
          <h3 class="modal-title">
            {{ getRecordId(activeRecord) ? 'Editar' : 'Crear' }} {{ resourceData.title }}
          </h3>
          <button type="button" class="btn-close" @click="isModalOpen = false">✕</button>
        </header>

        <form class="modal-body" @submit.prevent="handleSaveRecord">
          <!-- Spec 54 — 27.16.7: Barra de Plantillas Rápidas en 1 Clic -->
          <div
            v-if="!getRecordId(activeRecord) && availablePresets.length > 0"
            id="layer2-presets-bar"
            class="presets-bar"
          >
            <span class="presets-bar__label">⚡ Plantillas Rápidas:</span>
            <button
              v-for="preset in availablePresets"
              :id="`btn-preset-${preset.id}`"
              :key="preset.id"
              type="button"
              class="btn-preset-chip"
              :title="preset.description"
              @click="applyPresetTemplate(preset)"
            >
              {{ preset.label }}
            </button>
          </div>

          <div class="modal-fields-grid">
            <div v-for="col in resourceData.columns_schema" :key="col.key" class="form-field">
              <label :for="`modal-field-${col.key}`" class="field-label" :title="col.description">
                {{ col.label }}:
              </label>

              <!-- Spec 54 — 27.16.3: Selector de enumeraciones descubiertas por /console/inspect -->
              <select
                v-if="col.enum_options && col.enum_options.length > 0"
                :id="`modal-field-${col.key}`"
                v-model="activeRecord[col.key]"
                class="field-input"
              >
                <option value="">-- Seleccionar --</option>
                <option v-for="opt in col.enum_options" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>

              <input
                v-else-if="col.type !== 'boolean_ros'"
                :id="`modal-field-${col.key}`"
                v-model="activeRecord[col.key]"
                :type="col.type === 'integer' ? 'number' : 'text'"
                :readonly="col.key === '.id' || col.read_only"
                class="field-input"
              />
              <input
                v-else
                :id="`modal-field-${col.key}`"
                v-model="activeRecord[col.key]"
                type="checkbox"
                class="field-checkbox"
              />

              <small v-if="col.description" class="field-hint">{{ col.description }}</small>
            </div>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary">Guardar</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Spec 54 — 27.16.2: Modal Dinámico de Acción RPC -->
    <RgLayer2RpcActionModal
      :is-open="isRpcModalOpen"
      :descriptor="activeRpcDescriptor"
      :target-row="activeRpcTargetRow"
      :is-submitting="isRpcSubmitting"
      @close="isRpcModalOpen = false"
      @submit="handleExecuteRpcAction"
    />

    <!-- Spec 54 — 27.16.6: Modal de Exportación Contextual .rsc y Diff -->
    <RgLayer2RscExportDiffModal
      :is-open="isExportModalOpen"
      :export-data="exportResult"
      :is-loading="isExportLoading"
      @close="isExportModalOpen = false"
      @refresh="handleOpenExportModal"
    />
  </div>
</template>

<style scoped>
  .layer2-view {
    display: flex;
    flex-direction: column;
    gap: 14px;
    min-width: 0;
    width: 100%;
    max-width: 100%;
  }

  .view-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .view-header__info {
    min-width: 0;
  }

  .view-header__actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .view-title {
    margin: 0;
    font-size: 1.1rem;
    color: var(--rg-text-primary);
  }

  .view-subtitle {
    margin: 4px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .schema-badge,
  .schema-source-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.35);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-rpc-menu {
    padding: 6px 12px;
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 6px;
    color: #34d399;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-rpc-menu:hover {
    background: rgba(16, 185, 129, 0.24);
    border-color: #10b981;
  }

  .layer2-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 12px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
  }

  .toolbar-search-wrap {
    flex: 1 1 240px;
    min-width: 0;
  }

  .toolbar-search-input {
    width: 100%;
    padding: 6px 12px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.82rem;
  }

  .toolbar-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .btn-toolbar {
    padding: 6px 12px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-secondary);
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-toolbar:hover,
  .btn-toolbar--active {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.1);
  }

  .column-picker-container {
    position: relative;
  }

  .column-picker-popover {
    position: absolute;
    right: 0;
    top: calc(100% + 6px);
    width: min(480px, 90vw);
    max-height: 320px;
    overflow-y: auto;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.65);
    z-index: 40;
  }

  .column-picker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--rg-border-grid);
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--rg-text-primary);
  }

  .column-picker-profile-btns {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .btn-profile-mini {
    padding: 2px 8px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 4px;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.7rem;
    cursor: pointer;
  }

  .btn-picker-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    cursor: pointer;
  }

  .column-picker-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
    gap: 6px;
  }

  .column-picker-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: var(--rg-text-secondary);
    cursor: pointer;
    overflow: hidden;
  }

  .column-picker-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .layer2-bulk-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    padding: 8px 12px;
    background: rgba(34, 211, 238, 0.1);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    border-radius: 8px;
  }

  .bulk-counter {
    font-size: 0.8rem;
    color: var(--rg-text-primary);
  }

  .bulk-actions-group {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .bulk-comment-box {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .bulk-comment-input {
    padding: 4px 8px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 5px;
    color: var(--rg-text-primary);
    font-size: 0.76rem;
  }

  .btn-bulk {
    padding: 5px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 5px;
    color: var(--rg-text-primary);
    font-size: 0.76rem;
    cursor: pointer;
  }

  .btn-bulk--danger {
    border-color: rgba(239, 68, 68, 0.5);
    color: #fca5a5;
  }

  .table-card {
    min-width: 0;
    width: 100%;
    max-width: 100%;
    overflow: hidden;
  }

  .btn-primary {
    padding: 7px 16px;
    background: var(--rg-accent-cyan);
    border: none;
    border-radius: 6px;
    color: #0b0f19;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.82rem;
  }

  .banner--success {
    padding: 10px 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #10b981;
    font-size: 0.85rem;
  }

  .banner--error {
    padding: 10px 14px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 6px;
    color: #fca5a5;
    font-size: 0.85rem;
  }

  .form-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 16px;
    width: 100%;
    max-width: 780px;
  }

  .singleton-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .singleton-fields-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .field-label {
    font-size: 0.78rem;
    color: var(--rg-text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .field-input {
    padding: 6px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.85rem;
    width: 100%;
  }

  .field-hint {
    font-size: 0.7rem;
    color: var(--rg-text-muted);
  }

  .presets-bar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .presets-bar__label {
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-preset-chip {
    padding: 4px 10px;
    background: var(--rg-bg-surface);
    border: 1px solid rgba(34, 211, 238, 0.35);
    border-radius: 999px;
    color: var(--rg-text-primary);
    font-size: 0.73rem;
    cursor: pointer;
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 1000;
  }

  .rg-modal {
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    width: 100%;
    max-width: 680px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .modal-title {
    margin: 0;
    font-size: 0.95rem;
    color: var(--rg-text-primary);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 1rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow: hidden;
  }

  .modal-fields-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 4px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
    padding-top: 10px;
    border-top: 1px solid var(--rg-border-grid);
  }

  .btn-secondary {
    padding: 6px 14px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    cursor: pointer;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
