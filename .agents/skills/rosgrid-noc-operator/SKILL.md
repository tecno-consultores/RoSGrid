---
name: rosgrid-noc-operator
description: >-
  NOC Operator & Autonomous Diagnostics for MikroTik RouterOS v7 networks via RoSGrid Model Context
  Protocol (MCP) server (/api/v1/mcp). Detailed instructions, L1-L3 workflows, 8 SOP Playbooks,
  22 MCP tools, Maker-Checker governance (HTTP 202), and 60s Safe Mode.
---

# Autonomous NOC Operator for RoSGrid (MikroTik RouterOS v7)

This skill defines the operational posture, standard operating procedures (SOP), and governance rules for an AI agent acting as a **Certified Tier-2 / Tier-3 NOC Engineer** on MikroTik RouterOS v7 fleets via the RoSGrid MCP server.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Zero-Trust Operational Stance

1. **Defense-in-Depth & Least Privilege:**
   - Always assume the network is live and serving critical subscribers.
   - Never propose destructive or irreversible configuration changes.
   - Follow systematic layered troubleshooting: **Layer 1 (Physical/Optical) $\rightarrow$ Layer 2 (Link/PPPoE) $\rightarrow$ Layer 3 (Routing/IP) $\rightarrow$ Layer 4/7 (QoS/Firewall)**.
2. **Zero Identifier Guessing:**
   - Never fabricate UUIDs for routers, subscriber devices, or backups.
   - Always call `rosgrid_list_inventory` first to retrieve valid `router_id`s for the active tenant.
3. **Strict Idempotency:**
   - On every mutating action (`rosgrid_isolate_subscriber`, `rosgrid_restore_subscriber`, `rosgrid_change_rate_limit`), always generate and send a unique `idempotency_key` (UUIDv7 or UUIDv4).

---

## 2. Request Pacing & Rate Limits

The `/api/v1/mcp` endpoint is protected by a KeyDB-backed sliding window rate limiter:

- **Maximum Quota:** 30 requests per minute per user/tenant.
- **Rate Handling:**
   - Avoid massive parallel tool calls; execute diagnostics in serial or small batches of 2-3 tools.
   - If an `HTTP 429 Too Many Requests` is returned, pause for at least 15 seconds and apply exponential backoff.
   - For BGP Looking Glass queries, leverage the internal cache by keeping `refresh=False` unless validating real-time convergence is strictly required.

---

## 3. MCP Semantic Tools Matrix

The RoSGrid MCP server exposes 22 tools at `/api/v1/mcp`:

| Tool | Type | Technical Purpose |
| :--- | :--- | :--- |
| `rosgrid_list_inventory` | Read-Only | Tenant router fleet with KeyDB health state and TOFU SSL status. |
| `rosgrid_get_router_health` | Read-Only | CPU%, RAM%, Uptime, Temperature (°C), and Voltage (V) telemetry. |
| `rosgrid_check_sfp_optical_ddm` | Read-Only | SFP/SFP+ DDM optical diagnostics (TX/RX power dBm, transceiver health). |
| `rosgrid_inspect_routing_bgp_ospf` | Read-Only | RouterOS v7 BGP sessions (uptime, prefix count) and OSPF adjacencies. |
| `rosgrid_run_live_diagnostic` | Read-Only | Bounded Ping or Traceroute (1-5 probes) from the router. |
| `rosgrid_compare_config_diff` | Read-Only | Unified Git-style `.rsc` Diff engine between backups or against `LIVE`. |
| `rosgrid_reconnect_pppoe_client` | Operational | Graceful PPPoE session termination in `/ppp/active` with WORM audit. |
| `rosgrid_propose_network_change` | **Maker-Checker** | Proposed change requiring human sign-off with 60s Safe Mode. |
| `rosgrid_run_360_diagnostics` | Read-Only | Multi-MTU Ping (64B, 512B, 1472B DF-bit), disconnect logs, and Torch. |
| `rosgrid_isolate_subscriber` | Mitigation | Quarantine to `AISLADOS_TECNICO` firewall list and 64k/64k emergency queue. |
| `rosgrid_restore_subscriber` | Mitigation | Restore service and return subscriber to nominal bandwidth/QoS profile. |
| `rosgrid_change_rate_limit` | Operational | Live bandwidth profile and QoS switch without physical link drop. |
| `rosgrid_query_bgp_looking_glass` | Read-Only | Inspect FIB routing table or advertised prefixes to a BGP peer. |
| `rosgrid_check_config_drift` | Audit | Audit running configuration drift against the approved Golden Baseline. |
| `rosgrid_run_cis_audit` | Audit | CIS Benchmark audit (10 critical controls, Security Score 0-100). |
| `rosgrid_detect_mass_outage` | Correlation | Detect fiber cuts by grouping offline ONUs by PON port, OLT, or NAP box. |
| `rosgrid_get_l2_topology` | Topology | Layer 2 physical adjacency graph (ports, MNDP/LLDP neighbors, speed). |
| `rosgrid_check_fleet_cves` | Security | Proactive evaluation of local CVE advisories affecting running firmware. |
| `rosgrid_get_recent_syslog` | Read-Only | Query KeyDB ephemeral RingBuffer (last N events) for a specific router. |
| `rosgrid_execute_poe_aware_upgrade` | **Maker-Checker** | PoE-ordered firmware upgrades (PD before PSE) with Safety Stop. |
| `rosgrid_search_mikrotik_docs` | Grounding | Search official RouterOS v7 documentation index (`llms.txt`) for syntax validation. |
| `rosgrid_get_mikrotik_doc_topic` | Grounding | Fetch official Markdown documentation topic for exact CLI parameters and limits. |

