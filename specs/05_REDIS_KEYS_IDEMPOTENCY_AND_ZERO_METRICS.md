# 05 — ARQUITECTURA DE REDIS 7: IDEMPOTENCIA, SESIONES KILL-SWITCH, PUB/SUB Y MONITOR CERO-MÉTRICAS (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica el catálogo completo de llaves, estructuras de datos, scripts Lua atómicos y tiempos de expiración (TTL) en **Redis 7** (redis.asyncio). Redis cumple 5 funciones críticas en **RoSGrid**: Idempotencia de peticiones mutables, gestión de sesiones y *Kill-Switch* en tiempo real, caché efímero de lecturas REST de RouterOS, multiplexación Pub/Sub para gráficas en vivo estilo WinBox y máquina de estados *Zero-Storage* para monitoreo y alertas sin guardar métricas en PostgreSQL.




## **1. Mapa General de Espacios de Nombres (Key Namespaces)**

Toda llave en Redis DEBE incluir el prefijo rg: seguido del tenant\_id (para aislamiento criptográfico y lógico entre empresas):


| **Dominio** | **Patrón de Llave Redis** | **Tipo de Dato** | **TTL Exacto** | **Propósito** |
| - | - | - | - | - |
| **Lock Migración** | rg:global:migration\_lock | STRING | 120s | Respaldo secundario al pg\_advisory\_lock durante el arranque |
| **Pre-Auth 2FA** | rg:\{tenant\_id\}:preauth:\{challenge\_id\} | HASH | 180s (3 min) | Estado temporal entre validación de contraseña y código TOTP 2FA |
| **Step-Up Vault** | rg:\{tenant\_id\}:stepup:\{user\_id\}:\{router\_id\} | STRING | 30s | Token efímero tras validar 2FA para revelar clave de bóveda |
| **Sesión Activa** | rg:\{tenant\_id\}:sess:\{session\_id\} | HASH | 28800s (8 h) | Metadatos de sesión en vivo (IP, User-Agent, router actual, rol) |
| **Índice Usuario** | rg:\{tenant\_id\}:user\_sessions:\{user\_id\} | SET | 28800s (8 h) | Lista de session\_id activos de un técnico para el *Kill-Switch* |
| **Índice Tenant** | rg:\{tenant\_id\}:active\_sessions | ZSET | Sin expiración fija | Score = timestamp última actividad; lista todas las sesiones en vivo |
| **Refresh Family** | rg:\{tenant\_id\}:rt\_family:\{family\_id\} | HASH | 28800s (8 h) | Hash del Refresh Token vigente para detección de robo (Reuse Detection) |
| **Idempotencia** | rg:\{tenant\_id\}:idemp:\{user\_id\}:\{idemp\_key\} | HASH | 86400s (24 h) | Bloqueo IN\_PROGRESS y caché de respuesta de órdenes mutables |
| **Caché Lectura** | rg:\{tenant\_id\}:rcache:\{router\_id\}:\{endpoint\_hash\} | STRING | 3s a 15s | Caché ultracorto de lecturas /rest/\* para evitar saturar el MikroTik |
| **Suscriptores WS** | rg:\{tenant\_id\}:ws\_subs:\{router\_id\} | SET | 60s (renovable) | IDs de conexiones WebSocket viendo un router (activa/apaga el poller) |
| **Canal Pub/Sub** | rg:pubsub:telemetry:\{tenant\_id\}:\{router\_id\} | PUBSUB | Volátil | Difusión en memoria de puntos de CPU/RAM/Tráfico hacia navegadores |
| **Canal Eventos** | rg:pubsub:events:\{tenant\_id\} | PUBSUB | Volátil | Eventos críticos para Wallboard NOC y orden de expulsión *Kill-Switch* |
| **Estado Monitor** | rg:\{tenant\_id\}:mon\_state:\{router\_id\} | HASH | 600s (10 min) | Máquina de estados *Zero-Storage* (~200 bytes) para disparar alertas |
| **Safe Mode Watch** | rg:\{tenant\_id\}:safemode:\{router\_id\}:\{op\_id\} | HASH | 120s | Seguimiento de confirmación del *Dead Man's Switch* en el MikroTik |




## **2. Especificación del Middleware de Idempotencia (fastapi/src/redis\_layer/idempotency.py)**

Toda petición mutable (POST, PUT, PATCH, DELETE) enviada desde Vue 3 hacia endpoints que modifican la base de datos o un equipo MikroTik DEBE incluir la cabecera Idempotency-Key con un UUIDv7 válido.

