// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { resolveUrl } from '@/api/httpClient';

export type ApiHealthStatus = 'online' | 'offline' | 'degraded' | 'checking';

export interface ApiHealthServices {
  database: string;
  redis: string;
}

export interface ApiHeartbeatBroadcastMessage {
  status: ApiHealthStatus;
  latencyMs: number | null;
  lastCheckedIso: string;
  services: ApiHealthServices | null;
}

export const useApiHeartbeatStore = defineStore('apiHeartbeat', () => {
  const status = ref<ApiHealthStatus>('checking');
  const latencyMs = ref<number | null>(null);
  const lastChecked = ref<Date | null>(null);
  const services = ref<ApiHealthServices | null>(null);
  const isChecking = ref<boolean>(false);
  const lastError = ref<string | null>(null);

  let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  let broadcastChannel: BroadcastChannel | null = null;
  let isMonitoringActive = false;

  const isOnline = computed(() => status.value === 'online');
  const isOffline = computed(() => status.value === 'offline');
  const isDegraded = computed(() => status.value === 'degraded');

  // Sincronización entre pestañas del navegador mediante BroadcastChannel
  function initBroadcastChannel(): void {
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      try {
        broadcastChannel = new BroadcastChannel('rosgrid_api_heartbeat');
        broadcastChannel.onmessage = (event: MessageEvent<ApiHeartbeatBroadcastMessage>) => {
          if (event.data && typeof event.data === 'object') {
            status.value = event.data.status;
            latencyMs.value = event.data.latencyMs;
            services.value = event.data.services;
            if (event.data.lastCheckedIso) {
              lastChecked.value = new Date(event.data.lastCheckedIso);
            }
          }
        };
      } catch {
        broadcastChannel = null;
      }
    }
  }

  function broadcastHealthState(): void {
    if (broadcastChannel) {
      try {
        broadcastChannel.postMessage({
          status: status.value,
          latencyMs: latencyMs.value,
          lastCheckedIso: lastChecked.value ? lastChecked.value.toISOString() : new Date().toISOString(),
          services: services.value,
        });
      } catch {
        // Ignorar si el canal está cerrado
      }
    }
  }

  // Ping activo ligero hacia /api/v1/health (con fallback a /health) y timeout estricto de 4s
  async function checkHealth(force = false): Promise<void> {
    if (isChecking.value && !force) return;
    isChecking.value = true;
    lastError.value = null;

    const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const abortController = new AbortController();
    const timeoutId = setTimeout(() => abortController.abort(), 4000);

    try {
      const endpoint = force ? '/api/v1/health?force=true' : '/api/v1/health';
      let url = resolveUrl(endpoint);
      let response = await fetch(url, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: abortController.signal,
      });

      // Si el backend no tiene montado /api/v1/health (fallback a /health)
      if (response.status === 404) {
        const fallbackEndpoint = force ? '/health?force=true' : '/health';
        url = resolveUrl(fallbackEndpoint);
        response = await fetch(url, {
          method: 'GET',
          headers: { Accept: 'application/json' },
          signal: abortController.signal,
        });
      }

      clearTimeout(timeoutId);
      const duration = Math.round(
        (typeof performance !== 'undefined' ? performance.now() : Date.now()) - startTime,
      );

      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error(
          `Respuesta no válida del backend (recibido ${contentType || 'formato no reconocido'}). Se esperaba JSON.`,
        );
      }

      if (response.status === 200) {
        const data = (await response.json()) as {
          status?: string;
          database?: string;
          redis?: string;
        };

        if (data.status === 'unhealthy') {
          status.value = 'degraded';
        } else {
          status.value = 'online';
        }

        latencyMs.value = duration;
        services.value = {
          database: data.database || 'connected',
          redis: data.redis || 'connected',
        };
        lastError.value = null;
      } else if (response.status === 503) {
        let dbStatus = 'disconnected';
        let redisStatus = 'disconnected';
        try {
          const data = (await response.json()) as { database?: string; redis?: string };
          dbStatus = data.database || 'disconnected';
          redisStatus = data.redis || 'disconnected';
        } catch {
          // Fallback a disconnected
        }
        status.value = 'degraded';
        latencyMs.value = duration;
        services.value = { database: dbStatus, redis: redisStatus };
        lastError.value = 'Servicios dependientes (BD o Redis) no disponibles (503)';
      } else {
        status.value = 'offline';
        latencyMs.value = null;
        lastError.value = `HTTP ${response.status}: ${response.statusText}`;
      }
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      status.value = 'offline';
      latencyMs.value = null;
      const errorObj = err as Error;
      if (errorObj?.name === 'AbortError' || errorObj?.message?.includes('aborted')) {
        lastError.value = 'Tiempo de espera agotado (4s) al conectar con la API de RoSGrid.';
      } else if (
        (errorObj?.name === 'TypeError' && errorObj?.message?.includes('fetch')) ||
        errorObj?.message?.toLowerCase().includes('failed to fetch') ||
        errorObj?.message?.toLowerCase().includes('connection refused')
      ) {
        lastError.value = 'No se pudo conectar con el servidor (conexión rechazada o red caída).';
      } else if (errorObj?.message?.includes('JSON') || errorObj?.message?.includes('<!DOCTYPE')) {
        lastError.value = 'Respuesta no válida de la pasarela/API (esperado JSON, recibido HTML).';
      } else {
        lastError.value = errorObj?.message || 'Error desconocido al comprobar el API.';
      }
    } finally {
      isChecking.value = false;
      lastChecked.value = new Date();
      broadcastHealthState();
    }
  }

  // Interceptor pasivo: se actualiza con peticiones normales de la app
  function handleApiActivity(e: Event): void {
    const customEvent = e as CustomEvent<{
      ok?: boolean;
      status?: number;
      latencyMs?: number | null;
      url?: string;
    }>;
    if (!customEvent.detail) return;

    if (customEvent.detail.ok) {
      status.value = 'online';
      if (typeof customEvent.detail.latencyMs === 'number') {
        latencyMs.value = customEvent.detail.latencyMs;
      }
      lastChecked.value = new Date();
      resetIntervalTimer();
    } else if (customEvent.detail.status === 0) {
      status.value = 'offline';
      latencyMs.value = null;
      lastChecked.value = new Date();
    }
  }

  // Manejo de Page Visibility: pausar sondeo si la pestaña está oculta
  function handleVisibilityChange(): void {
    if (typeof document === 'undefined') return;
    if (document.hidden) {
      stopIntervalTimer();
    } else {
      const now = Date.now();
      const last = lastChecked.value ? lastChecked.value.getTime() : 0;
      // Si han pasado más de 45s desde el último chequeo, verificar de inmediato
      if (now - last > 45000) {
        checkHealth();
      }
      startIntervalTimer();
    }
  }

  function startIntervalTimer(intervalMs = 45000): void {
    stopIntervalTimer();
    heartbeatTimer = setInterval(() => {
      checkHealth();
    }, intervalMs);
  }

  function stopIntervalTimer(): void {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  function resetIntervalTimer(intervalMs = 45000): void {
    if (isMonitoringActive && (!document || !document.hidden)) {
      startIntervalTimer(intervalMs);
    }
  }

  function startMonitoring(intervalMs = 45000): void {
    if (isMonitoringActive) return;
    isMonitoringActive = true;

    initBroadcastChannel();

    if (typeof window !== 'undefined') {
      window.addEventListener('rosgrid:api-health-event', handleApiActivity);
    }
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    // Chequeo inicial inmediato y arranque del temporizador en reposo
    checkHealth();
    startIntervalTimer(intervalMs);
  }

  function stopMonitoring(): void {
    isMonitoringActive = false;
    stopIntervalTimer();

    if (typeof window !== 'undefined') {
      window.removeEventListener('rosgrid:api-health-event', handleApiActivity);
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }

    if (broadcastChannel) {
      try {
        broadcastChannel.close();
      } catch {
        // Ignorar
      }
      broadcastChannel = null;
    }
  }

  return {
    status,
    latencyMs,
    lastChecked,
    services,
    isChecking,
    lastError,
    isOnline,
    isOffline,
    isDegraded,
    checkHealth,
    startMonitoring,
    stopMonitoring,
    handleApiActivity,
  };
});
