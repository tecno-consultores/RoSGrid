<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch, onBeforeUnmount } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { RouterItem, VaultSecretData } from '@/types';

  const props = defineProps<{
    isOpen: boolean;
    router: RouterItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'rotated', routerId: string): void;
    (e: 'repinned', routerId: string): void;
  }>();

  const authStore = useAuthStore();

  const isRoleAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });

  const isUnlocked = ref(false);
  const isLoading = ref(false);
  const isOperating = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');

  // Formulario Step-Up
  const consultationReason = ref('');
  const totpCode = ref('');

  // Datos de la bóveda
  const vaultData = ref<VaultSecretData | null>(null);

  const remainingSeconds = ref(30);
  const isCopied = ref(false);
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  function purgeSecretMemory() {
    // Autodestrucción en memoria RAM
    if (vaultData.value) {
      vaultData.value.current_password = '';
      vaultData.value.previous_password = '';
    }
    isUnlocked.value = false;
    totpCode.value = '';
    consultationReason.value = '';
    stopCountdown();
  }

  function startPurgeTimer(seconds = 30) {
    stopCountdown();
    remainingSeconds.value = seconds;
    countdownTimer = setInterval(() => {
      if (remainingSeconds.value > 0) {
        remainingSeconds.value--;
      } else {
        purgeSecretMemory();
        successMessage.value =
          'El secreto fue purgado automáticamente de la memoria RAM (30s cumplidos).';
      }
    }, 1000);
  }

  function stopCountdown() {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }

  async function handleRevealSubmit() {
    if (!props.router) return;
    if (!consultationReason.value.trim() || totpCode.value.length !== 6) {
      errorMessage.value = 'El motivo y el código TOTP de 6 dígitos son obligatorios.';
      return;
    }

    isLoading.value = true;
    errorMessage.value = '';

    try {
      const res = await http.post<VaultSecretData>(
        `/api/v1/inventory/routers/${props.router.id}/vault/reveal`,
        {
          reason: consultationReason.value.trim(),
          totp_code: totpCode.value,
        },
      );

      vaultData.value = res.data;
      isUnlocked.value = true;
      startPurgeTimer(vaultData.value?.auto_purge_seconds || 30);
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      errorMessage.value =
        e.detail || e.message || 'Código 2FA incorrecto o error al consultar la bóveda.';
      isUnlocked.value = false;
      vaultData.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  async function copyToClipboard(text?: string) {
    if (!text || typeof navigator === 'undefined') return;
    try {
      await navigator.clipboard.writeText(text);
      isCopied.value = true;
      setTimeout(() => {
        isCopied.value = false;
      }, 2500);
    } catch {
      // Fallback
    }
  }

  async function handleRotateApiKey() {
    if (!props.router) return;
    if (
      !confirm(
        '¿Deseas rotar inmediatamente la clave API de este router en MikroTik y actualizar la Bóveda?',
      )
    ) {
      return;
    }

    isOperating.value = true;
    errorMessage.value = '';
    try {
      await http.post(`/api/v1/vault/routers/${props.router.id}/rotate`);
      successMessage.value = 'Rotación de clave API ejecutada exitosamente.';
      emit('rotated', props.router.id);
      purgeSecretMemory();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al rotar la clave de la API.';
    } finally {
      isOperating.value = false;
    }
  }

  async function handleRepinSsl() {
    if (!props.router) return;
    if (!confirm('¿Confirmas el Re-Pinning del certificado SSL TOFU de este router?')) {
      return;
    }

    isOperating.value = true;
    errorMessage.value = '';
    try {
      await http.post(`/api/v1/vault/routers/${props.router.id}/repin-ssl`);
      successMessage.value = 'Certificado SSL re-anclado (Pinned) correctamente.';
      emit('repinned', props.router.id);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al re-anclar certificado SSL.';
    } finally {
      isOperating.value = false;
    }
  }

  function handleCloseModal() {
    purgeSecretMemory();
    emit('close');
  }

  watch(
    () => props.isOpen,
    (open) => {
      if (!open) {
        purgeSecretMemory();
      } else {
        errorMessage.value = '';
        successMessage.value = '';
      }
    },
  );

  onBeforeUnmount(() => {
    purgeSecretMemory();
  });
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="handleCloseModal">
    <div class="rg-vault-modal" role="dialog" aria-modal="true" aria-labelledby="vault-modal-title">
      <header class="modal-header">
        <div>
          <h2 id="vault-modal-title" class="modal-title">
            🔐 Bóveda Criptográfica MikroTik (Step-Up 2FA)
          </h2>
          <p v-if="router" class="modal-subtitle">
            Router: <strong>{{ router.display_name }}</strong> ({{ router.ip_address }})
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de bóveda"
          @click="handleCloseModal"
        >
          ✕
        </button>
      </header>

      <div class="modal-body">
        <!-- Control de rol RBAC estricto -->
        <div v-if="!isRoleAuthorized" class="banner banner--error" role="alert">
          ⛔ Acceso denegado: Solo los roles <strong>SUPERADMIN_GLOBAL</strong> y
          <strong>TENANT_ADMIN</strong> tienen autorización para consultar la Bóveda de
          credenciales.
        </div>

        <div v-else>
          <div v-if="errorMessage" class="banner banner--error" role="alert">
            {{ errorMessage }}
          </div>
          <div v-if="successMessage" class="banner banner--success" role="status">
            {{ successMessage }}
          </div>

          <!-- Información estática de rotación -->
          <div class="vault-meta-grid">
            <div class="meta-item">
              <span class="meta-label">Usuario API MikroTik:</span>
              <strong class="meta-value">{{ vaultData?.api_username || 'rosgrid_svc' }}</strong>
            </div>
            <div class="meta-item">
              <span class="meta-label">Estado de Contraseña:</span>
              <span class="meta-value">••••••••••••••••••••••••</span>
            </div>
          </div>

          <!-- ESTADO 1: Formulario Step-Up 2FA (Bloqueado) -->
          <div v-if="!isUnlocked" class="stepup-box">
            <h3 class="stepup-title">Desafío Step-Up Requerido</h3>
            <p class="stepup-desc">
              Para revelar las claves de acceso de este equipo debes justificar la acción e
              introducir tu código 2FA TOTP actual.
            </p>

            <form class="stepup-form" @submit.prevent="handleRevealSubmit">
              <div class="form-group">
                <label for="consult-reason" class="form-label">
                  Motivo de Consulta (Auditoría Forense WORM) *
                </label>
                <input
                  id="consult-reason"
                  v-model="consultationReason"
                  type="text"
                  required
                  placeholder="ej. Mantenimiento urgente o cambio de infraestructura"
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label for="vault-totp" class="form-label"> Código 2FA TOTP (6 dígitos) * </label>
                <input
                  id="vault-totp"
                  v-model="totpCode"
                  type="text"
                  inputmode="numeric"
                  pattern="[0-9]{6}"
                  maxlength="6"
                  required
                  placeholder="000000"
                  class="form-input form-input--totp"
                />
              </div>

              <div class="form-actions">
                <button
                  type="submit"
                  class="btn-reveal"
                  :disabled="isLoading || totpCode.length !== 6 || !consultationReason.trim()"
                >
                  {{ isLoading ? 'Verificando...' : '🔓 Revelar Credenciales (30s)' }}
                </button>
              </div>
            </form>
          </div>

          <!-- ESTADO 2: Revelación Temporal con Autodestrucción en 30s -->
          <div v-else class="revealed-box">
            <div class="purge-timer-banner">
              <span>⚠️ Autodestrucción de memoria RAM en:</span>
              <strong class="timer-seconds">{{ remainingSeconds }}s</strong>
            </div>

            <div class="secret-field">
              <label class="form-label">Contraseña API Actual:</label>
              <div class="secret-input-row">
                <code class="secret-text">{{ vaultData?.current_password }}</code>
                <button
                  type="button"
                  class="btn-copy"
                  aria-label="Copiar contraseña al portapapeles"
                  @click="copyToClipboard(vaultData?.current_password)"
                >
                  {{ isCopied ? '✓ Copiado' : 'Copiar' }}
                </button>
              </div>
            </div>

            <div v-if="vaultData?.previous_password" class="secret-field">
              <label class="form-label">Contraseña API Anterior (Histórica):</label>
              <div class="secret-input-row">
                <code class="secret-text secret-text--prev">{{
                  vaultData?.previous_password
                }}</code>
              </div>
            </div>
          </div>

          <!-- Acciones Operativas de Bóveda -->
          <div class="vault-operations">
            <h4 class="ops-title">Operaciones Criptográficas en Caliente</h4>
            <div class="ops-buttons">
              <button
                type="button"
                class="btn-op btn-op--rotate"
                :disabled="isOperating"
                @click="handleRotateApiKey"
              >
                🔄 Rotar Clave API Ahora
              </button>
              <button
                type="button"
                class="btn-op btn-op--repin"
                :disabled="isOperating"
                @click="handleRepinSsl"
              >
                📌 Re-Pin SSL TOFU
              </button>
            </div>
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn-close-modal" @click="handleCloseModal">
          Cerrar Bóveda
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 16px;
  }

  .rg-vault-modal {
    width: 100%;
    max-width: 600px;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.7);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  }

  .modal-title {
    font-size: 1.15rem;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .modal-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 4px 0 0 0;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.2rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .vault-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    padding: 12px;
    border-radius: 6px;
    border: 1px solid var(--rg-border-grid, #1e293b);
  }

  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .meta-label {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .meta-value {
    font-size: 0.85rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .stepup-box {
    background: rgba(30, 41, 59, 0.5);
    border: 1px dashed var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 16px;
  }

  .stepup-title {
    font-size: 0.95rem;
    color: #fbbf24;
    margin: 0 0 6px 0;
  }

  .stepup-desc {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0 0 14px 0;
  }

  .stepup-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .form-input {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .form-input--totp {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 1.2rem;
    letter-spacing: 0.25em;
    text-align: center;
  }

  .btn-reveal {
    background: #fbbf24;
    color: #0b0f19;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.9rem;
    width: 100%;
  }

  .btn-reveal:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .revealed-box {
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid #10b981;
    border-radius: 6px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .purge-timer-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid #ef4444;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #fca5a5;
  }

  .timer-seconds {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 1.1rem;
    color: #ffffff;
  }

  .secret-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .secret-input-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111827;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 8px 12px;
  }

  .secret-text {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.95rem;
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .secret-text--prev {
    color: var(--rg-text-muted, #94a3b8);
  }

  .btn-copy {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
  }

  .vault-operations {
    border-top: 1px solid var(--rg-border-grid, #1e293b);
    padding-top: 12px;
  }

  .ops-title {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 0 0 8px 0;
  }

  .ops-buttons {
    display: flex;
    gap: 10px;
  }

  .btn-op {
    flex: 1;
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .btn-op--rotate:hover {
    border-color: #fbbf24;
    color: #fbbf24;
  }

  .btn-op--repin:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    padding: 14px 20px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-close-modal {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }

  @media (max-width: 640px) {
    .vault-meta-grid {
      grid-template-columns: 1fr;
    }

    .ops-buttons {
      flex-direction: column;
    }
  }
</style>
