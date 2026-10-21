# 30 — ENDPOINT MCP PROTEGIDO (`/api/v1/mcp` JSON-RPC 2.0 STREAMABLE HTTP) PARA AGENTES IA (HERMES AGENT, CLAUDE Y NOC AUTÓNOMO)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la arquitectura, contratos Pydantic v2, blindaje de seguridad y catálogo de herramientas del **Servidor Model Context Protocol (MCP) Integrado** en FastAPI (`POST /api/v1/mcp`). Su objetivo es permitir que agentes IA como **Hermes Agent**, **Claude Desktop / Claude Code** y orquestadores DevSecOps diagnostiquen y operen flotas MikroTik RouterOS v7+ bajo aislamiento Multi-Tenant (`RLS`), control de acceso por router, freno obligatorio **Maker-Checker**, protección **Safe Mode (60s)** y trazabilidad forense **WORM (`audit_logs`)**.

Todo el código generado DEBE mantener complejidad ciclomática **Grado A (`CC <= 5` por función en Radon)**, tipado estricto (`mypy --strict`), `0` alertas en `Bandit` y cobertura unitaria `>= 95%`.

---

## 1. Principios de Seguridad y Gobernanza del Endpoint MCP

1. **Superficie de Ataque Cero por Defecto (`ROSGRID_MCP_ENABLED`):**
   - En `fastapi/src/core/config.py` y `.env.example` se definen dos parámetros:
     - `ROSGRID_MCP_ENABLED: bool = False` (Deshabilitado por defecto).
     - `ROSGRID_MCP_RATE_LIMIT_PER_MIN: int = 30` (Límite de peticiones MCP por minuto por `SERVICE_ACCOUNT` en KeyDB).
   - Si `settings.ROSGRID_MCP_ENABLED` es `False`, el endpoint `POST /api/v1/mcp` devuelve inmediatamente HTTP `404 Not Found` (`{"detail": "MCP endpoint is disabled"}`) sin procesar el payload.
2. **Autenticación Exclusiva vía `SERVICE_ACCOUNT` + Validación CIDR:**
   - El endpoint `/api/v1/mcp` exige un token Bearer válido perteneciente **exclusivamente** al rol #11 **`SERVICE_ACCOUNT`** (o `TENANT_ADMIN` / `SUPERADMIN_GLOBAL` en modo auditoría explícita).
   - Valida que la IP de origen del cliente MCP esté autorizada en la lista blanca CIDR asociada a la cuenta de servicio y aplica el filtro de routers asignados (`user_router_permissions`) más la inyección de `SET LOCAL app.current_tenant_id` en PostgreSQL 17.
3. **Protección contra Ruido Vecino (*Rate-Limiting* en KeyDB Multi-Hilo):**
   - Cada llamada a `/api/v1/mcp` incrementa un contador atómico con `TTL` de 60 segundos en KeyDB (`mcp:ratelimit:{tenant_id}:{user_id}`). Si supera `ROSGRID_MCP_RATE_LIMIT_PER_MIN`, responde con HTTP `429 Too Many Requests`.
4. **Cero Acceso a la Bóveda de Secretos (`AES-256-GCM`):**
   - El servidor MCP **jamás** expone herramientas para revelar contraseñas de `router_credentials_vault` (`Split-Credential`). El agente IA invoca las herramientas por `router_id` y FastAPI utiliza internamente el pool TLS `Keep-Alive` autenticado.
5. **Freno Obligatorio *Maker-Checker* en Mutaciones de Red:**
   - Ningún agente IA puede modificar directamente reglas de Firewall, sesiones BGP/OSPF, rutas o direccionamiento IP en vivo.
   - La herramienta `rosgrid_propose_network_change` inserta la propuesta **forzosamente en la bandeja `approval_requests` (`status = "AWAITING_APPROVAL"`, HTTP `202 Accepted`)** y notifica a los supervisores humanos para que un `SUPERVISOR`, `SUPPORT_L3` o `TENANT_ADMIN` revise el Diff y lo apruebe ejecutándolo con **Safe Mode (60s)**.
6. **Auditoría Forense Inmutable WORM (`audit_logs`):**
   - Toda invocación a `tools/call` en `/api/v1/mcp` genera un registro firmado con `SHA-256` en `audit_logs` con `action_category = "MCP_AI_TOOL_CALL"`, indicando el nombre de la herramienta, el `router_id` y los argumentos sanitizados.
