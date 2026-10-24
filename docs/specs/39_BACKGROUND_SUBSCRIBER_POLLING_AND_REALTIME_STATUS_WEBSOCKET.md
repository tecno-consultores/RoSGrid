# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# 📑 Especificación 39: Sondeo Pasivo Escalonado de Fondo (Worker Jitter) y Notificación Reactiva WebSocket en Tiempo Real — RoSGrid

**Estado:** Aprobado para Implementación (Hito 23.26)  
**Licencia:** GPL-3.0-only  
**Estándar Aplicado:** QA Testing Blueprints (Nivel 11X) — Ephemeral Docker & Event-Driven Realtime

---

## 1. Contexto Operativo y Diagnóstico del Problema

En redes de telecomunicaciones e infraestructuras corporativas medianas y grandes (de 50 a 500 routers MikroTik y miles de dispositivos/clientes conectados), la monitorización visual continua de salud en el mapa cartográfico (`UnifiedNetworkMap.vue`) y en el Wallboard NOC plantea un desafío crítico de rendimiento y contención:

1. **El Riesgo del Polling Activo Masivo (Prohibido):**
   - Ejecutar pruebas activas (Ping ICMP o sondeos HTTP individuales) contra miles de clientes satura los enlaces de radio/fibra, inunda las colas de hardware en MikroTik y colapsa los workers asíncronos de RoSGrid por agotamiento de sockets.
2. **La Limitación del Refresco Manual:**
   - La sincronización pasiva implementada en el Hito 23.24 mediante la lectura de `/ip/dhcp-server/lease` y `/ppp/active` erradicó el tráfico ICMP hacia los clientes al consultar el estado directamente de la memoria del kernel de RouterOS en una única llamada compacta.
   - Sin embargo, esta sincronización depende actualmente de que el operador pulse manualmente `[ 🔄 Sincronizar DHCP ]` o abra la vista, lo que introduce latencia operativa si nadie interactúa con la pantalla.
3. **El Riesgo del Polling Simultáneo Ciego (*Thundering Herd*):**
   - Si un proceso de fondo en el worker consulta a todos los routers de la flota exactamente al mismo segundo (ejemplo: cron fijo a las `XX:00`), se genera un pico instantáneo de consumo de CPU en la flota MikroTik y en la base de datos PostgreSQL.
4. **El Riesgo del Polling HTTP desde el Navegador:**
   - Si el frontend ejecutara un `setInterval` cada 5 o 10 segundos para recargar la lista de miles de clientes mediante `GET /api/v1/subscribers`, saturaría la red del NOC y el servidor web con transferencias redundantes de datos idénticos.

---

## 2. Arquitectura de la Solución: Doble Vía Pasiva Escalonada y WebSocket

Para garantizar que el mapa de red y el Wallboard NOC reflejen el estado de salud de toda la flota en tiempo real con **cero saturación**, se establece un modelo de dos vías:

```
[ MikroTik RouterOS v7 ] ──(1. Lectura periódica pasiva)──> [ StaggeredSessionPoller (Worker) ]
         │                                                                   │
         │ (2. Syslog UDP 5514 instantáneo)                                 │ (3. Solo si hay cambio de estado)
         ▼                                                                   ▼
[ Syslog Collector UDP ] ─────────────────────────────────────────> [ KeyDB + PostgreSQL 17 ]
                                                                             │
                                                                             ▼ (4. Evento Pub/Sub)
                                                                 [ WebSocket Telemetry Hub ]
                                                                             │
                                                                             ▼ (5. DEVICE_STATUS_CHANGED)
                                                                [ UnifiedNetworkMap.vue (Navegador) ]
                                                                   (Mutación reactiva en RAM 60 FPS)
```

### Componente 1: Sondeo Pasivo Escalonado en Worker (`StaggeredSessionPoller`)

* **Ubicación:** `fastapi/src/workers/subscriber_status_poller.py` ejecutado dentro del ciclo de vida continuo del contenedor `rosgrid-worker`.
* **Frecuencia Base:** Cada `POLL_INTERVAL_SECONDS = 180` (3 minutos) por router.
* **Mecanismo de Escalonamiento con Jitter (*Inter-Router Jitter*):**
  - El worker obtiene la lista de routers activos del tenant.
  - Divide el intervalo total entre la cantidad de routers para calcular un espaciado dinámico:
    $$\Delta t = \max\left(2.0, \; \frac{\text{POLL\_INTERVAL\_SECONDS}}{\max(1, N_{\text{routers}})}\right) + \text{random\_jitter}(0.1, 0.5)$$
  - El worker procesa **un solo router a la vez**, asegurando que la carga sobre el pool de conexiones y sobre la CPU del host sea plana y constante (sin picos).
* **Inspección de Circuit Breaker y RCA Previo:**
  - Antes de intentar conectar al router, el worker verifica si el router está alcanzable (`is_reachable == true`) y si su Circuit Breaker está en estado `CLOSED`. Si está caído o en `CIRCUIT_OPEN`, se salta en $< 1\text{ ms}$ sin intentar conexiones de red.
* **Consulta Pasiva Compacta (1 Sola Llamada REST):**
  - **Modo Empresa:** Consulta `/ip/dhcp-server/lease` proyectando únicamente `status`, `address`, `mac-address`, `host-name`. Si `status in ('bound', 'active')`, el estado es `ONLINE`, de lo contrario `OFFLINE`.
  - **Modo ISP:** Consulta `/ppp/active` proyectando `name`, `address`, `uptime`. Si el usuario tiene sesión activa, el estado es `ONLINE`, de lo contrario `OFFLINE`.

### Componente 2: Optimizador de Escritura Cero (*Zero-Write DB Delta Filter*)

