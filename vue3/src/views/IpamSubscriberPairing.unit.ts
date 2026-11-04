// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import IpamManagementView from './IpamManagementView.vue';
import { useIpamStore } from '@/stores/useIpamStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { http } from '@/api/httpClient';
import type { CustomerService, SubscriberLiveCandidatesResponse } from '@/types';

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ params: {}, query: {} }),
}));

describe('IpamSubscriberPairing — Emparejamiento de Red FTTH (DHCP / PPPoE / IPAM)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();
    vi.spyOn(http, 'get').mockResolvedValue({ data: [] } as any);
  });

  const mockSubUnpaired: CustomerService = {
    id: 'sub-unpaired-01',
    tenant_id: 'ten-01',
    router_id: 'r-01',
    customer_name: 'Abonado 151515',
    endpoint_identifier: '151515',
    service_type: 'DHCP',
    auth_backend: 'LOCAL_SECRET',
    onu_mode: 'ROUTER',
    device_serial: 'HWTC12345678',
    assigned_ipv4: null,
    last_reachability_status: 'ONLINE',
    status: 'ACTIVE',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockSubPaired: CustomerService = {
    id: 'sub-paired-02',
    tenant_id: 'ten-01',
    router_id: 'r-01',
    customer_name: 'Abonado 202020',
    endpoint_identifier: '202020',
    service_type: 'PPPOE',
    auth_backend: 'LOCAL_SECRET',
    pppoe_username: 'cliente_202020',
    onu_mode: 'BRIDGE',
    device_serial: 'ZTEG87654321',
    assigned_ipv4: '10.250.3.55',
    onu_mac_address: 'AA:BB:CC:11:22:33',
    last_reachability_status: 'ONLINE',
    status: 'ACTIVE',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockCandidates: SubscriberLiveCandidatesResponse = {
    device_id: 'sub-unpaired-01',
    router_id: 'r-01',
    router_name: 'BRAS-Caracas-01',
    dhcp_leases: [
      {
        address: '10.250.3.55',
        mac_address: 'AA:BB:CC:11:22:33',
        host_name: 'FTTH-CLI-151515',
        server: 'dhcp1',
        status: 'bound',
      },
    ],
    pppoe_sessions: [
      {
        name: 'cliente_202020',
        address: '10.250.3.77',
        caller_id: 'AA:BB:CC:44:55:66',
        service: 'pppoe',
        uptime: '1d',
        source: 'active',
      },
    ],
    ipam_addresses: [
      {
        id: 'ip-01',
        tenant_id: 'ten-01',
        prefix_id: 'pfx-01',
        address: '10.250.3.90/24',
        ip_family: 'IPv4',
        status: 'ALLOCATED',
        description: 'Pool IPAM Residencial',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ],
  };

  it('renderiza la columna IPv4 / Sesión Emparejada con badges y el botón 🔗 Emparejar', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockImplementation(async () => {
      ipamStore.customerServices = [mockSubUnpaired, mockSubPaired];
    });
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    // Activar pestaña de Abonados (índice 1)
    const tabs = wrapper.findAll('.tab-btn');
    await tabs[1].trigger('click');
    await flushPromises();

    // Verificar encabezados
    expect(wrapper.text()).toContain('IPv4 / Sesión Emparejada');

    // Badge sin IP y badge con IP
    expect(wrapper.find('.pair-badge--unpaired').exists()).toBe(true);
    expect(wrapper.find('.pair-badge--unpaired').text()).toContain('Sin IP emparejada');
    expect(wrapper.find('.pair-badge--ok').exists()).toBe(true);
    expect(wrapper.find('.pair-badge--ok').text()).toContain('10.250.3.55');

    // Botones 🔗 Emparejar
    const btnPair = wrapper.find('#btn-pair-subscriber-sub-unpaired-01');
    expect(btnPair.exists()).toBe(true);
    expect(btnPair.text()).toContain('Emparejar');
  });

  it('abre el modal #modal-pair-subscriber y carga candidatos en vivo del router', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockImplementation(async () => {
      ipamStore.customerServices = [mockSubUnpaired];
    });
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();
    const fetchCandidatesSpy = vi
      .spyOn(ipamStore, 'fetchSubscriberLiveCandidates')
      .mockResolvedValue(mockCandidates);

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    // Ir a Abonados
    const tabs = wrapper.findAll('.tab-btn');
    await tabs[1].trigger('click');
    await flushPromises();

    // Abrir modal de emparejamiento
    const btnPair = wrapper.find('#btn-pair-subscriber-sub-unpaired-01');
    await btnPair.trigger('click');
    await flushPromises();

    expect(fetchCandidatesSpy).toHaveBeenCalledWith('sub-unpaired-01');
    const modal = wrapper.find('#modal-pair-subscriber');
    expect(modal.exists()).toBe(true);
    expect(modal.text()).toContain('Emparejar Red de Abonado FTTH');
    expect(modal.text()).toContain('BRAS-Caracas-01');
    expect(modal.text()).toContain('Leases DHCP Activos en el Router (1 detectados)');
  });

  it('permite seleccionar un Lease DHCP y guardar el emparejamiento con PATCH', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockImplementation(async () => {
      ipamStore.customerServices = [mockSubUnpaired];
    });
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchSubscriberLiveCandidates').mockResolvedValue(mockCandidates);
    const pairSpy = vi
      .spyOn(ipamStore, 'pairSubscriberNetwork')
      .mockResolvedValue({ ...mockSubUnpaired, assigned_ipv4: '10.250.3.55' });

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    const tabs = wrapper.findAll('.tab-btn');
    await tabs[1].trigger('click');
    await flushPromises();

    await wrapper.find('#btn-pair-subscriber-sub-unpaired-01').trigger('click');
    await flushPromises();

    // Seleccionar Lease DHCP
    const dhcpSelect = wrapper.find('#pair-dhcp-lease-select');
    expect(dhcpSelect.exists()).toBe(true);
    await dhcpSelect.setValue('10.250.3.55');
    await dhcpSelect.trigger('change');
    await flushPromises();

    // Guardar emparejamiento
    const form = wrapper.find('#modal-pair-subscriber form');
    await form.trigger('submit.prevent');
    await flushPromises();

    expect(pairSpy).toHaveBeenCalledWith(
      'sub-unpaired-01',
      expect.objectContaining({
        service_type: 'DHCP',
        assigned_ipv4: '10.250.3.55',
        onu_mac_address: 'AA:BB:CC:11:22:33',
      }),
    );
  });
});
