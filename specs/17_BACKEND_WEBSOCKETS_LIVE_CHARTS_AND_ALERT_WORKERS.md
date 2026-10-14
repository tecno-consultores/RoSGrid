# 17 — BACKEND WEBSOCKETS (GRÁFICAS EFÍMERAS WINBOX + NOC) Y WORKERS DE ALERTAS CERO-MÉTRICAS (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la arquitectura en tiempo real del Backend: los canales **WebSocket** (fastapi/src/api/v1/websockets.py) que alimentan las gráficas efímeras en memoria RAM de Vue 3 (estilo WinBox) y la pantalla Wallboard NOC, así como los **Workers Asíncronos** (fastapi/src/workers/) encargados del monitoreo de estado en Redis (*Zero-Storage*) y el despacho de alertas hacia **Telegram Bot, Correo SMTP y Webhooks firmados**.




## **1. Reglas de Autenticación y Seguridad en WebSockets**

1. **Autenticación Automática por Cookie \_\_Host-rg\_at:**

   - Como la conexión WebSocket nace desde el mismo origen a través del proxy inverso de Nginx (/ws/...), el navegador adjunta automáticamente la cookie HttpOnly \_\_Host-rg\_at (o rg\_at en entorno local QA) en el handshake HTTP Upgrade.

   - Queda **prohibido** pasar tokens JWT por query string (?token=...) para que jamás queden expuestos en los logs de acceso de Nginx.

2. **Validación Continua de Sesión y *Kill-Switch*:**

   - En el handshake se verifica EXISTS rg:\{tenant\_id\}:sess:\{session\_id\} en Redis y el permiso RBAC del usuario sobre el \{router\_id\}.

   - Cada worker WebSocket permanece suscrito al canal rg:pubsub:events:\{tenant\_id\}. Si recibe un evento SESSION\_KILLED cuyo target\_session\_id o target\_user\_id coincide con el de la conexión actual, cierra el socket inmediatamente con código 4401 ("Sesión revocada por un Administrador/Supervisor").




## **2. Canal WebSocket 1: Telemetría Efímera Estilo WinBox (/ws/v1/routers/\{router\_id\}/live-telemetry)**

**MANDAMIENTO ARQUITECTÓNICO:** Ningún mensaje transmitido por este WebSocket se guarda en PostgreSQL ni en listas históricas de Redis. Si el técnico deja la pestaña abierta 3 horas, ve 3 horas de gráfica; si cierra o refresca, empieza desde cero igual que WinBox.

### **2.1 Ciclo de Vida del Multiplexor (fastapi/src/services/telemetry\_multiplexer.py)**

1. **Conexión del Operador:**

   - El usuario se conecta a /ws/v1/routers/\{router\_id\}/live-telemetry.

   - Se actualiza en Redis su sesión activa (HSET rg:\{tenant\_id\}:sess:\{session\_id\} current\_router\_id \{router\_id\}) para que el Supervisor vea en vivo en qué MikroTik está metido el técnico.

   - Se agrega el connection\_id al conjunto rg:\{tenant\_id\}:ws\_subs:\{router\_id\}.

2. **Bucle de Sondeo Compartido (1 Poller por Router Activo):**

   - Mientras SCARD rg:\{tenant\_id\}:ws\_subs:\{router\_id\} \>= 1, una única tarea asíncrona consulta cada **2 segundos** al MikroTik:

     - GET \<api\_base\_url\>/rest/system/resource

     - GET \<api\_base\_url\>/rest/system/health

     - GET \<api\_base\_url\>/rest/interface?.proplist=.id,name,type,running,disabled,rx-byte,tx-byte,rx-packet,tx-packet,fp-rx-byte,fp-tx-byte

   - Calcula el diferencial (delta\_bytes \* 8 / delta\_seconds) respecto a la lectura de hace 2 segundos en memoria local del worker para obtener los **bps exactos (rx\_bps, tx\_bps)** de cada interfaz.

   - Publica el frame JSON en rg:pubsub:telemetry:\{tenant\_id\}:\{router\_id\}.

3. **Estructura Exacta del Frame JSON Enviado cada 2 Segundos al Navegador:**


\{


  "type": "TELEMETRY\_TICK",


  "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


  "timestamp\_iso": "2026-10-14T22:25:02Z",


  "system": \{


    "uptime": "18d04h12m30s",


    "cpu\_load\_pct": 24,


    "cpu\_count": 4,


    "cpu\_frequency\_mhz": 1400,


    "free\_memory\_bytes": 784334848,


    "total\_memory\_bytes": 1073741824,


    "memory\_used\_pct": 26.9,


    "free\_hdd\_bytes": 419430400,


    "total\_hdd\_bytes": 536870912,


    "temperature\_c": 46.0,


    "voltage\_v": 24.1


  \},


  "interfaces": \[


    \{


      "name": "ether1-WAN1",


      "running": true,


      "disabled": false,


      "rx\_bps": 412500800,


      "tx\_bps": 85400200,


      "rx\_pps": 38420,


      "tx\_pps": 14110


    \},


    \{


      "name": "ether2-WAN2",


      "running": true,


      "disabled": false,


      "rx\_bps": 398100400,


      "tx\_bps": 79200100,


      "rx\_pps": 36900,


      "tx\_pps": 13200


    \}


  \]


\}


