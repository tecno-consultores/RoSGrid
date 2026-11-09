/* eslint-disable security/detect-object-injection, sonarjs/cognitive-complexity */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { SystemRole, TenantFeatureFlags, UserInfo } from '@/types';
import { http } from '@/api/httpClient';

export const defaultTenantFeatures: TenantFeatureFlags = {
  isp_module_enabled: true,
  bgp_looking_glass_enabled: false,
  sfp_ddm_telemetry_enabled: true,
  ipfix_analytics_enabled: false,
  enforce_maker_checker: true,
  auto_safemode_enforced: true,
  ai_mcp_integration_enabled: true,
  nightly_backups_enabled: true,
  outbound_webhooks_enabled: true,
  config_drift_monitoring_enabled: false,
  cis_audit_enabled: true,
  sdwan_orchestrator_enabled: false,
  capsman_wifi_enabled: false,
  sla_tracker_enabled: false,
  mass_outage_threshold: 10,
  default_locale: 'es',
  l2_topology_enabled: true,
  syslog_collector_enabled: true,
  cve_scanner_enabled: true,
  prometheus_fleet_exporter_enabled: true,
  rogue_dhcp_enabled: true,
};

function getSafeLocalStorage(): Storage | null {
  try {
    if (
      typeof window !== 'undefined' &&
      window.localStorage &&
      typeof window.localStorage.getItem === 'function'
    ) {
      return window.localStorage;
    }
    if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
      return localStorage;
    }
  } catch {
    // Ignora acceso bloqueado a storage
  }
  return null;
}

function getStoredUser(): UserInfo | null {
  const storage = getSafeLocalStorage();
  if (!storage) return null;
  try {
    const raw = storage.getItem('rosgrid_user');
    return raw ? (JSON.parse(raw) as UserInfo) : null;
  } catch {
    return null;
  }
}

function saveSafeStorageItem(key: string, value: string): void {
  const activeStorage = getSafeLocalStorage();
  if (!activeStorage) return;
  try {
    activeStorage.setItem(key, value);
  } catch {
    // Ignora fallos de storage cuota
  }
}

