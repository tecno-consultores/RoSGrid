// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { createRouter, createWebHistory, type RouteRecordRaw, type RouteLocationNormalized } from 'vue-router';
import type { SystemRole, TenantFeatureFlags } from '@/types';
import { useAuthStore } from '@/stores/useAuthStore';
import { useWebFigStore } from '@/stores/useWebFigStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useI18n } from '@/composables/useI18n';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      requiresAuth: false,
      title: 'Iniciar Sesión — RoSGrid',
      titleKey: 'routes.login',
    },
  },
  {
    path: '/',
    alias: ['/dashboard'],
    name: 'DashboardRoot',
    component: () => import('@/views/DashboardHomeView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Centro de Mando — RoSGrid',
      titleKey: 'routes.dashboard',
    },
  },
  {
    path: '/inventory',
    alias: ['/inventory/routers'],
    name: 'RouterInventory',
    component: () => import('@/views/RouterInventoryView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Inventario de Equipos — RoSGrid',
      titleKey: 'routes.inventory',
    },
  },
  {
    path: '/inventory/cves',
    alias: ['/fleet/cve-matrix'],
    name: 'FleetCveMatrix',
    component: () => import('@/views/FleetCveMatrix.vue'),
    meta: {
      requiresAuth: true,
      title: 'Matriz de Vulnerabilidades CVE — RoSGrid',
      titleKey: 'routes.cve_matrix',
    },
  },
  {
    path: '/routers/:routerId/webfig',
    name: 'RouterWebFig',
    component: () => import('@/views/RouterWebFigLayout.vue'),
    meta: {
      requiresAuth: true,
      title: 'Consola WebFig — RoSGrid',
    },
    children: [
      {
        path: '',
        redirect: (to) => `/routers/${to.params.routerId}/webfig/live`,
      },
      {
        path: 'live',
        name: 'RouterLiveDashboard',
        component: () => import('@/views/RouterLiveDashboardView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Dashboard en Vivo — RoSGrid',
          tabLabel: 'Dashboard en Vivo',
          tabIcon: '📊',
        },
      },
      {
        path: 'interfaces',
        name: 'InterfacesAndSfp',
        component: () => import('@/views/InterfacesAndSfpView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Interfaces y SFP DDM — RoSGrid',
          tabLabel: 'Interfaces & SFP',
          tabIcon: '🔌',
        },
      },
      {
        path: 'bridge',
        name: 'BridgeSwitching',
        component: () => import('@/views/BridgeView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Bridge y Switching Capa 2 — RoSGrid',
          tabLabel: 'Bridge',
          tabIcon: '🌉',
        },
      },
      {
        path: 'wireguard',
        name: 'WireGuardVpn',
        component: () => import('@/views/WireGuardVpnView.vue'),
        meta: {
          requiresAuth: true,
          title: 'WireGuard VPN — RoSGrid',
          tabLabel: 'WireGuard',
          tabIcon: '🛡️',
        },
      },
      {
        path: 'ip',
        name: 'IpAddressesAndDhcp',
        component: () => import('@/views/IpAddressesAndDhcpView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Módulo IP & DHCP — RoSGrid',
          tabLabel: 'IP & DHCP',
          tabIcon: '🔢',
        },
      },
      {
        path: 'ipv6',
        name: 'Ipv6DualStack',
        component: () => import('@/views/Ipv6DualStackView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Pila Dual IPv6 — RoSGrid',
          tabLabel: 'IPv6',
          tabIcon: '🌐',
        },
      },
      {
        path: 'firewall',
        name: 'FirewallRules',
        component: () => import('@/views/FirewallRulesView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Reglas de Firewall — RoSGrid',
          tabLabel: 'Firewall',
          tabIcon: '🛡️',
        },
      },
      {
        path: 'routing',
        name: 'RoutingBgpOspf',
        component: () => import('@/views/RoutingBgpOspfView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Routing v7 BGP / OSPF — RoSGrid',
          tabLabel: 'Routing',
          tabIcon: '🌐',
        },
      },
      {
        path: 'ppp',
        name: 'PppAndQueues',
        component: () => import('@/views/PppAndQueuesView.vue'),
        meta: {
          requiresAuth: true,
          title: 'PPPoE y Colas — RoSGrid',
          tabLabel: 'PPP & Colas',
          tabIcon: '⚡',
        },
      },
      {
        path: 'tools',
        name: 'LiveToolsDiagnostics',
        component: () => import('@/views/LiveToolsDiagnosticsView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Herramientas y Diagnóstico — RoSGrid',
          tabLabel: 'Herramientas',
          tabIcon: '🛠️',
        },
      },
      {
        path: 'layer2/:rosPath(.*)',
        name: 'DynamicLayer2Resource',
        component: () => import('@/views/DynamicLayer2ResourceView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Recurso Capa 2 — RoSGrid',
          tabLabel: 'Capa 2',
          tabIcon: '⚙️',
        },
      },
      {
        path: 'backups',
        name: 'RouterBackupsGitDiff',
        component: () => import('@/views/RscGitDiffViewer.vue'),
        meta: {
          requiresAuth: true,
          title: 'Respaldos y Comparador Diff — RoSGrid',
          tabLabel: 'Respaldos',
          tabIcon: '💾',
        },
      },
      {
        path: 'syslog',
        name: 'RouterSyslogLive',
        component: () => import('@/views/RouterSyslogTerminalView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Syslog Live — RoSGrid',
          tabLabel: 'Syslog Live',
          tabIcon: '📜',
        },
      },
    ],
  },
  {
    path: '/approvals',
    alias: ['/operations/approvals'],
    name: 'ApprovalsInbox',
    component: () => import('@/views/ApprovalsInboxView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Bandeja Maker-Checker — RoSGrid',
      titleKey: 'routes.approvals',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3'],
    },
  },
  {
    path: '/backups',
    name: 'RscGitDiff',
    component: () => import('@/views/RscGitDiffViewer.vue'),
    meta: {
      requiresAuth: true,
      title: 'Respaldos y Comparador Diff — RoSGrid',
      titleKey: 'routes.diff_backups',
      requiredFeature: 'nightly_backups_enabled',
    },
  },
  {
    path: '/bulk-ops',
    name: 'BulkOperations',
    component: () => import('@/views/BulkOperationsAndUpdatesView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Operaciones Masivas y Actualizaciones — RoSGrid',
      titleKey: 'routes.bulk_ops',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
    },
  },
  {
    path: '/noc-wallboard',
    name: 'NocWallboard',
    component: () => import('@/views/NocWallboardView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Wallboard NOC 24/7 — RoSGrid',
      titleKey: 'routes.noc_wallboard',
    },
  },
  {
    path: '/audit-logs',
    alias: ['/audit'],
    name: 'ImmutableAuditLogs',
    component: () => import('@/views/ImmutableAuditLogsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Consola Forense WORM — RoSGrid',
      titleKey: 'routes.audit_logs',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'AUDITOR', 'SECURITY_OFFICER'],
    },
  },
  {
    path: '/inventory/maintenance-windows',
    name: 'MaintenanceWindows',
    component: () => import('@/views/MaintenanceWindowsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Ventanas de Mantenimiento — RoSGrid',
      titleKey: 'routes.maintenance_windows',
    },
  },
  {
    path: '/admin/tenants',
    name: 'TenantsManagement',
    component: () => import('@/views/admin/TenantsManagementView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Administración de Empresas — RoSGrid',
      titleKey: 'routes.tenants',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
  },
  {
    path: '/admin/tenants/:tenantId/modules',
    name: 'TenantModulesStudio',
    component: () => import('@/views/admin/TenantModulesStudioView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Módulos y Capacidades de Red — RoSGrid',
      titleKey: 'routes.tenant_modules',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
  },
  {
    path: '/users',
    alias: '/admin/users',
    name: 'UsersAndPermissions',
    component: () => import('@/views/UsersAndPermissionsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Usuarios y Matriz RBAC — RoSGrid',
      titleKey: 'routes.users_rbac',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
  },
  {
    path: '/sessions',
    alias: '/admin/active-sessions',
    name: 'ActiveSessionsKillSwitch',
    component: () => import('@/views/ActiveSessionsKillSwitchView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Sesiones Activas y Kill-Switch — RoSGrid',
      titleKey: 'routes.active_sessions',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR'],
    },
  },
  {
    path: '/ipam',
    name: 'IpamManagement',
    component: () => import('@/views/IpamManagementView.vue'),
    meta: {
      requiresAuth: true,
      title: 'IPAM Dual-Stack Universal & Clientes — RoSGrid',
      titleKey: 'routes.ipam',
    },
  },
  {
    path: '/field-ops',
    name: 'FieldTechOperations',
    component: () => import('@/views/FieldTechOperationsView.vue'),
    meta: {
      requiresAuth: true,
      requiredFeature: 'isp_module_enabled',
      title: 'Operaciones de Campo & Toolkit — RoSGrid',
      titleKey: 'routes.field_ops',
    },
  },
  {
    path: '/subscribers/map',
    name: 'SubscribersMap',
    component: () => import('@/views/SubscribersMapView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Mapa de Red & Clientes — RoSGrid',
      titleKey: 'routes.subscribers_map',
    },
  },
  {
    path: '/enterprise/compliance',
    alias: ['/compliance', '/fleet/compliance'],
    name: 'EnterpriseCompliance',
    component: () => import('@/views/EnterpriseComplianceView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Gestión de Flota & Cumplimiento Normativo — RoSGrid',
      titleKey: 'routes.enterprise_compliance',
    },
  },
  {
    path: '/topology/l2',
    alias: ['/topology', '/network/topology-l2'],
    name: 'L2Topology',
    component: () => import('@/views/L2TopologyView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Topología Física Layer 2 — RoSGrid',
      titleKey: 'routes.l2_topology',
    },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

function syncWebFigTab(to: RouteLocationNormalized): void {
  if (!to.path.includes('/webfig/') || !to.name) {
    return;
  }
  const webFigStore = useWebFigStore();
  const routerId = String(to.params.routerId || '');
  const tabId = String(to.name);
  const label = String(to.meta.tabLabel || to.name);
  const icon = String(to.meta.tabIcon || '📄');
  const isDashboard = tabId === 'RouterLiveDashboard';

  webFigStore.openOrFocusTab({
    tabId,
    routeName: String(to.name),
    label,
    icon,
    params: { routerId },
    closable: !isDashboard,
  });
}

function resolveBaseRouteTitle(to: RouteLocationNormalized): string {
  const titleKey = to.meta.titleKey as string | undefined;
  if (titleKey) {
    const { t } = useI18n();
    return `${t(titleKey)} — RoSGrid`;
  }
  if (to.meta.title) {
    return String(to.meta.title);
  }
  return typeof document !== 'undefined' ? document.title : 'RoSGrid';
}

function updateDocumentTitleWithRouterContext(to: RouteLocationNormalized): void {
  if (typeof document === 'undefined') return;
  const baseTitle = resolveBaseRouteTitle(to);
  const routerIdParam = to.params.routerId ? String(to.params.routerId) : '';
  if (!routerIdParam) {
    document.title = baseTitle;
    return;
  }

  const inventoryStore = useInventoryStore();
  const webFigStore = useWebFigStore();
  const matchedRouter =
    inventoryStore.routers.find((r) => r.id === routerIdParam) ||
    (webFigStore.currentRouter?.id === routerIdParam ? webFigStore.currentRouter : null);

  if (!matchedRouter) {
    document.title = baseTitle;
    return;
  }

  const routerName = matchedRouter.display_name || routerIdParam;
  const routerIp = matchedRouter.ip_address || '';
  const prefix = routerIp ? `[${routerName} · ${routerIp}] ` : `[${routerName}] `;
  document.title = `${prefix}${baseTitle}`;
}

router.beforeEach((to, _from, next) => {
  // 1. Actualización de título para WCAG 2.1 AA, SEO y Contexto de Router Multi-Pestaña (Hito 27.15)
  updateDocumentTitleWithRouterContext(to);

  const authStore = useAuthStore();
  const requiresAuth = to.meta.requiresAuth !== false;

  // 2. Control de autenticación y prevención de bucle infinito en expiración de sesión
  const forcedLogoutReasons = new Set([
    'session_expired',
    'session_revoked',
    'killed_by_admin',
    'SESSION_KILLED',
    'unauthorized',
  ]);
  if (
    to.path === '/login' &&
    typeof to.query.reason === 'string' &&
    forcedLogoutReasons.has(to.query.reason) &&
    authStore.isAuthenticated
  ) {
    authStore.clearAuth();
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    return next({ path: '/inventory' });
  }

  // 3. Reglas especiales RBAC por rol
  const role = authStore.currentRole;
  if (role === 'NOC_MONITOR' && to.path !== '/noc-wallboard') {
    return next({ path: '/noc-wallboard' });
  }

  // 4. Verificación de allowedRoles declarados en la ruta
  const allowed = to.meta.allowedRoles as SystemRole[] | undefined;
  if (allowed && role && !allowed.includes(role)) {
    return next({ path: '/inventory' });
  }

  // 5. Verificación de flags de características del Tenant (Subtarea 16.4)
  const requiredFeature = to.meta.requiredFeature as keyof TenantFeatureFlags | undefined;
  if (requiredFeature && !authStore.isFeatureEnabled(requiredFeature)) {
    return next({ path: '/inventory' });
  }

  // 6. Sincronización automática de pestañas de WebFig
  syncWebFigTab(to);

  next();
});
