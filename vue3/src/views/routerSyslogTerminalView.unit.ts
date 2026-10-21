// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import RouterSyslogTerminalView from './RouterSyslogTerminalView.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import type { RouterSyslogResponse, SyslogTemplateResponse } from '@/types';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { routerId: '00000000-0000-0000-0000-000000000001' },
  }),
}));

const MSG_LINK_DOWN = 'ether1 link down';
const MSG_LOGIN = 'User admin logged in';

const sampleSyslogData: RouterSyslogResponse = {
  router_id: '00000000-0000-0000-0000-000000000001',
  total_events: 2,
  critical_count: 1,
  events: [
    {
      timestamp: '2026-10-20 21:00:00',
      facility: 'daemon',
      severity: 'warning',
      topics: 'interface,warning',
      message: MSG_LINK_DOWN,
      is_critical: true,
      raw: '<12>Oct 20 21:00:00 MikroTik ether1 link down',
    },
    {
      timestamp: '2026-10-20 21:01:00',
      facility: 'system',
      severity: 'info',
      topics: 'system,info',
      message: 'User admin logged in from 10.0.0.50 via api',
      is_critical: false,
      raw: '<14>Oct 20 21:01:00 MikroTik User admin logged in',
    },
  ],
};

const sampleTemplate: SyslogTemplateResponse = {
  template_content: '/system logging action add name=rosgrid target=remote remote=192.168.1.10:5514',
  default_port: 5514,
  protocol: 'UDP/TCP',
  instructions: 'Ejecutar en la terminal CLI de MikroTik',
};

describe('RouterSyslogTerminalView.vue — Hito 23.5 Consola Syslog en Vivo', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();

    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url.includes('/syslog/template')) {
        return Promise.resolve({ data: sampleTemplate, status: 200, headers: new Headers() } as unknown as ApiResponse);
      }
      if (url.includes('/syslog')) {
        return Promise.resolve({ data: sampleSyslogData, status: 200, headers: new Headers() } as unknown as ApiResponse);
      }
      return Promise.resolve({ data: {}, status: 200, headers: new Headers() } as unknown as ApiResponse);
    });
  });

  it('monta correctamente y renderiza el encabezado de consola', async () => {
    const wrapper = mount(RouterSyslogTerminalView);
    await wrapper.vm.$nextTick();

    const h2 = wrapper.find('h2');
    expect(h2.exists()).toBe(true);
    expect(h2.text()).toContain('Consola Syslog en Vivo');
  });

  it('renderiza la lista de eventos en el terminal con badges de severidad', async () => {
    const wrapper = mount(RouterSyslogTerminalView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const lines = wrapper.findAll('.log-line');
    expect(lines.length).toBe(2);

    expect(wrapper.text()).toContain(MSG_LINK_DOWN);
    expect(wrapper.text()).toContain('CRIT 🚨');
    expect(wrapper.text()).toContain(MSG_LOGIN);
  });

  it('filtra eventos por severidad en la consola', async () => {
    const wrapper = mount(RouterSyslogTerminalView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const select = wrapper.find('#syslog-severity-filter');
    await select.setValue('WARNING');
    await wrapper.vm.$nextTick();

    const lines = wrapper.findAll('.log-line');
    expect(lines.length).toBe(1);
    expect(wrapper.text()).toContain(MSG_LINK_DOWN);
    expect(wrapper.text()).not.toContain(MSG_LOGIN);
  });

  it('abre el modal con la plantilla CLI de aprovisionamiento RouterOS', async () => {
    const wrapper = mount(RouterSyslogTerminalView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const tplBtn = wrapper.find('.btn-template');
    await tplBtn.trigger('click');
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.modal-dialog').exists()).toBe(true);
    expect(wrapper.text()).toContain('/system logging action add name=rosgrid');
  });

  it('limpia el buffer visual al pulsar el botón de limpiar', async () => {
    const wrapper = mount(RouterSyslogTerminalView);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const clearBtn = wrapper.find('.btn-clear');
    await clearBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('.log-line').length).toBe(0);
    expect(wrapper.text()).toContain('No hay eventos registrados en el RingBuffer');
  });
});
