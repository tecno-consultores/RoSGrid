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
    (http.get as any).mockResolvedValueOnce({ data: sampleVrfs });
    (http.get as any).mockResolvedValueOnce({ data: samplePrefixes });

    const store = useIpamStore();
    await store.fetchVrfs();
    expect(store.vrfs).toHaveLength(2);

    await store.fetchPrefixes();
    expect(store.prefixes).toHaveLength(3);
  });
});
