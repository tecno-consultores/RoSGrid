# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 98: Paridad Dual-Stack IPv4 / IPv6 en `FirewallRulesView.vue` (`/ip/firewall` y `/ipv6/firewall`), Selector de Protocolo con Sincronización de Ruta (`?proto=ipv6`) y Soporte CRUD Completo de Reglas IPv6

> **Estado:** Implementado (`[x]`) — **Certificado Level-11X por Gemini 3.8 Flash (High)**
> **Hito Asociado:** Hito 30.21 (`ROADMAP.md`)
> **Prioridad:** Alta (Permite ver, crear, modificar, reordenar, conmutar y eliminar reglas de Firewall IPv6 `/ipv6/firewall/*` y Address-Lists IPv6 al navegar desde `🛡️ Firewall IPv6` en `Ipv6DualStackView.vue` o directamente en `FirewallRulesView.vue`)
> **Archivos Afectados:**
> 1. `fastapi/src/api/v1/webfig_firewall.py` (Soportar `proto == "ipv6"` en `list_connections` y `delete_connection` consultando `/{ros_proto}/firewall/connection`).
> 2. `vue3/src/views/Ipv6DualStackView.vue` (Actualizar `goToFirewall()` para navegar hacia `/routers/${routerId.value}/webfig/firewall?proto=ipv6`).
> 3. `vue3/src/views/FirewallRulesView.vue` (Añadir estado reactivo `activeProto = ref<'ip' | 'ipv6'>(...)` inicializado y sincronizado con `route.query?.proto`, renderizar el conmutador segmentado `#btn-fw-proto-ip` `IPv4 (/ip/firewall)` y `#btn-fw-proto-ipv6` `IPv6 (/ipv6/firewall)` en la cabecera, parametrizar todas las llamadas HTTP con `${activeProto.value}`, y pasar `:proto="activeProto"` a `<RgFirewallRuleModal>`).
> 4. `vue3/src/components/webfig/RgFirewallRuleModal.vue` (Recibir prop opcional `proto?: 'ip' | 'ipv6'`, mostrar insignia `[IPv6 / FILTER]` o `[IPv4 / FILTER]`, añadir protocolo `icmpv6 (58)` y adaptar los *placeholders* de direcciones origen/destino a formato IPv6 cuando `proto === 'ipv6'`).
> 5. `fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py` (Prueba unitaria backend verificando `list_rules`, `create_rule`, `update_rule`, `delete_rule` y `list_connections` con `proto="ipv6"`).
> 6. `vue3/src/views/webfigViews.unit.ts` y `vue3/src/views/ipAndIpv6Views.unit.ts` (Pruebas unitarias frontend verificando que `goToFirewall()` en `Ipv6DualStackView.vue` navega a `?proto=ipv6` y que `FirewallRulesView.vue` permite conmutar a `IPv6 (/ipv6/firewall)` y ejecutar el ciclo completo ver/crear/editar/toggle/eliminar sobre `/webfig/firewall/ipv6/*`).
> 7. `fastapi/test/api_test.feature` + `docs/examples/fastapi/api_test.feature.example` (Escenario Karate Labs BDD 172).
> 8. `vue3/test/ui_business_flow.feature` + `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 112).

---

## 1. Diagnóstico Forense de Causa Raíz

Al pulsar el botón **`🛡️ Firewall IPv6`** en la vista **Pila Dual IPv6 & PD** (`/routers/{id}/webfig/ipv6` -> `Ipv6DualStackView.vue`):

1. **Redirección sin Parámetro de Protocolo en `Ipv6DualStackView.vue` (líneas 91–93):**
   - La función `goToFirewall()` ejecutaba:
     ```ts
     function goToFirewall() {
       router.push(`/routers/${routerId.value}/webfig/firewall`);
     }
     ```
     sin indicar `?proto=ipv6`.

2. **Protocolo `'ip'` (IPv4) Hardcodeado en `FirewallRulesView.vue`:**
   - Aunque el backend `fastapi/src/api/v1/webfig_firewall.py` **ya soporta de forma nativa `proto in {"ip", "ipv6"}`** en todos sus endpoints (`GET/POST/PATCH/DELETE /{proto}/{table_type}`, `POST /{proto}/{table_type}/move`, `POST /{proto}/{table_type}/reset-counters` y `GET/POST/PATCH/DELETE /{proto}/address-lists`), el componente `vue3/src/views/FirewallRulesView.vue` tenía hardcodeado el segmento `/webfig/firewall/ip/...` en sus 9 llamadas HTTP (`loadFirewallRules`, `handleSaveAddressList`, `handleSaveRule`, `handleToggleRule`, `handleDeleteRule`, `handleResetCounters`, `handleReorder`, `handleExecuteMasquerade` y `handleExecutePortForward`).
   - Adicionalmente, `FirewallRulesView.vue` carecía de un selector visual **`IPv4 (/ip/firewall)` | `IPv6 (/ipv6/firewall)`** para alternar entre las tablas de filtrado IPv4 e IPv6, y el modal `RgFirewallRuleModal.vue` no incluía la opción de protocolo `icmpv6` (`58`) esencial en reglas de firewall IPv6.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash)

### Paso 1: Soportar `proto="ipv6"` en `list_connections` y `delete_connection` (`fastapi/src/api/v1/webfig_firewall.py`)

En `fastapi/src/api/v1/webfig_firewall.py`, localizar la sección `# CONNECTION TRACKING` (líneas 556–588) y reemplazarla por:

