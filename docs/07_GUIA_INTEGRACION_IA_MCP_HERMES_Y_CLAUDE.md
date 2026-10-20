# 07 — Guía de Integración IA: Model Context Protocol (MCP) para Hermes Agent y Claude

Este manual técnico detalla la arquitectura, configuración y catálogo del **Servidor Model Context Protocol (MCP) Integrado** de **RoSGrid** (`POST /api/v1/mcp`). Permite que agentes inteligentes como **Hermes Agent** (agente de operaciones autónomas), **Claude Desktop / Claude Code** y orquestadores DevSecOps inspeccionen, diagnostiquen y propongan cambios en flotas MikroTik RouterOS v7+ con seguridad Multi-Tenant, control CIDR, bitácora WORM y freno obligatorio **Maker-Checker con Safe Mode (60s)**.

---

## 1. Arquitectura de Seguridad y Gobernanza MCP

```mermaid
graph TB
    subgraph "Agentes IA Externos"
        Hermes[Hermes Agent / Docker Autónomo]
        Claude[Claude Desktop / Claude Code]
    end

    subgraph "Barrera de Seguridad Perimetral"
        CIDR{Validación de Origen CIDR}
        RoleAuth{Rol SERVICE_ACCOUNT?}
        RateLimit{KeyDB Rate Limit <= 30 req/min}
    end

    Hermes -->|JSON-RPC 2.0 Streamable HTTP| CIDR
    Claude -->|POST /api/v1/mcp| CIDR
    CIDR --> RoleAuth
    RoleAuth --> RateLimit

    subgraph "Servidor MCP RoSGrid (FastAPI)"
        RateLimit --> Dispatcher[Dispatcher JSON-RPC 2.0]
        Dispatcher --> ToolsList["tools/list (16 Tools Semánticas)"]
        Dispatcher --> ToolExec["tools/call (Ejecutor Aislado)"]
        ToolExec --> AuditWORM[(Bitácora WORM: MCP_AI_TOOL_CALL)]
    end

    subgraph "Freno de Seguridad y Enlace a MikroTik"
        ToolExec --> ReadTools[1 a 7 & 9 a 16: Herramientas de Diagnóstico, Consulta y Aislamiento Técnico]
        ToolExec --> MutationTool[8: rosgrid_propose_network_change]
        
        ReadTools -->|Pool TLS Keep-Alive| MikroTik[MikroTik RouterOS v7]
        MutationTool -->|HTTP 202 Accepted| MakerChecker[Bandeja approval_requests: AWAITING_APPROVAL]
        MakerChecker -.->|Supervisión Humana Requerida| Supervisor[Supervisor Humano en WebFig]
        Supervisor -->|Aprobación Explícita| SafeMode[Ejecución con Safe Mode 60s]
        SafeMode --> MikroTik
    end
```

### 1.1 Principios de Seguridad Innegociables
1. **Superficie de Ataque Cero por Defecto:** En `fastapi/src/core/config.py` y `.env`, `ROSGRID_MCP_ENABLED` está en `false`. Si no se activa explícitamente, cualquier petición al endpoint devuelve inmediatamente HTTP `404 Not Found`.
2. **Rol Exclusivo `SERVICE_ACCOUNT` y Lista Blanca CIDR:** Solo tokens Bearer pertenecientes al rol `SERVICE_ACCOUNT` pueden interactuar con el endpoint. Cada cuenta cuenta con un arreglo `allowed_cidr_list` (ej. `["10.0.10.0/24", "192.168.1.50/32"]`). Si la IP del agente IA proviene de otro segmento, la conexión es rechazada con HTTP `403 Forbidden`.
3. **Protección contra Ruido Vecino (*Rate-Limiting* en KeyDB):** Cada petición incrementa un contador atómico con ventana móvil de 60 segundos (`mcp:ratelimit:{tenant_id}:{user_id}`). Si supera `ROSGRID_MCP_RATE_LIMIT_PER_MIN` (30 req/min), responde con HTTP `429 Too Many Requests`.
4. **Aislamiento *Split-Credential* (Cero Acceso a la Bóveda):** Ninguna herramienta MCP permite a la IA leer contraseñas de routers. La IA opera invocando las herramientas mediante el `router_id`; el backend resuelve internamente las credenciales y maneja la sesión HTTPS.
5. **Freno Obligatorio *Maker-Checker* en Mutaciones:** Los agentes IA **jamás pueden modificar directamente** reglas de firewall, sesiones BGP/OSPF ni direccionamiento. La herramienta `rosgrid_propose_network_change` inserta la propuesta forzosamente en `approval_requests` con estado `PENDING` (HTTP `202 Accepted`) para que un humano la apruebe y ejecute con Safe Mode (60s).
6. **Trazabilidad Forense WORM:** Toda invocación a `tools/call` queda sellada criptográficamente en `audit_logs` con `action_category = "MCP_AI_TOOL_CALL"`.

