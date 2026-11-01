# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación Técnica 60: Auditoría Integral Bidireccional de Endpoints Huérfanos, Corrección de Rutas Desalineadas (404/405) y Paridad Total Backend ↔ Frontend Vue 3

> **Hito de Referencia:** Hito 28 (`28.5`) — Mejoras Operativas de Pruebas Manuales (UAT)  
> **Estado:** Completado y Certificado al 100% en Docker Efímero (Rule Zero & Nivel 11X)  
> **Reglas de Gobernanza Aplicables:** `.agents/rules/frontend_parity_and_closure.md`, `.agents/rules/mandatory_qa_pyramid_and_doc_sync.md`, `.agents/rules/anti_regression_and_side_effects_guardrail.md`

---

## 1. Resumen Ejecutivo de la Auditoría Bidireccional (`OpenAPI` ↔ `vue3/src/`)

En cumplimiento de la directiva `.agents/rules/frontend_parity_and_closure.md` (*"Terminal ↔ Frontend Parity: Zero console-only actions or orphan API endpoints without a matching Vue 3 interface"*), se ejecutó una inspección estática bidireccional automatizada cruzando las **374 operaciones HTTP registradas en las 271 rutas de `app.openapi()` (`fastapi/src/api/router.py`)** contra las llamadas `http.get` / `http.post` / `http.put` / `http.patch` / `http.delete` en los **99 archivos fuente de `vue3/src/`**.

Los resultados se dividen en **4 categorías exactas**:

---

### Categoría 1: 5 Desajustes de Ruta / Método Front ↔ Back (`404 Not Found` / `405 Method Not Allowed` Silenciosos)

Son acciones donde **el botón o formulario ya existe en la interfaz Vue 3**, pero la URL o el verbo HTTP invocado difiere ligeramente de la ruta registrada en FastAPI (lo cual hacía que ambos extremos parecieran "huérfanos" en el cruce cruzado):

| # | Archivo Frontend (`vue3/src/...`) | Llamada Actual en Frontend | Ruta Real Registrada en FastAPI | Impacto en UAT | Solución Flash-Ready |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `components/inventory/VaultRevealModal.vue` (L137) | `POST /api/v1/vault/routers/${id}/rotate` | `POST /api/v1/inventory/routers/{router_id}/vault/rotate-now` (`vault.py`) | El botón `🔄 Rotar Clave API` falla con 404 en producción. | Añadir alias `/api/v1/vault/routers/{router_id}/rotate` en `vault.py` y alinear `VaultRevealModal.vue`. |
| **2** | `components/inventory/VaultRevealModal.vue` (L158) | `POST /api/v1/vault/routers/${id}/repin-ssl` | `POST /api/v1/inventory/routers/{router_id}/repin-ssl` (`inventory.py`) | El botón `📌 Re-Anclar SSL TOFU` falla con 404 en producción. | Añadir alias `/api/v1/vault/routers/{router_id}/repin-ssl` en `inventory.py` y alinear `VaultRevealModal.vue`. |
| **3** | `views/EnterpriseComplianceView.vue` (L592) | `POST /api/v1/sdwan/spokes` | `POST /api/v1/sdwan/provision-spoke` (`sdwan.py`) | El botón `➕ Aprovisionar Spoke WireGuard` en la pestaña SD-WAN falla con 404. | Registrar ambos paths (`/provision-spoke` y `/spokes`) en `sdwan.py` y alinear `EnterpriseComplianceView.vue`. |
| **4** | `views/EnterpriseComplianceView.vue` (L616) | `POST /api/v1/sdwan/multi-wan/failover` | `POST /api/v1/sdwan/multi-wan-failover` (`sdwan.py`) | El botón `⚡ Desplegar Failover Multi-WAN` en la pestaña SD-WAN falla con 404. | Registrar ambos paths (`/multi-wan-failover` y `/multi-wan/failover`) en `sdwan.py` y alinear `EnterpriseComplianceView.vue`. |
| **5** | `views/DynamicLayer2ResourceView.vue` (L409) | `PATCH /api/v1/routers/${id}/webfig/layer2/resource/${rosPath}` | Solo existía `PATCH .../resource/{ros_path:path}/{item_id}` (`webfig_layer2.py`) | Al guardar un menú singleton en Capa 2 (ej. `system/ntp/client` o `ip/settings`) vía `PATCH`, si `rosPath` no tiene `item_id` o tiene 1 solo segmento, carece de ruta singleton explícita. | Añadir endpoint `PATCH /routers/{router_id}/webfig/layer2/singleton/{ros_path:path}` y soporte en `update_layer2_resource` cuando el recurso es singleton. |

