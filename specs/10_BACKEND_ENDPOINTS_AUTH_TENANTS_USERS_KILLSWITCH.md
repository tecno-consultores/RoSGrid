# 10 — ENDPOINTS BACKEND: AUTENTICACIÓN MULTI-TENANT, 2FA TOTP, TENANTS, USUARIOS Y KILL-SWITCH (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los contratos HTTP exactos (Rutas, Métodos, Headers, Esquemas Pydantic v2 de Entrada/Salida, Códigos de Estado y Reglas RBAC) para los routers `fastapi/src/api/v1/auth.py`, `fastapi/src/api/v1/tenants.py`, `fastapi/src/api/v1/users.py` y `fastapi/src/api/v1/sessions.py`.

## **1. Router de Autenticación y 2FA (/api/v1/auth)**

### **1.1 POST /api/v1/auth/login — Paso 1: Credenciales Multi-Tenant (tenant_slug + Correo + Clave)**

- **Acceso:** Público (con Rate-Limiting por IP y por tenant_slug + email en Redis).
- **Request Body (LoginStep1Request):**

```json
{
  "tenant_slug": "isp-norte",
  "email": "jperez@ispnorte.net",
  "password": "MiPasswordUltraSegura2026!"
}
```

- **Respuestas:**
  - 200 OK (Credenciales válidas, pasa a desafío 2FA):

```json
{
  "challenge_id": "01928c11-2233-7a44-8555-6677889900aa",
  "tenant_slug": "isp-norte",
  "next_step": "VERIFY_2FA_TOTP",
  "totp_provisioning_uri": null,
  "expires_in_seconds": 180
}
```

*(Si el usuario entra por primera vez y debe enrolar su 2FA, `next_step` será "ENROLL_2FA_REQUIRED" y `totp_provisioning_uri` contendrá la URI `otpauth://totp/...` para renderizar el QR en Vue 3).*

- **Otras Respuestas:**
  - 401 Unauthorized: `{"detail": "Credenciales inválidas o empresa no encontrada"}`
  - 403 Forbidden: `{"detail": "Cuenta pendiente de aprobación por el Administrador"}` (si el usuario fue creado vía auto-registro y aún no ha sido aprobado).
  - 422 Unprocessable Entity: En desarrollo devuelve el array de errores de validación Pydantic. En producción (`ROSGRID_ENV=production`), se intercepta globalmente con `RequestValidationError` y devuelve `{"detail": "Los datos proporcionados no cumplen con los requisitos de validación."}`, ocultando la estructura interna mientras registra el detalle en los logs del contenedor.
  - 423 Locked: `{"detail": "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos."}`

- **Protección contra Asignación Masiva (*Mass Assignment*):**
  - Todos los modelos de entrada (`LoginStep1Request`, `RegisterOperatorRequest`, `UserCreate`, `UserUpdate`, etc.) implementan `model_config = ConfigDict(extra="forbid")`, rechazando cualquier atributo adicional enviado por el cliente (como `role`, `is_superuser`, etc.).


- **Auditoría Forense Inmutable WORM de Autenticación:**
  - Todos los intentos fallidos de inicio de sesión (`LOGIN_FAILED_USER_NOT_FOUND`, `LOGIN_FAILED_INVALID_PASSWORD`, `LOGIN_FAILED_ACCOUNT_LOCKED`, `LOGIN_FAILED_USER_INACTIVE`, `2FA_VERIFICATION_FAILED`) se registran atómicamente en `audit_logs` con su hash encadenado SHA-256, IP y User-Agent del actor.
  - Al completar exitosamente el flujo de autenticación se registra el evento `LOGIN_SUCCESSFUL`.

- **Política de Sesión Única Estricta:**
  - Cada operador o usuario solo puede tener una (1) sola sesión activa simultánea en KeyDB.
  - El inicio de una nueva sesión revoca forzosamente cualquier sesión previa del usuario mediante el Kill-Switch global `kill_all_user_sessions()`, notificando al canal WebSocket vía `SESSION_KILLED` y registrando el evento forense `SESSION_KILLED_DUPLICATE_LOGIN`.

