# Especificación Técnica 64: Aplicación Estricta de Visibilidad RBAC en Interfaz (Zero 403 Dead-Ends) & Paridad de Roles de Lectura

**Estado:** COMPLETADO AL 100% Y CERTIFICADO EN DOCKER EFÍMERO  
**Hito Asociado:** Hito 28 — Sub-tarea `28.9`  
**Dominios Afectados:**
- Frontend Pinia Auth Store: `vue3/src/stores/useAuthStore.ts`
- Frontend Global Sidebar Navigation: `vue3/src/components/common/RgResponsiveShell.vue`
- Frontend Enterprise Compliance & Security Suite: `vue3/src/views/EnterpriseComplianceView.vue`
- Frontend Command Center, Inventory & WebFig Sidebar: `vue3/src/views/DashboardHomeView.vue`, `vue3/src/views/RouterInventoryView.vue`, `vue3/src/components/webfig/RouterSidebarMenu.vue`
- Backend Read-Only Role Parity: `fastapi/src/api/v1/sdwan.py`, `fastapi/src/api/v1/switching.py`, `fastapi/src/api/v1/sla.py`, `fastapi/src/api/v1/wifi.py`
- Pruebas Unitarias 11X: `vue3/src/stores/useAuthStore.unit.ts`, `vue3/src/views/enterpriseComplianceView.unit.ts`

---

## 1. Diagnóstico de Causa Raíz (RCA)

Durante las pruebas UAT con una cuenta de nivel `SUPPORT_L1` (`prueba`), al navegar a **🛡️ Flota & Seguridad** (`/enterprise/compliance`), la interfaz mostró el banner rojo de error HTTP 403 (`"No tienes los privilegios requeridos para ejecutar esta acción"`) y además presentó en la barra lateral enlaces a vistas restringidas (`📦 Respaldos Diff`, `⚡ Acciones Masivas`, `👥 Usuarios & RBAC`):

1. **`canUseUserFeature` en `vue3/src/stores/useAuthStore.ts` carecía de la matriz base `POLICY_MATRIX` (11 roles × 30 acciones):**
   - La función `canUseUserFeature(actionKey, requireWrite)` solo tenía casos especiales para `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `AUDITOR` y `NOC_MONITOR`, retornando `true` por defecto para `SUPPORT_L1`, `SUPPORT_L2`, `SUPPORT_L3`, `SUPERVISOR`, `FIELD_TECH` e `INVENTORY_MANAGER` cuando el usuario no tenía un `feature_flags_override` explícito.
   - Además, los componentes de navegación y vistas (`RgResponsiveShell.vue`, `EnterpriseComplianceView.vue`, `DashboardHomeView.vue`, `RouterInventoryView.vue`, `RouterSidebarMenu.vue`) no invocaban `canUseUserFeature` para ocultar elementos con permiso `DENY` o botones de escritura con permiso `READ_ONLY`.
2. **Pestañas no filtradas por RBAC en `EnterpriseComplianceView.vue`:**
   - `availableTabs` solo filtraba por Feature Flags del tenant (`!tab.flag || authStore.isFeatureEnabled(tab.flag)`), dejando visibles para `SUPPORT_L1` las pestañas `Config Drift & Baselines` (`drift`), `CIS Hardening` (`cis`), `Auditoría WORM` (`audit`) y `Canales de Alerta & Notificación` (`notifications`), y seleccionando `drift` como pestaña inicial por defecto, lo que disparaba inmediatamente `GET /api/v1/compliance/config-drift/{router_id}` → `HTTP 403 Forbidden`.
3. **Desalineación puntual entre `POLICY_MATRIX` y las tuplas `_READ_ROLES` en Backend (`sdwan.py`, `switching.py`, `sla.py`, `wifi.py`):**
   - En `fastapi/src/rbac/policy_matrix.py`, `SUPPORT_L1` y `AUDITOR` tienen `ENTERPRISE_SDWAN_SLA_ROGUEDHCP: READ_ONLY` y `WIFI_CAPSMAN_PROVISIONING: READ_ONLY` (también `FIELD_TECH` en Wi-Fi), pero `_SDWAN_READ_ROLES`, `_SWITCHING_READ_ROLES` y `_SLA_READ_ROLES` omitían `SystemRoleEnum.SUPPORT_L1` (y `AUDITOR` en SD-WAN/Switching).

---

## 2. Bloques Deterministas `Target` / `Replacement`

### 2.1. `vue3/src/stores/useAuthStore.ts` — Matriz Base `ROLE_POLICY_MATRIX` (11 Roles × 30 Acciones) en `canUseUserFeature`

#### Archivo: `vue3/src/stores/useAuthStore.ts`

**Target:**
```ts
  function canUseUserFeature(actionKey: string, requireWrite = false): boolean {
    if (!user.value || !currentRole.value) return false;
    const role = currentRole.value;
    if (role === 'SUPERADMIN_GLOBAL') return true;

    const userOverrides = user.value.feature_flags_override;
    if (userOverrides && actionKey in userOverrides) {
      const level = userOverrides[actionKey];
      if (level === 'DENY') return false;
      if (level === 'READ_ONLY') return !requireWrite;
      if (level === 'ALLOW' || level === 'MAKER_CHECKER') return true;
    }

    if (role === 'TENANT_ADMIN') {
      return actionKey !== 'TENANT_MANAGEMENT';
    }
    if (role === 'AUDITOR') {
      return !requireWrite;
    }
    if (role === 'NOC_MONITOR') {
      return !requireWrite && (actionKey === 'VIEW_OSM_MAP_NOC_CHARTS' || actionKey.startsWith('VIEW_'));
    }
    return true;
  }
