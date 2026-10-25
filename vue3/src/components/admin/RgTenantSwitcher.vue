<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { http } from '@/api/httpClient';

  interface TenantSummary {
    id: string;
    name: string;
    slug: string;
    status: string;
  }

  const authStore = useAuthStore();
  const inventoryStore = useInventoryStore();
  const nocStore = useNocEventsStore();

  const isOpen = ref(false);
  const isLoading = ref(false);
  const isSwitching = ref(false);
  const searchQuery = ref('');
  const tenantsList = ref<TenantSummary[]>([]);
  const containerRef = ref<HTMLElement | null>(null);

  const isSuperAdmin = computed(() => authStore.currentRole === 'SUPERADMIN_GLOBAL');

  const filteredTenants = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return tenantsList.value;
    return tenantsList.value.filter(
      (t) => t.name.toLowerCase().includes(q) || t.slug.toLowerCase().includes(q),
    );
  });

  async function fetchTenants(): Promise<void> {
    if (!isSuperAdmin.value) return;
    isLoading.value = true;
    try {
      const res = await http.get<TenantSummary[]>('/api/v1/tenants');
      tenantsList.value = (res.data || []).filter((t) => t.status === 'ACTIVE');
    } catch {
      // Ignora errores si no hay permisos o fallo de red
    } finally {
      isLoading.value = false;
    }
  }

  function toggleDropdown(): void {
    if (!isSuperAdmin.value) return;
    isOpen.value = !isOpen.value;
    if (isOpen.value && tenantsList.value.length === 0) {
      fetchTenants();
    }
    if (isOpen.value) {
      searchQuery.value = '';
    }
  }

  function closeDropdown(): void {
    isOpen.value = false;
  }

  async function handleSelectTenant(target: TenantSummary): Promise<void> {
    if (target.slug === authStore.tenantSlug || isSwitching.value) {
      closeDropdown();
      return;
    }

    isSwitching.value = true;
    try {
      const success = await authStore.switchTenant(target.id);
      if (success) {
        closeDropdown();
        // Refrescar inventario y telemetría para el nuevo tenant
        await inventoryStore.fetchRouters(true);
        nocStore.fetchRecentAuditLogs(true);
      }
    } finally {
      isSwitching.value = false;
    }
  }

  function onDocumentClick(e: MouseEvent): void {
    if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
      closeDropdown();
    }
  }

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === 'Escape' && isOpen.value) {
      closeDropdown();
    }
  }

  onMounted(() => {
    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onKeydown);
    }
  });

  onBeforeUnmount(() => {
    if (typeof document !== 'undefined') {
      document.removeEventListener('click', onDocumentClick);
      document.removeEventListener('keydown', onKeydown);
    }
  });
</script>

