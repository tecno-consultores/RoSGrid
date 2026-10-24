# 33 — GESTIÓN CORPORATIVA DE FLOTAS, SD-WAN, COMPLIANCE CIS Y SEGURIDAD LAN (RoSGrid)

> **[DIRECTIVA DE SISTEMA]:** Esta especificación define de forma exhaustiva las capacidades de ingeniería de red para grandes empresas, bancos, cadenas de retail con cientos de sucursales, campus universitarios y hospitales que operan flotas de hardware MikroTik RouterOS v7+. RoSGrid actúa como una plataforma centralizada de orquestación, cumplimiento normativo (ISO 27001, PCI-DSS) y seguridad perimetral, prescindiendo de licencias recurrentes privativas.

---

## 1. Detección de Desviación de Configuración (*Config Drift Detection*) & Cumplimiento

### 1.1. El Reto Corporativo

En organizaciones con 50 a 500 sucursales, los administradores locales o técnicos de campo a menudo alteran configuraciones en WinBox de forma no autorizada (abrir puertos, cambiar DNS corporativo, desactivar reglas de firewall o crear usuarios locales). Esto viola normativas de auditoría y genera brechas de seguridad silenciosas.

### 1.2. Arquitectura de Plantilla Maestra (*Golden Baseline Template*)

- **Tabla `golden_config_templates`:**
  - `id`: UUID.
  - `tenant_id`: UUID.
  - `name`: String (ej. `Standard-Branch-Office-v7`).
  - `network_role`: Enum (`BRANCH`, `EDGE`, `CORE`, `CAMPUS`).
  - `baseline_rsc_content`: Text (Estructura modular canónica en RouterOS script).
  - `enforce_strict_firewall`: Boolean.
  - `enforce_ntp_dns`: Boolean.
  - `created_at`, `updated_at`: Timestamps.

### 1.3. Motor de Detección de Drift

- **Ejecución Periódica / Bajo Demanda:**
  1. Exporta el archivo `.rsc` en ejecución del router MikroTik.
  2. Normaliza el script (elimina timestamps y comentarios volátiles).
  3. Ejecuta un algoritmo de comparación de diferencias semánticas con la plantilla maestra asignada a ese `network_role`.
  4. Si hay divergencias, marca el router como `CONFIG_DRIFT_DETECTED`.
- **Vista Táctica & Git Diff Visual:**
  - El frontend resalta las líneas añadidas (`+`), modificadas o eliminadas (`-`).
- **Remediación en 1-Clic (*Auto-Revert*):**
  - Botón *"Revertir a Configuración Homologada"*: Aplica el bloque correctivo bajo una sesión de **Safe Mode (60s)** con registro de auditoría WORM y aprobación Maker-Checker.

---

## 2. Orquestador SD-WAN & Malla WireGuard Sucursales-a-Data Center (*Hub & Spoke*)

### 2.1. Arquitectura de Túneles Automatizada

- **Modelo:** Hub central (Data Center / Nube) y múltiples Spokes (Sucursales).
- **Aprovisionamiento Zero-Touch de WireGuard:**
  1. Al dar de alta una sucursal, RoSGrid genera el par de llaves WireGuard (pública/privada) mediante criptografía asimétrica local.
  2. Asigna una subred de transporte punto a punto `/30` o `/31` desde el IPAM interno.
  3. Inserta el Peer en el router Hub (`/interface/wireguard/peers/add`).
  4. Configura la interfaz y peer en el router Spoke vía REST API.
  5. Despliega adyacencia de enrutamiento dinámico (OSPF sobre WireGuard o BGP interno) para propagar las subredes locales de la sucursal instantáneamente.

### 2.2. Monitoreo Multi-WAN y Failover Inteligente

- Supervisión concurrente de hasta 3 enlaces WAN por sucursal (ej. Fibra principal + Starlink satelital + LTE/5G).
- Orquestación de **PBR (Policy-Based Routing)** y rutas recursivas con Netwatch:
  - Enrutamiento de tráfico crítico (ERP, Base de Datos, Telefonía IP) conmutado a enlace de respaldo en $< 1\text{ segundo}$ ante degradación o pérdida de paquetes en el enlace primario.

---

## 3. Auditoría de Seguridad & Endurecimiento CIS Benchmark para RouterOS

### 3.1. Escáner de Cumplimiento de Ciberseguridad (Security Score 0 a 100)

Endpoint `POST /api/v1/compliance/cis-audit/{router_id}` que evalúa las 10 directivas críticas de hardening:

1. **Servicios Inseguros:** Comprueba que `telnet`, `ftp`, `www` (sin SSL) y `api` (sin TLS) estén en `disabled=yes`.
2. **Defensa de Usuario Admin:** Verifica que el usuario por defecto `admin` no exista o esté deshabilitado.
3. **Restricción de Acceso a WinBox/API:** Verifica que `/ip/service/set winbox address=X.X.X.X/XX` solo admita bloques autorizados y no `0.0.0.0/0`.
4. **Protección Open DNS Resolver:** Verifica que `/ip/dns/set allow-remote-requests=no` o que el puerto UDP/53 esté bloqueado en la interfaz WAN.
5. **Detección de MAC-Server Expuesto:** Comprueba que `/tool/mac-server` y `/ip/neighbor/discovery-settings` estén deshabilitados en interfaces públicas.
6. **Estado de Paquetes RouterOS y RouterBOOT:** Comprueba si la versión de RouterOS y el firmware del microcontrolador RouterBOOT tienen parches de seguridad pendientes.
7. **Filtrado de Paquetes Bogon / RFC 1918:** Verifica reglas de firewall que impidan la entrada de IPs marcadas como marcianas en la interfaz WAN.
8. **Protección Brute-Force SSH/WinBox:** Verifica listas negras dinámicas para intentos fallidos repetidos.
9. **Cifrado de Túneles:** Valida el uso de suites criptográficas modernas (evitando DES, 3DES o MD5 en IPsec/WireGuard).
10. **Aislamiento de Interfaces de Gestión:** Verifica el uso de VLANs dedicadas para administración.