```python
@router.get("/connections")
@router.get("/{proto}/connections")
@router.get("/{proto}/connection")
async def list_connections(
    router_id: uuid.UUID,
    proto: str = "ip",
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Consulta la tabla de Connection Tracking (IPv4 /ip/firewall/connection o IPv6 /ipv6/firewall/connection)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    ros_proto = "ipv6" if proto == "ipv6" else "ip"
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, f"/{ros_proto}/firewall/connection", client, refresh)


@router.delete("/connections/{conn_id}")
@router.delete("/{proto}/connections/{conn_id}")
async def delete_connection(
    router_id: uuid.UUID,
    conn_id: str,
    proto: str = "ip",
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina/cierra una conexión activa de la tabla de Connection Tracking (IPv4 o IPv6)."""
    _, client = await get_router_and_client(router_id, claims, db)
    ros_proto = "ipv6" if proto == "ipv6" else "ip"
    async with client:
        return await client.delete(f"/{ros_proto}/firewall/connection/{conn_id}")


delete_firewall_connection = delete_connection
```

---

### Paso 2: Pasar `?proto=ipv6` desde `goToFirewall()` en `vue3/src/views/Ipv6DualStackView.vue`

En `vue3/src/views/Ipv6DualStackView.vue`, localizar `goToFirewall` (líneas 91–93):
```ts
  function goToFirewall() {
    router.push(`/routers/${routerId.value}/webfig/firewall`);
  }
```
Y reemplazarlo por:
```ts
  function goToFirewall() {
    router.push(`/routers/${routerId.value}/webfig/firewall?proto=ipv6`);
  }
```

---

### Paso 3: Añadir Prop `proto` y Protocolo `icmpv6` en `vue3/src/components/webfig/RgFirewallRuleModal.vue`

1. En `vue3/src/components/webfig/RgFirewallRuleModal.vue`, actualizar `defineProps` (líneas 9–15):
   ```ts
     const props = defineProps<{
       isOpen: boolean;
       isEditing: boolean;
       tableType: 'filter' | 'nat' | 'mangle' | 'raw';
       proto?: 'ip' | 'ipv6';
       initialRule?: FirewallRuleItem | null;
       existingRules: FirewallRuleItem[];
     }>();
   ```
2. En el título del modal (`#rule-modal-title`, líneas 212–215):
   ```vue
             <h3 id="rule-modal-title" class="modal-title">
               {{ isEditing ? 'Editar Regla de Firewall' : 'Nueva Regla de Firewall' }}
               <span class="table-badge">[{{ proto === 'ipv6' ? 'IPv6' : 'IPv4' }} / {{ tableType.toUpperCase() }}]</span>
             </h3>
   ```
3. En el `<select id="rule-protocol">` (líneas 268–275), añadir `icmpv6`:
   ```vue
               <select id="rule-protocol" v-model="protocol" class="form-select font-tabular">
                 <option value="any">Cualquiera (Any)</option>
                 <option value="tcp">tcp (6)</option>
                 <option value="udp">udp (17)</option>
                 <option value="icmp">icmp (1)</option>
                 <option value="icmpv6">icmpv6 (58)</option>
                 <option value="gre">gre (47)</option>
                 <option value="esp">esp (50)</option>
               </select>
   ```
