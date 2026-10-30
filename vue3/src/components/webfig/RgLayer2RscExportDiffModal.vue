<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import type { Layer2ExportResponse } from '@/types';

  const props = withDefaults(
    defineProps<{
      isOpen: boolean;
      exportData: Layer2ExportResponse | null;
      isLoading?: boolean;
    }>(),
    {
      isLoading: false,
    },
  );

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'refresh', payload: { compact: boolean; hide_sensitive: boolean }): void;
  }>();

  const activeTab = ref<'rsc' | 'diff'>('rsc');
  const compactMode = ref(true);
  const hideSensitive = ref(true);
  const copyFeedback = ref('');

  const diffLines = computed<Array<{ text: string; kind: 'add' | 'del' | 'meta' | 'ctx' }>>(() => {
    const raw = props.exportData?.unified_diff || '';
    if (!raw.trim()) return [];
    return raw.split('\n').map((line) => {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
        return { text: line, kind: 'meta' };
      }
      if (line.startsWith('+')) {
        return { text: line, kind: 'add' };
      }
      if (line.startsWith('-')) {
        return { text: line, kind: 'del' };
      }
      return { text: line, kind: 'ctx' };
    });
  });

  function triggerRefresh(): void {
    emit('refresh', {
      compact: compactMode.value,
      hide_sensitive: hideSensitive.value,
    });
  }

  async function copyRscToClipboard(): Promise<void> {
    if (!props.exportData?.exported_rsc) return;
    try {
      await navigator.clipboard?.writeText(props.exportData.exported_rsc);
      copyFeedback.value = '✅ Copiado';
    } catch {
      copyFeedback.value = '📋 Listo';
    }
    setTimeout(() => {
      copyFeedback.value = '';
    }, 2000);
  }
</script>

<template>
  <div
    v-if="isOpen"
    id="layer2-rsc-export-modal"
    class="rg-modal-backdrop"
    @click.self="emit('close')"
  >
    <div
      class="rg-modal font-tabular"
      role="dialog"
      aria-modal="true"
      aria-label="Exportación contextual .rsc y Diff contra respaldo Git"
    >
      <header class="modal-header">
        <div class="header-info">
          <h3 class="modal-title">
            📜 Exportación Contextual <code>/{{ exportData?.ros_path || '' }}</code>
          </h3>
          <span
            v-if="exportData"
            class="drift-badge"
            :class="exportData.has_drift ? 'drift-badge--warn' : 'drift-badge--ok'"
          >
            {{
              exportData.has_drift
                ? '⚠️ Desviación detectada vs Respaldo'
                : '✅ Sin cambios vs Respaldo'
            }}
          </span>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de exportación .rsc"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="export-toolbar">
        <div class="tab-group" role="tablist">
          <button
            id="tab-rsc-script"
            type="button"
            role="tab"
            class="tab-btn"
            :aria-selected="activeTab === 'rsc'"
            :class="{ 'tab-btn--active': activeTab === 'rsc' }"
            @click="activeTab = 'rsc'"
          >
            📄 Script .rsc Actual
          </button>
          <button
            id="tab-rsc-diff"
            type="button"
            role="tab"
            class="tab-btn"
            :aria-selected="activeTab === 'diff'"
            :class="{ 'tab-btn--active': activeTab === 'diff' }"
            @click="activeTab = 'diff'"
          >
            🔍 Diff Unificado
          </button>
        </div>

        <div class="export-options">
          <label class="opt-label">
            <input v-model="compactMode" type="checkbox" @change="triggerRefresh" />
            <span>compact</span>
          </label>
          <label class="opt-label">
            <input v-model="hideSensitive" type="checkbox" @change="triggerRefresh" />
            <span>hide-sensitive</span>
          </label>
          <button
            id="btn-copy-rsc"
            type="button"
            class="btn-tool"
            @click="copyRscToClipboard"
          >
            {{ copyFeedback || '📋 Copiar .rsc' }}
          </button>
        </div>
      </div>

      <div class="modal-body">
        <div v-if="isLoading" class="loading-box">⏳ Generando exportación contextual .rsc...</div>

        <pre
          v-else-if="activeTab === 'rsc'"
          id="layer2-rsc-code"
          class="code-viewer"
        ><code>{{ exportData?.exported_rsc || '# Sin configuración exportada' }}</code></pre>

        <div v-else id="layer2-rsc-diff-view" class="diff-viewer">
          <p v-if="diffLines.length === 0" class="no-diff-msg">
            ✅ No existen diferencias entre el estado vivo del submenú y el último respaldo.
          </p>
          <div
            v-for="(line, idx) in diffLines"
            :key="idx"
            class="diff-line"
            :class="`diff-line--${line.kind}`"
          >
            {{ line.text }}
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn-secondary" @click="emit('close')">Cerrar</button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.78);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 1050;
  }

  .rg-modal {
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    width: 100%;
    max-width: 760px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.65);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  }

  .header-info {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }

  .modal-title {
    margin: 0;
    font-size: 0.95rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .drift-badge {
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
  }

  .drift-badge--warn {
    background: rgba(245, 158, 11, 0.16);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  .drift-badge--ok {
    background: rgba(16, 185, 129, 0.16);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1rem;
    cursor: pointer;
  }

  .export-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px 16px;
    background: var(--rg-bg-elevated, #1e293b);
    border-bottom: 1px solid var(--rg-border-grid, #334155);
  }

  .tab-group {
    display: flex;
    gap: 6px;
  }

  .tab-btn {
    padding: 5px 10px;
    background: transparent;
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 5px;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.76rem;
    cursor: pointer;
  }

  .tab-btn--active {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.12);
  }

  .export-options {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.75rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .opt-label {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
  }

  .btn-tool {
    padding: 4px 10px;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 5px;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.75rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 14px 16px;
    overflow-y: auto;
    max-height: 56vh;
  }

  .code-viewer,
  .diff-viewer {
    margin: 0;
    padding: 12px;
    background: #090d16;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    font-size: 0.78rem;
    line-height: 1.45;
    overflow-x: auto;
    color: #e2e8f0;
  }

  .diff-line {
    white-space: pre;
    padding: 1px 6px;
  }

  .diff-line--add {
    background: rgba(16, 185, 129, 0.16);
    color: #6ee7b7;
  }

  .diff-line--del {
    background: rgba(239, 68, 68, 0.16);
    color: #fca5a5;
  }

  .diff-line--meta {
    color: #22d3ee;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    padding: 10px 16px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-secondary {
    padding: 6px 14px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    cursor: pointer;
    font-size: 0.8rem;
  }
</style>
