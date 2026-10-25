<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import type { RouterItem, TableColumn } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import OsmRouterMap from '@/components/inventory/OsmRouterMap.vue';
  import CsvOnboardingWizardModal from '@/components/inventory/CsvOnboardingWizardModal.vue';
  import VaultRevealModal from '@/components/inventory/VaultRevealModal.vue';
  import ManageNetworkRolesModal from '@/components/inventory/ManageNetworkRolesModal.vue';

  const router = useRouter();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();
  const { t } = useI18n();

  const isVaultAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });

  // Modos de visualización
  type ViewMode = 'table' | 'map' | 'split';
  const currentViewMode = ref<ViewMode>('table');

  // Filtros
  const searchFilter = ref('');
  const networkRoleFilter = ref('ALL');
  const adminStateFilter = ref('ALL');
  const operationalFilter = ref('ALL');

  // Router seleccionado para enfocar en mapa
  const selectedRouterId = ref<string | null>(null);

  // Modales
  const isCsvModalOpen = ref(false);
  const isVaultModalOpen = ref(false);
  const isRolesModalOpen = ref(false);
  const targetRouterForVault = ref<RouterItem | null>(null);

  // Feedback de operaciones
  const actionMessage = ref('');
  const actionError = ref('');

  const networkRoles = computed(() => {
    const rolesSet = new Set<string>(inventoryStore.networkRoles);
    for (const r of inventoryStore.routers) {
      if (r.network_role) {
        rolesSet.add(r.network_role);
      }
    }
    return Array.from(rolesSet);
  });

  const filteredRouters = computed<RouterItem[]>(() => {
    return inventoryStore.routers.filter((r) => {
      const q = searchFilter.value.trim().toLowerCase();
      const matchesSearch =
        !q ||
        r.display_name.toLowerCase().includes(q) ||
        (r.ros_identity && r.ros_identity.toLowerCase().includes(q)) ||
        (r.serial_number && r.serial_number.toLowerCase().includes(q)) ||
        (r.model && r.model.toLowerCase().includes(q)) ||
        r.ip_address.includes(q);

      const matchesRole =
        networkRoleFilter.value === 'ALL' || r.network_role === networkRoleFilter.value;
      const matchesAdmin =
        adminStateFilter.value === 'ALL' || r.admin_state === adminStateFilter.value;

      let matchesOperational = true;
      if (operationalFilter.value === 'ONLINE') {
        matchesOperational = r.is_reachable && r.ssl_trust_status !== 'FINGERPRINT_MISMATCH';
      } else if (operationalFilter.value === 'OFFLINE') {
        matchesOperational = !r.is_reachable;
      } else if (operationalFilter.value === 'SSL_MISMATCH') {
        matchesOperational = r.ssl_trust_status === 'FINGERPRINT_MISMATCH';
      }

      return matchesSearch && matchesRole && matchesAdmin && matchesOperational;
    });
  });

  // Columnas reactivas para RgDataTable
  const tableColumns = computed<TableColumn<Record<string, unknown>>[]>(() => [
    { key: 'display_name', label: t('inventory.col_name'), sortable: true },
    {
      key: 'network_role',
      label: t('inventory.col_role'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        if (!r.network_role) return '—';
        return t(`enums.network_role.${r.network_role}`, r.network_role);
      },
    },
    { key: 'ip_address', label: t('inventory.col_ip') },
    {
      key: 'hardware',
      label: t('inventory.col_hardware'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        const model = r.model || (r as any).model_name || r.board_name || 'CHR';
        const arch = r.architecture_name ? ` (${r.architecture_name})` : '';
        return `${model}${arch}`;
      },
    },
    { key: 'serial_number', label: t('inventory.col_serial') },
    { key: 'ros_version', label: t('inventory.col_routeros') },
    {
      key: 'syslog_status',
      label: t('inventory.col_syslog'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        if (r.syslog_active) {
          const count = r.syslog_event_count ? ` (${r.syslog_event_count})` : '';
          return `${t('inventory.syslog_active')}${count}`;
        }
        return t('inventory.syslog_inactive');
      },
    },
    {
      key: 'ssl_trust_status',
      label: t('inventory.col_ssl_tofu'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        return t(`enums.ssl_trust_status.${r.ssl_trust_status}`, r.ssl_trust_status);
      },
    },
    {
      key: 'admin_state',
      label: t('inventory.col_state'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        return t(`enums.admin_state.${r.admin_state}`, r.admin_state);
      },
    },
  ]);

  function openWebFig(routerId: string) {
    router.push(`/routers/${routerId}/webfig/live`);
  }

  function openVaultModal(targetRouter: RouterItem) {
    targetRouterForVault.value = targetRouter;
    isVaultModalOpen.value = true;
  }

  function focusOnMap(routerId: string) {
    selectedRouterId.value = routerId;
    if (currentViewMode.value === 'table') {
      currentViewMode.value = 'split';
    }
  }

  async function triggerDiscovery(targetRouter: RouterItem) {
    actionMessage.value = '';
    actionError.value = '';
    try {
      const res = await http.post<RouterItem>(
        `/api/v1/inventory/routers/${targetRouter.id}/discover`,
      );
      if (res.data) {
        inventoryStore.updateRouter(res.data);
      }
      actionMessage.value = t('inventory.discovery_ok', { name: targetRouter.display_name });
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      actionError.value = error.detail || error.message || 'Error al ejecutar autodescubrimiento.';
    }
  }

  async function handleDeleteRouter(targetRouter: RouterItem) {
    if (
      !confirm(t('inventory.confirm_delete', { name: targetRouter.display_name }))
    ) {
      return;
    }
    actionMessage.value = '';
    actionError.value = '';
    try {
      await http.delete(`/api/v1/inventory/routers/${targetRouter.id}`);
      actionMessage.value = t('inventory.deleted_ok', { name: targetRouter.display_name });
      await inventoryStore.fetchRouters();
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      actionError.value = error.detail || error.message || 'Error al eliminar el router.';
    }
  }

  async function toggleRouterMaintenance(item: RouterItem) {
    const nextState = item.admin_state === 'MAINTENANCE' ? 'PRODUCTION' : 'MAINTENANCE';
    const actionDesc =
      nextState === 'MAINTENANCE' ? 'poner en MANTENIMIENTO' : 'regresar a PRODUCCIÓN';
    if (!confirm(`¿Deseas ${actionDesc} el equipo "${item.display_name}"?`)) return;

    actionMessage.value = '';
    actionError.value = '';
    try {
      await http.put(`/api/v1/inventory/routers/${item.id}`, { admin_state: nextState });
      item.admin_state = nextState as 'PRODUCTION' | 'MAINTENANCE' | 'PROVISIONING' | 'DECOMMISSIONED';
      actionMessage.value = `El router "${item.display_name}" ahora se encuentra en estado ${nextState}.`;
      await inventoryStore.fetchRouters();
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionError.value =
        e.detail || e.message || 'Error al actualizar el estado administrativo del router.';
      setTimeout(() => {
        actionError.value = '';
      }, 4000);
    }
  }

  function handleCsvImported(count: number) {
    actionMessage.value = `Se importaron ${count} routers correctamente. Sincronizando inventario...`;
    inventoryStore.fetchRouters();
    setTimeout(() => {
      actionMessage.value = '';
    }, 4000);
  }

  const isRefreshing = ref(false);
  const isFleetUpdated = ref(false);

  async function handleManualRefresh() {
    isRefreshing.value = true;
    try {
      await inventoryStore.fetchRouters(true);
      isFleetUpdated.value = true;
      setTimeout(() => {
        isFleetUpdated.value = false;
      }, 3500);
    } finally {
      isRefreshing.value = false;
    }
  }

  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    }
    inventoryStore.fetchNetworkRoles();
  });