### **1.1B POST /api/v1/auth/register — Auto-Registro Web de Operadores (Maker-Checker)**

- **Acceso:** Público (sujeto al switch global en KeyDB `rosgrid:registration_enabled`). Si está deshabilitado responde HTTP 403 Forbidden.
- **Request Body (RegisterOperatorRequest):**

```json
{
  "full_name": "Ing. Roberto Díaz",
  "username": "rdiaz",
  "email": "rdiaz@isp.net",
  "password": "PasswordSeguro2026!",
  "tenant_id": "01928a00-1111-7000-8000-000000000001"
}
```

- **Comportamiento:**
  - Valida unicidad de `username` y `email`.
  - Crea el registro en `users` con rol inicial `SUPPORT_L1`, bandera `is_active=False` y estado en metadata `status='PENDING_APPROVAL'`.
  - Registra el evento `USER_REGISTRATION_REQUESTED` en `audit_logs` (WORM).
- **Respuestas:**
  - 201 Created: `{"status": "PENDING_APPROVAL", "user_id": "01928b55...", "message": "Solicitud de registro enviada con éxito. Un administrador debe aprobar tu cuenta antes de iniciar sesión."}`
  - 400 Bad Request: `{"detail": "El nombre de usuario o correo ya está registrado"}`
  - 403 Forbidden: `{"detail": "El registro público de usuarios se encuentra deshabilitado por el administrador"}`

### **1.2 POST /api/v1/auth/2fa/verify — Paso 2: Validación TOTP y Emisión de Cookies Split-Credential**

- **Acceso:** Público con challenge_id vigente en Redis (`rg:{tenant_id}:preauth:{challenge_id}`).
- **Request Body (Verify2FARequest):**

```json
{
  "challenge_id": "01928c11-2233-7a44-8555-6677889900aa",
  "totp_code": "482910"
}
```

- **Efecto en Cookies HTTP (Set-Cookie):**
  - Establece `__Host-rg_at` (`HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=600`).
  - Establece `__Host-rg_rt` (`HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh; Max-Age=28800`).
  - Establece `rg_csrf` (`Secure; SameSite=Strict; Path=/; Max-Age=28800`).
- **Response 200 OK (AuthSessionResponse):**

```json
{
  "session_id": "01928b4c-9988-7d11-9000-112233445566",
  "user": {
    "id": "01928a10-4b22-7c00-8123-9876543210ab",
    "username": "jperez",
    "email": "jperez@ispnorte.net",
    "full_name": "Jose Perez",
    "role": "SUPPORT_L3",
    "tenant_id": "01928000-1111-7000-8000-000000000001",
    "tenant_slug": "isp-norte",
    "tenant_name": "ISP Norte Telecom C.A.",
    "has_all_routers_access": true
  },
  "csrf_token": "9f8e7d6c5b4a3210.1792000000.a1b2c3d4e5f6..."
}
```

### **1.3 POST /api/v1/auth/refresh — Rotación Silenciosa de Refresh Token**

- **Acceso:** Requiere cookie `__Host-rg_rt`.
- **Respuesta 200 OK:** Rota el token en la familia de Redis (`rg:{tenant_id}:rt_family:{family_id}`), emite nuevas cookies `__Host-rg_at`, `__Host-rg_rt` y `rg_csrf`, y devuelve `{"status": "refreshed", "csrf_token": "..."}`.
- **Respuesta 401 Unauthorized:** Si el token expiró, la sesión fue destruida por *Kill-Switch* o se detectó robo por reúso (*Reuse Detection*).

### **1.4 POST /api/v1/auth/logout — Cierre de Sesión Propio**

- **Cabeceras Requeridas:** `X-CSRF-Token`.
- **Respuesta 204 No Content:** Elimina la sesión en Redis, limpia las 3 cookies y registra `USER_LOGOUT` en `audit_logs`.

### **1.5 GET /api/v1/auth/me — Perfil y Permisos de la Sesión Actual**