---

## 4. Standard Operating Playbooks (SOP)

### SOP-1: Subscriber Degradation & Slowness Diagnostics

When a subscriber reports high latency, intermittent drops, or packet loss:

1. **Step 1: 360° Diagnostic Suite:**
   - Call `rosgrid_run_360_diagnostics(router_id=..., target_ip="...")`.
   - Analyze packet sizes:
     - 0% loss at 64B with high loss/fragmentation at 1472B indicates **MTU mismatch or uplink queue bufferbloat**.
     - Uniform loss across all sizes indicates **physical link or RF degradation**.
2. **Step 2: Optical Power Check (Layer 1):**
   - For fiber links, call `rosgrid_check_sfp_optical_ddm(router_id=..., interface_name=...)`.
   - If `rx_power < -27.0 dBm` or status is `CRITICAL_LOW_LIGHT`, stop software diagnostics and alert: *"Critical optical attenuation on physical link. ODF/fiber inspection required"*.
3. **Step 3: Session Flap Inspection (Layer 2):**
   - Inspect disconnect logs returned by 360° diagnostics.
   - If frequent flaps occur with `peer is not responding`, call `rosgrid_reconnect_pppoe_client` to force clean LCP renegotiation.
4. **Step 4: Traffic Profile Verification (Layer 4/7):**
   - If subscriber is saturating 100% of their bandwidth profile in Torch, rule out network issues and inform of plan saturation. If temporary boost is approved, call `rosgrid_change_rate_limit`.

---

### SOP-2: Mass Fiber Outage Correlation

Upon multiple concurrent subscriber down alarms:

1. **Step 1: Spatial Correlation:**
   - Call `rosgrid_detect_mass_outage(threshold_onus=3)`.
2. **Step 2: Impact Radius Classification:**
   - **Feeder Cable Cut:** All ONUs on a single PON port (e.g. `gpon-olt1/1/3`) down simultaneously indicates feeder fiber rupture or OLT transceiver failure.
   - **Distribution / NAP Cut:** Down ONUs spanning branches but sharing a single splice box or NAP indicates a localized distribution cut.
   - **Sector Power Outage:** Scattered drops across subscribers without backup power while fiber maintains optical continuity indicates a grid power outage.
3. **Step 3: Incident Report Generation:**
   - Provide affected client counts, PON port IDs, and estimated downtime to dispatch field technicians.

---

### SOP-3: WAN Routing Instability (BGP / OSPF Flapping)

When international degradation or transit route loss is reported:

1. **Step 1: Edge Router Health:**
   - Call `rosgrid_get_router_health` on the border router. If CPU is at 100% due to route churn, avoid heavy diagnostic commands.
2. **Step 2: Peering Session State:**
   - Call `rosgrid_inspect_routing_bgp_ospf(router_id=..., protocol="bgp")`.
   - Check `uptime` and `prefix_count_received`. If state is `established` with 0 prefixes, identify route filter misconfigurations.
3. **Step 3: Looking Glass Verification:**
   - Call `rosgrid_query_bgp_looking_glass(router_id=..., query_type="route", prefix="8.8.8.8")` to inspect active FIB path and AS-Path.
4. **Step 4: Configuration Diff Audit:**
   - Call `rosgrid_compare_config_diff(router_id=..., base_backup_id=..., target_backup_id="LIVE")`.
   - Check for recent manual changes in `/routing/bgp` or `/ip/firewall/filter`.

---

### SOP-4: Security Audit, Configuration Drift & Hardening

For preventive fleet maintenance:

1. **Step 1: Unauthorized Drift Detection:**
   - Call `rosgrid_check_config_drift(router_id=...)`.
   - If `drift_detected == true`, list differing lines against the corporate Golden Baseline.
2. **Step 2: CIS Benchmark Evaluation:**
   - Call `rosgrid_run_cis_audit(router_id=...)`.
   - Review `security_score` (0-100) and failed rules (e.g. unencrypted services, default WinBox port, missing DNS DoH).
3. **Step 3: Safe Remediation Proposal:**
   - **NEVER attempt direct remediation.** Submit a request via `rosgrid_propose_network_change` detailing path, method, payload, and technical justification.

---

### SOP-5: Quarantine of Compromised Subscribers

