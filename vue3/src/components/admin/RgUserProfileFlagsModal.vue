<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

<script setup lang="ts">
  /* eslint-disable security/detect-object-injection */
  import { ref, computed, watch } from 'vue';
  import { http } from '@/api/httpClient';
  import type { UserManagementItem } from '@/types';

  interface ActionCatalogItem {
    key: string;
    label: string;
    category: string;
    description: string;
  }

  interface EffectivePermissionsResponse {
    user_id: string;
    username: string;
    role: string;
    role_defaults: Record<string, string>;
    tenant_role_overrides: Record<string, string>;
    user_overrides: Record<string, string>;
    effective_permissions: Record<string, string>;
    actions_catalog: ActionCatalogItem[];
  }

  const props = defineProps<{
    isOpen: boolean;
    user: UserManagementItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'saved', overrides: Record<string, string>): void;
  }>();

  const isLoading = ref(false);
  const isSaving = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');

  const searchQuery = ref('');
  const selectedCategory = ref('ALL');

  const actionsCatalog = ref<ActionCatalogItem[]>([]);
  const roleDefaults = ref<Record<string, string>>({});
  const effectivePermissions = ref<Record<string, string>>({});
  const currentOverrides = ref<Record<string, string | null>>({});

  const categories = computed(() => {
    const set = new Set<string>();
    actionsCatalog.value.forEach((act) => {
      if (act.category) set.add(act.category);
    });
    return Array.from(set).sort();
  });

  const filteredActions = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const cat = selectedCategory.value;

    return actionsCatalog.value.filter((act) => {
      const matchCat = cat === 'ALL' || act.category === cat;
      const matchQuery =
        !q ||
        act.key.toLowerCase().includes(q) ||
        act.label.toLowerCase().includes(q) ||
        act.description.toLowerCase().includes(q) ||
        act.category.toLowerCase().includes(q);
      return matchCat && matchQuery;
    });
  });

  const customOverridesCount = computed(() => {
    let count = 0;
    for (const key of Object.keys(currentOverrides.value)) {
      if (currentOverrides.value[key] !== null && currentOverrides.value[key] !== undefined) {
        count++;
      }
    }
    return count;
  });

  async function loadEffectivePermissions() {
    if (!props.user) return;
    isLoading.value = true;
    errorMessage.value = '';
    successMessage.value = '';

    try {
      const res = await http.get<EffectivePermissionsResponse>(
        `/api/v1/users/${props.user.id}/effective-permissions`,
      );
      actionsCatalog.value = res.data.actions_catalog || [];
      roleDefaults.value = res.data.role_defaults || {};
      effectivePermissions.value = res.data.effective_permissions || {};

      const overridesCopy: Record<string, string | null> = {};
      const savedOverrides = res.data.user_overrides || {};
      for (const act of actionsCatalog.value) {
        overridesCopy[act.key] = savedOverrides[act.key] ?? null;
      }
      currentOverrides.value = overridesCopy;
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cargar permisos del operador.';
    } finally {
      isLoading.value = false;
    }
  }

  watch(
    [() => props.isOpen, () => props.user],
    ([open, usr]) => {
      if (open && usr) {
        searchQuery.value = '';
        selectedCategory.value = 'ALL';
        loadEffectivePermissions();
      }
    },
    { immediate: true },
  );

  function setActionOverride(key: string, value: string | null) {
    currentOverrides.value[key] = value;
  }

  function resetAllToInherited() {
    for (const act of actionsCatalog.value) {
      currentOverrides.value[act.key] = null;
    }
  }

  async function handleSave() {
    if (!props.user) return;
    isSaving.value = true;
    errorMessage.value = '';
    successMessage.value = '';

    const payloadOverrides: Record<string, string | null> = {};
    for (const [k, v] of Object.entries(currentOverrides.value)) {
      payloadOverrides[k] = v;
    }

    try {
      const res = await http.patch<{
        status: string;
        feature_flags_override: Record<string, string>;
      }>(`/api/v1/users/${props.user.id}/feature-flags`, {
        feature_flags_override: payloadOverrides,
      });

      successMessage.value = 'Flags del perfil actualizados exitosamente.';
      emit('saved', res.data.feature_flags_override || {});
      setTimeout(() => {
        emit('close');
      }, 900);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al guardar los flags del perfil.';
    } finally {
      isSaving.value = false;
    }
  }

  function getBadgeClass(level: string) {
    switch (level) {
      case 'ALLOW':
        return 'badge-allow';
      case 'MAKER_CHECKER':
        return 'badge-mc';
      case 'READ_ONLY':
        return 'badge-ro';
      case 'DENY':
      default:
        return 'badge-deny';
    }
  }
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="emit('close')">
    <div
      class="rg-profile-flags-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-flags-title"
    >
      <header class="modal-header">
        <div>
          <h2 id="profile-flags-title" class="modal-title">
            🎛️ Flags de Funciones y Permisos por Operador
          </h2>
          <p v-if="user" class="modal-subtitle">
            Operador: <strong>@{{ user.username }}</strong>
            <span v-if="user.full_name"> ({{ user.full_name }})</span> · Rol Base:
            <span class="badge-role-tag">{{ user.role }}</span>
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de flags"
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

        <!-- Barra de Búsqueda y Filtros -->
        <div class="flags-toolbar">
          <div class="toolbar-search">
            <label for="search-profile-flags" class="sr-only">Buscar función</label>
            <input
              id="search-profile-flags"
              v-model="searchQuery"
              type="search"
              placeholder="🔍 Filtrar función por nombre, clave o descripción..."
              class="form-input search-input"
            />
          </div>

          <div class="toolbar-filters">
            <label for="filter-profile-category" class="sr-only">Categoría</label>
            <select
              id="filter-profile-category"
              v-model="selectedCategory"
              class="form-select cat-select"
            >
              <option value="ALL">Todas las Categorías ({{ actionsCatalog.length }})</option>
              <option v-for="cat in categories" :key="cat" :value="cat">
                {{ cat }}
              </option>
            </select>

            <button
              type="button"
              class="btn-reset-inherited"
              :disabled="customOverridesCount === 0 || isSaving"
              @click="resetAllToInherited"
            >
              ↺ Heredar Todo
            </button>
          </div>
        </div>

        <!-- Resumen de Métricas -->
        <div class="flags-summary-bar">
          <span class="summary-metric">
            Total Funciones: <strong>{{ actionsCatalog.length }}</strong>
          </span>
          <span class="summary-metric">
            Coincidentes: <strong>{{ filteredActions.length }}</strong>
          </span>
          <span class="summary-metric highlight">
            Overrides Personalizados: <strong>{{ customOverridesCount }}</strong>
          </span>
        </div>

        <!-- Tabla / Grid de Funciones -->
        <div v-if="isLoading" class="loading-state">
          <span>Cargando catálogo de funciones y permisos...</span>
        </div>

        <div v-else-if="filteredActions.length === 0" class="empty-state">
          <span>No se encontraron funciones que coincidan con la búsqueda.</span>
        </div>

        <div v-else class="flags-table-scroll">
          <table class="flags-table" aria-label="Catálogo de funciones y overrides">
            <thead>
              <tr>
                <th scope="col" style="width: 25%">Función</th>
                <th scope="col" style="width: 18%">Categoría</th>
                <th scope="col" style="width: 32%">Descripción</th>
                <th scope="col" style="width: 13%">Heredado (Rol)</th>
                <th scope="col" style="width: 12%">Estado en Perfil</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="act in filteredActions"
                :key="act.key"
                :class="{ 'row--customized': currentOverrides[act.key] !== null }"
              >
                <td class="col-name">
                  <div class="action-label">{{ act.label }}</div>
                  <code class="action-key">{{ act.key }}</code>
                </td>

                <td class="col-category">
                  <span class="badge-category">{{ act.category }}</span>
                </td>

                <td class="col-desc">
                  <span class="desc-text">{{ act.description }}</span>
                </td>

                <td class="col-inherited">
                  <span :class="['badge-perm', getBadgeClass(roleDefaults[act.key] || 'DENY')]">
                    {{ roleDefaults[act.key] || 'DENY' }}
                  </span>
                </td>

                <td class="col-override">
                  <select
                    :id="`select-override-${act.key}`"
                    class="form-select select-override"
                    :value="currentOverrides[act.key] ?? 'INHERIT'"
                    :aria-label="`Nivel de permiso para ${act.label}`"
                    @change="(e: Event) => {
                      const val = (e.target as HTMLSelectElement).value;
                      setActionOverride(act.key, val === 'INHERIT' ? null : val);
                    }"
                  >
                    <option value="INHERIT">
                      Heredado ({{ roleDefaults[act.key] || 'DENY' }})
                    </option>
                    <option value="ALLOW">ALLOW (Permitir)</option>
                    <option value="MAKER_CHECKER">MAKER_CHECKER (Aprobación)</option>
                    <option value="READ_ONLY">READ_ONLY (Solo Lectura)</option>
                    <option value="DENY">DENY (Prohibir)</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <footer class="modal-footer">
        <div class="footer-left">
          <span v-if="customOverridesCount > 0" class="override-notice">
            ⚠️ Hay {{ customOverridesCount }} override(s) individual(es) configurado(s).
          </span>
          <span v-else class="override-notice-clean">
            ✓ Este operador hereda el 100% de las políticas de su rol.
          </span>
        </div>

        <div class="footer-actions">
          <button
            type="button"
            class="btn-cancel"
            :disabled="isSaving"
            @click="emit('close')"
          >
            Cancelar
          </button>
          <button
            id="btn-save-user-flags"
            type="button"
            class="btn-submit"
            :disabled="isSaving || isLoading"
            @click="handleSave"
          >
            {{ isSaving ? 'Guardando...' : '💾 Guardar Flags' }}
          </button>
        </div>
      </footer>
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
    z-index: 1100;
    padding: var(--rg-space-md, 1rem);
  }

  .rg-profile-flags-modal {
    background: var(--rg-bg-card, #111827);
    color: var(--rg-text-primary, #f3f4f6);
    border: 1px solid var(--rg-border-subtle, #374151);
    border-radius: var(--rg-radius-md, 8px);
    width: 100%;
    max-width: 1180px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: var(--rg-space-md, 1rem) var(--rg-space-lg, 1.25rem);
    border-bottom: 1px solid var(--rg-border-subtle, #374151);
    background: var(--rg-bg-card-secondary, #1f2937);
    border-top-left-radius: var(--rg-radius-md, 8px);
    border-top-right-radius: var(--rg-radius-md, 8px);
  }

  .modal-title {
    font-size: var(--rg-font-size-lg, 1.125rem);
    font-weight: 700;
    color: var(--rg-accent-cyan, #00d2ff);
    margin: 0;
  }

  .modal-subtitle {
    font-size: var(--rg-font-size-sm, 0.875rem);
    color: var(--rg-text-secondary, #9ca3af);
    margin-top: 0.25rem;
  }

  .badge-role-tag {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    font-size: 0.75rem;
    border-radius: var(--rg-radius-xs, 4px);
    background: var(--rg-accent-cyan-subtle, rgba(0, 210, 255, 0.15));
    color: var(--rg-accent-cyan, #00d2ff);
    font-weight: 600;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary, #9ca3af);
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: var(--rg-radius-xs, 4px);
  }

  .btn-close:hover {
    color: var(--rg-text-primary, #f3f4f6);
    background: rgba(255, 255, 255, 0.1);
  }

  .modal-body {
    padding: var(--rg-space-md, 1rem) var(--rg-space-lg, 1.25rem);
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--rg-space-md, 1rem);
  }

  .msg-banner {
    padding: 0.75rem 1rem;
    border-radius: var(--rg-radius-sm, 6px);
    font-size: 0.875rem;
  }

  .msg-banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .msg-banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
  }

  .flags-toolbar {
    display: flex;
    gap: var(--rg-space-sm, 0.75rem);
    align-items: center;
    flex-wrap: wrap;
  }

  .toolbar-search {
    flex: 1;
    min-width: 280px;
  }

  .search-input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border-radius: var(--rg-radius-sm, 6px);
    background: var(--rg-bg-input, #1f2937);
    border: 1px solid var(--rg-border-subtle, #374151);
    color: var(--rg-text-primary, #f3f4f6);
    font-size: 0.875rem;
  }

  .toolbar-filters {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .cat-select {
    padding: 0.5rem 0.75rem;
    border-radius: var(--rg-radius-sm, 6px);
    background: var(--rg-bg-input, #1f2937);
    border: 1px solid var(--rg-border-subtle, #374151);
    color: var(--rg-text-primary, #f3f4f6);
    font-size: 0.875rem;
  }

  .btn-reset-inherited {
    padding: 0.5rem 0.75rem;
    border-radius: var(--rg-radius-sm, 6px);
    background: var(--rg-bg-card-secondary, #1f2937);
    border: 1px solid var(--rg-border-subtle, #374151);
    color: var(--rg-text-secondary, #9ca3af);
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
  }

  .btn-reset-inherited:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.08);
    color: var(--rg-text-primary, #f3f4f6);
  }

  .btn-reset-inherited:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .flags-summary-bar {
    display: flex;
    gap: var(--rg-space-md, 1rem);
    padding: 0.4rem 0.75rem;
    background: rgba(0, 0, 0, 0.25);
    border-radius: var(--rg-radius-sm, 6px);
    font-size: 0.8125rem;
    color: var(--rg-text-secondary, #9ca3af);
  }

  .summary-metric strong {
    color: var(--rg-text-primary, #f3f4f6);
  }

  .summary-metric.highlight strong {
    color: var(--rg-accent-cyan, #00d2ff);
  }

  .loading-state,
  .empty-state {
    padding: var(--rg-space-xl, 2rem);
    text-align: center;
    color: var(--rg-text-secondary, #9ca3af);
    font-size: 0.875rem;
  }

  .flags-table-scroll {
    overflow-x: auto;
    border: 1px solid var(--rg-border-subtle, #374151);
    border-radius: var(--rg-radius-sm, 6px);
  }

  .flags-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
    text-align: left;
  }

  .flags-table th {
    background: var(--rg-bg-card-secondary, #1f2937);
    color: var(--rg-text-secondary, #9ca3af);
    font-weight: 600;
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid var(--rg-border-subtle, #374151);
    white-space: nowrap;
  }

  .flags-table td {
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    vertical-align: middle;
  }

  .flags-table tr:hover {
    background: rgba(255, 255, 255, 0.02);
  }

  .row--customized {
    background: rgba(0, 210, 255, 0.04);
  }

  .action-label {
    font-weight: 600;
    color: var(--rg-text-primary, #f3f4f6);
  }

  .action-key {
    font-size: 0.72rem;
    color: var(--rg-text-muted, #6b7280);
    background: rgba(0, 0, 0, 0.3);
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
  }

  .badge-category {
    font-size: 0.72rem;
    padding: 0.15rem 0.4rem;
    border-radius: var(--rg-radius-xs, 4px);
    background: rgba(255, 255, 255, 0.06);
    color: var(--rg-text-secondary, #9ca3af);
  }

  .desc-text {
    color: var(--rg-text-secondary, #9ca3af);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .badge-perm {
    display: inline-block;
    padding: 0.15rem 0.45rem;
    border-radius: var(--rg-radius-xs, 4px);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .badge-allow {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
  }

  .badge-mc {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  .badge-ro {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
    border: 1px solid rgba(59, 130, 246, 0.4);
  }

  .badge-deny {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
  }

  .select-override {
    width: 100%;
    padding: 0.35rem 0.5rem;
    border-radius: var(--rg-radius-xs, 4px);
    background: var(--rg-bg-input, #1f2937);
    border: 1px solid var(--rg-border-subtle, #374151);
    color: var(--rg-text-primary, #f3f4f6);
    font-size: 0.775rem;
  }

  .select-override:focus {
    border-color: var(--rg-accent-cyan, #00d2ff);
    outline: none;
  }

  .modal-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--rg-space-md, 1rem) var(--rg-space-lg, 1.25rem);
    border-top: 1px solid var(--rg-border-subtle, #374151);
    background: var(--rg-bg-card-secondary, #1f2937);
    border-bottom-left-radius: var(--rg-radius-md, 8px);
    border-bottom-right-radius: var(--rg-radius-md, 8px);
  }

  .override-notice {
    font-size: 0.8125rem;
    color: #f59e0b;
  }

  .override-notice-clean {
    font-size: 0.8125rem;
    color: #10b981;
  }

  .footer-actions {
    display: flex;
    gap: 0.75rem;
  }

  .btn-cancel {
    padding: 0.5rem 1rem;
    border-radius: var(--rg-radius-sm, 6px);
    background: transparent;
    border: 1px solid var(--rg-border-subtle, #374151);
    color: var(--rg-text-secondary, #9ca3af);
    font-size: 0.875rem;
    cursor: pointer;
  }

  .btn-cancel:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.08);
    color: var(--rg-text-primary, #f3f4f6);
  }

  .btn-submit {
    padding: 0.5rem 1.25rem;
    border-radius: var(--rg-radius-sm, 6px);
    background: var(--rg-accent-cyan, #00d2ff);
    color: #0b1320;
    font-weight: 700;
    border: none;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .btn-submit:hover:not(:disabled) {
    background: #38e1ff;
  }

  .btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>
