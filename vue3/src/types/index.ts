// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

export type SystemRole =
  | 'SUPERADMIN_GLOBAL'
  | 'TENANT_ADMIN'
  | 'SUPERVISOR'
  | 'SUPPORT_L3'
  | 'SUPPORT_L2'
  | 'SUPPORT_L1'
  | 'INVENTORY_MANAGER'
  | 'SECURITY_OFFICER'
  | 'BILLING_ADMIN'
  | 'NOC_MONITOR'
  | 'AUDITOR';

export interface UserInfo {
  id: string;
  email: string;
  username: string;
  tenant_id: string;
  tenant_slug: string;
  role: SystemRole;
  totp_enabled: boolean;
  assigned_router_ids?: string[];
}

export type TableDensityMode = 'auto' | 'compact' | 'comfortable';
export type EffectiveTableDensity = 'compact' | 'comfortable';

export type ThemeMode = 'dark' | 'light' | 'noc-high-contrast';

export interface RouterItem {
  id: string;
  tenant_id: string;
  display_name: string;
  ros_identity?: string;
  ip_address: string;
  api_port: number;
  ros_version: string;
  architecture_name?: string;
  board_name?: string;
  serial_number?: string;
  model?: string;
  network_role?: string;
  latitude?: number;
  longitude?: number;
  admin_state: 'PROVISIONING' | 'PRODUCTION' | 'MAINTENANCE' | 'DECOMMISSIONED';
  is_reachable: boolean;
  last_seen_at?: string;
  ssl_trust_status?: 'PENDING_TOFU' | 'TRUSTED_PINNED' | 'FINGERPRINT_MISMATCH';
}

export interface MaintenanceWindowItem {
  id: string;
  tenant_id: string;
  router_id?: string;
  target_tag?: string;
  title: string;
  reason: string;
  starts_at: string;
  ends_at: string;
  suppress_alerts: boolean;
  is_cancelled: boolean;
}

export interface RouterTabItem {
  tabId: string;
  routeName: string;
  label: string;
  icon?: string;
  params?: Record<string, string>;
  closable: boolean;
}

export interface TelemetryPoint {
  timestampEpoch: number;
  timestampIso: string;
  cpuLoadPct: number;
  freeMemoryPct: number;
  rxBps?: number;
  txBps?: number;
  temperatureC?: number;
}

export interface NocEventItem {
  id: string;
  eventName: string;
  routerId?: string;
  routerDisplayName?: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  timestampIso: string;
}

export interface TableColumn<T = Record<string, unknown>> {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  formatter?: (row: T) => string | number;
}

export interface TableRowFlags {
  dynamic?: boolean; // [D]
  disabled?: boolean; // [X]
  invalid?: boolean; // [I]
  invalidReason?: string;
  running?: boolean; // [R]
}