### 1.2 ¿De Dónde Sale el Token Bearer y Cómo se Genera?
Para que un agente de IA pueda interactuar de manera desatendida y continua con `POST /api/v1/mcp` sin requerir interacción con navegador web ni desafíos 2FA manuales, RoSGrid implementa un flujo de emisión de **Tokens de Servicio de Larga Duración**:

1. **Paso 1 — Creación de la Cuenta de Servicio en RoSGrid:**
   - Un usuario con rol `SUPERADMIN_GLOBAL` o `TENANT_ADMIN` crea una cuenta con el rol especial **`SERVICE_ACCOUNT`** desde la interfaz web (*Usuarios y Permisos*) o mediante la API `POST /api/v1/users`.
   - Durante la creación, se define la lista blanca de segmentos de red permitidos (`allowed_cidr_list`, ej. `["192.168.1.50/32"]`). Si la petición proviene de otra IP, la API la rechazará automáticamente.

2. **Paso 2 — Emisión del Token con el Script Oficial `generar_token_mcp.py`:**
   - En el servidor donde corre RoSGrid, ejecuta el script dentro del contenedor de la API:
     ```bash
     docker exec -it rosgrid_api python3 /app/scripts/generar_token_mcp.py --username <NOMBRE_SERVICE_ACCOUNT> --expiry-days 365
     ```
   - **¿Qué hace este script internamente?**
     * Localiza la cuenta de servicio y verifica que posea el rol `SERVICE_ACCOUNT`.
     * Genera un identificador de sesión criptográfico (`session_id` UUIDv4) y registra la sesión activa en KeyDB (`rg:{tenant_id}:sess:{session_id}`) con un tiempo de vida (TTL) equivalente al número de días configurado.
     * Construye y firma criptográficamente un token JWT (`HS256`) utilizando la llave secreta `ROSGRID_JWT_SECRET_KEY`, inyectando los claims `sub` (User ID), `tid` (Tenant ID), `tslug` (Slug del Tenant), `sid` (Session ID) y `rol` (`SERVICE_ACCOUNT`).
     * Entrega en la terminal la cabecera completa lista para copiar y pegar:
       ```http
       Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...
       ```

3. **Paso 3 — Configuración en el Agente IA:**
   - El token generado se inyecta en la variable de entorno o cabecera `AUTHORIZATION` de la configuración del cliente MCP (Hermes Agent, Claude Desktop, etc.).

---

## 2. Protocolo de Transporte: JSON-RPC 2.0 sobre `POST /api/v1/mcp`

El endpoint implementa el estándar **MCP Streamable HTTP** sobre JSON-RPC 2.0.

### 2.1 Método `initialize`
Negociación inicial de versión y capacidades:
```json
// Petición
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}

// Respuesta
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "rosgrid-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

### 2.2 Métodos `ping` y `notifications/initialized`
Verificación de latencia y confirmación de sesión:
```json
// Petición
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "ping"
}

