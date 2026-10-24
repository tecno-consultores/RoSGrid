// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { ref, shallowRef, triggerRef } from 'vue';
import type {
  FiberCutIncident,
  FieldOrder,
  FieldVerifyResult,
  OpticalBoxDetailItem,
  OpticalBoxItem,
  SubscriberDeviceItem,
} from '@/types';

export const useFieldOpsStore = defineStore('fieldOps', () => {
  const orders = shallowRef<FieldOrder[]>([]);
  const incidents = shallowRef<FiberCutIncident[]>([]);
  const opticalBoxes = shallowRef<OpticalBoxItem[]>([]);
  const recentInstallations = shallowRef<SubscriberDeviceItem[]>([]);
  const selectedOpticalBox = ref<OpticalBoxDetailItem | null>(null);
  const activeVerification = ref<FieldVerifyResult | null>(null);
  const isVerifying = ref<boolean>(false);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  async function fetchOrders(myOrdersOnly: boolean = false): Promise<void> {
    try {
      isLoading.value = true;
      const { http } = await import('@/api/httpClient');
      const res = await http.get<FieldOrder[]>(
        `/api/v1/field-ops/orders?my_orders_only=${myOrdersOnly}`,
      );
      orders.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(orders);
    } catch (e: unknown) {
      error.value = (e as Error)?.message || 'Error al cargar órdenes de campo';
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchOpticalBoxes(routerId?: string): Promise<OpticalBoxItem[]> {
    try {
      isLoading.value = true;
      const { http } = await import('@/api/httpClient');
      const url = routerId
        ? `/api/v1/optical-boxes?router_id=${routerId}`
        : '/api/v1/optical-boxes';
      const res = await http.get<OpticalBoxItem[]>(url);
      opticalBoxes.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(opticalBoxes);
      return opticalBoxes.value;
    } catch (e: unknown) {
      error.value = (e as Error)?.message || 'Error al listar cajas NAP';
      return [];
    } finally {
      isLoading.value = false;
    }
  }

  async function createOpticalBox(payload: {
    router_id: string;
    box_code: string;
    brand?: string;
    model?: string;
    capacity_ports?: number;
    splitter_ratio?: string;
    installation_type?: string;
    physical_location?: string;
    input_power_dbm?: number;
    latitude: number;
    longitude: number;
    notes?: string;
  }): Promise<OpticalBoxItem> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<OpticalBoxItem>('/api/v1/optical-boxes', payload);
    opticalBoxes.value = [res.data, ...opticalBoxes.value];
    triggerRef(opticalBoxes);
    return res.data;
  }

  async function fetchOpticalBoxDetail(boxId: string): Promise<OpticalBoxDetailItem> {
    const { http } = await import('@/api/httpClient');
    const res = await http.get<OpticalBoxDetailItem>(`/api/v1/optical-boxes/${boxId}`);
    selectedOpticalBox.value = res.data;
    return res.data;
  }

  async function registerSubscriberDevice(payload: {
    router_id: string;
    endpoint_identifier: string;
    service_type: string;
    device_serial?: string;
    onu_mac_address?: string;
    onu_mode?: string;
    optical_box_id?: string;
    optical_box_port?: number;
    rx_optical_power_dbm?: number;
    drop_cable_meters?: number;
    latitude?: number;
    longitude?: number;
    bandwidth_profile_id?: string;
  }): Promise<SubscriberDeviceItem> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<SubscriberDeviceItem>('/api/v1/subscriber-devices', payload);
    recentInstallations.value = [res.data, ...recentInstallations.value];
    triggerRef(recentInstallations);
    return res.data;
  }

  async function pingSubscriberLive(deviceId: string): Promise<{
    device_id: string;
    last_reachability_status: string;
    ping_latency_ms?: number;
    packet_loss_pct?: number;
    message: string;
  }> {
    isVerifying.value = true;
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.post<{
        device_id: string;
        last_reachability_status: string;
        ping_latency_ms?: number;
        packet_loss_pct?: number;
        message: string;
      }>(`/api/v1/subscriber-devices/${deviceId}/ping`);
      return res.data;
    } finally {
      isVerifying.value = false;
    }
  }

  async function fetchRecentInstallations(): Promise<SubscriberDeviceItem[]> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.get<SubscriberDeviceItem[]>('/api/v1/subscriber-devices');
      const list = Array.isArray(res.data) ? res.data : [];
      recentInstallations.value = list.slice(0, 10);
      triggerRef(recentInstallations);
      return recentInstallations.value;
    } catch {
      return [];
    }
  }

  async function createOrder(payload: {
    customer_service_id: string;
    assigned_tech_id?: string;
    notes?: string;
  }): Promise<FieldOrder> {
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
      const res = await http.post<FieldVerifyResult>(
        `/api/v1/field-ops/verify/${customerServiceId}`,
        {
          customer_service_id: customerServiceId,
          onu_scanned_mac: scannedMac,
          onu_scanned_serial: scannedSerial,
        },
      );
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
      const res = await http.post<FiberCutIncident[]>(
        `/api/v1/field-ops/detect-fiber-cuts?threshold_onus=${thresholdOnus}`,
      );
      incidents.value = Array.isArray(res.data) ? res.data : [];
      triggerRef(incidents);
      return incidents.value;
    } catch (e: unknown) {
      error.value = (e as Error)?.message || 'Error en motor de detección de cortes';
      return [];
    }
  }

  return {
    orders,
    incidents,
    opticalBoxes,
    recentInstallations,
    selectedOpticalBox,
    activeVerification,
    isVerifying,
    isLoading,
    error,
    fetchOrders,
    fetchOpticalBoxes,
    createOpticalBox,
    fetchOpticalBoxDetail,
    registerSubscriberDevice,
    pingSubscriberLive,
    fetchRecentInstallations,
    createOrder,
    verifySubscriberLive,
    certifyInstallation,
    detectFiberCuts,
  };
});
