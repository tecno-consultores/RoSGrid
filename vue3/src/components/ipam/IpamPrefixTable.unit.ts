// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import IpamPrefixTable from './IpamPrefixTable.vue';
import { useIpamStore } from '@/stores/useIpamStore';
import type { IPAMPrefix, IPAMVrf } from '@/types';

const mockPrefixes: IPAMPrefix[] = [
  {
    id: 'p-01',
    tenant_id: 't-1',
    vrf_id: 'vrf-01',
    prefix: '100.64.0.0/20',
    ip_family: 'IPv4',
    role: 'CUSTOMER_RESIDENTIAL',
    status: 'ACTIVE',
    is_pool: false,
    description: 'CGNAT Supernet',
    utilization_pct: 25.0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'p-02',
    tenant_id: 't-1',
    vrf_id: 'vrf-01',
    prefix: '2803:cafe::/32',
    ip_family: 'IPv6',
    role: 'CUSTOMER_RESIDENTIAL',
    status: 'ACTIVE',
    is_pool: true,
    description: 'Bloque IPv6 Residencial',
    utilization_pct: 0.1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockVrfs: IPAMVrf[] = [
  {
    id: 'vrf-01',
    tenant_id: 't-1',
    name: 'default',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe('IpamPrefixTable.vue — Tabla Integral de Subredes y Pools IPAM', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();
  });

  it('renderiza cabecera de tabla y lista de prefijos', async () => {
    const ipamStore = useIpamStore();
    ipamStore.prefixes = mockPrefixes;
    ipamStore.vrfs = mockVrfs;
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();

    const wrapper = mount(IpamPrefixTable);
    await flushPromises();

    expect(wrapper.find('.ipam-toolbar').exists()).toBe(true);
    expect(wrapper.find('button[aria-label="Añadir nuevo prefijo"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('100.64.0.0/20');
    expect(wrapper.text()).toContain('2803:cafe::/32');
  });

  it('emite open-ip-grid al hacer click en el botón de ver matriz IPv4 /24', async () => {
    const ipamStore = useIpamStore();
    const slash24: IPAMPrefix = {
      ...mockPrefixes[0],
      id: 'p-24',
      prefix: '100.64.1.0/24',
    };
    ipamStore.prefixes = [slash24];
    ipamStore.vrfs = mockVrfs;
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();

    const wrapper = mount(IpamPrefixTable);
    await flushPromises();

    const gridBtn = wrapper.find('.btn-cell--grid');
    expect(gridBtn.exists()).toBe(true);
    await gridBtn.trigger('click');
    expect(wrapper.emitted('open-ip-grid')).toBeTruthy();
  });

  it('permite abrir el modal de nuevo prefijo y crear una subred', async () => {
    const ipamStore = useIpamStore();
    ipamStore.prefixes = [];
    ipamStore.vrfs = mockVrfs;
    vi.spyOn(ipamStore, 'fetchPrefixes').mockResolvedValue();
    vi.spyOn(ipamStore, 'fetchVrfs').mockResolvedValue();
    const createSpy = vi.spyOn(ipamStore, 'createPrefix').mockResolvedValue({} as any);

    const wrapper = mount(IpamPrefixTable);
    await flushPromises();

    const addBtn = wrapper.find('button[aria-label="Añadir nuevo prefijo"]');
    await addBtn.trigger('click');
    await flushPromises();

    expect(wrapper.find('#pfx-cidr').exists()).toBe(true);

    await wrapper.find('#pfx-cidr').setValue('10.100.0.0/24');
    await wrapper.find('form.modal-body').trigger('submit');

    expect(createSpy).toHaveBeenCalled();
  });
});
