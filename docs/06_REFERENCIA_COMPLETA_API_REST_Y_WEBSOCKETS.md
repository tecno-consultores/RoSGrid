# 06 — Referencia Completa de la API REST y WebSockets

> **Nota de Seguridad de Producción:**  
> En cumplimiento del estándar de endurecimiento de RoSGrid, la documentación interactiva Swagger UI (`/docs`), ReDoc (`/redoc`) y la especificación abierta OpenAPI (`/openapi.json`) están **deshabilitadas de forma estricta e inmutable en entornos productivos** (`ROSGRID_ENV=production`). Este documento constituye la especificación formal y exhaustiva de todas las interfaces REST y WebSockets del sistema.

---

## 1. Convenciones de Comunicación, Seguridad y Cabeceras

### 1.1 Esquemas de Autenticación
1. **Acceso de Usuarios y Operadores Web (Navegador):**
   - **Cookie Segura:** `__Host-rg_at` (o `rg_at` en testing): `HttpOnly; Secure; SameSite=Strict; Path=/`.
   - **Cabecera Anti-CSRF:** En peticiones mutantes (`POST`, `PUT`, `PATCH`, `DELETE`) es obligatoria la cabecera `X-CSRF-Token`.
2. **Acceso Máquina a Máquina (M2M) y Agentes IA (`SERVICE_ACCOUNT`):**
   - **Cabecera Authorization:** `Authorization: Bearer <TOKEN_JWT_VALIDO>`
   - **Validación de IP de Origen:** La dirección IP del cliente se verifica forzosamente contra la lista blanca CIDR asociada a la cuenta de servicio (`allowed_cidr_list`).

### 1.2 Idempotencia en Mutaciones Sensibles
Para prevenir la duplicación accidental de reglas o peticiones por cortes transitorios de red, los endpoints de mutación aceptan la cabecera opcional:
```http
Idempotency-Key: 018f23a4-8b1c-7e3f-912a-456789abcdef (UUIDv7)
```
RoSGrid almacena la respuesta en KeyDB durante 120 segundos. Las peticiones idénticas subsiguientes devuelven inmediatamente la respuesta cacheada sin re-ejecutar el comando en el MikroTik.

### 1.3 Códigos de Estado HTTP Estándar

| Código HTTP | Significado en RoSGrid |
| :--- | :--- |
| `200 OK` | Operación de lectura o mutación directa completada exitosamente. |
| `201 Created` | Recurso creado exitosamente (ej. nuevo usuario, router o respaldo generado). |
| `202 Accepted` | **Freno Maker-Checker Activo:** La mutación crítica ha sido interceptada y encolada en `approval_requests` (`status: PENDING`) en espera de autorización humana. |
| `401 Unauthorized` | Sesión no provista, token expirado, cookie inválida o sesión revocada por Kill-Switch. |
| `403 Forbidden` | Rol RBAC insuficiente, router no autorizado en la matriz de permisos o IP no autorizada en CIDR whitelist. |
| `404 Not Found` | Router, usuario, respaldo o recurso REST no encontrado en el Tenant actual. |
| `409 Conflict` | Conflicto de unicidad (ej. nombre de usuario, IP de router o nombre de regla duplicado). |
| `422 Unprocessable` | Validación fallida de esquema Pydantic v2 (parámetros requeridos faltantes o tipos erróneos). |
| `429 Too Many Requests`| Límite de tasa excedido en KeyDB (ej. más de 30 req/min en el endpoint MCP). |

---

## 2. Catálogo de Endpoints REST (`/api/v1/*`)

### 2.1 Autenticación y Sesiones (`/api/v1/auth`, `/api/v1/sessions`)

#### `POST /api/v1/auth/login`
- **Roles:** Público.
- **Entrada:** `{"username": "admin", "password": "secure_password"}`
- **Salida (200):** Si 2FA está deshabilitado, establece cookie `__Host-rg_at` y devuelve `{"status": "AUTHENTICATED", "user": {...}}`.
- **Salida (200 con Desafío 2FA):** `{"status": "CHALLENGE_2FA_REQUIRED", "challenge_id": "uuid", "expires_in_seconds": 300}`.

