// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { router } from './index';
import { useAuthStore } from '@/stores/useAuthStore';
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

describe('Router — Navigation Guards & RBAC 11 Roles', () => {
  beforeEach(async () => {
    window.localStorage.clear();
    setActivePinia(createPinia());
    document.title = 'RoSGrid';
    await router.push('/login');
  });

  const normalUser: UserInfo = {
    id: 'usr-1',
    username: 'operador',
    email: 'op@rosgrid.local',
    role: 'SUPPORT_L1',
    tenant_id: 'tenant-1',
    tenant_slug: 'demo',
    totp_enabled: false,
  };

  const adminUser: UserInfo = {
    id: 'usr-2',
    username: 'admin',
    email: 'admin@rosgrid.local',
    role: 'TENANT_ADMIN',
    tenant_id: 'tenant-1',
    tenant_slug: 'demo',
    totp_enabled: true,
  };

  it('permite acceso libre a /login sin requerir autenticación', async () => {
    await router.push('/login');
    expect(router.currentRoute.value.path).toBe('/login');
    expect(document.title).toContain('Iniciar Sesión');
  });

  it('redirige a /login cuando usuario no autenticado accede a ruta protegida', async () => {
    const auth = useAuthStore();
    auth.clearAuth();

    await router.push('/inventory');
    expect(router.currentRoute.value.path).toBe('/login');
    expect(router.currentRoute.value.query.redirect).toBe('/inventory');
  });

  it('permite acceso a ruta protegida si usuario está autenticado', async () => {
    const auth = useAuthStore();
    auth.setAuth(normalUser);

    await router.push('/inventory');
    expect(router.currentRoute.value.path).toBe('/inventory');
    expect(document.title).toContain('Inventario de Equipos');
  });

  it('bloquea ruta con RBAC cuando el rol no está permitido y redirige a /inventory', async () => {
    const auth = useAuthStore();
    auth.setAuth(normalUser); // SUPPORT_L1 no tiene acceso a /audit-logs

    await router.push('/audit-logs');
    expect(router.currentRoute.value.path).toBe('/inventory');
  });

  it('permite acceso a ruta protegida por RBAC si el rol está permitido', async () => {
    const auth = useAuthStore();
    auth.setAuth(adminUser); // TENANT_ADMIN sí tiene acceso a /audit-logs

    await router.push('/audit-logs');
    expect(router.currentRoute.value.path).toBe('/audit-logs');
  });

  it('sincroniza pestaña en useWebFigStore cuando navega a /webfig/live', async () => {
    const auth = useAuthStore();
    auth.setAuth(adminUser);

    await router.push('/routers/r-01/webfig/live');
    expect(router.currentRoute.value.path).toBe('/routers/r-01/webfig/live');

    await router.push('/routers/r-01/webfig/interfaces');
    expect(router.currentRoute.value.path).toBe('/routers/r-01/webfig/interfaces');
  });

  it('redirige a /inventory si usuario autenticado intenta entrar a /login', async () => {
    const auth = useAuthStore();
    auth.setAuth(normalUser);

    await router.push('/inventory');
    await router.push('/login');
    expect(router.currentRoute.value.path).toBe('/inventory');
  });

  it('limpia sesión obsoleta y permanece en /login cuando query.reason es session_expired (evita bucle infinito)', async () => {
    const auth = useAuthStore();
    auth.setAuth(normalUser);
    expect(auth.isAuthenticated).toBe(true);

    await router.push({ path: '/login', query: { reason: 'session_expired' } });
    expect(router.currentRoute.value.path).toBe('/login');
    expect(router.currentRoute.value.query.reason).toBe('session_expired');
    expect(auth.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem('rosgrid_user')).toBeNull();
  });

  it('redirige a /noc-wallboard si el rol es NOC_MONITOR', async () => {
    const auth = useAuthStore();
    auth.setAuth({ ...normalUser, role: 'NOC_MONITOR' });

    await router.push('/');
    expect(router.currentRoute.value.path).toBe('/noc-wallboard');
  });

  it('carga todos los componentes dinámicos de rutas', async () => {
    for (const r of router.getRoutes()) {
      if (typeof r.components?.default === 'function') {
        const mod = await (r.components.default as () => Promise<unknown>)();
        expect(mod).toBeTruthy();
      }
    }
  });

  it('gestiona rutas webfig sin tabLabel o tabIcon personalizados y con routerId vacío', async () => {
    router.addRoute({
      path: '/webfig/custom-tool',
      name: 'CustomToolTab',
      component: { template: '<div>custom</div>' },
      meta: { requiresAuth: true },
    });
    const auth = useAuthStore();
    auth.setAuth(adminUser);

    await router.push('/webfig/custom-tool');
    expect(router.currentRoute.value.path).toBe('/webfig/custom-tool');
    expect(router.currentRoute.value.name).toBe('CustomToolTab');
  });

  it('antepone el contexto dinámico del router ([display_name · ip_address]) en document.title para rutas /routers/:routerId/* (Hito 27.15)', async () => {
    const auth = useAuthStore();
    auth.setAuth(adminUser);

    const { useInventoryStore } = await import('@/stores/useInventoryStore');
    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-core-01',
        name: 'CCR2216-Core-CCS',
        display_name: 'CCR2216-Core-CCS',
        ip_address: '10.99.0.1',
        host: '10.99.0.1',
        port: 443,
        is_reachable: true,
      } as never,
    ];

    await router.push('/routers/r-core-01/webfig/firewall');
    expect(document.title).toContain('[CCR2216-Core-CCS · 10.99.0.1]');
    expect(document.title).toContain('Reglas de Firewall');
  });
});
