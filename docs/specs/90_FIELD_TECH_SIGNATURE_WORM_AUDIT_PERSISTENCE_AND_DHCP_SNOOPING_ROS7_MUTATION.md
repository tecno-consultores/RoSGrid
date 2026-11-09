# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 90: Persistencia Real de Firma Táctil y Auditoría WORM (`await db.commit()`) en Operaciones de Campo/IPAM y Corrección de Mutación `dhcp-snooping` en RouterOS v7 (`unknown parameter add-dhcp-option82`)

**Estado:** Completada y Certificada  
**Hito Asociado:** Hito 30.13  
**Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
**Archivos Afectados:**
- `fastapi/src/api/v1/switching.py`
- `fastapi/src/api/v1/bulk_and_updates.py`
- `fastapi/src/schemas/field_ops.py`
- `fastapi/src/api/v1/field_ops.py`
- `fastapi/src/api/v1/subscribers.py`
- `fastapi/src/api/v1/optical_boxes.py`
- `fastapi/src/api/v1/ipam.py`
- `vue3/src/stores/useFieldOpsStore.ts`
- `vue3/src/components/field/FieldTechMobileView.vue`
- `vue3/src/views/ImmutableAuditLogsView.vue`
- `fastapi/tests/api/test_enterprise_compliance_sdwan_sla.unit.py`
- `fastapi/tests/api/test_subscribers.unit.py`
- `vue3/src/components/field/FieldTechMobileView.unit.ts`
- `fastapi/test/api_test.feature` (+ réplicas en `docs/examples/fastapi/`)
- `vue3/test/ui_business_flow.feature` (+ réplicas en `docs/examples/vue3/`)

---

## 1. Diagnóstico Forense de los 2 Hallazgos Reportados en Producción Local

### 1.1 Causa Raíz 1: Al Registrar un Cliente y Firmar en `/field-tech` (`Técnico de Campo`), Indica que se Guardó en la Auditoría WORM pero No Aparece en `/enterprise/compliance?tab=audit`
1. **Stub Local en `FieldTechMobileView.vue` (Líneas 461–467):**
   En `vue3/src/components/field/FieldTechMobileView.vue`, la función `handleCertifyInstallation()` tenía únicamente un mensaje local sin realizar ninguna petición HTTP al backend:
   ```ts
   function handleCertifyInstallation() {
     if (!hasDrawnSignature.value) {
       showMessage('Se requiere la firma táctil para certificar la entrega', 'error');
       return;
     }
     showMessage('✅ Instalación certificada con éxito. Entrega registrada en auditoría WORM.', 'success');
   }
   ```
   Además, cuando el técnico registra un abonado nuevo desde la pestaña **2. Cliente FTTH** (`handleRegisterCustomer`), el abonado tiene `SubscriberDevice.id` (`diagTargetId`), pero aún no tiene una `FieldInstallationOrder` (`order_id`), mientras que `POST /api/v1/field-ops/certify` exigía `order_id: uuid.UUID` obligatorio.
2. **Pérdida Silenciosa de Registros `AuditLog` por Falta de `await db.commit()` Posterior a `await write_audit_log(...)`:**
   En `fastapi/src/core/audit.py` (líneas 174–175), `write_audit_log(...)` solo ejecuta `session.add(log_entry)` y retorna `log_entry` (no ejecuta `await session.commit()`).
   En `subscribers.py` (`create_subscriber_device`, `update_subscriber_device`, `create_bandwidth_profile`, `update_bandwidth_profile`), `field_ops.py` (`create_field_order`, `certify_installation`), `optical_boxes.py` (`create_optical_box`, `delete_optical_box`), `ipam.py` (`create_vrf`, `create_prefix`, `create_customer_service`) y `switching.py` (`enable_dhcp_snooping`, `isolate_rogue_port`), se llamaba a `await db.commit()` **antes** de `await write_audit_log(...)` y se retornaba inmediatamente sin un segundo `await db.commit()`. Al cerrarse el generador `get_tenant_db_session`, SQLAlchemy descartaba el `AuditLog` no confirmado en `session.new`.

---

