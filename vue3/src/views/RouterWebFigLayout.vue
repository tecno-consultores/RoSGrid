<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { useRoute, useRouter } from 'vue-router';
  import { useWebFigStore } from '@/stores/useWebFigStore';

  const route = useRoute();
  const router = useRouter();
  const webFigStore = useWebFigStore();

  function handleTabClick(tabId: string): void {
    const tab = webFigStore.openRouterTabs.find((t) => t.tabId === tabId);
    if (tab) {
      webFigStore.activeTabId = tabId;
      router.push({ name: tab.routeName, params: { routerId: route.params.routerId } });
    }
  }
</script>

<template>
  <div class="webfig-layout">
    <!-- Pestañas de Trabajo estilo WinBox/IDE -->
    <header class="webfig-tabs-bar" role="tablist" aria-label="Pestañas de configuración de router">
      <div
        v-for="tab in webFigStore.openRouterTabs"
        :key="tab.tabId"
        class="webfig-tab"
        :class="{ 'webfig-tab--active': webFigStore.activeTabId === tab.tabId }"
        role="tab"
        :aria-selected="webFigStore.activeTabId === tab.tabId"
        tabindex="0"
        @click="handleTabClick(tab.tabId)"
        @keydown.enter="handleTabClick(tab.tabId)"
      >
        <span class="tab-icon" aria-hidden="true">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <button
          v-if="tab.closable"
          type="button"
          class="btn-close-tab"
          aria-label="Cerrar pestaña"
          @click.stop="webFigStore.closeTab(tab.tabId)"
        >
          ✕
        </button>
      </div>
    </header>

    <div class="webfig-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
  .webfig-layout {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .webfig-tabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-surface);
    border-bottom: 1px solid var(--rg-border-panel);
    padding: 4px 8px 0;
    overflow-x: auto;
  }

  .webfig-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-panel);
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    color: var(--rg-text-secondary);
    font-size: 12px;
    cursor: pointer;
    user-select: none;
  }

  .webfig-tab--active {
    background: var(--rg-bg-canvas);
    color: var(--rg-accent-cyan);
    border-top: 2px solid var(--rg-accent-cyan);
    font-weight: 600;
  }

  .btn-close-tab {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 10px;
    cursor: pointer;
  }

  .btn-close-tab:hover {
    color: var(--rg-status-critical);
  }
</style>
