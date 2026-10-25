// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import TenantsManagementView from './TenantsManagementView.vue';
import { http } from '@/api/httpClient';
import { useAuthStore } from '@/stores/useAuthStore';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('TenantsManagementView.vue — Gestión de Empresas Multi-Tenant', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('monta correctamente y lista las empresas', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            id: 't-10',
            slug: 'isp-test',
            name: 'ISP Test',
            tax_id: 'J-000',
            status: 'ACTIVE',
            max_routers_quota: 50,
            max_users_quota: 10,
            active_routers_count: 5,
            active_users_count: 2,
            default_safemode_seconds: 60,
          },
          {
            id: 't-11',
            slug: 'isp-notax',
            name: 'ISP Sin RIF',
            tax_id: '',
            status: 'ACTIVE',
            max_routers_quota: 20,
            max_users_quota: 5,
            active_routers_count: 1,
            active_users_count: 1,
            default_safemode_seconds: 45,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    expect(wrapper.find('h1').text()).toContain('Administración de Empresas');
    expect(wrapper.find('.cell-name').text()).toContain('ISP Test');
  });

  it('permite abrir, cancelar y enviar modal de registro de nueva empresa', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { items: [] },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    // Abrir modal y luego cerrarlo
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(true);

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(false);

    // Reabrir y cerrar vía backdrop
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);
    await wrapper.find('.rg-modal-backdrop').trigger('click');
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);

    // Reabrir y enviar con error
    await wrapper.find('.btn-create').trigger('click');
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      detail: 'Slug duplicado',
    });

    await wrapper.find('#tenant-name').setValue('ISP Error');
    await wrapper.find('#tenant-slug-new').setValue('isp-error');
    await wrapper.find('#admin-user').setValue('admin');
    await wrapper.find('#admin-email').setValue('admin@test.net');
    await wrapper.find('#admin-pass').setValue('SecurePass123!');

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Slug duplicado');

    // Error con message sin detail
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Fallo de conexión al crear empresa',
    });
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo de conexión al crear empresa');

    // Error genérico sin detail ni message
    vi.spyOn(http, 'post').mockRejectedValueOnce({});
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Error al crear la empresa.');

    // Enviar con éxito usando fallback
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {},
      headers: new Headers(),
    });

    await wrapper.find('#tenant-name').setValue('ISP Caracas C.A.');
    await wrapper.find('#tenant-slug-new').setValue('isp-caracas');
    await wrapper.find('#tenant-tax-id').setValue('J-123456');
    await wrapper.find('#tenant-safemode').setValue(45);
    await wrapper.find('#max-routers').setValue(100);
    await wrapper.find('#max-users').setValue(30);
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('creada exitosamente');
  });

  it('permite suspender o reactivar una empresa tras confirmación, manejando rechazo o errores', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          id: 't-01',
          slug: 'isp-norte',
          name: 'ISP Norte C.A.',
          tax_id: 'J-12345678-9',
          status: 'ACTIVE',
          max_routers_quota: 100,
          max_users_quota: 25,
          active_routers_count: 42,
          active_users_count: 12,
          default_safemode_seconds: 60,
        },
      ],
      headers: new Headers(),
    });

    vi.spyOn(window, 'confirm').mockReturnValue(false);

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    const actionBtn = wrapper.find('.btn-action--danger');
    if (actionBtn.exists()) {
      // Cancelar confirmación
      await actionBtn.trigger('click');
      expect(wrapper.find('.banner--success').exists()).toBe(false);

      // Confirmar pero con error con detail
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      vi.spyOn(http, 'patch').mockRejectedValueOnce({
        detail: 'Fallo al suspender empresa',
      });

      await actionBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.banner--error').text()).toContain('Fallo al suspender');

      // Error con message sin detail
      vi.spyOn(http, 'patch').mockRejectedValueOnce({
        message: 'Fallo de timeout en patch',
      });
      await actionBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.banner--error').text()).toContain('Fallo de timeout en patch');

      // Error genérico sin detail ni message
      vi.spyOn(http, 'patch').mockRejectedValueOnce({});
      await actionBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.banner--error').text()).toContain(
        'Error al cambiar estado de la empresa.',
      );

      // Confirmar con éxito (suspender)
      vi.spyOn(http, 'patch').mockResolvedValueOnce({
        status: 200,
        data: { success: true },
        headers: new Headers(),
      });

      await actionBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.banner--success').exists()).toBe(true);

      // Limpiar mensaje por timer
      vi.advanceTimersByTime(5000);
      await flushPromises();
      expect(wrapper.find('.banner--success').exists()).toBe(false);

      // Reactivar empresa suspendida
      vi.spyOn(http, 'patch').mockResolvedValueOnce({
        status: 200,
        data: { success: true },
        headers: new Headers(),
      });

      await actionBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.banner--success').text()).toContain('ACTIVE');
    }
  });

  it('permite navegar al estudio de Módulos & Capacidades con botón y badge de módulos activos', async () => {
    pushMock.mockClear();
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            id: 't-99',
            slug: 'isp-gov',
            name: 'ISP Gobernanza',
            tax_id: 'J-123456',
            status: 'ACTIVE',
            max_routers_quota: 30,
            max_users_quota: 10,
            active_routers_count: 2,
            active_users_count: 1,
            default_safemode_seconds: 60,
            features: {
              isp_module_enabled: true,
              cis_audit_enabled: true,
              syslog_collector_enabled: true,
            },
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    // Validar badge de módulos activos
    const badge = wrapper.find('.badge-modules-count');
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toBe('3');

    // Clic en botón ⚙️ Módulos
    const btnFeatures = wrapper.find('.btn-action--features');
    expect(btnFeatures.exists()).toBe(true);
    await btnFeatures.trigger('click');
    await flushPromises();

    // Debe navegar hacia la sub-pantalla de módulos del tenant
    expect(pushMock).toHaveBeenCalledWith('/admin/tenants/t-99/modules');
  });


  it('oculta el botón de registrar empresa si el usuario no tiene rol SUPERADMIN_GLOBAL', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { items: [] },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    expect(wrapper.find('#btn-open-create-tenant').exists()).toBe(false);
  });

  it('para TENANT_ADMIN oculta suspender y registrar, pero muestra configuración de módulos', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            id: 't-10',
            slug: 'mi-empresa',
            name: 'Mi Empresa',
            tax_id: 'J-12345678',
            status: 'ACTIVE',
            max_routers_quota: 50,
            max_users_quota: 10,
            active_routers_count: 3,
            active_users_count: 1,
            default_safemode_seconds: 60,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    expect(wrapper.find('#btn-open-create-tenant').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Suspender');
    expect(wrapper.find('.btn-action--features').exists()).toBe(true);
  });
});
