# 13 — ENDPOINTS BACKEND WEBFIG CAPA 1: FIREWALL COMPLETO, DRAG & DROP DE REGLAS Y ROUTING AVANZADO v7 (BGP / OSPF / BFD) (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los endpoints de la **Capa 1 WebFig** para **Firewall** (fastapi/src/api/v1/webfig\_firewall.py) y **Enrutamiento Dinámico RouterOS v7** (fastapi/src/api/v1/webfig\_routing.py). Incluye soporte nativo para reordenamiento de reglas (*Drag & Drop* en la UI de Vue 3), gestión rápida de listas de direcciones (Address-Lists) y monitoreo/configuración de sesiones BGP, OSPF, tablas de ruteo (VRF/ECMP) y BFD.




## **1. Módulo de Firewall IPv4 e IPv6 (/api/v1/routers/\{router\_id\}/webfig/firewall)**

En RouterOS v7, el orden de las reglas en Filter, NAT, Mangle y RAW es determinante para el procesamiento de paquetes. RoSGrid expone endpoints unificados parametrizados por table\_type (filter, nat, mangle, raw) y protocolo (ip o ipv6).

### **1.1 Tabla de Endpoints de Firewall**

| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /firewall/\{proto\}/\{table\_type\} | GET /rest/\{proto\}/firewall/\{table\_type\} | SUPPORT\_L1 | No | Lista todas las reglas en orden exacto de ejecución, incluyendo contadores de paquetes (packets) y bytes (bytes), chain, action, dynamic y disabled |
| POST | /firewall/\{proto\}/\{table\_type\} | PUT /rest/\{proto\}/firewall/\{table\_type\} | SUPPORT\_L2 *(Si chain == "input" exige SUPPORT\_L3 o Maker-Checker)* | **Sí** | Crea una nueva regla de Firewall (con opción place-before para insertarla en una posición específica) |
| PATCH | /firewall/\{proto\}/\{table\_type\}/\{rule\_id\} | PATCH /rest/\{proto\}/firewall/\{table\_type\}/\{rule\_id\} | SUPPORT\_L2 *(Si chain == "input" -\> SUPPORT\_L3 / Maker-Checker)* | **Sí** | Modifica parámetros de una regla o la habilita/deshabilita |
| DELETE | /firewall/\{proto\}/\{table\_type\}/\{rule\_id\} | DELETE /rest/\{proto\}/firewall/\{table\_type\}/\{rule\_id\} | SUPPORT\_L2 *(Si chain == "input" -\> SUPPORT\_L3 / Maker-Checker)* | **Sí** | Elimina una regla (usando deshabilitación preventiva durante Safe Mode) |
| POST | /firewall/\{proto\}/\{table\_type\}/move | POST /rest/\{proto\}/firewall/\{table\_type\}/move | SUPPORT\_L2 / SUPPORT\_L3 | **Sí** | **Reordenamiento Drag & Drop:** Mueve una o varias reglas (numbers) antes de la regla destino (destination) |
| POST | /firewall/\{proto\}/\{table\_type\}/reset-counters | POST /rest/\{proto\}/firewall/\{table\_type\}/reset-counters-all | SUPPORT\_L2 | No | Reinicia a cero los contadores de bytes/paquetes de las reglas |
| GET | /firewall/\{proto\}/address-lists | GET /rest/\{proto\}/firewall/address-list | SUPPORT\_L1 | No | Lista entradas de address-list (filtrable por ?list=morosos o ?address=10.20.30.40) |
| POST | /firewall/\{proto\}/address-lists | PUT /rest/\{proto\}/firewall/address-list | SUPPORT\_L1 / SUPPORT\_L2 | **Sí** *(si la lista está referenciada en cadena input)* | Agrega una IP, rango o prefijo CIDR a un address-list con timeout opcional (ej. "24h") y comment |
| DELETE | /firewall/\{proto\}/address-lists/\{item\_id\} | DELETE /rest/\{proto\}/firewall/address-list/\{item\_id\} | SUPPORT\_L1 / SUPPORT\_L2 | **Sí** | Elimina una entrada de un address-list |
| GET | /firewall/connections | GET /rest/ip/firewall/connection | SUPPORT\_L1 | No | Consulta tabla de Connection Tracking (limitada a top 500 con filtros por src-address, dst-address, protocol, tcp-state) |
| DELETE | /firewall/connections/\{conn\_id\} | DELETE /rest/ip/firewall/connection/\{conn\_id\} | SUPPORT\_L1 | No | Cierra/elimina una conexión activa específica de la tabla de estado |

### **1.2 Contrato para Reordenamiento *Drag & Drop* (POST .../firewall/\{proto\}/\{table\_type\}/move)**

- **Request Body (FirewallRuleMoveRequest):**


\{


  "numbers": "\*1C",


  "destination": "\*14"


\}


