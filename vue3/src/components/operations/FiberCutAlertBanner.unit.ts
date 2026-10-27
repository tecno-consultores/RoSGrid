// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import FiberCutAlertBanner from './FiberCutAlertBanner.vue';
import { useFieldOpsStore } from '@/stores/useFieldOpsStore';

describe('FiberCutAlertBanner.vue — Detección Proactiva de Cortes de Fibra Óptica', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('no renderiza nada cuando no existen incidentes de corte de fibra', async () => {
    const fieldStore = useFieldOpsStore();
    fieldStore.incidents = [];
    vi.spyOn(fieldStore, 'detectFiberCuts').mockResolvedValue([]);

    const wrapper = mount(FiberCutAlertBanner);
    await flushPromises();

    expect(wrapper.find('.fiber-cut-alert-wrapper').exists()).toBe(false);
  });

  it('renderiza banner de alerta crítica cuando se detecta corte masivo', async () => {
    const fieldStore = useFieldOpsStore();
    fieldStore.incidents = [
      {
        id: 'inc-01',
        tenant_id: 't-1',
        router_id: 'r-01',
        pon_port: 'gpon-olt1/1/1',
        optical_box: 'NAP-CANDELARIA-04',
        affected_onus_count: 8,
        incident_summary: 'Posible corte de fibra troncal en GPON OLT 1/1/1',
        detected_at: new Date().toISOString(),
      } as any,
    ];
    vi.spyOn(fieldStore, 'detectFiberCuts').mockResolvedValue(fieldStore.incidents);

    const wrapper = mount(FiberCutAlertBanner);
    await flushPromises();

    expect(wrapper.find('.fiber-cut-alert-wrapper').exists()).toBe(true);
    expect(wrapper.find('.banner-headline').text()).toContain('Posible corte de fibra');
    expect(wrapper.find('.badge-affected').text()).toContain('8');
    expect(wrapper.text()).toContain('NAP-CANDELARIA-04');
  });

  it('permite re-verificar manualmente haciendo click en el botón de acción', async () => {
    const fieldStore = useFieldOpsStore();
    fieldStore.incidents = [
      {
        id: 'inc-01',
        tenant_id: 't-1',
        router_id: 'r-01',
        pon_port: 'gpon-olt1/1/1',
        optical_box: 'NAP-01',
        affected_onus_count: 5,
        incident_summary: 'Corte detectado',
        detected_at: new Date().toISOString(),
      } as any,
    ];
    const detectSpy = vi.spyOn(fieldStore, 'detectFiberCuts').mockResolvedValue([]);

    const wrapper = mount(FiberCutAlertBanner);
    await flushPromises();

    const btn = wrapper.find('.btn-banner-action');
    expect(btn.exists()).toBe(true);
    await btn.trigger('click');

    expect(detectSpy).toHaveBeenCalledWith(3);
  });
});
