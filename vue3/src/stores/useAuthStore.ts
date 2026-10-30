// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

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

  function setAuth(userInfo: UserInfo, token?: string | null, sid?: string | null): void {
    const activeStorage = getSafeLocalStorage();
    user.value = userInfo;
    currentRole.value = userInfo.role;
    tenantSlug.value = userInfo.tenant_slug;
    tenantFeatures.value = {
      ...((userInfo.tenant_feature_flags as Partial<TenantFeatureFlags>) ||
        userInfo.features ||
        {}),
    };
    if (activeStorage) {
      try {
        activeStorage.setItem('rosgrid_user', JSON.stringify(userInfo));
      } catch {
        // Ignora fallos de storage cuota
      }
    }
    if (token) {
      csrfToken.value = token;
      if (activeStorage) {
        try {
          activeStorage.setItem('rosgrid_csrf', token);
        } catch {
          // Ignora fallos de storage cuota
        }
      }
    }
    if (sid) {
      sessionId.value = sid;
      if (activeStorage) {
        try {
          activeStorage.setItem('rosgrid_session_id', sid);
        } catch {
          // Ignora fallos de storage cuota
        }
      }
    }
  }

  function setCsrfToken(token: string): void {
    const activeStorage = getSafeLocalStorage();
    csrfToken.value = token;
    if (activeStorage) {
      try {
        activeStorage.setItem('rosgrid_csrf', token);
      } catch {
        // Ignora fallos de storage cuota
      }
    }
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
    return Boolean((tenantFeatures.value as Record<string, unknown>)[flagName]);
  }

  function hasCapability(actionCode: string): boolean {
    if (!currentRole.value) return false;
    const role = currentRole.value;

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
    isAuthenticated,
    setAuth,
    setCsrfToken,
    clearAuth,
    updateTenantFeatures,
    fetchTenantFeatures,
    switchTenant,
    isFeatureEnabled,
    hasCapability,
    forceKillSwitchLogout,
  };
});
