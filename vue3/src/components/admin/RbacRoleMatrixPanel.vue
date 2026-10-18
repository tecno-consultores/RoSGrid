<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { RbacRoleItem, RbacActionItem } from '@/types';

  const authStore = useAuthStore();

  const isWriteAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });

  const isLoading = ref(false);
  const isSaving = ref(false);
  const isResetting = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');

  const rolesList = ref<RbacRoleItem[]>([]);
  const actionsList = ref<RbacActionItem[]>([]);
  const selectedRoleKey = ref<string>('SUPPORT_L2');

  const selectedRole = computed(() => {
    if (!Array.isArray(rolesList.value)) return null;
    return rolesList.value.find((r) => r.role === selectedRoleKey.value) || rolesList.value[0] || null;
  });

  // Agrupar acciones por categoría
  const groupedActions = computed(() => {
    const groups: Record<string, RbacActionItem[]> = {};
    if (!Array.isArray(actionsList.value)) return groups;
    for (const action of actionsList.value) {
      if (!groups[action.category]) {
        groups[action.category] = [];
      }
      groups[action.category].push(action);
    }
    return groups;
  });

  // Estadísticas del rol seleccionado
  const rolePermissionStats = computed(() => {
    if (!selectedRole.value || !selectedRole.value.permissions) {
      return { allow: 0, makerChecker: 0, readOnly: 0, deny: 0 };
    }
    let allow = 0;
    let makerChecker = 0;
    let readOnly = 0;
    let deny = 0;

    for (const level of Object.values(selectedRole.value.permissions || {})) {
      if (level === 'ALLOW') allow++;
      else if (level === 'MAKER_CHECKER') makerChecker++;
      else if (level === 'READ_ONLY') readOnly++;
      else if (level === 'DENY') deny++;
    }

    return { allow, makerChecker, readOnly, deny };
  });

  async function loadRbacData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const [resRoles, resActions] = await Promise.all([
        http.get<RbacRoleItem[]>('/api/v1/rbac/roles'),
        http.get<RbacActionItem[]>('/api/v1/rbac/actions'),
      ]);

      const rawRoles = resRoles?.data;
      rolesList.value = Array.isArray(rawRoles) ? rawRoles : ((rawRoles as any)?.items || []);
      const rawActions = resActions?.data;
      actionsList.value = Array.isArray(rawActions) ? rawActions : ((rawActions as any)?.items || []);

      if (Array.isArray(rolesList.value) && rolesList.value.length > 0 && !rolesList.value.some((r) => r.role === selectedRoleKey.value)) {
        selectedRoleKey.value = rolesList.value[0].role;
      }
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar la matriz de roles y permisos.';
    } finally {
      isLoading.value = false;
    }
  }

  function setActionPermission(actionKey: string, level: string) {
    if (!selectedRole.value || selectedRole.value.is_system_reserved || !isWriteAuthorized.value) {
      return;
    }
    selectedRole.value.permissions[actionKey] = level;
  }

  function applyBulkLevel(level: 'ALLOW' | 'MAKER_CHECKER' | 'READ_ONLY' | 'DENY') {
    if (!selectedRole.value || selectedRole.value.is_system_reserved || !isWriteAuthorized.value) {
      return;
    }
    for (const action of actionsList.value) {
      // No permitir TENANT_MANAGEMENT para roles que no sean superadmin
      if (action.key === 'TENANT_MANAGEMENT' && selectedRole.value.role !== 'SUPERADMIN_GLOBAL') {
        selectedRole.value.permissions[action.key] = 'DENY';
        continue;
      }
      selectedRole.value.permissions[action.key] = level;
    }
  }

  async function handleSavePermissions() {
    if (!selectedRole.value || selectedRole.value.is_system_reserved || !isWriteAuthorized.value) {
      return;
    }
    isSaving.value = true;
    errorMessage.value = '';
    successMessage.value = '';

    try {
      const res = await http.put<{ message?: string }>(
        `/api/v1/rbac/roles/${selectedRole.value.role}/permissions`,
        { permissions: selectedRole.value.permissions },
      );

      selectedRole.value.has_custom_overrides = true;
      successMessage.value =
        res.data.message || `Permisos del rol "${selectedRole.value.title}" guardados exitosamente.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al guardar los permisos del rol.';
    } finally {
      isSaving.value = false;
    }
  }

  async function handleResetPermissions() {
    if (!selectedRole.value || selectedRole.value.is_system_reserved || !isWriteAuthorized.value) {
      return;
    }
    if (!confirm(`¿Deseas restaurar los permisos del rol "${selectedRole.value.title}" a los valores predeterminados de fábrica?`)) {
      return;
    }

    isResetting.value = true;
    errorMessage.value = '';
    successMessage.value = '';

    try {
      const res = await http.post<{ permissions: Record<string, string>; message?: string }>(
        `/api/v1/rbac/roles/${selectedRole.value.role}/reset`,
      );

      selectedRole.value.permissions = res.data.permissions || {};
      selectedRole.value.has_custom_overrides = false;
      successMessage.value =
        res.data.message || `Permisos del rol "${selectedRole.value.title}" restaurados a fábrica.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al restaurar los permisos.';
    } finally {
      isResetting.value = false;
    }
  }

  onMounted(() => {
    loadRbacData();
  });