7. **Aislamiento de Tenant con Sentencias SQL Parametrizadas Seguras:**
   - La inyección de `SET LOCAL app.current_tenant_id` en las sesiones de base de datos se realiza a través de la función segura `set_tenant_context(session, tenant_id)`, garantizando que el `tenant_id` se enlace mediante `bindparam` y previniendo cualquier riesgo de inyección SQL.
8. **Emisión de Tokens y Supervisión de Sesiones (Frontend y Terminal):**
   - Emisión criptográfica de tokens Bearer JWT de larga duración mediante el endpoint `POST /api/v1/users/{user_id}/mcp-token` o la interfaz web `RgMcpTokenModal.vue` en `UsersAndPermissionsView.vue`.
   - Supervisión y Kill-Switch en vivo en `ActiveSessionsKillSwitchView.vue`, con trazabilidad de autoría (`issued_by_username`), filtro por agente y revocación en caliente en KeyDB.

---

## 2. Contrato de Transporte MCP: JSON-RPC 2.0 sobre `POST /api/v1/mcp`

Para evitar dependencias externas pesadas y aprovechar la velocidad de **`ORJSONResponse`**, RoSGrid implementa el estándar **MCP *Streamable HTTP* (JSON-RPC 2.0)** directamente con esquemas Pydantic v2 estrictos en `fastapi/src/schemas/mcp.py`:

### 2.1 Esquemas Pydantic v2 (`fastapi/src/schemas/mcp.py`)

~~~python
# SPDX-License-Identifier: GPL-3.0-only
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class McpJsonRpcRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int | None = None
    method: Literal[
        "initialize",
        "notifications/initialized",
        "ping",
        "tools/list",
        "tools/call",
    ]
    params: dict[str, Any] = Field(default_factory=dict)


class McpToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    inputSchema: dict[str, Any]


class McpJsonRpcError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: int
    message: str
    data: dict[str, Any] | None = None


class McpJsonRpcResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int | None = None
    result: dict[str, Any] | None = None
    error: McpJsonRpcError | None = None
~~~

### 2.2 Métodos JSON-RPC 2.0 Soportados

1. **`initialize`:** Devuelve `protocolVersion: "2025-03-26"`, `capabilities: {"tools": {"listChanged": False}}` y `serverInfo: {"name": "rosgrid-mcp-server", "version": "1.0.0"}`.
2. **`ping` / `notifications/initialized`:** Devuelve `{}` confirmando estado activo de la sesión MCP.
3. **`tools/list`:** Devuelve el arreglo de las **8 Tools semánticas de RoSGrid** con sus respectivos JSON Schemas de entrada (`inputSchema`).
4. **`tools/call`:** Recibe `params: {"name": "<tool_name>", "arguments": {...}}`, valida permisos sobre el `router_id`, registra la acción en la bitácora WORM, ejecuta el servicio interno y devuelve:

   ~~~json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "content": [
         {
           "type": "text",
           "text": "{\"status\":\"OK\",\"data\":{...}}"
         }
       ],
       "isError": false
     }
   }
   ~~~

---

## 3. Catálogo de las 14 Herramientas Semánticas MCP (`fastapi/src/api/v1/mcp.py`)

Para mantener la complejidad ciclomática **Grado A (`CC <= 5`)**, cada herramienta se implementa en su propia función auxiliar dedicada dentro de `src/api/v1/mcp.py` y se despacha mediante un diccionario de funciones (`TOOL_HANDLERS_MAP`):