// Respuesta
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {}
}
```

### 2.3 Método `tools/list`
Devuelve el catálogo de las 16 herramientas semánticas con sus esquemas JSON de entrada (`inputSchema`).

---

## 3. Catálogo Detallado de las 16 Herramientas Semánticas MCP

### Herramienta 1: `rosgrid_list_inventory`
- **Nivel de Riesgo:** Solo Lectura.
- **Descripción:** Lista los routers MikroTik autorizados para la cuenta con su ID, nombre, identidad RouterOS, modelo, versión v7, estado de conexión y TOFU SSL.
- **Argumentos:**
  - `status_filter` (opcional): `"ONLINE"`, `"OFFLINE"`, `"DEGRADED_HIGH_LOAD"`.
- **Ejemplo de Invocación:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "rosgrid_list_inventory",
    "arguments": { "status_filter": "ONLINE" }
  }
}
```

---

### Herramienta 2: `rosgrid_get_router_health`
- **Nivel de Riesgo:** Solo Lectura.
- **Descripción:** Consulta el estado físico del equipo (CPU%, RAM libre/total, Uptime, Temperatura en °C y Voltaje en V).
- **Argumentos:**
  - `router_id` (UUID requerido).
- **Respuesta:**
```json
{
  "status": "OK",
  "data": {
    "router_id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
    "cpu_load": 12,
    "free_memory_mb": 850.2,
    "total_memory_mb": 1024.0,
    "uptime": "42d 15h 22m",
    "temperature_c": 39.5,
    "voltage_v": 24.1
  }
}
```

---

### Herramienta 3: `rosgrid_check_sfp_optical_ddm`
- **Nivel de Riesgo:** Solo Lectura.
- **Descripción:** Consulta el diagnóstico óptico DDM de módulos de fibra SFP/SFP+ (`tx-power`, `rx-power` en dBm, temperatura) y clasifica el estado del enlace.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `interface_name` (opcional, ej. `"sfp-sfpplus1"`).
- **Respuesta:**
```json
{
  "status": "OK",
  "data": {
    "router_id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
    "interface": "sfp-sfpplus1",
    "sfp_rx_power_dbm": -22.4,
    "sfp_tx_power_dbm": -3.2,
    "optical_status": "WARNING"
  }
}
```

---

### Herramienta 4: `rosgrid_inspect_routing_bgp_ospf`
- **Nivel de Riesgo:** Solo Lectura.
- **Descripción:** Devuelve el estado de sesiones BGP v7 (estado `established`, prefijos recibidos, uptime) y adyacencias OSPF activas.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `protocol` (opcional: `"bgp"`, `"ospf"`, `"all"`, default `"all"`).

---

### Herramienta 5: `rosgrid_run_live_diagnostic`
- **Nivel de Riesgo:** Diagnóstico Activo Acotado.
- **Descripción:** Ejecuta una prueba de ping o traceroute acotada (máximo 5 paquetes) desde el MikroTik hacia un destino.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `tool` (`"ping"` o `"traceroute"`).
  - `target` (IP o FQDN).
  - `count` (entero de 1 a 5, default 4).

---

### Herramienta 6: `rosgrid_compare_config_diff`
- **Nivel de Riesgo:** Solo Lectura Forense.
- **Descripción:** Ejecuta el comparador Diff estilo Git (`unified_diff`) sobre los respaldos `.rsc` para determinar exactamente qué línea cambió antes de una caída.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `base_backup_id` (UUID requerido).
  - `target_backup_id` (UUID opcional o `"LIVE"`).

---

### Herramienta 7: `rosgrid_reconnect_pppoe_client`
- **Nivel de Riesgo:** Operación N1 Directa (Auditada en WORM).
- **Descripción:** Busca la sesión activa de un abonado PPPoE y solicita su reinicio limpio para resolver problemas de autenticación o bloqueo de sesión.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `pppoe_username` (string requerido).
  - `reason` (string requerido con la justificación del reinicio).

---

