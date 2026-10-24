# 20 — VISTAS FRONTEND: LOGIN MULTI-TENANT + 2FA, GESTIÓN DE USUARIOS, MATRIZ DE EQUIPOS Y KILL-SWITCH EN VIVO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las vistas de autenticación, administración de organizaciones, gestión de usuarios, matriz visual de asignación de MikroTiks por técnico y el panel de control de sesiones activas en tiempo real (*Kill-Switch*) dentro de `vue3/src/views/auth/` y `vue3/src/views/admin/`.

## **1. Vista de Inicio de Sesión Multi-Tenant + 2FA (vue3/src/views/auth/LoginView.vue)**

Ruta: `/login` (Una de las 3 rutas auditadas directamente por `@axe-core/playwright` y Snapshot Testing en `accessibility.e2e.ts`).

### **1.1 Etapa 1: Identificación Multi-Tenant y Credenciales Primarias**

El formulario presenta 3 campos obligatorios con etiquetas `<label>` explícitas y atributos `autocomplete`:

1. **Identificador de Empresa (`input#tenant-slug`):**
   - Placeholder: ej. `isp-norte`. Normaliza automáticamente a minúsculas y guiones.
2. **Correo Electrónico o Usuario (`input#login-email`):**
   - `autocomplete="username"`.
3. **Contraseña (`input#login-password`):**
   - `type="password"`, `autocomplete="current-password"`, con botón accesible (`aria-label="Mostrar u ocultar contraseña"`) para alternar visibilidad.
4. **Banner de Motivo de Redirección:**
   - Si la URL contiene `?reason=session_revoked`, muestra una alerta accesible (`role="alert"`) informando: *"Tu sesión fue cerrada por un Administrador o Supervisor"*.

### **1.1B Etapa 1B: Formulario de Auto-Registro de Operadores (`currentStep === 'REGISTER'`)**

- Si el auto-registro está habilitado por el Superadmin, se muestra el botón *"Solicitar acceso de operador"*.
- Al pulsar, la tarjeta de login transmuta al formulario de registro accesible:
  - Nombre completo (`full_name`)
  - Nombre de usuario (`username`)
  - Correo electrónico (`email`)
  - Contraseña robusta (`password`) y confirmación (`confirmPassword`)
- Al enviar (`POST /api/v1/auth/register`), el usuario entra en estado `PENDING_APPROVAL` y se muestra un banner táctil con mensaje explicativo invitando a contactar al Superadmin para su habilitación.
- Permite regresar inmediatamente al formulario de login mediante el botón *"Volver al inicio de sesión"*.

### **1.2 Etapa 2A: Enrolamiento Inicial de 2FA TOTP (Si `next_step === 'ENROLL_2FA_REQUIRED'`)**

- Renderiza en un `<canvas>` local (usando la librería qrcode sin llamadas externas a internet) el código QR del `totp_provisioning_uri`.
- Muestra la clave secreta en formato texto monoespaciado por si el técnico desea ingresarla manualmente en Google Authenticator / Authy / FreeOTP.
- Solicita ingresar el primer código de 6 dígitos generado por su aplicación para confirmar el enrolamiento y muestra los códigos de recuperación de emergencia por única vez con botón de descarga `.txt`.

### **1.3 Etapa 2B: Verificación de Código 2FA TOTP (`next_step === 'VERIFY_2FA_TOTP'`)**

- Presenta un campo numérico de 6 dígitos (`inputmode="numeric"`, `pattern="[0-9]{6}"`, `autocomplete="one-time-code"`) con cuenta regresiva del tiempo restante del `challenge_id` (180 segundos).
- Al completarse el 6.º dígito, dispara `POST /api/v1/auth/2fa/verify` y redirige al Dashboard (o al Wallboard NOC si el rol es `NOC_MONITOR`).

### **1.4 Pie de Página y Branding Institucional (`LoginView.vue`)**

El pie de la pantalla de login incorpora un bloque sutil y elegante (`.login-institutional-footer`), ubicado debajo de la tarjeta de inicio de sesión:

1. **Enlace al Repositorio Oficial en GitHub:**
   - Enlace `<a>` con `target="_blank" rel="noopener noreferrer"` hacia `https://github.com/tecno-consultores/RoSGrid/`.
   - Renderiza un icono SVG vectorial de GitHub (20x20px) con atributo `aria-label="Repositorio oficial de RoSGrid en GitHub"` y `title="Código fuente en GitHub"`.