<template>
  <!-- Modo Solo Lectura para Operadores no-SuperAdmin -->
  <div
    v-if="!isSuperAdmin"
    class="tenant-badge"
    :title="`Organización: ${authStore.tenantSlug || 'Predeterminada'}`"
  >
    <strong>{{ authStore.tenantSlug }}</strong>
  </div>

  <!-- Conmutador Interactivo Táctico para SuperAdmin Global -->
  <div v-else ref="containerRef" class="tenant-switcher-wrapper">
    <button
      type="button"
      class="tenant-switcher-btn"
      :class="{ 'tenant-switcher-btn--open': isOpen, 'tenant-switcher-btn--loading': isSwitching }"
      :disabled="isSwitching"
      aria-haspopup="listbox"
      :aria-expanded="isOpen"
      :title="`Organización actual: ${authStore.tenantSlug}. Clic para conmutar de empresa.`"
      @click="toggleDropdown"
    >
      <span class="switcher-icon" aria-hidden="true">🏢</span>
      <strong class="switcher-slug">{{ authStore.tenantSlug }}</strong>
      <span class="switcher-arrow" aria-hidden="true">{{ isSwitching ? '⏳' : isOpen ? '▲' : '▾' }}</span>
    </button>

    <!-- Menú Desplegable Flotante (Tactical NOC Popover) -->
    <transition name="fade-slide">
      <div v-if="isOpen" class="tenant-switcher-popover" role="listbox">
        <div class="popover-header">
          <span class="popover-title">Conmutar Organización</span>
          <span class="popover-badge">SuperAdmin</span>
        </div>

        <div class="popover-search">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="🔍 Buscar empresa..."
            class="search-input"
            autofocus
            @click.stop
          />
        </div>

        <div v-if="isLoading" class="popover-loading">Cargando empresas...</div>

        <ul v-else-if="filteredTenants.length > 0" class="tenant-items-list">
          <li
            v-for="t in filteredTenants"
            :key="t.id"
            class="tenant-option"
            :class="{ 'tenant-option--active': t.slug === authStore.tenantSlug }"
            role="option"
            :aria-selected="t.slug === authStore.tenantSlug"
            @click="handleSelectTenant(t)"
          >
            <span class="option-indicator">{{ t.slug === authStore.tenantSlug ? '●' : '○' }}</span>
            <div class="option-details">
              <span class="option-name">{{ t.name }}</span>
              <span class="option-slug">{{ t.slug }}</span>
            </div>
            <span v-if="t.slug === authStore.tenantSlug" class="active-pill">Actual</span>
          </li>
        </ul>

        <div v-else class="popover-empty">No se encontraron empresas activas</div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
  /* Badge estático idéntico al actual */
  .tenant-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 8px;
    background: rgba(6, 182, 212, 0.1);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 4px;
    color: var(--rg-accent-cyan, #06b6d4);
    font-size: 11px;
    letter-spacing: 0.05em;
    font-family: var(--rg-font-mono, monospace);
  }

  /* Conmutador Táctico */
  .tenant-switcher-wrapper {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .tenant-switcher-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    background: rgba(6, 182, 212, 0.12);
    border: 1px solid rgba(6, 182, 212, 0.35);
    border-radius: 5px;
    color: var(--rg-accent-cyan, #06b6d4);
    font-size: 11px;
    font-family: var(--rg-font-mono, monospace);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .tenant-switcher-btn:hover,
  .tenant-switcher-btn--open {
    background: rgba(6, 182, 212, 0.22);
    border-color: var(--rg-accent-cyan, #06b6d4);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
  }

  .tenant-switcher-btn--loading {
    opacity: 0.7;
    cursor: wait;
  }

  .switcher-icon {
    font-size: 12px;
  }

  .switcher-slug {
    font-weight: 700;
  }

  .switcher-arrow {
    font-size: 9px;
    opacity: 0.8;
  }

  /* Popover Flotante */
  .tenant-switcher-popover {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    width: 280px;
    max-height: 360px;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    z-index: 1000;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .popover-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(6, 182, 212, 0.08);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .popover-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--rg-text-primary, #f1f5f9);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .popover-badge {
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
    font-weight: 700;
    font-family: var(--rg-font-mono, monospace);
  }

  .popover-search {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .search-input {
    width: 100%;
    padding: 5px 8px;
    font-size: 11px;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 4px;
    color: var(--rg-text-primary, #f1f5f9);
    outline: none;
    font-family: inherit;
  }

  .search-input:focus {
    border-color: var(--rg-accent-cyan, #06b6d4);
  }

  .tenant-items-list {
    list-style: none;
    margin: 0;
    padding: 4px 0;
    overflow-y: auto;
    max-height: 240px;
  }

  .tenant-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .tenant-option:hover {
    background: rgba(6, 182, 212, 0.12);
  }

  .tenant-option--active {
    background: rgba(6, 182, 212, 0.18);
  }

  .option-indicator {
    font-size: 10px;
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .option-details {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }

  .option-name {
    font-size: 12px;
    font-weight: 500;
    color: var(--rg-text-primary, #f1f5f9);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .option-slug {
    font-size: 10px;
    color: var(--rg-text-muted, #94a3b8);
    font-family: var(--rg-font-mono, monospace);
  }

  .active-pill {
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    font-weight: 600;
  }

  .popover-loading,
  .popover-empty {
    padding: 16px;
    text-align: center;
    font-size: 11px;
    color: var(--rg-text-muted, #94a3b8);
  }

  /* Animación */
  .fade-slide-enter-active,
  .fade-slide-leave-active {
    transition: opacity 0.15s ease, transform 0.15s ease;
  }

  .fade-slide-enter-from,
  .fade-slide-leave-to {
    opacity: 0;
    transform: translateY(-4px);
  }
</style>
