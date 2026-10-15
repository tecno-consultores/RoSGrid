// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import App from './App.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useNocEventsStore } from '@/stores/useNocEventsStore';

let mockRoutePath = '/inventory';
vi.mock('vue-router', () => ({
  useRoute: () => ({
    get path() {
      return mockRoutePath;
    },
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const RouterViewStub = {
  name: 'RouterView',
  template: '<div class="router-view-content">PAGE_CONTENT</div>',
};

describe('App.vue — Orquestación Raíz y Ciclo de Vida', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockRoutePath = '/inventory';
  });

  it('monta RgResponsiveShell cuando no está en /login', () => {
    mockRoutePath = '/inventory';
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'admin',
      email: 'admin@corp',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      totp_enabled: true,
    });

    const wrapper = mount(App, {
      global: {
        components: {
          RouterView: RouterViewStub,
        },
        stubs: {
          RouterView: RouterViewStub,
          'router-view': RouterViewStub,
          RgResponsiveShell: {
            template: '<div class="stubbed-shell"><slot /></div>',
          },
        },
      },
    });

    expect(wrapper.find('.stubbed-shell').exists()).toBe(true);
  });

  it('renderiza directamente router-view en la ruta /login sin envoltorio shell', () => {
    mockRoutePath = '/login';
    const wrapper = mount(App, {
      global: {
        components: {
          RouterView: RouterViewStub,
        },
        stubs: {
          RouterView: RouterViewStub,
          'router-view': RouterViewStub,
          RgResponsiveShell: true,
        },
      },
    });

    expect(wrapper.find('.stubbed-shell').exists()).toBe(false);
    expect(wrapper.find('.router-view-content').exists()).toBe(true);
  });

  it('reacciona al cambio de autenticación conectando y desconectando eventos', async () => {
    const authStore = useAuthStore();
    const nocStore = useNocEventsStore();
    const connectSpy = vi.spyOn(nocStore, 'connectEventsWebSocket');
    const disconnectSpy = vi.spyOn(nocStore, 'disconnectEventsWebSocket');

    mount(App, {
      global: {
        components: { RouterView: RouterViewStub },
        stubs: { RouterView: RouterViewStub, RgResponsiveShell: true },
      },
    });

    authStore.setAuth({
      id: 'usr-1',
      username: 'test',
      email: 'test@local',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      totp_enabled: true,
    });
    await nextTick();
    expect(connectSpy).toHaveBeenCalled();

    authStore.clearAuth();
    await nextTick();
    expect(disconnectSpy).toHaveBeenCalled();
  });
});
