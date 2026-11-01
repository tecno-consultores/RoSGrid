# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación Técnica 59: Activación/Configuración Interactiva de DHCP Snooping y Puertos Trusted/Untrusted por Bridge bajo Safe Mode (60s) + Plantilla Masiva en Flota (`SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`)

> **Hito de Referencia:** Hito 28 (`28.4`) — Mejoras Operativas de Pruebas Manuales (UAT)  
> **Estado:** Especificación Aprobada ("Flash-Ready" para Ejecución Determinista por **Gemini 3.8 Flash High**)  
> **Reglas de Gobernanza Aplicables:** `.agents/rules/mandatory_qa_pyramid_and_doc_sync.md`, `.agents/rules/frontend_parity_and_closure.md`, `.agents/rules/anti_regression_and_side_effects_guardrail.md`

---

## 1. Contexto Operativo y Diagnóstico del Hallazgo en UAT

Durante las pruebas manuales en `http://localhost:8085/enterprise/compliance?tab=switching` (**Seguridad L2 & Rogue DHCP**) sobre el router `caps1 (10.250.3.20)`:

1. **Tarjetas de Bridge de Solo Lectura (`Bridge: bridge11 — DHCP Snooping: INACTIVO`, `Bridge: bridge15 — DHCP Snooping: INACTIVO`):**
   - La pestaña consulta `GET /api/v1/switching/dhcp-snooping/{router_id}` y muestra las tarjetas de cada bridge con el badge `DHCP Snooping: INACTIVO`, `Puertos Confiables (Trusted / Uplink)` y `Puertos de Acceso (Untrusted / Confinados)`, pero **carece de botones o controles interactivos** para encender/apagar DHCP Snooping o clasificar puertos como `Trusted` / `Untrusted`.
   - En el backend (`fastapi/src/api/v1/switching.py`, línea 107) ya existía el endpoint `POST /api/v1/switching/dhcp-snooping/enable`, el cual había quedado **huérfano** sin botón en `EnterpriseComplianceView.vue`.