#### `POST /api/v1/auth/verify-2fa`
- **Roles:** Público (con `challenge_id` válido).
- **Entrada:** `{"challenge_id": "uuid", "totp_code": "123456"}`
- **Salida (200):** Establece cookie `__Host-rg_at` y devuelve `{"status": "AUTHENTICATED", "user": {...}}`.

#### `POST /api/v1/auth/logout`
- **Roles:** Todos los usuarios autenticados.
- **Salida (200):** Invalida la sesión en KeyDB y elimina la cookie.

#### `GET /api/v1/sessions`
- **Roles:** `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`.
- **Salida (200):** Lista de sesiones activas en KeyDB con IP, navegador, último acceso y `session_id`.

#### `DELETE /api/v1/sessions/{session_id}` *(Kill-Switch)*
- **Roles:** `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`.
- **Salida (200):** Revoca inmediatamente la sesión en KeyDB y emite señal WebSocket para expulsar al navegador cliente.

---

### 2.2 Gestión de Inventario y Bóveda (`/api/v1/routers`)

#### `GET /api/v1/routers`
- **Roles:** Todos los roles (filtrado automáticamente por RLS y matriz de permisos por router).
- **Parámetros Query:** `status_filter` (`ONLINE`, `OFFLINE`), `role_filter`.
- **Salida (200):**
```json
{
  "total": 1,
  "items": [
    {
      "id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
      "display_name": "Edge-Core-01",
      "api_base_url": "https://10.0.0.1:443",
      "model_name": "CCR2004-16G-2S+",
      "ros_version": "7.16",
      "is_reachable": true,
      "ssl_trust_status": "TRUSTED_PINNED",
      "network_role": "CORE"
    }
  ]
}
```

#### `POST /api/v1/routers`
- **Roles:** `TENANT_ADMIN`, `INVENTORY_MANAGER`.
- **Entrada:**
```json
{
  "display_name": "Edge-Core-01",
  "api_base_url": "https://10.0.0.1:443",
  "api_port": 443,
  "network_role": "CORE",
  "physical_location": "Datacenter Principal Rack 2",
  "initial_api_username": "rosgrid_agent",
  "initial_api_password": "super_secret_password"
}
```
- **Salida (201):** Crea el router y almacena la contraseña cifrada con `AES-256-GCM` en la Bóveda.

#### `POST /api/v1/routers/{id}/vault/reveal` *(Step-Up Auth 2FA)*
- **Roles:** `TENANT_ADMIN`, `SUPERVISOR`.
- **Entrada:** `{"totp_code": "654321"}`
- **Salida (200):**
```json
{
  "username": "rosgrid_agent",
  "password": "unencrypted_password_for_onsite_work",
  "expires_in_seconds": 30
}
```

---

### 2.3 Consola WebFig Capa 1 y Capa 2 (`/api/v1/routers/{id}/...`)

#### `GET /api/v1/routers/{id}/interfaces`
- **Roles:** Lectura concedida en matriz de permisos.
- **Salida (200):** Lista de interfaces físicas con estadísticas en vivo de bytes, paquetes y estado SFP DDM (`tx-power`, `rx-power`, temperatura láser).

#### `POST /api/v1/routers/{id}/firewall/filter`
- **Roles:** `SUPPORT_L3`, `SUPPORT_L2`, `TENANT_ADMIN`.
- **Entrada:**
```json
{
  "chain": "input",
  "action": "drop",
  "src_address": "198.51.100.0/24",
  "comment": "Bloqueo por tráfico anómalo detectado"
}
```
- **Comportamiento:**
  - Si la regla afecta la cadena `input` crítica: **HTTP 202 Accepted** (Derivada a Maker-Checker).
  - Si el usuario cuenta con `bypass_maker_checker`: **HTTP 200 OK** (Ejecutada con Safe Mode de 60s).

#### `GET/POST/PATCH/DELETE /api/v1/routers/{id}/layer2/{resource_path}`
- **Roles:** `can_write_layer2` en matriz de permisos.
- **Descripción:** Acceso transparente a recursos de Capa 2 (Bridges, VLANs, Switch, WireGuard, Capsman, IoT).

