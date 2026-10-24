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
  l2_topology_enabled?: boolean;
  syslog_collector_enabled?: boolean;
  cve_scanner_enabled?: boolean;
  prometheus_fleet_exporter_enabled?: boolean;
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
  syslog_active?: boolean;
  syslog_event_count?: number;
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
  is_service_account?: boolean;
  issued_by_username?: string;
  allowed_cidr_list?: string[];
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
  execution_result?: Record<string, unknown> | null;
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

export type ZeroMetricsState = 'OPTIMAL' | 'DEGRADED' | 'DOWN';

export interface SubscriberDeviceItem {
  id: string;
  tenant_id: string;
  router_id: string;
  service_type: string;
  auth_backend: string;
  endpoint_identifier?: string | null;
  pppoe_username?: string | null;
  ipv4_address_id?: string | null;
  ipv6_delegated_prefix?: string | null;
  bandwidth_profile_id?: string | null;
  assigned_ipv4?: string | null;
  onu_mode: 'ROUTER' | 'BRIDGE' | string;
  onu_mac_address?: string | null;
  device_serial?: string | null;
  onu_serial_number?: string | null;
  cpe_wifi_mac_address?: string | null;
  pon_port?: string | null;
  optical_box?: string | null;
  optical_box_id?: string | null;
  optical_box_port?: number | null;
  rx_optical_power_dbm?: number | null;
  drop_cable_meters?: number | null;
  is_custom_coordinates?: boolean;
  last_reachability_status?: string | null;
  last_seen_at?: string | null;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  customer_name?: string | null;
  customer_code?: string | null;
  physical_address?: string | null;
  created_at: string;
  updated_at: string;
  ping_latency_ms?: number | null;
  packet_loss_pct?: number | null;
  zero_metrics_state?: ZeroMetricsState;
}

export interface OpticalBoxItem {
  id: string;
  tenant_id: string;
  router_id: string;
  box_code: string;
  brand?: string | null;
  model?: string | null;
  capacity_ports: number;
  splitter_ratio: string;
  installation_type: string;
  physical_location?: string | null;
  input_power_dbm?: number | null;
  latitude: number;
  longitude: number;
  status: string;
  notes?: string | null;
  occupied_ports_count: number;
  available_ports_count: number;
  created_at: string;
  updated_at: string;
}

export interface OpticalBoxPortStatus {
  port_number: number;
  is_occupied: boolean;
  subscriber_id?: string | null;
  subscriber_identifier?: string | null;
  assigned_ipv4?: string | null;
  reachability_status: 'FREE' | 'ONLINE' | 'OFFLINE' | 'DEGRADED' | string;
  rx_power_dbm?: number | null;
}

export interface OpticalBoxDetailItem extends OpticalBoxItem {
  ports: OpticalBoxPortStatus[];
  subscribers: SubscriberDeviceItem[];
}

// ============================================================================
// Hito 20: Enterprise Fleet Management & Security Compliance
// ============================================================================