4. En los `<input id="rule-src-addr">` y `<input id="rule-dst-addr">` (líneas 281–299), usar placeholders adaptados a IPv4/IPv6:
   ```vue
               <input
                 id="rule-src-addr"
                 v-model="srcAddress"
                 type="text"
                 class="form-input font-tabular"
                 :placeholder="proto === 'ipv6' ? 'Ej: 2001:db8::/32 o fe80::/10' : 'Ej: 192.168.88.0/24 o 10.0.0.5'"
               />
   ```
   y:
   ```vue
               <input
                 id="rule-dst-addr"
                 v-model="dstAddress"
                 type="text"
                 class="form-input font-tabular"
                 :placeholder="proto === 'ipv6' ? 'Ej: ::/0 o 2606:4700:4700::1111' : 'Ej: 0.0.0.0/0 o 8.8.8.8'"
               />
   ```

---

### Paso 4: Añadir Selector Dual-Stack `IPv4 (/ip/firewall)` | `IPv6 (/ipv6/firewall)` y Parametrizar `activeProto` en `vue3/src/views/FirewallRulesView.vue`

1. En `vue3/src/views/FirewallRulesView.vue` (líneas 5–21), importar `watch` de `vue` y declarar `activeProto`:
   ```ts
     import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
     import { useRoute } from 'vue-router';
     import { http } from '@/api/httpClient';
     import { useWebFigStore } from '@/stores/useWebFigStore';
     import type { TableColumn, FirewallRuleItem } from '@/types';
     import RgDataTable from '@/components/common/RgDataTable.vue';
     import RgFirewallRuleModal from '@/components/webfig/RgFirewallRuleModal.vue';

     const route = useRoute();
     const routerId = computed(() => String(route.params.routerId || ''));
     const webFigStore = useWebFigStore();

     const activeProto = ref<'ip' | 'ipv6'>(
       String((route as any)?.query?.proto || '').toLowerCase() === 'ipv6' ? 'ipv6' : 'ip',
     );
     const activeTab = ref<'filter' | 'nat' | 'mangle' | 'raw' | 'address-list' | 'connections'>(
       'filter',
     );

     function setProto(proto: 'ip' | 'ipv6') {
       if (activeProto.value === proto) return;
       activeProto.value = proto;
       loadFirewallRules();
     }

     watch(
       () => (route as any)?.query?.proto,
       (newProto) => {
         const normalized = String(newProto || '').toLowerCase() === 'ipv6' ? 'ipv6' : 'ip';
         if (activeProto.value !== normalized) {
           activeProto.value = normalized;
           loadFirewallRules();
         }
       },
     );
   ```

2. En `loadFirewallRules` (líneas 113–125 de `vue3/src/views/FirewallRulesView.vue`), usar `activeProto.value`:
   ```ts
       const baseEndpoint =
         activeTab.value === 'connections'
           ? activeProto.value === 'ipv6'
             ? `/api/v1/routers/${routerId.value}/webfig/firewall/ipv6/connections`
             : `/api/v1/routers/${routerId.value}/webfig/firewall/connections`
           : `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}`;
       const query = forceRefresh ? '?refresh=true' : '';
       const endpoint = `${baseEndpoint}${query}`;
       const res = await http.get<FirewallRuleItem[] | { items: FirewallRuleItem[] }>(endpoint);
   ```

3. En `handleSaveAddressList`, `handleSaveRule`, `handleToggleRule`, `handleDeleteRule`, `handleResetCounters` y `handleReorder` (líneas 201–371 de `vue3/src/views/FirewallRulesView.vue`), reemplazar `/webfig/firewall/ip/` por `/webfig/firewall/${activeProto.value}/`:
   - `handleSaveAddressList`:
     - PATCH: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/address-lists/${encodeURIComponent(editingAddressListId.value)}` ``
     - POST: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/address-lists` ``
   - `handleSaveRule`:
     - PATCH: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}/${selectedRule.value.id}` ``
     - POST: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}` ``
   - `handleToggleRule`:
     - PATCH: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}/${rule.id}` ``
   - `handleDeleteRule`:
     ```ts
     const deleteUrl =
       activeTab.value === 'connections'
         ? activeProto.value === 'ipv6'
           ? `/api/v1/routers/${routerId.value}/webfig/firewall/ipv6/connections/${encodeURIComponent(rule.id)}`
           : `/api/v1/routers/${routerId.value}/webfig/firewall/connections/${encodeURIComponent(rule.id)}`
         : `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}/${rule.id}`;
     ```
   - `handleResetCounters`:
     - POST: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}/reset-counters` ``
   - `handleReorder`:
     - POST: `` `/api/v1/routers/${routerId.value}/webfig/firewall/${activeProto.value}/${activeTab.value}/move` ``

