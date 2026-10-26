# 49 — WEBFIG v7 CAPA 1: RUTAS ESTÁTICAS IPv4/IPv6, BGP v7 INTERACTIVO, POLICY ROUTING Y ASISTENTES NAT EN 1 CLIC (RoSGrid)

**Autor:** RoSGrid Architecture Team & Antigravity AI Assistant  
**Fecha:** 26 de Octubre de 2026  
**Estado:** ESPECIFICACIÓN TÉCNICA OFICIAL (Hito 27 — Fase 4)  
**Ámbito:** `vue3/src/views/RoutingBgpOspfView.vue`, `vue3/src/views/FirewallRulesView.vue`, `fastapi/src/api/v1/webfig_routing.py`, `fastapi/src/api/v1/webfig_firewall.py`

---

## 1. Justificación y Objetivos de la Fase 4

Llevar el enrutamiento y la seguridad de RoSGrid al nivel más alto de productividad técnica mediante:
1. **Rutas Estáticas Dual-Stack (`/ip/route` e `/ipv6/route`):** Modal táctico para agregar y editar rutas con detección de caída de gateway (*Check Gateway* `ping` / `arp`), distancia administrativa y tablas de ruteo específicas.
2. **BGP v7 Interactivo:** Creación y edición de conexiones BGP (`/routing/bgp/connection`), templates (`/routing/bgp/template`), reinicio suave (*Soft Reset*) y visualización de prefijos RX/TX.
3. **Policy-Based Routing (PBR):** Creación de tablas de enrutamiento FIB (`/routing/table`) y reglas de enrutamiento (`/routing/rule`) para balanceo Multi-WAN.
4. **Wizards NAT de Productividad Extrema en 1 Clic:**
   - *Asistente Masquerade:* Configuración de salida a Internet con selección guiada de la interfaz WAN.
   - *Asistente Port Forwarding (Dst-NAT):* Asistente paso a paso para publicación de servidores locales (CCTV, Web, VPN) con validación automática de puertos y generación de regla espejo en Filter si es requerido.

---

## 2. Especificación de Rutas Estáticas (`RoutingBgpOspfView.vue`)

### 2.1 Pestaña `[ Rutas Estáticas ]`
- Visualización de la tabla unificada de rutas IPv4 e IPv6:
  - Columnas: `Flags` (`[D]` Dynamic, `[A]` Active, `[c]` Connect, `[s]` Static, `[b]` BGP, `[o]` OSPF), `Destino (Dst-Address)`, `Gateway`, `Distancia`, `Routing Table`, `Check Gateway`.
- **Modal de Creación / Edición de Ruta:**
  - `dst_address`: IP/prefijo destino (ej. `0.0.0.0/0` o `192.168.100.0/24`).
  - `gateway`: Dirección IP del siguiente salto o nombre de interfaz.
  - `distance`: Distancia administrativa (por defecto `1`).
  - `routing_table`: Selector entre tabla `main` o tablas FIB personalizadas.
  - `check_gateway`: Selector entre `none`, `ping` o `arp`.
  - `comment`: Comentario de auditoría.

---

## 3. Especificación de BGP v7 Interactivo (`RoutingBgpOspfView.vue`)

### 3.1 Pestaña `[ BGP v7 Sessions & Connections ]`
- **Sub-pestaña 1: Sesiones Activas:**
  - Columnas: `Nombre`, `Remote IP`, `Remote AS`, `Local AS`, `Estado` (`Established`, `Active`, `Connect`), `Prefijos RX`, `Prefijos TX`, `Uptime`.
  - Botón de acción: `[ 🔄 Soft Reset ]` para forzar refresco de rutas sin reiniciar la sesión TCP.
- **Sub-pestaña 2: Conexiones BGP (`/routing/bgp/connection`):**
  - Botón `[ + Nueva Conexión BGP ]`.
  - Campos: `name`, `remote.address`, `remote.as`, `local.as`, `templates`, `routing_table`, `connect` (boolean), `listen` (boolean).
  - Acciones: Editar, Habilitar/Deshabilitar y Eliminar con Safe Mode.

---

## 4. Especificación de Policy-Based Routing (PBR)

### 4.1 Tablas y Reglas de Enrutamiento
- Pestaña `[ Policy Routing & Tables ]`:
  - **Tablas (`/routing/table`):** Crear tablas con bandera `fib=true` para desviar tráfico específico por enlaces secundarios.
  - **Reglas (`/routing/rule`):** Crear reglas de ruteo con `src_address`, `dst_address`, `routing_mark` y `action` (`lookup`, `lookup-only-in-table`).

---

## 5. Especificación de Asistentes Visuales NAT (Wizards)

En `FirewallRulesView.vue` (Pestaña *NAT*):
1. **Botón `[ 🧙‍♂️ Wizard Masquerade (Compartir Internet) ]`:**
   - Modal simple: Selecciona la interfaz WAN (ej. `ether1` o `vlan100-internet`).
   - Genera automáticamente: `chain=srcnat out-interface=<wan> action=masquerade comment="NAT Masquerade RoSGrid Wizard"`.
2. **Botón `[ 🧙‍♂️ Wizard Port Forwarding (Abrir Puertos) ]`:**
   - Asistente en 2 pasos:
     - *Paso 1:* Interfaz de entrada (WAN), Protocolo (`TCP` o `UDP`), Puerto Externo (ej. `8080`).
     - *Paso 2:* IP Interna del Servidor (ej. `192.168.88.50`), Puerto Interno (ej. `80`).
     - *Opcional:* Checkbox `[x] Crear automáticamente regla en Filter (Forward) para permitir el tráfico`.
   - Genera la regla `dstnat` y opcionalmente la regla `forward` con Safe Mode y comprobación previa de colisión de puertos.

---

## 6. Cobertura de Pruebas y Certificación 11X

- Pruebas unitarias backend para endpoints de rutas estáticas y BGP en Pytest.
- Pruebas unitarias frontend para modales y wizards en Vitest.
- Escenarios BDD en Karate Labs para la creación de rutas estáticas y validación de reglas NAT.
