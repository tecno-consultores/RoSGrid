// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import TenantModulesAuditTab from './TenantModulesAuditTab.vue';
import { http } from '@/api/httpClient';

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
  },
}));

describe('TenantModulesAuditTab.vue — Historial Forense WORM de Módulos (Hito 26.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza estado de carga inicial y consulta el endpoint de auditoría del tenant', async () => {
    vi.mocked(http.get).mockImplementation(() => new Promise(() => {})); // Suspended promise

    const wrapper = mount(TenantModulesAuditTab, {
      props: {
        tenantId: '11111111-2222-3333-4444-555555555555',
      },
    });

    expect(wrapper.find('.spinner').exists()).toBe(true);
    expect(wrapper.text()).toContain('Cargando');
    expect(http.get).toHaveBeenCalledWith(
      '/api/v1/tenants/11111111-2222-3333-4444-555555555555/features/audit?limit=30',
    );
  });

  it('muestra la lista de modificaciones y formatea el diff de flags correctamente', async () => {
    const mockRecords = [
      {
        id: 'rec-001',
        created_at: '2026-10-25T14:30:00Z',
        actor_username: 'superadmin',
        actor_role: 'SUPERADMIN_GLOBAL',
        actor_ip: '192.168.1.100',
        event_category: 'GOVERNANCE',
        event_action: 'TENANT_FEATURE_FLAGS_UPDATED',
        status_code: 200,
        before_state: {
          isp_module_enabled: false,
          bgp_looking_glass_enabled: false,
        },
        after_state: {
          isp_module_enabled: true,
          bgp_looking_glass_enabled: true,
        },
        record_sha256_hash: 'hash-abc-123',
      },
    ];

    vi.mocked(http.get).mockResolvedValueOnce({ data: mockRecords } as any);

    const wrapper = mount(TenantModulesAuditTab, {
      props: {
        tenantId: '11111111-2222-3333-4444-555555555555',
      },
    });

    await flushPromises();

    expect(wrapper.find('.audit-table').exists()).toBe(true);
    expect(wrapper.text()).toContain('@superadmin');
    expect(wrapper.text()).toContain('SUPERADMIN_GLOBAL');
    expect(wrapper.text()).toContain('192.168.1.100');
    expect(wrapper.text()).toContain('isp module: OFF ➔ ON');
    expect(wrapper.text()).toContain('bgp looking glass: OFF ➔ ON');
    expect(wrapper.find('.btn-rollback').exists()).toBe(true);
  });

  it('emite rollback con before_state al pulsar el botón "Cargar esta versión"', async () => {
    const mockRecords = [
      {
        id: 'rec-002',
        created_at: '2026-10-25T14:35:00Z',
        actor_username: 'superadmin',
        actor_role: 'SUPERADMIN_GLOBAL',
        actor_ip: '10.0.0.1',
        event_category: 'GOVERNANCE',
        event_action: 'TENANT_FEATURE_FLAGS_UPDATED',
        status_code: 200,
        before_state: {
          isp_module_enabled: true,
          syslog_collector_enabled: true,
        },
        after_state: {
          isp_module_enabled: false,
          syslog_collector_enabled: false,
        },
        record_sha256_hash: 'hash-xyz-789',
      },
    ];

    vi.mocked(http.get).mockResolvedValueOnce({ data: mockRecords } as any);

    const wrapper = mount(TenantModulesAuditTab, {
      props: {
        tenantId: '11111111-2222-3333-4444-555555555555',
      },
    });

    await flushPromises();

    const btnRollback = wrapper.find('.btn-rollback');
    expect(btnRollback.exists()).toBe(true);
    await btnRollback.trigger('click');

    const emitted = wrapper.emitted('rollback');
    expect(emitted).toBeTruthy();
    expect(emitted![0][0]).toEqual({
      isp_module_enabled: true,
      syslog_collector_enabled: true,
    });
  });

  it('renderiza estado vacío cuando la API devuelve 0 modificaciones', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: [] } as any);

    const wrapper = mount(TenantModulesAuditTab, {
      props: {
        tenantId: '11111111-2222-3333-4444-555555555555',
      },
    });

    await flushPromises();

    expect(wrapper.find('.empty-title').exists()).toBe(true);
    expect(wrapper.text()).toContain('Sin modificaciones registradas');
  });

  it('despliega caja de error si la petición falla', async () => {
    vi.mocked(http.get).mockRejectedValueOnce(new Error('Network error'));

    const wrapper = mount(TenantModulesAuditTab, {
      props: {
        tenantId: '11111111-2222-3333-4444-555555555555',
      },
    });

    await flushPromises();

    expect(wrapper.find('.audit-state-box--error').exists()).toBe(true);
    expect(wrapper.text()).toContain('Error al consultar el historial');
  });
});
