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
        latitude:
          item.latitude !== null && item.latitude !== undefined && item.latitude !== ''
            ? Number(item.latitude)
            : undefined,
        longitude:
          item.longitude !== null && item.longitude !== undefined && item.longitude !== ''
            ? Number(item.longitude)
            : undefined,
        model: item.model || item.model_name || item.board_name,
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

  // Roles de red configurables
  const defaultRoles = [
    'CORE',
    'EDGE_BGP',
    'WAN_BALANCER',
    'BRAS_PPPOE',
    'DISTRIBUTION_SWITCH',
    'TOWER_AP',
    'CORPORATE_CPE',
  ];
  const networkRoles = ref<string[]>([...defaultRoles]);
  const customRoles = ref<Array<{ id: string; role_name: string; description?: string }>>([]);

  async function fetchNetworkRoles(): Promise<void> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.get<{ roles: string[]; custom_roles: Array<{ id: string; role_name: string; description?: string }> }>('/api/v1/inventory/network-roles');
      if (res.data?.roles && res.data.roles.length > 0) {
        networkRoles.value = res.data.roles;
        customRoles.value = res.data.custom_roles || [];
      }
    } catch {
      // Si la API falla temporalmente, se mantienen los roles existentes
    }
  }

  async function createCustomRole(roleName: string, description?: string): Promise<void> {
    const { http } = await import('@/api/httpClient');
    await http.post('/api/v1/inventory/network-roles', {
      role_name: roleName,
      description: description || null,
    });
    await fetchNetworkRoles();
  }

  async function deleteCustomRole(roleName: string): Promise<void> {
    const { http } = await import('@/api/httpClient');
    await http.delete(`/api/v1/inventory/network-roles/${encodeURIComponent(roleName)}`);
    await fetchNetworkRoles();
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
    networkRoles,
    customRoles,
    setRouters,
    updateRouter,
    setMaintenanceWindows,
    selectRouter,
    clearInventory,
    fetchRouters,
    deleteRouter,
    fetchNetworkRoles,
    createCustomRole,
    deleteCustomRole,
  };
});

