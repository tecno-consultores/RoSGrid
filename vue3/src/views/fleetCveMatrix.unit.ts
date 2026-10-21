// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import FleetCveMatrix from './FleetCveMatrix.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import type { FleetCveSummary, CveSyncResponse } from '@/types';

const mockPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const CVE_2023 = 'CVE-2023-32154';
const CVE_2024 = 'CVE-2024-38355';

const sampleCveSummary: FleetCveSummary = {
  total_evaluated_routers: 5,
  vulnerable_routers_count: 2,
  critical_routers_count: 1,
  high_routers_count: 1,
  total_unique_cves: 2,
  summary_by_severity: { CRITICAL: 1, HIGH: 1 },
  vulnerable_routers: [
    {
      router_id: 'r-001',
      display_name: 'Edge-CCR2004',
      ros_version: '7.12.0',
      total_vulnerabilities: 2,
      critical_count: 1,
      high_count: 1,
      medium_count: 0,
      max_cvss_score: 9.8,
      recommended_target_version: '7.16.2',
      vulnerabilities: [
        {
          cve_id: CVE_2023,
          title: 'Desbordamiento en IPv6 ND',
          cvss_score: 9.8,
          severity: 'CRITICAL',
          affected_versions_expr: '>=7.0.0,<7.9.2',
          fixed_in_version: '7.9.2',
          description_es: 'Desbordamiento de búfer crítico en IPv6 Router Advertisement.',
          remediation: 'Actualizar a v7.9.2 o deshabilitar IPv6.',
          published_date: '2023-05-22',
        },
        {
          cve_id: CVE_2024,
          title: 'Vulnerabilidad REST API',
          cvss_score: 7.5,
          severity: 'HIGH',
          affected_versions_expr: '>=7.0.0,<7.16.0',
          fixed_in_version: '7.16.0',
          description_es: 'Desbordamiento en parsing JSON de la API REST.',
          remediation: 'Actualizar a v7.16.0 o desactivar REST.',
          published_date: '2024-06-18',
        },
      ],
    },
  ],
  timestamp: '2026-10-20T21:00:00Z',
};

describe('FleetCveMatrix.vue — Hito 23.5 Matriz de Vulnerabilidades CVE', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    mockPush.mockReset();

    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url.includes('/api/v1/inventory/cves')) {
        return Promise.resolve({ data: sampleCveSummary, status: 200, headers: new Headers() } as unknown as ApiResponse);
      }
      return Promise.resolve({ data: {}, status: 200, headers: new Headers() } as unknown as ApiResponse);
    });

    vi.spyOn(http, 'post').mockImplementation((url: string) => {
      if (url.includes('/api/v1/inventory/cves/sync')) {
        const syncRes: CveSyncResponse = {
          success: true,
          source_url: 'https://services.nvd.nist.gov/rest/json/cves/2.0',
          total_cves: 6,
          updated_at: '2026-10-20T21:00:00Z',
          message: 'Sincronizado exitosamente con 6 boletines.',
        };
        return Promise.resolve({ data: syncRes, status: 200, headers: new Headers() } as unknown as ApiResponse);
      }
      return Promise.resolve({ data: {}, status: 200, headers: new Headers() } as unknown as ApiResponse);
    });
  });

  it('monta correctamente y muestra el título semántico h1', async () => {
    const wrapper = mount(FleetCveMatrix);
    await wrapper.vm.$nextTick();

    const h1 = wrapper.find('h1');
    expect(h1.exists()).toBe(true);
    expect(h1.text()).toContain('Matriz de Vulnerabilidades CVE');
  });

  it('renderiza tarjetas KPI con los valores evaluados de la flota', async () => {
    const wrapper = mount(FleetCveMatrix);
    // Esperar resolución de promesas
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const kpiCards = wrapper.findAll('.kpi-card');
    expect(kpiCards.length).toBe(4);

    const evaluatedVal = wrapper.find('.kpi-val');
    expect(evaluatedVal.text()).toBe('5');

    const recommendedVer = wrapper.find('.kpi-val--cyan');
    expect(recommendedVer.text()).toBe('7.16.2');
  });

  it('lista las vulnerabilidades únicas en la tabla táctica', async () => {
    const wrapper = mount(FleetCveMatrix);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const rows = wrapper.findAll('.cve-row');
    expect(rows.length).toBe(2);
    expect(wrapper.text()).toContain(CVE_2023);
    expect(wrapper.text()).toContain(CVE_2024);
  });

  it('permite filtrar por severidad de vulnerabilidad', async () => {
    const wrapper = mount(FleetCveMatrix);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const select = wrapper.find('#cve-severity-filter');
    await select.setValue('CRITICAL');
    await wrapper.vm.$nextTick();

    const rows = wrapper.findAll('.cve-row');
    expect(rows.length).toBe(1);
    expect(wrapper.text()).toContain(CVE_2023);
    expect(wrapper.text()).not.toContain(CVE_2024);
  });

  it('expande detalles al hacer clic en botón de detalle', async () => {
    const wrapper = mount(FleetCveMatrix);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const toggleBtn = wrapper.find('.btn-toggle-details');
    await toggleBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.cve-details-row').exists()).toBe(true);
    expect(wrapper.text()).toContain('Mitigación y Remediación Sugerida:');
    expect(wrapper.text()).toContain('Edge-CCR2004');
  });

  it('ejecuta sincronización remota al pulsar botón de sincronizar', async () => {
    const wrapper = mount(FleetCveMatrix);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const syncBtn = wrapper.find('.btn-sync-cve');
    await syncBtn.trigger('click');
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    expect(http.post).toHaveBeenCalledWith('/api/v1/inventory/cves/sync');
    expect(wrapper.find('.banner-success').exists()).toBe(true);
    expect(wrapper.find('.banner-success').text()).toContain('Sincronizado exitosamente');
  });

  it('navega hacia operaciones masivas al pulsar botón de actualizar flota', async () => {
    const wrapper = mount(FleetCveMatrix);
    await new Promise((r) => setTimeout(r, 20));
    await wrapper.vm.$nextTick();

    const remediateBtn = wrapper.find('.btn-remediate-fleet');
    await remediateBtn.trigger('click');

    expect(mockPush).toHaveBeenCalledWith('/bulk-ops');
  });
});
