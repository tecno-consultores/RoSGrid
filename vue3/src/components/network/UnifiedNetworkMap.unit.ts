// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import UnifiedNetworkMap from './UnifiedNetworkMap.vue';
import type { RouterItem, OpticalBoxItem, SubscriberDeviceItem } from '@/types';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';
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
      fitBounds: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
      on: vi.fn(),
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

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url === '/api/v1/topology/l2') {
        return {
          status: 200,
          headers: new Headers(),
          data: {
            nodes: [],
            edges: [
              {
                id: 'edge-1',
                source_router_id: 'r-core-1',
                source_interface: 'ether1',
                target_router_id: 'r-pop-2',
                target_interface: 'ether1',
                link_speed: '1Gbps',
                is_poe_delivering: true,
                poe_power_watts: 18.5,
                protocol: 'LLDP',
              },
            ],
            total_nodes: 2,
            total_edges: 1,
            timestamp: '2026-01-01T00:00:00Z',
          },
        };
      }
      return { status: 200, headers: new Headers(), data: {} };
    });
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
    expect(wrapper.text()).toContain('Clientes');
  });

  it('oculta toggle de Cajas NAP si isp_module_enabled es falso sin cajas cargadas y en modo no-subscribers (Spec 106)', () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: false };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'inventory',
        routers: mockRouters,
        opticalBoxes: [],
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
    expect(wrapper.text()).toContain('Clientes');
  });

  it('habilita canShowBoxesLayer en Cajas NAP si existen cajas cargadas o en modo subscribers aun con isp_module_enabled falso (Hito 30.29 / Spec 106)', () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = { isp_module_enabled: false };

    // Caso A: con cajas cargadas en modo inventario
    const wrapperWithBoxes = mount(UnifiedNetworkMap, {
      props: {
        mode: 'inventory',
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
    expect(wrapperWithBoxes.find('.btn-layer-boxes').exists()).toBe(true);

    // Caso B: en modo subscribers
    const wrapperSubscribers = mount(UnifiedNetworkMap, {
      props: {
        mode: 'subscribers',
        routers: mockRouters,
        opticalBoxes: [],
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: {
          RouterLink: true,
        },
      },
    });
    expect(wrapperSubscribers.find('.btn-layer-boxes').exists()).toBe(true);
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

  it('cuando allowWebfig es false (modo técnico de campo), NUNCA muestra el botón de WebFig incluso para SUPERADMIN_GLOBAL', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    authStore.tenantFeatures = { isp_module_enabled: true };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        allowWebfig: false,
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
    // El botón de WebFig NUNCA debe existir en el DOM
    expect(wrapper.find('.btn-open-webfig').exists()).toBe(false);
    expect(wrapper.find('.field-view-indicator').exists()).toBe(true);
    expect(wrapper.text()).toContain('Modo Operaciones de Campo: WebFig estrictamente deshabilitado');
    // Muestra el semáforo de salud del router
    expect(wrapper.find('.router-health-pill').exists()).toBe(true);
    expect(wrapper.text()).toContain('ONLINE / OPERATIVO');
  });

  it('agrupa correctamente múltiples routers co-ubicados (ej. 5 equipos en Guacara) y despliega tarjeta de sitio compartido', async () => {
    const guacaraRouters: RouterItem[] = [
      { id: 'r2', tenant_id: 't-1', display_name: 'r2', ip_address: '10.2.0.2', latitude: 10.230979, longitude: -67.880417, admin_state: 'PRODUCTION', is_reachable: true, serial_number: 'SN-R2' } as RouterItem,
      { id: 'r3', tenant_id: 't-1', display_name: 'r3', ip_address: '10.2.0.3', latitude: 10.230970, longitude: -67.880410, admin_state: 'PRODUCTION', is_reachable: true, serial_number: 'SN-R3' } as RouterItem,
      { id: 'r4', tenant_id: 't-1', display_name: 'r4', ip_address: '10.2.0.4', latitude: 10.230970, longitude: -67.880410, admin_state: 'PRODUCTION', is_reachable: true, serial_number: 'SN-R4' } as RouterItem,
      { id: 'r5', tenant_id: 't-1', display_name: 'r5', ip_address: '10.2.0.5', latitude: 10.230970, longitude: -67.880410, admin_state: 'PRODUCTION', is_reachable: true, serial_number: 'SN-R5' } as RouterItem,
      { id: 'r6', tenant_id: 't-1', display_name: 'r6', ip_address: '10.2.0.6', latitude: 10.230970, longitude: -67.880410, admin_state: 'PRODUCTION', is_reachable: true, serial_number: 'SN-R6' } as RouterItem,
    ];

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        routers: guacaraRouters,
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    const vm = wrapper.vm as unknown as {
      buildLocationGroups: (r: RouterItem[]) => Array<{ lat: number; lng: number; routers: RouterItem[] }>;
      activeLocationGroup: { lat: number; lng: number; routers: RouterItem[] } | null;
    };

    const groups = vm.buildLocationGroups(guacaraRouters);
    expect(groups.length).toBe(1);
    expect(groups[0].routers.length).toBe(5);

    // Simular activación del grupo al hacer click en el pin múltiple
    vm.activeLocationGroup = groups[0];
    await wrapper.vm.$nextTick();

    const groupCard = wrapper.find('.location-group-card');
    expect(groupCard.exists()).toBe(true);
    expect(groupCard.text()).toContain('Sitio Compartido (5 Equipos)');
    expect(groupCard.text()).toContain('r2');
    expect(groupCard.text()).toContain('r3');
    expect(groupCard.text()).toContain('r4');
    expect(groupCard.text()).toContain('r5');
    expect(groupCard.text()).toContain('r6');

    // Seleccionar el router r4 desde el panel
    const selectBtns = groupCard.findAll('.btn-select-group-router');
    expect(selectBtns.length).toBe(5);
    await selectBtns[2].trigger('click'); // r4

    expect(wrapper.emitted('select-router')).toBeTruthy();
    expect(wrapper.emitted('select-router')?.[0]).toEqual(['r4']);
    expect(vm.activeLocationGroup).toBeNull();
  });

  it('renderiza la leyenda de simbología geométrica (● Routers, ■ Cajas NAP, ▲ Clientes) en los botones de capa (Hito 28.19)', () => {
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
        stubs: { RouterLink: true },
      },
    });

    const routerBtn = wrapper.find('.btn-layer-routers');
    expect(routerBtn.find('.shape-legend--circle').text()).toBe('●');

    const boxBtn = wrapper.find('.btn-layer-boxes');
    expect(boxBtn.find('.shape-legend--square').text()).toBe('■');

    const subBtn = wrapper.find('.btn-layer-subs');
    expect(subBtn.find('.shape-legend--triangle').text()).toBe('▲');
  });

  it('resuelve coordenadas de respaldo desde la Caja NAP o Router para abonados sin GPS (Hito 28.19)', () => {
    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: mockRouters,
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    const vm = wrapper.vm as unknown as {
      resolveSubscriberBaseCoords: (s: SubscriberDeviceItem) => [number, number] | null;
      getSubscriberColor: (s: SubscriberDeviceItem) => string;
    };

    // Caso 1: Abonado con coordenadas explícitas
    const coords1 = vm.resolveSubscriberBaseCoords(mockSubscribers[0]);
    expect(coords1).toEqual([10.4715, -66.9115]);

    // Caso 2: Abonado sin coordenadas, hereda de su optical_box_id
    const subWithoutGps: SubscriberDeviceItem = {
      ...mockSubscribers[0],
      latitude: undefined,
      longitude: undefined,
      optical_box_id: 'box-1',
    };
    const coords2 = vm.resolveSubscriberBaseCoords(subWithoutGps);
    expect(coords2).toEqual([10.471, -66.911]); // Coordenadas de mockBoxes[0]

    // Caso 3: Abonado sin coordenadas ni caja, hereda de su router_id
    const subWithRouterOnly: SubscriberDeviceItem = {
      ...mockSubscribers[0],
      latitude: undefined,
      longitude: undefined,
      optical_box_id: undefined,
      optical_box: undefined,
      router_id: 'r-core-1',
    };
    const coords3 = vm.resolveSubscriberBaseCoords(subWithRouterOnly);
    expect(coords3).toEqual([10.4806, -66.9036]); // Coordenadas de mockRouters[0]

    // Colores según estado operativo:
    expect(vm.getSubscriberColor(mockSubscribers[0])).toBe('#EF4444'); // OFFLINE -> Rojo
    expect(vm.getSubscriberColor(mockSubscribers[1])).toBe('#10B981'); // ONLINE -> Verde Esmeralda
    const degradedSub: SubscriberDeviceItem = { ...mockSubscribers[1], ping_latency_ms: 55 };
    expect(vm.getSubscriberColor(degradedSub)).toBe('#F59E0B'); // Latencia >= 40ms -> Naranja
  });

  it('excluye equipos con admin_state === MAINTENANCE de la alerta RCA e incluye opción MAINTENANCE en filtro', async () => {
    const maintenanceRouter: RouterItem = {
      id: 'r-maint-3',
      tenant_id: 't-1',
      display_name: 'CCR2004-Mantenimiento',
      ros_identity: 'CCR-Maint',
      ip_address: '10.0.0.3',
      api_port: 8728,
      ros_version: '7.18',
      admin_state: 'MAINTENANCE',
      is_reachable: false, // Inalcanzable temporalmente debido al trabajo
      latitude: 10.4900,
      longitude: -66.9200,
      network_role: 'EDGE',
    };

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: [mockRouters[0], maintenanceRouter], // mockRouters[0] is reachable, maintenanceRouter is in MAINTENANCE
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    // La alerta RCA no debe activarse porque el router inalcanzable está bajo mantenimiento programado
    expect(wrapper.find('.rca-alert-banner').exists()).toBe(false);

    // Debe contener la opción MAINTENANCE en el selector
    const options = wrapper.findAll('.rg-select-filter option');
    const values = options.map((o) => o.attributes('value'));
    expect(values).toContain('MAINTENANCE');
  });

  it('renderiza el cuarto botón de capa #btn-layer-l2-links y conmuta polilíneas L2 (Spec 101 / Hito 30.24)', async () => {
    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'inventory',
        routers: mockRouters,
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    const l2Btn = wrapper.find('#btn-layer-l2-links');
    expect(l2Btn.exists()).toBe(true);
    expect(l2Btn.text()).toContain('Enlaces L2');

    // Por defecto en mode 'inventory' showL2Links es false
    expect(l2Btn.classes()).not.toContain('btn-layer-toggle--active');

    // Al hacer clic conmuta a true y consulta /api/v1/topology/l2
    await l2Btn.trigger('click');
    expect(l2Btn.classes()).toContain('btn-layer-toggle--active');
    expect(http.get).toHaveBeenCalledWith('/api/v1/topology/l2');

    // Comprobar contador actualizado tras carga
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('(1)');
  });

  it('activa la capa de enlaces L2 por defecto en mode="wallboard"', async () => {
    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        routers: mockRouters,
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    const l2Btn = wrapper.find('#btn-layer-l2-links');
    expect(l2Btn.exists()).toBe(true);
    expect(l2Btn.classes()).toContain('btn-layer-toggle--active');
    expect(http.get).toHaveBeenCalledWith('/api/v1/topology/l2');
  });

  it('despliega la tarjeta de detalle l2-edge-detail-card al seleccionar un enlace L2', async () => {
    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        routers: mockRouters,
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    const vm = wrapper.vm as unknown as { activeL2Edge: unknown };
    vm.activeL2Edge = {
      id: 'edge-1',
      source_router_id: 'r-core-1',
      source_interface: 'ether1',
      target_router_id: 'r-pop-2',
      target_interface: 'ether1',
      link_speed: '1Gbps',
      is_poe_delivering: true,
      poe_power_watts: 18.5,
      protocol: 'LLDP',
    };

    await wrapper.vm.$nextTick();

    const edgeCard = wrapper.find('.l2-edge-detail-card');
    expect(edgeCard.exists()).toBe(true);
    expect(edgeCard.text()).toContain('Enlace Físico Capa 2 (LLDP)');
    expect(edgeCard.text()).toContain('ether1');
    expect(edgeCard.text()).toContain('18.5W');

    // Botón de cierre
    const btnClose = edgeCard.find('.btn-close-card');
    expect(btnClose.exists()).toBe(true);
    await btnClose.trigger('click');
    expect(vm.activeL2Edge).toBeNull();
  });

  it('ejecuta fitMapToActiveNodes automáticamente al cargar nodos y al pulsar #btn-map-fit-bounds', async () => {
    const mockMapInstance = {
      setView: vi.fn().mockReturnThis(),
      fitBounds: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
      on: vi.fn(),
    };
    vi.spyOn(L, 'map').mockReturnValue(mockMapInstance as unknown as L.Map);

    const caraboboRouters: RouterItem[] = [
      {
        id: 'r-val-1',
        tenant_id: 't-1',
        display_name: 'CCR2004-Valencia',
        ros_identity: 'CCR-Val',
        ip_address: '10.230.0.1',
        api_port: 8728,
        ros_version: '7.18',
        admin_state: 'PRODUCTION',
        is_reachable: true,
        latitude: 10.2323,
        longitude: -67.8798,
        network_role: 'CORE_BGP',
      },
      {
        id: 'r-val-2',
        tenant_id: 't-1',
        display_name: 'RB4011-Naguanagua',
        ros_identity: 'RB4011-Nag',
        ip_address: '10.230.0.2',
        api_port: 8728,
        ros_version: '7.18',
        admin_state: 'PRODUCTION',
        is_reachable: true,
        latitude: 10.2450,
        longitude: -67.8900,
        network_role: 'DISTRIBUTION',
      },
    ];

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        routers: caraboboRouters,
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    await wrapper.vm.$nextTick();

    // Debe haber llamado a fitBounds al montar y detectar múltiples routers
    expect(mockMapInstance.fitBounds).toHaveBeenCalled();

    // El botón #btn-map-fit-bounds debe existir en el DOM
    const btnFit = wrapper.find('#btn-map-fit-bounds');
    expect(btnFit.exists()).toBe(true);
    expect(btnFit.text()).toContain('Centrar Red');

    // Al hacer clic en el botón, fuerza re-centrado
    mockMapInstance.fitBounds.mockClear();
    await btnFit.trigger('click');
    expect(mockMapInstance.fitBounds).toHaveBeenCalled();
  });

  it('ejecuta setView cuando solo existe 1 nodo con coordenadas válidas', async () => {
    const mockMapInstance = {
      setView: vi.fn().mockReturnThis(),
      fitBounds: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
      on: vi.fn(),
    };
    vi.spyOn(L, 'map').mockReturnValue(mockMapInstance as unknown as L.Map);

    const singleRouter: RouterItem[] = [
      {
        id: 'r-val-single',
        tenant_id: 't-1',
        display_name: 'CCR2004-Valencia-Single',
        ros_identity: 'CCR-Val-1',
        ip_address: '10.230.0.1',
        api_port: 8728,
        ros_version: '7.18',
        admin_state: 'PRODUCTION',
        is_reachable: true,
        latitude: 10.2323,
        longitude: -67.8798,
        network_role: 'CORE_BGP',
      },
    ];

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'wallboard',
        routers: singleRouter,
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    await wrapper.vm.$nextTick();
    expect(mockMapInstance.setView).toHaveBeenCalledWith(
      [10.2323, -67.8798],
      expect.any(Number),
    );
  });

  it('encuadra sobre abonados y cajas NAP en modo subscribers', async () => {
    const mockMapInstance = {
      setView: vi.fn().mockReturnThis(),
      fitBounds: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
      on: vi.fn(),
    };
    vi.spyOn(L, 'map').mockReturnValue(mockMapInstance as unknown as L.Map);

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        mode: 'subscribers',
        routers: [],
        opticalBoxes: mockBoxes,
        subscribers: mockSubscribers,
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    await wrapper.vm.$nextTick();
    expect(mockMapInstance.fitBounds).toHaveBeenCalled();
  });

  it('centra el mapa en authStore.tenantHqCoordinates cuando la empresa no tiene nodos geolocalizados y re-centra reactivamente (Spec 105)', async () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = {
      hq_latitude: 10.25,
      hq_longitude: -67.6,
    };

    const mockMapInstance = {
      setView: vi.fn().mockReturnThis(),
      fitBounds: vi.fn().mockReturnThis(),
      invalidateSize: vi.fn(),
      flyTo: vi.fn(),
      remove: vi.fn(),
      on: vi.fn(),
    };
    vi.spyOn(L, 'map').mockReturnValue(mockMapInstance as unknown as L.Map);

    const wrapper = mount(UnifiedNetworkMap, {
      props: {
        routers: [],
        opticalBoxes: [],
        subscribers: [],
      },
      global: {
        plugins: [pinia],
        stubs: { RouterLink: true },
      },
    });

    await wrapper.vm.$nextTick();

    (wrapper.vm as any).fitMapToActiveNodes(true);
    expect(mockMapInstance.setView).toHaveBeenCalledWith(
      [10.25, -67.6],
      expect.any(Number),
    );

    authStore.tenantFeatures = {
      hq_latitude: 10.4806,
      hq_longitude: -66.9036,
    };
    await wrapper.vm.$nextTick();

    expect(mockMapInstance.setView).toHaveBeenCalledWith(
      [10.4806, -66.9036],
      expect.any(Number),
    );
  });
});