---

### Categoría 2: Endpoints Operativos Huérfanos que Requieren Interfaz / Botón Táctico en Vue 3

Son endpoints de negocio completamente implementados en FastAPI que aún no tenían su botón, modal o sub-pestaña conectada en el frontend:

| Sub-módulo | Endpoints Huérfanos en Backend | Vista Vue 3 Destino | Acción UI a Incorporar |
| :--- | :--- | :--- | :--- |
| **1. Seguridad L2 & DHCP Snooping** *(Cubierto en Spec 59 / Hito 28.4)* | `POST /api/v1/switching/dhcp-snooping/enable` | `EnterpriseComplianceView.vue` (`tab=switching`) | Botón `[ ⚡ Activar DHCP Snooping ]` / `[ ⚙️ Configurar ]` en cada tarjeta de Bridge + botón `[ 🚀 Desplegar en Flota ]`. |
| **2. Perfiles de Ancho de Banda (QoS) y Gestión de Servicio de Abonados** | `GET / POST / PATCH / DELETE /api/v1/bandwidth-profiles`<br>`GET /api/v1/bandwidth-profiles/{id}/mikrotik-script`<br>`POST /api/v1/subscriber-devices/simulate-from-dhcp`<br>`GET /api/v1/subscriber-devices/{id}/mikrotik-queue-script`<br>`GET /api/v1/network-services/{id}`<br>`POST /api/v1/network-services/{id}/isolate`<br>`POST /api/v1/network-services/{id}/restore`<br>`POST /api/v1/network-services/{id}/change-rate-limit` | `IpamManagementView.vue` y `SubscribersMapView.vue` | Pestaña/Modal de **Planes de Ancho de Banda (`Bandwidth Profiles`)**, botón **`[ 🔄 Importar/Simular desde DHCP ]`** y acciones por abonado **`[ 🔒 Suspender (Isolate) ]`**, **`[ 🟢 Reconectar (Restore) ]`**, **`[ ⚡ Cambiar Plan QoS ]`** y **`[ 📜 Script Queue CLI ]`**. |
| **3. BGP Looking Glass y Detección/Mitigación de Anomalías de Tráfico** | `GET /api/v1/bgp/looking-glass/route`<br>`GET /api/v1/bgp/looking-glass/advertised`<br>`GET /api/v1/traffic-flow/anomalies`<br>`POST /api/v1/traffic-flow/mitigate` | `RoutingBgpOspfView.vue` y `EnterpriseComplianceView.vue` | Sub-pestaña **`🔍 BGP Looking Glass`** en `RoutingBgpOspfView.vue` (consulta de ruta específica y prefijos anunciados a peer) y tarjeta/panel **`🚨 Anomalías de Tráfico & Mitigación en 1 Clic`** en `EnterpriseComplianceView.vue`. |
| **4. Diagnóstico 360° de Abonado/Endpoint** | `POST /api/v1/diagnostics/endpoint-360` | `FieldTechOperationsView.vue` / `FieldTechMobileView.vue` | Botón **`[ 🩺 Ejecutar Diagnóstico 360° (Ping Multi-MTU + Logs + Torch) ]`** en la pestaña de Diagnósticos del Panel de Técnico de Campo. |
| **5. Telemetría Anónima de Instancia (`Beacon`)** | `GET /api/v1/system/telemetry-beacon/status`<br>`POST /api/v1/system/telemetry-beacon/trigger` | `TenantsManagementView.vue` | Tarjeta compacta en la cabecera de Administración de Empresas mostrando el estado del Beacon (`instance_id` anónimo, último latido) y botón **`[ 📡 Emitir Latido Ahora ]`**. |
| **6. WebFig Interfaces: Cable Test Ethernet (TDR) y Tabla Wi-Fi** | `POST /api/v1/routers/{id}/webfig/interfaces/ethernet/{item_id}/cable-test`<br>`GET /api/v1/routers/{id}/webfig/interfaces/wifi/registration-table` | `InterfacesAndSfpView.vue` | Botón por fila **`[ 🔌 Cable Test ]`** en interfaces Ethernet para diagnosticar pares abiertos/cortocircuitos y sub-pestaña **`📶 Clientes Wi-Fi Registrados`**. |
| **7. WebFig Firewall: Tabla de Conexiones Activas (`Conntrack`)** | `GET /api/v1/routers/{id}/webfig/firewall/connections`<br>`DELETE /api/v1/routers/{id}/webfig/firewall/connections/{conn_id}` | `FirewallRulesView.vue` | Sub-pestaña **`🔗 Conexiones Activas (Conntrack)`** con buscador por IP/puerto y botón **`[ ✕ Cortar Conexión ]`**. |
| **8. WebFig Colas: Reordenamiento (`Move`) y `Queue Tree` / `Queue Types`** | `POST /api/v1/routers/{id}/webfig/queues/simple/move`<br>`GET / POST / PATCH / DELETE /api/v1/routers/{id}/webfig/queues/tree`<br>`GET /api/v1/routers/{id}/webfig/queues/types` | `PppAndQueuesView.vue` | Conectar el evento `@move-row` en Simple Queues a `/queues/simple/move` y añadir la sub-pestaña **`🌳 Queue Tree (HTB) & Tipos`**. |
| **9. WebFig Routing: Sub-pestañas OSPF (Instancias/Áreas/Plantillas), BFD y Filtros de Ruteo** | `GET /api/v1/routers/{id}/webfig/routing/ospf/instances`<br>`GET /api/v1/routers/{id}/webfig/routing/ospf/areas`<br>`GET /api/v1/routers/{id}/webfig/routing/ospf/interface-templates`<br>`GET /api/v1/routers/{id}/webfig/routing/bfd/sessions`<br>`GET / POST / PATCH / DELETE /api/v1/routers/{id}/webfig/routing/filters/rules`<br>`GET /api/v1/routers/{id}/webfig/routing/bgp/templates`<br>`GET /api/v1/routers/{id}/webfig/routing/bgp/advertisements` | `RoutingBgpOspfView.vue` | Enriquecer la pestaña OSPF con sus tablas de **Instancias, Áreas e Interface-Templates**, la pestaña BGP con **Templates y Advertisements**, y añadir sub-pestañas **`🛡️ Filtros de Ruteo (`/routing/filter/rule`)`** y **`⚡ Sesiones BFD`**. |
| **10. WebFig Capa 2 Universal: Introspección y Catálogo RPC desde Backend** | `GET /api/v1/routers/{id}/webfig/layer2/inspect/{ros_path}`<br>`GET /api/v1/routers/{id}/webfig/layer2/rpc-catalog/{ros_path}` | `DynamicLayer2ResourceView.vue` | Consultar `/rpc-catalog/${rosPath}` al cargar el recurso y disponer de botón **`[ 🔍 Introspeccionar Esquema RouterOS ]`** que invoca `/inspect/${rosPath}`. |

