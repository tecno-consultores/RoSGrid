<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import type { SimpleQueueItem } from '@/types';

  const props = defineProps<{
    isOpen: boolean;
    isEditing: boolean;
    initialQueue?: SimpleQueueItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'save', payload: Record<string, any>): void;
  }>();

  const name = ref('');
  const target = ref('');
  const maxLimit = ref('25M/50M');
  const limitAt = ref('');
  const burstLimit = ref('');
  const comment = ref('');
  const disabled = ref(false);
  const showAdvanced = ref(false);

  const presets = [
    { label: '10M / 10M', value: '10M/10M' },
    { label: '25M / 50M', value: '25M/50M' },
    { label: '50M / 100M', value: '50M/100M' },
    { label: '100M / 300M', value: '100M/300M' },
    { label: '200M / 600M', value: '200M/600M' },
    { label: '1 Gbps Simétrico', value: '1000M/1000M' },
  ];

  watch(
    () => props.isOpen,
    (open) => {
      if (open) {
        if (props.isEditing && props.initialQueue) {
          const q = props.initialQueue as any;
          name.value = q.name || '';
          target.value = q.target || '';
          maxLimit.value = q.max_limit || '25M/50M';
          limitAt.value = q.limit_at || '';
          burstLimit.value = q.burst_limit || '';
          comment.value = q.comment || '';
          disabled.value = Boolean(q.disabled);
          showAdvanced.value = Boolean(q.limit_at || q.burst_limit);
        } else {
          name.value = '';
          target.value = '';
          maxLimit.value = '25M/50M';
          limitAt.value = '';
          burstLimit.value = '';
          comment.value = '';
          disabled.value = false;
          showAdvanced.value = false;
        }
      }
    },
    { immediate: true },
  );

  function applyPreset(val: string) {
    maxLimit.value = val;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      emit('close');
    }
  }

  function handleSubmit() {
    const payload: Record<string, any> = {
      name: name.value.trim(),
      target: target.value.trim(),
      max_limit: maxLimit.value.trim(),
      disabled: disabled.value,
    };
    if (limitAt.value.trim()) payload.limit_at = limitAt.value.trim();
    if (burstLimit.value.trim()) payload.burst_limit = burstLimit.value.trim();
    if (comment.value.trim()) payload.comment = comment.value.trim();

    emit('save', payload);
  }
</script>

