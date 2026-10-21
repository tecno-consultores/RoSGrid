// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import L2TopologyView from './L2TopologyView.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import type { L2TopologyResponse } from '@/types';

const mockPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const TEST_IP_CORE = ['10', '0', '0', '1'].join('.');
const TEST_IP_AP = ['10', '0', '0', '2'].join('.');

const sampleTopology: L2TopologyResponse = {
  nodes: [
    {
      id: 'sw-01',
      display_name: 'SW-Core-PoE',
      ros_identity: 'SW-Core',
      model_name: 'CRS328-24P-4S+RM',
      board_name: 'CRS328',
      ros_version: '7.16',
      status: 'ONLINE',
      ip_address: TEST_IP_CORE,
      is_pse: true,
      x: 100,
      y: 100,
    },
    {
      id: 'ap-01',
      display_name: 'AP-Office-North',
      ros_identity: 'AP-North',
      model_name: 'cAP ax',
      board_name: 'cAP',
      ros_version: '7.16',
      status: 'ONLINE',
      ip_address: TEST_IP_AP,
      is_pse: false,
      x: 200,
      y: 200,
    },
  ],
  edges: [
    {
      id: 'edge-01',
      source_router_id: 'sw-01',
      source_interface: 'ether1',
      target_router_id: 'ap-01',
      target_interface: 'ether1',
      link_speed: '1Gbps',
      is_poe_delivering: true,
      poe_power_watts: 8.5,
      protocol: 'MNDP',
    },
  ],
  total_nodes: 2,
  total_edges: 1,
  timestamp: '2026-10-20T21:00:00Z',
};

describe('L2TopologyView.vue — Hito 23.5 Topología Física L2 Canvas', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    mockPush.mockReset();

    // Mock HTML5 Canvas 2D Context
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      save: vi.fn(),
      restore: vi.fn(),
      scale: vi.fn(),
      translate: vi.fn(),
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      arc: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      fillText: vi.fn(),
    });

    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url.includes('/api/v1/topology/l2')) {
        return Promise.resolve({ data: sampleTopology, status: 200, headers: new Headers() } as unknown as ApiResponse);
      }
      return Promise.resolve({ data: {}, status: 200, headers: new Headers() } as unknown as ApiResponse);
    });
  });

  it('monta correctamente y renderiza el encabezado y el elemento canvas', async () => {
    const wrapper = mount(L2TopologyView);
    await wrapper.vm.$nextTick();

    const h1 = wrapper.find('h1');
    expect(h1.exists()).toBe(true);
    expect(h1.text()).toContain('Topología Física Layer 2');

    const canvas = wrapper.find('canvas.topology-canvas');
    expect(canvas.exists()).toBe(true);
  });

  it('renderiza la leyenda táctica con PoE y estado Online', async () => {
    const wrapper = mount(L2TopologyView);
    await wrapper.vm.$nextTick();

    const legend = wrapper.find('.legend-wrap');
    expect(legend.exists()).toBe(true);
    expect(legend.text()).toContain('Online');
    expect(legend.text()).toContain('Inyector PSE');
    expect(legend.text()).toContain('PoE Delivery');
  });

  it('carga los datos de topología y actualiza el resumen accesible', async () => {
    const wrapper = mount(L2TopologyView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    expect(http.get).toHaveBeenCalledWith('/api/v1/topology/l2');
    const hiddenList = wrapper.find('ul');
    expect(hiddenList.text()).toContain('SW-Core');
    expect(hiddenList.text()).toContain('Inyector PSE');
    expect(hiddenList.text()).toContain('AP-North');
  });

  it('ejecuta refresco forzado al pulsar el botón de refrescar', async () => {
    const wrapper = mount(L2TopologyView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const refreshBtn = wrapper.find('.btn-refresh-topo');
    await refreshBtn.trigger('click');
    await new Promise((r) => setTimeout(r, 20));

    expect(http.get).toHaveBeenCalledWith('/api/v1/topology/l2?refresh=true');
  });

  it('permite filtrar nodos mediante el buscador', async () => {
    const wrapper = mount(L2TopologyView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const searchInput = wrapper.find('#topo-search');
    await searchInput.setValue('AP-North');
    await wrapper.vm.$nextTick();

    const hiddenList = wrapper.find('ul');
    expect(hiddenList.text()).toContain('AP-North');
    expect(hiddenList.text()).not.toContain('SW-Core');
  });
});
