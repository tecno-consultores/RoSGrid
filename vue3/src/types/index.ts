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

export interface TenantItem {
  id: string;
  slug: string;
  name: string;
  tax_id?: string;
  status: 'ACTIVE' | 'SUSPENDED';
  max_routers_quota: number;
  max_users_quota: number;
  active_routers_count: number;
  active_users_count: number;
  default_safemode_seconds: number;
  created_at?: string;
}

export interface UserManagementItem {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role: SystemRole;
  totp_enabled: boolean;
  is_active: boolean;
  allowed_cidr_list?: string[];
  has_all_routers_access: boolean;
  assigned_router_ids?: string[];
  created_at?: string;
}

export interface RouterPermissionItem {
  router_id: string;
  router_name: string;
  network_role?: string;
  tag?: string;
  can_read: boolean;
  can_write_layer1: boolean;
  can_write_layer2: boolean;
  can_execute_diagnostics: boolean;
  can_trigger_backup: boolean;
  can_reboot: boolean;
  bypass_maker_checker: boolean;
}

export interface ActiveSessionItem {
  session_id: string;
  user_id: string;
  username: string;
  full_name?: string;
  role: SystemRole;
  ip_address: string;
  user_agent: string;
  current_router_id?: string;
  current_router_name?: string;
  current_view_path?: string;
  created_at: string;
  last_active_at: string;
  seconds_since_active: number;
}

export interface CsvDryRunRow {
  line: number;
  is_valid: boolean;
  display_name: string;
  ip_address: string;
  serial_number: string;
  error?: string;
}

export interface CsvDryRunResponse {
  total_rows: number;
  valid_rows_count: number;
  invalid_rows_count: number;
  rows: CsvDryRunRow[];
}

export interface VaultSecretData {
  router_id: string;
  api_username: string;
  current_password?: string;
  previous_password?: string;
  last_rotated_at?: string;
  next_rotation_due_at?: string;
  auto_purge_seconds: number;
}
