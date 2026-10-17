<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import type { TenantItem } from '@/types';

  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const tenants = ref<TenantItem[]>([]);

  // Modal de Crear Empresa
  const isCreateModalOpen = ref(false);
  const isCreating = ref(false);
  const newTenant = ref({
    slug: '',
    name: '',
    tax_id: '',
    admin_email: '',
    admin_username: '',
    admin_password: '',
    max_routers_quota: 50,
    max_users_quota: 20,
    default_safemode_seconds: 60,
  });

  async function loadTenants() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<TenantItem[] | { items: TenantItem[] }>('/api/v1/tenants');
      tenants.value = Array.isArray(res.data) ? res.data : (res.data?.items || []);
    } catch (err: unknown) {
      tenants.value = [];
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar organizaciones.';
    } finally {
      isLoading.value = false;
    }
  }

  async function toggleSuspendTenant(tenant: TenantItem) {
    const action = tenant.status === 'ACTIVE' ? 'suspender' : 'activar';
    if (!confirm(`¿Estás seguro de que deseas ${action} la organización "${tenant.name}"?`)) {
      return;
    }

    try {
      const newStatus = tenant.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
      await http.patch(`/api/v1/tenants/${tenant.id}`, { status: newStatus });
      tenant.status = newStatus;
      successMessage.value = `Estado de "${tenant.name}" actualizado a ${newStatus}.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cambiar estado de la empresa.';
    }
  }

  async function handleCreateTenant() {
    isCreating.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post<{ tenant: TenantItem }>('/api/v1/tenants', newTenant.value);
      tenants.value.push(
        res.data.tenant || {
          id: `t-${Date.now()}`,
          slug: newTenant.value.slug,
          name: newTenant.value.name,
          tax_id: newTenant.value.tax_id,
          status: 'ACTIVE',
          max_routers_quota: newTenant.value.max_routers_quota,
          max_users_quota: newTenant.value.max_users_quota,
          active_routers_count: 0,
          active_users_count: 1,
          default_safemode_seconds: newTenant.value.default_safemode_seconds,
        },
      );

      isCreateModalOpen.value = false;
      successMessage.value = `Empresa "${newTenant.value.name}" creada exitosamente.`;
      // Reset form
      newTenant.value = {
        slug: '',
        name: '',
        tax_id: '',
        admin_email: '',
        admin_username: '',
        admin_password: '',
        max_routers_quota: 50,
        max_users_quota: 20,
        default_safemode_seconds: 60,
      };
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear la empresa.';
    } finally {
      isCreating.value = false;
    }
  }

  onMounted(() => {
    loadTenants();
  });
</script>

<template>
  <div class="tenants-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Administración de Empresas (Multi-Tenant)</h1>
        <p class="view-subtitle">
          Gestión de organizaciones, cuotas de hardware MikroTik y suspensión de Tenants.
        </p>
      </div>
      <button type="button" class="btn-create" @click="isCreateModalOpen = true">
        + Registrar Empresa
      </button>
    </header>

    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="banner banner--success" role="status">
      {{ successMessage }}
    </div>

    <div class="table-container">
      <table class="rg-table" aria-label="Listado de empresas y cuotas">
        <thead>
          <tr>
            <th scope="col">Organización</th>
            <th scope="col">Slug</th>
            <th scope="col">RIF / Tax ID</th>
            <th scope="col">Estado</th>
            <th scope="col">Cuota Routers</th>
            <th scope="col">Cuota Usuarios</th>
            <th scope="col">Safe Mode</th>
            <th scope="col" class="col-actions">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tenants" :key="t.id">
            <td class="cell-name">
              <strong>{{ t.name }}</strong>
            </td>
            <td class="cell-slug">
              <code>{{ t.slug }}</code>
            </td>
            <td>{{ t.tax_id || '—' }}</td>
            <td>
              <span
                class="badge-status"
                :class="{
                  'badge-status--active': t.status === 'ACTIVE',
                  'badge-status--suspended': t.status === 'SUSPENDED',
                }"
              >
                {{ t.status }}
              </span>
            </td>
            <td class="cell-quota">
              <div class="quota-bar-track">
                <div
                  class="quota-bar-fill"
                  :style="{
                    width: `${Math.min(100, (t.active_routers_count / t.max_routers_quota) * 100)}%`,
                  }"
                ></div>
              </div>
              <span class="quota-text"
                >{{ t.active_routers_count }} / {{ t.max_routers_quota }}</span
              >
            </td>
            <td class="cell-quota">
              <div class="quota-bar-track">
                <div
                  class="quota-bar-fill"
                  :style="{
                    width: `${Math.min(100, (t.active_users_count / t.max_users_quota) * 100)}%`,
                  }"
                ></div>
              </div>
              <span class="quota-text">{{ t.active_users_count }} / {{ t.max_users_quota }}</span>
            </td>
            <td class="cell-safemode">{{ t.default_safemode_seconds }}s</td>
            <td class="col-actions">
              <button
                type="button"
                class="btn-action"
                :class="{ 'btn-action--danger': t.status === 'ACTIVE' }"
                @click="toggleSuspendTenant(t)"
              >
                {{ t.status === 'ACTIVE' ? 'Suspender' : 'Reactivar' }}
              </button>
            </td>
          </tr>
          <tr v-if="tenants.length === 0 && !isLoading">
            <td colspan="8" class="cell-empty">No hay organizaciones registradas.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Creación de Empresa -->
    <div v-if="isCreateModalOpen" class="rg-modal-backdrop" @click.self="isCreateModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-tenant-title">
        <header class="modal-header">
          <h2 id="modal-tenant-title" class="modal-title">Registrar Nueva Organización</h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isCreateModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleCreateTenant">
          <div class="form-row">
            <div class="form-group">
              <label for="tenant-name" class="form-label">Nombre Comercial *</label>
              <input
                id="tenant-name"
                v-model="newTenant.name"
                type="text"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="tenant-slug-new" class="form-label">Slug de Subdominio *</label>
              <input
                id="tenant-slug-new"
                v-model="newTenant.slug"
                type="text"
                required
                pattern="[a-z0-9-]+"
                placeholder="ej. isp-este"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="tenant-tax-id" class="form-label">RIF / Identificación Fiscal</label>
              <input id="tenant-tax-id" v-model="newTenant.tax_id" type="text" class="form-input" />
            </div>
            <div class="form-group">
              <label for="tenant-safemode" class="form-label"
                >Safe Mode por Defecto (segundos)</label
              >
              <input
                id="tenant-safemode"
                v-model.number="newTenant.default_safemode_seconds"
                type="number"
                min="10"
                max="300"
                class="form-input"
              />
            </div>
          </div>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Cuotas Asignadas</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="max-routers" class="form-label">Límite de Routers *</label>
                <input
                  id="max-routers"
                  v-model.number="newTenant.max_routers_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="max-users" class="form-label">Límite de Usuarios *</label>
                <input
                  id="max-users"
                  v-model.number="newTenant.max_users_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
            </div>
          </fieldset>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Administrador Inicial (TENANT_ADMIN)</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="admin-user" class="form-label">Username *</label>
                <input
                  id="admin-user"
                  v-model="newTenant.admin_username"
                  type="text"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="admin-email" class="form-label">Correo *</label>
                <input
                  id="admin-email"
                  v-model="newTenant.admin_email"
                  type="email"
                  required
                  class="form-input"
                />
              </div>
            </div>
            <div class="form-group">
              <label for="admin-pass" class="form-label">Contraseña Temporal *</label>
              <input
                id="admin-pass"
                v-model="newTenant.admin_password"
                type="password"
                required
                class="form-input"
              />
            </div>
          </fieldset>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isCreateModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-submit" :disabled="isCreating">
              {{ isCreating ? 'Creando...' : 'Crear Organización' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .tenants-view {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .view-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .view-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 4px 0 0 0;
  }

  .btn-create {
    background-color: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 700;
    cursor: pointer;
  }

  .banner {
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 0.85rem;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .table-container {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    overflow-x: auto;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .rg-table th {
    background-color: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 10px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
  }

  .rg-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-slug code {
    font-family: 'JetBrains Mono', monospace;
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-status {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
  }

  .badge-status--active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid #10b981;
  }

  .badge-status--suspended {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid #ef4444;
  }

  .quota-bar-track {
    width: 100px;
    height: 6px;
    background: var(--rg-bg-canvas, #0b0f19);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 4px;
  }

  .quota-bar-fill {
    height: 100%;
    background: var(--rg-accent-cyan, #22d3ee);
  }

  .quota-text {
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: var(--rg-text-muted, #94a3b8);
  }

  .cell-safemode {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }

  .btn-action {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75rem;
  }

  .btn-action--danger {
    border-color: #ef4444;
    color: #f87171;
  }

  .cell-empty {
    text-align: center;
    padding: 32px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 16px;
  }

  .rg-modal {
    width: 100%;
    max-width: 600px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
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

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.2rem;
    cursor: pointer;
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .form-row {
    display: flex;
    gap: 12px;
  }

  .form-group {
    flex: 1;
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

  .form-fieldset {
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .fieldset-legend {
    font-size: 0.75rem;
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 0 6px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 8px;
  }

  .btn-submit {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
