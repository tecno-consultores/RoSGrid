// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CapsmanSsidModal from './CapsmanSsidModal.vue';
import { http } from '@/api/httpClient';

vi.mock('@/api/httpClient', () => ({
  http: {
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('@/composables/useI18n', () => ({
  useI18n: () => ({
    t: (_key: string, defaultVal?: string) => defaultVal || _key,
  }),
}));

describe('CapsmanSsidModal.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('no se renderiza en el DOM cuando show es false', () => {
    const wrapper = mount(CapsmanSsidModal, {
      props: {
        show: false,
        routerId: 'r-123',
      },
    });
    expect(wrapper.find('.rg-modal-overlay').exists()).toBe(false);
  });

  it('crea una nueva configuración SSID tras validar campos obligatorios', async () => {
    (http.post as any).mockResolvedValueOnce({ data: { id: '*C1' } });

    const wrapper = mount(CapsmanSsidModal, {
      props: {
        show: true,
        routerId: 'r-123',
        editItem: null,
      },
    });

    await wrapper.find('#ssid-cfg-name').setValue('cfg-office');
    await wrapper.find('#ssid-name').setValue('Office-Corp');
    await wrapper.find('#ssid-sec-profile').setValue('sec-corp');
    await wrapper.find('#ssid-vlan-id').setValue(50);

    await wrapper.find('#btn-save-ssid').trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/wifi/capsman/r-123/configurations',
      expect.objectContaining({
        name: 'cfg-office',
        ssid: 'Office-Corp',
        security_profile: 'sec-corp',
        vlan_id: 50,
      }),
    );
    expect(wrapper.emitted('saved')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('modifica mediante PATCH una configuración existente en modo edición', async () => {
    (http.patch as any).mockResolvedValueOnce({ data: { status: 'ok' } });

    const editItem = {
      id: '*C99',
      name: 'cfg-branch',
      ssid: 'Old-SSID',
      security_type: 'sec-legacy',
      vlan_id: 10,
      client_isolation: true,
      hide_ssid: false,
      disabled: false,
    };

    const wrapper = mount(CapsmanSsidModal, {
      props: {
        show: true,
        routerId: 'r-123',
        editItem,
      },
    });

    // En modo edición, el input de nombre debe estar deshabilitado
    const nameInput = wrapper.find('#ssid-cfg-name');
    expect((nameInput.element as HTMLInputElement).disabled).toBe(true);

    // Cambiar SSID y guardar
    await wrapper.find('#ssid-name').setValue('Updated-Branch-SSID');
    await wrapper.find('#btn-save-ssid').trigger('click');
    await flushPromises();

    expect(http.patch).toHaveBeenCalledWith(
      '/api/v1/wifi/capsman/r-123/configurations/*C99',
      expect.objectContaining({
        ssid: 'Updated-Branch-SSID',
      }),
    );
    expect(wrapper.emitted('saved')).toBeTruthy();
  });
});