4. **Desconexión y Apagado Inmediato:**

   - En el bloque finally: del WebSocket, se ejecuta SREM rg:\{tenant\_id\}:ws\_subs:\{router\_id\} \{connection\_id\}. Si el conjunto queda vacío, el bucle de consulta hacia ese MikroTik se cancela en el acto.




## **3. Canal WebSocket 2: Eventos Globales, Wallboard NOC y *Kill-Switch* (/ws/v1/tenant/events)**

Este canal permanece abierto en todas las sesiones autenticadas (y especialmente en los televisores/pantallas con el rol **NOC\_MONITOR**):


- **Tipos de Eventos Transmitidos en Tiempo Real:**

  1. ROUTER\_STATE\_CHANGED: Cuando un MikroTik pasa de ONLINE a OFFLINE, DEGRADED\_HIGH\_LOAD, MAINTENANCE o SSL\_MISMATCH (actualiza al instante el color del pin en el mapa **OpenStreetMap** y las tarjetas del Wallboard NOC con sonido/alerta visual).

  2. APPROVAL\_REQUEST\_CREATED / APPROVAL\_REQUEST\_RESOLVED: Actualiza en vivo el contador de la campana de **Maker-Checker** para Supervisores y Soporte N3.

  3. BULK\_JOB\_PROGRESS: Actualiza la barra de progreso de las Acciones Masivas y Upgrades de RouterOS.

  4. SESSION\_KILLED: Fuerza el cierre inmediato de la sesión revocada en el navegador del técnico expulsado.




## **4. Workers Asíncronos en Segundo Plano (fastapi/src/workers/)**

El proceso rosgrid-worker ejecuta 4 tareas periódicas desacopladas (CC \<= 5 por función):

### **4.1 Worker 1: Monitor de Salud *Zero-Storage* (health\_monitor\_worker.py — Cada 30s)**

- Obtiene los routers con admin\_state == 'PRODUCTION'.

- Verifica si el router tiene una ventana activa en maintenance\_windows.

- Realiza un ping ligero por REST API (GET /rest/system/resource) con timeout de 5 segundos.

- Actualiza únicamente el Hash de 200 bytes rg:\{tenant\_id\}:mon\_state:\{router\_id\} en Redis.

- Si detecta una transición de estado (consecutive\_failures == 3 -\> OFFLINE, recuperación a ONLINE, consecutive\_high\_cpu == 4 -\> DEGRADED\_HIGH\_LOAD, o SSL\_MISMATCH) y **no** está en ventana de mantenimiento, encola la alerta para despacho inmediato.

### **4.2 Worker 2: Despachador Multi-Canal de Alertas (alert\_dispatcher\_worker.py)**

Lee los canales habilitados en notification\_channels del Tenant (desencriptando sus credenciales con AES-256-GCM) y despacha la alerta por:


1. **Bot de Telegram (TELEGRAM\_BOT):**

   - POST a la API de Telegram (sendMessage) con formato Markdown claro indicando: Empresa, Nombre del Router, Ubicación Física, Coordenadas OSM, Evento (🔴 ROUTER OFFLINE / 🟢 ROUTER ONLINE / ⚠️ ALERTA SSL TOFU / ⏳ APROBACIÓN PENDIENTE) y hora exacta (America/Caracas).

2. **Correo Electrónico (SMTP\_EMAIL):**

   - Envío asíncrono con plantilla HTML/Texto limpia a la lista de destinatarios configurada por el Tenant.

3. **Webhook HTTP Genérico Firmado (GENERIC\_WEBHOOK):**

   - Envía un POST JSON con cabecera X-RoSGrid-Signature-256 (HMAC-SHA256 del payload usando el secreto del canal) para integración segura con n8n, Slack, Discord o Mattermost.

4. **Notificación Web en Vivo (Wallboard NOC):**

   - Publica simultáneamente en rg:pubsub:events:\{tenant\_id\} para todas las pantallas abiertas en el NOC.

### **4.3 Worker 3: Respaldos Nocturnos Deduplicados y Purga de 30 Días (nightly\_backup\_worker.py)**

- Se ejecuta cada noche (por defecto a las 03:00 AM America/Caracas):

  - Descarga .rsc y .backup de todos los routers activos.

  - Aplica deduplicación por rsc\_sha256\_hash y calcula el Diff contra el backup anterior.

  - Elimina los registros de router\_backups y archivos .backup en disco con antigüedad mayor a **30 días** (expires\_at \< NOW()), garantizando conservar siempre al menos el último respaldo válido de cada equipo.

### **4.4 Worker 4: Rotación Programada de Credenciales API (vault\_rotation\_worker.py)**

- Revisa router\_credentials\_vault donde auto\_rotate\_enabled == True y next\_rotation\_due\_at \<= NOW(), ejecutando la rotación atómica de contraseña de 32 caracteres en el MikroTik y en la bóveda cifrada.