</script>

<template>
  <div class="rbac-matrix-panel">
    <!-- Barra informativa de estado -->
    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="banner banner--success" role="status">
      {{ successMessage }}
    </div>

    <!-- Selector Visual de Roles con Descripción Rápida -->
    <div class="roles-selector-container">
      <span class="selector-title">Seleccionar Perfil o Rol a Configurar:</span>
      <div class="roles-chips-grid" role="tablist" aria-label="Listado de Roles Disponibles">
        <button
          v-for="r in rolesList"
          :key="r.role"
          type="button"
          class="role-chip"
          :class="{
            'role-chip--active': r.role === selectedRoleKey,
            'role-chip--system': r.is_system_reserved,
            'role-chip--custom': r.has_custom_overrides,
          }"
          role="tab"
          :aria-selected="r.role === selectedRoleKey"
          @click="selectedRoleKey = r.role"
        >
          <span class="role-chip-level">Niv. {{ r.level }}</span>
          <span class="role-chip-title">{{ r.title }}</span>
          <span v-if="r.is_system_reserved" class="role-chip-badge badge--reserved">Master</span>
          <span v-else-if="r.has_custom_overrides" class="role-chip-badge badge--custom">Personalizado</span>
        </button>
      </div>
    </div>

    <!-- Ficha Detallada del Rol Seleccionado -->
    <div v-if="selectedRole" class="role-details-card">
      <div class="role-card-header">
        <div>
          <div class="role-heading-line">
            <h2 class="role-heading-title">{{ selectedRole.title }}</h2>
            <code class="role-code-badge">{{ selectedRole.role }}</code>
            <span v-if="selectedRole.is_system_reserved" class="badge-pill badge-pill--warning">
              🔒 Inmutable (Núcleo de Seguridad)
            </span>
            <span v-else-if="selectedRole.has_custom_overrides" class="badge-pill badge-pill--info">
              ⚡ Matriz Personalizada en este Tenant
            </span>
          </div>
          <!-- Descripción detallada orientada al administrador -->
          <p class="role-description-text">
            <strong>Descripción del Alcance:</strong> {{ selectedRole.description }}
          </p>
        </div>

        <!-- Estadísticas de Privilegios del Rol -->
        <div class="role-stats-summary">
          <div class="stat-badge stat-badge--allow" title="Acciones Permitidas Directamente">
            <span class="stat-num">{{ rolePermissionStats.allow }}</span>
            <span class="stat-label">Permitidas</span>
          </div>
          <div class="stat-badge stat-badge--mc" title="Acciones bajo Maker-Checker (4 Ojos)">
            <span class="stat-num">{{ rolePermissionStats.makerChecker }}</span>
            <span class="stat-label">Maker-Checker</span>
          </div>
          <div class="stat-badge stat-badge--ro" title="Acciones de Solo Lectura">
            <span class="stat-num">{{ rolePermissionStats.readOnly }}</span>
            <span class="stat-label">Solo Lectura</span>
          </div>
          <div class="stat-badge stat-badge--deny" title="Acciones Denegadas">
            <span class="stat-num">{{ rolePermissionStats.deny }}</span>
            <span class="stat-label">Denegadas</span>
          </div>
        </div>
      </div>

      <!-- Barra de herramientas de edición en lote y guardado -->
      <div class="role-toolbar">
        <div class="bulk-tools">
          <span class="tools-label">Asignación Rápida:</span>
          <button
            type="button"
            class="btn-bulk"
            :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="applyBulkLevel('ALLOW')"
          >
            ✅ Permitir Todo
          </button>
          <button
            type="button"
            class="btn-bulk"
            :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="applyBulkLevel('MAKER_CHECKER')"
          >
            🛡️ Todo Maker-Checker
          </button>
          <button
            type="button"
            class="btn-bulk"
            :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="applyBulkLevel('READ_ONLY')"
          >
            👁️ Todo Solo Lectura
          </button>
          <button
            type="button"
            class="btn-bulk"
            :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="applyBulkLevel('DENY')"
          >
            🚫 Denegar Todo
          </button>
        </div>

        <div class="action-tools">
          <button
            v-if="selectedRole.has_custom_overrides"
            type="button"
            class="btn-reset"
            :disabled="isResetting || selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="handleResetPermissions"
          >
            🔄 Restaurar a Fábrica
          </button>
          <button
            type="button"
            class="btn-save"
            :disabled="isSaving || selectedRole.is_system_reserved || !isWriteAuthorized"
            @click="handleSavePermissions"
          >
            <span v-if="isSaving">💾 Guardando...</span>
            <span v-else>💾 Guardar Permisos del Rol</span>
          </button>
        </div>
      </div>

      <!-- Tabla de Acciones y Niveles de Permiso Agrupados -->
      <div class="matrix-groups-container">
        <div v-for="(actions, category) in groupedActions" :key="category" class="category-block">
          <h3 class="category-title">{{ category }}</h3>

          <div class="actions-grid">
            <div v-for="act in actions" :key="act.key" class="action-card">
              <div class="action-info">
                <span class="action-name">{{ act.label }}</span>
                <code class="action-key">{{ act.key }}</code>
                <p class="action-desc">{{ act.description }}</p>
              </div>

              <!-- Selector de nivel de permiso -->
              <div class="permission-selector">
                <button
                  type="button"
                  class="btn-perm btn-perm--allow"
                  :class="{ 'btn-perm--active': selectedRole.permissions[act.key] === 'ALLOW' }"
                  :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
                  title="Permitido Directo (Sin Restricciones)"
                  @click="setActionPermission(act.key, 'ALLOW')"
                >
                  ALLOW
                </button>
                <button
                  type="button"
                  class="btn-perm btn-perm--mc"
                  :class="{ 'btn-perm--active': selectedRole.permissions[act.key] === 'MAKER_CHECKER' }"
                  :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
                  title="Requiere Aprobación Formal de Supervisor (Maker-Checker)"
                  @click="setActionPermission(act.key, 'MAKER_CHECKER')"
                >
                  MAKER-CHECKER
                </button>
                <button
                  type="button"
                  class="btn-perm btn-perm--ro"
                  :class="{ 'btn-perm--active': selectedRole.permissions[act.key] === 'READ_ONLY' }"
                  :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
                  title="Acceso de Solo Lectura (Inspección sin Modificar)"
                  @click="setActionPermission(act.key, 'READ_ONLY')"
                >
                  READ ONLY
                </button>
                <button
                  type="button"
                  class="btn-perm btn-perm--deny"
                  :class="{ 'btn-perm--active': selectedRole.permissions[act.key] === 'DENY' }"
                  :disabled="selectedRole.is_system_reserved || !isWriteAuthorized"
                  title="Denegado Totalmente"
                  @click="setActionPermission(act.key, 'DENY')"
                >
                  DENY
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .rbac-matrix-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .banner {
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.875rem;
    line-height: 1.4;
  }
  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  /* Selector de Chips de Roles */
  .roles-selector-container {
    background: var(--rg-bg-surface, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 8px;
    padding: 16px;
  }
  .selector-title {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #94a3b8);
    margin-bottom: 12px;
  }
  .roles-chips-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
  }
  .role-chip {
    background: var(--rg-bg-input, #0f172a);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }
  .role-chip:hover {
    border-color: var(--rg-accent-cyan, #06b6d4);
    background: rgba(6, 182, 212, 0.08);
  }
  .role-chip--active {
    border-color: var(--rg-accent-cyan, #06b6d4);
    background: rgba(6, 182, 212, 0.15);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  }
  .role-chip-level {
    font-size: 0.75rem;
    color: var(--rg-text-secondary, #94a3b8);
    font-weight: 600;
  }
  .role-chip-title {
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
  }
  .role-chip-badge {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    margin-top: 2px;
  }
  .badge--reserved {
    background: rgba(168, 85, 247, 0.2);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.4);
  }
  .badge--custom {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  /* Ficha de Detalles */
  .role-details-card {
    background: var(--rg-bg-surface, #1e293b);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .role-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
    padding-bottom: 16px;
  }
  .role-heading-line {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .role-heading-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--rg-text-primary, #f8fafc);
    margin: 0;
  }
  .role-code-badge {
    background: #0f172a;
    color: var(--rg-accent-cyan, #06b6d4);
    border: 1px solid var(--rg-border-grid, #334155);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
  }
  .badge-pill {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
  }
  .badge-pill--warning {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
    border: 1px solid rgba(234, 179, 8, 0.4);
  }
  .badge-pill--info {
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.4);
  }
  .role-description-text {
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 6px 0 0 0;
    max-width: 800px;
  }
  .role-description-text strong {
    color: var(--rg-accent-cyan, #06b6d4);
  }

  /* Estadísticas */
  .role-stats-summary {
    display: flex;
    gap: 8px;
  }
  .stat-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 6px 12px;
    border-radius: 6px;
    min-width: 65px;
  }
  .stat-num {
    font-size: 1.1rem;
    font-weight: 800;
  }
  .stat-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    font-weight: 600;
  }
  .stat-badge--allow {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .stat-badge--mc {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }
  .stat-badge--ro {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
  }
  .stat-badge--deny {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  /* Barra de herramientas */
  .role-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
  }
  .bulk-tools {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .tools-label {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #94a3b8);
    font-weight: 600;
  }
  .btn-bulk {
    background: #0f172a;
    border: 1px solid var(--rg-border-grid, #334155);
    color: var(--rg-text-primary, #f8fafc);
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 0.75rem;
    cursor: pointer;
  }
  .btn-bulk:hover:not(:disabled) {
    background: #1e293b;
    border-color: var(--rg-accent-cyan, #06b6d4);
  }
  .action-tools {
    display: flex;
    gap: 10px;
  }
  .btn-reset {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #334155);
    color: var(--rg-text-secondary, #94a3b8);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .btn-reset:hover:not(:disabled) {
    color: #f8fafc;
    border-color: #ef4444;
  }
  .btn-save {
    background: var(--rg-accent-cyan, #06b6d4);
    color: #0f172a;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 6px;
    border: none;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .btn-save:hover:not(:disabled) {
    background: #0891b2;
  }
  button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* Categorías y Acciones */
  .matrix-groups-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .category-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #06b6d4);
    margin: 0 0 10px 0;
    border-left: 3px solid var(--rg-accent-cyan, #06b6d4);
    padding-left: 8px;
  }
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 12px;
  }
  .action-card {
    background: var(--rg-bg-input, #0f172a);
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 10px;
  }
  .action-name {
    display: block;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
  }
  .action-key {
    font-size: 0.7rem;
    color: var(--rg-text-secondary, #94a3b8);
  }
  .action-desc {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #94a3b8);
    margin: 4px 0 0 0;
    line-height: 1.3;
  }

  /* Segmented Buttons de Permiso */
  .permission-selector {
    display: flex;
    background: #090d16;
    border: 1px solid var(--rg-border-grid, #334155);
    border-radius: 6px;
    padding: 2px;
    gap: 2px;
  }
  .btn-perm {
    flex: 1;
    background: transparent;
    border: none;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 6px 2px;
    border-radius: 4px;
    color: var(--rg-text-secondary, #94a3b8);
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
  }
  .btn-perm:hover:not(:disabled) {
    color: #f8fafc;
  }
  .btn-perm--allow.btn-perm--active {
    background: #10b981;
    color: #0f172a;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
  }
  .btn-perm--mc.btn-perm--active {
    background: #f59e0b;
    color: #0f172a;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
  }
  .btn-perm--ro.btn-perm--active {
    background: #3b82f6;
    color: #ffffff;
    box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
  }
  .btn-perm--deny.btn-perm--active {
    background: #ef4444;
    color: #ffffff;
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  }
</style>
