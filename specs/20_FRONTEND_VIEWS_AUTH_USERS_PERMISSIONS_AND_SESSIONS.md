# 20 — VISTAS FRONTEND: LOGIN MULTI-TENANT + 2FA, GESTIÓN DE USUARIOS, MATRIZ DE EQUIPOS Y KILL-SWITCH EN VIVO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las vistas de autenticación, administración de organizaciones, gestión de usuarios, matriz visual de asignación de MikroTiks por técnico y el panel de control de sesiones activas en tiempo real (*Kill-Switch*) dentro de vue3/src/views/auth/ y vue3/src/views/admin/.




## **1. Vista de Inicio de Sesión Multi-Tenant + 2FA (vue3/src/views/auth/LoginView.vue)**

Ruta: /login (Una de las 3 rutas auditadas directamente por @axe-core/playwright y Snapshot Testing en accessibility.e2e.ts).

### **1.1 Etapa 1: Identificación Multi-Tenant y Credenciales Primarias**

El formulario presenta 3 campos obligatorios con etiquetas \<label\> explícitas y atributos autocomplete:


1. **Identificador de Empresa (input\#tenant-slug):**

   - Placeholder: ej. isp-norte. Normaliza automáticamente a minúsculas y guiones.

2. **Correo Electrónico o Usuario (input\#login-email):**

   - autocomplete="username".

3. **Contraseña (input\#login-password):**

   - type="password", autocomplete="current-password", con botón accesible (aria-label="Mostrar u ocultar contraseña") para alternar visibilidad.

4. **Banner de Motivo de Redirección:**

   - Si la URL contiene ?reason=session\_revoked, muestra una alerta accesible (role="alert") informando: *"Tu sesión fue cerrada por un Administrador o Supervisor"*.

### **1.2 Etapa 2A: Enrolamiento Inicial de 2FA TOTP (Si next\_step === 'ENROLL\_2FA\_REQUIRED')**

- Renderiza en un \<canvas\> local (usando la librería qrcode sin llamadas externas a internet) el código QR del totp\_provisioning\_uri.

- Muestra la clave secreta en formato texto monoespaciado por si el técnico desea ingresarla manualmente en Google Authenticator / Authy / FreeOTP.

- Solicita ingresar el primer código de 6 dígitos generado por su aplicación para confirmar el enrolamiento y muestra los códigos de recuperación de emergencia por única vez con botón de descarga .txt.

### **1.3 Etapa 2B: Verificación de Código 2FA TOTP (next\_step === 'VERIFY\_2FA\_TOTP')**

- Presenta un campo numérico de 6 dígitos (inputmode="numeric", pattern="\[0-9\]\{6\}", autocomplete="one-time-code") con cuenta regresiva del tiempo restante del challenge\_id (180 segundos).

- Al completarse el 6.º dígito, dispara POST /api/v1/auth/2fa/verify y redirige al Dashboard (o al Wallboard NOC si el rol es NOC\_MONITOR).




## **2. Vista de Administración de Empresas — Multi-Tenant (vue3/src/views/admin/TenantsManagementView.vue)**

- **Ruta:** /admin/tenants

- **Acceso exclusivo:** Rol SUPERADMIN\_GLOBAL.

- **Funciones:**

  - Tabla de empresas registradas (slug, name, tax\_id, status, barra de uso de cuota de routers activos / max\_routers\_quota, barra de cuota de usuarios y default\_safemode\_seconds).

  - Modal de creación de nueva empresa que crea atómicamente el Tenant y su primer usuario TENANT\_ADMIN.

  - Botón rápido para poner una empresa en estado SUSPENDED (lo que bloquea nuevos logins y revoca sesiones activas de ese Tenant).




## **3. Vista de Gestión de Usuarios y Matriz de Asignación de Equipos (vue3/src/views/admin/UsersAndPermissionsView.vue)**

- **Ruta:** /admin/users

- **Roles con permiso de escritura:** SUPERADMIN\_GLOBAL y TENANT\_ADMIN (SUPERVISOR y AUDITOR tienen vista de solo lectura).

### **3.1 Listado y Creación de Usuarios con los 11 Roles**

- Tabla filtrable por rol (TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2, SUPPORT\_L1, FIELD\_TECH, INVENTORY\_MANAGER, AUDITOR, NOC\_MONITOR, SERVICE\_ACCOUNT), estado (Activo / Bloqueado) y estado de 2FA.

- Al crear o editar un usuario de tipo SERVICE\_ACCOUNT, exige configurar al menos una subred o IP en el campo allowed\_cidr\_list (ej. 10.10.50.10/32).

- Incluye botón **"Reiniciar 2FA"** protegido por el modal RgStepUp2FAModal.vue.

### **3.2 Cajón / Modal de Matriz de Asignación de MikroTiks por Usuario (UserRouterMatrixModal.vue)**

Cumple el requerimiento de que **el administrador asigne a cada usuario exactamente qué equipos y qué permisos tendrá**:


- Selector maestro: Switch **"Acceso a todos los MikroTiks del Tenant (has\_all\_routers\_access)"**.

- Cuando el switch está desactivado (comportamiento estándar para SUPPORT\_L1, SUPPORT\_L2, FIELD\_TECH y SERVICE\_ACCOUNT), despliega una tabla interactiva con buscador por nombre/rol/etiqueta donde el Administrador marca para cada MikroTik:

  - \[x\] **Asignado / Lectura (can\_read)**

  - \[x\] **Escritura Capa 1 (can\_write\_layer1)**

  - \[ \] **Escritura Capa 2 Dinámica (can\_write\_layer2)**

  - \[x\] **Ejecutar Diagnósticos (can\_execute\_diagnostics)**

  - \[x\] **Disparar Backup Manual (can\_trigger\_backup)**

  - \[ \] **Reiniciar Equipo (can\_reboot)**

  - \[ \] **Omitir Maker-Checker en este router (bypass\_maker\_checker)**

- Incluye botones de selección rápida por lote: *"Asignar todos los routers con etiqueta zona-norte"* o *"Asignar todos los routers con rol TOWER\_AP"*.

- Al guardar, invoca PUT /api/v1/users/\{user\_id\}/router-permissions con Idempotency-Key.




## **4. Panel de Control de Sesiones Activas y *Kill-Switch* en Tiempo Real (vue3/src/views/admin/ActiveSessionsKillSwitchView.vue)**

- **Ruta:** /admin/active-sessions

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR (y AUDITOR en modo lectura).

- **Actualización en Vivo:** Consulta GET /api/v1/sessions/active y se mantiene sincronizada mediante el WebSocket /ws/v1/tenant/events.

### **4.1 Columnas de la Tabla de Sesiones en Vivo**

1. **Técnico / Usuario:** Nombre completo, @username y badge de color con su Rol.

2. **Origen y Dispositivo:** Dirección IP (ip\_address) e icono de sistema operativo/navegador parseado del user\_agent (PC Linux/Windows, Tablet o Móvil).

3. **Actividad Actual en Vivo:**

   - Muestra el nombre del MikroTik que el técnico tiene abierto en ese instante (current\_router\_name con enlace directo) y el submenú exacto (current\_view\_path, ej. Firewall \> Filter Rules).

4. **Tiempo de Sesión y Última Acción:** Hora de inicio y hace cuántos segundos interactuó por última vez.

5. **Acciones de Contención Inmediata (*Kill-Switch*):**

   - Botón rojo **"Revocar Sesión"** (DELETE /api/v1/sessions/\{session\_id\}): Solicita motivo breve, destruye la sesión en Redis y cierra en el acto el WebSocket y la pantalla del técnico.

   - Botón crítico **"Expulsar de Todos los Dispositivos y Bloquear Cuenta"** (DELETE /api/v1/sessions/user/\{user\_id\}/all).
