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
  api_base_url?: string;
  api_port: number;
  tags?: string[] | Array<{ id?: string; tag: string }>;
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

export interface SfpOpticalDdmInfo {
  interface_name: string;
  tx_power_dbm: number;
  rx_power_dbm: number;
  optical_health: 'OPTIMAL' | 'WARNING' | 'CRITICAL_LOW_LIGHT';
  temperature_c: number;
  voltage_v: number;
  wavelength_nm?: number;
}

export interface FirewallRuleItem {
  id: string;
  chain:
    'input' | 'forward' | 'output' | 'prerouting' | 'postrouting' | 'srcnat' | 'dstnat' | string;
  action: string;
  src_address?: string;
  dst_address?: string;
  protocol?: string;
  dst_port?: string;
  bytes: number;
  packets: number;
  comment?: string;
  disabled: boolean;
  dynamic: boolean;
  invalid: boolean;
}

export interface BgpSessionItem {
  id: string;
  name: string;
  remote_address: string;
  remote_as: number;
  state: 'established' | 'connect' | 'active' | 'idle' | string;
  uptime: string;
  prefixes_received: number;
  prefixes_sent: number;
}

export interface PppActiveSessionItem {
  id: string;
  name: string;
  service: string;
  caller_id?: string;
  address: string;
  uptime: string;
  encoding?: string;
}

export interface SimpleQueueItem {
  id: string;
  name: string;
  target: string;
  max_limit: string;
  burst_limit?: string;
  bytes_in: number;
  bytes_out: number;
  packets_in: number;
  packets_out: number;
  disabled: boolean;
}

export interface DiagnosticLogItem {
  id: string;
  time: string;
  topics: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

export interface ApprovalRequestItem {
  id: string;
  requested_by: string;
  requested_by_username: string;
  requested_by_role: SystemRole;
  action_type: string;
  router_id: string;
  router_name: string;
  justification: string;
  previous_state_snapshot: Record<string, unknown>;
  request_payload: Record<string, unknown>;
  status: 'AWAITING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  created_at: string;
  reviewed_at?: string;
  review_comment?: string;
}

export interface BackupItem {
  id: string;
  router_id: string;
  filename: string;
  ros_version_at_backup: string;
  sha256_hash: string;
  lines_added: number;
  lines_removed: number;
  created_at: string;
  last_verified_identical_at?: string;
  size_bytes?: number;
}

export interface BulkJobItem {
  id: string;
  title: string;
  template_id?: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'ROLLED_BACK' | 'FAILED';
  target_count: number;
  success_count: number;
  failed_count: number;
  created_at: string;
  executed_by: string;
}

export interface AuditLogItem {
  id: string;
  actor_id: string;
  actor_username: string;
  actor_role: SystemRole;
  action_category: string;
  action_name: string;
  router_id?: string;
  router_name?: string;
  source_ip: string;
  http_status: number;
  id_key: string;
  before_state?: Record<string, unknown>;
  after_state?: Record<string, unknown>;
  prev_record_hash: string;
  record_sha256_hash: string;
  created_at: string;
}

export interface Layer2CatalogItem {
  ros_path: string;
  title: string;
  category: string;
  is_singleton: boolean;
}

export interface Layer2ResourceResponse {
  ros_path: string;
  title: string;
  is_singleton: boolean;
  columns_schema: Array<{ key: string; label: string; type: string }>;
  items: Array<Record<string, unknown>>;
  form_data?: Record<string, unknown>;
}
