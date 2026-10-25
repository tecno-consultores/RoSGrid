# 42 — REPORTE DE INVESTIGACIÓN: HARDENING CIS, OPTIMIZACIÓN DE RENDIMIENTO Y PLANTILLAS DE ACCIONES MASIVAS EN MIKROTIK ROUTEROS V7

> **ESTADO:** ESPECIFICACIÓN TÉCNICA Y REPORTE DE INGENIERÍA 11X  
> **ÁMBITO:** SEGURIDAD DE FLOTA, POLÍTICAS POR TENANT (ISP VS CORPORATIVO), FASTTRACK, L3HW Y BULK OPS  
> **AUTOR:** RoSGrid Architecture & Security Core  

---

## 1. Resumen Ejecutivo y Marco Normativo

A diferencia de sistemas operativos como Linux o Cisco IOS, el Center for Internet Security (CIS) no publica un benchmark estático monolítico para MikroTik RouterOS v7. Sin embargo, las directivas de seguridad de operadores globales, normativas NIST SP 800-123 y las mejores prácticas oficiales de MikroTik (Security Guide & RouterOS v7 Reference) consolidan un cuerpo de políticas obligatorias para operar infraestructura crítica.

En entornos reales existen **dos perfiles operacionales con requerimientos marcadamente distintos**:
1. **Entorno Corporativo / Campus:** Prioriza el control estricto de acceso de usuarios internos, aislamiento de gestión en VLANs dedicadas, prevención de servidores DHCP no autorizados (Rogue DHCP) y auditoría detallada de accesos administrativos.
2. **Proveedor de Servicios de Internet (ISP / WISP / Carrier):** Prioriza el rendimiento de reenvío de paquetes por segundo (PPS), protección de tránsito BGP, mitigación de ataques de amplificación DNS, filtrado estricto de Bogons / Anti-Spoofing (BCP 38 / RFC 2827), y aceleración por hardware (FastTrack y L3HW Offloading) sin degradar la calidad de servicio (QoS).

Por esta razón, **RoSGrid descentraliza el motor de políticas**: cada organización (tenant) puede seleccionar un perfil base (`CORPORATE`, `ISP`, `DATACENTER`) y ajustar individualmente cada regla según su infraestructura.

---

## 2. Catálogo de Políticas de CIS Hardening por Dominio y Perfil

A continuación se detalla la matriz de directivas recomendadas para parametrizar las políticas de cada empresa:

| Código | Título de la Directiva | Severidad | Peso | Perfil Recomendado | Comando de Remediación Canónico (RouterOS v7) |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **CIS-1.1** | Deshabilitar servicios de gestión inseguros en texto plano | CRÍTICA | 15 | TODOS | `/ip service set telnet,ftp,www,api disabled=yes` |
| **CIS-1.2** | Eliminar o deshabilitar usuario 'admin' por defecto | ALTA | 10 | TODOS | `/user set [find name=admin] disabled=yes` |
| **CIS-1.3** | Restricción CIDR estricta para WinBox y API REST | ALTA | 10 | TODOS | `/ip service set winbox,www-ssl address=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` |
| **CIS-1.4** | Mitigación de Open DNS Resolver / Amplificación DDoS | CRÍTICA | 12 | ISP & Datacenter | `/ip dns set allow-remote-requests=no` |
| **CIS-1.5** | Desactivar MNDP, CDP y LLDP en interfaces públicas WAN | ALTA | 10 | TODOS | `/ip neighbor discovery-settings set discover-interface-list=!WAN; /tool mac-server set allowed-interface-list=NONE` |
| **CIS-1.6** | Actualización de RouterOS y Firmware RouterBOARD | MEDIA | 8 | TODOS | `/system package update install; /system routerboard upgrade` |
| **CIS-1.7** | Filtrado estricto de Bogons / RFC 1918 / RFC 6598 en WAN | ALTA | 10 | ISP & Carrier | `/ip firewall raw add chain=prerouting in-interface-list=WAN src-address-list=bogons action=drop comment="Drop Bogons"` |
| **CIS-1.8** | Defensa dinámica de 3 etapas contra Brute-Force SSH/Winbox | ALTA | 10 | TODOS | `/ip firewall filter add chain=input protocol=tcp dst-port=22 connection-state=new src-address-list=ssh_stage3 action=add-src-to-address-list address-list=ssh_blacklist address-list-timeout=7d` |
| **CIS-1.9** | Criptografía robusta en túneles IPsec/WireGuard (No DES/3DES/MD5) | MEDIA | 8 | Corporativo & DC | `/ip ipsec profile set default enc-algorithm=aes-256,aes-128-gcm hash-algorithm=sha256` |
| **CIS-1.10**| Aislamiento de la gestión administrativa en VLAN dedicada | MEDIA | 7 | Corporativo | `/interface vlan add name=vlan99-mgmt vlan-id=99 interface=bridge` |
| **CIS-1.11**| Syslog remoto continuo hacia SIEM (Zero-Flash Degradation) | MEDIA | 8 | TODOS | `/system logging action add name=siem target=remote remote=10.10.99.50; /system logging add topics=firewall,account action=siem` |
| **CIS-1.12**| Seguridad de Enrutamiento BGP: Filtros de prefijo y MD5/TCP-AO | ALTA | 12 | ISP & Datacenter | `/routing bgp connection set [find] tcp-md5-key=StrongAuthKey output.keep-sent-attributes=yes` |
| **CIS-1.13**| DHCP Snooping activo en Bridge para prevenir Rogue DHCP | MEDIA | 8 | Corporativo | `/interface bridge set [find] dhcp-snooping=yes` |
| **CIS-1.14**| ICMP Rate Limiting para prevenir inundaciones de control plane | BAJA | 5 | TODOS | `/ip firewall filter add chain=input protocol=icmp limit=50/1s,5:packet action=accept` |

