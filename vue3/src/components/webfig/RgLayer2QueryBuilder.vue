<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import type { Layer2ColumnSchemaItem, Layer2QueryFilterItem } from '@/types';

  const props = withDefaults(
    defineProps<{
      columnsSchema: Layer2ColumnSchemaItem[];
      filters: Layer2QueryFilterItem[];
      proplistActive: boolean;
      isLoading?: boolean;
    }>(),
    {
      isLoading: false,
    },
  );

  const emit = defineEmits<{
    (e: 'update:filters', filters: Layer2QueryFilterItem[]): void;
    (e: 'update:proplistActive', active: boolean): void;
    (e: 'apply'): void;
    (e: 'clear'): void;
  }>();

  const draftField = ref<string>(props.columnsSchema[0]?.key || 'name');
  const draftOperator = ref<Layer2QueryFilterItem['operator']>('=');
  const draftValue = ref<string>('');

  watch(
    () => props.columnsSchema,
    (cols) => {
      if (cols.length > 0 && !cols.some((c) => c.key === draftField.value)) {
        draftField.value = cols[0].key;
      }
    },
    { immediate: true },
  );

  function notifyFilters(next: Layer2QueryFilterItem[]): void {
    emit('update:filters', next);
  }

  function addFilterPill(): void {
    const val = draftValue.value.trim();
    if (!draftField.value || !val) return;
    const next: Layer2QueryFilterItem[] = [
      ...props.filters,
      {
        field: draftField.value,
        operator: draftOperator.value,
        value: val,
      },
    ];
    draftValue.value = '';
    notifyFilters(next);
  }

  function removeFilterPill(index: number): void {
    const next = props.filters.filter((_, i) => i !== index);
    notifyFilters(next);
  }

  function handleClearAll(): void {
    draftValue.value = '';
    notifyFilters([]);
    emit('clear');
  }

  function toggleProplist(e: Event): void {
    const checked = (e.target as HTMLInputElement).checked;
    emit('update:proplistActive', checked);
  }
</script>

<template>
  <section
    id="layer2-query-builder"
    class="l2-query-builder font-tabular"
    aria-label="Constructor de consultas Server-Side RouterOS (.query y .proplist)"
  >
    <div class="qb-controls-row">
      <div class="qb-field-group">
        <label for="qb-select-field" class="qb-label">Campo:</label>
        <select id="qb-select-field" v-model="draftField" class="qb-select">
          <option v-for="col in columnsSchema" :key="col.key" :value="col.key">
            {{ col.label }} ({{ col.key }})
          </option>
        </select>
      </div>

      <div class="qb-field-group">
        <label for="qb-select-operator" class="qb-label">Op:</label>
        <select id="qb-select-operator" v-model="draftOperator" class="qb-select qb-select--op">
          <option value="=">=</option>
          <option value="!=">!=</option>
          <option value="~">~ (contiene)</option>
          <option value=">">&gt;</option>
          <option value="<">&lt;</option>
        </select>
      </div>

      <div class="qb-field-group qb-field-group--value">
        <label for="qb-input-value" class="qb-label">Valor:</label>
        <input
          id="qb-input-value"
          v-model="draftValue"
          type="text"
          class="qb-input"
          placeholder="Ej. true, rosgrid-ca, 10.0.0.1..."
          @keydown.enter.prevent="addFilterPill"
        />
      </div>

      <button
        id="btn-add-l2-filter"
        type="button"
        class="btn-qb-secondary"
        @click="addFilterPill"
      >
        + Condición
      </button>

      <label class="qb-proplist-toggle" title="Solicitar al router únicamente las columnas visibles">
        <input
          id="chk-proplist-optimize"
          type="checkbox"
          :checked="proplistActive"
          @change="toggleProplist"
        />
        <span>⚡ Optimizar Payload (<code>.proplist</code>)</span>
      </label>

      <div class="qb-actions">
        <button
          id="btn-apply-l2-query"
          type="button"
          class="btn-qb-primary"
          :disabled="isLoading"
          @click="emit('apply')"
        >
          🔎 Consultar Router (<code>.query</code>)
        </button>
        <button
          v-if="filters.length > 0"
          id="btn-clear-l2-query"
          type="button"
          class="btn-qb-clear"
          @click="handleClearAll"
        >
          Limpiar
        </button>
      </div>
    </div>

    <div v-if="filters.length > 0" class="qb-pills-row" role="list" aria-label="Filtros activos">
      <span
        v-for="(f, idx) in filters"
        :key="`${f.field}-${f.operator}-${f.value}-${idx}`"
        class="qb-pill"
        role="listitem"
      >
        <code>{{ f.field }} {{ f.operator }} {{ f.value }}</code>
        <button
          type="button"
          class="qb-pill-remove"
          :aria-label="`Eliminar condición ${f.field}`"
          @click="removeFilterPill(idx)"
        >
          ✕
        </button>
      </span>
    </div>
  </section>
</template>

<style scoped>
  .l2-query-builder {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px 12px;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px dashed rgba(34, 211, 238, 0.4);
    border-radius: 8px;
  }

  .qb-controls-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .qb-field-group {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .qb-field-group--value {
    flex: 1 1 180px;
  }

  .qb-label {
    font-size: 0.74rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .qb-select,
  .qb-input {
    padding: 5px 8px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 5px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.78rem;
  }

  .qb-input {
    width: 100%;
  }

  .qb-proplist-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: var(--rg-accent-cyan, #22d3ee);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 5px;
    background: rgba(34, 211, 238, 0.08);
  }

  .qb-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
  }

  .btn-qb-secondary,
  .btn-qb-clear {
    padding: 5px 10px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 5px;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.76rem;
    cursor: pointer;
  }

  .btn-qb-primary {
    padding: 5px 12px;
    background: var(--rg-accent-cyan, #22d3ee);
    border: none;
    border-radius: 5px;
    color: #0b0f19;
    font-weight: 700;
    font-size: 0.76rem;
    cursor: pointer;
  }

  .qb-pills-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }

  .qb-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.14);
    border: 1px solid rgba(34, 211, 238, 0.4);
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.74rem;
  }

  .qb-pill-remove {
    background: transparent;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 0.72rem;
    padding: 0;
  }
</style>
