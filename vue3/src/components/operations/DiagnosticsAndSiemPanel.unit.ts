// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import DiagnosticsAndSiemPanel from './DiagnosticsAndSiemPanel.vue';

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPut = vi.fn();

vi.mock('@/api/httpClient', () => ({
  http: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
  },
}));

describe('DiagnosticsAndSiemPanel.vue — Paquete 1-Click y SIEM del ISP (Spec 72)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({
      data: {
        enabled: false,
        protocol: 'GELF_UDP',
        host: '10.20.30.40',
        port: 12201,
        endpoint_path: '/gelf',
        use_tls: false,
        min_level: 'WARNING',
        include_frontend_errors: true,
        include_audit_events: true,
        custom_stream_label: 'rosgrid-isp-noc',
        has_auth_token: false,
        updated_at: null,
      },
    });
  });

  it('carga la configuración SIEM al montar y permite generar el paquete .zip de soporte', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        filename: 'rosgrid-support-bundle-20261103.zip',
        format: 'zip',
        content_type: 'application/zip',
        size_bytes: 2048,
        redacted_secrets_count: 3,
        included_files: ['metadata.json', 'frontend/ui_errors.json', 'backend/application_logs.log'],
        generated_at: '2026-11-03T22:00:00Z',
        bundle_base64: 'UEsDBAoAAAAAA==',
      },
    });

    const wrapper = mount(DiagnosticsAndSiemPanel);
    await flushPromises();

    expect(mockGet).toHaveBeenCalledWith('/api/v1/system/siem-config');

    await wrapper.find('#btn-download-support-bundle').trigger('click');
    await flushPromises();

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/system/diagnostics/bundle',
      expect.objectContaining({ format: 'zip', log_lines_limit: 500 }),
    );
    expect(wrapper.find('[data-testid="bundle-summary"]').text()).toContain(
      'rosgrid-support-bundle-20261103.zip',
    );
  });

  it('guarda la configuración del conector SIEM y ejecuta la prueba de envío', async () => {
    mockPut.mockResolvedValueOnce({
      data: {
        enabled: true,
        protocol: 'LOKI_HTTP',
        host: 'loki.isp.local',
        port: 3100,
        endpoint_path: '/loki/api/v1/push',
        use_tls: false,
        min_level: 'ERROR',
        include_frontend_errors: true,
        include_audit_events: true,
        custom_stream_label: 'rosgrid-isp-noc',
        has_auth_token: true,
        updated_at: '2026-11-03T22:05:00Z',
      },
    });
    mockPost.mockResolvedValueOnce({
      data: {
        success: true,
        protocol: 'LOKI_HTTP',
        target: 'http://loki.isp.local:3100/loki/api/v1/push',
        latency_ms: 12.4,
        detail: 'Evento de prueba entregado exitosamente',
      },
    });

    const wrapper = mount(DiagnosticsAndSiemPanel);
    await flushPromises();

    await wrapper.find('#siem-protocol-select').setValue('LOKI_HTTP');
    await wrapper.find('#btn-save-siem-config').trigger('click');
    await flushPromises();

    expect(mockPut).toHaveBeenCalledWith(
      '/api/v1/system/siem-config',
      expect.objectContaining({ protocol: 'LOKI_HTTP' }),
    );

    await wrapper.find('#btn-test-siem-config').trigger('click');
    await flushPromises();

    expect(mockPost).toHaveBeenCalledWith('/api/v1/system/siem-config/test', {});
    expect(wrapper.find('[data-testid="siem-test-summary"]').text()).toContain('12.4 ms');
  });
});