2. **Atribución de Autoría y Sitio Web:**
   - Texto con enlace `<a>`: *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/)"* (`target="_blank" rel="noopener noreferrer"`), con tipografía de alta legibilidad y estilo discreto.
3. **Versión y Licencia del Sistema:**
   - Presenta la cadena normalizada: *"Elaborado por Tecno Consultores 2023 C.A. • Licencia GNU GPLv3"*, acompañada del número de versión del sistema (ej. `v1.0.0` extraído del entorno de compilación).
4. **Diseño y Accesibilidad:**
   - Tipografía reducida (`0.75rem` / `12px`), colores tenues en gris pizarra (`--rg-text-muted`, ratio de contraste `>= 4.5:1` sobre `--rg-bg-canvas` para cumplir WCAG 2.1 AA) e interacciones hover con resplandor cian sutil (`--rg-accent-cyan`).

---

## **2. Vista de Administración de Empresas — Multi-Tenant (vue3/src/views/admin/TenantsManagementView.vue)**

- **Ruta:** `/admin/tenants`
- **Acceso exclusivo:** Rol `SUPERADMIN_GLOBAL`.
- **Funciones:**
  - Tabla de empresas registradas (slug, name, tax_id, status, barra de uso de cuota de routers activos / `max_routers_quota`, barra de cuota de usuarios y `default_safemode_seconds`).
  - Modal de creación de nueva empresa que crea atómicamente el Tenant y su primer usuario `TENANT_ADMIN`.
  - Botón rápido para poner una empresa en estado `SUSPENDED` (lo que bloquea nuevos logins y revoca sesiones activas de ese Tenant).

## **3. Vista de Gestión de Usuarios y Matriz de Asignación de Equipos (vue3/src/views/admin/UsersAndPermissionsView.vue)**

- **Ruta:** `/admin/users`
- **Roles con permiso de escritura:** `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` (`SUPERVISOR` y `AUDITOR` tienen vista de solo lectura).

### **3.1 Listado y Creación de Usuarios con los 11 Roles**

- Tabla filtrable por rol (`TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3`, `SUPPORT_L2`, `SUPPORT_L1`, `FIELD_TECH`, `INVENTORY_MANAGER`, `AUDITOR`, `NOC_MONITOR`, `SERVICE_ACCOUNT`), estado (Activo / Bloqueado) y estado de 2FA.
- Al crear o editar un usuario de tipo `SERVICE_ACCOUNT`, exige configurar al menos una subred o IP en el campo `allowed_cidr_list` (ej. `10.10.50.10/32`).
- Incluye botón **"Reiniciar 2FA"** protegido por el modal `RgStepUp2FAModal.vue`.

### **3.2 Cajón / Modal de Matriz de Asignación de MikroTiks por Usuario (UserRouterMatrixModal.vue)**

Cumple el requerimiento de que **el administrador asigne a cada usuario exactamente qué equipos y qué permisos tendrá**:

- Selector maestro: Switch **"Acceso a todos los MikroTiks del Tenant (`has_all_routers_access`)"**.
- Cuando el switch está desactivado (comportamiento estándar para `SUPPORT_L1`, `SUPPORT_L2`, `FIELD_TECH` y `SERVICE_ACCOUNT`), despliega una tabla interactiva con buscador por nombre/rol/etiqueta donde el Administrador marca para cada MikroTik:
  - `[x]` **Asignado / Lectura (`can_read`)**
  - `[x]` **Escritura Capa 1 (`can_write_layer1`)**
  - `[ ]` **Escritura Capa 2 Dinámica (`can_write_layer2`)**
  - `[x]` **Ejecutar Diagnósticos (`can_execute_diagnostics`)**
  - `[x]` **Disparar Backup Manual (`can_trigger_backup`)**
  - `[ ]` **Reiniciar Equipo (`can_reboot`)**
  - `[ ]` **Omitir Maker-Checker en este router (`bypass_maker_checker`)**
- Incluye botones de selección rápida por lote: *"Asignar todos los routers con etiqueta zona-norte"* o *"Asignar todos los routers con rol TOWER_AP"*.
- Al guardar, invoca `PUT /api/v1/users/{user_id}/router-permissions` con `Idempotency-Key`.

### **3.3 Pestaña de Solicitudes Pendientes (Maker-Checker de Cuentas) y Switch Global**

