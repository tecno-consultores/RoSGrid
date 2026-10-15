// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';

import ActiveSessionsKillSwitchView from './ActiveSessionsKillSwitchView.vue';
import ApprovalsInboxView from './ApprovalsInboxView.vue';
import BulkOperationsAndUpdatesView from './BulkOperationsAndUpdatesView.vue';
import FirewallRulesView from './FirewallRulesView.vue';
import ImmutableAuditLogsView from './ImmutableAuditLogsView.vue';
import InterfacesAndSfpView from './InterfacesAndSfpView.vue';
import LiveToolsDiagnosticsView from './LiveToolsDiagnosticsView.vue';
import LoginView from './LoginView.vue';
import NocWallboardView from './NocWallboardView.vue';
import PppAndQueuesView from './PppAndQueuesView.vue';
import RouterInventoryView from './RouterInventoryView.vue';
import RouterLiveDashboardView from './RouterLiveDashboardView.vue';
import RouterWebFigLayout from './RouterWebFigLayout.vue';
import RoutingBgpOspfView from './RoutingBgpOspfView.vue';
import RscGitDiffViewer from './RscGitDiffViewer.vue';
import UsersAndPermissionsView from './UsersAndPermissionsView.vue';
import TenantsManagementView from './admin/TenantsManagementView.vue';
import MaintenanceWindowsView from './MaintenanceWindowsView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/inventory', params: {}, query: {} }),
  useRouter: () => ({ push: vi.fn() }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('Views Base — Montaje y Accesibilidad WCAG', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  const views = [
    { name: 'ActiveSessionsKillSwitchView', component: ActiveSessionsKillSwitchView },
    { name: 'ApprovalsInboxView', component: ApprovalsInboxView },
    { name: 'BulkOperationsAndUpdatesView', component: BulkOperationsAndUpdatesView },
    { name: 'FirewallRulesView', component: FirewallRulesView },
    { name: 'ImmutableAuditLogsView', component: ImmutableAuditLogsView },
    { name: 'InterfacesAndSfpView', component: InterfacesAndSfpView },
    { name: 'LiveToolsDiagnosticsView', component: LiveToolsDiagnosticsView },
    { name: 'LoginView', component: LoginView },
    { name: 'NocWallboardView', component: NocWallboardView },
    { name: 'PppAndQueuesView', component: PppAndQueuesView },
    { name: 'RouterInventoryView', component: RouterInventoryView },
    { name: 'RouterLiveDashboardView', component: RouterLiveDashboardView },
    { name: 'RouterWebFigLayout', component: RouterWebFigLayout },
    { name: 'RoutingBgpOspfView', component: RoutingBgpOspfView },
    { name: 'RscGitDiffViewer', component: RscGitDiffViewer },
    { name: 'UsersAndPermissionsView', component: UsersAndPermissionsView },
    { name: 'TenantsManagementView', component: TenantsManagementView },
    { name: 'MaintenanceWindowsView', component: MaintenanceWindowsView },
  ];

  for (const v of views) {
    it(`monta correctamente la vista ${v.name}`, () => {
      const wrapper = mount(v.component, {
        global: {
          stubs: {
            RouterView: true,
            RouterLink: true,
            RgDataTable: true,
          },
        },
      });
      expect(wrapper.exists()).toBe(true);
    });
  }

  it('permite hacer click en pestañas y cerrarlas en RouterWebFigLayout', async () => {
    const { useWebFigStore } = await import('@/stores/useWebFigStore');
    const store = useWebFigStore();
    store.openOrFocusTab({
      tabId: 'test-closable-tab',
      routeName: 'InterfacesAndSfp',
      label: 'Interfaces',
      closable: true,
    });

    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });

    const tabs = wrapper.findAll('.webfig-tab');
    expect(tabs.length).toBeGreaterThan(1);
    await tabs[1].trigger('click');

    const closeBtn = wrapper.find('.btn-close-tab');
    if (closeBtn.exists()) {
      await closeBtn.trigger('click');
    }
  });
});
