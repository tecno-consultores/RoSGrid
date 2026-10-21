# RoSGrid MCP Tools Catalog (`/api/v1/mcp`)

This document details the input parameters, schemas, and usage directives for all 20 MCP tools exposed by the RoSGrid server for AI agents.

---

## 1. Observability & Fleet Inventory

### `rosgrid_list_inventory`
- **Description:** Lists authorized MikroTik routers for the tenant with ID, name, identity, model, RouterOS v7 version, KeyDB health status, and TOFU SSL certificate state.
- **Parameters:**
  - `status_filter` (string, optional): Filter by status (e.g. `ONLINE`, `OFFLINE`, `DEGRADED_HIGH_LOAD`).
  - `role_filter` (string, optional): Filter by label or role (e.g. `CORE_BGP`, `DISTRIBUTION`, `ACCESS_PPPOE`).

### `rosgrid_get_router_health`
- **Description:** Queries ephemeral KeyDB state and `/rest/system/resource` + `/rest/system/health`, returning CPU%, RAM%, disk space, Uptime, Temperature (°C), and Voltage (V).
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.

### `rosgrid_check_sfp_optical_ddm`
- **Description:** Queries DDM optical diagnostics for SFP/SFP+ transceivers (`tx-power` and `rx-power` in dBm, laser temperature, and health rating: `OPTIMAL`, `WARNING`, `CRITICAL_LOW_LIGHT`).
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `interface_name` (string, required): SFP interface name (e.g. `sfp-sfpplus1`).

---

## 2. Routing & Network Diagnostics

### `rosgrid_inspect_routing_bgp_ospf`
- **Description:** Summarizes RouterOS v7 BGP sessions (state `established`, received prefix count, uptime) and active OSPF adjacencies.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `protocol` (string enum: `["bgp", "ospf", "all"]`, optional, default `all`).

### `rosgrid_query_bgp_looking_glass`
- **Description:** Queries FIB routing table or advertised prefixes to a specific BGP neighbor without interactive SSH.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `query_type` (string enum: `["route", "advertised"]`, optional, default `route`).
  - `prefix` (string, optional): IPv4/IPv6 prefix or CIDR (e.g. `1.1.1.0/24`).
  - `peer_session` (string, optional): BGP peer name or IP.
  - `refresh` (boolean, optional, default `false`): If `true`, bypasses KeyDB cache and directly queries the router.

### `rosgrid_run_live_diagnostic`
- **Description:** Executes bounded Ping or Traceroute from the router to a target host, reporting latency (min, avg, max) and packet loss percentage.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `tool` (string enum: `["ping", "traceroute"]`, required).
  - `target` (string, required): Destination IP or FQDN.
  - `count` (integer, optional, range 1-5, default 4): Number of probes.

### `rosgrid_run_360_diagnostics`
- **Description:** Comprehensive 360° diagnostics suite: multi-MTU Ping (64B, 512B, 1472B DF-bit to diagnose MTU/fragmentation), disconnect logs from `/log`, and Torch active flow sampling.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `target_ip` (string, required): Subscriber or CPE IP address.
  - `device_serial` (string, optional): ONU or CPE serial number.
  - `interface` (string, optional): Interface name for Torch sampling (e.g. `ether1`).

---

## 3. Outside Plant & Outage Correlation

### `rosgrid_detect_mass_outage`
- **Description:** Spatial correlation engine detecting mass fiber cuts by clustering offline ONUs by PON port, OLT, or NAP box.
- **Parameters:**
  - `threshold_onus` (integer, optional, min 1, default 3): Minimum down ONUs in same cluster to declare outage.
  - `tenant_id` (string UUID, optional).

---

## 4. Subscriber Management & Service Mitigation

### `rosgrid_reconnect_pppoe_client`
- **Description:** Locates active subscriber session in `/ppp/active`, requests graceful termination to trigger clean LCP renegotiation, and logs to immutable WORM audit trail.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `pppoe_username` (string, required): Subscriber PPPoE username.
  - `reason` (string, required): Technical reason for reset.

### `rosgrid_isolate_subscriber`
- **Description:** Quarantines a compromised subscriber: adds IP to `AISLADOS_TECNICO` firewall list and switches QoS queue to 64k/64k.
- **Parameters:**
  - `subscriber_device_id` (string UUID, required): Subscriber device or service ID.
  - `reason` (string, optional): Reason for isolation (e.g. "Outbound port 25 SMTP spam flood").
  - `idempotency_key` (string UUID, optional): Idempotency key to prevent duplicates.

