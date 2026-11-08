# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 97: Visibilidad Inmediata de Servidores y Redes DHCP en `IpAddressesAndDhcpView.vue` (Orden Canónico WinBox + Carga Paralela con Contadores) y Creación de Concesiones Estáticas DHCP (`POST /dhcp-server/leases`)

> **Estado:** Pendiente de Implementación (`[ ]`) — **Optimizado para Ejecución Directa por Gemini 3.8 Flash (High)**
> **Hito Asociado:** Hito 30.20 (`ROADMAP.md`)
> **Prioridad:** Alta (Visibilidad inmediata de los servidores y redes DHCP de `r1` y paridad CRUD completa para crear concesiones estáticas, servidores y redes desde `/routers/{id}/webfig/ip`)
> **Archivos Afectados:**
> 1. `fastapi/src/schemas/webfig_l1_net.py` (Añadir `DhcpLeaseCreateRequest`, añadir `comment` a `DhcpServerCreateRequest` y `DhcpServerUpdateRequest`, y añadir `ntp_server` a `DhcpNetworkCreateRequest`).
> 2. `fastapi/src/api/v1/webfig_ip.py` (Añadir `POST /dhcp-server/leases` -> `create_dhcp_lease` con Safe Mode e invalidación de caché KeyDB `/ip/dhcp-server/lease`, invalidar caché en `make_dhcp_lease_static`/`update_dhcp_lease`/`delete_dhcp_lease`, y soportar `comment` en `create_dhcp_server`/`update_dhcp_server` y `ntp_server` en `create_dhcp_network`).
> 3. `vue3/src/views/IpAddressesAndDhcpView.vue` (Cambiar sub-pestaña por defecto `activeDhcpSubtab` a `'servers'` siguiendo el orden de WinBox `Servidores DHCP | Redes & Opciones | Concesiones Activas (Leases)`, cargar en paralelo las 3 colecciones al entrar a `Servidor DHCP` con insignias de conteo `(N)`, mostrar `Comentario` en Servidores DHCP y `Servidor NTP` en Redes DHCP, añadir botón `#btn-create-dhcp-lease` `+ Añadir Concesión Estática` y su modal de creación, y exponer botones de creación rápida tanto en la cabecera como en la barra de sub-pestañas y en `Registros DNS Estáticos`).
> 4. `fastapi/tests/api/test_webfig_dhcp_and_ipv6.unit.py` (Pruebas unitarias backend para `create_dhcp_lease`, `comment` en servidor DHCP y `ntp_server` en red DHCP).
> 5. `vue3/src/views/ipAndIpv6Views.unit.ts` (Pruebas unitarias frontend verificando que `Servidores DHCP` es la sub-pestaña inicial con carga paralela y probando la creación de una concesión estática DHCP).
> 6. `fastapi/test/api_test.feature` + `docs/examples/fastapi/api_test.feature.example` (Escenario Karate Labs BDD 171).
> 7. `vue3/test/ui_business_flow.feature` + `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 111).

---

## 1. Diagnóstico Forense de Causa Raíz

Al contrastar la vista `/routers/a1c66d5d-01cf-41c6-b217-7d2117202a39/webfig/ip` (router **`r1`**) con **WinBox (`IP -> DHCP Server`)**:

1. **Por qué no se ven de inmediato los 3 Servidores DHCP (`dhcp-anillo`, `dhcp-aps`, `dhcp-cctv`) ni las 3 Redes DHCP (`192.168.10.0/24`, `192.168.20.0/24`, `192.168.30.0/24`) de `r1` al entrar a la pestaña `Servidor DHCP`:**
   - En MikroTik RouterOS v7 (`r1`), existen **3 servidores DHCP** en `/ip/dhcp-server` (`dhcp-anillo` sobre `bridge-anillo`, `dhcp-aps` sobre `vlan20-aps`, `dhcp-cctv` sobre `vlan30-cctv`), **3 redes DHCP** en `/ip/dhcp-server/network` (`192.168.10.0/24`, `192.168.20.0/24`, `192.168.30.0/24`) y **0 concesiones activas** en `/ip/dhcp-server/lease` (`[]`).
   - En WinBox (`DHCP Server`), el orden de pestañas es: **1º `DHCP` (Servidores)**, **2º `Networks` (Redes)** y **3º `Leases` (Concesiones)**.
   - En `vue3/src/views/IpAddressesAndDhcpView.vue` (línea 21), `activeDhcpSubtab` se inicializaba en `'leases'` (`Concesiones Activas (Leases)`) como primera sub-pestaña y `loadData()` solo consultaba la sub-pestaña activa. Por ello, al pulsar **`Servidor DHCP`**, el operador veía una tabla vacía (*«No hay concesiones DHCP activas actualmente.»*) sin contadores en las sub-pestañas `Servidores DHCP` y `Redes & Opciones` que indicaran que existen 3 servidores y 3 redes configurados.

2. **Por qué «no hay cómo agregar, pero cuando sí hay creados sí se pueden editar y eliminar»:**
   - En la sub-pestaña **`Concesiones Activas (Leases)`** (`activeTab === 'dhcp-server' && activeDhcpSubtab === 'leases'`), la cabecera superior (`.header-actions`, líneas 728–753 de `IpAddressesAndDhcpView.vue`) **no renderizaba ningún botón de creación** (solo mostraba `🔄 Refrescar`).
   - Cuando ya existen concesiones (`v-for="lease in dhcpLeases"`), cada fila de la tabla sí muestra los botones `✏️` (Editar) y `🗑` (Eliminar), **pero no existía ni el botón `+ Añadir Concesión Estática` ni el modal en el frontend, ni tampoco el endpoint `POST /api/v1/routers/{router_id}/webfig/ip/dhcp-server/leases` en `fastapi/src/api/v1/webfig_ip.py`** para registrar una reservación DHCP estática (`address`, `mac-address`, `server`, `rate-limit`, `comment`).
   - Además, los botones `+ Crear Servidor DHCP`, `⚡ Asistente DHCP Setup` y `+ Crear Red DHCP` desaparecían por completo de la vista mientras el usuario estaba en la sub-pestaña `Leases`, y en la pestaña `DNS & Registros` la tarjeta inferior `Registros DNS Estáticos` no tenía un botón `+ Añadir Registro DNS` en su propio encabezado de sección.

3. **Campos Faltantes frente a WinBox en `r1` (`comment` en Servidores DHCP y `ntp-server` en Redes DHCP):**
   - En `r1`, el servidor `dhcp-cctv` tiene `"comment": "cctv"` y las 3 redes tienen `"ntp-server": "192.168.x.254"`, pero la tabla de `Servidores DHCP` no mostraba la columna `Comentario`, y la tabla/modal de `Redes & Opciones` no mostraba `Servidor NTP` al crear o listar.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash)

### Paso 1: Actualizar Esquemas Pydantic en `fastapi/src/schemas/webfig_l1_net.py`

En `fastapi/src/schemas/webfig_l1_net.py`, localizar `DhcpLeaseUpdateRequest` y los esquemas DHCP (líneas 241–289) y reemplazarlos por:

```python
class DhcpLeaseCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    mac_address: str = Field(..., min_length=11, max_length=17)
    server: str = Field(default="all", min_length=1, max_length=64)
    rate_limit: str | None = None
    comment: str | None = None
    disabled: bool = False


class DhcpLeaseUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    mac_address: str | None = Field(default=None, min_length=11, max_length=17)
    server: str | None = Field(default=None, min_length=1, max_length=64)
    rate_limit: str | None = None
    comment: str | None = None
    disabled: bool | None = None


class IpServiceUpdateRequest(StrictBaseModel):
    port: int | None = Field(default=None, ge=1, le=65535)
    address: str | None = None
    disabled: bool | None = None


# ============================================================================
# DHCPv4 SERVER, NETWORKS & CLIENTS
# ============================================================================


class DhcpServerCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    address_pool: str = Field(..., min_length=1, max_length=64)
    lease_time: str = Field(default="10m", max_length=16)
    comment: str | None = None
    disabled: bool = False


class DhcpServerUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    address_pool: str | None = Field(default=None, min_length=1, max_length=64)
    lease_time: str | None = Field(default=None, max_length=16)
    comment: str | None = None
    disabled: bool | None = None


class DhcpNetworkCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    gateway: str | None = None
    dns_server: str | None = None
    domain: str | None = None
    ntp_server: str | None = None
    comment: str | None = None


class DhcpNetworkUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    gateway: str | None = None
    dns_server: str | None = None
    domain: str | None = None
    ntp_server: str | None = None
    comment: str | None = None
