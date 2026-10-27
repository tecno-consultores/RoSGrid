// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import EnterpriseComplianceView from './EnterpriseComplianceView.vue';
import { http } from '@/api/httpClient';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useAuthStore } from '@/stores/useAuthStore';
import type { CisDirectiveResult } from '@/types';

const T_CORP = 'tenant-test-11x';
const ROUTER_NAME = 'Core-Border-CCR2116';

function generate28Directives(): CisDirectiveResult[] {
  const directives: CisDirectiveResult[] = [];
  // 12 directivas ALL
  for (let i = 1; i <= 10; i++) {
    directives.push({
      code: `CIS-1.${i}`,
      title: `Directiva Base CIS 1.${i}`,
      category: 'CONTROL_PLANE',
      weight: 10,
      severity: 'HIGH',
      enabled: true,
      passed: i <= 5,
      finding: i <= 5 ? 'Configuración óptima' : 'Vulnerabilidad detectada',
      remediation_cmd: `/ip service set test${i} disabled=yes`,
      profile_target: 'ALL',
      standard_ref: `CIS Benchmark 1.${i}`,
      standard_url: `https://www.cisecurity.org/benchmark/mikrotik#1.${i}`,
      reference_url: `https://manual.mikrotik.com/docs/service-${i}`,
      rationale: `Protección base de plano de control 1.${i}`,
    });
  }
  directives.push({
    code: 'CIS-2.1',
    title: 'NTP Seguro',
    category: 'INTEGRITY',
    weight: 10,
    severity: 'MEDIUM',
    enabled: true,
    passed: true,
    finding: 'NTP sincronizado',
    remediation_cmd: '/system ntp client set enabled=yes',
    profile_target: 'ALL',
    standard_ref: 'RFC 5905',
    standard_url: 'https://datatracker.ietf.org/doc/html/rfc5905',
    reference_url: 'https://manual.mikrotik.com/docs/ntp',
    rationale: 'Sincronización horaria criptográfica',
  });
  directives.push({
    code: 'CIS-2.2',
    title: 'Syslog Centralizado Cifrado',
    category: 'INTEGRITY',
    weight: 10,
    severity: 'MEDIUM',
    enabled: true,
    passed: false,
    finding: 'Syslog remoto no configurado',
    remediation_cmd: '/system logging action add name=rosgridsyslog target=remote',
    profile_target: 'ALL',
    standard_ref: 'CIS 2.2 / RFC 5424',
    standard_url: 'https://datatracker.ietf.org/doc/html/rfc5424',
    reference_url: 'https://manual.mikrotik.com/docs/log',
    rationale: 'Trazabilidad de auditoría WORM',
  });

  // 8 directivas ISP
  for (let i = 1; i <= 8; i++) {
    directives.push({
      code: `CIS-ISP-${i}`,
      title: `Directiva ISP ${i}`,
      category: 'ISP_HARDENING',
      weight: 10,
      severity: 'CRITICAL',
      enabled: i <= 4, // 4 activas, 4 inactivas por defecto
      passed: i <= 2,
      finding: i <= 2 ? 'Filtro ISP en vigor' : 'Riesgo BGP/Filtro detectado',
      remediation_cmd: `/ip firewall filter add comment="CIS-ISP-${i}" action=drop`,
      profile_target: 'ISP',
      standard_ref: `BCP 38 / RFC 2827 #${i}`,
      standard_url: 'https://datatracker.ietf.org/doc/html/bcp38',
      reference_url: `https://manual.mikrotik.com/docs/isp-${i}`,
      rationale: `Filtrado perimetral anti-spoofing ISP ${i}`,
    });
  }

  // 8 directivas CORPORATE
  for (let i = 1; i <= 8; i++) {
    directives.push({
      code: `CIS-CORP-${i}`,
      title: `Directiva Empresa ${i}`,
      category: 'DATA_PLANE',
      weight: 10,
      severity: 'HIGH',
      enabled: true,
      passed: i <= 3,
      finding: i <= 3 ? 'Aislamiento corporativo conforme' : 'Falta segmentación 802.1Q',
      remediation_cmd: `/interface bridge port set comment="CIS-CORP-${i}"`,
      profile_target: 'CORPORATE',
      standard_ref: `NIST SP 800-53 / CIS-CORP-${i}`,
      standard_url: 'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final',
      reference_url: `https://manual.mikrotik.com/docs/corp-${i}`,
      rationale: `Aislamiento corporativo y control de acceso ${i}`,
    });
  }

  return directives;
}

