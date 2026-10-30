// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useThemeAndLayoutStore } from './useThemeAndLayoutStore';

const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: storageMock,
  writable: true,
  configurable: true,
});

describe('useThemeAndLayoutStore — Densidad Dual & Temas WCAG 2.1 AA', () => {
  beforeEach(() => {
    window.localStorage.clear();
    setActivePinia(createPinia());
    document.documentElement.removeAttribute('data-theme');
  });

  it('inicia con tema dark y densidad auto por defecto', () => {
    const store = useThemeAndLayoutStore();
    expect(store.theme).toBe('dark');
    expect(store.tableDensityMode).toBe('auto');
  });

  it('permite cambiar a tema light y noc-high-contrast actualizando DOM', () => {
    const store = useThemeAndLayoutStore();
    store.setTheme('noc-high-contrast');
    expect(store.theme).toBe('noc-high-contrast');
    expect(document.documentElement.getAttribute('data-theme')).toBe('noc-high-contrast');

    store.setTheme('light');
    expect(store.theme).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('resuelve densidad compact y comfortable correctamente', () => {
    const store = useThemeAndLayoutStore();
    store.setTableDensityMode('compact');
    expect(store.tableDensityMode).toBe('compact');
    expect(store.effectiveTableDensity).toBe('compact');

    store.setTableDensityMode('comfortable');
    expect(store.tableDensityMode).toBe('comfortable');
    expect(store.effectiveTableDensity).toBe('comfortable');

    store.toggleTableDensity();
    expect(store.tableDensityMode).toBe('compact');

    // Modo auto con diferentes anchos de pantalla
    store.setTableDensityMode('auto');
    store.windowWidth = 1280;
    expect(store.effectiveTableDensity).toBe('compact');
    expect(store.isDesktopView).toBe(true);
    expect(store.isTabletView).toBe(false);
    expect(store.isMobileView).toBe(false);

    store.windowWidth = 800;
    expect(store.effectiveTableDensity).toBe('comfortable');
    expect(store.isDesktopView).toBe(false);
    expect(store.isTabletView).toBe(true);
    expect(store.isMobileView).toBe(false);

    store.windowWidth = 500;
    expect(store.effectiveTableDensity).toBe('comfortable');
    expect(store.isDesktopView).toBe(false);
    expect(store.isTabletView).toBe(false);
    expect(store.isMobileView).toBe(true);

    // Disparar evento resize para cubrir línea 19
    window.dispatchEvent(new Event('resize'));
  });

  it('controla apertura y cierre de mobile drawer y command palette', () => {
    const store = useThemeAndLayoutStore();
    expect(store.isMobileDrawerOpen).toBe(false);
    store.toggleMobileDrawer();
    expect(store.isMobileDrawerOpen).toBe(true);
    store.closeMobileDrawer();
    expect(store.isMobileDrawerOpen).toBe(false);

    expect(store.isCommandPaletteOpen).toBe(false);
    store.openCommandPalette();
    expect(store.isCommandPaletteOpen).toBe(true);
    store.closeCommandPalette();
    expect(store.isCommandPaletteOpen).toBe(false);
  });

  it('controla el formato de hora (24h vs 12h) y su alternancia', () => {
    const store = useThemeAndLayoutStore();
    expect(store.timeFormat).toBe('24h');

    store.setTimeFormat('12h');
    expect(store.timeFormat).toBe('12h');

    store.toggleTimeFormat();
    expect(store.timeFormat).toBe('24h');

    store.toggleTimeFormat();
    expect(store.timeFormat).toBe('12h');
  });

  it('persiste e hidrata rg_theme y rg_table_density en localStorage y sincroniza meta color-scheme y theme-color (Hito 27.15)', () => {
    const colorSchemeMeta = document.createElement('meta');
    colorSchemeMeta.setAttribute('name', 'color-scheme');
    colorSchemeMeta.setAttribute('content', 'dark light');
    document.head.appendChild(colorSchemeMeta);

    const themeColorMeta = document.createElement('meta');
    themeColorMeta.setAttribute('name', 'theme-color');
    themeColorMeta.setAttribute('content', '#0B111E');
    document.head.appendChild(themeColorMeta);

    const store = useThemeAndLayoutStore();
    store.setTheme('light');
    store.setTableDensityMode('comfortable');

    expect(window.localStorage.getItem('rg_theme')).toBe('light');
    expect(window.localStorage.getItem('rg_table_density')).toBe('comfortable');
    expect(colorSchemeMeta.getAttribute('content')).toBe('light');
    expect(themeColorMeta.getAttribute('content')).toBe('#F8FAFC');

    store.setTheme('noc-high-contrast');
    expect(colorSchemeMeta.getAttribute('content')).toBe('dark');
    expect(themeColorMeta.getAttribute('content')).toBe('#000000');

    // Nueva instancia de Pinia hidrata los valores guardados
    setActivePinia(createPinia());
    const hydratedStore = useThemeAndLayoutStore();
    expect(hydratedStore.theme).toBe('noc-high-contrast');
    expect(hydratedStore.tableDensityMode).toBe('comfortable');

    document.head.removeChild(colorSchemeMeta);
    document.head.removeChild(themeColorMeta);
  });
});
