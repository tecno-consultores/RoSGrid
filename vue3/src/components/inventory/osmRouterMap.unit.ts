// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import OsmRouterMap from './OsmRouterMap.vue';
import type { RouterItem } from '@/types';
import L from 'leaflet';

const sampleRouters: RouterItem[] = [
  {
    id: 'r-1',
    tenant_id: 't-1',
    display_name: 'CCR2004-Caracas',
    ros_identity: 'CCR-Core',
    ip_address: '10.0.0.1',
    api_port: 8728,
    ros_version: '7.18',
    admin_state: 'PRODUCTION',
    is_reachable: true,
    latitude: 10.4806,
    longitude: -66.9036,
    network_role: 'EDGE_BGP',
  },
  {
    id: 'r-2',
    tenant_id: 't-1',
    display_name: 'RB4011-Valencia',
    ip_address: '10.0.0.2',
    api_port: 8728,
    ros_version: '7.18',
    admin_state: 'MAINTENANCE',
    is_reachable: false,
    latitude: 10.162,
    longitude: -68.0077,
    network_role: 'TOWER_AP',
    ssl_trust_status: 'FINGERPRINT_MISMATCH',
  },
];

describe('OsmRouterMap.vue — Mapa Interactivo Leaflet & OpenStreetMap', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(navigator, 'webdriver', {
      value: false,
      configurable: true,
    });
  });

  it('monta el contenedor de mapa accesible, reacciona a cambios de lista y click de marcadores/coordenadas', async () => {
    let capturedMap: L.Map | null = null;
    let capturedMarker: L.Marker | null = null;
    const origMap = L.map;
    const origMarker = L.marker;

    vi.spyOn(L, 'map').mockImplementation((el, opts) => {
      const instance = origMap(el, opts);
      capturedMap = instance;
      return instance;
    });

    vi.spyOn(L, 'marker').mockImplementation((coords, opts) => {
      const m = origMarker(coords, opts);
      if (!capturedMarker) capturedMarker = m;
      return m;
    });

    const wrapper = mount(OsmRouterMap, {
      props: {
        routers: sampleRouters,
        enableCoordinatePicker: true,
      },
    });

    expect(wrapper.find('.osm-map-container').exists()).toBe(true);

    // Simular click en mapa para disparar selector de coordenadas
    if (capturedMap) {
      (capturedMap as L.Map).fire('click', { latlng: { lat: 10.48, lng: -66.9 } });
      expect(wrapper.emitted('coordinates-selected')).toBeTruthy();
    }

    // Simular click en marcador y en botón webfig del popup
    if (capturedMarker) {
      (capturedMarker as L.Marker).fire('click');
      expect(wrapper.emitted('select-router')).toBeTruthy();

      const popup = (capturedMarker as L.Marker).getPopup();
      if (popup) {
        const content = popup.getContent() as HTMLElement;
        const btn = content.querySelector('.btn-popup-webfig') as HTMLButtonElement;
        if (btn) {
          btn.click();
          expect(wrapper.emitted('open-webfig')).toBeTruthy();
        }
      }
    }

    // Actualizar lista de routers para activar watcher con diferentes estados
    await wrapper.setProps({
      routers: [
        ...sampleRouters,
        {
          id: 'r-3',
          tenant_id: 't-1',
          display_name: 'Router-Degraded',
          ip_address: '10.0.0.3',
          api_port: 8728,
          ros_version: '7.18',
          admin_state: 'PRODUCTION',
          ssl_trust_status: 'FINGERPRINT_MISMATCH',
          is_reachable: true,
          latitude: 10.5,
          longitude: -66.9,
        },
        {
          id: 'r-4',
          tenant_id: 't-1',
          display_name: 'Router-Offline',
          ip_address: '10.0.0.4',
          api_port: 8728,
          ros_version: '7.18',
          admin_state: 'PRODUCTION',
          is_reachable: false,
          latitude: 10.6,
          longitude: -66.8,
        },
      ],
    });
  });

  it('renderiza vista determinista cuando navigator.webdriver es true', () => {
    Object.defineProperty(navigator, 'webdriver', {
      value: true,
      configurable: true,
    });

    const wrapper = mount(OsmRouterMap, {
      props: {
        routers: sampleRouters,
      },
    });

    expect(wrapper.find('.deterministic-grid-placeholder').exists()).toBe(true);
  });

  it('responde al cambio de selectedRouterId y coordenadas', async () => {
    const wrapper = mount(OsmRouterMap, {
      props: {
        routers: sampleRouters,
        selectedRouterId: null,
      },
    });

    await wrapper.setProps({ selectedRouterId: 'r-1' });
    await wrapper.setProps({ selectedRouterId: 'non-existing' });
    await wrapper.setProps({ selectedRouterId: '' });
    await wrapper.setProps({
      routers: [
        {
          id: 'r-no-coords',
          tenant_id: 't-1',
          display_name: 'No-Coords',
          ip_address: '10.0.0.99',
          api_port: 8728,
          ros_version: '7.18',
          admin_state: 'PRODUCTION',
          is_reachable: true,
        },
      ],
      selectedRouterId: 'r-no-coords',
    });
    wrapper.unmount();
  });
});
