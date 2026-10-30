# 15 — ENDPOINTS BACKEND WEBFIG CAPA 2: MOTOR DINÁMICO UNIVERSAL PARA EL 100% DE ROUTEROS v7 (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la arquitectura y contratos del **Motor Dinámico Universal WebFig (Capa 2)** en fastapi/src/api/v1/webfig\_dynamic\_l2.py y fastapi/src/services/webfig\_l2\_service.py. Mientras la Capa 1 ofrece vistas especializadas para los módulos de uso diario, la **Capa 2** permite operar el **100% restante de los menús de RouterOS v7.1+** (incluyendo MPLS, VXLAN, ZeroTier, Containers, IoT, CAPsMAN/WifiWave2 avanzado, User-Manager, RADIUS, BFD avanzado, IPv6 ND, Certificates, SNMP, etc.) pasando por el mismo tubo de seguridad de RoSGrid: **RBAC, Idempotencia en Redis, Pinning SSL TOFU, Intercepción Maker-Checker, Safe Mode Anti-Bloqueo y Auditoría Inmutable**.




## **1. Reglas de Seguridad y Control de Acceso de la Capa 2**

1. **Matriz RBAC para Capa 2:**

   - **Lectura (GET / consulta de esquemas):** Permitida a SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2 y AUDITOR (además de validar en user\_router\_permissions que tenga acceso al router).

   - **Escritura y Ejecución (POST, PUT, PATCH, DELETE):** Permitida directamente solo a SUPERADMIN\_GLOBAL, TENANT\_ADMIN y SUPPORT\_L3 (siempre que user\_router\_permissions.can\_write\_layer2 == True o tenga acceso total al Tenant). Cualquier otro rol recibe HTTP 403 Forbidden.

2. **Lista Negra Estricta de Rutas Prohibidas en Capa 2 (FORBIDDEN\_L2\_PATHS):**

   - Para evitar que alguien utilice el motor dinámico de Capa 2 para evadir las reglas de negocio de RoSGrid, el validador validate\_l2\_ros\_path(ros\_path) bloquea con HTTP 403 Forbidden cualquier intento de acceder por Capa 2 a:

     - Modificación del usuario API propio de RoSGrid en /user (debe hacerse por el endpoint de Rotación de Bóveda).

     - Eliminación o modificación de los schedulers internos rosgrid-safemode-\* en /system/scheduler.

     - Deshabilitación del servicio www-ssl activo en /ip/service.

3. **Sanitización contra Path Traversal y SSRF:**

   - ros\_path se valida con la expresión regular estricta ^\[a-z0-9-\]+(?:/\[a-z0-9-\*.\_\]+)\*$. Queda prohibido incluir .., //, ?, \# o caracteres de control.




## **2. Catálogo de Endpoints de la Capa 2 (/api/v1/routers/\{router\_id\}/webfig/layer2)**

### **2.1 GET /api/v1/routers/\{router\_id\}/webfig/layer2/catalog — Árbol de Menús Soportados por el Router**

- Devuelve el árbol jerárquico de submenús de RouterOS v7 adaptado a los paquetes instalados en ese MikroTik (system/package), para que el frontend de Vue 3 construya el explorador lateral de Capa 2 e integre todas las rutas en el buscador global Ctrl + K.

- **Response 200 OK:**


\{


  "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


  "ros\_version": "7.16.1",


  "installed\_packages": \["routeros", "wifi-qcom", "container", "zerotier"\],


  "menu\_tree": \[


    \{


      "group": "MPLS & VPLS",


      "items": \[


        \{"label": "MPLS Interfaces", "ros\_path": "mpls/interface", "supports\_safe\_mode": true\},


        \{"label": "LDP Instance", "ros\_path": "mpls/ldp", "supports\_safe\_mode": true\},


        \{"label": "VPLS Tunnels", "ros\_path": "interface/vpls", "supports\_safe\_mode": true\}


      \]


    \},


    \{


      "group": "ZeroTier & Containers",


      "items": \[


        \{"label": "ZeroTier Instances", "ros\_path": "zerotier", "supports\_safe\_mode": true\},


        \{"label": "ZeroTier Interfaces", "ros\_path": "zerotier/interface", "supports\_safe\_mode": true\},


        \{"label": "OCI Containers", "ros\_path": "container", "supports\_safe\_mode": false\},


        \{"label": "Container Mounts", "ros\_path": "container/mounts", "supports\_safe\_mode": false\}


      \]


    \}


  \]


\}

### **2.2 GET /api/v1/routers/\{router\_id\}/webfig/layer2/resource/\{ros\_path:path\} — Lectura Universal e Inferencia de Columnas**

- Consulta GET \<api\_base\_url\>/rest/\{ros\_path\} en el MikroTik y devuelve tanto las filas como un **descriptor dinámico de columnas (columns\_schema)** inferido automáticamente para que Vue 3 renderice la tabla y los filtros sin código hardcodeado:

- **Response 200 OK (DynamicLayer2CollectionResponse):**


\{


  "ros\_path": "mpls/interface",


  "is\_singleton": false,


  "supports\_safe\_mode": true,


  "columns\_schema": \[


    \{"key": ".id", "label": "ID", "type": "readonly\_id", "sortable": true\},


    \{"key": "interface", "label": "Interface", "type": "string", "editable": true\},


    \{"key": "mpls-mtu", "label": "MPLS MTU", "type": "integer", "editable": true\},


    \{"key": "disabled", "label": "Disabled", "type": "boolean\_ros", "editable": true\},


    \{"key": "comment", "label": "Comment", "type": "string", "editable": true\}


  \],


  "items": \[


    \{


      ".id": "\*1",


      "interface": "all",


      "mpls-mtu": "1508",


      "disabled": "false",


      "dynamic": "false",


      "comment": "MPLS Backbone"


    \}


  \]


\}