```

---

### Paso 2: Añadir `POST /dhcp-server/leases` (`create_dhcp_lease`) y Soporte de `comment` / `ntp_server` en `fastapi/src/api/v1/webfig_ip.py`

1. En `fastapi/src/api/v1/webfig_ip.py`, importar `DhcpLeaseCreateRequest` dentro del bloque `from src.schemas.webfig_l1_net import (...)` (línea 27).
2. En la sección `# DHCP SERVER LEASES` (líneas 570–638 de `fastapi/src/api/v1/webfig_ip.py`), añadir `@router.post("/dhcp-server/leases", status_code=status.HTTP_201_CREATED)` e invalidar caché KeyDB en todas las mutaciones de leases:

```python
@router.get("/dhcp-server/leases")
async def list_dhcp_leases(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista concesiones de clientes DHCP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/ip/dhcp-server/lease", client, refresh)


@router.post("/dhcp-server/leases", status_code=status.HTTP_201_CREATED)
async def create_dhcp_lease(
    router_id: uuid.UUID,
    payload: DhcpLeaseCreateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una reservación DHCP estática en el router bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "address": payload.address,
        "mac-address": payload.mac_address,
        "server": payload.server or "all",
        "disabled": payload.disabled,
    }
    if payload.rate_limit:
        body["rate-limit"] = payload.rate_limit
    if payload.comment:
        body["comment"] = payload.comment

    async with client:
        res = await execute_safe_mutation(
            client=client,
            menu="ip/dhcp-server/lease",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/ip/dhcp-server/lease", json_data=body),
        )
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/lease")
    return res


@router.post("/dhcp-server/leases/{item_id}/make-static")
async def make_dhcp_lease_static(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Convierte un lease DHCP dinámico en reservación estática."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await client.post("/ip/dhcp-server/lease/make-static", json_data={"numbers": item_id})
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/lease")
    return res


@router.patch("/dhcp-server/leases/{item_id}")
async def update_dhcp_lease(
    router_id: uuid.UUID,
    item_id: str,
    payload: DhcpLeaseUpdateRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.SUPPORT_L2,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica una reservación estática DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.address:
        patch_data["address"] = payload.address
    if payload.mac_address:
        patch_data["mac-address"] = payload.mac_address
    if payload.server:
        patch_data["server"] = payload.server
    if payload.rate_limit is not None:
        patch_data["rate-limit"] = payload.rate_limit
    if payload.comment is not None:
        patch_data["comment"] = payload.comment
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    async with client:
        res = await client.patch(f"/ip/dhcp-server/lease/{item_id}", json_data=patch_data)
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/lease")
    return res


@router.delete("/dhcp-server/leases/{item_id}")
async def delete_dhcp_lease(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Libera o elimina una concesión DHCP."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await client.delete(f"/ip/dhcp-server/lease/{item_id}")
    await invalidate_webfig_cache(get_redis_client(), uuid.UUID(claims["tid"]), router_id, "/ip/dhcp-server/lease")
    return res
```

3. En `create_dhcp_server` y `update_dhcp_server` (`fastapi/src/api/v1/webfig_ip.py`, líneas 677–755), incluir `comment`:
   - En `create_dhcp_server`:
     ```python
     if payload.comment:
         body["comment"] = payload.comment
     ```
   - En `update_dhcp_server`:
     ```python
     if payload.comment is not None:
         patch_data["comment"] = payload.comment
     ```
4. En `create_dhcp_network` (`fastapi/src/api/v1/webfig_ip.py`, líneas 827–836), incluir `ntp_server`:
   ```python
   if payload.ntp_server:
       body["ntp-server"] = payload.ntp_server
   ```

---

### Paso 3: Actualizar `vue3/src/views/IpAddressesAndDhcpView.vue` (Sub-Pestaña Inicial `servers`, Carga Paralela, Contadores y Modal `+ Añadir Concesión Estática`)