### Herramienta 8: `rosgrid_propose_network_change`
- **Nivel de Riesgo:** **Gobernada por Freno Maker-Checker (HTTP 202).**
- **Descripción:** Ningún agente IA aplica cambios directamente en el MikroTik. Esta herramienta inserta la propuesta en la bandeja de aprobación humana `approval_requests`.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `category` (ej. `"FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE"`, `"ROUTING_BGP_OSPF_DEFAULT_CHANGE"`, `"WAN_TRUNK_INTERFACE_OR_IP_CHANGE"`).
  - `ros_path` (ej. `"/ip/firewall/filter"`).
  - `http_method` (`"POST"`, `"PATCH"`, `"DELETE"`, `"PUT"`).
  - `payload` (objeto con la configuración RouterOS v7).
  - `justification` (texto obligatorio explicando el motivo del cambio).
- **Respuesta (202 Accepted):**
```json
{
  "status": "OK",
  "data": {
    "status": "AWAITING_APPROVAL",
    "approval_request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "message": "Propuesta enviada exitosamente a la bandeja de aprobación Maker-Checker (Safe Mode 60s)"
  }
}
```

---

### Herramienta 9: `rosgrid_run_360_diagnostics`
- **Nivel de Riesgo:** Diagnóstico Técnico Avanzado.
- **Descripción:** Ejecuta una batería completa de pruebas: ping multi-MTU (64B, 512B, 1472B), análisis del historial de logs en RouterOS para determinar la causa de desconexión (`link down`, `peer not responding`, `user request`) y muestreo Torch de flujos activos.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `target_ip` (string requerido).
  - `device_serial` (string opcional).

---

### Herramienta 10: `rosgrid_isolate_subscriber`
- **Nivel de Riesgo:** Operación de Aislamiento Técnico (Idempotente).
- **Descripción:** Permite al agente IA aislar un equipo en MikroTik (bloqueo por lista de firewall `AISLADOS_TECNICO` o degradación a 64k) ante detección de bucles de capa 2, ataques DDoS o requerimiento de seguridad.
- **Argumentos:**
  - `subscriber_device_id` (UUID requerido).
  - `reason` (string justificando el aislamiento).
  - `idempotency_key` (UUIDv7 opcional).

---

### Herramienta 11: `rosgrid_restore_subscriber`
- **Nivel de Riesgo:** Operación de Restauración Técnica (Idempotente).
- **Descripción:** Restaura el servicio normal de un equipo previamente aislado, removiendo la regla de bloqueo y restableciendo los límites de cola nominales.
- **Argumentos:**
  - `subscriber_device_id` (UUID requerido).
  - `idempotency_key` (UUIDv7 opcional).

---

### Herramienta 12: `rosgrid_change_rate_limit` (Alias: `rosgrid_change_subscriber_rate_limit`)
- **Nivel de Riesgo:** Modificación Técnica de Ancho de Banda.
- **Descripción:** Aplica un nuevo perfil de velocidad (Queue Simple / PCQ con parámetros de Burst) al equipo sin desconectar la sesión física.
- **Argumentos:**
  - `subscriber_device_id` (UUID requerido).
  - `bandwidth_profile_id` (UUID requerido).
  - `idempotency_key` (UUID opcional).

---

### Herramienta 13: `rosgrid_query_bgp_looking_glass`
- **Nivel de Riesgo:** Solo Lectura de Enrutamiento BGP.
- **Descripción:** Realiza consultas directas a la tabla BGP de RouterOS v7 para verificar el camino óptimo (AS-Path), comunidades y prefijos anunciados o recibidos hacia proveedores de tránsito.
- **Argumentos:**
  - `router_id` (UUID requerido).
  - `query_type` (`"route"` o `"advertised"`).
  - `prefix` (string CIDR, ej. `"1.1.1.0/24"`).
  - `peer_session` (string opcional para consultar un peer específico).

---