| # | Nombre de la Tool MCP | Nivel de Riesgo | Argumentos (`inputSchema`) | Comportamiento y Respuesta |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `rosgrid_list_inventory` | Solo Lectura | `status_filter` (opcional), `role_filter` (opcional) | Lista routers MikroTik con estado en KeyDB y TOFU SSL. |
| **2** | `rosgrid_get_router_health` | Solo Lectura | `router_id` (UUID requerido) | Telemetría de CPU%, RAM%, Uptime, Temp (°C) y Voltaje (V). |
| **3** | `rosgrid_check_sfp_optical_ddm` | Solo Lectura | `router_id` (UUID requerido), `interface_name` (requerido) | Diagnóstico óptico DDM (`tx/rx-power`, Temp y clasificación). |
| **4** | `rosgrid_inspect_routing_bgp_ospf` | Solo Lectura | `router_id` (UUID requerido), `protocol` (`bgp`/`ospf`/`all`) | Resumen de sesiones BGP v7 y adyacencias OSPF. |
| **5** | `rosgrid_run_live_diagnostic` | Solo Lectura | `router_id`, `tool` (`ping`/`traceroute`), `target`, `count` | Ping/Traceroute acotado con latencia min/avg/max y pérdida. |
| **6** | `rosgrid_compare_config_diff` | Solo Lectura | `router_id`, `base_backup_id`, `target_backup_id` (o `LIVE`) | Motor Diff Git (`unified_diff`) sobre respaldos `.rsc`. |
| **7** | `rosgrid_reconnect_pppoe_client` | Operacional Directa | `router_id`, `pppoe_username`, `reason` | Reinicio limpio de sesión en `/ppp/active` auditado en WORM. |
| **8** | `rosgrid_propose_network_change` | **Maker-Checker (202)** | `router_id`, `category`, `ros_path`, `http_method`, `payload`, `justification` | Freno obligatorio; genera solicitud `PENDING` para aprobación humana con Safe Mode (60s). |
| **9** | `rosgrid_run_360_diagnostics` | Solo Lectura | `router_id`, `target_ip`, `device_serial` (opc), `interface` (opc) | Ping multi-MTU (64B, 512B, 1472B DF-bit), logs y Torch. |
| **10** | `rosgrid_isolate_subscriber` | Mitigación | `subscriber_device_id`, `reason`, `idempotency_key` (opc) | Aislamiento a lista `AISLADOS_TECNICO` y cola 64k/64k. |
| **11** | `rosgrid_restore_subscriber` | Mitigación | `subscriber_device_id`, `idempotency_key` (opc) | Restitución del servicio y retorno a colas nominales. |
| **12** | `rosgrid_change_rate_limit` | Operacional Directa | `subscriber_device_id`, `bandwidth_profile_id`, `idempotency_key` (opc) | Conmutación de ancho de banda y QoS sin corte físico. |
| **13** | `rosgrid_query_bgp_looking_glass` | Solo Lectura | `router_id`, `query_type` (`route`/`advertised`), `prefix`, `peer_session`, `refresh` | Consulta FIB de rutas o prefijos exportados a un peer. |
| **14** | `rosgrid_check_config_drift` | Auditoría | `router_id` (UUID requerido) | Auditoría de desviación contra Golden Baseline homologada. |
| **15** | `rosgrid_run_cis_audit` | Auditoría | `router_id` (UUID requerido) | Auditoría CIS Benchmark (10 directivas, Score 0-100). |
| **16** | `rosgrid_detect_mass_outage` | Correlación | `threshold_onus` (default 3), `tenant_id` (opcional) | Correlación espacial de caídas por puerto PON o caja NAP. |

---

## 4. Requisitos de Pruebas Unitarias (`fastapi/tests/test_mcp_endpoint.unit.py`)

Antigravity DEBE verificar:

1. Que `POST /api/v1/mcp` devuelva `404` cuando `ROSGRID_MCP_ENABLED == False`.
2. Que rechace con `403 Forbidden` a roles que no estén autorizados o IPs fuera del rango CIDR del `SERVICE_ACCOUNT`.
3. Que aplique el límite de tasa en KeyDB (`429 Too Many Requests` al exceder `ROSGRID_MCP_RATE_LIMIT_PER_MIN`).
4. Que `initialize` y `tools/list` devuelvan el catálogo completo con esquema JSON-RPC 2.0 válido.
5. Que cada una de las herramientas en `tools/call` funcione correctamente, que `rosgrid_propose_network_change` genere siempre una solicitud `AWAITING_APPROVAL` en **Maker-Checker** sin tocar directamente el MikroTik, y que quede rastro en la bitácora **WORM (`audit_logs`)**.

---

## 5. Skill Oficial de Operaciones para Agentes IA (`rosgrid-noc-operator`)

Para garantizar que los agentes operen bajo procedimientos estándar (SOP) sin riesgos de colisión, saturación de rate limits o mutaciones no autorizadas, RoSGrid provee la skill oficial:

- **Ruta en Workspace:** `.agents/skills/rosgrid-noc-operator/SKILL.md`
- **Ruta Global Antigravity:** `~/.gemini/config/skills/rosgrid-noc-operator/SKILL.md`
- **Referencias y Esquemas:** `.agents/skills/rosgrid-noc-operator/references/mcp_tools.md` y `routeros_flags.md`
- **Configuraciones de Clientes:** Snippets listos para Claude Desktop (`claude_desktop.json`) y Hermes Agent (`hermes_agent.yaml`).
