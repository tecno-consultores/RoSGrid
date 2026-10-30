// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgLayer2QueryBuilder from './RgLayer2QueryBuilder.vue';

describe('RgLayer2QueryBuilder.vue (Spec 54 — 27.16.4)', () => {
  const columnsSchema = [
    { key: 'name', label: 'Nombre', type: 'string' },
    { key: 'trusted', label: 'Confiable', type: 'boolean_ros' },
  ];

  it('permite agregar condiciones .query, alternar .proplist y emitir apply/clear', async () => {
    const wrapper = mount(RgLayer2QueryBuilder, {
      props: {
        columnsSchema,
        filters: [{ field: 'trusted', operator: '=', value: 'true' }],
        proplistActive: true,
      },
    });

    expect(wrapper.findAll('.qb-pill').length).toBe(1);

    await wrapper.find('#qb-input-value').setValue('rosgrid-ca');
    await wrapper.find('#btn-add-l2-filter').trigger('click');

    expect(wrapper.emitted('update:filters')?.[0][0]).toEqual([
      { field: 'trusted', operator: '=', value: 'true' },
      { field: 'name', operator: '=', value: 'rosgrid-ca' },
    ]);

    await wrapper.find('#chk-proplist-optimize').setValue(false);
    expect(wrapper.emitted('update:proplistActive')?.[0]).toEqual([false]);

    await wrapper.find('#btn-apply-l2-query').trigger('click');
    expect(wrapper.emitted('apply')).toBeTruthy();

    await wrapper.find('.qb-pill-remove').trigger('click');
    expect(wrapper.emitted('update:filters')?.[1][0]).toEqual([]);

    await wrapper.find('#btn-clear-l2-query').trigger('click');
    expect(wrapper.emitted('clear')).toBeTruthy();
  });
});
