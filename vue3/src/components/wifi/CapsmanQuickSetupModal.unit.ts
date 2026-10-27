// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CapsmanQuickSetupModal from './CapsmanQuickSetupModal.vue';
import { http } from '@/api/httpClient';

vi.mock('@/api/httpClient', () => ({
  http: {
    post: vi.fn(),
  },
}));

vi.mock('@/composables/useI18n', () => ({
  useI18n: () => ({
    t: (_key: string, defaultVal?: string) => defaultVal || _key,
  }),
}));

describe('CapsmanQuickSetupModal.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('no se renderiza en el DOM cuando show es false', () => {
    const wrapper = mount(CapsmanQuickSetupModal, {
      props: {
        show: false,
        routerId: 'r-12345',
      },
    });
    expect(wrapper.find('.rg-modal-overlay').exists()).toBe(false);
  });

  it('muestra error de validación cuando la contraseña es menor a 8 caracteres', async () => {
    const wrapper = mount(CapsmanQuickSetupModal, {
      props: {
        show: true,
        routerId: 'r-12345',
      },
    });

    const corpPassInput = wrapper.find('#corp-pass');
    await corpPassInput.setValue('short');

    const btnDeploy = wrapper.find('#btn-deploy-wizard');
    await btnDeploy.trigger('click');

    expect(wrapper.find('.rg-alert-danger').exists()).toBe(true);
    expect(http.post).not.toHaveBeenCalled();
  });

  it('despliega con éxito el asistente cuando el formulario es válido', async () => {
    (http.post as any).mockResolvedValueOnce({ data: { success: true } });

    const wrapper = mount(CapsmanQuickSetupModal, {
      props: {
        show: true,
        routerId: 'r-12345',
      },
    });

    await wrapper.find('#corp-ssid').setValue('HQ-Corp');
    await wrapper.find('#corp-pass').setValue('SecureCorporatePass123!');
    await wrapper.find('#guest-ssid').setValue('HQ-Guest');
    await wrapper.find('#guest-pass').setValue('SecureGuestPass123!');
    await wrapper.find('#guest-vlan').setValue(200);

    const btnDeploy = wrapper.find('#btn-deploy-wizard');
    await btnDeploy.trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/wifi/capsman/r-12345/quick-setup',
      expect.objectContaining({
        corporate_ssid: 'HQ-Corp',
        corporate_passphrase: 'SecureCorporatePass123!',
        guest_ssid_enabled: true,
        guest_ssid: 'HQ-Guest',
        guest_passphrase: 'SecureGuestPass123!',
        guest_vlan_id: 200,
      }),
    );
    expect(wrapper.emitted('saved')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
