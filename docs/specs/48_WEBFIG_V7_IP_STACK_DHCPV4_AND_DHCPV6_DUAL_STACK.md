# 48 — WEBFIG v7 CAPA 1: MÓDULO IP DEDICADO, DHCPv4 SERVER & CLIENT, PILA DUAL IPv6 Y DHCPv6-PD (RoSGrid)

**Autor:** RoSGrid Architecture Team & Antigravity AI Assistant  
**Fecha:** 26 de Octubre de 2026  
**Estado:** ESPECIFICACIÓN TÉCNICA OFICIAL (Hito 27 — Fases 2 y 3)  
**Ámbito:** `vue3/src/views/IpAddressesAndDhcpView.vue`, `vue3/src/views/Ipv6DualStackView.vue`, `fastapi/src/api/v1/webfig_ip.py`, `fastapi/src/api/v1/webfig_ipv6.py`

---

## 1. Justificación y Objetivos de las Fases 2 y 3

Proveer a los operadores de red de una interfaz centralizada y ergonómica para las tareas más frecuentes de Layer 3:
1. **Pila IPv4:** Asignación de direcciones IP (`/ip/address`), configuración de servidores DHCP con asistentes rápidos, gestión en vivo de concesiones (*DHCP Leases*) con botón de 1-clic "Make Static", clientes DHCP WAN, pools y DNS.
2. **Pila IPv6 (Dual-Stack Real):** Direccionamiento nativo IPv6 (`/ipv6/address`), soporte de DHCPv6 Client solicitando prefijos (Prefix Delegation) del upstream, DHCPv6 Server para delegar prefijos `/56` o `/64` a clientes, y tabla de vecinos descubiertos (NDP).

---

## 2. Vista Dedicada IPv4: `IpAddressesAndDhcpView.vue`

### 2.1 Estructura de Pestañas
1. **`[ Direcciones IP ]` (`/ip/address`):**
   - Tabla con columnas: `Dirección (CIDR)`, `Red (Network)`, `Interfaz`, `Comentario`, `Estado`.
   - Botón `[ + Asignar IP ]`: Modal con validación sintáctica de máscara de subred y selector de interfaz.
2. **`[ Servidor DHCP ]` (`/ip/dhcp-server`):**
   - **Pestaña Interna 1: Leases (Concesiones Activas):**
     - Tabla en tiempo real con `Dirección IP`, `Dirección MAC`, `Hostname del Cliente`, `Tiempo Restante`, `Estado` (`bound`, `waiting`).
     - Botón por fila: `[ 📌 Hacer Estática ]` (invoca `POST .../leases/{id}/make-static`).
     - Botón por fila: `[ 🚫 Bloquear Cliente ]` (inserta la IP en el address-list `BLOQUEADOS_DHCP`).
   - **Pestaña Interna 2: Servidores & Redes (`/ip/dhcp-server/network`):**
     - Subred, Gateway, Servidores DNS primario y secundario, Dominio, Servidores NTP.
     - Asistente **"DHCP Setup en 3 Pasos"**: Wizard guiado para crear Pool, Network y Server en una sola transacción.
3. **`[ Cliente DHCP ]` (`/ip/dhcp-client`):**
   - Tabla con interfaces WAN, estado de negociación (`bound`, `searching`, `renewing`), IP asignada por el proveedor y Gateway.
   - Botón `[ 🔄 Renovar Concesión (Renew) ]` y `[ ❌ Liberar (Release) ]`.
4. **`[ Pools de Direcciones ]` (`/ip/pool`):**
   - Creación y edición de rangos de direcciones (ej. `192.168.88.10-192.168.88.254`).
5. **`[ DNS y Caché ]` (`/ip/dns`):**
   - Servidores DNS Upstream, selector `Allow Remote Requests`, botón `[ 🧹 Vaciar Caché DNS ]` y tabla de registros DNS estáticos.
6. **`[ Tabla ARP ]` (`/ip/arp`):**
   - Inspección de IP vs. MAC aprendidas, con botón para convertir entradas dinámicas en estáticas (*Make Static*).

