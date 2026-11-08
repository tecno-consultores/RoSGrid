# Especificación 99: Filtrado de Paquetes Activos en Catálogo Capa 2 (`/system/package`) y Degradación Elegante para Paquetes Opcionales No Instalados (`container`, `zerotier`)

**Estado:** Pendiente de Implementación (`[ ]` Hito 30.22)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Backend (`fastapi/src/api/v1/webfig_layer2.py`) + Frontend (`vue3/src/components/webfig/RouterSidebarMenu.vue`, `vue3/src/views/DynamicLayer2ResourceView.vue`) + Suite de Pruebas 11X (`fastapi/tests/api/test_webfig_layer2_universal.unit.py`, `vue3/src/views/webfigViews.unit.ts`, Karate Labs BDD)

---

## 1. Diagnóstico Causa Raíz (Root-Cause Analysis)

Al inspeccionar el router real `r1` (`a1c66d5d-01cf-41c6-b217-7d2117202a39`, CHR RouterOS `v7.21.5 (long-term)`), se identificó por qué aparecían en el menú lateral (`CAPA 2 — MOTOR UNIVERSAL`) las entradas **OCI Containers** (`/webfig/layer2/container`) y **Container Mounts** (`/webfig/layer2/container/mounts`), arrojando al abrirlas el error:
> `No se pudo conectar al router MikroTik en container: RouterOS REST API Error [400]: no such command or directory (container)`

1. **Comportamiento Real de `/rest/system/package` en RouterOS v7.13+ / v7.21.5:**
   - En RouterOS v7 moderno, `GET /rest/system/package` devuelve no solo el paquete base activo (`routeros`), sino también el listado de paquetes opcionales disponibles en el canal pero **no instalados / deshabilitados**, con los atributos `'available': 'true'`, `'disabled': 'true'` y `'version': ''` (vacío):
     ```json
     [
       {".id": "*1", "available": "false", "disabled": "false", "name": "routeros", "version": "7.21.5"},
       {".id": "*3", "available": "true", "disabled": "true", "name": "container", "version": ""}
     ]
     ```
   - En `fastapi/src/api/v1/webfig_layer2.py` (línea 653), `get_catalog` extraía todos los nombres sin filtrar por estado activo:
     ```python
     installed_pkgs = [p.get("name", "") for p in raw_pkgs if isinstance(p, dict)] if isinstance(raw_pkgs, list) else []
     ```
   - Como consecuencia, `get_catalog` asumía erróneamente que el paquete `container` estaba instalado en `r1` e inyectaba el grupo `Containers` (`OCI Containers` y `Container Mounts`) en el árbol de navegación lateral.

2. **Falta de Degradación Elegante ante `no such command or directory` (Invariante Trimodal):**
   - Si un operador accede por URL directa a `/webfig/layer2/container` o `/webfig/layer2/zerotier` en un router que no tiene instalado ese paquete opcional (`.npk`), RouterOS devuelve `HTTP 400: no such command or directory (container)`.
   - `get_resource` en `webfig_layer2.py` dejaba propagar un `HTTP 502 Bad Gateway` (`No se pudo conectar al router MikroTik...`), simulando falsamente una falla de conectividad de red en lugar de indicar que el paquete opcional de RouterOS no está instalado en el equipo (`schema_source="package_not_installed"`).

---

## 2. Cambios Exactos Requeridos en Backend (`fastapi/`)

### 2.1. Filtrar Paquetes Realmente Instalados y Degradar `no such command or directory` en `fastapi/src/api/v1/webfig_layer2.py`

1. Justo antes de `_build_catalog_groups(packages: list[str])` (alrededor de la línea 573), añadir la función auxiliar `_is_ros_package_active`:

```python
def _is_ros_package_active(pkg: dict[str, Any]) -> bool:
    """Verifica que un paquete devuelto por /rest/system/package esté realmente instalado y habilitado en RouterOS v7."""
    name = str(pkg.get("name", "")).strip()
    if not name:
        return False
    if str(pkg.get("disabled", "false")).lower() in ("true", "yes", "1"):
        return False
    if str(pkg.get("available", "false")).lower() in ("true", "yes", "1"):
        return False
    if "version" in pkg and not str(pkg.get("version", "")).strip():
        return False
    return True
```

2. En `get_catalog` (línea 653 de `fastapi/src/api/v1/webfig_layer2.py`), reemplazar la construcción de `installed_pkgs` por:

```python
    installed_pkgs = (
        [str(p.get("name", "")).strip() for p in raw_pkgs if isinstance(p, dict) and _is_ros_package_active(p)]
        if isinstance(raw_pkgs, list)
        else []
    )
```