- **Acceso:** Cualquier usuario autenticado con sesión viva en Redis.
- **Nota de Compatibilidad Karate Labs:** Además de `/api/v1/auth/me`, el backend expondrá el alias `/users/me` que devuelve HTTP 401 `{"detail": "Not authenticated"}` cuando se invoca sin sesión (para cumplir exactamente el escenario base de `api_test.feature`).

## **2. Router de Administración de Empresas — Multi-Tenant (/api/v1/tenants)**

- **Rol Requerido:** Exclusivamente `SUPERADMIN_GLOBAL` (cualquier otro rol recibe 403 Forbidden).
- **Cabeceras Requeridas en Mutaciones:** `X-CSRF-Token` e `Idempotency-Key`.

| **Método** | **Ruta** | **Descripción** | **Código Éxito** |
| :--- | :--- | :--- | :---: |
| GET | `/api/v1/tenants` | Lista paginada de organizaciones (Tenants), estado, cuotas y conteo de routers/usuarios | 200 OK |
| POST | `/api/v1/tenants` | Crea un nuevo Tenant + su primer usuario `TENANT_ADMIN` inicial en una sola transacción | 201 Created |
| PATCH | `/api/v1/tenants/{tenant_id}` | Modifica estado (ACTIVE, SUSPENDED, MAINTENANCE), cuotas o default_safemode_seconds | 200 OK |

## **3. Router de Usuarios y Asignación de Equipos (/api/v1/users)**

- **Roles Permitidos:**
  - Lectura (GET): `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `AUDITOR`.
  - Escritura (POST, PATCH, PUT, DELETE): Exclusivamente `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`.

### **3.1 GET /api/v1/users — Listar Usuarios del Tenant**

- Soporta filtros `?role=SUPPORT_L2&is_active=true&search=perez`.

### **3.2 POST /api/v1/users — Crear Usuario dentro del Tenant**

- **Request Body (CreateUserRequest):**

```json
{
  "username": "stecnico1",
  "email": "soporte1@ispnorte.net",
  "full_name": "Carlos Mendoza",
  "temporary_password": "TempPassword#2026!",
  "role": "SUPPORT_L1",
  "has_all_routers_access": false,
  "allowed_cidr_list": []
}
```

### **3.3 PUT /api/v1/users/{user_id}/router-permissions — Asignar Routers y Permisos Granulares a un Técnico**

Reemplaza o sincroniza de forma atómica los equipos MikroTik que ese técnico tiene permiso de ver y operar (`user_router_permissions`):

- **Request Body (AssignUserRoutersRequest):**

```json
{
  "has_all_routers_access": false,
  "router_assignments": [
    {
      "router_id": "01928900-aaaa-7bbb-8ccc-111122223333",
      "can_read": true,
      "can_write_layer1": true,
      "can_write_layer2": false,
      "can_execute_diagnostics": true,
      "can_trigger_backup": true,
      "can_reboot": false,
      "bypass_maker_checker": false
    }
  ]
}
```

- **Efecto Inmediato:** Invalida la caché de permisos del usuario en Redis y registra el cambio en `audit_logs` (`USER_ROUTER_PERMISSIONS_UPDATED`).

### **3.4 POST /api/v1/users/{user_id}/reset-2fa — Reiniciar Enrolamiento 2FA TOTP de un Usuario**

- Requiere que el `TENANT_ADMIN` envíe su propio `totp_code` de confirmación. Borra el secreto TOTP del usuario objetivo, revoca todas sus sesiones activas en Redis (vía *Kill-Switch*) y lo obliga a escanear un nuevo código QR en su próximo inicio de sesión.

### **3.5 PUT /api/v1/users/{user_id}/approve — Aprobación Maker-Checker de Usuario Registrado**

- **Roles Permitidos:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Request Body (ApproveUserRequest):**

```json
{
  "role": "SUPPORT_L2",
  "can_write": true
}
```

- **Comportamiento:**
  - Valida que el usuario exista en el tenant y esté en estado pendiente.
  - Actualiza `is_active = True`, asigna el `role` y establece en metadata `status = 'ACTIVE'`.
  - Registra el evento de auditoría `USER_REGISTRATION_APPROVED` en `audit_logs` con `actor_user_id` del administrador aprobador.
- **Respuestas:**
  - 200 OK: `{"status": "ACTIVE", "user_id": "...", "message": "Usuario aprobado exitosamente"}`
  - 404 Not Found: `{"detail": "Usuario no encontrado"}`

### **3.6 DELETE /api/v1/users/{user_id}/reject — Rechazo y Eliminación Segura de Solicitud de Usuario**

- **Roles Permitidos:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`.
- **Comportamiento:**
  - Si el usuario nunca generó registros dependientes en tablas auditadas, se elimina físicamente de `users`.
  - Si existen referencias en `audit_logs` que dispararían el trigger de inmutabilidad WORM, se aplica soft-revocación segura (`is_active = False`, username ofuscado con sufijo de revocación y `status = 'REJECTED'`).
  - Registra el evento de auditoría `USER_REGISTRATION_REJECTED`.
