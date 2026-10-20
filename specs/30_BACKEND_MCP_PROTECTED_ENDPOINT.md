# 30 — ENDPOINT MCP PROTEGIDO (`/api/v1/mcp` JSON-RPC 2.0 STREAMABLE HTTP) PARA AGENTES IA (HERMES AGENT, CLAUDE Y NOC AUTÓNOMO)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la arquitectura, contratos Pydantic v2, blindaje de seguridad y catálogo de herramientas del **Servidor Model Context Protocol (MCP) Integrado** en FastAPI (`POST /api/v1/mcp`). Su objetivo es permitir que agentes IA como **Hermes Agent**, **Claude Desktop / Claude Code** y orquestadores DevSecOps diagnostiquen y operen flotas MikroTik RouterOS v7+ bajo aislamiento Multi-Tenant (`RLS`), control de acceso por router, freno obligatorio **Maker-Checker**, protección **Safe Mode (60s)** y trazabilidad forense **WORM (`audit_logs`)**.

Todo el código generado DEBE mantener complejidad ciclomática **Grado A (`CC <= 5` por función en Radon)**, tipado estricto (`mypy --strict`), `0` alertas en `Bandit` y cobertura unitaria `>= 95%`.

---

## 1. Principios de Seguridad y Gobernanza del Endpoint MCP

1. **Superficie de Ataque Cero por Defecto (`ROSGRID_MCP_ENABLED`):**
   - En `fastapi/src/core/config.py` y `.env.example` se definen dos parámetros:
     * `ROSGRID_MCP_ENABLED: bool = False` (Deshabilitado por defecto).
     * `ROSGRID_MCP_RATE_LIMIT_PER_MIN: int = 30` (Límite de peticiones MCP por minuto por `SERVICE_ACCOUNT` en KeyDB).
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

## 3. Catálogo de las 8 Herramientas Semánticas MCP (`fastapi/src/api/v1/mcp.py`)

Para mantener la complejidad ciclomática **Grado A (`CC <= 5`)**, cada herramienta se implementa en su propia función auxiliar dedicada dentro de `src/api/v1/mcp.py` (o `src/mcp/handlers.py`) y se despacha mediante un diccionario de funciones (`TOOL_HANDLERS_MAP`):

| # | Nombre de la Tool MCP | Nivel de Riesgo | Argumentos (`inputSchema`) | Comportamiento y Respuesta |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `rosgrid_list_inventory` | Solo Lectura | `status_filter` (opcional: `ONLINE`, `OFFLINE`, `DEGRADED_HIGH_LOAD`), `role_filter` (opcional) | Lista los routers MikroTik autorizados para el Tenant/Cuenta con su ID, nombre, identidad RouterOS, modelo, versión v7, estado en KeyDB y estado TOFU SSL. |
| **2** | `rosgrid_get_router_health` | Solo Lectura | `router_id` (UUID requerido) | Consulta el estado efímero en KeyDB y `/rest/system/resource` + `/rest/system/health`, devolviendo CPU%, RAM%, Disco, Uptime, Temperatura (°C) y Voltaje (V). |
| **3** | `rosgrid_check_sfp_optical_ddm` | Solo Lectura | `router_id` (UUID requerido), `interface_name` (opcional, ej. `sfp-sfpplus1`) | Consulta el diagnóstico óptico DDM (`tx-power`, `rx-power` en `dBm`, temperatura láser y clasificación `OPTIMAL`, `WARNING`, `CRITICAL_LOW_LIGHT`). |
| **4** | `rosgrid_inspect_routing_bgp_ospf` | Solo Lectura | `router_id` (UUID requerido), `protocol` (`bgp`, `ospf` o `all`) | Devuelve el resumen de sesiones BGP v7 (estado `established`, prefijos recibidos, uptime) y adyacencias OSPF activas. |
| **5** | `rosgrid_run_live_diagnostic` | Diagnóstico Activo Acotado | `router_id` (UUID requerido), `tool` (`ping` o `traceroute`), `target` (IP/Hostname), `count` (1 a 5, default 4) | Ejecuta `ping` o `traceroute` acotado desde el MikroTik y devuelve latencia `min/avg/max` y porcentaje de pérdida de paquetes. |
| **6** | `rosgrid_compare_config_diff` | Solo Lectura Forense | `router_id` (UUID requerido), `base_backup_id` (UUID requerido), `target_backup_id` (UUID opcional; si se omite compara contra `LIVE`) | Ejecuta el motor **Diff estilo Git (`unified_diff`)** sobre los respaldos `.rsc` para que la IA identifique qué línea exacta cambió antes de un incidente. |
| **7** | `rosgrid_reconnect_pppoe_client` | Operación N1 Directa (Auditada WORM) | `router_id` (UUID requerido), `pppoe_username` (string requerido), `reason` (string requerido) | Busca la sesión activa en `/ppp/active`, solicita su reconexión limpia, registra el evento en `audit_logs` (WORM) y devuelve confirmación. |
| **8** | `rosgrid_propose_network_change` | **Gobernada por Maker-Checker (202)** | `router_id` (UUID requerido), `category` (una de las 7 categorías críticas), `ros_path` (ej. `/ip/firewall/filter`), `http_method` (`POST`, `PATCH`, `DELETE`), `payload` (dict), `justification` (string requerido) | **Jamás aplica el cambio directo en el router.** Crea un registro en `approval_requests` (`status = "AWAITING_APPROVAL"`), dispara alerta a los aprobadores humanos y devuelve el `approval_request_id` para autorización humana con **Safe Mode (60s)**. |

---

## 4. Requisitos de Pruebas Unitarias (`fastapi/tests/test_mcp_endpoint.unit.py`)

Antigravity DEBE crear el archivo `fastapi/tests/test_mcp_endpoint.unit.py` verificando:
1. Que `POST /api/v1/mcp` devuelva `404` cuando `ROSGRID_MCP_ENABLED == False`.
2. Que rechace con `403 Forbidden` a roles que no estén autorizados o IPs fuera del rango CIDR del `SERVICE_ACCOUNT`.
3. Que aplique el límite de tasa en KeyDB (`429 Too Many Requests` al exceder `ROSGRID_MCP_RATE_LIMIT_PER_MIN`).
4. Que `initialize` y `tools/list` devuelvan exactamente las 8 herramientas con esquema JSON-RPC 2.0 válido.
5. Que cada una de las 8 herramientas en `tools/call` funcione correctamente, que `rosgrid_propose_network_change` genere siempre una solicitud `AWAITING_APPROVAL` en **Maker-Checker** sin tocar directamente el MikroTik, y que quede rastro en la bitácora **WORM (`audit_logs`)**.
