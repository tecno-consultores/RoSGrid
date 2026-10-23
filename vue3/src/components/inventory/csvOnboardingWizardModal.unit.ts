// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import CsvOnboardingWizardModal from './CsvOnboardingWizardModal.vue';
import { http } from '@/api/httpClient';

describe('CsvOnboardingWizardModal.vue — Asistente de Importación CSV en 2 Pasos', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.URL.revokeObjectURL = vi.fn();
  });

  it('no es visible cuando isOpen es false', () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: false },
    });
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('renderiza paso 1, permite descargar plantilla y valida archivo en dry-run con commit exitoso', async () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: true },
    });

    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 1');

    // Descarga de plantilla
    await wrapper.find('.btn-download-template').trigger('click');

    // Enviar sin archivo para cubrir validación
    await wrapper.find('.btn-primary').trigger('click');
    expect(wrapper.find('.banner--error').text()).toContain('selecciona un archivo');

    // Seleccionar archivo
    const file = new File(['display_name,ip_address\nCCR,10.0.0.1'], 'routers.csv', {
      type: 'text/csv',
    });
    const fileInput = wrapper.find('#csv-file-input');
    Object.defineProperty(fileInput.element, 'files', { value: [file] });
    await fileInput.trigger('change');

    // Disparar dry-run
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        total_rows: 2,
        valid_rows_count: 1,
        invalid_rows_count: 1,
        rows: [
          {
            line: 2,
            is_valid: true,
            display_name: 'CCR',
            ip_address: '10.0.0.1',
            serial_number: 'SN1',
          },
          {
            line: 3,
            is_valid: false,
            display_name: 'BadRouter',
            ip_address: 'bad-ip',
            serial_number: 'SN2',
            error: 'Dirección IP inválida',
          },
        ],
      },
      headers: new Headers(),
    });

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();

    // Ahora debe estar en paso 2
    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 2');
    expect(wrapper.find('.rg-preview-table').exists()).toBe(true);
    expect(wrapper.find('.badge-invalid').exists()).toBe(true);

    // Confirmar importación
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: { imported_count: 1 },
      headers: new Headers(),
    });

    await wrapper.findAll('.btn-primary')[0].trigger('click');
    await flushPromises();

    expect(wrapper.emitted('imported')).toBeTruthy();
  });

  it('permite volver al paso 1 desde el paso 2 y maneja fallback de errores', async () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: true },
    });

    const file = new File(['sample'], 'sample.csv', { type: 'text/csv' });
    const fileInput = wrapper.find('#csv-file-input');
    Object.defineProperty(fileInput.element, 'files', { value: [file] });
    await fileInput.trigger('change');

    // Simular error en dry-run para verificar mensaje de error real
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Dry-run offline'));

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Dry-run offline');
    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 1');

    // Ahora simular éxito en dry-run para avanzar a paso 2
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      headers: new Headers(),
      data: {
        total_rows: 2,
        valid_rows_count: 2,
        invalid_rows_count: 0,
        rows: [
          { line: 2, is_valid: true, display_name: 'Router-A', ip_address: '10.0.0.1' },
          { line: 3, is_valid: true, display_name: 'Router-B', ip_address: '10.0.0.2' },
        ],
      },
    });

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();
    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 2');

    // Probar volver al paso 1 usando el botón '← Volver a cargar archivo'
    const backBtn = wrapper.findAll('.btn-secondary')[0];
    await backBtn.trigger('click');
    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 1');

    // Volver al paso 2
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      headers: new Headers(),
      data: {
        total_rows: 2,
        valid_rows_count: 2,
        invalid_rows_count: 0,
        rows: [],
      },
    });
    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();
    expect(wrapper.find('#csv-wizard-title').text()).toContain('Paso 2');

    // Confirmar importación con error de red para verificar manejo de error
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Commit offline'));
    await wrapper.findAll('.btn-primary')[0].trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('Commit offline');

    // Botón cancelar
    const cancelBtns = wrapper.findAll('.btn-secondary');
    const cancelBtn = cancelBtns.find((b) => b.text().includes('Cancelar'));
    if (cancelBtn) {
      await cancelBtn.trigger('click');
      expect(wrapper.emitted('close')).toBeTruthy();
    }

    // Cerrar modal vía backdrop
    await wrapper.find('.rg-modal-backdrop').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    // Cerrar modal vía botón de cabecera
    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('procesa archivo CSV 100% válido sin errores en dry-run y confirma importación', async () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: true },
    });

    const file = new File(['valid_content'], 'valid.csv', { type: 'text/csv' });
    const fileInput = wrapper.find('#csv-file-input');
    Object.defineProperty(fileInput.element, 'files', { value: [file] });
    await fileInput.trigger('change');

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: {
        total_rows: 1,
        valid_rows_count: 1,
        invalid_rows_count: 0,
        rows: [
          {
            line: 2,
            is_valid: true,
            display_name: 'CCR-Valid',
            ip_address: '10.0.0.1',
            serial_number: 'SN-OK',
          },
        ],
      },
      headers: new Headers(),
    });

    await wrapper.find('.btn-primary').trigger('click');
    await flushPromises();

    expect(wrapper.find('.badge-invalid').exists()).toBe(false);

    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: { imported_count: 1, errors: [] },
      headers: new Headers(),
    });

    await wrapper.findAll('.btn-primary')[0].trigger('click');
    await flushPromises();

    expect(wrapper.emitted('imported')).toBeTruthy();
  });

  it('proporciona enlace de descarga nativa con href a /api/v1/inventory/template-csv y nombre correcto', () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: true },
    });

    const link = wrapper.find('a.btn-download-template');
    expect(link.exists()).toBe(true);
    expect(link.attributes('href')).toContain('/api/v1/inventory/template-csv');
    expect(link.attributes('download')).toBe('rosgrid-inventario-plantilla.csv');
  });

  it('permite invocar el clic sobre el enlace de descarga de plantilla sin errores', async () => {
    const wrapper = mount(CsvOnboardingWizardModal, {
      props: { isOpen: true },
    });

    await wrapper.find('.btn-download-template').trigger('click');
    expect(wrapper.exists()).toBe(true);
  });
});
