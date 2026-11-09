/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import SubscribersMapView from './SubscribersMapView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
import { http } from '@/api/httpClient';

vi.mock('@/components/network/UnifiedNetworkMap.vue', () => ({
  default: {
    name: 'UnifiedNetworkMap',
    template: '<div class="mock-unified-network-map" data-testid="unified-network-map"></div>',
    props: ['routers', 'opticalBoxes', 'subscribers', 'selectedId', 'mode'],
    emits: ['select-subscriber', 'select-box', 'select-router', 'diagnose-subscriber'],
  },
}));

const MOCK_SERIAL = 'ZTEGC00001';
const MOCK_MAP_SELECTOR = '.mock-unified-network-map';

describe('SubscribersMapView.vue — Vista Bimodal de Mapa de Red y Clientes', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/inventory/routers')) {
        return {
          status: 200,
          headers: new Headers(),
          data: [
            {
              id: 'r-1',
              display_name: 'ROUTER-CORE-01',
              ip_address: '10.0.0.1',
              admin_state: 'PRODUCTION',
              is_reachable: true,
            },
          ],
        } as never;
      }
      return {
        status: 200,
        headers: new Headers(),
        data: [
          {
            id: 'onu-01',
            tenant_id: 't-1',
            router_id: 'r-1',
            service_type: 'FTTH_PPPOE',
            auth_backend: 'INTERNAL',
            onu_mode: 'ROUTER',
            device_serial: MOCK_SERIAL,
            onu_serial_number: MOCK_SERIAL,
            customer_name: 'Carlos Santana',
            customer_code: 'CLI-01',
            endpoint_identifier: 'CLI-01',
            assigned_ipv4: '192.168.88.50',
            pon_port: 'sfp-plus1',
            optical_box: 'NAP-A',
            latitude: 10.4806,
            longitude: -66.9036,
            is_custom_coordinates: false,
            last_reachability_status: 'ONLINE',
            status: 'ACTIVE',
            ping_latency_ms: 22,
            packet_loss_pct: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: 'onu-02',
            tenant_id: 't-1',
            router_id: 'r-1',
            service_type: 'FTTH_PPPOE',
            auth_backend: 'INTERNAL',
            onu_mode: 'BRIDGE',
            device_serial: 'HWTC00002',
            onu_serial_number: 'HWTC00002',
            customer_name: 'Ana Maria',
            customer_code: 'CLI-02',
            endpoint_identifier: 'CLI-02',
            assigned_ipv4: '192.168.88.51',
            pon_port: 'sfp-plus1',
            optical_box: 'NAP-A',
            latitude: 10.481,
            longitude: -66.904,
            is_custom_coordinates: true,
            last_reachability_status: 'ONLINE',
            status: 'ACTIVE',
            ping_latency_ms: 75,
            packet_loss_pct: 2,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      } as never;
    });
  });

  it('renderiza título de Modo ISP cuando isp_module_enabled está activo y no muestra botón de simulación', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2'); // Total equipos
    });
    expect(wrapper.text()).toContain('Mapa de Cobertura FTTH y Cajas NAP');
    expect(wrapper.find('.btn-simulate-dhcp').exists()).toBe(false);
  });

  it('renderiza título de Modo Empresa (No-ISP) y botón de sincronización DHCP', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: false });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2');
    });
    expect(wrapper.text()).toContain('Mapa de Red y Clientes DHCP');
    expect(wrapper.find('.btn-sync-dhcp').exists()).toBe(true);
    expect(wrapper.find('.btn-simulate-dhcp').exists()).toBe(false);
  });

  it('ejecuta sincronización DHCP real desde la interfaz', async () => {
    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: {
        message: 'Sincronización DHCP completada: 5 leases procesados.',
        routers_polled: 1,
        leases_found: 5,
        created_count: 3,
        updated_count: 2,
      },
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find('.btn-sync-dhcp').exists()).toBe(true);
    });

    await wrapper.find('.btn-sync-dhcp').trigger('click');
    expect(postSpy).toHaveBeenCalledWith('/api/v1/subscriber-devices/sync-dhcp');
  });

  it('abre drawer de cliente y permite test ping 1-click en vivo', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: {
        device_id: 'onu-01',
        last_reachability_status: 'ONLINE',
        ping_latency_ms: 12,
        packet_loss_pct: 0,
        message: 'Host alcanzable con 12ms',
      },
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
      expect(wrapper.text()).toContain('2');
    });

    const mapComponent = wrapper.findComponent({ name: 'UnifiedNetworkMap' });
    mapComponent.vm.$emit('select-subscriber', 'onu-01');
    await wrapper.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapper.find('.onu-detail-drawer').exists()).toBe(true);
    });
    expect(wrapper.text()).toContain('192.168.88.50');

    // Botón Ping 1-Click
    const pingBtn = wrapper.find('.drawer-ping-section button');
    await pingBtn.trigger('click');

    expect(postSpy).toHaveBeenCalledWith('/api/v1/subscriber-devices/onu-01/ping');
  });

  it('abre drawer de Caja NAP al emitir select-box', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const fieldStore = useFieldOpsStore();
    vi.spyOn(fieldStore, 'fetchOpticalBoxDetail').mockResolvedValue({
      id: 'box-01',
      tenant_id: 't-1',
      router_id: 'r-1',
      box_code: 'NAP-NORTE-01',
      capacity_ports: 16,
      splitter_ratio: '1:16',
      installation_type: 'POSTE',
      physical_location: 'Calle 4ta Poste 10',
      input_power_dbm: -15.5,
      latitude: 10.48,
      longitude: -66.90,
      status: 'ACTIVE',
      occupied_ports_count: 2,
      available_ports_count: 14,
      ports: [
        {
          port_number: 1,
          is_occupied: true,
          subscriber_id: 'onu-01',
          subscriber_identifier: 'ZTEGC00001',
          reachability_status: 'ONLINE',
        },
        {
          port_number: 2,
          is_occupied: false,
          reachability_status: 'FREE',
        },
      ],
      subscribers: [
        { id: 'onu-01', endpoint_identifier: 'CLI-01', device_serial: 'ZTEGC00001', optical_box_port: 1 } as never,
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const wrapper = mount(SubscribersMapView, {
      global: {
        stubs: {
          RouterLink: true,
        },
      },
    });
    await vi.waitFor(() => {
      expect(wrapper.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const mapComponent = wrapper.findComponent({ name: 'UnifiedNetworkMap' });
    mapComponent.vm.$emit('select-box', 'box-01');
    await wrapper.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NAP-NORTE-01');
      expect(wrapper.text()).toContain('Matriz de Puertos');
    });
  });

  it('muestra el botón #btn-import-subscribers-csv solo para SUPERADMIN_GLOBAL / TENANT_ADMIN y ejecuta dry-run + commit (Spec 100)', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'NOC_MONITOR';

    const wrapperNoc = mount(SubscribersMapView, {
      global: {
        stubs: { RouterLink: true },
      },
    });
    await vi.waitFor(() => {
      expect(wrapperNoc.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });
    expect(wrapperNoc.find('#btn-import-subscribers-csv').exists()).toBe(false);
    expect(wrapperNoc.find('#btn-import-optical-boxes-csv').exists()).toBe(false);

    authStore.currentRole = 'TENANT_ADMIN';
    authStore.tenantFeatures = { isp_module_enabled: true };
    const wrapperAdmin = mount(SubscribersMapView, {
      global: {
        stubs: { RouterLink: true },
      },
    });
    await vi.waitFor(() => {
      expect(wrapperAdmin.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });
    const importBtn = wrapperAdmin.find('#btn-import-subscribers-csv');
    expect(importBtn.exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-import-optical-boxes-csv').exists()).toBe(true);

    // Abrir modal
    await importBtn.trigger('click');
    expect(wrapperAdmin.find('#modal-import-subscribers-csv').exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-download-subscribers-csv-template').exists()).toBe(true);
    expect(wrapperAdmin.find('#input-subscribers-csv-file').exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-run-subscribers-dry-run').exists()).toBe(true);

    // Mock de descarga de plantilla CSV
    const spyGet = vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      headers: new Headers(),
      data: 'endpoint_identifier,onu_serial_number',
    } as never);

    await wrapperAdmin.find('#btn-download-subscribers-csv-template').trigger('click');
    expect(spyGet).toHaveBeenCalledWith('/api/v1/subscriber-devices/template-csv');

    // Mock de Dry-Run
    const dryRunPayload = {
      total_rows: 1,
      valid_rows_count: 1,
      invalid_rows_count: 0,
      can_proceed: true,
      rows: [
        {
          row_number: 2,
          endpoint_identifier: 'CLI-FTTH-001',
          onu_serial_number: 'HWTC12345678',
          onu_mac_address: 'AA:BB:CC:11:22:33',
          assigned_ipv4: '100.64.10.15',
          router_name: 'ROUTER-CORE-01',
          optical_box_name: 'NAP-NORTE-01',
          will_auto_create_box: true,
          box_port_number: 1,
          latitude: 10.4812,
          longitude: -66.9041,
          service_status: 'ACTIVE',
          is_valid: true,
          errors: [],
        },
      ],
    };
    const spyPost = vi.spyOn(http, 'post').mockImplementation(async (url: string) => {
      if (url.includes('/import-csv/dry-run')) {
        return { status: 200, headers: new Headers(), data: dryRunPayload } as never;
      }
      if (url.includes('/import-csv/commit')) {
        return {
          status: 200,
          headers: new Headers(),
          data: { imported_count: 1, created_ids: ['uuid-01'], message: 'Se importaron 1 clientes exitosamente.' },
        } as never;
      }
      return { status: 200, headers: new Headers(), data: {} } as never;
    });

    // Simular archivo seleccionado
    const fakeFile = new File(['csv content'], 'clientes.csv', { type: 'text/csv' });
    const fileInput = wrapperAdmin.find('#input-subscribers-csv-file');
    Object.defineProperty(fileInput.element, 'files', {
      value: [fakeFile],
      writable: false,
    });
    await fileInput.trigger('change');

    // Ejecutar Dry-Run
    await wrapperAdmin.find('#btn-run-subscribers-dry-run').trigger('click');
    await wrapperAdmin.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapperAdmin.find('.csv-preview-table').exists()).toBe(true);
      expect(wrapperAdmin.text()).toContain('CLI-FTTH-001');
      expect(wrapperAdmin.find('.badge-auto-create-box').exists()).toBe(true);
      expect(wrapperAdmin.find('#btn-commit-subscribers-csv').exists()).toBe(true);
    });

    // Ejecutar Commit
    await wrapperAdmin.find('#btn-commit-subscribers-csv').trigger('click');
    await wrapperAdmin.vm.$nextTick();

    await vi.waitFor(() => {
      expect(spyPost).toHaveBeenCalledWith(
        '/api/v1/subscriber-devices/import-csv/commit',
        expect.objectContaining({ rows: dryRunPayload.rows }),
      );
      expect(wrapperAdmin.find('#modal-import-subscribers-csv').exists()).toBe(false);
    });
  });

  it('asistente de carga masiva CSV de Cajas NAP con soporte Upsert (Hito 30.26 / Spec 103)', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';
    authStore.tenantFeatures = { isp_module_enabled: true };
    const wrapperAdmin = mount(SubscribersMapView, {
      global: {
        stubs: { RouterLink: true },
      },
    });
    await vi.waitFor(() => {
      expect(wrapperAdmin.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    const btnBoxes = wrapperAdmin.find('#btn-import-optical-boxes-csv');
    expect(btnBoxes.exists()).toBe(true);

    // Abrir modal Cajas NAP CSV
    await btnBoxes.trigger('click');
    expect(wrapperAdmin.find('#modal-import-optical-boxes-csv').exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-download-optical-boxes-csv-template').exists()).toBe(true);
    expect(wrapperAdmin.find('#input-optical-boxes-csv-file').exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-run-optical-boxes-dry-run').exists()).toBe(true);

    // Mock de descarga de plantilla CSV de Cajas NAP
    const spyGet = vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      headers: new Headers(),
      data: 'box_code,router_name,capacity_ports',
    } as never);

    await wrapperAdmin.find('#btn-download-optical-boxes-csv-template').trigger('click');
    expect(spyGet).toHaveBeenCalledWith('/api/v1/optical-boxes/template-csv');

    // Mock de Dry-Run con Upsert (1 actualización y 1 nueva)
    const boxesDryRunPayload = {
      total_rows: 2,
      valid_rows_count: 2,
      invalid_rows_count: 0,
      can_proceed: true,
      rows: [
        {
          row_number: 2,
          box_code: 'NAP-NORTE-01',
          router_name: 'ROUTER-CORE-01',
          capacity_ports: 32,
          splitter_ratio: '1:32',
          installation_type: 'FACADE',
          input_power_dbm: -17.5,
          latitude: 10.2323,
          longitude: -67.8798,
          physical_location: 'Poste P-14',
          is_update: true,
          is_valid: true,
          errors: [],
        },
        {
          row_number: 3,
          box_code: 'NAP-SUR-02',
          router_name: 'ROUTER-CORE-01',
          capacity_ports: 8,
          splitter_ratio: '1:8',
          installation_type: 'POLE',
          input_power_dbm: -18.2,
          latitude: 10.235,
          longitude: -67.881,
          physical_location: 'Poste Sur 10',
          is_update: false,
          is_valid: true,
          errors: [],
        },
      ],
    };

    const spyPost = vi.spyOn(http, 'post').mockImplementation(async (url: string) => {
      if (url.includes('/optical-boxes/import-csv/dry-run')) {
        return { status: 200, headers: new Headers(), data: boxesDryRunPayload } as never;
      }
      if (url.includes('/optical-boxes/import-csv/commit')) {
        return {
          status: 200,
          headers: new Headers(),
          data: {
            imported_count: 1,
            updated_count: 1,
            box_ids: ['box-uuid-01', 'box-uuid-02'],
            message: 'Se procesaron 2 Cajas NAP exitosamente (1 nuevas, 1 actualizadas).',
          },
        } as never;
      }
      return { status: 200, headers: new Headers(), data: {} } as never;
    });

    // Simular archivo seleccionado
    const fakeFile = new File(['csv content'], 'cajas.csv', { type: 'text/csv' });
    const fileInput = wrapperAdmin.find('#input-optical-boxes-csv-file');
    Object.defineProperty(fileInput.element, 'files', {
      value: [fakeFile],
      writable: false,
    });
    await fileInput.trigger('change');

    // Ejecutar Dry-Run
    await wrapperAdmin.find('#btn-run-optical-boxes-dry-run').trigger('click');
    await wrapperAdmin.vm.$nextTick();

    await vi.waitFor(() => {
      expect(wrapperAdmin.find('#modal-import-optical-boxes-csv .csv-preview-table').exists()).toBe(true);
      expect(wrapperAdmin.text()).toContain('NAP-NORTE-01');
      expect(wrapperAdmin.text()).toContain('NAP-SUR-02');
      expect(wrapperAdmin.find('.badge-upsert').exists()).toBe(true);
      expect(wrapperAdmin.find('.badge-create').exists()).toBe(true);
      expect(wrapperAdmin.find('#btn-commit-optical-boxes-csv').exists()).toBe(true);
    });

    // Ejecutar Commit
    await wrapperAdmin.find('#btn-commit-optical-boxes-csv').trigger('click');
    await wrapperAdmin.vm.$nextTick();

    await vi.waitFor(() => {
      expect(spyPost).toHaveBeenCalledWith(
        '/api/v1/optical-boxes/import-csv/commit',
        expect.objectContaining({ rows: boxesDryRunPayload.rows }),
      );
      expect(wrapperAdmin.find('#modal-import-optical-boxes-csv').exists()).toBe(false);
    });
  });

  it('paridad de visibilidad en #btn-import-optical-boxes-csv sin depender de isp_module_enabled y eliminación de doble ícono DHCP (Hito 30.29 / Spec 106)', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';
    // Empresa privada / no-ISP con isp_module_enabled = false
    authStore.tenantFeatures = { isp_module_enabled: false };

    const wrapperAdmin = mount(SubscribersMapView, {
      global: {
        stubs: { RouterLink: true },
      },
    });
    await vi.waitFor(() => {
      expect(wrapperAdmin.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });

    // 1. Ambos botones de importación masiva CSV deben ser visibles para administradores
    expect(wrapperAdmin.find('#btn-import-subscribers-csv').exists()).toBe(true);
    expect(wrapperAdmin.find('#btn-import-optical-boxes-csv').exists()).toBe(true);

    // 2. Botón de sincronización DHCP debe existir con ID y NO contener doble ícono "🔄 🔄"
    const syncBtn = wrapperAdmin.find('#btn-sync-dhcp-clients');
    expect(syncBtn.exists()).toBe(true);
    const syncText = syncBtn.text();
    expect(syncText).not.toContain('🔄 🔄');
    expect(syncText).toContain('Sincronizar Dispositivos DHCP');

    // 3. Para roles sin privilegios masivos (ej. NOC_MONITOR), ambos botones permanecen ocultos
    authStore.currentRole = 'NOC_MONITOR';
    const wrapperNoc = mount(SubscribersMapView, {
      global: {
        stubs: { RouterLink: true },
      },
    });
    await vi.waitFor(() => {
      expect(wrapperNoc.find(MOCK_MAP_SELECTOR).exists()).toBe(true);
    });
    expect(wrapperNoc.find('#btn-import-subscribers-csv').exists()).toBe(false);
    expect(wrapperNoc.find('#btn-import-optical-boxes-csv').exists()).toBe(false);
  });
});
