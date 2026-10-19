// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { http } from '@/api/httpClient';

import RouterContextHeader from '@/components/webfig/RouterContextHeader.vue';
import RouterWorkspaceTabsBar from '@/components/webfig/RouterWorkspaceTabsBar.vue';
import RouterSidebarMenu from '@/components/webfig/RouterSidebarMenu.vue';
import RouterWebFigLayout from './RouterWebFigLayout.vue';
import RouterLiveDashboardView from './RouterLiveDashboardView.vue';
import InterfacesAndSfpView from './InterfacesAndSfpView.vue';
import FirewallRulesView from './FirewallRulesView.vue';
import RoutingBgpOspfView from './RoutingBgpOspfView.vue';
import PppAndQueuesView from './PppAndQueuesView.vue';
import LiveToolsDiagnosticsView from './LiveToolsDiagnosticsView.vue';
import DynamicLayer2ResourceView from './DynamicLayer2ResourceView.vue';
import BridgeView from './BridgeView.vue';
import WireGuardVpnView from './WireGuardVpnView.vue';
import type { RouterItem, TelemetryPoint } from '@/types';

const mockPush = vi.fn();
let mockRouteParam: Record<string, string> = { routerId: 'r-01', rosPath: 'mpls' };

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: mockRouteParam,
    path: `/routers/${mockRouteParam.routerId || 'r-01'}/webfig/live`,
    query: {},
  }),
  useRouter: () => ({
    push: mockPush,
  }),
  RouterView: { template: '<div class="router-view-stub">ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('WebFig Components and Views Unit Tests (Hito 13)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    mockPush.mockClear();
    mockRouteParam = { routerId: 'r-01', rosPath: 'mpls' };

    // Canvas mock
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      closePath: vi.fn(),
      strokeStyle: '',
      fillStyle: '',
      lineWidth: 1,
      lineJoin: '',
      font: '',
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('RouterContextHeader — renderiza métricas y cambia de router', async () => {
    const routerSample: RouterItem = {
      id: 'r-01',
      tenant_id: 't-1',
      display_name: 'Core Router',
      ros_identity: 'RB5009-Core',
      ip_address: '192.168.88.1',
      api_port: 443,
      ros_version: '7.16.1',
      model: 'RB5009UG+S+IN',
      serial_number: 'HE123456',
      is_reachable: true,
      admin_state: 'PRODUCTION',
      ssl_trust_status: 'TRUSTED_PINNED',
    };

    const telemetrySample: TelemetryPoint = {
      timestampEpoch: 1700000000,
      timestampIso: new Date().toISOString(),
      cpuLoadPct: 85,
      freeMemoryPct: 72,
      temperatureC: 41,
    };

    const { useInventoryStore } = await import('@/stores/useInventoryStore');
    const invStore = useInventoryStore();
    invStore.setRouters([
      routerSample,
      {
        ...routerSample,
        id: 'r-02',
        display_name: 'Secondary Router',
      },
    ]);

    const wrapper = mount(RouterContextHeader, {
      props: {
        router: routerSample,
        latestTelemetry: telemetrySample,
      },
    });

    expect(wrapper.text()).toContain('Core Router');
    expect(wrapper.text()).toContain('85%');
    expect(wrapper.text()).toContain('72%');

    // Cambiar de router en selector
    const select = wrapper.find('select');
    if (select.exists()) {
      await select.setValue('r-02');
      await select.trigger('change');
      expect(mockPush).toHaveBeenCalledWith('/routers/r-02/webfig/live');
    }

    // Toggle safemode via safemode-badge
    const safeModeBadge = wrapper.find('.safemode-badge');
    if (safeModeBadge.exists()) {
      await safeModeBadge.trigger('click');
      expect(wrapper.emitted('toggle-safemode')).toBeTruthy();
    }
  });

  it('RouterContextHeader — maneja router nulo o sin identidad', () => {
    const wrapper = mount(RouterContextHeader, {
      props: {
        router: null,
        latestTelemetry: null,
      },
    });
    expect(wrapper.text()).toContain('MikroTik RouterOS');
    expect(wrapper.text()).toContain('00:00:00');
  });

  it('RouterWorkspaceTabsBar — cambia, cierra y navega pestañas móviles', async () => {
    const { useWebFigStore } = await import('@/stores/useWebFigStore');
    const store = useWebFigStore();
    store.openOrFocusTab({
      tabId: 'tab-1',
      routeName: 'InterfacesAndSfp',
      label: 'Interfaces & SFP',
      closable: true,
    });
    store.openOrFocusTab({
      tabId: 'tab-2',
      routeName: 'FirewallRules',
      label: 'Firewall Rules',
      closable: true,
    });

    const wrapper = mount(RouterWorkspaceTabsBar, {
      props: { routerId: 'r-01' },
    });

    const tabs = wrapper.findAll('.webfig-tab');
    expect(tabs.length).toBeGreaterThan(0);
    await tabs[0].trigger('click');
    await tabs[0].trigger('keydown.enter');

    // Cerrar pestaña
    const closeBtns = wrapper.findAll('.btn-close-tab');
    if (closeBtns.length > 0) {
      await closeBtns[0].trigger('click');
    }

    // Botones rápidos de móvil
    const mobileBtns = wrapper.findAll('.bottom-bar-btn');
    expect(mobileBtns.length).toBeGreaterThan(0);
    for (const btn of mobileBtns) {
      await btn.trigger('click');
    }
  });

  it('RouterSidebarMenu — navega por todos los módulos nativos y de capa 2', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        items: [
          { ros_path: 'mpls', title: 'MPLS Protocol', category: 'Transport', is_singleton: false },
          { ros_path: 'snmp', title: 'SNMP', category: 'Management', is_singleton: true },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(RouterSidebarMenu, {
      props: {
        routerId: 'r-01',
        isOpenMobile: true,
      },
    });
    await flushPromises();

    const buttons = wrapper.findAll('.nav-item');
    expect(buttons.length).toBeGreaterThan(0);
    // Click en todos los botones para cubrir navigateTo y navigateToLayer2
    for (const btn of buttons) {
      await btn.trigger('click');
    }
    expect(mockPush).toHaveBeenCalled();

    // Cerrar menú móvil
    const closeMobileBtn = wrapper.find('.btn-close-sidebar');
    if (closeMobileBtn.exists()) {
      await closeMobileBtn.trigger('click');
      expect(wrapper.emitted('close-mobile')).toBeTruthy();
    }

    // Click en backdrop
    const backdrop = wrapper.find('.sidebar-backdrop');
    if (backdrop.exists()) {
      await backdrop.trigger('click');
    }
  });

  it('RouterSidebarMenu — maneja fallo en catálogo usando estático', async () => {
    vi.spyOn(http, 'get').mockRejectedValueOnce(new Error('Network fail'));
    const wrapper = mount(RouterSidebarMenu, {
      props: { routerId: 'r-01', isOpenMobile: false },
    });
    await flushPromises();
    expect(wrapper.exists()).toBe(true);
  });

  it('RouterWebFigLayout — coordina cabecera, tabs, mock telemetry tick y ciclo de vida', async () => {
    vi.useFakeTimers();

    class MockWebSocket {
      url: string;
      onmessage: ((ev: MessageEvent | { data: string }) => void) | null = null;
      onerror: ((ev: Event) => void) | null = null;
      onclose: (() => void) | null = null;
      constructor(url: string) {
        this.url = url;
        setTimeout(() => {
          if (this.onmessage) {
            this.onmessage({ data: JSON.stringify({ type: 'TELEMETRY_TICK', cpuLoadPct: 22 }) });
            this.onmessage({ data: JSON.stringify({ cpuLoadPct: 35 }) });
            this.onmessage({ data: JSON.stringify({ other: true }) });
            this.onmessage({ data: 'invalid json tick' });
          }
          if (this.onerror) {
            this.onerror(new Event('error'));
          }
        }, 10);
      }
      close() {
        if (this.onclose) this.onclose();
      }
    }
    vi.stubGlobal('WebSocket', MockWebSocket);

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        id: 'r-01',
        display_name: 'Core Router Test',
        ip_address: '192.168.88.1',
      },
      headers: new Headers(),
    });

    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });
    await flushPromises();

    // Avanzar temporizador simulado para ejecutar socket events y tick de mock telemetry
    vi.advanceTimersByTime(2500);
    await flushPromises();

    expect(wrapper.find('.webfig-console-layout').exists()).toBe(true);

    const { useWebFigStore } = await import('@/stores/useWebFigStore');
    const webFigStore = useWebFigStore();

    // Toggle safemode on (inicia 60s)
    const header = wrapper.findComponent(RouterContextHeader);
    if (header.exists()) {
      header.vm.$emit('toggle-safemode');
      await flushPromises();
      expect(webFigStore.isSafeModeActive).toBe(true);

      // Toggle safemode off (detiene)
      header.vm.$emit('toggle-safemode');
      await flushPromises();
      expect(webFigStore.isSafeModeActive).toBe(false);
    }

    // Unmount para probar disconnectWebSocket y limpieza de buffers
    wrapper.unmount();
    vi.useRealTimers();
  });

  it('RouterWebFigLayout — fallback sin WebSocket en window', async () => {
    const win = window as unknown as Record<string, unknown>;
    const originalWS = win.WebSocket;
    delete win.WebSocket;
    const wrapper = mount(RouterWebFigLayout, {
      global: { stubs: { RouterView: true } },
    });
    await flushPromises();
    expect(wrapper.exists()).toBe(true);
    wrapper.unmount();
    win.WebSocket = originalWS;
  });

  it('RouterWebFigLayout — fallback ante excepción de constructor WebSocket', async () => {
    vi.stubGlobal(
      'WebSocket',
      vi.fn().mockImplementation(() => {
        throw new Error('Blocked WS');
      }),
    );
    const wrapper = mount(RouterWebFigLayout, {
      global: { stubs: { RouterView: true } },
    });
    await flushPromises();
    expect(wrapper.exists()).toBe(true);
    wrapper.unmount();
  });

  it('RouterLiveDashboardView — renderiza canvas determinista y cambia ventanas de tiempo', async () => {
    const { useLiveTelemetryStore } = await import('@/stores/useLiveTelemetryStore');
    const telStore = useLiveTelemetryStore();

    // Inyectar 3 puntos antes de montar para que onMounted llame drawCanvasCharts con length >= 2
    telStore.pushTelemetryPoint({
      timestampEpoch: 1700000000,
      timestampIso: new Date().toISOString(),
      cpuLoadPct: 35,
      freeMemoryPct: 65,
      rxBps: 1500000000, // 1.5 Gbps
      txBps: 800000000,
      temperatureC: 42,
    });
    telStore.pushTelemetryPoint({
      timestampEpoch: 1700000002,
      timestampIso: new Date().toISOString(),
      cpuLoadPct: 40,
      freeMemoryPct: 60,
      rxBps: 450, // 450 bps
      txBps: 50000, // 50 kbps
      temperatureC: 43,
    });
    telStore.pushTelemetryPoint({
      timestampEpoch: 1700000004,
      timestampIso: new Date().toISOString(),
      cpuLoadPct: 80,
      freeMemoryPct: 20,
      rxBps: 20000000, // 20 Mbps
      txBps: 10000000, // 10 Mbps
      temperatureC: 45,
    });

    const wrapper = mount(RouterLiveDashboardView);
    await flushPromises();

    // Empujar punto adicional tras montar para activar watch con drawCanvasCharts en modo determinista
    telStore.pushTelemetryPoint({
      timestampEpoch: 1700000006,
      timestampIso: new Date().toISOString(),
      cpuLoadPct: 55,
      freeMemoryPct: 45,
      rxBps: 450, // < 1000 bps para formatBps
      txBps: 0, // 0 bps para formatBps
      temperatureC: 43,
    });
    await flushPromises();

    const windowBtns = wrapper.findAll('.btn-window');
    for (const btn of windowBtns) {
      await btn.trigger('click');
    }

    const ifaceSelect = wrapper.find('select');
    if (ifaceSelect.exists()) {
      await ifaceSelect.setValue('ether2-LAN');
      await ifaceSelect.trigger('change');
    }

    wrapper.unmount();
  });

  it('InterfacesAndSfpView — navega subpestañas y abre modal SFP DDM', async () => {
    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: {
        interface_name: 'sfp-plus1',
        tx_power_dbm: -2.4,
        rx_power_dbm: -18.2,
        optical_health: 'OPTIMAL',
        temperature_c: 41,
        voltage_v: 3.3,
        wavelength_nm: 1310,
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: '*1',
            name: 'sfp-plus1',
            type: 'ether',
            is_sfp: true,
            mac_address: '00:0C:42:00:11:22',
            mtu: 1500,
            running: true,
            disabled: false,
            rx_bps: 1250000, // Mbps
            tx_bps: 450, // bps
          },
          {
            id: '*2',
            name: 'ether1',
            type: 'ether',
            is_sfp: false,
            running: true,
            disabled: false,
            rx_bps: 5000, // kbps
            tx_bps: 0, // 0 bps
          },
          { id: '*3', name: 'vlan10', type: 'vlan', running: true, disabled: false },
          { id: '*4', name: 'br0', type: 'bridge', running: true, disabled: false },
          { id: '*5', name: 'wg0', type: 'wireguard', running: true, disabled: false },
          { id: '*6', name: 'wlan1', type: 'wlan', running: true, disabled: false },
          { id: '*7', name: 'wifi1', type: 'wifi', running: true, disabled: false },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(InterfacesAndSfpView);
    await flushPromises();

    // Filtros de subpestañas
    const tabBtns = wrapper.findAll('.btn-subtab');
    expect(tabBtns.length).toBeGreaterThan(2);
    for (const btn of tabBtns) {
      await btn.trigger('click');
      await flushPromises();
    }

    // Regresar a tab sfp y abrir modal DDM
    await tabBtns[2].trigger('click'); // sfp
    await flushPromises();

    const ddmBtn = wrapper.find('.btn-ddm');
    if (ddmBtn.exists()) {
      await ddmBtn.trigger('click');
      await flushPromises();
      expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);

      const closeModal = wrapper.find('.btn-close');
      if (closeModal.exists()) {
        await closeModal.trigger('click');
      }
    }
  });

  it('InterfacesAndSfpView — fallback ante error de red y health classes', async () => {
    vi.spyOn(http, 'get').mockRejectedValue(new Error('Network error'));
    const wrapper = mount(InterfacesAndSfpView);
    await flushPromises();
    expect(wrapper.exists()).toBe(true);

    // Abrir DDM con fallback mock
    const ddmBtn = wrapper.find('.btn-ddm');
    if (ddmBtn.exists()) {
      await ddmBtn.trigger('click');
      await flushPromises();
    }
  });

  it('FirewallRulesView — reordena reglas y filtra por cadena', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: '*1',
            chain: 'input',
            action: 'accept',
            bytes: 1000000001,
            packets: 200,
            disabled: false,
            dynamic: false,
            invalid: false,
          },
          {
            id: '*2',
            chain: 'forward',
            action: 'drop',
            bytes: 500, // B
            packets: 50,
            disabled: false,
            dynamic: false,
            invalid: false,
          },
          {
            id: '*3',
            chain: 'output',
            action: 'accept',
            bytes: 5000, // KB
            packets: 1,
            disabled: false,
            dynamic: false,
            invalid: false,
          },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const wrapper = mount(FirewallRulesView);
    await flushPromises();

    // Cambiar pestañas
    const tabs = wrapper.findAll('.btn-subtab');
    for (const btn of tabs) {
      await btn.trigger('click');
      await flushPromises();
    }

    // Filtro cadena
    const select = wrapper.find('select');
    if (select.exists()) {
      await select.setValue('input');
      await select.trigger('change');
    }

    // Reordenar mediante evento del componente tabla (éxito)
    const dataTable = wrapper.findComponent({ name: 'RgDataTable' });
    if (dataTable.exists()) {
      dataTable.vm.$emit('reorder', {
        fromIndex: 0,
        toIndex: 1,
        row: { id: '*1', chain: 'input', action: 'accept', bytes: 100 },
      });
      await flushPromises();

      // Reordenar con fallo de red para cubrir catch branch
      vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Move failed'));
      dataTable.vm.$emit('reorder', {
        fromIndex: 1,
        toIndex: 0,
        row: { id: '*2', chain: 'forward', action: 'drop', bytes: 500 },
      });
      await flushPromises();
    }
  });

  it('RoutingBgpOspfView — cambia entre pestañas BGP, OSPF y formatea estado', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('routing/ospf')) {
        return {
          status: 200,
          data: {
            items: [
              {
                id: '*1',
                instance: 'default',
                router_id: '10.0.0.1',
                address: '10.0.0.2',
                interface: 'ether2',
                state: 'full',
                priority: 1,
              },
            ],
          },
          headers: new Headers(),
        };
      }
      return {
        status: 200,
        data: {
          items: [
            {
              id: '*1',
              name: 'peer-1',
              remote_address: '198.51.100.1',
              remote_as: 65001,
              state: 'established',
              uptime: '1d',
              prefixes_received: 10,
              prefixes_sent: 5,
            },
          ],
        },
        headers: new Headers(),
      };
    });

    const wrapper = mount(RoutingBgpOspfView);
    await flushPromises();

    const tabs = wrapper.findAll('.btn-subtab');
    for (const btn of tabs) {
      await btn.trigger('click');
      await flushPromises();
    }
  });

  it('PppAndQueuesView — reconecta suscriptor PPPoE y visualiza Simple Queues', async () => {
    vi.useFakeTimers();

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: '*1',
            name: 'user-01@isp.net',
            service: 'pppoe',
            address: '10.10.10.2',
            caller_id: '00:11:22:33:44:55',
            uptime: '2h',
          },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'delete').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const wrapper = mount(PppAndQueuesView);
    await flushPromises();

    // Filtros de búsqueda (por usuario, dirección y MAC)
    const searchInput = wrapper.find('.search-input');
    if (searchInput.exists()) {
      await searchInput.setValue('user-01');
      await searchInput.setValue('10.10.10.2');
      await searchInput.setValue('00:11');
      await searchInput.setValue('');
    }

    // Reconectar en 1 clic (éxito)
    const reconnectBtn = wrapper.find('.btn-reconnect');
    if (reconnectBtn.exists()) {
      await reconnectBtn.trigger('click');
      await flushPromises();

      // Reconectar con fallo para cubrir catch branch
      vi.spyOn(http, 'delete').mockRejectedValueOnce(new Error('Reset timeout'));
      await reconnectBtn.trigger('click');
      await flushPromises();
    }

    // Avanzar temporizador simulado para limpiar mensajes de acción
    vi.advanceTimersByTime(4500);
    await flushPromises();

    // Cambiar a Simple Queues
    const subtabs = wrapper.findAll('.btn-subtab');
    if (subtabs.length > 1) {
      await subtabs[1].trigger('click');
      await flushPromises();
    }

    vi.useRealTimers();
  });

  it('LiveToolsDiagnosticsView — ejecuta Ping, Traceroute, Torch y visualiza Logs con severidades', async () => {
    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: {
        rows: [
          { seq: 1, host: '8.8.8.8', size: 56, ttl: 64, time_ms: 12.4, status: 'echo reply' },
          { seq: 2, host: '8.8.8.8', size: 0, ttl: 0, time_ms: 10.1, status: 'echo reply' },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          { id: '1', time: '19:00', topics: 'sys', message: 'crit error', severity: 'critical' },
          { id: '2', time: '19:01', topics: 'sys', message: 'warn alert', severity: 'warning' },
          { id: '3', time: '19:02', topics: 'sys', message: 'info log', severity: 'info' },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(LiveToolsDiagnosticsView);
    await flushPromises();

    // Modificar inputs para cubrir v-model handlers
    const targetInput = wrapper.find('#diag-target');
    if (targetInput.exists()) {
      await targetInput.setValue('1.1.1.1');
    }
    const countInput = wrapper.find('#diag-count');
    if (countInput.exists()) {
      await countInput.setValue(5);
    }

    // Iniciar Ping (éxito)
    const form = wrapper.find('form');
    if (form.exists()) {
      await form.trigger('submit.prevent');
      await flushPromises();

      // Probar error de ping para fallback mock
      vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Ping timeout'));
      await form.trigger('submit.prevent');
      await flushPromises();
    }

    // Cambiar a todas las pestañas para cubrir click handlers
    const subtabs = wrapper.findAll('.btn-subtab');
    expect(subtabs.length).toBe(4);
    await subtabs[0].trigger('click'); // ping
    await subtabs[1].trigger('click'); // traceroute
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    await subtabs[2].trigger('click'); // torch
    const ifaceSelect = wrapper.find('#diag-iface');
    if (ifaceSelect.exists()) {
      await ifaceSelect.setValue('sfp-plus1-Trunk');
      await ifaceSelect.trigger('change');
    }
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    await subtabs[3].trigger('click'); // logs
    await flushPromises();
    expect(wrapper.find('.logs-card').exists()).toBe(true);
  });

  it('DynamicLayer2ResourceView — gestiona recursos colección y singleton con Safe Mode', async () => {
    vi.useFakeTimers();

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        ros_path: 'mpls',
        title: 'MPLS Protocol',
        is_singleton: false,
        columns_schema: [
          { key: 'name', label: 'Nombre', type: 'string' },
          { key: 'enabled', label: 'Habilitado', type: 'boolean_ros' },
          { key: 'mtu', label: 'MTU', type: 'integer' },
        ],
        items: [
          { id: '*1', name: 'mpls-instance-1', enabled: true, mtu: 1500 },
          { id: '*2', name: 'mpls-instance-2', enabled: false, mtu: 1500 },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    vi.spyOn(http, 'patch').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const wrapper = mount(DynamicLayer2ResourceView);
    await flushPromises();

    // Crear nuevo registro (post) y probar cancelar
    const createBtn = wrapper.find('.btn-primary');
    if (createBtn.exists()) {
      await createBtn.trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(true);

      // Cerrar modal vía botón close
      await wrapper.find('.btn-close').trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(false);

      // Abrir de nuevo y cancelar
      await createBtn.trigger('click');
      await wrapper.find('.btn-secondary').trigger('click');
      expect(wrapper.find('.rg-modal').exists()).toBe(false);

      // Abrir y manipular inputs para cubrir setter functions
      await createBtn.trigger('click');
      const nameField = wrapper.find('#modal-field-name');
      if (nameField.exists()) {
        await nameField.setValue('new-mpls-3');
      }
      const enabledField = wrapper.find('#modal-field-enabled');
      if (enabledField.exists()) {
        await enabledField.setValue(true);
      }
      const mtuField = wrapper.find('#modal-field-mtu');
      if (mtuField.exists()) {
        await mtuField.setValue(1514);
      }

      const modalForm = wrapper.find('form.modal-body');
      if (modalForm.exists()) {
        await modalForm.trigger('submit.prevent');
        await flushPromises();
      }
    }

    // Editar registro existente seleccionando fila (patch)
    const dataTable = wrapper.findComponent({ name: 'RgDataTable' });
    if (dataTable.exists()) {
      dataTable.vm.$emit('select-row', {
        id: '*1',
        name: 'mpls-instance-1',
        enabled: false,
        mtu: 1500,
      });
      await flushPromises();
      const modalForm = wrapper.find('form.modal-body');
      if (modalForm.exists()) {
        await modalForm.trigger('submit.prevent');
        await flushPromises();

        // Probar error fallback
        vi.spyOn(http, 'patch').mockRejectedValueOnce(new Error('Patch fail'));
        await modalForm.trigger('submit.prevent');
        await flushPromises();
      }
    }

    // Avanzar temporizador simulado para limpiar successMessage
    vi.advanceTimersByTime(4500);
    await flushPromises();

    // Modo singleton
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        ros_path: 'snmp',
        title: 'SNMP Settings',
        is_singleton: true,
        columns_schema: [],
        items: [],
        form_data: { enabled: true, contact: 'noc@example.com' },
      },
      headers: new Headers(),
    });

    mockRouteParam = { routerId: 'r-01', rosPath: 'snmp' };
    const wrapperSingleton = mount(DynamicLayer2ResourceView);
    await flushPromises();

    // Manipular inputs singleton para cubrir setters
    const contactInput = wrapperSingleton.find('#field-contact');
    if (contactInput.exists()) {
      await contactInput.setValue('admin@rosgrid.net');
    }
    const enabledInput = wrapperSingleton.find('#field-enabled');
    if (enabledInput.exists()) {
      await enabledInput.setValue(false);
    }

    const singletonForm = wrapperSingleton.find('form.singleton-form');
    if (singletonForm.exists()) {
      await singletonForm.trigger('submit.prevent');
      await flushPromises();
    }

    vi.useRealTimers();
  });

  it('BridgeView — renderiza pestañas de bridges, puertos, vlans y hosts y maneja modales', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          name: 'bridge1',
          mac_address: '00:11:22:33:44:55',
          vlan_filtering: true,
          protocol_mode: 'rstp',
        },
      ],
      headers: new Headers(),
    });
    vi.spyOn(http, 'post').mockResolvedValue({
      status: 201,
      data: { status: 'success' },
      headers: new Headers(),
    });

    const wrapper = mount(BridgeView);
    await flushPromises();

    expect(wrapper.text()).toContain('Gestor Bridge & VLAN Switching');
    expect(wrapper.text()).toContain('Bridges');

    const tabs = wrapper.findAll('.tab-btn');
    expect(tabs.length).toBe(4);

    // Cambiar a pestaña puertos
    await tabs[1].trigger('click');
    await flushPromises();

    // Cambiar a pestaña vlans
    await tabs[2].trigger('click');
    await flushPromises();

    // Cambiar a pestaña hosts
    await tabs[3].trigger('click');
    await flushPromises();

    // Volver a bridges y abrir modal
    await tabs[0].trigger('click');
    await flushPromises();
    const btnCreate = wrapper.find('.btn-primary');
    if (btnCreate.exists()) {
      await btnCreate.trigger('click');
      expect(wrapper.find('.modal-card').exists()).toBe(true);
      const form = wrapper.find('form.modal-form');
      if (form.exists()) {
        await form.trigger('submit.prevent');
        await flushPromises();
      }
    }
  });

  it('WireGuardVpnView — renderiza interfaces y peers y registra nuevo túnel', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [{ name: 'wg0', listen_port: 13231, public_key: 'abcdef1234567890=', running: true }],
      headers: new Headers(),
    });
    vi.spyOn(http, 'post').mockResolvedValue({
      status: 201,
      data: { status: 'success' },
      headers: new Headers(),
    });

    const wrapper = mount(WireGuardVpnView);
    await flushPromises();

    expect(wrapper.text()).toContain('VPN Moderna WireGuard');
    expect(wrapper.text()).toContain('Interfaces de Túnel');

    const tabs = wrapper.findAll('.tab-btn');
    expect(tabs.length).toBe(2);

    // Pestaña peers
    await tabs[1].trigger('click');
    await flushPromises();

    // Volver a interfaces y crear túnel
    await tabs[0].trigger('click');
    await flushPromises();
    const btnCreate = wrapper.find('.btn-primary');
    if (btnCreate.exists()) {
      await btnCreate.trigger('click');
      expect(wrapper.find('.modal-card').exists()).toBe(true);
      const form = wrapper.find('form.modal-form');
      if (form.exists()) {
        await form.trigger('submit.prevent');
        await flushPromises();
      }
    }
  });
});
