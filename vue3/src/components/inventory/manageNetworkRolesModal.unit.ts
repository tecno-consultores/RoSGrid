// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ManageNetworkRolesModal from './ManageNetworkRolesModal.vue';
import { useInventoryStore } from '@/stores/useInventoryStore';

describe('ManageNetworkRolesModal.vue — Personalización de Roles de Red', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('no es visible en el DOM cuando isOpen es false', () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: false },
    });
    expect(wrapper.find('.modal-backdrop').exists()).toBe(false);
  });

  it('renderiza título, descripción y estructura de campos alineados cuando isOpen es true', () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    expect(wrapper.find('#manage-roles-title').text()).toContain('Personalización de Roles de Red');
    expect(wrapper.find('.role-form').exists()).toBe(true);
    expect(wrapper.find('.form-row').exists()).toBe(true);
    expect(wrapper.find('#new-role-input').exists()).toBe(true);
    expect(wrapper.find('#new-role-desc').exists()).toBe(true);
    expect(wrapper.find('.btn-primary').exists()).toBe(true);
    expect(wrapper.find('.help-text').text()).toContain('MAYÚSCULAS_CON_GUIONES');
  });

  it('emite evento "close" al hacer clic en el botón cerrar o en el backdrop', async () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const closeBtn = wrapper.find('.btn-close');
    await closeBtn.trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();

    const backdrop = wrapper.find('.modal-backdrop');
    await backdrop.trigger('click');
    expect(wrapper.emitted('close')?.length).toBe(2);
  });

  it('normaliza la entrada del nuevo rol a mayúsculas y guiones bajos', async () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const input = wrapper.find('#new-role-input');
    await input.setValue('iot gateway branch 1!');
    expect((input.element as HTMLInputElement).value).toBe('IOT_GATEWAY_BRANCH_1');
  });

  it('muestra error de validación cuando el nombre del rol está vacío', async () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const form = wrapper.find('.role-form');
    await form.trigger('submit.prevent');

    expect(wrapper.find('.alert--error').exists()).toBe(true);
    expect(wrapper.find('.alert--error').text()).toContain('obligatorio');
  });

  it('muestra error cuando el rol ya existe en roles estándar o personalizados', async () => {
    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const input = wrapper.find('#new-role-input');
    await input.setValue('CORE');

    const form = wrapper.find('.role-form');
    await form.trigger('submit.prevent');

    expect(wrapper.find('.alert--error').exists()).toBe(true);
    expect(wrapper.find('.alert--error').text()).toContain('ya existe');
  });

  it('crea exitosamente un rol personalizado llamando al store y limpia los campos', async () => {
    const inventoryStore = useInventoryStore();
    const createSpy = vi.spyOn(inventoryStore, 'createCustomRole').mockResolvedValueOnce();

    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    await wrapper.find('#new-role-input').setValue('WAN_SDWAN');
    await wrapper.find('#new-role-desc').setValue('SD-WAN multiproveedor');
    await wrapper.find('.role-form').trigger('submit.prevent');
    await flushPromises();

    expect(createSpy).toHaveBeenCalledWith('WAN_SDWAN', 'SD-WAN multiproveedor');
    expect(wrapper.find('.alert--success').exists()).toBe(true);
    expect(wrapper.find('.alert--success').text()).toContain('creado exitosamente');
    expect((wrapper.find('#new-role-input').element as HTMLInputElement).value).toBe('');
  });

  it('maneja error devuelto por la API al crear rol', async () => {
    const inventoryStore = useInventoryStore();
    vi.spyOn(inventoryStore, 'createCustomRole').mockRejectedValueOnce({
      response: { data: { detail: 'Conflicto de unicidad en tenant' } },
    });

    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    await wrapper.find('#new-role-input').setValue('REDUNDANT_BGP');
    await wrapper.find('.role-form').trigger('submit.prevent');
    await flushPromises();

    expect(wrapper.find('.alert--error').text()).toContain('Conflicto de unicidad');
  });

  it('elimina un rol personalizado cuando el usuario confirma en el diálogo', async () => {
    const inventoryStore = useInventoryStore();
    inventoryStore.customRoles = [
      {
        id: 'cr-custom-1',
        role_name: 'CUSTOM_TEST',
        description: 'Rol para testing',
      },
    ];
    inventoryStore.networkRoles = [...inventoryStore.networkRoles, 'CUSTOM_TEST'];

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const deleteSpy = vi.spyOn(inventoryStore, 'deleteCustomRole').mockResolvedValueOnce();

    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const deleteBtn = wrapper.find('.btn-delete-role');
    expect(deleteBtn.exists()).toBe(true);
    await deleteBtn.trigger('click');
    await flushPromises();

    expect(deleteSpy).toHaveBeenCalledWith('CUSTOM_TEST');
    expect(wrapper.find('.alert--success').text()).toContain('eliminado correctamente');
  });

  it('cancela la eliminación si el usuario cancela en el confirm', async () => {
    const inventoryStore = useInventoryStore();
    inventoryStore.customRoles = [
      {
        id: 'cr-custom-1',
        role_name: 'CUSTOM_TEST',
        description: 'Rol para testing',
      },
    ];
    inventoryStore.networkRoles = [...inventoryStore.networkRoles, 'CUSTOM_TEST'];

    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const deleteSpy = vi.spyOn(inventoryStore, 'deleteCustomRole');

    const wrapper = mount(ManageNetworkRolesModal, {
      props: { isOpen: true },
    });

    const deleteBtn = wrapper.find('.btn-delete-role');
    await deleteBtn.trigger('click');
    await flushPromises();

    expect(deleteSpy).not.toHaveBeenCalled();
  });
});