```

**Replacement:**
```ts
  const ROLE_POLICY_MATRIX: Record<string, Record<string, 'ALLOW' | 'MAKER_CHECKER' | 'READ_ONLY' | 'DENY'>> = {
    SUPERADMIN_GLOBAL: {},
    TENANT_ADMIN: {
      TENANT_MANAGEMENT: 'DENY',
    },
    SUPERVISOR: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'READ_ONLY',
      REVEAL_VAULT_KEYS: 'DENY',
      WEBFIG_L2_UNIVERSAL: 'READ_ONLY',
      WEBFIG_L2_RPC_COMMANDS: 'MAKER_CHECKER',
    },
    SUPPORT_L3: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
    },
    SUPPORT_L2: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      ROUTER_INVENTORY_CSV: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'DENY',
      SCHEDULE_MAINTENANCE: 'MAKER_CHECKER',
      CRITICAL_NETWORK_ACTIONS: 'MAKER_CHECKER',
      REBOOT_SHUTDOWN: 'MAKER_CHECKER',
      WEBFIG_L2_UNIVERSAL: 'READ_ONLY',
      WEBFIG_L2_RPC_COMMANDS: 'MAKER_CHECKER',
      WEBFIG_L2_BULK_OPS: 'MAKER_CHECKER',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'MAKER_CHECKER',
      BULK_ACTIONS_UPGRADE_ROS: 'MAKER_CHECKER',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'READ_ONLY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'MAKER_CHECKER',
    },
    SUPPORT_L1: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      ROUTER_INVENTORY_CSV: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'DENY',
      SCHEDULE_MAINTENANCE: 'DENY',
      VIEW_OSM_MAP_NOC_CHARTS: 'ALLOW',
      LIVE_DIAGNOSTICS: 'ALLOW',
      L1_OPERATIONS: 'ALLOW',
      CONFIG_STANDARD_L1: 'MAKER_CHECKER',
      CRITICAL_NETWORK_ACTIONS: 'MAKER_CHECKER',
      REBOOT_SHUTDOWN: 'MAKER_CHECKER',
      WEBFIG_L2_UNIVERSAL: 'DENY',
      WEBFIG_L2_RPC_COMMANDS: 'DENY',
      WEBFIG_L2_BULK_OPS: 'DENY',
      WEBFIG_L2_EXPORT_RSC: 'DENY',
      MANUAL_BACKUP_DIFF_GIT: 'DENY',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'DENY',
      BULK_ACTIONS_UPGRADE_ROS: 'DENY',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
      IPAM_VRFS_PREFIXES_MGMT: 'READ_ONLY',
      SUBSCRIBERS_QOS_PROVISIONING: 'ALLOW',
      FIELD_OPS_OPTICAL_NAP_MGMT: 'READ_ONLY',
      BGP_LOOKING_GLASS_IPFIX: 'READ_ONLY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'DENY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'READ_ONLY',
      WIFI_CAPSMAN_PROVISIONING: 'READ_ONLY',
      TOPOLOGY_L2_CVE_SYSLOG_MCP: 'READ_ONLY',
    },
    FIELD_TECH: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      ROUTER_INVENTORY_CSV: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'DENY',
      SCHEDULE_MAINTENANCE: 'DENY',
      VIEW_OSM_MAP_NOC_CHARTS: 'ALLOW',
      LIVE_DIAGNOSTICS: 'ALLOW',
      L1_OPERATIONS: 'ALLOW',
      CONFIG_STANDARD_L1: 'DENY',
      CRITICAL_NETWORK_ACTIONS: 'DENY',
      REBOOT_SHUTDOWN: 'MAKER_CHECKER',
      WEBFIG_L2_UNIVERSAL: 'DENY',
      WEBFIG_L2_RPC_COMMANDS: 'DENY',
      WEBFIG_L2_BULK_OPS: 'DENY',
      WEBFIG_L2_EXPORT_RSC: 'DENY',
      MANUAL_BACKUP_DIFF_GIT: 'DENY',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'DENY',
      BULK_ACTIONS_UPGRADE_ROS: 'DENY',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
      IPAM_VRFS_PREFIXES_MGMT: 'READ_ONLY',
      SUBSCRIBERS_QOS_PROVISIONING: 'READ_ONLY',
      FIELD_OPS_OPTICAL_NAP_MGMT: 'ALLOW',
      BGP_LOOKING_GLASS_IPFIX: 'DENY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'DENY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'DENY',
      WIFI_CAPSMAN_PROVISIONING: 'READ_ONLY',
      TOPOLOGY_L2_CVE_SYSLOG_MCP: 'READ_ONLY',
    },
    INVENTORY_MANAGER: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      ROUTER_INVENTORY_CSV: 'ALLOW',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'ALLOW',
      SCHEDULE_MAINTENANCE: 'ALLOW',
      VIEW_OSM_MAP_NOC_CHARTS: 'ALLOW',
      LIVE_DIAGNOSTICS: 'DENY',
      L1_OPERATIONS: 'DENY',
      CONFIG_STANDARD_L1: 'DENY',
      CRITICAL_NETWORK_ACTIONS: 'DENY',
      REBOOT_SHUTDOWN: 'DENY',
      WEBFIG_L2_UNIVERSAL: 'DENY',
      WEBFIG_L2_RPC_COMMANDS: 'DENY',
      WEBFIG_L2_BULK_OPS: 'DENY',
      WEBFIG_L2_EXPORT_RSC: 'READ_ONLY',
      MANUAL_BACKUP_DIFF_GIT: 'ALLOW',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'DENY',
      BULK_ACTIONS_UPGRADE_ROS: 'DENY',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
      IPAM_VRFS_PREFIXES_MGMT: 'ALLOW',
      SUBSCRIBERS_QOS_PROVISIONING: 'DENY',
      FIELD_OPS_OPTICAL_NAP_MGMT: 'ALLOW',
      BGP_LOOKING_GLASS_IPFIX: 'DENY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'DENY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'DENY',
      WIFI_CAPSMAN_PROVISIONING: 'DENY',
      TOPOLOGY_L2_CVE_SYSLOG_MCP: 'READ_ONLY',
    },
    AUDITOR: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'READ_ONLY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'READ_ONLY',
      ROUTER_INVENTORY_CSV: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'DENY',
      SCHEDULE_MAINTENANCE: 'DENY',
      VIEW_OSM_MAP_NOC_CHARTS: 'ALLOW',
      LIVE_DIAGNOSTICS: 'DENY',
      L1_OPERATIONS: 'DENY',
      CONFIG_STANDARD_L1: 'DENY',
      CRITICAL_NETWORK_ACTIONS: 'DENY',
      REBOOT_SHUTDOWN: 'DENY',
      WEBFIG_L2_UNIVERSAL: 'READ_ONLY',
      WEBFIG_L2_RPC_COMMANDS: 'DENY',
      WEBFIG_L2_BULK_OPS: 'DENY',
      WEBFIG_L2_EXPORT_RSC: 'ALLOW',
      MANUAL_BACKUP_DIFF_GIT: 'READ_ONLY',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'DENY',
      BULK_ACTIONS_UPGRADE_ROS: 'DENY',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'ALLOW',
      IPAM_VRFS_PREFIXES_MGMT: 'READ_ONLY',
      SUBSCRIBERS_QOS_PROVISIONING: 'READ_ONLY',
      FIELD_OPS_OPTICAL_NAP_MGMT: 'READ_ONLY',
      BGP_LOOKING_GLASS_IPFIX: 'READ_ONLY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'READ_ONLY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'READ_ONLY',
      WIFI_CAPSMAN_PROVISIONING: 'READ_ONLY',
      TOPOLOGY_L2_CVE_SYSLOG_MCP: 'ALLOW',
    },
    NOC_MONITOR: {
      TENANT_MANAGEMENT: 'DENY',
      USER_MANAGEMENT: 'DENY',
      VIEW_ACTIVE_SESSIONS_KILLSWITCH: 'DENY',
      ROUTER_INVENTORY_CSV: 'DENY',
      REVEAL_VAULT_KEYS: 'DENY',
      TRIGGER_PASSWORD_ROTATION: 'DENY',
      SCHEDULE_MAINTENANCE: 'DENY',
      VIEW_OSM_MAP_NOC_CHARTS: 'ALLOW',
      LIVE_DIAGNOSTICS: 'DENY',
      L1_OPERATIONS: 'DENY',
      CONFIG_STANDARD_L1: 'DENY',
      CRITICAL_NETWORK_ACTIONS: 'DENY',
      REBOOT_SHUTDOWN: 'DENY',
      WEBFIG_L2_UNIVERSAL: 'DENY',
      WEBFIG_L2_RPC_COMMANDS: 'DENY',
      WEBFIG_L2_BULK_OPS: 'DENY',
      WEBFIG_L2_EXPORT_RSC: 'DENY',
      MANUAL_BACKUP_DIFF_GIT: 'DENY',
      RESTORE_BACKUP_CUSTOM_SCRIPT: 'DENY',
      BULK_ACTIONS_UPGRADE_ROS: 'DENY',
      APPROVE_MAKER_CHECKER: 'DENY',
      AUDIT_LOGS_QUERY: 'DENY',
      IPAM_VRFS_PREFIXES_MGMT: 'DENY',
      SUBSCRIBERS_QOS_PROVISIONING: 'DENY',
      FIELD_OPS_OPTICAL_NAP_MGMT: 'DENY',
      BGP_LOOKING_GLASS_IPFIX: 'READ_ONLY',
      ENTERPRISE_CIS_DRIFT_COMPLIANCE: 'DENY',
      ENTERPRISE_SDWAN_SLA_ROGUEDHCP: 'READ_ONLY',
      WIFI_CAPSMAN_PROVISIONING: 'DENY',
      TOPOLOGY_L2_CVE_SYSLOG_MCP: 'READ_ONLY',
    },
  };

  function canUseUserFeature(actionKey: string, requireWrite = false): boolean {
    if (!user.value || !currentRole.value) return false;
    const role = currentRole.value;
    if (role === 'SUPERADMIN_GLOBAL') return true;

    const userOverrides = user.value.feature_flags_override;
    if (userOverrides && actionKey in userOverrides) {
      const level = userOverrides[actionKey];
      if (level === 'DENY') return false;
      if (level === 'READ_ONLY') return !requireWrite;
      if (level === 'ALLOW' || level === 'MAKER_CHECKER') return true;
    }

    const rolePolicies = ROLE_POLICY_MATRIX[role];
    if (rolePolicies) {
      const policy = rolePolicies[actionKey] || 'ALLOW';
      if (policy === 'DENY') return false;
      if (policy === 'READ_ONLY') return !requireWrite;
      return true;
    }

    if (role === 'AUDITOR') {
      return !requireWrite;
    }
    if (role === 'NOC_MONITOR') {
      return !requireWrite && (actionKey === 'VIEW_OSM_MAP_NOC_CHARTS' || actionKey.startsWith('VIEW_'));
    }
    return true;
  }