2. **Grounding Oficial de MikroTik RouterOS v7 (`/interface/bridge` y `/interface/bridge/port`):**
   - En RouterOS v7 ([Bridging and Switching — DHCP Snooping and DHCP Option 82](https://manual.mikrotik.com/docs/display/ROS/Bridging+and+Switching#BridgingandSwitching-DHCPSnoopingandDHCPOption82)), todos los puertos de un bridge nacen por defecto con `trusted=no` (`Untrusted`).
   - Al activar `dhcp-snooping=yes` en un bridge, RouterOS descarta todos los paquetes `DHCP Offer` y `DHCP Ack` entrantes por puertos `trusted=no`. Por ello, la activación segura exige permitir al operador marcar simultáneamente cuáles puertos de ese bridge son **`Trusted (Uplink)`** (y opcionalmente activar `add-dhcp-option82=yes`) bajo **Safe Mode de 60 segundos**.
   - Asimismo, en la API REST de RouterOS v7, la mutación canónica por nombre de bridge o nombre de puerto se realiza mediante `POST /rest/interface/bridge/set` (`{"numbers": bridge_name, "dhcp-snooping": "yes"|"no", "add-dhcp-option82": "yes"|"no"}`) y `POST /rest/interface/bridge/port/set` (`{"numbers": port_id_or_name, "trusted": "yes"|"no"}`).
3. **Estrategia Dual Aprobada (Activación Local por Bridge + Botón Secundario a Acciones Masivas):**
   - **Opción 1 (Principal — Activación y Configuración Local en Cada Tarjeta de Bridge):** Botón táctico en cada tarjeta (`[ ⚡ Activar DHCP Snooping ]` cuando está inactivo, o `[ ⚙️ Configurar / Desactivar ]` cuando está activo) que despliega un modal/panel interactivo para ese bridge con conmutador de `DHCP Snooping`, conmutador de `Add DHCP Option 82` y selección por checkboxes de los puertos `Trusted (Uplink)` frente a `Untrusted (Acceso)`, ejecutando `POST /api/v1/switching/dhcp-snooping/enable` bajo **Safe Mode (60s)**.
   - **Opción 2 (Complementaria — Botón Secundario hacia Plantilla en Acciones Masivas):** Botón secundario en la cabecera de la pestaña (`#btn-bulk-dhcp-snooping`, `[ 🚀 Desplegar en Flota (Acciones Masivas) ]`) que navega a `/bulk-ops?template=SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82&from=switching`, preseleccionando la nueva plantilla oficial **#16 `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`**.

---

## 2. Blueprint "Flash-Ready" Paso a Paso (Para Ejecución por Gemini 3.8 Flash High)

> **INSTRUCCIÓN PARA EL AGENTE EJECUTOR (GEMINI 3.8 FLASH HIGH):**
> Aplica los siguientes bloques `Target` / `Replacement` exactamente como están especificados. Mantén todas las funciones con Complejidad Ciclomática Radon Grado A (`CC <= 5`).

---

### 2.1. Paso 1: Extender `DhcpSnoopingState` y `DhcpSnoopingEnableRequest` en `fastapi/src/schemas/enterprise.py`

En `fastapi/src/schemas/enterprise.py` (líneas 246–262), añadir soporte para `enabled: bool = True`, `add_dhcp_option82: bool = False` y `untrusted_ports: list[str]`:

- **Target:**
```python
class DhcpSnoopingState(BaseModel):
    """Estado de DHCP Snooping y puertos confiables en el bridge."""

    bridge_name: str
    dhcp_snooping_enabled: bool
    trusted_ports: list[str]
    untrusted_ports: list[str]


class DhcpSnoopingEnableRequest(StrictBaseModel):
    """Solicitud para habilitar DHCP Snooping y marcar puertos troncales/acceso."""

    router_id: uuid.UUID
    bridge_name: str = Field("bridge", max_length=64)
    trusted_ports: list[str] = Field(default_factory=list)
```

- **Replacement:**
```python
class DhcpSnoopingState(BaseModel):
    """Estado de DHCP Snooping, Option 82 y puertos confiables en el bridge."""

    bridge_name: str
    dhcp_snooping_enabled: bool
    add_dhcp_option82: bool = False
    trusted_ports: list[str]
    untrusted_ports: list[str]


class DhcpSnoopingEnableRequest(StrictBaseModel):
    """Solicitud para habilitar/configurar DHCP Snooping y marcar puertos troncales/acceso."""

    router_id: uuid.UUID
    bridge_name: str = Field("bridge", max_length=64)
    enabled: bool = True
    add_dhcp_option82: bool = False
    trusted_ports: list[str] = Field(default_factory=list)
    untrusted_ports: list[str] = Field(default_factory=list)
```

---

### 2.2. Paso 2: Actualizar `fastapi/src/api/v1/switching.py` (Mutación Canónica RouterOS v7 y Grado A Radon)

En `fastapi/src/api/v1/switching.py` (líneas 74–172), extraer helpers de complejidad Grado A (`CC <= 4`) para construir el estado de los bridges y aplicar la configuración de `dhcp-snooping`, `add-dhcp-option82` y puertos `trusted`/`untrusted` mediante `POST /interface/bridge/set` y `POST /interface/bridge/port/set`:

- **Target:**
```python
        states: list[DhcpSnoopingState] = []
        if isinstance(bridges, list):
            for b in bridges:
                b_name = str(b.get("name", "bridge"))
                snooping = b.get("dhcp-snooping") in (True, "true", "yes")

                trusted: list[str] = []
                untrusted: list[str] = []
                if isinstance(ports, list):
                    for p in ports:
                        if str(p.get("bridge")) == b_name:
                            p_name = str(p.get("interface", ""))
                            is_trusted = p.get("trusted") in (True, "true", "yes")
                            if is_trusted:
                                trusted.append(p_name)
                            else:
                                untrusted.append(p_name)

                states.append(
                    DhcpSnoopingState(
                        bridge_name=b_name,
                        dhcp_snooping_enabled=snooping,
                        trusted_ports=trusted,
                        untrusted_ports=untrusted,
                    )
                )
            return states
    except Exception as exc:
        logger.debug("Sondeo REST de DHCP Snooping: %s", exc)

    return []


@router.post(
    "/dhcp-snooping/enable",
    response_model=DhcpSnoopingState,
    summary="Activar DHCP Snooping en bridge y marcar puertos troncales como confiables (Trusted)",
    dependencies=[Depends(require_roles(*_SWITCHING_WRITE_ROLES))],
)
async def enable_dhcp_snooping(
    payload: DhcpSnoopingEnableRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> DhcpSnoopingState:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    trusted_list = payload.trusted_ports or ["sfp-sfpplus1"]

    try:
        _, client = await get_router_and_client(router_obj.id, claims, db)

        async def _apply_snooping() -> dict[str, Any]:
            await client.patch(f"/interface/bridge/{payload.bridge_name}", json_data={"dhcp-snooping": "true"})
            for p in trusted_list:
                await client.patch(f"/interface/bridge/port/{p}", json_data={"trusted": "true"})
            return {"status": "ok"}

        await execute_safe_mutation(
            client=client,
            menu="/switching",
            action="enable_snooping",
            coro_fn=_apply_snooping,
        )
    except Exception as exc:
        logger.warning("Simulación de activación DHCP Snooping: %s", exc)

    # WORM log
    actor = audit_actor_from_claims(claims, request)
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=actor["actor_user_id"],
        actor_username=actor["actor_username"],
        actor_role=actor["actor_role"],
        actor_ip=actor["actor_ip"],
        actor_user_agent=actor["actor_user_agent"],
        event_category="SWITCHING_SECURITY",
        event_action="ENABLE_DHCP_SNOOPING",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"snooping": False},
        after_state={"bridge": payload.bridge_name, "trusted_ports": trusted_list},
        status_code=200,
    )

    return DhcpSnoopingState(
        bridge_name=payload.bridge_name,
        dhcp_snooping_enabled=True,
        trusted_ports=trusted_list,
        untrusted_ports=[],
    )
```

- **Replacement:**
```python
        if isinstance(bridges, list):
            return _parse_bridge_snooping_states(bridges, ports if isinstance(ports, list) else [])
    except Exception as exc:
        logger.debug("Sondeo REST de DHCP Snooping: %s", exc)

    return []


def _classify_bridge_ports(b_name: str, ports: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Separa los puertos de un bridge en listas trusted y untrusted."""
    trusted: list[str] = []
    untrusted: list[str] = []
    for p in ports:
        if str(p.get("bridge")) != b_name:
            continue
        p_name = str(p.get("interface", ""))
        if p.get("trusted") in (True, "true", "yes"):
            trusted.append(p_name)
        else:
            untrusted.append(p_name)
    return trusted, untrusted


def _parse_bridge_snooping_states(
    bridges: list[dict[str, Any]],
    ports: list[dict[str, Any]],
) -> list[DhcpSnoopingState]:
    """Construye la lista de estados de DHCP Snooping por cada bridge del router."""
    states: list[DhcpSnoopingState] = []
    for b in bridges:
        b_name = str(b.get("name", "bridge"))
        snooping = b.get("dhcp-snooping") in (True, "true", "yes")
        opt82 = b.get("add-dhcp-option82") in (True, "true", "yes")
        trusted, untrusted = _classify_bridge_ports(b_name, ports)
        states.append(
            DhcpSnoopingState(
                bridge_name=b_name,
                dhcp_snooping_enabled=snooping,
                add_dhcp_option82=opt82,
                trusted_ports=trusted,
                untrusted_ports=untrusted,
            )
        )
    return states


async def _mutate_bridge_snooping_on_ros(
    client: Any,
    payload: DhcpSnoopingEnableRequest,
    trusted_list: list[str],
) -> None:
    """Aplica dhcp-snooping, add-dhcp-option82 y puertos trusted/untrusted en RouterOS v7."""
    snoop_str = "yes" if payload.enabled else "no"
    opt82_str = "yes" if (payload.enabled and payload.add_dhcp_option82) else "no"
    await client.post(
        "/interface/bridge/set",
        json_data={
            "numbers": payload.bridge_name,
            "dhcp-snooping": snoop_str,
            "add-dhcp-option82": opt82_str,
        },
    )
    for p_trusted in trusted_list:
        await client.post(
            "/interface/bridge/port/set",
            json_data={"numbers": p_trusted, "trusted": "yes"},
        )
    for p_untrusted in payload.untrusted_ports:
        if p_untrusted not in trusted_list:
            await client.post(
                "/interface/bridge/port/set",
                json_data={"numbers": p_untrusted, "trusted": "no"},
            )


@router.post(
    "/dhcp-snooping/enable",
    response_model=DhcpSnoopingState,
    summary="Activar/Configurar DHCP Snooping en bridge y marcar puertos troncales como confiables (Trusted)",
    dependencies=[Depends(require_roles(*_SWITCHING_WRITE_ROLES))],
)
async def enable_dhcp_snooping(
    payload: DhcpSnoopingEnableRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> DhcpSnoopingState:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    trusted_list = list(payload.trusted_ports)

    try:
        _, client = await get_router_and_client(router_obj.id, claims, db)

        async def _apply_snooping() -> dict[str, Any]:
            await _mutate_bridge_snooping_on_ros(client, payload, trusted_list)
            return {"status": "ok"}

        await execute_safe_mutation(
            client=client,
            menu="/switching",
            action="enable_snooping",
            coro_fn=_apply_snooping,
        )
    except Exception as exc:
        logger.warning("Simulación de configuración DHCP Snooping: %s", exc)

    actor = audit_actor_from_claims(claims, request)
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=actor["actor_user_id"],
        actor_username=actor["actor_username"],
        actor_role=actor["actor_role"],
        actor_ip=actor["actor_ip"],
        actor_user_agent=actor["actor_user_agent"],
        event_category="SWITCHING_SECURITY",
        event_action="ENABLE_DHCP_SNOOPING" if payload.enabled else "DISABLE_DHCP_SNOOPING",
        router_id=router_obj.id,
        router_display_name=router_obj.display_name,
        before_state={"snooping": not payload.enabled},
        after_state={
            "bridge": payload.bridge_name,
            "enabled": payload.enabled,
            "add_dhcp_option82": payload.add_dhcp_option82,
            "trusted_ports": trusted_list,
        },
        status_code=200,
    )

    remaining_untrusted = [p for p in payload.untrusted_ports if p not in trusted_list]
    return DhcpSnoopingState(
        bridge_name=payload.bridge_name,
        dhcp_snooping_enabled=payload.enabled,
        add_dhcp_option82=payload.enabled and payload.add_dhcp_option82,
        trusted_ports=trusted_list,
        untrusted_ports=remaining_untrusted,
    )
```

---

### 2.3. Paso 3: Añadir Plantilla Oficial #16 `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82` en `fastapi/src/api/v1/bulk_and_updates.py`

En `fastapi/src/api/v1/bulk_and_updates.py`, al final de `_DEFAULT_STARTER_TEMPLATES` (después de `ACTUALIZACION_ROUTEROS_Y_FIRMWARE`), añadir la plantilla #16:

```python
    {
        "name": "SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82",
        "category": "SECURITY",
        "description": (
            "Activa DHCP Snooping y DHCP Option 82 en el bridge especificado y configura "
            "el puerto troncal (Uplink) como Trusted para prevenir servidores Rogue DHCP en la LAN."
        ),
        "ros_command_template": (
            "/interface bridge port set [find where bridge={{ bridge_name }} and interface={{ trusted_uplink_port }}] trusted=yes\n"
            "/interface bridge set [find where name={{ bridge_name }}] dhcp-snooping=yes add-dhcp-option82={{ add_option82 }}"
        ),
        "variables_schema": [
            {
                "key": "bridge_name",
                "label": "Nombre del Bridge Objetivo",
                "default_val": "bridge1",
            },
            {
                "key": "trusted_uplink_port",
                "label": "Puerto Troncal Confiable (Trusted / Uplink hacia DHCP Server)",
                "default_val": "ether1",
            },
            {
                "key": "add_option82",
                "label": "Inyectar DHCP Option 82 (yes / no)",
                "default_val": "yes",
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "interface/bridge/port/set",
                "payload": {
                    "numbers": "{{ trusted_uplink_port }}",
                    "trusted": "yes",
                },
                "cli_command": "/interface bridge port set {{ trusted_uplink_port }} trusted=yes",
            },
            {
                "method": "POST",
                "endpoint": "interface/bridge/set",
                "payload": {
                    "numbers": "{{ bridge_name }}",
                    "dhcp-snooping": "yes",
                    "add-dhcp-option82": "{{ add_option82 }}",
                },
                "cli_command": "/interface bridge set {{ bridge_name }} dhcp-snooping=yes add-dhcp-option82={{ add_option82 }}",
            },
        ],
        "requires_safemode": True,
    },
```

Y en `vue3/src/views/BulkOperationsAndUpdatesView.vue`:
- En `getTemplateKey(name: string)`, añadir:
  ```typescript
  SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82: 'seguridad_l2_dhcp_snooping_y_option82',
  ```
- En `onMounted()` de `BulkOperationsAndUpdatesView.vue`, si `route?.query?.template` coincide con el nombre de cualquier plantilla en `templates.value` (como `ACTUALIZACION_ROUTEROS_Y_FIRMWARE` o `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`), seleccionarla automáticamente (`onSelectTemplate(matchedTpl.id)`) y avanzar a `wizardStep.value = 2`.

---

### 2.4. Paso 4: Activación Interactiva por Bridge + Botón Secundario a Acciones Masivas en `vue3/src/views/EnterpriseComplianceView.vue`

En `vue3/src/views/EnterpriseComplianceView.vue`:

1. Importar `useRouter` desde `'vue-router'` (si no está importado) e instanciar `const router = useRouter();`.
2. Extender `interface DhcpSnoopingState` con `add_dhcp_option82?: boolean;`.
3. Añadir el estado reactivo y las funciones de configuración de DHCP Snooping por Bridge y navegación a `/bulk-ops`:
   ```typescript
   const selectedBridgeForSnooping = ref<DhcpSnoopingState | null>(null);
   const snoopingForm = ref<{
     bridge_name: string;
     enabled: boolean;
     add_dhcp_option82: boolean;
     all_ports: string[];
     trusted_ports: string[];
     manual_trusted_port: string;
   }>({
     bridge_name: '',
     enabled: true,
     add_dhcp_option82: false,
     all_ports: [],
     trusted_ports: [],
     manual_trusted_port: '',
   });

   function openSnoopingConfigModal(bridge: DhcpSnoopingState) {
     const allPorts = Array.from(new Set([...(bridge.trusted_ports || []), ...(bridge.untrusted_ports || [])]));
     selectedBridgeForSnooping.value = bridge;
     snoopingForm.value = {
       bridge_name: bridge.bridge_name,
       enabled: !bridge.dhcp_snooping_enabled ? true : bridge.dhcp_snooping_enabled,
       add_dhcp_option82: Boolean(bridge.add_dhcp_option82),
       all_ports: allPorts,
       trusted_ports: [...(bridge.trusted_ports || [])],
       manual_trusted_port: '',
     };
   }

   function toggleTrustedPortInForm(portName: string) {
     const idx = snoopingForm.value.trusted_ports.indexOf(portName);
     if (idx >= 0) {
       snoopingForm.value.trusted_ports.splice(idx, 1);
     } else {
       snoopingForm.value.trusted_ports.push(portName);
     }
   }

   function addManualTrustedPort() {
     const p = snoopingForm.value.manual_trusted_port.trim();
     if (!p) return;
     if (!snoopingForm.value.all_ports.includes(p)) {
       snoopingForm.value.all_ports.push(p);
     }
     if (!snoopingForm.value.trusted_ports.includes(p)) {
       snoopingForm.value.trusted_ports.push(p);
     }
     snoopingForm.value.manual_trusted_port = '';
   }

   async function handleSaveBridgeSnooping() {
     if (!selectedRouterId.value || !selectedBridgeForSnooping.value) return;
     actionLoading.value = true;
     errorMessage.value = '';
     const untrusted = snoopingForm.value.all_ports.filter(
       (p) => !snoopingForm.value.trusted_ports.includes(p),
     );
     try {
       const res = await http.post<DhcpSnoopingState>('/api/v1/switching/dhcp-snooping/enable', {
         router_id: selectedRouterId.value,
         bridge_name: snoopingForm.value.bridge_name,
         enabled: snoopingForm.value.enabled,
         add_dhcp_option82: snoopingForm.value.add_dhcp_option82,
         trusted_ports: snoopingForm.value.trusted_ports,
         untrusted_ports: untrusted,
       });
       const target = snoopingBridges.value.find((b) => b.bridge_name === res.data.bridge_name);
       if (target) {
         target.dhcp_snooping_enabled = res.data.dhcp_snooping_enabled;
         target.add_dhcp_option82 = res.data.add_dhcp_option82;
         target.trusted_ports = res.data.trusted_ports;
         target.untrusted_ports = res.data.untrusted_ports;
       }
       successMessage.value = res.data.dhcp_snooping_enabled
         ? `DHCP Snooping activado en ${res.data.bridge_name} bajo Safe Mode (60s).`
         : `DHCP Snooping desactivado en ${res.data.bridge_name} bajo Safe Mode (60s).`;
       selectedBridgeForSnooping.value = null;
     } catch (err: unknown) {
       const e = err as { response?: { data?: { detail?: string } }; message?: string };
       errorMessage.value = e.response?.data?.detail || e.message || 'Error al configurar DHCP Snooping';
     } finally {
       actionLoading.value = false;
     }
   }

   function navigateToBulkDhcpSnooping(bridgeName?: string) {
     router.push({
       path: '/bulk-ops',
       query: {
         template: 'SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82',
         bridge: bridgeName || snoopingBridges.value[0]?.bridge_name || 'bridge1',
         from: 'switching',
       },
     });
   }
   ```

4. **Actualizar el `<template>` de `#panel-switching` (líneas 1638–1680 de `vue3/src/views/EnterpriseComplianceView.vue`):**

- **Target:**
```html
      <!-- ================================================================= -->
      <!-- TAB 4: Seguridad L2 & Rogue DHCP (Sub-tarea 20.4)                 -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'switching'"
        id="panel-switching"
        role="tabpanel"
        aria-labelledby="tab-btn-switching"
        class="tab-panel"
      >
        <div class="snooping-cards-grid">
          <div v-for="b in snoopingBridges" :key="b.bridge_name" class="bridge-card">
            <div class="bridge-header">
              <h2 class="bridge-name">Bridge: {{ b.bridge_name }}</h2>
              <span
                class="badge"
                :class="b.dhcp_snooping_enabled ? 'badge-success' : 'badge-danger'"
              >
                DHCP Snooping: {{ b.dhcp_snooping_enabled ? t('common.status_active', 'ACTIVO') : t('common.status_inactive', 'INACTIVO') }}
              </span>
            </div>

            <div class="ports-classification">
              <div>
                <span class="ports-title text-success">{{ t('enterprise.switching_trusted', 'Puertos Confiables (Trusted / Uplink):') }}</span>
                <div class="tags-group">
                  <span v-for="p in b.trusted_ports" :key="p" class="port-tag tag-trusted">
                    {{ p }}
                  </span>
                </div>
              </div>

              <div>
                <span class="ports-title text-warning"
                  >{{ t('enterprise.switching_untrusted', 'Puertos de Acceso (Untrusted / Confinados):') }}</span
                >
                <div class="tags-group">
                  <span v-for="p in b.untrusted_ports" :key="p" class="port-tag tag-untrusted">
                    {{ p }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
```

- **Replacement:**
```html
      <!-- ================================================================= -->
      <!-- TAB 4: Seguridad L2 & Rogue DHCP (Sub-tarea 20.4 / Hito 28.4)     -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'switching'"
        id="panel-switching"
        role="tabpanel"
        aria-labelledby="tab-btn-switching"
        class="tab-panel"
      >
        <div class="panel-action-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem;">
          <div>
            <span class="text-subtle text-xs">
              Configure <strong>DHCP Snooping</strong> individualmente por Bridge bajo Safe Mode (60s) o despliegue la política en toda la flota.
            </span>
          </div>
          <button
            id="btn-bulk-dhcp-snooping"
            type="button"
            class="tactical-btn btn-secondary"
            @click="navigateToBulkDhcpSnooping()"
          >
            <span>🚀</span>
            <span>{{ t('enterprise.btn_bulk_dhcp_snooping', 'Desplegar en Flota (Acciones Masivas)') }}</span>
          </button>
        </div>

        <div class="snooping-cards-grid">
          <div v-for="b in snoopingBridges" :key="b.bridge_name" class="bridge-card">
            <div class="bridge-header" style="display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
              <h2 class="bridge-name">Bridge: {{ b.bridge_name }}</h2>
              <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                <span
                  class="badge"
                  :class="b.dhcp_snooping_enabled ? 'badge-success' : 'badge-danger'"
                >
                  DHCP Snooping: {{ b.dhcp_snooping_enabled ? t('common.status_active', 'ACTIVO') : t('common.status_inactive', 'INACTIVO') }}
                </span>
                <span v-if="b.add_dhcp_option82" class="badge badge-info">Option 82</span>
                <button
                  :id="`btn-toggle-snooping-${b.bridge_name}`"
                  type="button"
                  class="tactical-btn"
                  :class="b.dhcp_snooping_enabled ? 'btn-secondary' : 'btn-primary'"
                  style="padding: 0.25rem 0.65rem; font-size: 0.75rem;"
                  @click="openSnoopingConfigModal(b)"
                >
                  <span v-if="b.dhcp_snooping_enabled">⚙️ Configurar / Desactivar</span>
                  <span v-else>⚡ Activar DHCP Snooping</span>
                </button>
              </div>
            </div>

            <div class="ports-classification">
              <div>
                <span class="ports-title text-success">{{ t('enterprise.switching_trusted', 'Puertos Confiables (Trusted / Uplink):') }}</span>
                <div class="tags-group">
                  <span v-for="p in b.trusted_ports" :key="p" class="port-tag tag-trusted">
                    {{ p }}
                  </span>
                  <span v-if="b.trusted_ports.length === 0" class="text-subtle text-xs">Ningún puerto marcado como Trusted</span>
                </div>
              </div>

              <div>
                <span class="ports-title text-warning"
                  >{{ t('enterprise.switching_untrusted', 'Puertos de Acceso (Untrusted / Confinados):') }}</span
                >
                <div class="tags-group">
                  <span v-for="p in b.untrusted_ports" :key="p" class="port-tag tag-untrusted">
                    {{ p }}
                  </span>
                  <span v-if="b.untrusted_ports.length === 0" class="text-subtle text-xs">Sin puertos Untrusted en este bridge</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Táctico de Activación / Configuración de DHCP Snooping por Bridge -->
        <div
          v-if="selectedBridgeForSnooping"
          id="modal-dhcp-snooping-config"
          class="modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-snooping-title"
        >
          <div class="modal-card remediation-modal">
            <header class="modal-header">
              <h3 id="modal-snooping-title">
                🛡️ Configurar DHCP Snooping — Bridge: {{ snoopingForm.bridge_name }}
              </h3>
              <button
                type="button"
                class="btn-close"
                aria-label="Cerrar modal de DHCP Snooping"
                @click="selectedBridgeForSnooping = null"
              >
                ✕
              </button>
            </header>
            <div class="modal-body">
              <div class="safemode-shield-alert mb-3">
                <span class="shield-icon">⚠️</span>
                <div class="shield-text">
                  <strong>Regla de Oro en RouterOS v7 (Puertos Trusted):</strong>
                  <p class="text-xs text-subtle mb-0">
                    Al activar <code>dhcp-snooping=yes</code>, RouterOS descarta paquetes <code>DHCP Offer/Ack</code> en todos los puertos <em>Untrusted</em>. Asegúrese de marcar el puerto troncal (Uplink hacia el servidor DHCP legítimo) como <strong>Trusted</strong>.
                  </p>
                </div>
              </div>

              <div class="form-group mb-3">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                  <input id="chk-snooping-enabled" v-model="snoopingForm.enabled" type="checkbox" />
                  <strong>Habilitar DHCP Snooping en <code>{{ snoopingForm.bridge_name }}</code></strong>
                </label>
              </div>

              <div class="form-group mb-3">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                  <input id="chk-snooping-option82" v-model="snoopingForm.add_dhcp_option82" type="checkbox" :disabled="!snoopingForm.enabled" />
                  <span>Inyectar <strong>DHCP Option 82</strong> (Agent Circuit ID / Remote ID)</span>
                </label>
              </div>

              <div class="form-group mb-3">
                <label class="text-xs font-bold mb-1" style="display: block;">
                  Seleccione los Puertos Confiables (Trusted / Uplink) en <code>{{ snoopingForm.bridge_name }}</code>:
                </label>
                <div v-if="snoopingForm.all_ports.length > 0" class="tags-group" style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
                  <button
                    v-for="p in snoopingForm.all_ports"
                    :key="p"
                    type="button"
                    class="port-tag"
                    :class="snoopingForm.trusted_ports.includes(p) ? 'tag-trusted' : 'tag-untrusted'"
                    style="cursor: pointer; border: 1px solid currentColor;"
                    @click="toggleTrustedPortInForm(p)"
                  >
                    {{ snoopingForm.trusted_ports.includes(p) ? `✓ Trusted: ${p}` : `Untrusted: ${p}` }}
                  </button>
                </div>
                <p v-else class="text-xs text-subtle mb-2">
                  Este bridge aún no tiene puertos miembros asociados en <code>/interface/bridge/port</code>.
                </p>

                <div style="display: flex; gap: 0.5rem; align-items: center;">
                  <input
                    id="input-manual-trusted-port"
                    v-model="snoopingForm.manual_trusted_port"
                    type="text"
                    class="tactical-input"
                    placeholder="Añadir interfaz troncal (ej: ether1 o sfp-sfpplus1)"
                  />
                  <button type="button" class="tactical-btn btn-secondary" @click="addManualTrustedPort">
                    + Añadir Trusted
                  </button>
                </div>
              </div>

              <div class="modal-actions-row">
                <button type="button" class="tactical-btn btn-secondary" @click="selectedBridgeForSnooping = null">
                  {{ t('common.cancel', 'Cancelar') }}
                </button>
                <button
                  id="btn-save-dhcp-snooping"
                  type="button"
                  class="tactical-btn btn-primary"
                  :disabled="actionLoading"
                  @click="handleSaveBridgeSnooping"
                >
                  <span v-if="actionLoading">⏳ Aplicando bajo Safe Mode...</span>
                  <span v-else>⚡ Guardar y Aplicar (Safe Mode 60s)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
```

---

### 2.5. Paso 5: Pruebas Nivel 11X y Escenarios Karate Labs BDD

1. **Pruebas Unitarias Backend (`fastapi/tests/api/test_enterprise_suite_hito20.unit.py`):**
   - Verificar `POST /api/v1/switching/dhcp-snooping/enable` con `enabled=True, add_dhcp_option82=True, trusted_ports=["ether1"], untrusted_ports=["ether2"]` y con `enabled=False`.
   - Verificar que la plantilla `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82` está presente en `_DEFAULT_STARTER_TEMPLATES`.
2. **Pruebas Unitarias Frontend (`vue3/src/views/EnterpriseComplianceView.unit.ts`):**
   - Verificar la apertura del modal `#modal-dhcp-snooping-config` al hacer clic en `#btn-toggle-snooping-bridge1`, el envío de `POST /api/v1/switching/dhcp-snooping/enable` al pulsar `#btn-save-dhcp-snooping`, y la navegación a `/bulk-ops` al pulsar `#btn-bulk-dhcp-snooping`.
3. **Escenarios Karate Labs BDD:**
   - En `fastapi/test/api_test.feature` (y `docs/examples/fastapi/test/api_test.feature`): validar contrato de `POST /api/v1/switching/dhcp-snooping/enable`.
   - En `vue3/test/ui_business_flow.feature` (y `docs/examples/vue3/test/ui_business_flow.feature`): validar presencia de controles de activación de DHCP Snooping y botón de despliegue masivo en `/enterprise/compliance?tab=switching`.
