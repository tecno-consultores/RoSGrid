// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import type { WebFigDynamic } from '@/types';
import { useVersionCheckStore } from './useVersionCheckStore';
import { useAuthStore } from './useAuthStore';

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('useVersionCheckStore — Comprobador Pasivo de Versiones (Hito 30.42)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('inicializa con valores por defecto seguros', () => {
    const store = useVersionCheckStore();
    expect(store.currentVersion).toBe('1.3.0');
    expect(store.latestVersion).toBeNull();
    expect(store.updateAvailable).toBe(false);
    expect(store.canSeeUpdateNotice).toBe(false);
    expect(store.canTriggerManualCheck).toBe(false);
  });

  it('calcula canSeeUpdateNotice según rol administrativo y disponibilidad de update', () => {
    const store = useVersionCheckStore();
    const auth = useAuthStore();

    store.updateAvailable = true;

    // Rol NOC_MONITOR -> false
    auth.user = { id: '1', role: 'NOC_MONITOR' } as WebFigDynamic;
    expect(store.canSeeUpdateNotice).toBe(false);

    // Rol FIELD_TECH -> false
    auth.user = { id: '1', role: 'FIELD_TECH' } as WebFigDynamic;
    expect(store.canSeeUpdateNotice).toBe(false);

    // Rol SUPERVISOR -> true
    auth.user = { id: '1', role: 'SUPERVISOR' } as WebFigDynamic;
    expect(store.canSeeUpdateNotice).toBe(true);

    // Rol TENANT_ADMIN -> true
    auth.user = { id: '1', role: 'TENANT_ADMIN' } as WebFigDynamic;
    expect(store.canSeeUpdateNotice).toBe(true);

    // Rol SUPERADMIN_GLOBAL -> true
    auth.user = { id: '1', role: 'SUPERADMIN_GLOBAL' } as WebFigDynamic;
    expect(store.canSeeUpdateNotice).toBe(true);

    // Si updateAvailable es false, ningún rol lo ve
    store.updateAvailable = false;
    expect(store.canSeeUpdateNotice).toBe(false);
  });

  it('calcula canTriggerManualCheck solo para SUPERADMIN y TENANT_ADMIN', () => {
    const store = useVersionCheckStore();
    const auth = useAuthStore();

    auth.user = { id: '1', role: 'SUPERVISOR' } as WebFigDynamic;
    expect(store.canTriggerManualCheck).toBe(false);

    auth.user = { id: '1', role: 'TENANT_ADMIN' } as WebFigDynamic;
    expect(store.canTriggerManualCheck).toBe(true);

    auth.user = { id: '1', role: 'SUPERADMIN_GLOBAL' } as WebFigDynamic;
    expect(store.canTriggerManualCheck).toBe(true);
  });

  it('applyStatus actualiza reactivamente el estado', () => {
    const store = useVersionCheckStore();
    store.applyStatus({
      enabled: true,
      current_version: '1.3.0',
      latest_version: '1.4.0',
      update_available: true,
      release_url: 'https://github.com/tecno-consultores/RoSGrid/releases/tag/v1.4.0',
      release_name: 'v1.4.0 Release',
      published_at: '2026-11-20T00:00:00Z',
      last_checked_at: '2026-11-20T01:00:00Z',
      last_status: 'ok',
    });

    expect(store.currentVersion).toBe('1.3.0');
    expect(store.latestVersion).toBe('1.4.0');
    expect(store.updateAvailable).toBe(true);
    expect(store.releaseName).toBe('v1.4.0 Release');
  });

  it('fetchVersionStatus llama al endpoint GET de forma fail-silent', async () => {
    const store = useVersionCheckStore();
    const { http } = await import('@/api/httpClient');
    (http.get as WebFigDynamic).mockResolvedValueOnce({
      data: {
        enabled: true,
        current_version: '1.3.0',
        latest_version: '1.4.0',
        update_available: true,
        release_url: 'https://github.com/tecno-consultores/RoSGrid/releases',
        release_name: 'v1.4.0',
        published_at: '2026-12-01T00:00:00Z',
        last_checked_at: '2026-12-01T01:00:00Z',
        last_status: 'ok',
      },
    });

    await store.fetchVersionStatus();
    expect(http.get).toHaveBeenCalledWith('/api/v1/system/version-check');
    expect(store.latestVersion).toBe('1.4.0');
  });

  it('refreshVersionCheck llama al endpoint POST de refresh', async () => {
    const store = useVersionCheckStore();
    const { http } = await import('@/api/httpClient');
    (http.post as WebFigDynamic).mockResolvedValueOnce({
      data: {
        enabled: true,
        current_version: '1.3.0',
        latest_version: '1.5.0',
        update_available: true,
        release_url: 'https://github.com/tecno-consultores/RoSGrid/releases',
        release_name: 'v1.5.0',
        published_at: '2026-12-05T00:00:00Z',
        last_checked_at: '2026-12-05T01:00:00Z',
        last_status: 'ok',
      },
    });

    await store.refreshVersionCheck();
    expect(http.post).toHaveBeenCalledWith('/api/v1/system/version-check/refresh', {});
    expect(store.latestVersion).toBe('1.5.0');
    expect(store.isRefreshing).toBe(false);
  });
});