```

---

### 2.2. `vue3/src/components/common/RgResponsiveShell.vue` — Filtrado RBAC de la Barra Lateral Global

#### Archivo: `vue3/src/components/common/RgResponsiveShell.vue`

**Target:**
```ts
      {
        name: 'ApprovalsInbox',
        path: '/approvals',
        label: t('nav.maker_checker', 'Maker-Checker'),
        icon: '🛡️',
        badge: nocStore.pendingApprovalsCount,
      },
      {
        name: 'IpamManagement',
        path: '/ipam',
        label: t('nav.ipam', 'IPAM'),
        icon: '🌐',
      },
    ];

    items.push({
      name: 'SubscribersMap',
      path: '/subscribers/map',
      label: t('nav.subscribers_map', 'Mapa de Clientes'),
      icon: '📍',
    });

    if (authStore.isFeatureEnabled('isp_module_enabled')) {
      items.push({
        name: 'FieldTechOperations',
        path: '/field-ops',
        label: t('nav.field_ops', 'Técnico de Campo'),
        icon: '🛠️',
      });
    }

    items.push({
      name: 'L2Topology',
      path: '/topology/l2',
      label: t('nav.l2_topology', 'Topología L2'),
      icon: '🗺️',
    });

    if (authStore.isFeatureEnabled('nightly_backups_enabled')) {
      items.push({
        name: 'RscGitDiff',
        path: '/backups',
        label: t('nav.backups_diff', 'Respaldos Diff'),
        icon: '📦',
      });
    }

    items.push(
      {
        name: 'BulkOperations',
        path: '/bulk-ops',
        label: t('nav.bulk_ops', 'Acciones Masivas'),
        icon: '⚡',
      },
      {
        name: 'UsersAndPermissions',
        path: '/users',
        label: t('nav.users_rbac', 'Usuarios & RBAC'),
        icon: '👥',
      },
    );

    if (authStore.currentRole === 'SUPERADMIN_GLOBAL' || authStore.currentRole === 'TENANT_ADMIN') {
      items.push({
        name: 'TenantsManagement',
        path: '/admin/tenants',
        label: t('nav.tenants', 'Empresas (Tenants)'),
        icon: '🏢',
      });
    }

    items.push({
      name: 'EnterpriseCompliance',
      path: '/enterprise/compliance',
      label: t('nav.compliance', 'Flota & Seguridad'),
      icon: '🛡️',
    });
