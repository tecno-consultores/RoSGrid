// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useApiHeartbeatStore } from './useApiHeartbeatStore';

describe('useApiHeartbeatStore — Monitoreo Ligero y Resiliente de API', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('inicializa con estado checking y métricas nulas', () => {
    const store = useApiHeartbeatStore();
    expect(store.status).toBe('checking');
    expect(store.latencyMs).toBeNull();
    expect(store.services).toBeNull();
    expect(store.isChecking).toBe(false);
  });

  it('marca estado online cuando /health responde 200 OK healthy', async () => {
    const store = useApiHeartbeatStore();

    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({
        status: 'healthy',
        service: 'rosgrid-api',
        database: 'connected',
        redis: 'connected',
      }),
    });

    await store.checkHealth();

    expect(store.status).toBe('online');
    expect(store.isOnline).toBe(true);
    expect(store.isOffline).toBe(false);
    expect(store.services).toEqual({ database: 'connected', redis: 'connected' });
    expect(typeof store.latencyMs).toBe('number');
  });

  it('marca estado degraded cuando /health responde 200 pero status es unhealthy', async () => {
    const store = useApiHeartbeatStore();

    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({
        status: 'unhealthy',
        database: 'connected',
        redis: 'disconnected',
      }),
    });

    await store.checkHealth();

    expect(store.status).toBe('degraded');
    expect(store.isDegraded).toBe(true);
  });

  it('marca estado degraded cuando /health responde 503 Service Unavailable', async () => {
    const store = useApiHeartbeatStore();

    global.fetch = vi.fn().mockResolvedValue({
      status: 503,
      ok: false,
      json: async () => ({
        status: 'unhealthy',
        database: 'disconnected',
        redis: 'disconnected',
      }),
    });

    await store.checkHealth();

    expect(store.status).toBe('degraded');
    expect(store.isDegraded).toBe(true);
  });

  it('marca estado offline cuando fetch lanza un error de red o timeout', async () => {
    const store = useApiHeartbeatStore();

    global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch / Connection refused'));

    await store.checkHealth();

    expect(store.status).toBe('offline');
    expect(store.isOffline).toBe(true);
    expect(store.latencyMs).toBeNull();
    expect(store.lastError).toContain('Connection refused');
  });

  it('actualiza estado pasivamente al recibir evento rosgrid:api-health-event exitoso', () => {
    const store = useApiHeartbeatStore();

    const event = new CustomEvent('rosgrid:api-health-event', {
      detail: { ok: true, status: 200, latencyMs: 16, url: '/api/v1/routers' },
    });

    store.handleApiActivity(event);

    expect(store.status).toBe('online');
    expect(store.latencyMs).toBe(16);
    expect(store.lastChecked).toBeInstanceOf(Date);
  });

  it('marca offline pasivamente al recibir evento de fallo de red (status: 0)', () => {
    const store = useApiHeartbeatStore();

    const event = new CustomEvent('rosgrid:api-health-event', {
      detail: { ok: false, status: 0, latencyMs: null, url: '/api/v1/routers' },
    });

    store.handleApiActivity(event);

    expect(store.status).toBe('offline');
    expect(store.latencyMs).toBeNull();
  });

  it('inicia y detiene el monitoreo sin duplicar listeners', async () => {
    const store = useApiHeartbeatStore();
    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ status: 'healthy', database: 'connected', redis: 'connected' }),
    });

    store.startMonitoring(10000);
    expect(store.isChecking).toBe(true);

    await vi.waitFor(() => expect(store.isChecking).toBe(false));
    expect(store.status).toBe('online');

    store.stopMonitoring();
  });
});
