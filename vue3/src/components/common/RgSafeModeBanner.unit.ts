/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgSafeModeBanner from './RgSafeModeBanner.vue';
import { useWebFigStore } from '@/stores/useWebFigStore';

describe('RgSafeModeBanner.vue — Dead Man Switch 60s Banner & Verificación en Vivo', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('no se renderiza si isSafeModeActive es false y no hay notificación de reversión', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = false;
    webFigStore.safeModeRevertedNotice = '';

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner').exists()).toBe(false);
    expect(wrapper.find('.rg-safemode-reverted-notice').exists()).toBe(false);
  });

  it('se renderiza con cuenta regresiva cuando Safe Mode está activo', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    webFigStore.safeModeCountdownSeconds = 45;
    webFigStore.safeModeSummary = 'Cambio de IP en ether1';
    webFigStore.safeModeJobName = 'rosgrid-safemode-xyz';

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-banner').exists()).toBe(true);
    expect(wrapper.find('.countdown-val').text()).toBe('45s');
    expect(wrapper.text()).toContain('Cambio de IP en ether1');
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

  it('muestra badge de verificación en vivo cuando safeModeLiveVerified es true', () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    webFigStore.safeModeLiveVerified = true;
    webFigStore.safeModeVerifyLatencyMs = 28.5;

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.safemode-badge--live').exists()).toBe(true);
    expect(wrapper.text()).toContain('28.5 ms');
  });

  it('ejecuta verifySafeModeOnRouter al pulsar #btn-safemode-verify-live', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    const verifySpy = vi.spyOn(webFigStore, 'verifySafeModeOnRouter').mockResolvedValue(undefined);

    const wrapper = mount(RgSafeModeBanner);
    await wrapper.find('#btn-safemode-verify-live').trigger('click');
    expect(verifySpy).toHaveBeenCalledTimes(1);
  });

  it('ejecuta rollbackSafeModeChanges al pulsar #btn-safemode-rollback', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    const rollbackSpy = vi.spyOn(webFigStore, 'rollbackSafeModeChanges').mockResolvedValue(undefined);

    const wrapper = mount(RgSafeModeBanner);
    await wrapper.find('#btn-safemode-rollback').trigger('click');
    expect(rollbackSpy).toHaveBeenCalledTimes(1);
  });

  it('ejecuta confirmSafeModeChanges al pulsar #btn-safemode-confirm', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = true;
    const confirmSpy = vi.spyOn(webFigStore, 'confirmSafeModeChanges').mockResolvedValue(undefined);

    const wrapper = mount(RgSafeModeBanner);
    await wrapper.find('#btn-safemode-confirm').trigger('click');
    expect(confirmSpy).toHaveBeenCalledTimes(1);
  });

  it('muestra banner informativo de reversión completada y permite descartarlo', async () => {
    const webFigStore = useWebFigStore();
    webFigStore.isSafeModeActive = false;
    webFigStore.safeModeRevertedNotice = 'Reversión completada: se restauró el estado previo.';

    const wrapper = mount(RgSafeModeBanner);
    expect(wrapper.find('.rg-safemode-reverted-notice').exists()).toBe(true);
    expect(wrapper.text()).toContain('Reversión completada');

    await wrapper.find('#btn-safemode-dismiss-notice').trigger('click');
    expect(webFigStore.safeModeRevertedNotice).toBe('');
  });

  it('muestra banner de espera de aprobación Maker-Checker ante HTTP 202', async () => {
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
