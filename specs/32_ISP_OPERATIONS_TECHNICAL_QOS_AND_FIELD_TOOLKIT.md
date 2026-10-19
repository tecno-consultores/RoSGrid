# 32 — OPERACIONES ISP, QOS TÉCNICO, API DE APROVISIONAMIENTO Y TOOLKIT DE CAMPO (RoSGrid)

> **[DIRECTIVA DE SISTEMA]:** Esta especificación define de forma exhaustiva la arquitectura técnica del módulo ISP y operaciones de campo en RoSGrid. **Queda terminantemente prohibido incorporar campos o lógica de facturación, cobros, pasarelas de pago o datos personales de abonados.** RoSGrid es una plataforma de ingeniería de red y orquestación de infraestructura MikroTik. Cualquier sistema de facturación o CRM externo se conectará a través de la API REST idempotente aquí descrita.

---

## 1. Principio Fundamental: Cero Facturación y Cero Datos Personales

RoSGrid no es un BSS/ERP. En el modelo de datos de RoSGrid:
1. **Identificadores Técnicos Únicos:**
   - Todo servicio o equipo de abonado se referencia exclusivamente por su `device_serial` (serial de la ONU, ej. `ZTEGC1234567`) o un `endpoint_identifier` técnico (ej. nombre de usuario PPPoE `usr_ftth_4091` o código de circuito).
   - Queda prohibido almacenar nombres de personas, números de identificación fiscal/cédula, direcciones postales o datos financieros.
2. **Desacoplamiento Total:**
   - La correlación entre la persona/cliente y su serial técnico reside en el sistema de facturación externo del ISP.
   - RoSGrid solo conoce: el router de acceso MikroTik, la interfaz/VLAN, la IP/IPv6 asignada, el perfil de ancho de banda y las coordenadas GPS del equipo.

---

## 2. Modelo de Datos y Entidades Técnicas (`fastapi/src/models/ipam.py`)

### 2.1. Tabla `bandwidth_profiles`
Define los perfiles de ingeniería de tráfico sin referencias monetarias:
- `id`: UUID (Clave primaria).
- `tenant_id`: UUID (Multi-tenant RLS).
- `name`: String (ej. `100M-Down-50M-Up-Default`).
- `rate_down_kbps`: Integer (Velocidad nominal de descarga en kbps).
- `rate_up_kbps`: Integer (Velocidad nominal de subida en kbps).
- `burst_down_kbps`: Integer (Tasa máxima durante ráfagas de bajada).
- `burst_up_kbps`: Integer (Tasa máxima durante ráfagas de subida).
- `burst_threshold_down_kbps`: Integer (Umbral de activación de ráfaga bajada).
- `burst_threshold_up_kbps`: Integer (Umbral de activación de ráfaga subida).
- `burst_time_seconds`: Integer (Ventana de tiempo para cálculo de ráfaga, ej. 8s).
- `priority`: Integer (1 a 8, donde 1 es máxima prioridad y 8 es mínima).
- `queue_type`: String (ej. `pcq-download-default`, `pcq-upload-default`, `default-small`).
- `created_at`, `updated_at`: Timestamps.

### 2.2. Tabla `subscriber_devices` (Refactorización Técnica de CustomerService)
- `id`: UUID.
- `tenant_id`: UUID.
- `router_id`: UUID (FK a `routers`).
- `device_serial`: String (Serial físico de la ONU o equipo CPE).
- `endpoint_identifier`: String (Usuario PPPoE o identificador de sesión).
- `assigned_ipv4`: String nullable.
- `assigned_ipv6_prefix`: String nullable (/56 o /64).
- `bandwidth_profile_id`: UUID nullable (FK a `bandwidth_profiles`).
- `onu_mode`: Enum (`ROUTER`, `BRIDGE`).
- `latitude`: Float nullable (GPS).
- `longitude`: Float nullable (GPS).
- `status`: Enum (`PENDING_ACTIVATION`, `ACTIVE`, `ISOLATED_ADMINISTRATIVE`, `SUSPENDED_TECHNICAL`, `DECOMMISSIONED`).
- `created_at`, `updated_at`: Timestamps.

---

## 3. API de Aprovisionamiento Técnico con Idempotencia Obligatoria

Los sistemas de facturación/CRM externos consumen estos endpoints utilizando la cabecera `Idempotency-Key` (UUIDv7):

### 3.1. `POST /api/v1/network-services/{id}/isolate`
- **Propósito:** Restringir el tráfico del abonado (por ejemplo, ante suspensión administrativa ordenada por el CRM externo).
- **Mecanismo en MikroTik:**
  1. Agrega la IP del abonado a la lista `/ip/firewall/address-list add list=AISLADOS_TECNICO address={ip}`.
  2. Alternativamente, conmuta la velocidad de su Simple Queue a `64k/64k` para preservar conectividad de monitoreo sin cortar la sesión física.
- **Idempotencia:** Si la IP ya está en la lista o aislada, responde HTTP 200 con `{ status: "ALREADY_ISOLATED" }` sin error ni mutaciones redundantes.

### 3.2. `POST /api/v1/network-services/{id}/restore`
- **Propósito:** Restablecer el servicio técnico al estado normal en milisegundos tras la orden del CRM externo.
- **Mecanismo en MikroTik:**
  1. Elimina la IP de la lista `AISLADOS_TECNICO`.
  2. Restaura los límites normales de su Simple Queue/PCQ según su `bandwidth_profile_id`.
- **Idempotencia:** Si ya está activo, responde HTTP 200 con `{ status: "ALREADY_ACTIVE" }`.

