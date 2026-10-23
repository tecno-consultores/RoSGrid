// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import DashboardHomeView from './DashboardHomeView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';

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

  it('el reloj fue trasladado a la barra superior global y no se renderiza en la pantalla principal', async () => {
    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    // El reloj ya no se muestra en el hub principal
    expect(wrapper.find('.clock-card').exists()).toBe(false);
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
