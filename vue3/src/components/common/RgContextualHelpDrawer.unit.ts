// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import RgContextualHelpDrawer from './RgContextualHelpDrawer.vue';
import { useContextualHelp } from '@/composables/useContextualHelp';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    path: '/routers/r-01/webfig/firewall',
    name: 'FirewallRules',
  }),
}));

describe('RgContextualHelpDrawer.vue — Cajón de Ayuda Contextual In-App (Hito 27.14)', () => {
  beforeEach(() => {
    const help = useContextualHelp();
    help.closeHelp();
  });

  it('permanece oculto cuando isHelpOpen es false y se despliega con atributos WCAG 2.1 AA al abrirse', async () => {
    const help = useContextualHelp();
    const wrapper = mount(RgContextualHelpDrawer);

    expect(wrapper.find('#rg-contextual-help-drawer').exists()).toBe(false);

    help.openHelp();
    await wrapper.vm.$nextTick();

    const drawer = wrapper.find('#rg-contextual-help-drawer');
    expect(drawer.exists()).toBe(true);
    expect(drawer.attributes('role')).toBe('dialog');
    expect(drawer.attributes('aria-modal')).toBe('true');
    expect(drawer.attributes('aria-labelledby')).toBe('help-drawer-title');
    expect(wrapper.find('#help-drawer-title').text()).toContain('Firewall');
  });

  it('permite cambiar de tópico desde el selector, volver a la pantalla actual y copiar guía como Markdown', async () => {
    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: writeTextSpy },
    });

    const help = useContextualHelp();
    help.openHelp();
    const wrapper = mount(RgContextualHelpDrawer);
    await wrapper.vm.$nextTick();

    const selector = wrapper.find<HTMLSelectElement>('#help-topic-selector');
    expect(selector.exists()).toBe(true);
    await selector.setValue('webfig-routing');
    expect(wrapper.find('#help-drawer-title').text()).toContain('BGP v7');

    const resetBtn = wrapper.find('#btn-reset-help-topic');
    expect(resetBtn.exists()).toBe(true);
    await resetBtn.trigger('click');
    expect(wrapper.find('#help-drawer-title').text()).toContain('Firewall');

    const copyBtn = wrapper.find('#btn-copy-help-markdown');
    expect(copyBtn.exists()).toBe(true);
    await copyBtn.trigger('click');
    await flushPromises();
    expect(writeTextSpy).toHaveBeenCalled();
    expect(copyBtn.text()).toContain('Guía Copiada');
  });

  it('cumple la frontera arquitectónica: cero botones de exportación a PDF dentro de la consola RoSGrid', async () => {
    const help = useContextualHelp();
    help.openHelp();
    const wrapper = mount(RgContextualHelpDrawer);
    await wrapper.vm.$nextTick();

    expect(wrapper.html().toLowerCase()).not.toContain('descargar pdf');
    expect(wrapper.html().toLowerCase()).not.toContain('exportar pdf');
  });

  it('cierra el cajón al hacer clic en el botón cerrar o en el backdrop (light dismiss)', async () => {
    const help = useContextualHelp();
    help.openHelp();
    const wrapper = mount(RgContextualHelpDrawer);
    await wrapper.vm.$nextTick();

    await wrapper.find('#btn-close-contextual-help').trigger('click');
    expect(help.isHelpOpen.value).toBe(false);

    help.openHelp();
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="help-drawer-backdrop"]').trigger('click');
    expect(help.isHelpOpen.value).toBe(false);
  });
});