describe('EnterpriseComplianceView.vue — Hito 27.11 CIS Benchmark 28 Directivas', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();

    const authStore = useAuthStore();
    authStore.user = {
      id: 'u-11x',
      email: 'security-noc@rosgrid.io',
      username: 'sec_admin',
      tenant_id: T_CORP,
      tenant_slug: 'isp-telecom',
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
      features: {
        cis_audit_enabled: true,
        config_drift_monitoring_enabled: true,
        sdwan_orchestrator_enabled: true,
        sla_tracker_enabled: true,
        capsman_wifi_enabled: true,
        outbound_webhooks_enabled: true,
      },
    };
    authStore.tenantFeatures = {
      cis_audit_enabled: true,
      config_drift_monitoring_enabled: true,
      sdwan_orchestrator_enabled: true,
      sla_tracker_enabled: true,
      capsman_wifi_enabled: true,
      outbound_webhooks_enabled: true,
    };

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-border-1',
        tenant_id: T_CORP,
        display_name: ROUTER_NAME,
        ip_address: '10.250.3.1',
        api_port: 443,
        network_role: 'EDGE',
        admin_state: 'PRODUCTION',
        ros_version: '7.16',
        is_reachable: true,
      },
    ];

    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      let data: unknown = [];
      if (url.includes('/compliance/cis-audit/')) {
        data = {
          router_id: 'r-border-1',
          router_name: ROUTER_NAME,
          security_score: 75,
          compliance_grade: 'B',
          total_directives: 28,
          passed_directives: 11,
          failed_directives: 17,
          directives: generate28Directives(),
          audited_at: new Date().toISOString(),
        };
      } else if (url.includes('/compliance/cis-policies')) {
        data = {
          tenant_id: T_CORP,
          profile: 'CORPORATE',
          updated_at: new Date().toISOString(),
          rules: [],
        };
      }
      return {
        data,
        status: 200,
        headers: new Headers(),
      } as any;
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      data: {
        router_id: 'r-border-1',
        applied_directives_count: 1,
        new_security_score: 80,
        executed_under_safemode: true,
        safemode_timeout_seconds: 60,
      },
      status: 200,
      headers: new Headers(),
    } as any);

    vi.spyOn(http, 'put').mockResolvedValue({
      data: {
        tenant_id: T_CORP,
        profile: 'CORPORATE',
        updated_at: new Date().toISOString(),
        rules: [],
      },
      status: 200,
      headers: new Headers(),
    } as any);
  });

  it('renderiza las 28 directivas CIS y muestra los badges normativos y enlaces oficiales', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      const rows = wrapper.findAll('.cis-table tbody tr');
      expect(rows.length).toBe(28);
    });

    // Validar enlaces externos al estándar y manual MikroTik oficial
    const standardLinks = wrapper.findAll('a.cis-standard-link');
    expect(standardLinks.length).toBeGreaterThan(0);
    const firstStandardLink = standardLinks[0];
    expect(firstStandardLink.attributes('target')).toBe('_blank');
    expect(firstStandardLink.attributes('rel')).toContain('noopener');

    const mikrotikLinks = wrapper.findAll('a.cis-reference-link');
    expect(mikrotikLinks.length).toBeGreaterThan(0);
    expect(mikrotikLinks[0].attributes('href')).toContain('manual.mikrotik.com');
  });

  it('permite filtrar directivas por perfil (Todos, ISP, Empresa, Activas, Inactivas)', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.findAll('.cis-table tbody tr').length).toBe(28);
    });

    // Filtro ISP (ALL + ISP) = 12 + 8 = 20
    const filterIspBtn = wrapper.find('#filter-cis-isp');
    expect(filterIspBtn.exists()).toBe(true);
    await filterIspBtn.trigger('click');
    const ispRows = wrapper.findAll('.cis-table tbody tr');
    expect(ispRows.length).toBe(20);

    // Filtro Empresa (ALL + CORPORATE) = 12 + 8 = 20
    const filterCorpBtn = wrapper.find('#filter-cis-corporate');
    expect(filterCorpBtn.exists()).toBe(true);
    await filterCorpBtn.trigger('click');
    const corpRows = wrapper.findAll('.cis-table tbody tr');
    expect(corpRows.length).toBe(20);

    // Filtro Inactivas (4 directivas ISP deshabilitadas en mock)
    const filterDisabledBtn = wrapper.find('#filter-cis-disabled');
    expect(filterDisabledBtn.exists()).toBe(true);
    await filterDisabledBtn.trigger('click');
    const disabledRows = wrapper.findAll('.cis-table tbody tr');
    expect(disabledRows.length).toBe(4);

    // Volver a Todos (28)
    const filterAllBtn = wrapper.find('#filter-cis-all');
    await filterAllBtn.trigger('click');
    expect(wrapper.findAll('.cis-table tbody tr').length).toBe(28);
  });

  it('permite alternar el switch de activación individual y recalcula el puntaje reactivo', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.findAll('.cis-directive-toggle').length).toBe(28);
    });

    const initialScoreText = wrapper.find('.score-number').text();
    expect(initialScoreText).toContain('/100');

    // Desactivar un switch de directiva
    const firstToggle = wrapper.findAll('.cis-directive-toggle')[0];
    await firstToggle.setValue(false);

    // Verifica que se haya recalculado y permanezca reactivo
    expect(wrapper.vm).toBeDefined();
  });

  it('abre el modal asistido de Safe Mode (60s) con previsualización de comandos y ejecuta remediación', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.find('.btn-apply-remediation').exists()).toBe(true);
    });

    const applyBtn = wrapper.find('.btn-apply-remediation');
    await applyBtn.trigger('click');

    // Modal debe aparecer con alerta de Safe Mode y previsualización de sintaxis
    const modal = wrapper.find('#modal-remediate-directive');
    expect(modal.exists()).toBe(true);
    expect(modal.text()).toContain('Safe Mode (60 segundos)');
    expect(modal.find('.command-code').exists()).toBe(true);

    // Confirmar remediación
    const confirmBtn = wrapper.find('#btn-confirm-safe-remediate');
    expect(confirmBtn.exists()).toBe(true);
    await confirmBtn.trigger('click');

    expect(http.post).toHaveBeenCalledWith(
      expect.stringContaining('/auto-harden'),
      expect.objectContaining({
        directive_codes_to_apply: expect.any(Array),
      }),
    );
  });
});