1. **Cambiar la sub-pestaña por defecto de `activeDhcpSubtab` a `'servers'` y añadir el estado `isCreateLeaseModalOpen` / `newLease` (líneas 19–61 de `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   ```ts
     // Subpestaña de DHCP Server (Orden canónico WinBox: Servidores -> Redes -> Concesiones)
     type DhcpServerSubtab = 'servers' | 'networks' | 'leases';
     const activeDhcpSubtab = ref<DhcpServerSubtab>('servers');
   ```
   Y junto a `isEditLeaseModalOpen` (líneas 46–61), añadir `isCreateLeaseModalOpen`, `newLease`, `comment` en `newServer`/`editServerForm`, y `ntp_server` en `newNetwork`:
   ```ts
     const isCreateLeaseModalOpen = ref(false);
     const newLease = ref({
       address: '',
       mac_address: '',
       server: 'all',
       rate_limit: '',
       comment: '',
       disabled: false,
     });
     const isEditLeaseModalOpen = ref(false);
     const editingLeaseId = ref('');
     const editLeaseForm = ref({ address: '', mac_address: '', server: 'all', rate_limit: '', comment: '' });

     const isServerModalOpen = ref(false);
     const newServer = ref({ name: 'dhcp-lan', interface: 'ether1', address_pool: 'pool-ether1', lease_time: '12h', comment: '', disabled: false });
     const isEditServerModalOpen = ref(false);
     const editingServerId = ref('');
     const editServerForm = ref({ name: '', interface: '', address_pool: '', lease_time: '12h', comment: '', disabled: false });

     const isNetworkModalOpen = ref(false);
     const newNetwork = ref({ address: '192.168.88.0/24', gateway: '192.168.88.1', dns_server: '8.8.8.8,1.1.1.1', ntp_server: '', domain: '', comment: '' });
   ```

2. **Cargar en paralelo `dhcpServers`, `dhcpNetworks` y `dhcpLeases` cuando `activeTab.value === 'dhcp-server'` en `loadData` (líneas 124–135 de `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   Reemplazar el bloque `else if (activeTab.value === 'dhcp-server')` por:
   ```ts
         } else if (activeTab.value === 'dhcp-server') {
           const [srvRes, netRes, leaseRes] = await Promise.all([
             http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-servers${query}`),
             http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/networks${query}`),
             http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/leases${query}`),
           ]);
           dhcpServers.value = Array.isArray(srvRes.data) ? srvRes.data : srvRes.data?.items || [];
           dhcpNetworks.value = Array.isArray(netRes.data) ? netRes.data : netRes.data?.items || [];
           dhcpLeases.value = Array.isArray(leaseRes.data) ? leaseRes.data : leaseRes.data?.items || [];
         }
   ```

3. **Añadir `handleCreateLease()` en la sección de acciones de DHCP Leases (junto a `openEditLeaseModal` en `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   ```ts
     async function handleCreateLease() {
       webFigStore.startSafeModeCountdown(60);
       try {
         await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/dhcp-server/leases`, newLease.value);
         actionMessage.value = `Concesión estática ${newLease.value.address} (${newLease.value.mac_address}) creada.`;
         isCreateLeaseModalOpen.value = false;
         newLease.value = { address: '', mac_address: '', server: 'all', rate_limit: '', comment: '', disabled: false };
         loadData(true);
       } catch (err: any) {
         errorMessage.value = err?.detail || err?.message || 'Error al crear concesión estática DHCP.';
       }
     }
   ```
   Y en `openEditServerModal(srv: any)` (línea 317), incluir `comment: String(srv.comment || '')`.

4. **Mostrar botones de creación para las 3 sub-pestañas de `Servidor DHCP` en `.header-actions` (líneas 728–753 de `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   ```vue
           <template v-else-if="activeTab === 'dhcp-server'">
             <button
               v-if="activeDhcpSubtab === 'servers'"
               id="btn-create-dhcp-server"
               type="button"
               class="btn-tactical btn-outline"
               @click="isServerModalOpen = true"
             >
               + Crear Servidor DHCP
             </button>
             <button
               v-if="activeDhcpSubtab === 'networks'"
               id="btn-create-dhcp-network"
               type="button"
               class="btn-tactical btn-cyan"
               @click="isNetworkModalOpen = true"
             >
               + Crear Red DHCP
             </button>
             <button
               v-if="activeDhcpSubtab === 'leases'"
               id="btn-create-dhcp-lease"
               type="button"
               class="btn-tactical btn-cyan"
               @click="isCreateLeaseModalOpen = true"
             >
               + Añadir Concesión Estática
             </button>
             <button
               id="btn-dhcp-wizard"
               type="button"
               class="btn-tactical btn-cyan"
               @click="isDhcpWizardOpen = true"
             >
               ⚡ Asistente DHCP Setup
             </button>
           </template>
   ```

