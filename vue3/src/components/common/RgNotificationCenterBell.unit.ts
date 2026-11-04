// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgNotificationCenterBell from './RgNotificationCenterBell.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useNocEventsStore } from '@/stores/useNocEventsStore';
import { http } from '@/api/httpClient';

const BELL_BADGE_ID = '#notification-bell-badge';
const BELL_BTN_ID = '#btn-notification-bell';
const BORDE_CARACAS_NAME = 'Borde-Caracas';
const R111_NAME = 'r111';
const OFFLINE_STATUS = 'OFFLINE';
const MAINT_WINDOWS_PATH = '/inventory/maintenance-windows';
const BGP_OUTAGE_MSG = 'Sesión BGP caída con upstream';

const storageMock = (() => {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, String(value));
    },
    clear: () => {
      store.clear();
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: storageMock,
  writable: true,
  configurable: true,
});

if (typeof globalThis !== 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', {
    value: storageMock,
    writable: true,
    configurable: true,
  });
}

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('RgNotificationCenterBell.vue — Centro Táctico de Notificaciones In-App 11X', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
    vi.clearAllMocks();
    window.localStorage.clear();

    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-checker-1',
      username: 'sinfallas',
      email: 'sinfallas@rosgrid.local',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'sistemas',
      totp_enabled: true,
    });
  });

  it('muestra insignia con conteo de ítems que requieren acción (Maker-Checker + Router OFFLINE) y filtra ruido de sesión', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'app-101',
            status: 'PENDING',
            summary: 'Eliminar regla de firewall crítica',
            router_id: 'r-1',
            router_name: BORDE_CARACAS_NAME,
            requested_by: 'usr-maker-2',
            requested_by_username: 'operador_l2',
            created_at: '2026-11-04T18:00:00Z',
          },
        ],
      },
    } as never);

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-down-1',
        display_name: 'Core-Valencia',
        ip_address: '10.250.3.9',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'PRODUCTION',
        last_reachability_status: OFFLINE_STATUS,
        tags: [],
      },
    ] as never;

    const nocStore = useNocEventsStore();
    nocStore.recentEvents = [
      {
        id: 'ev-noise-1',
        eventName: 'MAINTENANCE',
        type: 'MAINTENANCE',
        severity: 'INFO',
        message: 'Session token renewed (por sinfallas)',
        summary: 'Session token renewed (por sinfallas)',
        router_name: 'sinfallas',
        routerDisplayName: 'sinfallas',
        timestampIso: '2026-11-04T18:01:00Z',
        timestamp: '2026-11-04T18:01:00Z',
      },
      {
        id: 'ev-bgp-1',
        eventName: 'WARNING',
        type: 'WARNING',
        severity: 'WARNING',
        message: BGP_OUTAGE_MSG,
        summary: BGP_OUTAGE_MSG,
        router_id: 'r-1',
        routerId: 'r-1',
        router_name: BORDE_CARACAS_NAME,
        routerDisplayName: BORDE_CARACAS_NAME,
        timestampIso: '2026-11-04T18:02:00Z',
        timestamp: '2026-11-04T18:02:00Z',
      },
      {
        id: 'ev-bgp-2',
        eventName: 'WARNING',
        type: 'WARNING',
        severity: 'WARNING',
        message: BGP_OUTAGE_MSG,
        summary: BGP_OUTAGE_MSG,
        router_id: 'r-1',
        routerId: 'r-1',
        router_name: BORDE_CARACAS_NAME,
        routerDisplayName: BORDE_CARACAS_NAME,
        timestampIso: '2026-11-04T18:03:00Z',
        timestamp: '2026-11-04T18:03:00Z',
      },
    ];

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    // 1 solicitud Maker-Checker + 1 router OFFLINE = 2 acciones requeridas
    const badge = wrapper.find(BELL_BADGE_ID);
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toBe('2');

    await wrapper.find(BELL_BTN_ID).trigger('click');
    await flushPromises();

    const text = wrapper.find('#rg-notification-popover').text();
    expect(text).toContain(BORDE_CARACAS_NAME);
    expect(text).toContain('Core-Valencia');
    // El ruido de "Session token renewed" jamás debe aparecer
    expect(text).not.toContain('Session token renewed');
    // Los 2 eventos BGP del mismo router se deduplican con ×2
    expect(text).toContain('×2');
  });

  it('permite aprobar en 1 clic desde la campana y reconocer (Ack) una caída sin borrar ítems no resueltos al marcar vistas', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: {
        items: [
          {
            id: 'app-202',
            status: 'PENDING',
            summary: 'Reinicio programado de nodo',
            router_id: 'r-1',
            router_name: R111_NAME,
            requested_by: 'usr-maker-9',
            requested_by_username: 'tecnico_noc',
            created_at: '2026-11-04T18:05:00Z',
          },
        ],
      },
    } as never);
    vi.mocked(http.post).mockResolvedValueOnce({ data: { status: 'APPROVED' } } as never);

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-down-2',
        display_name: 'Nodo-Maracay',
        ip_address: '10.250.3.20',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'PRODUCTION',
        last_reachability_status: OFFLINE_STATUS,
        tags: [],
      },
    ] as never;

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    await wrapper.find(BELL_BTN_ID).trigger('click');
    await flushPromises();

    // Al hacer clic en "✓ Vistas", se reconocen las alertas de red pero la aprobación Maker-Checker sigue requiriendo firma
    await wrapper.find('#btn-notif-mark-all-read').trigger('click');
    expect(wrapper.find(BELL_BADGE_ID).text()).toBe('1');

    // Aprobar en 1 clic desde la fila de la campana
    const approveBtn = wrapper.find('.btn-inline-action--approve');
    expect(approveBtn.exists()).toBe(true);
    await approveBtn.trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/operations/approvals/app-202/approve',
      expect.objectContaining({
        review_comment: expect.any(String),
      }),
    );
    expect(wrapper.find(BELL_BADGE_ID).exists()).toBe(false);
  });

  it('permite activar el modo Snooze de 30 minutos (🔕 30m) y navegar al hacer clic en una notificación', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: { items: [] } } as never);
    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-maint-1',
        display_name: R111_NAME,
        ip_address: '10.250.3.8',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'MAINTENANCE',
        last_reachability_status: 'ONLINE',
        tags: [],
      },
    ] as never;

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    await wrapper.find(BELL_BTN_ID).trigger('click');
    await wrapper.find('#btn-notif-snooze-30m').trigger('click');
    expect(wrapper.find(BELL_BTN_ID).text()).toContain('🔕');

    const firstRow = wrapper.find('.notif-row');
    await firstRow.trigger('click');
    expect(pushMock).toHaveBeenCalledWith(MAINT_WINDOWS_PATH);
  });
});
