# MikroTik RouterOS v7 Native Flags & Identifiers Reference

Quick reference guide for AI agents to interpret RouterOS states and nomenclature returned in REST API (`/rest/*`) and MCP tool payloads.

---

## 1. Standard RouterOS Flags

In RouterOS configuration tables (firewall, interfaces, routes, queues, pools), entries are tagged with single-letter flags that agents must honor:

- **`[D]` (*Dynamic*):**
  - **Meaning:** Entry generated automatically by a system daemon or routing protocol (e.g. learned BGP/OSPF routes, DHCP client IP, active leases, dynamic PPPoE queues).
  - **Agent Directive:** **Never attempt to edit or delete `[D]` entries directly.** To modify a dynamic attribute, change the parent profile or originating service configuration.
- **`[X]` (*Disabled*):**
  - **Meaning:** Entry administratively disabled (`disabled=true`).
  - **Agent Directive:** The rule does not process traffic. To reactivate, submit a `PATCH` with `{"disabled": false}` via Maker-Checker.
- **`[I]` (*Invalid*):**
  - **Meaning:** Entry referencing a non-existent or misconfigured resource (e.g. firewall rule bound to a deleted interface, or static route with unreachable gateway).
  - **Agent Directive:** Flag as high-priority anomaly in audits and diagnostics reports.
- **`[R]` (*Running*):**
  - **Meaning:** Physical or logical interface with carrier established (*link up*).
  - **Agent Directive:** If an Ethernet or SFP port lacks `[R]`, a Layer 1 issue exists (unplugged cable, dark fiber, missing optical power, or administratively disabled with `[X]`).

---

## 2. RouterOS Internal Identifiers (`.id`)

- RouterOS v7 uses internal hexadecimal identifiers prefixed with an asterisk: `*1`, `*1A`, `*2B`.
- When submitting mutations via `rosgrid_propose_network_change` or targeted REST queries, always use the exact `.id` or unique selector.
- `.id` values are ephemeral across router reboots or item deletions; never assume they remain constant over time.
