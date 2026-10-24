// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgApiHealthBadge from './RgApiHealthBadge.vue';
import { useApiHeartbeatStore } from '@/stores/useApiHeartbeatStore';

describe('RgApiHealthBadge.vue — Indicador Táctico de Disponibilidad de API', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renderiza con estado ONLINE y muestra la latencia en milisegundos', async () => {
    const store = useApiHeartbeatStore();
    store.status = 'online';
    store.latencyMs = 18;
    store.services = { database: 'connected', redis: 'connected' };

    const wrapper = mount(RgApiHealthBadge);

    const badge = wrapper.find('#api-health-badge');
    expect(badge.exists()).toBe(true);
    expect(badge.classes()).toContain('rg-health-badge--online');
    expect(wrapper.text()).toContain('API');
    expect(wrapper.text()).toContain('18ms');
    expect(badge.attributes('role')).toBe('status');
  });

  it('renderiza con estado OFFLINE cuando el backend no responde', async () => {
    const store = useApiHeartbeatStore();
    store.status = 'offline';
    store.latencyMs = null;

    const wrapper = mount(RgApiHealthBadge);

    const badge = wrapper.find('#api-health-badge');
    expect(badge.classes()).toContain('rg-health-badge--offline');
    expect(wrapper.text()).toContain('API');
    expect(wrapper.text()).toContain('OFFLINE');
  });

  it('abre el popover táctico al hacer clic en el botón del badge', async () => {
    const store = useApiHeartbeatStore();
    store.status = 'online';
    store.latencyMs = 12;
    store.services = { database: 'connected', redis: 'connected' };

    const wrapper = mount(RgApiHealthBadge);

    expect(wrapper.find('.rg-health-popover').exists()).toBe(false);

    await wrapper.find('#api-health-badge').trigger('click');

    expect(wrapper.find('.rg-health-popover').exists()).toBe(true);
    expect(wrapper.text()).toContain('Telemetría Backend');
    expect(wrapper.text()).toContain('PostgreSQL:');
    expect(wrapper.text()).toContain('KeyDB Caché:');
  });

  it('ejecuta ping forzado al presionar el botón de reintento en el popover', async () => {
    const store = useApiHeartbeatStore();
    const checkSpy = vi.spyOn(store, 'checkHealth').mockResolvedValue();

    const wrapper = mount(RgApiHealthBadge);
    await wrapper.find('#api-health-badge').trigger('click');

    const retryBtn = wrapper.find('.btn-ping-action');
    expect(retryBtn.exists()).toBe(true);

    await retryBtn.trigger('click');
    expect(checkSpy).toHaveBeenCalledWith(true);
  });

  it('cierra el popover al presionar la tecla Escape', async () => {
    const wrapper = mount(RgApiHealthBadge);
    await wrapper.find('#api-health-badge').trigger('click');
    expect(wrapper.find('.rg-health-popover').exists()).toBe(true);

    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escapeEvent);
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.rg-health-popover').exists()).toBe(false);
  });
});
