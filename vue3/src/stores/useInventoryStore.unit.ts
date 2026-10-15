// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useInventoryStore } from './useInventoryStore';
import type { RouterItem, MaintenanceWindowItem } from '@/types';

describe('useInventoryStore — Inventario Flota MikroTik (shallowRef)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  const sampleRouters: RouterItem[] = [
    {
      id: 'r-01',
      tenant_id: 'tenant-1',
      display_name: 'CCR2004-Edge-Core',
      ros_identity: 'Edge-Core-1',
      ip_address: '10.0.0.1',
      api_port: 8728,
      ros_version: '7.15.2',
      model: 'CCR2004-16G-2S+',
      serial_number: 'SN12345CCR',
      network_role: 'CORE',
      admin_state: 'PRODUCTION',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
    },
    {
      id: 'r-02',
      tenant_id: 'tenant-1',
      display_name: 'RB5009-Tower-North',
      ros_identity: 'Tower-North',
      ip_address: '10.0.1.1',
      api_port: 8728,
      ros_version: '7.14.3',
      model: 'RB5009UG+S+IN',
      network_role: 'TOWER',
      admin_state: 'MAINTENANCE',
      is_reachable: true,
      last_seen_at: new Date().toISOString(),
    },
    {
      id: 'r-03',
      tenant_id: 'tenant-1',
      display_name: 'hAP-ax3-Branch-West',
      ros_identity: 'Branch-West',
      ip_address: '192.168.10.1',
      api_port: 8728,
      ros_version: '7.12.1',
      model: 'hAP ax3',
      network_role: 'BRANCH',
      admin_state: 'DECOMMISSIONED',
      is_reachable: false,
      last_seen_at: new Date().toISOString(),
    },
  ];

  it('inicia con colección vacía y sin selección', () => {
    const store = useInventoryStore();
    expect(store.routers).toEqual([]);
    expect(store.selectedRouter).toBeNull();
  });

  it('asigna routers masivos usando shallowRef y filtra por búsqueda', () => {
    const store = useInventoryStore();
    store.setRouters(sampleRouters);

    expect(store.routers.length).toBe(3);
    expect(store.filteredRouters.length).toBe(3);

    store.searchQuery = 'RB5009';
    expect(store.filteredRouters.length).toBe(1);
    expect(store.filteredRouters[0].display_name).toBe('RB5009-Tower-North');

    // Búsqueda por serial_number y ros_identity
    store.searchQuery = 'SN12345CCR';
    expect(store.filteredRouters.length).toBe(1);
    store.searchQuery = 'Edge-Core-1';
    expect(store.filteredRouters.length).toBe(1);

    store.searchQuery = '';
    store.filterRole = 'CORE';
    expect(store.filteredRouters.length).toBe(1);

    store.filterRole = null;
    store.filterStatus = 'MAINTENANCE';
    expect(store.filteredRouters.length).toBe(1);
    expect(store.filteredRouters[0].id).toBe('r-02');
  });

  it('selecciona router y actualiza sus datos en la lista', () => {
    const store = useInventoryStore();
    store.setRouters(sampleRouters);

    store.selectRouter('r-01');
    expect(store.selectedRouter?.display_name).toBe('CCR2004-Edge-Core');

    const updated = { ...sampleRouters[0], display_name: 'CCR2004-Core-Renamed' };
    store.updateRouter(updated);

    expect(store.selectedRouter?.display_name).toBe('CCR2004-Core-Renamed');

    // Seleccionar ID inexistente para probar fallback a null
    store.selectRouter('r-inexistente');
    expect(store.selectedRouter).toBeNull();
  });

  it('administra ventanas de mantenimiento y carga routers vía fetchRouters', async () => {
    const store = useInventoryStore();
    const mw: MaintenanceWindowItem[] = [
      {
        id: 'mw-1',
        tenant_id: 'tenant-1',
        title: 'Upgrade RouterOS v7.16',
        reason: 'Security patch',
        starts_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 3600000).toISOString(),
        suppress_alerts: true,
        is_cancelled: false,
      },
    ];

    store.setMaintenanceWindows(mw);
    expect(store.maintenanceWindows.length).toBe(1);
    expect(store.maintenanceWindows[0].title).toBe('Upgrade RouterOS v7.16');

    // Probar fetchRouters exitoso
    const { http } = await import('@/api/httpClient');
    const getSpy = vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { items: sampleRouters },
      headers: new Headers(),
    });

    await store.fetchRouters();
    expect(store.routers.length).toBe(3);
    getSpy.mockRestore();

    // Probar fetchRouters en fallo (fallback a mocks)
    store.clearInventory();
    const failSpy = vi.spyOn(http, 'get').mockRejectedValueOnce(new Error('Network error'));
    await store.fetchRouters();
    expect(store.routers.length).toBeGreaterThan(0);
    failSpy.mockRestore();

    store.clearInventory();
    expect(store.routers).toEqual([]);
    expect(store.maintenanceWindows).toEqual([]);
    expect(store.selectedRouterId).toBeNull();
  });
});
