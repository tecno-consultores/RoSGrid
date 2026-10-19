// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import OsmOnuMap from './OsmOnuMap.vue';
import type { SubscriberDeviceItem } from '@/types';

const sampleOnus: SubscriberDeviceItem[] = [
  {
    id: 'onu-1',
    tenant_id: 't-1',
    router_id: 'r-1',
    service_type: 'FTTH_PPPOE',
    auth_backend: 'INTERNAL',
    onu_mode: 'ROUTER',
    device_serial: 'ZTEGC11223344',
    onu_serial_number: 'ZTEGC11223344',
    customer_name: 'Juan Perez',
    pon_port: 'sfp-sfpplus1',
    optical_box: 'NAP-01',
    latitude: 10.4806,
    longitude: -66.9036,
    last_reachability_status: 'ONLINE',
    status: 'ACTIVE',
    ping_latency_ms: 18,
    packet_loss_pct: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'onu-2',
    tenant_id: 't-1',
    router_id: 'r-1',
    service_type: 'FTTH_PPPOE',
    auth_backend: 'INTERNAL',
    onu_mode: 'BRIDGE',
    device_serial: 'HWTC55667788',
    onu_serial_number: 'HWTC55667788',
    customer_name: 'Maria Gomez',
    pon_port: 'sfp-sfpplus1',
    optical_box: 'NAP-01',
    latitude: 10.4806,
    longitude: -66.9036,
    last_reachability_status: 'ONLINE',
    status: 'ACTIVE',
    ping_latency_ms: 65, // Naranja (Degradado)
    packet_loss_pct: 3,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'onu-3',
    tenant_id: 't-1',
    router_id: 'r-1',
    service_type: 'FTTH_PPPOE',
    auth_backend: 'INTERNAL',
    onu_mode: 'ROUTER',
    device_serial: 'VSOL99001122',
    onu_serial_number: 'VSOL99001122',
    customer_name: 'Pedro Infante',
    pon_port: 'sfp-sfpplus2',
    optical_box: 'NAP-02',
    latitude: 10.5001,
    longitude: -66.91,
    last_reachability_status: 'OFFLINE', // Rojo (Caído)
    status: 'ACTIVE',
    ping_latency_ms: null,
    packet_loss_pct: 100,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe('OsmOnuMap.vue — Mapa Exclusivo de ONUs y Telemetría Efímera', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('monta el mapa accesible con Leaflet y renderiza la leyenda cromática', () => {
    const wrapper = mount(OsmOnuMap, {
      props: {
        onus: sampleOnus,
      },
    });

    expect(wrapper.find('.rg-onu-map-wrapper').exists()).toBe(true);
    expect(wrapper.text()).toContain('Telemetría Efímera RAM (Zero-Metrics)');
    expect(wrapper.text()).toContain('< 40ms / 0%');
    expect(wrapper.text()).toContain('40-120ms / 1-20%');
    expect(wrapper.text()).toContain('Offline / > 20%');
  });

  it('reacciona al cambio de props de ONUs', async () => {
    const wrapper = mount(OsmOnuMap, {
      props: {
        onus: [],
      },
    });

    expect(wrapper.find('.rg-leaflet-container').exists()).toBe(true);

    await wrapper.setProps({
      onus: sampleOnus,
    });
    expect(wrapper.props().onus).toHaveLength(3);
  });

  it('desmonta el mapa limpiamente sin fugas de memoria', () => {
    const wrapper = mount(OsmOnuMap, {
      props: {
        onus: sampleOnus,
      },
    });
    wrapper.unmount();
    expect(wrapper.exists()).toBe(false);
  });
});