### **2.1 Flujo Atómico de Idempotencia y Aislamiento Multi-Tenant**

1. **Validación de Formato:** Si falta la cabecera `Idempotency-Key` o no es un UUID válido en una ruta mutable protegida, FastAPI responde inmediatamente HTTP 400 Bad Request (`{"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"}`).

2. **Resolución Segura de Actores Multi-Tenant:**
   - Para evitar colisiones entre diferentes inquilinos u operadores que puedan generar o reutilizar un mismo identificador, el middleware extrae de forma autónoma `tenant_id` y `user_id` decodificando el JWT presente en la cookie de sesión (`__Host-rg_at` / `rg_at`) o la cabecera `Authorization: Bearer`.
   - Si la petición es anónima o previa a autenticación, se utiliza un espacio de nombres aislado `anonymous`.

3. **Huella del Payload (request_hash):** Se calcula el SHA-256 de `f"{request.method}:{request.url.path}:{raw_body_bytes}"`.

4. **Adquisición Atómica en Redis:**
   - Llave canónica: `rg:{tenant_id}:{user_id}:idemp:{idempotency_key}`
   - Si la llave **no existe**, se crea atómicamente con estado `status = "IN_PROGRESS"`, `request_hash = <sha256>`, y `EXPIRE 60` segundos mientras se ejecuta la operación en el MikroTik.
   - Si la llave **ya existe** y su `request_hash` **no coincide** con el de la nueva petición, devuelve HTTP 422 Unprocessable Entity (`{"detail": "Conflicto de Idempotency-Key: la llave ya fue utilizada con un payload diferente"}`).
   - Si la llave **ya existe** con `status = "IN_PROGRESS"`, devuelve HTTP 409 Conflict (`{"detail": "La operación con esta Idempotency-Key ya se encuentra en ejecución en el router"}`).
   - Si la llave **ya existe** con `status = "COMPLETED"`, FastAPI devuelve exactamente el mismo `status_code` y `response_json` almacenado, añadiendo la cabecera `X-Idempotent-Replay: true`, **sin volver a tocar el MikroTik ni PostgreSQL**.

5. **Finalización:** Al completarse la operación con código 2xx (o 202 Accepted si fue a Maker-Checker), se actualiza el Hash en Redis con `status = "COMPLETED"`, `status_code`, `response_json` y se ajusta el TTL a 86400 segundos (24 horas). Si ocurre un error de red transitorio 502/504, se elimina la llave en Redis para permitir que el operador reintente limpiamente.




## **3. Control de Sesiones Activas y *Kill-Switch* en Tiempo Real**

Para que el **Administrador de Tenant** y el **Supervisor** vean en vivo qué técnicos están dentro de RoSGrid y puedan expulsarlos instantáneamente:

### **3.1 Estructura del Hash de Sesión (rg:\{tenant\_id\}:sess:\{session\_id\})**

\{


  "session\_id": "01928b4c-...",


  "user\_id": "01928a10-...",


  "username": "jperez",


  "full\_name": "Jose Perez",


  "role": "SUPPORT\_L2",


  "ip\_address": "192.168.10.45",


  "user\_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86\_64)...",


  "current\_router\_id": "01928900-...",


  "current\_router\_name": "RB4011-Borde-Norte",


  "current\_view\_path": "/routers/01928900-.../firewall/filter",


  "created\_at": "2026-10-14T18:00:00Z",


  "last\_activity\_at": "2026-10-14T18:10:42Z",


  "refresh\_family\_id": "fam\_981723..."


\}

### **3.2 Ejecución del *Kill-Switch* (Revocación Inmediata)**

Cuando un Supervisor o Admin pulsa **"Cerrar Sesión Forzosamente"** sobre un session\_id o user\_id:


1. FastAPI elimina en una transacción pipeline de Redis:

   - DEL rg:\{tenant\_id\}:sess:\{session\_id\}

   - DEL rg:\{tenant\_id\}:rt\_family:\{refresh\_family\_id\}

   - SREM rg:\{tenant\_id\}:user\_sessions:\{user\_id\} \{session\_id\}

   - ZREM rg:\{tenant\_id\}:active\_sessions \{session\_id\}

2. FastAPI publica un mensaje en el canal Pub/Sub rg:pubsub:events:\{tenant\_id\}:


\{


  "event": "SESSION\_KILLED",


  "target\_session\_id": "01928b4c-...",


  "target\_user\_id": "01928a10-...",


  "reason": "Sesión revocada manualmente por el Supervisor",


  "killed\_by": "supervisor\_admin"


\}