```

**Replacement:**
```ts
    ];

    if (
      !authStore.user ||
      authStore.canUseUserFeature('APPROVE_MAKER_CHECKER', false) ||
      authStore.canUseUserFeature('CONFIG_STANDARD_L1', true) ||
      authStore.canUseUserFeature('REBOOT_SHUTDOWN', true)
    ) {
      items.push({
        name: 'ApprovalsInbox',
        path: '/approvals',
        label: t('nav.maker_checker', 'Maker-Checker'),
        icon: '🛡️',
        badge: nocStore.pendingApprovalsCount,
      });
    }

    if (!authStore.user || authStore.canUseUserFeature('IPAM_VRFS_PREFIXES_MGMT', false)) {
      items.push({
        name: 'IpamManagement',
        path: '/ipam',
        label: t('nav.ipam', 'IPAM'),
        icon: '🌐',
      });
    }

    if (!authStore.user || authStore.canUseUserFeature('SUBSCRIBERS_QOS_PROVISIONING', false)) {
      items.push({
        name: 'SubscribersMap',
        path: '/subscribers/map',
        label: t('nav.subscribers_map', 'Mapa de Clientes'),
        icon: '📍',
      });
    }

    if (
      authStore.isFeatureEnabled('isp_module_enabled') &&
      (!authStore.user || authStore.canUseUserFeature('FIELD_OPS_OPTICAL_NAP_MGMT', false))
    ) {
      items.push({
        name: 'FieldTechOperations',
        path: '/field-ops',
        label: t('nav.field_ops', 'Técnico de Campo'),
        icon: '🛠️',
      });
    }

    if (!authStore.user || authStore.canUseUserFeature('TOPOLOGY_L2_CVE_SYSLOG_MCP', false)) {
      items.push({
        name: 'L2Topology',
        path: '/topology/l2',
        label: t('nav.l2_topology', 'Topología L2'),
        icon: '🗺️',
      });
    }

    if (
      authStore.isFeatureEnabled('nightly_backups_enabled') &&
      (!authStore.user || authStore.canUseUserFeature('MANUAL_BACKUP_DIFF_GIT', false))
    ) {
      items.push({
        name: 'RscGitDiff',
        path: '/backups',
        label: t('nav.backups_diff', 'Respaldos Diff'),
        icon: '📦',
      });
    }

    if (!authStore.user || authStore.canUseUserFeature('BULK_ACTIONS_UPGRADE_ROS', false)) {
      items.push({
        name: 'BulkOperations',
        path: '/bulk-ops',
        label: t('nav.bulk_ops', 'Acciones Masivas'),
        icon: '⚡',
      });
    }

    if (
      !authStore.user ||
      authStore.canUseUserFeature('USER_MANAGEMENT', false) ||
      authStore.canUseUserFeature('VIEW_ACTIVE_SESSIONS_KILLSWITCH', false)
    ) {
      items.push({
        name: 'UsersAndPermissions',
        path: '/users',
        label: t('nav.users_rbac', 'Usuarios & RBAC'),
        icon: '👥',
      });
    }

    if (authStore.currentRole === 'SUPERADMIN_GLOBAL' || authStore.currentRole === 'TENANT_ADMIN') {
      items.push({
        name: 'TenantsManagement',
        path: '/admin/tenants',
        label: t('nav.tenants', 'Empresas (Tenants)'),
        icon: '🏢',
      });
    }

    if (
      !authStore.user ||
      authStore.canUseUserFeature('ENTERPRISE_CIS_DRIFT_COMPLIANCE', false) ||
      authStore.canUseUserFeature('ENTERPRISE_SDWAN_SLA_ROGUEDHCP', false) ||
      authStore.canUseUserFeature('TOPOLOGY_L2_CVE_SYSLOG_MCP', false) ||
      authStore.canUseUserFeature('AUDIT_LOGS_QUERY', false) ||
      authStore.canUseUserFeature('WIFI_CAPSMAN_PROVISIONING', false)
    ) {
      items.push({
        name: 'EnterpriseCompliance',
        path: '/enterprise/compliance',
        label: t('nav.compliance', 'Flota & Seguridad'),
        icon: '🛡️',
      });
    }
```

---

### 2.3. `vue3/src/views/EnterpriseComplianceView.vue` — Visibilidad de Pestañas y Acciones de Mutación según RBAC

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 1 — Definición de Pestañas y Guardias RBAC)

**Target:**
```ts
  interface TabDef {
    id: TabType;
    flag?: keyof TenantFeatureFlags;
  }

  const allTabs: TabDef[] = [
    { id: 'drift', flag: 'config_drift_monitoring_enabled' },
    { id: 'cis', flag: 'cis_audit_enabled' },
    { id: 'cves' },
    { id: 'audit' },
    { id: 'sdwan', flag: 'sdwan_orchestrator_enabled' },
    { id: 'switching' },
    { id: 'sla', flag: 'sla_tracker_enabled' },
    { id: 'wifi', flag: 'capsman_wifi_enabled' },
    { id: 'notifications', flag: 'outbound_webhooks_enabled' },
  ];

  const availableTabs = computed(() => {
    return allTabs.filter((tab) => !tab.flag || authStore.isFeatureEnabled(tab.flag));
  });

  const initialQueryTab = route?.query?.tab as TabType | undefined;
  const activeTab = ref<TabType>(
    initialQueryTab && allTabs.some((t) => t.id === initialQueryTab)
      ? initialQueryTab
      : availableTabs.value[0]?.id || 'switching',
  );

  watch(activeTab, (newTab) => {
    if (router && route && route.query?.tab !== newTab) {
      router.replace({ query: { ...route.query, tab: newTab } }).catch(() => {});
    }
  });

  watch(
    () => route?.query?.tab,
    (newTab) => {
      if (newTab && typeof newTab === 'string' && allTabs.some((t) => t.id === newTab)) {
        activeTab.value = newTab as TabType;
      }
    },
  );
```

**Replacement:**
```ts
  interface TabDef {
    id: TabType;
    flag?: keyof TenantFeatureFlags;
    actionKey?: string;
    allowedRoles?: string[];
  }

  const allTabs: TabDef[] = [
    {
      id: 'drift',
      flag: 'config_drift_monitoring_enabled',
      actionKey: 'ENTERPRISE_CIS_DRIFT_COMPLIANCE',
    },
    {
      id: 'cis',
      flag: 'cis_audit_enabled',
      actionKey: 'ENTERPRISE_CIS_DRIFT_COMPLIANCE',
    },
    { id: 'cves', actionKey: 'TOPOLOGY_L2_CVE_SYSLOG_MCP' },
    { id: 'audit', actionKey: 'AUDIT_LOGS_QUERY' },
    {
      id: 'sdwan',
      flag: 'sdwan_orchestrator_enabled',
      actionKey: 'ENTERPRISE_SDWAN_SLA_ROGUEDHCP',
    },
    { id: 'switching', actionKey: 'ENTERPRISE_SDWAN_SLA_ROGUEDHCP' },
    {
      id: 'sla',
      flag: 'sla_tracker_enabled',
      actionKey: 'ENTERPRISE_SDWAN_SLA_ROGUEDHCP',
    },
    {
      id: 'wifi',
      flag: 'capsman_wifi_enabled',
      actionKey: 'WIFI_CAPSMAN_PROVISIONING',
    },
    {
      id: 'notifications',
      flag: 'outbound_webhooks_enabled',
      allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR'],
    },
  ];

  const availableTabs = computed(() => {
    return allTabs.filter((tab) => {
      if (tab.flag && !authStore.isFeatureEnabled(tab.flag)) {
        return false;
      }
      if (authStore.user) {
        if (tab.allowedRoles && (!authStore.currentRole || !tab.allowedRoles.includes(authStore.currentRole))) {
          return false;
        }
        if (tab.actionKey && !authStore.canUseUserFeature(tab.actionKey, false)) {
          return false;
        }
      }
      return true;
    });
  });

  function isTabAllowed(tabId: TabType): boolean {
    return availableTabs.value.some((t) => t.id === tabId);
  }

  const canWriteCompliance = computed(
    () => !authStore.user || authStore.canUseUserFeature('ENTERPRISE_CIS_DRIFT_COMPLIANCE', true),
  );
  const canWriteSdwanSlaSwitching = computed(
    () => !authStore.user || authStore.canUseUserFeature('ENTERPRISE_SDWAN_SLA_ROGUEDHCP', true),
  );
  const canWriteWifi = computed(
    () => !authStore.user || authStore.canUseUserFeature('WIFI_CAPSMAN_PROVISIONING', true),
  );

  const initialQueryTab = route?.query?.tab as TabType | undefined;
  const activeTab = ref<TabType>(
    initialQueryTab && availableTabs.value.some((t) => t.id === initialQueryTab)
      ? initialQueryTab
      : availableTabs.value[0]?.id || 'cves',
  );

  watch(activeTab, (newTab) => {
    if (router && route && route.query?.tab !== newTab) {
      router.replace({ query: { ...route.query, tab: newTab } }).catch(() => {});
    }
  });

  watch(
    () => route?.query?.tab,
    (newTab) => {
      if (newTab && typeof newTab === 'string' && availableTabs.value.some((t) => t.id === newTab)) {
        activeTab.value = newTab as TabType;
      }
    },
  );
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 2 — Retorno Temprano en `loadTabData` y Barra de Pestañas `<nav>`)