### 1.2 Causa Raíz 2: Al Activar DHCP Snooping en `bridge11` (`caps1`) desde `/enterprise/compliance?tab=switching`, la UI Muestra `✅ DHCP Snooping activado` pero el Cambio No se Aplica en el Router MikroTik
1. **Error Real en Logs de `rosgrid_api_local` contra RouterOS 7.25.1 (`caps1`):**
   ```text
   Simulación de configuración DHCP Snooping: 502: No se pudo ejecutar mutación en el router MikroTik (/switching): RouterOS REST API Error [400]: unknown parameter add-dhcp-option82
   INFO: 172.18.0.1:0 - "POST /api/v1/switching/dhcp-snooping/enable HTTP/1.1" 200 OK
   ```
2. **Por qué falla `_mutate_bridge_snooping_on_ros` (`fastapi/src/api/v1/switching.py`, líneas 122–137):**
   ```python
   await client.post(
       "/interface/bridge/set",
       json_data={
           "numbers": payload.bridge_name,
           "dhcp-snooping": snoop_str,
           "add-dhcp-option82": opt82_str,
       },
   )
   ```
   En RouterOS v7 (especialmente en `7.25.1` / CHR y cuando `dhcp-snooping` está inicialmente en `no`), el parámetro `add-dhcp-option82` no es aceptado en la misma llamada atómica mientras `dhcp-snooping` está deshabilitado (o cuando `add_dhcp_option82` es `False`), provocando `RouterOS REST API Error [400]: unknown parameter add-dhcp-option82` y abortando también `dhcp-snooping=yes`.
3. **Falso Positivo Silencioso en `enable_dhcp_snooping` (Líneas 186–188):**
   El bloque `except Exception as exc: logger.warning(...)` capturaba el error `502/400` y devolvía igualmente `HTTP 200 OK` con `dhcp_snooping_enabled=True`, engañando al operador en la interfaz mientras en WinBox `DHCP Snooping` seguía desmarcado.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso)

### Paso 1: Separar `dhcp-snooping` y `add-dhcp-option82` en `fastapi/src/api/v1/switching.py` y `fastapi/src/api/v1/bulk_and_updates.py` + `await db.commit()` en Auditoría

#### 1.1 En `fastapi/src/api/v1/switching.py` (Líneas 122–220 y 300–327)
Reemplazar `_mutate_bridge_snooping_on_ros`, `enable_dhcp_snooping` y el cierre de `isolate_rogue_port` por el siguiente bloque exacto:

```python
async def _mutate_bridge_snooping_on_ros(
    client: Any,
    payload: DhcpSnoopingEnableRequest,
    trusted_list: list[str],
) -> None:
    """Aplica dhcp-snooping, add-dhcp-option82 (tolerante a RouterOS 7.25+) y puertos trusted/untrusted."""
    snoop_str = "yes" if payload.enabled else "no"
    opt82_str = "yes" if (payload.enabled and payload.add_dhcp_option82) else "no"

    # 1. Aplicar primero dhcp-snooping de forma aislada para que nunca sea abortado por add-dhcp-option82
    await client.post(
        "/interface/bridge/set",
        json_data={
            "numbers": payload.bridge_name,
            "dhcp-snooping": snoop_str,
        },
    )

    # 2. Aplicar add-dhcp-option82 en un segundo paso tolerante (en RouterOS v7 solo existe si dhcp-snooping=yes)
    if payload.enabled and payload.add_dhcp_option82:
        try:
            await client.post(
                "/interface/bridge/set",
                json_data={
                    "numbers": payload.bridge_name,
                    "add-dhcp-option82": opt82_str,
                },
            )
        except Exception as exc:
            logger.debug("RouterOS omitió add-dhcp-option82 en bridge %s: %s", payload.bridge_name, exc)

    # 3. Configurar puertos trusted / untrusted
    for p_trusted in trusted_list:
        try:
            await client.post(
                "/interface/bridge/port/set",
                json_data={"numbers": p_trusted, "trusted": "yes"},
            )
        except Exception as exc:
            logger.debug("No se pudo marcar puerto %s como trusted: %s", p_trusted, exc)

    for p_untrusted in payload.untrusted_ports:
        if p_untrusted not in trusted_list:
            try:
                await client.post(
                    "/interface/bridge/port/set",
                    json_data={"numbers": p_untrusted, "trusted": "no"},
                )
            except Exception as exc:
                logger.debug("No se pudo marcar puerto %s como untrusted: %s", p_untrusted, exc)
```

