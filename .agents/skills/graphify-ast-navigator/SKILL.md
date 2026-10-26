---
name: graphify-ast-navigator
description: >-
  Navigates and queries the RoSGrid AST knowledge graph (Graphify) to inspect symbols, calculate blast radius
  before refactoring, verify layer boundaries, and query the local MCP topology server.
---

# Graphify AST Navigator & Topology Governance Skill

This skill guides AI agents (Google Antigravity, Claude, Hermes Agent) to leverage the **Graphify AST Knowledge Graph** in RoSGrid, achieving up to 80% token savings when navigating complex dependencies.

> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and explain findings in Spanish.

---

## 0. Canonical Architectural Directive: CLI-First vs. MCP Protocol

RoSGrid enforces a clear operational separation depending on the execution capability of the AI agent:

| Agent Profile | Preferred Modality | Rationale & Mechanism |
| :--- | :--- | :--- |
| **Shell-Capable Agents**<br>*(Google Antigravity, local terminal agents)* | **`CLI & Direct Scripts`**<br>*(MANDATORY)* | **Zero background latency, zero RAM consumption, zero port exposure.**<br>Do **NOT** spawn Docker MCP daemons or occupy port 8080. Query AST graphs directly via specialized Python scripts (`inspect_blast_radius.py`, `verify_topological_health.py`), one-line Python queries, or `jq` against `graphify-out/graph.json`. |
| **External IDE / Non-Shell Agents**<br>*(Claude Desktop, remote Hermes Agent)* | **`MCP Streamable HTTP`**<br>*(Optional on-demand)* | Connected over JSON-RPC / SSE via `graphify-mcp` service on `http://localhost:8080/mcp` using descriptors in `.agents/configs/`. |

---

## 1. Quick Blast Radius Inspection (Pre-Refactor — CLI First)

Before modifying any shared function, database model, or Pinia store, determine its exact blast radius:

```bash
# Inspect direct and transitive inbound callers:
python3 .agents/scripts/inspect_blast_radius.py "<symbol_name>"
```

### Risk Classification:
- **`🔴 HIGH / CRITICAL`**: >= 10 direct callers or touches security primitives (`auth`, `vault`, `safemode`, `rls`, `csrf`).
  - *Action:* The implementation plan MUST enumerate all affected callers and assert that their parameter schemas and return types remain 100% backward-compatible.
- **`🟡 MODERATE`**: 3 to 9 callers.
  - *Action:* Audit caller modules and run target unit tests.
- **`🟢 LOW`**: 1 to 2 callers (isolated impact).

---

## 2. Topological Health & Layer Boundaries

Audit architectural separation of concerns and ensure zero forbidden layer coupling:

```bash
# Audit layer boundaries and reverse coupling:
python3 .agents/scripts/verify_topological_health.py
```

### Invariant Rules:
1. `src/mikrotik/`, `src/models/`, `src/core/`, `src/schemas/` must **NEVER** import or call `src/api/` (strict fail-closed).
2. `src/mikrotik/` must **NEVER** depend on `src/workers/`.
3. `src/components/common/` in Vue 3 must **NEVER** depend on `src/views/`.

---

## 3. Ad-hoc Direct AST Queries via CLI (Zero Overhead)

Shell-capable agents should query the raw AST files directly via python or jq without starting any daemon:

```bash
# 1. Search for symbols matching a pattern in Backend graph:
python3 -c "
import json
g = json.load(open('fastapi/graphify-out/graph.json'))
matches = [n['label'] for n in g['nodes'] if 'safemode' in n['label'].lower()]
print('Matches:', matches[:15])
"

# 2. Check cluster / architectural community report:
head -n 45 fastapi/graphify-out/GRAPH_REPORT.md

# 3. Direct jq filtering on nodes or link targets:
jq '.nodes[] | select(.label | test("RouterOS"; "i")) | {id, label, source_file}' fastapi/graphify-out/graph.json | head -n 20
```

---

## 4. Running the Dedicated MCP Topology Server (External Non-Shell Clients ONLY)

> **AGENT DIRECTIVE:** Shell-capable agents (Antigravity) **MUST NOT** use this method. It is reserved exclusively for external clients (Hermes Agent, Claude Desktop) that lack terminal access and connect over Model Context Protocol:

```bash
# Start the MCP server (Streamable HTTP on port 8080):
docker compose -f fastapi/docker-compose.qa.yml --profile graphify up -d graphify

# Endpoint URL:
# http://localhost:8080/mcp

# Stop when finished:
docker compose -f fastapi/docker-compose.qa.yml --profile graphify down -v
```

Pre-configured client descriptors:
- `.agents/configs/claude_desktop_graphify.json`
- `.agents/configs/hermes_agent_graphify.yaml`

---

## 5. Full AST Graph Refresh

Whenever major milestones or structural refactorings are concluded, regenerate the entire AST:

```bash
./scripts/actualizar-grafos-graphify.sh
```
