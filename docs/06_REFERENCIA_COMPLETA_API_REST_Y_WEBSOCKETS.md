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
| `429 Too Many Requests` | Límite de tasa excedido en KeyDB (ej. más de 30 req/min en el endpoint MCP). |

---

## 2. Catálogo de Endpoints REST (`/api/v1/*`)

### 2.1 Autenticación y Sesiones (`/api/v1/auth`, `/api/v1/sessions`)

#### `GET /api/v1/auth/bootstrap-status`

- **Roles:** Público.
- **Propósito:** Determinar si el sistema requiere inicialización del primer usuario (`COUNT(users) == 0`) y si el auto-registro público está habilitado en KeyDB.
- **Salida (200):**

```json
{
  "is_bootstrapped": true,
  "tenants_count": 1,
  "users_count": 1,
  "registration_enabled": true,
  "message": "Sistema ya inicializado"
}
```

#### `POST /api/v1/auth/bootstrap`

- **Roles:** Público (restringido exclusivamente a cuando `COUNT(users) == 0`; si ya existen usuarios responde `403 Forbidden`).
- **Propósito:** Crear atómicamente la Organización Principal y el usuario `SUPERADMIN_GLOBAL` inicial.
- **Entrada:**

```json
{
  "tenant_name": "Empresa Principal",
  "tenant_slug": "master",
  "admin_username": "superadmin",
  "admin_email": "admin@empresa.com",
  "admin_password": "ClaveSegura123!",
  "admin_full_name": "Super Administrador"
}
```

- **Salida (201 Created):**

```json
{
  "status": "success",
  "tenant_id": "uuid",
  "tenant_slug": "master",
  "admin_id": "uuid",
  "admin_username": "superadmin",
  "totp_secret": "JBSWY3DPEHPK3PXP",
  "totp_provisioning_uri": "otpauth://totp/RoSGrid:admin@empresa.com?secret=...",
  "backup_codes": ["A1B2C3D4", "E5F6G7H8", "..."],
  "message": "Super Administrador y Tenant Principal creados exitosamente."
}
```

#### `POST /api/v1/auth/register`

- **Roles:** Público (sujeto al flag en KeyDB `rg:config:public_registration_enabled`).
- **Propósito:** Solicitar registro como nuevo operador. Crea la cuenta en estado `is_active = false` (`PENDING_APPROVAL`). Cualquier intento de login previo a aprobación responderá `403 Forbidden`.
- **Entrada:**

```json
{
  "tenant_slug": "isp-local",
  "username": "tecnico_redes",
  "email": "tecnico@isp.net",
  "full_name": "Carlos Rodríguez",
  "password": "Password123!"
}
```

- **Salida (201 Created):**

```json
{
  "status": "PENDING_APPROVAL",
  "message": "Tu cuenta fue creada exitosamente y se encuentra pendiente de aprobación por el Administrador.",
  "user_id": "uuid",
  "username": "tecnico_redes",
  "is_active": false
}
```

#### `POST /api/v1/auth/login`

- **Roles:** Público.
- **Entrada:** `{"tenant_slug": "isp-local", "username_or_email": "tecnico_redes", "password": "secure_password"}`
- **Salida (200 con Desafío 2FA):** `{"next_step": "VERIFY_2FA_TOTP", "challenge_id": "uuid", "expires_in_seconds": 180}`.
- **Salida (403 Forbidden para Cuenta Pendiente):** `{"detail": "Tu cuenta está pendiente de aprobación por el Administrador. No puedes ingresar hasta que sea autorizada y se te asigne un rol."}`.

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

### 2.2 Gestión de Usuarios, Roles RBAC y Aprobaciones (`/api/v1/users`)

#### `GET /api/v1/users`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `AUDITOR`.
- **Parámetros Query:** `pending_only` (`true`/`false`), `role`, `search`.
- **Salida (200):** Lista de usuarios del tenant con indicación de `is_active`, `role`, `totp_enabled`, `has_all_routers_access`.

#### `POST /api/v1/users`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Propósito:** Creación directa de operador aprovisionado por el Administrador (con `is_active = true` inmediato).

#### `PUT /api/v1/users/{user_id}/approve`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Propósito:** Aprobar y activar una cuenta de auto-registro en estado PENDIENTE, asignándole su rol operativo y permisos iniciales de router.
- **Entrada:**

```json
{
  "role": "SUPPORT_L2",
  "has_all_routers_access": true,
  "allowed_cidr_list": ["10.250.0.0/16"]
}
```

- **Salida (200):** Objeto de usuario con `is_active: true` y rol asignado.

