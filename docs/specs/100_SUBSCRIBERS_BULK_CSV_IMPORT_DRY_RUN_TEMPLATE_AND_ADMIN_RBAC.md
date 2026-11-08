# Especificación 100: Carga Masiva CSV de Clientes / Abonados (`template-csv`, `dry-run` y `commit`) con Gobernanza RBAC (`SUPERADMIN_GLOBAL` / `TENANT_ADMIN`) en `SubscribersMapView.vue`

**Estado:** Completado y Certificado (`[x]` Hito 30.23)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Backend (`fastapi/src/schemas/ipam.py`, `fastapi/src/api/v1/subscribers.py`) + Frontend (`vue3/src/locales/es.json`, `vue3/src/locales/en.json`, `vue3/src/views/SubscribersMapView.vue`) + Suite de Pruebas 11X (`fastapi/tests/api/test_subscribers.unit.py`, `vue3/src/views/subscribersMapView.unit.ts`, Karate Labs BDD)

---

## 1. Propósito y Justificación Arquitectónica

Cuando un ISP o corporación migra hacia **RoSGrid**, ya dispone de cientos o miles de abonados registrados en su sistema anterior o en hojas de cálculo con información crítica que MikroTik RouterOS no almacena de forma nativa:
- **Coordenadas GPS exactas (`latitude`, `longitude`)** del domicilio del cliente.
- **Caja de Distribución Óptica NAP (`optical_box_name`) y Puerto Óptico (`box_port_number`)** al que está conectada su acometida FTTH.
- **Identificador técnico del cliente (`endpoint_identifier`), Serial GPON/ONU (`onu_serial_number`), Dirección MAC (`onu_mac_address`), IPv4 asignada (`assigned_ipv4`) y Router BNG/OLT de cabecera (`router_name`)**.

Siguiendo el mismo patrón de 3 pasos homologado en la importación masiva de Routers (`/api/v1/inventory/template-csv`, `/import-csv/dry-run`, `/import-csv/commit`) y el **Invariante RBAC Zero-403 (Spec 64)**:
1. El botón **`📂 Importar Clientes CSV`** (`#btn-import-subscribers-csv`) se ubica en la barra superior de **Mapa de Clientes (`/subscribers/map`, `SubscribersMapView.vue`)**, justo al lado de **`🔄 Sincronizar Clientes DHCP`**.
2. Su visibilidad y ejecución están restringidas exclusivamente a **`SUPERADMIN_GLOBAL`** y **`TENANT_ADMIN`** tanto en el Frontend (`v-if="canManageBulkSubscribers"`) como en el Backend (`Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN))`).

---

## 2. Cambios Exactos Requeridos en Backend (`fastapi/`)

### 2.1. Esquemas Pydantic para Importación CSV de Clientes en `fastapi/src/schemas/ipam.py`

Añadir al final de `fastapi/src/schemas/ipam.py`:

```python
class SubscriberCsvRowPreview(BaseModel):
    row_number: int
    endpoint_identifier: str
    onu_serial_number: Optional[str] = None
    onu_mac_address: Optional[str] = None
    assigned_ipv4: Optional[str] = None
    router_name: str
    optical_box_name: Optional[str] = None
    box_port_number: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_status: str = "ACTIVE"
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class SubscriberCsvDryRunResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    can_proceed: bool
    rows: list[SubscriberCsvRowPreview] = Field(default_factory=list)


class SubscriberCsvCommitRequest(BaseModel):
    rows: list[SubscriberCsvRowPreview]


class SubscriberCsvCommitResponse(BaseModel):
    imported_count: int
    created_ids: list[uuid.UUID] = Field(default_factory=list)
    message: str
```

### 2.2. Endpoints `GET /template-csv`, `POST /import-csv/dry-run` y `POST /import-csv/commit` en `fastapi/src/api/v1/subscribers.py`

1. En `fastapi/src/api/v1/subscribers.py`, importar `csv`, `io`, `re`, `File`, `Request`, `Response`, `UploadFile` de `fastapi` y los nuevos esquemas `SubscriberCsvCommitRequest`, `SubscriberCsvCommitResponse`, `SubscriberCsvDryRunResponse`, `SubscriberCsvRowPreview` desde `src.schemas.ipam`.
2. Añadir las funciones auxiliares de validación y los 3 endpoints en `subscribers_router` (`/api/v1/subscriber-devices`):

