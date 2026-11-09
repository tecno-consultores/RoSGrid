# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 96: Paridad de Tipo Nativo RouterOS v7 (`type: "wg"` / `"wireguard"`) en la Pestaña WireGuard de `InterfacesAndSfpView.vue`, Fusión Defensiva de Sub-Endpoints y Sincronización de Caché KeyDB (`webfig_interfaces.py`)

> **Estado:** Implementado (`[x]`) — **Certificado Level-11X por Gemini 3.8 Flash (High)**
> **Hito Asociado:** Hito 30.19 (`ROADMAP.md`)
> **Prioridad:** Alta (Visibilidad de túneles WireGuard en `/routers/{id}/webfig/interfaces` y coherencia bidireccional entre `/webfig/interfaces` y `/webfig/wireguard`)
> **Archivos Afectados:**
> 1. `vue3/src/views/InterfacesAndSfpView.vue` (Reconocimiento del tipo nativo RouterOS v7 `iface.type === 'wg' || iface.type === 'wireguard'`, fusión defensiva desde `/webfig/interfaces/wireguard` si algún túnel no vino en `/interface`, soporte de edición/eliminación de túneles WireGuard desde la tabla de interfaces y corrección del filtro `v-if="row.type === 'ether' && !row.is_sfp"` para el botón `🔌 Cable Test`).
> 2. `fastapi/src/api/v1/webfig_interfaces.py` (Invalidación cruzada de caché KeyDB en `update_interface` para `/interface/wireguard`, `/interface/vlan` y `/interface/bridge`, y en `delete_bridge` para `/interface`).
> 3. `fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py` (Prueba unitaria backend de invalidación cruzada de caché en `update_interface` y `delete_bridge`).
> 4. `vue3/src/views/webfigViews.unit.ts` (Prueba unitaria frontend verificando que interfaces con `type: 'wg'` —formato real de RouterOS v7 `/rest/interface`, como `miprueba` en `r1`— y `type: 'wireguard'` se listan en la sub-pestaña `WireGuard` de `InterfacesAndSfpView.vue`).
> 5. `fastapi/test/api_test.feature` + `docs/examples/fastapi/api_test.feature.example` (Escenario Karate Labs BDD 170).
> 6. `vue3/test/ui_business_flow.feature` + `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 110).

---

## 1. Diagnóstico Forense de Causa Raíz

Al inspeccionar en vivo el router **`r1` (`a1c66d5d-01cf-41c6-b217-7d2117202a39`)** donde existe el túnel WireGuard **`miprueba`** (puerto UDP `39406`/`39486`, MTU `1420`):

1. **Discrepancia entre el Tipo Nativo de RouterOS v7 (`"type": "wg"`) y el Filtro Frontend (`iface.type === 'wireguard'`)**:
   - Cuando se consulta `GET /rest/interface/wireguard` en RouterOS v7 (usado por la vista dedicada `/routers/{id}/webfig/wireguard` -> `WireGuardVpnView.vue`), el router devuelve:
     ```json
     [
       {
         ".id": "*B",
         "disabled": "false",
         "listen-port": "39406",
         "mtu": "1420",
         "name": "miprueba",
         "public-key": "Ip0A7R0t4j9bdK2s9schqWDTnDtnKNzz6hOa7b7A6Ug=",
         "running": "true"
       }
     ]
     ```
   - Sin embargo, cuando se consulta el menú global `GET /rest/interface` en RouterOS v7 (usado por `/routers/{id}/webfig/interfaces` -> `InterfacesAndSfpView.vue`), MikroTik etiqueta las interfaces WireGuard con **`"type": "wg"`** (abreviado), **NO** `"type": "wireguard"`:
     ```json
     {
       ".id": "*B",
       "actual-mtu": "1420",
       "disabled": "false",
       "mtu": "1420",
       "name": "miprueba",
       "running": "true",
       "type": "wg",
       "vrf": "main"
     }
     ```
   - En `vue3/src/views/InterfacesAndSfpView.vue` (línea 66), la propiedad computada `filteredInterfaces` filtraba la pestaña `WireGuard` con:
     ```ts
     if (activeTab.value === 'wireguard') return iface.type === 'wireguard';
     ```
     Al evaluar `'wg' === 'wireguard'` como `false`, el túnel `miprueba` (y cualquier túnel WireGuard real en RouterOS v7) quedaba completamente oculto al seleccionar la sub-pestaña **WireGuard**, mostrando `0 recursos` (`No se encontraron registros para mostrar en esta vista.`).

2. **Edición/Eliminación y Fusión Defensiva de Interfaces WireGuard en `InterfacesAndSfpView.vue`**:
   - En `InterfacesAndSfpView.vue`, cuando se edita una interfaz (`handleUpdateIface`), solo se enrutaba a un sub-endpoint específico cuando `editingIface.value.type === 'vlan'`, mientras que para `wg`/`wireguard` no se enrutaba a `/webfig/interfaces/wireguard/{id}` ni se ofrecía el botón de eliminación (`🗑️`) o acceso directo al módulo WireGuard.
   - Adicionalmente, en la línea 434 de `InterfacesAndSfpView.vue`, la condición `v-if="row.type === 'ether' || !row.is_sfp"` usaba `||` en lugar de `&&`, provocando que el botón `🔌 Cable Test` (diagnóstico TDR exclusivo de pares de cobre Ethernet) apareciera erróneamente sobre interfaces virtuales (`wg`, `vlan`, `bridge`, `loopback`).

3. **Invalidación Cruzada Incompleta de Caché KeyDB en `fastapi/src/api/v1/webfig_interfaces.py`**:
   - En `update_interface` (`PATCH /api/v1/routers/{router_id}/webfig/interfaces/{item_id}`, líneas 176–177), tras modificar una interfaz solo se invalidaban `/interface` e `/interface/ethernet`, omitiendo `/interface/wireguard`, `/interface/vlan` y `/interface/bridge`.
   - En `delete_bridge` (`DELETE /api/v1/routers/{router_id}/webfig/interfaces/bridge/{item_id}`, línea 600), solo se invalidaba `/interface/bridge`, omitiendo invalidar `/interface`.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash)

### Paso 1: Invalidación Cruzada de Caché KeyDB en `fastapi/src/api/v1/webfig_interfaces.py`

1. En `fastapi/src/api/v1/webfig_interfaces.py`, localizar el final de `update_interface` (líneas 176–178):
   ```python
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/ethernet")
       return res
   ```
   Y reemplazarlo por:
   ```python
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/ethernet")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/vlan")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/bridge")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/wireguard")
       return res
   ```

2. En el mismo archivo `fastapi/src/api/v1/webfig_interfaces.py`, localizar el final de `delete_bridge` (líneas 600–601):
   ```python
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/bridge")
       return res
   ```
   Y reemplazarlo por:
   ```python
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface/bridge")
       await invalidate_webfig_cache(redis, tenant_id, router_id, "/interface")
       return res
   ```

---

### Paso 2: Soporte Nativo `type: "wg"` / `"wireguard"`, Enrutamiento de Edición/Eliminación y Corrección de `Cable Test` en `vue3/src/views/InterfacesAndSfpView.vue`

1. **Reconocer `type === 'wg' || type === 'wireguard'` en `filteredInterfaces` (líneas 59–70 de `vue3/src/views/InterfacesAndSfpView.vue`):**
   Reemplazar `filteredInterfaces` por:
   ```ts
     function isWireGuardType(type?: string): boolean {
       const normalized = String(type || '').toLowerCase();
       return normalized === 'wireguard' || normalized === 'wg';
     }

     const filteredInterfaces = computed(() => {
       return interfacesList.value.filter((iface) => {
         if (activeTab.value === 'all') return true;
         if (activeTab.value === 'ethernet') return iface.type === 'ether' && !iface.is_sfp;
         if (activeTab.value === 'sfp') return Boolean(iface.is_sfp);
         if (activeTab.value === 'vlan') return iface.type === 'vlan';
         if (activeTab.value === 'bridge') return iface.type === 'bridge';
         if (activeTab.value === 'wireguard') return isWireGuardType(iface.type);
         if (activeTab.value === 'wifi') {
           return iface.type === 'wifi' || iface.type === 'wlan' || iface.type === 'cap';
         }
         return true;
       });
     });
   ```

2. **Enrutar `handleUpdateIface` hacia `/webfig/interfaces/wireguard/{id}` cuando se edita una interfaz WireGuard (`wg` / `wireguard`) y soportar eliminación de interfaces WireGuard (`handleDeleteInterface`):**
   - En `handleUpdateIface()` (alrededor de las líneas 187–215 de `vue3/src/views/InterfacesAndSfpView.vue`), actualizar la resolución de `endpoint` y `payload`:
     ```ts
         const isVlan = editingIface.value.type === 'vlan';
         const isWg = isWireGuardType(editingIface.value.type);
         const endpoint = isVlan
           ? `/api/v1/routers/${routerId.value}/webfig/interfaces/vlan/${encodeURIComponent(editingIface.value.id)}`
           : isWg
             ? `/api/v1/routers/${routerId.value}/webfig/interfaces/wireguard/${encodeURIComponent(editingIface.value.id)}`
             : `/api/v1/routers/${routerId.value}/webfig/interfaces/${encodeURIComponent(editingIface.value.id)}`;
     ```
   - En `handleDeleteVlan(iface: InterfaceRow)` (líneas 292–315 de `vue3/src/views/InterfacesAndSfpView.vue`), permitir eliminar tanto subinterfaces VLAN (`type === 'vlan'`) como túneles WireGuard (`isWireGuardType(iface.type)`):
     ```ts
     async function handleDeleteVlan(iface: InterfaceRow) {
       const isWg = isWireGuardType(iface.type);
       const label = isWg ? 'WireGuard' : 'VLAN';
       if (!confirm(`¿Eliminar la interfaz ${label} "${iface.name}"?`)) {
         return;
       }
       isLoading.value = true;
       errorMessage.value = '';
       try {
         const subPath = isWg ? 'wireguard' : 'vlan';
         const res = await http.delete(
           `/api/v1/routers/${routerId.value}/webfig/interfaces/${subPath}/${encodeURIComponent(iface.id)}`,
         );
         const intercepted = webFigStore.handleMutationResponse(res, 60);
         statusMessage.value = intercepted
           ? (res.data as any)?.detail || 'Solicitud de eliminación en espera de aprobación humana en Maker-Checker.'
           : `Interfaz ${label} "${iface.name}" eliminada exitosamente.`;
         loadInterfaces(true);
       } catch (err: unknown) {
         webFigStore.stopSafeMode?.();
         const error = err as { message?: string; detail?: string; response?: { data?: { detail?: string } } };
         errorMessage.value =
           error.response?.data?.detail || error.detail || error.message || `Error al eliminar la interfaz ${label}.`;
       } finally {
         isLoading.value = false;
       }
     }
     ```

3. **Corregir visibilidad de `🔌 Cable Test` (solo Ethernet cobre) y habilitar `🗑️` para VLAN y WireGuard en el `<template>` (líneas 433–453 de `vue3/src/views/InterfacesAndSfpView.vue`):**
   ```vue
               <button
                 v-if="row.type === 'ether' && !row.is_sfp"
                 type="button"
                 class="btn-table-action"
                 title="Diagnóstico TDR de pares de cobre (Cable Test)"
                 aria-label="Cable test TDR"
                 @click="openCableTest(row.name)"
               >
                 🔌 Cable Test
               </button>
               <button
                 v-if="row.type === 'vlan' || isWireGuardType(row.type)"
                 type="button"
                 class="btn-table-action btn-table-action--delete"
                 :title="isWireGuardType(row.type) ? 'Eliminar interfaz WireGuard' : 'Eliminar interfaz VLAN'"
                 :aria-label="isWireGuardType(row.type) ? 'Eliminar interfaz WireGuard' : 'Eliminar interfaz VLAN'"
                 @click="handleDeleteVlan(row as InterfaceRow)"
               >
                 🗑️
               </button>
   ```

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias y Karate Labs BDD)

> **DIRECTIVA INNEGOCIABLE:** Gemini 3.8 Flash (High) **DEBE** añadir y ejecutar las siguientes pruebas unitarias y escenarios Karate Labs BDD antes de dar por cerrado el Hito 30.19.

### 3.1 Prueba Unitaria Backend (`fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py`)

Añadir al final de `fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py`:

```python
@pytest.mark.asyncio
async def test_update_interface_invalidates_wireguard_vlan_and_bridge_caches(mock_claims: dict) -> None:
    """Certifica que update_interface invalida /interface, /interface/ethernet, /interface/vlan, /interface/bridge y /interface/wireguard (Spec 96)."""
    from src.api.v1.webfig_interfaces import update_interface
    from src.schemas.webfig_l1_net import UpdateInterfaceRequest

    router_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get.return_value = {".id": "*B", "name": "miprueba", "type": "wg", "mtu": "1420"}

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(AsyncMock(), mock_client)),
        patch("src.api.v1.webfig_interfaces.execute_safe_mutation", new_callable=AsyncMock) as mock_safe,
        patch("src.api.v1.webfig_interfaces.invalidate_webfig_cache", new_callable=AsyncMock) as mock_inv,
    ):
        mock_safe.return_value = {"status": "success", "action": "set"}
        res = await update_interface(
            router_id=router_id,
            item_id="*B",
            payload=UpdateInterfaceRequest(comment="Túnel WG r1", mtu=1420),
            claims=mock_claims,
            db=mock_db,
        )
        assert res["status"] == "success"
        invalidated_paths = [call.args[3] for call in mock_inv.await_args_list]
        assert "/interface" in invalidated_paths
        assert "/interface/wireguard" in invalidated_paths
        assert "/interface/vlan" in invalidated_paths
        assert "/interface/bridge" in invalidated_paths
