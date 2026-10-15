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
    }>(),
    {
      rowKey: 'id',
      sortableRows: false,
      selectedKey: null,
      ariaLabel: 'Tabla de datos técnicos',
      caption: 'Listado de recursos MikroTik',
    },
  );

  const emit = defineEmits<{
    (e: 'select-row', row: T): void;
    (e: 'reorder', payload: { fromIndex: number; toIndex: number; row: T }): void;
  }>();

  defineSlots<{
    default?(): unknown;
    actions?(props: { row: T }): unknown;
  }>();

  const themeStore = useThemeAndLayoutStore();

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
    const k = row[props.rowKey];
    return k !== undefined && k !== null ? String(k) : String(index);
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

    <!-- Contenedor con Scroll Virtual -->
    <div
      ref="scrollContainerRef"
      class="rg-table-scroll"
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
              v-for="col in columns"
              :key="col.key"
              scope="col"
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
            <td :colspan="columns.length + 3"></td>
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
                v-for="col in columns"
                :key="col.key"
                class="rg-data"
                :style="{ textAlign: col.align || 'left' }"
              >
                {{ col.formatter ? col.formatter(row) : (row[col.key] ?? '—') }}
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
              <td :colspan="columns.length + 3">
                <dl class="details-grid">
                  <template v-for="col in columns" :key="col.key">
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
            <td :colspan="columns.length + 3"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
  .rg-table-wrapper {
    display: flex;
    flex-direction: column;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    border-radius: 6px;
    overflow: hidden;
  }

  .rg-table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--rg-bg-elevated);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .rg-table-counter {
    font-size: 12px;
    color: var(--rg-text-muted);
    font-family: var(--rg-font-mono);
  }

  .rg-density-toggle {
    background: transparent;
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-secondary);
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
  }

  .rg-density-toggle:hover {
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
  }

  .rg-table-scroll {
    max-height: 520px;
    overflow: auto;
    position: relative;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
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
    font-size: 12px;
    text-align: left;
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
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
  }

  .rg-row-details td {
    background: var(--rg-bg-canvas);
    padding: 12px;
  }

  .details-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    row-gap: 6px;
    font-size: 12px;
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