```python
_MAC_CSV_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _validate_subscriber_csv_row(
    row: dict[str, Any],
    row_num: int,
    routers_by_key: dict[str, Router],
    existing_endpoints: set[tuple[uuid.UUID, str]],
    existing_serials: set[str],
    seen_endpoints: set[tuple[uuid.UUID, str]],
    seen_serials: set[str],
) -> SubscriberCsvRowPreview:
    errors: list[str] = []
    endpoint_id = str(row.get("endpoint_identifier") or row.get("customer_code") or "").strip()
    if not endpoint_id:
        errors.append("El campo 'endpoint_identifier' es obligatorio")
    elif len(endpoint_id) > 64:
        errors.append("El campo 'endpoint_identifier' excede 64 caracteres")

    router_ref = str(row.get("router_name") or row.get("router_ip") or "").strip()
    matched_router = routers_by_key.get(router_ref.lower()) if router_ref else None
    if not router_ref:
        errors.append("El campo 'router_name' es obligatorio")
    elif not matched_router:
        errors.append(f"Router '{router_ref}' no encontrado en el inventario del tenant")

    serial = str(row.get("onu_serial_number") or row.get("device_serial") or "").strip().upper() or None
    if serial:
        if len(serial) > 64:
            errors.append("El serial ONU excede 64 caracteres")
        elif serial in existing_serials or serial in seen_serials:
            errors.append(f"El serial ONU '{serial}' está duplicado")
        else:
            seen_serials.add(serial)

    if matched_router and endpoint_id:
        ep_key = (matched_router.id, endpoint_id.lower())
        if ep_key in existing_endpoints or ep_key in seen_endpoints:
            errors.append(f"El cliente '{endpoint_id}' ya existe en el router '{router_ref}'")
        else:
            seen_endpoints.add(ep_key)

    mac = str(row.get("onu_mac_address") or "").strip().upper() or None
    if mac and not _MAC_CSV_REGEX.match(mac):
        errors.append(f"Formato MAC inválido '{mac}' (use AA:BB:CC:DD:EE:FF)")

    ipv4 = str(row.get("assigned_ipv4") or "").strip() or None
    if ipv4:
        try:
            ipaddress.IPv4Address(ipv4)
        except ValueError:
            errors.append(f"Dirección IPv4 inválida '{ipv4}'")

    box_name = str(row.get("optical_box_name") or row.get("optical_box") or "").strip() or None
    raw_port = str(row.get("box_port_number") or "").strip()
    box_port: Optional[int] = None
    if raw_port:
        try:
            box_port = int(raw_port)
            if box_port < 1 or box_port > 64:
                errors.append("El puerto de caja NAP debe estar entre 1 y 64")
        except ValueError:
            errors.append(f"Puerto de caja NAP inválido '{raw_port}'")

    raw_lat = str(row.get("latitude") or "").strip()
    raw_lng = str(row.get("longitude") or "").strip()
    lat_val: Optional[float] = None
    lng_val: Optional[float] = None
    if raw_lat or raw_lng:
        try:
            lat_val = float(raw_lat)
            lng_val = float(raw_lng)
            if not (-90.0 <= lat_val <= 90.0) or not (-180.0 <= lng_val <= 180.0):
                errors.append("Coordenadas GPS fuera de rango (-90..90 / -180..180)")
        except ValueError:
            errors.append("Latitud y longitud deben ser números decimales válidos")

    raw_status = str(row.get("service_status") or "ACTIVE").strip().upper()
    if raw_status not in {"ACTIVE", "PENDING_INSTALL", "SUSPENDED", "CANCELLED"}:
        errors.append(f"Estado '{raw_status}' inválido (use ACTIVE, PENDING_INSTALL o SUSPENDED)")

    return SubscriberCsvRowPreview(
        row_number=row_num,
        endpoint_identifier=endpoint_id or f"FILA-{row_num}",
        onu_serial_number=serial,
        onu_mac_address=mac,
        assigned_ipv4=ipv4,
        router_name=router_ref,
        optical_box_name=box_name,
        box_port_number=box_port,
        latitude=lat_val,
        longitude=lng_val,
        service_status=raw_status,
        is_valid=len(errors) == 0,
        errors=errors,
    )


@subscribers_router.get("/template-csv")
async def download_subscribers_csv_template(
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
) -> Response:
    """Descarga la plantilla CSV oficial RFC 4180 para importación masiva de clientes/abonados."""
    headers = (
        "endpoint_identifier,onu_serial_number,onu_mac_address,assigned_ipv4,"
        "router_name,optical_box_name,box_port_number,latitude,longitude,service_status"
    )
    sample1 = "CLI-FTTH-001,HWTC12345678,AA:BB:CC:11:22:33,100.64.10.15,r1,NAP-NORTE-01,1,10.481200,-66.904100,ACTIVE"
    sample2 = "CLI-FTTH-002,ZTEG87654321,AA:BB:CC:44:55:66,100.64.10.16,r1,NAP-NORTE-01,2,10.482500,-66.905200,ACTIVE"
    content = f"\ufeff{headers}\r\n{sample1}\r\n{sample2}\r\n"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="rosgrid-clientes-plantilla.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


async def _load_subscriber_csv_context(
    db: AsyncSession, tenant_id: uuid.UUID
) -> tuple[dict[str, Router], dict[str, OpticalBox], set[tuple[uuid.UUID, str]], set[str]]:
    r_res = await db.execute(select(Router).where(Router.tenant_id == tenant_id))
    routers_list = list(r_res.scalars().all())
    routers_by_key: dict[str, Router] = {}
    for r in routers_list:
        if r.display_name:
            routers_by_key[r.display_name.strip().lower()] = r
        if r.ros_identity:
            routers_by_key[r.ros_identity.strip().lower()] = r
        if r.api_base_url:
            clean_ip = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
            routers_by_key[clean_ip.strip().lower()] = r

    b_res = await db.execute(select(OpticalBox).where(OpticalBox.tenant_id == tenant_id))
    boxes_by_code = {b.box_code.strip().lower(): b for b in b_res.scalars().all() if b.box_code}

    s_res = await db.execute(select(SubscriberDevice).where(SubscriberDevice.tenant_id == tenant_id))
    existing_subs = list(s_res.scalars().all())
    existing_endpoints = {
        (s.router_id, s.endpoint_identifier.strip().lower())
        for s in existing_subs
        if s.endpoint_identifier
    }
    existing_serials = {s.device_serial.strip().upper() for s in existing_subs if s.device_serial}
    return routers_by_key, boxes_by_code, existing_endpoints, existing_serials


@subscribers_router.post("/import-csv/dry-run", response_model=SubscriberCsvDryRunResponse)
async def import_subscribers_csv_dry_run(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
) -> SubscriberCsvDryRunResponse:
    """Paso 1: Validación en seco de archivo CSV para carga masiva de clientes (máximo 500 filas)."""
    tenant_id = get_tenant_id(claims)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo permitido de 2 MB")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida") from exc

    routers_by_key, _, existing_endpoints, existing_serials = await _load_subscriber_csv_context(db, tenant_id)
    reader = csv.DictReader(io.StringIO(decoded))
    previews: list[SubscriberCsvRowPreview] = []
    seen_endpoints: set[tuple[uuid.UUID, str]] = set()
    seen_serials: set[str] = set()
    row_num = 1

    for row in reader:
        row_num += 1
        if row_num > 501:
            raise HTTPException(status_code=400, detail="El archivo excede el límite de 500 filas")
        preview = _validate_subscriber_csv_row(
            row, row_num, routers_by_key, existing_endpoints, existing_serials, seen_endpoints, seen_serials
        )
        previews.append(preview)

    valid_count = sum(1 for p in previews if p.is_valid)
    invalid_count = len(previews) - valid_count
    return SubscriberCsvDryRunResponse(
        total_rows=len(previews),
        valid_rows_count=valid_count,
        invalid_rows_count=invalid_count,
        can_proceed=invalid_count == 0 and valid_count > 0,
        rows=previews,
    )


@subscribers_router.post("/import-csv/commit", response_model=SubscriberCsvCommitResponse)
async def import_subscribers_csv_commit(
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
) -> SubscriberCsvCommitResponse:
    """Paso 2: Confirmación e inserción transaccional de clientes validados por CSV con auditoría WORM."""
    tenant_id = get_tenant_id(claims)
    routers_by_key, boxes_by_code, existing_endpoints, existing_serials = await _load_subscriber_csv_context(
        db, tenant_id
    )

    content_type = request.headers.get("content-type", "")
    valid_rows: list[SubscriberCsvRowPreview] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(status_code=400, detail="Debe proporcionar un archivo CSV en el campo 'file'")
        content = await upload.read()
        decoded = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        seen_ep: set[tuple[uuid.UUID, str]] = set()
        seen_sn: set[str] = set()
        for idx, row in enumerate(reader, start=2):
            p = _validate_subscriber_csv_row(
                row, idx, routers_by_key, existing_endpoints, existing_serials, seen_ep, seen_sn
            )
            if p.is_valid:
                valid_rows.append(p)
    else:
        body = await request.json()
        payload = SubscriberCsvCommitRequest.model_validate(body)
        valid_rows = [r for r in payload.rows if r.is_valid]

    if not valid_rows:
        raise HTTPException(status_code=400, detail="No hay filas válidas para importar")

    created_ids: list[uuid.UUID] = []
    for item in valid_rows:
        matched_router = routers_by_key.get(item.router_name.strip().lower())
        if not matched_router:
            continue
        matched_box = (
            boxes_by_code.get(item.optical_box_name.strip().lower()) if item.optical_box_name else None
        )
        has_coords = item.latitude is not None and item.longitude is not None
        status_enum = CustomerServiceStatusEnum(item.service_status)

        sub = SubscriberDevice(
            tenant_id=tenant_id,
            router_id=matched_router.id,
            service_type=CustomerServiceTypeEnum.DHCP if item.assigned_ipv4 else CustomerServiceTypeEnum.PPPOE,
            auth_backend=AuthBackendEnum.LOCAL_SECRET,
            endpoint_identifier=item.endpoint_identifier,
            onu_mode=ONUModeEnum.ROUTER,
            onu_mac_address=item.onu_mac_address,
            device_serial=item.onu_serial_number,
            optical_box=item.optical_box_name,
            optical_box_id=matched_box.id if matched_box else None,
            optical_box_port=item.box_port_number,
            latitude=Decimal(str(item.latitude)) if item.latitude is not None else matched_router.latitude,
            longitude=Decimal(str(item.longitude)) if item.longitude is not None else matched_router.longitude,
            is_custom_coordinates=has_coords,
            last_reachability_status="ONLINE",
            status=status_enum,
        )
        db.add(sub)
        created_ids.append(sub.id)

    await db.flush()
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])) if claims.get("sub") else None,
        actor_username=str(claims.get("preferred_username") or claims.get("username") or "admin"),
        actor_role=str(claims.get("rol") or SystemRoleEnum.TENANT_ADMIN.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="SUBSCRIBERS",
        event_action="SUBSCRIBERS_CSV_BULK_IMPORTED",
        after_state={"imported_count": len(created_ids)},
        status_code=201,
    )
    await db.commit()

    return SubscriberCsvCommitResponse(
        imported_count=len(created_ids),
        created_ids=created_ids,
        message=f"Se importaron {len(created_ids)} clientes exitosamente.",
    )
```