- **Protección Safe Mode en move:**

  - Antes de mover una regla encima de otra, el motor de Safe Mode guarda la secuencia actual de IDs de esa cadena y programa el comando inverso /ip/firewall/filter/move numbers=\*1C destination=\*1D en el /system/scheduler por 60 segundos. Si mover una regla drop arriba corta el acceso de RoSGrid al MikroTik, el router restaura automáticamente la posición original de la regla.




## **2. Módulo de Enrutamiento Avanzado RouterOS v7 (/api/v1/routers/\{router\_id\}/webfig/routing)**

En RouterOS v7, toda la pila de enrutamiento dinámico fue rediseñada bajo /routing/bgp, /routing/ospf, /routing/table, /routing/rule, /routing/bfd y /routing/filter.

### **2.1 Tabla de Endpoints de Routing v7**

| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /routing/tables | GET /rest/routing/table | SUPPORT\_L1 | No | Lista tablas de enrutamiento (main, tablas FIB adicionales para balanceo ECMP/PBR y VRFs) |
| POST | /routing/tables | PUT /rest/routing/table | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Crea una nueva tabla de ruteo con flag fib |
| GET | /routing/rules | GET /rest/routing/rule | SUPPORT\_L1 | No | Lista reglas de Policy Routing (src-address, dst-address, routing-mark, action, table) |
| POST | /routing/rules | PUT /rest/routing/rule | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Crea una regla de selección de tabla de enrutamiento |
| GET | /routing/bgp/templates | GET /rest/routing/bgp/template | SUPPORT\_L1 | No | Lista plantillas BGP (as, router-id, address-families, output.network, output.filter-chain) |
| GET | /routing/bgp/connections | GET /rest/routing/bgp/connection | SUPPORT\_L1 | No | Lista conexiones de peering BGP configuradas (remote.address, remote.as, local.role, templates) |
| POST | /routing/bgp/connections | PUT /rest/routing/bgp/connection | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Crea una nueva sesión BGP en RouterOS v7 |
| PATCH | /routing/bgp/connections/\{item\_id\} | PATCH /rest/routing/bgp/connection/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica o habilita/deshabilita un peer BGP |
| DELETE | /routing/bgp/connections/\{item\_id\} | DELETE /rest/routing/bgp/connection/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Elimina una conexión BGP |
| GET | /routing/bgp/sessions | GET /rest/routing/bgp/session | SUPPORT\_L1 | No | **Estado BGP en Vivo:** Devuelve sesiones establecidas (established, uptime, prefix-count, remote.address, remote.as, ebgp) |
| GET | /routing/bgp/advertisements | GET /rest/routing/bgp/advertisements | SUPPORT\_L1 | No | Lista prefijos anunciados en vivo a cada peer BGP (dst, nexthop, as-path, origin) |
| GET | /routing/ospf/instances | GET /rest/routing/ospf/instance | SUPPORT\_L1 | No | Lista instancias OSPF v2/v3 (version, router-id, redistribute) |
| GET | /routing/ospf/areas | GET /rest/routing/ospf/area | SUPPORT\_L1 | No | Lista áreas OSPF (area-id, instance, type) |
| GET | /routing/ospf/interface-templates | GET /rest/routing/ospf/interface-template | SUPPORT\_L1 | No | Lista plantillas de interfaz OSPF (interfaces, area, type, cost, priority) |
| GET | /routing/ospf/neighbors | GET /rest/routing/ospf/neighbor | SUPPORT\_L1 | No | **Adyacencias OSPF en Vivo:** Estado (Full, 2-Way, Init), router-id, address, adjacency |
| GET | /routing/bfd/sessions | GET /rest/routing/bfd/session | SUPPORT\_L1 | No | Lista estado de sesiones BFD de detección rápida de caída de enlace (state, uptime, remote-address) |
| GET | /routing/filters/rules | GET /rest/routing/filter/rule | SUPPORT\_L1 | No | Lista reglas de filtros de enrutamiento de RouterOS v7 (chain, rule, disabled) |
| POST | /routing/filters/rules | PUT /rest/routing/filter/rule | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Crea regla de filtro de prefijos (if (dst in 10.0.0.0/8) \{ accept \}) |
| PATCH | /routing/filters/rules/\{item\_id\} | PATCH /rest/routing/filter/rule/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica regla de filtro de enrutamiento |




## **3. Esquema Pydantic de Resumen de Salud BGP (BgpPeerStatusSummary)**

Para facilitar la visualización tanto en la vista de Routing como en el panel de **Supervisión / NOC**, el endpoint GET /routing/bgp/sessions normaliza la salida de RouterOS v7:


\{


  "total\_configured\_connections": 4,


  "established\_sessions\_count": 4,


  "sessions": \[


    \{


      "id": "\*3000001",


      "name": "ISP-Upstream-1-v4",


      "remote\_address": "186.10.20.1",


      "remote\_as": 65001,


      "local\_as": 65500,


      "established": true,


      "uptime": "4w2d11h05m",


      "prefix\_count": 945120,


      "hold\_time": "1m30s",


      "keepalive\_time": "30s"


    \}


  \]


\}