### `rosgrid_restore_subscriber`
- **Description:** Restores service for a quarantined subscriber: removes from `AISLADOS_TECNICO` and re-applies nominal bandwidth/QoS profile.
- **Parameters:**
  - `subscriber_device_id` (string UUID, required): Subscriber device ID.
  - `idempotency_key` (string UUID, optional): Idempotency key.

### `rosgrid_change_rate_limit`
- **Description:** Dynamically modifies subscriber bandwidth profile (Simple Queue / PCQ with Burst) without dropping physical link or resetting PPPoE session.
- **Parameters:**
  - `subscriber_device_id` (string UUID, required): Subscriber device ID.
  - `bandwidth_profile_id` (string UUID, required): New bandwidth profile ID.
  - `idempotency_key` (string UUID, optional): Idempotency key.

---

## 5. Configuration Drift, Diff & Security Audits

### `rosgrid_compare_config_diff`
- **Description:** Runs Git-style `unified_diff` across `.rsc` backups or against `LIVE` running configuration.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `base_backup_id` (string UUID, required): Origin backup ID.
  - `target_backup_id` (string UUID or `"LIVE"`, optional): Target backup ID or live config.

### `rosgrid_check_config_drift`
- **Description:** Audits configuration drift by comparing running router state against the approved corporate Golden Baseline.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.

### `rosgrid_run_cis_audit`
- **Description:** Executes automated CIS Benchmark security audit for RouterOS v7, evaluating 10 critical security controls and computing the Security Score (0-100).
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.

---

## 6. Governed Mutations & Maker-Checker

### `rosgrid_propose_network_change`
- **Description:** Submits a network mutation to the Maker-Checker authorization queue (returns `HTTP 202 Accepted`). Enforces 60-second Safe Mode upon human approval.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `category` (string, required): Change category (e.g. `FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE`, `ROUTING_BGP_OSPF_DEFAULT_CHANGE`).
  - `ros_path` (string, required): RouterOS REST path (e.g. `/ip/firewall/filter`, `/ip/service`).
  - `http_method` (string enum: `["POST", "PATCH", "DELETE", "PUT"]`, required).
  - `payload` (object, required): JSON object containing RouterOS v7 configuration attributes.
  - `justification` (string, required): Formal technical justification for the human approver.

---

## 7. Layer 2 Topology, PoE Automation & Ephemeral Syslog

### `rosgrid_get_l2_topology`
- **Description:** Queries Layer 2 physical interconnection graph discovered via MNDP, LLDP, and CDP. Returns verified port-to-port links (`RouterA:sfp1 <---> SwitchB:sfp24`), link state, and negotiated speed.
- **Parameters:**
  - `router_id` (string UUID, optional): When specified, filters direct adjacencies for that router; when omitted, returns full tenant topology.

### `rosgrid_check_fleet_cves`
- **Description:** Proactively evaluates active RouterOS versions against the local sovereign CVE vulnerability catalog.
- **Parameters:**
  - `router_id` (string UUID, optional): Filter by router ID.
  - `min_severity` (string enum: `["CRITICAL", "HIGH", "MEDIUM", "ALL"]`, optional, default `"HIGH"`).

### `rosgrid_get_recent_syslog`
- **Description:** Reads recent Syslog events from the volatile KeyDB RingBuffer (up to 500 events per router in RAM). Rapidly surfaces interface down flaps and kernel reboots.
- **Parameters:**
  - `router_id` (string UUID, required): Router identifier.
  - `limit` (integer, optional, range 10-100, default 30): Number of recent entries to return.
  - `topic_filter` (string, optional): Filter by topic (e.g. `"interface"`, `"route,bgp"`, `"system,error"`).

### `rosgrid_execute_poe_aware_upgrade`
- **Description:** Initiates mass firmware upgrade with PoE-aware topological ordering (PD devices before PSE switches) and automatic Safety Stop upon post-reboot failure. Enforces Maker-Checker workflow (`HTTP 202 Accepted`).
- **Parameters:**
  - `router_ids` (array of string UUID, required): Target router IDs.
  - `target_version` (string, required): Target RouterOS v7 version (e.g. `"7.16.1"`).
  - `safety_stop_threshold_percent` (float, optional, default 1.0): Failure percentage threshold to halt execution.
  - `justification` (string, required): Formal maintenance justification.
