<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { useRoute, useRouter } from 'vue-router';
  import { useWebFigStore } from '@/stores/useWebFigStore';

  const props = defineProps<{
    routerId: string;
  }>();

  const emit = defineEmits<{
    (e: 'toggle-sidebar'): void;
  }>();

  const route = useRoute();
  const router = useRouter();
  const webFigStore = useWebFigStore();

  function handleTabClick(tabId: string): void {
    const tab = webFigStore.openRouterTabs.find((t) => t.tabId === tabId);
    if (tab) {
      webFigStore.activeTabId = tabId;
      router.push({
        name: tab.routeName,
        params: { routerId: props.routerId },
      });
    }
  }

  function handleCloseTab(tabId: string): void {
    webFigStore.closeTab(tabId);
    // Navegar a la pestaña activa tras el cierre
    const active = webFigStore.openRouterTabs.find((t) => t.tabId === webFigStore.activeTabId);
    if (active) {
      router.push({
        name: active.routeName,
        params: { routerId: props.routerId },
      });
    }
  }

  function navigateQuick(path: string): void {
    router.push(`/routers/${props.routerId}/webfig/${path}`);
  }
</script>

<template>
  <div class="workspace-tabs-container">
    <!-- Pestañas Desktop / Tablet (>= 768px) y Swipeable Pills (< 768px) -->
    <nav
      class="webfig-tabs-bar"
      role="tablist"
      aria-label="Pestañas de trabajo abiertas del router (máximo 5 en RAM)"
    >
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
        <span class="tab-icon" aria-hidden="true">{{ tab.icon || '📄' }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <button
          v-if="tab.closable"
          type="button"
          class="btn-close-tab"
          :aria-label="`Cerrar pestaña ${tab.label}`"
          @click.stop="handleCloseTab(tab.tabId)"
        >
          ✕
        </button>
      </div>
    </nav>

    <!-- Barra Inferior Fija para Móviles (< 768px) -->
    <nav class="mobile-bottom-bar" aria-label="Navegación rápida móvil de WebFig">
      <button
        type="button"
        class="bottom-bar-btn"
        :class="{ 'bottom-bar-btn--active': route.path.includes('/webfig/live') }"
        aria-label="Ir a Dashboard en Vivo"
        @click="navigateQuick('live')"
      >
        <span class="btn-icon">📊</span>
        <span class="btn-text">Vivo</span>
      </button>

      <button
        type="button"
        class="bottom-bar-btn"
        :class="{ 'bottom-bar-btn--active': route.path.includes('/webfig/interfaces') }"
        aria-label="Ir a Interfaces y SFP"
        @click="navigateQuick('interfaces')"
      >
        <span class="btn-icon">🔌</span>
        <span class="btn-text">SFP/Red</span>
      </button>

      <button
        type="button"
        class="bottom-bar-btn"
        :class="{ 'bottom-bar-btn--active': route.path.includes('/webfig/ppp') }"
        aria-label="Ir a PPP y Colas"
        @click="navigateQuick('ppp')"
      >
        <span class="btn-icon">⚡</span>
        <span class="btn-text">PPP</span>
      </button>

      <button
        type="button"
        class="bottom-bar-btn"
        :class="{ 'bottom-bar-btn--active': route.path.includes('/webfig/tools') }"
        aria-label="Ir a Herramientas y Diagnóstico"
        @click="navigateQuick('tools')"
      >
        <span class="btn-icon">🛠️</span>
        <span class="btn-text">Tools</span>
      </button>

      <button
        type="button"
        class="bottom-bar-btn btn-menu-toggle"
        aria-label="Abrir menú completo de módulos RouterOS"
        @click="emit('toggle-sidebar')"
      >
        <span class="btn-icon">☰</span>
        <span class="btn-text">Menú</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
  .workspace-tabs-container {
    width: 100%;
  }

  .webfig-tabs-bar {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 6px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    overflow-x: auto;
    white-space: nowrap;
    scrollbar-width: thin;
  }

  .webfig-tab {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: var(--rg-bg-surface);
    border: 1px solid transparent;
    border-radius: 5px;
    color: var(--rg-text-secondary);
    font-size: 0.85rem;
    cursor: pointer;
    user-select: none;
    transition: all 0.15s ease;
  }

  .webfig-tab:hover {
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
  }

  .webfig-tab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    border-color: var(--rg-border-grid);
    border-bottom: 2px solid var(--rg-accent-cyan);
    font-weight: 600;
  }

  .btn-close-tab {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 0.75rem;
    padding: 2px 4px;
    border-radius: 3px;
    cursor: pointer;
    line-height: 1;
  }

  .btn-close-tab:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  /* Barra inferior móvil */
  .mobile-bottom-bar {
    display: none;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: var(--rg-bg-surface);
    border-top: 1px solid var(--rg-border-grid);
    z-index: 100;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
  }

  .bottom-bar-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    min-height: 44px;
    cursor: pointer;
  }

  .bottom-bar-btn--active {
    color: var(--rg-accent-cyan);
  }

  .btn-icon {
    font-size: 1.15rem;
    line-height: 1;
  }

  .btn-text {
    font-size: 0.65rem;
    margin-top: 2px;
  }

  @media (max-width: 768px) {
    .webfig-tabs-bar {
      padding: 6px;
      gap: 6px;
    }

    .webfig-tab {
      padding: 6px 12px;
      font-size: 0.8rem;
    }

    .mobile-bottom-bar {
      display: flex;
    }

    .workspace-tabs-container {
      margin-bottom: 60px;
    }
  }
</style>
