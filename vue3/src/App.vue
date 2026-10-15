<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, onMounted, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
  import RgResponsiveShell from '@/components/common/RgResponsiveShell.vue';

  const route = useRoute();
  const authStore = useAuthStore();
  const nocStore = useNocEventsStore();
  const themeStore = useThemeAndLayoutStore();

  const isLoginRoute = computed(() => route.path === '/login');

  onMounted(() => {
    themeStore.setTheme(themeStore.theme);
    if (authStore.isAuthenticated) {
      nocStore.connectEventsWebSocket();
    }
  });

  watch(
    () => authStore.isAuthenticated,
    (isAuth) => {
      if (isAuth) {
        nocStore.connectEventsWebSocket();
      } else {
        nocStore.disconnectEventsWebSocket();
      }
    },
  );
</script>

<template>
  <div class="app-root">
    <router-view v-if="isLoginRoute" />
    <RgResponsiveShell v-else>
      <router-view />
    </RgResponsiveShell>
  </div>
</template>

<style>
  .app-root {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
</style>
