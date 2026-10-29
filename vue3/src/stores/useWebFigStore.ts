// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { ref, shallowRef, triggerRef } from 'vue';
import type { RouterItem, RouterTabItem } from '@/types';

export const MAX_OPEN_TABS = 5;

const DEFAULT_DASHBOARD_TAB: RouterTabItem = {
  tabId: 'RouterLiveDashboard',
  routeName: 'RouterLiveDashboard',
  label: 'Dashboard en Vivo',
  icon: '📊',
  closable: false,
};

export const useWebFigStore = defineStore('webfig', () => {
  const currentRouter = shallowRef<RouterItem | null>(null);

  // Cola FIFO/LRU de hasta 5 pestañas activas
  const openRouterTabs = ref<RouterTabItem[]>([DEFAULT_DASHBOARD_TAB]);
  const activeTabId = ref<string>('RouterLiveDashboard');

  // Estado Safe Mode (Dead Man's Switch a 60s) & Gobernanza Maker-Checker (En Espera)
  const isSafeModeActive = ref<boolean>(false);
  const safeModeCountdownSeconds = ref<number>(60);
  const isMakerCheckerPending = ref<boolean>(false);
  const makerCheckerMessage = ref<string>('');
  const makerCheckerApprovalId = ref<string | null>(null);
  let safeModeTimer: ReturnType<typeof setInterval> | null = null;

  function setCurrentRouter(router: RouterItem | null): void {
    currentRouter.value = router;
    triggerRef(currentRouter);
  }

  function openOrFocusTab(tab: RouterTabItem): void {
    const existingIndex = openRouterTabs.value.findIndex(
      (t) =>
        t.tabId === tab.tabId ||
        (t.routeName === tab.routeName && t.routeName === 'RouterLiveDashboard'),
    );
    if (existingIndex !== -1) {
      activeTabId.value = openRouterTabs.value[existingIndex].tabId;
      return;
    }

    // Si excede el límite máximo (5 pestañas), expulsar la primera pestaña cerrable (FIFO)
    if (openRouterTabs.value.length >= MAX_OPEN_TABS) {
      const closableIndex = openRouterTabs.value.findIndex((t) => t.closable);
      if (closableIndex !== -1) {
        openRouterTabs.value.splice(closableIndex, 1);
      }
    }

    openRouterTabs.value.push(tab);
    activeTabId.value = tab.tabId;
  }

  function closeTab(tabId: string): void {
    const idx = openRouterTabs.value.findIndex((t) => t.tabId === tabId);
    if (idx === -1) return;

    const tab = openRouterTabs.value[idx];
    if (!tab.closable) return;

    openRouterTabs.value.splice(idx, 1);

    // Si la pestaña cerrada era la activa, enfocar la anterior o el Dashboard
    if (activeTabId.value === tabId) {
      const nextTab = openRouterTabs.value[Math.max(0, idx - 1)];
      activeTabId.value = nextTab ? nextTab.tabId : DEFAULT_DASHBOARD_TAB.tabId;
    }
  }

  function startSafeModeCountdown(initialSeconds = 60): void {
    isMakerCheckerPending.value = false;
    makerCheckerMessage.value = '';
    makerCheckerApprovalId.value = null;
    isSafeModeActive.value = true;
    safeModeCountdownSeconds.value = initialSeconds;

    if (safeModeTimer) {
      clearInterval(safeModeTimer);
    }

    safeModeTimer = setInterval(() => {
      if (safeModeCountdownSeconds.value > 0) {
        safeModeCountdownSeconds.value -= 1;
      } else {
        stopSafeMode();
      }
    }, 1000);
  }

  function stopSafeMode(): void {
    isSafeModeActive.value = false;
    safeModeCountdownSeconds.value = 60;
    if (safeModeTimer) {
      clearInterval(safeModeTimer);
      safeModeTimer = null;
    }
  }

  function notifyMakerCheckerPending(message?: string, approvalId?: string | null): void {
    stopSafeMode();
    isMakerCheckerPending.value = true;
    makerCheckerMessage.value =
      message ||
      'Operación enviada a Maker-Checker. En espera de aprobación humana por Nivel 3, Supervisor o Administrador (sin cuenta regresiva de 60s).';
    makerCheckerApprovalId.value = approvalId || null;
  }

  function dismissMakerCheckerPending(): void {
    isMakerCheckerPending.value = false;
    makerCheckerMessage.value = '';
    makerCheckerApprovalId.value = null;
  }

  function handleMutationResponse(res: unknown, fallbackSeconds = 60): boolean {
    const r = res as {
      status?: number;
      isMakerCheckerIntercepted?: boolean;
      data?: { status?: string; detail?: string; approval_request_id?: string };
    } | null;
    const isIntercepted =
      r?.status === 202 ||
      r?.isMakerCheckerIntercepted === true ||
      r?.data?.status === 'INTERCEPTED_FOR_APPROVAL';

    if (isIntercepted) {
      notifyMakerCheckerPending(r?.data?.detail, r?.data?.approval_request_id);
      return true;
    }

    dismissMakerCheckerPending();
    startSafeModeCountdown(fallbackSeconds);
    return false;
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('rosgrid:maker-checker-intercepted', ((ev: CustomEvent) => {
      const detail = ev?.detail as { detail?: string; approval_request_id?: string } | undefined;
      notifyMakerCheckerPending(detail?.detail, detail?.approval_request_id);
    }) as EventListener);

    window.addEventListener('rosgrid:mutation-failed', () => {
      stopSafeMode();
    });
  }

  function clearRouterWorkspace(): void {
    currentRouter.value = null;
    triggerRef(currentRouter);
    openRouterTabs.value = [DEFAULT_DASHBOARD_TAB];
    activeTabId.value = DEFAULT_DASHBOARD_TAB.tabId;
    stopSafeMode();
    dismissMakerCheckerPending();
  }

  return {
    currentRouter,
    openRouterTabs,
    activeTabId,
    isSafeModeActive,
    safeModeCountdownSeconds,
    isMakerCheckerPending,
    makerCheckerMessage,
    makerCheckerApprovalId,
    setCurrentRouter,
    openOrFocusTab,
    closeTab,
    startSafeModeCountdown,
    stopSafeMode,
    notifyMakerCheckerPending,
    dismissMakerCheckerPending,
    handleMutationResponse,
    clearRouterWorkspace,
  };
});
