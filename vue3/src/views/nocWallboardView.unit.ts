// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { http } from '@/api/httpClient';
import NocWallboardView from './NocWallboardView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {},
    path: '/noc-wallboard',
    query: {},
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('NocWallboardView.vue — Conmutador de Mapa Geográfico y Grafo L2/PoE (Hito 30.24 / Spec 101)', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    vi.restoreAllMocks();

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/routers')) {
        return {
          status: 200,
          data: {
            items: [
              {
                id: 'r-01',
                tenant_id: 't-1',
                display_name: 'Core-CCR2004',
                ip_address: '10.0.0.1',
                is_reachable: true,
                admin_state: 'PRODUCTION',
                ssl_trust_status: 'TRUSTED_PINNED',
                latitude: 10.48,
                longitude: -66.90,
              },
            ],
          },
          headers: new Headers(),
        };
      }
      return { status: 200, data: { items: [] }, headers: new Headers() };
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renderiza inicialmente el mapa geográfico y el botón de alternancia #btn-wallboard-toggle-l2-view', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: { template: '<div class="stub-unified-map">UNIFIED_MAP</div>' },
          L2TopologyView: { template: '<div class="stub-l2-topology">L2_TOPOLOGY</div>' },
        },
      },
    });
    await flushPromises();

    const toggleBtn = wrapper.find('#btn-wallboard-toggle-l2-view');
    expect(toggleBtn.exists()).toBe(true);
    expect(toggleBtn.text()).toContain('Grafo L2 / PoE');

    // Inicialmente debe mostrar el UnifiedNetworkMap y no el L2TopologyView
    expect(wrapper.find('.stub-unified-map').exists()).toBe(true);
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(false);
  });

  it('conmuta hacia el Grafo Esquemático L2 y regresa al Mapa Geográfico al hacer clic en #btn-wallboard-toggle-l2-view', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: { template: '<div class="stub-unified-map">UNIFIED_MAP</div>' },
          L2TopologyView: { template: '<div class="stub-l2-topology">L2_TOPOLOGY</div>' },
        },
      },
    });
    await flushPromises();

    const toggleBtn = wrapper.find('#btn-wallboard-toggle-l2-view');

    // Clic 1: Cambiar a Grafo L2 / PoE
    await toggleBtn.trigger('click');
    expect(toggleBtn.text()).toContain('Mapa Geográfico');
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(true);
    expect(wrapper.find('.stub-unified-map').exists()).toBe(false);

    // Clic 2: Regresar al Mapa Geográfico
    await toggleBtn.trigger('click');
    expect(toggleBtn.text()).toContain('Grafo L2 / PoE');
    expect(wrapper.find('.stub-unified-map').exists()).toBe(true);
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(false);
  });

  it('permite refrescar la infraestructura con #btn-wallboard-refresh', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    const refreshBtn = wrapper.find('#btn-wallboard-refresh');
    expect(refreshBtn.exists()).toBe(true);

    await refreshBtn.trigger('click');
    expect(http.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/inventory/routers'),
    );
  });
});
