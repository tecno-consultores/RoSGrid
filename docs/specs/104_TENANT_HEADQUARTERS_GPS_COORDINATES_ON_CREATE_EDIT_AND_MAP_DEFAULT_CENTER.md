# Especificación 104: Coordenadas GPS de Sede Principal (`hq_latitude`, `hq_longitude`) al Crear / Editar Empresa (`Tenant`) y Centrado Cartográfico Predeterminado por Empresa

**Estado:** Pendiente de Implementación (`[ ]` Hito 30.27)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Base de Datos y Backend (`fastapi/migrations/versions/0015_tenant_hq_coordinates.py`, `fastapi/src/models/core.py`, `fastapi/src/schemas/tenants.py`, `fastapi/src/api/v1/tenants.py`) + Frontend (`vue3/src/types/index.ts`, `vue3/src/stores/useAuthStore.ts`, `vue3/src/views/admin/TenantsManagementView.vue`, `vue3/src/components/network/UnifiedNetworkMap.vue`, `vue3/src/components/inventory/OsmRouterMap.vue`) + Suite de Pruebas 11X

---

## 1. Propósito y Justificación Arquitectónica

En una plataforma multi-tenant donde cada ISP o corporación opera en una ciudad, estado o país distinto (ej. Carabobo, Caracas, Bogotá, Madrid, Buenos Aires), el centro predeterminado de los mapas no debe ser una constante global fija en Caracas (`[10.4806, -66.9036]`), sino **la ubicación de la Sede Principal (`hq_latitude`, `hq_longitude`) configurada en la propia Empresa (`Tenant`)**.

De esta manera:
1. Al crear o editar una empresa en **Empresas (`TenantsManagementView.vue`)**, el administrador puede definir la **Latitud y Longitud de la Sede Principal** (o capturarlas con 1 clic mediante el botón **`📍 Capturar mi GPS actual`**).
2. Incluso cuando la empresa está recién creada y aún tiene **0 routers y 0 clientes**, todos los mapas (`UnifiedNetworkMap.vue`, `OsmRouterMap.vue`, `OsmOnuMap.vue`, `SubscribersMapView.vue`) y formularios (`FieldTechMobileView.vue`) abren centrados inmediatamente en la **Sede Principal de la Empresa**.
3. Cuando la empresa ya cuenta con equipos geolocalizados, el mapa arranca en la Sede Principal del Tenant y encuadra suavemente la flota activa (`Spec 102`).

---

## 2. Cambios Exactos Requeridos en Base de Datos y Backend (`fastapi/`)

### 2.1. Modelo ORM `Tenant` (`fastapi/src/models/core.py`) y Migración Alembic `0015_tenant_hq_coordinates.py`

1. En `fastapi/src/models/core.py`, añadir en la clase `Tenant`:
```python
    hq_latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True, default=10.480600)
    hq_longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True, default=-66.903600)
```
*(Importando `Numeric` desde `sqlalchemy`).*

2. Crear la migración idempotente `fastapi/migrations/versions/0015_tenant_hq_coordinates.py` (`revision = "0015_tenant_hq_coordinates"`, `down_revision = "0014_field_order_signature_svg"`):
```python
def upgrade() -> None:
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS hq_latitude NUMERIC(9, 6) DEFAULT 10.480600;"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS hq_longitude NUMERIC(9, 6) DEFAULT -66.903600;"
    )


def downgrade() -> None:
    op.drop_column("tenants", "hq_longitude")
    op.drop_column("tenants", "hq_latitude")
```

### 2.2. Esquemas Pydantic (`fastapi/src/schemas/tenants.py`) y Endpoints (`fastapi/src/api/v1/tenants.py`)