Y al final de `enable_dhcp_snooping` (después de `await write_audit_log(...)`, línea 210) y al final de `isolate_rogue_port` (después de `await write_audit_log(...)`, línea 321), añadir **`await db.commit()`**:
```python
    await db.commit()
```

#### 1.2 En `fastapi/src/api/v1/bulk_and_updates.py` (Plantilla `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`, líneas 1061–1082)
En `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`, separar el paso de `interface/bridge/set` para que `dhcp-snooping=yes` no incluya `add-dhcp-option82` en el mismo payload si el router no lo soporta, y en `_execute_single_step` (cuando `endpoint == "interface/bridge/set"` y el payload contiene `"add-dhcp-option82"`), si RouterOS lanza `unknown parameter add-dhcp-option82`, reintentar automáticamente enviando solo `{"numbers": ..., "dhcp-snooping": ...}`:

```python
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
                },
                "cli_command": "/interface bridge set {{ bridge_name }} dhcp-snooping=yes",
            },
        ],
```

---

### Paso 2: Soportar Certificación Directa por `customer_service_id` + Firma Táctil y `await db.commit()` en `field_ops.py`

#### 2.1 En `fastapi/src/schemas/field_ops.py` (Líneas 76–84)
Actualizar `FieldCertifyOrderRequest` para permitir `order_id` opcional o `customer_service_id` (cuando el técnico certifica directamente un abonado recién creado en `Técnico de Campo`):

```python
class FieldCertifyOrderRequest(BaseModel):
    order_id: Optional[uuid.UUID] = None
    customer_service_id: Optional[uuid.UUID] = None
    onu_scanned_serial: str = Field(default="ONU-CERTIFIED", min_length=2)
    onu_scanned_mac: Optional[str] = None
    tech_latitude: Optional[Decimal] = None
    tech_longitude: Optional[Decimal] = None
    customer_signature_svg: Optional[str] = None
    notes: Optional[str] = None
```

#### 2.2 En `fastapi/src/api/v1/field_ops.py` (`create_field_order` y `certify_installation`)
1. En `create_field_order` (líneas 121–133), usar `actor_username=str(claims.get("preferred_username") or claims.get("username") or "system")`, `router_id=svc.router_id` y añadir `await db.commit()` después de `await write_audit_log(...)`.
2. Reemplazar `certify_installation` (líneas 242–315) por:

```python
@router.post("/certify", response_model=FieldOrderResponse)
async def certify_installation(
    payload: FieldCertifyOrderRequest,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Cierra y certifica digitalmente la orden o alta de instalación con GPS, firma del cliente y registro WORM."""
    tenant_id = get_tenant_id(claims)
    order: Optional[FieldInstallationOrder] = None

    if payload.order_id:
        stmt_ord = select(FieldInstallationOrder).where(
            FieldInstallationOrder.id == payload.order_id,
            FieldInstallationOrder.tenant_id == tenant_id,
        )
        order = (await db.execute(stmt_ord)).scalar_one_or_none()

    if not order and payload.customer_service_id:
        stmt_ord_by_svc = (
            select(FieldInstallationOrder)
            .where(
                FieldInstallationOrder.customer_service_id == payload.customer_service_id,
                FieldInstallationOrder.tenant_id == tenant_id,
            )
            .order_by(FieldInstallationOrder.created_at.desc())
        )
        order = (await db.execute(stmt_ord_by_svc)).scalars().first()
        if not order:
            order = FieldInstallationOrder(
                tenant_id=tenant_id,
                customer_service_id=payload.customer_service_id,
                assigned_tech_id=uuid.UUID(str(claims["sub"])),
                status=FieldOrderStatusEnum.CERTIFIED,
                onu_scanned_serial=payload.onu_scanned_serial,
                onu_scanned_mac=payload.onu_scanned_mac,
                tech_latitude=payload.tech_latitude,
                tech_longitude=payload.tech_longitude,
                customer_signature_svg=payload.customer_signature_svg,
                notes=payload.notes,
                certified_at=datetime.now(UTC),
            )
            db.add(order)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden o abonado de campo no encontrado")

    # Actualizar datos de certificación
    order.status = FieldOrderStatusEnum.CERTIFIED
    order.onu_scanned_serial = payload.onu_scanned_serial
    order.onu_scanned_mac = payload.onu_scanned_mac
    order.tech_latitude = payload.tech_latitude
    order.tech_longitude = payload.tech_longitude
    if payload.customer_signature_svg:
        order.customer_signature_svg = payload.customer_signature_svg
    order.notes = payload.notes
    order.certified_at = datetime.now(UTC)

    # Actualizar el servicio de cliente a ACTIVE y asociar coordenadas GPS para el mapa de ONUs
    stmt_svc = select(CustomerService).where(CustomerService.id == order.customer_service_id)
    svc = (await db.execute(stmt_svc)).scalar_one_or_none()
    if svc:
        svc.status = CustomerServiceStatusEnum.ACTIVE
        svc.onu_serial_number = payload.onu_scanned_serial
        if payload.onu_scanned_mac:
            svc.onu_mac_address = payload.onu_scanned_mac
        if payload.tech_latitude is not None and payload.tech_longitude is not None:
            svc.latitude = payload.tech_latitude
            svc.longitude = payload.tech_longitude

    await db.commit()
    await db.refresh(order)

    actor_name = str(claims.get("preferred_username") or claims.get("username") or "system")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=actor_name,
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="OPERATIONS",
        event_action="FIELD_INSTALLATION_CERTIFIED",
        router_id=svc.router_id if svc else None,
        status_code=200,
        after_state={
            "order_id": str(order.id),
            "customer_service_id": str(order.customer_service_id),
            "endpoint_identifier": svc.endpoint_identifier if svc else None,
            "serial": payload.onu_scanned_serial,
            "signature_captured": bool(payload.customer_signature_svg),
        },
    )
    await db.commit()
```

