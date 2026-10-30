<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts" generic="T extends Record<string, unknown>">
  import { computed, onMounted, ref } from 'vue';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
  import type { TableColumn, TableRowFlags } from '@/types';

  const props = withDefaults(
    defineProps<{
      columns: TableColumn<T>[];
      rows: T[];
      rowKey?: string;
      sortableRows?: boolean;
      selectedKey?: string | null;
      ariaLabel?: string;
      caption?: string;
      emptyMessage?: string;
    }>(),
    {
      rowKey: 'id',
      sortableRows: false,
      selectedKey: null,
      ariaLabel: 'Tabla de datos técnicos',
      caption: 'Listado de recursos MikroTik',
      emptyMessage: 'No se encontraron registros para mostrar en esta vista.',
    },
  );

  const emit = defineEmits<{
    (e: 'select-row', row: T): void;
    (e: 'reorder', payload: { fromIndex: number; toIndex: number; row: T }): void;
  }>();

  defineSlots<{
    default?(): unknown;
    actions?(props: { row: T }): unknown;
    empty?(): unknown;
  }>();

  const themeStore = useThemeAndLayoutStore();

  // Filtrar columna 'actions' duplicada cuando se usa el slot #actions
  const dataColumns = computed(() => props.columns.filter((c) => c.key !== 'actions'));

  // Virtual Scrolling Nativo (> 100 filas)
  const scrollContainerRef = ref<HTMLElement | null>(null);
  const scrollTop = ref<number>(0);
  const containerHeight = ref<number>(480);
  const expandedRowKeys = ref<Set<string>>(new Set());

  const isVirtualActive = computed(() => props.rows.length > 100);

  const rowHeight = computed(() => {
    return themeStore.effectiveTableDensity === 'compact' ? 32 : 44;
  });

  const totalRows = computed(() => props.rows.length);

  const visibleRange = computed(() => {
    if (!isVirtualActive.value) {
      return { start: 0, end: totalRows.value };
    }
    const itemH = rowHeight.value;
    const start = Math.max(0, Math.floor(scrollTop.value / itemH) - 10);
    const visibleCount = Math.ceil(containerHeight.value / itemH) + 20;
    const end = Math.min(totalRows.value, start + visibleCount);
    return { start, end };
  });

  const topSpacerHeight = computed(() => {
    if (!isVirtualActive.value) return 0;
    return visibleRange.value.start * rowHeight.value;
  });

  const bottomSpacerHeight = computed(() => {
    if (!isVirtualActive.value) return 0;
    return (totalRows.value - visibleRange.value.end) * rowHeight.value;
  });

  const visibleRows = computed(() => {
    if (!isVirtualActive.value) {
      return props.rows;
    }
    return props.rows.slice(visibleRange.value.start, visibleRange.value.end);
  });

  function handleScroll(e: Event): void {
    const target = e.target as HTMLElement;
    scrollTop.value = target.scrollTop;
  }

  onMounted(() => {
    if (scrollContainerRef.value) {
      containerHeight.value = scrollContainerRef.value.clientHeight || 480;
    }
  });

  // Selector de filas y detalles en móvil
  function getKey(row: T, index: number): string {
    const k = row[props.rowKey] ?? row['.id'] ?? row['id'];
    return k !== undefined && k !== null ? String(k) : String(index);
  }

  function getCellText(col: TableColumn<T>, row: T): string {
    return String(col.formatter ? col.formatter(row) : (row[col.key] ?? '—'));
  }

  function handleRowClick(row: T): void {
    emit('select-row', row);
  }

  function toggleDetails(key: string): void {
    if (expandedRowKeys.value.has(key)) {
      expandedRowKeys.value.delete(key);
    } else {
      expandedRowKeys.value.add(key);
    }
  }

  // Banderas / Flags nativas RouterOS ([D], [X], [I], [R])
  function getRowFlags(row: T): TableRowFlags {
    const flags = row.flags as TableRowFlags | undefined;
    if (flags) return flags;

    return {
      dynamic: Boolean(row.dynamic || row['.dynamic']),
      disabled: Boolean(row.disabled || row['.disabled']),
      invalid: Boolean(row.invalid || row['.invalid']),
      invalidReason: String(row.invalidReason || row['comment'] || ''),
      running: Boolean(row.running || row.is_reachable),
    };
  }

  // Reordenamiento por Teclado (Alt + Arriba / Alt + Abajo) y Drag & Drop
  let draggedIndex: number | null = null;

  function moveRow(index: number, direction: 'up' | 'down'): void {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= props.rows.length) return;

    emit('reorder', {
      fromIndex: index,
      toIndex: targetIndex,
      row: props.rows[index],
    });
  }

  function handleDragStart(index: number, e: DragEvent): void {
    draggedIndex = index;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
    }
  }

  function handleDrop(targetIndex: number, e: DragEvent): void {
    e.preventDefault();
    if (draggedIndex !== null && draggedIndex !== targetIndex) {
      emit('reorder', {
        fromIndex: draggedIndex,
        toIndex: targetIndex,
        row: props.rows[draggedIndex],
      });
    }
    draggedIndex = null;
  }
