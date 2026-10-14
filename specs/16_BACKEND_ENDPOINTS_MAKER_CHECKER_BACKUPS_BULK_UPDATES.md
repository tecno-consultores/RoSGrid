# 16 — ENDPOINTS BACKEND: MAKER-CHECKER, BACKUPS DEDUPLICADOS Y DIFF GIT (.rsc), PLANTILLAS, ACCIONES MASIVAS, UPDATES Y AUDITORÍA (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los contratos HTTP para los módulos operativos avanzados: bandeja de aprobaciones **Maker-Checker** (fastapi/src/api/v1/approvals.py), respaldos .rsc/.backup con comparador **Diff estilo Git** (fastapi/src/api/v1/backups.py), plantillas parametrizables y acciones masivas multi-router (fastapi/src/api/v1/bulk\_ops.py), actualización centralizada de RouterOS v7 (fastapi/src/api/v1/updates.py) y la consola de consulta/exportación de la **Auditoría Inmutable** (fastapi/src/api/v1/audit.py).




## **1. Bandeja de Aprobaciones Críticas — *Maker-Checker* (/api/v1/operations/approvals)**

### **1.1 GET /api/v1/operations/approvals — Listar Solicitudes de Cambio**

- **Roles Permitidos:**

  - SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, AUDITOR: Ven todas las solicitudes del Tenant (filtrables por ?status=PENDING).

  - SUPPORT\_L2, SUPPORT\_L1, FIELD\_TECH: Ven únicamente las solicitudes creadas por ellos mismos (requested\_by == current\_user.id).

### **1.2 POST /api/v1/operations/approvals/\{approval\_id\}/approve — Aprobar y Ejecutar Cambio en el MikroTik**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3.

- **Regla Inquebrantable de Segregación de Funciones (SoD):**

  - Un usuario **NO PUEDE** aprobar su propia solicitud (approval.requested\_by == current\_user.id -\> HTTP 403 Forbidden: "Violación Maker-Checker: El solicitante no puede aprobar su propio cambio").

- **Request Body (ApproveRequestPayload):**


\{


  "review\_comment": "Cambio validado con ingeniería. Autorizado durante ventana nocturna."


\}


- **Proceso:**

  1. Verifica que status == 'PENDING' y expires\_at \> NOW().

  2. Despacha la operación exacta almacenada (ros\_rest\_method, ros\_rest\_path, request\_payload) hacia el MikroTik (o hacia el motor de bulk\_jobs si es una acción masiva) activando el **Safe Mode Anti-Bloqueo** de 60 segundos.

  3. Actualiza status = 'APPROVED\_AND\_EXECUTED', reviewed\_by, reviewed\_at, executed\_at y execution\_result.

  4. Escribe MAKER\_CHECKER\_APPROVED\_AND\_EXECUTED en audit\_logs.

### **1.3 POST /api/v1/operations/approvals/\{approval\_id\}/reject — Rechazar Solicitud de Cambio**

- Marca status = 'REJECTED', guarda el motivo en review\_comment, notifica al solicitante por WebSocket y escribe en audit\_logs.




## **2. Respaldos Automáticos (.rsc y .backup) y Comparador Visual Diff Estilo Git (/api/v1/routers/\{router\_id\}/backups)**

### **2.1 GET /api/v1/routers/\{router\_id\}/backups — Historial de Respaldos (Retención 30 Días con Deduplicación)**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2, INVENTORY\_MANAGER, AUDITOR.

- **Response 200 OK:**


\{


  "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


  "retention\_days": 30,


  "items": \[


    \{


      "id": "01928d00-2222-7a00-8000-000000000002",


      "backup\_type": "AUTOMATIC\_NIGHTLY",


      "ros\_version\_at\_backup": "7.16.1",


      "rsc\_sha256\_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",


      "rsc\_size\_bytes": 18420,


      "diff\_lines\_added": 12,


      "diff\_lines\_removed": 3,


      "parent\_backup\_id": "01928d00-1111-7a00-8000-000000000001",


      "has\_binary\_backup": true,


      "created\_at": "2026-10-14T03:00:00Z",


      "last\_verified\_identical\_at": "2026-10-14T15:00:00Z"


    \}


  \]


\}

### **2.2 POST /api/v1/routers/\{router\_id\}/backups/trigger — Ejecutar Backup Manual Inmediato (.rsc + .backup)**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2, INVENTORY\_MANAGER, SERVICE\_ACCOUNT.

- **Proceso:**

  1. Invoca POST \<api\_base\_url\>/rest/export (\{"terse": "false", "show-sensitive": "false"\}) y POST \<api\_base\_url\>/rest/system/backup/save en el MikroTik.

  2. Normaliza el texto .rsc (eliminando la marca de tiempo de cabecera de RouterOS para que el hash solo cambie si cambió una línea real de configuración).

  3. Calcula rsc\_sha256\_hash. Si coincide con el último backup de ese router, actualiza last\_verified\_identical\_at = NOW() y devuelve \{"status": "IDENTICAL\_SKIPPED\_DEDUPLICATED"\}.

  4. Si hubo cambios: calcula con difflib.unified\_diff las líneas añadidas (diff\_lines\_added) y eliminadas (diff\_lines\_removed) respecto al backup anterior, cifra el .rsc con AES-256-GCM e inserta el nuevo registro con expires\_at = NOW() + 30 days.

### **2.3 GET /api/v1/routers/\{router\_id\}/backups/diff — Comparador Visual Estilo Git entre Dos Versiones .rsc**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2, AUDITOR.

