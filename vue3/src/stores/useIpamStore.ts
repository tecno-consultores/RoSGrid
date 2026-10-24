// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref, shallowRef, triggerRef } from 'vue';
import type {
  CustomerService,
  IPAMAddress,
  IPAMPrefix,
  IPAMVrf,
  IPFamily,
  IPPrefixRole,
} from '@/types';

export const useIpamStore = defineStore('ipam', () => {
  const vrfs = shallowRef<IPAMVrf[]>([]);
  const prefixes = shallowRef<IPAMPrefix[]>([]);
  const addresses = shallowRef<IPAMAddress[]>([]);
  const customerServices = shallowRef<CustomerService[]>([]);

  const selectedVrfId = ref<string | null>(null);
  const selectedPrefixId = ref<string | null>(null);
  const filterFamily = ref<IPFamily | null>(null);
  const filterRole = ref<IPPrefixRole | null>(null);
  const searchQuery = ref<string>('');
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const filteredPrefixes = computed<IPAMPrefix[]>(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const vrfId = selectedVrfId.value;
    const fam = filterFamily.value;
    const role = filterRole.value;

    return prefixes.value.filter((p) => {
      if (vrfId && p.vrf_id !== vrfId) return false;
      if (fam && p.ip_family !== fam) return false;
      if (role && p.role !== role) return false;
      if (!q) return true;
      return (
        p.prefix.toLowerCase().includes(q) ||
        (p.description && p.description.toLowerCase().includes(q))
      );
    });
  });

  const selectedPrefix = computed<IPAMPrefix | null>(() => {
    if (!selectedPrefixId.value) return null;
    return prefixes.value.find((p) => p.id === selectedPrefixId.value) || null;
  });

  // VRFs
  async function fetchVrfs(): Promise<void> {
    try {
      isLoading.value = true;
      const { http } = await import('@/api/httpClient');
      const res = await http.get<IPAMVrf[]>('/api/v1/ipam/vrfs');
      vrfs.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(vrfs);
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al cargar VRFs';
    } finally {
      isLoading.value = false;
    }
  }

  async function createVrf(payload: {
    name: string;
    route_distinguisher?: string;
    description?: string;
  }): Promise<IPAMVrf> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<IPAMVrf>('/api/v1/ipam/vrfs', payload);
    vrfs.value = [...vrfs.value, res.data];
    triggerRef(vrfs);
    return res.data;
  }

  // Prefixes
  async function fetchPrefixes(): Promise<void> {
    try {
      isLoading.value = true;
      const { http } = await import('@/api/httpClient');
      const res = await http.get<IPAMPrefix[]>('/api/v1/ipam/prefixes');
      prefixes.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(prefixes);
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al cargar prefijos IPAM';
    } finally {
      isLoading.value = false;
    }
  }

  async function createPrefix(payload: {
    vrf_id: string;
    prefix: string;
    ip_family: IPFamily;
    role?: IPPrefixRole;
    is_pool?: boolean;
    default_child_prefix_len?: number;
    description?: string;
  }): Promise<IPAMPrefix> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<IPAMPrefix>('/api/v1/ipam/prefixes', payload);
    prefixes.value = [...prefixes.value, res.data];
    triggerRef(prefixes);
    return res.data;
  }

  async function getNextAvailable(
    prefixId: string,
  ): Promise<{ next_available: string; is_subnet: boolean; message: string }> {
    const { http } = await import('@/api/httpClient');
    const res = await http.get<{ next_available: string; is_subnet: boolean; message: string }>(
      `/api/v1/ipam/prefixes/${prefixId}/next-available`,
    );
    return res.data;
  }

  // Addresses
  async function fetchAddresses(prefixId?: string): Promise<void> {
    try {
      const { http } = await import('@/api/httpClient');
      const url = prefixId
        ? `/api/v1/ipam/addresses?prefix_id=${prefixId}`
        : '/api/v1/ipam/addresses';
      const res = await http.get<IPAMAddress[]>(url);
      addresses.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(addresses);
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al cargar direcciones IP';
    }
  }

  // Customer Services
  async function fetchCustomerServices(): Promise<void> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.get<CustomerService[]>('/api/v1/ipam/customer-services');
      customerServices.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(customerServices);
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al cargar servicios de clientes';
    }
  }


  async function createCustomerService(
    payload: Partial<CustomerService>,
  ): Promise<CustomerService> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<CustomerService>('/api/v1/ipam/customer-services', payload);
    customerServices.value = [...customerServices.value, res.data];
    triggerRef(customerServices);
    return res.data;
  }

  // Sync from MikroTik
  async function syncMikrotikIpam(
    routerId: string,
  ): Promise<{ synced_prefixes: number; synced_ips: number; message: string }> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<{ synced_prefixes: number; synced_ips: number; message: string }>(
      `/api/v1/ipam/sync-mikrotik/${routerId}`,
    );
    await fetchPrefixes();
    await fetchAddresses();
    return res.data;
  }

  // Sync all routers from MikroTik
  async function syncAllMikrotikIpam(): Promise<{
    synced_prefixes: number;
    synced_ips: number;
    routers_processed: number;
    message: string;
  }> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<{
      synced_prefixes: number;
      synced_ips: number;
      routers_processed: number;
      message: string;
    }>('/api/v1/ipam/sync-all');
    await fetchPrefixes();
    await fetchAddresses();
    return res.data;
  }

  return {
    vrfs,
    prefixes,
    addresses,
    customerServices,
    selectedVrfId,
    selectedPrefixId,
    filterFamily,
    filterRole,
    searchQuery,
    isLoading,
    error,
    filteredPrefixes,
    selectedPrefix,
    fetchVrfs,
    createVrf,
    fetchPrefixes,
    createPrefix,
    getNextAvailable,
    fetchAddresses,
    fetchCustomerServices,
    createCustomerService,
    syncMikrotikIpam,
    syncAllMikrotikIpam,
  };
});

