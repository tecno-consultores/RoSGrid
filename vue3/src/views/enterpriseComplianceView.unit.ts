// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import EnterpriseComplianceView from './EnterpriseComplianceView.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useAuthStore } from '@/stores/useAuthStore';

const T_CORP = 't-corp-1';
const CORE_NAME = 'Core-CCR2004';
const SSID_NAME = 'CORP-SECURE-WIFI';

describe('EnterpriseComplianceView.vue — Hito 20 Suite Corporativa', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();

    const authStore = useAuthStore();
    authStore.user = {
      id: 'u-1',
      email: 'admin@corp.net',
      username: 'admin_corp',
      tenant_id: T_CORP,
      tenant_slug: 'corp-tenant',
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
      features: {
        config_drift_monitoring_enabled: true,
        cis_audit_enabled: true,
        sdwan_orchestrator_enabled: true,
        sla_tracker_enabled: true,
        capsman_wifi_enabled: true,
        outbound_webhooks_enabled: true,
      },
    };
    authStore.tenantFeatures = {
      config_drift_monitoring_enabled: true,
      cis_audit_enabled: true,
      sdwan_orchestrator_enabled: true,
      sla_tracker_enabled: true,
      capsman_wifi_enabled: true,
      outbound_webhooks_enabled: true,
    };

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-1',
        tenant_id: T_CORP,
        display_name: CORE_NAME,
        ip_address: '10.0.0.1',
        api_port: 443,
        network_role: 'CORE',
        admin_state: 'PRODUCTION',
        ros_version: '7.16',
        is_reachable: true,
      },
      {
        id: 'r-2',
        tenant_id: T_CORP,
        display_name: 'Branch-Maracaibo',
        ip_address: '10.0.0.2',
        api_port: 443,
        network_role: 'CORPORATE_CPE',
        admin_state: 'PRODUCTION',
        ros_version: '7.16',
        is_reachable: true,
      },
    ];

    // Mock API GET handler
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      let data: unknown = {};
      if (url.includes('/compliance/golden-templates')) {
        data = [
          {
            id: 'tpl-1',
            tenant_id: T_CORP,
            name: 'Baseline-CORE-Strict',
            network_role: 'CORE',
            baseline_rsc_content: '/ip service set telnet disabled=yes',
            enforce_strict_firewall: true,
            enforce_ntp_dns: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ];
      } else if (url.includes('/compliance/config-drift/')) {
        data = {
          router_id: 'r-1',
          router_name: CORE_NAME,
          network_role: 'CORE',
          drift_detected: true,
          baseline_template_name: 'Baseline-CORE-Strict',
          added_lines: ['/ip service set telnet disabled=no'],
          removed_lines: [],
          diff_unified:
            '--- golden\n+++ active\n@@ -1 +1 @@\n-/ip service set telnet disabled=yes\n+/ip service set telnet disabled=no',
          total_drift_lines: 1,
          checked_at: new Date().toISOString(),
        };
      } else if (url.includes('/compliance/cis-audit/')) {
        data = {
          router_id: 'r-1',
          router_name: CORE_NAME,
          security_score: 85,
          compliance_grade: 'B',
          total_directives: 10,
          passed_directives: 8,
          failed_directives: 2,
          directives: [
            {
              code: 'CIS-1.1',
              title: 'Deshabilitar servicios obsoletos',
              passed: false,
              weight: 15,
              finding: 'Telnet se encuentra activo',
              remediation_cmd: '/ip service set telnet disabled=yes',
            },
          ],
          audited_at: new Date().toISOString(),
        };
      } else if (url.includes('/compliance/cis-policies')) {
        data = {
          tenant_id: T_CORP,
          profile: 'CORPORATE',
          updated_at: new Date().toISOString(),
          rules: [
            {
              code: 'CIS-1.1',
              title: 'Deshabilitar servicios obsoletos',
              category: 'CONTROL_PLANE',
              weight: 15,
              severity: 'HIGH',
              enabled: true,
              remediation_cmd: '/ip service set telnet disabled=yes',
              profile_target: 'ALL',
            },
          ],
        };
      } else if (url.includes('/sdwan/topology/')) {
        data = {
          tenant_id: T_CORP,
          total_spokes: 2,
          active_spokes: 2,
          degraded_spokes: 0,
          down_spokes: 0,
          tunnels: [
            {
              id: 'tun-1',
              hub_router_id: 'r-1',
              spoke_router_id: 'r-2',
              spoke_name: 'Maracaibo-Branch',
              interface_name: 'wg-sdwan0',
              allocated_subnet: '10.250.0.0/31',
              hub_endpoint: '200.1.1.1:51820',
              spoke_public_key: 'mockPublicKey==',
              routing_protocol: 'BGP',
              multi_wan_failover_enabled: true,
              status: 'ACTIVE',
              created_at: new Date().toISOString(),
            },
          ],
        };
      } else if (url.includes('/switching/dhcp-snooping/')) {
        data = [
          {
            bridge_name: 'bridge1',
            dhcp_snooping_enabled: true,
            trusted_ports: ['sfp-sfpplus1'],
            untrusted_ports: ['ether2', 'ether3'],
          },
        ];
      } else if (url.includes('/switching/rogue-dhcp/alerts/')) {
        data = [
          {
            id: 'alert-01',
            router_id: 'r-1',
            bridge_name: 'bridge1',
            interface_name: 'ether4',
            rogue_server_mac: 'B8:69:F4:11:22:33',
            rogue_server_ip: '192.168.1.1',
            detected_at: new Date().toISOString(),
            status: 'ALERT_ACTIVE',
          },
        ];
      } else if (url.includes('/sla/metrics/')) {
        data = [
          {
            id: 'sla-1',
            router_id: 'r-1',
            target_host: '8.8.8.8',
            target_name: 'Google-DNS',
            uptime_percent: 99.98,
            avg_latency_ms: 14.5,
            p95_latency_ms: 22.0,
            p99_latency_ms: 35.0,
            jitter_ms: 2.1,
            packet_loss_pct: 0.0,
            sla_threshold_ms: 50.0,
            compliance_status: 'COMPLIANT',
            recorded_at: new Date().toISOString(),
          },
        ];
      } else if (url.includes('/sla/reports/export')) {
        data = {
          tenant_name: 'Corp Tenant',
          period: 'OCT-2026',
          total_targets_monitored: 1,
          global_uptime_percent: 99.98,
          total_contract_breaches: 0,
          total_downtime_minutes: 8.6,
          metrics: [],
          exported_at: new Date().toISOString(),
        };
      } else if (url.includes('/wifi/capsman/') && url.includes('/overview')) {
        data = {
          router_id: 'r-1',
          capsman_running: true,
          active_radios_count: 6,
          managed_aps_count: 3,
          connected_clients_count: 24,
        };
      } else if (url.includes('/wifi/capsman/') && url.includes('/ssids')) {
        data = [
          {
            id: 'ssid-1',
            name: 'Corp-Secure',
            ssid: SSID_NAME,
            security_type: 'WPA3-Enterprise 802.1X',
            vlan_id: 20,
            client_isolation: false,
            rate_limit_profile: '100M/50M',
          },
        ];
      } else if (url.includes('/wifi/clients/')) {
        data = [
          {
            mac_address: 'F4:D4:88:12:34:56',
            ip_address: '10.20.1.45',
            hostname: 'laptop-director',
            ap_name: 'AP-Piso2',
            ssid: SSID_NAME,
            signal_rssi_dbm: -58,
            snr_db: 42,
            wifi_standard: 'Wi-Fi 6 (802.11ax)',
            tx_rate_mbps: 866.7,
            rx_rate_mbps: 866.7,
            fast_roaming_supported: true,
            connected_duration_seconds: 3600,
          },
        ];
      }
      return { data, status: 200, headers: new Headers() } as unknown as ApiResponse;
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      data: {
        remediation_summary: 'Configuración revertida con éxito.',
        audit_log_id: 'worm-log-uuid-1234',
      },
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);
  });

  it('renderiza la vista con el header táctico, badge de Safe Mode y pestañas', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Gestión de Flota & Cumplimiento Normativo');
    });
    expect(wrapper.text()).toContain('Safe Mode (60s)');
    expect(wrapper.find('#tab-btn-drift').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-cis').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-sdwan').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-switching').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-sla').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-wifi').exists()).toBe(true);
  });

  it('permite alternar a la pestaña CIS Hardening y muestra el puntaje', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('85/100');
      expect(wrapper.text()).toContain('Grado B');
      expect(wrapper.text()).toContain('CIS-1.1');
    });
  });

  it('permite abrir el modal de personalización de directivas CIS y guardar configuración', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.find('#btn-open-cis-policies').exists()).toBe(true);
    });

    const openPoliciesBtn = wrapper.find('#btn-open-cis-policies');
    await openPoliciesBtn.trigger('click');

    expect(wrapper.find('.cis-policies-modal').exists()).toBe(true);
    expect(wrapper.text()).toContain('Políticas de Seguridad CIS Hardening — Personalización de Empresa');

    const saveBtn = wrapper.find('#btn-save-cis-policies');
    expect(saveBtn.exists()).toBe(true);

    vi.spyOn(http, 'put').mockResolvedValueOnce({
      data: {
        tenant_id: T_CORP,
        profile: 'ISP',
        updated_at: new Date().toISOString(),
        rules: [],
      },
    } as any);

    await saveBtn.trigger('click');
    expect(http.put).toHaveBeenCalledWith(
      '/api/v1/compliance/cis-policies',
      expect.objectContaining({
        profile: expect.any(String),
      }),
    );
  });

  it('muestra el botón Aplicar en directivas CIS fallidas y permite ejecutar la remediación individual', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const cisTabBtn = wrapper.find('#tab-btn-cis');
    await cisTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.find('.btn-apply-remediation').exists()).toBe(true);
    });

    const applyBtn = wrapper.find('.btn-apply-remediation');
    expect(applyBtn.text()).toContain('Aplicar');

    await applyBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.find('#modal-remediate-directive').exists()).toBe(true);
    });
    const confirmBtn = wrapper.find('#btn-confirm-safe-remediate');
    expect(confirmBtn.exists()).toBe(true);
    await confirmBtn.trigger('click');

    expect(http.post).toHaveBeenCalledWith(
      expect.stringContaining('/auto-harden'),
      expect.objectContaining({
        directive_codes_to_apply: ['CIS-1.1'],
      }),
    );
  });

  it('permite alternar a la pestaña SD-WAN y lista túneles Spoke', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const sdwanTabBtn = wrapper.find('#tab-btn-sdwan');
    await sdwanTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Maracaibo-Branch');
      expect(wrapper.text()).toContain('10.250.0.0/31');
    });
  });

  it('permite alternar a la pestaña Switching y muestra Rogue DHCP', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const switchTabBtn = wrapper.find('#tab-btn-switching');
    await switchTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('bridge1');
      expect(wrapper.text()).toContain('B8:69:F4:11:22:33');
    });
  });

  it('permite alternar a la pestaña SLA y Wi-Fi', async () => {
    const wrapper = mount(EnterpriseComplianceView);
    const slaTabBtn = wrapper.find('#tab-btn-sla');
    await slaTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Google-DNS');
      expect(wrapper.text()).toContain('COMPLIANT');
    });

    const wifiTabBtn = wrapper.find('#tab-btn-wifi');
    await wifiTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain(SSID_NAME);
      expect(wrapper.text()).toContain('F4:D4:88:12:34:56');
    });
  });

  it('muestra mensajes de estado vacío cuando no hay SSIDs ni clientes WiFi ni CAPsMAN activo', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      let data: unknown = [];
      if (url.includes('/wifi/capsman/') && url.includes('/overview')) {
        data = {
          router_id: 'r-1',
          capsman_running: false,
          active_radios_count: 0,
          managed_aps_count: 0,
          connected_clients_count: 0,
        };
      } else if (url.includes('/wifi/capsman/') && url.includes('/ssids')) {
        data = [];
      } else if (url.includes('/wifi/clients/')) {
        data = [];
      }
      return { data, status: 200, headers: new Headers() } as unknown as ApiResponse;
    });

    const wrapper = mount(EnterpriseComplianceView);
    const wifiTabBtn = wrapper.find('#tab-btn-wifi');
    await wifiTabBtn.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('No se encontraron perfiles de SSIDs');
      expect(wrapper.text()).toContain('No hay clientes inalámbricos conectados en este momento');
      expect(wrapper.text()).toContain('El controlador CAPsMAN / WiFi no se encuentra activo');
    });
  });


  it('ejecuta reversión de config drift en 1 clic', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      data: {
        remediation_summary:
          'Configuración revertida a la plantilla homologada CORE bajo Safe Mode (60s).',
        audit_log_id: 'worm-log-uuid-1234',
      },
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(EnterpriseComplianceView);
    await vi.waitFor(() => {
      expect(wrapper.find('#btn-revert-drift').exists()).toBe(true);
    });

    const revertBtn = wrapper.find('#btn-revert-drift');
    await revertBtn.trigger('click');

    await vi.waitFor(() => {
      expect(http.post).toHaveBeenCalledWith(
        '/api/v1/compliance/config-drift/revert',
        expect.objectContaining({ router_id: 'r-1', enforce_safemode: true }),
      );
    });
  });

  it('oculta la pestaña Config Drift cuando el flag config_drift_monitoring_enabled es falso', async () => {
    const authStore = useAuthStore();
    authStore.tenantFeatures = {
      config_drift_monitoring_enabled: false,
      cis_audit_enabled: true,
      sdwan_orchestrator_enabled: true,
      sla_tracker_enabled: true,
      capsman_wifi_enabled: true,
      outbound_webhooks_enabled: true,
    };

    const wrapper = mount(EnterpriseComplianceView);
    await vi.waitFor(() => {
      expect(wrapper.find('#tab-btn-cis').exists()).toBe(true);
    });

    expect(wrapper.find('#tab-btn-drift').exists()).toBe(false);
    expect(wrapper.find('#panel-drift').exists()).toBe(false);
  });
});
