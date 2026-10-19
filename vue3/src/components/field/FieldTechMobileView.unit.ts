// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import FieldTechMobileView from './FieldTechMobileView.vue';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';

describe('FieldTechMobileView.vue — Panel Responsive del Técnico de Campo', () => {
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

  it('renderiza encabezado táctico, lista de órdenes y selector de pestañas', async () => {
    const store = useFieldOpsStore();
    store.orders = [
      {
        id: 'ord-12345678',
        tenant_id: 't-1',
        customer_service_id: 'CLI-9901',
        status: 'ASSIGNED',
        notes: 'Instalación nueva fibra óptica',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const wrapper = mount(FieldTechMobileView);
    expect(wrapper.text().toUpperCase()).toContain('TÉCNICO DE CAMPO');
    expect(wrapper.text()).toContain('CLI-9901');
    expect(wrapper.text()).toContain('ORD-ord-1234');
  });

  it('permite seleccionar una orden y pasa a modo de verificación', async () => {
    const store = useFieldOpsStore();
    store.orders = [
      {
        id: 'ord-99887766',
        tenant_id: 't-1',
        customer_service_id: 'CLI-5544',
        status: 'ASSIGNED',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const wrapper = mount(FieldTechMobileView);
    const orderCard = wrapper.find('.order-card');
    await orderCard.trigger('click');

    const inputSub = wrapper.find('#sub-id');
    expect((inputSub.element as HTMLInputElement).value).toBe('CLI-5544');
  });

  it('ejecuta captura de coordenadas GPS con feedback reactivo', async () => {
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
    const btnGps = wrapper.find('#btn-prominent-gps-header');
    await btnGps.trigger('click');

    expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled();
    expect(wrapper.text()).toContain('10.4806');
    expect(wrapper.text()).toContain('-66.9036');
  });

  it('ejecuta verificación 1-click y muestra métricas en vivo', async () => {
    const store = useFieldOpsStore();
    vi.spyOn(store, 'verifySubscriberLive').mockImplementation(async () => {
      store.activeVerification = {
        customer_service_id: 'CLI-TEST',
        session_active: true,
        connection_type: 'PPPOE',
        uptime_seconds: 3600,
        assigned_ipv4: '100.64.10.5',
        detected_mode: 'ROUTER',
        ping_success: true,
        ping_avg_ms: 18,
        ping_loss_pct: 0,
        traffic_rx_kbps: 4500,
        traffic_tx_kbps: 1200,
        status_summary: 'Enlace óptico excelente',
      };
      return store.activeVerification;
    });

    const wrapper = mount(FieldTechMobileView);
    const input = wrapper.find('#sub-id');
    await input.setValue('CLI-TEST');

    const btnTest = wrapper.find('#btn-run-1click-test');
    await btnTest.trigger('click');

    expect(store.verifySubscriberLive).toHaveBeenCalledWith('CLI-TEST', undefined, undefined);
    expect(wrapper.text()).toContain('EN LÍNEA EN ROUTEROS');
    expect(wrapper.text()).toContain('18 ms');
    expect(wrapper.text()).toContain('100.64.10.5');
  });

  it('permite dibujar y limpiar la firma en el canvas', async () => {
    const wrapper = mount(FieldTechMobileView);
    const canvas = wrapper.find('.signature-pad');

    await canvas.trigger('mousedown', { clientX: 20, clientY: 20 });
    await canvas.trigger('mousemove', { clientX: 60, clientY: 60 });
    await canvas.trigger('mouseup');

    const btnClear = wrapper.find('.btn-clear-sig');
    await btnClear.trigger('click');
    expect(btnClear.exists()).toBe(true);
  });

  it('ejecuta certificación de instalación cuando el serial está ingresado', async () => {
    const store = useFieldOpsStore();
    vi.spyOn(store, 'certifyInstallation').mockResolvedValue({
      id: 'ord-1',
      tenant_id: 't-1',
      customer_service_id: 'CLI-CERT',
      status: 'CERTIFIED',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const wrapper = mount(FieldTechMobileView);
    const inputCircuit = wrapper.find('#cert-circuit-id');
    await inputCircuit.setValue('CLI-CERT');

    const inputSerial = wrapper.find('#cert-serial');
    await inputSerial.setValue('ZTEGC99887766');

    const btnCertify = wrapper.find('#btn-certify-installation');
    await btnCertify.trigger('click');

    expect(store.certifyInstallation).toHaveBeenCalled();
  });

  it('ejecuta diagnóstico rápido 360° en desktop', async () => {
    const wrapper = mount(FieldTechMobileView);
    const inputSub = wrapper.find('#sub-id');
    await inputSub.setValue('CLI-360');

    const btn360 = wrapper.find('.toolkit-360-header button');
    await btn360.trigger('click');

    // Espera actualización asíncrona
    await vi.waitFor(() => {
      expect(wrapper.find('.diag360-result-banner').exists()).toBe(true);
    });
  });
});
