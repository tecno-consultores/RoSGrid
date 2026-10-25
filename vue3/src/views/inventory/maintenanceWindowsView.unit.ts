// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import MaintenanceWindowsView from '../MaintenanceWindowsView.vue';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { http } from '@/api/httpClient';
import type { RouterItem } from '@/types';

const SAMPLE_ROUTER_1: RouterItem = {
  id: 'r-01',
  tenant_id: 't-1',
  display_name: 'CORE-01',
  ip_address: '192.168.88.1',
  api_port: 443,
  ros_version: 'v7',
  admin_state: 'PRODUCTION',
  network_role: 'CORE',
  model: 'CCR2004',
  is_reachable: true,
};

const SAMPLE_ROUTER_2: RouterItem = {
  id: 'r-02',
  tenant_id: 't-1',
  display_name: 'EDGE-02',
  ip_address: '10.0.0.1',
  api_port: 443,
  ros_version: 'v7',
  admin_state: 'PRODUCTION',
  network_role: 'EDGE_BGP',
  model: 'RB5009',
  is_reachable: true,
};

describe('MaintenanceWindowsView.vue — Ventanas de Mantenimiento Programadas', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    vi.useFakeTimers();

    const inventoryStore = useInventoryStore();
    inventoryStore.setRouters([SAMPLE_ROUTER_1, SAMPLE_ROUTER_2]);

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/maintenance/windows')) {
        return {
          status: 200,
          data: [
            {
              id: 'mw-99',
              tenant_id: 't-1',
              router_id: 'r-01',
              title: 'Parche de Seguridad',
              reason: 'Actualización ROS v7',
              starts_at: new Date().toISOString(),
              ends_at: new Date(Date.now() + 3600000).toISOString(),
              suppress_alerts: true,
              is_cancelled: false,
            },
          ],
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });
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
            router_id: 'r-01',
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

    // Muestra el nombre del router amigable
    expect(wrapper.find('.badge-target--router').text()).toContain('CORE-01');

    // Cancelar rechazada por confirmación
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    await wrapper.find('.btn-cancel-window').trigger('click');
    expect(wrapper.find('.banner--success').exists()).toBe(false);

    // Cancelar con error de red
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Fallo al cancelar ventana',
    });

    await wrapper.find('.btn-cancel-window').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo al cancelar');

    // Cancelar exitosa vía POST /windows/{id}/cancel
    vi.spyOn(http, 'post').mockResolvedValueOnce({
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

  it('permite abrir modal, seleccionar routers de la lista interactiva y programar ventana cerrando el modal', async () => {
    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    // Abrir y cerrar modal con botón X
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(true);

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(false);

    // Reabrir y verificar selección de routers interactiva
    await wrapper.find('.btn-create').trigger('click');
    expect(wrapper.find('.router-checklist').exists()).toBe(true);

    // Marcar checkbox del primer router
    const checkboxes = wrapper.findAll('.router-checkbox');
    expect(checkboxes.length).toBeGreaterThanOrEqual(2);
    await checkboxes[0].setValue(true);

    // Llenar campos requeridos
    await wrapper.find('#mw-title').setValue('Actualización RouterOS v7.18');
    await wrapper.find('#mw-reason').setValue('Parche de vulnerabilidad y mejoras BGP');
    await wrapper.find('#mw-starts').setValue('2026-10-25T10:00');
    await wrapper.find('#mw-ends').setValue('2026-10-25T12:00');

    // Simular error de servidor al enviar
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Error simulado de validación',
    });

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--error').text()).toContain('Error simulado');
    // Si falla, el modal debe permanecer para que el usuario corrija
    expect(wrapper.find('.rg-modal').exists()).toBe(true);

    // Ahora simular creación exitosa en backend
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {
        id: 'mw-nuevo-1',
        tenant_id: 't-1',
        title: 'Actualización RouterOS v7.18',
        reason: 'Parche de vulnerabilidad y mejoras BGP',
        router_id: 'r-01',
        starts_at: '2026-10-25T10:00:00Z',
        ends_at: '2026-10-25T12:00:00Z',
        suppress_alerts: true,
        is_cancelled: false,
        created_by: 'u-1',
        created_at: new Date().toISOString(),
      },
      headers: new Headers(),
    });

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    // 1. Mensaje de éxito visible
    expect(wrapper.find('.banner--success').text()).toContain('programada exitosamente');
    // 2. ¡EL MODAL DEBE ESTAR CERRADO!
    expect(wrapper.find('.rg-modal').exists()).toBe(false);
  });

  it('permite cambiar a alcance por etiqueta (tag) o global y crear ventana', async () => {
    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    await wrapper.find('.btn-create').trigger('click');

    // Cambiar a etiqueta
    const scopeButtons = wrapper.findAll('.scope-btn');
    expect(scopeButtons.length).toBe(3);
    await scopeButtons[1].trigger('click'); // Tag

    expect(wrapper.find('#mw-tag').exists()).toBe(true);
    await wrapper.find('#mw-title').setValue('Mantenimiento Fibra');
    await wrapper.find('#mw-reason').setValue('Cambio de OLT');
    await wrapper.find('#mw-tag').setValue('ftth-norte');
    await wrapper.find('#mw-starts').setValue('2026-10-25T14:00');
    await wrapper.find('#mw-ends').setValue('2026-10-25T16:00');

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {
        id: 'mw-tag-1',
        tenant_id: 't-1',
        title: 'Mantenimiento Fibra',
        reason: 'Cambio de OLT',
        target_tag: 'ftth-norte',
        starts_at: '2026-10-25T14:00:00Z',
        ends_at: '2026-10-25T16:00:00Z',
        suppress_alerts: true,
        is_cancelled: false,
        created_by: 'u-1',
        created_at: new Date().toISOString(),
      },
      headers: new Headers(),
    });

    await wrapper.find('.modal-form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.banner--success').text()).toContain('programada exitosamente');
    expect(wrapper.find('.rg-modal').exists()).toBe(false);
  });

  it('bloquea la escritura manual por teclado en inputs de fecha y permite navegación o apertura por calendario', async () => {
    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    await wrapper.find('.btn-create').trigger('click');

    const startsInput = wrapper.find('#mw-starts');
    const endsInput = wrapper.find('#mw-ends');
    expect(startsInput.exists()).toBe(true);
    expect(endsInput.exists()).toBe(true);

    // 1. Teclas normales (números, letras, backspace) deben ser bloqueadas (defaultPrevented = true)
    const keyEventA = new KeyboardEvent('keydown', { key: 'a', cancelable: true });
    startsInput.element.dispatchEvent(keyEventA);
    expect(keyEventA.defaultPrevented).toBe(true);

    const keyEventDigit = new KeyboardEvent('keydown', { key: '2', cancelable: true });
    endsInput.element.dispatchEvent(keyEventDigit);
    expect(keyEventDigit.defaultPrevented).toBe(true);

    // 2. Tecla Tab para accesibilidad no debe ser prevenida
    const keyEventTab = new KeyboardEvent('keydown', { key: 'Tab', cancelable: true });
    startsInput.element.dispatchEvent(keyEventTab);
    expect(keyEventTab.defaultPrevented).toBe(false);

    // 3. Tecla Escape para cerrar modal no debe ser prevenida
    const keyEventEscape = new KeyboardEvent('keydown', { key: 'Escape', cancelable: true });
    endsInput.element.dispatchEvent(keyEventEscape);
    expect(keyEventEscape.defaultPrevented).toBe(false);

    // 4. Los botones de disparador de calendario existen y son accesibles
    const calendarButtons = wrapper.findAll('.btn-calendar-trigger');
    expect(calendarButtons.length).toBe(2);
    expect(calendarButtons[0].attributes('title')).toBe('Abrir selector de fecha y hora');
    expect(calendarButtons[1].attributes('title')).toBe('Abrir selector de fecha y hora');
  });
});
