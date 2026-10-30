// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { EffectiveTableDensity, TableDensityMode, ThemeMode } from '@/types';

const VALID_THEMES = new Set<ThemeMode>(['dark', 'light', 'noc-high-contrast']);
const VALID_DENSITIES = new Set<TableDensityMode>(['auto', 'compact', 'comfortable']);

function getSafeStorage(): Storage | null {
  try {
    if (typeof window !== 'undefined' && window.localStorage && typeof window.localStorage.getItem === 'function') {
      return window.localStorage;
    }
    if (typeof localStorage !== 'undefined' && localStorage && typeof localStorage.getItem === 'function') {
      return localStorage;
    }
  } catch {
    return null;
  }
  return null;
}

function readStorageItem(key: string): string | null {
  const storage = getSafeStorage();
  if (!storage) return null;
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorageItem(key: string, value: string): void {
  const storage = getSafeStorage();
  if (!storage || typeof storage.setItem !== 'function') return;
  try {
    storage.setItem(key, value);
  } catch {
    // Ignorar fallo cuando el almacenamiento está bloqueado (incógnito estricto)
  }
}

function applyThemeToDom(targetTheme: ThemeMode): void {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-theme', targetTheme);

  const colorSchemeMeta = document.querySelector('meta[name="color-scheme"]');
  if (colorSchemeMeta) {
    colorSchemeMeta.setAttribute('content', targetTheme === 'light' ? 'light' : 'dark');
  }

  const themeColorMeta = document.querySelector('meta[name="theme-color"]');
  if (themeColorMeta) {
    let hexColor = '#0B111E';
    if (targetTheme === 'light') {
      hexColor = '#F8FAFC';
    } else if (targetTheme === 'noc-high-contrast') {
      hexColor = '#000000';
    }
    themeColorMeta.setAttribute('content', hexColor);
  }
}

export const useThemeAndLayoutStore = defineStore('themeAndLayout', () => {
  const savedTheme = readStorageItem('rg_theme') as ThemeMode | null;
  const initialTheme: ThemeMode = savedTheme && VALID_THEMES.has(savedTheme) ? savedTheme : 'dark';

  const savedDensity = readStorageItem('rg_table_density') as TableDensityMode | null;
  const initialDensity: TableDensityMode =
    savedDensity && VALID_DENSITIES.has(savedDensity) ? savedDensity : 'auto';

  const theme = ref<ThemeMode>(initialTheme);
  const tableDensityMode = ref<TableDensityMode>(initialDensity);
  const windowWidth = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 1200);

  const isMobileDrawerOpen = ref<boolean>(false);
  const isCommandPaletteOpen = ref<boolean>(false);

  // Formato de hora táctico ('24h' o '12h' AM/PM) con persistencia
  const savedTimeFormat = readStorageItem('rg_time_format');
  const timeFormat = ref<'24h' | '12h'>(savedTimeFormat === '12h' ? '12h' : '24h');

  if (savedTheme && VALID_THEMES.has(savedTheme)) {
    applyThemeToDom(initialTheme);
  }

  // Listener reactivo de redimensionamiento
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth;
    });
  }

  // Densidad Dual Adaptativa
  const effectiveTableDensity = computed<EffectiveTableDensity>(() => {
    if (tableDensityMode.value === 'compact') return 'compact';
    if (tableDensityMode.value === 'comfortable') return 'comfortable';
    // Modo 'auto': Compacto (32px) en Desktop >= 1024px, Cómodo (44px) en Móvil/Tablet < 1024px
    return windowWidth.value >= 1024 ? 'compact' : 'comfortable';
  });

  const isMobileView = computed<boolean>(() => windowWidth.value < 768);
  const isTabletView = computed<boolean>(
    () => windowWidth.value >= 768 && windowWidth.value < 1024,
  );
  const isDesktopView = computed<boolean>(() => windowWidth.value >= 1024);

  function setTheme(newTheme: ThemeMode): void {
    theme.value = newTheme;
    writeStorageItem('rg_theme', newTheme);
    applyThemeToDom(newTheme);
  }

  function setTableDensityMode(mode: TableDensityMode): void {
    tableDensityMode.value = mode;
    writeStorageItem('rg_table_density', mode);
  }

  function toggleTableDensity(): void {
    const current = effectiveTableDensity.value;
    const nextMode: TableDensityMode = current === 'compact' ? 'comfortable' : 'compact';
    tableDensityMode.value = nextMode;
    writeStorageItem('rg_table_density', nextMode);
  }

  function setTimeFormat(format: '24h' | '12h'): void {
    timeFormat.value = format;
    writeStorageItem('rg_time_format', format);
  }

  function toggleTimeFormat(): void {
    const next = timeFormat.value === '24h' ? '12h' : '24h';
    setTimeFormat(next);
  }

  function toggleMobileDrawer(): void {
    isMobileDrawerOpen.value = !isMobileDrawerOpen.value;
  }

  function closeMobileDrawer(): void {
    isMobileDrawerOpen.value = false;
  }

  function openCommandPalette(): void {
    isCommandPaletteOpen.value = true;
  }

  function closeCommandPalette(): void {
    isCommandPaletteOpen.value = false;
  }

  function toggleCommandPalette(): void {
    isCommandPaletteOpen.value = !isCommandPaletteOpen.value;
  }

  return {
    theme,
    tableDensityMode,
    windowWidth,
    effectiveTableDensity,
    isMobileView,
    isTabletView,
    isDesktopView,
    isMobileDrawerOpen,
    isCommandPaletteOpen,
    timeFormat,
    setTheme,
    setTableDensityMode,
    toggleTableDensity,
    setTimeFormat,
    toggleTimeFormat,
    toggleMobileDrawer,
    closeMobileDrawer,
    openCommandPalette,
    closeCommandPalette,
    toggleCommandPalette,
  };
});