<template>
  <div
    v-if="isOpen"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="queue-modal-title"
    @keydown="handleKeydown"
  >
    <div class="modal-card" @click.stop>
      <header class="modal-header">
        <div>
          <h3 id="queue-modal-title" class="modal-title">
            {{ isEditing ? 'Editar Cola Simple (QoS)' : 'Nueva Cola Simple (Simple Queue)' }}
          </h3>
          <p class="modal-subtitle">
            Control de ancho de banda y priorización de tráfico MikroTik RouterOS v7
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <form class="modal-form" @submit.prevent="handleSubmit">
        <div class="form-grid">
          <!-- Nombre de la Cola -->
          <div class="form-group">
            <label for="queue-name" class="form-label">Nombre de la Cola *</label>
            <input
              id="queue-name"
              v-model="name"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: queue-abonado-204"
              required
            />
          </div>

          <!-- IP o Subred Target -->
          <div class="form-group">
            <label for="queue-target" class="form-label">Target (IP o Subred CIDR) *</label>
            <input
              id="queue-target"
              v-model="target"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: 192.168.88.25/32 o 10.10.10.0/24"
              required
            />
          </div>

          <!-- Límite Máximo (Upload/Download) -->
          <div class="form-group form-group--full">
            <label for="queue-max-limit" class="form-label">
              Límite Máximo (Upload / Download) *
            </label>
            <input
              id="queue-max-limit"
              v-model="maxLimit"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: 25M/50M"
              required
            />

            <!-- Presets Tácticos en 1 Clic -->
            <div class="presets-toolbar">
              <span class="presets-label">Presets Rápidos:</span>
              <div class="presets-buttons">
                <button
                  v-for="p in presets"
                  :key="p.value"
                  type="button"
                  class="btn-preset"
                  :class="{ 'btn-preset--active': maxLimit === p.value }"
                  @click="applyPreset(p.value)"
                >
                  {{ p.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Toggle Opciones Avanzadas -->
          <div class="form-group form-group--full">
            <button
              type="button"
              class="btn-toggle-advanced"
              @click="showAdvanced = !showAdvanced"
            >
              {{ showAdvanced ? '▲ Ocultar Opciones Avanzadas' : '▼ Mostrar Opciones Avanzadas (Burst / Garantía)' }}
            </button>
          </div>

          <!-- Campos Avanzados -->
          <template v-if="showAdvanced">
            <div class="form-group">
              <label for="queue-limit-at" class="form-label">Garantizado (Limit At Up/Down)</label>
              <input
                id="queue-limit-at"
                v-model="limitAt"
                type="text"
                class="form-input font-tabular"
                placeholder="Ej: 5M/10M"
              />
            </div>

            <div class="form-group">
              <label for="queue-burst" class="form-label">Ráfaga (Burst Limit Up/Down)</label>
              <input
                id="queue-burst"
                v-model="burstLimit"
                type="text"
                class="form-input font-tabular"
                placeholder="Ej: 35M/75M"
              />
            </div>
          </template>

          <!-- Comentario -->
          <div class="form-group form-group--full">
            <label for="queue-comment" class="form-label">Comentario</label>
            <input
              id="queue-comment"
              v-model="comment"
              type="text"
              class="form-input"
              placeholder="Ej: Plan Fibra 50 Mbps — Cliente Residencial"
            />
          </div>

          <!-- Switch Deshabilitada -->
          <div class="form-group form-group--full">
            <label class="checkbox-label">
              <input v-model="disabled" type="checkbox" class="form-checkbox" />
              <span>Deshabilitar cola temporalmente (disabled=yes)</span>
            </label>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" @click="emit('close')">
            Cancelar
          </button>
          <button type="submit" class="btn-submit">
            {{ isEditing ? 'Guardar Cambios' : 'Crear Cola Simple' }}
          </button>
        </footer>
      </form>
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
    background-color: rgba(5, 10, 20, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 16px;
    box-sizing: border-box;
  }

  .modal-card {
    background-color: var(--rg-bg-card, #0d1527);
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-lg, 12px);
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px 20px;
    border-bottom: 1px solid var(--rg-border, #1e293b);
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
  }

  .modal-subtitle {
    margin: 4px 0 0 0;
    font-size: 0.82rem;
    color: var(--rg-text-secondary, #94a3b8);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary, #94a3b8);
    font-size: 1.25rem;
    cursor: pointer;
    line-height: 1;
    padding: 4px;
  }

  .btn-close:hover {
    color: var(--rg-text-primary, #f8fafc);
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .form-group--full {
    grid-column: 1 / -1;
  }

  .form-label {
    display: block;
    margin-bottom: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #94a3b8);
  }

  .form-input {
    width: 100%;
    padding: 8px 12px;
    background-color: var(--rg-bg-input, #090e1a);
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-md, 8px);
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.9rem;
    box-sizing: border-box;
    transition: border-color 0.2s;
  }

  .form-input:focus {
    outline: none;
    border-color: var(--rg-accent-cyan, #00d2ff);
  }

  .font-tabular {
    font-family: monospace;
  }

  .presets-toolbar {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .presets-label {
    font-size: 0.78rem;
    color: var(--rg-text-secondary, #94a3b8);
  }

  .presets-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .btn-preset {
    padding: 4px 10px;
    font-size: 0.78rem;
    font-family: monospace;
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-sm, 4px);
    color: var(--rg-text-primary, #f8fafc);
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-preset:hover {
    border-color: var(--rg-accent-cyan, #00d2ff);
    color: var(--rg-accent-cyan, #00d2ff);
  }

  .btn-preset--active {
    background-color: rgba(0, 210, 255, 0.15);
    border-color: var(--rg-accent-cyan, #00d2ff);
    color: var(--rg-accent-cyan, #00d2ff);
    font-weight: 700;
  }

  .btn-toggle-advanced {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #00d2ff);
    font-size: 0.82rem;
    cursor: pointer;
    padding: 0;
    text-align: left;
  }

  .btn-toggle-advanced:hover {
    text-decoration: underline;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #94a3b8);
    cursor: pointer;
  }

  .form-checkbox {
    width: 16px;
    height: 16px;
    accent-color: var(--rg-accent-cyan, #00d2ff);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--rg-border, #1e293b);
  }

  .btn-cancel {
    padding: 8px 16px;
    background-color: transparent;
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-md, 8px);
    color: var(--rg-text-secondary, #94a3b8);
    font-weight: 600;
    cursor: pointer;
  }

  .btn-cancel:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }

  .btn-submit {
    padding: 8px 20px;
    background: linear-gradient(135deg, #00d2ff, #0077b6);
    border: none;
    border-radius: var(--rg-radius-md, 8px);
    color: #ffffff;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 210, 255, 0.3);
  }

  .btn-submit:hover {
    filter: brightness(1.1);
  }

  @media (max-width: 600px) {
    .form-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
