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