- **Respuestas:**
  - 200 OK: `{"status": "REJECTED", "user_id": "...", "message": "Solicitud de usuario rechazada y eliminada"}`

### **3.7 Switch Global de Auto-Registro: POST y GET /api/v1/users/registration-***

- **GET /api/v1/users/registration-status:**
  - Retorna `{"registration_enabled": true}` leyendo la llave `rosgrid:registration_enabled` en KeyDB (por defecto `True`).
- **POST /api/v1/users/registration-toggle:**
  - **Roles Permitidos:** `SUPERADMIN_GLOBAL`.
  - Alterna el estado en KeyDB y audita el evento `REGISTRATION_SWITCH_TOGGLED`.
  - Retorna el nuevo estado booleano.

## **4. Router de Control de Sesiones en Vivo y *Kill-Switch* (/api/v1/sessions)**

Permite al **Administrador de Tenant** y al **Supervisor** auditar en tiempo real quién está conectado a RoSGrid, qué MikroTik está visualizando y expulsarlo en el acto.

### **4.1 GET /api/v1/sessions/active — Listar Técnicos Conectados en Tiempo Real**

- **Roles Permitidos:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `AUDITOR`.
- **Fuente de Datos:** Lee directamente el índice `rg:{tenant_id}:active_sessions` y los hashes `rg:{tenant_id}:sess:*` en Redis.
- **Response 200 OK:**

```json
{
  "total_active_sessions": 2,
  "items": [
    {
      "session_id": "01928b4c-9988-7d11-9000-112233445566",
      "user_id": "01928a10-4b22-7c00-8123-9876543210ab",
      "username": "stecnico1",
      "full_name": "Carlos Mendoza",
      "role": "SUPPORT_L1",
      "ip_address": "192.168.20.14",
      "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8)...",
      "current_router_id": "01928900-aaaa-7bbb-8ccc-111122223333",
      "current_router_name": "RB4011-Nodo-Valencia",
      "current_view_path": "/routers/01928900-.../interfaces",
      "created_at": "2026-10-14T16:30:00Z",
      "last_activity_at": "2026-10-14T18:18:10Z"
    }
  ]
}
```

### **4.2 DELETE /api/v1/sessions/{session_id} — Ejecutar *Kill-Switch* sobre una Sesión Específica**

- **Roles Permitidos:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`.
- **Cabeceras Requeridas:** `X-CSRF-Token`, `Idempotency-Key`.
- **Query / Body Opcional:** `{"reason": "Fin de turno / Intervención no autorizada en router de borde"}`.
- **Proceso:**
  1. Elimina el Hash de sesión y su familia de Refresh Token en Redis.
  2. Publica el evento `SESSION_KILLED` en `rg:pubsub:events:{tenant_id}` cerrando en el acto cualquier WebSocket abierto por esa sesión.
  3. Registra `SESSION_KILLED_BY_ADMIN` en `audit_logs`.
- **Respuesta:** 200 OK (`{"status": "terminated", "session_id": "..."}`).

### **4.3 DELETE /api/v1/sessions/user/{user_id}/all — Ejecutar *Kill-Switch* Total + Bloqueo Opcional de Usuario**

- Revoca simultáneamente todas las sesiones activas de ese usuario en todos sus dispositivos y opcionalmente marca `is_locked = True` en PostgreSQL.
