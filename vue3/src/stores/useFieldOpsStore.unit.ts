// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useFieldOpsStore } from './useFieldOpsStore';
import type { FiberCutIncident, FieldOrder, FieldVerifyResult } from '@/types';

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('useFieldOpsStore — Operaciones de Campo y Detección de Cortes', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  const sampleOrders: FieldOrder[] = [
    {
      id: 'ord-01',
      tenant_id: 't-1',
      customer_service_id: 'svc-01',
      status: 'ASSIGNED',
      notes: 'Instalación de ONU ZTE en Torre Residencial',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'ord-02',
      tenant_id: 't-1',
      customer_service_id: 'svc-02',
      status: 'CERTIFIED',
      onu_scanned_serial: 'ZTEGC1234567',
      onu_scanned_mac: '48:8F:5A:11:22:33',
      tech_latitude: 10.480594,
      tech_longitude: -66.903603,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const sampleVerification: FieldVerifyResult = {
    customer_service_id: 'svc-01',
    session_active: true,
    connection_type: 'PPPOE',
    uptime_seconds: 120,
    assigned_ipv4: '100.64.10.155',
    assigned_ipv6_prefix: '2803:cafe:b001:5600::/56',
    detected_mac: '48:8F:5A:11:22:33',
    detected_mode: 'ROUTER',
    ping_success: true,
    ping_avg_ms: 1.4,
    ping_loss_pct: 0,
    traffic_rx_kbps: 250.0,
    traffic_tx_kbps: 45.0,
    status_summary: 'Sesión activa y latencia óptima',
  };

  const sampleIncidents: FiberCutIncident[] = [
    {
      id: 'inc-01',
      tenant_id: 't-1',
      router_id: 'r-01',
      pon_port: 'gpon-olt1/1/1',
      optical_box: 'NAP-04',
      affected_onus_count: 5,
      status: 'DETECTED',
      incident_summary: 'POSIBLE CORTE DE FIBRA ÓPTICA: 5 ONUs caídas en Puerto gpon-olt1/1/1',
      detected_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  it('inicia con listas vacías y sin verificación activa', () => {
    const store = useFieldOpsStore();
    expect(store.orders).toEqual([]);
    expect(store.incidents).toEqual([]);
    expect(store.activeVerification).toBeNull();
    expect(store.isVerifying).toBe(false);
  });

  it('fetchOrders actualiza la lista de órdenes', async () => {
    const { http } = await import('@/api/httpClient');
    (http.get as any).mockResolvedValueOnce({ data: sampleOrders });

    const store = useFieldOpsStore();
    await store.fetchOrders(true);
    expect(store.orders).toHaveLength(2);
    expect(store.orders[0].id).toBe('ord-01');
  });

  it('verifySubscriberLive ejecuta diagnóstico y guarda resultado', async () => {
    const { http } = await import('@/api/httpClient');
    (http.post as any).mockResolvedValueOnce({ data: sampleVerification });

    const store = useFieldOpsStore();
    const res = await store.verifySubscriberLive('svc-01', '48:8F:5A:11:22:33');

    expect(res.session_active).toBe(true);
    expect(res.detected_mode).toBe('ROUTER');
    expect(store.activeVerification?.assigned_ipv4).toBe('100.64.10.155');
  });

  it('detectFiberCuts detecta caídas masivas agrupadas por PON / NAP', async () => {
    const { http } = await import('@/api/httpClient');
    (http.post as any).mockResolvedValueOnce({ data: sampleIncidents });

    const store = useFieldOpsStore();
    const incs = await store.detectFiberCuts(3);

    expect(incs).toHaveLength(1);
    expect(incs[0].affected_onus_count).toBe(5);
    expect(store.incidents[0].pon_port).toBe('gpon-olt1/1/1');
  });
});
