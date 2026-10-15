// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { SystemRole, UserInfo } from '@/types';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null);
  const tenantSlug = ref<string | null>(null);
  const currentRole = ref<SystemRole | null>(null);
  const csrfToken = ref<string | null>(null);

  const isAuthenticated = computed<boolean>(() => user.value !== null);

  function setAuth(userInfo: UserInfo, token?: string | null): void {
    user.value = userInfo;
    currentRole.value = userInfo.role;
    tenantSlug.value = userInfo.tenant_slug;
    if (token) {
      csrfToken.value = token;
    }
  }

  function setCsrfToken(token: string): void {
    csrfToken.value = token;
  }

  function clearAuth(): void {
    user.value = null;
    currentRole.value = null;
    tenantSlug.value = null;
    csrfToken.value = null;
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
