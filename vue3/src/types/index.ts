// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

export type SystemRole =
  | 'SUPERADMIN_GLOBAL'
  | 'TENANT_ADMIN'
  | 'SUPERVISOR'
  | 'SUPPORT_L3'
  | 'SUPPORT_L2'
  | 'SUPPORT_L1'
  | 'FIELD_TECH'
  | 'INVENTORY_MANAGER'
  | 'SECURITY_OFFICER'
  | 'BILLING_ADMIN'
  | 'NOC_MONITOR'
  | 'AUDITOR'
  | 'SERVICE_ACCOUNT';

export interface RbacRoleItem {
  role: string;
  title: string;
  description: string;
  level: number;
  badge_color: string;
  is_system_reserved: boolean;
  has_custom_overrides: boolean;
  permissions: Record<string, string>;
}

export interface RbacActionItem {
  key: string;
  label: string;
  category: string;
  description: string;
}

export interface TenantFeatureFlags {
  isp_module_enabled: boolean;
  bgp_looking_glass_enabled: boolean;
  sfp_ddm_telemetry_enabled: boolean;
  ipfix_analytics_enabled: boolean;
  enforce_maker_checker: boolean;
  auto_safemode_enforced: boolean;
  ai_mcp_integration_enabled: boolean;
  nightly_backups_enabled: boolean;
  outbound_webhooks_enabled: boolean;
  config_drift_monitoring_enabled: boolean;
  cis_audit_enabled: boolean;
  sdwan_orchestrator_enabled: boolean;
  capsman_wifi_enabled: boolean;
  sla_tracker_enabled: boolean;
  mass_outage_threshold: number;
  default_locale: string;
}