**Target:**
```ts
    if (activeTab.value === 'notifications') {
      return;
    }
```

**Replacement:**
```ts
    if (
      activeTab.value === 'notifications' ||
      activeTab.value === 'cves' ||
      activeTab.value === 'audit'
    ) {
      return;
    }
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 3 — Botones de Pestañas y Controles de Mutación)

**Target:**
```vue
    <!-- Barra de Pestañas Tácticas (Módulos dinámicos por Feature Flags) -->
    <nav class="tactical-tabs-nav" :aria-label="t('enterprise.tabs_aria', 'Módulos de Cumplimiento')">
      <button
        v-if="authStore.isFeatureEnabled('config_drift_monitoring_enabled')"
        id="tab-btn-drift"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'drift' }"
        :aria-selected="activeTab === 'drift'"
        role="tab"
        aria-controls="panel-drift"
        @click="activeTab = 'drift'"
      >
        <span class="tab-icon">📑</span>
        <span>{{ t('enterprise.tab_drift', 'Config Drift & Baselines') }}</span>
      </button>

      <button
        v-if="authStore.isFeatureEnabled('cis_audit_enabled')"
        id="tab-btn-cis"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'cis' }"
        :aria-selected="activeTab === 'cis'"
        role="tab"
        aria-controls="panel-cis"
        @click="activeTab = 'cis'"
      >
        <span class="tab-icon">🔒</span>
        <span>{{ t('enterprise.tab_cis', 'CIS Hardening') }}</span>
      </button>

      <button
        id="tab-btn-cves"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'cves' }"
        :aria-selected="activeTab === 'cves'"
        role="tab"
        aria-controls="panel-cves"
        @click="activeTab = 'cves'"
      >
        <span class="tab-icon">🛡️</span>
        <span>{{ t('enterprise.tab_cves', 'Matriz de CVEs') }}</span>
      </button>

      <button
        id="tab-btn-audit"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'audit' }"
        :aria-selected="activeTab === 'audit'"
        role="tab"
        aria-controls="panel-audit"
        @click="activeTab = 'audit'"
      >
        <span class="tab-icon">📜</span>
        <span>{{ t('enterprise.tab_audit', 'Auditoría WORM') }}</span>
      </button>

      <button
        v-if="authStore.isFeatureEnabled('sdwan_orchestrator_enabled')"
        id="tab-btn-sdwan"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sdwan' }"
        :aria-selected="activeTab === 'sdwan'"
        role="tab"
        aria-controls="panel-sdwan"
        @click="activeTab = 'sdwan'"
      >
        <span class="tab-icon">🌐</span>
        <span>{{ t('enterprise.tab_sdwan', 'SD-WAN Hub & Spoke') }}</span>
      </button>

      <button
        id="tab-btn-switching"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'switching' }"
        :aria-selected="activeTab === 'switching'"
        role="tab"
        aria-controls="panel-switching"
        @click="activeTab = 'switching'"
      >
        <span class="tab-icon">⚡</span>
        <span>{{ t('enterprise.tab_switching', 'Seguridad L2 & Rogue DHCP') }}</span>
      </button>

      <button
        v-if="authStore.isFeatureEnabled('sla_tracker_enabled')"
        id="tab-btn-sla"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sla' }"
        :aria-selected="activeTab === 'sla'"
        role="tab"
        aria-controls="panel-sla"
        @click="activeTab = 'sla'"
      >
        <span class="tab-icon">⏱️</span>
        <span>{{ t('enterprise.tab_sla', 'Telemetría de SLA') }}</span>
      </button>

      <button
        v-if="authStore.isFeatureEnabled('capsman_wifi_enabled')"
        id="tab-btn-wifi"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'wifi' }"
        :aria-selected="activeTab === 'wifi'"
        role="tab"
        aria-controls="panel-wifi"
        @click="activeTab = 'wifi'"
      >
        <span class="tab-icon">📶</span>
        <span>{{ t('enterprise.tab_wifi', 'Wi-Fi CAPsMAN') }}</span>
      </button>

      <button
        v-if="authStore.isFeatureEnabled('outbound_webhooks_enabled')"
        id="tab-btn-notifications"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'notifications' }"
        :aria-selected="activeTab === 'notifications'"
        role="tab"
        aria-controls="panel-notifications"
        @click="activeTab = 'notifications'"
      >
        <span class="tab-icon">🔔</span>
        <span>{{ t('enterprise.tab_notifications', 'Canales de Alerta & Notificación') }}</span>
      </button>
    </nav>
