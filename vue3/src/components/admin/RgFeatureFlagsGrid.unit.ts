// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgFeatureFlagsGrid from './RgFeatureFlagsGrid.vue';
import { defaultTenantFeatures } from '@/stores/useAuthStore';

describe('RgFeatureFlagsGrid.vue — Cuadrícula Táctica de Feature Flags y Arquetipos', () => {
  it('renderiza los 4 cuadrantes tácticos y los 4 arquetipos en 1 clic', () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: { ...defaultTenantFeatures },
        tenantName: 'ISP Fibra Óptica',
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    // 4 cuadrantes
    const quadrants = wrapper.findAll('.quadrant-card');
    expect(quadrants.length).toBe(4);

    // Arquetipos en barra superior (ahora incluye Modo Contingencia - Hito 26.3)
    const presets = wrapper.findAll('.btn-preset');
    expect(presets.length).toBe(5);
    expect(wrapper.text()).toContain('Modo Corporativo');
    expect(wrapper.text()).toContain('Modo ISP & WISP');
    expect(wrapper.text()).toContain('Modo NOC Mínimo');
    expect(wrapper.text()).toContain('Modo Contingencia / Bajo Consumo');
  });

  it('aplica el arquetipo Corporativo activando seguridad y apagando BGP/Abonados', async () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: {
          ...defaultTenantFeatures,
          isp_module_enabled: true,
          bgp_looking_glass_enabled: true,
          cis_audit_enabled: false,
        },
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    const btnCorp = wrapper.findAll('.btn-preset')[0];
    await btnCorp.trigger('click');

    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    const updated = emitted![0][0] as typeof defaultTenantFeatures;
    expect(updated.cis_audit_enabled).toBe(true);
    expect(updated.enforce_maker_checker).toBe(true);
    expect(updated.auto_safemode_enforced).toBe(true);
    expect(updated.isp_module_enabled).toBe(false);
    expect(updated.bgp_looking_glass_enabled).toBe(false);
  });

  it('aplica el Modo Contingencia / Bajo Consumo apagando recolectores intensivos y mostrando el banner', async () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: {
          ...defaultTenantFeatures,
          syslog_collector_enabled: true,
          ipfix_analytics_enabled: true,
          prometheus_fleet_exporter_enabled: true,
          sfp_ddm_telemetry_enabled: true,
          config_drift_monitoring_enabled: true,
          sdwan_orchestrator_enabled: true,
        },
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    const btnContingency = wrapper.find('.btn-preset--contingency');
    expect(btnContingency.exists()).toBe(true);
    await btnContingency.trigger('click');

    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    const updated = emitted![0][0] as typeof defaultTenantFeatures;
    expect(updated.syslog_collector_enabled).toBe(false);
    expect(updated.ipfix_analytics_enabled).toBe(false);
    expect(updated.prometheus_fleet_exporter_enabled).toBe(false);
    expect(updated.sfp_ddm_telemetry_enabled).toBe(false);
    expect(updated.config_drift_monitoring_enabled).toBe(false);
    expect(updated.sdwan_orchestrator_enabled).toBe(false);

    // Banner visible
    expect(wrapper.find('.contingency-banner').exists()).toBe(true);
    expect(wrapper.text()).toContain('Modo Contingencia Aplicado');
  });

  it('aplica DAG Hard Lock deshabilitando switches hijos cuando isp_module_enabled está apagado', async () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: {
          ...defaultTenantFeatures,
          isp_module_enabled: false,
          bgp_looking_glass_enabled: false,
          sla_tracker_enabled: false,
        },
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    // Validar alertas de dependencia y switches deshabilitados
    const dependencyAlerts = wrapper.findAll('.dependency-alert');
    expect(dependencyAlerts.length).toBeGreaterThanOrEqual(2);
    expect(wrapper.text()).toContain('🔒 Requiere activar previamente: Módulo ISP');

    const disabledSwitches = wrapper.findAll('.switch-toggle--disabled input');
    expect(disabledSwitches.length).toBeGreaterThanOrEqual(2);
    for (const sw of disabledSwitches) {
      expect((sw.element as HTMLInputElement).disabled).toBe(true);
    }
  });

  it('despliega modal de Radio de Impacto al intentar apagar flag crítica de gobernanza', async () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: {
          ...defaultTenantFeatures,
          enforce_maker_checker: true,
        },
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    // Encuentra los switches y conmuta el de Maker-Checker (flag crítica)
    const switches = wrapper.findAll('.switch-toggle input');
    for (const sw of switches) {
      if ((sw.element as HTMLInputElement).checked) {
        await sw.trigger('change');
        if (wrapper.find('.impact-modal-backdrop').exists()) {
          break;
        }
      }
    }

    expect(wrapper.find('.impact-modal-backdrop').exists()).toBe(true);
    expect(wrapper.text()).toContain('Radio de Impacto');
  });

  it('emite evento save al hacer clic en Guardar Capacidades', async () => {
    const wrapper = mount(RgFeatureFlagsGrid, {
      props: {
        modelValue: { ...defaultTenantFeatures },
      },
      global: {
        stubs: {
          'router-link': true,
        },
      },
    });

    const btnSave = wrapper.find('.btn-save-features');
    expect(btnSave.exists()).toBe(true);
    await btnSave.trigger('click');

    expect(wrapper.emitted('save')).toBeTruthy();
  });
});