### 3.2. Puntuación y Remediación en 1-Clic

- El sistema asigna una calificación global (0 a 100%).
- Botón *"Endurecer Router Automáticamente (Auto-Hardening)"*: Genera el script correctivo, lo aplica con Safe Mode y eleva la calificación a 100%.

---

## 4. Detección de Rogue DHCP & Seguridad de Conmutación (Switching / LAN)

### 4.1. El Problema de Redes Corporativas

Un usuario conecta un router WiFi doméstico o switch no gestionado en una toma de red, lo que inicia un servidor DHCP no autorizado (Rogue DHCP) que reparte puertas de enlace falsas, causando caídas masivas en toda la planta o ataques Man-in-the-Middle.

### 4.2. Detección y Mitigación en RoSGrid

1. **DHCP Snooping Automatizado:**
   - Activa `/interface/bridge/set dhcp-snooping=yes` en los bridges de acceso.
   - Marca únicamente los puertos de subida hacia el core como `trusted=yes`.
   - Si un paquete `DHCP-OFFER` o `DHCP-ACK` entra por un puerto `trusted=no`, el chip de conmutación lo descarta inmediatamente por hardware.
2. **Alerta Inmediata al NOC:**
   - Detecta el evento de alerta en RouterOS (`dhcp-snooping, warning: rogue dhcp detected`).
   - Envía notificación push al Wallboard NOC especificando el puerto físico exacto (ej. `ether14`) y la dirección MAC del intruso.
   - Opción para deshabilitar administrativamente el puerto afectado con 1 clic.

---

## 5. Monitor de Cumplimiento de SLA para Enlaces Dedicados

### 5.1. Propósito

Las empresas pagan tarifas premium por enlaces de fibra con compromisos contractuales de nivel de servicio (SLA). Este módulo registra métricas continuas para respaldar reclamos de notas de crédito o penalizaciones por incumplimiento.

### 5.2. Métricas y Registro

- **Sondeo Proactivo:** Envío de paquetes de prueba continuos hacia la IP del gateway del carrier y servidores de referencia.
- **Parámetros Registrados:**
  - Disponibilidad porcentual (Uptime vs Downtime).
  - Latencia media y percentiles P95/P99.
  - Jitter (variación de retardo).
  - Porcentaje de pérdida de paquetes.
- **Generador de Reportes de Cumplimiento de SLA:**
  - Generación de informes exportables (PDF/CSV) que certifican los minutos totales de caída, número de micro-cortes y períodos donde la latencia excedió el umbral pactado en el contrato.

---

## 6. Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2)

### 6.1. Orquestación Unificada de Puntos de Acceso (APs)

Para campus, centros de distribución, clínicas y edificios corporativos:

- **SSID Corporativo Seguro:** WPA3-Enterprise con autenticación 802.1X / EAP-TLS y asignación dinámica de VLANs según el rol del empleado.
- **SSID Invitados:** Aislado en su propia VLAN, con límite de velocidad estricto y aislamiento de clientes (Client Isolation activo para evitar que un invitado vea a otros equipos).
- **SSID Dispositivos IoT / Operativos:** Clave precompartida WPA2/WPA3 con direccionamiento estático o DHCP reservado para impresoras de red, cámaras y lectores de códigos de barras.

### 6.2. Telemetría de Radiofrecuencia y Roaming

- Visor centralizado de clientes inalámbricos conectados:
  - Nivel de señal RSSI (dBm), relación señal a ruido (SNR) y estándar en uso (802.11ax / ac / n).
  - Trazabilidad de eventos de itinerancia (*Fast Roaming 802.11r/k/v*) entre puntos de acceso sin cortes de llamada en VoIP.

---

## 7. Integración de Canales de Alerta y Notificación Multicanal (`NotificationChannelsPanel.vue`)

Para alertamiento corporativo en tiempo real ante eventos de desconexión de routers, deriva de configuración, ataques de rogue DHCP y caídas de enlaces WAN:

### 7.1. Arquitectura de Canales Cifrados (AES-256-GCM)

- **Pestaña Táctica en Enterprise Compliance:** Integrada como 7.ª pestaña interactiva en `EnterpriseComplianceView.vue`.
- **Tipos de Canales Soportados:**
  - **Telegram Bot (`TELEGRAM_BOT`):** Token del bot y Chat ID con entrega inmediata mediante API de Telegram.
  - **Servidor de Correo SMTP (`SMTP_EMAIL`):** Servidor, puerto TLS/STARTTLS, credenciales autenticadas y lista de destinatarios.
  - **Webhook Genérico HTTP (`GENERIC_WEBHOOK`):** Endpoint HTTPS receptor de alertas estructuradas en JSON con cabecera de autenticación opcional.
- **Suscripción Selectiva de Eventos:**
  - `ROUTER_OFFLINE`, `ROUTER_ONLINE`, `DEGRADED_HIGH_LOAD`, `SSL_MISMATCH`, `CONFIG_DRIFT_DETECTED`, `ROGUE_DHCP_ALERT`.
- **Despacho Interactivo de Pruebas en Vivo:**
  - Ejecución de `POST /api/v1/operations/notification-channels/{id}/test` desde la interfaz para verificar conectividad y credenciales sin necesidad de generar una alerta real en la red.