---

## 3. Optimización de Rendimiento en RouterOS v7: FastTrack, Conntrack y L3HW

### 3.1 La Paradoja de FastTrack vs Queue Trees (QoS)
En RouterOS v7, el reenvío FastTrack (`action=fasttrack-connection`) puentea la pila de inspección profunda de paquetes y evaluación de conntrack para conexiones establecidas y relacionadas, multiplicando hasta por 5 el throughput del equipo y reduciendo el uso de CPU.

**Conflicto Fundamental:**
Los paquetes que son procesados por FastTrack **omiten completamente las colas simples (`/queue simple`) y los árboles de colas (`/queue tree`)**. Si un ISP activa FastTrack global, el control de ancho de banda y la priorización de tráfico (QoS) dejan de funcionar.

**Solución Arquitectónica (Selective FastTracking):**
Clasificar el tráfico que requiere modelado mediante marcas de paquete (`packet-mark`) antes de la regla de FastTrack:
```text
/ip firewall mangle
add chain=forward action=mark-packet new-packet-mark=qos-shaped passthrough=no src-address-list=client_tier1

/ip firewall filter
add chain=forward action=fasttrack-connection connection-state=established,related packet-mark=!qos-shaped hw-offload=yes comment="FastTrack sin afectar clientes moldeados"
add chain=forward action=accept connection-state=established,related
```

### 3.2 L3 Hardware Offloading (L3HW) en Switches CRS3xx y Routers CCR2xxx
RouterOS v7 introdujo enrutamiento de velocidad de cable por conmutación de silicio (L3HW):
1. **Compatibilidad:** CRS3xx, CRS5xx, CCR2004, CCR2116, CCR2216.
2. **Activación de VLAN Filtering en Hardware:**
   ```text
   /interface bridge set bridge vlan-filtering=yes
   /interface bridge port set [find] hw=yes
   ```
3. **Monitoreo de Desbordamiento:** Las tablas de hardware (TCAM/ACL) tienen capacidades finitas (ej. 4.000 a 16.000 rutas según chip Marvell/Realtek). Cuando la capacidad se excede, el exceso cae suavemente al procesador CPU sin interrumpir el servicio.

---

## 4. Plantillas Maestras para Acciones Masivas (Bulk Ops Golden Templates)

### Plantilla 1: Blindaje Inmediato de Control Plane (Baseline Universal)
```rsc
# RoSGrid Golden Template: Universal Control Plane Hardening
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set api disabled=yes
/ip dns set allow-remote-requests=no
/ip neighbor discovery-settings set discover-interface-list=!WAN
/tool mac-server set allowed-interface-list=NONE
/tool mac-server mac-winbox set allowed-interface-list=LAN
/tool mac-server ping set enabled=no
/ip firewall filter
add chain=input action=accept connection-state=established,related,untracked comment="Accept established/related"
add chain=input action=drop connection-state=invalid comment="Drop invalid connections"
add chain=input action=accept protocol=icmp limit=50/1s,5:packet comment="Allow limited ICMP"
add chain=input action=drop in-interface-list=WAN comment="Drop unsolicited input from WAN"
```

