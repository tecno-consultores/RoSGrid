# Especificación Técnica 91: Eliminación del Falso Positivo `0.0.0.0` en Detección de Anomalías de Tráfico, Paridad de Columnas en UI y Sondeo Real `/rest/ping` en Telemetría SLA (Hito 30.14)

**Estado:** `PROPOSED (READY FOR IMPLEMENTATION)`  
**Hito Asociado:** `Hito 30.14`  
**Prioridad:** `CRÍTICA (Bloqueante Operativo en Telemetría de SLA & Mitigación de Anomalías / FastDrop)`  
**Módulos Afectados:**
- Backend:
  - [`fastapi/src/api/v1/traffic_flow.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py)
  - [`fastapi/src/schemas/traffic_flow.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/traffic_flow.py)
  - [`fastapi/src/api/v1/sla.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/sla.py)
- Frontend:
  - [`vue3/src/views/EnterpriseComplianceView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue)
- Pruebas 11X:
  - [`fastapi/tests/unit/test_traffic_flow.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/unit/test_traffic_flow.unit.py)
  - [`fastapi/tests/unit/test_sla_tracker.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/unit/test_sla_tracker.unit.py)
  - [`vue3/src/views/EnterpriseComplianceView.unit.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.unit.ts)
  - [`fastapi/test/api_test.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/test/api_test.feature) y [`vue3/test/ui_business_flow.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature) (+ réplicas en `docs/examples/`)

---

## 1. Contexto y Diagnóstico de Causa Raíz (Root Cause Analysis)

Durante las pruebas operativas en `/enterprise/compliance?tab=sla` (**Flota & Seguridad -> Telemetría de SLA -> Detección de Anomalías de Tráfico & Mitigación en 1 Clic**), se identificaron tres defectos técnicos:

### 1.1. Falso Positivo de `0.0.0.0` como Anomalía de Tráfico (`GET /api/v1/traffic-flow/anomalies`)
- **Síntoma:** En la tabla **Detección de Anomalías de Tráfico & Mitigación en 1 Clic**, aparece `0.0.0.0` reportada con severidad `ANOMALÍA` y botón **FastDrop**, aun cuando el router se encuentra en estado normal sin ataques.
- **Causa Raíz 1 (Ausencia de filtro de direcciones RFC reservadas/no enrutables):**
  En [`_aggregate_connection_stats`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L71-L91) y [`_extract_ip_from_address`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L35-L45) (`fastapi/src/api/v1/traffic_flow.py`), al inspeccionar `/ip/firewall/connection` en RouterOS v7, las conexiones de control local (DHCP Discovery/Offer `0.0.0.0:68 -> 255.255.255.255:67`, BOOTP, MNDP, RoMON o sockets UDP sin dirección asignada) contienen `src-address="0.0.0.0:68"`. El extractor devuelve `"0.0.0.0"` sin descartar direcciones especiales no atribuibles a un host atacante:
  - `0.0.0.0` / `::` (`ip.is_unspecified`)
  - `127.0.0.0/8` / `::1` (`ip.is_loopback`)
  - `169.254.0.0/16` / `fe80::/10` (`ip.is_link_local`)
  - `224.0.0.0/4` / `ff00::/8` (`ip.is_multicast`)
  - `255.255.255.255` (Broadcast limitado)
  - Direcciones IP propias de las interfaces del router (`/rest/ip/address`).
- **Causa Raíz 2 (Cálculo erróneo de `estimated_pps` a partir del contador acumulado histórico `orig-packets`):**
  En [`traffic_flow.py#L82-L90`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L82-L90):
  ```python
  raw_pkts = item.get("orig-packets") or item.get("packets") or 1
  ...
  stats["count"] += 1
  stats["pps"] += max(1, orig_packets // 10)
  ```
  En RouterOS v7 (`/ip/firewall/connection`), `orig-packets` es el **contador acumulado durante toda la vida de la conexión** (por ejemplo, `1d 19h` de uptime), **no** paquetes por segundo (PPS). Una única sesión persistente o socket de control con `10,000` paquetes acumulados a lo largo de varios días recibe `stats["pps"] = 1000`, superando `threshold_pps=1000` con solo `1` conexión activa.
- **Riesgo de Mitigación (`FastDrop` sobre `0.0.0.0`):**
  Si el operador pulsa **FastDrop** sobre `0.0.0.0`, [`mitigate_traffic_anomaly`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L186-L245) inyecta `0.0.0.0` en `/ip/firewall/address-list` (`ROSGRID_FAST_DROP`) o `/ip/route` (`blackhole`), lo cual es inválido y peligroso.

### 1.2. Columnas `Conexiones Concurrentes` y `Tasa de Tráfico` mostrando `—` en [`EnterpriseComplianceView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue#L2395-L2403)
- **Síntoma:** En la fila de anomalía detectada, tanto **Conexiones Concurrentes** como **Tasa de Tráfico** muestran `—`.
- **Causa Raíz:** Desajuste de nombres de campos entre el esquema backend [`TrafficAnomalyItem`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/traffic_flow.py#L18-L30) y la plantilla Vue:
  - El backend serializa `connection_count` (`int`) y `estimated_pps` (`int`).
  - La vista [`EnterpriseComplianceView.vue#L2397-L2398`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue#L2397-L2398) lee `a.conns_count || a.conns || '—'` y `a.rate_mbps ? `${a.rate_mbps} Mbps` : '—'`.
  - Adicionalmente, en [`handleMitigateAnomaly`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue#L700-L712), si el usuario pulsa el botón superior **Mitigar Anomalía (FastDrop 300s)** cuando no hay anomalías, el código usa el fallback harcodeado `'198.51.100.99'`.

### 1.3. Timeout de `/rest/ping` en `POST /api/v1/sla/probes/run` ([`fastapi/src/api/v1/sla.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/sla.py#L305-L344))
- **Síntoma:** Al ejecutar sondeos SLA sobre `9.9.9.9` y `10.250.3.1`, ambos muestran exactamente los valores de contingencia (`14.5 ms`, `22 ms`, `35 ms`, `2.1 ms`).
- **Causa Raíz:** En [`run_sla_probe`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/sla.py#L316-L319), se invoca `client.post("/ping", json_data={"address": payload.target_host, "count": count})` con `count=10` o `count=20` sin especificar `interval`. En RouterOS v7, `/rest/ping` espera `1s` entre paquetes ICMP por defecto, tardando `10s–20s` y excediendo el timeout HTTP del cliente (`10s`), lo que dispara el bloque `except` con los valores estáticos `14.5 / 22.0 / 35.0 / 2.1`.

---

## 2. Diseño Técnico de la Solución (Instrucciones Exactas de Implementación)

### 2.1. Backend: Filtro RFC de IPs No Enrutables y Tasa Real en [`fastapi/src/api/v1/traffic_flow.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py)

1. **Función Validadora `_is_valid_anomaly_source_ip(ip_str: str, local_router_ips: set[str] | None = None) -> bool`:**
   Usar el módulo estándar `ipaddress` de Python para descartar cualquier dirección que NO sea un host válido de origen:
   ```python
   import ipaddress

   def _is_valid_anomaly_source_ip(
       ip_str: str,
       local_router_ips: set[str] | None = None,
   ) -> bool:
       """Descarta 0.0.0.0, broadcast, loopback, link-local, multicast e IPs propias del router."""
       if not ip_str or ip_str in {"0.0.0.0", "255.255.255.255", "::", "::1"}:
           return False
       if local_router_ips and ip_str in local_router_ips:
           return False
       try:
           ip_obj = ipaddress.ip_address(ip_str)
       except ValueError:
           return False
       if (
           ip_obj.is_unspecified
           or ip_obj.is_loopback
           or ip_obj.is_multicast
           or ip_obj.is_link_local
       ):
           return False
       return True
   ```

2. **Cálculo Preciso en `_aggregate_connection_stats` ([`traffic_flow.py#L71-L91`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L71-L91)):**
   - Filtrar `src_ip` mediante `_is_valid_anomaly_source_ip(src_ip, local_router_ips)`.
   - Para `pps`:
     - Si el elemento de `/ip/firewall/connection` incluye tasa instantánea (`orig-rate` en bps) o si el test/fixture provee `orig-pps` / `orig-packets`:
       - Si el ítem tiene `orig-rate` numérico (`> 0`), convertir `int(orig_rate) // (8 * 512)`.
       - Si solo tiene `orig-packets` (`packets`), **solo** usar `orig_packets // 10` cuando el ítem no proviene de una única sesión aislada o exigir en `_analyze_connections` que para `HIGH_PPS_BURST` basado en estimación de paquetes exista un mínimo de actividad concurrente (`count >= 3` o `orig-packets` explícito en ráfaga sobre una IP válida no reservada).
     - Con el filtro `_is_valid_anomaly_source_ip`, `0.0.0.0`, `127.0.0.1`, `255.255.255.255`, `169.254.x.x`, `224.x.x.x` y las IPs locales de las interfaces del router jamás entrarán al mapa `ip_stats`.
   - En `detect_traffic_anomalies` ([`traffic_flow.py#L140-L183`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L140-L183)), obtener opcionalmente `/ip/address` (de forma tolerante a fallos) para extraer las IPs locales del propio router (`address.split("/")[0]`) y pasarlas como `local_router_ips` a `_analyze_connections(conns_list, threshold_conns, threshold_pps, local_router_ips=local_ips)`.

3. **Guardrail en `POST /api/v1/traffic-flow/mitigate` ([`traffic_flow.py#L186-L245`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/traffic_flow.py#L186-L245)):**
   - Antes de abrir sesión con el router, validar `_is_valid_anomaly_source_ip(payload.target_ip.split("/")[0].strip())`.
   - Si devuelve `False` (por ejemplo, `0.0.0.0`, `127.0.0.1`, `255.255.255.255`, multicast o link-local), lanzar `HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Dirección IP reservada o inválida para mitigación FastDrop/Blackhole.")`.

### 2.2. Frontend: Paridad de Columnas y Botón de Mitigación en [`vue3/src/views/EnterpriseComplianceView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue)

1. **Renderizado de Columnas en la Tabla de Anomalías ([`EnterpriseComplianceView.vue#L2395-L2408`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue#L2395-L2408)):**
   Actualizar las celdas para soportar los campos canónicos de `TrafficAnomalyItem` (`connection_count`, `estimated_pps`, `anomaly_type`, `severity`):
   ```html
   <tr v-for="a in trafficAnomalies" :key="a.ip_address || a.ip">
     <td class="font-mono text-cyan">{{ a.ip_address || a.ip }}</td>
     <td class="font-mono">{{ a.connection_count ?? a.conns_count ?? a.conns ?? '—' }}</td>
     <td class="font-mono">
       {{ a.rate_mbps ? `${a.rate_mbps} Mbps` : (a.estimated_pps != null ? `${a.estimated_pps} pps` : '—') }}
     </td>
     <td>
       <span class="badge-danger">{{ a.severity || 'ANOMALÍA' }}</span>
       <span v-if="a.anomaly_type" class="text-xs text-muted" style="margin-left: 0.35rem;">({{ a.anomaly_type }})</span>
     </td>
     <td>
       <button class="btn-action-amber btn-xs" :disabled="loading" @click="handleMitigateAnomaly(a.ip_address || a.ip)">
         🛡️ FastDrop
       </button>
     </td>
   </tr>
   ```

2. **Eliminación de IP Harcodeada en `handleMitigateAnomaly` ([`EnterpriseComplianceView.vue#L700-L712`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.vue#L700-L712)):**
   - Deshabilitar el botón superior **Mitigar Anomalía (FastDrop 300s)** cuando `trafficAnomalies.length === 0` (`:disabled="loading || trafficAnomalies.length === 0"`).
   - En `handleMitigateAnomaly(ip?: string)`, resolver `const targetIp = ip || trafficAnomalies.value[0]?.ip_address || trafficAnomalies.value[0]?.ip` y, si `!targetIp || targetIp === '0.0.0.0'`, mostrar `errorMsg.value = 'No hay ninguna IP anómala válida seleccionada para mitigar.'` y abortar sin llamar a la API.

### 2.3. Backend: Sondeo `/rest/ping` Rápido en Tiempo Real en [`fastapi/src/api/v1/sla.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/sla.py)

En [`run_sla_probe`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/sla.py#L305-L336):
- Limitar los paquetes ICMP del sondeo interactivo o usar intervalo sub-segundo compatible con RouterOS v7 (`/rest/ping`):
  - En RouterOS v7 `/rest/ping`, enviar `{"address": payload.target_host, "count": min(count, 5)}` (5 paquetes ICMP toman `~4s`, completando holgadamente dentro del timeout de `10s` del cliente HTTP sin requerir parámetros no soportados).
  - Si `ping_res` devuelve diccionarios con `time` real (`"4ms520us"`, `"12ms"`, `"850us"`, o `avg-rtt` / `min-rtt` / `max-rtt`), extraer también `avg-rtt` / `max-rtt` como respaldo si `time` no viene en algún paquete individual, asegurando que la tabla de SLA refleje la latencia real medida desde el router MikroTik hacia `9.9.9.9` y el Gateway WAN.

---

## 3. Criterios de Aceptación y Pirámide de Pruebas 11X

1. **Pruebas Unitarias Backend:**
   - En [`fastapi/tests/unit/test_traffic_flow.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/unit/test_traffic_flow.unit.py):
     - Verificar que conexiones en `/ip/firewall/connection` con `src-address="0.0.0.0:68"`, `127.0.0.1:53`, `255.255.255.255:67`, `169.254.1.10:1234`, `224.0.0.5` o la propia IP del router (`10.250.3.20`) sean **excluidas al 100%** y devuelvan `anomalies_detected == 0`.
     - Verificar que `POST /api/v1/traffic-flow/mitigate` con `target_ip="0.0.0.0"` o `target_ip="127.0.0.1"` sea rechazado con `HTTP 422`.
   - En [`fastapi/tests/unit/test_sla_tracker.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/unit/test_sla_tracker.unit.py):
     - Verificar que `POST /api/v1/sla/probes/run` limite la ráfaga interactiva de `/ping` para no agotar el timeout HTTP y calcule RTT real.
2. **Pruebas Unitarias Frontend:**
   - En [`vue3/src/views/EnterpriseComplianceView.unit.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/EnterpriseComplianceView.unit.ts):
     - Verificar que la tabla de anomalías renderice `connection_count` y `estimated_pps` (`pps`) en lugar de `—`, y que el botón de mitigación superior esté deshabilitado cuando `trafficAnomalies` está vacío.
3. **Escenarios BDD Karate Labs:**
   - Añadir validación en [`fastapi/test/api_test.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/test/api_test.feature) y [`vue3/test/ui_business_flow.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature) (y réplicas en `docs/examples/`).