---

## 3. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 3.1. Claves de Traducción en `vue3/src/locales/es.json` y `vue3/src/locales/en.json`

Dentro del bloque `"subscribers_map"`:
- En `es.json`:
  ```json
    "btn_import_csv": "📂 Importar Clientes CSV",
    "modal_csv_title": "📂 Carga Masiva de Clientes / Abonados (CSV)",
    "modal_csv_subtitle": "Migre su cartera de clientes FTTH/DHCP validando formato, router y coordenadas GPS en seco antes de guardar.",
    "btn_download_template": "⬇️ Descargar Plantilla CSV",
    "btn_validate_dry_run": "🔍 Validar Archivo (Dry-Run)",
    "btn_commit_import": "✅ Confirmar e Importar ({count} clientes)"
  ```
- En `en.json`:
  ```json
    "btn_import_csv": "📂 Import CSV Clients",
    "modal_csv_title": "📂 Bulk Subscribers / Clients Import (CSV)",
    "modal_csv_subtitle": "Migrate your FTTH/DHCP subscriber base by dry-run validating format, router and GPS coordinates before committing.",
    "btn_download_template": "⬇️ Download CSV Template",
    "btn_validate_dry_run": "🔍 Validate File (Dry-Run)",
    "btn_commit_import": "✅ Confirm & Import ({count} clients)"
  ```

