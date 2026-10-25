// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

/**
 * useTabLifecycleCoordinator
 *
 * Coordinador de ciclo de vida multi-pestaña (Hito 23.27).
 * Detecta el cierre de la última pestaña o ventana del navegador y despacha
 * de manera fiable una notificación efímera al backend (/api/v1/auth/session-closing)
 * mediante navigator.sendBeacon con fallback a fetch(..., { keepalive: true }).
 */

import { onMounted, onUnmounted, ref } from 'vue';
import { useAuthStore } from '@/stores/useAuthStore';

interface TabLifecycleMessage {
  type: 'TAB_PING' | 'TAB_PONG' | 'TAB_CLOSING';
  tabId: string;
  timestamp: number;
}

const BROADCAST_CHANNEL_NAME = 'rosgrid_tab_lifecycle_bus';
const PING_INTERVAL_MS = 5000;
const TAB_TIMEOUT_MS = 12000;

export function useTabLifecycleCoordinator() {
  const authStore = useAuthStore();
  const currentTabId = ref<string>(
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `tab-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  );

  const initialMap = new Map<string, number>();
  initialMap.set(currentTabId.value, Date.now());
  const activeTabs = ref<Map<string, number>>(initialMap);
  let channel: BroadcastChannel | null = null;
  let pingTimer: ReturnType<typeof setInterval> | null = null;
  let cleanupTimer: ReturnType<typeof setInterval> | null = null;

  function pruneStaleTabs(): void {
    const now = Date.now();
    for (const [id, lastSeen] of activeTabs.value.entries()) {
      if (id !== currentTabId.value && now - lastSeen > TAB_TIMEOUT_MS) {
        activeTabs.value.delete(id);
      }
    }
  }

  function broadcast(msg: TabLifecycleMessage): void {
    try {
      if (channel) {
        channel.postMessage(msg);
      }
    } catch {
      // Ignorar errores en navegadores con sandbox restringido
    }
  }

  function handleMessage(event: MessageEvent<TabLifecycleMessage>): void {
    const data = event.data;
    if (!data || !data.type || !data.tabId) return;

    if (data.tabId === currentTabId.value) return;

    if (data.type === 'TAB_PING') {
      activeTabs.value.set(data.tabId, Date.now());
      // Responder con pong para anunciar existencia
      broadcast({
        type: 'TAB_PONG',
        tabId: currentTabId.value,
        timestamp: Date.now(),
      });
    } else if (data.type === 'TAB_PONG') {
      activeTabs.value.set(data.tabId, Date.now());
    } else if (data.type === 'TAB_CLOSING') {
      activeTabs.value.delete(data.tabId);
    }
  }

  function dispatchSessionClosingBeacon(): void {
    // Si no está autenticado o no hay session_id en el store, no se notifica
    const storeRecord = authStore as unknown as Record<string, unknown>;
    const tokenPayload = storeRecord.tokenPayload as Record<string, unknown> | undefined;
    const sessionId = authStore.user?.id
      ? String(storeRecord.sessionId || tokenPayload?.sid || '')
      : '';

    // Enviar petición a /api/v1/auth/session-closing
    const payload = JSON.stringify({
      session_id: sessionId || 'current',
      client_timestamp: Date.now(),
    });

    const endpoint = '/api/v1/auth/session-closing';
    let beaconSent = false;

    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      try {
        const blob = new Blob([payload], { type: 'application/json' });
        beaconSent = navigator.sendBeacon(endpoint, blob);
      } catch {
        beaconSent = false;
      }
    }

    if (!beaconSent && typeof fetch === 'function') {
      try {
        fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: payload,
          keepalive: true,
          credentials: 'include',
        }).catch(() => {});
      } catch {
        // Ignorar fallos finales durante cierre
      }
    }
  }

  function handlePageClose(): void {
    pruneStaleTabs();
    activeTabs.value.delete(currentTabId.value);

    // Si no quedan más pestañas activas de la misma aplicación
    const otherActiveTabs = Array.from(activeTabs.value.keys()).filter(
      (id) => id !== currentTabId.value,
    );

    if (otherActiveTabs.length === 0 && authStore.isAuthenticated) {
      dispatchSessionClosingBeacon();
    } else {
      broadcast({
        type: 'TAB_CLOSING',
        tabId: currentTabId.value,
        timestamp: Date.now(),
      });
    }
  }

  onMounted(() => {
    activeTabs.value.set(currentTabId.value, Date.now());

    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      try {
        channel = new BroadcastChannel(BROADCAST_CHANNEL_NAME);
        channel.onmessage = handleMessage;
      } catch {
        channel = null;
      }
    }

    // Emitir ping inicial
    broadcast({
      type: 'TAB_PING',
      tabId: currentTabId.value,
      timestamp: Date.now(),
    });

    // Pings periódicos
    pingTimer = setInterval(() => {
      broadcast({
        type: 'TAB_PING',
        tabId: currentTabId.value,
        timestamp: Date.now(),
      });
      activeTabs.value.set(currentTabId.value, Date.now());
    }, PING_INTERVAL_MS);

    cleanupTimer = setInterval(() => {
      pruneStaleTabs();
    }, TAB_TIMEOUT_MS);

    if (typeof window !== 'undefined') {
      window.addEventListener('pagehide', handlePageClose);
      window.addEventListener('beforeunload', handlePageClose);
    }
  });

  onUnmounted(() => {
    if (pingTimer) clearInterval(pingTimer);
    if (cleanupTimer) clearInterval(cleanupTimer);

    if (typeof window !== 'undefined') {
      window.removeEventListener('pagehide', handlePageClose);
      window.removeEventListener('beforeunload', handlePageClose);
    }

    if (channel) {
      channel.close();
      channel = null;
    }
  });

  return {
    currentTabId,
    activeTabs,
    dispatchSessionClosingBeacon,
    handlePageClose,
  };
}