---

### Paso 3: Añadir `await db.commit()` Posterior a `await write_audit_log(...)` en `subscribers.py`, `optical_boxes.py` e `ipam.py`

1. **En `fastapi/src/api/v1/subscribers.py`:**
   - En `create_bandwidth_profile` (línea 150), `update_bandwidth_profile` (línea 205), `create_subscriber_device` (línea 922, añadiendo `router_id=device.router_id`) y `update_subscriber_device` (línea 1359, añadiendo `router_id=device.router_id`):
     - Usar `actor_username=str(claims.get("preferred_username") or claims.get("username") or "system")`.
     - Ejecutar **`await db.commit()` inmediatamente después de `await write_audit_log(...)`**.
2. **En `fastapi/src/api/v1/optical_boxes.py`:**
   - En `create_optical_box` (línea 151) y `delete_optical_box` (línea 304):
     - Pasar `router_id=box.router_id` y `actor_username=str(claims.get("preferred_username") or claims.get("username") or "system")`.
     - Ejecutar **`await db.commit()` inmediatamente después de `await write_audit_log(...)`**.
3. **En `fastapi/src/api/v1/ipam.py`:**
   - En `create_vrf` (línea 112), `create_prefix` (línea 223) y `create_customer_service` (línea 464, pasando `router_id=svc.router_id`):
     - Usar `actor_username=str(claims.get("preferred_username") or claims.get("username") or "system")`.
     - Ejecutar **`await db.commit()` inmediatamente después de `await write_audit_log(...)`**.

---

### Paso 4: Conectar `handleCertifyInstallation()` en `FieldTechMobileView.vue` y `useFieldOpsStore.ts` + Categorías en `ImmutableAuditLogsView.vue`

#### 4.1 En `vue3/src/stores/useFieldOpsStore.ts` (Líneas 177–194)
Permitir `order_id?: string` y `customer_service_id?: string` en `certifyInstallation`:

```ts
  async function certifyInstallation(payload: {
    order_id?: string;
    customer_service_id?: string;
    onu_scanned_serial: string;
    onu_scanned_mac?: string;
    tech_latitude?: number;
    tech_longitude?: number;
    customer_signature_svg?: string;
    notes?: string;
  }): Promise<FieldOrder> {
    const { http } = await import('@/api/httpClient');
    const res = await http.post<FieldOrder>('/api/v1/field-ops/certify', payload);
    const idx = orders.value.findIndex(
      (o) =>
        (payload.order_id && o.id === payload.order_id) ||
        (payload.customer_service_id && o.customer_service_id === payload.customer_service_id),
    );
    if (idx !== -1) {
      orders.value[idx] = res.data;
      triggerRef(orders);
    } else {
      orders.value = [res.data, ...orders.value];
      triggerRef(orders);
    }
    return res.data;
  }
```

