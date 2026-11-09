# Especificación Técnica 94: Remediación de Error HTTP 500 al Finalizar y Certificar Instalación en Campo (`column field_installation_orders.customer_signature_svg does not exist`), Guardrail de Paridad de Columnas ORM/Alembic e Internacionalización Completa de `FieldTechMobileView.vue`

**Estado:** Implementado y Certificado al 100% (`Hito 30.17` en `ROADMAP.md`)
**Componentes Afectados:**
- Migración de Base de Datos PostgreSQL (Alembic):
  - `fastapi/migrations/versions/0014_field_order_signature_svg.py` *(nuevo archivo)*
- Endpoints Backend:
  - `fastapi/src/api/v1/field_ops.py` (`certify_installation` y `create_field_order`)
- Script de Gobernanza y Certificación ORM/Alembic:
  - `.agents/scripts/verify_alembic_orm_parity.py`
- Diccionarios y Vista Frontend:
  - `vue3/src/locales/es.json` (bloque `"field_tech"`)
  - `vue3/src/locales/en.json` (bloque `"field_tech"`)
  - `vue3/src/components/field/FieldTechMobileView.vue`
- Pruebas Nivel 11X (Creación y Ejecución Obligatoria):
  - `fastapi/tests/api/test_subscribers.unit.py`
  - `vue3/src/components/field/FieldTechMobileView.unit.ts`
  - `fastapi/test/api_test.feature` y `docs/examples/fastapi/api_test.feature.example` (Escenario Karate Labs BDD 169)
  - `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 108)

---

## 1. Diagnóstico Forense de Causa Raíz (Evidencia en Logs de `rosgrid_api_local` y `rosgrid_db_local`)

Al hacer clic en **`🚀 Finalize & Certify Installation`** (`#btn-certify-order`) en la vista **Field Technician Dashboard FTTH** (`/field-ops`), el backend responde con **`⚠️ HTTP 500: Internal Server Error`**.

### 1.1. Causa Raíz 1 (Error 500 en PostgreSQL): `UndefinedColumnError: column field_installation_orders.customer_signature_svg does not exist`
La traza exacta capturada en `rosgrid_api_local` es:
```text
sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError)
column field_installation_orders.customer_signature_svg does not exist
[SQL: SELECT field_installation_orders.id, ..., field_installation_orders.customer_signature_svg, ...
FROM field_installation_orders
WHERE field_installation_orders.customer_service_id = $1::UUID AND field_installation_orders.tenant_id = $2::UUID
ORDER BY field_installation_orders.created_at DESC]
```
**Por qué ocurre esta discrepancia entre el modelo SQLAlchemy ORM y PostgreSQL:**
1. En la migración `0004_ipam_and_field_ops.py` (línea 175), la tabla `field_installation_orders` fue creada originalmente con la columna `sa.Column("customer_signature_svg", sa.Text(), nullable=True)`.
2. Sin embargo, en la migración `0005_tenant_feature_flags_and_technical_qos.py` (líneas 97–98), se ejecutó `op.drop_column("field_installation_orders", "customer_signature_svg")`, eliminando la columna en PostgreSQL mientras que el modelo ORM `FieldInstallationOrder` (`fastapi/src/models/ipam.py`, línea 416) conservó `customer_signature_svg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)`.
3. Al conectarse en el Hito 30.13 (`Spec 90`) el botón `#btn-certify-order` de `FieldTechMobileView.vue` con `POST /api/v1/field-ops/certify`, SQLAlchemy intenta seleccionar e insertar `customer_signature_svg` en `field_installation_orders`, provocando el `HTTP 500` inmediato en PostgreSQL.
4. **Por qué escapó al validador `.agents/scripts/verify_alembic_orm_parity.py`:** El script solo verificaba existencia de nombres de tablas (`__tablename__` vs `op.create_table` / `op.rename_table`), pero no verificaba **paridad a nivel de columnas** (columnas eliminadas con `op.drop_column` en una migración que siguen declaradas en `Base.metadata.tables`).

