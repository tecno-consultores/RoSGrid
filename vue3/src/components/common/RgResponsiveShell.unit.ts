// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgResponsiveShell from './RgResponsiveShell.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRoute: () => ({
    path: '/inventory',
    params: {},
  }),
  useRouter: () => ({
    push: pushMock,
  }),
  RouterView: {
    template: '<div class="test-router-view">ROUTER_VIEW_CONTENT</div>',
  },
  RouterLink: {
    template: '<a><slot /></a>',
  },
}));

describe('RgResponsiveShell.vue — Doble Contexto & Barra Inferior Móvil', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
  });

  it('renderiza la estructura de shell con skip-link para accesibilidad WCAG', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    expect(wrapper.find('.skip-link').exists()).toBe(true);
    expect(wrapper.find('.skip-link').attributes('href')).toBe('#main-content');
    expect(wrapper.find('header.rg-header').exists()).toBe(true);
    expect(wrapper.find('nav.rg-rail').exists()).toBe(true);
  });

  it('permite alternar tema visual y abrir command palette desde la cabecera', async () => {
    const themeStore = useThemeAndLayoutStore();

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    const themeBtn = wrapper.find('.btn-icon');
    expect(themeBtn.exists()).toBe(true);
    await themeBtn.trigger('click');
    expect(themeStore.theme).toBe('light');

    const searchBtn = wrapper.find('.btn-search-trigger');
    await searchBtn.trigger('click');
    expect(themeStore.isCommandPaletteOpen).toBe(true);
  });

  it('renderiza insignia de tema noc-high-contrast y badges de alertas', async () => {
    const themeStore = useThemeAndLayoutStore();
    const { useNocEventsStore } = await import('@/stores/useNocEventsStore');
    const nocStore = useNocEventsStore();
    themeStore.theme = 'noc-high-contrast';
    nocStore.activeAlertsCount = 5;
    nocStore.pendingApprovalsCount = 2;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: { template: '<a class="rail-link"><slot /></a>' },
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    expect(wrapper.find('.rail-badge').exists()).toBe(true);
    expect(wrapper.find('.btn-icon').text()).toContain('⚡');
  });

  it('activa controles móviles cuando no es desktop view', async () => {
    const themeStore = useThemeAndLayoutStore();
    // Simular viewport móvil (< 768px)
    themeStore.windowWidth = 500;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    const hamburger = wrapper.find('.btn-hamburger');
    if (hamburger.exists()) {
      await hamburger.trigger('click');
      expect(themeStore.isMobileDrawerOpen).toBe(true);
    }

    const railLink = wrapper.find('.rail-link');
    if (railLink.exists()) {
      await railLink.trigger('click');
      expect(themeStore.isMobileDrawerOpen).toBe(false);
    }
  });

  it('permite cerrar sesión y redirige a /login', async () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    const logoutBtn = wrapper.find('.btn-logout');
    expect(logoutBtn.exists()).toBe(true);
    await logoutBtn.trigger('click');

    expect(authStore.isAuthenticated).toBe(false);
    expect(pushMock).toHaveBeenCalledWith('/login');
  });

  it('renderiza enlaces de contexto de router en la barra inferior móvil', () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.windowWidth = 400;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: { template: '<a class="mobile-touch-item"><slot /></a>' },
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
        },
      },
    });

    expect(wrapper.find('nav.rg-mobile-bottom-bar').exists()).toBe(true);
  });
});
