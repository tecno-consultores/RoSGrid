// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref, shallowRef, triggerRef } from 'vue';
import type { MaintenanceWindowItem, RouterItem } from '@/types';

export const useInventoryStore = defineStore('inventory', () => {
  // shallowRef obligatorio para colecciones masivas de hardware
  const routers = shallowRef<RouterItem[]>([]);
  const maintenanceWindows = shallowRef<MaintenanceWindowItem[]>([]);

  const selectedRouterId = ref<string | null>(null);
  const filterRole = ref<string | null>(null);
  const filterStatus = ref<string | null>(null);
  const searchQuery = ref<string>('');

  const selectedRouter = computed<RouterItem | null>(() => {
    if (!selectedRouterId.value) return null;
    return routers.value.find((r) => r.id === selectedRouterId.value) || null;
  });

  const filteredRouters = computed<RouterItem[]>(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const role = filterRole.value;
    const status = filterStatus.value;

    return routers.value.filter((r) => {
      if (role && r.network_role !== role) return false;
      if (status && r.admin_state !== status) return false;
      if (!q) return true;
      return (
        r.display_name.toLowerCase().includes(q) ||
        r.ip_address.toLowerCase().includes(q) ||
        (r.serial_number && r.serial_number.toLowerCase().includes(q)) ||
        (r.ros_identity && r.ros_identity.toLowerCase().includes(q))
      );
    });
  });

  function setRouters(items: RouterItem[]): void {
    routers.value = items;
    triggerRef(routers);
  }

  function updateRouter(updated: RouterItem): void {
    const idx = routers.value.findIndex((r) => r.id === updated.id);
    if (idx !== -1) {
      routers.value[idx] = updated;
      triggerRef(routers);
    }
  }

  function setMaintenanceWindows(items: MaintenanceWindowItem[]): void {
    maintenanceWindows.value = items;
    triggerRef(maintenanceWindows);
  }

  function selectRouter(id: string | null): void {
    selectedRouterId.value = id;
  }

  function clearInventory(): void {
    routers.value = [];
    maintenanceWindows.value = [];
    selectedRouterId.value = null;
    triggerRef(routers);
    triggerRef(maintenanceWindows);
  }

  async function fetchRouters(): Promise<void> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>('/api/v1/inventory/routers');
      const raw = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      const items: RouterItem[] = raw.map((item: any) => ({
        ...item,
        ip_address:
          item.ip_address ||
          (item.api_base_url
            ? item.api_base_url.replace(/^https?:\/\//, '').split('/')[0].split(':')[0]
            : ''),
        ros_version: item.ros_version || 'v7',
        is_reachable: item.is_reachable ?? false,
      }));
      setRouters(items);
    } catch {
      // Sin datos de demostración: si falla la red, el inventario permanece vacío
      setRouters([]);
    }
  }

  async function deleteRouter(routerId: string): Promise<void> {
    const { http } = await import('@/api/httpClient');
    await http.delete(`/api/v1/inventory/routers/${routerId}`);
    routers.value = routers.value.filter((r) => r.id !== routerId);
  }

  return {
    routers,
    maintenanceWindows,
    selectedRouterId,
    selectedRouter,
    filterRole,
    filterStatus,
    searchQuery,
    filteredRouters,
    setRouters,
    updateRouter,
    setMaintenanceWindows,
    selectRouter,
    clearInventory,
    fetchRouters,
    deleteRouter,
  };
});
