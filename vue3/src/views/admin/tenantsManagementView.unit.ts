/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

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

  it('muestra correctamente el estado de telemetría de beacon y actualiza tras disparar latido', async () => {
    let currentBeaconData = {
      enabled: true,
      instance_id: '9ce21f55a851ed11a59d48b7c0ba02ad6fd2bdbe5ddf87bdaab637fb344c511f',
      last_sent_at: '2026-11-01T23:08:40Z',
      last_heartbeat_at: '2026-11-01T23:08:40Z',
      last_status: 'http_202',
      fleet_bucket: '1-10',
      router_count: 7,
    };

    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url.includes('/api/v1/system/telemetry-beacon/status')) {
        return Promise.resolve({
          status: 200,
          data: currentBeaconData,
          headers: new Headers(),
        });
      }
      return Promise.resolve({
        status: 200,
        data: { items: [] },
        headers: new Headers(),
      });
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    const beaconCard = wrapper.find('.beacon-card');
    expect(beaconCard.exists()).toBe(true);
    expect(beaconCard.text()).toContain('9ce21f55a851ed11a59d48b7c0ba02ad6fd2bdbe5ddf87bdaab637fb344c511f');
    expect(beaconCard.text()).toContain('7 routers (1-10)');
    expect(beaconCard.text()).toContain(new Date('2026-11-01T23:08:40Z').toLocaleString());
    expect(beaconCard.text()).not.toContain('[http_202]');

    // Probar emisión manual de latido
    vi.spyOn(http, 'post').mockImplementation((url: string) => {
      if (url.includes('/api/v1/system/telemetry-beacon/trigger')) {
        currentBeaconData = {
          ...currentBeaconData,
          last_sent_at: '2026-11-01T23:15:00Z',
          last_heartbeat_at: '2026-11-01T23:15:00Z',
        };
        return Promise.resolve({
          status: 200,
          data: {
            message: 'Latido de telemetría emitido con éxito.',
            ...currentBeaconData,
          },
          headers: new Headers(),
        });
      }
      return Promise.resolve({ status: 200, data: {}, headers: new Headers() });
    });

    const btnTrigger = wrapper.find('#btn-trigger-beacon');
    expect(btnTrigger.exists()).toBe(true);
    expect(btnTrigger.classes()).toContain('btn-beacon');
    await btnTrigger.trigger('click');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('Latido de telemetría emitido con éxito.');
    expect(beaconCard.text()).toContain(new Date('2026-11-01T23:15:00Z').toLocaleString());
  });

  it('permite editar los datos y cuotas de una organización existente vía PATCH /api/v1/tenants/:id (Hito 28.11)', async () => {
    const mockTenants = [
      {
        id: 't-01',
        slug: 'isp-norte',
        name: 'ISP Norte',
        tax_id: 'J-12345678-0',
        status: 'ACTIVE',
        max_routers_quota: 50,
        max_users_quota: 20,
        active_routers_count: 5,
        active_users_count: 2,
        default_safemode_seconds: 60,
        require_2fa_all_users: true,
      },
    ];

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: { items: mockTenants },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    const editBtn = wrapper.find('#btn-edit-tenant-isp-norte');
    expect(editBtn.exists()).toBe(true);
    await editBtn.trigger('click');

    expect(wrapper.find('#modal-edit-tenant').exists()).toBe(true);
    await wrapper.find('#edit-tenant-name').setValue('ISP Norte Renovado C.A.');
    await wrapper.find('#edit-tenant-tax-id').setValue('J-99999999-9');
    await wrapper.find('#edit-max-routers').setValue('150');
    await wrapper.find('#edit-max-users').setValue('45');
    await wrapper.find('#edit-tenant-safemode').setValue('45');

    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: {
        ...mockTenants[0],
        name: 'ISP Norte Renovado C.A.',
        tax_id: 'J-99999999-9',
        max_routers_quota: 150,
        max_users_quota: 45,
        default_safemode_seconds: 45,
      },
      headers: new Headers(),
    });

    await wrapper.find('#form-edit-tenant').trigger('submit');
    await flushPromises();

    expect(patchSpy).toHaveBeenCalledWith(
      '/api/v1/tenants/t-01',
      expect.objectContaining({
        name: 'ISP Norte Renovado C.A.',
        slug: 'isp-norte',
        tax_id: 'J-99999999-9',
        max_routers_quota: 150,
        max_users_quota: 45,
        default_safemode_seconds: 45,
      }),
    );
    expect(wrapper.text()).toContain('Datos y cuotas de "ISP Norte Renovado C.A." actualizados exitosamente.');
  });

  it('permite registrar coordenadas GPS de sede principal y capturar ubicación al crear empresa (Spec 104)', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: { items: [] },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('#modal-create-tenant').exists()).toBe(true);

    const latInput = wrapper.find('#input-tenant-hq-lat');
    const lngInput = wrapper.find('#input-tenant-hq-lng');
    const gpsBtn = wrapper.find('#btn-tenant-capture-gps');

    expect(latInput.exists()).toBe(true);
    expect(lngInput.exists()).toBe(true);
    expect(gpsBtn.exists()).toBe(true);

    // Probar captura GPS con mock de navigator.geolocation
    const originalGeolocation = navigator.geolocation;
    const mockGeolocation = {
      getCurrentPosition: vi.fn().mockImplementation((success) => {
        success({
          coords: {
            latitude: 10.254321,
            longitude: -67.587654,
          },
        });
      }),
    };
    Object.defineProperty(navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true,
    });

    await gpsBtn.trigger('click');
    expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();

    // Rellenar datos obligatorios
    await wrapper.find('#tenant-name').setValue('ISP Geoubicado S.A.');
    await wrapper.find('#tenant-slug-new').setValue('isp-geoubicado');
    await wrapper.find('#admin-user').setValue('geoadmin');
    await wrapper.find('#admin-email').setValue('geoadmin@isp.test');
    await wrapper.find('#admin-pass').setValue('Password123!');

    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {
        id: 't-geo',
        name: 'ISP Geoubicado S.A.',
        slug: 'isp-geoubicado',
        hq_latitude: 10.254321,
        hq_longitude: -67.587654,
      },
      headers: new Headers(),
    });

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/tenants',
      expect.objectContaining({
        name: 'ISP Geoubicado S.A.',
        slug: 'isp-geoubicado',
        hq_latitude: 10.254321,
        hq_longitude: -67.587654,
      }),
    );

    // Restaurar geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      writable: true,
      configurable: true,
    });
  });

  it('permite editar coordenadas GPS de sede principal en modal de edición (Spec 104)', async () => {
    const mockTenants = [
      {
        id: 't-02',
        slug: 'isp-sur',
        name: 'ISP Sur',
        tax_id: 'J-22222222-2',
        status: 'ACTIVE',
        max_routers_quota: 30,
        max_users_quota: 10,
        active_routers_count: 2,
        active_users_count: 1,
        default_safemode_seconds: 60,
        require_2fa_all_users: true,
        hq_latitude: 10.200000,
        hq_longitude: -67.800000,
      },
    ];

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: { items: mockTenants },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    const editBtn = wrapper.find('#btn-edit-tenant-isp-sur');
    expect(editBtn.exists()).toBe(true);
    await editBtn.trigger('click');

    const latEdit = wrapper.find('#edit-tenant-hq-lat');
    const lngEdit = wrapper.find('#edit-tenant-hq-lng');
    const gpsBtnEdit = wrapper.find('#btn-tenant-capture-gps-edit');

    expect(latEdit.exists()).toBe(true);
    expect(lngEdit.exists()).toBe(true);
    expect(gpsBtnEdit.exists()).toBe(true);

    await latEdit.setValue('10.450000');
    await lngEdit.setValue('-66.850000');

    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: {
        ...mockTenants[0],
        hq_latitude: 10.45,
        hq_longitude: -66.85,
      },
      headers: new Headers(),
    });

    await wrapper.find('#form-edit-tenant').trigger('submit');
    await flushPromises();

    expect(patchSpy).toHaveBeenCalledWith(
      '/api/v1/tenants/t-02',
      expect.objectContaining({
        hq_latitude: 10.45,
        hq_longitude: -66.85,
      }),
    );
  });

  it('actualiza inmediatamente authStore.tenantFeatures cuando se edita la empresa activa (Spec 105)', async () => {
    const authStore = useAuthStore();
    authStore.tenantSlug = 'isp-sur';
    const updateSpy = vi.spyOn(authStore, 'updateTenantFeatures');
    const fetchSpy = vi.spyOn(authStore, 'fetchTenantFeatures').mockResolvedValue();

    const mockTenants = [
      {
        id: 't-02',
        slug: 'isp-sur',
        name: 'ISP Sur',
        tax_id: 'J-87654321-0',
        status: 'ACTIVE',
        max_routers_quota: 30,
        max_users_quota: 15,
        active_routers_count: 3,
        active_users_count: 1,
        default_safemode_seconds: 60,
        require_2fa_all_users: true,
        hq_latitude: 10.2123,
        hq_longitude: -67.9876,
      },
    ];

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: { items: mockTenants },
      headers: new Headers(),
    });

    const wrapper = mount(TenantsManagementView);
    await flushPromises();

    const editBtn = wrapper.find('#btn-edit-tenant-isp-sur');
    await editBtn.trigger('click');

    await wrapper.find('#edit-tenant-hq-lat').setValue('10.450000');
    await wrapper.find('#edit-tenant-hq-lng').setValue('-66.850000');

    vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: {
        ...mockTenants[0],
        hq_latitude: 10.45,
        hq_longitude: -66.85,
      },
      headers: new Headers(),
    });

    await wrapper.find('#form-edit-tenant').trigger('submit');
    await flushPromises();

    expect(updateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        hq_latitude: 10.45,
        hq_longitude: -66.85,
      }),
    );
    expect(fetchSpy).toHaveBeenCalled();
  });
});
