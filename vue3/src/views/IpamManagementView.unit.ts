// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import IpamManagementView from './IpamManagementView.vue';
import { useIpamStore } from '@/stores/useIpamStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { http } from '@/api/httpClient';

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ params: {}, query: {} }),
}));

describe('IpamManagementView.vue — Centro de Mando IPAM y Gestión de Clientes', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();
    vi.spyOn(http, 'get').mockResolvedValue({ data: [] } as never);
  });

  it('renderiza la cabecera IPAM, métricas KPI y las pestañas operativas', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockResolvedValue();
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    expect(wrapper.find('[role="region"].ipam-management-view').exists()).toBe(true);
    expect(wrapper.find('.ipam-kpi-grid').exists()).toBe(true);
    expect(wrapper.find('.ipam-tabs-nav').exists()).toBe(true);
  });

  it('permite alternar entre pestañas de Prefijos, Abonados, Sincronización MikroTik y QoS', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockResolvedValue();
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    const tabs = wrapper.findAll('.tab-btn');
    expect(tabs.length).toBeGreaterThanOrEqual(4);

    // Click en la pestaña de Abonados
    await tabs[1].trigger('click');
    expect(wrapper.find('.subscribers-section').exists()).toBe(true);
    expect(wrapper.find('#btn-simulate-dhcp-subscribers').exists()).toBe(true);

    // Click en la pestaña de Sincronización MikroTik
    await tabs[2].trigger('click');
    expect(wrapper.find('.sync-section').exists()).toBe(true);

    // Click en la pestaña de Planes de Ancho de Banda (QoS)
    await tabs[3].trigger('click');
    await flushPromises();
    expect(wrapper.find('.bandwidth-section').exists()).toBe(true);
  });
});
