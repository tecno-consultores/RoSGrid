# 12 — ENDPOINTS BACKEND WEBFIG CAPA 1: INTERFACES, ÓPTICA SFP, VLAN, BRIDGE, WIREGUARD, WIFI E IP/IPv6 (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los endpoints especializados de la **Capa 1 WebFig** para la gestión de **Interfaces** (fastapi/src/api/v1/webfig\_interfaces.py) y **Pila IP/IPv6** (fastapi/src/api/v1/webfig\_ip.py). Toda operación mutable (POST, PUT, PATCH, DELETE) pasa obligatoriamente por:


1. Verificación de acceso RBAC y asignación de equipo (verify\_router\_access).

2. Evaluación de intercepción **Maker-Checker** (si la acción es crítica para el rol del operador, devuelve HTTP 202 Accepted).

3. Ejecución protegida con **Dead Man's Switch (Safe Mode)** vía /rest/system/scheduler cuando modifica interfaces troncales, VLANs, Bridges, IPs o rutas.

4. Registro de before\_state y after\_state en audit\_logs.




## **1. Prefijo Base y Reglas Comunes**

- **Prefijo Base:** /api/v1/routers/\{router\_id\}/webfig

- **Cabeceras Requeridas en Mutaciones:** X-CSRF-Token e Idempotency-Key (UUIDv7).

- **Caché Corto de Lectura en Redis:** Las peticiones GET admiten ?refresh=true para forzar consulta directa al MikroTik ignorando el caché de 5 segundos en rg:\{tenant\_id\}:rcache:\{router\_id\}:\{endpoint\_hash\}.




## **2. Módulo de Interfaces (/api/v1/routers/\{router\_id\}/webfig/interfaces)**

| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /interfaces | GET /rest/interface | SUPPORT\_L1 / FIELD\_TECH | No | Lista todas las interfaces con estado (running, disabled, mtu, mac-address, rx-byte, tx-byte) |
| PATCH | /interfaces/\{item\_id\} | PATCH /rest/interface/\{item\_id\} | SUPPORT\_L2 *(Crítica si es WAN/Trunk -\> Maker-Checker)* | **Sí** | Modifica comentario, MTU, estado disabled o nombre de interfaz |
| GET | /interfaces/ethernet | GET /rest/interface/ethernet | SUPPORT\_L1 / FIELD\_TECH | No | Lista puertos físicos Ethernet, velocidad negociada, auto-negotiation y PoE |
| POST | /interfaces/ethernet/\{item\_id\}/sfp-monitor | POST /rest/interface/ethernet/monitor (\{"numbers": item\_id, "once": true\}) | SUPPORT\_L1 / FIELD\_TECH | No | **Diagnóstico Óptico SFP/SFP+ DDM:** Devuelve potencia óptica sfp-tx-power (dBm), sfp-rx-power (dBm), temperatura del transceptor, voltaje, fabricante y longitud de onda |
| POST | /interfaces/ethernet/\{item\_id\}/cable-test | POST /rest/interface/ethernet/cable-test (\{"numbers": item\_id, "once": true\}) | SUPPORT\_L1 / FIELD\_TECH | No | Ejecuta prueba TDR de pares de cobre (estado abierto/corto y distancia en metros) |
| GET | /interfaces/vlan | GET /rest/interface/vlan | SUPPORT\_L1 | No | Lista subinterfaces 802.1Q / 802.1ad (vlan-id, interface, mtu, arp) |
| POST | /interfaces/vlan | PUT /rest/interface/vlan | SUPPORT\_L2 | **Sí** | Crea una nueva VLAN validando vlan\_id entre 1 y 4094 |
| PATCH | /interfaces/vlan/\{item\_id\} | PATCH /rest/interface/vlan/\{item\_id\} | SUPPORT\_L2 | **Sí** | Modifica parámetros de una VLAN existente |
| DELETE | /interfaces/vlan/\{item\_id\} | DELETE /rest/interface/vlan/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Elimina una VLAN (deshabilitación preventiva en Safe Mode) |
| GET | /interfaces/bridge | GET /rest/interface/bridge | SUPPORT\_L1 | No | Lista Bridges, STP/RSTP/MSTP y estado de vlan-filtering |
| POST | /interfaces/bridge | PUT /rest/interface/bridge | SUPPORT\_L2 | **Sí** | Crea un nuevo Bridge |
| PATCH | /interfaces/bridge/\{item\_id\} | PATCH /rest/interface/bridge/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica Bridge (ej. activar vlan-filtering exige Safe Mode obligatorio) |
| GET | /interfaces/bridge/ports | GET /rest/interface/bridge/port | SUPPORT\_L1 / FIELD\_TECH | No | Lista puertos miembros de cada Bridge, pvid, frame-types y hw offload |
| POST | /interfaces/bridge/ports | PUT /rest/interface/bridge/port | SUPPORT\_L2 | **Sí** | Agrega un puerto a un Bridge |
| GET | /interfaces/bridge/vlans | GET /rest/interface/bridge/vlan | SUPPORT\_L1 | No | Lista tabla de VLANs del Bridge (tagged, untagged, vlan-ids) |
| GET | /interfaces/bridge/hosts | GET /rest/interface/bridge/host | SUPPORT\_L1 / FIELD\_TECH | No | Tabla FDB de MACs aprendidas por puerto en los Bridges |
| GET | /interfaces/wireguard | GET /rest/interface/wireguard | SUPPORT\_L1 | No | Lista interfaces WireGuard (listen-port, public-key, mtu) |
| POST | /interfaces/wireguard | PUT /rest/interface/wireguard | SUPPORT\_L2 | **Sí** | Crea interfaz túnel WireGuard |
| GET | /interfaces/wireguard/peers | GET /rest/interface/wireguard/peers | SUPPORT\_L1 | No | Lista Peers WireGuard (allowed-address, endpoint-address, last-handshake, rx, tx) |
| POST | /interfaces/wireguard/peers | PUT /rest/interface/wireguard/peers | SUPPORT\_L2 | **Sí** | Registra un nuevo Peer WireGuard |
| GET | /interfaces/wifi/registration-table | GET /rest/interface/wifi/registration-table *(fallback a /rest/interface/wireless/registration-table)* | SUPPORT\_L1 / FIELD\_TECH | No | Lista estaciones/clientes inalámbricos conectados, señal (signal), CCQ/SNR, velocidad TX/RX y uptime |

