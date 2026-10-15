// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import MaintenanceWindowsView from '../MaintenanceWindowsView.vue';
import { http } from '@/api/httpClient';

describe('MaintenanceWindowsView.vue — Ventanas de Mantenimiento Programadas', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('monta la vista, lista las ventanas y permite cancelarlas con manejo de errores', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            id: 'mw-99',
            tenant_id: 't-1',
            router_id: 'r-1',
            title: 'Parche de Seguridad',
            reason: 'Actualización ROS v7',
            starts_at: new Date().toISOString(),
            ends_at: new Date(Date.now() + 3600000).toISOString(),
            suppress_alerts: true,
            is_cancelled: false,
          },
          {
            id: 'mw-100',
            tenant_id: 't-1',
            target_tag: 'zona-norte',
            title: 'Mantenimiento Tag',
            reason: 'Antenas',
            starts_at: new Date().toISOString(),
            ends_at: new Date(Date.now() + 3600000).toISOString(),
            suppress_alerts: true,
            is_cancelled: false,
          },
          {
            id: 'mw-101',
            tenant_id: 't-1',
            title: 'Mantenimiento Global',
            reason: 'Data center',
            starts_at: new Date().toISOString(),
            ends_at: new Date(Date.now() + 3600000).toISOString(),
            suppress_alerts: false,
            is_cancelled: true,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    expect(wrapper.find('h1').text()).toContain('Ventanas de Mantenimiento');
    expect(wrapper.find('.cell-title strong').text()).toBe('Parche de Seguridad');

    // Cancelar rechazada por confirmación
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    await wrapper.find('.btn-cancel-window').trigger('click');
    expect(wrapper.find('.banner--success').exists()).toBe(false);

    // Cancelar con error de red
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.spyOn(http, 'delete').mockRejectedValueOnce({
      message: 'Fallo al cancelar ventana',
    });

    await wrapper.find('.btn-cancel-window').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo al cancelar');

    // Cancelar exitosa
    vi.spyOn(http, 'delete').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-cancel-window').trigger('click');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('cancelada exitosamente');

    // Avanzar reloj para limpiar mensaje por timer
    vi.advanceTimersByTime(5000);
    await flushPromises();
    expect(wrapper.find('.banner--success').exists()).toBe(false);
  });

  it('permite abrir modal, manejar error y programar nueva ventana de mantenimiento', async () => {
    const wrapper = mount(MaintenanceWindowsView);
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
      message: 'Rango de fechas inválido',
    });

    await wrapper.find('#mw-title').setValue('Cambio de Fibra');
    await wrapper.find('#mw-reason').setValue('Empalme');
    await wrapper.find('#mw-router').setValue('r-01');
    await wrapper.find('#mw-tag').setValue('zona-norte');
    await wrapper.find('#mw-starts').setValue('2026-10-20T10:00');
    await wrapper.find('#mw-ends').setValue('2026-10-20T12:00');
    const chk = wrapper.find('.checkbox-label input[type="checkbox"]');
    await chk.setValue(false);
    await chk.setValue(true);

    // Cancelar con botón Cancelar del modal
    await wrapper.find('.btn-cancel').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(false);

    // Reabrir modal
    await wrapper.find('.btn-create').trigger('click');
    await wrapper.find('#mw-title').setValue('Cambio de Fibra');
    await wrapper.find('#mw-starts').setValue('2026-10-20T10:00');
    await wrapper.find('#mw-ends').setValue('2026-10-20T12:00');
    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Rango de fechas inválido');

    // Ahora enviar con éxito usando fallback
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {},
      headers: new Headers(),
    });

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('programada exitosamente');
  });
});
