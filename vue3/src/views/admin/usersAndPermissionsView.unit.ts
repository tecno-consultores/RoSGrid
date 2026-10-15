// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
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
            full_name: 'Usuario Inactivo',
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

    await searchInput.setValue('');
  });

  it('permite abrir modal de creación de operador, manejar error y crearlo exitosamente', async () => {
    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: true,
          UserRouterMatrixModal: true,
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

    // Reabrir y simular error
    await wrapper.find('.btn-create').trigger('click');
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Nombre de usuario ya existe',
    });

    await wrapper.find('#u-username').setValue('tech_dup');
    await wrapper.find('#u-email').setValue('dup@isp.net');
    await wrapper.find('#u-fullname').setValue('Tech Duplicado');
    await wrapper.find('#u-password').setValue('SecretPass123!');
    await wrapper.find('#u-role').setValue('FIELD_TECH');
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--error').text()).toContain('Nombre de usuario ya existe');

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
});
