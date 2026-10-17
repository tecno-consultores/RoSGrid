# 10 — ENDPOINTS BACKEND: AUTENTICACIÓN MULTI-TENANT, 2FA TOTP, TENANTS, USUARIOS Y KILL-SWITCH (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los contratos HTTP exactos (Rutas, Métodos, Headers, Esquemas Pydantic v2 de Entrada/Salida, Códigos de Estado y Reglas RBAC) para los routers fastapi/src/api/v1/auth.py, fastapi/src/api/v1/tenants.py, fastapi/src/api/v1/users.py y fastapi/src/api/v1/sessions.py.




## **1. Router de Autenticación y 2FA (/api/v1/auth)**

### **1.1 POST /api/v1/auth/login — Paso 1: Credenciales Multi-Tenant (tenant\_slug + Correo + Clave)**

- **Acceso:** Público (con Rate-Limiting por IP y por tenant\_slug + email en Redis).

- **Request Body (LoginStep1Request):**


\{


  "tenant\_slug": "isp-norte",


  "email": "jperez@ispnorte.net",


  "password": "MiPasswordUltraSegura2026!"


\}


- **Respuestas:**

  - 200 OK (Credenciales válidas, pasa a desafío 2FA):


\{


  "challenge\_id": "01928c11-2233-7a44-8555-6677889900aa",


  "tenant\_slug": "isp-norte",


  "next\_step": "VERIFY\_2FA\_TOTP",


  "totp\_provisioning\_uri": null,


  "expires\_in\_seconds": 180


\}