### **2.1 Esquema Pydantic Ejemplo: Respuesta de Diagnóstico Óptico SFP (SfpDiagnosticsResponse)**

\{


  "interface\_id": "\*2",


  "interface\_name": "sfp-sfpplus1",


  "status": "link-ok",


  "rate": "10Gbps",


  "full\_duplex": true,


  "sfp\_module\_present": true,


  "sfp\_vendor\_name": "MikroTik",


  "sfp\_part\_number": "S+31DLC10D",


  "sfp\_wavelength\_nm": 1310,


  "sfp\_temperature\_c": 42.0,


  "sfp\_supply\_voltage\_v": 3.31,


  "sfp\_tx\_bias\_ma": 18.5,


  "sfp\_tx\_power\_dbm": -3.12,


  "sfp\_rx\_power\_dbm": -6.45,


  "optical\_health": "OPTIMAL"


\}


*(El campo calculado optical\_health devuelve "OPTIMAL" si sfp\_rx\_power\_dbm \>= -20, "WARNING" entre -20 y -25, y "CRITICAL\_LOW\_LIGHT" si es \< -25 dBm).*

### **2.2 Esquemas Pydantic: Gestión de Bridges y Puertos Capa 2**

Los esquemas de validación estricta (`StrictBaseModel`, `extra='forbid'`) garantizan que los parámetros enviados desde el frontend cumplan estrictamente con las especificaciones de RouterOS v7:

- **BridgeCreateRequest (`fastapi/src/schemas/webfig_l1_net.py`):**
  ```json
  {
    "name": "bridge1",
    "protocol_mode": "rstp",
    "vlan_filtering": true,
    "mtu": 1500,
    "comment": "Bridge principal LAN con RSTP"
  }
  ```
  - `name`: Nombre de la interfaz bridge (1-64 caracteres, obligatorio).
  - `protocol_mode`: Modo del Spanning Tree Protocol (`rstp`, `stp`, `mstp`, `none`, opcional). Mapeado a `protocol-mode` en RouterOS v7.
  - `vlan_filtering`: Booleano (por defecto `false`), convertido a `"yes"` / `"no"` para RouterOS v7 REST API.
  - `mtu`: Tamaño máximo de unidad de transmisión (68-65535, opcional).
  - `comment`: Comentario de auditoría o descripción técnica.

- **BridgeUpdateRequest (`fastapi/src/schemas/webfig_l1_net.py`):**
  - Permite actualización parcial bajo Safe Mode de `name`, `protocol_mode`, `vlan_filtering`, `disabled`, `mtu` y `comment`.

- **BridgePortCreateRequest (`fastapi/src/schemas/webfig_l1_net.py`):**
  ```json
  {
    "bridge": "bridge1",
    "interface": "ether2",
    "pvid": 100,
    "hw": true,
    "frame_types": "admit-all",
    "ingress_filtering": true
  }
  ```
  - `ingress_filtering`: Booleano (por defecto `false`), convertido a `"yes"` / `"no"` en RouterOS v7 para descarte estricto de tramas no etiquetadas o ajenas a la PVID.

## **3. Módulo de Direccionamiento IP, ARP, Pools, DHCP, DNS y Servicios (/api/v1/routers/\{router\_id\}/webfig/ip)**

