// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CapsmanSecurityProfilesModal from './CapsmanSecurityProfilesModal.vue';
import { http } from '@/api/httpClient';

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/composables/useI18n', () => ({
  useI18n: () => ({
    t: (_key: string, defaultVal?: string) => defaultVal || _key,
  }),
}));

describe('CapsmanSecurityProfilesModal.vue', () => {
  const mockProfiles = [
    {
      id: '*1',
      name: 'sec-corporate',
      authentication_types: ['wpa2-psk', 'wpa3-psk'],
      passphrase_masked: '********',
      wps_disabled: true,
      ft_enabled: true,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('no se renderiza en el DOM cuando show es false', () => {
    const wrapper = mount(CapsmanSecurityProfilesModal, {
      props: {
        show: false,
        routerId: 'r-123',
      },
    });
    expect(wrapper.find('.rg-modal-overlay').exists()).toBe(false);
  });

  it('carga y muestra la lista de perfiles existentes al montarse', async () => {
    (http.get as any).mockResolvedValueOnce({ data: mockProfiles });

    const wrapper = mount(CapsmanSecurityProfilesModal, {
      props: {
        show: true,
        routerId: 'r-123',
      },
    });

    await flushPromises();
    expect(http.get).toHaveBeenCalledWith('/api/v1/wifi/capsman/r-123/security-profiles');
    expect(wrapper.text()).toContain('sec-corporate');
  });

  it('crea un nuevo perfil de seguridad válido tras desplegar el formulario', async () => {
    (http.get as any).mockResolvedValue({ data: mockProfiles });
    (http.post as any).mockResolvedValueOnce({ data: { id: '*2', name: 'sec-guests' } });

    const wrapper = mount(CapsmanSecurityProfilesModal, {
      props: {
        show: true,
        routerId: 'r-123',
      },
    });
    await flushPromises();

    // Abrir formulario
    await wrapper.find('#btn-toggle-add-sec').trigger('click');

    // Llenar campos
    await wrapper.find('#new-sec-name').setValue('sec-guests');
    await wrapper.find('#new-sec-pass').setValue('GuestPskKey123!');

    // Guardar
    await wrapper.find('#btn-save-sec-profile').trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/wifi/capsman/r-123/security-profiles',
      expect.objectContaining({
        name: 'sec-guests',
        passphrase: 'GuestPskKey123!',
      }),
    );
    expect(wrapper.emitted('updated')).toBeTruthy();
  });

  it('elimina un perfil al hacer click en el botón de eliminación tras confirmación', async () => {
    (http.get as any).mockResolvedValue({ data: mockProfiles });
    (http.delete as any).mockResolvedValueOnce({ data: { success: true } });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    const wrapper = mount(CapsmanSecurityProfilesModal, {
      props: {
        show: true,
        routerId: 'r-123',
      },
    });
    await flushPromises();

    const deleteBtn = wrapper.find('.rg-btn-danger-sm');
    await deleteBtn.trigger('click');
    await flushPromises();

    expect(http.delete).toHaveBeenCalledWith('/api/v1/wifi/capsman/r-123/security-profiles/*1');
    expect(wrapper.emitted('updated')).toBeTruthy();
  });
});
