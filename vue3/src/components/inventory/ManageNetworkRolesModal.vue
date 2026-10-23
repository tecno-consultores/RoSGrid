<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { useInventoryStore } from '@/stores/useInventoryStore';

  defineProps<{
    isOpen: boolean;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
  }>();

  const inventoryStore = useInventoryStore();

  const newRoleName = ref('');
  const newRoleDesc = ref('');
  const isSubmitting = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');

  const standardRoles = [
    'CORE',
    'EDGE_BGP',
    'WAN_BALANCER',
    'BRAS_PPPOE',
    'DISTRIBUTION_SWITCH',
    'TOWER_AP',
    'CORPORATE_CPE',
  ];

  const customRoleNames = computed(() => {
    return inventoryStore.customRoles.map((r) => r.role_name);
  });

  function formatRoleInput(val: string) {
    newRoleName.value = val
      .toUpperCase()
      .replace(/\s+/g, '_')
      .replace(/[^A-Z0-9_-]/g, '');
  }

  async function handleCreateRole() {
    errorMessage.value = '';
    successMessage.value = '';
    const cleanName = newRoleName.value.trim().toUpperCase();

    if (!cleanName) {
      errorMessage.value = 'El nombre del rol es obligatorio.';
      return;
    }
    if (cleanName.length < 2 || cleanName.length > 64) {
      errorMessage.value = 'El nombre del rol debe tener entre 2 y 64 caracteres.';
      return;
    }
    if (standardRoles.includes(cleanName) || customRoleNames.value.includes(cleanName)) {
      errorMessage.value = `El rol "${cleanName}" ya existe en el sistema.`;
      return;
    }

    try {
      isSubmitting.value = true;
      await inventoryStore.createCustomRole(cleanName, newRoleDesc.value.trim());
      successMessage.value = `Rol "${cleanName}" creado exitosamente.`;
      newRoleName.value = '';
      newRoleDesc.value = '';
    } catch (err: any) {
      errorMessage.value = err.response?.data?.detail || 'Error al guardar el rol de red.';
    } finally {
      isSubmitting.value = false;
    }
  }

  async function handleDeleteRole(roleName: string) {
    if (!confirm(`¿Estás seguro de eliminar el rol personalizado "${roleName}"?`)) {
      return;
    }

    errorMessage.value = '';
    successMessage.value = '';

    try {
      isSubmitting.value = true;
      await inventoryStore.deleteCustomRole(roleName);
      successMessage.value = `Rol "${roleName}" eliminado correctamente.`;
    } catch (err: any) {
      errorMessage.value = err.response?.data?.detail || 'Error al eliminar el rol.';
    } finally {
      isSubmitting.value = false;
    }
  }

  function handleClose() {
    errorMessage.value = '';
    successMessage.value = '';
    newRoleName.value = '';
    newRoleDesc.value = '';
    emit('close');
  }
</script>

