// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useNocEventsStore } from './useNocEventsStore';

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  public readyState = 0; // CONNECTING
  public onopen: (() => void) | null = null;
  public onmessage: ((event: { data: string }) => void) | null = null;
  public onclose: (() => void) | null = null;
  public onerror: (() => void) | null = null;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) this.onopen();
    }, 10);
  }

  public close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}

describe('useNocEventsStore — WebSocket Global & Alertas NOC', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('inicia desconectado y sin eventos', () => {
    const store = useNocEventsStore();
    expect(store.isConnected).toBe(false);
    expect(store.recentEvents).toEqual([]);
    expect(store.activeAlertsCount).toBe(0);
    expect(store.pendingApprovalsCount).toBe(0);
  });

  it('conecta websocket y procesa ciclo de vida', () => {
    const store = useNocEventsStore();
    store.connectEventsWebSocket('ws://localhost:8000/ws/test');

    expect(MockWebSocket.instances.length).toBe(1);
    vi.advanceTimersByTime(20);

    expect(store.isConnected).toBe(true);

    // Conectar cuando ya está conectado para cubrir rama guard
    store.connectEventsWebSocket();

    // Mensaje inválido para cubrir bloque catch
    store.handleIncomingEvent('INVALID_NON_JSON_STRING');

    // Enviar mensajes a través del socket con distintas variantes
    const ws = MockWebSocket.instances[0];
    if (ws.onmessage) {
      ws.onmessage({
        data: JSON.stringify({
          id: 'ws-1',
          event_name: 'ROUTER_ALERT',
          severity: 'CRITICAL',
          message: 'Falla de enlace',
        }),
      });
      // Mensaje con event en lugar de event_name, severity WARNING y detail
      ws.onmessage({
        data: JSON.stringify({
          event: 'MAKER_CHECKER_REQUESTED',
          severity: 'WARNING',
          detail: 'Aprobación de regla firewall requerida',
        }),
      });
      // Mensaje vacío para ejercitar todos los fallbacks predeterminados
      ws.onmessage({
        data: JSON.stringify({}),
      });
    }

    expect(store.recentEvents.length).toBe(3);
    expect(store.activeAlertsCount).toBe(2);
    expect(store.pendingApprovalsCount).toBe(1);

    // Simular error y cierre con backoff
    if (ws.onerror) {
      ws.onerror();
    }
    if (ws.onclose) {
      ws.onclose();
    }

    // Avanzar temporizador para ejecutar reconexión automática
    vi.advanceTimersByTime(6000);

    // Desconectar mientras reconnectTimer está activo
    store.disconnectEventsWebSocket();
    expect(store.isConnected).toBe(false);

    // Conectar sin wsUrl usando protocolo https
    const origLocation = window.location;
    Object.defineProperty(window, 'location', {
      value: { protocol: 'https:', host: 'rosgrid.local' },
      writable: true,
      configurable: true,
    });
    store.connectEventsWebSocket();
    expect(MockWebSocket.instances.length).toBeGreaterThan(1);
    store.disconnectEventsWebSocket();
    Object.defineProperty(window, 'location', {
      value: origLocation,
      writable: true,
      configurable: true,
    });

    // Error en constructor de WebSocket
    vi.stubGlobal('WebSocket', () => {
      throw new Error('WebSocket blocked by CSP');
    });
    store.connectEventsWebSocket('ws://blocked');
    expect(store.isConnected).toBe(false);
  });

  it('procesa mensaje entrante de alerta crítica incrementando contador', () => {
    const store = useNocEventsStore();
    const eventPayload = JSON.stringify({
      id: 'alt-001',
      event_name: 'BGP_SESSION_DOWN',
      router_id: 'r-01',
      router_display_name: 'CCR2004-Edge-Core',
      severity: 'CRITICAL',
      message: 'Sesión BGP con AS27775 caída',
      timestamp_iso: new Date().toISOString(),
    });

    store.handleIncomingEvent(eventPayload);

    expect(store.recentEvents.length).toBe(1);
    expect(store.activeAlertsCount).toBe(1);
    expect(store.recentEvents[0].eventName).toBe('BGP_SESSION_DOWN');
  });

  it('procesa evento de aprobación Maker-Checker incrementando pendingApprovalsCount', () => {
    const store = useNocEventsStore();
    const approvalPayload = JSON.stringify({
      id: 'appr-001',
      event_name: 'APPROVAL_NEEDED',
      router_id: 'r-02',
      severity: 'INFO',
      message: 'Se requiere aprobación dual para regla de firewall',
    });

    store.handleIncomingEvent(approvalPayload);

    expect(store.pendingApprovalsCount).toBe(1);
  });

  it('procesa SESSION_KILLED ejecutando kill-switch', () => {
    const store = useNocEventsStore();
    const killedPayload = JSON.stringify({
      event_name: 'SESSION_KILLED',
    });

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    store.handleIncomingEvent(killedPayload);

    expect(eventSpy).toHaveBeenCalledOnce();
    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });

  it('ignora SESSION_KILLED cuando killed_by es SUPERADMIN_TENANT_SWITCH para evitar auto-deslogueo', () => {
    const store = useNocEventsStore();
    const switchPayload = JSON.stringify({
      event_name: 'SESSION_KILLED',
      killed_by: 'SUPERADMIN_TENANT_SWITCH',
      reason: 'Conmutación al tenant fibra-norte',
    });

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    store.handleIncomingEvent(switchPayload);

    expect(eventSpy).not.toHaveBeenCalled();
    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });

  it('reacciona al evento rosgrid:tenant-switched reconectando el WebSocket', () => {
    const store = useNocEventsStore();
    store.connectEventsWebSocket('ws://localhost:8000/ws/test');
    vi.advanceTimersByTime(20);
    expect(store.isConnected).toBe(true);

    const initialInstanceCount = MockWebSocket.instances.length;

    window.dispatchEvent(new CustomEvent('rosgrid:tenant-switched'));
    vi.advanceTimersByTime(200);

    expect(MockWebSocket.instances.length).toBeGreaterThan(initialInstanceCount);
  });

  it('permite limpiar la lista de eventos con clearEvents', () => {
    const store = useNocEventsStore();
    store.handleIncomingEvent(
      JSON.stringify({
        event_name: 'ROUTER_ONLINE',
        severity: 'INFO',
      }),
    );
    expect(store.recentEvents.length).toBe(1);

    store.clearEvents();
    expect(store.recentEvents).toEqual([]);
    expect(store.activeAlertsCount).toBe(0);
  });
});
