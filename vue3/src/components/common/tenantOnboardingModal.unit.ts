// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import TenantOnboardingModal from './TenantOnboardingModal.vue';
import { http } from '@/api/httpClient';
import { useAuthStore } from '@/stores/useAuthStore';

const T_ID = '00000000-0000-0000-0000-000000000001';

describe('TenantOnboardingModal.vue — Onboarding de Feature Flags', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();

    const authStore = useAuthStore();
    authStore.user = {
      id: 'u-admin',
      email: 'admin@fibertel.net',
      username: 'admin_isp',
      tenant_id: T_ID,
      tenant_slug: 'fibertel-corp',
      role: 'TENANT_ADMIN',
      totp_enabled: true,
      features: {},
    };
  });

  it('renderiza el modal con el título y las opciones de arquetipos', () => {
    const wrapper = mount(TenantOnboardingModal);
    expect(wrapper.text()).toContain('Configuración Inicial de Despliegue — RoSGrid');
    expect(wrapper.text()).toContain('fibertel-corp');
    expect(wrapper.text()).toContain('Corporativo / Empresa');
    expect(wrapper.text()).toContain('Proveedor ISP / WISP');
    expect(wrapper.text()).toContain('Personalizado');
  });

  it('permite seleccionar el arquetipo ISP y ajusta el perfil', async () => {
    const wrapper = mount(TenantOnboardingModal);
    const ispBtn = wrapper.findAll('.archetype-card')[1];
    await ispBtn.trigger('click');

    expect(ispBtn.classes()).toContain('is-selected');
    const submitBtn = wrapper.find('#btn-confirm-onboarding');
    expect(submitBtn.text()).toContain('Comenzar con Perfil ISP');
  });

  it('muestra sección de switches detallados al elegir Personalizado', async () => {
    const wrapper = mount(TenantOnboardingModal);
    const customBtn = wrapper.findAll('.archetype-card')[2];
    await customBtn.trigger('click');

    expect(wrapper.find('.custom-flags-section').exists()).toBe(true);
    expect(wrapper.text()).toContain('Personalización Fina de Feature Flags');
    expect(wrapper.text()).toContain('Módulo de Clientes ISP & Suscripciones');
  });

  it('envía la configuración y emite completed al confirmar', async () => {
    const wrapper = mount(TenantOnboardingModal);
    vi.spyOn(http, 'patch').mockResolvedValueOnce({
      data: {
        isp_module_enabled: false,
        onboarding_completed: true,
      },
    } as any);

    const submitBtn = wrapper.find('#btn-confirm-onboarding');
    await submitBtn.trigger('click');

    expect(http.patch).toHaveBeenCalledWith(
      `/api/v1/tenants/${T_ID}/features`,
      expect.objectContaining({
        onboarding_completed: true,
      }),
    );
    expect(wrapper.emitted('completed')).toBeTruthy();
  });
});
