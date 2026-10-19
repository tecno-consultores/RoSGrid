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
    let wrapper = mount(LoginView);
    expect(wrapper.find('.alert-banner--warning').text()).toContain('Tu sesión fue revocada');

    mockQuery = { reason: 'killed_by_admin' };
    wrapper = mount(LoginView);
    expect(wrapper.find('.alert-banner--warning').text()).toContain('Tu sesión fue revocada');

    mockQuery = { reason: 'session_expired' };
    wrapper = mount(LoginView);
    expect(wrapper.find('.alert-banner--warning').text()).toContain('Tu sesión ha expirado');

    mockQuery = { reason: 'unauthorized' };
    wrapper = mount(LoginView);
    expect(wrapper.find('.alert-banner--warning').text()).toContain('Debes iniciar sesión');
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
    expect(mockPush).toHaveBeenCalledWith('/');
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

  it('expira el desafío 2FA y regresa a CREDENTIALS al llegar a 0 el temporizador', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'VERIFY_2FA_TOTP',
        challenge_id: 'ch-expire',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    // Avanzar reloj 185 segundos para expirar el desafío
    vi.advanceTimersByTime(185000);
    await flushPromises();

    expect(wrapper.find('.alert-banner--danger').text()).toContain('ha expirado');
    expect(wrapper.find('.login-form').exists()).toBe(true);

    // Desmontar para cubrir onBeforeUnmount con stopCountdown
    wrapper.unmount();
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

  it('permite alternar a modo código de respaldo y valida 8 caracteres alfanuméricos', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        next_step: 'VERIFY_2FA_TOTP',
        challenge_id: 'ch-verify-backup',
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await wrapper.find('#tenant-slug').setValue('isp-norte');
    await wrapper.find('#login-email').setValue('admin@isp.net');
    await wrapper.find('#login-password').setValue('Password123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    // Clic en alternar a código de respaldo
    await wrapper.find('.btn-toggle-backup').trigger('click');
    expect(wrapper.find('.step-title').text()).toContain('Código de Respaldo');

    // Intentar enviar con menos de 8 caracteres
    await wrapper.find('#verify-totp-input').setValue('123');
    await wrapper.find('.verify-form').trigger('submit');
    expect(wrapper.find('.alert-banner--danger').text()).toContain('exactamente 8 caracteres');

    // Ingresar código de respaldo válido de 8 caracteres
    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        user: {
          id: 'u-1',
          email: 'admin@isp.net',
          username: 'admin',
          role: 'SUPERADMIN_GLOBAL',
          tenant_id: 't-1',
          tenant_slug: 'isp-norte',
          totp_enabled: true,
        },
        csrf_token: 'csrf-backup',
      },
      headers: new Headers(),
    });

    await wrapper.find('#verify-totp-input').setValue('8BB8B5C7');
    await flushPromises();
    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/auth/2fa/verify',
      expect.objectContaining({
        totp_code: '8BB8B5C7',
      }),
    );
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
    expect(mockPush).toHaveBeenCalledWith('/');
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

  it('detecta automáticamente primer uso y activa el paso BOOTSTRAP si is_bootstrapped es false', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    expect(wrapper.find('#bootstrap-tenant-name').exists()).toBe(true);
    expect(wrapper.find('h2').text()).toContain('Configuración Inicial de RoSGrid');
  });

  it('valida campos obligatorios y contraseñas en el formulario de bootstrap', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    // 1. Campos vacíos
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'Todos los campos marcados con asterisco son obligatorios.',
    );

    // 2. Contraseña corta (<12)
    await wrapper.find('#bootstrap-tenant-name').setValue('Empresa Master');
    await wrapper.find('#bootstrap-tenant-slug').setValue('master');
    await wrapper.find('#bootstrap-admin-user').setValue('superadmin');
    await wrapper.find('#bootstrap-admin-email').setValue('admin@empresa.com');
    await wrapper.find('#bootstrap-admin-name').setValue('Super Administrador');
    await wrapper.find('#bootstrap-admin-pass').setValue('corta');
    await wrapper.find('#bootstrap-admin-pass-confirm').setValue('corta');
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'La contraseña debe tener al menos 12 caracteres.',
    );

    // 3. Contraseñas no coinciden
    await wrapper.find('#bootstrap-admin-pass').setValue('PasswordLargo123!');
    await wrapper.find('#bootstrap-admin-pass-confirm').setValue('PasswordDiferente123!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.alert-banner--danger').text()).toContain('Las contraseñas no coinciden.');
  });

  it('ejecuta bootstrap inicial exitoso y transiciona a ENROLL_2FA', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {
        status: 'success',
        tenant_slug: 'master',
        admin_username: 'superadmin',
        totp_secret: 'JBSWY3DPEHPK3PXP',
        totp_provisioning_uri: 'otpauth://totp/RoSGrid:superadmin?secret=JBSWY3DPEHPK3PXP',
        backup_codes: ['AAAA-1111', 'BBBB-2222'],
      },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    const slugInput = wrapper.find('#bootstrap-tenant-slug');
    await slugInput.setValue('Master_Org!');
    await slugInput.trigger('input');

    await wrapper.find('#bootstrap-tenant-name').setValue('Empresa Master');
    await wrapper.find('#bootstrap-tenant-slug').setValue('master');
    await wrapper.find('#bootstrap-admin-user').setValue('superadmin');
    await wrapper.find('#bootstrap-admin-email').setValue('admin@master.com');
    await wrapper.find('#bootstrap-admin-name').setValue('Super Administrador');
    await wrapper.find('#bootstrap-admin-pass').setValue('ClaveSegura2026!');
    await wrapper.find('#bootstrap-admin-pass-confirm').setValue('ClaveSegura2026!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.enroll-container').exists()).toBe(true);
    expect(wrapper.find('.secret-key').text()).toContain('JBSWY3DPEHPK3PXP');

    const downloadBtn = wrapper.find('.btn-download-backup');
    if (downloadBtn.exists()) {
      await downloadBtn.trigger('click');
    }
  });

  it('maneja error en bootstrap inicial mostrando mensaje de error', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockRejectedValueOnce({
      detail: 'El sistema ya ha sido inicializado.',
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    await wrapper.find('#bootstrap-tenant-name').setValue('Empresa Master');
    await wrapper.find('#bootstrap-tenant-slug').setValue('master');
    await wrapper.find('#bootstrap-admin-user').setValue('superadmin');
    await wrapper.find('#bootstrap-admin-email').setValue('admin@master.com');
    await wrapper.find('#bootstrap-admin-name').setValue('Super Administrador');
    await wrapper.find('#bootstrap-admin-pass').setValue('ClaveSegura2026!');
    await wrapper.find('#bootstrap-admin-pass-confirm').setValue('ClaveSegura2026!');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'El sistema ya ha sido inicializado.',
    );
  });

  it('renderiza pie de página institucional accesible con atribución, versión, licencia y enlace a GitHub', async () => {
    const wrapper = mount(LoginView);
    await flushPromises();

    const footer = wrapper.find('footer.login-footer');
    expect(footer.exists()).toBe(true);
    expect(footer.text()).toContain('Elaborado por');
    expect(footer.text()).toContain('Tecno Consultores 2023 C.A.');
    expect(footer.text()).toContain('v1.0');
    expect(footer.text()).toContain('Licencia GNU GPLv3');

    const tecnoLink = footer.find('a[href="https://www.tecnoconsultores.net/"]');
    expect(tecnoLink.exists()).toBe(true);
    expect(tecnoLink.attributes('target')).toBe('_blank');

    const githubLink = footer.find('a[href="https://github.com/tecno-consultores/RoSGrid/"]');
    expect(githubLink.exists()).toBe(true);
    expect(githubLink.attributes('aria-label')).toContain('GitHub');
  });
});
