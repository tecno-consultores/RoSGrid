// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import UnifiedNetworkMap from './UnifiedNetworkMap.vue';
import type { RouterItem, OpticalBoxItem, SubscriberDeviceItem } from '@/types';
import { useAuthStore } from '@/stores/useAuthStore';
import L from 'leaflet';

const mockRouters: RouterItem[] = [
  {
    id: 'r-core-1',
    tenant_id: 't-1',
    display_name: 'CCR2004-Core-NOC',
    ros_identity: 'CCR-Core',
    ip_address: '10.0.0.1',
    api_port: 8728,
    ros_version: '7.18',
    admin_state: 'PRODUCTION',
    is_reachable: true,
    latitude: 10.4806,
    longitude: -66.9036,
    network_role: 'CORE_BGP',
  },
  {
    id: 'r-pop-2',
    tenant_id: 't-1',
    display_name: 'RB4011-Pop-Sur',
    ros_identity: 'RB4011-Sur',
    ip_address: '10.0.0.2',
    api_port: 8728,
    ros_version: '7.18',
    admin_state: 'PRODUCTION',
    is_reachable: false, // Router Caído
    latitude: 10.4700,
    longitude: -66.9100,
    network_role: 'DISTRIBUTION',
  },
];

const mockBoxes: OpticalBoxItem[] = [
  {
    id: 'box-1',
    tenant_id: 't-1',
    router_id: 'r-pop-2',
    box_code: 'NAP-SUR-01',
    capacity_ports: 16,
    occupied_ports_count: 8,
    available_ports_count: 8,
    splitter_ratio: '1:16',
    installation_type: 'POSTE',
    latitude: 10.4710,
    longitude: -66.9110,
    status: 'ACTIVE',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

const mockSubscribers: SubscriberDeviceItem[] = [
  {
    id: 'sub-1',
    tenant_id: 't-1',
    router_id: 'r-pop-2', // Depende del router caído
    service_type: 'FTTH_PPPOE',
    auth_backend: 'ROUTEROS_LOCAL',
    onu_mode: 'BRIDGE',
    optical_box_id: 'box-1',
    endpoint_identifier: 'CLI-1001-FTTH',
    assigned_ipv4: '100.64.0.15',
    last_reachability_status: 'OFFLINE',
    latitude: 10.4715,
    longitude: -66.9115,
    status: 'ACTIVE',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'sub-2',
    tenant_id: 't-1',
    router_id: 'r-core-1', // Depende del router activo
    service_type: 'CORP_DHCP',
    auth_backend: 'ROUTEROS_LOCAL',
    onu_mode: 'ROUTER',
    endpoint_identifier: 'CLI-1002-CORP',
    assigned_ipv4: '10.0.0.50',
    last_reachability_status: 'ONLINE',
    ping_latency_ms: 4.2,
    packet_loss_pct: 0,
    latitude: 10.4810,
    longitude: -66.9040,
    status: 'ACTIVE',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

describe('UnifiedNetworkMap.vue — Mapa de Red Unificado & Gobierno RCA (Hito 23.25)', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    vi.restoreAllMocks();
    pinia = createPinia();
    setActivePinia(pinia);

    // Mock seguro de headless y Leaflet
    Object.defineProperty(navigator, 'webdriver', {
      value: false,
      configurable: true,
    });

    vi.spyOn(L, 'map').mockReturnValue({
      setView: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
    } as unknown as L.Map);

    vi.spyOn(L, 'layerGroup').mockReturnValue({
      addTo: vi.fn().mockReturnThis(),
      clearLayers: vi.fn(),
      addLayer: vi.fn(),
    } as unknown as L.LayerGroup);

    vi.spyOn(L, 'tileLayer').mockReturnValue({
      addTo: vi.fn().mockReturnThis(),
    } as unknown as L.TileLayer);

    vi.spyOn(L.control, 'zoom').mockReturnValue({
      addTo: vi.fn(),
    } as unknown as L.Control.Zoom);
  });

  it('renderiza la barra táctica con los 3 botones de capa cuando isp_module_enabled está activo', () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    expect(wrapper.find('.unified-map-toolbar').exists()).toBe(true);
    expect(wrapper.find('.btn-layer-routers').exists()).toBe(true);
    expect(wrapper.find('.btn-layer-boxes').exists()).toBe(true);
    expect(wrapper.find('.btn-layer-subs').exists()).toBe(true);
    expect(wrapper.text()).toContain('Abonados FTTH');
  });

  it('oculta estrictamente el toggle de Cajas NAP si isp_module_enabled es falso (Empresas Privadas / No-ISPs)', () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: false };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    expect(wrapper.find('.btn-layer-routers').exists()).toBe(true);
    expect(wrapper.find('.btn-layer-boxes').exists()).toBe(false);
    expect(wrapper.find('.btn-layer-subs').exists()).toBe(true);
    expect(wrapper.text()).toContain('Dispositivos DHCP');
  });

  it('permite alternar el estado activo de las capas al hacer click en los botones', async () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'subscribers',
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    const btnRouters = wrapper.find('.btn-layer-routers');
    expect(btnRouters.attributes('aria-pressed')).toBe('false');

    await btnRouters.trigger('click');
    expect(btnRouters.attributes('aria-pressed')).toBe('true');
    expect(btnRouters.classes()).toContain('btn-layer-toggle--active');
  });

  it('despliega la franja de alerta táctica de Causa Raíz (RCA) si un router de cabecera está caído', async () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    const rcaAlert = wrapper.find('.rca-header-alert-strip');
    expect(rcaAlert.exists()).toBe(true);
    expect(rcaAlert.text()).toContain('ALERTA DE CABECERA');
    expect(rcaAlert.text()).toContain('RB4011-Pop-Sur');
    expect(rcaAlert.text()).toContain('1 abonados dependientes afectados');

    const focusBtn = wrapper.find('.btn-rca-focus');
    expect(focusBtn.exists()).toBe(true);
    await focusBtn.trigger('click');
  });

  it('aplica gobernanza RBAC para WebFig: bloquea acceso para técnicos de calle (FIELD_TECH)', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'FIELD_TECH';
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    // Simular selección de router en el componente
    (wrapper.vm as unknown as { activeRouter: RouterItem }).activeRouter = mockRouters[0];
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.router-detail-card').exists()).toBe(true);
    expect(wrapper.find('.rbac-restricted-box').exists()).toBe(true);
    expect(wrapper.find('.btn-open-webfig').exists()).toBe(false);
    expect(wrapper.text()).toContain('Acceso a configuración WebFig restringido para ingenieros de NOC');
  });

  it('permite acceso a consola WebFig para administradores e ingenieros de NOC', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });

    // Simular selección de router
    (wrapper.vm as unknown as { activeRouter: RouterItem }).activeRouter = mockRouters[0];
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.router-detail-card').exists()).toBe(true);
    expect(wrapper.find('.btn-open-webfig').exists()).toBe(true);
    expect(wrapper.find('.rbac-restricted-box').exists()).toBe(false);
  });
});
