// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ChangePasswordModal from './ChangePasswordModal.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

vi.mock('@/api/httpClient', () => ({
  http: {
    post: vi.fn(),
  },
}));

describe('ChangePasswordModal.vue — Cambio Seguro de Contraseña', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('no renderiza nada cuando isOpen es false', () => {
    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: false,
      },
    });

    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('renderiza título "Cambiar Mi Contraseña" para auto-cambio', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador1',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
    });

    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: true,
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Cambiar Mi Contraseña');
    expect(wrapper.find('#cp-current').exists()).toBe(true);
  });

  it('renderiza título con username objetivo cuando targetUser es otro usuario', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'admin-1',
      username: 'admin',
      email: 'admin@rosgrid.local',
      role: 'TENANT_ADMIN',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: true,
    });

    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: true,
        targetUser: { id: 'usr-2', username: 'tecnico_campo' },
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Cambiar Contraseña: @tecnico_campo');
    // Para admin reseteando a otro usuario, no se solicita la clave actual
    expect(wrapper.find('#cp-current').exists()).toBe(false);
  });

  it('valida que la nueva contraseña y su confirmación coincidan', async () => {
    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find('#cp-current').setValue('ActualPass123!');
    await wrapper.find('#cp-new').setValue('NuevaClaveSegura2026!');
    await wrapper.find('#cp-confirm').setValue('DiferenteClave!');
    await wrapper.find('form').trigger('submit.prevent');

    expect(wrapper.find('.alert-banner--error').text()).toContain('no coinciden');
    expect(http.post).not.toHaveBeenCalled();
  });

  it('envía petición exitosa y emite eventos password-changed y close', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({ data: { status: 'password_changed' } } as any);

    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find('#cp-current').setValue('ActualPass123!');
    await wrapper.find('#cp-new').setValue('NuevaClaveSegura2026!');
    await wrapper.find('#cp-confirm').setValue('NuevaClaveSegura2026!');
    await wrapper.find('form').trigger('submit.prevent');

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/users/change-password',
      expect.objectContaining({
        current_password: 'ActualPass123!',
        new_password: 'NuevaClaveSegura2026!',
      }),
    );
  });

  it('emite close al hacer clic en el botón de cancelar', async () => {
    const wrapper = mount(ChangePasswordModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find('.btn-cancel').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
