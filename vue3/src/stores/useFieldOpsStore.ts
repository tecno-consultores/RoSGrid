// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { ref, shallowRef, triggerRef } from 'vue';
import type { FiberCutIncident, FieldOrder, FieldVerifyResult } from '@/types';

export const useFieldOpsStore = defineStore('fieldOps', () => {
  const orders = shallowRef<FieldOrder[]>([]);
  const incidents = shallowRef<FiberCutIncident[]>([]);
  const activeVerification = ref<FieldVerifyResult | null>(null);
  const isVerifying = ref<boolean>(false);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  async function fetchOrders(myOrdersOnly: boolean = false): Promise<void> {
    try {
      isLoading.value = true;
      const { http } = await import('@/api/httpClient');
      const res = await http.get<FieldOrder[]>(`/api/v1/field-ops/orders?my_orders_only=${myOrdersOnly}`);
      orders.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(orders);
    } catch (e: any) {
      error.value = e?.message || 'Error al cargar órdenes de campo';
    } finally {
      isLoading.value = false;
    }
  }

  async function createOrder(payload: { customer_service_id: string; assigned_tech_id?: string; notes?: string }): Promise<FieldOrder> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<FieldOrder>('/api/v1/field-ops/orders', payload);
    orders.value = [res.data, ...orders.value];
    triggerRef(orders);
    return res.data;
  }

  async function verifySubscriberLive(
    customerServiceId: string,
    scannedMac?: string,
    scannedSerial?: string,
  ): Promise<FieldVerifyResult> {
    try {
      isVerifying.value = true;
      activeVerification.value = null;
      const { http } = await import('@/api/httpClient');
      const res = await http.post<FieldVerifyResult>(`/api/v1/field-ops/verify/${customerServiceId}`, {
        customer_service_id: customerServiceId,
        onu_scanned_mac: scannedMac,
        onu_scanned_serial: scannedSerial,
      });
      activeVerification.value = res.data;
      return res.data;
    } finally {
      isVerifying.value = false;
    }
  }

  async function certifyInstallation(payload: {
    order_id: string;
    onu_scanned_serial: string;
    onu_scanned_mac?: string;
    tech_latitude?: number;
    tech_longitude?: number;
    customer_signature_svg?: string;
    notes?: string;
  }): Promise<FieldOrder> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<FieldOrder>('/api/v1/field-ops/certify', payload);
    const idx = orders.value.findIndex((o) => o.id === payload.order_id);
    if (idx !== -1) {
      orders.value[idx] = res.data;
      triggerRef(orders);
    }
    return res.data;
  }

  async function detectFiberCuts(thresholdOnus: number = 3): Promise<FiberCutIncident[]> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.post<FiberCutIncident[]>(`/api/v1/field-ops/detect-fiber-cuts?threshold_onus=${thresholdOnus}`);
      incidents.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(incidents);
      return incidents.value;
    } catch (e: any) {
      error.value = e?.message || 'Error en motor de detección de cortes';
      return [];
    }
  }

  return {
    orders,
    incidents,
    activeVerification,
    isVerifying,
    isLoading,
    error,
    fetchOrders,
    createOrder,
    verifySubscriberLive,
    certifyInstallation,
    detectFiberCuts,
  };
});