<template>
  <div
    v-if="isOpen"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="manage-roles-title"
    @click.self="handleClose"
  >
    <div class="modal-card">
      <div class="modal-header">
        <h2 id="manage-roles-title" class="modal-title">
          <span class="icon" aria-hidden="true">🏷️</span>
          Personalización de Roles de Red
        </h2>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar ventana de roles"
          @click="handleClose"
        >
          ✕
        </button>
      </div>

      <div class="modal-body">
        <p class="modal-description">
          Define y administra los roles de red disponibles para clasificar los routers MikroTik de
          tu organización. Los roles estándar son globales; los roles personalizados aplican a tu
          empresa.
        </p>

        <!-- Feedback de operaciones -->
        <div v-if="errorMessage" class="alert alert--error" role="alert">
          <span class="alert-icon" aria-hidden="true">⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>

        <div v-if="successMessage" class="alert alert--success" role="status">
          <span class="alert-icon" aria-hidden="true">✅</span>
          <span>{{ successMessage }}</span>
        </div>

        <!-- Formulario para agregar nuevo rol -->
        <form class="role-form" @submit.prevent="handleCreateRole">
          <div class="form-row">
            <div class="form-group flex-2">
              <label for="new-role-input" class="form-label">
                Nuevo Rol de Red: <span class="required">*</span>
              </label>
              <input
                id="new-role-input"
                v-model="newRoleName"
                type="text"
                class="form-control"
                placeholder="Ej. IOT_GATEWAY, BACKHAUL_RADIO"
                maxlength="64"
                :disabled="isSubmitting"
                @input="formatRoleInput(($event.target as HTMLInputElement).value)"
              />
            </div>

            <div class="form-group flex-3">
              <label for="new-role-desc" class="form-label">Descripción Opcional:</label>
              <input
                id="new-role-desc"
                v-model="newRoleDesc"
                type="text"
                class="form-control"
                placeholder="Ej. Enlaces de radio troncales MikroTik"
                maxlength="255"
                :disabled="isSubmitting"
              />
            </div>

            <div class="form-group flex-btn">
              <label class="form-label form-label-spacer" aria-hidden="true">&nbsp;</label>
              <button
                type="submit"
                class="btn-primary"
                :disabled="isSubmitting || !newRoleName.trim()"
              >
                {{ isSubmitting ? 'Guardando...' : '+ Crear Rol' }}
              </button>
            </div>
          </div>
          <span class="help-text">Se normaliza automáticamente en MAYÚSCULAS_CON_GUIONES</span>
        </form>

        <!-- Listado de roles actuales -->
        <div class="roles-section">
          <h3 class="section-title">
            Roles de Red Disponibles ({{ inventoryStore.networkRoles.length }})
          </h3>

          <div class="roles-grid">
            <div
              v-for="role in inventoryStore.networkRoles"
              :key="role"
              class="role-card"
              :class="{ 'role-card--custom': customRoleNames.includes(role) }"
            >
              <div class="role-card-header">
                <span class="role-name">{{ role }}</span>
                <span
                  class="role-badge"
                  :class="customRoleNames.includes(role) ? 'badge-custom' : 'badge-standard'"
                >
                  {{ customRoleNames.includes(role) ? 'Personalizado' : 'Estándar' }}
                </span>
              </div>

              <div class="role-card-footer">
                <span v-if="customRoleNames.includes(role)" class="role-desc-text">
                  {{
                    inventoryStore.customRoles.find((c) => c.role_name === role)?.description ||
                    'Rol de empresa'
                  }}
                </span>
                <span v-else class="role-desc-text system-desc"> Rol de arquitectura base </span>

                <button
                  v-if="customRoleNames.includes(role)"
                  type="button"
                  class="btn-delete-role"
                  title="Eliminar este rol personalizado"
                  :disabled="isSubmitting"
                  @click="handleDeleteRole(role)"
                >
                  🗑️ Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="handleClose">Cerrar</button>
      </div>
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
    background-color: rgba(2, 6, 23, 0.78);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1200;
    padding: 1rem;
  }

  .modal-card {
    background: #0f172a;
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 8px;
    width: 100%;
    max-width: 720px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow:
      0 16px 40px rgba(0, 0, 0, 0.6),
      0 0 20px rgba(0, 240, 255, 0.15);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    background: rgba(15, 23, 42, 0.95);
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #00f0ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: monospace;
    letter-spacing: 0.5px;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.25rem;
    cursor: pointer;
    line-height: 1;
    padding: 0.25rem;
    border-radius: 4px;
    transition:
      color 0.15s,
      background-color 0.15s;
  }

  .btn-close:hover {
    color: #fff;
    background: rgba(239, 68, 68, 0.2);
  }

  .modal-body {
    padding: 1.25rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .modal-description {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0;
    line-height: 1.4;
  }

  .alert {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 0.85rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .alert--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .alert--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
  }

  .role-form {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 6px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .flex-2 {
    flex: 2;
    min-width: 180px;
  }

  .flex-3 {
    flex: 3;
    min-width: 200px;
  }

  .flex-btn {
    display: flex;
    flex-direction: column;
    min-width: 130px;
  }

  .form-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #cbd5e1;
    font-family: monospace;
    text-transform: uppercase;
    line-height: 1.2;
    height: 16px;
    display: flex;
    align-items: center;
  }

  .form-label-spacer {
    visibility: hidden;
    user-select: none;
  }

  .required {
    color: #ef4444;
  }

  .form-control {
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 4px;
    padding: 0 0.75rem;
    height: 38px;
    color: #f8fafc;
    font-size: 0.85rem;
    font-family: monospace;
    box-sizing: border-box;
    width: 100%;
  }

  .form-control:focus {
    outline: none;
    border-color: #00f0ff;
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.3);
  }

  .help-text {
    font-size: 0.7rem;
    color: #64748b;
    margin-top: 0.1rem;
  }

  .btn-primary {
    background: #00f0ff;
    color: #020617;
    border: none;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0 1.25rem;
    height: 38px;
    border-radius: 4px;
    cursor: pointer;
    font-family: monospace;
    transition:
      background-color 0.15s,
      transform 0.1s;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
  }

  .btn-primary:hover:not(:disabled) {
    background: #38bdf8;
    transform: translateY(-1px);
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .roles-section {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .section-title {
    font-size: 0.85rem;
    color: #e2e8f0;
    margin: 0;
    font-family: monospace;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .roles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.65rem;
  }

  .role-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 6px;
    padding: 0.65rem 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    transition: border-color 0.15s;
  }

  .role-card--custom {
    border-color: rgba(0, 240, 255, 0.35);
    background: rgba(8, 47, 73, 0.25);
  }

  .role-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .role-name {
    font-family: monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: #f1f5f9;
  }

  .role-badge {
    font-size: 0.65rem;
    padding: 0.15rem 0.45rem;
    border-radius: 3px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .badge-standard {
    background: rgba(100, 116, 139, 0.25);
    color: #94a3b8;
    border: 1px solid rgba(100, 116, 139, 0.4);
  }

  .badge-custom {
    background: rgba(0, 240, 255, 0.15);
    color: #00f0ff;
    border: 1px solid rgba(0, 240, 255, 0.4);
  }

  .role-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .role-desc-text {
    font-size: 0.75rem;
    color: #cbd5e1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .system-desc {
    color: #64748b;
    font-style: italic;
  }

  .btn-delete-role {
    background: transparent;
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #f87171;
    border-radius: 3px;
    font-size: 0.7rem;
    padding: 0.2rem 0.45rem;
    cursor: pointer;
    font-family: monospace;
    transition:
      background-color 0.15s,
      border-color 0.15s;
    white-space: nowrap;
  }

  .btn-delete-role:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
  }

  .modal-footer {
    padding: 0.75rem 1.25rem;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    display: flex;
    justify-content: flex-end;
    background: rgba(15, 23, 42, 0.95);
  }

  .btn-secondary {
    background: #334155;
    color: #e2e8f0;
    border: none;
    font-size: 0.85rem;
    padding: 0.45rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: monospace;
  }

  .btn-secondary:hover {
    background: #475569;
  }
</style>