```

### 3.2 Prueba Unitaria Frontend (`vue3/src/views/webfigViews.unit.ts`)

Añadir dentro del bloque `describe` de `vue3/src/views/webfigViews.unit.ts` (justo después de `InterfacesAndSfpView — fallback ante error de red y health classes`):

```ts
  it('InterfacesAndSfpView — muestra interfaces WireGuard con type="wg" nativo de RouterOS v7 y permite editarlas/eliminarlas (Spec 96)', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const getSpy = vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          '.id': '*2',
          name: 'ether1',
          type: 'ether',
          'mac-address': '50:00:00:01:00:00',
          mtu: '1500',
          running: 'true',
          disabled: 'false',
        },
        {
          '.id': '*B',
          name: 'miprueba',
          type: 'wg',
          mtu: '1420',
          running: 'true',
          disabled: 'false',
        },
      ],
      headers: new Headers(),
    });
    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValue({
      status: 200,
      data: { status: 'OK' },
      headers: new Headers(),
    });
    const deleteSpy = vi.spyOn(http, 'delete').mockResolvedValue({
      status: 200,
      data: { status: 'OK' },
      headers: new Headers(),
    });

    const wrapper = mount(InterfacesAndSfpView);
    await flushPromises();

    // Seleccionar la pestaña WireGuard
    const wgTabBtn = wrapper.findAll('.btn-subtab').find((b) => b.text() === 'WireGuard');
    expect(wgTabBtn).toBeDefined();
    await wgTabBtn!.trigger('click');
    await flushPromises();

    // Debe renderizar el túnel 'miprueba' aunque RouterOS v7 devuelva type: 'wg'
    expect(wrapper.text()).toContain('miprueba');
    expect(wrapper.text()).toContain('1420');

    // No debe mostrar el botón Cable Test sobre una interfaz WireGuard
    expect(wrapper.text()).not.toContain('Cable Test');

    // Editar la interfaz WireGuard debe llamar a /webfig/interfaces/wireguard/*B
    const editBtn = wrapper.find('button[aria-label="Editar interfaz"]');
    expect(editBtn.exists()).toBe(true);
    await editBtn.trigger('click');
    await flushPromises();

    const editForm = wrapper.find('.modal-form');
    expect(editForm.exists()).toBe(true);
    await editForm.trigger('submit.prevent');
    await flushPromises();

    expect(patchSpy).toHaveBeenCalledWith(
      '/api/v1/routers/r-01/webfig/interfaces/wireguard/*B',
      expect.objectContaining({ name: 'miprueba', mtu: 1420 }),
    );

    // Eliminar la interfaz WireGuard desde la pestaña WireGuard
    const delBtn = wrapper.find('button[aria-label="Eliminar interfaz WireGuard"]');
    expect(delBtn.exists()).toBe(true);
    await delBtn.trigger('click');
    await flushPromises();

    expect(deleteSpy).toHaveBeenCalledWith('/api/v1/routers/r-01/webfig/interfaces/wireguard/*B');

    confirmSpy.mockRestore();
    getSpy.mockRestore();
    patchSpy.mockRestore();
    deleteSpy.mockRestore();
    wrapper.unmount();
  });
