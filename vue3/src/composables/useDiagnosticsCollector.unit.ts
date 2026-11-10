// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDiagnosticsCollector } from './useDiagnosticsCollector';

const mockPost = vi.fn();

vi.mock('@/api/httpClient', () => ({
  http: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

describe('useDiagnosticsCollector — Ring Buffer de Diagnóstico UI (Spec 72)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPost.mockResolvedValue({
      data: { recorded: true, buffered_count: 1, forwarded_to_siem: false },
    });
    const { clearDiagnosticBuffer } = useDiagnosticsCollector();
    clearDiagnosticBuffer();
  });

  it('agrega eventos al Ring Buffer y permite sincronizarlos con /api/v1/system/diagnostics/ui-error', async () => {
    mockPost.mockResolvedValueOnce({
      data: { recorded: true, buffered_count: 1, forwarded_to_siem: true },
    });

    const { uiDiagnosticBuffer, pushDiagnosticEvent, reportDiagnosticEventToBackend } =
      useDiagnosticsCollector();

    const entry = pushDiagnosticEvent({
      category: 'HTTP_ERROR',
      message: 'HTTP 502 Bad Gateway en /api/v1/routers',
      status_code: 502,
      url: '/api/v1/routers',
      latency_ms: 145,
    });

    expect(uiDiagnosticBuffer.value.length).toBe(1);
    expect(uiDiagnosticBuffer.value[0]?.status_code).toBe(502);

    const response = await reportDiagnosticEventToBackend(entry);
    expect(mockPost).toHaveBeenCalledWith('/api/v1/system/diagnostics/ui-error', entry);
    expect(response.recorded).toBe(true);
    expect(response.forwarded_to_siem).toBe(true);
  });

  it('captura eventos globales rosgrid:api-health-event fallidos automáticamente', () => {
    const { uiDiagnosticBuffer } = useDiagnosticsCollector();
    window.dispatchEvent(
      new CustomEvent('rosgrid:api-health-event', {
        detail: { ok: false, status: 500, latencyMs: 88, url: '/api/v1/inventory/cves' },
      }),
    );
    expect(uiDiagnosticBuffer.value.length).toBe(1);
    expect(uiDiagnosticBuffer.value[0]?.category).toBe('HTTP_ERROR');
  });

  it('no captura eventos rosgrid:api-health-event de la propia ruta de reporte para evitar bucle', () => {
    const { uiDiagnosticBuffer } = useDiagnosticsCollector();
    window.dispatchEvent(
      new CustomEvent('rosgrid:api-health-event', {
        detail: { ok: false, status: 500, latencyMs: 50, url: '/api/v1/system/diagnostics/ui-error' },
      }),
    );
    expect(uiDiagnosticBuffer.value.length).toBe(0);
  });

  it('no envía POST /api/v1/system/diagnostics/ui-error ante errores 401 o de /api/v1/auth/ para evitar tormentas sin sesión', () => {
    const { uiDiagnosticBuffer } = useDiagnosticsCollector();
    window.dispatchEvent(
      new CustomEvent('rosgrid:api-health-event', {
        detail: {
          ok: false,
          status: 401,
          latencyMs: 12,
          url: '/api/v1/auth/2fa/confirm-enrollment',
        },
      }),
    );
    expect(uiDiagnosticBuffer.value.length).toBe(1);
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('captura excepciones globales window error', () => {
    const { uiDiagnosticBuffer } = useDiagnosticsCollector();
    const errorEvent = new ErrorEvent('error', {
      message: 'Uncaught TypeError: Cannot read property of undefined',
      filename: 'RouterInventoryView.vue',
    });
    window.dispatchEvent(errorEvent);
    expect(uiDiagnosticBuffer.value.length).toBe(1);
    expect(uiDiagnosticBuffer.value[0]?.category).toBe('VUE_EXCEPTION');
    expect(uiDiagnosticBuffer.value[0]?.message).toContain('Cannot read property');
  });
});
