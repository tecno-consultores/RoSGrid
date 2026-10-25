<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted, computed } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import { useAuthStore, defaultTenantFeatures } from '@/stores/useAuthStore';
  import type { TenantFeatureFlags } from '@/types';
  import RgFeatureFlagsGrid from '@/components/admin/RgFeatureFlagsGrid.vue';

  const { t } = useI18n();

  interface TenantItem {
    id: string;
    name: string;
    slug: string;
    status: string;
    features?: TenantFeatureFlags;
  }

  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();

  const tenantId = computed(() => String(route.params.tenantId || ''));
  const currentTenant = ref<TenantItem | null>(null);
  const tenantFeatures = ref<TenantFeatureFlags>({ ...defaultTenantFeatures });
  const isLoading = ref(true);
  const isSaving = ref(false);
  const saveSuccessMessage = ref('');
  const errorMessage = ref('');

  async function loadTenantData(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      // 1. Cargar lista de tenants para obtener metadatos del tenant actual
      const tenantsRes = await http.get<TenantItem[]>('/api/v1/tenants');
      const found = (tenantsRes.data || []).find((t) => t.id === tenantId.value);
      if (found) {
        currentTenant.value = found;
      }

      // 2. Cargar features del tenant
      const featRes = await http.get<TenantFeatureFlags>(`/api/v1/tenants/${tenantId.value}/features`);
      tenantFeatures.value = { ...defaultTenantFeatures, ...(featRes.data || {}) };
    } catch {
      errorMessage.value = 'No se pudieron cargar los datos y capacidades de la empresa.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleSaveFeatures(): Promise<void> {
    isSaving.value = true;
    saveSuccessMessage.value = '';
    errorMessage.value = '';
    try {
      const res = await http.patch<TenantFeatureFlags>(
        `/api/v1/tenants/${tenantId.value}/features`,
        tenantFeatures.value,
      );
      tenantFeatures.value = { ...defaultTenantFeatures, ...(res.data || tenantFeatures.value) };

      // Si el tenant editado es el tenant activo del usuario actual, sincronizar authStore
      if (authStore.user?.tenant_id === tenantId.value) {
        authStore.updateTenantFeatures(tenantFeatures.value);
      }

      saveSuccessMessage.value = 'Capacidades y módulos guardados exitosamente.';
      setTimeout(() => {
        saveSuccessMessage.value = '';
      }, 4000);
    } catch {
      errorMessage.value = 'Error al guardar los cambios de módulos del tenant.';
    } finally {
      isSaving.value = false;
    }
  }

  function goBack(): void {
    router.push('/admin/tenants');
  }

  onMounted(() => {
    loadTenantData();
  });
</script>

<template>
  <div class="tenant-modules-studio">
    <!-- Barra de Navegación Superior y Breadcrumbs -->
    <header class="studio-header">
      <div class="breadcrumbs">
        <router-link to="/admin/tenants" class="breadcrumb-link">
          Empresas (Tenants)
        </router-link>
        <span class="breadcrumb-sep">❯</span>
        <span class="breadcrumb-current">{{ currentTenant?.name || tenantId }}</span>
        <span class="breadcrumb-sep">❯</span>
        <span class="breadcrumb-leaf">⚙️ Módulos & Capacidades</span>
      </div>

      <div class="header-actions">
        <button type="button" class="btn-back" @click="goBack">
          {{ t('tenants_mgmt.studio_back', '⬅ Volver a Empresas') }}
        </button>
      </div>
    </header>

    <!-- Notificaciones en Pantalla -->
    <div v-if="saveSuccessMessage" class="feedback-banner feedback-banner--success" role="alert">
      ✔ {{ saveSuccessMessage }}
    </div>
    <div v-if="errorMessage" class="feedback-banner feedback-banner--error" role="alert">
      ✖ {{ errorMessage }}
    </div>

    <!-- Contenido Principal -->
    <div v-if="isLoading" class="loading-state">
      <span class="spinner" aria-hidden="true">⏳</span>
      <p>{{ t('tenants_mgmt.studio_loading', 'Cargando capacidades de la empresa...') }}</p>
    </div>

    <main v-else class="studio-main-content">
      <RgFeatureFlagsGrid
        v-model="tenantFeatures"
        :is-saving="isSaving"
        :tenant-name="currentTenant?.name || currentTenant?.slug"
        @save="handleSaveFeatures"
      />
    </main>
  </div>
</template>

<style scoped>
  .tenant-modules-studio {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-bottom: 24px;
  }

  .studio-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, #1e293b);
    border-radius: 8px;
    padding: 12px 18px;
  }

  .breadcrumbs {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .breadcrumb-link {
    color: var(--rg-accent-cyan, #06b6d4);
    text-decoration: none;
    font-weight: 500;
  }

  .breadcrumb-link:hover {
    text-decoration: underline;
  }

  .breadcrumb-sep {
    color: var(--rg-text-muted, #94a3b8);
    font-size: 11px;
  }

  .breadcrumb-current {
    color: var(--rg-text-primary, #f1f5f9);
    font-weight: 600;
  }

  .breadcrumb-leaf {
    color: var(--rg-text-muted, #94a3b8);
  }

  .btn-back {
    padding: 6px 14px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 6px;
    color: var(--rg-text-primary, #f1f5f9);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-back:hover {
    background: rgba(6, 182, 212, 0.15);
    border-color: var(--rg-accent-cyan, #06b6d4);
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .feedback-banner {
    padding: 10px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
  }

  .feedback-banner--success {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.4);
    color: #22c55e;
  }

  .feedback-banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #ef4444;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px;
    gap: 12px;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 13px;
  }

  .spinner {
    font-size: 28px;
  }

  .studio-main-content {
    display: flex;
    flex-direction: column;
  }
</style>
