// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import SubscribersMapView from './SubscribersMapView.vue';
import { http } from '@/api/httpClient';

vi.mock('@/components/inventory/OsmOnuMap.vue', () => ({
  default: {
    name: 'OsmOnuMap',
    template: '<div class="mock-osm-onu-map" data-testid="osm-onu-map"></div>',
    props: ['onus', 'selectedOnuId'],
    emits: ['select-onu', 'verify-onu', 'diagnose-onu'],
  },
}));

const MOCK_SERIAL = 'ZTEGC00001';
const MOCK_MAP_SELECTOR = '.mock-osm-onu-map';

describe('SubscribersMapView.vue — Vista de Mapa de Clientes / ONUs', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: [
        {
          id: 'onu-01',
          tenant_id: 't-1',
          router_id: 'r-1',
          service_type: 'FTTH_PPPOE',
          auth_backend: 'INTERNAL',
          onu_mode: 'ROUTER',
          device_serial: MOCK_SERIAL,
          onu_serial_number: MOCK_SERIAL,
          customer_name: 'Carlos Santana',
          customer_code: 'CLI-01',
          pon_port: 'sfp-plus1',
          optical_box: 'NAP-A',
          latitude: 10.4806,
          longitude: -66.9036,
          last_reachability_status: 'ONLINE',
          status: 'ACTIVE',
          ping_latency_ms: 22,
          packet_loss_pct: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'onu-02',
          tenant_id: 't-1',
          router_id: 'r-1',
          service_type: 'FTTH_PPPOE',
          auth_backend: 'INTERNAL',
          onu_mode: 'BRIDGE',
          device_serial: 'HWTC00002',
          onu_serial_number: 'HWTC00002',
          customer_name: 'Ana Maria',
          customer_code: 'CLI-02',
          pon_port: 'sfp-plus1',
          optical_box: 'NAP-A',
          latitude: 10.481,
          longitude: -66.904,
          last_reachability_status: 'ONLINE',
          status: 'ACTIVE',
          ping_latency_ms: 75,
          packet_loss_pct: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'onu-03',
          tenant_id: 't-1',
          router_id: 'r-1',
          service_type: 'FTTH_PPPOE',
          auth_backend: 'INTERNAL',
          onu_mode: 'ROUTER',
          device_serial: 'ZTEGC00003',
          onu_serial_number: 'ZTEGC00003',
          customer_name: 'Luis Miguel',
          customer_code: 'CLI-03',
          pon_port: 'sfp-plus2',
          optical_box: 'NAP-B',
          latitude: 10.485,
          longitude: -66.908,
          last_reachability_status: 'OFFLINE',
          status: 'ACTIVE',
          ping_latency_ms: null,
          packet_loss_pct: 100,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    });
  });

  it('carga lista de ONUs y renderiza KPIs Zero-Metrics', async () => {
    const wrapper = mount(SubscribersMapView);
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('3'); // Total ONUs
    });
    expect(wrapper.text()).toContain('Mapa de Clientes y ONUs');
  });

  it('filtra por texto de búsqueda', async () => {
    const wrapper = mount(SubscribersMapView);
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const searchInput = wrapper.find('.rg-search-input');
    await searchInput.setValue(MOCK_SERIAL);

    const clearBtn = wrapper.find('.btn-clear-search');
    expect(clearBtn.exists()).toBe(true);
    await clearBtn.trigger('click');
    expect((searchInput.element as HTMLInputElement).value).toBe('');
  });

  it('filtra por chip de estado cromático (OPTIMAL, DEGRADED, DOWN)', async () => {
    const wrapper = mount(SubscribersMapView);
    await vi.waitFor(() => {
      expect(wrapper.find('.filter-chips').exists()).toBe(true);
    });

    const chips = wrapper.findAll('.chip-btn');
    await chips[1].trigger('click'); // OPTIMAL
    expect(chips[1].classes()).toContain('active');

    await chips[2].trigger('click'); // DEGRADED
    expect(chips[2].classes()).toContain('active');

    await chips[3].trigger('click'); // DOWN
    expect(chips[3].classes()).toContain('active');
  });

  it('abre y cierra el drawer de detalle al seleccionar una ONU', async () => {
    const wrapper = mount(SubscribersMapView);
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('3');
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const osmMapComponent = wrapper.findComponent({ name: 'OsmOnuMap' });
    osmMapComponent.vm.$emit('select-onu', 'onu-01');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.onu-detail-drawer').exists()).toBe(true);
    expect(wrapper.text()).toContain('Carlos Santana');

    const btnClose = wrapper.find('.btn-close-drawer');
    await btnClose.trigger('click');
    expect(wrapper.find('.onu-detail-drawer').exists()).toBe(false);
  });

  it('ejecuta acciones de test 1-click y diagnóstico 360 desde el mapa', async () => {
    const wrapper = mount(SubscribersMapView);
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const osmMapComponent = wrapper.findComponent({ name: 'OsmOnuMap' });
    osmMapComponent.vm.$emit('verify-onu', {
      id: 'onu-01',
      device_serial: MOCK_SERIAL,
    });
    expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('1-Click'));

    osmMapComponent.vm.$emit('diagnose-onu', {
      id: 'onu-01',
      device_serial: MOCK_SERIAL,
    });
    expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('360°'));
  });
});