export interface UserInfo {
  id: string;
  email: string;
  username: string;
  tenant_id: string;
  tenant_slug: string;
  role: SystemRole;
  totp_enabled: boolean;
  assigned_router_ids?: string[];
  features?: Partial<TenantFeatureFlags>;
  tenant_feature_flags?: Partial<TenantFeatureFlags> | Record<string, boolean>;
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
  features?: Partial<TenantFeatureFlags>;
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
    | 'input'
    | 'forward'
    | 'output'
    | 'prerouting'
    | 'postrouting'
    | 'srcnat'
    | 'dstnat'
    | (string & {});
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
  state: 'established' | 'connect' | 'active' | 'idle' | (string & {});
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
  has_binary_backup?: boolean;
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

// ============================================================================
// IPAM & FIELD OPS TYPES
// ============================================================================

export type IPFamily = 'IPv4' | 'IPv6';
export type IPPrefixRole =
  | 'CGNAT'
  | 'PUBLIC_DYNAMIC'
  | 'PUBLIC_STATIC'
  | 'INFRA_P2P'
  | 'LOOPBACK'
  | 'CUSTOMER_RESIDENTIAL'
  | 'CUSTOMER_CORPORATE'
  | 'MGMT';

export type IPPrefixStatus = 'ACTIVE' | 'RESERVED' | 'DEPRECATED';
export type IPAddressStatus =
  | 'ALLOCATED'
  | 'RESERVED'
  | 'SOFT_LOCKED'
  | 'DHCP_STATIC'
  | 'DHCP_DYNAMIC'
  | 'QUARANTINE'
  | 'DEPRECATED';

export type CustomerServiceType = 'PPPOE' | 'DHCP' | 'STATIC';
export type AuthBackend = 'LOCAL_SECRET' | 'RADIUS';
export type ONUMode = 'ROUTER' | 'BRIDGE' | 'UNKNOWN';
export type CustomerServiceStatus = 'ACTIVE' | 'PENDING_INSTALL' | 'SUSPENDED' | 'TERMINATED';
export type FieldOrderStatus = 'ASSIGNED' | 'IN_PROGRESS' | 'CERTIFIED' | 'FAILED' | 'CANCELLED';
export type FiberCutStatus = 'DETECTED' | 'INVESTIGATING' | 'RESOLVED';

export interface IPAMVrf {
  id: string;
  tenant_id: string;
  name: string;
  route_distinguisher?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface IPAMPrefix {
  id: string;
  tenant_id: string;
  vrf_id: string;
  parent_id?: string;
  prefix: string;
  ip_family: IPFamily;
  role: IPPrefixRole;
  status: IPPrefixStatus;
  is_pool: boolean;
  default_child_prefix_len?: number;
  utilization_pct: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface IPAMAddress {
  id: string;
  tenant_id: string;
  prefix_id: string;
  address: string;
  ip_family: IPFamily;
  status: IPAddressStatus;
  router_id?: string;
  interface_name?: string;
  mac_address?: string;
  dns_ptr?: string;
  description?: string;
  soft_lock_until?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerService {
  id: string;
  tenant_id: string;
  router_id: string;
  customer_name: string;
  customer_code?: string;
  service_type: CustomerServiceType;
  auth_backend: AuthBackend;
  pppoe_username?: string;
  ipv4_address_id?: string;
  ipv6_delegated_prefix?: string;
  onu_mode: ONUMode;
  onu_mac_address?: string;
  onu_serial_number?: string;
  cpe_wifi_mac_address?: string;
  pon_port?: string;
  optical_box?: string;
  last_reachability_status: string;
  last_seen_at?: string;
  status: CustomerServiceStatus;
  physical_address?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
  updated_at: string;
}

export interface FieldOrder {
  id: string;
  tenant_id: string;
  customer_service_id: string;
  assigned_tech_id?: string;
  status: FieldOrderStatus;
  onu_scanned_serial?: string;
  onu_scanned_mac?: string;
  detected_mode?: string;
  ping_avg_ms?: number;
  ping_loss_pct?: number;
  traffic_rx_kbps?: number;
  traffic_tx_kbps?: number;
  tech_latitude?: number;
  tech_longitude?: number;
  customer_signature_svg?: string;
  notes?: string;
  certified_at?: string;
  created_at: string;
  updated_at: string;
}

export interface FieldVerifyResult {
  customer_service_id: string;
  session_active: boolean;
  connection_type: string;
  uptime_seconds: number;
  assigned_ipv4?: string;
  assigned_ipv6_prefix?: string;
  detected_mac?: string;
  detected_mode: string;
  ping_success: boolean;
  ping_avg_ms?: number;
  ping_loss_pct: number;
  traffic_rx_kbps: number;
  traffic_tx_kbps: number;
  status_summary: string;
}

export interface FiberCutIncident {
  id: string;
  tenant_id: string;
  router_id: string;
  pon_port: string;
  optical_box?: string;
  affected_onus_count: number;
  status: FiberCutStatus;
  incident_summary: string;
  detected_at: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface BandwidthProfileItem {
  id: string;
  tenant_id: string;
  name: string;
  rate_down_kbps: number;
  rate_up_kbps: number;
  burst_down_kbps: number;
  burst_up_kbps: number;
  burst_threshold_down_kbps: number;
  burst_threshold_up_kbps: number;
  burst_time_seconds: number;
  priority: number;
  queue_type: string;
  created_at: string;
  updated_at: string;
}

export interface ChangeRateLimitRequest {
  bandwidth_profile_id: string;
}

export interface NetworkServiceActionResponse {
  status: 'ISOLATED' | 'ALREADY_ISOLATED' | 'RESTORED' | 'ALREADY_ACTIVE' | 'RATE_LIMIT_UPDATED';
  service_id: string;
  endpoint_identifier?: string;
  message: string;
  bandwidth_profile_id?: string;
  bandwidth_profile_name?: string;
  rate_down_kbps?: number;
  rate_up_kbps?: number;
}

// ============================================================================
// HITO 18: DIAGNÓSTICO 360°, BGP LOOKING GLASS E IPFIX MITIGATION
// ============================================================================

export interface PingMtuStats {
  size: number;
  sent: number;
  received: number;
  packet_loss_pct: number;
  min_rtt_ms?: number | null;
  avg_rtt_ms?: number | null;
  max_rtt_ms?: number | null;
  jitter_ms?: number | null;
  df_bit: boolean;
}

export interface MultiMtuPingSummary {
  ping_64: PingMtuStats;
  ping_512: PingMtuStats;
  ping_1472: PingMtuStats;
  mtu_dispersion_detected: boolean;
  mtu_pass_1500: boolean;
}

export interface DisconnectLogItem {
  time?: string | null;
  topics?: string | null;
  message: string;
}

export interface DisconnectLogAnalysis {
  detected_reason: string;
  last_disconnect_time?: string | null;
  matched_logs: DisconnectLogItem[];
}

export interface TorchTopFlowItem {
  protocol: string;
  port?: number | null;
  src_address?: string | null;
  dst_address?: string | null;
  tx_rate_kbps: number;
  rx_rate_kbps: number;
}

export interface Endpoint360Request {
  router_id: string;
  target_ip: string;
  device_serial?: string | null;
  interface?: string | null;
}

export interface Endpoint360Response {
  router_id: string;
  target_ip: string;
  device_serial?: string | null;
  interface?: string | null;
  overall_status: 'OPTIMAL' | 'DEGRADED' | 'DOWN';
  multi_mtu: MultiMtuPingSummary;
  disconnect_analysis: DisconnectLogAnalysis;
  torch_top_flows: TorchTopFlowItem[];
  diagnostic_timestamp: string;
  raw_details?: Record<string, unknown>;
}

export interface BgpLookingGlassRouteItem {
  prefix: string;
  gateway: string;
  immediate_gw?: string | null;
  as_path: string;
  communities: string[];
  scope?: number | null;
  active: boolean;
  protocol: string;
  uptime?: string | null;
  attributes?: Record<string, unknown>;
}

export interface BgpLookingGlassRouteResponse {
  router_id: string;
  prefix: string;
  total_routes: number;
  routes: BgpLookingGlassRouteItem[];
}

export interface BgpLookingGlassAdvertisedItem {
  peer: string;
  prefix: string;
  nexthop: string;
  as_path?: string | null;
  origin?: string | null;
  communities: string[];
}

export interface BgpLookingGlassAdvertisedResponse {
  router_id: string;
  peer: string;
  total_advertised: number;
  advertisements: BgpLookingGlassAdvertisedItem[];
}

export interface TrafficAnomalyItem {
  ip_address: string;
  connection_count: number;
  estimated_pps: number;
  protocols: string[];
  anomaly_type: 'HIGH_CONNECTION_COUNT' | 'HIGH_PPS_BURST' | 'POSSIBLE_SYN_FLOOD';
  severity: 'WARNING' | 'HIGH' | 'CRITICAL';
}

export interface TrafficAnomaliesResponse {
  router_id: string;
  threshold_pps: number;
  threshold_conns: number;
  anomalies_detected: number;
  items: TrafficAnomalyItem[];
}

export interface TrafficMitigationRequest {
  router_id: string;
  target_ip: string;
  action: 'fast_drop' | 'blackhole';
  comment?: string;
  duration_seconds?: number;
}

export interface TrafficMitigationResponse {
  status: string;
  router_id: string;
  target_ip: string;
  action_taken: string;
  rule_or_list_id: string;
  safemode_applied: boolean;
  audit_event: string;
}
