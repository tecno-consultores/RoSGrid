# 📋 Plan Maestro de Pruebas Manuales y Aceptación de Usuario (UAT 11X) — RoSGrid

**Licencia:** GPL-3.0-only  
**Copyright:** (C) 2026 RoSGrid Contributors  
**Audiencia:** Ingenieros de Red, Administradores de Sistemas, Auditores de Seguridad y Operadores NOC  
**Objetivo:** Certificar la experiencia humana de usuario, la estabilidad operativa de extremo a extremo (E2E) y la interacción real con equipos MikroTik RouterOS v7+ antes de cada pase a producción.

---

## 1. Alcance y Gobernanza de las Pruebas Manuales

Las pruebas automatizadas de RoSGrid (cobertura unitaria `>= 95%`, mutación, accesibilidad WCAG 2.1 AA y contratos OpenAPI) garantizan la solidez lógica del código. El presente **Plan Maestro de Pruebas de Aceptación de Usuario (UAT)** complementa dicha base mediante la validación manual de:

1. **Ergonomía Táctica NOC:** Legibilidad, alta densidad visual, respuesta del Canvas 2D en telemetría en tiempo real y navegación sin recargas.
2. **Resiliencia Operativa en Vivo:** Verificación visual del Safe Mode (60s), prevención de auto-desconexión y reversión de cambios en enlace físico.
3. **Flujos de Gobernanza y Segregación:** Mecanismo Maker-Checker con aprobación humana, rotación de claves y Step-Up Auth (30s) en Bóveda.
4. **Interacción con Hardware y Firmware Real:** Validación sobre MikroTik RouterOS v7.12+ (Cloud Hosted Router CHR o RouterBOARD físico).

---

## 2. Entornos y Requisitos Previos

### A. Topología de Prueba Recomendada

- **Servidor RoSGrid:** Instancia local levantada con `./probar-prod-local.sh --keep-alive` o stack en servidor de laboratorio (Docker Compose).
- **Equipo MikroTik de Prueba:**
  - Instancia MikroTik CHR v7 en Proxmox/VirtualBox/GNS3 o RouterBOARD físico (hEX, RB4011, etc.).
  - REST API activa en puerto HTTPS 443 o HTTP 80 (`/ip/service/enable rest`).
  - Usuario local con permisos REST API (`group=full` o permisos específicos).
- **Navegador del Operador:** Google Chrome, Firefox o Edge en modo incógnito o limpio.

---

## 3. Matriz de Casos de Prueba Manuales

### Módulo 1: Bootstrap Inicial sobre Base de Datos Virgen

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-01** | Autodetección de DB virgen | Contenedores recién creados sin usuarios | 1. Acceder a `http://localhost:8085/`. 2. Observar la pantalla inicial. | La interfaz detecta `is_bootstrapped=false` y muestra el Asistente de Configuración Inicial (*Bootstrap Superadmin*). |
| **UAT-02** | Creación de Organización y Superadmin | Pantalla de Bootstrap activa | 1. Ingresar Organización: `ISP Central`. 2. Slug: `isp-central`. 3. Admin: `admin_root`. 4. Email: `root@isp.net`. 5. Contraseña: `MasterRoot2026!`. 6. Presionar *Inicializar Sistema*. | Modal de éxito indicando que la organización y el Superadmin fueron creados. Redirección automática a la vista de login. |
| **UAT-03** | Bloqueo de Re-Bootstrap | Sistema ya inicializado | 1. Intentar acceder a `/bootstrap` o enviar `POST /api/v1/auth/bootstrap`. | El sistema responde HTTP 409 Conflict o redirige a `/login`, impidiendo sobreescribir la configuración. |

---

### Módulo 2: Autenticación Zero-Trust, 2FA TOTP y Bloqueo

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-04** | Enrolamiento Obligatorio 2FA TOTP | Usuario recién creado sin 2FA | 1. Ingresar slug, email y contraseña. 2. Presionar *Iniciar Sesión*. | Aparece pantalla de enrolamiento obligatorio con código QR y URI `otpauth://`. No se permite acceso al NOC sin enrolar. |
| **UAT-05** | Confirmación de Token TOTP | QR escaneado en app autenticadora | 1. Ingresar código de 6 dígitos de la app. 2. Presionar *Verificar*. | Acceso concedido al Dashboard NOC. Se emite cookie `__Host-rg_at` (`HttpOnly; Secure; SameSite=Strict`). |
| **UAT-06** | Bloqueo por Fuerza Bruta | Usuario registrado | 1. Intentar login con contraseña incorrecta 5 veces consecutivas. | Al 5to intento fallido, el sistema bloquea la cuenta por 15 minutos e informa: *"Cuenta bloqueada temporalmente por seguridad"*. |

