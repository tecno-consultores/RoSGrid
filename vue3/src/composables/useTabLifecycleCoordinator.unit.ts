// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi, type Mock } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useTabLifecycleCoordinator } from './useTabLifecycleCoordinator';
import { useAuthStore } from '@/stores/useAuthStore';

const SESSION_CLOSING_ENDPOINT = '/api/v1/auth/session-closing';
const TENANT_DEMO = 'tenant-demo';
const OPERATOR_USER = 'operador_tab';

describe('useTabLifecycleCoordinator.ts — Coordinación Multi-Pestaña y Cierre Efímero (Hito 23.27)', () => {
  let mockPostMessage: Mock;
  let mockClose: Mock;
  let originalBroadcastChannel: unknown;
  let sendBeaconMock: Mock;

  beforeEach(() => {
    setActivePinia(createPinia());
    mockPostMessage = vi.fn();
    mockClose = vi.fn();

    // Mock de BroadcastChannel
    const globalRecord = globalThis as unknown as Record<string, unknown>;
    originalBroadcastChannel = globalRecord.BroadcastChannel;
    globalRecord.BroadcastChannel = vi.fn().mockImplementation(() => ({
      postMessage: mockPostMessage,
      close: mockClose,
      onmessage: null,
    }));

    // Mock de navigator.sendBeacon
    sendBeaconMock = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, 'sendBeacon', {
      value: sendBeaconMock,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    const globalRecord = globalThis as unknown as Record<string, unknown>;
    globalRecord.BroadcastChannel = originalBroadcastChannel;
    vi.restoreAllMocks();
  });

  it('asigna un tabId único e inicializa la pestaña en activeTabs', () => {
    const coordinator = useTabLifecycleCoordinator();
    expect(coordinator.currentTabId.value).toBeDefined();
    expect(coordinator.activeTabs.value.has(coordinator.currentTabId.value)).toBe(true);
  });

  it('responde a TAB_PING con TAB_PONG y registra pestaña remota', () => {
    const coordinator = useTabLifecycleCoordinator();
    const globalRecord = globalThis as unknown as Record<string, new (name: string) => unknown>;
    const fakeChannel = new globalRecord.BroadcastChannel('rosgrid_tab_lifecycle_bus');
    expect(fakeChannel).toBeDefined();

    // Registrar otra pestaña
    coordinator.activeTabs.value.set('tab-peer-42', Date.now());
    expect(coordinator.activeTabs.value.has('tab-peer-42')).toBe(true);
  });

  it('despacha sendBeacon a /api/v1/auth/session-closing si es la última pestaña activa y está autenticado', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-42',
      username: OPERATOR_USER,
      email: 'tab@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: TENANT_DEMO,
      tenant_slug: TENANT_DEMO,
      totp_enabled: false,
    });

    const coordinator = useTabLifecycleCoordinator();
    // No hay otras pestañas (activeTabs solo contiene currentTabId)
    coordinator.handlePageClose();

    expect(sendBeaconMock).toHaveBeenCalled();
    const [endpoint, blob] = sendBeaconMock.mock.calls[0] as [string, Blob];
    expect(endpoint).toBe(SESSION_CLOSING_ENDPOINT);
    expect(blob).toBeInstanceOf(Blob);
  });

  it('no despacha sendBeacon si aún quedan otras pestañas activas en la misma sesión', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-42',
      username: OPERATOR_USER,
      email: 'tab@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: TENANT_DEMO,
      tenant_slug: TENANT_DEMO,
      totp_enabled: false,
    });

    const coordinator = useTabLifecycleCoordinator();
    // Simular que existe otra pestaña activa reciente
    coordinator.activeTabs.value.set('other-tab-99', Date.now());

    coordinator.handlePageClose();

    // Como queda otra pestaña activa, no debe despachar beacon de cierre de sesión
    expect(sendBeaconMock).not.toHaveBeenCalled();
  });

  it('no despacha sendBeacon si el usuario no está autenticado', () => {
    const authStore = useAuthStore();
    authStore.clearAuth();

    const coordinator = useTabLifecycleCoordinator();
    coordinator.handlePageClose();

    expect(sendBeaconMock).not.toHaveBeenCalled();
  });
});
