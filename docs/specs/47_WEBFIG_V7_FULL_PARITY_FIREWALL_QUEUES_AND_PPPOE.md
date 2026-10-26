# 47 — WEBFIG v7 CAPA 1: PARIDAD TOTAL, MODALES DE CREACIÓN DE REGLAS DE FIREWALL, SIMPLE QUEUES CON PRESETS Y GESTIÓN ACTIVA PPPoE (RoSGrid)

**Autor:** RoSGrid Architecture Team & Antigravity AI Assistant  
**Fecha:** 26 de Octubre de 2026  
**Estado:** ESPECIFICACIÓN TÉCNICA OFICIAL (Hito 27 — Fase 1)  
**Ámbito:** `vue3/src/views/FirewallRulesView.vue`, `vue3/src/views/PppAndQueuesView.vue`, `fastapi/src/api/v1/webfig_firewall.py`, `fastapi/src/api/v1/webfig_queues.py`, `fastapi/src/api/v1/webfig_ppp.py`

---

## 1. Justificación y Objetivos de la Fase 1

Eliminar de raíz la condición de "solo lectura" en los módulos más utilizados de la consola WebFig:
1. **Firewall:** Permitir la adición y edición reactiva de reglas en las tablas *Filter*, *NAT*, *Mangle* y *RAW*, con posicionamiento asistido (`place-before`), soporte de Safe Mode automático (60s) y Maker-Checker en cadena `input`.
2. **Simple Queues (QoS):** Permitir la creación y edición de colas simples de limitación de ancho de banda con botones de presets rápidos (`10M`, `50M`, `100M`, `300M`, `1G`), burst y semáforo cromático de saturación en tiempo real.
3. **PPPoE Operativo:** Incorporar la acción de desconexión inmediata de clientes activos (*Kick Session*), así como la edición y borrado de Secrets y Profiles.

---

## 2. Especificación Técnica: Firewall Rules (`FirewallRulesView.vue`)

### 2.1 Botonera de Acciones Superior
- En cada pestaña (*Filter*, *NAT*, *Mangle*, *RAW*, *Address-Lists*), añadir la barra de herramientas táctica:
  - `[ + Nueva Regla ]`: Abre el modal unificado adaptado a la tabla activa.
  - `[ 🔄 Resetear Contadores ]`: Reinicia a cero los contadores de bytes y paquetes de la tabla actual.
  - `[ ⚡ Safe Mode ]`: Estado y conmutador manual del Dead Man's Switch.

### 2.2 Modal de Creación / Edición de Regla de Firewall (`RgFirewallRuleModal.vue`)
- **Campos Principales:**
  - `table_type`: Oculto/determinado por la pestaña activa (`filter`, `nat`, `mangle`, `raw`).
  - `chain`: Desplegable contextual dependiente de la tabla:
    - *Filter:* `input`, `forward`, `output`, o cadena personalizada.
    - *NAT:* `srcnat`, `dstnat`.
    - *Mangle:* `prerouting`, `input`, `forward`, `output`, `postrouting`.
    - *RAW:* `prerouting`, `output`.
  - `action`: Desplegable de acciones nativas RouterOS v7:
    - *Filter:* `accept`, `drop`, `reject`, `fasttrack-connection`, `jump`, `return`, `log`.
    - *NAT:* `masquerade`, `dst-nat`, `src-nat`, `redirect`.
    - *Mangle:* `mark-packet`, `mark-connection`, `mark-routing`, `change-mss`, `accept`.
  - `protocol`: `tcp`, `udp`, `icmp`, `gre`, `esp`, `any`.
  - `src_address` / `dst_address`: Inputs con validación CIDR o IP única.
  - `src_port` / `dst_port`: Input numérico o rango (ej. `80,443` o `1000-2000`).
  - `in_interface` / `out_interface`: Desplegables alimentados dinámicamente desde el inventario de interfaces del router.
  - `comment`: Texto explicativo obligatorio para auditoría.
  - `place_before`: Posicionamiento exacto (ID de regla antes de la cual se insertará la nueva regla).