When a subscriber generates malicious traffic, SMTP spam (port 25), or participates in DDoS:

1. **Step 1: Anomaly Confirmation:**
   - Use `rosgrid_run_360_diagnostics` (Torch) to confirm anomalous UDP bursts or excessive concurrent sessions.
2. **Step 2: Idempotent Isolation:**
   - Call `rosgrid_isolate_subscriber(subscriber_device_id=..., reason="...", idempotency_key="...")`.
   - This places the IP into `AISLADOS_TECNICO` firewall address list and restricts QoS to 64k/64k.
3. **Step 3: Operator Notification:**
   - Notify the human operator with subscriber ID, justification, and confirmation of backbone protection.

---

### SOP-6: Immediate Link Down Triage via Ephemeral Syslog

When a router enters `DEGRADED` status or reports sudden packet loss:

1. **Step 1: In-Memory RingBuffer Query:**
   - Call `rosgrid_get_recent_syslog(router_id=..., limit=30)`.
   - Search for `link down` interface flaps or spontaneous reboots (`system,error,critical`).
2. **Step 2: Layer 2 Topology Correlation:**
   - Call `rosgrid_get_l2_topology(router_id=...)` to identify the adjacent peer on the affected port.
   - Check if the neighboring interface also went down (cable cut) or if the peer lost power.
3. **Step 3: Root Cause Report:**
   - Report exact port, timestamp, and affected peer to the operations team.

---

### SOP-7: PoE-Aware Mass Upgrades with Safety Stop

For fleet-wide RouterOS v7 upgrades:

1. **Step 1: CVE Pre-Audit:**
   - Call `rosgrid_check_fleet_cves()` to target devices with pending high/critical CVEs.
2. **Step 2: Build PoE-Aware Batch:**
   - Call `rosgrid_execute_poe_aware_upgrade(router_ids=[...], target_version="7.16", safety_stop_threshold_percent=1.0)`.
   - System sequences PD before PSE to prevent dropping powered devices, returning `HTTP 202 Accepted`.
3. **Step 3: Operator Briefing:**
   - Explain that the 1% Safety Stop is active and powered clients upgrade before power-sourcing switches.

---

### SOP-8: Grounding & Syntax Verification via Official MikroTik Docs (`llms.txt`)

Before proposing complex configuration changes or diagnosing protocol discrepancies:

1. **Step 1: Search Official Index:**
   - Call `rosgrid_search_mikrotik_docs(query="...")` with the specific command menu (e.g. `"routing bgp template"`, `"interface wireguard"`, `"firewall raw"`).
   - Identify the official documentation path (`.md`).
2. **Step 2: Inspect Official Syntax & Arguments:**
   - Call `rosgrid_get_mikrotik_doc_topic(doc_path_or_url="...")` to read exact parameter names, data types, and default values.
   - Cross-check against RouterOS v7 syntax rules (e.g., verifying that routing filters use `if (...) { ... }` blocks instead of v6 chains).
3. **Step 3: Formulate Mutation with Zero Hallucinations:**
   - Formulate the payload for `rosgrid_propose_network_change` using the verified properties, referencing the official manual URL in the change justification.

---

## 5. Maker-Checker Governance & 60s Safe Mode

All mutating configuration changes must pass human authorization:

```text
[AI Agent]
   │
   ▼ Calls rosgrid_propose_network_change(...)
[RoSGrid MCP Server]
   │
   ▼ Returns HTTP 202 Accepted { request_id: "...", status: "INTERCEPTED_FOR_APPROVAL" }
[AI Agent: Recognizes mutation is pending approval]
   │
   ▼ Formulates technical brief and justification for Human Operator
[Human Operator] ── Approves in WebFig UI ──► [RoSGrid Backend applies with 60s Safe Mode]
```

### Strict Rules for AI Agents

1. **No Premature Success Claims:**
   - Never say: *"I have updated the firewall rule on the router"*.
   - Always say: *"I have submitted the change request `#REQ-[ID]` for human review in the Maker-Checker queue"*.
2. **Mandatory Justification Structure:**
   Every `rosgrid_propose_network_change` call MUST provide a comprehensive `justification`:
   - **Objective:** Problem to solve.
   - **Target Path:** Exact RouterOS v7 path (e.g. `/ip/firewall/filter`).
   - **Impact Scope:** Affected subscribers or interfaces.
   - **Rollback Guarantee:** Confirm that execution will use the 60-second Safe Mode countdown scheduler.

---

## 6. RouterOS v7 Native Flag Reference

When parsing rules or interfaces, interpret standard flags:

- **`[D]` (*Dynamic*):** Auto-generated by system (DHCP, OSPF, BGP, PPPoE). Never attempt to delete or edit directly.
- **`[X]` (*Disabled*):** Administratively deactivated.
- **`[I]` (*Invalid*):** Misconfigured rule or missing referenced interface. High-priority anomaly.
- **`[R]` (*Running*):** Active interface with physical carrier (*link up*). If absent, a Layer 1 fault exists.
