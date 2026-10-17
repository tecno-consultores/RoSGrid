# 08 — CONECTOR REST ROUTEROS v7+, PINNING SSL AUTOFIRMADO (TOFU) Y MOTOR SAFE MODE ANTI-BLOQUEO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la arquitectura interna del paquete fastapi/src/mikrotik/, encargado de comunicarse con la **REST API nativa de RouterOS v7.1+ (\<api\_base\_url\>/rest/...)**. Incluye la verificación criptográfica de certificados SSL autofirmados mediante huella SHA-256 (**TOFU — Trust On First Use**) y el protocolo **Dead Man's Switch (Safe Mode)** usando /system/scheduler para revertir automáticamente cambios que dejen incomunicado al MikroTik.




## **1. Arquitectura Modular del Paquete fastapi/src/mikrotik/ (Complejidad Grado A)**

Para garantizar que radon cc --min C src/ arroje 0 alertas y el índice de mantenibilidad (radon mi) sea Grado A, el conector se divide en 4 módulos pequeños y desacoplados:


1. fastapi/src/mikrotik/ssl\_tofu.py — Extracción y verificación del fingerprint SHA-256 del certificado X.509 autofirmado del MikroTik.

2. fastapi/src/mikrotik/client.py — Cliente asíncrono httpx.AsyncClient con autenticación HTTP Basic desencriptada al vuelo desde la bóveda AES-256-GCM, reintentos controlados y normalización de errores de RouterOS.

