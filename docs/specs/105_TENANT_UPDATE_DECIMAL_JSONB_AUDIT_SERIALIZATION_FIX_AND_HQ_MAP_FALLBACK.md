# Especificación 105: Remediación de Error `HTTP 500` (`Object of type Decimal is not JSON serializable`) al Actualizar Coordenadas GPS de Sede Principal (`PATCH /api/v1/tenants/{id}`) y Re-Centrado Reactivo de Mapas sobre la Sede Principal

**Estado:** Pendiente de Ejecución (`[ ]` Hito 30.28)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Backend (`fastapi/src/core/audit.py`, `fastapi/src/api/v1/tenants.py`) + Frontend (`vue3/src/views/admin/TenantsManagementView.vue`, `vue3/src/components/network/UnifiedNetworkMap.vue`, `vue3/src/components/inventory/OsmRouterMap.vue`) + Pruebas Unitarias y Karate Labs BDD

---

## 1. Diagnóstico Forense de Causa Raíz

Al editar una empresa en **Administración de Empresas (`/admin/tenants`)** y guardar las nuevas coordenadas de la Sede Principal (`hq_latitude`, `hq_longitude`), el navegador recibe **`HTTP 500: Internal Server Error`**.

La traza exacta en `rosgrid_api_local` revela la causa raíz:

```text
File "/usr/local/lib/python3.15/json/encoder.py", line 182, in default
  raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')
sqlalchemy.exc.StatementError: (builtins.TypeError) Object of type Decimal is not JSON serializable
[SQL: INSERT INTO audit_logs (..., before_state, after_state, ...) VALUES (..., $15::JSONB, $16::JSONB, ...)]
```

### ¿Por qué ocurre este fallo?
1. En PostgreSQL, las columnas `Tenant.hq_latitude` y `Tenant.hq_longitude` están definidas como `NUMERIC(9, 6)`. Cuando SQLAlchemy carga la entidad `Tenant` desde PostgreSQL, hidrata ambos atributos como objetos `decimal.Decimal` (por ejemplo, `Decimal('10.480600')` y `Decimal('-66.903600')`).
2. En `PATCH /api/v1/tenants/{tenant_id}` (`update_tenant` en `fastapi/src/api/v1/tenants.py`), la función `_apply_tenant_updates` construye `before_state` leyendo directamente los atributos del modelo ORM:
   ```python
   before_state = {field: getattr(tenant, field, None) for field in update_data}
   ```
   Como resultado, `before_state["hq_latitude"]` y `before_state["hq_longitude"]` contienen objetos `Decimal` (y `before_state["status"]` contiene `TenantStatusEnum` cuando se modifica el estado).
3. Al invocar `write_audit_log(...)` (`fastapi/src/core/audit.py`), `compute_audit_record_hash` no falla porque usa `json.dumps(..., default=str)`, pero `sanitize_sensitive_data(before_state)` devuelve los objetos `Decimal` intactos y los asigna a la columna `AuditLog.before_state` (`JSONB`).
4. Cuando se ejecuta `await db.commit()`, el compilador `JSONB` de SQLAlchemy invoca `json.dumps(value)` (sin `default`), lanzando `TypeError: Object of type Decimal is not JSON serializable`.

### ¿Por qué las pruebas unitarias previas no lo detectaron?
En `test_tenants_and_users.unit.py`, el objeto `Tenant()` en memoria tenía `hq_latitude = 10.4806` (`float`) en lugar de `Decimal("10.480600")` (como lo hidrata PostgreSQL `NUMERIC(9, 6)`), y el `MockDbSession` no ejecutaba `json.dumps()` estricto sobre `AuditLog.before_state` / `AuditLog.after_state`.

Adicionalmente, cuando una empresa tiene `0 routers`, `0 cajas NAP` y `0 abonados` (como la empresa `sistemas` en producción local), `fitMapToActiveNodes()` en `UnifiedNetworkMap.vue` retornaba temprano cuando `coords.length === 0` sin aplicar `mapInstance.setView(authStore.tenantHqCoordinates, props.zoomLevel)`, ni escuchaba cambios reactivos en `authStore.tenantHqCoordinates`.

---

## 2. Cambios Exactos Requeridos en Backend (`fastapi/`)

### 2.1. Normalización Universal de Tipos JSONB en `sanitize_sensitive_data` (`fastapi/src/core/audit.py`)

