// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import IpamIpGridModal from './IpamIpGridModal.vue';
import { useIpamStore } from '@/stores/useIpamStore';
import type { IPAMPrefix } from '@/types';

const mockPrefix: IPAMPrefix = {
  id: 'pfx-01',
  tenant_id: 't-1',
  vrf_id: 'vrf-01',
  prefix: '100.64.10.0/24',
  ip_family: 'IPv4',
  role: 'CUSTOMER_RESIDENTIAL',
  status: 'ACTIVE',
  is_pool: true,
  description: 'Carrier-Grade CGNAT Pool',
  utilization_pct: 1.95,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('IpamIpGridModal.vue — Cuadrícula Visual 16x16 de Hosts IPv4', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('renderiza encabezado con el prefijo y los 256 bloques de direcciones', async () => {
    const ipamStore = useIpamStore();
    ipamStore.addresses = [
      {
        id: 'addr-01',
        tenant_id: 't-1',
        prefix_id: 'pfx-01',
        address: '100.64.10.1/32',
        ip_family: 'IPv4',
        status: 'ALLOCATED',
        description: 'Gateway Mikrotik',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    vi.spyOn(ipamStore, 'fetchAddresses').mockResolvedValue();

    const wrapper = mount(IpamIpGridModal, {
      props: {
        prefix: mockPrefix,
      },
    });
    await flushPromises();

    expect(wrapper.find('#grid-modal-title').text()).toContain('Matriz Visual');
    expect(wrapper.find('.prefix-tag').text()).toBe('100.64.10.0/24');
    expect(wrapper.findAll('.ip-tile').length).toBe(256);
  });

  it('emite evento close al hacer click en el botón de cerrar', async () => {
    const wrapper = mount(IpamIpGridModal, {
      props: {
        prefix: mockPrefix,
      },
    });

    const closeBtn = wrapper.find('.btn-close');
    await closeBtn.trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('muestra detalle al seleccionar un cuadrante de IP específica', async () => {
    const ipamStore = useIpamStore();
    ipamStore.addresses = [];
    vi.spyOn(ipamStore, 'fetchAddresses').mockResolvedValue();

    const wrapper = mount(IpamIpGridModal, {
      props: {
        prefix: mockPrefix,
      },
    });
    await flushPromises();

    // Seleccionar IP número 10
    const tiles = wrapper.findAll('.ip-tile');
    expect(tiles.length).toBe(256);
    await tiles[10].trigger('click');

    expect(wrapper.find('.ip-detail-panel').exists()).toBe(true);
    expect(wrapper.find('.detail-ip').text()).toContain('100.64.10.10/32');
  });
});
