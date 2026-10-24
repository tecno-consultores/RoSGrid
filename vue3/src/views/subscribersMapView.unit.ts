// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import SubscribersMapView from './SubscribersMapView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
import { http } from '@/api/httpClient';

vi.mock('@/components/network/UnifiedNetworkMap.vue', () => ({
  default: {
    name: 'UnifiedNetworkMap',
    template: '<div class="mock-unified-network-map" data-testid="unified-network-map"></div>',
    props: ['routers', 'opticalBoxes', 'subscribers', 'selectedId', 'mode'],
    emits: ['select-subscriber', 'select-box', 'select-router', 'diagnose-subscriber'],
  },
}));

const MOCK_SERIAL = 'ZTEGC00001';
const MOCK_MAP_SELECTOR = '.mock-unified-network-map';

describe('SubscribersMapView.vue — Vista Bimodal de Mapa de Red y Clientes', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/inventory/routers')) {
        return {
          status: 200,
          headers: new Headers(),
          data: [
            {
              id: 'r-1',
              display_name: 'ROUTER-CORE-01',
              ip_address: '10.0.0.1',
              admin_state: 'PRODUCTION',
              is_reachable: true,
            },
          ],
        } as any;
      }
      return {
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
            endpoint_identifier: 'CLI-01',
            assigned_ipv4: '192.168.88.50',
            pon_port: 'sfp-plus1',
            optical_box: 'NAP-A',
            latitude: 10.4806,
            longitude: -66.9036,
            is_custom_coordinates: false,
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
            endpoint_identifier: 'CLI-02',
            assigned_ipv4: '192.168.88.51',
            pon_port: 'sfp-plus1',
            optical_box: 'NAP-A',
            latitude: 10.481,
            longitude: -66.904,
            is_custom_coordinates: true,
            last_reachability_status: 'ONLINE',
            status: 'ACTIVE',
            ping_latency_ms: 75,
            packet_loss_pct: 2,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      } as any;
    });
  });

  it('renderiza título de Modo ISP cuando isp_module_enabled está activo y no muestra botón de simulación', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2'); // Total equipos
    });
    expect(wrapper.text()).toContain('Mapa de Cobertura FTTH y Cajas NAP');
    expect(wrapper.find('.btn-simulate-dhcp').exists()).toBe(false);
  });

  it('renderiza título de Modo Empresa (No-ISP) y botón de sincronización DHCP', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: false });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2');
    });
    expect(wrapper.text()).toContain('Mapa de Red y Clientes DHCP');
    expect(wrapper.find('.btn-sync-dhcp').exists()).toBe(true);
    expect(wrapper.find('.btn-simulate-dhcp').exists()).toBe(false);
  });

  it('ejecuta sincronización DHCP real desde la interfaz', async () => {
    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: {
        message: 'Sincronización DHCP completada: 5 leases procesados.',
        routers_polled: 1,
        leases_found: 5,
        created_count: 3,
        updated_count: 2,
      },
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find('.btn-sync-dhcp').exists()).toBe(true);
    });

    await wrapper.find('.btn-sync-dhcp').trigger('click');
    expect(postSpy).toHaveBeenCalledWith('/api/v1/subscriber-devices/sync-dhcp');
  });

  it('abre drawer de cliente y permite test ping 1-click en vivo', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: {
        device_id: 'onu-01',
        last_reachability_status: 'ONLINE',
        ping_latency_ms: 12,
        packet_loss_pct: 0,
        message: 'Host alcanzable con 12ms',
      },
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
      expect(wrapper.text()).toContain('2');
    });

    const mapComponent = wrapper.findComponent({ name: 'UnifiedNetworkMap' });
    mapComponent.vm.$emit('select-subscriber', 'onu-01');
    await wrapper.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapper.find('.onu-detail-drawer').exists()).toBe(true);
    });
    expect(wrapper.text()).toContain('192.168.88.50');

    // Botón Ping 1-Click
    const pingBtn = wrapper.find('.drawer-ping-section button');
    await pingBtn.trigger('click');

    expect(postSpy).toHaveBeenCalledWith('/api/v1/subscriber-devices/onu-01/ping');
  });

  it('abre drawer de Caja NAP al emitir select-box', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const fieldStore = useFieldOpsStore();
    vi.spyOn(fieldStore, 'fetchOpticalBoxDetail').mockResolvedValue({
      id: 'box-01',
      tenant_id: 't-1',
      router_id: 'r-1',
      box_code: 'NAP-NORTE-01',
      capacity_ports: 16,
      splitter_ratio: '1:16',
      installation_type: 'POSTE',
      physical_location: 'Calle 4ta Poste 10',
      input_power_dbm: -15.5,
      latitude: 10.48,
      longitude: -66.90,
      status: 'ACTIVE',
      occupied_ports_count: 2,
      available_ports_count: 14,
      ports: [
        {
          port_number: 1,
          is_occupied: true,
          subscriber_id: 'onu-01',
          subscriber_identifier: 'ZTEGC00001',
          reachability_status: 'ONLINE',
        },
        {
          port_number: 2,
          is_occupied: false,
          reachability_status: 'FREE',
        },
      ],
      subscribers: [
        { id: 'onu-01', endpoint_identifier: 'CLI-01', device_serial: 'ZTEGC00001', optical_box_port: 1 } as any,
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const mapComponent = wrapper.findComponent({ name: 'UnifiedNetworkMap' });
    mapComponent.vm.$emit('select-box', 'box-01');
    await wrapper.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NAP-NORTE-01');
      expect(wrapper.text()).toContain('Matriz de Puertos');
    });
  });
});