En `fastapi/src/core/audit.py`:
1. Importar `date`, `datetime`, `Decimal` y `Enum` en la cabecera del archivo:
```python
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
```
2. Actualizar `sanitize_sensitive_data(data: Any) -> Any` para normalizar recursivamente `Decimal` $\rightarrow$ `float`, `Enum` $\rightarrow$ `data.value` y `UUID`/`datetime`/`date` $\rightarrow$ `str`, garantizando que cualquier diccionario almacenado en `AuditLog.before_state` o `AuditLog.after_state` sea 100% serializable por `json.dumps` nativo en PostgreSQL `JSONB`:

```python
def sanitize_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    if isinstance(data, (list, tuple, set)):
        return [sanitize_sensitive_data(item) for item in data]
    if isinstance(data, str):
        return sanitize_log_string(data)
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, (uuid.UUID, datetime, date)):
        return str(data)
    return data
```

### 2.2. Normalización de `before_state` en `_apply_tenant_updates` (`fastapi/src/api/v1/tenants.py`)

En `fastapi/src/api/v1/tenants.py`:
1. Importar `Decimal` desde `decimal` y `Enum` desde `enum`.
2. Actualizar `_apply_tenant_updates` para que `before_state` convierta instancias `Decimal` a `float` y `Enum` a su `.value`, manteniendo simetría exacta con `after_state`:

```python
def _normalize_tenant_audit_value(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, Enum):
        return val.value
    return val


async def _apply_tenant_updates(
    db: AsyncSession, tenant: Tenant, update_data: dict[str, Any]
) -> dict[str, Any]:
    """Aplica las modificaciones de metadatos/cuotas sobre el Tenant y retorna before_state (CC = 3)."""
    before_state = {
        field: _normalize_tenant_audit_value(getattr(tenant, field, None))
        for field in update_data
    }
    if update_data.get("slug"):
        update_data["slug"] = await _validate_unique_tenant_slug(db, tenant, str(update_data["slug"]))
    for field, value in update_data.items():
        setattr(tenant, field, value)
    return before_state
```

---

## 3. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 3.1. Sincronización Inmediata de `hq_latitude` / `hq_longitude` en `TenantsManagementView.vue`

En `handleUpdateTenant()` dentro de `vue3/src/views/admin/TenantsManagementView.vue`:
- Al completar `PATCH /api/v1/tenants/${editingTenant.value.id}`, si el tenant editado corresponde al tenant activo en sesión (`String(authStore.user?.tenant_id) === String(editingTenant.value.id)` o `authStore.tenantSlug === editingTenant.value.slug` o `authStore.tenantSlug === payload.slug`), actualizar inmediatamente `authStore.updateTenantFeatures({ hq_latitude: payload.hq_latitude, hq_longitude: payload.hq_longitude })` además de llamar a `await authStore.fetchTenantFeatures()`:

```ts
      if (
        String(authStore.user?.tenant_id) === String(editingTenant.value.id) ||
        authStore.tenantSlug === editingTenant.value.slug ||
        authStore.tenantSlug === payload.slug
      ) {
        authStore.updateTenantFeatures({
          hq_latitude: payload.hq_latitude,
          hq_longitude: payload.hq_longitude,
        });
        await authStore.fetchTenantFeatures();
      }
```

### 3.2. Fallback a `authStore.tenantHqCoordinates` cuando `coords.length === 0` y Watcher Reactivo en `UnifiedNetworkMap.vue` y `OsmRouterMap.vue`

