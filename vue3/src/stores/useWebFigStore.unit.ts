// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useWebFigStore, MAX_OPEN_TABS } from './useWebFigStore';
import type { RouterTabItem } from '@/types';

// Mock del cliente HTTP para interceptar confirm, rollback y verify
vi.mock('@/api/httpClient', () => ({
  http: {
    post: vi.fn().mockResolvedValue({
      data: {
        verified: true,
        latency_ms: 15.4,
        job_name: 'rosgrid-safemode-abc',
        summary: 'Ajuste de MTU',
      },
    }),
  },
}));

describe('useWebFigStore — Pestañas en RAM (Cola máx 5) y Safe Mode 60s 2 Fases', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('inicia con pestaña Dashboard por defecto y Safe Mode inactivo', () => {
    const store = useWebFigStore();
    expect(store.openRouterTabs.length).toBe(1);
    expect(store.activeTabId).toBe('RouterLiveDashboard');
    expect(store.isSafeModeActive).toBe(false);
    expect(store.safeModeCountdownSeconds).toBe(60);
  });

  it('abre pestaña y la enfoca', () => {
    const store = useWebFigStore();
    const tab: RouterTabItem = {
      tabId: 'interfaces-sfp',
      routeName: 'InterfacesAndSfp',
      label: 'Interfaces & SFP',
      icon: '🔌',
      closable: true,
    };
    store.openOrFocusTab(tab);

    expect(store.openRouterTabs.length).toBe(2);
    expect(store.activeTabId).toBe('interfaces-sfp');

    // Re-enfocar la misma pestaña no añade duplicados
    store.openOrFocusTab(tab);
    expect(store.openRouterTabs.length).toBe(2);
  });

  it('limita la cola a un máximo de 5 pestañas expulsando la primera cerrable (FIFO)', () => {
    const store = useWebFigStore();
    for (let i = 1; i <= 5; i++) {
      store.openOrFocusTab({
        tabId: `tab-${i}`,
        routeName: `Route-${i}`,
        label: `Pestaña ${i}`,
        icon: '📁',
        closable: true,
      });
    }

    expect(store.openRouterTabs.length).toBe(MAX_OPEN_TABS);
    // tab-1 debe haber sido expulsada al intentar agregar más de 5 pestañas
    expect(store.openRouterTabs.some((t) => t.tabId === 'tab-1')).toBe(false);
  });

  it('permite cerrar pestaña y re-enfoca pestaña adyacente', () => {
    const store = useWebFigStore();
    const tab1: RouterTabItem = {
      tabId: 't1',
      routeName: 'R1',
      label: 'T1',
      icon: '1',
      closable: true,
    };
    const tab2: RouterTabItem = {
      tabId: 't2',
      routeName: 'R2',
      label: 'T2',
      icon: '2',
      closable: true,
    };
    store.openOrFocusTab(tab1);
    store.openOrFocusTab(tab2);

    expect(store.activeTabId).toBe('t2');
    store.closeTab('t2');

    expect(store.openRouterTabs.some((t) => t.tabId === 't2')).toBe(false);
    expect(store.activeTabId).toBe('t1');

    // Intentar cerrar pestaña inexistente y pestaña no cerrable (dashboard)
    store.closeTab('non-existent-tab');
    store.closeTab('RouterLiveDashboard');
    expect(store.openRouterTabs.some((t) => t.tabId === 'RouterLiveDashboard')).toBe(true);
  });

  it('activa Safe Mode con Dead Man Switch de 60s y cuenta regresiva con auto-rollback', async () => {
    const store = useWebFigStore();
    store.setCurrentRouter({
      id: 'r-test-1',
      tenant_id: 't-1',
      display_name: 'CHR-Test',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15',
      admin_state: 'PRODUCTION',
      is_reachable: true,
    });

    store.startSafeModeCountdown(2, {
      job_name: 'rosgrid-safemode-auto',
      summary: 'Cambio de prueba',
    });

    expect(store.isSafeModeActive).toBe(true);
    expect(store.safeModeCountdownSeconds).toBe(2);
    expect(store.safeModeJobName).toBe('rosgrid-safemode-auto');

    // Avanzar el reloj hasta expirar la cuenta regresiva
    await vi.advanceTimersByTimeAsync(3000);

    expect(store.isSafeModeActive).toBe(false);
    expect(store.safeModeRevertedNotice).toContain('Tiempo de Safe Mode (60s) agotado');
  });

  it('asigna y limpia el router actual y limpia el espacio de trabajo', () => {
    const store = useWebFigStore();
    store.setCurrentRouter({
      id: 'r-1',
      tenant_id: 't-1',
      display_name: 'CCR',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15',
      admin_state: 'PRODUCTION',
      is_reachable: true,
    });
    expect(store.currentRouter?.display_name).toBe('CCR');

    store.clearRouterWorkspace();
    expect(store.currentRouter).toBeNull();
    expect(store.openRouterTabs.length).toBe(1);
    expect(store.activeTabId).toBe('RouterLiveDashboard');
  });

  it('confirma cambios llamando al endpoint /safemode/confirm y emite refresco', async () => {
    const store = useWebFigStore();
    store.setCurrentRouter({
      id: 'r-confirm-1',
      tenant_id: 't-1',
      display_name: 'CCR-1',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15',
      admin_state: 'PRODUCTION',
      is_reachable: true,
    });

    store.startSafeModeCountdown(60, { job_name: 'job-to-confirm' });
    expect(store.isSafeModeActive).toBe(true);

    const refreshSpy = vi.fn();
    window.addEventListener('rosgrid:webfig-refresh', refreshSpy);

    await store.confirmSafeModeChanges();

    expect(store.isSafeModeActive).toBe(false);
    expect(refreshSpy).toHaveBeenCalled();
    window.removeEventListener('rosgrid:webfig-refresh', refreshSpy);
  });

  it('revierte cambios manualmente llamando a /safemode/rollback y muestra aviso', async () => {
    const store = useWebFigStore();
    store.setCurrentRouter({
      id: 'r-rollback-1',
      tenant_id: 't-1',
      display_name: 'CCR-1',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15',
      admin_state: 'PRODUCTION',
      is_reachable: true,
    });

    store.startSafeModeCountdown(60, { summary: 'VLAN 100 eliminada' });
    await store.rollbackSafeModeChanges(false);

    expect(store.isSafeModeActive).toBe(false);
    expect(store.safeModeRevertedNotice).toContain('Cambio revertido manualmente');
    expect(store.safeModeRevertedNotice).toContain('VLAN 100 eliminada');

    store.dismissSafeModeRevertedNotice();
    expect(store.safeModeRevertedNotice).toBe('');
  });

  it('verifica cambios en vivo en el router llamando a /safemode/verify', async () => {
    const store = useWebFigStore();
    store.setCurrentRouter({
      id: 'r-verify-1',
      tenant_id: 't-1',
      display_name: 'CCR-1',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15',
      admin_state: 'PRODUCTION',
      is_reachable: true,
    });

    store.startSafeModeCountdown(60);
    await store.verifySafeModeOnRouter();

    expect(store.safeModeLiveVerified).toBe(true);
    expect(store.safeModeVerifyLatencyMs).toBe(15.4);
    expect(store.safeModeJobName).toBe('rosgrid-safemode-abc');
  });

  it('handleMutationResponse captura metadatos de _safemode de la respuesta del backend', () => {
    const store = useWebFigStore();
    store.handleMutationResponse({
      status: 200,
      data: {
        success: true,
        _safemode: {
          job_name: 'rosgrid-safemode-meta',
          expires_in: 60,
          summary: 'Cambio de comentario en interfaz',
          rollback_cli: '/interface/set ether1 comment="antiguo"',
        },
      },
    });

    expect(store.isSafeModeActive).toBe(true);
    expect(store.safeModeJobName).toBe('rosgrid-safemode-meta');
    expect(store.safeModeSummary).toBe('Cambio de comentario en interfaz');
    expect(store.safeModeRollbackCli).toBe('/interface/set ether1 comment="antiguo"');
  });
});