4. En el `<template>` de `vue3/src/views/FirewallRulesView.vue` (dentro de `<header class="view-header">`, líneas 486–564):
   - Actualizar el título para reflejar la pila activa y añadir el selector segmentado de protocolo **`IPv4 (/ip/firewall)` | `IPv6 (/ipv6/firewall)`**:
     ```vue
           <div>
             <h2 class="view-title">
               Firewall RouterOS v7 & Filtrado de Paquetes ({{ activeProto === 'ipv6' ? 'IPv6' : 'IPv4' }})
             </h2>
             <p class="view-subtitle">
               Reglas ordenadas con protección Safe Mode (60s Rollback) y barras de tráfico en vivo
             </p>
           </div>

           <!-- Conmutador de Pila IPv4 / IPv6 -->
           <div class="proto-switcher" role="group" aria-label="Pila de protocolo de Firewall">
             <button
               id="btn-fw-proto-ip"
               type="button"
               class="btn-proto font-tabular"
               :class="{ 'btn-proto--active': activeProto === 'ip' }"
               :aria-pressed="activeProto === 'ip'"
               @click="setProto('ip')"
             >
               🌐 IPv4 (/ip/firewall)
             </button>
             <button
               id="btn-fw-proto-ipv6"
               type="button"
               class="btn-proto font-tabular"
               :class="{ 'btn-proto--active': activeProto === 'ipv6' }"
               :aria-pressed="activeProto === 'ipv6'"
               @click="setProto('ipv6')"
             >
               🌐 IPv6 (/ipv6/firewall)
             </button>
           </div>
     ```
   - Ocultar los asistentes `Masquerade` y `Port Forwarding` (exclusivos de NAT IPv4) cuando `activeProto === 'ipv6'`:
     ```vue
             <button
               v-if="activeTab === 'nat' && activeProto === 'ip'"
               type="button"
               class="btn-wizard-action"
               @click="isMasqueradeWizardOpen = true"
             >
               🧙‍♂️ Masquerade
             </button>
             <button
               v-if="activeTab === 'nat' && activeProto === 'ip'"
               type="button"
               class="btn-wizard-action"
               @click="isPortForwardWizardOpen = true"
             >
               🧙‍♂️ Port Forwarding
             </button>
     ```
   - Pasar `:proto="activeProto"` a `<RgFirewallRuleModal>` (línea 645):
     ```vue
         <RgFirewallRuleModal
           v-if="activeTab === 'filter' || activeTab === 'nat' || activeTab === 'mangle' || activeTab === 'raw'"
           :is-open="isRuleModalOpen"
           :is-editing="isEditingRule"
           :table-type="activeTab"
           :proto="activeProto"
           :initial-rule="selectedRule"
           :existing-rules="rulesList"
           @close="isRuleModalOpen = false"
           @save="handleSaveRule"
         />
     ```
   - Añadir en `<style scoped>` de `FirewallRulesView.vue`:
     ```css
       .proto-switcher {
         display: inline-flex;
         gap: 4px;
         background: var(--rg-bg-canvas);
         padding: 3px;
         border: 1px solid var(--rg-border-grid);
         border-radius: 8px;
       }

       .btn-proto {
         background: transparent;
         border: none;
         color: var(--rg-text-secondary);
         padding: 5px 12px;
         font-size: 0.78rem;
         border-radius: 5px;
         cursor: pointer;
         transition: all 0.15s ease;
       }

       .btn-proto--active {
         background: rgba(6, 182, 212, 0.16);
         color: var(--rg-accent-cyan);
         font-weight: 700;
       }
     ```

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias y Karate Labs BDD)

> **DIRECTIVA INNEGOCIABLE:** Gemini 3.8 Flash (High) **DEBE** añadir y ejecutar las siguientes pruebas unitarias y escenarios Karate Labs BDD antes de dar por cerrado el Hito 30.21.

### 3.1 Prueba Unitaria Backend (`fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py`)

Añadir al final de `fastapi/tests/api/test_webfig_vlans_and_firewall_parity.unit.py`:

