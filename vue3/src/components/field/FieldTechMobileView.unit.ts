// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import FieldTechMobileView from './FieldTechMobileView.vue';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useAuthStore } from '@/stores/useAuthStore';

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('FieldTechMobileView.vue — Panel Responsive del Técnico de Campo FTTH', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();

    // Mock Canvas getContext
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      clearRect: vi.fn(),
    });
    HTMLCanvasElement.prototype.toDataURL = vi.fn().mockReturnValue('data:image/png;base64,mock');
  });

  it('bloquea el panel con aviso táctico si la organización tiene isp_module_enabled desactivado', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: false });

    const wrapper = mount(FieldTechMobileView);
    expect(wrapper.find('.non-isp-blocker').exists()).toBe(true);
    expect(wrapper.text()).toContain('Módulo FTTH/ISP Desactivado');
  });

  it('renderiza encabezado táctico y las 3 pestañas operativas en Modo ISP', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(FieldTechMobileView);
    expect(wrapper.find('.field-header').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-nap').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-customer').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-diagnostics').exists()).toBe(true);
  });

  it('permite registrar una nueva Caja NAP', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const invStore = useInventoryStore();
    invStore.routers = [
      {
        id: 'r-01',
        display_name: 'CCR2004-Core',
        ip_address: '10.0.0.1',
        admin_state: 'PRODUCTION',
        network_role: 'CORE_ROUTER',
      } as any,
    ];

    const fieldStore = useFieldOpsStore();
    const createBoxSpy = vi.spyOn(fieldStore, 'createOpticalBox').mockResolvedValue({
      id: 'box-100',
      tenant_id: 't-1',
      router_id: 'r-01',
      box_code: 'NAP-AV01-P12',
      capacity_ports: 16,
      splitter_ratio: '1:16',
      installation_type: 'POSTE',
      latitude: 10.4806,
      longitude: -66.9036,
      status: 'ACTIVE',
      occupied_ports_count: 0,
      available_ports_count: 16,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const wrapper = mount(FieldTechMobileView);
    await wrapper.find('#nap-router-select').setValue('r-01');
    await wrapper.find('#nap-code-input').setValue('NAP-AV01-P12');
    await wrapper.find('form').trigger('submit');

    expect(createBoxSpy).toHaveBeenCalled();
  });

  it('normaliza seriales GPON en el formulario de alta de cliente', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(FieldTechMobileView);
    await wrapper.find('#tab-btn-customer').trigger('click');

    const serialInput = wrapper.find('#cust-onu-serial');
    await serialInput.setValue('4857544312345678'); // 'HWTC' en ASCII HEX
    const btnNormalize = wrapper.find('.input-with-btn button');
    await btnNormalize.trigger('click');

    expect((serialInput.element as HTMLInputElement).value).toBe('HWTC12345678');
  });

  it('ejecuta captura de coordenadas GPS con feedback reactivo', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const mockGeolocation = {
      getCurrentPosition: vi.fn((success) => {
        success({
          coords: {
            latitude: 10.4806,
            longitude: -66.9036,
          },
        });
      }),
    };
    Object.defineProperty(navigator, 'geolocation', {
      value: mockGeolocation,
      configurable: true,
    });

    const wrapper = mount(FieldTechMobileView);
    const btnGps = wrapper.find('#btn-global-gps');
    await btnGps.trigger('click');

    expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    expect(wrapper.text()).toContain('10.4806');
    expect(wrapper.text()).toContain('-66.9036');
  });

  it('ejecuta test ping 1-click desde MikroTik en la pestaña de diagnósticos', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const fieldStore = useFieldOpsStore();
    fieldStore.recentInstallations = [
      {
        id: 'dev-1',
        router_id: 'r-1',
        endpoint_identifier: 'CLI-001',
        customer_code: 'CLI-001',
        device_serial: 'HWTC11223344',
        last_reachability_status: 'UNKNOWN',
      } as any,
    ];

    const pingSpy = vi.spyOn(fieldStore, 'pingSubscriberLive').mockResolvedValue({
      device_id: 'dev-1',
      last_reachability_status: 'ONLINE',
      ping_latency_ms: 18,
      packet_loss_pct: 0,
      message: 'Ping MikroTik completado: 18ms',
    });

    const wrapper = mount(FieldTechMobileView);
    await wrapper.find('#tab-btn-diagnostics').trigger('click');

    await wrapper.find('#diag-target-select').setValue('dev-1');
    const btnPing = wrapper.find('.diag-action-bar button');
    await btnPing.trigger('click');

    expect(pingSpy).toHaveBeenCalledWith('dev-1', false, false);
  });

  it('permite dibujar y limpiar la firma en el canvas táctil', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(FieldTechMobileView);
    await wrapper.find('#tab-btn-diagnostics').trigger('click');

    const canvas = wrapper.find('.signature-pad');
    await canvas.trigger('mousedown', { clientX: 20, clientY: 20 });
    await canvas.trigger('mousemove', { clientX: 60, clientY: 60 });
    await canvas.trigger('mouseup');

    const btnClear = wrapper.find('.sig-header button');
    await btnClear.trigger('click');
    expect(btnClear.exists()).toBe(true);
  });

  it('permite alternar a la pestaña de mapa de zona y renderiza la sección cartográfica', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(FieldTechMobileView, {
      global: {
        stubs: {
          UnifiedNetworkMap: true,
        },
      },
    });

    const tabMap = wrapper.find('#tab-btn-map');
    expect(tabMap.exists()).toBe(true);
    await tabMap.trigger('click');

    expect(wrapper.find('.tab-pane-map').exists()).toBe(true);
    expect(wrapper.text()).toContain('Mapa de Zona & Topología FTTH');
  });

  it('muestra banner de advertencia cuando otro técnico atendió el servicio y permite forzar prueba', async () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const fieldStore = useFieldOpsStore();
    fieldStore.recentInstallations = [
      {
        id: 'dev-1',
        tenant_id: 't-1',
        router_id: 'r-1',
        service_type: 'FTTH_PPPOE',
        auth_backend: 'ROUTEROS_LOCAL',
        endpoint_identifier: 'CLI-001',
        onu_mode: 'BRIDGE',
        status: 'ACTIVE',
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
    ];
    const pingSpy = vi.spyOn(fieldStore, 'pingSubscriberLive').mockResolvedValueOnce({
      device_id: 'dev-1',
      assigned_ipv4: '100.64.0.15',
      last_reachability_status: 'ONLINE',
      ping_latency_ms: 15,
      packet_loss_pct: 0,
      message: 'Ping previo en caché',
      is_cached: true,
      cache_ttl_remaining: 10,
      operational_lock: {
        technician_id: 'tech-99',
        technician_name: 'Carlos Mendoza',
        action: 'DIAGNOSTICO_ACTIVO',
        locked_at: '2026-10-24T16:00:00Z',
        minutes_ago: 3,
        is_locked_by_other: true,
      },
    }).mockResolvedValueOnce({
      device_id: 'dev-1',
      assigned_ipv4: '100.64.0.15',
      last_reachability_status: 'ONLINE',
      ping_latency_ms: 12,
      packet_loss_pct: 0,
      message: 'Diagnóstico 360 forzado',
      is_cached: false,
      cache_ttl_remaining: 15,
      gateway_ping: { status: 'PASS', latency_ms: 0.8, target: '10.0.0.1' },
      internet_ping: { status: 'PASS', latency_ms: 14.5, target: '1.1.1.1' },
      dns_check: { status: 'PASS', domain: 'google.com', resolved_ip: '142.250.190.46' },
      mtu_test: { status: 'PASS', size_bytes: 1500 },
    });

    const wrapper = mount(FieldTechMobileView);
    await wrapper.find('#tab-btn-diagnostics').trigger('click');
    await wrapper.find('#diag-target-select').setValue('dev-1');

    const btnPing = wrapper.find('.diag-btns-group button');
    await btnPing.trigger('click');
    await flushPromises();

    expect(wrapper.find('.lock-override-banner').exists()).toBe(true);
    expect(wrapper.text()).toContain('Carlos Mendoza');

    const btnForce = wrapper.find('.lock-override-banner button');
    expect(btnForce.exists()).toBe(true);
    await btnForce.trigger('click');
    await flushPromises();

    expect(pingSpy).toHaveBeenLastCalledWith('dev-1', true, true);
  });
});
