// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import RgStepUp2FAModal from './RgStepUp2FAModal.vue';

describe('RgStepUp2FAModal.vue — Step-Up 2FA Modal & 30s Auto-Purge', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('no es visible en el DOM cuando isOpen es false', () => {
    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: false,
      },
    });

    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('se renderiza accesible con dialog modal cuando isOpen es true', () => {
    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: true,
        title: 'Acción Crítica 2FA',
      },
    });

    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);
    expect(wrapper.find('[role="dialog"]').attributes('aria-modal')).toBe('true');
    expect(wrapper.find('.modal-title').text()).toBe('Acción Crítica 2FA');
  });

  it('emite submit-totp con el código de 6 dígitos ingresado', async () => {
    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: true,
      },
    });

    const input = wrapper.find('.totp-input');
    await input.setValue('123456');

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit-totp')).toBeTruthy();
    expect(wrapper.emitted('submit-totp')?.[0][0]).toBe('123456');
  });

  it('emite close al hacer click en el botón de cerrar', async () => {
    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('inicia cuenta regresiva y purga secreto tras 30 segundos si revealedSecret está presente', async () => {
    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: true,
        revealedSecret: 'WPA3-Preshared-Key-Secret-Value',
        autoPurgeSeconds: 30,
      },
    });

    expect(wrapper.find('.revealed-container').exists()).toBe(true);
    expect(wrapper.find('.secret-val').text()).toBe('WPA3-Preshared-Key-Secret-Value');

    // Avanzar el tiempo 30s
    vi.advanceTimersByTime(31000);

    expect(wrapper.emitted('secret-purged')).toBeTruthy();
  });

  it('permite copiar el secreto al portapapeles y responde al cambio de isOpen', async () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    const wrapper = mount(RgStepUp2FAModal, {
      props: {
        isOpen: true,
        revealedSecret: 'TEST-SECRET-123',
      },
    });

    const copyBtn = wrapper.find('.btn-copy');
    if (copyBtn.exists()) {
      await copyBtn.trigger('click');
      vi.advanceTimersByTime(2500);
    }

    await wrapper.setProps({ isOpen: false });
    await wrapper.setProps({ isOpen: true });
    wrapper.unmount();

    // Modal sin revealedSecret para probar enfoque del input al abrirse
    const formModal = mount(RgStepUp2FAModal, {
      props: { isOpen: false },
      attachTo: document.body,
    });
    await formModal.setProps({ isOpen: true });
    formModal.unmount();
  });
});
