// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgLayer2RpcActionModal from './RgLayer2RpcActionModal.vue';
import type { Layer2RpcActionDescriptor } from '@/types';

const DEFAULT_CA_NAME = 'rosgrid-ca';
const SAMPLE_CERT_NAME = 'api-ssl-cert';

describe('RgLayer2RpcActionModal.vue (Spec 54 — 27.16.2)', () => {
  const sampleDescriptor: Layer2RpcActionDescriptor = {
    action: 'sign',
    label: 'Firmar Certificado (CA)',
    icon: '✍️',
    scope: 'row',
    requires_safe_mode: true,
    requires_confirmation: true,
    params_schema: [
      {
        key: 'certificate',
        label: 'Plantilla de Certificado',
        type: 'string',
        required: true,
        description: 'Nombre del certificado a firmar.',
      },
      {
        key: 'ca',
        label: 'Autoridad Certificadora',
        type: 'enum',
        required: false,
        default: DEFAULT_CA_NAME,
        options: [DEFAULT_CA_NAME, 'corp-ca'],
      },
    ],
  };

  it('prellena valores por defecto y objetivo de fila al abrirse y emite submit', async () => {
    const wrapper = mount(RgLayer2RpcActionModal, {
      props: {
        isOpen: true,
        descriptor: sampleDescriptor,
        targetRow: { '.id': '*A', name: SAMPLE_CERT_NAME },
      },
    });

    expect(wrapper.find('#layer2-rpc-modal').exists()).toBe(true);
    expect(wrapper.text()).toContain('Firmar Certificado (CA)');
    expect(wrapper.text()).toContain(SAMPLE_CERT_NAME);

    await wrapper.find('form').trigger('submit.prevent');
    const emitted = wrapper.emitted('submit');
    expect(emitted).toBeTruthy();
    expect(emitted?.[0][0]).toEqual({
      action: 'sign',
      params: {
        certificate: SAMPLE_CERT_NAME,
        ca: DEFAULT_CA_NAME,
      },
      target_id: '*A',
      requires_safe_mode: true,
    });
  });

  it('emite close al pulsar el botón cancelar o cerrar', async () => {
    const wrapper = mount(RgLayer2RpcActionModal, {
      props: {
        isOpen: true,
        descriptor: {
          action: 'make-static',
          label: 'Convertir Lease en Estático',
          icon: '📌',
          scope: 'row',
          requires_safe_mode: true,
          requires_confirmation: false,
          params_schema: [],
        },
        targetRow: { id: '*12', address: '192.168.88.50' },
      },
    });

    expect(wrapper.find('.empty-params-hint').exists()).toBe(true);
    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
