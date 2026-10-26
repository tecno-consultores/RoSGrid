// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgFirewallRuleModal from './RgFirewallRuleModal.vue';

describe('RgFirewallRuleModal.vue — Creación y Edición de Reglas de Firewall', () => {
  const sampleRules = [
    {
      id: '*1',
      chain: 'forward',
      action: 'accept',
      bytes: 100,
      packets: 1,
      disabled: false,
      dynamic: false,
      invalid: false,
      comment: 'Regla 1',
    },
    {
      id: '*2',
      chain: 'input',
      action: 'drop',
      bytes: 50,
      packets: 2,
      disabled: false,
      dynamic: false,
      invalid: false,
      comment: 'Drop input',
    },
  ];

  it('no renderiza nada si isOpen es false', () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: false,
        isEditing: false,
        tableType: 'filter',
        existingRules: [],
      },
    });
    expect(wrapper.find('.modal-backdrop').exists()).toBe(false);
  });

  it('renderiza título y opciones para tabla Filter al estar abierto', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'filter',
        existingRules: sampleRules,
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Nueva Regla de Firewall');
    expect(wrapper.find('.table-badge').text()).toBe('[FILTER]');

    const chainSelect = wrapper.find('#rule-chain');
    expect(chainSelect.exists()).toBe(true);
    const options = chainSelect.findAll('option');
    expect(options.some((o) => o.text().includes('forward'))).toBe(true);
  });

  it('muestra opciones contextuales de NAT (srcnat / dstnat)', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'nat',
        existingRules: [],
      },
    });

    expect(wrapper.find('.table-badge').text()).toBe('[NAT]');
    const chainSelect = wrapper.find('#rule-chain');
    const options = chainSelect.findAll('option');
    expect(options.some((o) => o.text().includes('srcnat'))).toBe(true);
    expect(options.some((o) => o.text().includes('dstnat'))).toBe(true);
  });

  it('despliega campos to_addresses y to_ports cuando la acción es dst-nat', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'nat',
        existingRules: [],
      },
    });

    const actionSelect = wrapper.find('#rule-action');
    await actionSelect.setValue('dst-nat');

    expect(wrapper.find('#rule-to-addr').exists()).toBe(true);
    expect(wrapper.find('#rule-to-ports').exists()).toBe(true);
  });

  it('activa alerta crítica si chain=input y action=drop', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'filter',
        existingRules: [],
      },
    });

    await wrapper.find('#rule-chain').setValue('input');
    await wrapper.find('#rule-action').setValue('drop');

    expect(wrapper.find('.critical-warning').exists()).toBe(true);
    expect(wrapper.find('.critical-warning').text()).toContain('Regla Crítica de Entrada');
  });

  it('emite evento save con payload completo al enviar el formulario', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'filter',
        existingRules: sampleRules,
      },
    });

    await wrapper.find('#rule-chain').setValue('forward');
    await wrapper.find('#rule-action').setValue('accept');
    await wrapper.find('#rule-protocol').setValue('tcp');
    await wrapper.find('#rule-dst-port').setValue('443');
    await wrapper.find('#rule-comment').setValue('Permitir HTTPS');

    await wrapper.find('form').trigger('submit.prevent');

    expect(wrapper.emitted('save')).toBeTruthy();
    const emitted = wrapper.emitted('save')?.[0]?.[0] as Record<string, any>;
    expect(emitted.chain).toBe('forward');
    expect(emitted.action).toBe('accept');
    expect(emitted.protocol).toBe('tcp');
    expect(emitted.dst_port).toBe('443');
    expect(emitted.comment).toBe('Permitir HTTPS');
    expect(emitted.disabled).toBe(false);
  });

  it('pre-carga datos al editar una regla existente', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: true,
        tableType: 'filter',
        initialRule: {
          id: '*10',
          chain: 'input',
          action: 'accept',
          protocol: 'tcp',
          dst_port: '8291',
          comment: 'Winbox Access',
          disabled: true,
          bytes: 0,
          packets: 0,
          dynamic: false,
          invalid: false,
        },
        existingRules: sampleRules,
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Editar Regla de Firewall');
    expect((wrapper.find('#rule-comment').element as HTMLInputElement).value).toBe('Winbox Access');
    expect((wrapper.find('#rule-dst-port').element as HTMLInputElement).value).toBe('8291');
  });

  it('emite close al hacer clic en el botón cerrar o tecla Escape', async () => {
    const wrapper = mount(RgFirewallRuleModal, {
      props: {
        isOpen: true,
        isEditing: false,
        tableType: 'filter',
        existingRules: [],
      },
    });

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    await wrapper.find('.modal-backdrop').trigger('keydown', { key: 'Escape' });
    expect(wrapper.emitted('close')?.length).toBe(2);
  });
});