</script>

<template>
  <div class="inventory-view">
    <header class="inventory-header">
      <div>
        <h1 class="inventory-title">{{ t('inventory.title') }}</h1>
        <p class="inventory-subtitle">
          {{ t('inventory.subtitle') }}
        </p>
      </div>

      <div class="header-actions">
        <!-- Selector de Modos de Vista -->
        <div class="view-mode-toggle" role="group" aria-label="Modo de visualización de inventario">
          <button
            type="button"
            class="btn-toggle"
            :class="{ 'btn-toggle--active': currentViewMode === 'table' }"
            aria-label="Ver solo tabla"
            @click="currentViewMode = 'table'"
          >
            {{ t('inventory.view_table') }}
          </button>
          <button
            type="button"
            class="btn-toggle"
            :class="{ 'btn-toggle--active': currentViewMode === 'split' }"
            aria-label="Ver modo dividido (tabla y mapa)"
            @click="currentViewMode = 'split'"
          >
            {{ t('inventory.view_split') }}
          </button>
          <button
            type="button"
            class="btn-toggle"
            :class="{ 'btn-toggle--active': currentViewMode === 'map' }"
            aria-label="Ver solo mapa geográfico"
            @click="currentViewMode = 'map'"
          >
            {{ t('inventory.view_map') }}
          </button>
        </div>

        <button
          v-if="isVaultAuthorized"
          type="button"
          class="btn-manage-roles"
          aria-label="Personalizar roles de red de equipos"
          @click="isRolesModalOpen = true"
        >
          {{ t('inventory.btn_roles') }}
        </button>

        <button
          type="button"
          class="btn-import-csv"
          aria-label="Abrir asistente de importación CSV"
          @click="isCsvModalOpen = true"
        >
          {{ t('inventory.btn_import_csv') }}
        </button>

        <button
          type="button"
          class="btn-cve-matrix"
          aria-label="Ver matriz de vulnerabilidades CVE"
          @click="router.push('/inventory/cves')"
        >
          {{ t('inventory.btn_cve_matrix') }}
        </button>

        <button
          type="button"
          class="btn-maintenance-windows"
          aria-label="Abrir gestión de ventanas de mantenimiento"
          @click="router.push('/inventory/maintenance-windows')"
        >
          <span class="btn-icon" aria-hidden="true">🛠️</span>
          <span>{{ t('inventory.btn_maintenance_windows', 'Ventanas de Mantenimiento') }}</span>
        </button>

        <button
          type="button"
          class="btn btn-primary"
          :class="{ 'btn-primary--loading': isRefreshing }"
          :disabled="isRefreshing"
          aria-label="Actualizar datos de la flota"
          @click="handleManualRefresh"
        >
          <span v-if="isRefreshing" class="btn-spinner" aria-hidden="true">⏳</span>
          <span v-else class="btn-icon" aria-hidden="true">🔄</span>
          <span>{{ isRefreshing ? t('inventory.btn_refreshing') : t('inventory.btn_refresh') }}</span>
        </button>

        <div v-if="isFleetUpdated" class="status-indicator success" role="status" aria-live="polite">
          <span class="status-icon" aria-hidden="true">✓</span>
          <span class="status-text">{{ t('inventory.updated') }}</span>
        </div>
      </div>
    </header>

    <div v-if="actionMessage" class="banner banner--success" role="status">
      {{ actionMessage }}
    </div>
    <div v-if="actionError" class="banner banner--error" role="alert">
      {{ actionError }}
    </div>

    <!-- Barra de Filtros Accesibles -->
    <div class="filters-bar">
      <div class="filter-item">
        <label for="inv-search" class="filter-label">{{ t('inventory.filter_search_label') }}</label>
        <input
          id="inv-search"
          v-model="searchFilter"
          type="search"
          :placeholder="t('inventory.filter_search_placeholder')"
          class="filter-input"
        />
      </div>

      <div class="filter-item">
        <div class="filter-label-wrap">
          <label for="inv-role" class="filter-label">{{ t('inventory.filter_role_label') }}</label>
          <button
            v-if="isVaultAuthorized"
            type="button"
            class="btn-text-action"
            title="Gestionar roles de red personalizados"
            @click="isRolesModalOpen = true"
          >
            {{ t('inventory.filter_customize') }}
          </button>
        </div>
        <select id="inv-role" v-model="networkRoleFilter" class="filter-select">
          <option value="ALL">{{ t('enums.network_role.ALL') }}</option>
          <option v-for="role in networkRoles" :key="role" :value="role">
            {{ t(`enums.network_role.${role}`, role) }}
          </option>
        </select>
      </div>

      <div class="filter-item">
        <label for="inv-admin-state" class="filter-label">{{ t('inventory.filter_admin_label') }}</label>
        <select id="inv-admin-state" v-model="adminStateFilter" class="filter-select">
          <option value="ALL">{{ t('enums.admin_state.ALL') }}</option>
          <option value="PRODUCTION">{{ t('enums.admin_state.PRODUCTION') }}</option>
          <option value="MAINTENANCE">{{ t('enums.admin_state.MAINTENANCE') }}</option>
          <option value="STAGING_LAB">{{ t('enums.admin_state.STAGING_LAB') }}</option>
          <option value="PROVISIONING">{{ t('enums.admin_state.PROVISIONING') }}</option>
          <option value="DECOMMISSIONED">{{ t('enums.admin_state.DECOMMISSIONED') }}</option>
        </select>
      </div>

      <div class="filter-item">
        <label for="inv-operational" class="filter-label">{{ t('inventory.filter_operational_label') }}</label>
        <select id="inv-operational" v-model="operationalFilter" class="filter-select">
          <option value="ALL">{{ t('enums.operational.ALL') }}</option>
          <option value="ONLINE">{{ t('enums.operational.ONLINE') }}</option>
          <option value="OFFLINE">{{ t('enums.operational.OFFLINE') }}</option>
          <option value="SSL_MISMATCH">{{ t('enums.operational.SSL_MISMATCH') }}</option>
        </select>
      </div>
    </div>

    <!-- Contenido Principal según modo de visualización -->
    <div
      class="inventory-content"
      :class="{
        'inventory-content--split': currentViewMode === 'split',
        'inventory-content--map-only': currentViewMode === 'map',
      }"
    >
      <!-- Panel de Tabla de Inventario -->
      <section
        v-if="currentViewMode !== 'map'"
        class="panel-table"
        aria-label="Tabla de inventario de routers"
      >
        <div class="table-wrapper">
          <RgDataTable
            :columns="tableColumns"
            :rows="filteredRouters as unknown as Record<string, unknown>[]"
            :caption="t('inventory.table_caption')"
            :show-density-toggle="true"
          >
            <template #actions="{ row }">
              <div v-if="row" class="table-row-actions">
                <button
                  type="button"
                  class="btn-row-action btn-row-action--webfig"
                  aria-label="Abrir consola WebFig"
                  @click="openWebFig(String(row.id))"
                >
                  {{ t('inventory.action_webfig') }}
                </button>

                <button
                  type="button"
                  class="btn-row-action btn-row-action--syslog"
                  :class="{ 'btn-row-action--syslog-active': (row as unknown as RouterItem).syslog_active }"
                  :aria-label="`Abrir consola Syslog de ${(row as unknown as RouterItem).display_name}`"
                  @click="router.push(`/routers/${String(row.id)}/webfig/syslog`)"
                >
                  {{ (row as unknown as RouterItem).syslog_active ? t('inventory.action_syslog_active') : t('inventory.action_syslog') }}
                </button>

                <button
                  v-if="(row as unknown as RouterItem).latitude !== undefined"
                  type="button"
                  class="btn-row-action btn-row-action--map"
                  aria-label="Centrar en el mapa"
                  @click="focusOnMap(String(row.id))"
                >
                  {{ t('inventory.action_map') }}
                </button>

                <button
                  v-if="isVaultAuthorized"
                  type="button"
                  class="btn-row-action btn-row-action--vault"
                  aria-label="Consultar Bóveda de credenciales"
                  @click="openVaultModal(row as unknown as RouterItem)"
                >
                  {{ t('inventory.action_vault') }}
                </button>

                <button
                  type="button"
                  class="btn-row-action"
                  :class="(row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? 'btn-row-action--prod' : 'btn-row-action--maint'"
                  :aria-label="((row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? 'Regresar a Producción' : 'Poner en Mantenimiento') + ` ${(row as unknown as RouterItem).display_name}`"
                  @click="toggleRouterMaintenance(row as unknown as RouterItem)"
                >
                  {{ (row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? '🟢 En Servicio' : '🛠️ Mantenimiento' }}
                </button>

                <button
                  type="button"
                  class="btn-row-action btn-row-action--tofu"
                  aria-label="Disparar autodescubrimiento"
                  @click="triggerDiscovery(row as unknown as RouterItem)"
                >
                  {{ t('inventory.action_tofu') }}
                </button>

                <button
                  v-if="isVaultAuthorized"
                  type="button"
                  class="btn-row-action btn-row-action--delete"
                  aria-label="Eliminar router del inventario"
                  @click="handleDeleteRouter(row as unknown as RouterItem)"
                >
                  {{ t('inventory.action_delete') }}
                </button>
              </div>
            </template>
          </RgDataTable>
        </div>
      </section>

      <!-- Panel de Mapa OpenStreetMap -->
      <section
        v-if="currentViewMode !== 'table'"
        class="panel-map"
        aria-label="Mapa interactivo de nodos MikroTik"
      >
        <OsmRouterMap
          :routers="filteredRouters"
          :selected-router-id="selectedRouterId"
          @select-router="(id) => (selectedRouterId = id)"
          @open-webfig="openWebFig"
        />
      </section>
    </div>

    <!-- Modales Auxiliares -->
    <CsvOnboardingWizardModal
      :is-open="isCsvModalOpen"
      @close="isCsvModalOpen = false"
      @imported="handleCsvImported"
    />

    <VaultRevealModal
      :is-open="isVaultModalOpen"
      :router="targetRouterForVault"
      @close="isVaultModalOpen = false"
    />

    <ManageNetworkRolesModal :is-open="isRolesModalOpen" @close="isRolesModalOpen = false" />
  </div>
</template>

<style scoped>
  .inventory-view {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .inventory-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }

  .inventory-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .inventory-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 4px 0 0 0;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .view-mode-toggle {
    display: flex;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    overflow: hidden;
  }

  .btn-toggle {
    background: var(--rg-bg-surface, #111827);
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    padding: 8px 14px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-toggle--active {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    font-weight: 700;
  }

  .btn-import-csv {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-cve-matrix {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fbbf24;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cve-matrix:hover {
    background: rgba(245, 158, 11, 0.25);
    color: #fff;
  }

  .btn-maintenance-windows {
    background: rgba(147, 51, 234, 0.15);
    border: 1px solid #a855f7;
    color: #c084fc;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .btn-maintenance-windows:hover {
    background: rgba(147, 51, 234, 0.25);
    color: #fff;
  }

  .btn-manage-roles {
    background: rgba(14, 165, 233, 0.15);
    border: 1px solid rgba(14, 165, 233, 0.4);
    color: #38bdf8;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    font-family: monospace;
    transition: all 0.2s;
  }

  .btn-manage-roles:hover {
    background: rgba(14, 165, 233, 0.25);
    border-color: #38bdf8;
    color: #fff;
  }

  .filter-label-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .btn-text-action {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.72rem;
    font-family: monospace;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
    opacity: 0.85;
    transition: opacity 0.15s;
  }

  .btn-text-action:hover {
    opacity: 1;
    color: #38bdf8;
  }

  .banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .filters-bar {
    display: flex;
    gap: 12px;
    background: var(--rg-bg-surface, #111827);
    padding: 12px 16px;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    flex-wrap: wrap;
  }

  .filter-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 170px;
  }

  .filter-label {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .filter-input,
  .filter-select {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .inventory-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
    flex: 1;
  }

  .inventory-content--split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  @media (max-width: 1024px) {
    .inventory-content--split {
      grid-template-columns: 1fr;
    }
  }

  .panel-table {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    overflow: hidden;
  }

  .panel-map {
    height: calc(100vh - 230px);
    min-height: 520px;
    max-height: calc(100vh - 180px);
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid var(--rg-border-grid, #1e293b);
  }

  .table-row-actions {
    display: flex;
    gap: 4px;
  }

  .btn-row-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    cursor: pointer;
  }

  .btn-row-action--webfig {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-row-action--syslog {
    border-color: #38bdf8;
    color: #38bdf8;
  }

  .btn-row-action--syslog-active {
    background: rgba(16, 185, 129, 0.2);
    border-color: #10b981;
    color: #34d399;
    font-weight: 600;
  }

  .btn-row-action--vault {
    border-color: #fbbf24;
    color: #fbbf24;
  }

  .btn-row-action--maint {
    border-color: #a855f7;
    color: #c084fc;
  }

  .btn-row-action--maint:hover {
    background: rgba(168, 85, 247, 0.15);
  }

  .btn-row-action--prod {
    border-color: #10b981;
    color: #34d399;
    background: rgba(16, 185, 129, 0.12);
  }

  .btn-row-action--prod:hover {
    background: rgba(16, 185, 129, 0.25);
  }

  .btn-row-action--delete {
    border-color: #ef4444;
    color: #f87171;
  }

  .btn-row-action--delete:hover {
    background: rgba(239, 68, 68, 0.15);
  }

  .btn.btn-primary,
  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn.btn-primary:hover:not(:disabled),
  .btn-primary:hover:not(:disabled) {
    background: rgba(34, 211, 238, 0.25);
    border-color: #38bdf8;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(34, 211, 238, 0.35);
  }

  .btn.btn-primary:active,
  .btn-primary:active {
    transform: scale(0.98);
  }

  .btn.btn-primary:disabled,
  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .status-indicator.success {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 4px;
    background: transparent;
    border: none;
    color: #34d399;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    animation: fadeInScale 0.25s ease-out;
  }

  .status-indicator.success .status-icon {
    font-size: 0.95rem;
    font-weight: 800;
    color: #10b981;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }

  .status-indicator.success .status-text {
    line-height: 1;
  }

  @keyframes fadeInScale {
    from {
      opacity: 0;
      transform: translateY(-2px) scale(0.96);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes pulseGlow {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.5;
      transform: scale(1.2);
    }
  }
</style>
