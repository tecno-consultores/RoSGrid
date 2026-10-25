<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, onMounted, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
  import RgResponsiveShell from '@/components/common/RgResponsiveShell.vue';
  import TenantOnboardingModal from '@/components/common/TenantOnboardingModal.vue';
  import { useTabLifecycleCoordinator } from '@/composables/useTabLifecycleCoordinator';

  const route = useRoute();
  const authStore = useAuthStore();
  const nocStore = useNocEventsStore();
  const themeStore = useThemeAndLayoutStore();

  useTabLifecycleCoordinator();

  const isLoginRoute = computed(() => route.path === '/login');

  const shouldShowOnboarding = computed(() => {
    if (isLoginRoute.value) return false;
    if (!authStore.isAuthenticated) return false;
    const role = authStore.currentRole;
    const isPrivilegedAdmin = role === 'SUPERADMIN_GLOBAL' || role === 'TENANT_ADMIN';
    if (!isPrivilegedAdmin) return false;
    return authStore.tenantFeatures?.onboarding_completed === false;
  });

  onMounted(() => {
    themeStore.setTheme(themeStore.theme);
    if (authStore.isAuthenticated) {
      nocStore.connectEventsWebSocket();
      authStore.fetchTenantFeatures();
    }
  });

  watch(
    () => authStore.isAuthenticated,
    (isAuth) => {
      if (isAuth) {
        nocStore.connectEventsWebSocket();
        authStore.fetchTenantFeatures();
      } else {
        nocStore.disconnectEventsWebSocket();
      }
    },
  );
</script>

<template>
  <div class="app-root" :class="{ 'app-root--login': isLoginRoute }">
    <router-view v-if="isLoginRoute" />
    <RgResponsiveShell v-else>
      <router-view v-slot="{ Component, route: currentRoute }">
        <transition name="rg-page-fade" mode="out-in">
          <component :is="Component" :key="currentRoute.matched[0]?.path || currentRoute.path" />
        </transition>
      </router-view>
    </RgResponsiveShell>

    <!-- Modal de Onboarding Inicial para Admins -->
    <TenantOnboardingModal
      v-if="shouldShowOnboarding"
      @completed="authStore.fetchTenantFeatures()"
    />
  </div>
</template>

<style>
  .app-root {
    height: 100vh;
    max-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .app-root--login {
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  /* Transición táctica de cambio de pantalla */
  .rg-page-fade-enter-active,
  .rg-page-fade-leave-active {
    transition:
      opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1),
      transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .rg-page-fade-enter-from {
    opacity: 0;
    transform: translateY(6px);
  }

  .rg-page-fade-leave-to {
    opacity: 0;
    transform: translateY(-6px);
  }

  /* Accesibilidad WCAG 2.1 AA - Respetar preferencia de reducción de movimiento */
  @media (prefers-reduced-motion: reduce) {
    .rg-page-fade-enter-active,
    .rg-page-fade-leave-active {
      transition: none !important;
    }
    .rg-page-fade-enter-from,
    .rg-page-fade-leave-to {
      opacity: 1 !important;
      transform: none !important;
    }
  }
</style>
