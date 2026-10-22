<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch, computed } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';

  const props = defineProps<{
    isOpen: boolean;
    targetUser?: { id: string; username: string } | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'password-changed'): void;
  }>();

  const authStore = useAuthStore();

  const currentPassword = ref('');
  const newPassword = ref('');
  const confirmPassword = ref('');
  const showPasswords = ref(false);
  const isSubmitting = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');

  const isSelfChange = computed(() => {
    if (!props.targetUser) return true;
    return props.targetUser.id === authStore.user?.id;
  });

  const modalTitle = computed(() => {
    if (!isSelfChange.value && props.targetUser) {
      return `Cambiar Contraseña: @${props.targetUser.username}`;
    }
    return 'Cambiar Mi Contraseña';
  });

  function resetState() {
    currentPassword.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    showPasswords.value = false;
    isSubmitting.value = false;
    errorMessage.value = '';
    successMessage.value = '';
  }

  watch(
    () => props.isOpen,
    (val) => {
      if (val) {
        resetState();
      }
    },
  );

  async function handleSubmit() {
    errorMessage.value = '';
    successMessage.value = '';

    if (isSelfChange.value && !currentPassword.value) {
      errorMessage.value = 'Debes ingresar tu contraseña actual.';
      return;
    }

    if (!newPassword.value || newPassword.value.length < 8) {
      errorMessage.value = 'La nueva contraseña debe tener al menos 8 caracteres.';
      return;
    }

    if (newPassword.value !== confirmPassword.value) {
      errorMessage.value = 'La nueva contraseña y su confirmación no coinciden.';
      return;
    }

    isSubmitting.value = true;
    try {
      const payload: {
        user_id?: string;
        current_password?: string;
        new_password: string;
      } = {
        new_password: newPassword.value,
      };

      if (props.targetUser && !isSelfChange.value) {
        payload.user_id = props.targetUser.id;
      }

      if (isSelfChange.value) {
        payload.current_password = currentPassword.value;
      }

      await http.post('/api/v1/users/change-password', payload);

      successMessage.value = 'Contraseña actualizada exitosamente.';
      setTimeout(() => {
        emit('password-changed');
        emit('close');
      }, 1200);
    } catch (err: unknown) {
      const error = err as {
        detail?: string;
        message?: string;
        data?: { detail?: string };
      };
      errorMessage.value =
        error.data?.detail || error.detail || error.message || 'Error al actualizar la contraseña.';
    } finally {
      isSubmitting.value = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && props.isOpen) {
      emit('close');
    }
  }
</script>

<template>
  <div
    v-if="isOpen"
    class="rg-modal-backdrop"
    role="presentation"
    @click.self="emit('close')"
    @keydown="handleKeydown"
  >
    <div
      class="rg-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-pass-title"
    >
      <header class="modal-header">
        <h2 id="change-pass-title" class="modal-title">
          <span class="modal-icon" aria-hidden="true">🔑</span>
          {{ modalTitle }}
        </h2>
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
        <div v-if="errorMessage" class="alert-banner alert-banner--error" role="alert">
          <span>⚠️ {{ errorMessage }}</span>
        </div>
        <div v-if="successMessage" class="alert-banner alert-banner--success" role="status">
          <span>✓ {{ successMessage }}</span>
        </div>

        <!-- Campo Contraseña Actual (solo para auto-cambio) -->
        <div v-if="isSelfChange" class="form-group">
          <label for="cp-current" class="form-label">Contraseña Actual *</label>
          <input
            id="cp-current"
            v-model="currentPassword"
            :type="showPasswords ? 'text' : 'password'"
            class="form-input"
            required
            autocomplete="current-password"
            placeholder="Ingresa tu contraseña actual"
          />
        </div>

        <!-- Campo Nueva Contraseña -->
        <div class="form-group">
          <label for="cp-new" class="form-label">Nueva Contraseña (mínimo 8 caracteres) *</label>
          <input
            id="cp-new"
            v-model="newPassword"
            :type="showPasswords ? 'text' : 'password'"
            class="form-input"
            required
            minlength="8"
            autocomplete="new-password"
            placeholder="••••••••••••"
          />
        </div>

        <!-- Confirmación de Nueva Contraseña -->
        <div class="form-group">
          <label for="cp-confirm" class="form-label">Confirmar Nueva Contraseña *</label>
          <input
            id="cp-confirm"
            v-model="confirmPassword"
            :type="showPasswords ? 'text' : 'password'"
            class="form-input"
            required
            minlength="8"
            autocomplete="new-password"
            placeholder="••••••••••••"
          />
        </div>

        <!-- Toggle Mostrar Contraseñas -->
        <div class="form-check">
          <label class="check-label">
            <input
              type="checkbox"
              v-model="showPasswords"
              class="form-checkbox"
            />
            <span>Mostrar contraseñas en texto claro</span>
          </label>
        </div>

        <footer class="modal-footer">
          <button
            type="button"
            class="btn-cancel"
            :disabled="isSubmitting"
            @click="emit('close')"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="btn-submit"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Actualizando...' : 'Guardar Nueva Contraseña' }}
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
    background-color: rgba(5, 8, 16, 0.85);
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 16px;
  }

  .rg-modal {
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border, #1f293d);
    border-radius: 12px;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: rgba(0, 243, 255, 0.04);
    border-bottom: 1px solid var(--rg-border, #1f293d);
  }

  .modal-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f9fafb);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .modal-icon {
    font-size: 1.2rem;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #9ca3af);
    font-size: 1.2rem;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
    transition: color 0.15s, background-color 0.15s;
  }

  .btn-close:hover {
    color: #fff;
    background-color: rgba(255, 255, 255, 0.08);
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .alert-banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.88rem;
    line-height: 1.4;
  }

  .alert-banner--error {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #fca5a5;
  }

  .alert-banner--success {
    background-color: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #6ee7b7;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #d1d5db);
  }

  .form-input {
    background-color: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--rg-border, #1f293d);
    border-radius: 6px;
    padding: 10px 12px;
    color: #fff;
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .form-input:focus {
    border-color: var(--rg-primary, #00f3ff);
    box-shadow: 0 0 0 2px rgba(0, 243, 255, 0.2);
  }

  .form-check {
    display: flex;
    align-items: center;
  }

  .check-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.84rem;
    color: var(--rg-text-muted, #9ca3af);
    cursor: pointer;
    user-select: none;
  }

  .form-checkbox {
    accent-color: var(--rg-primary, #00f3ff);
    cursor: pointer;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 8px;
    padding-top: 14px;
    border-top: 1px solid var(--rg-border, #1f293d);
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border, #1f293d);
    color: var(--rg-text-muted, #9ca3af);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-cancel:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    color: #fff;
  }

  .btn-submit {
    background: var(--rg-primary, #00f3ff);
    color: #000;
    border: none;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
  }

  .btn-submit:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  .btn-submit:disabled,
  .btn-cancel:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
