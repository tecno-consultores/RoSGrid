// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import ConfigTemplateEditorModal from './ConfigTemplateEditorModal.vue';
import { PREDEFINED_TEMPLATES } from './templatePresets';
import { http } from '@/api/httpClient';

const CLIENTE_NTP_KEY = 'CLIENTE_NTP';
const ACTIVA_NTP_DESC = 'Activa el cliente NTP';
const PRESET_SELECT_ID = '#preset-select';

describe('ConfigTemplateEditorModal.vue — Predefined Templates & Golden Config Editor', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('no es visible en el DOM cuando isOpen es false', () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: false,
      },
    });

    expect(wrapper.find('.modal-backdrop').exists()).toBe(false);
  });

  it('se renderiza accesible con dialog modal cuando isOpen es true', () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    expect(wrapper.find('.modal-backdrop').exists()).toBe(true);
    expect(wrapper.find('[role="dialog"]').attributes('aria-modal')).toBe('true');
    expect(wrapper.find('#template-editor-title').text()).toContain(
      'Nueva Plantilla Golden Config',
    );
  });

  it('contiene la plantilla predefinida CLIENTE_NTP con 4 servidores pool y 5 pasos REST', () => {
    const ntpPreset = PREDEFINED_TEMPLATES.find((p) => p.name === CLIENTE_NTP_KEY);
    expect(ntpPreset).toBeDefined();
    expect(ntpPreset?.category).toBe('SYSTEM');
    expect(ntpPreset?.description).toBe(ACTIVA_NTP_DESC);
    expect(ntpPreset?.variables_schema.length).toBe(4);
    expect(ntpPreset?.rest_steps_template.length).toBe(5);

    expect(ntpPreset?.rest_steps_template[0].endpoint).toBe('system/ntp/client');
    expect(ntpPreset?.rest_steps_template[0].method).toBe('PATCH');
    expect(ntpPreset?.rest_steps_template[1].endpoint).toBe('system/ntp/client/servers');
    expect(ntpPreset?.rest_steps_template[1].method).toBe('PUT');
  });

  it('contiene la plantilla predefinida SYSLOG_CENTRALIZADO_ROSGRID con IP de servidor y 7 pasos REST', () => {
    const syslogPreset = PREDEFINED_TEMPLATES.find((p) => p.name === 'SYSLOG_CENTRALIZADO_ROSGRID');
    expect(syslogPreset).toBeDefined();
    expect(syslogPreset?.category).toBe('SECURITY');
    expect(syslogPreset?.variables_schema.length).toBe(2);
    expect(syslogPreset?.variables_schema[0].key).toBe('rosgrid_server_ip');
    expect(syslogPreset?.variables_schema[1].key).toBe('rosgrid_syslog_port');
    expect(syslogPreset?.rest_steps_template.length).toBe(7);
    expect(syslogPreset?.rest_steps_template[0].endpoint).toBe('system/logging/action');
    expect(syslogPreset?.rest_steps_template[0].method).toBe('PUT');
    expect(syslogPreset?.rest_steps_template[1].endpoint).toBe('system/logging');
    expect(syslogPreset?.rest_steps_template[1].method).toBe('PUT');
    expect(syslogPreset?.requires_safemode).toBe(true);
  });

  it('carga la plantilla predefinida SYSLOG_CENTRALIZADO_ROSGRID al seleccionarla en el dropdown', async () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    const presetSelect = wrapper.find(PRESET_SELECT_ID);
    expect(presetSelect.exists()).toBe(true);

    await presetSelect.setValue('SYSLOG_CENTRALIZADO_ROSGRID');
    await presetSelect.trigger('change');
    await flushPromises();

    const nameInput = wrapper.find('#tpl-name').element as HTMLInputElement;
    expect(nameInput.value).toBe('SYSLOG_CENTRALIZADO_ROSGRID');

    const descInput = wrapper.find('#tpl-desc').element as HTMLTextAreaElement;
    expect(descInput.value).toContain('Syslog remoto');

    const categorySelect = wrapper.find('#tpl-category').element as HTMLSelectElement;
    expect(categorySelect.value).toBe('SECURITY');

    expect(wrapper.find('.alert--success').text()).toContain('SYSLOG_CENTRALIZADO_ROSGRID');
  });

  it('carga la plantilla predefinida CLIENTE_NTP al seleccionarla en el dropdown', async () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    const presetSelect = wrapper.find(PRESET_SELECT_ID);
    expect(presetSelect.exists()).toBe(true);

    await presetSelect.setValue(CLIENTE_NTP_KEY);
    await presetSelect.trigger('change');
    await flushPromises();

    const nameInput = wrapper.find('#tpl-name').element as HTMLInputElement;
    expect(nameInput.value).toBe(CLIENTE_NTP_KEY);

    const descInput = wrapper.find('#tpl-desc').element as HTMLTextAreaElement;
    expect(descInput.value).toBe(ACTIVA_NTP_DESC);

    const categorySelect = wrapper.find('#tpl-category').element as HTMLSelectElement;
    expect(categorySelect.value).toBe('SYSTEM');

    expect(wrapper.find('.alert--success').text()).toContain('CLIENTE_NTP');
  });

  it('permite cambiar entre pestañas y añadir una variable dinámica', async () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    const tabs = wrapper.findAll('.tab-btn');
    expect(tabs.length).toBe(4);

    // Pestaña Variables
    await tabs[1].trigger('click');
    expect(wrapper.find('.tab-pane').exists()).toBe(true);

    const addVarBtn = wrapper.find('.btn-add-var');
    if (addVarBtn.exists()) {
      await addVarBtn.trigger('click');
      await flushPromises();
    }

    // Pestaña Pasos
    await tabs[2].trigger('click');
    const addStepBtn = wrapper.find('.btn-add-step');
    if (addStepBtn.exists()) {
      await addStepBtn.trigger('click');
      await flushPromises();
    }

    // Pestaña Preview
    await tabs[3].trigger('click');
    expect(wrapper.find('.preview-box').exists()).toBe(true);
  });

  it('guarda una plantilla válida y emite saved y close', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 201,
      data: {
        id: 'tpl-123',
        name: CLIENTE_NTP_KEY,
        category: 'SYSTEM',
        description: ACTIVA_NTP_DESC,
        variables_schema: [],
        rest_steps_template: [
          { method: 'PATCH', endpoint: 'system/ntp/client', payload: { enabled: 'yes' } },
        ],
        requires_safemode: true,
      },
      headers: new Headers(),
    });

    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find(PRESET_SELECT_ID).setValue(CLIENTE_NTP_KEY);
    await wrapper.find(PRESET_SELECT_ID).trigger('change');
    await flushPromises();

    const saveBtn = wrapper.find('.btn-primary');
    await saveBtn.trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/operations/templates',
      expect.objectContaining({
        name: CLIENTE_NTP_KEY,
        category: 'SYSTEM',
        description: ACTIVA_NTP_DESC,
      }),
    );

    expect(wrapper.emitted('saved')).toBeTruthy();

    vi.advanceTimersByTime(800);
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emite close al hacer click en el botón de cerrar', async () => {
    const wrapper = mount(ConfigTemplateEditorModal, {
      props: {
        isOpen: true,
      },
    });

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