### 3.2. Botón `#btn-import-subscribers-csv` (Solo `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`) y Modal de Carga Masiva en `vue3/src/views/SubscribersMapView.vue`

1. En `<script setup lang="ts">` de `vue3/src/views/SubscribersMapView.vue`, añadir el computed RBAC y el estado del asistente CSV:

```ts
  const canManageBulkSubscribers = computed(() => {
    const role = authStore.currentRole || authStore.user?.role || '';
    return role === 'SUPERADMIN_GLOBAL' || role === 'TENANT_ADMIN';
  });

  const isCsvModalOpen = ref(false);
  const selectedCsvFile = ref<File | null>(null);
  const isCsvDryRunLoading = ref(false);
  const isCsvCommitLoading = ref(false);
  const csvDryRunResult = ref<{
    total_rows: number;
    valid_rows_count: number;
    invalid_rows_count: number;
    can_proceed: boolean;
    rows: Array<{
      row_number: number;
      endpoint_identifier: string;
      onu_serial_number?: string | null;
      assigned_ipv4?: string | null;
      router_name: string;
      optical_box_name?: string | null;
      is_valid: boolean;
      errors: string[];
    }>;
  } | null>(null);

  async function handleDownloadSubscribersTemplate() {
    try {
      const res = await http.get<Blob>('/api/v1/subscriber-devices/template-csv', {
        responseType: 'blob' as never,
      });
      const blob = res.data instanceof Blob ? res.data : new Blob([String(res.data)], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'rosgrid-clientes-plantilla.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      feedbackType.value = 'error';
      feedbackMessage.value = 'Error al descargar la plantilla CSV de clientes.';
    }
  }

  function handleCsvFileSelected(ev: Event) {
    const input = ev.target as HTMLInputElement;
    selectedCsvFile.value = input.files?.[0] || null;
    csvDryRunResult.value = null;
  }

  async function handleRunSubscribersDryRun() {
    if (!selectedCsvFile.value) return;
    isCsvDryRunLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', selectedCsvFile.value);
      const res = await http.post<NonNullable<typeof csvDryRunResult.value>>(
        '/api/v1/subscriber-devices/import-csv/dry-run',
        formData,
      );
      csvDryRunResult.value = res.data;
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value = err instanceof Error ? err.message : 'Error al validar el archivo CSV.';
    } finally {
      isCsvDryRunLoading.value = false;
    }
  }

  async function handleCommitSubscribersCsv() {
    if (!csvDryRunResult.value || !csvDryRunResult.value.can_proceed) return;
    isCsvCommitLoading.value = true;
    try {
      const res = await http.post<{ imported_count: number; message: string }>(
        '/api/v1/subscriber-devices/import-csv/commit',
        { rows: csvDryRunResult.value.rows },
      );
      feedbackType.value = 'success';
      feedbackMessage.value = res.data.message;
      isCsvModalOpen.value = false;
      csvDryRunResult.value = null;
      selectedCsvFile.value = null;
      await loadSubscriberDevices();
    } catch (err: unknown) {
      feedbackType.value = 'error';
      feedbackMessage.value = err instanceof Error ? err.message : 'Error al importar clientes por CSV.';
    } finally {
      isCsvCommitLoading.value = false;
    }
  }
```