```

**Replacement:**
```vue
    <!-- Barra de Pestañas Tácticas (Módulos dinámicos por Feature Flags + RBAC) -->
    <nav class="tactical-tabs-nav" :aria-label="t('enterprise.tabs_aria', 'Módulos de Cumplimiento')">
      <button
        v-if="isTabAllowed('drift')"
        id="tab-btn-drift"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'drift' }"
        :aria-selected="activeTab === 'drift'"
        role="tab"
        aria-controls="panel-drift"
        @click="activeTab = 'drift'"
      >
        <span class="tab-icon">📑</span>
        <span>{{ t('enterprise.tab_drift', 'Config Drift & Baselines') }}</span>
      </button>

      <button
        v-if="isTabAllowed('cis')"
        id="tab-btn-cis"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'cis' }"
        :aria-selected="activeTab === 'cis'"
        role="tab"
        aria-controls="panel-cis"
        @click="activeTab = 'cis'"
      >
        <span class="tab-icon">🔒</span>
        <span>{{ t('enterprise.tab_cis', 'CIS Hardening') }}</span>
      </button>

      <button
        v-if="isTabAllowed('cves')"
        id="tab-btn-cves"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'cves' }"
        :aria-selected="activeTab === 'cves'"
        role="tab"
        aria-controls="panel-cves"
        @click="activeTab = 'cves'"
      >
        <span class="tab-icon">🛡️</span>
        <span>{{ t('enterprise.tab_cves', 'Matriz de CVEs') }}</span>
      </button>

      <button
        v-if="isTabAllowed('audit')"
        id="tab-btn-audit"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'audit' }"
        :aria-selected="activeTab === 'audit'"
        role="tab"
        aria-controls="panel-audit"
        @click="activeTab = 'audit'"
      >
        <span class="tab-icon">📜</span>
        <span>{{ t('enterprise.tab_audit', 'Auditoría WORM') }}</span>
      </button>

      <button
        v-if="isTabAllowed('sdwan')"
        id="tab-btn-sdwan"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sdwan' }"
        :aria-selected="activeTab === 'sdwan'"
        role="tab"
        aria-controls="panel-sdwan"
        @click="activeTab = 'sdwan'"
      >
        <span class="tab-icon">🌐</span>
        <span>{{ t('enterprise.tab_sdwan', 'SD-WAN Hub & Spoke') }}</span>
      </button>

      <button
        v-if="isTabAllowed('switching')"
        id="tab-btn-switching"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'switching' }"
        :aria-selected="activeTab === 'switching'"
        role="tab"
        aria-controls="panel-switching"
        @click="activeTab = 'switching'"
      >
        <span class="tab-icon">⚡</span>
        <span>{{ t('enterprise.tab_switching', 'Seguridad L2 & Rogue DHCP') }}</span>
      </button>

      <button
        v-if="isTabAllowed('sla')"
        id="tab-btn-sla"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sla' }"
        :aria-selected="activeTab === 'sla'"
        role="tab"
        aria-controls="panel-sla"
        @click="activeTab = 'sla'"
      >
        <span class="tab-icon">⏱️</span>
        <span>{{ t('enterprise.tab_sla', 'Telemetría de SLA') }}</span>
      </button>

      <button
        v-if="isTabAllowed('wifi')"
        id="tab-btn-wifi"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'wifi' }"
        :aria-selected="activeTab === 'wifi'"
        role="tab"
        aria-controls="panel-wifi"
        @click="activeTab = 'wifi'"
      >
        <span class="tab-icon">📶</span>
        <span>{{ t('enterprise.tab_wifi', 'Wi-Fi CAPsMAN') }}</span>
      </button>

      <button
        v-if="isTabAllowed('notifications')"
        id="tab-btn-notifications"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'notifications' }"
        :aria-selected="activeTab === 'notifications'"
        role="tab"
        aria-controls="panel-notifications"
        @click="activeTab = 'notifications'"
      >
        <span class="tab-icon">🔔</span>
        <span>{{ t('enterprise.tab_notifications', 'Canales de Alerta & Notificación') }}</span>
      </button>
    </nav>
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 4 — Ocultación de Controles de Escritura en Modo `READ_ONLY`)

**Target:**
```vue
          <button
            id="btn-revert-drift"
            type="button"
            class="tactical-btn btn-danger"
            :disabled="actionLoading || !driftResult?.drift_detected"
            @click="handleRevertDrift"
          >
            <span>🔄</span>
            {{ t('enterprise.revert_drift', 'Revertir a Plantilla Homologada') }}
          </button>
```

**Replacement:**
```vue
          <button
            v-if="canWriteCompliance"
            id="btn-revert-drift"
            type="button"
            class="tactical-btn btn-danger"
            :disabled="actionLoading || !driftResult?.drift_detected"
            @click="handleRevertDrift"
          >
            <span>🔄</span>
            {{ t('enterprise.revert_drift', 'Revertir a Plantilla Homologada') }}
          </button>
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 5 — Ocultación de Formularios de Escritura en SD-WAN, SLA y Wi-Fi para `READ_ONLY`)

**Target:**
```vue
        <div class="sdwan-grid">
          <!-- Formulario de Aprovisionamiento Spoke -->
```

**Replacement:**
```vue
        <div v-if="canWriteSdwanSlaSwitching" class="sdwan-grid">
          <!-- Formulario de Aprovisionamiento Spoke -->
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 6 — Ocultación de Sondeo Manual SLA y Barra de Acciones Wi-Fi para `READ_ONLY`)

**Target:**
```vue
        <!-- Formulario de Ejecución de Sondeo Inmediato -->
        <div class="sla-form-card" style="margin-top: 1.5rem">
```

**Replacement:**
```vue
        <!-- Formulario de Ejecución de Sondeo Inmediato -->
        <div v-if="canWriteSdwanSlaSwitching" class="sla-form-card" style="margin-top: 1.5rem">
```

#### Archivo: `vue3/src/views/EnterpriseComplianceView.vue` (Bloque 7 — Barra de Operaciones Tácticas Wi-Fi)

**Target:**
```vue
        <!-- Barra de Operaciones Tácticas Wi-Fi -->
        <div class="wifi-action-toolbar" style="margin-top: 1.25rem; display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;">
```

**Replacement:**
```vue
        <!-- Barra de Operaciones Tácticas Wi-Fi -->
        <div v-if="canWriteWifi" class="wifi-action-toolbar" style="margin-top: 1.25rem; display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;">
```

---

### 2.4. `vue3/src/views/DashboardHomeView.vue`, `vue3/src/views/RouterInventoryView.vue` y `vue3/src/components/webfig/RouterSidebarMenu.vue`

#### Archivo: `vue3/src/views/DashboardHomeView.vue`

**Target:**
```ts
  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters(true);
    }
    inventoryStore.fetchNetworkRoles();
    nocStore.connectEventsWebSocket();
    nocStore.fetchRecentAuditLogs();
  });
```

**Replacement:**
```ts
  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters(true);
    }
    inventoryStore.fetchNetworkRoles();
    nocStore.connectEventsWebSocket();
    if (!authStore.user || authStore.canUseUserFeature('AUDIT_LOGS_QUERY', false)) {
      nocStore.fetchRecentAuditLogs();
    }
  });
```

#### Archivo: `vue3/src/views/DashboardHomeView.vue` (Bloque 2 — Filtrado de Baldosas por Acción RBAC)

**Target:**
```ts
    {
      id: 'backups',
      title: t('dashboard.tools.backups_title'),
      category: t('dashboard.tools.backups_cat'),
      description: t('dashboard.tools.backups_desc'),
      icon: '📦',
      route: '/backups',
      requiredFeature: 'nightly_backups_enabled',
    },
    {
      id: 'bulk-ops',
      title: t('dashboard.tools.bulk_ops_title'),
      category: t('dashboard.tools.bulk_ops_cat'),
      description: t('dashboard.tools.bulk_ops_desc'),
      icon: '⚡',
      route: '/bulk-ops',
    },
    {
      id: 'compliance',
      title: t('dashboard.tools.compliance_title', 'Flota & Seguridad'),
      category: t('dashboard.tools.compliance_cat', 'Gobernanza'),
      description: t('dashboard.tools.compliance_desc', 'Auditoría WORM, Matriz CVE, Drift y CIS Hardening'),
      icon: '🛡️',
      route: '/enterprise/compliance',
    },
    {
      id: 'sessions',
      title: t('dashboard.tools.sessions_title'),
      category: t('dashboard.tools.sessions_cat'),
      description: t('dashboard.tools.sessions_desc'),
      icon: '🛑',
      route: '/users?tab=sessions',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SECURITY_OFFICER'],
    },
    {
      id: 'users',
      title: t('dashboard.tools.users_title'),
      category: t('dashboard.tools.users_cat'),
      description: t('dashboard.tools.users_desc'),
      icon: '👥',
      route: '/users',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
    {
      id: 'audit',
      title: t('dashboard.tools.audit_title'),
      category: t('dashboard.tools.audit_cat'),
      description: t('dashboard.tools.audit_desc'),
      icon: '📜',
      route: '/enterprise/compliance?tab=audit',
    },
```

