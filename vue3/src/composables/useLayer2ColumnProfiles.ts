// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

const memoryFallbackStore = new Map<string, string>();

function readStorageItem(key: string): string | null {
  try {
    if (typeof window !== 'undefined' && typeof window.localStorage?.getItem === 'function') {
      return window.localStorage.getItem(key);
    }
  } catch {
    // Fallback a memoria
  }
  return memoryFallbackStore.get(key) ?? null;
}

function writeStorageItem(key: string, value: string): void {
  memoryFallbackStore.set(key, value);
  try {
    if (typeof window !== 'undefined' && typeof window.localStorage?.setItem === 'function') {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Fallback silencioso
  }
}

function removeStorageItem(key: string): void {
  memoryFallbackStore.delete(key);
  try {
    if (typeof window !== 'undefined' && typeof window.localStorage?.removeItem === 'function') {
      window.localStorage.removeItem(key);
    }
  } catch {
    // Fallback silencioso
  }
}

/**
 * Composable de Persistencia de Perfiles de Columnas de Capa 2 por Tenant y Ruta RouterOS (Spec 54 — 27.16.7).
 */
export function useLayer2ColumnProfiles() {
  function getStorageKey(rosPath: string, tenantSlug = 'default'): string {
    const cleanPath = rosPath.replace(/^\/+|\/+$/g, '');
    return `rg_l2_cols:${tenantSlug}:${cleanPath}`;
  }

  function loadSavedColumns(rosPath: string, tenantSlug = 'default'): string[] {
    try {
      const raw = readStorageItem(getStorageKey(rosPath, tenantSlug));
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter((k) => typeof k === 'string') : [];
    } catch {
      return [];
    }
  }

  function saveColumnProfile(rosPath: string, keys: string[], tenantSlug = 'default'): void {
    const unique = Array.from(new Set(keys.filter((k) => typeof k === 'string' && k.length > 0)));
    writeStorageItem(getStorageKey(rosPath, tenantSlug), JSON.stringify(unique));
  }

  function clearColumnProfile(rosPath: string, tenantSlug = 'default'): void {
    removeStorageItem(getStorageKey(rosPath, tenantSlug));
  }

  function hasSavedProfile(rosPath: string, tenantSlug = 'default'): boolean {
    return loadSavedColumns(rosPath, tenantSlug).length > 0;
  }

  function writeRawProfileForTesting(key: string, rawValue: string): void {
    writeStorageItem(key, rawValue);
  }

  return {
    getStorageKey,
    loadSavedColumns,
    saveColumnProfile,
    clearColumnProfile,
    hasSavedProfile,
    writeRawProfileForTesting,
  };
}