---

### 2.4 Operaciones: Aprobaciones Maker-Checker y Respaldos (`/api/v1/operations/*`)

#### `GET /api/v1/operations/approvals`
- **Roles:** `TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3`, `AUDITOR`.
- **Salida (200):** Lista de solicitudes pendientes (`status: PENDING`), expiradas o aprobadas con diff del cambio y justificación técnica.

#### `POST /api/v1/operations/approvals/{id}/approve`
- **Roles:** `TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3` (Segregación: el aprobador debe ser un usuario distinto al solicitante).
- **Salida (200):** Ejecuta la mutación almacenada utilizando Safe Mode (60s) y actualiza el estado a `APPROVED_AND_EXECUTED`.

#### `GET /api/v1/routers/{id}/backups/diff`
- **Roles:** `SUPPORT_L3`, `SUPPORT_L2`, `AUDITOR`.
- **Parámetros Query:** `base_backup_id` (UUID), `target_backup_id` (UUID o `"LIVE"`).
- **Salida (200):**
```json
{
  "router_id": "uuid",
  "lines_added": 4,
  "lines_removed": 1,
  "unified_diff_text": "--- base.rsc\n+++ target.rsc\n@@ -10,3 +10,6 @@\n-/ip firewall filter add chain=input action=accept\n+/ip firewall filter add chain=input action=drop",
  "side_by_side_hunks": [...]
}
```

---

### 2.5 Endpoint MCP Protegido para Agentes IA (`POST /api/v1/mcp`)

- **Protocolo:** JSON-RPC 2.0 *Streamable HTTP*.
- **Roles Exclusivos:** `SERVICE_ACCOUNT` (o `TENANT_ADMIN` / `SUPERADMIN_GLOBAL` en auditoría).
- **Seguridad:** Requiere `ROSGRID_MCP_ENABLED=true` y verificación de origen contra la lista blanca CIDR.
- **Rate-Limiting:** Máximo 30 peticiones por minuto por cuenta.
- **Métodos Soportados:** `initialize`, `ping`, `notifications/initialized`, `tools/list`, `tools/call`.

*(La especificación técnica completa y ejemplos de las 8 Tools MCP se detallan en el manual `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`).*

---

## 3. Especificación de Canales WebSocket (`/ws/v1/*`)

Los canales WebSocket de RoSGrid requieren pasar la cookie `__Host-rg_at` durante el apretón de manos inicial (`Upgrade: websocket`) y operan frames codificados en JSON ultrarrápido con **`orjson`**.

### 3.1 Canal de Telemetría en Vivo de Router
```http
GET /ws/v1/routers/{router_id}/live-telemetry HTTP/1.1
Upgrade: websocket
Connection: Upgrade
```
- **Frecuencia de Emisión:** 1 tick cada 2 segundos.
- **Estructura de la Trama (`TELEMETRY_TICK`):**
```json
{
  "event": "TELEMETRY_TICK",
  "router_id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
  "timestamp": "2026-10-16T00:30:00Z",
  "metrics": {
    "cpu_load_percent": 14,
    "free_memory_mb": 842.5,
    "total_memory_mb": 1024.0,
    "voltage_v": 24.2,
    "temperature_c": 38.5,
    "traffic_bps": {
      "ether1_rx": 45210800,
      "ether1_tx": 12890500,
      "sfp-sfpplus1_rx": 985400120,
      "sfp-sfpplus1_tx": 450120800
    }
  }
}
```

### 3.2 Canal Global de Eventos del Tenant
```http
GET /ws/v1/tenant/events HTTP/1.1
Upgrade: websocket
Connection: Upgrade
```
- **Trama `MAKER_CHECKER_REQUEST_CREATED`:** Notifica a los supervisores cuando un cambio ha quedado encolado para su revisión.
- **Trama `NOC_ROUTER_STATE_CHANGED`:** Alerta instantánea cuando un equipo pasa a estado `OFFLINE` o `DEGRADED`.
- **Trama `SESSION_KILLED`:** Fuerza el cierre de sesión del usuario especificado.
