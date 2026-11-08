# Especificación 103: Carga Masiva CSV de Cajas NAP (`OpticalBox` Upsert) y Auto-Creación Inteligente de Cajas NAP Inexistentes al Importar Clientes CSV

**Estado:** Pendiente de Implementación (`[ ]` Hito 30.26)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Backend (`fastapi/src/schemas/ipam.py`, `fastapi/src/api/v1/optical_boxes.py`, `fastapi/src/api/v1/subscribers.py`) + Frontend (`vue3/src/locales/es.json`, `vue3/src/locales/en.json`, `vue3/src/views/SubscribersMapView.vue`) + Suite de Pruebas 11X (`fastapi/tests/api/test_subscribers.unit.py`, `vue3/src/views/subscribersMapView.unit.ts`, Karate Labs BDD)

---

## 1. Propósito y Respuesta Arquitectónica: ¿Qué pasa si se sube un CSV de Clientes con Cajas NAP que aún no existen?

Cuando un ISP migra su planta externa a **RoSGrid**, pueden ocurrir dos escenarios reales:
1. **Escenario A (Importación primero de Clientes con nombres de Cajas NAP que aún no existen en PostgreSQL):**
   - Si el archivo CSV de clientes incluye `optical_box_name = "NAP-NORTE-05"` y esa caja aún no existe en la tabla `optical_boxes`, **no debe fallar ni dejar al cliente huérfano (`optical_box_id = None`)**:
   - Durante el **Dry-Run** (`POST /api/v1/subscriber-devices/import-csv/dry-run`), la fila es **válida (`is_valid = True`)** y devuelve el indicador `will_auto_create_box = True`.
   - Durante el **Commit** (`POST /api/v1/subscriber-devices/import-csv/commit`), el backend **auto-crea automáticamente la `OpticalBox` faltante** en PostgreSQL (asociada al `router_id` de la fila, con `capacity_ports = 16`, `splitter_ratio = "1:16"`, y coordenadas iniciales heredadas del cliente o del router) y vincula `sub.optical_box_id = nueva_caja.id` (igual que la importación de Routers auto-crea roles personalizados).
2. **Escenario B (Carga Masiva CSV de Cajas NAP con Upsert Inteligente):**
   - En la barra superior de `Mapa de Clientes` (`SubscribersMapView.vue`), junto a `📂 Importar Clientes CSV`, se añade el botón **`📦 Importar Cajas NAP CSV`** (`#btn-import-optical-boxes-csv`, exclusivo para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN`).
   - Si el administrador sube el CSV de Cajas NAP *antes* del de clientes, se crean todas las cajas con sus coordenadas exactas de poste, capacidad y splitter.
   - Y si el administrador sube el CSV de Cajas NAP *después* de haber subido el CSV de clientes (donde las cajas se habían auto-creado), `POST /api/v1/optical-boxes/import-csv/commit` ejecuta un **Upsert por `box_code`**: actualiza las cajas existentes con sus coordenadas GPS exactas de poste, capacidad (`8/16/32`), splitter (`1:8`/`1:16`), potencia óptica (`input_power_dbm`) y dirección física sin arrojar error de duplicado.

---

## 2. Cambios Exactos Requeridos en Backend (`fastapi/`)

### 2.1. Esquemas Pydantic en `fastapi/src/schemas/ipam.py`

1. En `SubscriberCsvRowPreview` (`fastapi/src/schemas/ipam.py`), añadir el campo:
```python
    will_auto_create_box: bool = False
```

2. Añadir al final de `fastapi/src/schemas/ipam.py` los esquemas para Cajas NAP CSV:
```python
class OpticalBoxCsvRowPreview(BaseModel):
    row_number: int
    box_code: str
    router_name: str
    capacity_ports: int = 16
    splitter_ratio: str = "1:16"
    installation_type: str = "POLE"
    input_power_dbm: Optional[float] = None
    latitude: float
    longitude: float
    physical_location: Optional[str] = None
    is_update: bool = False
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class OpticalBoxCsvDryRunResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    can_proceed: bool
    rows: list[OpticalBoxCsvRowPreview] = Field(default_factory=list)


class OpticalBoxCsvCommitRequest(BaseModel):
    rows: list[OpticalBoxCsvRowPreview]


class OpticalBoxCsvCommitResponse(BaseModel):
    imported_count: int
    updated_count: int = 0
    box_ids: list[uuid.UUID] = Field(default_factory=list)
    message: str
```

### 2.2. Auto-Creación de Cajas NAP Faltantes en `fastapi/src/api/v1/subscribers.py`

1. En `_validate_subscriber_csv_row` (`fastapi/src/api/v1/subscribers.py`), recibir `boxes_by_code: dict[str, OpticalBox] | None = None` y calcular:
```python
    will_auto_create = bool(
        box_name and (boxes_by_code is None or box_name.strip().lower() not in boxes_by_code)
    )
```
pasando `will_auto_create_box=will_auto_create` al construir `SubscriberCsvRowPreview(...)`.
En `import_subscribers_csv_dry_run` y `import_subscribers_csv_commit`, pasar `boxes_by_code` a `_validate_subscriber_csv_row`.

2. En `import_subscribers_csv_commit` (`fastapi/src/api/v1/subscribers.py`), cuando `item.optical_box_name` no exista aún en `boxes_by_code`, auto-crear la instancia `OpticalBox` y registrarla en `boxes_by_code`:

```python
        matched_box = (
            boxes_by_code.get(item.optical_box_name.strip().lower()) if item.optical_box_name else None
        )
        if item.optical_box_name and not matched_box:
            box_lat = (
                Decimal(str(item.latitude))
                if item.latitude is not None
                else (matched_router.latitude or Decimal("10.480600"))
            )
            box_lng = (
                Decimal(str(item.longitude))
                if item.longitude is not None
                else (matched_router.longitude or Decimal("-66.903600"))
            )
            matched_box = OpticalBox(
                tenant_id=tenant_id,
                router_id=matched_router.id,
                box_code=item.optical_box_name.strip(),
                capacity_ports=max(16, item.box_port_number or 16),
                splitter_ratio="1:16",
                installation_type="POLE",
                latitude=box_lat,
                longitude=box_lng,
                status="ACTIVE",
                notes="Auto-creada automáticamente durante importación CSV de clientes",
            )
            db.add(matched_box)
            await db.flush()
            boxes_by_code[item.optical_box_name.strip().lower()] = matched_box
```

### 2.3. Endpoints `GET /template-csv`, `POST /import-csv/dry-run` y `POST /import-csv/commit` en `fastapi/src/api/v1/optical_boxes.py`

En `fastapi/src/api/v1/optical_boxes.py`, añadir los 3 endpoints bajo `optical_boxes_router` (`/api/v1/optical-boxes`), protegidos con `Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN))`:

- **`GET /api/v1/optical-boxes/template-csv`**:
  - Cabeceras RFC 4180 con UTF-8 BOM:
    `box_code,router_name,capacity_ports,splitter_ratio,installation_type,input_power_dbm,latitude,longitude,physical_location`
  - Filas de ejemplo:
    `NAP-NORTE-01,r1,16,1:16,POLE,-18.50,10.232347,-67.879893,"Poste P-14 Av. Principal"`
    `NAP-NORTE-02,r1,8,1:8,FACADE,-19.20,10.233100,-67.880500,"Fachada Edif. Centro"`
- **`POST /api/v1/optical-boxes/import-csv/dry-run`**:
  - Valida hasta 500 filas: `box_code` obligatorio (`<= 64` chars, sin duplicados dentro del mismo CSV), `router_name` existente en el tenant, `capacity_ports` entero entre `1` y `64`, `latitude` (`-90..90`) y `longitude` (`-180..180`) obligatorios. Si `box_code` ya existe en la BD del tenant, marca `is_update=True` (para indicar que actualizará la caja existente).
- **`POST /api/v1/optical-boxes/import-csv/commit`**:
  - Ejecuta **Upsert transaccional**: si `box_code` ya existe en `optical_boxes` del tenant, actualiza su `router_id`, `capacity_ports`, `splitter_ratio`, `installation_type`, `input_power_dbm`, `latitude`, `longitude` y `physical_location`; si no existe, crea un nuevo `OpticalBox`. Registra auditoría WORM `OPTICAL_BOXES_CSV_BULK_IMPORTED` y hace `await db.commit()`.

---

## 3. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 3.1. Botón `#btn-import-optical-boxes-csv` y Modal `#modal-import-optical-boxes-csv` en `vue3/src/views/SubscribersMapView.vue`

