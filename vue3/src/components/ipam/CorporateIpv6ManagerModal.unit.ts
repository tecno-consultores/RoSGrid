// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import CorporateIpv6ManagerModal from './CorporateIpv6ManagerModal.vue';
import { useIpamStore } from '@/stores/useIpamStore';

describe('CorporateIpv6ManagerModal.vue — Gestor de Asignación IPv6 Corporativo', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();
  });

  it('renderiza título del modal y previsualización de prefijo calculado', () => {
    const wrapper = mount(CorporateIpv6ManagerModal);
    expect(wrapper.find('#corp-modal-title').text()).toContain('Gestor de Asignación IPv6');
    expect(wrapper.find('.preview-box').exists()).toBe(true);
  });

  it('emite close al hacer click en el botón de cerrar', async () => {
    const wrapper = mount(CorporateIpv6ManagerModal);
    const closeBtn = wrapper.find('.btn-close');
    await closeBtn.trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('permite registrar una asignación IPv6 corporativa', async () => {
    const ipamStore = useIpamStore();
    ipamStore.vrfs = [{ id: 'vrf-01', name: 'default', rd: '65000:1', tenant_id: 't-1' } as any];
    const createSpy = vi.spyOn(ipamStore, 'createPrefix').mockResolvedValue({} as any);

    const wrapper = mount(CorporateIpv6ManagerModal);
    await wrapper.find('#corp-client').setValue('Banco Central');
    await wrapper.find('#corp-contract').setValue('RIF-J-0000000-1');
    await wrapper.find('form').trigger('submit');

    expect(createSpy).toHaveBeenCalled();
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