---

### Categoría 3: Endpoints Consumidos por Sistemas Externos, Aliases BDD o Motor Universal Capa 2 (No Huérfanos)

Para trazabilidad en el validador automatizado `.agents/scripts/verify_no_orphan_api_endpoints.py`, los siguientes endpoints se declaran en la lista blanca de arquitectura (`ARCHITECTURAL_EXTERNAL_OR_LAYER2_ENDPOINTS`):

1. **Observabilidad & Healthchecks Externos:**
   - `GET /health`, `GET /api/v1/health`, `GET /metrics`, `GET /api/v1/metrics/fleet` (consumidos por Docker healthcheck, Prometheus scraper y `httpClient.ts`).
2. **Protocolo MCP para Agentes IA Externos:**
   - `POST /api/v1/mcp` (consumido por Claude Code, Claude Desktop, Cursor, Hermes Agent).
3. **Aliases de Compatibilidad Retroactiva y Contratos BDD:**
   - `GET /users/me`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout` (invocados por suites BDD y clientes API).
   - `PUT /api/v1/tenants/{tenant_id}/features` (alias de `PATCH /api/v1/tenants/{tenant_id}/features`).
   - `POST /api/v1/wifi/capsman/{router_id}/ssids` (alias retrocompatible de `POST .../configurations`).
   - `GET /api/v1/routers/{router_id}/webfig/firewall/{proto}/connection` y `/connections`, `/address-list` (aliases singulares/plurales).
4. **Endpoints L1 de Sistema/IP/PPP Atendidos por el Motor Universal Capa 2 (`DynamicLayer2ResourceView.vue`):**
   - `/webfig/system/identity`, `/webfig/system/live-status`, `/webfig/system/packages`, `/webfig/system/reboot`, `/webfig/system/scheduler`, `/webfig/system/scripts`, `/webfig/system/users`, `/webfig/ip/neighbors`, `/webfig/ip/services`, `/webfig/ppp/ipsec/active-peers`: estas rutas permanecen disponibles para clientes REST/MCP y, además, en `RouterLiveDashboardView.vue` se conectarán los botones rápidos de **`[ ✏️ Cambiar Identidad ]`** (`PATCH .../webfig/system/identity`) y **`[ 🔄 Reiniciar Router ]`** (`POST .../webfig/system/reboot`) para acceso táctico desde el Dashboard en Vivo del router.

---

## 2. Blueprint "Flash-Ready" Paso a Paso (Para Ejecución por Gemini 3.8 Flash High)

### 2.1. Corrección Inmediata de los 5 Desajustes de Ruta Front ↔ Back (`28.5.1`)

#### A. En `vue3/src/components/inventory/VaultRevealModal.vue` (líneas 137 y 158):

- **Target:**
```typescript
    try {
      await http.post(`/api/v1/vault/routers/${props.router.id}/rotate`);
      successMessage.value = 'Rotación de clave API ejecutada exitosamente.';
      emit('rotated', props.router.id);
      purgeSecretMemory();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al rotar la clave de la API.';
    } finally {
      isOperating.value = false;
    }
  }

  async function handleRepinSsl() {
    if (!props.router) return;
    if (!confirm('¿Confirmas el Re-Pinning del certificado SSL TOFU de este router?')) {
      return;
    }

    isOperating.value = true;
    errorMessage.value = '';
    try {
      await http.post(`/api/v1/vault/routers/${props.router.id}/repin-ssl`);
```

- **Replacement:**
```typescript
    try {
      await http.post(`/api/v1/inventory/routers/${props.router.id}/vault/rotate-now`);
      successMessage.value = 'Rotación de clave API ejecutada exitosamente.';
      emit('rotated', props.router.id);
      purgeSecretMemory();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al rotar la clave de la API.';
    } finally {
      isOperating.value = false;
    }
  }

  async function handleRepinSsl() {
    if (!props.router) return;
    if (!confirm('¿Confirmas el Re-Pinning del certificado SSL TOFU de este router?')) {
      return;
    }

    isOperating.value = true;
    errorMessage.value = '';
    try {
      await http.post(`/api/v1/inventory/routers/${props.router.id}/repin-ssl`);
```

*(Nota: Actualizar cualquier test en `vue3/src/` que verifique la URL de `rotate` o `repin-ssl` en `VaultRevealModal`, y añadir además los alias `@router.post("/vault/routers/{router_id}/rotate")` en `vault.py` y `@router.post("/vault/routers/{router_id}/repin-ssl")` en `inventory.py` para compatibilidad retroactiva total).*

#### B. En `vue3/src/views/EnterpriseComplianceView.vue` (líneas 592 y 616) y `fastapi/src/api/v1/sdwan.py`:

En `vue3/src/views/EnterpriseComplianceView.vue`:
- Cambiar `await http.post('/api/v1/sdwan/spokes', {` por `await http.post('/api/v1/sdwan/provision-spoke', {`.
- Cambiar `'/api/v1/sdwan/multi-wan/failover',` por `'/api/v1/sdwan/multi-wan-failover',`.
- Y en `fastapi/src/api/v1/sdwan.py`, añadir un segundo decorador `@router.post("/spokes", ... include_in_schema=False)` sobre `provision_spoke_tunnel` y `@router.post("/multi-wan/failover", ... include_in_schema=False)` sobre `deploy_multi_wan_failover` para que tanto la ruta canónica como el alias funcionen sin romper ningún test existente.

#### C. En `fastapi/src/api/v1/webfig_layer2.py`:

Añadir soporte para `PATCH /routers/{router_id}/webfig/layer2/resource/{ros_path:path}` cuando `ros_path` corresponde a un menú singleton en `_SINGLETON_PATHS` (como `system/ntp/client`, `ip/dns`, `ip/settings`, `system/identity`, `system/clock`), de modo que si el último segmento no es un `.id` sino parte del menú singleton, invoque `POST /rest/{ros_path}/set` con el payload recibido.

---

### 2.2. Conexión de Endpoints Operativos de ISP, Abonados y Diagnóstico 360° (`28.5.2`)

1. **En `vue3/src/views/IpamManagementView.vue`:**
   - Añadir pestaña/sección **`⚡ Planes de Ancho de Banda (Bandwidth Profiles)`** que consuma:
     - `GET /api/v1/bandwidth-profiles` (listar perfiles QoS).
     - `POST /api/v1/bandwidth-profiles` (crear perfil QoS).
     - `PATCH /api/v1/bandwidth-profiles/{profile_id}` (editar perfil QoS).
     - `DELETE /api/v1/bandwidth-profiles/{profile_id}` (eliminar perfil QoS).
     - `GET /api/v1/bandwidth-profiles/{profile_id}/mikrotik-script` (mostrar modal con script RouterOS v7).
   - En la barra de acciones de Abonados (`Subscriber Devices`), añadir el botón **`[ 🔄 Importar / Simular desde DHCP ]`** (`#btn-simulate-dhcp-subscribers`) que invoca `POST /api/v1/subscriber-devices/simulate-from-dhcp` y recarga la tabla, además de botones por fila para **`[ 📜 Script Queue ]`** (`GET /api/v1/subscriber-devices/{id}/mikrotik-queue-script`) y acciones de servicio (`POST /api/v1/network-services/{id}/isolate`, `/restore`, `/change-rate-limit`).
2. **En `vue3/src/components/field/FieldTechMobileView.vue` (pestaña `⚡ Diagnósticos y Certificación`):**
   - Añadir el botón **`[ 🩺 Ejecutar Diagnóstico 360° ]`** (`#btn-run-diagnostics-360`) que invoque `POST /api/v1/diagnostics/endpoint-360` y muestre el resultado de Ping Multi-MTU, logs de desconexión y muestreo Torch.

---

### 2.3. Conexión de BGP Looking Glass, Anomalías de Tráfico y Telemetría Beacon (`28.5.3`)

1. **En `vue3/src/views/RoutingBgpOspfView.vue`:**
   - Añadir en la pestaña BGP un panel interactivo **`🔍 BGP Looking Glass`** que permita consultar:
     - `GET /api/v1/bgp/looking-glass/route?router_id=${routerId.value}&dst_prefix=${prefix}`
     - `GET /api/v1/bgp/looking-glass/advertised?router_id=${routerId.value}&peer_name=${peer}`
   - Así como cargar `GET /api/v1/routers/${routerId.value}/webfig/routing/bgp/templates` y `/advertisements`.
2. **En `vue3/src/views/EnterpriseComplianceView.vue`:**
   - Añadir sección/tarjeta **`🚨 Detección de Anomalías de Tráfico & Mitigación`** que consulte `GET /api/v1/traffic-flow/anomalies?router_id=${selectedRouterId.value}` y ofrezca el botón **`[ 🛡️ Mitigar Anomalía ]`** (`POST /api/v1/traffic-flow/mitigate`).
3. **En `vue3/src/views/admin/TenantsManagementView.vue`:**
   - Añadir tarjeta de estado **`📡 Telemetría Anónima de Instancia (Beacon)`** que consulte `GET /api/v1/system/telemetry-beacon/status` y permita disparar un latido manual mediante **`[ ⚡ Emitir Latido Ahora ]`** (`POST /api/v1/system/telemetry-beacon/trigger`).

---

### 2.4. Conexión de Endpoints WebFig Especializados (Cable Test, Conntrack, Queue Tree, OSPF/BFD/Filtros, Identidad/Reboot) (`28.5.4`)

1. **`vue3/src/views/InterfacesAndSfpView.vue`:**
   - Añadir botón por fila **`[ 🔌 Cable Test ]`** en interfaces Ethernet que invoque `POST /api/v1/routers/${routerId.value}/webfig/interfaces/ethernet/${encodeURIComponent(iface.name)}/cable-test` y muestre el estado de los pares (`status`, ` cable-pairs`).
2. **`vue3/src/views/FirewallRulesView.vue`:**
   - Añadir sub-pestaña **`🔗 Conexiones (Conntrack)`** que consulte `GET /api/v1/routers/${routerId.value}/webfig/firewall/connections` y permita eliminar una conexión activa con `DELETE /api/v1/routers/${routerId.value}/webfig/firewall/connections/${encodeURIComponent(conn.id)}`.
3. **`vue3/src/views/PppAndQueuesView.vue`:**
   - Conectar el reordenamiento de Simple Queues a `POST /api/v1/routers/${routerId.value}/webfig/queues/simple/move` y añadir sub-pestaña **`🌳 Queue Tree (HTB)`** (`GET/POST/PATCH/DELETE /api/v1/routers/${routerId.value}/webfig/queues/tree` y `GET .../queues/types`).
4. **`vue3/src/views/RoutingBgpOspfView.vue`:**
   - Conectar en la pestaña OSPF las consultas a `/webfig/routing/ospf/instances`, `/areas` e `/interface-templates`; añadir sub-pestaña **`🛡️ Filtros de Ruteo`** (`GET/POST/PATCH/DELETE /webfig/routing/filters/rules`) y sección **`⚡ Sesiones BFD`** (`GET /webfig/routing/bfd/sessions`).
5. **`vue3/src/views/RouterLiveDashboardView.vue`:**
   - Añadir en la cabecera de acciones rápidas del Dashboard en Vivo del router los botones **`[ ✏️ Identidad ]`** (`PATCH /api/v1/routers/${routerId.value}/webfig/system/identity`), **`[ 🔄 Sincronizar Datos ]`** (`POST /api/v1/inventory/routers/${routerId.value}/sync-discovery`) y **`[ ⚠️ Reiniciar Router ]`** (`POST /api/v1/routers/${routerId.value}/webfig/system/reboot` con confirmación).

---

### 2.5. Guardrail Automatizado `.agents/scripts/verify_no_orphan_api_endpoints.py` (`28.5.5`)

Crear el script `.agents/scripts/verify_no_orphan_api_endpoints.py` e integrarlo en `.agents/scripts/certify_task_completion.sh`:
- Verifica en menos de 2 segundos que **ninguna llamada `http.<method>('/api/v1/...')` en `vue3/src/` apunte a una ruta inexistente (0 llamadas 404/405)**.
- Verifica que el 100% de las rutas de `app.openapi()` estén referenciadas en `vue3/src/` o declaradas explícitamente en `ARCHITECTURAL_EXTERNAL_OR_LAYER2_ENDPOINTS`.