#### `DELETE /api/v1/users/{user_id}/reject`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Propósito:** Rechazar y eliminar una solicitud pendiente. Compatible con la inmutabilidad de RoSGrid WORM: si el usuario ya registró eventos en `audit_logs`, se revoca y bloquea irreversiblemente en lugar de violar la restricción del disparador WORM.
- **Salida (204 No Content).**

#### `POST /api/v1/users/registration-toggle`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Propósito:** Conmutador global en KeyDB (`rg:config:public_registration_enabled`) para permitir o suspender el auto-registro web.
- **Entrada:** `{"enabled": true}` o `{"enabled": false}`
- **Salida (200):** `{"registration_enabled": bool}`.

#### `PUT /api/v1/users/{user_id}/router-permissions`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Propósito:** Asignar granularmente la matriz de routers autorizados para un técnico (`can_read`, `can_write_layer1`, `can_write_layer2`, `can_reboot`, `bypass_maker_checker`).

#### `POST /api/v1/users/{user_id}/reset-2fa`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN` (con Step-Up Auth TOTP obligatorio del administrador).
- **Propósito:** Reiniciar el segundo factor de un operador que haya extraviado su dispositivo.

---

### 2.3 Gestión de Inventario y Bóveda (`/api/v1/inventory`, `/api/v1/routers`)

#### `POST /api/v1/inventory/routers/{router_id}/discover`

