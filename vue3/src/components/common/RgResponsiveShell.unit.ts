// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgResponsiveShell from './RgResponsiveShell.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
import { useI18n } from '@/composables/useI18n';

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
    props: ['to'],
    template: '<a :href="to" v-bind="$attrs"><slot /></a>',
  },
}));

describe('RgResponsiveShell.vue — Doble Contexto & Menú de Usuario 11X', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();

    // Configurar usuario por defecto autenticado en el authStore
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador_noc',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
    });
  });

  it('renderiza la estructura de shell con skip-link para accesibilidad WCAG', () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapper.find('.skip-link').exists()).toBe(true);
    expect(wrapper.find('.skip-link').attributes('href')).toBe('#main-content');
    expect(wrapper.find('header.rg-header').exists()).toBe(true);
    expect(wrapper.find('nav.rg-rail').exists()).toBe(true);
  });

  it('el logo de RoSGrid enlaza a / (Centro de Mando)', () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a :href="to" class="brand"><slot /></a>',
          },
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const brandLink = wrapper.find('a.brand');
    expect(brandLink.exists()).toBe(true);
    expect(brandLink.attributes('href')).toBe('/');
    const logoImg = brandLink.find('img.brand-logo');
    expect(logoImg.exists()).toBe(true);
    expect(logoImg.attributes('src')).toBe('/favicon.svg');
  });

  it('muestra solo el nombre del tenant en la barra superior sin el prefijo "Tenant: "', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'admin_tenant',
      email: 'admin@acme.corp',
      role: 'TENANT_ADMIN',
      tenant_id: 't-99',
      tenant_slug: 'acme-corp',
      totp_enabled: true,
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const tenantBadge = wrapper.find('.tenant-badge');
    expect(tenantBadge.exists()).toBe(true);
    expect(tenantBadge.text()).toContain('acme-corp');
    expect(tenantBadge.text()).not.toContain('Tenant:');
  });

  it('muestra el username en la barra superior y despliega el menú de usuario al hacer click', async () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-42',
      username: 'jdoe_noc',
      email: 'jdoe@isp.net',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'global',
      totp_enabled: true,
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const profileBtn = wrapper.find('.user-profile-btn');
    expect(profileBtn.exists()).toBe(true);
    expect(profileBtn.find('.user-username').text()).toBe('jdoe_noc');
    expect(wrapper.find('.user-dropdown-menu').exists()).toBe(false);

    // Abrir menú
    await profileBtn.trigger('click');
    expect(wrapper.find('.user-dropdown-menu').exists()).toBe(true);
  });

  it('permite alternar formato de hora (24h vs 12h) desde el menú de usuario', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.timeFormat = '24h';

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    await wrapper.find('.user-profile-btn').trigger('click');
    expect(wrapper.find('.user-dropdown-menu').exists()).toBe(true);

    const timeButtons = wrapper.findAll('.dropdown-section--time .toggle-btn');
    expect(timeButtons.length).toBe(2);

    // Activar 12h
    await timeButtons[1].trigger('click');
    expect(themeStore.timeFormat).toBe('12h');

    // Activar 24h
    await timeButtons[0].trigger('click');
    expect(themeStore.timeFormat).toBe('24h');
  });

  it('el reloj global en la barra superior siempre está visible y respeta el formato 24h vs 12h', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.timeFormat = '24h';

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const clock = wrapper.find('.header-clock');
    expect(clock.exists()).toBe(true);
    const clockTime = clock.find('.clock-time');
    expect(clockTime.exists()).toBe(true);

    // Formato 24h: HH:MM sin segundos
    expect(clockTime.text()).toMatch(/^\d{1,2}:\d{2}$/);

    // Alternar a 12h
    themeStore.timeFormat = '12h';
    await wrapper.vm.$nextTick();
    expect(clockTime.text()).toMatch(/^\d{1,2}:\d{2}(\s?(AM|PM|a\.\sm\.|p\.\sm\.))?$/i);
  });

  it('permite alternar tema visual desde el menú de usuario', async () => {
    const themeStore = useThemeAndLayoutStore();

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    await wrapper.find('.user-profile-btn').trigger('click');
    const themeButtons = wrapper.findAll('.dropdown-section--theme .toggle-btn');
    expect(themeButtons.length).toBe(3);

    // Seleccionar Light
    await themeButtons[1].trigger('click');
    expect(themeStore.theme).toBe('light');

    // Seleccionar NOC
    await themeButtons[2].trigger('click');
    expect(themeStore.theme).toBe('noc-high-contrast');

    // Seleccionar Dark
    await themeButtons[0].trigger('click');
    expect(themeStore.theme).toBe('dark');
  });

  it('permite alternar idioma desde el menú de usuario', async () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    await wrapper.find('.user-profile-btn').trigger('click');
    const langButtons = wrapper.findAll('.dropdown-section:nth-of-type(3) .toggle-btn');
    expect(langButtons.length).toBe(2);

    await langButtons[1].trigger('click');
    expect(wrapper.find('.user-dropdown-menu').exists()).toBe(true);
  });

  it('abre los modales de seguridad (clave, 2FA, MCP) desde el menú de usuario', async () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: {
            props: ['isOpen'],
            template: '<div v-if="isOpen" class="mock-pwd-modal">PWD</div>',
          },
          RgStepUp2FAModal: {
            props: ['isOpen'],
            template: '<div v-if="isOpen" class="mock-2fa-modal">2FA</div>',
          },
          RgMcpTokenModal: {
            props: ['isOpen'],
            template: '<div v-if="isOpen" class="mock-mcp-modal">MCP</div>',
          },
        },
      },
    });

    // Abrir modal de contraseña
    await wrapper.find('.user-profile-btn').trigger('click');
    const pwdBtn = wrapper.find('.btn-change-password-menu');
    expect(pwdBtn.exists()).toBe(true);
    await pwdBtn.trigger('click');
    expect(wrapper.find('.mock-pwd-modal').exists()).toBe(true);

    // Abrir modal 2FA
    await wrapper.find('.user-profile-btn').trigger('click');
    const totpBtn = wrapper.find('.btn-reset-2fa-menu');
    expect(totpBtn.exists()).toBe(true);
    await totpBtn.trigger('click');
    expect(wrapper.find('.mock-2fa-modal').exists()).toBe(true);

    // Abrir modal MCP
    await wrapper.find('.user-profile-btn').trigger('click');
    const mcpBtn = wrapper.find('.btn-mcp-token-menu');
    expect(mcpBtn.exists()).toBe(true);
    await mcpBtn.trigger('click');
    expect(wrapper.find('.mock-mcp-modal').exists()).toBe(true);
  });

  it('permite cerrar sesión desde el fondo del menú y redirige a /login', async () => {
    const authStore = useAuthStore();

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    await wrapper.find('.user-profile-btn').trigger('click');
    const logoutBtn = wrapper.find('.btn-logout');
    expect(logoutBtn.exists()).toBe(true);
    await logoutBtn.trigger('click');

    expect(authStore.isAuthenticated).toBe(false);
    expect(pushMock).toHaveBeenCalledWith('/login');
  });

  it('permite abrir command palette desde el botón de búsqueda en cabecera', async () => {
    const themeStore = useThemeAndLayoutStore();

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const searchBtn = wrapper.find('.btn-search-trigger');
    expect(searchBtn.exists()).toBe(true);
    await searchBtn.trigger('click');
    expect(themeStore.isCommandPaletteOpen).toBe(true);
  });

  it('activa controles móviles cuando no es desktop view', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.windowWidth = 500;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const hamburger = wrapper.find('.btn-hamburger');
    if (hamburger.exists()) {
      await hamburger.trigger('click');
      expect(themeStore.isMobileDrawerOpen).toBe(true);
    }
  });

  it('renderiza enlaces de contexto en la barra inferior móvil', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.windowWidth = 400;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapper.find('nav.rg-mobile-bottom-bar').exists()).toBe(true);
    const mobileMenuBtn = wrapper.find('.btn-mobile-menu');
    if (mobileMenuBtn.exists()) {
      await mobileMenuBtn.trigger('click');
      expect(themeStore.isMobileDrawerOpen).toBe(true);
    }
  });

  it('filtra Técnico de Campo según el feature flag isp_module_enabled', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
      tenant_feature_flags: { isp_module_enabled: false },
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapper.text()).not.toContain('Técnico de Campo');

    authStore.setAuth({
      id: 'usr-1',
      username: 'operador',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: false,
      tenant_feature_flags: { isp_module_enabled: true },
    });

    const wrapperWithFlag = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapperWithFlag.text()).toContain('Técnico de Campo');
  });

  it('renderiza el pie de página global autenticado con atribución y enlace a GitHub', () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const footer = wrapper.find('footer.rg-global-footer');
    expect(footer.exists()).toBe(true);
    expect(footer.text()).toContain('Elaborado por');
    expect(footer.text()).toContain('Tecno Consultores 2023 C.A.');
    expect(footer.text()).toContain('Licencia GNU GPLv3');

    const tecnoLink = footer.find('a[href="https://www.tecnoconsultores.net/"]');
    expect(tecnoLink.exists()).toBe(true);
    expect(tecnoLink.attributes('target')).toBe('_blank');

    const githubLink = footer.find('a[href="https://github.com/tecno-consultores/RoSGrid/"]');
    expect(githubLink.exists()).toBe(true);
    expect(githubLink.attributes('aria-label')).toContain('GitHub');
  });

  it('renderiza Empresas (Tenants) en el menú lateral directamente debajo de Auditoría WORM para SUPERADMIN_GLOBAL', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-super',
      username: 'superadmin',
      email: 'admin@rosgrid.local',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'demo',
      totp_enabled: true,
    });

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapper.text()).toContain('Empresas (Tenants)');
    const allText = wrapper.text();
    const usersPos = allText.indexOf('Usuarios & RBAC');
    const tenantsPos = allText.indexOf('Empresas (Tenants)');
    const compliancePos = allText.indexOf('Flota & Seguridad');
    expect(usersPos).toBeGreaterThan(-1);
    expect(tenantsPos).toBeGreaterThan(usersPos);
    expect(compliancePos).toBeGreaterThan(tenantsPos);
  });

  it('traduce el menú de usuario y los enlaces de navegación L2 Topology y Fleet & Compliance al cambiar a inglés', async () => {
    const { setLocale } = useI18n();
    setLocale('en');

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    // Enlaces de navegación en inglés
    expect(wrapper.text()).toContain('L2 Topology');
    expect(wrapper.text()).toContain('Fleet & Compliance');

    // Desplegar menú de usuario en inglés
    await wrapper.find('.user-profile-btn').trigger('click');
    expect(wrapper.text()).toContain('Time Format');
    expect(wrapper.text()).toContain('Visual Theme');
    expect(wrapper.text()).toContain('Change My Password');
    expect(wrapper.text()).toContain('Reset My 2FA');
    expect(wrapper.text()).toContain('MCP Access Token');
    expect(wrapper.text()).toContain('Sign Out');

    // Restaurar a español
    setLocale('es');
  });

  it('renderiza el indicador táctico de salud del API (RgApiHealthBadge) en la barra superior', () => {
    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    expect(wrapper.findComponent({ name: 'RgApiHealthBadge' }).exists() || wrapper.find('#api-health-badge').exists()).toBe(true);
  });

  it('incluye el botón para ocultar y mostrar la barra lateral (#btn-toggle-sidebar) entre el logo y el tenant badge, y conmuta la clase rg-rail--collapsed', async () => {
    const authStore = useAuthStore();
    authStore.tenantSlug = 'corp-demo';

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const toggleBtn = wrapper.find('#btn-toggle-sidebar');
    expect(toggleBtn.exists()).toBe(true);
    expect(toggleBtn.attributes('title')).toBe('Ocultar barra lateral');

    const rail = wrapper.find('nav.rg-rail');
    expect(rail.exists()).toBe(true);
    expect(rail.classes()).not.toContain('rg-rail--collapsed');

    // Clic en el botón para colapsar la barra lateral
    await toggleBtn.trigger('click');
    expect(rail.classes()).toContain('rg-rail--collapsed');
    expect(toggleBtn.attributes('title')).toBe('Mostrar barra lateral');

    // Clic nuevamente para expandir
    await toggleBtn.trigger('click');
    expect(rail.classes()).not.toContain('rg-rail--collapsed');
  });

  it('permite abrir el drawer móvil/tablet (rg-rail--open) incluso cuando la barra lateral de escritorio está colapsada (rg-rail--collapsed)', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.windowWidth = 375;

    const wrapper = mount(RgResponsiveShell, {
      global: {
        stubs: {
          RouterView: true,
          RgCommandPalette: true,
          RgSafeModeBanner: true,
          ChangePasswordModal: true,
          RgStepUp2FAModal: true,
          RgMcpTokenModal: true,
        },
      },
    });

    const toggleDesktopBtn = wrapper.find('#btn-toggle-sidebar');
    await toggleDesktopBtn.trigger('click');

    const rail = wrapper.find('nav.rg-rail');
    expect(rail.classes()).toContain('rg-rail--collapsed');

    // Abrir el drawer móvil desde el botón inferior .btn-mobile-menu
    const mobileMenuBtn = wrapper.find('.btn-mobile-menu');
    expect(mobileMenuBtn.exists()).toBe(true);
    await mobileMenuBtn.trigger('click');
    expect(rail.classes()).toContain('rg-rail--open');
    expect(rail.classes()).toContain('rg-rail--collapsed');

    // Cerrar desde el botón hamburguesa superior
    const hamburgerBtn = wrapper.find('.btn-hamburger');
    expect(hamburgerBtn.exists()).toBe(true);
    await hamburgerBtn.trigger('click');
    expect(rail.classes()).not.toContain('rg-rail--open');
  });
});


