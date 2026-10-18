<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { http } from '@/api/httpClient';
  import type { RouterPermissionItem, UserManagementItem } from '@/types';

  const props = defineProps<{
    isOpen: boolean;
    user: UserManagementItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'saved', permissions: RouterPermissionItem[]): void;
  }>();

  const isLoading = ref(false);
  const isSaving = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const searchQuery = ref('');
  const hasAllRoutersAccess = ref(false);

  // Lista de permisos por router
  const permissionsList = ref<RouterPermissionItem[]>([]);

  // Filtro reactivo en la tabla de routers
  const filteredPermissions = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return permissionsList.value;
    return permissionsList.value.filter(
      (p) =>
        p.router_name.toLowerCase().includes(q) ||
        (p.network_role && p.network_role.toLowerCase().includes(q)) ||
        (p.tag && p.tag.toLowerCase().includes(q)),
    );
  });

  async function loadUserPermissions() {
    if (!props.user) return;
    isLoading.value = true;
    errorMessage.value = '';
    hasAllRoutersAccess.value = props.user.has_all_routers_access;

    try {
      const res = await http.get<{
        has_all_routers_access: boolean;
        permissions: RouterPermissionItem[];
      }>(`/api/v1/users/${props.user.id}/router-permissions`);

      hasAllRoutersAccess.value =
        res.data.has_all_routers_access ?? props.user.has_all_routers_access;
      permissionsList.value = res.data.permissions || [];
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar routers asignados.';
      permissionsList.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  watch(
    [() => props.isOpen, () => props.user],
    ([open, usr]) => {
      if (open && usr) {
        errorMessage.value = '';
        successMessage.value = '';
        loadUserPermissions();
      }
    },
    { immediate: true },
  );

  // Asignación rápida por lote
  function assignByFilter(
    key: 'can_read' | 'can_write_layer1' | 'can_execute_diagnostics',
    value: boolean,
  ) {
    for (const item of filteredPermissions.value) {
      if (key === 'can_read') {
        item.can_read = value;
      } else if (key === 'can_write_layer1') {
        item.can_write_layer1 = value;
      } else if (key === 'can_execute_diagnostics') {
        item.can_execute_diagnostics = value;
      }
    }
  }

  function assignByRole(role: string) {
    for (const item of permissionsList.value) {
      if (item.network_role === role) {
        item.can_read = true;
        item.can_execute_diagnostics = true;
      }
    }
  }

  function assignByTag(tag: string) {
    for (const item of permissionsList.value) {
      if (item.tag === tag) {
        item.can_read = true;
        item.can_write_layer1 = true;
      }
    }
  }

  async function handleSave() {
    if (!props.user) return;
    isSaving.value = true;
    errorMessage.value = '';
    successMessage.value = '';

    try {
      await http.put(`/api/v1/users/${props.user.id}/router-permissions`, {
        has_all_routers_access: hasAllRoutersAccess.value,
        router_assignments: permissionsList.value,
        permissions: permissionsList.value,
      });

      successMessage.value = 'Permisos de routers actualizados exitosamente.';
      emit('saved', permissionsList.value);
      setTimeout(() => {
        emit('close');
      }, 1000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al guardar los permisos de routers.';
    } finally {
      isSaving.value = false;
    }
  }
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="emit('close')">
    <div
      class="rg-matrix-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="matrix-modal-title"
    >
      <header class="modal-header">
        <div>
          <h2 id="matrix-modal-title" class="modal-title">
            Matriz de Asignación de Equipos MikroTik
          </h2>
          <p v-if="user" class="modal-subtitle">
            Operador: <strong>{{ user.full_name || user.username }}</strong> ({{ user.role }})
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de matriz"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="modal-body">
        <div v-if="errorMessage" class="msg-banner msg-banner--error" role="alert">
          {{ errorMessage }}
        </div>
        <div v-if="successMessage" class="msg-banner msg-banner--success" role="status">
          {{ successMessage }}
        </div>

        <!-- Switch Maestro: Acceso a todos los routers -->
        <div class="master-switch-box">
          <label class="switch-label">
            <input
              id="master-all-access-switch"
              v-model="hasAllRoutersAccess"
              type="checkbox"
              class="switch-input"
            />
            <span class="switch-slider" aria-hidden="true"></span>
            <span class="switch-text">
              Acceso a todos los MikroTiks del Tenant (has_all_routers_access)
            </span>
          </label>
          <span class="switch-help">
            Si está activado, el operador podrá acceder a cualquier router nuevo o existente con los
            permisos de su rol.
          </span>
        </div>

        <!-- Tabla detallada cuando hasAllRoutersAccess es falso -->
        <div v-if="!hasAllRoutersAccess" class="matrix-table-container">
          <!-- Barra de búsqueda y asignación por lote -->
          <div class="matrix-toolbar">
            <input
              id="matrix-search"
              v-model="searchQuery"
              type="search"
              placeholder="Buscar por nombre, rol o etiqueta..."
              class="search-input"
              aria-label="Buscar routers en la matriz"
            />

            <div class="batch-buttons">
              <button type="button" class="btn-batch" @click="assignByFilter('can_read', true)">
                + Leer Todos
              </button>
              <button
                type="button"
                class="btn-batch"
                @click="assignByFilter('can_write_layer1', true)"
              >
                + L1 Todos
              </button>
              <button
                type="button"
                class="btn-batch"
                @click="assignByFilter('can_execute_diagnostics', true)"
              >
                + Diag Todos
              </button>
              <button type="button" class="btn-batch" @click="assignByTag('zona-norte')">
                + Tag: zona-norte
              </button>
              <button type="button" class="btn-batch" @click="assignByRole('TOWER_AP')">
                + Rol: TOWER_AP
              </button>
            </div>
          </div>

          <div class="table-scroll">
            <table class="rg-matrix-table" aria-label="Permisos granulares por router">
              <thead>
                <tr>
                  <th scope="col">Router</th>
                  <th scope="col">Rol / Tag</th>
                  <th scope="col">Lectura</th>
                  <th scope="col">Escritura L1</th>
                  <th scope="col">Escritura L2</th>
                  <th scope="col">Diagnóstico</th>
                  <th scope="col">Backup</th>
                  <th scope="col">Reboot</th>
                  <th scope="col">Omitir M-C</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredPermissions" :key="item.router_id">
                  <td class="cell-name">
                    <strong>{{ item.router_name }}</strong>
                  </td>
                  <td class="cell-tags">
                    <span v-if="item.network_role" class="badge-role">{{ item.network_role }}</span>
                    <span v-if="item.tag" class="badge-tag">{{ item.tag }}</span>
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-read-${item.router_id}`"
                      v-model="item.can_read"
                      type="checkbox"
                      :aria-label="`Lectura en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-l1-${item.router_id}`"
                      v-model="item.can_write_layer1"
                      type="checkbox"
                      :aria-label="`Escritura L1 en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-l2-${item.router_id}`"
                      v-model="item.can_write_layer2"
                      type="checkbox"
                      :aria-label="`Escritura L2 en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-diag-${item.router_id}`"
                      v-model="item.can_execute_diagnostics"
                      type="checkbox"
                      :aria-label="`Diagnóstico en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-bku-${item.router_id}`"
                      v-model="item.can_trigger_backup"
                      type="checkbox"
                      :aria-label="`Backup en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-reb-${item.router_id}`"
                      v-model="item.can_reboot"
                      type="checkbox"
                      :aria-label="`Reinicio en ${item.router_name}`"
                    />
                  </td>
                  <td class="cell-check">
                    <input
                      :id="`chk-mc-${item.router_id}`"
                      v-model="item.bypass_maker_checker"
                      type="checkbox"
                      :aria-label="`Omitir Maker-Checker en ${item.router_name}`"
                    />
                  </td>
                </tr>
                <tr v-if="filteredPermissions.length === 0">
                  <td colspan="9" class="cell-empty">
                    No hay routers disponibles o que coincidan con la búsqueda.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn-secondary" :disabled="isSaving" @click="emit('close')">
          Cancelar
        </button>
        <button type="button" class="btn-primary" :disabled="isSaving" @click="handleSave">
          {{ isSaving ? 'Guardando...' : 'Guardar Asignaciones' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
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

  .rg-matrix-modal {
    width: 100%;
    max-width: 980px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-lg, 8px);
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
    font-size: 1.2rem;
    font-weight: 700;
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

  .btn-close:hover {
    color: var(--rg-text-primary, #f8fafc);
  }

  .modal-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .msg-banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .msg-banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .msg-banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .master-switch-box {
    background-color: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .switch-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--rg-text-primary, #f8fafc);
  }

  .switch-help {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    margin-left: 30px;
  }

  .matrix-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }

  .search-input {
    flex: 1;
    min-width: 240px;
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .batch-buttons {
    display: flex;
    gap: 8px;
  }

  .btn-batch {
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .btn-batch:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
  }

  .table-scroll {
    overflow-x: auto;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
  }

  .rg-matrix-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .rg-matrix-table th {
    background-color: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
    white-space: nowrap;
  }

  .rg-matrix-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-name strong {
    color: var(--rg-text-primary, #f8fafc);
    font-family: 'JetBrains Mono', monospace;
  }

  .cell-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .badge-role {
    font-size: 0.7rem;
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-tag {
    font-size: 0.7rem;
    background: rgba(148, 163, 184, 0.2);
    color: #cbd5e1;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .cell-check {
    text-align: center;
  }

  .cell-check input {
    cursor: pointer;
  }

  .cell-empty {
    text-align: center;
    color: var(--rg-text-muted, #94a3b8);
    padding: 24px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-primary {
    background-color: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    border-radius: 6px;
    padding: 8px 18px;
    cursor: pointer;
  }
</style>