**Replacement:**
```ts
    {
      id: 'backups',
      title: t('dashboard.tools.backups_title'),
      category: t('dashboard.tools.backups_cat'),
      description: t('dashboard.tools.backups_desc'),
      icon: '📦',
      route: '/backups',
      requiredFeature: 'nightly_backups_enabled',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'INVENTORY_MANAGER', 'AUDITOR'],
    },
    {
      id: 'bulk-ops',
      title: t('dashboard.tools.bulk_ops_title'),
      category: t('dashboard.tools.bulk_ops_cat'),
      description: t('dashboard.tools.bulk_ops_desc'),
      icon: '⚡',
      route: '/bulk-ops',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
    },
    {
      id: 'compliance',
      title: t('dashboard.tools.compliance_title', 'Flota & Seguridad'),
      category: t('dashboard.tools.compliance_cat', 'Gobernanza'),
      description: t('dashboard.tools.compliance_desc', 'Auditoría WORM, Matriz CVE, Drift y CIS Hardening'),
      icon: '🛡️',
      route: '/enterprise/compliance',
    },
    {
      id: 'sessions',
      title: t('dashboard.tools.sessions_title'),
      category: t('dashboard.tools.sessions_cat'),
      description: t('dashboard.tools.sessions_desc'),
      icon: '🛑',
      route: '/users?tab=sessions',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'AUDITOR', 'SECURITY_OFFICER'],
    },
    {
      id: 'users',
      title: t('dashboard.tools.users_title'),
      category: t('dashboard.tools.users_cat'),
      description: t('dashboard.tools.users_desc'),
      icon: '👥',
      route: '/users',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
    {
      id: 'audit',
      title: t('dashboard.tools.audit_title'),
      category: t('dashboard.tools.audit_cat'),
      description: t('dashboard.tools.audit_desc'),
      icon: '📜',
      route: '/enterprise/compliance?tab=audit',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'AUDITOR', 'SECURITY_OFFICER'],
    },
```

#### Archivo: `vue3/src/views/RouterInventoryView.vue`

**Target:**
```ts
  const isVaultAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });
```

**Replacement:**
```ts
  const isVaultAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });

  const canImportCsv = computed(
    () => !authStore.user || authStore.canUseUserFeature('ROUTER_INVENTORY_CSV', true),
  );

  const canScheduleMaintenance = computed(
    () => !authStore.user || authStore.canUseUserFeature('SCHEDULE_MAINTENANCE', true),
  );
```

#### Archivo: `vue3/src/views/RouterInventoryView.vue` (Bloque 2 — Ocultar Botones de CSV y Mantenimiento cuando no hay permiso)

**Target:**
```vue
        <button
          type="button"
          class="btn-import-csv"
          :aria-label="t('inventory.aria_import_csv', 'Abrir asistente de importación CSV')"
          @click="isCsvModalOpen = true"
        >
          {{ t('inventory.btn_import_csv') }}
        </button>

        <button
          type="button"
          class="btn-cve-matrix"
          :aria-label="t('inventory.aria_cve_matrix', 'Ver matriz de vulnerabilidades CVE')"
          @click="router.push('/inventory/cves')"
        >
          {{ t('inventory.btn_cve_matrix') }}
        </button>

        <button
          type="button"
          class="btn-maintenance-windows"
          :aria-label="t('inventory.aria_maintenance_windows', 'Abrir gestión de ventanas de mantenimiento')"
          @click="router.push('/inventory/maintenance-windows')"
        >
          <span class="btn-icon" aria-hidden="true">🛠️</span>
          <span>{{ t('inventory.btn_maintenance_windows', 'Ventanas de Mantenimiento') }}</span>
        </button>
```

**Replacement:**
```vue
        <button
          v-if="canImportCsv"
          type="button"
          class="btn-import-csv"
          :aria-label="t('inventory.aria_import_csv', 'Abrir asistente de importación CSV')"
          @click="isCsvModalOpen = true"
        >
          {{ t('inventory.btn_import_csv') }}
        </button>

        <button
          type="button"
          class="btn-cve-matrix"
          :aria-label="t('inventory.aria_cve_matrix', 'Ver matriz de vulnerabilidades CVE')"
          @click="router.push('/inventory/cves')"
        >
          {{ t('inventory.btn_cve_matrix') }}
        </button>

        <button
          v-if="canScheduleMaintenance"
          type="button"
          class="btn-maintenance-windows"
          :aria-label="t('inventory.aria_maintenance_windows', 'Abrir gestión de ventanas de mantenimiento')"
          @click="router.push('/inventory/maintenance-windows')"
        >
          <span class="btn-icon" aria-hidden="true">🛠️</span>
          <span>{{ t('inventory.btn_maintenance_windows', 'Ventanas de Mantenimiento') }}</span>
        </button>
```

#### Archivo: `vue3/src/views/RouterInventoryView.vue` (Bloque 3 — Botón Mantenimiento en Fila de Tabla)

**Target:**
```vue
                <button
                  type="button"
                  class="btn-row-action"
                  :class="(row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? 'btn-row-action--prod' : 'btn-row-action--maint'"
                  :aria-label="((row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? t('inventory.action_return_production') : t('inventory.action_put_maintenance')) + ` ${(row as unknown as RouterItem).display_name}`"
                  @click="toggleRouterMaintenance(row as unknown as RouterItem)"
                >
                  {{ (row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? t('inventory.btn_in_service', '🟢 En Servicio') : t('inventory.btn_maintenance', '🛠️ Mantenimiento') }}
                </button>
```

**Replacement:**
```vue
                <button
                  v-if="canScheduleMaintenance"
                  type="button"
                  class="btn-row-action"
                  :class="(row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? 'btn-row-action--prod' : 'btn-row-action--maint'"
                  :aria-label="((row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? t('inventory.action_return_production') : t('inventory.action_put_maintenance')) + ` ${(row as unknown as RouterItem).display_name}`"
                  @click="toggleRouterMaintenance(row as unknown as RouterItem)"
                >
                  {{ (row as unknown as RouterItem).admin_state === 'MAINTENANCE' ? t('inventory.btn_in_service', '🟢 En Servicio') : t('inventory.btn_maintenance', '🛠️ Mantenimiento') }}
                </button>
```

