// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useIpamStore } from './useIpamStore';
import type { IPAMPrefix, IPAMVrf } from '@/types';

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('useIpamStore — Gestor IPAM Dual-Stack Universal', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  const sampleVrfs: IPAMVrf[] = [
    {
      id: 'vrf-1',
      tenant_id: 't-1',
      name: 'default',
      description: 'VRF Principal',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'vrf-2',
      tenant_id: 't-1',
      name: 'vrf-clientes',
      route_distinguisher: '65000:100',
      description: 'VRF Abonados FTTH',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const samplePrefixes: IPAMPrefix[] = [
    {
      id: 'pfx-1',
      tenant_id: 't-1',
      vrf_id: 'vrf-1',
      prefix: '100.64.0.0/16',
      ip_family: 'IPv4',
      role: 'CGNAT',
      status: 'ACTIVE',
      is_pool: true,
      utilization_pct: 65.5,
      description: 'Supernet CGNAT Residencial',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'pfx-2',
      tenant_id: 't-1',
      vrf_id: 'vrf-2',
      prefix: '2803:cafe::/32',
      ip_family: 'IPv6',
      role: 'CUSTOMER_RESIDENTIAL',
      status: 'ACTIVE',
      is_pool: false,
      default_child_prefix_len: 56,
      utilization_pct: 12.0,
      description: 'Bloque IPv6 Delegado Clientes',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'pfx-3',
      tenant_id: 't-1',
      vrf_id: 'vrf-2',
      prefix: '2803:cafe:b000::/48',
      ip_family: 'IPv6',
      role: 'CUSTOMER_CORPORATE',
      status: 'ACTIVE',
      is_pool: false,
      default_child_prefix_len: 64,
      utilization_pct: 25.0,
      description: 'Bloque Corporativo Banco Mercantil',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  it('inicia con colecciones vacías y sin filtros', () => {
    const store = useIpamStore();
    expect(store.vrfs).toEqual([]);
    expect(store.prefixes).toEqual([]);
    expect(store.addresses).toEqual([]);
    expect(store.customerServices).toEqual([]);
    expect(store.selectedVrfId).toBeNull();
    expect(store.selectedPrefixId).toBeNull();
  });

  it('filtra prefijos por VRF, Familia IP y Rol', () => {
    const store = useIpamStore();
    store.prefixes = samplePrefixes;

    // Filtro por Familia IPv6
    store.filterFamily = 'IPv6';
    expect(store.filteredPrefixes).toHaveLength(2);

    // Filtro por Rol Corporativo
    store.filterRole = 'CUSTOMER_CORPORATE';
    expect(store.filteredPrefixes).toHaveLength(1);
    expect(store.filteredPrefixes[0].prefix).toBe('2803:cafe:b000::/48');

    // Filtro por VRF
    store.filterRole = null;
    store.filterFamily = null;
    store.selectedVrfId = 'vrf-1';
    expect(store.filteredPrefixes).toHaveLength(1);
    expect(store.filteredPrefixes[0].prefix).toBe('100.64.0.0/16');

    // Búsqueda por texto libre
    store.selectedVrfId = null;
    store.searchQuery = 'Mercantil';
    expect(store.filteredPrefixes).toHaveLength(1);
    expect(store.filteredPrefixes[0].description).toContain('Mercantil');
  });

  it('calcula selectedPrefix reactivamente', () => {
    const store = useIpamStore();
    store.prefixes = samplePrefixes;
    expect(store.selectedPrefix).toBeNull();

    store.selectedPrefixId = 'pfx-2';
    expect(store.selectedPrefix?.prefix).toBe('2803:cafe::/32');
  });

  it('fetchVrfs y fetchPrefixes obtienen datos del backend', async () => {
    const { http } = await import('@/api/httpClient');
    vi.mocked(http.get).mockResolvedValueOnce({ data: sampleVrfs } as never);
    vi.mocked(http.get).mockResolvedValueOnce({ data: samplePrefixes } as never);

    const store = useIpamStore();
    await store.fetchVrfs();
    expect(store.vrfs).toHaveLength(2);

    await store.fetchPrefixes();
    expect(store.prefixes).toHaveLength(3);
  });

  it('syncAllMikrotikIpam envía petición POST /api/v1/ipam/sync-all y recarga colecciones', async () => {
    const { http } = await import('@/api/httpClient');
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        synced_prefixes: 3,
        synced_ips: 13,
        routers_processed: 6,
        message: 'Descubrimiento IPAM completado en 6 routers',
      },
    } as never);
    vi.mocked(http.get).mockResolvedValueOnce({ data: samplePrefixes } as never);
    vi.mocked(http.get).mockResolvedValueOnce({ data: [] } as never);

    const store = useIpamStore();
    const result = await store.syncAllMikrotikIpam();

    expect(http.post).toHaveBeenCalledWith('/api/v1/ipam/sync-all');
    expect(result.synced_prefixes).toBe(3);
    expect(result.synced_ips).toBe(13);
    expect(store.prefixes).toHaveLength(3);
  });

  it('actualiza customerServices reactivamente ante evento rosgrid:device-status-changed', () => {
    const store = useIpamStore();
    store.customerServices = [
      {
        id: 'dev-42',
        tenant_id: 't-1',
        router_id: 'r-1',
        customer_name: 'Cliente 42',
        service_type: 'DHCP',
        auth_backend: 'LOCAL_SECRET',
        endpoint_identifier: 'CLI-042',
        onu_mode: 'ROUTER',
        last_reachability_status: 'OFFLINE',
        last_seen_at: '2026-11-04T12:00:00Z',
        status: 'ACTIVE',
        created_at: '2026-11-04T10:00:00Z',
        updated_at: '2026-11-04T12:00:00Z',
      },
      {
        id: 'dev-43',
        tenant_id: 't-1',
        router_id: 'r-1',
        customer_name: 'Cliente 43',
        service_type: 'DHCP',
        auth_backend: 'LOCAL_SECRET',
        endpoint_identifier: 'CLI-043',
        onu_mode: 'ROUTER',
        last_reachability_status: 'OFFLINE',
        last_seen_at: '2026-11-04T12:00:00Z',
        status: 'ACTIVE',
        created_at: '2026-11-04T10:00:00Z',
        updated_at: '2026-11-04T12:00:00Z',
      },
    ];

    window.dispatchEvent(
      new CustomEvent('rosgrid:device-status-changed', {
        detail: {
          deviceId: 'dev-42',
          status: 'ONLINE',
          lastSeenAt: '2026-11-04T21:00:00Z',
        },
      }),
    );

    expect(store.customerServices[0].last_reachability_status).toBe('ONLINE');
    expect(store.customerServices[0].last_seen_at).toBe('2026-11-04T21:00:00Z');
    // dev-43 permanece inalterado
    expect(store.customerServices[1].last_reachability_status).toBe('OFFLINE');

    // Evento sin deviceId no altera el estado
    window.dispatchEvent(
      new CustomEvent('rosgrid:device-status-changed', {
        detail: {},
      }),
    );
    expect(store.customerServices[0].last_reachability_status).toBe('ONLINE');
  });
});


