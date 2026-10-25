// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgTenantSwitcher from './RgTenantSwitcher.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useNocEventsStore } from '@/stores/useNocEventsStore';
import { http } from '@/api/httpClient';

describe('RgTenantSwitcher.vue — Conmutador Rápido de Contexto de Tenant', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('muestra etiqueta estática no interactiva para roles que no son SUPERADMIN_GLOBAL', () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'TENANT_ADMIN';
    authStore.tenantSlug = 'empresa-demo';

    const wrapper = mount(RgTenantSwitcher);
    expect(wrapper.find('.tenant-badge').exists()).toBe(true);
    expect(wrapper.find('.tenant-switcher-btn').exists()).toBe(false);
    expect(wrapper.text()).toContain('empresa-demo');
  });

  it('muestra botón interactivo desplegable para SUPERADMIN_GLOBAL', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    authStore.tenantSlug = 'sistemas';

    const wrapper = mount(RgTenantSwitcher);
    const trigger = wrapper.find('.tenant-switcher-btn');
    expect(trigger.exists()).toBe(true);
    expect(trigger.text()).toContain('sistemas');
  });

  it('despliega popover al hacer clic, lista empresas y permite filtrar con el buscador', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    authStore.tenantSlug = 'sistemas';

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: [
        { id: 't-1', name: 'Sistemas Central', slug: 'sistemas', status: 'ACTIVE' },
        { id: 't-2', name: 'Fibra Norte', slug: 'fibra-norte', status: 'ACTIVE' },
        { id: 't-3', name: 'Empresa Inactiva', slug: 'inactiva', status: 'SUSPENDED' },
      ],
      headers: new Headers(),
    });

    const wrapper = mount(RgTenantSwitcher);
    const trigger = wrapper.find('.tenant-switcher-btn');

    // Abre el desplegable
    await trigger.trigger('click');
    await flushPromises();

    expect(wrapper.find('.tenant-switcher-popover').exists()).toBe(true);
    const items = wrapper.findAll('.tenant-option');
    // Solo las 2 activas deben listarse
    expect(items.length).toBe(2);

    // Filtrar con el buscador
    const searchInput = wrapper.find('.search-input');
    await searchInput.setValue('fibra');
    await flushPromises();

    const filtered = wrapper.findAll('.tenant-option');
    expect(filtered.length).toBe(1);
    expect(filtered[0].text()).toContain('Fibra Norte');
  });

  it('conmuta de tenant exitosamente actualizando authStore, inventario y eventos', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'SUPERADMIN_GLOBAL';
    authStore.tenantSlug = 'sistemas';

    const inventoryStore = useInventoryStore();
    const nocStore = useNocEventsStore();

    const switchSpy = vi.spyOn(authStore, 'switchTenant').mockResolvedValue(true);

    const fetchRoutersSpy = vi.spyOn(inventoryStore, 'fetchRouters').mockResolvedValue();
    const fetchAuditSpy = vi.spyOn(nocStore, 'fetchRecentAuditLogs').mockResolvedValue();

    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: [
        { id: 't-1', name: 'Sistemas Central', slug: 'sistemas', status: 'ACTIVE' },
        { id: 't-2', name: 'Fibra Norte', slug: 'fibra-norte', status: 'ACTIVE' },
      ],
      headers: new Headers(),
    });

    const wrapper = mount(RgTenantSwitcher);
    await wrapper.find('.tenant-switcher-btn').trigger('click');
    await flushPromises();

    // Selecciona el segundo tenant
    const items = wrapper.findAll('.tenant-option');
    await items[1].trigger('click');
    await flushPromises();

    expect(switchSpy).toHaveBeenCalledWith('t-2');
    expect(fetchRoutersSpy).toHaveBeenCalledWith(true);
    expect(fetchAuditSpy).toHaveBeenCalledWith(true);
  });
});
