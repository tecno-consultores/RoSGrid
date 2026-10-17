<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { http } from '@/api/httpClient';
  import type { RouterItem, TableColumn } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import OsmRouterMap from '@/components/inventory/OsmRouterMap.vue';
  import CsvOnboardingWizardModal from '@/components/inventory/CsvOnboardingWizardModal.vue';
  import VaultRevealModal from '@/components/inventory/VaultRevealModal.vue';

  const router = useRouter();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();

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
  const targetRouterForVault = ref<RouterItem | null>(null);

  // Feedback de operaciones
  const actionMessage = ref('');
  const actionError = ref('');

  const networkRoles = [
    'CORE',
    'EDGE_BGP',
    'WAN_BALANCER',
    'BRAS_PPPOE',
    'DISTRIBUTION_SWITCH',
    'TOWER_AP',
    'CORPORATE_CPE',
  ];

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

  // Columnas para RgDataTable
  const tableColumns: TableColumn<Record<string, unknown>>[] = [
    { key: 'display_name', label: 'Nombre / Identity', sortable: true },
    { key: 'network_role', label: 'Rol de Red' },
    { key: 'ip_address', label: 'Dirección IP / Puerto' },
    { key: 'hardware', label: 'Modelo y Arquitectura' },
    { key: 'serial_number', label: 'Serial' },
    { key: 'ros_version', label: 'RouterOS' },
    { key: 'ssl_trust_status', label: 'SSL TOFU' },
    { key: 'admin_state', label: 'Estado' },
  ];

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
      await http.post(`/api/v1/inventory/routers/${targetRouter.id}/discover`);
      actionMessage.value = `Autodescubrimiento TOFU disparado para ${targetRouter.display_name}.`;
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      actionError.value = error.detail || error.message || 'Error al ejecutar autodescubrimiento.';
    }
  }

  async function handleDeleteRouter(targetRouter: RouterItem) {
    if (!confirm(`¿Está seguro de eliminar permanentemente el equipo "${targetRouter.display_name}"?`)) {
      return;
    }
    actionMessage.value = '';
    actionError.value = '';
    try {
      await http.delete(`/api/v1/inventory/routers/${targetRouter.id}`);
      actionMessage.value = `Router "${targetRouter.display_name}" eliminado correctamente.`;
      await inventoryStore.fetchRouters();
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      actionError.value = error.detail || error.message || 'Error al eliminar el router.';
    }
  }

  function handleCsvImported(count: number) {
    actionMessage.value = `Se importaron ${count} routers correctamente. Sincronizando inventario...`;
    inventoryStore.fetchRouters();
    setTimeout(() => {
      actionMessage.value = '';
    }, 4000);
  }

  const isFleetUpdated = ref(false);

  function handleManualRefresh() {
    inventoryStore.fetchRouters();
    isFleetUpdated.value = true;
    setTimeout(() => {
      isFleetUpdated.value = false;
    }, 4000);
  }

  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    }
  });
</script>

<template>
  <div class="inventory-view">
    <header class="inventory-header">
      <div>
        <h1 class="inventory-title">Inventario de Equipos — Flota MikroTik</h1>
        <p class="inventory-subtitle">
          Supervisión de hardware RouterOS v7, mapa geográfico OpenStreetMap y gestión de acceso.
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
            📋 Tabla
          </button>
          <button
            type="button"
            class="btn-toggle"
            :class="{ 'btn-toggle--active': currentViewMode === 'split' }"
            aria-label="Ver modo dividido (tabla y mapa)"
            @click="currentViewMode = 'split'"
          >
            ◫ Dividida
          </button>
          <button
            type="button"
            class="btn-toggle"
            :class="{ 'btn-toggle--active': currentViewMode === 'map' }"
            aria-label="Ver solo mapa geográfico"
            @click="currentViewMode = 'map'"
          >
            🗺 Mapa
          </button>
        </div>

        <button
          type="button"
          class="btn-import-csv"
          aria-label="Abrir asistente de importación CSV"
          @click="isCsvModalOpen = true"
        >
          📂 Importar CSV
        </button>

        <button
          type="button"
          class="btn btn-primary"
          aria-label="Actualizar datos de la flota"
          @click="handleManualRefresh"
        >
          Actualizar Datos
        </button>

        <div v-if="isFleetUpdated" class="status-indicator success" role="status">
          <span class="status-text">Actualizado</span>
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
        <label for="inv-search" class="filter-label">Buscar Router:</label>
        <input
          id="inv-search"
          v-model="searchFilter"
          type="search"
          placeholder="Nombre, identity, IP, serial o modelo..."
          class="filter-input"
        />
      </div>

      <div class="filter-item">
        <label for="inv-role" class="filter-label">Rol en la Red:</label>
        <select id="inv-role" v-model="networkRoleFilter" class="filter-select">
          <option value="ALL">Todos los Roles</option>
          <option v-for="role in networkRoles" :key="role" :value="role">{{ role }}</option>
        </select>
      </div>

      <div class="filter-item">
        <label for="inv-admin-state" class="filter-label">Estado Administrativo:</label>
        <select id="inv-admin-state" v-model="adminStateFilter" class="filter-select">
          <option value="ALL">Todos</option>
          <option value="PRODUCTION">Producción</option>
          <option value="MAINTENANCE">Mantenimiento</option>
          <option value="PROVISIONING">Aprovisionamiento</option>
          <option value="DECOMMISSIONED">Retirado</option>
        </select>
      </div>

      <div class="filter-item">
        <label for="inv-operational" class="filter-label">Salud Operativa:</label>
        <select id="inv-operational" v-model="operationalFilter" class="filter-select">
          <option value="ALL">Todos los Estados</option>
          <option value="ONLINE">Online (Reachable)</option>
          <option value="OFFLINE">Offline / Inalcanzable</option>
          <option value="SSL_MISMATCH">SSL Mismatch</option>
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
            caption="Listado de MikroTiks registrados en RoSGrid"
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
                  📡 WebFig
                </button>

                <button
                  v-if="(row as unknown as RouterItem).latitude !== undefined"
                  type="button"
                  class="btn-row-action btn-row-action--map"
                  aria-label="Centrar en el mapa"
                  @click="focusOnMap(String(row.id))"
                >
                  📍 Mapa
                </button>

                <button
                  v-if="isVaultAuthorized"
                  type="button"
                  class="btn-row-action btn-row-action--vault"
                  aria-label="Consultar Bóveda de credenciales"
                  @click="openVaultModal(row as unknown as RouterItem)"
                >
                  🔐 Bóveda
                </button>

                <button
                  type="button"
                  class="btn-row-action btn-row-action--tofu"
                  aria-label="Disparar autodescubrimiento"
                  @click="triggerDiscovery(row as unknown as RouterItem)"
                >
                  🔍 TOFU
                </button>

                <button
                  v-if="isVaultAuthorized"
                  type="button"
                  class="btn-row-action btn-row-action--delete"
                  aria-label="Eliminar router del inventario"
                  @click="handleDeleteRouter(row as unknown as RouterItem)"
                >
                  🗑️ Eliminar
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

  .btn-row-action--vault {
    border-color: #fbbf24;
    color: #fbbf24;
  }

  .btn-row-action--delete {
    border-color: #ef4444;
    color: #f87171;
  }

  .btn-row-action--delete:hover {
    background: rgba(239, 68, 68, 0.15);
  }

  .status-indicator.success {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 4px;
    color: #34d399;
    font-size: 0.8rem;
    font-weight: 600;
  }
</style>