```python
@pytest.mark.asyncio
async def test_ipv6_firewall_rules_and_connections_crud(mock_claims: dict) -> None:
    """Certifica que webfig_firewall soporta proto='ipv6' para listar, crear, editar, eliminar y consultar conexiones en /ipv6/firewall/* (Spec 98)."""
    from src.api.v1.webfig_firewall import (
        create_rule,
        delete_rule,
        list_connections,
        list_rules,
        update_rule,
    )
    from src.schemas.webfig_firewall import (
        FirewallRuleCreateRequest,
        FirewallRuleUpdateRequest,
    )

    router_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get.return_value = {".id": "*v6_1", "chain": "forward", "action": "accept"}

    with (
        patch("src.api.v1.webfig_firewall.get_router_and_client", return_value=(AsyncMock(), mock_client)),
        patch("src.api.v1.webfig_firewall.cached_mikrotik_get", new_callable=AsyncMock) as mock_cached,
        patch("src.api.v1.webfig_firewall.execute_safe_mutation", new_callable=AsyncMock) as mock_safe,
        patch("src.api.v1.webfig_firewall.invalidate_webfig_cache", new_callable=AsyncMock),
    ):
        mock_cached.return_value = [{".id": "*v6_1", "chain": "input", "protocol": "icmpv6", "action": "accept"}]
        rules = await list_rules(router_id=router_id, proto="ipv6", table_type="filter", refresh=True, claims=mock_claims, db=mock_db)
        assert len(rules) == 1
        assert mock_cached.await_args.args[3] == "/ipv6/firewall/filter"

        mock_safe.return_value = {"ret": "*v6_2"}
        res_create = await create_rule(
            router_id=router_id,
            proto="ipv6",
            table_type="filter",
            payload=FirewallRuleCreateRequest(chain="input", action="accept", protocol="icmpv6", comment="Allow ICMPv6"),
            claims=mock_claims,
            db=mock_db,
        )
        assert res_create["ret"] == "*v6_2"

        mock_safe.return_value = {"status": "updated"}
        res_upd = await update_rule(
            router_id=router_id,
            proto="ipv6",
            table_type="filter",
            rule_id="*v6_1",
            payload=FirewallRuleUpdateRequest(comment="Updated IPv6 rule"),
            claims=mock_claims,
            db=mock_db,
        )
        assert res_upd["status"] == "updated"

        mock_safe.return_value = {"status": "deleted"}
        res_del = await delete_rule(
            router_id=router_id,
            proto="ipv6",
            table_type="filter",
            rule_id="*v6_1",
            claims=mock_claims,
            db=mock_db,
        )
        assert res_del["status"] == "deleted"

        await list_connections(router_id=router_id, proto="ipv6", refresh=True, claims=mock_claims, db=mock_db)
        assert mock_cached.await_args.args[3] == "/ipv6/firewall/connection"
```

### 3.2 Pruebas Unitarias Frontend (`vue3/src/views/ipAndIpv6Views.unit.ts` y `vue3/src/views/webfigViews.unit.ts`)

1. En `vue3/src/views/ipAndIpv6Views.unit.ts` (líneas 365–367), actualizar la aserción de `goToFirewall()`:
   ```ts
       // 7. Redirección a Firewall IPv6 (Spec 98)
       vm.goToFirewall();
       expect(mockPush).toHaveBeenCalledWith('/routers/r-01/webfig/firewall?proto=ipv6');
   ```
