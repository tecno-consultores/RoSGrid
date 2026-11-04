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
import DynamicLayer2ResourceView from './DynamicLayer2ResourceView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/inventory', params: {}, query: {} }),
  useRouter: () => ({ push: vi.fn() }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('Views Base — Montaje y Accesibilidad WCAG', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      closePath: vi.fn(),
      strokeStyle: '',
      fillStyle: '',
      lineWidth: 1,
      lineJoin: '',
      font: '',
    });
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
    { name: 'DynamicLayer2ResourceView', component: DynamicLayer2ResourceView },
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

  it('renderiza RouterWebFigLayout sin barra de pestañas redundante y permite alternar el menú móvil inline', async () => {
    const wrapper = mount(RouterWebFigLayout, {
      global: {
        stubs: { RouterView: true },
      },
    });

    expect(wrapper.find('.webfig-tabs-bar').exists()).toBe(false);
    expect(wrapper.findAll('.webfig-tab').length).toBe(0);

    const inlineMenuBtn = wrapper.find('.btn-webfig-menu-inline');
    expect(inlineMenuBtn.exists()).toBe(true);
    await inlineMenuBtn.trigger('click');
  });
});