3. fastapi/src/mikrotik/safemode.py — Motor de protección anti-bloqueo (*Dead Man's Switch*) que inyecta, verifica y limpia el /system/scheduler de reversión en el router.

4. fastapi/src/mikrotik/normalizers.py — Conversores puros de tipos de RouterOS (ej. conversión entre booleanos JSON "true"/"false" de RouterOS y tipos Python/Pydantic, y limpieza de comentarios de fecha en .rsc).




## **2. Verificación de Certificados SSL Autofirmados (TOFU SHA-256)**

Los routers MikroTik utilizan habitualmente certificados SSL autofirmados en el servicio www-ssl. Desactivar verify=False a ciegas en producción permitiría ataques *Man-in-the-Middle (MitM)* en los que un atacante intercepte la contraseña de la API REST. Por ello, RoSGrid implementa **TOFU (*Trust On First Use*) con Pinning SHA-256**:

### **2.1 Flujo de Conexión y Verificación (ssl\_tofu.py)**

1. **Contexto SSL Personalizado:**

   - Se crea un ssl.SSLContext(ssl.PROTOCOL\_TLS\_CLIENT) con check\_hostname = False y verify\_mode = ssl.CERT\_NONE (para permitir que el handshake TLS con el certificado autofirmado del MikroTik se complete y podamos inspeccionar el certificado binario DER del peer).

   - Se exige TLS 1.2 o TLS 1.3 (minimum\_version = ssl.TLSVersion.TLSv1\_2).

2. **Inspección del Certificado Peer (peercert\_der):**

   - Al establecer la conexión o mediante el stream de socket TLS de httpx/ssl, se obtiene der\_cert = ssl\_object.getpeercert(binary\_form=True).

   - Se calcula observed\_fp = hashlib.sha256(der\_cert).hexdigest().lower().

3. **Evaluación contra el Estado del Router en PostgreSQL:**

   - **Caso A (router.ssl\_trust\_status == 'PENDING\_TOFU'):**

     - Es la primera conexión al MikroTik (o el Administrador acaba de autorizar un *Re-Pin* explícito tras renovar el certificado).

     - RoSGrid guarda ssl\_sha256\_fingerprint = observed\_fp, ssl\_trust\_status = 'TRUSTED\_PINNED', ssl\_pinned\_at = NOW(), registra el evento ROUTER\_SSL\_TOFU\_PINNED en audit\_logs y continúa.

   - **Caso B (router.ssl\_trust\_status == 'TRUSTED\_PINNED' y observed\_fp == router.ssl\_sha256\_fingerprint):**

     - Huella idéntica. La conexión es auténtica y continúa normalmente.

   - **Caso C (observed\_fp != router.ssl\_sha256\_fingerprint):**

     - **BLOQUEO INMEDIATO:** El certificado del MikroTik cambió sin autorización o hay un ataque MitM en curso.

     - Se aborta la petición antes de procesar datos, se marca el router con ssl\_trust\_status = 'FINGERPRINT\_MISMATCH', se dispara la alerta crítica SSL\_MISMATCH a Telegram/SMTP/Webhook/NOC, se registra en audit\_logs y se lanza la excepción MikrotikSSLFingerprintMismatchError (HTTP 502 Bad Gateway con código SSL\_FINGERPRINT\_MISMATCH).

     - Un TENANT\_ADMIN o SUPERADMIN\_GLOBAL podrá revisar la nueva huella en la interfaz y, si fue un cambio legítimo de certificado en el router, autorizar el **Re-Pin SSL** con su código 2FA TOTP.




## **3. Especificación del Cliente REST RouterOS v7 (client.py)**

La REST API de RouterOS v7 mapea todos los menús de consola bajo \<api\_base\_url\>/rest/\<menu\>:


| **Operación en RoSGrid** | **Método HTTP hacia MikroTik** | **Ruta Ejemplo en RouterOS v7** | **Notas de Implementación** |
| - | - | - | - |
| **Listar registros** | GET | \<api\_base\_url\>/rest/ip/address | Soporta filtros query string: ?.proplist=.id,address,interface,disabled&disabled=false |
| **Leer un registro por ID** | GET | \<api\_base\_url\>/rest/ip/address/\*1 | Devuelve un objeto JSON con los atributos del ítem |
| **Crear un registro nuevo** | PUT | \<api\_base\_url\>/rest/ip/firewall/filter | En RouterOS v7 REST API, PUT crea un nuevo elemento y devuelve el objeto creado con su .id |
| **Modificar un registro existente** | PATCH | \<api\_base\_url\>/rest/ip/firewall/filter/\*1A | Modifica parcialmente solo las propiedades enviadas en el JSON |
| **Eliminar un registro** | DELETE | \<api\_base\_url\>/rest/ip/firewall/filter/\*1A | Devuelve 204 No Content |
| **Ejecutar comandos / acciones** | POST | \<api\_base\_url\>/rest/ping o /rest/ip/firewall/filter/move | En RouterOS v7 REST API, POST invoca cualquier método CLI (ej. print, move, reset-counters, check-for-updates) |

### **3.1 Manejo de Reintento con previous\_password durante Rotación**

Si al conectarse al MikroTik con current\_password (desencriptada de router\_credentials\_vault) el router responde HTTP 401 Unauthorized y existe previous\_password\_ciphertext con una rotación reciente (\< 5 minutos), el cliente intenta una única vez con previous\_password. Si tampoco autentica, lanza MikrotikAuthFailedError sin seguir reintentando (para no bloquear al usuario en el router).

### **3.2 Requerimiento Crítico de Políticas de Usuario en RouterOS v7.13+ (`rest-api`)**
A partir de MikroTik RouterOS v7.13+, MikroTik introdujo una política de seguridad explícita llamada `rest-api` para usuarios locales en `/user group`.
- Si el grupo asignado al usuario de RoSGrid carece del flag `rest-api`, RouterOS rechazará inmediatamente las peticiones HTTP con **HTTP 401 Unauthorized**, y en WinBox se observará que el usuario registra 0 conexiones.
- **Configuración requerida en RouterOS v7.13+:**
  ```routeros
  /user group add name=rosgrid-api-group policy=read,write,api,rest-api,test
  /user add name=rosgrid_agent group=rosgrid-api-group password="ClaveSegura"
  ```
- El cliente `fastapi/src/mikrotik/client.py` normaliza este error informando al operador la necesidad de habilitar la política `rest-api` en el grupo si recibe un 401 persistente.





## **4. Motor de Protección Anti-Bloqueo: *Dead Man's Switch (Safe Mode)* (safemode.py)**

Como la REST API de RouterOS v7 es HTTP sin estado (*stateless*), no mantiene una sesión TCP interactiva como WinBox. Si un técnico modifica por error una IP, una VLAN, una ruta o una regla de Firewall y corta la comunicación entre RoSGrid y el MikroTik, una API común dejaría el router huérfano en la torre o nodo remoto.


Para evitarlo al 100%, RoSGrid implementa el protocolo **Dead Man's Switch en 5 Pasos**:

### **Paso 1: Captura del Estado Previo (Snapshot) y Generación del Comando Inverso**

Antes de ejecutar una modificación (PATCH, PUT, DELETE o POST .../move) en un módulo sensible (Interfaces, IP Addresses, Routes, VLAN, Bridge, Firewall, Routing BGP/OSPF, Services):


1. FastAPI lee el estado actual del recurso en el MikroTik (GET /rest/\<path\>/\<id\>) y lo guarda en memoria (before\_state).

2. Construye el script RouterOS CLI exacto que restaura ese estado (rollback\_cli\_command):

   - *Ejemplo si se va a modificar una IP (\*4):* /ip/address/set \[find .id=\*4\] address="192.168.88.1/24" interface="bridgeLocal" disabled=no

   - *Ejemplo si se va a agregar una nueva regla de Firewall Input:* /ip/firewall/filter/remove \[find comment="rg-op-01928f11"\]

   - *Ejemplo si se va a eliminar un registro existente:* En lugar de hacer DELETE directo en el Paso 3, durante la ventana de Safe Mode primero lo **deshabilita** (PATCH \{"disabled": "true"\}), y solo cuando se confirma conectividad en el Paso 4 ejecuta el DELETE definitivo. Si el deshabilitarlo corta la conexión, el scheduler simplemente ejecuta set \[find .id=\*X\] disabled=no y el router revive sin haber perdido su posición ni su .id.

### **Paso 2: Inyección del /system/scheduler de Reversión en el MikroTik**

FastAPI crea un scheduler temporal dentro del propio MikroTik vía PUT /rest/system/scheduler:


\{


  "name": "rosgrid-safemode-01928f11",


  "start-time": "startup",


  "interval": "00:01:00",


  "comment": "ROSGRID\_DEADMAN\_SWITCH\_AUTO\_ROLLBACK",


  "on-event": ":do \{ \<rollback\_cli\_command\> \} on-error=\{\}; /system/scheduler/remove \[find name=\\"rosgrid-safemode-01928f11\\"\]"


\}


*(El intervalo se toma de tenant.default\_safemode\_seconds, por defecto 60s, y el script se auto-elimina tras revertir el cambio).*

### **Paso 3: Aplicación del Cambio Solicitado**

FastAPI envía la operación (PATCH, PUT o deshabilitación previa a DELETE) a la REST API del MikroTik.

### **Paso 4: Verificación Activa de Supervivencia y Limpieza (Commit)**

Inmediatamente después (con 3 reintentos espaciados cada 2 segundos si hay un micro-corte de reconexión ARP/STP):


1. FastAPI realiza una llamada de verificación GET /rest/system/identity al MikroTik.

2. **Si el MikroTik responde HTTP 200 OK:**

   - La red sigue viva y el cambio es seguro.

   - FastAPI elimina el scheduler temporal (DELETE /rest/system/scheduler/\<scheduler\_id\>).

   - Si la operación original era un DELETE que fue convertido preventivamente en disabled=true, ahora ejecuta el DELETE definitivo sobre el ítem ya inactivo.

   - Registra la operación exitosa en audit\_logs con before\_state y after\_state.

### **Paso 5: Autocuración Autónoma en Caso de Corte (Auto-Rollback)**

- **Si el cambio dejó incomunicado al MikroTik (Timeout / Connection Error en los 3 intentos):**

  - FastAPI **no puede** conectarse para borrar el scheduler.

  - Al cumplirse los **60 segundos**, el reloj interno del propio MikroTik dispara rosgrid-safemode-01928f11, revierte el cambio a su estado anterior, borra el scheduler temporal y el router recupera conectividad automáticamente.

  - FastAPI espera a que venza la ventana, verifica que el router volvió a estar en línea, registra el evento SAFEMODE\_AUTO\_ROLLBACK\_TRIGGERED en audit\_logs, notifica al NOC y devuelve al técnico en Vue 3 un mensaje claro: HTTP 409 Conflict — "El cambio aplicado interrumpió la conectividad con el MikroTik y fue revertido automáticamente por el Safe Mode de RoSGrid."
