// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import type { SystemRole, TenantFeatureFlags } from '@/types';
import { useAuthStore } from '@/stores/useAuthStore';
import { useWebFigStore } from '@/stores/useWebFigStore';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      requiresAuth: false,
      title: 'Iniciar Sesión — RoSGrid',
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
    },
  },
  {
    path: '/inventory',
    alias: ['/inventory/routers'],
    name: 'RouterInventory',
    component: () => import('@/views/RouterInventoryView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Inventario de Equipos MikroTik — RoSGrid',
    },
  },
  {
    path: '/inventory/cves',
    name: 'FleetCveMatrix',
    component: () => import('@/views/FleetCveMatrix.vue'),
    meta: {
      requiresAuth: true,
      title: 'Matriz de Vulnerabilidades CVE — RoSGrid',
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
    },
  },
  {
    path: '/audit-logs',
    name: 'ImmutableAuditLogs',
    component: () => import('@/views/ImmutableAuditLogsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Consola Forense WORM — RoSGrid',
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
    },
  },
  {
    path: '/admin/tenants',
    name: 'TenantsManagement',
    component: () => import('@/views/admin/TenantsManagementView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Administración de Empresas — RoSGrid',
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
    },
  },
  {
    path: '/subscribers/map',
    name: 'SubscribersMap',
    component: () => import('@/views/SubscribersMapView.vue'),
    meta: {
      requiresAuth: true,
      requiredFeature: 'isp_module_enabled',
      title: 'Mapa Exclusivo de Clientes y ONUs — RoSGrid',
    },
  },
  {
    path: '/enterprise/compliance',
    name: 'EnterpriseCompliance',
    component: () => import('@/views/EnterpriseComplianceView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Gestión de Flota & Cumplimiento Normativo — RoSGrid',
    },
  },
  {
    path: '/topology/l2',
    alias: ['/topology'],
    name: 'L2Topology',
    component: () => import('@/views/L2TopologyView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Topología Física Layer 2 — RoSGrid',
    },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  // 1. Actualización de título para WCAG 2.1 AA y SEO
  if (to.meta.title && typeof document !== 'undefined') {
    document.title = String(to.meta.title);
  }

  const authStore = useAuthStore();
  const requiresAuth = to.meta.requiresAuth !== false;

  // 2. Control de autenticación
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

  // 5. Sincronización automática de pestañas de WebFig
  if (to.path.includes('/webfig/') && to.name) {
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

  next();
});
