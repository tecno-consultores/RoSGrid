// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { ref, shallowRef, triggerRef } from 'vue';
import type { NocEventItem } from '@/types';
import { useAuthStore } from './useAuthStore';

export const useNocEventsStore = defineStore('nocEvents', () => {
  const isConnected = ref<boolean>(false);
  const pendingApprovalsCount = ref<number>(0);
  const activeAlertsCount = ref<number>(0);
  const recentEvents = shallowRef<NocEventItem[]>([]);

  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function handleIncomingEvent(rawMessage: string): void {
    try {
      const payload = JSON.parse(rawMessage);
      const eventName = payload.event_name || payload.event || 'UNKNOWN';

      // Intercepción del Kill-Switch en vivo
      if (eventName === 'SESSION_KILLED') {
        const authStore = useAuthStore();
        authStore.forceKillSwitchLogout('Sesión finalizada por el Administrador');
        return;
      }

      if (eventName === 'APPROVAL_NEEDED' || eventName === 'MAKER_CHECKER_REQUESTED') {
        pendingApprovalsCount.value += 1;
      }

      const eventItem: NocEventItem = {
        id: payload.id || crypto.randomUUID(),
        eventName,
        routerId: payload.router_id,
        routerDisplayName: payload.router_display_name,
        severity: payload.severity || 'INFO',
        message: payload.message || payload.detail || `Evento de red: ${eventName}`,
        timestampIso: payload.timestamp_iso || new Date().toISOString(),
      };

      if (eventItem.severity === 'CRITICAL' || eventItem.severity === 'WARNING') {
        activeAlertsCount.value += 1;
      }

      // Mantener últimos 100 eventos en memoria
      const list = [eventItem, ...recentEvents.value].slice(0, 100);
      recentEvents.value = list;
      triggerRef(recentEvents);
    } catch {
      // Ignorar mensajes mal formateados
    }
  }

  function connectEventsWebSocket(wsUrl?: string): void {
    if (typeof window === 'undefined') return;
    if (
      socket &&
      (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const targetUrl = wsUrl || `${protocol}//${window.location.host}/ws/v1/tenant/events`;

    try {
      socket = new WebSocket(targetUrl);

      socket.onopen = () => {
        isConnected.value = true;
      };

      socket.onmessage = (event: MessageEvent) => {
        handleIncomingEvent(event.data);
      };

      socket.onclose = () => {
        isConnected.value = false;
        socket = null;
        // Reintento con backoff
        reconnectTimer = setTimeout(() => {
          connectEventsWebSocket(wsUrl);
        }, 5000);
      };

      socket.onerror = () => {
        isConnected.value = false;
        if (socket) {
          socket.close();
        }
      };
    } catch {
      isConnected.value = false;
    }
  }

  function disconnectEventsWebSocket(): void {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (socket) {
      socket.close();
      socket = null;
    }
    isConnected.value = false;
  }

  function clearEvents(): void {
    recentEvents.value = [];
    activeAlertsCount.value = 0;
    triggerRef(recentEvents);
  }

  return {
    isConnected,
    pendingApprovalsCount,
    activeAlertsCount,
    recentEvents,
    handleIncomingEvent,
    connectEventsWebSocket,
    disconnectEventsWebSocket,
    clearEvents,
  };
});