* **Regla Innegociable:** No se realizan escrituras en PostgreSQL ni emisiones a la red si el estado de reachability del dispositivo no ha cambiado.
* **Mapeo Delta:**
  - El worker contrasta el estado detectado (`nuevo_status`) con el valor registrado en base de datos (`dev.last_reachability_status`).
  - Si `nuevo_status == dev.last_reachability_status`: **Cero escrituras en PostgreSQL, cero eventos WebSocket.** Solo se actualiza un timestamp efímero en KeyDB (`last_seen`).
  - Si `nuevo_status != dev.last_reachability_status`:
    1. Actualiza `SubscriberDevice.last_reachability_status = nuevo_status` y `last_seen_at = now()`.
    2. Persiste en PostgreSQL con `await db.commit()`.
    3. Publica un mensaje compacto en el canal Redis/KeyDB: `rg:{tenant_id}:events:device_status`.

### Componente 3: Vía Rápida por Syslog UDP 5514 (*Fast Path*)

* El colector Syslog existente (`fastapi/src/workers/syslog_collector.py`) analiza eventos nativos de desconexión:
  - `pppoe,info: <user>: disconnected`
  - `dhcp,info: deassigned <ip>`
  - `interface,warning: <iface> link down`
* Al detectar un evento de desconexión o reconexión de un cliente conocido:
  - Actualiza inmediatamente el estado en base de datos y KeyDB sin esperar los 3 minutos del sondeo periódico.
  - Dispara el evento Pub/Sub de actualización inmediata.

### Componente 4: Emisión Reactiva por WebSocket hacia el Frontend

* **Canal WebSocket:** `/api/v1/ws/telemetry` o endpoint dedicado de eventos de dispositivos.
* **Carga Útil Compacta (*Payload* $< 120\text{ bytes}$):**
  ```json
  {
    "type": "DEVICE_STATUS_CHANGED",
    "device_id": "018f89e2-3b4a-7c91-bf10-0987654321ab",
    "status": "OFFLINE",
    "router_id": "018f89e2-1234-7a8b-9c0d-112233445566",
    "last_seen_at": "2026-10-24T20:40:15.123Z"
  }
  ```
* **Mutación Reactiva en Frontend ([UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue)):**
  - El componente mantiene la referencia de los dispositivos en un array reactivo (`subscribers`).
  - Al recibir el evento `DEVICE_STATUS_CHANGED`:
    1. Localiza el dispositivo en memoria en $O(1)$ o $O(N)$ mediante `id`.
    2. Actualiza `sub.last_reachability_status = event.status`.
    3. Leaflet actualiza únicamente el marcador del dispositivo afectado modificando el estilo CSS o clase (`--sub-color` a `#EF4444` o `#00F0FF`).
  - **Impacto en el Navegador:** Cero repintados masivos del mapa, cero peticiones HTTP de recarga, rendimiento continuo a 60 FPS.

---

## 3. Especificación de Endpoints y Estructura en KeyDB

### Llaves en KeyDB (Redis Layer)

| Clave | Tipo | TTL | Propósito |
| :--- | :--- | :--- | :--- |
| `rg:{tenant}:poller:last_run:{router_id}` | `STRING` | 600s | Timestamp Unix del último sondeo exitoso del router para evitar ejecuciones duplicadas en clusters de workers. |
| `rg:{tenant}:sub:status:{device_id}` | `STRING` | 86400s | Estado actual en RAM (`ONLINE` o `OFFLINE`) para resolución ultra-rápida. |
| `rg:{tenant}:channel:device_status` | `PUB/SUB` | N/A | Canal de distribución interna de eventos de cambio de estado hacia los WebSockets de FastAPI. |

### Configuración en Variables de Entorno (`fastapi/src/core/config.py`)

```python
# Frecuencia de sondeo pasivo escalonado en el worker (segundos)
ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS: int = 180

# Pausa mínima entre sondeos de routers en el mismo worker (jitter base)
ROSGRID_INTER_ROUTER_JITTER_MIN_SECONDS: float = 2.0
ROSGRID_INTER_ROUTER_JITTER_MAX_SECONDS: float = 5.0
```

---

## 4. Matriz de Cobertura y Aseguramiento QA 11X

Cualquier implementación de esta especificación debe superar estrictamente las siguientes compuertas en contenedores efímeros Docker (`Rule Zero`):

1. **Backend Unitario (`fastapi/tests/workers/test_subscriber_status_poller.unit.py`):**
   - Prueba de escalonamiento temporal (*inter-router jitter*).
   - Prueba de omisión inmediata si el router tiene Circuit Breaker abierto.
   - Prueba de filtro delta (*Zero-Write*): verificar que si el estado no cambia, no se ejecutan operaciones de escritura en la base de datos.
   - Prueba de publicación de evento en KeyDB Pub/Sub ante transición `ONLINE <-> OFFLINE`.
   - Cobertura $\ge 95\%$.
2. **Frontend Unitario (`vue3/src/components/network/UnifiedNetworkMap.unit.ts`):**
   - Prueba de recepción de mensaje WebSocket `DEVICE_STATUS_CHANGED`.
   - Verificación de que el marcador correspondiente conmuta su color y clase sin recrear la capa completa del mapa.
3. **Escenarios BDD en Karate Labs:**
   - **Karate API (`fastapi/test/api_test.feature` y réplica en `docs/examples/`):** Escenario 85 validando la respuesta del poller y la publicación de estados en KeyDB.
   - **Karate UI (`vue3/test/ui_business_flow.feature` y réplica en `docs/examples/`):** Escenario 36 validando la transición reactiva de color del marcador en el mapa unificado sin recargar la página.
4. **Linters y Tipado Estricto:**
   - 0 errores en `ruff check`, `mypy`, `vue-tsc --noEmit` y `eslint`.