### 3.3. `POST /api/v1/network-services/{id}/change-rate-limit`
- **Payload:** `{ bandwidth_profile_id: UUID }`.
- **Mecanismo en MikroTik:**
  1. Modifica en caliente los parámetros `max-limit`, `burst-limit`, `burst-threshold` y `burst-time` en `/queue/simple` sin cortar la sesión PPPoE/DHCP del cliente.

### 3.4. Motor de Webhooks Salientes Técnicos
Cuando ocurren eventos de red en RoSGrid, se despacha un `HTTP POST` con firma `X-RoSGrid-Signature: sha256={hmac}` hacia las URLs registradas:
- `DEVICE_ACTIVATED_GPS`: Técnico activó equipo con coordenadas definitivas.
- `DEVICE_ISOLATED`: Servicio restringido en MikroTik.
- `DEVICE_RESTORED`: Servicio normalizado.
- `MASS_OUTAGE_TRIGGERED`: Más de 10 equipos cayeron simultáneamente.

---

## 4. Suite de Diagnóstico 360° de Abonado / Enlace

Disponible tanto para el personal del NOC como para el técnico de campo en ruta:

### 4.1. Endpoint `POST /api/v1/diagnostics/endpoint-360`
- **Entrada:** `{ router_id: UUID, target_ip: str, device_serial: str }`.
- **Ejecución en MikroTik v7:**
  1. **Ping Multi-MTU Secuencial:**
     - 3 paquetes de 64 bytes (latencia base).
     - 3 paquetes de 512 bytes (estabilidad bajo carga moderada).
     - 3 paquetes de 1472 bytes (verificación de fragmentación DF-bit en MTU 1500).
     - Retorna: latencia mínima, media, máxima, jitter y porcentaje de pérdida por tamaño.
  2. **Parseo de Desconexiones en `/log`:**
     - Filtra eventos recientes con tópicos `pppoe`, `ppp`, `interface` asociados a la IP o sesión.
     - Clasifica el motivo exacto de RouterOS:
       * `user request` (El usuario apagó su router o desconectó el cable).
       * `peer is not responding` (Corte de fibra, corte eléctrico en la zona o micro-corte óptico).
       * `link down` (Puerto Ethernet o SFP desconectado físicamente).
       * `authentication failed` (Clave PPPoE errónea).
  3. **Muestreo Torch Instantáneo:**
     - Ejecuta `/tool/torch` durante 2.5 segundos filtrando por la IP del equipo.
     - Retorna el Top 5 de flujos activos (Protocolo, Puerto, Tx/Rx rate kbps).

---

## 5. Mapa Separado de ONUs y Telemetría Efímera

### 5.1. Aislamiento Físico y Conceptual del Mapa de Routers
- Los routers de infraestructura (Core, Distribución, BGP) se visualizan exclusivamente en `/inventory` (mapa de infraestructura).
- Las ONUs y equipos de última milla se visualizan en `/subscribers/map` (`OsmOnuMap.vue`).

### 5.2. Regla de Oro Zero-Metrics
- Las métricas de estado de las ONUs **JAMÁS** se escriben en PostgreSQL.
- Se procesan en memoria efímera y se reflejan en el mapa con 3 estados cromáticos:
  - 🟢 **Verde (Óptimo):** Latencia ping $< 40\text{ ms}$, 0% de pérdida.
  - 🟠 **Naranja (Degradado):** Latencia entre $40\text{ ms}$ y $120\text{ ms}$ o pérdida parcial de paquetes ($1-20\%$).
  - 🔴 **Rojo (Caído / Offline):** Sin respuesta a ping o sesión caída.

### 5.3. Alerta de Caída Masiva (Mass Outage Alert)
- Si en un ciclo de sondeo caen simultáneamente más de `mass_outage_threshold` equipos (por defecto 10), el sistema:
  1. Emite un evento WebSocket `MASS_OUTAGE_DETECTED` al Wallboard NOC con sonido táctico de alarma y banner de alta visibilidad.
  2. Registra el evento en la tabla `audit_logs` con hash encadenado HMAC-SHA256 para constancia forense.

---

## 6. Panel Responsive del Técnico de Calle

### 6.1. Corrección de Maquetación y Fluidez Multi-Dispositivo
- Queda prohibido el uso de contenedores fijos verticales estrechos (`max-width: 480px`).
- El diseño debe ser fluido y adaptable a:
  - **Smartphones:** Layout táctil vertical de 1 columna con botones mínimos de $48\text{px}$.
  - **Tablets:** Layout de 2 columnas (lista de órdenes pendientes a la izquierda, diagnóstico y firma a la derecha).
  - **Laptops de Servicio:** Vista extendida con acceso rápido a herramientas de diagnóstico 360°.

### 6.2. Activación con Captura GPS
- Formulario limpio: **Solo pide el Serial de la ONU** (escaneado o escrito) y un identificador técnico de circuito.
- Botón prominente: *"📍 Capturar Coordenadas GPS"* (invoca la API nativa `navigator.geolocation.getCurrentPosition`).
- Al guardar la activación, las coordenadas se asocian al equipo y aparece inmediatamente en el mapa `/subscribers/map`.

---

## 7. Arquitectura de Internacionalización (i18n)

- RoSGrid implementa una capa reactiva de localización preparada para múltiples idiomas:
  - `locales/es.json`: Diccionario base en Español (por defecto).
  - `locales/en.json`: Diccionario base en Inglés.
- Los componentes acceden a las cadenas mediante `$t('key')` o composable `useI18n()`.
- Cualquier tercero puede añadir un nuevo idioma simplemente colocando un archivo `.json` en la carpeta de locales sin alterar la lógica de negocio.