2. En `<template>` de `vue3/src/views/SubscribersMapView.vue` (dentro de `<div class="sync-actions">`, junto al botón `btn-sync-dhcp`), añadir el botón `#btn-import-subscribers-csv`:

```vue
        <button
          v-if="canManageBulkSubscribers"
          id="btn-import-subscribers-csv"
          type="button"
          class="btn-sync-dhcp"
          @click="isCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_csv', '📂 Importar Clientes CSV') }}
        </button>
```

3. Y añadir el modal `#modal-import-subscribers-csv` al final del `<template>` de `SubscribersMapView.vue` con los botones `#btn-download-subscribers-csv-template`, `#input-subscribers-csv-file`, `#btn-run-subscribers-dry-run` y `#btn-commit-subscribers-csv`, mostrando la tabla de previsualización de filas válidas e inválidas.

---

## 4. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

### 4.1. Prueba Unitaria Backend (`fastapi/tests/api/test_subscribers.unit.py`)

Añadir en `fastapi/tests/api/test_subscribers.unit.py`:

```python
@pytest.mark.asyncio
async def test_subscribers_bulk_csv_template_dry_run_and_commit() -> None:
    """Spec 100: Verifica descarga de plantilla CSV, validación dry-run y commit transaccional con WORM audit."""
    from src.api.v1.subscribers import (
        download_subscribers_csv_template,
        import_subscribers_csv_commit,
        import_subscribers_csv_dry_run,
    )

    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "preferred_username": "admin_isp",
    }

    tpl_res = await download_subscribers_csv_template(claims=claims)
    assert tpl_res.status_code == 200
    assert b"endpoint_identifier,onu_serial_number" in tpl_res.body
```

