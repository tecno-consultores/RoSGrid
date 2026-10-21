# Catálogo de Herramientas MCP de RoSGrid (`/api/v1/mcp`)

Este documento detalla los parámetros de entrada, esquemas y directrices de uso de las 18 herramientas MCP expuestas por el servidor RoSGrid para agentes de Inteligencia Artificial.

---

## 1. Herramientas de Observabilidad e Inventario

### `rosgrid_list_inventory`

- **Descripción:** Lista los enrutadores MikroTik autorizados para el Tenant con su ID, nombre, identidad RouterOS, modelo, versión de firmware v7, estado de conexión en KeyDB y estado TOFU SSL.
- **Parámetros:**
  - `status_filter` (string, opcional): Filtrar por estado (ej. `ONLINE`, `OFFLINE`, `DEGRADED_HIGH_LOAD`).
  - `role_filter` (string, opcional): Filtrar por etiqueta o rol (ej. `CORE_BGP`, `DISTRIBUTION`, `ACCESS_PPPOE`).

### `rosgrid_get_router_health`

- **Descripción:** Consulta el estado efímero en KeyDB y `/rest/system/resource` + `/rest/system/health`, devolviendo CPU%, RAM%, espacio en disco, Uptime, Temperatura (°C) y Voltaje (V).
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.

### `rosgrid_check_sfp_optical_ddm`

- **Descripción:** Consulta el diagnóstico óptico DDM de transceptores SFP/SFP+ (potencias `tx-power` y `rx-power` en dBm, temperatura del láser y clasificación de salud: `OPTIMAL`, `WARNING`, `CRITICAL_LOW_LIGHT`).
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `interface_name` (string, obligatorio): Nombre de la interfaz SFP (ej. `sfp-sfpplus1`).

---

## 2. Herramientas de Ruteo y Diagnóstico de Red

### `rosgrid_inspect_routing_bgp_ospf`

- **Descripción:** Devuelve el resumen de sesiones BGP RouterOS v7 (estado `established`, conteo de prefijos recibidos, uptime) y adyacencias OSPF activas.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `protocol` (string enum: `["bgp", "ospf", "all"]`, opcional, por defecto `all`).

### `rosgrid_query_bgp_looking_glass`

- **Descripción:** Consulta la tabla de rutas FIB o los prefijos anunciados a un vecino BGP específico sin requerir acceso SSH interactivo.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `query_type` (string enum: `["route", "advertised"]`, opcional, por defecto `route`).
  - `prefix` (string, opcional): Prefijo IPv4/IPv6 o CIDR a consultar (ej. `1.1.1.0/24`).
  - `peer_session` (string, opcional): Nombre o IP del vecino BGP.
  - `refresh` (boolean, opcional, por defecto `false`): Si es `true`, evade la caché de KeyDB y consulta directamente el router.

### `rosgrid_run_live_diagnostic`

- **Descripción:** Ejecuta Ping o Traceroute acotado desde el enrutador hacia un destino específico, midiendo latencia (mínima, promedio, máxima) y porcentaje de pérdida de paquetes.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `tool` (string enum: `["ping", "traceroute"]`, obligatorio).
  - `target` (string, obligatorio): IP de destino o nombre de dominio (FQDN).
  - `count` (integer, opcional, rango 1 a 5, por defecto 4): Número de sondas.

### `rosgrid_run_360_diagnostics`

- **Descripción:** Suite de diagnóstico 360° en MikroTik v7: ping multi-MTU (64B, 512B, 1472B con flag DF-bit para detectar problemas de MTU), análisis del `/log` de desconexiones y muestreo Torch de flujos activos.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `target_ip` (string, obligatorio): Dirección IP del abonado o CPE.
  - `device_serial` (string, opcional): Serial de la ONU o equipo de cliente.
  - `interface` (string, opcional): Nombre de la interfaz para muestreo Torch (ej. `ether1`).

---

## 3. Herramientas de Correlación y Gestión de Planta Externa

### `rosgrid_detect_mass_outage`

- **Descripción:** Motor de correlación espacial para detectar caídas masivas y cortes de fibra óptica, agrupando ONUs fuera de línea por puerto PON, OLT o caja NAP.
- **Parámetros:**
  - `threshold_onus` (integer, opcional, mínimo 1, por defecto 3): Umbral mínimo de equipos caídos en el mismo agrupador para clasificar corte.
  - `tenant_id` (string UUID, opcional).

---

## 4. Herramientas de Operación y Mitigación de Servicios

### `rosgrid_reconnect_pppoe_client`

- **Descripción:** Busca la sesión activa del cliente en `/ppp/active`, solicita su terminación limpia para forzar reconexión LCP y registra el evento en los logs de auditoría inmutables (WORM).
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `pppoe_username` (string, obligatorio): Nombre de usuario PPPoE de la sesión.
  - `reason` (string, obligatorio): Justificación técnica del reinicio.

### `rosgrid_isolate_subscriber`

- **Descripción:** Aplica aislamiento técnico preventivo sobre un abonado comprometido: lo incorpora a la lista de firewall `AISLADOS_TECNICO` y conmuta su cola de ancho de banda a 64k/64k simétricos.
- **Parámetros:**
  - `subscriber_device_id` (string UUID, obligatorio): Identificador del dispositivo o servicio.
  - `reason` (string, opcional): Motivo del aislamiento (ej. "Tráfico masivo SMTP puerto 25 detectado").
  - `idempotency_key` (string UUID, opcional): Llave de idempotencia para evitar duplicados.