1. En `SubscribersMapView.vue`, dentro de `<div class="sync-actions">` (junto a `#btn-import-subscribers-csv`), añadir el botón `#btn-import-optical-boxes-csv` visible cuando `canManageBulkSubscribers && isIspMode`:

```vue
        <button
          v-if="canManageBulkSubscribers && isIspMode"
          id="btn-import-optical-boxes-csv"
          type="button"
          class="btn-sync-dhcp"
          @click="isBoxesCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_boxes_csv', '📦 Importar Cajas NAP CSV') }}
        </button>
```

2. En el modal `#modal-import-subscribers-csv` (clientes), cuando una fila del Dry-Run tenga `row.will_auto_create_box === true`, mostrar la insignia informativa `✨ Auto-creará Caja NAP ({{ row.optical_box_name }})`.
3. Añadir el modal `#modal-import-optical-boxes-csv` conectado a `/api/v1/optical-boxes/template-csv`, `/api/v1/optical-boxes/import-csv/dry-run` y `/api/v1/optical-boxes/import-csv/commit`, refrescando `fieldStore.fetchOpticalBoxes()` y `loadSubscriberDevices()` al confirmar.

---

## 4. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

### 4.1. Prueba Unitaria Backend (`fastapi/tests/api/test_subscribers.unit.py`)
- Verificar que al importar un CSV de clientes con un `optical_box_name` que no existe en `optical_boxes`, el Dry-Run marca `will_auto_create_box=True` y el Commit auto-crea el registro `OpticalBox` y asigna su `id` en `sub.optical_box_id`.
- Verificar que `GET /api/v1/optical-boxes/template-csv`, `POST /api/v1/optical-boxes/import-csv/dry-run` y `POST /api/v1/optical-boxes/import-csv/commit` crean nuevas Cajas NAP y actualizan (Upsert) cajas previamente auto-creadas.

### 4.2. Prueba Unitaria Frontend (`vue3/src/views/subscribersMapView.unit.ts`)
- Verificar que `#btn-import-optical-boxes-csv` solo es visible para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` y abre `#modal-import-optical-boxes-csv`.

### 4.3. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + `docs/examples/`)
- Escenario 175 en `api_test.feature`: `GET /api/v1/optical-boxes/template-csv` devuelve `HTTP 200` y contiene `box_code,router_name`.
- Escenario 117 en `ui_business_flow.feature`: Flujo de carga masiva CSV de Cajas NAP y auto-creación de cajas en Mapa de Clientes.