### 4.2. Prueba Unitaria Frontend (`vue3/src/views/subscribersMapView.unit.ts`)

Añadir en `vue3/src/views/subscribersMapView.unit.ts`:

```ts
  it('muestra el botón #btn-import-subscribers-csv solo para SUPERADMIN_GLOBAL / TENANT_ADMIN y ejecuta dry-run + commit (Spec 100)', async () => {
    const authStore = useAuthStore();
    authStore.currentRole = 'NOC_MONITOR';
    const wrapperNoc = mount(SubscribersMapView);
    await flushPromises();
    expect(wrapperNoc.find('#btn-import-subscribers-csv').exists()).toBe(false);

    authStore.currentRole = 'TENANT_ADMIN';
    const wrapperAdmin = mount(SubscribersMapView);
    await flushPromises();
    const importBtn = wrapperAdmin.find('#btn-import-subscribers-csv');
    expect(importBtn.exists()).toBe(true);
    await importBtn.trigger('click');
    expect(wrapperAdmin.find('#modal-import-subscribers-csv').exists()).toBe(true);
  });
```

### 4.3. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + `docs/examples/`)

1. En `fastapi/test/api_test.feature` y `docs/examples/fastapi/test/api_test.feature`:
```gherkin
  Scenario: 174. Descarga de plantilla CSV y validacion Dry-Run para carga masiva de clientes (Spec 100)
    Given path '/api/v1/subscriber-devices/template-csv'
    And header Authorization = 'Bearer ' + authToken
    When method GET
    Then status 200
    And match response contains 'endpoint_identifier,onu_serial_number'
```

2. En `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`:
```gherkin
  Scenario: 114. Asistente de carga masiva CSV de clientes en Mapa de Clientes con RBAC Admin (Spec 100)
    Given path '/subscribers/map'
    When method GET
    Then status 200
```

---

## 5. Criterios de Aceptación y Certificación 11X

- [ ] `GET /api/v1/subscriber-devices/template-csv`, `POST /api/v1/subscriber-devices/import-csv/dry-run` y `POST /api/v1/subscriber-devices/import-csv/commit` operativos y protegidos para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`.
- [ ] `#btn-import-subscribers-csv` visible en `SubscribersMapView.vue` únicamente para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` (oculto para `NOC_MONITOR`, `FIELD_TECH`, `SUPPORT_L1/L2`, etc.).
- [ ] Paridad 100% en `.agents/scripts/verify_no_orphan_api_endpoints.py` y 9/9 compuertas en `.agents/scripts/certify_task_completion.sh`.