- **Query Params:** ?base\_backup\_id=\<uuid\>&target\_backup\_id=\<uuid\> (o ?target\_backup\_id=LIVE para comparar un backup contra la configuración en vivo actual del MikroTik).

- **Response 200 OK (BackupGitDiffResponse):**


\{


  "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


  "base\_backup\_id": "01928d00-1111-7a00-8000-000000000001",


  "base\_created\_at": "2026-10-13T03:00:00Z",


  "target\_backup\_id": "01928d00-2222-7a00-8000-000000000002",


  "target\_created\_at": "2026-10-14T03:00:00Z",


  "lines\_added": 2,


  "lines\_removed": 1,


  "unified\_diff\_text": "--- backup\_2026-10-13.rsc\\n+++ backup\_2026-10-14.rsc\\n@@ -45,3 +45,4 @@\\n /ip firewall filter\\n-add action=accept chain=input dst-port=8291 protocol=tcp\\n+add action=accept chain=input dst-port=8291 protocol=tcp src-address-list=noc-mgmt\\n+add action=drop chain=input comment=\\"Drop resto WinBox\\" dst-port=8291 protocol=tcp",


  "side\_by\_side\_hunks": \[


    \{


      "section\_header": "/ip firewall filter",


      "old\_line\_num": 46,


      "new\_line\_num": 46,


      "change\_type": "MODIFIED",


      "old\_text": "add action=accept chain=input dst-port=8291 protocol=tcp",


      "new\_text": "add action=accept chain=input dst-port=8291 protocol=tcp src-address-list=noc-mgmt"


    \}


  \]


\}




## **3. Plantillas Parametrizables (*Golden Configs*) y Acciones Masivas (/api/v1/operations)**

### **3.1 Endpoints de Plantillas (/api/v1/operations/templates)**

- GET /api/v1/operations/templates: Lista plantillas del Tenant (ej. *"Hardening SSH/WinBox"*, *"Crear VLAN Clientes"*, *"Actualizar Servidores DNS"*).

- POST /api/v1/operations/templates: Crea una nueva plantilla con variables tipadas (variables\_schema) y pasos REST (rest\_steps\_template).

- POST /api/v1/operations/templates/\{template\_id\}/render-preview: Renderiza los pasos reemplazando las variables enviadas sin tocar ningún MikroTik todavía.

### **3.2 Endpoints de Acciones Masivas Multi-Router (/api/v1/operations/bulk-jobs)**

- POST /api/v1/operations/bulk-jobs:

  - Selecciona routers por lista explícita de router\_ids, por network\_role o por etiqueta tag.

  - Si el usuario es SUPPORT\_L2, la creación del trabajo masivo queda en status = 'AWAITING\_APPROVAL' vinculada a una solicitud en approval\_requests.

  - Si el usuario es SUPPORT\_L3, SUPERVISOR, TENANT\_ADMIN o SUPERADMIN\_GLOBAL, el worker ejecuta la operación en lotes concurrentes controlados (máximo 10 routers en paralelo por Tenant) aplicando **Safe Mode individual en cada router**.

- GET /api/v1/operations/bulk-jobs/\{job\_id\}: Devuelve el progreso en vivo (succeeded\_count, failed\_count y el detalle router por router desde bulk\_job\_items).




## **4. Actualización Centralizada de RouterOS v7 y RouterBOOT (/api/v1/operations/ros-updates)**

### **4.1 GET /api/v1/operations/ros-updates/status — Resumen de Versiones de toda la Flota**

- Devuelve qué MikroTiks están al día y cuáles tienen una actualización pendiente (update\_available\_version != ros\_version o firmware\_version != upgrade\_firmware\_version).

### **4.2 POST /api/v1/operations/ros-updates/execute — Lanzar o Programar Actualización Segura de RouterOS**

- **Regla Obligatoria Pre-Upgrade:**

  1. El worker ejecuta primero un **Backup Completo Pre-Upgrade (.rsc + .backup)** del MikroTik y verifica que se haya guardado en PostgreSQL/disco. Si el backup falla, **aborta la actualización de ese router**.

  2. Ejecuta POST \<api\_base\_url\>/rest/system/package/update/install (o agenda su ejecución dentro de una **Ventana de Mantenimiento** activa).

  3. Opcionalmente configura auto-upgrade=yes en /rest/system/routerboard/settings para que el RouterBOOT también quede actualizado tras el reinicio.




## **5. Consola y Exportación de Auditoría Inmutable (/api/v1/audit/logs)**

Diseñada específicamente para el rol **AUDITOR**, **SUPERVISOR**, **TENANT\_ADMIN** y **SUPERADMIN\_GLOBAL**:


- GET /api/v1/audit/logs:

  - Filtros avanzados: actor\_user\_id, actor\_role, router\_id, event\_category, event\_action, date\_from, date\_to, status\_code y búsqueda en JSON.

- POST /api/v1/audit/logs/verify-integrity:

  - Recorre la cadena de hashes (prev\_record\_hash -\> record\_sha256\_hash) del Tenant en audit\_logs y certifica matemáticamente que el 100% de las filas mantienen integridad criptográfica intacta (\{"integrity\_status": "VERIFIED\_INTACT", "verified\_records\_count": 14520\}).

- GET /api/v1/audit/logs/export:

  - Exporta el rango filtrado en formato CSV o JSON firmado con su hash SHA-256 en cabecera.