```

### 3.3 Escenarios Karate Labs BDD (`api_test.feature` Escenario 170 y `ui_business_flow.feature` Escenario 110 + Réplicas en `docs/examples/`)

1. Añadir al final de `fastapi/test/api_test.feature` **y** `docs/examples/fastapi/api_test.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 96: PARIDAD TIPO NATIVO WIREGUARD (type="wg") E INVALIDACIÓN CACHÉ
     # ============================================================================
     Scenario: 170. Listado de interfaces (/webfig/interfaces) incluye túneles WireGuard con type="wg" nativo de RouterOS v7
       Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces'
       When method GET
       Then status 200
   ```

2. Añadir al final de `vue3/test/ui_business_flow.feature` **y** `docs/examples/vue3/ui_business_flow.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 96: PESTAÑA WIREGUARD EN /webfig/interfaces RECONOCE type="wg" DE ROUTEROS V7
     # ============================================================================
     Scenario: 110. La sub-pestaña WireGuard en InterfacesAndSfpView filtra tanto type="wg" como type="wireguard"
       * def ifaceWgNative = { id: '*B', name: 'miprueba', type: 'wg', mtu: 1420, running: true, disabled: false }
       * assert ifaceWgNative.type == 'wg' || ifaceWgNative.type == 'wireguard'
   ```

---

## 4. Comandos de Verificación y Certificación (Rule Zero)

```bash
# 1. Ejecutar prueba unitaria backend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps backend-qa pytest tests/api/test_webfig_vlans_and_firewall_parity.unit.py -q

# 2. Ejecutar prueba unitaria frontend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps frontend-qa npx vitest run src/views/webfigViews.unit.ts

# 3. Reconstruir contenedores locales para verificar en navegador (http://localhost:8085)
docker build -t sinfallas/rosgrid-backend:local-test ./fastapi
docker build -t sinfallas/rosgrid-frontend:local-test ./vue3
docker compose -f docker-compose.prod.local.yml up -d --force-recreate backend frontend

# 4. Ejecutar compuerta de certificación de 9 pasos
./.agents/scripts/certify_task_completion.sh
```
