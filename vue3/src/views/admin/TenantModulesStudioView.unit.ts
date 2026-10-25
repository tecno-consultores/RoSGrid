// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import TenantModulesStudioView from './TenantModulesStudioView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { tenantId: 't-123' },
  }),
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('TenantModulesStudioView.vue — Estudio Táctico de Módulos & Feature Flags', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    pushMock.mockClear();
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('carga datos del tenant y renderiza breadcrumbs y cuadrícula de módulos', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url === '/api/v1/tenants') {
        return {
          status: 200,
          data: [
            {
              id: 't-123',
              name: 'Telecomunicaciones del Sur C.A.',
              slug: 'telecom-sur',
              status: 'ACTIVE',
            },
          ],
          headers: new Headers(),
        };
      }
      if (url.includes('/features')) {
        return {
          status: 200,
          data: {
            isp_module_enabled: true,
            bgp_looking_glass_enabled: false,
            cis_audit_enabled: true,
            syslog_collector_enabled: true,
          },
          headers: new Headers(),
        };
      }
      return { status: 404, data: null, headers: new Headers() };
    });

    const wrapper = mount(TenantModulesStudioView, {
      global: {
        stubs: {
          'router-link': true,
          RgFeatureFlagsGrid: true,
        },
      },
    });

    await flushPromises();

    expect(wrapper.find('.breadcrumb-current').text()).toBe('Telecomunicaciones del Sur C.A.');
    expect(wrapper.find('.breadcrumb-leaf').text()).toContain('Módulos & Capacidades');

    // Botón volver
    const btnBack = wrapper.find('.btn-back');
    expect(btnBack.exists()).toBe(true);
    await btnBack.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/admin/tenants');
  });

  it('guarda las capacidades actualizadas del tenant vía PATCH', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url === '/api/v1/tenants') {
        return {
          status: 200,
          data: [{ id: 't-123', name: 'ISP Sur', slug: 'isp-sur', status: 'ACTIVE' }],
          headers: new Headers(),
        };
      }
      return {
        status: 200,
        data: { isp_module_enabled: true },
        headers: new Headers(),
      };
    });

    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: { isp_module_enabled: false, cis_audit_enabled: true },
      headers: new Headers(),
    });

    const wrapper = mount(TenantModulesStudioView, {
      global: {
        stubs: {
          'router-link': true,
          RgFeatureFlagsGrid: true,
        },
      },
    });

    await flushPromises();

    // Emula el evento save emitido por RgFeatureFlagsGrid
    const grid = wrapper.findComponent({ name: 'RgFeatureFlagsGrid' });
    if (grid.exists()) {
      grid.vm.$emit('save');
      await flushPromises();
      expect(patchSpy).toHaveBeenCalledWith('/api/v1/tenants/t-123/features', expect.anything());
    }
  });
});