export interface GoldenConfigTemplate {
  id: string;
  tenant_id: string;
  name: string;
  network_role: string;
  baseline_rsc_content: string;
  enforce_strict_firewall: boolean;
  enforce_ntp_dns: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConfigDriftCheckResponse {
  router_id: string;
  router_name: string;
  network_role: string;
  drift_detected: boolean;
  baseline_template_name: string;
  added_lines: string[];
  removed_lines: string[];
  diff_unified: string;
  total_drift_lines: number;
  checked_at: string;
}

export interface ConfigDriftRevertRequest {
  router_id: string;
  template_id?: string | null;
  enforce_safemode?: boolean;
}

export interface ConfigDriftRevertResponse {
  router_id: string;
  status: string;
  executed_safemode: boolean;
  audit_log_id: string;
  remediation_summary: string;
}

export interface CisDirectiveResult {
  code: string;
  title: string;
  passed: boolean;
  weight: number;
  finding: string;
  remediation_cmd: string;
}

export interface CisAuditResponse {
  router_id: string;
  router_name: string;
  security_score: number;
  compliance_grade: string;
  total_directives: number;
  passed_directives: number;
  failed_directives: number;
  directives: CisDirectiveResult[];
  audited_at: string;
}

export interface CisAutoHardenRequest {
  router_id: string;
  directive_codes_to_apply?: string[] | null;
}

export interface CisAutoHardenResponse {
  router_id: string;
  new_security_score: number;
  applied_directives_count: number;
  executed_under_safemode: boolean;
  remediation_script: string;
  audit_log_id: string;
}

export interface SdwanSpokeTunnel {
  id: string;
  hub_router_id: string;
  spoke_router_id: string;
  spoke_name: string;
  interface_name: string;
  allocated_subnet: string;
  hub_endpoint: string;
  spoke_public_key: string;
  routing_protocol: string;
  multi_wan_failover_enabled: boolean;
  status: 'ACTIVE' | 'DEGRADED' | 'DOWN' | string;
  rx_bytes?: number;
  tx_bytes?: number;
  latency_ms?: number;
  created_at: string;
}

export interface SdwanTopologyResponse {
  tenant_id: string;
  total_spokes: number;
  active_spokes: number;
  degraded_spokes: number;
  down_spokes: number;
  tunnels: SdwanSpokeTunnel[];
}

export interface SdwanProvisionSpokeRequest {
  hub_router_id: string;
  spoke_router_id: string;
  spoke_name: string;
  allocated_subnet?: string | null;
  hub_endpoint?: string | null;
  spoke_public_key?: string | null;
  routing_protocol?: 'BGP' | 'OSPF' | 'STATIC' | string;
  multi_wan_failover_enabled?: boolean;
}

export interface SdwanMultiWanFailoverRequest {
  router_id: string;
  primary_wan_interface: string;
  backup_wan_interface: string;
  check_host: string;
  failover_threshold_ms: number;
}

export interface SdwanMultiWanFailoverResponse {
  router_id: string;
  failover_policy_deployed: boolean;
  netwatch_script_id: string;
  deployed_under_safemode: boolean;
}

export interface DhcpSnoopingState {
  bridge_name: string;
  dhcp_snooping_enabled: boolean;
  trusted_ports: string[];
  untrusted_ports: string[];
}

export interface DhcpSnoopingEnableRequest {
  router_id: string;
  bridge_name: string;
  trusted_ports: string[];
}

export interface RogueDhcpAlertItem {
  id: string;
  router_id: string;
  bridge_name: string;
  interface_name: string;
  rogue_server_mac: string;
  rogue_server_ip: string;
  detected_at: string;
  status: string;
}

export interface RogueDhcpIsolatePortRequest {
  router_id: string;
  interface_name: string;
  reason?: string;
}

export interface RogueDhcpIsolatePortResponse {
  router_id: string;
  interface_name: string;
  isolated: boolean;
  executed_under_safemode: boolean;
  audit_log_id: string;
}

export interface SlaMetricItem {
  id: string;
  router_id: string;
  target_host: string;
  target_name: string;
  uptime_percent: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  jitter_ms: number;
  packet_loss_pct: number;
  sla_threshold_ms: number;
  compliance_status: 'COMPLIANT' | 'BREACHED' | string;
  recorded_at: string;
}

export interface SlaProbeRunRequest {
  router_id: string;
  target_host: string;
  target_name?: string;
  count?: number;
  sla_threshold_ms?: number;
}

export interface SlaReportSummary {
  tenant_name: string;
  period: string;
  total_targets_monitored: number;
  global_uptime_percent: number;
  total_contract_breaches: number;
  total_downtime_minutes: number;
  metrics: SlaMetricItem[];
  exported_at: string;
}

export interface CapsmanOverviewResponse {
  router_id: string;
  capsman_running: boolean;
  active_radios_count: number;
  managed_aps_count: number;
  connected_clients_count: number;
}

export interface WifiSsidProfile {
  id: string;
  name: string;
  ssid: string;
  security_type: string;
  vlan_id?: number | null;
  client_isolation: boolean;
  rate_limit_profile?: string | null;
}

export interface WifiClientItem {
  mac_address: string;
  ip_address?: string | null;
  hostname?: string | null;
  ap_name: string;
  ssid: string;
  signal_rssi_dbm: number;
  snr_db: number;
  wifi_standard: string;
  tx_rate_mbps: number;
  rx_rate_mbps: number;
  fast_roaming_supported: boolean;
  connected_duration_seconds: number;
}

export interface GenerateMcpTokenRequest {
  expiry_days: number;
}

export interface McpTokenResponse {
  token: string;
  token_type: string;
  session_id: string;
  expires_at: string;
  expiry_days: number;
  user_id: string;
  username: string;
  tenant_slug: string;
  role: string;
  allowed_cidr_list: string[];
  issued_by: string;
}

export type AlertChannelType = 'TELEGRAM_BOT' | 'SMTP_EMAIL' | 'GENERIC_WEBHOOK';

export interface NotificationChannelItem {
  id: string;
  tenant_id: string;
  name: string;
  channel_type: AlertChannelType;
  is_enabled: boolean;
  subscribed_events: string[];
  created_at: string;
  updated_at: string;
}

export interface NotificationChannelCreateRequest {
  name: string;
  channel_type: AlertChannelType;
  is_enabled: boolean;
  config: Record<string, any>;
  subscribed_events: string[];
}

export interface NotificationChannelUpdateRequest {
  name?: string;
  is_enabled?: boolean;
  config?: Record<string, any>;
  subscribed_events?: string[];
}

export interface NotificationTestResponse {
  status: 'SUCCESS' | 'FAILED';
  detail: string;
}

// ==============================================================================
// Tipos para Automatización Táctica de Flota, Topología L2, Syslog y CVEs (Hito 23.5)
// ==============================================================================

export type CveSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CveItem {
  cve_id: string;
  title: string;
  cvss_score: number;
  severity: CveSeverity;
  affected_versions_expr: string;
  fixed_in_version: string;
  description_es: string;
  remediation: string;
  published_date: string;
}

export interface RouterCveEvaluation {
  router_id: string;
  display_name: string;
  ros_version: string | null;
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  max_cvss_score: number;
  vulnerabilities: CveItem[];
  recommended_target_version?: string | null;
}

export interface FleetCveSummary {
  total_evaluated_routers: number;
  vulnerable_routers_count: number;
  critical_routers_count: number;
  high_routers_count: number;
  total_unique_cves: number;
  summary_by_severity: Record<string, number>;
  vulnerable_routers: RouterCveEvaluation[];
  timestamp: string;
  last_synced_at?: string | null;
  cache_expires_at?: string | null;
  cache_ttl_seconds?: number | null;
  is_cache_fresh?: boolean;
  auto_synced?: boolean;
}

export interface CveSyncResponse {
  success: boolean;
  source_url: string;
  total_cves: number;
  updated_at: string;
  message: string;
}

export interface TopologyNode {
  id: string;
  display_name: string;
  ros_identity: string;
  model_name?: string | null;
  board_name?: string | null;
  ros_version?: string | null;
  status: string;
  ip_address: string;
  is_pse: boolean;
  x?: number;
  y?: number;
}

export interface TopologyEdge {
  id: string;
  source_router_id: string;
  source_interface: string;
  target_router_id: string;
  target_interface: string;
  link_speed?: string | null;
  is_poe_delivering: boolean;
  poe_power_watts?: number | null;
  protocol: string;
}

export interface L2TopologyResponse {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  total_nodes: number;
  total_edges: number;
  timestamp: string;
}

export interface SyslogEvent {
  timestamp: string;
  facility: string;
  severity: string;
  topics: string;
  message: string;
  is_critical: boolean;
  raw: string;
}

export interface RouterSyslogResponse {
  router_id: string;
  total_events: number;
  critical_count: number;
  events: SyslogEvent[];
}

export interface SyslogTemplateResponse {
  template_content: string;
  default_port: number;
  protocol: string;
  instructions: string;
}

export interface OperationalLock {
  technician_id: string;
  technician_name: string;
  action: string;
  locked_at: string;
  minutes_ago?: number;
}

export interface OperationalStatusResponse {
  device_id: string;
  is_locked: boolean;
  is_locked_by_other: boolean;
  technician_id?: string | null;
  technician_name?: string | null;
  action?: string | null;
  locked_at?: string | null;
  minutes_ago?: number;
  message?: string | null;
  root_cause?: {
    root_cause: string;
    root_cause_device_name?: string;
    message: string;
  } | null;
}

export interface SubscriberDevicePingResponse {
  device_id: string;
  assigned_ipv4?: string;
  last_reachability_status: string;
  ping_latency_ms?: number;
  packet_loss_pct?: number;
  message: string;
  is_cached?: boolean;
  cache_ttl_remaining?: number;
  status?: string;
  root_cause_device_name?: string | null;
  operational_lock?: OperationalLock | null;
}


