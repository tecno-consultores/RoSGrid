/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

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
    vi.spyOn(http, 'get').mockResolvedValue({ data: [] } as never);
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
    expect(modal.text()).toContain('Leases DHCP Activos en BRAS-Caracas-01 (1 detectados)');
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
        provision_on_router: true,
      }),
    );
  });

  it('soporta arquitectura desacoplada L2 Bridge -> BNG mostrando badge Auto-detectado y selector de BNG', async () => {
    const ipamStore = useIpamStore();
    const invStore = useInventoryStore();

    invStore.routers = [
      { id: 'r-bridge', display_name: 'r3-Bridge', ip_address: '10.0.0.3' } as never,
      { id: 'r-bng', display_name: 'r111-BNG', ip_address: '10.0.0.111' } as never,
    ];

    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchCustomerServices').mockImplementation(async () => {
      ipamStore.customerServices = [mockSubUnpaired];
    });
    vi.spyOn(invStore, 'fetchRouters').mockResolvedValue();

    const splitCandidates: SubscriberLiveCandidatesResponse = {
      ...mockCandidates,
      router_id: 'r-bng',
      router_name: 'r111-BNG',
      access_router_id: 'r-bridge',
      access_router_name: 'r3-Bridge',
      auto_switched_bng: true,
      matched_mac_address: 'AA:BB:CC:11:22:33',
      matched_ipv4: '10.250.3.55',
    };

    const fetchCandidatesSpy = vi
      .spyOn(ipamStore, 'fetchSubscriberLiveCandidates')
      .mockResolvedValue(splitCandidates);

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    const tabs = wrapper.findAll('.tab-btn');
    await tabs[1].trigger('click');
    await flushPromises();

    await wrapper.find('#btn-pair-subscriber-sub-unpaired-01').trigger('click');
    await flushPromises();

    const modal = wrapper.find('#modal-pair-subscriber');
    expect(modal.text()).toContain('Nodo Físico L2: r3-Bridge');
    expect(modal.text()).toContain('Cabecera BNG/DHCP: r111-BNG');
    expect(modal.text()).toContain('Auto-detectado');

    const bngSelect = wrapper.find('#pair-bng-router-select');
    expect(bngSelect.exists()).toBe(true);

    // Cambiar manualmente el router BNG
    await bngSelect.setValue('r-bridge');
    await bngSelect.trigger('change');
    await flushPromises();

    expect(fetchCandidatesSpy).toHaveBeenCalledWith('sub-unpaired-01', 'r-bridge');
  });

  it('permite aprovisionar en MikroTik con PPPoE, contraseña y caller-id MAC', async () => {
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
      .mockResolvedValue({ ...mockSubUnpaired, service_type: 'PPPOE' });

    const wrapper = mount(IpamManagementView);
    await flushPromises();

    const tabs = wrapper.findAll('.tab-btn');
    await tabs[1].trigger('click');
    await flushPromises();

    await wrapper.find('#btn-pair-subscriber-sub-unpaired-01').trigger('click');
    await flushPromises();

    // Cambiar a PPPOE
    await wrapper.find('#pair-proto-select').setValue('PPPOE');
    await flushPromises();

    await wrapper.find('#pair-pppoe-user').setValue('cliente_ftth_99');
    await wrapper.find('#pair-pppoe-password').setValue('MySecretPass');
    await wrapper.find('#pair-assigned-ipv4').setValue('10.250.3.70');
    await wrapper.find('#pair-onu-mac').setValue('AA:BB:CC:33:44:55');

    // Submit
    const form = wrapper.find('#modal-pair-subscriber form');
    await form.trigger('submit.prevent');
    await flushPromises();

    expect(pairSpy).toHaveBeenCalledWith(
      'sub-unpaired-01',
      expect.objectContaining({
        service_type: 'PPPOE',
        endpoint_identifier: 'cliente_ftth_99',
        pppoe_password: 'MySecretPass',
        assigned_ipv4: '10.250.3.70',
        onu_mac_address: 'AA:BB:CC:33:44:55',
        provision_on_router: true,
      }),
    );
  });
});
