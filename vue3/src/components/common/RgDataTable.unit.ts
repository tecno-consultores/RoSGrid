// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgDataTable from './RgDataTable.vue';
import type { TableColumn } from '@/types';

interface TestRow extends Record<string, unknown> {
  id: string;
  name: string;
  ip?: string;
  status?: string;
  disabled?: boolean;
  invalid?: boolean;
  dynamic?: boolean;
  running?: boolean;
}

describe('RgDataTable.vue — WinBox 32px / Táctil 44px & RouterOS Flags', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  const columns: TableColumn<Record<string, unknown>>[] = [
    { key: 'name', label: 'Nombre', sortable: true, formatter: (row) => `dev:${row.name}` },
    { key: 'ip', label: 'Dirección IP', align: 'center' },
    { key: 'status', label: 'Estado', align: 'right' },
  ];

  const sampleRows: TestRow[] = [
    { id: '1', name: 'ether1', ip: '10.0.0.1', status: 'up', running: true },
    { id: '2', name: 'ether2', ip: '', status: '', disabled: true },
    { id: '3', name: 'ether3', ip: '10.0.0.3', status: 'invalid', invalid: true, dynamic: true },
    { id: '4', name: 'ether4', ip: undefined, status: undefined },
  ];

  it('renderiza encabezados y filas correctamente con accesibilidad WCAG', () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
        caption: 'Interfaces de Red',
      },
    });

    expect(wrapper.find('caption').text()).toBe('Interfaces de Red');
    expect(wrapper.findAll('th').length).toBe(4);
    expect(wrapper.findAll('tbody tr.rg-table-row').length).toBe(4);
  });

  it('renderiza insignias RouterOS v7 ([D], [X], [I], [R]) según banderas de fila', () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
      },
    });

    const rows = wrapper.findAll('tbody tr.rg-table-row');
    expect(rows[0].find('.rg-flag--r').exists()).toBe(true);
    expect(rows[0].find('.rg-flag--r').text()).toBe('[R]');
    expect(rows[1].find('.rg-flag--x').exists()).toBe(true);
    expect(rows[1].find('.rg-flag--x').text()).toBe('[X]');
    expect(rows[2].find('.rg-flag--d').exists()).toBe(true);
    expect(rows[2].find('.rg-flag--d').text()).toBe('[D]');
    expect(rows[2].find('.rg-flag--i').exists()).toBe(true);
    expect(rows[2].find('.rg-flag--i').text()).toBe('[I]');
  });

  it('emite select-row al hacer click en una fila', async () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
      },
    });

    await wrapper.findAll('tbody tr.rg-table-row')[0].trigger('click');
    expect(wrapper.emitted('select-row')).toBeTruthy();
    expect(wrapper.emitted('select-row')?.[0][0]).toEqual(sampleRows[0]);
  });

  it('permite alternar densidad de tabla con el botón del toolbar', async () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
      },
    });

    const toggleBtn = wrapper.find('.rg-density-toggle');
    expect(toggleBtn.exists()).toBe(true);
    await toggleBtn.trigger('click');
  });

  it('soporta reordenamiento por botones de flechas y Drag & Drop cuando sortableRows es true', async () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
        sortableRows: true,
      },
    });

    const arrows = wrapper.findAll('.btn-arrow');
    expect(arrows.length).toBeGreaterThan(0);
    // Click en primera flecha hacia arriba (límite superior, no debe mover)
    await arrows[0].trigger('click');
    // Click en mover hacia abajo en primera fila
    await arrows[1].trigger('click');
    expect(wrapper.emitted('reorder')).toBeTruthy();
    // Click en última flecha hacia abajo (límite inferior, no debe mover)
    await arrows[arrows.length - 1].trigger('click');

    // Simular drag and drop
    const rows = wrapper.findAll('tbody tr.rg-table-row');
    // Drop en misma fila (sin reorder)
    await rows[0].trigger('dragstart', { dataTransfer: { effectAllowed: '' } });
    await rows[0].trigger('drop');

    // Drop sin haber iniciado drag (draggedIndex === null)
    await rows[1].trigger('drop');

    // Drag sin dataTransfer
    await rows[0].trigger('dragstart', {});

    // Drag y drop exitoso entre filas distintas
    await rows[0].trigger('dragstart', { dataTransfer: { effectAllowed: '' } });
    await rows[1].trigger('dragover');
    await rows[1].trigger('drop');
    expect(wrapper.emitted('reorder')?.length).toBeGreaterThan(1);
  });

  it('activa Virtual Scrolling cuando rows > 100 limitando filas y respondiendo al scroll', async () => {
    const manyRows: TestRow[] = Array.from({ length: 150 }, (_, i) => ({
      id: `row-${i}`,
      name: `iface-${i}`,
      ip: `10.0.0.${i}`,
      status: 'up',
    }));

    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: manyRows,
      },
    });

    const renderedRows = wrapper.findAll('tbody tr.rg-table-row');
    expect(renderedRows.length).toBeLessThan(150);
    expect(renderedRows.length).toBeGreaterThan(0);

    const scrollContainer = wrapper.find('.rg-table-scroll');
    await scrollContainer.trigger('scroll');
  });

  it('permite expandir y colapsar detalles de fila en modo comfortable', async () => {
    const { useThemeAndLayoutStore } = await import('@/stores/useThemeAndLayoutStore');
    const themeStore = useThemeAndLayoutStore();
    themeStore.setTableDensityMode('comfortable');

    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
      },
    });

    const expandBtn = wrapper.find('.btn-details-toggle');
    expect(expandBtn.exists()).toBe(true);
    await expandBtn.trigger('click');
    expect(wrapper.find('.rg-row-details').exists()).toBe(true);
    await expandBtn.trigger('click');
    expect(wrapper.find('.rg-row-details').exists()).toBe(false);
  });

  it('renderiza el slot de acciones personalizadas cuando se proporciona', () => {
    const wrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: sampleRows,
      },
      slots: {
        actions: '<button class="test-action-btn">Acción</button>',
      },
    });
    expect(wrapper.findAll('.col-custom-actions').length).toBe(5);
    expect(wrapper.find('.test-action-btn').exists()).toBe(true);
  });

  it('renderiza el Empty State táctico (Refactoring UI) cuando rows está vacío y soporta slot personalizado', () => {
    const defaultEmptyWrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: [],
        emptyMessage: 'No hay reglas de firewall registradas.',
      },
    });

    const emptyBox = defaultEmptyWrapper.find('.rg-table-empty');
    expect(emptyBox.exists()).toBe(true);
    expect(emptyBox.attributes('role')).toBe('status');
    expect(emptyBox.text()).toContain('No hay reglas de firewall registradas.');

    const customSlotWrapper = mount(RgDataTable, {
      props: {
        columns,
        rows: [],
      },
      slots: {
        empty: '<div class="custom-empty-cta">+ Crear Primera Regla</div>',
      },
    });

    expect(customSlotWrapper.find('.custom-empty-cta').exists()).toBe(true);
    expect(customSlotWrapper.find('.custom-empty-cta').text()).toBe('+ Crear Primera Regla');
  });
});
