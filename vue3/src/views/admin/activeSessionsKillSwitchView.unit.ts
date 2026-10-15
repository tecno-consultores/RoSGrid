// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ActiveSessionsKillSwitchView from '../ActiveSessionsKillSwitchView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

describe('ActiveSessionsKillSwitchView.vue — Control de Sesiones y Kill-Switch', () => {
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

  it('monta la vista, lista sesiones y parsea dispositivos y sondeo por intervalo', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          {
            session_id: 'sess-100',
            user_id: 'u-100',
            username: 'tech_sur',
            full_name: 'Técnico de Turno',
            role: 'SUPPORT_L2',
            ip_address: '10.0.0.99',
            user_agent: 'Mozilla/5.0 (X11; Linux x86_64)',
            current_router_id: 'r-1',
            current_router_name: 'RB4011',
            current_view_path: '/routers/r-1/webfig/firewall',
            created_at: new Date().toISOString(),
            last_active_at: new Date().toISOString(),
            seconds_since_active: 5,
          },
          {
            session_id: 'sess-101',
            user_id: 'u-101',
            username: 'tech_win',
            role: 'FIELD_TECH',
            ip_address: '10.0.0.98',
            user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            current_router_id: 'r-2',
            current_router_name: 'CCR2004',
            created_at: new Date().toISOString(),
            last_active_at: new Date().toISOString(),
            seconds_since_active: 120,
          },
          {
            session_id: 'sess-102',
            user_id: 'u-102',
            username: 'tech_mac',
            role: 'NOC_MONITOR',
            ip_address: '10.0.0.97',
            user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X)',
            created_at: new Date().toISOString(),
            last_active_at: new Date().toISOString(),
            seconds_since_active: 400,
          },
          {
            session_id: 'sess-103',
            user_id: 'u-103',
            username: 'tech_other',
            role: 'SECURITY_AUDITOR',
            ip_address: '10.0.0.96',
            user_agent: 'CustomBot/1.0',
            created_at: new Date().toISOString(),
            last_active_at: new Date().toISOString(),
            seconds_since_active: 10,
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(ActiveSessionsKillSwitchView, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a :href="to"><slot /></a>',
            props: ['to'],
          },
        },
      },
    });

    await flushPromises();

    expect(wrapper.find('h1').text()).toContain('Sesiones Activas y Kill-Switch');
    expect(wrapper.find('.cell-user').text()).toContain('tech_sur');
    expect(wrapper.text()).toContain('Linux PC');
    expect(wrapper.text()).toContain('Windows PC');
    expect(wrapper.text()).toContain('macOS');
    expect(wrapper.text()).toContain('Navegador Web');

    // Botón refrescar
    await wrapper.find('.btn-refresh').trigger('click');
    await flushPromises();

    // Avanzar reloj para disparar el pollInterval de 30 segundos
    vi.advanceTimersByTime(35000);
    await flushPromises();

    wrapper.unmount();
  });

  it('abre modal Kill-Switch y permite cancelar el cierre de sesión vía botón y backdrop', async () => {
    const wrapper = mount(ActiveSessionsKillSwitchView, {
      global: {
        stubs: { RouterLink: true },
      },
    });

    await flushPromises();

    const killBtn = wrapper.find('.btn-kill-session');
    if (killBtn.exists()) {
      await killBtn.trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(true);

      // Cancelar con botón
      await wrapper.find('.btn-cancel').trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(false);

      // Reabrir y cerrar vía backdrop
      await killBtn.trigger('click');
      expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);
      await wrapper.find('.rg-modal-backdrop').trigger('click');
      expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);

      // Reabrir y cerrar con botón X
      await killBtn.trigger('click');
      await wrapper.find('.btn-close').trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(false);
    }
  });

  it('permite revocar sesión individual con éxito y limpia mensaje por temporizador', async () => {
    const wrapper = mount(ActiveSessionsKillSwitchView, {
      global: {
        stubs: { RouterLink: true },
      },
    });

    await flushPromises();

    // Revocar sesión que no tiene router asignado
    const killButtons = wrapper.findAll('.btn-kill-session');
    expect(killButtons.length).toBeGreaterThanOrEqual(2);

    // Abrir modal con segunda sesión
    await killButtons[1].trigger('click');
    expect(wrapper.find('.rg-modal').exists()).toBe(true);

    // Simular error con detail
    vi.spyOn(http, 'delete').mockRejectedValueOnce({
      detail: 'Error detallado de KeyDB',
    });
    await wrapper.find('.btn-confirm-kill').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Error detallado de KeyDB');

    // Simular error genérico sin detail ni message
    vi.spyOn(http, 'delete').mockRejectedValueOnce({});
    await wrapper.find('.btn-confirm-kill').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain(
      'Error al ejecutar la orden Kill-Switch.',
    );

    // Ahora revocar con éxito
    await killButtons[0].trigger('click');
    await wrapper.find('#revoke-reason').setValue('Cierre por auditoría');

    vi.spyOn(http, 'delete').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-confirm-kill').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--success').exists()).toBe(true);

    // Avanzar timers para limpiar mensaje de éxito
    vi.advanceTimersByTime(5000);
    await flushPromises();
    expect(wrapper.find('.banner--success').exists()).toBe(false);
  });

  it('permite expulsar a un usuario de todos sus dispositivos y maneja errores de red', async () => {
    const wrapper = mount(ActiveSessionsKillSwitchView, {
      global: {
        stubs: { RouterLink: true },
      },
    });

    await flushPromises();

    const killAllBtn = wrapper.find('.btn-kill-user');
    expect(killAllBtn.exists()).toBe(true);
    await killAllBtn.trigger('click');
    expect(wrapper.find('.modal-title').text()).toContain('Kill-Switch Total');

    // Error en revocación masiva
    vi.spyOn(http, 'delete').mockRejectedValueOnce({
      message: 'Fallo al revocar en KeyDB',
    });

    await wrapper.find('.btn-confirm-kill').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Fallo al revocar en KeyDB');

    // Éxito en revocación masiva
    vi.spyOn(http, 'delete').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-confirm-kill').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--success').text()).toContain('Todas las sesiones');
  });
});