### 1.2. Causa Raíz 2 (Riesgo Transaccional y Truncamiento en `certify_installation` — `fastapi/src/api/v1/field_ops.py`)
1. **Doble `await db.commit()` y reinicio de `set_config(..., is_local=true)`:**
   En `fastapi/src/db/session.py` (línea 41), `set_tenant_context` invoca `set_config('app.current_tenant_id', :tid, true)` con `is_local=true` (ámbito exclusivo de la transacción actual). En `certify_installation` (`field_ops.py`, líneas 315 y 338) y `create_field_order` (líneas 118 y 134), llamar a `await db.commit()` antes de `await db.refresh(order)` y antes de `await write_audit_log(...)` cierra la primera transacción y deja `app.current_tenant_id = ''` en la segunda transacción. Usar `await db.flush()` antes de `write_audit_log(...)` y ejecutar un **único** `await db.commit()` al final mantiene toda la operación y el registro WORM dentro de la misma transacción atómica con RLS activo.
2. **Longitud de `onu_scanned_mac` (`VARCHAR(17)`) y `onu_scanned_serial` (`VARCHAR(64)`):**
   Truncar defensivamente `onu_scanned_mac` a 17 caracteres y `onu_scanned_serial` a 64 caracteres evita errores `StringDataRightTruncationError` si el formulario envía cadenas con prefijos o espacios.

### 1.3. Causa Raíz 3 (Textos en Español en `/field-ops` cuando el Idioma Activo es Inglés `EN`)
Como se observa en la captura de pantalla del usuario en `http://localhost:8085/field-ops` con idioma inglés activo:
- El botón de la 4.ª pestaña muestra `🗺️ Mapa de Zona` (línea 606 de `FieldTechMobileView.vue`).
- En la pestaña **Diagnostics & Certification** (`activeTab === 'diagnostics'`):
  - El título muestra `⚡ Diagnóstico en Tiempo Real y Certificación 1-Click` y el subtítulo `Verifique conectividad ICMP, salto de gateway, salida a internet y resolución DNS desde el router MikroTik.` (líneas 1055–1058).
  - Los 3 botones muestran `⚡ Ping 1-Click`, `🌐 Diagnóstico Rápido` y `🩺 Diagnóstico 360° Integral (MTU+Logs+Torch)` (líneas 1086–1106).
  - La marca de agua del canvas muestra `Dibujar rúbrica de conformidad aquí con el dedo o stylus` (línea 1187).
  - La tarjeta de actividad reciente muestra `Puerto 1` (línea 1226) en lugar de `Port 1`.
- En las pestañas **Register NAP Box** y **Register New FTTH Customer**, los encabezados de tarjeta y etiquetas secundarias también tienen cadenas fijas en español sin `t('field_tech.*')`.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash High)

### Paso 1: Crear la Migración Alembic `fastapi/migrations/versions/0014_field_order_signature_svg.py`

> **REGLA CRÍTICA DE ALEMBIC:** El identificador `revision` debe tener `<= 32` caracteres (`"0014_field_order_signature_svg"` tiene 30 caracteres).

Crear el archivo `fastapi/migrations/versions/0014_field_order_signature_svg.py` con el siguiente contenido exacto:

```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0014_field_order_signature_svg

Revision ID: 0014_field_order_signature_svg
Revises: 0013_tenant_onboarding_flag
Create Date: 2026-11-07 20:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_field_order_signature_svg"
down_revision: str | None = "0013_tenant_onboarding_flag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Restaura customer_signature_svg en field_installation_orders (eliminada en 0005)
    # usando DDL idempotente para tolerar bases de datos donde ya exista o no exista.
    op.execute(
        sa.text(
            "ALTER TABLE field_installation_orders "
            "ADD COLUMN IF NOT EXISTS customer_signature_svg TEXT;"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE field_installation_orders "
            "DROP COLUMN IF EXISTS customer_signature_svg;"
        )
    )
```

---

### Paso 2: Transacción Atómica y Sanitización en `fastapi/src/api/v1/field_ops.py`

