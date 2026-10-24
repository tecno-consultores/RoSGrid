# 14 — ENDPOINTS BACKEND WEBFIG CAPA 1: PPPoE / VPNs, QUEUES, SYSTEM Y HERRAMIENTAS DE DIAGNÓSTICO EN VIVO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los endpoints especializados de la **Capa 1 WebFig** para **PPP & VPN** (fastapi/src/api/v1/webfig\_ppp.py), **Queues** (fastapi/src/api/v1/webfig\_queues.py), **System** (fastapi/src/api/v1/webfig\_system.py) y **Tools de Diagnóstico en Vivo** (fastapi/src/api/v1/webfig\_tools.py).




## **1. Módulo PPPoE, Perfiles y VPNs (/api/v1/routers/\{router\_id\}/webfig/ppp)**

Si el ISP o empresa decide usar PPPoE o túneles L2TP/SSTP/OpenVPN/IPsec en un MikroTik, estos endpoints permiten configurarlo y operar las sesiones activas de forma centralizada:


| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /ppp/active | GET /rest/ppp/active | SUPPORT\_L1 / FIELD\_TECH | No | Lista sesiones PPPoE/VPN activas (name, service, caller-id, address, uptime, encoding) |
| DELETE | /ppp/active/\{session\_id\} | DELETE /rest/ppp/active/\{session\_id\} | SUPPORT\_L1 / FIELD\_TECH | No | **Reconexión Rápida L1:** Desconecta la sesión PPP activa para forzar la reconexión inmediata del CPE |
| GET | /ppp/secrets | GET /rest/ppp/secret | SUPPORT\_L1 | No | Lista cuentas PPP (name, service, profile, remote-address, last-logged-out, disabled) — **nunca** devuelve el campo de clave en texto plano a roles L1/L2 |
| POST | /ppp/secrets | PUT /rest/ppp/secret | SUPPORT\_L2 | No | Crea un nuevo secret PPPoE/VPN |
| PATCH | /ppp/secrets/\{item\_id\} | PATCH /rest/ppp/secret/\{item\_id\} | SUPPORT\_L2 (L1 solo puede cambiar profile o disabled si el Admin lo autoriza) | No | Modifica perfil de velocidad, IP remota o estado de un secret |
| DELETE | /ppp/secrets/\{item\_id\} | DELETE /rest/ppp/secret/\{item\_id\} | SUPPORT\_L2 | No | Elimina un secret PPP |
| GET | /ppp/profiles | GET /rest/ppp/profile | SUPPORT\_L1 | No | Lista perfiles PPP (name, local-address, remote-address, rate-limit, dns-server, address-list) |
| POST | /ppp/profiles | PUT /rest/ppp/profile | SUPPORT\_L2 | No | Crea un nuevo perfil de ancho de banda/configuración PPP |
| PATCH | /ppp/profiles/\{item\_id\} | PATCH /rest/ppp/profile/\{item\_id\} | SUPPORT\_L2 | No | Modifica un perfil PPP |
| GET | /ppp/pppoe-servers | GET /rest/interface/pppoe-server/server | SUPPORT\_L1 | No | Lista servidores concentradores PPPoE por interfaz (service-name, interface, default-profile, max-mtu) |
| POST | /ppp/pppoe-servers | PUT /rest/interface/pppoe-server/server | SUPPORT\_L2 | **Sí** | Crea un servidor PPPoE sobre una interfaz o VLAN |
| GET | /ppp/ipsec/active-peers | GET /rest/ip/ipsec/active-peers | SUPPORT\_L1 | No | Lista túneles IPsec activos (state, remote-address, uptime, rx-bytes, tx-bytes) |




## **2. Módulo de Control de Ancho de Banda — Queues (/api/v1/routers/\{router\_id\}/webfig/queues)**

| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /queues/simple | GET /rest/queue/simple | SUPPORT\_L1 | No | Lista Simple Queues (name, target, max-limit, limit-at, burst-limit, queue, packet-marks, bytes, rate) |
| POST | /queues/simple | PUT /rest/queue/simple | SUPPORT\_L2 | No | Crea una nueva Simple Queue |
| PATCH | /queues/simple/\{item\_id\} | PATCH /rest/queue/simple/\{item\_id\} | SUPPORT\_L2 | No | Modifica límites de velocidad (max-limit, ej. "100M/100M") o estado de la cola |
| DELETE | /queues/simple/\{item\_id\} | DELETE /rest/queue/simple/\{item\_id\} | SUPPORT\_L2 | No | Elimina una Simple Queue |
| POST | /queues/simple/move | POST /rest/queue/simple/move | SUPPORT\_L2 | No | Reordena la prioridad de evaluación de Simple Queues (*Drag & Drop*) |
| GET | /queues/tree | GET /rest/queue/tree | SUPPORT\_L1 | No | Lista árbol HTB de Queue Tree (name, parent, packet-mark, queue, max-limit, priority) |
| POST | /queues/tree | PUT /rest/queue/tree | SUPPORT\_L2 | No | Crea nodo en Queue Tree |
| PATCH | /queues/tree/\{item\_id\} | PATCH /rest/queue/tree/\{item\_id\} | SUPPORT\_L2 | No | Modifica nodo de Queue Tree |
| DELETE | /queues/tree/\{item\_id\} | DELETE /rest/queue/tree/\{item\_id\} | SUPPORT\_L2 | No | Elimina nodo de Queue Tree |
| GET | /queues/types | GET /rest/queue/type | SUPPORT\_L1 | No | Lista disciplinas de encolamiento (pcq, cake, fq-codel, sfq, pfifo) |