### Plantilla 2: Aceleración FastTrack & Optimización Conntrack (Perfil ISP)
```rsc
# RoSGrid Golden Template: ISP Carrier FastTrack & Anti-Bogon
/ip firewall raw
add chain=prerouting in-interface-list=WAN src-address=0.0.0.0/8 action=drop comment="Drop Bogon 0.0.0.0/8"
add chain=prerouting in-interface-list=WAN src-address=10.0.0.0/8 action=drop comment="Drop Bogon RFC1918 10/8"
add chain=prerouting in-interface-list=WAN src-address=100.64.0.0/10 action=drop comment="Drop Bogon CGNAT from WAN"
add chain=prerouting in-interface-list=WAN src-address=127.0.0.0/8 action=drop comment="Drop Loopback"
add chain=prerouting in-interface-list=WAN src-address=169.254.0.0/16 action=drop comment="Drop APIPA"
add chain=prerouting in-interface-list=WAN src-address=172.16.0.0/12 action=drop comment="Drop Bogon RFC1918 172.16/12"
add chain=prerouting in-interface-list=WAN src-address=192.168.0.0/16 action=drop comment="Drop Bogon RFC1918 192.168/16"

/ip firewall filter
add chain=forward action=fasttrack-connection connection-state=established,related hw-offload=yes comment="L3HW FastTrack"
add chain=forward action=accept connection-state=established,related comment="Accept established/related forward"
add chain=forward action=drop connection-state=invalid comment="Drop invalid forward"
```

### Plantilla 3: Prevención de Intrusión y Fuerza Bruta SSH/Winbox (3-Stage Port Knocking)
```rsc
# RoSGrid Golden Template: Dynamic Brute Force Blacklist
/ip firewall filter
add chain=input protocol=tcp dst-port=22 connection-state=new src-address-list=ssh_blacklist action=drop comment="Drop SSH Blacklisted"
add chain=input protocol=tcp dst-port=22 connection-state=new src-address-list=ssh_stage3 action=add-src-to-address-list address-list=ssh_blacklist address-list-timeout=7d comment="Add to Blacklist 7d"
add chain=input protocol=tcp dst-port=22 connection-state=new src-address-list=ssh_stage2 action=add-src-to-address-list address-list=ssh_stage3 address-list-timeout=1m comment="Step to Stage 3"
add chain=input protocol=tcp dst-port=22 connection-state=new src-address-list=ssh_stage1 action=add-src-to-address-list address-list=ssh_stage2 address-list-timeout=1m comment="Step to Stage 2"
add chain=input protocol=tcp dst-port=22 connection-state=new action=add-src-to-address-list address-list=ssh_stage1 address-list-timeout=1m comment="Record initial attempt"
```

---

## 5. Arquitectura de Implementación en RoSGrid

1. **Gestión de Políticas por Tenant:**
   - La tabla de auditoría CIS consulta la clave `rg:{tenant_id}:cis_policy_rules` en KeyDB.
   - Si no está personalizada, inicializa automáticamente el catálogo canónico de acuerdo al perfil corporativo o ISP.
   - Cada regla puede ser habilitada o deshabilitada (`enabled: boolean`) y su peso ajustado (`weight: number`).
   - El **Security Score (0-100)** se normaliza dinámicamente:
     $$\text{Score} = \left( \frac{\sum_{i \in \text{Aprobadas}} W_i}{\sum_{j \in \text{Habilitadas}} W_j} \right) \times 100$$
2. **Onboarding Inicial de Feature Flags:**
   - En el primer inicio de sesión del SuperAdmin o Admin de Tenant, se presenta el modal interactivo de bienvenida y activación de módulos.
   - El tenant define su arquetipo operativo (`ISP`, `CORPORATE`, `CUSTOM`) en 1 clic.
   - La selección persiste en `/api/v1/tenants/{id}/features` y marca `onboarding_completed: true` para no volver a interrumpir la operativa diaria.