- **Campos Específicos para NAT:**
  - Si `action == 'dst-nat'`: `to_addresses` (IP destino LAN) y `to_ports` (Puerto destino LAN).
  - Si `action == 'src-nat'`: `to_addresses` (IP pública fija de salida).
- **Campos Específicos para Mangle:**
  - `new_packet_mark`, `new_connection_mark`, `passthrough` (boolean).
- **Gobernanza de Seguridad:**
  - Si `chain == 'input'` y `action == 'drop'`: Advertencia visual roja y activación forzada de Safe Mode de 60 segundos. Si el usuario tiene rol inferior a `SUPPORT_L3`, intercepción HTTP 202 Maker-Checker.

---

## 3. Especificación Técnica: Simple Queues (`PppAndQueuesView.vue`)

### 3.1 Modal de Creación / Edición de Cola Simple (`RgSimpleQueueModal.vue`)
- **Campos:**
  - `name`: Nombre de la cola (ej. `queue-cliente-101`).
  - `target`: IP o prefijo CIDR del cliente (ej. `192.168.88.25/32` o `10.10.10.0/24`).
  - `max_limit`: Límite en formato RouterOS `Upload/Download` (ej. `20M/50M`).
  - **Barra de Presets Tácticos en 1 Clic:**
    - `[ 10M / 10M ]`
    - `[ 25M / 50M ]`
    - `[ 50M / 100M ]`
    - `[ 100M / 300M ]`
    - `[ 200M / 600M ]`
    - `[ 1 Gbps Simétrico ]`
  - `parent`: Selector de cola padre para contención (*Parent Queue*).
  - `priority`: Selector de prioridad QoS de 1 (máxima) a 8 (mínima). Por defecto 8/8.
  - `burst_limit`, `burst_threshold`, `burst_time`: Opciones avanzadas colapsables.
  - `comment`: Comentario de identificación del abonado.
- **Visualización en Tabla:**
  - Barra de progreso interactiva calculada con `rate / max_limit`:
    - 🟢 < 70% de utilización.
    - 🟡 70% a 90% de utilización.
    - 🔴 > 90% (Saturación crítica de enlace).

---

## 4. Especificación Técnica: PPPoE Operativo (`PppAndQueuesView.vue`)

### 4.1 Desconexión Inmediata (Kick Session)
- En la pestaña `PPPoE Activo`, añadir botón `[ ⏏ Desconectar ]` por cada fila.
- **Endpoint de Backend:** `DELETE /api/v1/routers/{router_id}/webfig/ppp/active/{session_id}`.
- Invoca en RouterOS v7: `DELETE /rest/ppp/active/{session_id}`.
- Confirmación mediante diálogo modal accesible con tecla `Escape` o `Enter`.
- Actualización inmediata de la lista de sesiones activas sin recarga de página.

### 4.2 Edición y Borrado de Secrets y Profiles
- Añadir botones de acción por fila en las tablas `Secrets` y `Profiles`:
  - `[ ✏ Editar ]`: Abre el modal con datos pre-cargados.
  - `[ ⏸ Deshabilitar / ▶ Habilitar ]`: Conmuta la bandera `disabled` mediante `PATCH`.
  - `[ 🗑 Eliminar ]`: Confirmación previa y eliminación mediante `DELETE`.

---

## 5. Gobernanza 11X de Calidad y Pruebas Requeridas

1. **Backend Pytest:**
   - Tests unitarios en `tests/api/test_webfig_firewall_mutations.unit.py` validando creación con `place-before`, Safe Mode y 403/202 en cadena `input`.
   - Tests unitarios en `tests/api/test_webfig_queues_mutations.unit.py` validando creación con presets y borrado.
   - Tests unitarios en `tests/api/test_webfig_ppp_kick.unit.py` validando la expulsión de sesiones activas.
2. **Frontend Vitest:**
   - Tests en `FirewallRulesView.unit.ts` y `PppAndQueuesView.unit.ts` certificando el renderizado de modales, envío de payloads y reactividad del semáforo.
3. **Karate Labs BDD:**
   - Escenarios de creación de reglas y expulsión de clientes PPPoE en `api_test.feature` y `ui_business_flow.feature`.