---

## 3. Vista Dedicada IPv6: `Ipv6DualStackView.vue`

### 3.1 Estructura de Pestañas
1. **`[ Direcciones IPv6 ]` (`/ipv6/address`):**
   - Tabla con `Prefijo / Dirección IPv6` (ej. `2001:db8:1000::1/64`), `Interfaz`, flags `[A]` (Advertise/SLAAC), `[G]` (Global), `[L]` (Link-Local).
   - Modal de creación con conmutador para generación automática EUI-64.
2. **`[ DHCPv6 Client & PD ]` (`/ipv6/dhcp-client`):**
   - Configuración del cliente DHCPv6 en la interfaz WAN para solicitar prefijo al ISP (`request=prefix`).
   - Opción para inyectar automáticamente el prefijo recibido dentro de un Pool IPv6 local (`pool-name`).
   - Visualización del prefijo delegado activo (ej. `2800:bf0:80::/56`).
3. **`[ DHCPv6 Server ]` (`/ipv6/dhcp-server`):**
   - Servidor DHCPv6 para delegación de prefijos `/64` a routers o CPEs de abonados aguas abajo.
   - Lista de bindings y leases IPv6 activos.
4. **`[ Vecinos IPv6 / NDP ]` (`/ipv6/neighbor` y `/ipv6/nd`):**
   - Tabla de descubrimiento de vecinos (equivalente a la tabla ARP de IPv4) mostrando dirección IPv6, MAC física e interfaz.
   - Configuración de Router Advertisements (RA): intervalos de emisión, banderas Managed (M) y Other Configuration (O).
5. **`[ Firewall IPv6 ]` (Acceso rápido / Redirección):**
   - Enlace o selector que conmuta `FirewallRulesView.vue` a modo protocolo `ipv6`.

---

## 4. Endpoints Nuevos de Backend Requeridos

En `fastapi/src/api/v1/webfig_ip.py` y nuevo router `fastapi/src/api/v1/webfig_ipv6.py`:
- `GET/POST/DELETE /routers/{id}/webfig/ip/dhcp-server`
- `GET/POST/PATCH/DELETE /routers/{id}/webfig/ip/dhcp-server/network`
- `GET/POST/PATCH/DELETE /routers/{id}/webfig/ip/dhcp-client`
- `POST /routers/{id}/webfig/ip/dhcp-client/{item_id}/renew`
- `POST /routers/{id}/webfig/ip/dhcp-client/{item_id}/release`
- `GET/POST/DELETE /routers/{id}/webfig/ipv6/addresses`
- `GET/POST/PATCH/DELETE /routers/{id}/webfig/ipv6/dhcp-client`
- `GET/POST/PATCH/DELETE /routers/{id}/webfig/ipv6/dhcp-server`
- `GET/POST/DELETE /routers/{id}/webfig/ipv6/pools`
- `GET /routers/{id}/webfig/ipv6/neighbors`
- `GET/PATCH /routers/{id}/webfig/ipv6/nd`

---

## 5. Aseguramiento 11X y Seguridad
- Toda creación o modificación de direcciones IP y servidores DHCP se ejecuta bajo la protección de **Safe Mode (60s Dead Man's Switch)**, habilitada para roles desde `SUPPORT_L2` hasta `SUPERADMIN_GLOBAL`.
- **Creación Idempotente de Pools, Redes y Servidores DHCP:** Los endpoints `POST /pools`, `POST /dhcp-server/networks` y `POST /dhcp-servers` detectan colisiones de recursos preexistentes en RouterOS v7 (`MikrotikApiError` HTTP 400) y actualizan de forma idempotente el registro existente vía `PATCH`, invalidando el caché corto de KeyDB (`invalidate_webfig_cache`) y evitando errores `HTTP 500`.
- Regla Anti-Suicidio: Prohibición de eliminar o modificar la dirección IP a través de la cual RoSGrid está conectado al router sin activación explícita de Safe Mode y confirmación visual.
- Cobertura de pruebas unitarias `>= 95%` en backend y 100% de aserciones pasando en Vitest frontend.
