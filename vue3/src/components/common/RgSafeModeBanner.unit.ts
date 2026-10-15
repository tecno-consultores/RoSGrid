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
});