1. En `vue3/src/components/network/UnifiedNetworkMap.vue`:
   - En `fitMapToActiveNodes(force = false)`:
     Cuando `coords.length === 0` (empresa sin routers, cajas ni abonados geolocalizados), centrar el mapa en `authStore.tenantHqCoordinates`:
     ```ts
     function fitMapToActiveNodes(force = false): void {
       if (!mapInstance || isHeadlessTest.value) return;
       if (hasInitialAutoCentered.value && !force) return;

       const coords = collectAllValidCoordinates();
       if (coords.length === 0) {
         try {
           mapInstance.setView(authStore.tenantHqCoordinates, props.zoomLevel);
         } catch {
           // Ignorar en entornos JSDOM sin layout
         }
         return;
       }

       try {
         hasInitialAutoCentered.value = true;
         if (coords.length === 1) {
           mapInstance.setView(coords[0], Math.max(props.zoomLevel, 14));
         } else {
           const bounds = L.latLngBounds(coords);
           mapInstance.fitBounds(bounds, { padding: [48, 48], maxZoom: 15 });
         }
       } catch {
         // Ignorar en entornos JSDOM sin layout
       }
     }
     ```
   - Añadir un `watch` sobre `() => authStore.tenantHqCoordinates` para que, si la empresa no tiene nodos geolocalizados o aún no se ha auto-encuadrado sobre nodos, el mapa mueva su cámara inmediatamente al actualizarse las coordenadas de la Sede Principal:
     ```ts
     watch(
       () => authStore.tenantHqCoordinates,
       (newHq) => {
         if (!mapInstance || isHeadlessTest.value) return;
         if (collectAllValidCoordinates().length === 0) {
           try {
             mapInstance.setView(newHq, props.zoomLevel);
           } catch {
             // Ignorar en entornos JSDOM
           }
         }
       },
     );
     ```

2. En `vue3/src/components/inventory/OsmRouterMap.vue`:
   - En `renderMarkers()`, cuando `groups.length === 0`, centrar el mapa en `authStore.tenantHqCoordinates`:
     ```ts
     if (groups.length === 0) {
       try {
         mapInstance.setView(authStore.tenantHqCoordinates, 6);
       } catch {
         // Ignorar en entorno JSDOM
       }
     }
     ```
   - Añadir también el `watch(() => authStore.tenantHqCoordinates, ...)` cuando `props.routers.length === 0`.

---

## 4. Blindaje Estructural del Arnés de Pruebas (`conftest.py` y `MockDbSession`) y Pruebas Nivel 11X

### 4.1. Por Qué Escapó de las Pruebas Anteriores y Cómo Blindar el Arnés Globalmente

El fallo no fue detectado en el Hito 30.27 por tres puntos ciegos del arnés de pruebas en memoria:
1. **`MockDbSession.commit()` (`test_tenants_and_users.unit.py`) solo hacía `self.committed = True`:** A diferencia del compilador `JSONB` real de SQLAlchemy + PostgreSQL (que ejecuta `json.dumps(value)` estricto sin `default=str` durante el `flush`/`commit`), `MockDbSession` guardaba el objeto `AuditLog` en una lista de Python (`self.added`) sin serializar jamás `before_state` ni `after_state` a JSON.
2. **`make_asserting_audit_mock` (`fastapi/tests/conftest.py`) no validaba serialización JSONB:** Validaba `event_category`, `event_action`, `actor_username` y la ausencia de UUIDs crudos, pero no ejecutaba `json.dumps(before_state)` ni `json.dumps(after_state)`.
3. **Hidratación `float` vs `Decimal` en fixtures ORM:** En PostgreSQL, las columnas `NUMERIC(9, 6)` se hidratan como `decimal.Decimal`, mientras que en el test unitario se asignaron como `float`.

#### Cambios Obligatorios en `fastapi/tests/conftest.py`:
En `make_asserting_audit_mock` (`fastapi/tests/conftest.py`), añadir validación estricta `json.dumps()` (sin `default=str`) sobre `before_state` y `after_state` tras pasarlos por `sanitize_sensitive_data`:

```python
        import json
        from src.core.audit import sanitize_sensitive_data

        before_st = kwargs.get("before_state")
        after_st = kwargs.get("after_state")
        if before_st is not None:
            json.dumps(sanitize_sensitive_data(before_st))
        if after_st is not None:
            json.dumps(sanitize_sensitive_data(after_st))
```

#### Cambios Obligatorios en `MockDbSession` (`fastapi/tests/api/test_tenants_and_users.unit.py`):
En `MockDbSession.add()` y `MockDbSession.commit()`, emular el compilador `JSONB` de SQLAlchemy ejecutando `json.dumps()` sobre `before_state` y `after_state` de cualquier `AuditLog` agregado a la sesión:

```python
    async def commit(self) -> None:
        import json

        for item in self.added:
            for jsonb_attr in ("before_state", "after_state"):
                val = getattr(item, jsonb_attr, None)
                if val is not None:
                    json.dumps(val)
        self.committed = True
```

