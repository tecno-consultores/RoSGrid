// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgSafeModeBanner from './RgSafeModeBanner.vue';
import { useWebFigStore } from '@/stores/useWebFigStore';

describe('RgSafeModeBanner.vue — Dead Man Switch 60s Banner', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('no se renderiza si isSafeModeActive es false', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = false;

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner').exists()).toBe(false);
  });

  it('se renderiza con cuenta regresiva cuando Safe Mode está activo', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    webFigStore.safeModeCountdownSeconds = 45;

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner').exists()).toBe(true);
    expect(wrapper.find('.countdown-val').text()).toBe('45s');
    expect(wrapper.find('aside').attributes('aria-live')).toBe('polite');
  });

  it('aplica clase de advertencia pulsante cuando restan <= 15 segundos', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    webFigStore.safeModeCountdownSeconds = 10;

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner--warning').exists()).toBe(true);
    expect(wrapper.find('.pulse-anim').exists()).toBe(true);
  });

  it('llama a stopSafeMode al hacer click en Confirmar Cambios', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;

    const wrapper = mount(RgSafeModeBanner);
    await wrapper.find('.banner-btn').trigger('click');

    expect(webFigStore.isSafeModeActive).toBe(false);
  });

  it('muestra banner de espera de aprobación Maker-Checker (sin cuenta regresiva de 60s) ante HTTP 202', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.startSafeModeCountdown(60);
    expect(webFigStore.isSafeModeActive).toBe(true);

    const intercepted = webFigStore.handleMutationResponse({
      status: 202,
      isMakerCheckerIntercepted: true,
      data: {
        status: 'INTERCEPTED_FOR_APPROVAL',
        approval_request_id: 'appr-001',
        detail: 'Operación en espera de aprobación humana en la bandeja Maker-Checker.',
      },
    });

    expect(intercepted).toBe(true);
    expect(webFigStore.isSafeModeActive).toBe(false);
    expect(webFigStore.isMakerCheckerPending).toBe(true);

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner').exists()).toBe(false);
    expect(wrapper.find('.rg-maker-checker-banner').exists()).toBe(true);
    expect(wrapper.text()).toContain('EN ESPERA DE APROBACIÓN HUMANA (Maker-Checker)');
    expect(wrapper.text()).toContain('PENDIENTE DE REVISIÓN');

    await wrapper.find('.banner-btn--mc').trigger('click');
    expect(webFigStore.isMakerCheckerPending).toBe(false);
  });
});