## **3. Módulo de Sistema, Recursos en Vivo y Usuarios del Router (/api/v1/routers/\{router\_id\}/webfig/system)**

**REGLA DE ORO (CERO BASE DE DATOS DE MÉTRICAS):** El endpoint /system/live-status consulta en tiempo real al MikroTik y devuelve la instantánea al navegador, pero **NO guarda** CPU, RAM, voltaje ni temperatura en PostgreSQL.


| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /system/live-status | GET /rest/system/resource + GET /rest/system/health + GET /rest/system/routerboard + GET /rest/system/clock | NOC\_MONITOR / SUPPORT\_L1 / Todos | No | Devuelve estado instantáneo de CPU, RAM libre/total, disco, uptime, temperatura (°C), voltaje (V), hora NTP y versión de RouterOS/RouterBOOT |
| PATCH | /system/identity | POST /rest/system/identity/set (\{"name": ...\}) | SUPPORT\_L2 | No | Cambia el identity interno del MikroTik y actualiza ros\_identity en el inventario de RoSGrid |
| GET | /system/users | GET /rest/user + GET /rest/user/active | SUPPORT\_L2 | No | Lista usuarios internos del MikroTik (name, group, address, last-logged-in) y sesiones activas de WinBox/SSH/WebFig/API en el propio router |
| POST | /system/users | PUT /rest/user | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Crea un usuario interno en el MikroTik |
| PATCH | /system/users/\{item\_id\} | PATCH /rest/user/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica grupo, IP permitida o clave de un usuario interno (protege que no se deshabilite el usuario API propio de RoSGrid) |
| GET | /system/scripts | GET /rest/system/script | SUPPORT\_L2 | No | Lista scripts almacenados en el router (name, owner, policy, run-count, source) |
| POST | /system/scripts | PUT /rest/system/script | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | No | Crea un script en el MikroTik |
| POST | /system/scripts/\{item\_id\}/run | POST /rest/system/script/run (\{".id": item\_id\}) | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Ejecuta un script existente dentro del MikroTik |
| GET | /system/scheduler | GET /rest/system/scheduler | SUPPORT\_L1 | No | Lista tareas programadas en el router (oculta de la edición manual los schedulers internos rosgrid-safemode-\*) |
| GET | /system/packages | GET /rest/system/package + POST /rest/system/package/update/check-for-updates | SUPPORT\_L1 | No | Lista paquetes instalados (routeros, bgp, wifi-qcom, container, etc.) y consulta si hay una nueva versión disponible en el canal (stable / long-term) |
| POST | /system/reboot | POST /rest/system/reboot | SUPPORT\_L3 (L1, L2, FIELD\_TECH -\> *Maker-Checker*) | N/A | Reinicia el MikroTik registrando el motivo obligatorio en audit\_logs |




## **4. Módulo de Herramientas y Diagnóstico en Vivo (/api/v1/routers/\{router\_id\}/webfig/tools)**

Diseñado para que **Soporte N1, N2, N3 y Técnicos de Campo** ejecuten diagnósticos desde el propio MikroTik sin necesitar WinBox ni SSH:

### **4.1 POST /api/v1/routers/\{router\_id\}/webfig/tools/ping — Ejecutar Ping desde el MikroTik**

- **Roles Permitidos:** SUPPORT\_L1, FIELD\_TECH, SUPPORT\_L2, SUPPORT\_L3, SUPERVISOR, TENANT\_ADMIN, SUPERADMIN\_GLOBAL.

- **Request Body (RouterPingRequest):**


\{


  "address": "8.8.8.8",


  "count": 5,


  "size": 64,


  "src\_address": null,


  "interface": null,


  "routing\_table": "main",


  "do\_not\_fragment": false


\}


- **Validación Estricta:** count limitado entre 1 y 20 por llamada HTTP para no bloquear workers (POST /rest/ping).

- **Response 200 OK:**


\{


  "target": "8.8.8.8",


  "sent": 5,


  "received": 5,


  "packet\_loss\_pct": 0,


  "min\_rtt\_ms": 12.4,


  "avg\_rtt\_ms": 13.1,


  "max\_rtt\_ms": 14.8,


  "results": \[


    \{"seq": 0, "host": "8.8.8.8", "size": 64, "ttl": 117, "time": "12ms400us", "status": "ok"\}


  \]


\}

### **4.2 POST /api/v1/routers/\{router\_id\}/webfig/tools/traceroute — Ejecutar Traceroute desde el MikroTik**

- Ejecuta POST /rest/tool/traceroute con count: 3, max-hops: 20 y timeout: "1s", devolviendo la lista ordenada de saltos (hop, address, loss, last, avg, best, worst).

### **4.3 POST /api/v1/routers/\{router\_id\}/webfig/tools/torch — Captura Corta de Tráfico (Torch por Interfaz)**

- Ejecuta POST /rest/tool/torch con duration: 3 segundos sobre la interfaz seleccionada (interface, src-address, dst-address, port, protocol) devolviendo el top de flujos de consumo en vivo (src-address, dst-address, ip-protocol, tx, rx, tx-packets, rx-packets).

### **4.4 GET /api/v1/routers/\{router\_id\}/webfig/tools/logs — Lectura del Log Interno del MikroTik**

- Consulta GET /rest/log con filtro por topics (ej. bgp, ospf, pppoe, firewall, system, error, critical) y búsqueda textual, devolviendo las últimas 250 líneas del buffer de memoria del router.
