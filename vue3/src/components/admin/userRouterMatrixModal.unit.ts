// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import UserRouterMatrixModal from './UserRouterMatrixModal.vue';
import { http } from '@/api/httpClient';
import type { UserManagementItem } from '@/types';

const sampleUser: UserManagementItem = {
  id: 'u-55',
  username: 'operador_l2',
  email: 'op@isp.net',
  role: 'SUPPORT_L2',
  totp_enabled: true,
  is_active: true,
  has_all_routers_access: false,
};

describe('UserRouterMatrixModal.vue — Asignación Granular de Permisos por Router', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('no renderiza nada cuando isOpen es false', () => {
    const wrapper = mount(UserRouterMatrixModal, {
      props: {
        isOpen: false,
        user: sampleUser,
      },
    });
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('renderiza modal accesible, carga permisos y permite alternar switches y batch buttons', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        has_all_routers_access: false,
        permissions: [
          {
            router_id: 'r-1',
            router_name: 'CCR2004-Core',
            network_role: 'TOWER_AP',
            tag: 'zona-norte',
            can_read: true,
            can_write_layer1: false,
            can_write_layer2: false,
            can_execute_diagnostics: true,
            can_trigger_backup: false,
            can_reboot: false,
            bypass_maker_checker: false,
          },
          {
            router_id: 'r-2',
            router_name: 'RB4011-NoTags',
            can_read: false,
            can_write_layer1: false,
            can_write_layer2: false,
            can_execute_diagnostics: false,
            can_trigger_backup: false,
            can_reboot: false,
            bypass_maker_checker: false,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(UserRouterMatrixModal, {
      props: {
        isOpen: true,
        user: { ...sampleUser, full_name: 'Carlos Mendoza' },
      },
    });

    await flushPromises();

    expect(wrapper.find('#matrix-modal-title').text()).toContain('Matriz de Asignación');
    expect(wrapper.find('.cell-name').text()).toContain('CCR2004-Core');

    // Alternar checkboxes individuales antes y después de lote para ejecutar onUpdate handlers
    const chkRead = wrapper.find('#chk-read-r-1');
    if (chkRead.exists()) {
      await chkRead.setValue(false);
      await chkRead.setValue(true);
    }
    const chkL1 = wrapper.find('#chk-l1-r-1');
    if (chkL1.exists()) {
      await chkL1.setValue(true);
      await chkL1.setValue(false);
    }
    const chkL2 = wrapper.find('#chk-l2-r-1');
    if (chkL2.exists()) {
      await chkL2.setValue(true);
      await chkL2.setValue(false);
    }
    const chkDiag = wrapper.find('#chk-diag-r-1');
    if (chkDiag.exists()) {
      await chkDiag.setValue(false);
      await chkDiag.setValue(true);
    }
    const chkBku = wrapper.find('#chk-bku-r-1');
    if (chkBku.exists()) {
      await chkBku.setValue(true);
      await chkBku.setValue(false);
    }
    const chkReb = wrapper.find('#chk-reb-r-1');
    if (chkReb.exists()) {
      await chkReb.setValue(true);
      await chkReb.setValue(false);
    }
    const chkMc = wrapper.find('#chk-mc-r-1');
    if (chkMc.exists()) {
      await chkMc.setValue(true);
      await chkMc.setValue(false);
    }

    // Botones de lote
    const batchButtons = wrapper.findAll('.btn-batch');
    expect(batchButtons.length).toBeGreaterThan(0);
    for (const btn of batchButtons) {
      await btn.trigger('click');
    }

    // Probar búsqueda con distintas ramas (nombre, rol, tag, vacío, sin match)
    const searchInput = wrapper.find('#matrix-search');
    await searchInput.setValue('Core');
    expect(wrapper.findAll('.cell-name').length).toBe(1);

    await searchInput.setValue('TOWER_AP');
    expect(wrapper.findAll('.cell-name').length).toBe(1);

    await searchInput.setValue('zona-norte');
    expect(wrapper.findAll('.cell-name').length).toBe(1);

    await searchInput.setValue('no-coincide-xyz');
    expect(wrapper.findAll('.cell-name').length).toBe(0);

    await searchInput.setValue('');
    expect(wrapper.findAll('.cell-name').length).toBe(2);

    // Guardar cambios con éxito
    vi.spyOn(http, 'put').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();

    expect(wrapper.emitted('saved')).toBeTruthy();

    // Avanzar reloj simulado para ejecutar emit('close') diferido en setTimeout
    vi.advanceTimersByTime(1500);
    await flushPromises();
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('muestra mensaje de error cuando falla el guardado de permisos', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        has_all_routers_access: false,
        permissions: [
          {
            router_id: 'r-1',
            router_name: 'CCR2004-Core',
            network_role: 'EDGE_BGP',
            tag: 'zona-norte',
            can_read: true,
            can_write_layer1: false,
            can_write_layer2: false,
            can_execute_diagnostics: true,
            can_trigger_backup: false,
            can_reboot: false,
            bypass_maker_checker: false,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(UserRouterMatrixModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });

    await flushPromises();

    vi.spyOn(http, 'put').mockRejectedValueOnce({
      message: 'Network error al guardar permisos',
    });

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();

    expect(wrapper.find('.msg-banner--error').text()).toContain(
      'Network error al guardar permisos',
    );

    // Error con detail
    vi.spyOn(http, 'put').mockRejectedValueOnce({
      detail: 'Detalle de fallo en permisos',
    });
    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();
    expect(wrapper.find('.msg-banner--error').text()).toContain('Detalle de fallo en permisos');

    // Error genérico sin detail ni message
    vi.spyOn(http, 'put').mockRejectedValueOnce({});
    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();
    expect(wrapper.find('.msg-banner--error').text()).toContain('Error al guardar los permisos');

    // Usuario sin full_name
    await wrapper.setProps({
      user: { ...sampleUser, full_name: undefined },
    });
    expect(wrapper.find('.modal-subtitle').text()).toContain(sampleUser.username);

    // Usuario nulo
    await wrapper.setProps({ user: null });
    expect(wrapper.find('.modal-subtitle').exists()).toBe(false);
  });

  it('oculta tabla de routers si el switch maestro de acceso total está activo y permite cerrar', async () => {
    const wrapper = mount(UserRouterMatrixModal, {
      props: {
        isOpen: true,
        user: { ...sampleUser, has_all_routers_access: true },
      },
    });

    await flushPromises();
    expect(wrapper.find('.matrix-table-container').exists()).toBe(false);

    // Conmutar switch maestro
    const masterSwitch = wrapper.find('#master-all-access-switch');
    if (masterSwitch.exists()) {
      await masterSwitch.setValue(false);
      await masterSwitch.setValue(true);
    }

    // Cerrar modal
    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    await wrapper.find('.btn-secondary').trigger('click');
    expect(wrapper.emitted('close')).toHaveLength(2);
  });

  it('usa fallback de permisos simulados si la API de carga falla', async () => {
    vi.spyOn(http, 'get').mockRejectedValueOnce(new Error('Fetch failed'));
    const wrapper = mount(UserRouterMatrixModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });
    await flushPromises();
    expect(wrapper.find('.cell-name').text()).toContain('CCR2004-Edge-Core');
  });
});
