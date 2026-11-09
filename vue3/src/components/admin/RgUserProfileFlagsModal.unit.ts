/* eslint-disable sonarjs/no-duplicate-string */
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import RgUserProfileFlagsModal from './RgUserProfileFlagsModal.vue';
import { http } from '@/api/httpClient';
import type { UserManagementItem } from '@/types';

const sampleUser: UserManagementItem = {
  id: 'u-101',
  username: 'operador_demo',
  email: 'demo@rosgrid.net',
  full_name: 'Operador Demo',
  role: 'SUPPORT_L2',
  totp_enabled: true,
  is_active: true,
  has_all_routers_access: false,
};

const mockEffectiveResponse = {
  status: 200,
  data: {
    user_id: 'u-101',
    username: 'operador_demo',
    role: 'SUPPORT_L2',
    role_defaults: {
      LIVE_DIAGNOSTICS: 'ALLOW',
      CONFIG_STANDARD_L1: 'ALLOW',
      WEBFIG_L2_RPC_COMMANDS: 'MAKER_CHECKER',
      TENANT_MANAGEMENT: 'DENY',
    },
    tenant_role_overrides: {},
    user_overrides: {
      WEBFIG_L2_RPC_COMMANDS: 'ALLOW',
    },
    effective_permissions: {
      LIVE_DIAGNOSTICS: 'ALLOW',
      CONFIG_STANDARD_L1: 'ALLOW',
      WEBFIG_L2_RPC_COMMANDS: 'ALLOW',
      TENANT_MANAGEMENT: 'DENY',
    },
    actions_catalog: [
      {
        key: 'LIVE_DIAGNOSTICS',
        label: 'Herramientas en Vivo',
        category: 'Telemetría y Diagnóstico',
        description: 'Pruebas de conectividad y análisis de flujos por socket en vivo.',
      },
      {
        key: 'CONFIG_STANDARD_L1',
        label: 'Configuración Estándar Capa 1',
        category: 'Configuración y Control de Red',
        description: 'Parámetros de MTU, comentarios y asignaciones de red estándar.',
      },
      {
        key: 'WEBFIG_L2_RPC_COMMANDS',
        label: 'Comandos RPC Contextuales Capa 2',
        category: 'Motor Universal Capa 2',
        description: 'Ejecución de verbos POST dinámicos.',
      },
      {
        key: 'TENANT_MANAGEMENT',
        label: 'Administración de Empresas',
        category: 'Administración y Seguridad',
        description: 'Creación, suspensión y cuotas de organizaciones/tenants.',
      },
    ],
  },
  headers: new Headers(),
};

describe('RgUserProfileFlagsModal.vue — Gobernanza Granular de Flags en Perfiles de Usuario', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('no renderiza nada cuando isOpen es false', () => {
    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: false,
        user: sampleUser,
      },
    });
    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('renderiza modal accesible, carga catálogo de 4 funciones y muestra overrides', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce(mockEffectiveResponse);

    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });

    await flushPromises();

    expect(http.get).toHaveBeenCalledWith('/api/v1/users/u-101/effective-permissions');
    expect(wrapper.find('.modal-title').text()).toContain('Flags de Funciones y Permisos');
    expect(wrapper.find('.modal-subtitle').text()).toContain('@operador_demo');

    // Comprobar filas renderizadas
    const rows = wrapper.findAll('.flags-table tbody tr');
    expect(rows.length).toBe(4);

    // Override personalizado detectado (WEBFIG_L2_RPC_COMMANDS = ALLOW)
    expect(wrapper.text()).toContain('Hay 1 override(s) individual(es)');
  });

  it('filtra funciones por texto de búsqueda y por categoría', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce(mockEffectiveResponse);

    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });
    await flushPromises();

    // 1. Filtrar por texto "Capa 2"
    const searchInput = wrapper.find('#search-profile-flags');
    await searchInput.setValue('Capa 2');
    expect(wrapper.findAll('.flags-table tbody tr').length).toBe(1);
    expect(wrapper.text()).toContain('WEBFIG_L2_RPC_COMMANDS');

    // 2. Limpiar texto y filtrar por categoría "Telemetría y Diagnóstico"
    await searchInput.setValue('');
    const catSelect = wrapper.find('#filter-profile-category');
    await catSelect.setValue('Telemetría y Diagnóstico');
    expect(wrapper.findAll('.flags-table tbody tr').length).toBe(1);
    expect(wrapper.text()).toContain('LIVE_DIAGNOSTICS');
  });

  it('permite cambiar override individual y restablecer todos a herencia de rol', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce(mockEffectiveResponse);

    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });
    await flushPromises();

    // Modificar LIVE_DIAGNOSTICS a DENY
    const select = wrapper.find('#select-override-LIVE_DIAGNOSTICS');
    await select.setValue('DENY');

    expect(wrapper.text()).toContain('Hay 2 override(s) individual(es)');

    // Botón Heredar Todo
    const btnReset = wrapper.find('.btn-reset-inherited');
    await btnReset.trigger('click');

    expect(wrapper.text()).toContain('Este operador hereda el 100% de las políticas');
  });

  it('guarda exitosamente los flags llamando a PATCH /api/v1/users/{id}/feature-flags', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce(mockEffectiveResponse);
    vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: {
        status: 'success',
        feature_flags_override: {
          WEBFIG_L2_RPC_COMMANDS: 'ALLOW',
        },
      },
      headers: new Headers(),
    });

    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });
    await flushPromises();

    const saveBtn = wrapper.find('#btn-save-user-flags');
    await saveBtn.trigger('click');
    await flushPromises();

    expect(http.patch).toHaveBeenCalledWith('/api/v1/users/u-101/feature-flags', {
      feature_flags_override: expect.objectContaining({
        WEBFIG_L2_RPC_COMMANDS: 'ALLOW',
      }),
    });
    expect(wrapper.emitted('saved')).toBeTruthy();

    vi.advanceTimersByTime(1000);
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('muestra mensaje de error cuando la API falla', async () => {
    vi.spyOn(http, 'get').mockRejectedValueOnce({
      detail: 'Fallo simulado al conectar con el servidor',
    });

    const wrapper = mount(RgUserProfileFlagsModal, {
      props: {
        isOpen: true,
        user: sampleUser,
      },
    });
    await flushPromises();

    expect(wrapper.find('.msg-banner--error').text()).toContain(
      'Fallo simulado al conectar con el servidor',
    );
  });
});
