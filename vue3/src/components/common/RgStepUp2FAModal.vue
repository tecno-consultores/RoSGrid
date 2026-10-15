<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, nextTick, onUnmounted, ref, watch } from 'vue';

  const props = withDefaults(
    defineProps<{
      isOpen: boolean;
      title?: string;
      description?: string;
      revealedSecret?: string | null;
      autoPurgeSeconds?: number;
    }>(),
    {
      title: 'Autenticación Step-Up Requerida',
      description: 'Ingresa tu código 2FA TOTP de 6 dígitos para autorizar esta acción sensible.',
      revealedSecret: null,
      autoPurgeSeconds: 30,
    },
  );

  const emit = defineEmits<{
    (e: 'submit-totp', code: string): void;
    (e: 'close'): void;
    (e: 'secret-purged'): void;
  }>();

  const totpCode = ref<string>('');
  const inputRef = ref<HTMLInputElement | null>(null);
  const remainingSeconds = ref<number>(props.autoPurgeSeconds);
  const isCopied = ref<boolean>(false);
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  const progressPct = computed(() => {
    return (remainingSeconds.value / props.autoPurgeSeconds) * 100;
  });

  watch(
    () => props.isOpen,
    (open) => {
      if (open) {
        totpCode.value = '';
        isCopied.value = false;
        nextTick(() => {
          inputRef.value?.focus();
        });
      } else {
        stopCountdown();
      }
    },
  );

  watch(
    () => props.revealedSecret,
    (secret) => {
      if (secret) {
        startPurgeCountdown();
      }
    },
    { immediate: true },
  );

  function startPurgeCountdown(): void {
    stopCountdown();
    remainingSeconds.value = props.autoPurgeSeconds;

    countdownTimer = setInterval(() => {
      if (remainingSeconds.value > 1) {
        remainingSeconds.value -= 1;
      } else {
        stopCountdown();
        emit('secret-purged');
        emit('close');
      }
    }, 1000);
  }

  function stopCountdown(): void {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }

  function handleSubmit(): void {
    const cleanCode = totpCode.value.trim();
    if (cleanCode.length === 6) {
      emit('submit-totp', cleanCode);
    }
  }

  async function handleCopy(): Promise<void> {
    if (props.revealedSecret && typeof navigator !== 'undefined' && navigator.clipboard) {
      await navigator.clipboard.writeText(props.revealedSecret);
      isCopied.value = true;
      setTimeout(() => {
        isCopied.value = false;
      }, 2000);
    }
  }

  onUnmounted(() => {
    stopCountdown();
  });
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="emit('close')">
    <div class="rg-stepup-modal" role="dialog" aria-modal="true" aria-labelledby="stepup-title">
      <header class="modal-header">
        <h2 id="stepup-title" class="modal-title">{{ title }}</h2>
        <button type="button" class="btn-close" aria-label="Cerrar modal" @click="emit('close')">
          ✕
        </button>
      </header>

      <div class="modal-body">
        <p class="modal-desc">{{ description }}</p>

        <!-- Etapa 1: Ingreso de código TOTP -->
        <form v-if="!revealedSecret" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="totp-input" class="form-label">Código 2FA TOTP (6 dígitos):</label>
            <input
              id="totp-input"
              ref="inputRef"
              v-model="totpCode"
              type="text"
              inputmode="numeric"
              pattern="[0-9]{6}"
              maxlength="6"
              placeholder="123456"
              class="totp-input"
              required
            />
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-submit" :disabled="totpCode.trim().length !== 6">
              Verificar y Autorizar
            </button>
          </div>
        </form>

        <!-- Etapa 2: Secreto Revelado con Barra de Autodestrucción en 30s -->
        <div v-else class="revealed-container">
          <div class="secret-box">
            <code class="secret-val">{{ revealedSecret }}</code>
            <button
              type="button"
              class="btn-copy"
              aria-label="Copiar credencial al portapapeles"
              @click="handleCopy"
            >
              {{ isCopied ? '✓ Copiado' : 'Copiar' }}
            </button>
          </div>

          <div class="purge-timer-box">
            <div class="timer-label">
              <span>Autodestrucción de memoria en:</span>
              <strong>{{ remainingSeconds }}s</strong>
            </div>
            <div
              class="progress-bar-track"
              role="progressbar"
              :aria-valuenow="remainingSeconds"
              :aria-valuemax="autoPurgeSeconds"
              aria-valuemin="0"
            >
              <div class="progress-bar-fill" :style="{ width: `${progressPct}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.8);
    backdrop-filter: blur(4px);
    z-index: 11000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }

  .rg-stepup-modal {
    width: 100%;
    max-width: 480px;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    border-radius: 8px;
    box-shadow:
      0 16px 32px rgba(0, 0, 0, 0.6),
      var(--rg-cyan-glow);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    background: var(--rg-bg-elevated);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .modal-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--rg-text-primary);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 16px;
    cursor: pointer;
  }

  .modal-body {
    padding: 20px 16px;
  }

  .modal-desc {
    font-size: 13px;
    color: var(--rg-text-secondary);
    margin-bottom: 16px;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .form-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 6px;
    color: var(--rg-text-secondary);
  }

  .totp-input {
    width: 100%;
    padding: 10px 14px;
    font-size: 20px;
    text-align: center;
    letter-spacing: 6px;
    font-family: var(--rg-font-mono);
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-accent-cyan);
    border-radius: 6px;
    outline: none;
  }

  .totp-input:focus {
    border-color: var(--rg-accent-cyan);
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
  }

  .btn-submit {
    background: var(--rg-accent-cyan-dark);
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .btn-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .revealed-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .secret-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-panel);
    padding: 10px 14px;
    border-radius: 6px;
  }

  .secret-val {
    font-family: var(--rg-font-mono);
    font-size: 15px;
    color: var(--rg-status-online-text);
    word-break: break-all;
  }

  .btn-copy {
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-accent-cyan);
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
  }

  .purge-timer-box {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .timer-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--rg-text-muted);
  }

  .progress-bar-track {
    width: 100%;
    height: 6px;
    background: var(--rg-bg-elevated);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: var(--rg-status-warning);
    transition: width 1s linear;
  }
</style>