*(Si el usuario entra por primera vez y debe enrolar su 2FA, next\_step será "ENROLL\_2FA\_REQUIRED" y totp\_provisioning\_uri contendrá la URI otpauth://totp/... para renderizar el QR en Vue 3).*


  - 401 Unauthorized: \{"detail": "Credenciales inválidas o empresa no encontrada"\}

  - 403 Forbidden: \{"detail": "Cuenta pendiente de aprobación por el Administrador"\} (si el usuario fue creado vía auto-registro y aún no ha sido aprobado).

  - 423 Locked: \{"detail": "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos."\}

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

- **Acceso:** Público con challenge\_id vigente en Redis (rg:\{tenant\_id\}:preauth:\{challenge\_id\}).

- **Request Body (Verify2FARequest):**


\{


  "challenge\_id": "01928c11-2233-7a44-8555-6677889900aa",


  "totp\_code": "482910"


\}


- **Efecto en Cookies HTTP (Set-Cookie):**

  - Establece \_\_Host-rg\_at (HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=600).

  - Establece \_\_Host-rg\_rt (HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh; Max-Age=28800).

  - Establece rg\_csrf (Secure; SameSite=Strict; Path=/; Max-Age=28800).

- **Response 200 OK (AuthSessionResponse):**


\{


  "session\_id": "01928b4c-9988-7d11-9000-112233445566",


  "user": \{


    "id": "01928a10-4b22-7c00-8123-9876543210ab",


    "username": "jperez",


    "email": "jperez@ispnorte.net",


    "full\_name": "Jose Perez",


    "role": "SUPPORT\_L3",


    "tenant\_id": "01928000-1111-7000-8000-000000000001",


    "tenant\_slug": "isp-norte",


    "tenant\_name": "ISP Norte Telecom C.A.",


    "has\_all\_routers\_access": true


  \},


  "csrf\_token": "9f8e7d6c5b4a3210.1792000000.a1b2c3d4e5f6..."


\}

### **1.3 POST /api/v1/auth/refresh — Rotación Silenciosa de Refresh Token**

- **Acceso:** Requiere cookie \_\_Host-rg\_rt.

- **Respuesta 200 OK:** Rota el token en la familia de Redis (rg:\{tenant\_id\}:rt\_family:\{family\_id\}), emite nuevas cookies \_\_Host-rg\_at, \_\_Host-rg\_rt y rg\_csrf, y devuelve \{"status": "refreshed", "csrf\_token": "..."\}.

- **Respuesta 401 Unauthorized:** Si el token expiró, la sesión fue destruida por *Kill-Switch* o se detectó robo por reúso (*Reuse Detection*).

### **1.4 POST /api/v1/auth/logout — Cierre de Sesión Propio**

- **Cabeceras Requeridas:** X-CSRF-Token.

- **Respuesta 204 No Content:** Elimina la sesión en Redis, limpia las 3 cookies y registra USER\_LOGOUT en audit\_logs.

### **1.5 GET /api/v1/auth/me — Perfil y Permisos de la Sesión Actual**

- **Acceso:** Cualquier usuario autenticado con sesión viva en Redis.

- **Nota de Compatibilidad Karate Labs:** Además de /api/v1/auth/me, el backend expondrá el alias /users/me que devuelve HTTP 401 \{"detail": "Not authenticated"\} cuando se invoca sin sesión (para cumplir exactamente el escenario base de api\_test.feature).




## **2. Router de Administración de Empresas — Multi-Tenant (/api/v1/tenants)**

- **Rol Requerido:** Exclusivamente SUPERADMIN\_GLOBAL (cualquier otro rol recibe 403 Forbidden).

- **Cabeceras Requeridas en Mutaciones:** X-CSRF-Token e Idempotency-Key.


| **Método** | **Ruta** | **Descripción** | **Código Éxito** |
| - | - | - | :-: |
| GET | /api/v1/tenants | Lista paginada de organizaciones (Tenants), estado, cuotas y conteo de routers/usuarios | 200 OK |
| POST | /api/v1/tenants | Crea un nuevo Tenant + su primer usuario TENANT\_ADMIN inicial en una sola transacción | 201 Created |
| PATCH | /api/v1/tenants/\{tenant\_id\} | Modifica estado (ACTIVE, SUSPENDED, MAINTENANCE), cuotas o default\_safemode\_seconds | 200 OK |




## **3. Router de Usuarios y Asignación de Equipos (/api/v1/users)**

- **Roles Permitidos:**

  - Lectura (GET): SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, AUDITOR.

  - Escritura (POST, PATCH, PUT, DELETE): Exclusivamente SUPERADMIN\_GLOBAL y TENANT\_ADMIN.

### **3.1 GET /api/v1/users — Listar Usuarios del Tenant**

- Soporta filtros ?role=SUPPORT\_L2&is\_active=true&search=perez.

### **3.2 POST /api/v1/users — Crear Usuario dentro del Tenant**

- **Request Body (CreateUserRequest):**


\{


  "username": "stecnico1",


  "email": "soporte1@ispnorte.net",


  "full\_name": "Carlos Mendoza",


  "temporary\_password": "TempPassword\#2026!",


  "role": "SUPPORT\_L1",


  "has\_all\_routers\_access": false,


  "allowed\_cidr\_list": \[\]


\}

### **3.3 PUT /api/v1/users/\{user\_id\}/router-permissions — Asignar Routers y Permisos Granulares a un Técnico**

- Reemplaza o sincroniza de forma atómica los equipos MikroTik que ese técnico tiene permiso de ver y operar (user\_router\_permissions):

- **Request Body (AssignUserRoutersRequest):**


\{


  "has\_all\_routers\_access": false,


  "router\_assignments": \[


    \{


      "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


      "can\_read": true,


      "can\_write\_layer1": true,


      "can\_write\_layer2": false,


      "can\_execute\_diagnostics": true,


      "can\_trigger\_backup": true,


      "can\_reboot": false,


      "bypass\_maker\_checker": false


    \}


  \]


\}


- **Efecto Inmediato:** Invalida la caché de permisos del usuario en Redis y registra el cambio en audit\_logs (USER\_ROUTER\_PERMISSIONS\_UPDATED).

### **3.4 POST /api/v1/users/\{user\_id\}/reset-2fa — Reiniciar Enrolamiento 2FA TOTP de un Usuario**

- Requiere que el TENANT\_ADMIN envíe su propio totp\_code de confirmación. Borra el secreto TOTP del usuario objetivo, revoca todas sus sesiones activas en Redis (vía *Kill-Switch*) y lo obliga a escanear un nuevo código QR en su próximo inicio de sesión.

### **3.5 PUT /api/v1/users/\{user\_id\}/approve — Aprobación Maker-Checker de Usuario Registrado**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN.
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

### **3.6 DELETE /api/v1/users/\{user\_id\}/reject — Rechazo y Eliminación Segura de Solicitud de Usuario**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN.
- **Comportamiento:**
  - Si el usuario nunca generó registros dependientes en tablas auditadas, se elimina físicamente de `users`.
  - Si existen referencias en `audit_logs` que dispararían el trigger de inmutabilidad WORM, se aplica soft-revocación segura (`is_active = False`, username ofuscado con sufijo de revocación y `status = 'REJECTED'`).
  - Registra el evento de auditoría `USER_REGISTRATION_REJECTED`.
- **Respuestas:**
  - 200 OK: `{"status": "REJECTED", "user_id": "...", "message": "Solicitud de usuario rechazada y eliminada"}`

### **3.7 Switch Global de Auto-Registro: POST y GET /api/v1/users/registration-***

- **GET /api/v1/users/registration-status:**
  - Retorna `{ "registration_enabled": true/false }` leyendo la llave `rosgrid:registration_enabled` en KeyDB (por defecto `True`).
- **POST /api/v1/users/registration-toggle:**
  - **Roles Permitidos:** SUPERADMIN\_GLOBAL.
  - Alterna el estado en KeyDB y audita el evento `REGISTRATION_SWITCH_TOGGLED`.
  - Retorna el nuevo estado booleano.




## **4. Router de Control de Sesiones en Vivo y *Kill-Switch* (/api/v1/sessions)**

Permite al **Administrador de Tenant** y al **Supervisor** auditar en tiempo real quién está conectado a RoSGrid, qué MikroTik está visualizando y expulsarlo en el acto.

### **4.1 GET /api/v1/sessions/active — Listar Técnicos Conectados en Tiempo Real**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, AUDITOR.

- **Fuente de Datos:** Lee directamente el índice rg:\{tenant\_id\}:active\_sessions y los hashes rg:\{tenant\_id\}:sess:\* en Redis.

- **Response 200 OK:**


\{


  "total\_active\_sessions": 2,


  "items": \[


    \{


      "session\_id": "01928b4c-9988-7d11-9000-112233445566",


      "user\_id": "01928a10-4b22-7c00-8123-9876543210ab",


      "username": "stecnico1",


      "full\_name": "Carlos Mendoza",


      "role": "SUPPORT\_L1",


      "ip\_address": "192.168.20.14",


      "user\_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8)...",


      "current\_router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


      "current\_router\_name": "RB4011-Nodo-Valencia",


      "current\_view\_path": "/routers/01928900-.../interfaces",


      "created\_at": "2026-10-14T16:30:00Z",


      "last\_activity\_at": "2026-10-14T18:18:10Z"


    \}


  \]


\}

### **4.2 DELETE /api/v1/sessions/\{session\_id\} — Ejecutar *Kill-Switch* sobre una Sesión Específica**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR.

- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.

- **Query / Body Opcional:** \{"reason": "Fin de turno / Intervención no autorizada en router de borde"\}.

- **Proceso:**

  1. Elimina el Hash de sesión y su familia de Refresh Token en Redis.

  2. Publica el evento SESSION\_KILLED en rg:pubsub:events:\{tenant\_id\} cerrando en el acto cualquier WebSocket abierto por esa sesión.

  3. Registra SESSION\_KILLED\_BY\_ADMIN en audit\_logs.

- **Respuesta:** 200 OK (\{"status": "terminated", "session\_id": "..."\}).

### **4.3 DELETE /api/v1/sessions/user/\{user\_id\}/all — Ejecutar *Kill-Switch* Total + Bloqueo Opcional de Usuario**

- Revoca simultáneamente todas las sesiones activas de ese usuario en todos sus dispositivos y opcionalmente marca is\_locked = True en PostgreSQL.
