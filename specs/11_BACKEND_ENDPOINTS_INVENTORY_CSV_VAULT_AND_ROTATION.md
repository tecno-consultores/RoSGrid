# 11 — ENDPOINTS BACKEND: INVENTARIO MIKROTIK, IMPORTACIÓN MASIVA CSV, BÓVEDA STEP-UP, ROTACIÓN DE CLAVES Y MANTENIMIENTO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los endpoints de `fastapi/src/api/v1/inventory.py`, `fastapi/src/api/v1/vault.py` y `fastapi/src/api/v1/maintenance.py`. Incluye el flujo de alta con autodescubrimiento vía REST API de RouterOS v7, el importador masivo CSV en 2 pasos (*Dry-Run* + ejecución), la consulta de claves protegida con *Step-Up Auth* (exclusiva para los 2 roles superiores), la rotación automática de contraseñas API y las ventanas de mantenimiento.

## **1. Endpoints de Inventario de Equipos MikroTik (/api/v1/inventory/routers)**

### **1.1 GET /api/v1/inventory/routers — Listar Equipos MikroTik (Tabla y Mapa OpenStreetMap)**

- **Roles Permitidos:** Todos los roles autenticados (filtrado automáticamente según `user_router_permissions` si el rol no tiene acceso global al Tenant).
- **Filtros Query String:**
  - `network_role` (CORE, EDGE_BGP, WAN_BALANCER, BRAS_PPPOE, DISTRIBUTION_SWITCH, TOWER_AP, CORPORATE_CPE)
  - `admin_state` (PRODUCTION, MAINTENANCE, STAGING_LAB, RETIRED)
  - `tag` (ej. zona-norte)
  - `search` (busca por display_name, serial_number, ros_identity, physical_location o api_base_url)
- **Enriquecimiento con Estado Efímero de Redis:**
  - El endpoint combina los metadatos de PostgreSQL con una lectura en pipeline (MGET / HGETALL) de `rg:{tenant_id}:mon_state:{router_id}` en Redis para devolver el estado operativo en vivo (ONLINE, DEGRADED_HIGH_LOAD, OFFLINE, SSL_MISMATCH) y el último porcentaje instantáneo de CPU/RAM para colorear los pines en el mapa **OpenStreetMap**.

### **1.2 POST /api/v1/inventory/routers — Registrar un Nuevo MikroTik + Pinning TOFU Inicial**

- **Roles Permitidos:** SUPERADMIN_GLOBAL, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3, INVENTORY_MANAGER.
- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.
- **Request Body (CreateRouterRequest):**

```json
{
  "display_name": "RB4011-Balanceador-Principal",
  "api_base_url": "<api_base_url_https>",
  "api_port": 443,
  "api_username": "rosgrid_api_admin",
  "api_password": "ClaveInicialMikrotik#2026",
  "network_role": "WAN_BALANCER",
  "admin_state": "PRODUCTION",
  "physical_location": "Centro de Datos Naguanagua, Rack 2, U14",
  "latitude": 10.264500,
  "longitude": -68.010200,
  "online_since_date": "2025-06-15",
  "serial_number": "D4460B123456",
  "tags": ["balanceador", "naguanagua", "doble-wan"],
  "operational_notes": "Balanceo ECMP L4 con 2 enlaces de 600 Mbps",
  "site_contact_info": "NOC Local Ext 104",
  "auto_rotate_credentials": true,
  "rotation_interval_days": 30,
  "connect_and_discover_now": true
}
```

- **Proceso:**
  1. Verifica cuota disponible en `tenants.max_routers_quota`.
  2. Inserta el router en `routers` y sus etiquetas en `router_tags`.
  3. Cifra `api_password` con AES-256-GCM (AAD = `f"{tenant_id}:{router_id}"`) e inserta en `router_credentials_vault`.
  4. Si `connect_and_discover_now == true`:
     - Conecta a `/rest/system/resource`, `/rest/system/routerboard` y `/rest/system/identity` del MikroTik.
     - Captura la huella SHA-256 del certificado SSL autofirmado (**TOFU**) y pasa `ssl_trust_status` a `'TRUSTED_PINNED'`.
     - Actualiza automáticamente `ros_identity`, `board_name`, `model_name`, `architecture_name`, `ros_version`, `firmware_version` y `serial_number`.
  5. Registra `ROUTER_CREATED` en `audit_logs` y responde 201 Created.

### **1.3 POST /api/v1/inventory/routers/{router_id}/discover y /sync-discovery — Forzar Autodescubrimiento y Pinning TOFU**

- **Roles Permitidos:** SUPERADMIN_GLOBAL, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3, INVENTORY_MANAGER.
- **Acción:** Consulta bajo demanda el MikroTik físico/CHR vía REST API (`/rest/system/resource`, `/rest/system/routerboard`, `/rest/system/identity`), calcula y fija la huella SSL TOFU SHA-256 en caso de estar pendiente, y actualiza modelo, arquitectura, versión de RouterOS, firmware y uptime en tiempo real. Utilizado por el botón *TOFU / Redescubrir* en la grilla de la UI.

### **1.4 POST /api/v1/inventory/routers/{router_id}/repin-ssl — Autorizar Cambio de Certificado SSL Autofirmado (Re-Pin TOFU)**

- **Roles Permitidos:** Exclusivamente SUPERADMIN_GLOBAL y TENANT_ADMIN.
- **Request Body:** `{"totp_code": "123456", "expected_new_sha256_fingerprint": "a9f4..."}`.
- Actualiza la huella SHA-256 autorizada tras verificar el código 2FA del administrador y escribe `ROUTER_SSL_REPINNED` en `audit_logs`.