### `rosgrid_restore_subscriber`

- **Descripción:** Restaura el servicio de un abonado previamente aislado: lo retira de `AISLADOS_TECNICO` y restablece su perfil nominal de ancho de banda y QoS.
- **Parámetros:**
  - `subscriber_device_id` (string UUID, obligatorio): Identificador del dispositivo o servicio.
  - `idempotency_key` (string UUID, opcional): Llave de idempotencia.

### `rosgrid_change_rate_limit`

- **Descripción:** Modifica en caliente el perfil de ancho de banda (Simple Queue / PCQ con Burst) del abonado sin interrumpir la conexión física ni desconectar la sesión PPPoE/IP.
- **Parámetros:**
  - `subscriber_device_id` (string UUID, obligatorio): Identificador del dispositivo o servicio.
  - `bandwidth_profile_id` (string UUID, obligatorio): Identificador del nuevo perfil.
  - `idempotency_key` (string UUID, opcional): Llave de idempotencia.

---

## 5. Herramientas de Auditoría, Diff y Seguridad

### `rosgrid_compare_config_diff`

- **Descripción:** Ejecuta el motor Diff estilo Git (`unified_diff`) sobre respaldos `.rsc` para que el operador o la IA identifiquen qué líneas cambiaron antes de un incidente.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `base_backup_id` (string UUID, obligatorio): Identificador del respaldo de origen.
  - `target_backup_id` (string UUID o `"LIVE"`, opcional): Respaldo de destino o configuración activa en vivo.

### `rosgrid_check_config_drift`

- **Descripción:** Audita desviaciones de configuración comparando el estado actual del router contra la Golden Baseline homologada por la empresa.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.

### `rosgrid_run_cis_audit`

- **Descripción:** Ejecuta la auditoría automatizada de seguridad CIS Benchmark para RouterOS v7, evaluando 10 directivas críticas y calculando el Security Score (0-100).
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.

---

## 6. Herramienta de Gobierno y Mutación Controlada

### `rosgrid_propose_network_change`

- **Descripción:** Propone una mutación de red sometida al flujo Maker-Checker (retorna `HTTP 202 Accepted`). Inserta la propuesta en la cola de aprobación humana y garantiza Safe Mode (60 segundos) al ser ejecutada.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `category` (string, obligatorio): Categoría crítica del cambio (ej. `FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE`, `ROUTING_BGP_OSPF_DEFAULT_CHANGE`).
  - `ros_path` (string, obligatorio): Ruta REST de RouterOS (ej. `/ip/firewall/filter`, `/ip/service`).
  - `http_method` (string enum: `["POST", "PATCH", "DELETE", "PUT"]`, obligatorio).
  - `payload` (object, obligatorio): Objeto JSON con los atributos de configuración de RouterOS v7.
  - `justification` (string, obligatorio): Justificación técnica formal visible en la interfaz para el aprobador.

---

## 7. Herramientas de Topología Física L2, Automatización PoE y Syslog Efímero

### `rosgrid_get_l2_topology`

- **Descripción:** Consulta el grafo de interconexión física de Capa 2 descubierto mediante paquetes MNDP, LLDP y CDP entre los enrutadores y switches del tenant. Devuelve las aristas verificadas puerto a puerto (ej. `RouterA:sfp1 <---> SwitchB:sfp24`), estado de enlace y velocidad negociada.
- **Parámetros:**
  - `router_id` (string UUID, opcional): Si se especifica, filtra solo las adyacencias directas de ese router; si se omite, retorna la matriz de toda la flota.

### `rosgrid_check_fleet_cves`

- **Descripción:** Evalúa de forma proactiva la versión activa de RouterOS de cada equipo contra el catálogo local soberano de vulnerabilidades CVE (sin fugas hacia servicios de nube externos).
- **Parámetros:**
  - `router_id` (string UUID, opcional): Filtrar por un router particular.
  - `min_severity` (string enum: `["CRITICAL", "HIGH", "MEDIUM", "ALL"]`, opcional, por defecto `"HIGH"`).

### `rosgrid_get_recent_syslog`

- **Descripción:** Lee del RingBuffer volátil en RAM de KeyDB los últimos eventos Syslog registrados para un router específico (máximo 500 retendidos en memoria). Permite identificar caídas físicas instantáneas (`link down`), desconexiones BGP y reinicios.
- **Parámetros:**
  - `router_id` (string UUID, obligatorio): Identificador del router.
  - `limit` (integer, opcional, rango 10 a 100, por defecto 30): Número de eventos recientes a retornar.
  - `topic_filter` (string, opcional): Filtrar por tópico (ej. `"interface"`, `"route,bgp"`, `"system,error"`).

### `rosgrid_execute_poe_aware_upgrade`

- **Descripción:** Genera una solicitud de actualización masiva con ordenamiento consciente de dependencias PoE (equipos alimentados PD se actualizan antes que los alimentadores PSE) y freno de seguridad (*Safety Stop*) ante fallos post-reinicio. Sometido al flujo Maker-Checker (`HTTP 202 Accepted`).
- **Parámetros:**
  - `router_ids` (array de string UUID, obligatorio): Lista de routers a actualizar.
  - `target_version` (string, obligatorio): Versión destino de RouterOS v7 (ej. `"7.16.1"`).
  - `safety_stop_threshold_percent` (float, opcional, por defecto 1.0): Porcentaje de fallos post-reinicio que detendrá automáticamente el resto del lote.
  - `justification` (string, obligatorio): Justificación formal del mantenimiento.