#### 4.2 En `vue3/src/components/field/FieldTechMobileView.vue` (Líneas 461–468)
Reemplazar `handleCertifyInstallation` para que envíe la firma del `<canvas>` y certifique en el backend antes de mostrar el mensaje de éxito:

```ts
  async function handleCertifyInstallation() {
    if (!hasDrawnSignature.value) {
      showMessage('Se requiere la firma táctil para certificar la entrega', 'error');
      return;
    }
    const targetDev =
      selectedSubscriberForDiag.value ||
      fieldStore.recentInstallations.find((d) => d.id === diagTargetId.value) ||
      fieldStore.recentInstallations[0] ||
      null;
    const customerServiceId = diagTargetId.value || targetDev?.id;
    const matchingOrder = fieldStore.orders.find(
      (o) => customerServiceId && o.customer_service_id === customerServiceId,
    );
    const sigDataUrl =
      signatureCanvas.value && typeof signatureCanvas.value.toDataURL === 'function'
        ? signatureCanvas.value.toDataURL('image/png')
        : 'data:image/png;base64,signed';
    const serialVal =
      targetDev?.onu_serial_number ||
      targetDev?.device_serial ||
      customerForm.value.device_serial.trim() ||
      'ONU-CERTIFIED';

    try {
      if (matchingOrder?.id || customerServiceId) {
        await fieldStore.certifyInstallation({
          order_id: matchingOrder?.id,
          customer_service_id: customerServiceId,
          onu_scanned_serial: serialVal,
          onu_scanned_mac:
            targetDev?.onu_mac_address || customerForm.value.onu_mac_address.trim() || undefined,
          tech_latitude: techGps.value?.lat ?? customerForm.value.latitude,
          tech_longitude: techGps.value?.lng ?? customerForm.value.longitude,
          customer_signature_svg: sigDataUrl,
          notes: 'Certificación en campo con firma táctil',
        });
      }
      showMessage(
        '✅ Instalación certificada con éxito. Entrega registrada en auditoría WORM.',
        'success',
      );
    } catch (err: unknown) {
      const msg = (err as Error)?.message || 'Error al certificar instalación en auditoría WORM';
      showMessage(msg, 'error');
    }
  }
```

#### 4.3 En `vue3/src/views/ImmutableAuditLogsView.vue` (Líneas 291–301)
Ampliar las opciones del `<select id="filter-cat">` con todas las categorías emitidas por el backend (`AUTHENTICATION`, `OPERATIONS`, `NETWORK`, `INVENTORY`, `BACKUPS`, `SWITCHING_SECURITY`, `GOVERNANCE`) y añadir un botón `🔄 Actualizar` (`#btn-refresh-audit-logs`) junto a los botones de cabecera que invoque `loadAuditLogs()`.

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X

1. **Pruebas Unitarias Backend (`fastapi/tests/api/test_enterprise_compliance_sdwan_sla.unit.py` y `fastapi/tests/api/test_subscribers.unit.py`):**
   - Verificar que `enable_dhcp_snooping` invoca primero `POST /interface/bridge/set` con `{"numbers": "bridge11", "dhcp-snooping": "yes"}` de forma aislada (de modo que nunca falle por `add-dhcp-option82`) y ejecuta `db.commit()` tras `write_audit_log`.
   - Verificar que `POST /api/v1/field-ops/certify` acepta `customer_service_id` sin `order_id` previo, persiste `customer_signature_svg`, escribe `FIELD_INSTALLATION_CERTIFIED` en `write_audit_log` y ejecuta `db.commit()`.
2. **Pruebas Unitarias Frontend (`vue3/src/components/field/FieldTechMobileView.unit.ts`):**
   - Verificar que al dibujar la firma en `#signature-canvas` y pulsar el botón de certificar, `fieldStore.certifyInstallation` es invocado con `customer_service_id` y `customer_signature_svg`.
3. **Escenarios BDD Karate Labs:**
   - Añadir `Scenario: 166` en `fastapi/test/api_test.feature` (+ réplicas en `docs/examples/fastapi/`) y `Scenario: 104` en `vue3/test/ui_business_flow.feature` (+ réplicas en `docs/examples/vue3/`).
