// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import CapsmanProvisioningModal from './CapsmanProvisioningModal.vue';
import { http } from '@/api/httpClient';

describe('CapsmanProvisioningModal.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('lista reglas de aprovisionamiento existentes al montarse', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: [
        {
          id: '*P1',
          name: 'prov-all-bands',
          action: 'create-dynamic-enabled',
          master_configuration: 'cfg-corporate',
          slave_configurations: ['cfg-guest'],
          supported_bands: ['2ghz-ax', '5ghz-ax'],
          identity_regex: '.*',
          disabled: false,
          comment: 'Global Rule',
        },
      ],
      headers: new Headers(),
    });

    const wrapper = mount(CapsmanProvisioningModal, {
      props: {
        show: true,
        routerId: 'r-01',
        availableConfigs: [
          {
            id: '*C1',
            name: 'cfg-corporate',
            ssid: 'RoSGrid-Corp',
            security_type: 'wpa3-psk',
            client_isolation: false,
          },
        ],
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain('prov-all-bands');
    expect(wrapper.text()).toContain('cfg-corporate');
    expect(wrapper.text()).toContain('cfg-guest');
  });

  it('valida formulario, crea una nueva regla y alterna bandas', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [],
      headers: new Headers(),
    });
    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 201,
      data: { id: '*P2', name: 'prov-hq' },
      headers: new Headers(),
    });

    const wrapper = mount(CapsmanProvisioningModal, {
      props: {
        show: true,
        routerId: 'r-01',
      },
    });
    await flushPromises();

    // Abrir formulario
    await wrapper.find('#btn-toggle-add-prov').trigger('click');

    // Intentar guardar sin master_configuration
    await wrapper.find('#btn-save-prov-rule').trigger('click');
    expect(wrapper.find('[role="alert"]').exists()).toBe(true);

    // Completar master_configuration, slaves y alternar banda
    await wrapper.find('#prov-name').setValue('prov-hq');
    await wrapper.find('#prov-master').setValue('cfg-corporate');
    await wrapper.find('#prov-slaves').setValue('cfg-guest, cfg-iot');
    const bandCheckboxes = wrapper.findAll('.rg-bands-row input[type="checkbox"]');
    if (bandCheckboxes.length > 0) {
      await bandCheckboxes[0].trigger('change');
      await bandCheckboxes[0].trigger('change');
    }

    await wrapper.find('#btn-save-prov-rule').trigger('click');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/wifi/capsman/r-01/provisioning',
      expect.objectContaining({
        name: 'prov-hq',
        master_configuration: 'cfg-corporate',
        slave_configurations: ['cfg-guest', 'cfg-iot'],
      }),
    );
    expect(wrapper.emitted('updated')).toBeTruthy();
  });

  it('elimina una regla y maneja errores de red', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: [
        {
          id: '*P1',
          name: 'prov-del',
          action: 'create-dynamic-enabled',
          master_configuration: 'cfg-corp',
          slave_configurations: [],
          supported_bands: [],
          identity_regex: '.*',
          disabled: false,
        },
      ],
      headers: new Headers(),
    });
    const delSpy = vi.spyOn(http, 'delete').mockResolvedValueOnce({
      status: 204,
      data: null,
      headers: new Headers(),
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    const wrapper = mount(CapsmanProvisioningModal, {
      props: {
        show: true,
        routerId: 'r-01',
      },
    });
    await flushPromises();

    const delBtn = wrapper.find('.rg-btn-danger-sm');
    await delBtn.trigger('click');
    await flushPromises();
    expect(delSpy).toHaveBeenCalledWith('/api/v1/wifi/capsman/r-01/provisioning/*P1');

    // Simular fallo en fetchRules
    vi.spyOn(http, 'get').mockRejectedValueOnce(new Error('Network down'));
    await wrapper.find('#btn-refresh-prov-rules').trigger('click');
    await flushPromises();
    expect(wrapper.find('[role="alert"]').text()).toContain('Network down');
  });
});