3. El gestor de WebSockets de FastAPI escucha ese evento, cierra en el acto con código 4401 (Session Revoked) todos los WebSockets asociados a ese session\_id, y el interceptor de Vue 3 limpia la memoria de la pestaña y redirige al usuario a /login?reason=session\_revoked.




## **4. Multiplexor WebSocket para Gráficas Efímeras Estilo WinBox (Cero Base de Datos)**

Para cumplir la regla de **no almacenar métricas históricas** y permitir que las gráficas funcionen exactamente igual que WinBox (se alimentan mientras tienes la ventana abierta y se resetean si sales):


1. **Registro de Observadores Activos:**

   - Cuando un técnico entra a la vista de un MikroTik (router\_id), su navegador abre el WebSocket /ws/v1/routers/\{router\_id\}/live-telemetry.

   - El servidor añade el identificador de conexión al conjunto rg:\{tenant\_id\}:ws\_subs:\{router\_id\}.

2. **Activación Bajo Demanda del Poller Efímero:**

   - Si el tamaño del conjunto (SCARD) pasa de 0 a 1, se inicia una corrutina asíncrona ligera que consulta cada **2 segundos** en lote /rest/system/resource, /rest/system/health y /rest/interface del MikroTik.

   - Si hay 5 técnicos viendo el mismo router simultáneamente (SCARD == 5), FastAPI sigue haciendo **1 sola consulta cada 2 segundos** al MikroTik y publica el frame JSON en el canal Redis Pub/Sub rg:pubsub:telemetry:\{tenant\_id\}:\{router\_id\}.

3. **Apagado Instantáneo al Cerrar la Pestaña:**

   - Cuando un técnico cierra la pestaña o cambia de pantalla, el servidor ejecuta SREM.

   - En el instante en que SCARD rg:\{tenant\_id\}:ws\_subs:\{router\_id\} llega a 0, la corrutina se detiene inmediatamente. **Ningún dato de esa gráfica queda escrito en PostgreSQL ni en Redis.**




## **5. Máquina de Estados *Zero-Storage* para Monitoreo y Alertas en Segundo Plano**

Para detectar caídas de routers, uso crítico de CPU/RAM o cambios no autorizados de certificado SSL sin guardar series de tiempo:

### **5.1 Estructura del Hash Ultraligero (rg:\{tenant\_id\}:mon\_state:\{router\_id\})**

Cada router en estado administrativo PRODUCTION tiene **un único Hash en Redis** (~200 bytes) que se sobrescribe en cada ciclo del worker (cada 30 segundos):


\{


  "operational\_status": "ONLINE",          // ONLINE | DEGRADED\_HIGH\_LOAD | OFFLINE | SSL\_MISMATCH


  "consecutive\_failures": "0",             // Entero: al llegar a 3 pasa a OFFLINE y dispara alerta


  "consecutive\_high\_cpu": "0",             // Entero: si CPU \>= 90% por 4 ciclos seguidos dispara alerta


  "last\_cpu\_load\_pct": "18",               // Solo el último valor instantáneo para pintar el pin en el mapa NOC


  "last\_free\_memory\_pct": "74",            // Solo el último valor instantáneo para el Wallboard NOC


  "in\_maintenance\_window": "false",        // true si hay ventana activa en maintenance\_windows


  "last\_state\_change\_epoch": "1791998400", // Timestamp del último cambio de estado


  "last\_check\_epoch": "1792001200"         // Timestamp del chequeo recién ejecutado


\}

### **5.2 Regla de Disparo por Transición de Estado (Edge-Triggered Alerts)**

- El worker compara el prev\_status (leído del Hash en Redis) con el new\_status resultante del chequeo actual:

  - **ONLINE -\> OFFLINE (tras 3 fallos consecutivos):** Si in\_maintenance\_window == "false", emite evento ROUTER\_DOWN hacia Telegram, SMTP, Webhook y el canal Pub/Sub del Wallboard NOC.

  - **OFFLINE -\> ONLINE:** Emite evento de recuperación ROUTER\_UP con el cálculo de cuántos minutos estuvo inalcanzable (now - last\_state\_change\_epoch).

  - **ONLINE -\> DEGRADED\_HIGH\_LOAD (CPU \>= 90% en 4 ciclos consecutivos):** Emite alerta HIGH\_CPU.

  - **ANY -\> SSL\_MISMATCH:** Emite alerta de seguridad crítica inmediata SSL\_MISMATCH indicando que la huella SHA-256 del certificado autofirmado del MikroTik no coincide con la registrada en TOFU.
