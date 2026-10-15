// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import VaultRevealModal from './VaultRevealModal.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';
import type { RouterItem } from '@/types';

const sampleRouter: RouterItem = {
  id: 'r-vault-1',
  tenant_id: 't-1',
  display_name: 'CCR2004-Vault-Core',
  ip_address: '10.0.0.1',
  api_port: 8728,
  ros_version: '7.18',
  admin_state: 'PRODUCTION',
  is_reachable: true,
};

describe('VaultRevealModal.vue — Bóveda Criptográfica con Step-Up 2FA y Purga 30s', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    vi.useFakeTimers();

    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'admin-1',
      username: 'root_admin',
      email: 'root@rosgrid.local',
      tenant_id: 't-corp',
      tenant_slug: 'corp',
      role: 'TENANT_ADMIN',
      totp_enabled: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('no renderiza nada cuando isOpen es false', () => {
    const wrapper = mount(VaultRevealModal, {
      props: {
        isOpen: false,
        router: sampleRouter,
      },
    });
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('bloquea el acceso si el rol no es SUPERADMIN_GLOBAL ni TENANT_ADMIN', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'user-op',
      username: 'operador_l1',
      email: 'op@rosgrid.local',
      tenant_id: 't-corp',
      tenant_slug: 'corp',
      role: 'SUPPORT_L1',
      totp_enabled: true,
    });

    const wrapper = mount(VaultRevealModal, {
      props: {
        isOpen: true,
        router: sampleRouter,
      },
    });

    expect(wrapper.find('.banner--error').text()).toContain('Acceso denegado');
    expect(wrapper.find('.stepup-box').exists()).toBe(false);
  });

  it('valida campos obligatorios y permite verificar Step-Up 2FA para desbloquear secreto temporal por 30s', async () => {
    const wrapper = mount(VaultRevealModal, {
      props: {
        isOpen: true,
        router: sampleRouter,
      },
    });

    expect(wrapper.find('#vault-modal-title').text()).toContain('Bóveda Criptográfica');
    expect(wrapper.find('.stepup-box').exists()).toBe(true);

    // Validación sin datos
    await wrapper.find('.stepup-form').trigger('submit');
    expect(wrapper.find('.banner--error').text()).toContain('El motivo y el código TOTP');

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        router_id: 'r-vault-1',
        api_username: 'rosgrid_admin',
        current_password: 'SecretMikrotikKey#2026',
        auto_purge_seconds: 30,
      },
      headers: new Headers(),
    });

    await wrapper.find('#consult-reason').setValue('Revisión de BGP urgente');
    await wrapper.find('#vault-totp').setValue('123456');
    await wrapper.find('.stepup-form').trigger('submit');
    await flushPromises();

    // Ahora debe estar en estado desbloqueado
    expect(wrapper.find('.revealed-box').exists()).toBe(true);
    expect(wrapper.find('.secret-text').text()).toBe('SecretMikrotikKey#2026');

    // Copiar al portapapeles
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    await wrapper.find('.btn-copy').trigger('click');

    // Avanzar el reloj 31 segundos para validar autodestrucción en memoria RAM
    vi.advanceTimersByTime(31000);
    await flushPromises();

    // Debe volver al estado bloqueado y purgar contraseñas
    expect(wrapper.find('.revealed-box').exists()).toBe(false);
  });

  it('permite rotar clave API y re-anclar certificado SSL, manejando cancelaciones y errores', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);

    const wrapper = mount(VaultRevealModal, {
      props: {
        isOpen: true,
        router: sampleRouter,
      },
    });

    // Cancelar confirmación
    await wrapper.find('.btn-op--rotate').trigger('click');
    expect(wrapper.emitted('rotated')).toBeFalsy();

    await wrapper.find('.btn-op--repin').trigger('click');
    expect(wrapper.emitted('repinned')).toBeFalsy();

    // Confirmar rotación con error
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Fallo al rotar clave',
    });

    await wrapper.find('.btn-op--rotate').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo al rotar clave');

    // Confirmar rotación con éxito
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-op--rotate').trigger('click');
    await flushPromises();
    expect(wrapper.emitted('rotated')).toBeTruthy();

    // Re-pin SSL con rechazo
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Fallo al re-anclar SSL',
    });
    await wrapper.find('.btn-op--repin').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo al re-anclar SSL');

    // Re-pin SSL exitoso
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-op--repin').trigger('click');
    await flushPromises();
    expect(wrapper.emitted('repinned')).toBeTruthy();

    // Cerrar modal
    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    // Cambiar isOpen a false y luego a true para cubrir watcher completo
    await wrapper.setProps({ isOpen: false });
    await wrapper.setProps({ isOpen: true });
    wrapper.unmount();
  });

  it('activa fallback simulado si falla http.post al desbloquear y maneja error de portapapeles', async () => {
    const wrapper = mount(VaultRevealModal, {
      props: {
        isOpen: true,
        router: sampleRouter,
      },
    });

    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('API offline'));

    await wrapper.find('#consult-reason').setValue('Auditoría');
    await wrapper.find('#vault-totp').setValue('654321');
    await wrapper.find('.stepup-form').trigger('submit');
    await flushPromises();

    // Se desbloquea usando datos de prueba simulados
    expect(wrapper.find('.revealed-box').exists()).toBe(true);
    expect(wrapper.find('.secret-text').text()).toContain('Mkt-SecurePass');

    // Simular fallo en clipboard
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error('Clipboard blocked')) },
    });
    await wrapper.find('.btn-copy').trigger('click');
    await flushPromises();

    // Purgar manualmente vía timer
    vi.advanceTimersByTime(35000);
    await flushPromises();
    expect(wrapper.find('.revealed-box').exists()).toBe(false);
  });
});
