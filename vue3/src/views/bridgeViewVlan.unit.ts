// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { http } from '@/api/httpClient';
import BridgeView from './BridgeView.vue';
import InterfacesAndSfpView from './InterfacesAndSfpView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { routerId: 'r-01' },
    path: '/routers/r-01/webfig/bridge',
    query: {},
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('BridgeView & InterfacesAndSfpView VLAN Creation Parity', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('renders BridgeView and displays + Definir VLAN en Bridge when activeTab is vlans', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/interfaces/bridge/vlans')) {
        return {
          data: [
            {
              id: '*1',
              bridge: 'bridge1',
              'vlan-ids': '10,20',
              tagged: 'ether1',
              untagged: 'ether2',
            },
          ],
        } as any;
      }
      return {
        data: [{ id: '*B1', name: 'bridge1', vlan_filtering: true }],
      } as any;
    });

    const wrapper = mount(BridgeView, {
      global: {
        stubs: {
          RgDataTable: {
            template: `
              <div class="rg-data-table-stub">
                <slot name="actions" :row="{ id: '*1', bridge: 'bridge1', vlan_ids: '10,20' }" />
              </div>
            `,
          },
        },
      },
    });

    await flushPromises();

    // Switch to vlans tab
    const vlanTabBtn = wrapper.findAll('.tab-btn').find((b) => b.text().includes('Tabla VLANs'));
    expect(vlanTabBtn).toBeDefined();
    await vlanTabBtn?.trigger('click');
    await flushPromises();

    // Check header buttons for VLAN definition
    const defineVlanBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Definir VLAN en Bridge'));
    const subIfaceBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Subinterfaz 802.1Q'));
    expect(defineVlanBtn).toBeDefined();
    expect(subIfaceBtn).toBeDefined();

    // Open define VLAN modal
    await defineVlanBtn?.trigger('click');
    await flushPromises();

    expect(wrapper.find('#modal-vlan-title').exists()).toBe(true);

    // Mock post call
    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({ data: { status: 'success' } } as any);

    // Submit form
    await wrapper.find('#vlan-ids').setValue('50');
    await wrapper.find('.modal-form').trigger('submit.prevent');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/routers/r-01/webfig/interfaces/bridge/vlans',
      expect.objectContaining({
        vlan_ids: '50',
      }),
    );
  });

  it('renders InterfacesAndSfpView and allows creating a subinterface VLAN', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      data: [
        { id: '*1', name: 'ether1', type: 'ether' },
        { id: '*2', name: 'vlan10', type: 'vlan' },
      ],
    } as any);

    const wrapper = mount(InterfacesAndSfpView, {
      global: {
        stubs: {
          RgDataTable: {
            template: `
              <div class="rg-data-table-stub">
                <slot name="actions" :row="{ id: '*2', name: 'vlan10', type: 'vlan' }" />
              </div>
            `,
          },
        },
      },
    });

    await flushPromises();

    // Check presence of create VLAN button
    const createVlanBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Crear Subinterfaz VLAN'));
    expect(createVlanBtn).toBeDefined();

    await createVlanBtn?.trigger('click');
    await flushPromises();

    expect(wrapper.find('#modal-vlan-create-title').exists()).toBe(true);

    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({ data: { status: 'success' } } as any);

    await wrapper.find('#vlan-create-name').setValue('vlan99-test');
    await wrapper.find('#vlan-create-id').setValue('99');
    await wrapper.find('#vlan-create-parent').setValue('ether1');
    await wrapper.find('.modal-form').trigger('submit.prevent');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/routers/r-01/webfig/interfaces/vlan',
      expect.objectContaining({
        name: 'vlan99-test',
        vlan_id: 99,
        interface: 'ether1',
      }),
    );
  });

  it('renders BridgeView tab labels cleanly without misleading (0) counters', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      data: [{ id: '*B1', name: 'bridge1', vlan_filtering: true }],
    } as any);

    const wrapper = mount(BridgeView, {
      global: {
        stubs: {
          RgDataTable: { template: '<div class="rg-data-table-stub" />' },
        },
      },
    });

    await flushPromises();

    const tabs = wrapper.findAll('.tab-btn');
    expect(tabs.length).toBe(4);
    expect(tabs[0].text()).toBe('🌉 Bridges');
    expect(tabs[1].text()).toBe('🔌 Puertos Miembro');
    expect(tabs[2].text()).toBe('🏷️ Tabla VLANs');
    expect(tabs[3].text()).toBe('💻 Hosts / FDB MAC');
    expect(wrapper.text()).not.toMatch(/\(\d+\)/);
  });
});