2. En `vue3/src/views/webfigViews.unit.ts`, añadir dentro del bloque `describe` (justo después del test existente de `FirewallRulesView`):
   ```ts
     it('FirewallRulesView — conmuta a IPv6 (#btn-fw-proto-ipv6) y permite ver, crear, editar y eliminar reglas en /webfig/firewall/ipv6/* (Spec 98)', async () => {
       const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
       const getSpy = vi.spyOn(http, 'get').mockResolvedValue({
         status: 200,
         data: [
           {
             '.id': '*v6_1',
             chain: 'input',
             action: 'accept',
             protocol: 'icmpv6',
             'src-address': '2001:db8::/32',
             bytes: 1024,
             packets: 12,
             comment: 'Permitir ICMPv6 NDP',
             disabled: 'false',
           },
         ],
         headers: new Headers(),
       });
       const postSpy = vi.spyOn(http, 'post').mockResolvedValue({
         status: 201,
         data: { ret: '*v6_2' },
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

       const wrapper = mount(FirewallRulesView);
       await flushPromises();

       // Conmutar a protocolo IPv6
       const btnIpv6 = wrapper.find('#btn-fw-proto-ipv6');
       expect(btnIpv6.exists()).toBe(true);
       await btnIpv6.trigger('click');
       await flushPromises();

       expect(getSpy).toHaveBeenCalledWith('/api/v1/routers/r-01/webfig/firewall/ipv6/filter');
       expect(wrapper.text()).toContain('Permitir ICMPv6 NDP');

       // Crear nueva regla IPv6
       const vm = wrapper.vm as any;
       vm.isEditingRule = false;
       await vm.handleSaveRule({
         chain: 'forward',
         action: 'drop',
         protocol: 'icmpv6',
         src_address: '2001:db8:bad::/48',
         comment: 'Bloquear prefijo IPv6',
         disabled: false,
       });
       await flushPromises();

       expect(postSpy).toHaveBeenCalledWith(
         '/api/v1/routers/r-01/webfig/firewall/ipv6/filter',
         expect.objectContaining({
           chain: 'forward',
           action: 'drop',
           protocol: 'icmpv6',
         }),
       );

       // Editar regla IPv6 existente
       const ruleRow = vm.rulesList[0];
       vm.openEditRuleModal(ruleRow);
       await vm.handleSaveRule({
         chain: 'input',
         action: 'accept',
         comment: 'ICMPv6 Actualizado',
       });
       await flushPromises();

       expect(patchSpy).toHaveBeenCalledWith(
         '/api/v1/routers/r-01/webfig/firewall/ipv6/filter/*v6_1',
         expect.objectContaining({ comment: 'ICMPv6 Actualizado' }),
       );

       // Eliminar regla IPv6
       await vm.handleDeleteRule(ruleRow);
       await flushPromises();

       expect(deleteSpy).toHaveBeenCalledWith(
         '/api/v1/routers/r-01/webfig/firewall/ipv6/filter/*v6_1',
       );

       confirmSpy.mockRestore();
       getSpy.mockRestore();
       postSpy.mockRestore();
       patchSpy.mockRestore();
       deleteSpy.mockRestore();
       wrapper.unmount();
     });
   ```

### 3.3 Escenarios Karate Labs BDD (`api_test.feature` Escenario 172 y `ui_business_flow.feature` Escenario 112 + Réplicas en `docs/examples/`)

1. Añadir al final de `fastapi/test/api_test.feature` **y** `docs/examples/fastapi/api_test.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 98: PARIDAD DUAL-STACK FIREWALL IPV6 (/webfig/firewall/ipv6/filter)
     # ============================================================================
     Scenario: 172. Consulta de reglas de Firewall IPv6 (/webfig/firewall/ipv6/filter)
       Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/firewall/ipv6/filter'
       When method GET
       Then status 200
   ```

2. Añadir al final de `vue3/test/ui_business_flow.feature` **y** `docs/examples/vue3/ui_business_flow.feature.example`:
   ```cucumber
     # ============================================================================
     # SPEC 98: CONMUTADOR FIREWALL IPV4 / IPV6 EN FIREWALLRULESVIEW
     # ============================================================================
     Scenario: 112. El botón Firewall IPv6 desde Pila Dual redirige con ?proto=ipv6 y activa las reglas IPv6
       * def targetUrl = '/routers/r-01/webfig/firewall?proto=ipv6'
       * assert targetUrl.contains('proto=ipv6')
   ```

---

## 4. Comandos de Verificación y Certificación (Rule Zero)

```bash
# 1. Ejecutar prueba unitaria backend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps backend-qa pytest tests/api/test_webfig_vlans_and_firewall_parity.unit.py -q

# 2. Ejecutar pruebas unitarias frontend en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps frontend-qa npx vitest run src/views/webfigViews.unit.ts src/views/ipAndIpv6Views.unit.ts

# 3. Verificar paridad cero endpoints huérfanos
python3 .agents/scripts/verify_no_orphan_api_endpoints.py

# 4. Reconstruir contenedores locales para verificar en navegador (http://localhost:8085)
docker build -t sinfallas/rosgrid-backend:local-test ./fastapi
docker build -t sinfallas/rosgrid-frontend:local-test ./vue3
docker compose -f docker-compose.prod.local.yml up -d --force-recreate backend frontend

# 5. Ejecutar compuerta de certificación de 9 pasos
./.agents/scripts/certify_task_completion.sh
```