1. En `fastapi/src/schemas/tenants.py`:
   - En `TENANT_FEATURE_DEFAULTS`, añadir:
     ```python
     "hq_latitude": 10.4806,
     "hq_longitude": -66.9036,
     ```
   - En `extract_tenant_features(tenant: Any)`, convertir `Decimal` a `float` si `key in ("hq_latitude", "hq_longitude")` y `value is not None`.
   - En `CreateTenantRequest`, `UpdateTenantFeaturesRequest`, `UpdateTenantRequest`, `TenantFeaturesResponse` y `TenantResponse`, añadir:
     ```python
     hq_latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
     hq_longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
     ```
2. En `create_tenant` y `update_tenant` (`fastapi/src/api/v1/tenants.py`), persistir `hq_latitude` y `hq_longitude` en la entidad `Tenant` (usando `10.4806` y `-66.9036` como respaldo si no se envían al crear).

---

## 3. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 3.1. Getter `tenantHqCoordinates` en `vue3/src/stores/useAuthStore.ts`

En `useAuthStore.ts` (y en `TenantFeatureFlags` / `TenantItem` dentro de `vue3/src/types/index.ts`), añadir `hq_latitude?: number | null` y `hq_longitude?: number | null`, y exponer el computed `tenantHqCoordinates`:

```ts
  const tenantHqCoordinates = computed<[number, number]>(() => {
    const lat = Number(tenantFeatures.value?.hq_latitude);
    const lng = Number(tenantFeatures.value?.hq_longitude);
    if (!Number.isNaN(lat) && !Number.isNaN(lng) && !(lat === 0 && lng === 0)) {
      return [lat, lng];
    }
    return [10.4806, -66.9036];
  });
```

### 3.2. Campos de Coordenadas de Sede Principal y Botón `📍 Capturar GPS` en `vue3/src/views/admin/TenantsManagementView.vue`

1. En `newTenant` y `editingTenant` de `TenantsManagementView.vue`, añadir `hq_latitude: 10.4806` y `hq_longitude: -66.9036`.
2. Añadir la función `captureBrowserGps(target: 'create' | 'edit')` que usa `navigator.geolocation.getCurrentPosition` para rellenar `hq_latitude` y `hq_longitude`.
3. En los modales de **Crear Empresa** y **Editar Empresa** de `TenantsManagementView.vue`, añadir los inputs `#input-tenant-hq-lat`, `#input-tenant-hq-lng` y el botón `#btn-tenant-capture-gps` (`📍 Capturar GPS Sede`), enviando `hq_latitude` y `hq_longitude` en el `POST /api/v1/tenants` y `PATCH /api/v1/tenants/{id}` (y refrescando `authStore.fetchTenantFeatures` si el tenant editado es el activo).

### 3.3. Uso de `authStore.tenantHqCoordinates` como Centro Inicial en Todos los Mapas

En `UnifiedNetworkMap.vue`, `OsmRouterMap.vue`, `OsmOnuMap.vue` y `SubscribersMapView.vue`, utilizar `authStore.tenantHqCoordinates` como coordenada inicial de la cámara cuando no existan equipos cargados o antes de que responda la API.

---

## 4. Pruebas Obligatorias Nivel 11X (Unitarias + Paridad ORM/Alembic + Karate Labs BDD)

1. **Paridad ORM / Alembic (`.agents/scripts/verify_alembic_orm_parity.py`):** Debe certificar 100% de paridad entre `Tenant.hq_latitude` / `Tenant.hq_longitude` y `0015_tenant_hq_coordinates.py`.
2. **Prueba Unitaria Backend (`fastapi/tests/api/test_tenants_and_users.unit.py` o `test_operations_endpoints_full.unit.py`):** Verificar creación y actualización de `hq_latitude` y `hq_longitude` en `Tenant` y su exposición en `/api/v1/tenants/{id}/features`.
3. **Prueba Unitaria Frontend (`vue3/src/views/admin/tenantsManagementView.unit.ts`):** Verificar que los modales de Crear y Editar Empresa renderizan `#input-tenant-hq-lat` y `#input-tenant-hq-lng` y envían las coordenadas de la sede principal en el payload.
4. **Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` Escenario 176 y `vue3/test/ui_business_flow.feature` Escenario 118 + `docs/examples/`).**
