<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch, computed } from 'vue';
  import type { Layer2RpcActionDescriptor } from '@/types';

  const props = withDefaults(
    defineProps<{
      isOpen: boolean;
      descriptor: Layer2RpcActionDescriptor | null;
      targetRow?: Record<string, unknown> | null;
      isSubmitting?: boolean;
    }>(),
    {
      targetRow: null,
      isSubmitting: false,
    },
  );

  const emit = defineEmits<{
    (e: 'close'): void;
    (
      e: 'submit',
      payload: {
        action: string;
        params: Record<string, unknown>;
        target_id?: string | null;
        requires_safe_mode: boolean;
      },
    ): void;
  }>();

  const formValues = ref<Record<string, unknown>>({});

  const targetRowId = computed<string | null>(() => {
    if (!props.targetRow) return null;
    const raw = props.targetRow['.id'] ?? props.targetRow.id ?? null;
    return raw ? String(raw) : null;
  });

  const targetRowLabel = computed<string>(() => {
    if (!props.targetRow) return '';
    return String(
      props.targetRow.name ??
        props.targetRow['common-name'] ??
        props.targetRow.address ??
        props.targetRow['.id'] ??
        props.targetRow.id ??
        '',
    );
  });

  function initForm(): void {
    const next: Record<string, unknown> = {};
    if (!props.descriptor) {
      formValues.value = next;
      return;
    }
    for (const param of props.descriptor.params_schema) {
      if (param.default !== undefined && param.default !== null) {
        next[param.key] = param.default;
      } else if (param.type === 'boolean_ros') {
        next[param.key] = false;
      } else {
        next[param.key] = '';
      }
    }
    if (props.targetRow) {
      const rowName = props.targetRow.name ?? props.targetRow['.id'] ?? props.targetRow.id;
      if (rowName && 'certificate' in next && !next.certificate) {
        next.certificate = String(rowName);
      }
      if (targetRowId.value && 'numbers' in next && !next.numbers) {
        next.numbers = targetRowId.value;
      }
    }
    formValues.value = next;
  }

  watch(
    () => [props.isOpen, props.descriptor, props.targetRow],
    () => {
      if (props.isOpen) {
        initForm();
      }
    },
    { immediate: true },
  );

  function handleSubmit(): void {
    if (!props.descriptor) return;
    const cleanedParams = Object.fromEntries(
      Object.entries(formValues.value).filter(
        ([, v]) => v !== '' && v !== undefined && v !== null,
      ),
    );
    emit('submit', {
      action: props.descriptor.action,
      params: cleanedParams,
      target_id: targetRowId.value,
      requires_safe_mode: props.descriptor.requires_safe_mode,
    });
  }
</script>

<template>
  <div
    v-if="isOpen && descriptor"
    id="layer2-rpc-modal"
    class="rg-modal-backdrop"
    @click.self="emit('close')"
  >
    <div class="rg-modal" role="dialog" aria-modal="true" :aria-label="descriptor.label">
      <header class="modal-header">
        <div class="modal-header__titles">
          <h3 class="modal-title">{{ descriptor.icon }} {{ descriptor.label }}</h3>
          <span v-if="targetRowLabel" class="target-chip">
            Objetivo: <code>{{ targetRowLabel }}</code>
          </span>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal RPC"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <form class="modal-body" @submit.prevent="handleSubmit">
        <div class="rpc-meta-banner">
          <span class="meta-verb">POST /rest/.../{{ descriptor.action }}</span>
          <span v-if="descriptor.requires_safe_mode" class="badge-safemode">
            🛡️ Safe Mode (60s)
          </span>
          <span v-if="descriptor.requires_confirmation" class="badge-confirm">
            ⚠️ Requiere confirmación
          </span>
        </div>

        <p v-if="descriptor.params_schema.length === 0" class="empty-params-hint">
          Esta acción RPC se ejecutará directamente sobre el registro seleccionado sin parámetros
          adicionales.
        </p>

        <div v-else class="rpc-fields-list">
          <div v-for="param in descriptor.params_schema" :key="param.key" class="form-field">
            <label :for="`rpc-param-${param.key}`" class="field-label">
              {{ param.label }}
              <span v-if="param.required" class="req-star" aria-hidden="true">*</span>
            </label>

            <select
              v-if="param.type === 'enum' && param.options?.length"
              :id="`rpc-param-${param.key}`"
              v-model="formValues[param.key]"
              :required="param.required"
              class="field-input"
            >
              <option v-for="opt in param.options" :key="opt" :value="opt">
                {{ opt }}
              </option>
            </select>

            <input
              v-else-if="param.type === 'boolean_ros'"
              :id="`rpc-param-${param.key}`"
              v-model="formValues[param.key]"
              type="checkbox"
              class="field-checkbox"
            />

            <input
              v-else
              :id="`rpc-param-${param.key}`"
              v-model="formValues[param.key]"
              :type="param.type === 'integer' ? 'number' : 'text'"
              :required="param.required"
              class="field-input"
            />

            <small v-if="param.description" class="field-hint">{{ param.description }}</small>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-secondary" @click="emit('close')">Cancelar</button>
          <button
            id="btn-confirm-rpc-action"
            type="submit"
            class="btn-primary"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '⏳ Ejecutando...' : `⚡ Ejecutar ${descriptor.action}` }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
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
    max-width: 540px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 14px 32px rgba(0, 0, 0, 0.65);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  }

  .modal-header__titles {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .modal-title {
    margin: 0;
    font-size: 0.95rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .target-chip {
    font-size: 0.75rem;
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .rpc-meta-banner {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 6px 10px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    font-size: 0.74rem;
  }

  .meta-verb {
    font-family: var(--rg-font-mono, monospace);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .badge-safemode {
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
  }

  .badge-confirm {
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
  }

  .empty-params-hint {
    margin: 0;
    font-size: 0.82rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .rpc-fields-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .field-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .req-star {
    color: #f87171;
  }

  .field-input {
    padding: 6px 10px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.84rem;
  }

  .field-hint {
    font-size: 0.72rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding-top: 10px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-secondary {
    padding: 6px 12px;
    background: var(--rg-bg-elevated, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    cursor: pointer;
    font-size: 0.8rem;
  }

  .btn-primary {
    padding: 6px 14px;
    background: var(--rg-accent-cyan, #22d3ee);
    border: none;
    border-radius: 6px;
    color: #0b0f19;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.8rem;
  }
</style>