| **Método** | **Ruta en RoSGrid** | **Endpoint Equivalente en RouterOS v7** | **Rol Mínimo Directo** | **Safe Mode** | **Descripción** |
| - | - | - | - | :-: | - |
| GET | /ip/addresses | GET /rest/ip/address | SUPPORT\_L1 / FIELD\_TECH | No | Lista direcciones IPv4 configuradas (address, network, interface, dynamic, disabled) |
| POST | /ip/addresses | PUT /rest/ip/address | SUPPORT\_L2 | **Sí** | Asigna nueva dirección CIDR a una interfaz |
| PATCH | /ip/addresses/\{item\_id\} | PATCH /rest/ip/address/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica una IP existente (protegido por Safe Mode para evitar pérdida de gestión) |
| DELETE | /ip/addresses/\{item\_id\} | DELETE /rest/ip/address/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Elimina una dirección IP |
| GET | /ip/routes | GET /rest/ip/route | SUPPORT\_L1 | No | Lista tabla de enrutamiento IPv4 (dst-address, gateway, distance, routing-table, active, ecmp) |
| POST | /ip/routes | PUT /rest/ip/route | SUPPORT\_L2 *(Si dst-address == 0.0.0.0/0 exige SUPPORT\_L3 o Maker-Checker)* | **Sí** | Crea ruta estática o ruta balanceada ECMP |
| PATCH | /ip/routes/\{item\_id\} | PATCH /rest/ip/route/\{item\_id\} | SUPPORT\_L2 / SUPPORT\_L3 | **Sí** | Modifica ruta existente |
| DELETE | /ip/routes/\{item\_id\} | DELETE /rest/ip/route/\{item\_id\} | SUPPORT\_L2 / SUPPORT\_L3 | **Sí** | Elimina ruta |
| GET | /ip/arp | GET /rest/ip/arp | SUPPORT\_L1 / FIELD\_TECH | No | Lista tabla ARP (address, mac-address, interface, complete, dynamic, published) |
| POST | /ip/arp | PUT /rest/ip/arp | SUPPORT\_L2 | No | Crea amarre ARP estático (IP + MAC + Interface) |
| DELETE | /ip/arp/\{item\_id\} | DELETE /rest/ip/arp/\{item\_id\} | SUPPORT\_L1 | No | Limpia entrada ARP o elimina amarre estático |
| GET | /ip/pools | GET /rest/ip/pool | SUPPORT\_L1 | No | Lista pools de direcciones (name, ranges, next-pool) |
| POST | /ip/pools | PUT /rest/ip/pool | SUPPORT\_L2 | No | Crea un nuevo pool de IPs |
| GET | /ip/dhcp-server/leases | GET /rest/ip/dhcp-server/lease | SUPPORT\_L1 / FIELD\_TECH | No | Lista concesiones DHCP (address, mac-address, host-name, status, expires-after, dynamic, rate-limit) |
| POST | /ip/dhcp-server/leases/\{item\_id\}/make-static | POST /rest/ip/dhcp-server/lease/make-static (\{".id": item\_id\}) | SUPPORT\_L1 | No | Convierte un lease dinámico de cliente en reservación estática |
| PATCH | /ip/dhcp-server/leases/\{item\_id\} | PATCH /rest/ip/dhcp-server/lease/\{item\_id\} | SUPPORT\_L2 | No | Modifica IP fija, comentario, address-list o rate-limit de un lease estático |
| DELETE | /ip/dhcp-server/leases/\{item\_id\} | DELETE /rest/ip/dhcp-server/lease/\{item\_id\} | SUPPORT\_L1 | No | Libera/elimina un lease DHCP para forzar renovación |
| GET | /ip/dns | GET /rest/ip/dns + GET /rest/ip/dns/static | SUPPORT\_L1 | No | Obtiene servidores DNS configurados, estado de allow-remote-requests, tamaño de caché y registros estáticos |
| POST | /ip/dns/flush-cache | POST /rest/ip/dns/cache/flush | SUPPORT\_L1 | No | Vacía la caché DNS del MikroTik |
| GET | /ip/neighbors | GET /rest/ip/neighbor | SUPPORT\_L1 / FIELD\_TECH | No | Descubre equipos vecinos conectados por MNDP/CDP/LLDP (identity, address, mac-address, interface, version, board) |
| GET | /ip/services | GET /rest/ip/service | SUPPORT\_L1 | No | Lista servicios del propio router (www-ssl, winbox, ssh, api, api-ssl, telnet, ftp, www) con puerto y address permitida |
| PATCH | /ip/services/\{item\_id\} | PATCH /rest/ip/service/\{item\_id\} | SUPPORT\_L3 (L2 -\> *Maker-Checker*) | **Sí** | Modifica puerto, lista de IPs permitidas (address) o deshabilita servicios inseguros (prohibido deshabilitar www-ssl activo que usa RoSGrid sin confirmación expresa) |




## **4. Protección Especial Anti-Suicidio en /ip/services**

El servicio WebFigIpService en fastapi/src/services/webfig\_ip\_service.py DEBE incluir una regla preventiva inquebrantable (CC \<= 3):


- Si un usuario intenta enviar un PATCH a /ip/services/\{item\_id\} sobre el servicio www-ssl con disabled=true o cambiando el puerto port sin actualizar simultáneamente la configuración del router en RoSGrid, el backend rechaza la petición con HTTP 422 Unprocessable Entity (\{"detail": "Operación bloqueada: No puedes deshabilitar el servicio www-ssl a través del cual RoSGrid administra este MikroTik."\}).