5. **Reordenar `.subtabs-bar` de `Servidor DHCP` al orden WinBox (`Servidores DHCP` -> `Redes & Opciones` -> `Concesiones Activas (Leases)`) con insignias de conteo `(N)` (líneas 879–904 de `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   ```vue
       <!-- Subpestañas para DHCP Server (Orden WinBox: Servidores -> Redes -> Concesiones) -->
       <div v-if="activeTab === 'dhcp-server'" class="subtabs-bar">
         <button
           id="subtab-dhcp-servers"
           type="button"
           class="subtab-btn"
           :class="{ 'subtab-btn--active': activeDhcpSubtab === 'servers' }"
           @click="setDhcpSubtab('servers')"
         >
           Servidores DHCP ({{ dhcpServers.length }})
         </button>
         <button
           id="subtab-dhcp-networks"
           type="button"
           class="subtab-btn"
           :class="{ 'subtab-btn--active': activeDhcpSubtab === 'networks' }"
           @click="setDhcpSubtab('networks')"
         >
           Redes & Opciones ({{ dhcpNetworks.length }})
         </button>
         <button
           id="subtab-dhcp-leases"
           type="button"
           class="subtab-btn"
           :class="{ 'subtab-btn--active': activeDhcpSubtab === 'leases' }"
           @click="setDhcpSubtab('leases')"
         >
           Concesiones Activas (Leases) ({{ dhcpLeases.length }})
         </button>
       </div>
   ```

6. **Añadir columna `Comentario` en la tabla de `Servidores DHCP` y columna `Servidor NTP` en la tabla de `Redes & Opciones` (líneas 1020–1113 de `vue3/src/views/IpAddressesAndDhcpView.vue`):**
   - En `SERVERS` (`v-else-if="activeDhcpSubtab === 'servers'"`):
     Añadir `<th>Comentario</th>` antes de `<th>Estado</th>`, `<td class="text-muted">{{ srv.comment || '—' }}</td>` en cada fila, y ajustar `colspan="7"` en la fila vacía.
   - En `NETWORKS`:
     Añadir `<th>Servidor NTP</th>` después de `<th>Servidores DNS</th>`, `<td class="font-mono text-muted">{{ net['ntp-server'] || net.ntp_server || '—' }}</td>` en cada fila, y ajustar `colspan="7"` en la fila vacía.

7. **Añadir el Modal de Creación de Concesión Estática (`isCreateLeaseModalOpen`) en `vue3/src/views/IpAddressesAndDhcpView.vue`:**
   Justo antes del modal `<!-- MODAL: EDITAR LEASE DHCP -->`, añadir:
   ```vue
       <!-- MODAL: CREAR CONCESIÓN ESTÁTICA DHCP -->
       <div v-if="isCreateLeaseModalOpen" class="modal-backdrop" @click.self="isCreateLeaseModalOpen = false">
         <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-create-lease-title">
           <h2 id="modal-create-lease-title" class="modal-title">+ Añadir Concesión DHCP Estática (/ip/dhcp-server/lease)</h2>
           <form @submit.prevent="handleCreateLease">
             <div class="form-group">
               <label for="new-lease-ip">Dirección IPv4 a Reservar</label>
               <input
                 id="new-lease-ip"
                 v-model="newLease.address"
                 type="text"
                 class="form-input font-mono"
                 placeholder="192.168.10.50"
                 required
               />
             </div>
             <div class="form-group">
               <label for="new-lease-mac">Dirección MAC del Cliente</label>
               <input
                 id="new-lease-mac"
                 v-model="newLease.mac_address"
                 type="text"
                 class="form-input font-mono"
                 placeholder="AA:BB:CC:DD:EE:FF"
                 required
               />
             </div>
             <div class="form-group">
               <label for="new-lease-server">Servidor DHCP</label>
               <input
                 id="new-lease-server"
                 v-model="newLease.server"
                 type="text"
                 class="form-input font-mono"
                 placeholder="all o dhcp-anillo"
               />
             </div>
             <div class="form-group">
               <label for="new-lease-rate">Límite de Velocidad (Rate Limit Rx/Tx)</label>
               <input
                 id="new-lease-rate"
                 v-model="newLease.rate_limit"
                 type="text"
                 class="form-input font-mono"
                 placeholder="10M/50M (Opcional)"
               />
             </div>
             <div class="form-group">
               <label for="new-lease-comment">Comentario / Suscriptor</label>
               <input
                 id="new-lease-comment"
                 v-model="newLease.comment"
                 type="text"
                 class="form-input"
                 placeholder="Ej: Cámara IP / Impresora"
               />
             </div>
             <div class="modal-actions">
               <button type="button" class="btn-tactical btn-outline" @click="isCreateLeaseModalOpen = false">
                 Cancelar
               </button>
               <button id="btn-submit-create-lease" type="submit" class="btn-tactical btn-cyan">
                 Crear Concesión Estática
               </button>
             </div>
           </form>
         </div>
       </div>
   ```

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias y Karate Labs BDD)

> **DIRECTIVA INNEGOCIABLE:** Gemini 3.8 Flash (High) **DEBE** añadir y ejecutar las siguientes pruebas unitarias y escenarios Karate Labs BDD antes de dar por cerrado el Hito 30.20.

### 3.1 Prueba Unitaria Backend (`fastapi/tests/api/test_webfig_dhcp_and_ipv6.unit.py`)

Añadir al final de `fastapi/tests/api/test_webfig_dhcp_and_ipv6.unit.py`:

```python
@pytest.mark.asyncio
async def test_webfig_dhcp_lease_create_static_and_ntp_network(
    fake_client_and_router: tuple[Router, AsyncMock],
) -> None:
    """Certifica la creación de reservaciones estáticas DHCP (POST /dhcp-server/leases) y soporte de comment/ntp_server (Spec 97)."""
    from src.schemas.webfig_l1_net import DhcpLeaseCreateRequest

    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        lease_payload = DhcpLeaseCreateRequest(
            address="192.168.10.50",
            mac_address="AA:BB:CC:11:22:33",
            server="dhcp-anillo",
            rate_limit="20M/20M",
            comment="PC Contabilidad",
        )
        res_lease = await api_wf_ip.create_dhcp_lease(r.id, lease_payload, claims=claims, db=db)
        assert res_lease.get("ret") == "*1"
        assert "_safemode" in res_lease

        net_payload = DhcpNetworkCreateRequest(
            address="192.168.10.0/24",
            gateway="192.168.10.254",
            dns_server="192.168.10.254",
            ntp_server="192.168.10.254",
            comment="pc",
        )
        res_net = await api_wf_ip.create_dhcp_network(r.id, net_payload, claims=claims, db=db)
        assert res_net.get("ret") == "*1"
```

### 3.2 Prueba Unitaria Frontend (`vue3/src/views/ipAndIpv6Views.unit.ts`)

Añadir dentro del bloque `describe` de `vue3/src/views/ipAndIpv6Views.unit.ts`:

```ts
  it('IpAddressesAndDhcpView — abre Servidores DHCP por defecto con carga paralela y permite añadir concesión estática (Spec 97)', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/dhcp-servers')) {
        return {
          status: 200,
          data: [
            { '.id': '*1', name: 'dhcp-anillo', interface: 'bridge-anillo', 'address-pool': 'pool-pcs', 'lease-time': '30m', disabled: 'false' },
            { '.id': '*2', name: 'dhcp-aps', interface: 'vlan20-aps', 'address-pool': 'pool-aps', 'lease-time': '30m', disabled: 'false' },
            { '.id': '*3', name: 'dhcp-cctv', interface: 'vlan30-cctv', 'address-pool': 'dhcp_pool2', 'lease-time': '30m', comment: 'cctv', disabled: 'false' },
          ],
          headers: new Headers(),
        };
      }
      if (url.includes('/dhcp-server/networks')) {
        return {
          status: 200,
          data: [
            { '.id': '*1', address: '192.168.10.0/24', gateway: '192.168.10.254', 'dns-server': '192.168.10.254', 'ntp-server': '192.168.10.254', comment: 'pc' },
          ],
          headers: new Headers(),
        };
      }
      if (url.includes('/dhcp-server/leases')) {
        return { status: 200, data: [], headers: new Headers() };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
      status: 201,
      data: { ret: '*9' },
      headers: new Headers(),
    });

    const wrapper = mount(IpAddressesAndDhcpView);
    await flushPromises();

    const vm = wrapper.vm as any;
    vm.setTab('dhcp-server');
    await flushPromises();

    // Por defecto debe abrir la subpestaña 'servers' y mostrar los 3 servidores DHCP de r1
    expect(vm.activeDhcpSubtab).toBe('servers');
    expect(wrapper.text()).toContain('dhcp-anillo');
    expect(wrapper.text()).toContain('dhcp-aps');
    expect(wrapper.text()).toContain('dhcp-cctv');
    expect(wrapper.text()).toContain('Servidores DHCP (3)');
    expect(wrapper.text()).toContain('Redes & Opciones (1)');

    // Cambiar a Concesiones Activas (Leases) y verificar que existe el botón '+ Añadir Concesión Estática'
    vm.setDhcpSubtab('leases');
    await flushPromises();

    const addLeaseBtn = wrapper.find('#btn-create-dhcp-lease');
    expect(addLeaseBtn.exists()).toBe(true);
    await addLeaseBtn.trigger('click');
    await flushPromises();

    vm.newLease = {
      address: '192.168.10.50',
      mac_address: 'AA:BB:CC:11:22:33',
      server: 'dhcp-anillo',
      rate_limit: '10M/10M',
      comment: 'Cliente Estático',
      disabled: false,
    };
    await vm.handleCreateLease();
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/routers/r-01/webfig/ip/dhcp-server/leases',
      expect.objectContaining({
        address: '192.168.10.50',
        mac_address: 'AA:BB:CC:11:22:33',
        server: 'dhcp-anillo',
      }),
    );

    wrapper.unmount();
  });
