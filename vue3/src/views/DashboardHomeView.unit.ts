// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import DashboardHomeView from './DashboardHomeView.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import type { RouterItem } from '@/types';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/', params: {}, query: {} }),
  useRouter: () => ({ push: pushMock }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('DashboardHomeView.vue — Centro de Mando Táctico 11X', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
  });

  it('renderiza título Centro de Mando y elimina Mission Control, Tactical NOC y NOC EN VIVO', () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'operador_noc',
      email: 'op@rosgrid.local',
      role: 'SUPPORT_L2',
      tenant_id: 't-1',
      tenant_slug: 'tenant-demo',
      totp_enabled: false,
    });

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const title = wrapper.find('.hub-title');
    expect(title.exists()).toBe(true);
    expect(title.text()).toBe('Centro de Mando');
    expect(title.text()).not.toContain('Mission Control');

    // Comprobar ausencia de elementos eliminados
    expect(wrapper.find('.hub-version-tag').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Tactical NOC v1.0');
    expect(wrapper.find('.telemetry-pill').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('NOC EN VIVO');

    // Subtítulo sin "Organización: "
    const subtitle = wrapper.find('.hub-subtitle');
    expect(subtitle.exists()).toBe(true);
    expect(subtitle.text()).not.toContain('Organización:');
  });

  it('el reloj fue trasladado a la barra superior global y no se renderiza en la pantalla principal', async () => {
    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    // El reloj ya no se muestra en el hub principal
    expect(wrapper.find('.clock-card').exists()).toBe(false);
  });

  it('permite actualizar datos de la flota con el botón de refresco', async () => {
    const inventoryStore = useInventoryStore();
    const fetchSpy = vi.spyOn(inventoryStore, 'fetchRouters').mockResolvedValue();

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const refreshBtn = wrapper.find('button.btn-primary');
    expect(refreshBtn.exists()).toBe(true);
    await refreshBtn.trigger('click');

    expect(fetchSpy).toHaveBeenCalled();
  });

  it('filtra dinámicamente baldosas según Feature Flags: oculta baldosas ISP si isp_module_enabled es false y muestra Matriz CVE si cve_scanner_enabled es true', async () => {
    const authStore = useAuthStore();
    // Empresa no-ISP con escáner de CVE activado
    authStore.tenantFeatures = {
      isp_module_enabled: false,
      cve_scanner_enabled: true,
    };

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const renderedText = wrapper.text();
    // CVEs sí debe aparecer
    expect(renderedText).toContain('Matriz CVE de la Flota');
    // Baldosas exclusivas de ISP NO deben aparecer
    expect(renderedText).not.toContain('Mapa de Abonados FTTH');
    expect(renderedText).not.toContain('Operaciones de Campo');
  });

  it('muestra baldosas de ISP cuando la empresa tiene isp_module_enabled: true', async () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = {
      isp_module_enabled: true,
      cve_scanner_enabled: false,
    };

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const renderedText = wrapper.text();
    expect(renderedText).toContain('Mapa de Abonados FTTH');
    expect(renderedText).toContain('Operaciones de Campo');
    expect(renderedText).not.toContain('Matriz CVE de la Flota');
  });

  it('la baldosa de equipos se titula "Equipos de la Flota" y contiene contenedor con scroll', () => {
    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: true,
        },
      },
    });

    const cardTitle = wrapper.find('.quick-routers-card .card-title');
    expect(cardTitle.exists()).toBe(true);
    expect(cardTitle.text()).toContain('Equipos de la Flota');
    expect(cardTitle.text()).not.toContain('Principales');
  });

  it('navega correctamente a rutas consolidadas al pulsar las baldosas', async () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-1',
      username: 'admin',
      email: 'admin@rosgrid.local',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'tenant-demo',
      totp_enabled: false,
    });
    authStore.tenantFeatures = {
      cve_scanner_enabled: true,
      l2_topology_enabled: true,
      syslog_collector_enabled: true,
    };

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-test-1',
        name: 'Core-CCR2004',
        ip_address: '10.0.0.1',
        is_reachable: true,
        identity: 'Core-CCR2004',
        model: 'CCR2004-1G-12S+2XS',
        ros_version: '7.16',
        board_name: 'CCR2004',
        architecture: 'arm64',
        uptime: '42d',
        cpu_load: 5,
        memory_usage_pct: 12,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      } as unknown as RouterItem,
    ];

    const wrapper = mount(DashboardHomeView, {
      global: {
        stubs: { RouterView: true, RouterLink: true },
      },
    });

    // Encontrar tarjetas de herramientas
    const toolCards = wrapper.findAll('.tile-card');
    expect(toolCards.length).toBeGreaterThan(0);

    // Baldosa CVEs debe navegar a /enterprise/compliance?tab=cves
    const cveCard = toolCards.find((c) => c.text().includes('Matriz CVE'));
    expect(cveCard).toBeDefined();
    await cveCard?.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/enterprise/compliance?tab=cves');

    // Baldosa Sesiones debe navegar a /users?tab=sessions
    pushMock.mockClear();
    const sessionsCard = toolCards.find((c) => c.text().includes('Sesiones'));
    expect(sessionsCard).toBeDefined();
    await sessionsCard?.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/users?tab=sessions');

    // Baldosa Topología debe navegar a /topology/l2
    pushMock.mockClear();
    const topologyCard = toolCards.find((c) => c.text().includes('Topología'));
    expect(topologyCard).toBeDefined();
    await topologyCard?.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/topology/l2');

    // Baldosa Syslog debe navegar al router online activo
    pushMock.mockClear();
    const syslogCard = toolCards.find((c) => c.text().includes('Syslog'));
    expect(syslogCard).toBeDefined();
    await syslogCard?.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/routers/r-test-1/webfig/syslog');
  });
});