### Herramienta 14: `rosgrid_check_config_drift`
- **Nivel de Riesgo:** Auditoría de Cumplimiento Corporativo.
- **Descripción:** Compara la configuración en ejecución del router contra la Plantilla Maestra (*Golden Baseline Template*) de la empresa y devuelve el diff semántico de líneas no autorizadas.
- **Argumentos:**
  - `router_id` (UUID requerido).

---

### Herramienta 15: `rosgrid_run_cis_audit`
- **Nivel de Riesgo:** Auditoría de Ciberseguridad.
- **Descripción:** Evalúa las 10 directivas críticas de endurecimiento CIS Benchmark en RouterOS y retorna el Security Score (0 a 100) junto con la lista detallada de vulnerabilidades detectadas.
- **Argumentos:**
  - `router_id` (UUID requerido).

---

### Herramienta 16: `rosgrid_detect_mass_outage`
- **Nivel de Riesgo:** Monitoreo y Respuesta a Incidentes.
- **Descripción:** Analiza en memoria efímera el estado de los equipos de última milla y determina si hay una caída masiva activa en un sector, rama PON o switch, evaluando si supera el umbral configurado (`mass_outage_threshold`).
- **Argumentos:**
  - `tenant_id` (UUID opcional).

---

## 4. Configuración en Clientes IA

### 4.1 Configuración para Hermes Agent
En el archivo de manifiesto del agente Hermes (`hermes_agent_config.yaml`):

```yaml
mcp_servers:
  rosgrid:
    url: "https://rosgrid.mi-empresa.com/api/v1/mcp"
    transport: "http"
    headers:
      Authorization: "Bearer eyJhbGciOiJIUzI1NiIsIn..."
      Content-Type: "application/json"
    timeout_seconds: 15
    rate_limit_per_minute: 30
```

### 4.2 Configuración para Claude Desktop / Claude Code (`claude_desktop_config.json`)
Agrega el servidor en el bloque de MCP de Claude:

```json
{
  "mcpServers": {
    "rosgrid-network": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://rosgrid.mi-empresa.com/api/v1/mcp",
        "--header",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn..."
      ]
    }
  }
}
```

---

## 5. Flujo Operativo: NOC Autónomo 24/7 con Webhooks + Maker-Checker

```mermaid
sequenceDiagram
    autonumber
    participant MT as MikroTik Edge
    participant RoSGrid as RoSGrid Backend & Webhook Dispatcher
    participant Hermes as Hermes Agent (IA Autónomo)
    participant Supervisor as Ingeniero de Guardia (Humano)

    MT-->>RoSGrid: Pérdida de paquetes / Caída BGP detectada
    RoSGrid->>Hermes: Envía Webhook HMAC-SHA256 (Alerta: BGP_PEER_DOWN)
    Note over Hermes: Hermes despierta y analiza el evento
    Hermes->>RoSGrid: POST /api/v1/mcp (rosgrid_check_sfp_optical_ddm)
    RoSGrid-->>Hermes: Óptica en estado OPTIMAL (-14 dBm)
    Hermes->>RoSGrid: POST /api/v1/mcp (rosgrid_compare_config_diff vs LIVE)
    RoSGrid-->>Hermes: Diff revela cambio no autorizado en prefijos BGP
    Hermes->>RoSGrid: POST /api/v1/mcp (rosgrid_propose_network_change)
    Note over RoSGrid: Freno Maker-Checker intercepta cambio
    RoSGrid-->>Hermes: 202 Accepted (approval_request_id: 9b1deb4d)
    RoSGrid->>Supervisor: Notificación Telegram / Email (Propuesta IA Pendiente)
    Supervisor->>RoSGrid: Revisa Diff en ApprovalsInboxView.vue y aprueba
    RoSGrid->>MT: Aplica corrección BGP con Safe Mode (60s)
    RoSGrid-->>Supervisor: Sesión BGP reestablecida con éxito
    Note over RoSGrid: Evento firmado en WORM (MCP_AI_TOOL_CALL)
```