- **Switch de Registro en la Barra Superior:**
  - Control tipo toggle táctil *"Permitir Nuevos Registros"*, visible exclusivamente para el `SUPERADMIN_GLOBAL`.
  - Al alternar, invoca `POST /api/v1/users/registration-toggle` y actualiza la bandera en KeyDB en tiempo real con feedback visual táctico.
- **Pestaña "Solicitudes Pendientes" en la Vista de Usuarios:**
  - Muestra un badge con el conteo de operadores en espera de aprobación.
  - Cada fila presenta los datos del solicitante (nombre, usuario, correo, fecha de solicitud).
  - **Selector de Rol y Acceso:** Menú desplegable táctil para elegir el rol operativo que se otorgará (ej. `SUPPORT_L1`, `SUPPORT_L2`, `OPERATOR_RW`).
  - **Acción "Aprobar" (Verde):** Ejecuta `PUT /api/v1/users/{user_id}/approve`, activando la cuenta y registrando el evento de auditoría WORM.
  - **Acción "Rechazar" (Rojo):** Ejecuta `DELETE /api/v1/users/{user_id}/reject` con confirmación, eliminando o revocando la solicitud de manera limpia y sin corromper la inmutabilidad de la base de datos.

### **3.4 Modal Interactivo de Emisión de Tokens MCP (RgMcpTokenModal.vue)**

Permite a los administradores generar y entregar Bearer Tokens JWT de larga duración para agentes de IA (Claude Desktop, Hermes Agent, scripts de automatización) sin depender exclusivamente del terminal:

- **Activación:** Botón táctico **`⚡ Token MCP`** en cada fila de usuario autorizado (`SERVICE_ACCOUNT`, `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`).
- **Selector de Vigencia:** Presets de 30, 90, 180, 365 (1 año) y 730 (2 años) días.
- **Validaciones Visuales:** Alerta de seguridad si la cuenta de servicio no tiene segmentos de red configurados en su lista blanca CIDR.
- **Emisión Segura:** Invoca `POST /api/v1/users/{user_id}/mcp-token` con clave de idempotencia y registra la sesión directamente en KeyDB.
- **Entrega Segura y Snippets de 1-Clic:**
  - Campo de solo lectura para copiar el token JWT con botón interactivo.
  - Bloque preformateado para `claude_desktop_config.json` con comando `npx -y @modelcontextprotocol/server-fetch`.
  - Variables de entorno para agentes autónomos (Hermes Agent / `config.yaml`).
  - Advertencia de que el token es mostrado por única vez.

## **4. Panel de Control de Sesiones Activas y *Kill-Switch* en Tiempo Real (vue3/src/views/admin/ActiveSessionsKillSwitchView.vue)**

- **Ruta:** `/admin/active-sessions`
- **Roles Permitidos:** `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR` (y `AUDITOR` en modo lectura).
- **Actualización en Vivo:** Consulta `GET /api/v1/sessions/active` y se mantiene sincronizada mediante el WebSocket `/ws/v1/tenant/events`.
- **Filtros Tácticos:** Pestañas superiores para segmentar la visualización:
  - **Todas:** Listado unificado con indicador numérico.
  - **Operadores Humanos:** Filtra usuarios técnicos y administradores interactivos.
  - **Agentes IA MCP:** Filtra exclusivamente sesiones de cuentas de servicio y daemons MCP.

### **4.1 Columnas de la Tabla de Sesiones en Vivo**

1. **Técnico / Agente IA:** Nombre completo, @username, badge de color con su Rol y distintivo especial `[🤖 MCP SERVICE ACCOUNT]` para agentes inteligentes.
2. **Autoría y Linaje:** Badge `Por: @usuario` indicando qué operador emitió el token (o `CLI (Terminal)` si provino del script de mantenimiento).
3. **Origen y Seguridad CIDR:** Dirección IP (`ip_address`), segmentos de red permitidos (`allowed_cidr_list`) e icono de cliente parseado del `user_agent` (ej. `RoSGrid-MCP-Daemon/1.0`).
4. **Actividad y Vigencia:** Última actividad registrada, tiempo transcurrido y fecha de expiración de la sesión en KeyDB.
5. **Acciones de Contención Inmediata (*Kill-Switch*):**
   - Botón rojo **"Revocar Sesión"** (`DELETE /api/v1/sessions/{session_id}`): Destruye la sesión en KeyDB y expulsa al técnico o agente de inmediato.
   - Botón crítico **"Expulsar de Todos los Dispositivos y Bloquear Cuenta"** (`DELETE /api/v1/sessions/user/{user_id}/all`).
