# 11 — ENDPOINTS BACKEND: INVENTARIO MIKROTIK, IMPORTACIÓN MASIVA CSV, BÓVEDA STEP-UP, ROTACIÓN DE CLAVES Y MANTENIMIENTO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los endpoints de fastapi/src/api/v1/inventory.py, fastapi/src/api/v1/vault.py y fastapi/src/api/v1/maintenance.py. Incluye el flujo de alta con autodescubrimiento vía REST API de RouterOS v7, el importador masivo CSV en 2 pasos (*Dry-Run* + ejecución), la consulta de claves protegida con *Step-Up Auth* (exclusiva para los 2 roles superiores), la rotación automática de contraseñas API y las ventanas de mantenimiento.




## **1. Endpoints de Inventario de Equipos MikroTik (/api/v1/inventory/routers)**

### **1.1 GET /api/v1/inventory/routers — Listar Equipos MikroTik (Tabla y Mapa OpenStreetMap)**

- **Roles Permitidos:** Todos los roles autenticados (filtrado automáticamente según user\_router\_permissions si el rol no tiene acceso global al Tenant).

- **Filtros Query String:**

  - network\_role (CORE, EDGE\_BGP, WAN\_BALANCER, BRAS\_PPPOE, DISTRIBUTION\_SWITCH, TOWER\_AP, CORPORATE\_CPE)

  - admin\_state (PRODUCTION, MAINTENANCE, STAGING\_LAB, RETIRED)

  - tag (ej. zona-norte)

  - search (busca por display\_name, serial\_number, ros\_identity, physical\_location o api\_base\_url)

- **Enriquecimiento con Estado Efímero de Redis:**

  - El endpoint combina los metadatos de PostgreSQL con una lectura en pipeline (MGET / HGETALL) de rg:\{tenant\_id\}:mon\_state:\{router\_id\} en Redis para devolver el estado operativo en vivo (ONLINE, DEGRADED\_HIGH\_LOAD, OFFLINE, SSL\_MISMATCH) y el último porcentaje instantáneo de CPU/RAM para colorear los pines en el mapa **OpenStreetMap**.

### **1.2 POST /api/v1/inventory/routers — Registrar un Nuevo MikroTik + Pinning TOFU Inicial**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, INVENTORY\_MANAGER.

- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.

- **Request Body (CreateRouterRequest):**


\{


  "display\_name": "RB4011-Balanceador-Principal",


  "api\_base\_url": "\<api\_base\_url\_https\>",


  "api\_port": 443,


  "api\_username": "rosgrid\_api\_admin",


  "api\_password": "ClaveInicialMikrotik\#2026",


  "network\_role": "WAN\_BALANCER",


  "admin\_state": "PRODUCTION",


  "physical\_location": "Centro de Datos Naguanagua, Rack 2, U14",


  "latitude": 10.264500,


  "longitude": -68.010200,


  "online\_since\_date": "2025-06-15",


  "serial\_number": "D4460B123456",


  "tags": \["balanceador", "naguanagua", "doble-wan"\],


  "operational\_notes": "Balanceo ECMP L4 con 2 enlaces de 600 Mbps",


  "site\_contact\_info": "NOC Local Ext 104",


  "auto\_rotate\_credentials": true,


  "rotation\_interval\_days": 30,


  "connect\_and\_discover\_now": true


\}


- **Proceso:**

  1. Verifica cuota disponible en tenants.max\_routers\_quota.

  2. Inserta el router en routers y sus etiquetas en router\_tags.

  3. Cifra api\_password con AES-256-GCM (AAD = f"\{tenant\_id\}:\{router\_id\}") e inserta en router\_credentials\_vault.

  4. Si connect\_and\_discover\_now == true:

     - Conecta a /rest/system/resource, /rest/system/routerboard y /rest/system/identity del MikroTik.

     - Captura la huella SHA-256 del certificado SSL autofirmado (**TOFU**) y pasa ssl\_trust\_status a 'TRUSTED\_PINNED'.

     - Actualiza automáticamente ros\_identity, board\_name, model\_name, architecture\_name, ros\_version, firmware\_version y serial\_number (si el equipo reporta su serial de hardware).

  5. Registra ROUTER\_CREATED en audit\_logs y responde 201 Created.

### **1.3 POST /api/v1/inventory/routers/\{router\_id\}/sync-discovery — Forzar Autodescubrimiento de Hardware y Versión**

- Consulta bajo demanda el MikroTik y actualiza modelo, versión de RouterOS, firmware y disponibilidad de paquetes de actualización.

### **1.4 POST /api/v1/inventory/routers/\{router\_id\}/repin-ssl — Autorizar Cambio de Certificado SSL Autofirmado (Re-Pin TOFU)**

- **Roles Permitidos:** Exclusivamente SUPERADMIN\_GLOBAL y TENANT\_ADMIN.

- **Request Body:** \{"totp\_code": "123456", "expected\_new\_sha256\_fingerprint": "a9f4..."\}.

- Actualiza la huella SHA-256 autorizada tras verificar el código 2FA del administrador y escribe ROUTER\_SSL\_REPINNED en audit\_logs.




## **2. Importación Masiva de Equipos por CSV en 2 Pasos (/api/v1/inventory/import-csv)**

Como acordamos en el diseño, el onboarding por CSV es de **baja complejidad** reutilizando los validadores Pydantic de CreateRouterRequest y se divide en 2 endpoints simples:

### **2.1 POST /api/v1/inventory/import-csv/dry-run — Paso 1: Validación en Seco (Sin Escribir en Base de Datos)**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, INVENTORY\_MANAGER.

- **Entrada:** multipart/form-data con archivo .csv (máximo 500 filas, 2 MB).

- **Columnas del CSV:** display\_name,api\_base\_url,api\_port,api\_username,api\_password,network\_role,admin\_state,physical\_location,latitude,longitude,online\_since\_date,serial\_number,tags

- **Proceso:**

  - Analiza fila por fila con csv.DictReader en memoria.

  - Verifica formato HTTPS, roles válidos, rangos de coordenadas GPS y duplicados contra la base de datos o dentro del mismo archivo CSV.

- **Response 200 OK (CsvDryRunResponse):**


\{


  "total\_rows": 15,


  "valid\_rows\_count": 14,


  "invalid\_rows\_count": 1,


  "can\_proceed": true,


  "rows\_preview": \[


    \{


      "row\_number": 2,


      "display\_name": "CCR2004-Core-1",


      "is\_valid": true,


      "errors": \[\]


    \},


    \{


      "row\_number": 3,


      "display\_name": "RB4011-Repetido",


      "is\_valid": false,


      "errors": \["El serial\_number D4460B999 ya existe en este Tenant"\]


    \}


  \]


\}

### **2.2 POST /api/v1/inventory/import-csv/commit — Paso 2: Confirmación e Importación Transaccional**

- Recibe la lista de filas validadas, cifra cada contraseña con AES-256-GCM, inserta en bloque en PostgreSQL, registra el lote en audit\_logs y encola en el worker el autodescubrimiento TOFU en segundo plano para los nuevos routers.




## **3. Endpoints de Bóveda Criptográfica y Rotación de Claves (/api/v1/inventory/routers/\{router\_id\}/vault)**

### **3.1 POST /api/v1/inventory/routers/\{router\_id\}/vault/reveal — Revelar Claves API (*Step-Up Auth* de 30 Segundos)**

- **Roles Permitidos:** **EXCLUSIVAMENTE SUPERADMIN\_GLOBAL y TENANT\_ADMIN** (los 2 perfiles más altos del sistema). Cualquier otro perfil recibe HTTP 403 Forbidden.

- **Cabeceras Requeridas:** X-CSRF-Token, Idempotency-Key.

- **Request Body (VaultRevealRequest):**


\{


  "totp\_code": "839201",


  "reason": "Revisión de emergencia por mantenimiento en sitio"


\}


- **Proceso:**

  1. Verifica el código 2FA TOTP en vivo del administrador.

  2. Escribe de manera inmutable en audit\_logs el evento CREDENTIAL\_REVEALED incluyendo reason, actor\_ip y router\_id.

  3. Desencripta current\_password y previous\_password (si existe) usando AES-256-GCM con AAD = f"\{tenant\_id\}:\{router\_id\}".

- **Response 200 OK (Con cabecera Cache-Control: no-store):**


\{


  "router\_id": "01928900-aaaa-7bbb-8ccc-111122223333",


  "api\_username": "rosgrid\_api\_admin",


  "current\_password": "rG9\#mK2$vP8!xL4@qW7&zN1\*tB5^cF3\_",


  "previous\_password": "ClaveAnteriorAntesDeRotacion\#2026",


  "last\_rotated\_at": "2026-10-01T03:00:00Z",


  "next\_rotation\_due\_at": "2026-10-31T03:00:00Z",


  "display\_ttl\_seconds": 30


\}

### **3.2 POST /api/v1/inventory/routers/\{router\_id\}/vault/rotate-now — Rotación Automática de Contraseña API en el MikroTik**

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, INVENTORY\_MANAGER.

- **Algoritmo Seguro de Rotación sin Pérdida de Acceso:**

  1. Genera en memoria una nueva contraseña criptográfica de 32 caracteres (secrets.token\_urlsafe(24) + símbolos seguros sin comillas ni espacios que afecten scripts de RouterOS).

  2. Mueve la current\_password\_\* actual de la bóveda a las columnas previous\_password\_\* y guarda la nueva contraseña cifrada como current\_password\_\* dentro de una transacción pendiente.

  3. Se conecta al MikroTik usando la contraseña anterior y ejecuta PATCH /rest/user/\<api\_username\> con \{"password": "\<nueva\_clave\_32\_chars\>"\}.

  4. Realiza inmediatamente una petición de comprobación GET /rest/system/identity autenticándose con la **nueva contraseña**.

  5. Si responde 200 OK, hace COMMIT en PostgreSQL actualizando last\_rotated\_at = NOW() y registra CREDENTIAL\_AUTO\_ROTATED en audit\_logs.




## **4. Endpoints de Ventanas de Mantenimiento Programadas (/api/v1/maintenance/windows)**

| **Método** | **Ruta** | **Roles Permitidos** | **Descripción** |
| - | - | - | - |
| GET | /api/v1/maintenance/windows | Todos los roles | Lista ventanas activas, futuras e históricas del Tenant |
| POST | /api/v1/maintenance/windows | SUPERADMIN, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, INVENTORY\_MGR (SUPPORT\_L2 va a *Maker-Checker*) | Crea una ventana por router\_id o por target\_tag entre starts\_at y ends\_at |
| POST | /api/v1/maintenance/windows/\{window\_id\}/cancel | SUPERADMIN, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3 | Cancela anticipadamente una ventana y reactiva el envío de alertas en Redis |