export const useAuthStore = defineStore('auth', () => {
  const storage = getSafeLocalStorage();
  const initialUser = getStoredUser();
  const user = ref<UserInfo | null>(initialUser);
  const tenantSlug = ref<string | null>(initialUser?.tenant_slug ?? null);
  const currentRole = ref<SystemRole | null>(initialUser?.role ?? null);
  const tenantFeatures = ref<Partial<TenantFeatureFlags>>(
    (initialUser?.tenant_feature_flags as Partial<TenantFeatureFlags>) ||
      initialUser?.features ||
      {},
  );
  const csrfToken = ref<string | null>(storage ? storage.getItem('rosgrid_csrf') : null);
  const sessionId = ref<string | null>(storage ? storage.getItem('rosgrid_session_id') : null);

  if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
    window.addEventListener('storage', (event: StorageEvent) => {
      if (event.key === 'rosgrid_user') {
        const nextUser = getStoredUser();
        user.value = nextUser;
        currentRole.value = nextUser?.role ?? null;
        tenantSlug.value = nextUser?.tenant_slug ?? null;
        tenantFeatures.value = {
          ...((nextUser?.tenant_feature_flags as Partial<TenantFeatureFlags>) ||
            nextUser?.features ||
            {}),
        };
      } else if (event.key === 'rosgrid_csrf') {
        csrfToken.value = event.newValue;
      } else if (event.key === 'rosgrid_session_id') {
        sessionId.value = event.newValue;
      }
    });

    window.addEventListener('rosgrid:session-expired', () => {
      clearAuth();
    });
  }

  const isAuthenticated = computed<boolean>(() => user.value !== null);

  const tenantHqCoordinates = computed<[number, number]>(() => {
    const lat = Number(tenantFeatures.value?.hq_latitude);
    const lng = Number(tenantFeatures.value?.hq_longitude);
    if (!Number.isNaN(lat) && !Number.isNaN(lng) && !(lat === 0 && lng === 0)) {
      return [lat, lng];
    }
    return [10.4806, -66.9036];
  });

  function setAuth(userInfo: UserInfo, token?: string | null, sid?: string | null): void {
    user.value = userInfo;
    currentRole.value = userInfo.role;
    tenantSlug.value = userInfo.tenant_slug;
    tenantFeatures.value = {
      ...((userInfo.tenant_feature_flags as Partial<TenantFeatureFlags>) ||
        userInfo.features ||
        {}),
    };
    saveSafeStorageItem('rosgrid_user', JSON.stringify(userInfo));
    if (token) {
      csrfToken.value = token;
      saveSafeStorageItem('rosgrid_csrf', token);
    }
    if (sid) {
      sessionId.value = sid;
      saveSafeStorageItem('rosgrid_session_id', sid);
    }
  }

  function setCsrfToken(token: string): void {
    csrfToken.value = token;
    saveSafeStorageItem('rosgrid_csrf', token);
  }

  function clearAuth(): void {
    const activeStorage = getSafeLocalStorage();
    user.value = null;
    currentRole.value = null;
    tenantSlug.value = null;
    csrfToken.value = null;
    sessionId.value = null;
    tenantFeatures.value = {};
    if (activeStorage) {
      try {
        activeStorage.removeItem('rosgrid_user');
        activeStorage.removeItem('rosgrid_csrf');
        activeStorage.removeItem('rosgrid_session_id');
      } catch {
        // Ignora fallos de storage cuota
      }
    }
  }

  function updateTenantFeatures(features: Partial<TenantFeatureFlags>): void {
    const activeStorage = getSafeLocalStorage();
    tenantFeatures.value = { ...tenantFeatures.value, ...features };
    if (user.value) {
      user.value = {
        ...user.value,
        features: { ...(user.value.features || {}), ...features },
        tenant_feature_flags: {
          ...((user.value.tenant_feature_flags as Partial<TenantFeatureFlags>) || {}),
          ...features,
        },
      };
      if (activeStorage) {
        try {
          activeStorage.setItem('rosgrid_user', JSON.stringify(user.value));
        } catch {
          // Ignora fallos de storage cuota
        }
      }
    }
  }

  async function fetchTenantFeatures(): Promise<void> {
    const tid = user.value?.tenant_id;
    if (!tid) return;
    try {
      const res = await http.get<TenantFeatureFlags>(`/api/v1/tenants/${tid}/features`);
      if (res.data) {
        updateTenantFeatures(res.data);
      }
    } catch {
      // Ignora errores si no hay conexión o no está autenticado aún
    }
  }

  function isFeatureEnabled(flagName: string): boolean {
    if (tenantFeatures.value && (tenantFeatures.value as Record<string, unknown>)[flagName] !== undefined) {
      return Boolean((tenantFeatures.value as Record<string, unknown>)[flagName]);
    }
    if (user.value?.tenant_feature_flags && (user.value.tenant_feature_flags as Record<string, unknown>)[flagName] !== undefined) {
      return Boolean((user.value.tenant_feature_flags as Record<string, unknown>)[flagName]);
    }
    if (user.value?.features && (user.value.features as Record<string, unknown>)[flagName] !== undefined) {
      return Boolean((user.value.features as Record<string, unknown>)[flagName]);
    }
    return false;
  }

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
    const role = currentRole.value || user.value?.role;
    if (!user.value || !role) return false;
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

  function hasCapability(actionCode: string): boolean {
    const role = currentRole.value || user.value?.role;
    if (!role) return false;

    if (role === 'SUPERADMIN_GLOBAL' || role === 'TENANT_ADMIN') {
      return true;
    }
    if (role === 'AUDITOR') {
      return actionCode.startsWith('READ_') || actionCode.startsWith('EXPORT_');
    }
    if (role === 'NOC_MONITOR') {
      return actionCode === 'READ_DASHBOARD' || actionCode === 'READ_ALERTS';
    }
    if (role === 'SECURITY_OFFICER') {
      return actionCode.startsWith('SECURITY_') || actionCode.startsWith('READ_');
    }
    if (role === 'INVENTORY_MANAGER') {
      return actionCode.startsWith('INVENTORY_') || actionCode.startsWith('READ_');
    }
    return !actionCode.startsWith('ADMIN_');
  }

  function forceKillSwitchLogout(reason = 'SESSION_KILLED'): void {
    clearAuth();
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('rosgrid:kill-switch', { detail: { reason } }));
      if (window.location.pathname !== '/login') {
        try {
          window.location.href = `/login?reason=${encodeURIComponent(reason)}`;
        } catch {
          // Fallback para entornos de prueba JSDOM donde window.location.href arroja error de navegación
        }
      }
    }
  }

  async function switchTenant(targetTenantId: string): Promise<boolean> {
    try {
      const res = await http.post<{
        session_id: string;
        user: UserInfo;
        csrf_token: string;
      }>('/api/v1/auth/switch-tenant', { target_tenant_id: targetTenantId });

      if (res.data?.user) {
        setAuth(res.data.user, res.data.csrf_token, res.data.session_id);
        if (typeof window !== 'undefined') {
          window.dispatchEvent(
            new CustomEvent('rosgrid:tenant-switched', {
              detail: { tenantId: targetTenantId, tenantSlug: res.data.user.tenant_slug },
            }),
          );
        }
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  return {
    user,
    tenantSlug,
    currentRole,
    csrfToken,
    sessionId,
    tenantFeatures,
    tenantHqCoordinates,
    isAuthenticated,
    setAuth,
    setCsrfToken,
    clearAuth,
    updateTenantFeatures,
    fetchTenantFeatures,
    switchTenant,
    isFeatureEnabled,
    canUseUserFeature,
    hasCapability,
    forceKillSwitchLogout,
  };
});
