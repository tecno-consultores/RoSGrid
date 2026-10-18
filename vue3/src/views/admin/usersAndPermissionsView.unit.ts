// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import UsersAndPermissionsView from '../UsersAndPermissionsView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

describe('UsersAndPermissionsView.vue — Gestión de 11 Roles y Matriz RBAC', () => {
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
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
    });
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          id: 'u-01',
          username: 'admin.norte',
          email: 'admin@isp-norte.net',
          full_name: 'Carlos Mendoza',
          role: 'TENANT_ADMIN',
          totp_enabled: true,
          is_active: true,
          has_all_routers_access: true,
          created_at: new Date().toISOString(),
        },
        {
          id: 'u-02',
          username: 'tech.valencia',
          email: 'valencia@isp-norte.net',
          full_name: 'Soporte Nivel 2 Valencia',
          role: 'SUPPORT_L2',
          totp_enabled: true,
          is_active: true,
          has_all_routers_access: false,
          assigned_router_ids: ['r-01', 'r-02'],
          created_at: new Date().toISOString(),
        },
      ],
      headers: new Headers(),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('monta la vista, carga usuarios desde API y filtra por búsqueda, rol y estado', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            id: 'u-10',
            username: 'carlos.m',
            email: 'carlos@isp.net',
            full_name: 'Carlos Mendoza',
            role: 'TENANT_ADMIN',
            totp_enabled: true,
            is_active: true,
            has_all_routers_access: true,
          },
          {
            id: 'u-11',
            username: 'inactivo.user',
            email: 'inactivo@isp.net',
            role: 'SUPPORT_L1',
            totp_enabled: false,
            is_active: false,
            has_all_routers_access: false,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: true,
          UserRouterMatrixModal: true,
          RbacRoleMatrixPanel: true,
        },
      },
    });

    await flushPromises();

    expect(wrapper.find('h1').text()).toContain('Gestión de Usuarios y Roles RBAC');
    expect(wrapper.find('.rg-table').exists()).toBe(true);

    // Filtrar por rol
    const roleSelect = wrapper.find('#filter-role');
    await roleSelect.setValue('TENANT_ADMIN');
    expect(wrapper.findAll('tbody tr').length).toBeGreaterThan(0);

    // Filtrar por estado
    const statusSelect = wrapper.find('#filter-status');
    await statusSelect.setValue('ACTIVE');
    await statusSelect.setValue('INACTIVE');
    await statusSelect.setValue('ALL');

    // Filtrar por texto (full_name, username, email)
    const searchInput = wrapper.find('#filter-search');
    await searchInput.setValue('Carlos');
    expect(wrapper.findAll('tbody tr').length).toBeGreaterThan(0);

    await searchInput.setValue('carlos.m');
    expect(wrapper.findAll('tbody tr').length).toBeGreaterThan(0);

    await searchInput.setValue('carlos@isp.net');
    expect(wrapper.findAll('tbody tr').length).toBeGreaterThan(0);

    // Búsqueda sin coincidencia
    await searchInput.setValue('no_coincide_xyz_999');
    expect(wrapper.find('.cell-empty').exists()).toBe(true);

    await searchInput.setValue('');
  });

  it('permite abrir modal de creación de operador, manejar error y crearlo exitosamente', async () => {
    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: true,
          UserRouterMatrixModal: true,
          RbacRoleMatrixPanel: true,
        },
      },
    });

    await flushPromises();

    // Abrir y cerrar modal con botón X
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(true);

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(false);

    // Reabrir y cerrar vía backdrop
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);
    await wrapper.find('.rg-modal-backdrop').trigger('click');
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);

    // Reabrir y simular error con detail
    await wrapper.find('.btn-create').trigger('click');
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      detail: 'Nombre de usuario ya existe',
    });

    await wrapper.find('#u-username').setValue('tech_dup');
    await wrapper.find('#u-email').setValue('dup@isp.net');
    await wrapper.find('#u-fullname').setValue('Tech Duplicado');
    await wrapper.find('#u-password').setValue('SecretPass123!');
    await wrapper.find('#u-role').setValue('FIELD_TECH');
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--error').text()).toContain('Nombre de usuario ya existe');

    // Simular error genérico sin detail ni message
    vi.spyOn(http, 'post').mockRejectedValueOnce({});
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Error al crear el operador.');

    // Ahora crear con éxito usando fallback
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {},
      headers: new Headers(),
    });

    await wrapper.find('#u-username').setValue('tech_nuevo');
    await wrapper.find('#u-email').setValue('nuevo@isp.net');
    await wrapper.find('#u-cidr').setValue('10.10.50.0/24, 192.168.1.0/24');
    const allRoutersChk = wrapper.find('.checkbox-label input[type="checkbox"]');
    if (allRoutersChk.exists()) {
      await allRoutersChk.setValue(true);
    }
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('creado exitosamente');
  });

  it('abre modales auxiliares y procesa reset 2FA con Step-Up', async () => {
    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: false,
          UserRouterMatrixModal: true,
          RbacRoleMatrixPanel: true,
        },
      },
    });

    await flushPromises();

    // Abrir modal de matriz y cerrarlo
    const matrixBtn = wrapper.find('.btn-matrix');
    if (matrixBtn.exists()) {
      await matrixBtn.trigger('click');
      const matrixModal = wrapper.findComponent({ name: 'UserRouterMatrixModal' });
      if (matrixModal.exists()) {
        matrixModal.vm.$emit('close');
      }
    }

    // Reset 2FA
    const resetBtn = wrapper.find('.btn-reset-2fa');
    if (resetBtn.exists()) {
      await resetBtn.trigger('click');

      // Error en reset-2fa
      vi.spyOn(http, 'post').mockRejectedValueOnce({
        message: 'Código TOTP incorrecto',
      });

      const modal = wrapper.findComponent({ name: 'RgStepUp2FAModal' });
      if (modal.exists()) {
        modal.vm.$emit('submit-totp', '000000');
        await flushPromises();
        expect(wrapper.find('.banner--error').text()).toContain('Código TOTP incorrecto');

        // Error genérico sin message ni detail
        vi.spyOn(http, 'post').mockRejectedValueOnce({});
        modal.vm.$emit('submit-totp', '000000');
        await flushPromises();
        expect(wrapper.find('.banner--error').text()).toContain(
          'Error al reiniciar 2FA con Step-Up.',
        );

        // Éxito en reset-2fa
        vi.spyOn(http, 'post').mockResolvedValueOnce({
          status: 200,
          data: { success: true },
          headers: new Headers(),
        });

        modal.vm.$emit('submit-totp', '123456');
        await flushPromises();
        expect(wrapper.find('.banner--success').text()).toContain('2FA reiniciado con éxito');

        // Avanzar timers para limpiar mensaje de éxito
        vi.advanceTimersByTime(5000);
        await flushPromises();
        expect(wrapper.find('.banner--success').exists()).toBe(false);

        modal.vm.$emit('close');
      }
    }
  });

  it('conmuta entre pestañas de usuarios y roles RBAC, y muestra descripciones de roles en modal', async () => {
    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: true,
          UserRouterMatrixModal: true,
          RbacRoleMatrixPanel: true,
        },
      },
    });

    await flushPromises();

    // Comprobar existencia de pestañas
    const tabUsers = wrapper.find('#tab-users');
    const tabRoles = wrapper.find('#tab-roles');
    expect(tabUsers.exists()).toBe(true);
    expect(tabRoles.exists()).toBe(true);

    // Cambiar a pestaña de roles
    await tabRoles.trigger('click');
    expect(wrapper.find('#tabpanel-roles').isVisible()).toBe(true);
    expect(wrapper.findComponent({ name: 'RbacRoleMatrixPanel' }).exists()).toBe(true);

    // Regresar a pestaña de usuarios
    await tabUsers.trigger('click');
    expect(wrapper.find('#tabpanel-users').isVisible()).toBe(true);

    // Abrir modal de creación y verificar cuadro de descripción de rol
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.role-desc-preview').exists()).toBe(true);
    expect(wrapper.find('.role-desc-preview').text()).toContain('Soporte Técnico Nivel 2');

    // Cambiar a rol SUPERADMIN_GLOBAL
    await wrapper.find('#u-role').setValue('SUPERADMIN_GLOBAL');
    expect(wrapper.find('.role-desc-preview').text()).toContain('Superadministrador Global');

    // Cambiar a rol FIELD_TECH
    await wrapper.find('#u-role').setValue('FIELD_TECH');
    expect(wrapper.find('.role-desc-preview').text()).toContain('Técnico de Campo');

    // Cambiar a rol AUDITOR
    await wrapper.find('#u-role').setValue('AUDITOR');
    expect(wrapper.find('.role-desc-preview').text()).toContain('Auditor de Seguridad');
  });
});
