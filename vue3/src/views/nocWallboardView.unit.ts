/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { http } from '@/api/httpClient';
import NocWallboardView from './NocWallboardView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {},
    path: '/noc-wallboard',
    query: {},
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('NocWallboardView.vue — Conmutador de Mapa Geográfico y Grafo L2/PoE (Hito 30.24 / Spec 101)', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    vi.restoreAllMocks();

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/routers')) {
        return {
          status: 200,
          data: {
            items: [
              {
                id: 'r-01',
                tenant_id: 't-1',
                display_name: 'Core-CCR2004',
                ip_address: '10.0.0.1',
                is_reachable: true,
                admin_state: 'PRODUCTION',
                ssl_trust_status: 'TRUSTED_PINNED',
                latitude: 10.48,
                longitude: -66.90,
              },
            ],
          },
          headers: new Headers(),
        };
      }
      return { status: 200, data: { items: [] }, headers: new Headers() };
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renderiza inicialmente el mapa geográfico y el botón de alternancia #btn-wallboard-toggle-l2-view', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: { template: '<div class="stub-unified-map">UNIFIED_MAP</div>' },
          L2TopologyView: { template: '<div class="stub-l2-topology">L2_TOPOLOGY</div>' },
        },
      },
    });
    await flushPromises();

    const toggleBtn = wrapper.find('#btn-wallboard-toggle-l2-view');
    expect(toggleBtn.exists()).toBe(true);
    expect(toggleBtn.text()).toContain('Grafo L2 / PoE');

    // Inicialmente debe mostrar el UnifiedNetworkMap y no el L2TopologyView
    expect(wrapper.find('.stub-unified-map').exists()).toBe(true);
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(false);
  });

  it('conmuta hacia el Grafo Esquemático L2 y regresa al Mapa Geográfico al hacer clic en #btn-wallboard-toggle-l2-view', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: { template: '<div class="stub-unified-map">UNIFIED_MAP</div>' },
          L2TopologyView: { template: '<div class="stub-l2-topology">L2_TOPOLOGY</div>' },
        },
      },
    });
    await flushPromises();

    const toggleBtn = wrapper.find('#btn-wallboard-toggle-l2-view');

    // Clic 1: Cambiar a Grafo L2 / PoE
    await toggleBtn.trigger('click');
    expect(toggleBtn.text()).toContain('Mapa Geográfico');
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(true);
    expect(wrapper.find('.stub-unified-map').exists()).toBe(false);

    // Clic 2: Regresar al Mapa Geográfico
    await toggleBtn.trigger('click');
    expect(toggleBtn.text()).toContain('Grafo L2 / PoE');
    expect(wrapper.find('.stub-unified-map').exists()).toBe(true);
    expect(wrapper.find('.stub-l2-topology').exists()).toBe(false);
  });

  it('permite refrescar la infraestructura con #btn-wallboard-refresh', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    const refreshBtn = wrapper.find('#btn-wallboard-refresh');
    expect(refreshBtn.exists()).toBe(true);

    await refreshBtn.trigger('click');
    expect(http.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/inventory/routers'),
    );
  });

  it('renderiza la cinta de eventos como HUD flotante semitransparente (.wallboard-events-overlay) y permite minimizarlo y expandirlo (Hito 30.31 / Spec 108)', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    // Inicialmente el HUD de eventos está expandido y tiene clase .wallboard-events-overlay
    const eventsHud = wrapper.find('#wallboard-events-hud');
    expect(eventsHud.exists()).toBe(true);
    expect(eventsHud.classes()).toContain('wallboard-events-overlay');

    const toggleBtn = wrapper.find('#btn-wallboard-toggle-events-hud');
    expect(toggleBtn.exists()).toBe(true);
    expect(wrapper.find('#btn-wallboard-expand-events-hud').exists()).toBe(false);

    // Clic en minimizar el HUD
    await toggleBtn.trigger('click');

    expect(wrapper.find('#wallboard-events-hud').exists()).toBe(false);
    const expandPill = wrapper.find('#btn-wallboard-expand-events-hud');
    expect(expandPill.exists()).toBe(true);
    expect(expandPill.text()).toContain('Eventos en Vivo');

    // Clic en la píldora para restaurar el HUD
    await expandPill.trigger('click');

    expect(wrapper.find('#wallboard-events-hud').exists()).toBe(true);
    expect(wrapper.find('#btn-wallboard-expand-events-hud').exists()).toBe(false);
  });

  it('mantiene la jerarquía estructural de .noc-wallboard con .wallboard-header, .wallboard-body y #wallboard-events-hud sin desbordamiento (Spec 110)', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    const rootWallboard = wrapper.find('.noc-wallboard');
    expect(rootWallboard.exists()).toBe(true);
    expect(rootWallboard.find('.wallboard-header').exists()).toBe(true);
    expect(rootWallboard.find('.wallboard-body').exists()).toBe(true);
    expect(rootWallboard.find('#wallboard-events-hud').exists()).toBe(true);
  });

  it('hereda dinámicamente el tema global sin fijar data-theme="noc-high-contrast" hardcodeado en .noc-wallboard (Spec 111)', async () => {
    const wrapper = mount(NocWallboardView, {
      global: {
        plugins: [pinia],
        stubs: {
          UnifiedNetworkMap: true,
          L2TopologyView: true,
        },
      },
    });
    await flushPromises();

    const root = wrapper.find('.noc-wallboard');
    expect(root.exists()).toBe(true);
    expect(root.attributes('data-theme')).toBeUndefined();
  });

  it('certifica la semitransparencia táctica real (Glass HUD) en NocWallboardView y tokens de themes.css (Hito 30.42)', async () => {
    const fs = await import('fs');
    const path = await import('path');

    const themesPath = path.resolve(__dirname, '../assets/themes.css');
    const viewPath = path.resolve(__dirname, './NocWallboardView.vue');

    const themesCss = fs.readFileSync(themesPath, 'utf-8');
    const viewVue = fs.readFileSync(viewPath, 'utf-8');

    // Verifica que los tokens de cristal están definidos en themes.css
    expect(themesCss).toContain('--rg-hud-glass-bg:');
    expect(themesCss).toContain('--rg-hud-glass-card-bg:');
    expect(themesCss).toContain('--rg-hud-glass-border:');

    // Valida que el canal alfa de --rg-hud-glass-bg es < 0.60
    const glassBgMatches = themesCss.match(/--rg-hud-glass-bg:\s*rgba\([^)]+,\s*([\d.]+)\);/g) || [];
    expect(glassBgMatches.length).toBeGreaterThanOrEqual(3);
    for (const match of glassBgMatches) {
      const alphaVal = parseFloat(match.replace(/.*,\s*([\d.]+)\);/, '$1'));
      expect(alphaVal).toBeLessThan(0.60);
    }

    // Verifica que NocWallboardView usa los tokens de cristal en lugar de opacidades >= 75%
    expect(viewVue).toContain('background: var(--rg-hud-glass-bg);');
    expect(viewVue).toContain('background: var(--rg-hud-glass-card-bg);');
    expect(viewVue).toContain('backdrop-filter: blur(5px)');
  });
});