---

### Módulo 3: Inventario de Routers, Pinning SSL TOFU y Bóveda

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-07** | Alta Individual con Pinning TOFU | Router MikroTik accesible por red | 1. Ir a *Inventario* -> *Nuevo Router*. 2. Ingresar Nombre, IP, Puerto REST, Usuario y Clave. 3. Guardar. | Se abre modal TOFU mostrando la huella SHA-256 del certificado SSL autofirmado del router. Al confirmar, el router pasa a estado *Activo*. |
| **UAT-07B** | Redescubrimiento Dinámico TOFU | Router registrado en Inventario | 1. En la fila del router, hacer clic en el botón *TOFU / Redescubrir*. 2. Observar la notificación toast y actualización de datos. | Se invoca `POST /api/v1/inventory/routers/{id}/discover`. El sistema consulta al MikroTik real, extrae versión de RouterOS, arquitectura de CPU, memoria y huella SSL, actualizando la ficha en vivo sin recargar. |
| **UAT-08** | Importación Masiva CSV (Dry-Run + Commit) | Archivo CSV con 3 routers | 1. Abrir Asistente CSV. 2. Cargar archivo. 3. Presionar *Validar (Dry-Run)*. 4. Revisar tabla de validación. 5. Presionar *Importar*. | Paso 1 muestra resumen sin guardar en DB. Paso 2 confirma los registros en DB y muestra los 3 routers en la grilla. |
| **UAT-09** | Revelación de Clave (*Step-Up Auth* 30s) | Router en inventario con clave cifrada | 1. Ir a la Bóveda del router. 2. Clic en icono del ojo para ver clave. 3. Ingresar código 2FA TOTP en el modal emergente. | La clave se descifra en pantalla con una barra de progreso regresiva de 30 segundos. Al expirar, se borra de la memoria y se enmascara nuevamente. |
| **UAT-10** | Rotación Automática de Claves API | Router conectado | 1. Presionar *Rotar Clave API*. 2. Confirmar acción. | RoSGrid genera clave de 32 bytes, actualiza el usuario en MikroTik vía REST, cifra la nueva clave en DB con AES-256-GCM y registra auditoría. |

---

### Módulo 4: Consola WebFig Táctica y Telemetría NOC

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-11** | Navegación de Interfaces y SFP DDM | Router con interfaces activas | 1. Seleccionar router. 2. Abrir pestaña *Interfaces*. 3. Expandir módulo SFP DDM. | Se muestran interfaces físicas, VLANs, estado de enlace, RX/TX power y temperatura en tiempo real sin recargar página. |
| **UAT-12** | Telemetría en RAM (Canvas 2D) | Gráfica de tráfico abierta | 1. Observar la gráfica WinBox en vivo. 2. Cambiar a otro router en el menú lateral. | Gráfica renderiza fluidamente a 60 FPS mediante WebSocket. Al cambiar de router, el RingBuffer de memoria se limpia inmediatamente. |
| **UAT-13** | Inspección de Tablas de Firewall | Pestaña *Firewall* seleccionada | 1. Filtrar reglas por cadena (`input`, `forward`). 2. Modificar comentarios o estado habilitado/deshabilitado. | Cambio de estado reflejado con insignias tácticas `[X]` (Disabled) y `[I]` (Invalid) idénticas a WinBox. |

---