- **Detección Automática de Menús Singleton:** En RouterOS v7 algunos menús no devuelven una lista \[...\] sino un único diccionario JSON \{...\} (ej. ip/settings, system/ntp/client, snmp). El motor detecta isinstance(data, dict), marca is\_singleton = True y permite a Vue 3 mostrar directamente un formulario de edición en lugar de una tabla.

### **2.3 POST /api/v1/routers/\{router\_id\}/webfig/layer2/resource/\{ros\_path:path\} — Creación Universal de Registro (PUT /rest/...)**

- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.

- **Request Body (DynamicLayer2WriteRequest):**


\{


  "attributes": \{


    "interface": "ether2",


    "mpls-mtu": "1526",


    "comment": "Enlace MPLS Nodo Sur"


  \},


  "enable\_safemode": true


\}


- **Proceso:**

  1. Evalúa si ros\_path cae en alguna regla de **Maker-Checker** (si aplica, devuelve 202 Accepted).

  2. Si enable\_safemode == true (forzado a true en rutas de red), activa el **Dead Man's Switch** de 60 segundos en /system/scheduler.

  3. Envía PUT \<api\_base\_url\>/rest/\{ros\_path\} al MikroTik.

  4. Verifica conectividad, limpia el scheduler temporal y escribe en audit\_logs con categoría WEBFIG\_L2 y acción L2\_RESOURCE\_CREATED.

### **2.4 PATCH /api/v1/routers/\{router\_id\}/webfig/layer2/resource/\{ros\_path:path\}/\{item\_id\} — Edición Universal de Registro**

- Lee el before\_state desde el MikroTik, programa el comando exacto de reversión en el /system/scheduler del router, aplica PATCH \<api\_base\_url\>/rest/\{ros\_path\}/\{item\_id\}, verifica que el router siga respondiendo y registra before\_state y after\_state en audit\_logs.

### **2.5 DELETE /api/v1/routers/\{router\_id\}/webfig/layer2/resource/\{ros\_path:path\}/\{item\_id\} — Eliminación Universal Protegida**

- Lee el registro antes de borrarlo, aplica la estrategia de deshabilitación preventiva durante la ventana de Safe Mode (si el recurso admite disabled), verifica supervivencia, elimina definitivamente y registra L2\_RESOURCE\_DELETED en audit\_logs.

### **2.6 POST /api/v1/routers/\{router\_id\}/webfig/layer2/command/\{ros\_path:path\} — Ejecución Controlada de Acciones CLI vía REST**

- Permite invocar métodos específicos de un submenú (ej. POST /rest/certificate/sign, POST /rest/container/start o POST /rest/container/stop) auditando la entrada y el resultado.

---

## **3. Extensiones Next-Gen del Motor Universal de Capa 2 (Hito 27.16 — Spec 54)**

> **Referencia Canónica:** Véase [docs/specs/54_WEBFIG_L2_UNIVERSAL_ENGINE_NEXTGEN_RPC_INSPECT_QUERY_BULK_AND_PROFILES.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/specs/54_WEBFIG_L2_UNIVERSAL_ENGINE_NEXTGEN_RPC_INSPECT_QUERY_BULK_AND_PROFILES.md) para el detalle integral de esquemas Pydantic, flujos de seguridad y componentes UI.

1. **`GET /api/v1/routers/{router_id}/webfig/layer2/rpc-catalog/{ros_path:path}` y Catálogo de Verbos RPC (`L2_RPC_ACTIONS_CATALOG`):**
   - Expone los verbos RPC seguros soportados por cada submenú (`add-acme`, `sign`, `export-certificate`, `create-certificate-request`, `make-static`, `start`, `stop`, `run`, `kill-connections`) con validación de argumentos, soporte por menú o por fila (`.id`) y ejecución bajo Safe Mode (60s) / Maker-Checker (`HTTP 202`).
2. **`GET /api/v1/routers/{router_id}/webfig/layer2/inspect/{ros_path:path}` — Introspección Automática con `/rest/console/inspect`:**
   - Consulta `POST /rest/console/inspect` (`request="syntax"` y `request="completion"`) con caché en KeyDB (`rg:{tid}:l2_schema:{ros_ver}:{ros_path}`, TTL 24h) para descubrir el 100% de las propiedades válidas, tipos, enumeraciones y descripciones incluso cuando la tabla en el router tiene **0 registros**.
3. **`POST /api/v1/routers/{router_id}/webfig/layer2/query/{ros_path:path}` y Query Param `?proplist=` — Filtrado Server-Side (`.query`) y Proyección (`.proplist`):**
   - Delega el filtrado (`.query`) y la selección de columnas (`.proplist`) al motor C++ de RouterOS v7 mediante `POST /rest/{ros_path}/print`, reduciendo hasta en un **85%** el payload JSON en tablas masivas (`/ip/arp`, `/ip/firewall/address-list`, `/routing/route`, `/certificate`).
4. **`POST /api/v1/routers/{router_id}/webfig/layer2/bulk/{ros_path:path}` — Operaciones por Lote (`Bulk Enable / Disable / Comment / Remove`):**
   - Ejecuta mutaciones masivas sobre múltiples `.id` seleccionados bajo un **único scheduler atómico de reversión Safe Mode (60s)** y un registro consolidado WORM (`L2_BULK_MUTATION_EXECUTED`).
5. **`POST /api/v1/routers/{router_id}/webfig/layer2/export/{ros_path:path}` — Exportación Contextual `.rsc` y Comparador Diff:**
   - Invoca `POST /rest/{ros_path}/export` (`compact`/`terse`) y calcula el `unified_diff` contra la sección homónima del último respaldo Git almacenado en `router_backups`.