### 4.2. Prueba Unitaria y de Serialización JSONB Estricta en Backend (`fastapi/tests/api/test_tenants_and_users.unit.py`)

En `fastapi/tests/api/test_tenants_and_users.unit.py`, actualizar/añadir la prueba `test_tenant_hq_coordinates_create_update_and_decimal_audit_jsonb_serialization`:
1. Instanciar el `Tenant` existente con valores `Decimal("10.480600")` y `Decimal("-66.903600")` (idéntico a como PostgreSQL `NUMERIC(9, 6)` hidrata el modelo ORM).
2. Ejecutar `PATCH /api/v1/tenants/{t1.id}` con `{"name": "Tecno Carabobo", "hq_latitude": 10.232345, "hq_longitude": -67.879812}`.
3. Verificar que responde `HTTP 200`, que el registro `AuditLog` creado en `db.added` tiene `before_state["hq_latitude"] == 10.4806` (`isinstance(..., float)`), y que `json.dumps(audit_entry.before_state)` y `json.dumps(audit_entry.after_state)` se ejecutan en `MockDbSession.commit()` **sin lanzar `TypeError: Object of type Decimal is not JSON serializable`**.

### 4.2. Prueba Unitaria Frontend (`vue3/src/views/admin/tenantsManagementView.unit.ts` y `vue3/src/components/network/UnifiedNetworkMap.unit.ts`)

1. En `tenantsManagementView.unit.ts`, verificar que al guardar la edición de la empresa activa (`handleUpdateTenant`), se invoca `PATCH /api/v1/tenants/{id}` con `hq_latitude` y `hq_longitude` numéricos y se actualiza `authStore.tenantHqCoordinates` inmediatamente.
2. En `UnifiedNetworkMap.unit.ts`, verificar que cuando `routers = []`, `opticalBoxes = []` y `subscribers = []`, `fitMapToActiveNodes(true)` centra el mapa en `authStore.tenantHqCoordinates`.

### 4.3. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + `docs/examples/`)

1. En `fastapi/test/api_test.feature` (y `docs/examples/fastapi/api_test.feature.example`), añadir el **`Scenario: 177`**:
```gherkin
  # ============================================================================
  # SPEC 105: SERIALIZACIÓN JSONB DE DECIMAL EN AUDITORÍA WORM AL EDITAR TENANT
  # ============================================================================
  Scenario: 177. Actualizacion PATCH de coordenadas GPS de Sede Principal sin error Decimal en AuditLog JSONB (Spec 105)
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000000'
    And request { name: 'Tecno Sede Carabobo', hq_latitude: 10.232345, hq_longitude: -67.879812 }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }
```

2. En `vue3/test/ui_business_flow.feature` (y `docs/examples/vue3/ui_business_flow.feature.example`), añadir el **`Scenario: 119`**:
```gherkin
  # ============================================================================
  # SPEC 105: GUARDADO DE COORDENADAS HQ Y RE-CENTRADO REACTIVO EN EMPRESAS SIN NODOS
  # ============================================================================
  Scenario: 119. Guardado PATCH de coordenadas GPS de Sede Principal y fallback reactivo en mapas sin nodos (Spec 105)
    * def patchTenantHq = { id: 'tenant-sistemas', hq_latitude: 10.232345, hq_longitude: -67.879812, before_hq_lat_type: 'float' }
    * assert patchTenantHq.hq_latitude == 10.232345
    * assert patchTenantHq.hq_longitude == -67.879812
    * assert patchTenantHq.before_hq_lat_type == 'float'
```

---

## 5. Criterios de Aceptación y Compuerta de Cierre (Level-11X Gate)

1. `sanitize_sensitive_data` en `fastapi/src/core/audit.py` convierte `Decimal` $\rightarrow$ `float`, `Enum` $\rightarrow$ `value` y `UUID`/`datetime`/`date` $\rightarrow$ `str` recursivamente.
2. `PATCH /api/v1/tenants/{id}` actualiza las coordenadas de la Sede Principal sobre registros PostgreSQL `NUMERIC(9, 6)` devolviendo `HTTP 200 OK` y persistiendo `AuditLog` en `JSONB` sin `TypeError`.
3. Todas las suites unitarias y Karate Labs BDD pasan al 100% en contenedores efímeros (`Regla Cero`) y `./.agents/scripts/certify_task_completion.sh` aprueba las 9/9 compuertas.