En `fastapi/src/api/v1/field_ops.py`:
1. En `create_field_order` (líneas 110–135), reemplazar el doble `await db.commit()` por `await db.flush()` antes de `await write_audit_log(...)` y un único `await db.commit()` + `await db.refresh(order)` al final.
2. En `certify_installation` (líneas 244–355), sanitizar `clean_serial = (payload.onu_scanned_serial or "ONU-CERTIFIED").strip()[:64]` y `clean_mac = payload.onu_scanned_mac.strip()[:17] if payload.onu_scanned_mac else None`, y usar `await db.flush()` antes de `await write_audit_log(...)` seguido de un único `await db.commit()` + `await db.refresh(order)`:

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

    clean_serial = (payload.onu_scanned_serial or "ONU-CERTIFIED").strip()[:64]
    clean_mac = payload.onu_scanned_mac.strip()[:17] if payload.onu_scanned_mac else None

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
        ord_scalars = (await db.execute(stmt_ord_by_svc)).scalars()
        orders_matched = ord_scalars.all() if hasattr(ord_scalars, "all") else list(ord_scalars)
        order = orders_matched[0] if orders_matched else None
        if not order:
            order = FieldInstallationOrder(
                tenant_id=tenant_id,
                customer_service_id=payload.customer_service_id,
                assigned_tech_id=uuid.UUID(str(claims["sub"])),
                status=FieldOrderStatusEnum.CERTIFIED,
                onu_scanned_serial=clean_serial,
                onu_scanned_mac=clean_mac,
                tech_latitude=payload.tech_latitude,
                tech_longitude=payload.tech_longitude,
                customer_signature_svg=payload.customer_signature_svg,
                notes=payload.notes,
                certified_at=datetime.now(UTC),
            )
            db.add(order)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden o abonado de campo no encontrado",
        )

    # Actualizar datos de certificación
    order.status = FieldOrderStatusEnum.CERTIFIED
    order.onu_scanned_serial = clean_serial
    order.onu_scanned_mac = clean_mac
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
        svc.onu_serial_number = clean_serial
        if clean_mac:
            svc.onu_mac_address = clean_mac
        if payload.tech_latitude is not None and payload.tech_longitude is not None:
            svc.latitude = payload.tech_latitude
            svc.longitude = payload.tech_longitude

    if hasattr(db, "flush"):
        await db.flush()

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
            "serial": clean_serial,
            "signature_captured": bool(payload.customer_signature_svg),
        },
    )
    await db.commit()
    await db.refresh(order)

    if payload.tech_latitude is not None and payload.tech_longitude is not None:
        await publish_network_service_event(
            tenant_id=tenant_id,
            event_name="DEVICE_ACTIVATED_GPS",
            payload={
                "order_id": str(order.id),
                "customer_service_id": str(order.customer_service_id),
                "device_serial": clean_serial,
                "latitude": float(payload.tech_latitude),
                "longitude": float(payload.tech_longitude),
                "activated_at": datetime.now(UTC).isoformat(),
            },
        )

    return order
