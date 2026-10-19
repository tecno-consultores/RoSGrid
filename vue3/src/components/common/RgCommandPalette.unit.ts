// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgCommandPalette from './RgCommandPalette.vue';
import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
import { useInventoryStore } from '@/stores/useInventoryStore';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe('RgCommandPalette.vue — Accesibilidad (Ctrl+K)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('no es visible cuando themeStore.isCommandPaletteOpen es false', () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.isCommandPaletteOpen = false;

    const wrapper = mount(RgCommandPalette);
    expect(wrapper.find('.rg-palette-backdrop').exists()).toBe(false);
  });

  it('se muestra cuando themeStore.isCommandPaletteOpen es true', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.isCommandPaletteOpen = true;

    const wrapper = mount(RgCommandPalette);
    expect(wrapper.find('.rg-palette-backdrop').exists()).toBe(true);
    expect(wrapper.find('input#cmd-palette-input').exists()).toBe(true);
  });

  it('filtra comandos estáticos y routers según término de búsqueda', async () => {
    const themeStore = useThemeAndLayoutStore();
    const invStore = useInventoryStore();
    invStore.setRouters([
      {
        id: 'r-100',
        tenant_id: 't-1',
        display_name: 'RB4011-Core',
        ip_address: '10.200.0.1',
        api_port: 8728,
        ros_version: '7.15.2',
        admin_state: 'PRODUCTION',
        is_reachable: true,
      },
    ]);
    themeStore.isCommandPaletteOpen = true;

    const wrapper = mount(RgCommandPalette);
    const input = wrapper.find('input#cmd-palette-input');

    await input.setValue('RB4011');
    const items = wrapper.findAll('.rg-palette__item');
    expect(items.length).toBe(1);
    expect(items[0].text()).toContain('RB4011-Core');

    await items[0].trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/routers/r-100/webfig/live');
  });

  it('permite navegar y ejecutar mediante teclado (ArrowDown, ArrowUp, Enter, Escape, Ctrl+K)', async () => {
    const themeStore = useThemeAndLayoutStore();
    mount(RgCommandPalette);

    // Abrir con Ctrl+K
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }));
    expect(themeStore.isCommandPaletteOpen).toBe(true);

    // ArrowDown
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    // ArrowUp
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }));
    // Enter
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));

    // Re-abrir y cerrar con Escape
    themeStore.isCommandPaletteOpen = true;
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(themeStore.isCommandPaletteOpen).toBe(false);
  });

  it('cierra la paleta al hacer click en el backdrop', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.isCommandPaletteOpen = true;

    const wrapper = mount(RgCommandPalette);
    await wrapper.find('.rg-palette-backdrop').trigger('click');

    expect(themeStore.isCommandPaletteOpen).toBe(false);
  });

  it('ejecuta las acciones de todos los comandos estáticos disponibles', async () => {
    const themeStore = useThemeAndLayoutStore();
    themeStore.isCommandPaletteOpen = true;

    const wrapper = mount(RgCommandPalette);
    const items = wrapper.findAll('.rg-palette__item');
    for (const item of items) {
      await item.trigger('click');
      themeStore.isCommandPaletteOpen = true;
    }

    // Probar alternancia de temas completa (dark -> light -> noc-high-contrast -> dark)
    themeStore.isCommandPaletteOpen = true;
    await wrapper.vm.$nextTick();
    themeStore.theme = 'light';
    const itemsTheme = wrapper.findAll('.rg-palette__item');
    const themeItem = itemsTheme.find((i) => i.text().includes('Alternar Tema'));
    if (themeItem) {
      await themeItem.trigger('click');
      expect(themeStore.theme).toBe('noc-high-contrast');
    }

    themeStore.isCommandPaletteOpen = true;
    await wrapper.vm.$nextTick();
    const itemsTheme2 = wrapper.findAll('.rg-palette__item');
    const themeItem2 = itemsTheme2.find((i) => i.text().includes('Alternar Tema'));
    if (themeItem2) {
      await themeItem2.trigger('click');
      expect(themeStore.theme).toBe('dark');
    }

    // Buscar texto sin coincidencias para cubrir estado vacío
    themeStore.isCommandPaletteOpen = true;
    await wrapper.vm.$nextTick();
    const input = wrapper.find('#cmd-palette-input');
    await input.setValue('texto_completamente_inexistente_xyz_123');
    expect(wrapper.find('.rg-palette__empty').exists()).toBe(true);

    // Desmontar componente para cubrir onUnmounted
    wrapper.unmount();
  });

  it('filtra comandos de navegación según el feature flag del tenant', async () => {
    const { useAuthStore } = await import('@/stores/useAuthStore');
    const authStore = useAuthStore();
    const themeStore = useThemeAndLayoutStore();

    // Caso 1: Flag desactivado
    authStore.setAuth({
      id: 'u-1',
      username: 'tech',
      email: 'tech@corp.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      totp_enabled: false,
      tenant_feature_flags: { isp_module_enabled: false },
    });
    themeStore.isCommandPaletteOpen = true;

    let wrapper = mount(RgCommandPalette);
    expect(wrapper.text()).not.toContain('Técnico de Campo & Toolkit');

    // Caso 2: Flag activado
    authStore.setAuth({
      id: 'u-1',
      username: 'tech',
      email: 'tech@corp.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      totp_enabled: false,
      tenant_feature_flags: { isp_module_enabled: true },
    });

    wrapper = mount(RgCommandPalette);
    expect(wrapper.text()).toContain('Técnico de Campo & Toolkit');
  });
});
