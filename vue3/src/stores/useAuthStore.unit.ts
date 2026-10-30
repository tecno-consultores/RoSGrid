// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from './useAuthStore';
import type { UserInfo } from '@/types';

const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: storageMock,
  writable: true,
  configurable: true,
});

describe('useAuthStore — Autenticación Zero-Trust & RBAC', () => {
  beforeEach(() => {
    window.localStorage.clear();
    setActivePinia(createPinia());
  });

  const sampleUser: UserInfo = {
    id: 'usr-001',
    username: 'admin',
    email: 'admin@rosgrid.local',
    tenant_id: 'tenant-global',
    tenant_slug: 'corp',
    role: 'SUPERADMIN_GLOBAL',
    totp_enabled: true,
  };

  it('inicia en estado no autenticado por defecto', () => {
    const auth = useAuthStore();
    expect(auth.isAuthenticated).toBe(false);
    expect(auth.user).toBeNull();
    expect(auth.currentRole).toBeNull();
    expect(auth.tenantSlug).toBeNull();
  });

  it('asigna sesión con setAuth y calcula permisos correctamente', () => {
    const auth = useAuthStore();
    auth.setAuth(sampleUser, 'sample-csrf-token');

    expect(auth.isAuthenticated).toBe(true);
    expect(auth.user).toEqual(sampleUser);
    expect(auth.currentRole).toBe('SUPERADMIN_GLOBAL');
    expect(auth.tenantSlug).toBe('corp');
    expect(auth.csrfToken).toBe('sample-csrf-token');
    expect(auth.hasCapability('ANY_ACTION')).toBe(true);
  });

  it('evalúa capacidades para roles con privilegios restringidos', () => {
    const auth = useAuthStore();
    auth.setAuth({ ...sampleUser, role: 'AUDITOR' });
    expect(auth.hasCapability('READ_LOGS')).toBe(true);
    expect(auth.hasCapability('EXPORT_REPORTS')).toBe(true);
    expect(auth.hasCapability('WRITE_CONFIG')).toBe(false);

    auth.setAuth({ ...sampleUser, role: 'NOC_MONITOR' });
    expect(auth.hasCapability('READ_DASHBOARD')).toBe(true);
    expect(auth.hasCapability('WRITE_CONFIG')).toBe(false);

    auth.setAuth({ ...sampleUser, role: 'SECURITY_OFFICER' });
    expect(auth.hasCapability('SECURITY_AUDIT')).toBe(true);
    expect(auth.hasCapability('ADMIN_DELETE')).toBe(false);

    auth.setAuth({ ...sampleUser, role: 'INVENTORY_MANAGER' });
    expect(auth.hasCapability('INVENTORY_EDIT')).toBe(true);
    expect(auth.hasCapability('ADMIN_DELETE')).toBe(false);

    auth.setAuth({ ...sampleUser, role: 'SUPPORT_L3' });
    expect(auth.hasCapability('APPLY_CONFIG')).toBe(true);
    expect(auth.hasCapability('ADMIN_DELETE')).toBe(false);
  });

  it('limpia estado al invocar clearAuth', () => {
    const auth = useAuthStore();
    auth.setAuth(sampleUser);
    expect(auth.isAuthenticated).toBe(true);

    auth.clearAuth();
    expect(auth.isAuthenticated).toBe(false);
    expect(auth.user).toBeNull();
    expect(auth.currentRole).toBeNull();
    expect(auth.csrfToken).toBeNull();
  });

  it('permite actualizar el CSRF token', () => {
    const auth = useAuthStore();
    auth.setCsrfToken('new-csrf-token');
    expect(auth.csrfToken).toBe('new-csrf-token');
  });

  it('ejecuta forceKillSwitchLogout limpiando la sesión y disparando evento', () => {
    const auth = useAuthStore();
    auth.setAuth(sampleUser);

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    auth.forceKillSwitchLogout('Test Kill');

    expect(auth.isAuthenticated).toBe(false);
    expect(eventSpy).toHaveBeenCalledOnce();

    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });

  it('evalúa correctamente los feature flags del tenant con isFeatureEnabled', () => {
    const auth = useAuthStore();
    expect(auth.isFeatureEnabled('isp_module_enabled')).toBe(false);

    auth.setAuth({
      ...sampleUser,
      tenant_feature_flags: {
        isp_module_enabled: true,
        nightly_backups_enabled: false,
      },
    });

    expect(auth.isFeatureEnabled('isp_module_enabled')).toBe(true);
    expect(auth.isFeatureEnabled('nightly_backups_enabled')).toBe(false);
    expect(auth.isFeatureEnabled('unknown_flag')).toBe(false);
  });

  it('purga la sesión reactivamente al recibir el evento rosgrid:session-expired', () => {
    const auth = useAuthStore();
    auth.setAuth(sampleUser, 'csrf-tok-123', 'sid-999');
    expect(auth.isAuthenticated).toBe(true);
    expect(auth.sessionId).toBe('sid-999');
    expect(window.localStorage.getItem('rosgrid_user')).toBeTruthy();

    window.dispatchEvent(new CustomEvent('rosgrid:session-expired'));

    expect(auth.isAuthenticated).toBe(false);
    expect(auth.user).toBeNull();
    expect(auth.csrfToken).toBeNull();
    expect(auth.sessionId).toBeNull();
    expect(window.localStorage.getItem('rosgrid_user')).toBeNull();
    expect(window.localStorage.getItem('rosgrid_csrf')).toBeNull();
    expect(window.localStorage.getItem('rosgrid_session_id')).toBeNull();
  });
});