### Módulo 5: Protocolo Safe Mode y Resiliencia Anti-Bloqueo

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-14** | Activación del Banner Safe Mode | Conexión activa a router | 1. Activar el toggle *Safe Mode* en la barra superior. 2. Aplicar un cambio de IP o regla de firewall. | Aparece el banner cian táctico con el cronómetro regresivo de 60 segundos (*Dead Man's Switch*). |
| **UAT-15** | Reversión Automática por Corte de Enlace | Safe Mode activo | 1. Modificar regla de firewall que corte la IP de RoSGrid. 2. Esperar 60 segundos sin confirmar. | El scheduler del MikroTik detecta la pérdida de confirmación y revierte automáticamente la configuración, restaurando el acceso. |
| **UAT-16** | Confirmación Manual de Cambio | Safe Mode activo con cambio válido | 1. Aplicar cambio válido. 2. Presionar *Confirmar Cambios* en el banner. | El timer se detiene, el scheduler se elimina del router y el cambio queda consolidado de manera permanente. |

---

### Módulo 6: Gobernanza Maker-Checker

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-17** | Intercepción de Acción Crítica (HTTP 202) | Usuario con rol `OPERATOR_RW` | 1. Intentar reiniciar router o borrar regla de firewall crítica. | La acción no se ejecuta de inmediato; el sistema responde HTTP 202 Accepted y genera solicitud en bandeja de aprobaciones. |
| **UAT-18** | Aprobación con Diff Visual | Usuario con rol `TENANT_ADMIN` | 1. Abrir *Bandeja de Aprobaciones*. 2. Inspeccionar solicitud pendiente con el visor Diff. 3. Presionar *Aprobar*. | El cambio se aplica en el MikroTik, el operador solicitante recibe notificación y se genera registro inmutable en `audit_logs`. |
| **UAT-19** | Rechazo con Justificación | Solicitud pendiente en bandeja | 1. Presionar *Rechazar* e ingresar motivo: *"IP en conflicto con subred corporativa"*. | La solicitud pasa a estado *Rechazada*, no se aplica ningún cambio en el router y se notifica al operador. |

---

### Módulo 7: Backups Automatizados y Comparador Diff Git

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-20** | Generación de Backup Manual `.rsc` | Router en línea | 1. Ir a *Backups* -> *Generar Backup Ahora*. 2. Seleccionar tipo Script Export (`.rsc`). | Se genera el backup, se calcula su hash SHA-256 y se almacena en el volumen aislado `/var/lib/rosgrid/backups/`. |
| **UAT-21** | Comparación de Versiones (Diff Estilo Git) | Al menos 2 backups del mismo router | 1. Seleccionar dos versiones consecutivas. 2. Presionar *Comparar Versiones*. | El visor visual muestra adiciones en verde (`+`) y eliminaciones en rojo (`-`), permitiendo auditoría forense precisa. |

---

### Módulo 8: Kill-Switch y Revocación de Sesiones

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-22** | Expulsión Forzosa en Tiempo Real | Operador con sesión abierta en otra pestaña | 1. Superadmin ingresa a *Gestión de Usuarios*. 2. Clic en *Revocar Sesiones* del operador. | En la pestaña del operador, el WebSocket recibe `SESSION_KILLED`, se borran las cookies y el navegador redirige instantáneamente al login. |

---

### Módulo 9: Integración de Agentes IA vía MCP

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-23** | Generación de Token MCP para Agente | Script `generar_token_mcp.py` | 1. Ejecutar script especificando usuario y organización. 2. Obtener token Bearer JWT. | Se emite token de 365 días con rol `SERVICE_ACCOUNT` y claims restringidos. |
| **UAT-24** | Ejecución de Diagnóstico MCP | Agente IA o cliente HTTP | 1. Enviar payload JSON-RPC invocando `rosgrid_get_router_health`. | La API responde el estado del router con latencia mínima y sin bypass de políticas de seguridad. |
| **UAT-25** | Intercepción MCP en Maker-Checker | Agente IA solicita cambio mutable | 1. Agente invoca `rosgrid_propose_network_change`. | La operación queda retenida en bandeja Maker-Checker; no se ejecuta hasta que un humano la autorice en la UI. |

---

### Módulo 10: Auto-Registro de Operadores y Aprobación Maker-Checker

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-26** | Solicitud de Auto-Registro Web | Sistema inicializado y toggle activo | 1. En la pantalla de login, hacer clic en *"Solicitar acceso de operador"*. 2. Completar formulario con nombre, username, email y contraseña. 3. Enviar solicitud. | Mensaje de éxito indicando que la solicitud está en estado `PENDING_APPROVAL`. Intento de login posterior arroja HTTP 403 (*"Cuenta pendiente de aprobación"*). |
| **UAT-27** | Aprobación de Cuenta por Superadmin | Solicitud pendiente en el sistema | 1. Superadmin inicia sesión e ingresa a *Usuarios y Permisos*. 2. Localiza al usuario en la pestaña *Solicitudes Pendientes*. 3. Asigna rol (ej. `OPERATOR_RW`) y hace clic en *Aprobar*. | El usuario pasa a estado activo, se habilita el acceso y se audita el evento con inmutabilidad WORM. |
| **UAT-28** | Rechazo y Toggle de Registro | Solicitud pendiente | 1. En *Solicitudes Pendientes*, hacer clic en *Rechazar*. 2. En la barra superior, desactivar el switch *Permitir Nuevos Registros*. | La solicitud se descarta de forma segura. El formulario de login oculta el enlace de registro y cualquier intento directo vía API responde HTTP 403 (*"El auto-registro está deshabilitado"*). |

---

### Módulo 11: Centro de Mando Táctico "Mission Control" y Wallboard NOC

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-29** | Tablero Táctico Mission Control | Sesión activa en RoSGrid | 1. Navegar a la raíz `/` (o hacer clic en el isotipo de RoSGrid). 2. En la franja superior de KPIs, observar las 4 tarjetas tácticas: *Flota MikroTik* (Total, Online, Offline), *Disponibilidad Flota* (%), *Alertas NOC Activas* (en curso / despejado), y *Maker-Checker* (pendientes). 3. En la sección inferior, revisar la agrupación de equipos por "Rol de Red". | Los relojes (Local y UTC en vivo) se actualizan segundo a segundo sin parpadeo. Los KPIs reflejan el estado del parque de routers y el WebSocket muestra `NOC EN VIVO`. |
| **UAT-30** | Wallboard NOC y Apertura Directa de WebFig | Al menos un router en Inventario | 1. Ingresar a *Wallboard NOC* (`/noc-wallboard`). 2. Observar la franja superior de KPIs (*TOTAL*, *ONLINE*, *CARGA ALTA*, *OFFLINE*, *MANTENIMIENTO*, *ALERTA TOFU*). 3. Hacer clic sobre el pin de un router en el mapa OSM. 4. Probar clic en *"Abrir WebFig"* en el popup y en la barra flotante HUD inferior. | Ambos botones redirigen inmediatamente a la consola operativa en vivo (`/routers/:id/webfig/live`) del router seleccionado. |
| **UAT-31** | Modo TV Pantalla Completa | Wallboard abierto | 1. Presionar el botón *"🖥️ Modo TV"*. 2. Observar comportamiento. 3. Presionar *"🗗 Salir TV"* o tecla `Esc`. | La pantalla entra a modo inmersivo sin barras de navegación del navegador, optimizado para salas de monitoreo 24/7. |

---

### Módulo 12: Gestor de Plantillas de Configuración "Golden Config" & Acciones Masivas

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-32** | Creación y Edición de Plantillas Golden Config | Rol `SUPERADMIN` o `TENANT_ADMIN` | 1. Ir a *Acciones Masivas* (`/bulk-ops`). 2. En el *Paso 1*, seleccionar al menos un router y hacer clic en *"Siguiente: Configurar Plantilla ➔"*. 3. En el *Paso 2*, hacer clic en el botón superior **`+ Nueva Plantilla`**. 4. Ingresar Nombre (ej. `Hardening DNS & NTP`), Categoría, Script Jinja2 (`/ip dns set allow-remote-requests=no`) y definir variables. 5. Guardar. | La plantilla se valida sintácticamente, se almacena en base de datos y aparece seleccionable en la cuadrícula de plantillas. |
| **UAT-33** | Despliegue Masivo con Simulación Dry-Run | Plantilla seleccionada en Paso 2 | 1. Con la plantilla seleccionada en el Paso 2, rellenar los valores de las variables. 2. Hacer clic en *"Siguiente: Simulación Dry-Run ➔"*. 3. En el *Paso 3*, inspeccionar la previsualización del script renderizado. 4. Clic en *"Siguiente: Confirmar Ejecución ➔"* y luego en *"🚀 Desplegar a la Flota (Safe Mode)"*. | Se inicia la tarea masiva, los comandos se aplican bajo Safe Mode (60s) en cada router y se registra la auditoría forense WORM. |

---

### Módulo 13: Roles de Red Personalizados y Auto-Registro en CSV

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-34** | Creación de Rol de Infraestructura | Usuario administrador en *Inventario* | 1. En la cabecera de *Inventario*, hacer clic en el botón **`🏷️ Roles de Red`**. 2. En el modal, ingresar nombre del rol: `CORE_BGP_MPLS` y su descripción. 3. Guardar. | El nuevo rol aparece de inmediato en el filtro desplegable de roles de inventario y en los formularios de edición de routers. |
| **UAT-35** | Auto-Registro Dinámico desde Archivo CSV | Archivo CSV con columna `network_role` desconocida (ej. `TOWER_SECTORIAL`) | 1. En *Inventario*, abrir *"📂 Importar CSV"*. 2. Cargar CSV que contenga un rol no registrado previamente. 3. Completar validación y confirmación. | RoSGrid detecta el rol nuevo, lo registra automáticamente en la tabla `tenant_custom_roles` de PostgreSQL y completa la importación sin errores. |

---

### Módulo 14: Comparador Diff Avanzado y Descarga Segura de Respaldos

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-36** | Selección Interactiva de Tarjetas en Diff | Al menos 2 respaldos en los últimos 30 días | 1. Ir a *Respaldos y Diff* (`/backups`). 2. Hacer clic directamente en una tarjeta para seleccionarla como `[🔵 BASE]`. 3. Hacer clic en el botón `Objetivo (Der)` de otra tarjeta. | Las tarjetas se resaltan con bordes de alto contraste e insignias `[🔵 BASE]` y `[🟢 OBJETIVO]`. El comparador inferior actualiza el diff side-by-side de inmediato. |
| **UAT-37** | Descarga Segura de Script `.rsc` vs `.backup` | Router con respaldos generados | 1. Hacer clic en el icono del script (`📜`): debe descargar un archivo con nombre `rosgrid-backup-<routerId>-<backupId>.rsc`. 2. Observar el botón del binario (`💾`): si el punto de restauración es una exportación de configuración en texto plano, el botón se muestra inhabilitado con tooltip indicativo; si existe una instantánea binaria nativa en disco, permite su descarga binaria directa. | El archivo `.rsc` se descarga con su extensión correcta y puede abrirse con cualquier editor de texto o terminal. |
| **UAT-37B** | Generación de Nuevo Respaldo y Deduplicación | Router en línea | 1. Presionar el botón *"➕ Nuevo Respaldo"*. 2. Si la configuración del router no ha cambiado desde el último respaldo, el sistema emite el aviso informativo: *"Configuración idéntica al último respaldo. Se aplicó deduplicación inteligente"*. 3. Modificar un comentario o valor en el router y presionar *"➕ Nuevo Respaldo"*. | Al detectar un cambio real en el hash SHA-256, se crea de inmediato un nuevo punto de restauración en la lista con su contador de líneas añadidas/eliminadas. |

---

### Módulo 15: Administración Integral de Usuarios, Roles RBAC y Bóveda

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-38** | Creación de Nuevo Usuario Operador | Sesión como `SUPERADMIN` o `TENANT_ADMIN` | 1. Ir a *Usuarios y Permisos* (`/users`). 2. Clic en *"Crear Usuario"*. 3. Ingresar Nombre, Username, Email, Rol (ej. `SUPPORT_L2`) y Contraseña inicial. 4. Guardar. | El usuario aparece en la lista de usuarios activos con su insignia de rol correspondiente y se genera registro de auditoría. |
| **UAT-39** | Asignación Granular de Routers (Matriz de Acceso) | Usuario creado con rol operativo | 1. En la fila del usuario, hacer clic en el botón *"Asignar Routers"*. 2. En el modal, seleccionar 1 o 2 routers específicos y guardar. | El operador solo podrá visualizar y operar los routers asignados explícitamente en el inventario y WebFig. |
| **UAT-40** | Cambio de Contraseña de Operador | Usuario seleccionado | 1. En la fila del usuario, clic en *"Cambiar Clave"*. 2. Ingresar nueva contraseña segura y confirmar. | La contraseña se hashea con Argon2id en base de datos; la sesión anterior se invalida forzosamente. |
| **UAT-41** | Eliminación / Desactivación de Usuario | Usuario no-superadmin | 1. En la fila del usuario, hacer clic en *"Eliminar"*. 2. Confirmar en el diálogo emergente. | El usuario se elimina de la base de datos o se revoca su estado; si tenía sesión activa, el WebSocket dispara el kill-switch cerrándola de inmediato. |

---

### Módulo 16: Gestión Multi-Tenant y Aislamiento RLS

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-42** | Creación de Organización (Tenant) | Rol `SUPERADMIN_GLOBAL` | 1. Ir a *Organizaciones / Tenants* (`/tenants`). 2. Clic en *"Nueva Organización"*. 3. Ingresar Nombre (ej. `Sucursal Maracaibo`), Slug (`maracaibo`), cuota de routers y usuarios. 4. Guardar. | El nuevo inquilino se crea con su propio esquema RLS en PostgreSQL 17. |
| **UAT-43** | Aislamiento Estricto de Datos entre Tenants | Dos tenants creados con routers propios | 1. Iniciar sesión con usuario del Tenant A. 2. Verificar que no aparezcan routers ni auditoría del Tenant B en ninguna pantalla ni petición API. | Aislamiento total: PostgreSQL aplica `FORCE ROW LEVEL SECURITY` mediante `app.current_tenant_id` garantizando fuga de datos cero. |

---

### Módulo 17: Ventanas de Mantenimiento y Supresión de Alertas

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-44** | Programación de Ventana de Mantenimiento | Router en producción | 1. Ir a *Ventanas de Mantenimiento* (`/maintenance`). 2. Clic en *"Programar Ventana"*. 3. Seleccionar router, fecha/hora inicio y fin. 4. Guardar. | El router muestra la insignia táctica *"MANTENIMIENTO"* en Wallboard e Inventario, y las alertas de desconexión se silencian temporalmente. |

---

### Módulo 18: Herramientas Operativas WebFig en Vivo

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-45** | Utilidades de Diagnóstico en Vivo (Ping / Traceroute) | Conexión activa a router en WebFig | 1. En la consola WebFig del router, ir a la pestaña *Tools / Diagnóstico*. 2. Ingresar IP destino (ej. `8.8.8.8`) y presionar *Iniciar Ping*. | La terminal en vivo muestra los paquetes ICMP, RTT y pérdida de paquetes en tiempo real sin recargar página. |
| **UAT-46** | Reordenamiento de Reglas de Firewall (Drag & Drop / Teclado) | Pestaña *Firewall* activa | 1. Arrastrar una regla de firewall a una nueva posición o seleccionarla y presionar `Alt + Flecha Arriba`. | La posición se actualiza visualmente y se envía la mutación `/ip/firewall/filter/move` al router bajo Safe Mode (60s). |

---

### Módulo 19: Feature Flags y Gobernanza Modular por Tenant

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-47** | Conmutación de Módulo ISP (ON/OFF) | Rol `SUPERADMIN_GLOBAL` | 1. Ir a `/tenants` y abrir pestaña *"Módulos & Capacidades"*. 2. Desactivar switch *"Módulo ISP & Operaciones de Campo"*. 3. Guardar. 4. Observar la barra lateral y paleta `Ctrl+K`. | Desaparecen inmediatamente las opciones *"Técnico de Campo"* y *"Mapa de Abonados"*. La UI se simplifica 100% a modo corporativo. |
| **UAT-48** | Protección de Rutas y API ante Módulo Desactivado | Tenant con `isp_module_enabled=false` | 1. Intentar acceder por URL a `/field-ops`. 2. Enviar petición API `POST /api/v1/network-services/1/isolate`. | El router frontend redirige al dashboard con notificación toast. La API responde HTTP 403 Forbidden con `{ "code": "FEATURE_MODULE_DISABLED" }`. |
| **UAT-49** | Activación Selectiva de BGP Looking Glass | Red con ASN propio | 1. En el panel de Feature Flags, activar switch *"BGP Looking Glass"*. 2. Guardar y verificar la consola. | Aparece la herramienta BGP Looking Glass permitiendo consultas de rutas y AS-Path sin acceso a SSH. |
| **UAT-50** | Ajuste de Umbral de Caída Masiva | Superadmin configurando tenant | 1. Modificar campo numérico *"Umbral de Caída Masiva"* de 10 a 5. 2. Guardar. | El valor se persiste en la columna `mass_outage_threshold` de la tabla `tenants` y el worker ajusta su sensibilidad en caliente. |

---

### Módulo 20: QoS Técnico, API de Aprovisionamiento y Webhooks

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-51** | Creación de Perfil Técnico de Ancho de Banda | Rol `ADMIN` o `OPERATOR` | 1. Ir a configuración de QoS/Colas. 2. Crear perfil *"100M/50M-Burst"*: Up 50M, Down 100M, Burst Up 75M, Burst Down 150M, Burst Time 8s, Prioridad 3. 3. Guardar. | Se crea el registro en `bandwidth_profiles` sin referencias a precios ni facturación, listo para aplicarse a Simple Queues o PCQ. |
| **UAT-52** | Aislamiento Técnico Idempotente de Equipo | Equipo activo en MikroTik | 1. Enviar `POST /api/v1/network-services/{id}/isolate` con cabecera `Idempotency-Key: {uuid}`. 2. Repetir la misma petición con la misma llave. | En la 1ra petición la IP entra en la Address List `AISLADOS_TECNICO` o limita a 64k. La 2da petición retorna HTTP 200 `{ status: "ALREADY_ISOLATED" }` sin mutaciones dobles. |
| **UAT-53** | Restauración Inmediata de Servicio | Equipo en estado aislado | 1. Enviar `POST /api/v1/network-services/{id}/restore` con `Idempotency-Key`. | La IP se remueve de la lista de bloqueo y su cola vuelve a los límites nominales en milisegundos sin reiniciar la sesión física. |
| **UAT-54** | Despacho de Webhook Firmado con HMAC | URL de webhook configurada | 1. Ejecutar acción de aislamiento o cambio de perfil. 2. Inspeccionar servidor receptor de webhooks. | El servidor receptor recibe `HTTP POST` con cabecera `X-RoSGrid-Signature: sha256=...` validable mediante la clave secreta compartida. |

---

### Módulo 21: Diagnóstico 360°, BGP Looking Glass y Flujos IPFIX

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-55** | Diagnóstico 360° con Ping Multi-MTU | Equipo accesible en MikroTik | 1. Ejecutar prueba 360° hacia la IP del equipo. 2. Observar panel de resultados. | Muestra métricas de latencia y pérdida para paquetes de 64B, 512B y 1472B, identificando problemas de jitter o fragmentación de MTU. |
| **UAT-56** | Parseo de Causa de Desconexión en Logs | Sesión PPPoE desconectada | 1. Desconectar físicamente el cable de red de un equipo. 2. Ejecutar diagnóstico 360°. | El sistema parsea `/log` de RouterOS e informa con precisión: *"Motivo: peer is not responding (Corte de enlace físico / micro-corte óptico)"*. |
| **UAT-57** | Muestreo Torch Instantáneo por IP | Tráfico activo hacia el cliente | 1. En diagnóstico 360°, iniciar muestreo Torch (2.5s). | Muestra los 5 principales flujos de red clasificados por protocolo, puerto y velocidad Tx/Rx en kbps. |
| **UAT-58** | Consulta BGP Looking Glass sin SSH | Sesión BGP activa en router Edge | 1. Ir a BGP Looking Glass. 2. Ingresar prefijo `8.8.8.8/32`. 3. Consultar. | Retorna la ruta activa, Next-Hop, AS-Path completo y comunidades BGP directamente desde la tabla de rutas de RouterOS v7. |

---

### Módulo 22: Mapa de Clientes/ONUs, Alerta Masiva, Responsive e i18n

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-59** | Mapa de ONUs Separado de Infraestructura | ONUs con coordenadas GPS | 1. Acceder a `/subscribers/map`. 2. Comparar con el mapa de routers en `/inventory`. | El mapa de ONUs es independiente. Los marcadores muestran estado cromático en vivo: Verde (óptimo), Naranja (latencia alta) o Rojo (offline). |
| **UAT-60** | Alarma NOC por Caída Masiva (> 10 Equipos) | 12 equipos simulando caída simultánea | 1. Forzar timeout o caída en 12 equipos de la misma zona. 2. Observar el Wallboard NOC. | Se dispara banner de emergencia visual y auditivo *"ALERTA: Caída masiva detectada (12 equipos)"*, y se estampa entrada WORM en `audit_logs`. |
| **UAT-61** | Toolkit de Campo Fluido y Responsive | Dispositivo móvil, tablet o laptop | 1. Abrir vista de Técnico de Campo en navegador redimensionado a 375px (móvil), 768px (tablet) y 1280px (laptop). | El contenido se adapta fluidamente sin el rectángulo vertical estrecho forzado. Botones táctiles de al menos 48px en móvil. |
| **UAT-62** | Activación Técnica con Captura GPS | Técnico en campo registrando equipo | 1. Ingresar serial de la ONU (sin nombres de cliente). 2. Presionar *"📍 Capturar Coordenadas GPS"*. 3. Confirmar activación. | El navegador lee la geolocalización satelital, asocia las coordenadas al equipo y este aparece de inmediato en el mapa `/subscribers/map`. |
| **UAT-63** | Conmutación de Idioma i18n | Interfaz en Español (default) | 1. En la barra superior, cambiar selector de idioma de *"ES"* a *"EN"*. | Toda la terminología de navegación, menús tácticos y estados conmuta fluidamente a Inglés mediante los diccionarios JSON reactivos. |

---

### Módulo 23: Suite Corporativa — Config Drift, CIS Hardening, SD-WAN, Rogue DHCP, SLA y CAPsMAN

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-64** | Detección de Desviación (*Config Drift*) | Router con regla de firewall alterada localmente | 1. Ejecutar análisis de Drift contra la Plantilla Maestra (*Golden Baseline*). 2. Observar el visor Diff. | Se resalta en rojo la regla no autorizada. El router pasa a estado `CONFIG_DRIFT_DETECTED`. |
| **UAT-65** | Remediación en 1-Clic (*Auto-Revert*) | Drift detectado en router | 1. Presionar *"Revertir a Configuración Homologada"*. 2. Confirmar con aprobación Maker-Checker. | RoSGrid aplica el bloque correctivo bajo Safe Mode (60s), eliminando la regla no autorizada y normalizando el estado a `COMPLIANT`. |
| **UAT-66** | Auditoría CIS Benchmark y Security Score | Router recién instalado | 1. Ejecutar auditoría CIS en el router. 2. Revisar puntuación. | Muestra calificación (ej. 60/100) listando vulnerabilidades: Telnet activo, usuario `admin` existente y DNS remoto permitido. |
| **UAT-67** | Auto-Endurecimiento (*Auto-Hardening*) | Router con vulnerabilidades CIS | 1. Presionar *"Endurecer Router Automáticamente"*. | Aplica script correctivo con Safe Mode: desactiva servicios inseguros, renombra `admin` y restringe WinBox, elevando el Score a 100/100. |
| **UAT-68** | Detección de Rogue DHCP en Switch | Switch MikroTik con DHCP Snooping | 1. Conectar servidor DHCP falso en puerto no confiable (`trusted=no`). 2. Observar alerta NOC. | El chip de conmutación descarta los paquetes por hardware y RoSGrid alerta al operador con la MAC del intruso y el puerto físico exacto. |
| **UAT-69** | Reporte Mensual de Cumplimiento de SLA | Enlace WAN dedicado monitoreado | 1. Ir a Monitor de SLA. 2. Exportar reporte mensual en PDF/CSV. | Genera documento formal con porcentaje de disponibilidad (Uptime), latencia P95/P99 y lista de caídas para reclamos contractuales. |
| **UAT-70** | Centralización WiFi CAPsMAN (SSIDs) | Entorno con Access Points MikroTik | 1. Desplegar perfil inalámbrico con SSIDs Corporativo (802.1X), Invitados y Dispositivos IoT. | Los APs se aprovisionan simultáneamente, aplicando aislamiento de clientes en la red de invitados y roaming rápido 802.11r. |

---

### Módulo 24: Agentes de IA vía MCP (Asistencia Técnica Autónoma)

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-71** | Diagnóstico Autónomo de Equipo vía MCP | Agente IA (Claude / Hermes) conectado a `/api/v1/mcp` | 1. Indicar al agente: *"Diagnostica la ONU con serial ZTEGC1234567"*. | El agente invoca la tool `rosgrid_run_360_diagnostics`, evalúa latencia multi-MTU y causas de log, y entrega diagnóstico técnico resumido. |
| **UAT-72** | Aislamiento Técnico de Dispositivo por IA | Permiso de agente configurado | 1. Indicar al agente: *"Aísla el equipo con ID 42 por reporte de bucle"*. | El agente invoca `rosgrid_isolate_subscriber` con cabecera de idempotencia; el cambio se aplica y queda registrado en la bitácora WORM. |
| **UAT-73** | Consulta de Rutas BGP vía IA | BGP Looking Glass habilitado | 1. Indicar al agente: *"Verifica por cuál proveedor estamos alcanzando el prefijo 1.1.1.0/24"*. | El agente invoca `rosgrid_query_bgp_looking_glass` y analiza el AS-Path y Next-Hop activo de forma autónoma. |
| **UAT-74** | Detección de Cortes y Caídas Masivas por IA | Evento de caída masiva activo | 1. Indicar al agente: *"Revisa si hay cortes masivos de red en este momento"*. | El agente invoca `rosgrid_detect_mass_outage`, identifica los equipos caídos y la rama o zona afectada, y recomienda acciones de mitigación. |

---

### Módulo 25: Branding Institucional, Footer Global y Enlaces Oficiales

| ID | Caso de Prueba | Precondición | Pasos de Ejecución | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-75** | Branding Institucional en Login y Shell | Navegador en `/login` y sesión activa en el sistema | 1. Cargar `/login` y verificar el pie de página. 2. Hacer clic en el icono de GitHub. 3. Iniciar sesión y verificar la base del sitio (`RgResponsiveShell.vue`). | En `/login` se muestra el enlace al repositorio `https://github.com/tecno-consultores/RoSGrid/` con icono SVG de GitHub, versión del sistema, licencia GNU GPLv3 y el texto *"Elaborado por Tecno Consultores 2023 C.A."*. Dentro de la aplicación, el footer global exhibe el crédito institucional con tipografía accesible (`--rg-text-muted`, contraste >= 4.5:1) sin obstruir la cuadrícula de monitoreo. |

---

## 4. Plantilla de Bitácora de Ejecución (Sign-off)

```markdown
# 📝 Registro de Ejecución UAT — Versión [X.Y.Z]
- **Fecha:** AAAA-MM-DD
- **Ejecutor:** Nombre y Apellido
- **Entorno:** [Producción Local / Laboratorio CHR / RouterBOARD Físico]
- **Dispositivo MikroTik:** Modelo [ej. CHR / RB4011], RouterOS v[7.14.x]

| ID Caso | Módulo | Resultado (Pass/Fail/Block) | Evidencia / Comentarios |
| :--- | :--- | :--- | :--- |
| UAT-01 | Bootstrap Virgin DB | PASS | Autodetección inmediata en http://localhost:8085/ |
| UAT-02 | Creación Superadmin | PASS | Organización creada y login redirigido |
| ... | ... | ... | ... |

### Veredicto Final:
[ ] APROBADO PARA PRODUCCIÓN (Release Candidate)
[ ] BLOQUEADO (Se requieren correcciones antes del despliegue)
```
