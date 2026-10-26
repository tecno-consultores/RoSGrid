// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgSimpleQueueModal from './RgSimpleQueueModal.vue';

describe('RgSimpleQueueModal.vue — Creación y Edición de Simple Queues', () => {
  it('no renderiza nada cuando isOpen es false', () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: false,
        isEditing: false,
      },
    });
    expect(wrapper.find('.modal-backdrop').exists()).toBe(false);
  });

  it('renderiza título y presets de velocidad al estar abierto', () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: false,
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Nueva Cola Simple');
    const presets = wrapper.findAll('.btn-preset');
    expect(presets.length).toBe(6);
    expect(presets[0].text()).toBe('10M / 10M');
    expect(presets[5].text()).toBe('1 Gbps Simétrico');
  });

  it('actualiza el valor de max_limit al hacer clic en un preset', async () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: false,
      },
    });

    const presets = wrapper.findAll('.btn-preset');
    await presets[3].trigger('click'); // 100M / 300M

    const inputMax = wrapper.find('#queue-max-limit');
    expect((inputMax.element as HTMLInputElement).value).toBe('100M/300M');
  });

  it('despliega y oculta opciones avanzadas de Burst y Garantía', async () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: false,
      },
    });

    expect(wrapper.find('#queue-limit-at').exists()).toBe(false);
    const toggleBtn = wrapper.find('.btn-toggle-advanced');
    await toggleBtn.trigger('click');

    expect(wrapper.find('#queue-limit-at').exists()).toBe(true);
    expect(wrapper.find('#queue-burst').exists()).toBe(true);
  });

  it('emite save con el payload completo al enviar el formulario', async () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: false,
      },
    });

    await wrapper.find('#queue-name').setValue('queue-fibra-100');
    await wrapper.find('#queue-target').setValue('192.168.88.50/32');
    await wrapper.find('#queue-max-limit').setValue('50M/100M');
    await wrapper.find('#queue-comment').setValue('Cliente VIP');

    await wrapper.find('form').trigger('submit.prevent');

    expect(wrapper.emitted('save')).toBeTruthy();
    const emitted = wrapper.emitted('save')?.[0]?.[0] as Record<string, any>;
    expect(emitted.name).toBe('queue-fibra-100');
    expect(emitted.target).toBe('192.168.88.50/32');
    expect(emitted.max_limit).toBe('50M/100M');
    expect(emitted.comment).toBe('Cliente VIP');
    expect(emitted.disabled).toBe(false);
  });

  it('pre-carga datos al editar una cola existente', () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: true,
        initialQueue: {
          id: '*1',
          name: 'queue-existente',
          target: '10.10.10.0/24',
          max_limit: '200M/600M',
          bytes_in: 0,
          bytes_out: 0,
          packets_in: 0,
          packets_out: 0,
          disabled: true,
        },
      },
    });

    expect(wrapper.find('.modal-title').text()).toContain('Editar Cola Simple');
    expect((wrapper.find('#queue-name').element as HTMLInputElement).value).toBe('queue-existente');
    expect((wrapper.find('#queue-target').element as HTMLInputElement).value).toBe('10.10.10.0/24');
    expect((wrapper.find('#queue-max-limit').element as HTMLInputElement).value).toBe('200M/600M');
  });

  it('emite close al hacer clic en cerrar o presionar Escape', async () => {
    const wrapper = mount(RgSimpleQueueModal, {
      props: {
        isOpen: true,
        isEditing: false,
      },
    });

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    await wrapper.find('.modal-backdrop').trigger('keydown', { key: 'Escape' });
    expect(wrapper.emitted('close')?.length).toBe(2);
  });
});