- **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPPORT_L3`.
- **Propósito:** Ejecutar autodescubrimiento y captura criptográfica de huella SSL (TOFU) del router MikroTik. Consumido por el botón TOFU de la UI.
- **Salida (200):** Objeto del router con `model_name`, `ros_version`, `cpu_count`, `total_memory`, `is_reachable: true`.

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

### 2.4 Consola WebFig Capa 1 y Capa 2 (`/api/v1/routers/{id}/...`)

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

### 2.5 Operaciones: Aprobaciones Maker-Checker y Respaldos (`/api/v1/operations/*`)

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
  "side_by_side_hunks": []
}
```

---

### 2.6 Endpoint MCP Protegido para Agentes IA (`POST /api/v1/mcp`)

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
- **Trama `MASS_OUTAGE_DETECTED`:** Alerta prioritaria cuando caen simultáneamente más de `mass_outage_threshold` equipos de última milla.
- **Trama `SESSION_KILLED`:** Fuerza el cierre de sesión del usuario especificado.

---

## 4. Endpoints de Gobernanza Modular, Feature Flags y Operaciones

### 4.1 Feature Flags por Empresa (`/api/v1/tenants/{id}/features`)

Permite la gobernanza modular de capacidades por organización. La consulta se acelera mediante la capa L2 de KeyDB (`rg:{id}:features`) con invalidación en caliente ante mutaciones.

- **`GET /api/v1/tenants/{id}/features`**
  - **Roles:** `SUPERADMIN_GLOBAL` o miembros del propio tenant (`TENANT_ADMIN`, etc.).
  - **Salida (200 OK):**
    ```json
    {
      "isp_module_enabled": true,
      "bgp_looking_glass_enabled": false,
      "sfp_ddm_telemetry_enabled": true,
      "ipfix_analytics_enabled": false,
      "enforce_maker_checker": true,
      "auto_safemode_enforced": true,
      "ai_mcp_integration_enabled": true,
      "nightly_backups_enabled": true,
      "outbound_webhooks_enabled": true,
      "config_drift_monitoring_enabled": false,
      "cis_audit_enabled": true,
      "sdwan_orchestrator_enabled": false,
      "capsman_wifi_enabled": false,
      "sla_tracker_enabled": false,
      "mass_outage_threshold": 10,
      "default_locale": "es"
    }
    ```

- **`PATCH /api/v1/tenants/{id}/features`**
  - **Roles:** Exclusivo `SUPERADMIN_GLOBAL`.
  - **Cabecera Requerida:** `Idempotency-Key: {uuid}`.
  - **Entrada:** Cualquier subconjunto de los 16 atributos del esquema anterior.
  - **Comportamiento:** Persiste en PostgreSQL, invalida la caché KeyDB y genera traza forense inmutable WORM en `audit_logs` con `event_action: "UPDATE_TENANT_FEATURE_FLAGS"`.
  - **Salida (200 OK):** Objeto con el estado consolidado de los Feature Flags del tenant.

---

### 4.2 Dispositivos de Abonados & Perfiles de Calidad de Servicio (QoS Técnico)

> **Gobernanza de Datos (Purga de PII):** RoSGrid no almacena datos personales de clientes (nombres, cédulas, teléfonos o direcciones residenciales). La vinculación técnica se realiza de forma estrictamente seudónima mediante `endpoint_identifier` y el serial técnico del equipo `device_serial`.

#### A. Perfiles de Ancho de Banda (`/api/v1/bandwidth-profiles`)

- **`GET /api/v1/bandwidth-profiles`:** Lista perfiles QoS del tenant con conteo de dispositivos asignados (`subscribers_count`).
- **`POST /api/v1/bandwidth-profiles`:** Crea un nuevo perfil técnico.
  - **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
  - **Cabecera:** `Idempotency-Key: {uuid}`.
  - **Entrada:**
    ```json
    {
      "name": "Plan-Fibra-100M",
      "rate_down_kbps": 102400,
      "rate_up_kbps": 51200,
      "burst_down_kbps": 122880,
      "burst_up_kbps": 61440,
      "burst_threshold_down_kbps": 81920,
      "burst_threshold_up_kbps": 40960,
      "burst_time_seconds": 16,
      "priority": 4,
      "queue_type": "pcq-download-custom"
    }
    ```
- **`GET /api/v1/bandwidth-profiles/{id}`:** Consulta detalle de un perfil.
- **`PATCH /api/v1/bandwidth-profiles/{id}`:** Modifica parámetros de velocidad o ráfagas.
- **`DELETE /api/v1/bandwidth-profiles/{id}`:** Elimina el perfil (rechazado con HTTP 409 si tiene abonados asociados).
- **`GET /api/v1/bandwidth-profiles/{id}/mikrotik-script?target_ip=100.64.0.10`:** Genera scripts CLI RouterOS v7 listos para Simple Queues (`/queue/simple/add`) y Queue Tree (`/queue/tree/add`).

#### B. Dispositivos de Abonados (`/api/v1/subscriber-devices`)

- **`GET /api/v1/subscriber-devices`:** Lista abonados con filtros opcionales (`router_id`, `service_type`, `status`).
- **`POST /api/v1/subscriber-devices`:** Registra un nuevo dispositivo de acceso.
  - **Roles:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPPORT_L2`, `FIELD_TECH`.
  - **Cabecera:** `Idempotency-Key: {uuid}`.
  - **Entrada:**
    ```json
    {
      "router_id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
      "endpoint_identifier": "CLI-CAR-0042",
      "service_type": "PPPOE",
      "auth_backend": "LOCAL_SECRET",
      "bandwidth_profile_id": "b1a2c3d4-0000-1111-2222-333344445555",
      "onu_mode": "ROUTER",
      "onu_mac_address": "AA:BB:CC:DD:EE:FF",
      "device_serial": "ALCLB1234567",
      "pon_port": "pon-1/1/2",
      "optical_box": "NAP-CENTRO-01",
      "latitude": 10.4806,
      "longitude": -66.9036
    }
    ```
- **`GET /api/v1/subscriber-devices/{id}`:** Detalle técnico del abonado.
- **`PATCH /api/v1/subscriber-devices/{id}`:** Actualización técnica de parámetros de red (MAC, serial, caja óptica, estado).
- **`DELETE /api/v1/subscriber-devices/{id}`:** Desincorporación del dispositivo.
- **`GET /api/v1/subscriber-devices/{id}/mikrotik-queue-script`:** Genera dinámicamente el comando de provisión de cola `/queue/simple/add` basado en el perfil asociado.

#### B. API de Aprovisionamiento Técnico Idempotente (`/api/v1/network-services`)

> **Idempotencia Obligatoria:** Todo endpoint mutante requiere la cabecera `Idempotency-Key` con un UUIDv7 válido. Si la operación ya fue procesada, responde con el estado actual sin mutaciones redundantes ni errores (HTTP 200).

- **`POST /api/v1/network-services/{id}/isolate`**
  - **Cabecera:** `Idempotency-Key: {uuid}`.
  - **Mecanismo en MikroTik:** Agrega la IP a la lista de firewall `AISLADOS_TECNICO` o conmuta la velocidad de su cola a `64k/64k` para mantener telemetría sin cortar la sesión física.
  - **Respuesta (200 OK):** `{ "status": "ISOLATED" | "ALREADY_ISOLATED", "service_id": "{id}", "endpoint_identifier": "{ep}", "message": "..." }`.
  - **Evento Emitido:** `DEVICE_ISOLATED`.

- **`POST /api/v1/network-services/{id}/restore`**
  - **Cabecera:** `Idempotency-Key: {uuid}`.
  - **Mecanismo en MikroTik:** Retira la IP de la lista `AISLADOS_TECNICO` y restaura los límites normales de su cola Simple Queue según su `bandwidth_profile_id`.
  - **Respuesta (200 OK):** `{ "status": "RESTORED" | "ALREADY_ACTIVE", "service_id": "{id}", "endpoint_identifier": "{ep}", "message": "..." }`.
  - **Evento Emitido:** `DEVICE_RESTORED`.

- **`POST /api/v1/network-services/{id}/change-rate-limit`**
  - **Cabecera:** `Idempotency-Key: {uuid}`.
  - **Entrada:** `{ "bandwidth_profile_id": "{uuid}" }`.
  - **Mecanismo en MikroTik:** Modifica en caliente los parámetros `max-limit`, `burst-limit`, `burst-threshold` y `burst-time` en `/queue/simple` sin desconectar al abonado.
  - **Respuesta (200 OK):** `{ "status": "RATE_LIMIT_UPDATED", "bandwidth_profile_name": "...", "rate_down_kbps": 100000, "rate_up_kbps": 50000 }`.

- **`GET /api/v1/network-services/{id}`**
  - **Respuesta (200 OK):** Retorna el detalle técnico consolidado del servicio de red, estado de aislamiento, IP asignada y perfil QoS.

### 4.3 Webhooks Salientes Técnicos

RoSGrid despacha peticiones `POST` firmadas criptográficamente con `X-RoSGrid-Signature: sha256={hmac}` y `X-RoSGrid-Signature-256: {hmac}` hacia las URLs registradas ante eventos de red:

- `DEVICE_ACTIVATED_GPS`: Activación de abonado con coordenadas GPS definitivas por el técnico de campo.
- `DEVICE_ISOLATED`: Suspensión o aislamiento preventivo del servicio en MikroTik.
- `DEVICE_RESTORED`: Restablecimiento del servicio y normalización de colas.
- `MASS_OUTAGE_TRIGGERED`: Detección de caída masiva (>= 10 ONUs caídas en el mismo puerto PON o caja óptica).

```json
{
  "event": "DEVICE_ACTIVATED_GPS",
  "timestamp": "2026-10-19T22:40:00Z",
  "payload": {
    "order_id": "c7a8b9c0-1234-4567-89ab-cdef01234567",
    "customer_service_id": "b1a2c3d4-0000-1111-2222-333344445555",
    "device_serial": "ZTEGC1234567",
    "latitude": 10.4806,
    "longitude": -66.9036,
    "activated_at": "2026-10-19T22:40:00Z"
  }
}
```

### 4.4 Diagnóstico 360°, BGP Looking Glass e IPFIX
- `POST /api/v1/diagnostics/endpoint-360`: Ejecuta ping secuencial multi-MTU (64B, 512B, 1472B), parsea causas de desconexión en `/log` de RouterOS (`link down`, `peer is not responding`, `user request`) y realiza muestreo Torch de 2.5s por IP.
- `GET /api/v1/bgp/looking-glass/route?router_id={id}&prefix={cidr}`: Consulta la tabla de rutas BGP v7 mostrando AS-Path, Next-Hop y comunidades.
- `GET /api/v1/bgp/looking-glass/advertised?router_id={id}&peer={name}`: Muestra los prefijos anunciados a un carrier específico.
- `GET /api/v1/traffic-flow/anomalies`: Detecta IPs con altas tasas de PPS o conexiones concurrentes anómalas.
- `POST /api/v1/traffic-flow/mitigate`: Aplica regla FastDrop/Blackhole con Safe Mode y registro WORM.

### 4.5 Suite Corporativa & Enterprise
- `POST /api/v1/compliance/drift-check/{router_id}`: Compara la configuración en ejecución contra la Plantilla Maestra (*Golden Baseline*). Retorna diff semántico en formato Git.
- `POST /api/v1/compliance/drift-revert/{router_id}`: Aplica reversión a la configuración canónica con Safe Mode y Maker-Checker.
- `POST /api/v1/compliance/cis-audit/{router_id}`: Evalúa las 10 directivas críticas CIS y genera Security Score (0 a 100).
- `POST /api/v1/compliance/cis-harden/{router_id}`: Ejecuta auto-endurecimiento cerrando servicios vulnerables.
- `POST /api/v1/sdwan/mesh-provision`: Genera llaves WireGuard, asigna `/30` y despliega adyacencia de enrutamiento dinámico Hub & Spoke.
- `GET /api/v1/switching/rogue-dhcp-alerts`: Lista eventos de DHCP Snooping y puertos con intrusos detectados.
- `GET /api/v1/sla/reports/monthly`: Genera reporte auditable de disponibilidad y latencia P95/P99 para reclamos a carriers.
- `GET/POST /api/v1/wifi/capsman/profiles`: Gestiona perfiles centralizados de SSIDs Corporativo (802.1X), Invitados e IoT.

