// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RouterInventoryView from '../RouterInventoryView.vue';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

const mockPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
  useRoute: () => ({ query: {} }),
}));

describe('RouterInventoryView.vue — Inventario y Modos Tabla, Mapa y Dividido', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    mockPush.mockReset();
    vi.useFakeTimers();

    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'admin-1',
      username: 'root_admin',
      email: 'root@rosgrid.local',
      tenant_id: 't-corp',
      tenant_slug: 'corp',
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('monta la vista, alterna modos de visualización y filtra routers', async () => {
    const inventoryStore = useInventoryStore();
    inventoryStore.setRouters([
      {
        id: 'r-01',
        tenant_id: 't-1',
        display_name: 'CCR2004-Edge-1',
        ros_identity: 'Edge1',
        ip_address: '10.0.0.1',
        api_port: 8728,
        ros_version: '7.18',
        model: 'CCR2004-1G-12S+2XS',
        serial_number: 'SN123456',
        network_role: 'EDGE_BGP',
        admin_state: 'PRODUCTION',
        is_reachable: true,
        latitude: 10.48,
        longitude: -66.9,
      },
      {
        id: 'r-02',
        tenant_id: 't-1',
        display_name: 'RB4011-Tower-2',
        ros_identity: 'Tower2',
        ip_address: '10.0.0.2',
        api_port: 8728,
        ros_version: '7.18',
        network_role: 'TOWER_AP',
        admin_state: 'MAINTENANCE',
        is_reachable: false,
        ssl_trust_status: 'FINGERPRINT_MISMATCH',
        latitude: 10.1,
        longitude: -68.0,
      },
    ]);

    const wrapper = mount(RouterInventoryView, {
      global: {
        stubs: {
          RgDataTable: {
            template: `
              <div class="rg-datatable-stub">
                <slot name="actions" :row="filteredRouters[0]" />
              </div>
            `,
            props: ['columns', 'rows'],
            computed: {
              filteredRouters() {
                return (this as unknown as { rows: unknown[] }).rows;
              },
            },
          },
          OsmRouterMap: true,
          CsvOnboardingWizardModal: true,
          VaultRevealModal: true,
        },
      },
    });

    expect(wrapper.find('h1').text()).toContain('Inventario de Equipos');

    // Conmutar modos de vista
    const toggleButtons = wrapper.findAll('.btn-toggle');
    await toggleButtons[1].trigger('click'); // Split
    expect(wrapper.find('.inventory-content--split').exists()).toBe(true);

    await toggleButtons[2].trigger('click'); // Map
    expect(wrapper.find('.inventory-content--map-only').exists()).toBe(true);

    await toggleButtons[0].trigger('click'); // Table

    // Filtros
    const searchInput = wrapper.find('#inv-search');
    await searchInput.setValue('CCR2004');

    const roleSelect = wrapper.find('#inv-role');
    await roleSelect.setValue('EDGE_BGP');

    const adminSelect = wrapper.find('#inv-admin-state');
    await adminSelect.setValue('PRODUCTION');

    const healthSelect = wrapper.find('#inv-operational');
    await healthSelect.setValue('ONLINE');
    await healthSelect.setValue('OFFLINE');
    await healthSelect.setValue('SSL_MISMATCH');
    await healthSelect.setValue('ALL');

    // WebFig
    await wrapper.find('.btn-row-action--webfig').trigger('click');
    expect(mockPush).toHaveBeenCalledWith('/routers/r-01/webfig/live');

    // Bóveda
    await wrapper.find('.btn-row-action--vault').trigger('click');
    expect(wrapper.findComponent({ name: 'VaultRevealModal' }).exists()).toBe(true);

    // Mapa focus
    await wrapper.find('.btn-row-action--map').trigger('click');
    expect(wrapper.find('.inventory-content--split').exists()).toBe(true);

    // Autodescubrimiento con éxito
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    await wrapper.find('.btn-row-action--tofu').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--success').text()).toContain('Autodescubrimiento TOFU');

    // Avanzar reloj para limpiar mensaje
    vi.advanceTimersByTime(5000);
    await flushPromises();
    expect(wrapper.find('.banner--success').exists()).toBe(false);

    // Autodescubrimiento con error
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      message: 'Timeout de descubrimiento',
    });
    await wrapper.find('.btn-row-action--tofu').trigger('click');
    await flushPromises();
    expect(wrapper.find('.banner--error').text()).toContain('Timeout de descubrimiento');

    // Modal de CSV
    await wrapper.find('.btn-import-csv').trigger('click');
    const csvModal = wrapper.findComponent({ name: 'CsvOnboardingWizardModal' });
    if (csvModal.exists()) {
      csvModal.vm.$emit('imported', 5);
      await flushPromises();
      expect(wrapper.find('.banner--success').text()).toContain('Se importaron 5 routers');

      // Avanzar reloj para limpiar mensaje de importación
      vi.advanceTimersByTime(5000);
      await flushPromises();
      expect(wrapper.find('.banner--success').exists()).toBe(false);

      csvModal.vm.$emit('close');
    }

    const vaultModal = wrapper.findComponent({ name: 'VaultRevealModal' });
    if (vaultModal.exists()) {
      vaultModal.vm.$emit('close');
    }
  });
});