3. En `get_resource` (líneas 720–749 de `fastapi/src/api/v1/webfig_layer2.py`), capturar el caso en que RouterOS devuelve `no such command or directory` para degradar limpiamente sin arrojar `HTTP 502`:

```python
    endpoint_query = f"{clean_path}?.proplist={','.join(normalized_props)}" if normalized_props else clean_path
    try:
        raw_data = await cached_mikrotik_get(
            redis=redis,
            tenant_id=tenant_id,
            router_id=router_id,
            endpoint=endpoint_query,
            client=client,
            refresh=refresh,
            ttl_seconds=5,
        )
    except HTTPException as exc:
        detail_lower = str(exc.detail).lower()
        if "no such command or directory" in detail_lower or "bad command name" in detail_lower:
            fallback_cols = _parse_console_inspect_syntax(clean_path, [])
            return DynamicLayer2CollectionResponse(
                ros_path=clean_path,
                is_singleton=False,
                supports_safe_mode=False,
                columns_schema=fallback_cols,
                items=[],
                form_data=None,
                available_rpc_actions=[],
                schema_source="package_not_installed",
                is_server_filtered=False,
            )
        raise
```

---

## 3. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 3.1. Catálogo Base Sin Paquetes Opcionales No Confirmados en `vue3/src/components/webfig/RouterSidebarMenu.vue`

En `vue3/src/components/webfig/RouterSidebarMenu.vue` (líneas 33–50), actualizar el estado predeterminado de `layer2Catalog` para que contenga únicamente módulos estándar integrados en el paquete base `routeros` (de modo que `OCI Containers` y `ZeroTier` solo aparezcan si `/api/v1/routers/{id}/webfig/layer2/catalog` confirma que el paquete `.npk` está activo):

```ts
  const layer2Catalog = ref<Layer2CatalogItem[]>([
    { ros_path: 'mpls/interface', title: 'MPLS Interfaces', category: 'MPLS & VPLS', is_singleton: false },
    { ros_path: 'mpls/ldp', title: 'LDP Instance', category: 'MPLS & VPLS', is_singleton: false },
    { ros_path: 'interface/vpls', title: 'VPLS Tunnels', category: 'MPLS & VPLS', is_singleton: false },
    { ros_path: 'certificate', title: 'Certificates', category: 'Certificates & Security', is_singleton: false },
    { ros_path: 'snmp', title: 'SNMP Settings', category: 'SNMP & Management', is_singleton: true },
    {
      ros_path: 'snmp/community',
      title: 'SNMP Communities',
      category: 'SNMP & Management',
      is_singleton: false,
    },
  ]);
```

### 3.2. Aviso Informativo de Paquete No Instalado en `vue3/src/views/DynamicLayer2ResourceView.vue`

1. En `<script setup lang="ts">` de `vue3/src/views/DynamicLayer2ResourceView.vue`, añadir el computed `isPackageNotInstalled`:

```ts
  const isPackageNotInstalled = computed(
    () => resourceData.value.schema_source === 'package_not_installed',
  );
```

2. En `<template>` de `vue3/src/views/DynamicLayer2ResourceView.vue` (justo debajo de `<div v-if="errorMessage" class="alert-error">`), renderizar un banner informativo cuando `isPackageNotInstalled` sea `true` y deshabilitar el botón `+ Nuevo Registro`:

```vue
    <div
      v-if="isPackageNotInstalled"
      id="layer2-package-not-installed-banner"
      class="alert-warning"
      role="status"
    >
      📦 El paquete opcional de RouterOS v7 requerido para <code>/{{ rosPath }}</code> no está instalado o habilitado en este router (verifique <code>/system/package</code>).
    </div>
```

Y en el botón `+ Nuevo Registro` de la cabecera:
```vue
        <button
          v-if="!resourceData.is_singleton"
          type="button"
          class="btn-primary"
          :disabled="isPackageNotInstalled"
          @click="openCreateModal"
        >
          + Nuevo Registro
        </button>
```

---

## 4. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

### 4.1. Prueba Unitaria Backend (`fastapi/tests/api/test_webfig_layer2_universal.unit.py`)

Importar `_is_ros_package_active` en `fastapi/tests/api/test_webfig_layer2_universal.unit.py` y añadir al final del archivo:

```python
@pytest.mark.asyncio
async def test_layer2_catalog_filters_disabled_packages_and_graceful_missing_package() -> None:
    """Spec 99: Filtra paquetes deshabilitados/no instalados en /system/package y degrada 'no such command or directory'."""
    assert _is_ros_package_active({"name": "routeros", "disabled": "false", "available": "false", "version": "7.21.5"}) is True
    assert _is_ros_package_active({"name": "container", "disabled": "true", "available": "true", "version": ""}) is False
    assert _is_ros_package_active({"name": "zerotier", "disabled": "false", "available": "true", "version": ""}) is False
    assert _is_ros_package_active({"name": ""}) is False

    router_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    claims = {
        "tid": str(tenant_id),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "preferred_username": "admin_noc",
    }
    db = AsyncMock()
    router_obj = SimpleNamespace(id=router_id, display_name="r1", ros_version="7.21.5")
    client = AsyncMock()

    raw_ros721_pkgs = [
        {".id": "*1", "name": "routeros", "disabled": "false", "available": "false", "version": "7.21.5"},
        {".id": "*3", "name": "container", "disabled": "true", "available": "true", "version": ""},
    ]

    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(router_obj, client))),
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=AsyncMock()),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", AsyncMock(return_value=raw_ros721_pkgs)),
    ):
        cat = await get_catalog(router_id, refresh=False, claims=claims, db=db)
        assert cat.installed_packages == ["routeros"]
        group_names = [g.group for g in cat.menu_tree]
        assert "Containers" not in group_names

    # Degradación elegante cuando el paquete container no está instalado (400 no such command or directory)
    missing_pkg_exc = HTTPException(
        status_code=502,
        detail="No se pudo conectar al router MikroTik en container: RouterOS REST API Error [400]: no such command or directory (container)",
    )
    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(router_obj, client))),
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=AsyncMock()),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", AsyncMock(side_effect=missing_pkg_exc)),
    ):
        res_missing = await get_resource(router_id, "container", refresh=False, proplist=None, claims=claims, db=db)
        assert res_missing.schema_source == "package_not_installed"
        assert res_missing.items == []
```

### 4.2. Prueba Unitaria Frontend (`vue3/src/views/webfigViews.unit.ts`)

Añadir en `vue3/src/views/webfigViews.unit.ts` (dentro del `describe` principal):

```ts
  it('DynamicLayer2ResourceView — muestra banner informativo cuando schema_source es package_not_installed (Spec 99)', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: {
        ros_path: 'container',
        title: 'Container',
        is_singleton: false,
        columns_schema: [{ key: 'name', label: 'Nombre', type: 'string' }],
        items: [],
        schema_source: 'package_not_installed',
      },
      headers: new Headers(),
    });

    const wrapper = mount(DynamicLayer2ResourceView);
    await flushPromises();

    const banner = wrapper.find('#layer2-package-not-installed-banner');
    expect(banner.exists()).toBe(true);
    expect(banner.text()).toContain('/system/package');
  });
```

### 4.3. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + `docs/examples/`)

1. En `fastapi/test/api_test.feature` y `docs/examples/fastapi/test/api_test.feature`:
```gherkin
  Scenario: 173. Catalogo WebFig Capa 2 filtra paquetes opcionales deshabilitados y degrada paquetes no instalados (Spec 99)
    Given path '/api/v1/routers/' + routerId + '/webfig/layer2/catalog'
    And header Authorization = 'Bearer ' + authToken
    When method GET
    Then status 200
    And match response.menu_tree == '#[]'
```

2. En `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`:
```gherkin
  Scenario: 113. Degradacion elegante de paquete opcional RouterOS no instalado en Capa 2 (Spec 99)
    Given path '/routers/' + routerId + '/webfig/layer2/container'
    When method GET
    Then status 200
```

---

## 5. Criterios de Aceptación y Certificación 11X

- [ ] `GET /api/v1/routers/{id}/webfig/layer2/catalog` excluye paquetes con `disabled="true"`, `available="true"` o `version=""`, ocultando `OCI Containers` y `Container Mounts` del menú lateral en routers donde `container.npk` no está instalado.
- [ ] `GET /api/v1/routers/{id}/webfig/layer2/resource/container` devuelve `HTTP 200` con `schema_source="package_not_installed"` e `items=[]` (en lugar de `HTTP 502`) cuando RouterOS responde `no such command or directory`.
- [ ] `DynamicLayer2ResourceView.vue` muestra `#layer2-package-not-installed-banner` y deshabilita `+ Nuevo Registro` cuando `schema_source === 'package_not_installed'`.
- [ ] Cobertura unitaria Pytest `>= 95%`, Vitest `100%` pass y `.agents/scripts/certify_task_completion.sh` en verde.
