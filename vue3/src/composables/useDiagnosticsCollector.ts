// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { ref } from 'vue';
import { http } from '@/api/httpClient';

export type DiagnosticEventCategory =
  | 'HTTP_ERROR'
  | 'VUE_EXCEPTION'
  | 'UNHANDLED_REJECTION'
  | 'API_LATENCY'
  | 'MANUAL_NOTE';

export interface UiDiagnosticEventItem {
  timestamp: string;
  category: DiagnosticEventCategory;
  message: string;
  route: string;
  status_code?: number | null;
  url?: string | null;
  latency_ms?: number | null;
}

export interface UiErrorTelemetryRecordResponse {
  recorded: boolean;
  buffered_count: number;
  forwarded_to_siem: boolean;
}

const MAX_RING_BUFFER_ITEMS = 100;
const uiDiagnosticBuffer = ref<UiDiagnosticEventItem[]>([]);
let listenersAttached = false;

function pushDiagnosticEvent(event: Omit<UiDiagnosticEventItem, 'timestamp' | 'route'> & { route?: string }) {
  const currentRoute =
    event.route || (typeof window !== 'undefined' ? window.location.pathname : '/');
  const entry: UiDiagnosticEventItem = {
    timestamp: new Date().toISOString(),
    category: event.category,
    message: String(event.message || 'Unknown UI diagnostic event').slice(0, 1000),
    route: currentRoute,
    status_code: event.status_code ?? null,
    url: event.url ?? null,
    latency_ms: event.latency_ms ?? null,
  };
  uiDiagnosticBuffer.value = [entry, ...uiDiagnosticBuffer.value].slice(0, MAX_RING_BUFFER_ITEMS);
  return entry;
}

function attachGlobalDiagnosticListeners() {
  if (listenersAttached || typeof window === 'undefined') {
    return;
  }
  listenersAttached = true;

  window.addEventListener('rosgrid:api-health-event', (evt: Event) => {
    const custom = evt as CustomEvent<{
      ok: boolean;
      status?: number;
      latencyMs?: number;
      url?: string;
    }>;
    const detail = custom.detail;
    if (
      detail &&
      !detail.ok &&
      !String(detail.url || '').includes('/api/v1/system/diagnostics/ui-error')
    ) {
      const entry = pushDiagnosticEvent({
        category: 'HTTP_ERROR',
        message: `HTTP ${detail.status ?? 0} en ${detail.url ?? '/api'}`,
        status_code: detail.status ?? 0,
        url: detail.url ?? null,
        latency_ms: detail.latencyMs ?? null,
      });
      http.post('/api/v1/system/diagnostics/ui-error', entry).catch(() => {});
    }
  });

  window.addEventListener('error', (evt: ErrorEvent) => {
    if (evt?.message) {
      const entry = pushDiagnosticEvent({
        category: 'VUE_EXCEPTION',
        message: evt.message,
        url: evt.filename || null,
      });
      http.post('/api/v1/system/diagnostics/ui-error', entry).catch(() => {});
    }
  });
}

export function useDiagnosticsCollector() {
  attachGlobalDiagnosticListeners();

  function clearDiagnosticBuffer() {
    uiDiagnosticBuffer.value = [];
  }

  async function reportDiagnosticEventToBackend(item: UiDiagnosticEventItem) {
    const res = await http.post<UiErrorTelemetryRecordResponse>(
      '/api/v1/system/diagnostics/ui-error',
      item,
    );
    return res.data;
  }

  return {
    uiDiagnosticBuffer,
    pushDiagnosticEvent,
    clearDiagnosticBuffer,
    reportDiagnosticEventToBackend,
  };
}
