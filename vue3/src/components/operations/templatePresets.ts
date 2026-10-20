// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

export interface PredefinedTemplateVariable {
  key: string;
  label: string;
  default_val: string;
  var_type: string;
}

export interface PredefinedTemplateStep {
  method: 'PATCH' | 'POST' | 'PUT' | 'DELETE' | 'GET';
  endpoint: string;
  payload?: Record<string, string | number | boolean>;
  cli_command?: string;
}

export interface PredefinedTemplate {
  name: string;
  category: string;
  description: string;
  requires_safemode: boolean;
  variables_schema: PredefinedTemplateVariable[];
  rest_steps_template: PredefinedTemplateStep[];
}

const NTP_SERVERS_ENDPOINT = 'system/ntp/client/servers';

export const PREDEFINED_TEMPLATES: PredefinedTemplate[] = [
  {
    name: 'CLIENTE_NTP',
    category: 'SYSTEM',
    description: 'Activa el cliente NTP',
    requires_safemode: true,
    variables_schema: [
      {
        key: 'ntp_server_0',
        label: 'Servidor NTP Pool 0',
        default_val: '0.pool.ntp.org',
        var_type: 'string',
      },
      {
        key: 'ntp_server_1',
        label: 'Servidor NTP Pool 1',
        default_val: '1.pool.ntp.org',
        var_type: 'string',
      },
      {
        key: 'ntp_server_2',
        label: 'Servidor NTP Pool 2',
        default_val: '2.pool.ntp.org',
        var_type: 'string',
      },
      {
        key: 'ntp_server_3',
        label: 'Servidor NTP Pool 3',
        default_val: '3.pool.ntp.org',
        var_type: 'string',
      },
    ],
    rest_steps_template: [
      {
        method: 'PATCH',
        endpoint: 'system/ntp/client',
        payload: { enabled: 'yes' },
        cli_command: '/system ntp client set enabled=yes',
      },
      {
        method: 'PUT',
        endpoint: NTP_SERVERS_ENDPOINT,
        payload: { address: '{{ ntp_server_0 }}' },
        cli_command: '/system ntp client servers add address={{ ntp_server_0 }}',
      },
      {
        method: 'PUT',
        endpoint: NTP_SERVERS_ENDPOINT,
        payload: { address: '{{ ntp_server_1 }}' },
        cli_command: '/system ntp client servers add address={{ ntp_server_1 }}',
      },
      {
        method: 'PUT',
        endpoint: NTP_SERVERS_ENDPOINT,
        payload: { address: '{{ ntp_server_2 }}' },
        cli_command: '/system ntp client servers add address={{ ntp_server_2 }}',
      },
      {
        method: 'PUT',
        endpoint: NTP_SERVERS_ENDPOINT,
        payload: { address: '{{ ntp_server_3 }}' },
        cli_command: '/system ntp client servers add address={{ ntp_server_3 }}',
      },
    ],
  },
  {
    name: 'DNS_CORPORATIVO_RESILIENTE',
    category: 'NETWORK',
    description:
      'Configura servidores DNS redundantes (Quad9 y Cloudflare) y vacía la caché de resolución.',
    requires_safemode: true,
    variables_schema: [
      {
        key: 'dns_servers',
        label: 'Servidores DNS (separados por coma)',
        default_val: '9.9.9.9,1.1.1.1',
        var_type: 'string',
      },
      {
        key: 'allow_remote',
        label: 'Permitir peticiones remotas',
        default_val: 'no',
        var_type: 'string',
      },
    ],
    rest_steps_template: [
      {
        method: 'PATCH',
        endpoint: 'ip/dns',
        payload: { servers: '{{ dns_servers }}', 'allow-remote-requests': '{{ allow_remote }}' },
        cli_command:
          '/ip dns set servers={{ dns_servers }} allow-remote-requests={{ allow_remote }}',
      },
      {
        method: 'POST',
        endpoint: 'ip/dns/cache/flush',
        payload: {},
        cli_command: '/ip dns cache flush',
      },
    ],
  },
  {
    name: 'SNMP_V2C_MONITOREO_NOC',
    category: 'SECURITY',
    description:
      'Configura comunidad SNMP v2c para supervisión y telemetría desde el Wallboard NOC.',
    requires_safemode: true,
    variables_schema: [
      {
        key: 'snmp_community',
        label: 'Nombre de Comunidad SNMP',
        default_val: 'RoSGrid_NOC',
        var_type: 'string',
      },
      {
        key: 'snmp_addresses',
        label: 'Subredes autorizadas (separadas por coma)',
        default_val: '10.0.0.0/8,192.168.0.0/16',
        var_type: 'string',
      },
    ],
    rest_steps_template: [
      {
        method: 'PATCH',
        endpoint: 'snmp',
        payload: { enabled: 'yes' },
        cli_command: '/snmp set enabled=yes',
      },
      {
        method: 'PATCH',
        endpoint: 'snmp/community/*0',
        payload: { name: '{{ snmp_community }}', addresses: '{{ snmp_addresses }}' },
        cli_command:
          '/snmp community set [find default=yes] name={{ snmp_community }} addresses={{ snmp_addresses }}',
      },
    ],
  },
];
