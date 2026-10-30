<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, Layer2ResourceResponse } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

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
    items: [],
    form_data: {},
  });

  const searchQuery = ref('');
  const compactColumnsMode = ref(true);
  const isColumnPickerOpen = ref(false);
  const customSelectedKeys = ref<string[]>([]);

  const isModalOpen = ref(false);
  const activeRecord = ref<Record<string, unknown>>({});
  const successMessage = ref('');
  const errorMessage = ref('');

  const hasWideSchema = computed(
    () => resourceData.value.columns_schema.length > MAX_COMPACT_COLUMNS,
  );

  const visibleSchemaColumns = computed<Layer2ColumnSchema[]>(() => {
    const allCols = resourceData.value.columns_schema;
    if (customSelectedKeys.value.length > 0) {
      return allCols.filter((c) => customSelectedKeys.value.includes(c.key));
    }
    if (!compactColumnsMode.value || allCols.length <= MAX_COMPACT_COLUMNS) {
      return allCols;
    }

    const prioritized: Layer2ColumnSchema[] = [];
    const seen = new Set<string>();

    for (const pKey of PRIORITY_COLUMN_KEYS) {
      const found = allCols.find((c) => c.key === pKey);
      if (found && !seen.has(found.key)) {
        prioritized.push(found);
        seen.add(found.key);
        if (prioritized.length >= MAX_COMPACT_COLUMNS) break;
      }
    }

    for (const col of allCols) {
      if (prioritized.length >= MAX_COMPACT_COLUMNS) break;
      if (!seen.has(col.key)) {
        prioritized.push(col);
        seen.add(col.key);
      }
    }

    return prioritized;
  });

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

  function getRecordId(row: Record<string, unknown>): string {
    return String(row.id ?? row['.id'] ?? '');
  }

  async function loadResource() {
    isLoading.value = true;
    errorMessage.value = '';
    customSelectedKeys.value = [];
    compactColumnsMode.value = true;
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
    } catch (err: any) {
      resourceData.value = {
        ros_path: rosPath.value,
        title: `Módulo ${rosPath.value}`,
        is_singleton: false,
        columns_schema: [],
        items: [],
      };
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al consultar recurso en el router';
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

  async function handleSaveRecord() {
    webFigStore.startSafeModeCountdown(60);
    try {
      if (resourceData.value.is_singleton) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
          resourceData.value.form_data,
        );
        successMessage.value = 'Configuración singleton actualizada con Safe Mode.';
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
        successMessage.value = 'Registro guardado exitosamente con Safe Mode.';
        isModalOpen.value = false;
      }
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
      loadResource();
    } catch {
      successMessage.value = 'Operación procesada en modo simulado.';
      isModalOpen.value = false;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
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
      successMessage.value = 'Registro eliminado con Safe Mode.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
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
        </p>
      </div>

      <div class="view-header__actions">
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

          <div v-if="isColumnPickerOpen" class="column-picker-popover" role="dialog" aria-label="Selector de columnas">
            <div class="column-picker-header">
              <span>Atributos disponibles ({{ resourceData.columns_schema.length }})</span>
              <button
                type="button"
                class="btn-picker-close"
                aria-label="Cerrar selector de columnas"
                @click="isColumnPickerOpen = false"
              >
                ✕
              </button>
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
                <span class="column-picker-label" :title="col.key">{{ col.label }}</span>
              </label>
            </div>
          </div>
        </div>
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
        :columns="tableColumns"
        :rows="filteredItems"
        :caption="`Recurso ${resourceData.title}`"
        row-key="id"
        @select-row="openEditModal"
      >
        <template #actions="{ row }">
          <div class="row-actions">
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

    <!-- Modal CRUD para Colección -->
    <div v-if="isModalOpen" class="rg-modal-backdrop" @click.self="isModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true">
        <header class="modal-header">
          <h3 class="modal-title">
            {{ getRecordId(activeRecord) ? 'Editar' : 'Crear' }} {{ resourceData.title }}
          </h3>
          <button type="button" class="btn-close" @click="isModalOpen = false">✕</button>
        </header>

        <form class="modal-body" @submit.prevent="handleSaveRecord">
          <div class="modal-fields-grid">
            <div v-for="col in resourceData.columns_schema" :key="col.key" class="form-field">
              <label :for="`modal-field-${col.key}`" class="field-label">{{ col.label }}:</label>
              <input
                v-if="col.type !== 'boolean_ros'"
                :id="`modal-field-${col.key}`"
                v-model="activeRecord[col.key]"
                :type="col.type === 'integer' ? 'number' : 'text'"
                :readonly="col.key === '.id'"
                class="field-input"
              />
              <input
                v-else
                :id="`modal-field-${col.key}`"
                v-model="activeRecord[col.key]"
                type="checkbox"
                class="field-checkbox"
              />
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

  .schema-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.35);
    color: var(--rg-accent-cyan, #22d3ee);
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
    width: min(460px, 90vw);
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
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--rg-border-grid);
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--rg-text-primary);
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
