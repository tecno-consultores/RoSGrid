// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import DashboardHomeView from './DashboardHomeView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/', params: {}, query: {} }),
  useRouter: () => ({ push: pushMock }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('DashboardHomeView.vue — Centro de Mando Táctico 11X', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
  });

  it('renderiza título Centro de Mando y elimina Mission Control, Tactical NOC y NOC EN VIVO', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador_noc',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'tenant-demo',
      totp_enabled: false,
    });

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const title = wrapper.find('.hub-title');
    expect(title.exists()).toBe(true);
    expect(title.text()).toBe('Centro de Mando');
    expect(title.text()).not.toContain('Mission Control');

    // Comprobar ausencia de elementos eliminados
    expect(wrapper.find('.hub-version-tag').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Tactical NOC v1.0');
    expect(wrapper.find('.telemetry-pill').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('NOC EN VIVO');

    // Subtítulo sin "Organización: "
    const subtitle = wrapper.find('.hub-subtitle');
    expect(subtitle.exists()).toBe(true);
    expect(subtitle.text()).not.toContain('Organización:');
  });

  it('el reloj muestra solo una hora y respeta el formato configurado 24h vs 12h', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.timeFormat = '24h';

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const clockCard = wrapper.find('.clock-card');
    expect(clockCard.exists()).toBe(true);
    expect(clockCard.find('.clock-time').exists()).toBe(true);
    // Eliminación de la hora pequeña UTC
    expect(clockCard.find('.clock-utc').exists()).toBe(false);

    // En formato 24h debe ser HH:MM (sin segundos)
    const timeText24 = clockCard.find('.clock-time').text();
    expect(timeText24).toMatch(/^\d{1,2}:\d{2}$/);

    // Cambiar a formato 12h
    themeStore.timeFormat = '12h';
    await wrapper.vm.$nextTick();
    const timeText12 = clockCard.find('.clock-time').text();
    expect(timeText12).toMatch(/^\d{1,2}:\d{2}(\s?(AM|PM|a\.\sm\.|p\.\sm\.))?$/i);
  });

  it('permite actualizar datos de la flota con el botón de refresco', async () => {
    const inventoryStore = useInventoryStore();
    const fetchSpy = vi.spyOn(inventoryStore, 'fetchRouters').mockResolvedValue();

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const refreshBtn = wrapper.find('button.btn-primary');
    expect(refreshBtn.exists()).toBe(true);
    await refreshBtn.trigger('click');

    expect(fetchSpy).toHaveBeenCalled();
  });
});
