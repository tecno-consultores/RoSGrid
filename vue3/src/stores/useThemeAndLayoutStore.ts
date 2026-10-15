// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { EffectiveTableDensity, TableDensityMode, ThemeMode } from '@/types';

export const useThemeAndLayoutStore = defineStore('themeAndLayout', () => {
  const theme = ref<ThemeMode>('dark');
  const tableDensityMode = ref<TableDensityMode>('auto');
  const windowWidth = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 1200);

  const isMobileDrawerOpen = ref<boolean>(false);
  const isCommandPaletteOpen = ref<boolean>(false);

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
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', newTheme);
    }
  }

  function setTableDensityMode(mode: TableDensityMode): void {
    tableDensityMode.value = mode;
  }

  function toggleTableDensity(): void {
    const current = effectiveTableDensity.value;
    tableDensityMode.value = current === 'compact' ? 'comfortable' : 'compact';
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
    setTheme,
    setTableDensityMode,
    toggleTableDensity,
    toggleMobileDrawer,
    closeMobileDrawer,
    openCommandPalette,
    closeCommandPalette,
    toggleCommandPalette,
  };
});
