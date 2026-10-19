// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RbacRoleMatrixPanel from './RbacRoleMatrixPanel.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { http } from '@/api/httpClient';

const mockRoles = [
  {
    role: 'SUPERADMIN_GLOBAL',
    title: 'Superadministrador Global',
    description: 'Control absoluto del sistema.',
    level: 0,
    badge_color: 'purple',
    is_system_reserved: true,
    has_custom_overrides: false,
    permissions: {
      ROUTER_CONFIG_WRITE: 'ALLOW',
      SECURITY_FIREWALL: 'ALLOW',
      TENANT_MANAGEMENT: 'ALLOW',
    },
  },
  {
    role: 'SUPPORT_L2',
    title: 'Soporte Técnico Nivel 2',
    description: 'Operador de segundo nivel NOC.',
    level: 4,
    badge_color: 'amber',
    is_system_reserved: false,
    has_custom_overrides: false,
    permissions: {
      ROUTER_CONFIG_WRITE: 'MAKER_CHECKER',
      SECURITY_FIREWALL: 'READ_ONLY',
      TENANT_MANAGEMENT: 'DENY',
    },
  },
  {
    role: 'AUDITOR',
    title: 'Auditor de Seguridad',
    description: 'Auditoría forense de solo lectura.',
    level: 8,
    badge_color: 'indigo',
    is_system_reserved: false,
    has_custom_overrides: true,
    permissions: {
      ROUTER_CONFIG_WRITE: 'DENY',
      SECURITY_FIREWALL: 'READ_ONLY',
      TENANT_MANAGEMENT: 'DENY',
    },
  },
];

const mockActions = [
  {
    key: 'ROUTER_CONFIG_WRITE',
    label: 'Configuración General de Routers',
    category: 'Infraestructura de Red',
    description: 'Modificación de parámetros en RouterOS.',
  },
  {
    key: 'SECURITY_FIREWALL',
    label: 'Reglas de Firewall y Filtros',
    category: 'Seguridad Perimetral',
    description: 'Gestión de filtros y chains.',
  },
  {
    key: 'TENANT_MANAGEMENT',
    label: 'Administración de Empresas',
    category: 'Administración',
    description: 'Creación de tenants.',
  },
];

describe('RbacRoleMatrixPanel.vue — Matriz de Roles y Políticas RBAC', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();

    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'admin-1',
      username: 'root_admin',
      email: 'root@rosgrid.local',
      tenant_id: 't-corp',
      tenant_slug: 'corp',
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
    });

    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url.includes('/api/v1/rbac/roles')) {
        return Promise.resolve({
          status: 200,
          data: mockRoles,
          headers: new Headers(),
        });
      }
      if (url.includes('/api/v1/rbac/actions')) {
        return Promise.resolve({
          status: 200,
          data: mockActions,
          headers: new Headers(),
        });
      }
      return Promise.reject(new Error(`Not mocked: ${url}`));
    });
  });

  it('monta el componente, carga roles y acciones y permite seleccionar un rol', async () => {
    const wrapper = mount(RbacRoleMatrixPanel);
    await flushPromises();

    expect(wrapper.find('.selector-title').text()).toContain('Seleccionar Perfil o Rol');

    // Comprobar chips de roles cargados
    const roleChips = wrapper.findAll('.role-chip');
    expect(roleChips.length).toBe(mockRoles.length);

    // Seleccionar rol SUPPORT_L2
    const l2Chip = roleChips.find((c) => c.text().includes('Soporte Técnico Nivel 2'));
    expect(l2Chip).toBeDefined();
    await l2Chip?.trigger('click');

    expect(wrapper.find('.role-heading-title').text()).toContain('Soporte Técnico Nivel 2');
    expect(wrapper.find('.role-description-text').text()).toContain(
      'Operador de segundo nivel NOC.',
    );
  });

  it('permite cambiar permisos de una acción mediante los botones segmentados', async () => {
    const wrapper = mount(RbacRoleMatrixPanel);
    await flushPromises();

    // Seleccionar SUPPORT_L2
    const roleChips = wrapper.findAll('.role-chip');
    const l2Chip = roleChips.find((c) => c.text().includes('Soporte Técnico Nivel 2'));
    await l2Chip?.trigger('click');

    // Cambiar primer permiso a ALLOW
    const allowBtn = wrapper.find('.btn-perm--allow');
    expect(allowBtn.exists()).toBe(true);
    await allowBtn.trigger('click');

    // Simular guardado
    const putSpy = vi.spyOn(http, 'put').mockResolvedValueOnce({
      status: 200,
      data: { message: 'Permisos actualizados' },
      headers: new Headers(),
    });

    const saveBtn = wrapper.find('.btn-save');
    await saveBtn.trigger('click');
    await flushPromises();

    expect(putSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/rbac/roles/SUPPORT_L2/permissions'),
      expect.objectContaining({
        permissions: expect.any(Object),
      }),
    );
    expect(wrapper.find('.banner--success').text()).toContain('Permisos actualizados');
  });

  it('permite aplicar asignación masiva de permisos (Bulk Tools) y restaurar a fábrica', async () => {
    const wrapper = mount(RbacRoleMatrixPanel);
    await flushPromises();

    // Seleccionar SUPPORT_L2
    const roleChips = wrapper.findAll('.role-chip');
    const l2Chip = roleChips.find((c) => c.text().includes('Soporte Técnico Nivel 2'));
    await l2Chip?.trigger('click');

    // Clic en "Maker-Checker" masivo
    const bulkBtns = wrapper.findAll('.btn-bulk');
    const mcBulkBtn = bulkBtns.find((b) => b.text().includes('Maker-Checker'));
    expect(mcBulkBtn).toBeDefined();
    await mcBulkBtn?.trigger('click');

    // Ahora seleccionar AUDITOR (que tiene has_custom_overrides: true)
    const auditorChip = roleChips.find((c) => c.text().includes('Auditor de Seguridad'));
    await auditorChip?.trigger('click');

    // Clic en "Restablecer Valores de Fábrica"
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const resetSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      status: 200,
      data: { message: 'Permisos restablecidos' },
      headers: new Headers(),
    });

    const resetBtn = wrapper.find('.btn-reset');
    expect(resetBtn.exists()).toBe(true);
    await resetBtn.trigger('click');
    await flushPromises();

    expect(resetSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/rbac/roles/AUDITOR/reset'),
    );
  });
});