```

---

### Paso 3: Ampliar `.agents/scripts/verify_alembic_orm_parity.py` con Auditoría de Columnas Eliminadas (`op.drop_column`)

En `.agents/scripts/verify_alembic_orm_parity.py`, añadir una función `verify_dropped_columns_not_in_orm()` que recorra los archivos de `fastapi/migrations/versions/*.py` en orden cronológico (`sorted(MIGRATIONS_DIR.glob("*.py"))`), registre las columnas eliminadas con `op.drop_column("<table>", "<col>")` y las columnas añadidas con `op.add_column("<table>", sa.Column("<col>", ...))` o `ADD COLUMN IF NOT EXISTS <col>`, y verifique que ninguna columna actualmente marcada como eliminada siga declarada como ` mapped_column(` en la clase ORM correspondiente de `fastapi/src/models/*.py`:

```python
def verify_dropped_columns_not_in_orm() -> list[tuple[str, str]]:
    """Detecta columnas eliminadas vía op.drop_column que siguen declaradas en los modelos ORM sin migración de restauración."""
    drop_re = re.compile(r'op\.drop_column\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)')
    add_re = re.compile(
        r'op\.add_column\(\s*["\']([^"\']+)["\']\s*,\s*sa\.Column\(\s*["\']([^"\']+)["\']'
    )
    sql_add_re = re.compile(
        r'ALTER\s+TABLE\s+([a-zA-Z0-9_]+)\s+ADD\s+COLUMN(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-zA-Z0-9_]+)',
        re.IGNORECASE,
    )
    rename_table_re = re.compile(
        r'op\.rename_table\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'
    )

    dropped_cols: set[tuple[str, str]] = set()
    for mig_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        content = mig_file.read_text(encoding="utf-8")
        # Extraer solo el cuerpo de upgrade() antes de def downgrade()
        upgrade_body = content.split("def downgrade")[0]
        for m in drop_re.finditer(upgrade_body):
            dropped_cols.add((m.group(1), m.group(2)))
        for m in rename_table_re.finditer(upgrade_body):
            old_t, new_t = m.group(1), m.group(2)
            for t, c in list(dropped_cols):
                if t == old_t:
                    dropped_cols.add((new_t, c))
        for m in add_re.finditer(upgrade_body):
            dropped_cols.discard((m.group(1), m.group(2)))
        for m in sql_add_re.finditer(upgrade_body):
            dropped_cols.discard((m.group(1), m.group(2)))

    # Verificar si alguna columna en dropped_cols sigue definida como mapped_column en el ORM
    violations: list[tuple[str, str]] = []
    class_split_re = re.compile(r"(?=^class\s+\w+\()", re.MULTILINE)
    tname_re = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
    for py_file in MODELS_DIR.glob("*.py"):
        if py_file.name in ("__init__.py", "base.py"):
            continue
        content = py_file.read_text(encoding="utf-8")
        for block in class_split_re.split(content):
            tm = tname_re.search(block)
            if not tm:
                continue
            table_name = tm.group(1)
            for t, col_name in sorted(dropped_cols):
                if t == table_name and re.search(rf"^\s*{re.escape(col_name)}\s*:\s*Mapped\[", block, re.MULTILINE):
                    violations.append((table_name, col_name))
    return violations
```
Invocar `verify_dropped_columns_not_in_orm()` dentro de `main()` de `.agents/scripts/verify_alembic_orm_parity.py`.

---

### Paso 4: Completar la Traducción al Inglés (`i18n` EN/ES) de `FieldTechMobileView.vue`

1. **En `vue3/src/locales/es.json` y `vue3/src/locales/en.json` (bloque `"field_tech"`):**
   Añadir las siguientes claves después de `"ports_24"`:
   - En `vue3/src/locales/es.json`:
   ```json
    "ports_24": "24 Puertos",
    "ports_8": "8 Puertos",
    "ports_16": "16 Puertos",
    "tab_map": "Mapa de Zona",
    "nap_form_title": "Registrar Nueva Caja de Distribución Óptica (NAP)",
    "nap_form_desc": "Geolocalice la caja y configure su capacidad de splitters para permitir altas de clientes.",
    "nap_router_label": "Router Asignador / Sede *",
    "nap_router_placeholder": "Seleccione un router...",
    "nap_location_placeholder": "Ej: Av. Bolívar Poste Eléctrico #14 frente a FarmaCentro",
    "nap_deployed_list_title": "Cajas NAP Desplegadas",
    "nap_empty_hint": "No hay cajas NAP registradas aún. Registre la primera caja a la izquierda.",
    "nap_unspecified_location": "Ubicación sin especificar",
    "cust_form_title": "Registrar y Aprovisionar Nuevo Cliente FTTH",
    "cust_form_desc": "Asocie la ONU al puerto disponible de la Caja NAP y valide la potencia óptica recibida en domicilio.",
    "cust_nap_placeholder": "Seleccione una caja NAP...",
    "port_label": "Puerto",
    "cust_onu_mac_label": "MAC WAN de la ONU (Para Reserva DHCP / PPPoE en NOC) *",
    "optional_inventory": "(Opcional — Inventario)",
    "optical_advice_optimal": "El nivel de luz se encuentra en el rango de máxima estabilidad y cero jitter.",
    "optical_advice_warning": "Atenuación elevada. Verifique curvatura del cable drop o limpieza del conector SC/APC.",
    "optical_advice_critical": "Riesgo inminente de desconexión o pérdida de tramas FEC. Requiere re-fusionar el drop.",
    "home_coords_title": "Coordenadas del Domicilio",
    "nap_detail_title": "Detalle de la Caja NAP",
    "nap_detail_empty": "Seleccione una Caja NAP en el formulario para inspeccionar sus puertos y capacidad.",
    "nap_port_matrix_title": "Matriz de Puertos",
    "diag_form_title": "Diagnóstico en Tiempo Real y Certificación 1-Click",
    "diag_form_desc": "Verifique conectividad ICMP, salto de gateway, salida a internet y resolución DNS desde el router MikroTik.",
    "btn_testing_ping": "⏳ Probando...",
    "btn_ping_1click": "⚡ Ping 1-Click",
    "btn_diagnosing": "⏳ Diagnosticando...",
    "btn_quick_diag": "🌐 Diagnóstico Rápido",
    "btn_running_360": "⏳ Ejecutando 360°...",
    "btn_diag_360": "🩺 Diagnóstico 360° Integral (MTU+Logs+Torch)",
    "signature_watermark": "Dibujar rúbrica de conformidad aquí con el dedo o stylus",
    "recent_empty_hint": "No hay instalaciones recientes registradas en este turno.",
    "map_form_title": "Mapa de Zona & Topología FTTH",
    "map_form_desc": "Visualice clientes y cajas NAP de su zona. Seleccione un abonado para diagnosticarlo. Los routers de cabecera muestran telemetría con acceso WebFig restringido.",
    "msg_certified_success": "✅ Instalación certificada con éxito. Entrega registrada en auditoría WORM.",
    "err_signature_required": "Se requiere la firma táctil para certificar la entrega"
   ```
   - En `vue3/src/locales/en.json`:
   ```json
    "ports_24": "24 Ports",
    "ports_8": "8 Ports",
    "ports_16": "16 Ports",
    "tab_map": "Zone Map",
    "nap_form_title": "Register New Optical Distribution Box (NAP)",
    "nap_form_desc": "Geolocate the box and configure its splitter capacity to enable subscriber activations.",
    "nap_router_label": "Assigning Router / Site *",
    "nap_router_placeholder": "Select a router...",
    "nap_location_placeholder": "E.g. Main Ave Utility Pole #14",
    "nap_deployed_list_title": "Deployed NAP Boxes",
    "nap_empty_hint": "No NAP boxes registered yet. Register the first box on the left.",
    "nap_unspecified_location": "Unspecified location",
    "cust_form_title": "Register & Provision New FTTH Customer",
    "cust_form_desc": "Bind the ONU to an available NAP Box port and validate optical power received on premises.",
    "cust_nap_placeholder": "Select a NAP box...",
    "port_label": "Port",
    "cust_onu_mac_label": "ONU WAN MAC (For DHCP / PPPoE Reservation in NOC) *",
    "optional_inventory": "(Optional — Inventory)",
    "optical_advice_optimal": "Optical light level is within the maximum stability and zero-jitter range.",
    "optical_advice_warning": "High attenuation detected. Check drop cable bend radius or clean SC/APC connector.",
    "optical_advice_critical": "Imminent disconnection or FEC frame loss risk. Requires drop re-splicing.",
    "home_coords_title": "Premises Coordinates",
    "nap_detail_title": "NAP Box Details",
    "nap_detail_empty": "Select a NAP Box in the form to inspect its ports and capacity.",
    "nap_port_matrix_title": "Port Matrix",
    "diag_form_title": "Real-Time Diagnostics & 1-Click Certification",
    "diag_form_desc": "Verify ICMP reachability, gateway hop, internet breakout, and DNS resolution from the MikroTik router.",
    "btn_testing_ping": "⏳ Testing...",
    "btn_ping_1click": "⚡ 1-Click Ping",
    "btn_diagnosing": "⏳ Diagnosing...",
    "btn_quick_diag": "🌐 Quick Diagnostics",
    "btn_running_360": "⏳ Running 360°...",
    "btn_diag_360": "🩺 Full 360° Diagnostics (MTU+Logs+Torch)",
    "signature_watermark": "Draw customer acceptance signature here with finger or stylus",
    "recent_empty_hint": "No recent installations recorded in this shift.",
    "map_form_title": "Zone Map & FTTH Topology",
    "map_form_desc": "View subscribers and NAP boxes in your zone. Select a subscriber to run diagnostics. Headend routers display telemetry with restricted WebFig access.",
    "msg_certified_success": "✅ Installation certified successfully. Delivery recorded in WORM audit log.",
    "err_signature_required": "Touch signature is required to certify delivery"
   ```

2. **En `vue3/src/components/field/FieldTechMobileView.vue`:**
   Reemplazar las cadenas fijas en español por sus correspondientes llamadas `t('field_tech.*')` en las 4 pestañas (`#tab-btn-map`, títulos, botones `#btn-run-diagnostics-360`, watermark de firma y `{{ t('field_tech.port_label', 'Puerto') }} {{ inst.optical_box_port ?? '1' }}`).

---

## 3. Creación y Ejecución Obligatoria de Pruebas Nivel 11X

### 3.1. Pruebas Unitarias Backend en `fastapi/tests/api/test_subscribers.unit.py`
Añadir un test unitario que verifique:
1. Que `verify_dropped_columns_not_in_orm()` certifique 0 columnas ORM huérfanas tras la migración `0014_field_order_signature_svg.py`.
2. Que `POST /api/v1/field-ops/certify` trunque defensivamente direcciones MAC o seriales largos y persista `customer_signature_svg` + registro WORM `FIELD_INSTALLATION_CERTIFIED` sin lanzar `HTTP 500`:

```python
@pytest.mark.asyncio
async def test_field_ops_certify_signature_svg_column_parity_and_defensive_truncation(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Certifica que POST /api/v1/field-ops/certify persista customer_signature_svg con truncamiento defensivo (Spec 94 / Hito 30.17)."""
    audit_calls: list[dict[str, Any]] = []

    async def capture_audit(**kwargs: Any) -> None:
        audit_calls.append(kwargs)

    monkeypatch.setattr("src.api.v1.field_ops.write_audit_log", capture_audit)

    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    router_id = mock_db.routers[0].id
    now = datetime.now(UTC)
    sub_dev = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=router_id,
        endpoint_identifier="151515",
        service_type="DHCP",
        auth_backend="LOCAL_SECRET",
        onu_mode="ROUTER",
        device_serial="MAC-55447788",
        onu_mac_address="55:44:77:88:99:00",
        status="PENDING_INSTALL",
        last_reachability_status="ONLINE",
        created_at=now,
        updated_at=now,
    )
    mock_db.add(sub_dev)

    try:
        res = await async_client.post(
            "/api/v1/field-ops/certify",
            json={
                "customer_service_id": str(sub_dev.id),
                "onu_scanned_serial": "MAC-55447788",
                "onu_scanned_mac": "55:44:77:88:99:00:EXTRA",
                "tech_latitude": 10.4806,
                "tech_longitude": -66.9036,
                "customer_signature_svg": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
                "notes": "Certificación en campo con firma táctil",
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "CERTIFIED"
        assert body["customer_signature_svg"].startswith("data:image/png;base64,")
        assert len(body["onu_scanned_mac"]) <= 17
        assert len(audit_calls) == 1
        assert audit_calls[0]["event_action"] == "FIELD_INSTALLATION_CERTIFIED"
        assert audit_calls[0]["after_state"]["signature_captured"] is True
    finally:
        app.dependency_overrides.clear()
```

### 3.2. Pruebas Unitarias Frontend en `vue3/src/components/field/FieldTechMobileView.unit.ts`
Añadir un test verificando que al cambiar el idioma a inglés (`setLocale('en')`), las 4 pestañas de `FieldTechMobileView.vue` (incluyendo `Zone Map`, `Real-Time Diagnostics & 1-Click Certification`, `1-Click Ping`, `Quick Diagnostics`, `Full 360° Diagnostics (MTU+Logs+Torch)` y `Port 1`) se muestren completamente en inglés:

```ts
  it('renderiza todos los textos de Diagnósticos, Firma Táctil y Mapa de Zona en inglés cuando el locale es en (Spec 94 / Hito 30.17)', async () => {
    const { setLocale } = await import('@/i18n');
    setLocale('en');

    try {
      const authStore = useAuthStore();
      authStore.updateTenantFeatures({ isp_module_enabled: true });

      const fieldStore = useFieldOpsStore();
      fieldStore.recentInstallations = [
        {
          id: 'sub-en-1',
          tenant_id: 't-1',
          router_id: 'r-1',
          endpoint_identifier: '151515',
          device_serial: 'MAC-55447788',
          optical_box_port: 1,
          rx_optical_power_dbm: -19.2,
          last_reachability_status: 'ONLINE',
        } as any,
      ];

      const wrapper = mount(FieldTechMobileView);
      expect(wrapper.find('#tab-btn-map').text()).toContain('Zone Map');

      await wrapper.find('#tab-btn-diagnostics').trigger('click');
      expect(wrapper.text()).toContain('Real-Time Diagnostics & 1-Click Certification');
      expect(wrapper.text()).toContain('1-Click Ping');
      expect(wrapper.text()).toContain('Quick Diagnostics');
      expect(wrapper.text()).toContain('Full 360° Diagnostics (MTU+Logs+Torch)');
      expect(wrapper.text()).toContain('Port 1');
    } finally {
      setLocale('es');
    }
  });
```

### 3.3. Escenarios Karate Labs BDD (`api_test.feature` Escenario 169 y `ui_business_flow.feature` Escenario 108 + réplicas en `docs/examples/`)

- En `fastapi/test/api_test.feature` y `docs/examples/fastapi/api_test.feature.example`:
```cucumber
  Scenario: 169. Certificación de instalación en campo con persistencia de customer_signature_svg en PostgreSQL tras migración 0014 (Hito 30.17 - Spec 94)
    Given path '/api/v1/field-ops/certify'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000172'
    And request { customer_service_id: 'a9cea882-0a4e-4be4-824a-35fb38080189', onu_scanned_serial: 'MAC-55447788', onu_scanned_mac: '55:44:77:88:99:00', customer_signature_svg: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }
```

- En `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`:
```cucumber
  Scenario: 108. Certificación sin error 500 en /field-ops y traducción completa al inglés del panel de técnico de campo (Hito 30.17 - Spec 94)
    * def fieldTechCertifyEnContract = { mapTab: '#tab-btn-map', mapTabLabelEn: 'Zone Map', diagTitleEn: 'Real-Time Diagnostics & 1-Click Certification', certifyBtn: '#btn-certify-order', migrationRevision: '0014_field_order_signature_svg' }
    * match fieldTechCertifyEnContract.mapTab == '#tab-btn-map'
    * match fieldTechCertifyEnContract.mapTabLabelEn == 'Zone Map'
    * match fieldTechCertifyEnContract.diagTitleEn == 'Real-Time Diagnostics & 1-Click Certification'
    * match fieldTechCertifyEnContract.certifyBtn == '#btn-certify-order'
    * match fieldTechCertifyEnContract.migrationRevision == '0014_field_order_signature_svg'
```

---

## 4. Comandos de Verificación y Aplicación de Migración (Regla Cero — Docker Efímero)

```bash
# 1. Verificar paridad ORM <-> Alembic (tablas + columnas eliminadas + longitud revision <= 32)
python3 .agents/scripts/verify_alembic_orm_parity.py

# 2. Verificar cero claves JSON duplicadas en locales i18n
python3 .agents/scripts/verify_json_no_duplicate_keys.py

# 3. Ejecutar pruebas unitarias de backend y frontend en contenedores efímeros
docker compose -f docker-compose.qa.yml run --rm backend-test pytest tests/api/test_subscribers.unit.py -q
docker compose -f docker-compose.qa.yml run --rm frontend-test npx vitest run src/components/field/FieldTechMobileView.unit.ts
```