## **2. Importación Masiva de Equipos por CSV en 2 Pasos (/api/v1/inventory/import-csv)**

Como acordamos en el diseño, el onboarding por CSV es de **baja complejidad** reutilizando los validadores Pydantic de CreateRouterRequest y se divide en 2 endpoints simples:

### **2.1 POST /api/v1/inventory/import-csv/dry-run — Paso 1: Validación en Seco (Sin Escribir en Base de Datos)**

- **Roles Permitidos:** SUPERADMIN_GLOBAL, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3, INVENTORY_MANAGER.
- **Entrada:** multipart/form-data con archivo .csv (máximo 500 filas, 2 MB).
- **Columnas del CSV:** `display_name,api_base_url,api_port,api_username,api_password,network_role,admin_state,physical_location,latitude,longitude,online_since_date,serial_number,tags`
- **Proceso:**
  - Analiza fila por fila con `csv.DictReader` en memoria.
  - Verifica formato HTTPS, roles válidos, rangos de coordenadas GPS y duplicados contra la base de datos o dentro del mismo archivo CSV.
- **Response 200 OK (CsvDryRunResponse):**

```json
{
  "total_rows": 15,
  "valid_rows_count": 14,
  "invalid_rows_count": 1,
  "can_proceed": true,
  "rows_preview": [
    {
      "row_number": 2,
      "display_name": "CCR2004-Core-1",
      "is_valid": true,
      "errors": []
    },
    {
      "row_number": 3,
      "display_name": "RB4011-Repetido",
      "is_valid": false,
      "errors": ["El serial_number D4460B999 ya existe en este Tenant"]
    }
  ]
}
```

### **2.2 POST /api/v1/inventory/import-csv/commit — Paso 2: Confirmación e Importación Transaccional**

- Recibe la lista de filas validadas, cifra cada contraseña con AES-256-GCM, inserta en bloque en PostgreSQL, registra el lote en `audit_logs` y encola en el worker el autodescubrimiento TOFU en segundo plano para los nuevos routers.

## **3. Endpoints de Bóveda Criptográfica y Rotación de Claves (/api/v1/inventory/routers/{router_id}/vault)**

### **3.1 POST /api/v1/inventory/routers/{router_id}/vault/reveal — Revelar Claves API (*Step-Up Auth* de 30 Segundos)**

- **Roles Permitidos:** **EXCLUSIVAMENTE SUPERADMIN_GLOBAL y TENANT_ADMIN** (los 2 perfiles más altos del sistema). Cualquier otro perfil recibe HTTP 403 Forbidden.
- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.
- **Request Body (VaultRevealRequest):**

```json
{
  "totp_code": "839201",
  "reason": "Revisión de emergencia por mantenimiento en sitio"
}
```

- **Proceso:**
  1. Verifica el código 2FA TOTP en vivo del administrador.
  2. Escribe de manera inmutable en `audit_logs` el evento `CREDENTIAL_REVEALED` incluyendo reason, actor_ip y router_id.
  3. Desencripta `current_password` y `previous_password` (si existe) usando AES-256-GCM con AAD = `f"{tenant_id}:{router_id}"`.
- **Response 200 OK (Con cabecera Cache-Control: no-store):**

```json
{
  "router_id": "01928900-aaaa-7bbb-8ccc-111122223333",
  "api_username": "rosgrid_api_admin",
  "current_password": "rG9#mK2$vP8!xL4@qW7&zN1*tB5^cF3_",
  "previous_password": "ClaveAnteriorAntesDeRotacion#2026",
  "last_rotated_at": "2026-10-01T03:00:00Z",
  "next_rotation_due_at": "2026-10-31T03:00:00Z",
  "display_ttl_seconds": 30
}
```

### **3.2 POST /api/v1/inventory/routers/{router_id}/vault/rotate-now — Rotación Automática de Contraseña API en el MikroTik**

- **Roles Permitidos:** SUPERADMIN_GLOBAL, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3, INVENTORY_MANAGER.
- **Algoritmo Seguro de Rotación sin Pérdida de Acceso:**
  1. Genera en memoria una nueva contraseña criptográfica de 32 caracteres (`secrets.token_urlsafe(24)` + símbolos seguros sin comillas ni espacios que afecten scripts de RouterOS).
  2. Mueve la `current_password_*` actual de la bóveda a las columnas `previous_password_*` y guarda la nueva contraseña cifrada como `current_password_*` dentro de una transacción pendiente.
  3. Se conecta al MikroTik usando la contraseña anterior y ejecuta `PATCH /rest/user/<api_username>` con `{"password": "<nueva_clave_32_chars>"}`.
  4. Realiza inmediatamente una petición de comprobación `GET /rest/system/identity` autenticándose con la **nueva contraseña**.
  5. Si responde 200 OK, hace COMMIT en PostgreSQL actualizando `last_rotated_at = NOW()` y registra `CREDENTIAL_AUTO_ROTATED` en `audit_logs`.

## **4. Endpoints de Ventanas de Mantenimiento Programadas (/api/v1/maintenance/windows)**

| **Método** | **Ruta** | **Roles Permitidos** | **Descripción** |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/maintenance/windows` | Todos los roles | Lista ventanas activas, futuras e históricas del Tenant |
| POST | `/api/v1/maintenance/windows` | SUPERADMIN, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3, INVENTORY_MGR | Crea una ventana por router_id o por target_tag entre starts_at y ends_at |
| POST | `/api/v1/maintenance/windows/{window_id}/cancel` | SUPERADMIN, TENANT_ADMIN, SUPERVISOR, SUPPORT_L3 | Cancela anticipadamente una ventana y reactiva el envío de alertas en Redis |