```

### 3.3 Escenarios Karate Labs BDD (`api_test.feature` Escenario 171 y `ui_business_flow.feature` Escenario 111 + Réplicas en `docs/examples/`)

1. Añadir al final de `fastapi/test/api_test.feature` **y** `docs/examples/fastapi/api_test.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 97: SERVIDORES DHCP, REDES NTP Y CREACIÓN DE CONCESIÓN ESTÁTICA DHCP
     # ============================================================================
     Scenario: 171. Listado de servidores DHCP (/webfig/ip/dhcp-servers) y redes DHCP (/webfig/ip/dhcp-server/networks)
       Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-servers'
       When method GET
       Then status 200
   ```

2. Añadir al final de `vue3/test/ui_business_flow.feature` **y** `docs/examples/vue3/ui_business_flow.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 97: SUBPESTAÑA POR DEFECTO SERVIDORES DHCP Y CREACIÓN DE LEASE ESTÁTICO
     # ============================================================================
     Scenario: 111. El módulo Servidor DHCP abre por defecto Servidores DHCP y permite añadir concesiones estáticas
       * def defaultDhcpSubtab = 'servers'
       * assert defaultDhcpSubtab == 'servers'
   ```

---

## 4. Comandos de Verificación y Certificación (Rule Zero)

```bash
# 1. Ejecutar prueba unitaria backend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps backend-qa pytest tests/api/test_webfig_dhcp_and_ipv6.unit.py -q

# 2. Ejecutar prueba unitaria frontend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps frontend-qa npx vitest run src/views/ipAndIpv6Views.unit.ts

# 3. Verificar paridad cero endpoints huérfanos
python3 .agents/scripts/verify_no_orphan_api_endpoints.py

# 4. Reconstruir contenedores locales para verificar en navegador (http://localhost:8085)
docker build -t sinfallas/rosgrid-backend:local-test ./fastapi
docker build -t sinfallas/rosgrid-frontend:local-test ./vue3
docker compose -f docker-compose.prod.local.yml up -d --force-recreate backend frontend

# 5. Ejecutar compuerta de certificación de 9 pasos
./.agents/scripts/certify_task_completion.sh
```
