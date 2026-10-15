// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import LoginView from '../LoginView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

const mockPush = vi.fn();
let mockQuery: Record<string, string> = {};

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: mockQuery, path: '/login' }),
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('qrcode', () => ({
  default: {
    toCanvas: vi.fn().mockResolvedValue(undefined),
  },
}));

describe('LoginView.vue — Autenticación Multi-Tenant en 2 Etapas y 2FA TOTP', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockPush.mockReset();
    mockQuery = {};
    vi.useFakeTimers();
    window.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-file');
    window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('renderiza formulario de credenciales accesible con h1 y etiquetas, y precarga tenant desde query', async () => {
    mockQuery = { tenant: 'isp-valencia' };
    const wrapper = mount(LoginView);
    await flushPromises();
    expect(wrapper.find('h1').text()).toBe('RoSGrid');
    expect(wrapper.find('#tenant-slug').exists()).toBe(true);
    expect((wrapper.find('#tenant-slug').element as HTMLInputElement).value).toBe('isp-valencia');
  });

  it('muestra banner de advertencia si la URL contiene query reason', () => {
    mockQuery = { reason: 'session_revoked' };
    const wrapper = mount(LoginView);
    const alert = wrapper.find('.alert-banner--warning');
    expect(alert.exists()).toBe(true);
    expect(alert.text()).toContain('Tu sesión fue revocada');
  });

  it('normaliza tenant slug en minúsculas y caracteres válidos', async () => {
    const wrapper = mount(LoginView);
    const tenantInput = wrapper.find('#tenant-slug');
    await tenantInput.setValue('ISP-Norte_123!');
    await tenantInput.trigger('input');
    expect((tenantInput.element as HTMLInputElement).value.toLowerCase()).toContain('isp-norte');
  });

  it('permite alternar visibilidad de contraseña', async () => {
    const wrapper = mount(LoginView);
    const passwordInput = wrapper.find('#login-password');
    const toggleBtn = wrapper.find('.btn-toggle-visibility');

    expect(passwordInput.attributes('type')).toBe('password');
    await toggleBtn.trigger('click');
    expect(passwordInput.attributes('type')).toBe('text');
    await toggleBtn.trigger('click');
    expect(passwordInput.attributes('type')).toBe('password');
  });

  it('valida campos obligatorios antes de enviar', async () => {
    const wrapper = mount(LoginView);
    await wrapper.find('form').trigger('submit');
    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'Todos los campos son obligatorios',
    );
  });

  it('pasa a etapa ENROLL_2FA_REQUIRED cuando la API lo indica y permite descargar códigos y confirmar', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'ENROLL_2FA_REQUIRED',
        challenge_id: 'ch-123',
        totp_provisioning_uri: 'otpauth://totp/RoSGrid:admin?secret=JBSWY3DPEHPK3PXP',
        totp_secret: 'JBSWY3DPEHPK3PXP',
        backup_codes: ['1111-2222', '3333-4444'],
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.enroll-container').exists()).toBe(true);
    expect(wrapper.find('.secret-key').text()).toContain('JBSWY3DPEHPK3PXP');

    // Descargar códigos de respaldo
    await wrapper.find('.btn-download-backup').trigger('click');

    // Código con longitud inválida
    const totpInput = wrapper.find('#enroll-totp-input');
    await totpInput.setValue('12');
    await wrapper.find('.confirm-form').trigger('submit');
    expect(wrapper.find('.alert-banner--danger').text()).toContain('código de 6 dígitos');

    // Error en confirmación de enrolamiento
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Código de enrolamiento inválido',
    });

    await totpInput.setValue('000000');
    await wrapper.find('.confirm-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.alert-banner--danger').text()).toContain('Código de enrolamiento');

    // Confirmar enrolamiento con éxito
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        user: {
          id: 'u-1',
          email: 'admin@isp.net',
          username: 'admin',
          tenant_id: 't-1',
          tenant_slug: 'isp-norte',
          role: 'TENANT_ADMIN',
          totp_enabled: true,
        },
        csrf_token: 'csrf-123',
      },
      headers: new Headers(),
    });

    await totpInput.setValue('123456');
    await wrapper.find('.confirm-form').trigger('submit');
    await flushPromises();

    const authStore = useAuthStore();
    expect(authStore.isAuthenticated).toBe(true);
    expect(mockPush).toHaveBeenCalledWith('/inventory');
  });

  it('pasa a etapa VERIFY_2FA_TOTP, maneja error de verificación y completa login al verificar código', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'VERIFY_2FA_TOTP',
        challenge_id: 'ch-verify-99',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.verify-container').exists()).toBe(true);

    // Error en verificación
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Código expirado',
    });

    const verifyInput = wrapper.find('#verify-totp-input');
    await verifyInput.setValue('111111');
    await verifyInput.trigger('input');
    await flushPromises();
    expect(wrapper.find('.alert-banner--danger').text()).toContain('Código expirado');

    // Verificación exitosa con redirección NOC
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        user: {
          id: 'u-noc',
          email: 'noc@isp.net',
          username: 'noc_op',
          tenant_id: 't-1',
          tenant_slug: 'isp-norte',
          role: 'NOC_MONITOR',
          totp_enabled: true,
        },
        csrf_token: 'csrf-noc',
      },
      headers: new Headers(),
    });

    await verifyInput.setValue('654321');
    await verifyInput.trigger('input');
    await flushPromises();

    const authStore = useAuthStore();
    expect(authStore.isAuthenticated).toBe(true);
    expect(mockPush).toHaveBeenCalledWith('/noc-wallboard');
  });

  it('permite volver al formulario de credenciales desde verify', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'VERIFY_2FA_TOTP',
        challenge_id: 'ch-verify-99',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    await wrapper.find('.btn-back').trigger('click');
    expect(wrapper.find('.login-form').exists()).toBe(true);
  });

  it('valida longitud de 6 dígitos en desafío 2FA verify', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'VERIFY_2FA_TOTP',
        challenge_id: 'ch-verify-99',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    await wrapper.find('.verify-form').trigger('submit');
    expect(wrapper.find('.alert-banner--danger').text()).toContain('exactamente 6 dígitos');
  });

  it('permite autenticación directa cuando la API retorna usuario sin 2FA', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        user: {
          id: 'u-direct',
          email: 'direct@isp.net',
          username: 'direct_user',
          role: 'SUPPORT_L1',
          tenant_id: 't-1',
          tenant_slug: 'isp-norte',
          totp_enabled: false,
        },
        csrf_token: 'csrf-direct',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('direct@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    const authStore = useAuthStore();
    expect(authStore.isAuthenticated).toBe(true);
    expect(mockPush).toHaveBeenCalledWith('/inventory');
  });

  it('muestra mensaje de error cuando fallan las credenciales', async () => {
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Credenciales inválidas',
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('wrong@isp.net');
    await wrapper.find('#login-password').setValue('WrongPass123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.alert-banner--danger').text()).toContain('Credenciales inválidas');
  });

  it('maneja error en generación de canvas de código QR sin lanzar excepción', async () => {
    const qrcode = await import('qrcode');
    vi.spyOn(qrcode.default, 'toCanvas').mockRejectedValueOnce(new Error('Canvas failure'));

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'ENROLL_2FA_REQUIRED',
        challenge_id: 'ch-qr-fail',
        totp_provisioning_uri: 'otpauth://totp/RoSGrid:admin?secret=SECRET123',
        totp_secret: 'SECRET123',
        backup_codes: ['9999-8888'],
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('qr@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.enroll-container').exists()).toBe(true);
  });
});
