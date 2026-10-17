// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { SystemRole, UserInfo } from '@/types';

function getStoredUser(): UserInfo | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem('rosgrid_user');
    return raw ? (JSON.parse(raw) as UserInfo) : null;
  } catch {
    return null;
  }
}

export const useAuthStore = defineStore('auth', () => {
  const initialUser = getStoredUser();
  const user = ref<UserInfo | null>(initialUser);
  const tenantSlug = ref<string | null>(initialUser?.tenant_slug ?? null);
  const currentRole = ref<SystemRole | null>(initialUser?.role ?? null);
  const csrfToken = ref<string | null>(
    typeof localStorage !== 'undefined' ? localStorage.getItem('rosgrid_csrf') : null,
  );

  const isAuthenticated = computed<boolean>(() => user.value !== null);

  function setAuth(userInfo: UserInfo, token?: string | null): void {
    user.value = userInfo;
    currentRole.value = userInfo.role;
    tenantSlug.value = userInfo.tenant_slug;
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('rosgrid_user', JSON.stringify(userInfo));
      } catch {
        // Ignora fallos de storage cuota
      }
    }
    if (token) {
      csrfToken.value = token;
      if (typeof localStorage !== 'undefined') {
        try {
          localStorage.setItem('rosgrid_csrf', token);
        } catch {
          // Ignora fallos de storage cuota
        }
      }
    }
  }

  function setCsrfToken(token: string): void {
    csrfToken.value = token;
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('rosgrid_csrf', token);
      } catch {
        // Ignora fallos de storage cuota
      }
    }
  }

  function clearAuth(): void {
    user.value = null;
    currentRole.value = null;
    tenantSlug.value = null;
    csrfToken.value = null;
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.removeItem('rosgrid_user');
        localStorage.removeItem('rosgrid_csrf');
      } catch {
        // Ignora fallos de storage cuota
      }
    }
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
        window.location.href = `/login?reason=${encodeURIComponent(reason)}`;
      }
    }
  }

  return {
    user,
    tenantSlug,
    currentRole,
    csrfToken,
    isAuthenticated,
    setAuth,
    setCsrfToken,
    clearAuth,
    hasCapability,
    forceKillSwitchLogout,
  };
});