</script>

<template>
  <div class="rg-table-wrapper" :class="`rg-density-${themeStore.effectiveTableDensity}`">
    <!-- Barra Superior: Conmutador de Densidad y Total -->
    <header class="rg-table-toolbar">
      <div class="rg-table-toolbar__title">
        <span class="rg-table-counter">{{ totalRows }} recursos</span>
      </div>
      <div class="rg-table-toolbar__actions">
        <button
          type="button"
          class="rg-density-toggle"
          :aria-label="`Cambiar densidad de tabla (actual: ${themeStore.effectiveTableDensity})`"
          @click="themeStore.toggleTableDensity()"
        >
          <span v-if="themeStore.effectiveTableDensity === 'compact'" aria-hidden="true"
            >≡ Compacta (32px)</span
          >
          <span v-else aria-hidden="true">☰ Cómoda (44px)</span>
        </button>
      </div>
    </header>

    <!-- Contenedor con Scroll Virtual y Container Queries -->
    <div
      ref="scrollContainerRef"
      class="rg-table-scroll table-wrapper"
      role="region"
      tabindex="0"
      :aria-label="ariaLabel"
      @scroll.passive="handleScroll"
    >
      <table class="rg-table" role="table">
        <caption class="sr-only">
          {{
            caption
          }}
        </caption>
        <thead>
          <tr>
            <th v-if="sortableRows" class="col-drag" scope="col" aria-label="Orden">#</th>
            <th class="col-flags" scope="col" aria-label="Banderas MikroTik">Flags</th>
            <th
              v-for="col in dataColumns"
              :key="col.key"
              scope="col"
              :class="{ 'num-col': col.align === 'right' }"
              :style="{ width: col.width, textAlign: col.align || 'left' }"
            >
              {{ col.label }}
            </th>
            <th v-if="$slots.actions" class="col-custom-actions" scope="col">Acciones</th>
            <th
              v-if="themeStore.effectiveTableDensity === 'comfortable'"
              class="col-actions"
              scope="col"
            >
              Detalles
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Espaciador Virtual Superior -->
          <tr
            v-if="topSpacerHeight > 0"
            :style="{ height: `${topSpacerHeight}px` }"
            aria-hidden="true"
          >
            <td :colspan="dataColumns.length + 3"></td>
          </tr>

          <!-- Filas Visibles -->
          <template v-for="(row, idx) in visibleRows" :key="getKey(row, visibleRange.start + idx)">
            <tr
              class="rg-table-row"
              :class="{
                'rg-row--active': selectedKey === getKey(row, visibleRange.start + idx),
                'rg-row--disabled': getRowFlags(row).disabled,
              }"
              :draggable="sortableRows"
              @click="handleRowClick(row)"
              @dragstart="handleDragStart(visibleRange.start + idx, $event)"
              @dragover.prevent
              @drop="handleDrop(visibleRange.start + idx, $event)"
            >
              <!-- Drag / Reorder Controls -->
              <td v-if="sortableRows" class="col-drag" @click.stop>
                <div class="drag-controls">
                  <button
                    type="button"
                    class="btn-arrow"
                    aria-label="Mover fila hacia arriba"
                    :disabled="visibleRange.start + idx === 0"
                    @click="moveRow(visibleRange.start + idx, 'up')"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    class="btn-arrow"
                    aria-label="Mover fila hacia abajo"
                    :disabled="visibleRange.start + idx === totalRows - 1"
                    @click="moveRow(visibleRange.start + idx, 'down')"
                  >
                    ▼
                  </button>
                </div>
              </td>

              <!-- Flags MikroTik -->
              <td class="col-flags">
                <div class="flags-container">
                  <span v-if="getRowFlags(row).dynamic" class="rg-flag rg-flag--d" title="Dynamic"
                    >[D]</span
                  >
                  <span v-if="getRowFlags(row).disabled" class="rg-flag rg-flag--x" title="Disabled"
                    >[X]</span
                  >
                  <span
                    v-if="getRowFlags(row).invalid"
                    class="rg-flag rg-flag--i"
                    :title="getRowFlags(row).invalidReason || 'Regla Inválida'"
                    >[I]</span
                  >
                  <span v-if="getRowFlags(row).running" class="rg-flag rg-flag--r" title="Running"
                    >[R]</span
                  >
                </div>
              </td>

              <!-- Celdas de Datos -->
              <td
                v-for="col in dataColumns"
                :key="col.key"
                class="rg-data"
                :class="{ 'num-col': col.align === 'right' }"
                :data-label="col.label"
                :title="getCellText(col, row)"
                :style="{ textAlign: col.align || 'left' }"
              >
                {{ getCellText(col, row) }}
              </td>

              <!-- Acciones Personalizadas -->
              <td v-if="$slots.actions" class="col-custom-actions" @click.stop>
                <slot name="actions" :row="row" />
              </td>

              <!-- Botón Móvil: Ver Detalles -->
              <td
                v-if="themeStore.effectiveTableDensity === 'comfortable'"
                class="col-actions"
                @click.stop
              >
                <button
                  type="button"
                  class="btn-details-toggle"
                  :aria-expanded="expandedRowKeys.has(getKey(row, visibleRange.start + idx))"
                  @click="toggleDetails(getKey(row, visibleRange.start + idx))"
                >
                  {{
                    expandedRowKeys.has(getKey(row, visibleRange.start + idx)) ? 'Ocultar' : '+ Ver'
                  }}
                </button>
              </td>
            </tr>

            <!-- Fila Expandida de Detalles Secundarios (Móvil) -->
            <tr
              v-if="expandedRowKeys.has(getKey(row, visibleRange.start + idx))"
              class="rg-row-details"
            >
              <td :colspan="dataColumns.length + 3">
                <dl class="details-grid">
                  <template v-for="col in dataColumns" :key="col.key">
                    <dt>{{ col.label }}:</dt>
                    <dd class="rg-data">
                      {{ col.formatter ? col.formatter(row) : (row[col.key] ?? '—') }}
                    </dd>
                  </template>
                </dl>
              </td>
            </tr>
          </template>

          <!-- Espaciador Virtual Inferior -->
          <tr
            v-if="bottomSpacerHeight > 0"
            :style="{ height: `${bottomSpacerHeight}px` }"
            aria-hidden="true"
          >
            <td :colspan="dataColumns.length + 3"></td>
          </tr>
        </tbody>
      </table>

      <!-- Refactoring UI: Empty State Táctico ("Empty states come first") -->
      <div
        v-if="totalRows === 0"
        class="rg-table-empty"
        role="status"
        aria-live="polite"
      >
        <slot name="empty">
          <span class="rg-table-empty__icon" aria-hidden="true">📭</span>
          <p class="rg-table-empty__text">{{ emptyMessage }}</p>
        </slot>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .rg-table-wrapper {
    display: flex;
    flex-direction: column;
    min-width: 0;
    width: 100%;
    max-width: 100%;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    border-radius: var(--rg-radius-lg, 8px);
    box-shadow: var(--rg-inset-highlight);
    overflow: hidden;
  }

  .rg-table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--rg-space-2, 8px);
    padding: var(--rg-space-2, 8px) var(--rg-space-3, 12px);
    background: var(--rg-bg-elevated);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .rg-table-counter {
    font-size: var(--rg-text-xs, 0.75rem);
    color: var(--rg-text-muted);
    font-family: var(--rg-font-mono);
  }

  .rg-density-toggle {
    background: transparent;
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-secondary);
    font-size: var(--rg-text-xs, 0.75rem);
    padding: 4px 8px;
    border-radius: var(--rg-radius-sm, 4px);
    cursor: pointer;
  }

  .rg-density-toggle:hover {
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
  }

  .rg-table-scroll {
    width: 100%;
    max-width: 100%;
    max-height: 520px;
    overflow: auto;
    position: relative;
    container-type: inline-size;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--rg-text-sm, 0.8125rem);
  }

  td.rg-data {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .num-col {
    font-variant-numeric: tabular-nums lining-nums;
  }

  /* Densidad Compacta (32px WinBox) */
  .rg-density-compact th,
  .rg-density-compact td {
    height: 32px;
    padding: 2px 8px;
    border-right: 1px solid var(--rg-border-grid);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  /* Densidad Cómoda (44px Táctil) */
  .rg-density-comfortable th,
  .rg-density-comfortable td {
    height: 44px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  thead th {
    position: sticky;
    top: 0;
    background: var(--rg-bg-elevated);
    color: var(--rg-text-secondary);
    font-weight: 600;
    font-size: var(--rg-text-xs, 0.75rem);
    text-align: left;
    white-space: nowrap;
    z-index: 10;
    user-select: none;
  }

  .rg-table-row {
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .rg-table-row:hover {
    background-color: var(--rg-bg-elevated);
  }

  .col-flags {
    width: 65px;
    min-width: 65px;
    text-align: center;
  }

  .flags-container {
    display: flex;
    gap: 2px;
    justify-content: center;
  }

  .col-drag {
    width: 36px;
    text-align: center;
  }

  .drag-controls {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .btn-arrow {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 8px;
    cursor: pointer;
    line-height: 1;
  }

  .btn-arrow:hover:not(:disabled) {
    color: var(--rg-accent-cyan);
  }

  .btn-details-toggle {
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-accent-cyan);
    padding: 4px 8px;
    border-radius: var(--rg-radius-sm, 4px);
    font-size: var(--rg-text-2xs, 0.6875rem);
    cursor: pointer;
  }

  .col-custom-actions {
    white-space: nowrap;
    text-align: right;
    position: sticky;
    right: 0;
    background: var(--rg-bg-surface);
    box-shadow: -4px 0 8px rgba(0, 0, 0, 0.2);
    z-index: 5;
  }

  thead th.col-custom-actions {
    background: var(--rg-bg-elevated);
    z-index: 12;
  }

  .rg-table-row:hover td.col-custom-actions {
    background: var(--rg-bg-elevated);
  }

  .col-custom-actions :deep(.row-actions),
  .col-custom-actions :deep(.row-actions-group) {
    display: inline-flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
  }

  .col-custom-actions :deep(.btn-table-action),
  .col-custom-actions :deep(.btn-row-action),
  .col-custom-actions :deep(.btn-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    background: var(--rg-btn-action-bg, #1e293b);
    border: 1px solid var(--rg-btn-action-border, #334155);
    border-radius: var(--rg-radius-sm, 4px);
    color: var(--rg-btn-action-fg, #cbd5e1);
    font-size: 0.75rem;
    font-weight: 500;
    padding: 3px 8px;
    cursor: pointer;
    transition: all 0.15s ease;
    line-height: 1.2;
  }

  .col-custom-actions :deep(.btn-table-action:hover),
  .col-custom-actions :deep(.btn-row-action:hover),
  .col-custom-actions :deep(.btn-icon:hover) {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
    box-shadow: 0 0 8px rgba(34, 211, 238, 0.15);
  }

  .col-custom-actions :deep(.btn-table-action--delete),
  .col-custom-actions :deep(.btn-table-action--danger),
  .col-custom-actions :deep(.btn-row-action--danger),
  .col-custom-actions :deep(.btn-danger) {
    border-color: var(--rg-btn-action-danger-border, rgba(239, 68, 68, 0.45));
    color: var(--rg-btn-action-danger-fg, #fca5a5);
  }

  .col-custom-actions :deep(.btn-table-action--delete:hover),
  .col-custom-actions :deep(.btn-table-action--danger:hover),
  .col-custom-actions :deep(.btn-row-action--danger:hover),
  .col-custom-actions :deep(.btn-danger:hover) {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.2);
  }

  .rg-row-details td {
    background: var(--rg-bg-canvas);
    padding: var(--rg-space-3, 12px);
  }

  /* Refactoring UI: Demote labels (<dt>) so values (<dd>) stand out */
  .details-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    row-gap: 6px;
    align-items: baseline;
    font-size: var(--rg-text-xs, 0.75rem);
  }

  .details-grid dt {
    font-size: var(--rg-text-2xs, 0.6875rem);
    font-weight: 600;
    color: var(--rg-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .details-grid dd {
    font-size: var(--rg-text-xs, 0.75rem);
    font-weight: 600;
    color: var(--rg-text-primary);
    word-break: break-word;
  }

  @container (max-width: 480px) {
    .details-grid {
      grid-template-columns: 1fr;
      row-gap: 4px;
    }

    .details-grid dd {
      margin-bottom: 6px;
    }
  }

  @media (max-width: 480px) {
    .details-grid {
      grid-template-columns: 1fr;
      row-gap: 4px;
    }

    .details-grid dd {
      margin-bottom: 6px;
    }
  }

  .rg-table-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--rg-space-2, 8px);
    padding: var(--rg-space-8, 32px) var(--rg-space-4, 16px);
    text-align: center;
    color: var(--rg-text-muted);
    background: var(--rg-bg-surface);
  }

  .rg-table-empty__icon {
    font-size: var(--rg-text-xl, 1.5rem);
    opacity: 0.65;
    line-height: 1;
  }

  .rg-table-empty__text {
    font-size: var(--rg-text-sm, 0.8125rem);
    color: var(--rg-text-secondary);
    max-width: 55ch;
    margin: 0;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>