#### Archivo: `vue3/src/components/webfig/RouterSidebarMenu.vue`

**Target:**
```ts
  import { ref, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import type { Layer2CatalogItem } from '@/types';
```

**Replacement:**
```ts
  import { ref, computed, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import type { Layer2CatalogItem } from '@/types';
```

#### Archivo: `vue3/src/components/webfig/RouterSidebarMenu.vue` (Bloque 2 — Guardias de Respaldos y Capa 2 Dinámica)

**Target:**
```ts
  const route = useRoute();
  const router = useRouter();
  const { t } = useI18n();
```

**Replacement:**
```ts
  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();
  const { t } = useI18n();

  const canUseBackups = computed(
    () => !authStore.user || authStore.canUseUserFeature('MANUAL_BACKUP_DIFF_GIT', false),
  );
  const canUseLayer2 = computed(
    () => !authStore.user || authStore.canUseUserFeature('WEBFIG_L2_UNIVERSAL', false),
  );
```

#### Archivo: `vue3/src/components/webfig/RouterSidebarMenu.vue` (Bloque 3 — `onMounted` y Plantilla de Menú Lateral WebFig)

**Target:**
```ts
  onMounted(() => {
    loadLayer2Catalog();
  });
```

**Replacement:**
```ts
  onMounted(() => {
    if (canUseLayer2.value) {
      loadLayer2Catalog();
    }
  });
```

**Target:**
```vue
          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/backups') }"
            @click="navigateTo('backups')"
          >
            <span class="item-icon">💾</span>
            <span class="item-text">{{ t('webfig.nav_backups') }}</span>
          </button>
        </div>

        <!-- Sección 3: Capa 2 Dinámica -->
        <div class="nav-group">
```

**Replacement:**
```vue
          <button
            v-if="canUseBackups"
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/backups') }"
            @click="navigateTo('backups')"
          >
            <span class="item-icon">💾</span>
            <span class="item-text">{{ t('webfig.nav_backups') }}</span>
          </button>
        </div>

        <!-- Sección 3: Capa 2 Dinámica -->
        <div v-if="canUseLayer2" class="nav-group">
```

---

### 2.5. Paridad de Roles de Lectura en Backend (`sdwan.py`, `switching.py`, `sla.py`, `wifi.py`)

#### Archivo: `fastapi/src/api/v1/sdwan.py`

**Target:**
```python
_SDWAN_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.NOC_MONITOR,
)
```

**Replacement:**
```python
_SDWAN_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
)
```

#### Archivo: `fastapi/src/api/v1/switching.py`

**Target:**
```python
_SWITCHING_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.NOC_MONITOR,
)
```

**Replacement:**
```python
_SWITCHING_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
)
```

#### Archivo: `fastapi/src/api/v1/sla.py`

**Target:**
```python
_SLA_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
)
```

**Replacement:**
```python
_SLA_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
)
```

#### Archivo: `fastapi/src/api/v1/wifi.py`

**Target:**
```python
_WIFI_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.NOC_MONITOR,
)
```

**Replacement:**
```python
_WIFI_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.FIELD_TECH,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
)
```

---

### 2.6. Pruebas Unitarias 11X (`vue3/src/stores/useAuthStore.unit.ts` y `vue3/src/views/enterpriseComplianceView.unit.ts`)

#### Archivo: `vue3/src/stores/useAuthStore.unit.ts`

Añadir prueba unitaria certificando que `canUseUserFeature` evalúa `ROLE_POLICY_MATRIX` para `SUPPORT_L1`, `SUPPORT_L2` y `feature_flags_override`:

```ts
  it('evalúa ROLE_POLICY_MATRIX en canUseUserFeature para SUPPORT_L1 y respeta feature_flags_override (Hito 28.9)', () => {
    const auth = useAuthStore();
    auth.setAuth({
      ...sampleUser,
      role: 'SUPPORT_L1',
    });

    expect(auth.canUseUserFeature('ENTERPRISE_CIS_DRIFT_COMPLIANCE', false)).toBe(false);
    expect(auth.canUseUserFeature('AUDIT_LOGS_QUERY', false)).toBe(false);
    expect(auth.canUseUserFeature('MANUAL_BACKUP_DIFF_GIT', false)).toBe(false);
    expect(auth.canUseUserFeature('BULK_ACTIONS_UPGRADE_ROS', false)).toBe(false);
    expect(auth.canUseUserFeature('USER_MANAGEMENT', false)).toBe(false);
    expect(auth.canUseUserFeature('WEBFIG_L2_UNIVERSAL', false)).toBe(false);
    expect(auth.canUseUserFeature('ENTERPRISE_SDWAN_SLA_ROGUEDHCP', false)).toBe(true);
    expect(auth.canUseUserFeature('ENTERPRISE_SDWAN_SLA_ROGUEDHCP', true)).toBe(false);
    expect(auth.canUseUserFeature('CONFIG_STANDARD_L1', true)).toBe(true);
  });
```

#### Archivo: `vue3/src/views/enterpriseComplianceView.unit.ts`

Añadir prueba unitaria certificando que un operador `SUPPORT_L1` al abrir `/enterprise/compliance` no ve las pestañas restringidas (`#tab-btn-drift`, `#tab-btn-cis`, `#tab-btn-audit`, `#tab-btn-notifications`) ni recibe errores 403 al inicializar en la primera pestaña permitida (`cves`):

```ts
  it('oculta pestañas restringidas (drift, cis, audit, notifications) para SUPPORT_L1 evitando errores 403 al entrar (Hito 28.9)', async () => {
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'u-l1',
      email: 'l1@corp.net',
      username: 'prueba_l1',
      tenant_id: T_CORP,
      tenant_slug: 'corp-tenant',
      role: 'SUPPORT_L1',
      totp_enabled: false,
      tenant_feature_flags: {
        config_drift_monitoring_enabled: true,
        cis_audit_enabled: true,
        sdwan_orchestrator_enabled: true,
        sla_tracker_enabled: true,
        capsman_wifi_enabled: true,
        outbound_webhooks_enabled: true,
      },
    });

    const wrapper = mount(EnterpriseComplianceView, {
      global: {
        stubs: {
          FleetCveMatrix: { template: '<div id="cve-matrix-stub">CVE Matrix</div>' },
          ImmutableAuditLogsView: true,
          OutboundWebhooksConfigPanel: true,
        },
      },
    });

    expect(wrapper.find('#tab-btn-drift').exists()).toBe(false);
    expect(wrapper.find('#tab-btn-cis').exists()).toBe(false);
    expect(wrapper.find('#tab-btn-audit').exists()).toBe(false);
    expect(wrapper.find('#tab-btn-notifications').exists()).toBe(false);
    expect(wrapper.find('#tab-btn-cves').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-sdwan').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-switching').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-sla').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-wifi').exists()).toBe(true);
    expect(wrapper.find('.alert-error').exists()).toBe(false);
  });
```
