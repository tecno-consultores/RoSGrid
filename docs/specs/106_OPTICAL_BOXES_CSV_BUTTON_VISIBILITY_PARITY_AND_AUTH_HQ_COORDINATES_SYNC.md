# Especificación 106: Visibilidad Directa del Botón `📦 Importar Cajas NAP CSV` para Administradores en `/subscribers-map`, Capa de Cajas NAP Dinámica en `UnifiedNetworkMap.vue` y Sincronización de `hq_latitude`/`hq_longitude` en Login (`auth.py`)

**Estado:** Pendiente de Ejecución (`[ ]` Hito 30.29)  
**Target de Ejecución:** Gemini 3.8 Flash (High)  
**Ámbito:** Frontend (`vue3/src/views/SubscribersMapView.vue`, `vue3/src/components/network/UnifiedNetworkMap.vue`) + Backend (`fastapi/src/api/v1/auth.py`) + Pruebas Unitarias y Karate Labs BDD

---

## 1. Diagnóstico Forense de Causa Raíz

1. **Por qué no se veía el botón `📦 Importar Cajas NAP CSV` (`#btn-import-optical-boxes-csv`) en `/subscribers-map`:**
   - En `vue3/src/views/SubscribersMapView.vue` (líneas 707–726):
     - El botón `#btn-import-subscribers-csv` (`📂 Importar Clientes CSV`) tiene `v-if="canManageBulkSubscribers"`.
     - En cambio, el botón `#btn-import-optical-boxes-csv` (`📦 Importar Cajas NAP CSV`) fue condicionado a `v-if="canManageBulkSubscribers && isIspMode"`.
   - En la base de datos local, la empresa `sistemas` (`tecno`) tiene `isp_module_enabled = false`, por lo que `isIspMode` evalúa a `false` y oculta el botón `📦 Importar Cajas NAP CSV` aunque el usuario sea `SUPERADMIN_GLOBAL` o `TENANT_ADMIN` y sí vea al lado el botón `📂 Importar Clientes CSV` (cuya plantilla CSV incluye `optical_box_name` y auto-crea cajas NAP).
2. **Ocultamiento de la capa `■ Cajas NAP` en `UnifiedNetworkMap.vue` cuando `isp_module_enabled` es `false` pero existen Cajas NAP cargadas:**
   - En `vue3/src/components/network/UnifiedNetworkMap.vue` (líneas 446, 574 y 868), el botón de capa `■ Cajas NAP` y el renderizado de `boxesLayer` dependían exclusivamente de `isIspMode`. Si un administrador importa Cajas NAP por CSV o desde clientes CSV en un tenant con `isp_module_enabled = false`, las cajas creadas en PostgreSQL no se dibujaban en el mapa.
3. **Omisión de `hq_latitude` y `hq_longitude` en `_extract_tenant_features` dentro de `fastapi/src/api/v1/auth.py`:**
   - En `fastapi/src/api/v1/auth.py` (líneas 390–424), la función local `_extract_tenant_features(tenant)` mantenía una lista propia de flags que no incluía `"hq_latitude"` ni `"hq_longitude"` (a diferencia de `extract_tenant_features(tenant)` en `fastapi/src/schemas/tenants.py`). Por ello, al iniciar sesión o cambiar de tenant (`/auth/switch-tenant`), `user.tenant_feature_flags` no traía las coordenadas de la Sede Principal hasta llamar manualmente a `/api/v1/tenants/{id}/features`.
4. **Doble ícono `🔄 🔄` en el botón «Sincronizar Dispositivos DHCP» de `SubscribersMapView.vue`:**
   - En `vue3/src/locales/es.json` y `en.json` (línea 154), la clave `subscribers_map.btn_sync_dhcp` ya incluye el emoji `🔄` (`"🔄 Sincronizar Dispositivos DHCP"` / `"🔄 Sync DHCP Devices"`), pero en `SubscribersMapView.vue` (líneas 701–703) además se renderizaba `<span v-else>🔄</span>` antes de `t('subscribers_map.btn_sync_dhcp')`, produciendo el texto duplicado `🔄 🔄 Sincronizar Dispositivos DHCP`.

---

## 2. Cambios Exactos Requeridos en Frontend (`vue3/`)

### 2.1. Eliminación del Doble Ícono `🔄 🔄` en Sincronizar DHCP y Paridad de Visibilidad RBAC en `#btn-import-optical-boxes-csv` (`vue3/src/views/SubscribersMapView.vue`)

En `vue3/src/views/SubscribersMapView.vue` (líneas 694–726):
1. En el botón de sincronizar DHCP, eliminar el `<span v-else>🔄</span>` redundante (o usar `t('subscribers_map.btn_sync_dhcp').replace(/^🔄\s*/, '')` junto al `<span>`) para que renderice un único ícono `🔄 Sincronizar Dispositivos DHCP`.
2. Cambiar `v-if="canManageBulkSubscribers && isIspMode"` por **`v-if="canManageBulkSubscribers"`** en `#btn-import-optical-boxes-csv`, de modo que siempre que el administrador (`SUPERADMIN_GLOBAL` o `TENANT_ADMIN`) vea `📂 Importar Clientes CSV`, vea inmediatamente a su lado `📦 Importar Cajas NAP CSV`:

```html
        <!-- Botón Modo Empresa / Común: Sincronizar leases DHCP reales desde MikroTik -->
        <button
          id="btn-sync-dhcp-clients"
          type="button"
          class="btn-sync-dhcp"
          :disabled="isSyncingDhcp"
          aria-label="Sincronizar Dispositivos DHCP"
          @click="handleSyncDhcpClients"
        >
          <span v-if="isSyncingDhcp">⏳ {{ t('subscribers_map.syncing_dhcp') }}</span>
          <span v-else>{{ t('subscribers_map.btn_sync_dhcp') }}</span>
        </button>
        <!-- Botón Carga Masiva CSV Clientes (Solo SUPERADMIN_GLOBAL y TENANT_ADMIN) -->
        <button
          v-if="canManageBulkSubscribers"
          id="btn-import-subscribers-csv"
          type="button"
          class="btn-sync-dhcp"
          aria-label="Importar Clientes CSV"
          @click="isCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_csv', '📂 Importar Clientes CSV') }}
        </button>
        <!-- Botón Carga Masiva CSV Cajas NAP (Hito 30.26 / Spec 103 & Spec 106) -->
        <button
          v-if="canManageBulkSubscribers"
          id="btn-import-optical-boxes-csv"
          type="button"
          class="btn-sync-dhcp"
          aria-label="Importar Cajas NAP CSV"
          @click="isBoxesCsvModalOpen = true"
        >
          {{ t('subscribers_map.btn_import_boxes_csv', '📦 Importar Cajas NAP CSV') }}
        </button>
```

### 2.2. Habilitación de la Capa de Cajas NAP (`canShowBoxesLayer`) en `vue3/src/components/network/UnifiedNetworkMap.vue`

En `vue3/src/components/network/UnifiedNetworkMap.vue`:
1. Definir el computed `canShowBoxesLayer`:
```ts
  const canShowBoxesLayer = computed(
    () =>
      isIspMode.value ||
      props.opticalBoxes.length > 0 ||
      props.mode === 'subscribers' ||
      props.mode === 'wallboard',
  );
```
2. Reemplazar `isIspMode.value && showBoxes.value` por `canShowBoxesLayer.value && showBoxes.value` en `collectAllValidCoordinates()` (línea 446) y en `renderAllLayers()` (línea 574).
3. En el template de `UnifiedNetworkMap.vue` (línea 868), mostrar el botón de capa `■ Cajas NAP` con `v-if="canShowBoxesLayer"` en lugar de `v-if="isIspMode"`.

---

## 3. Cambios Exactos Requeridos en Backend (`fastapi/`)

### 3.1. Unificación de `_extract_tenant_features` en `fastapi/src/api/v1/auth.py` con `extract_tenant_features` de `fastapi/src/schemas/tenants.py`

En `fastapi/src/api/v1/auth.py` (líneas 390–424):
- Añadir `"hq_latitude": 10.4806` y `"hq_longitude": -66.9036` en `_extract_tenant_features(tenant: Tenant)` convirtiendo `Decimal` a `float` cuando `val is not None`:

```python
def _extract_tenant_features(tenant: Tenant) -> dict[str, Any]:
    features_dict: dict[str, Any] = {
        "isp_module_enabled": True,
        "bgp_looking_glass_enabled": False,
        "sfp_ddm_telemetry_enabled": True,
        "ipfix_analytics_enabled": False,
        "enforce_maker_checker": True,
        "auto_safemode_enforced": True,
        "ai_mcp_integration_enabled": True,
        "nightly_backups_enabled": True,
        "outbound_webhooks_enabled": True,
        "config_drift_monitoring_enabled": False,
        "cis_audit_enabled": True,
        "sdwan_orchestrator_enabled": False,
        "capsman_wifi_enabled": False,
        "sla_tracker_enabled": False,
        "l2_topology_enabled": True,
        "syslog_collector_enabled": True,
        "cve_scanner_enabled": True,
        "prometheus_fleet_exporter_enabled": True,
        "rogue_dhcp_enabled": True,
        "onboarding_completed": False,
        "mass_outage_threshold": 10,
        "default_locale": "es",
        "hq_latitude": 10.4806,
        "hq_longitude": -66.9036,
    }
    for key in list(features_dict.keys()):
        val = getattr(tenant, key, None)
        if val is not None:
            if key in ("hq_latitude", "hq_longitude"):
                val = float(val)
            features_dict[key] = val

    custom_features = getattr(tenant, "features", None)
    if isinstance(custom_features, dict):
        features_dict.update(custom_features)

    return features_dict
```

---

## 4. Pruebas Obligatorias Nivel 11X (Unitarias + Karate Labs BDD)

1. **Prueba Unitaria Frontend (`vue3/src/views/subscribersMapView.unit.ts`):**
   - Verificar que `#btn-import-optical-boxes-csv` (`📦 Importar Cajas NAP CSV`) se renderiza para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` incluso cuando `isp_module_enabled: false` en `authStore`, y permanece oculto para roles operativos como `NOC_MONITOR` o `FIELD_TECH`.
2. **Prueba Unitaria Backend (`fastapi/tests/api/test_tenants_and_users.unit.py` o `test_switch_tenant.unit.py`):**
   - Verificar que `_extract_tenant_features(tenant)` en `fastapi/src/api/v1/auth.py` incluye `hq_latitude` y `hq_longitude` como `float` incluso cuando el `Tenant` tiene valores `Decimal("10.231001")` y `Decimal("-67.880387")`.
3. **Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` Escenario 178 y `vue3/test/ui_business_flow.feature` Escenario 120 + `docs/examples/`):**
   - En `fastapi/test/api_test.feature` (+ `docs/examples/fastapi/api_test.feature.example`), añadir el **`Scenario: 178`** validando el contrato de `_extract_tenant_features` con `hq_latitude` y `hq_longitude` en `/api/v1/auth/me`.
   - En `vue3/test/ui_business_flow.feature` (+ `docs/examples/vue3/ui_business_flow.feature.example`), añadir el **`Scenario: 120`** validando la visibilidad paritaria de `#btn-import-subscribers-csv` y `#btn-import-optical-boxes-csv` para `SUPERADMIN_GLOBAL` / `TENANT_ADMIN` independientemente de `isp_module_enabled`.

---

## 5. Criterios de Aceptación y Compuerta de Cierre (Level-11X Gate)

1. En `/subscribers-map`, los botones `📂 Importar Clientes CSV` (`#btn-import-subscribers-csv`) y `📦 Importar Cajas NAP CSV` (`#btn-import-optical-boxes-csv`) son ambos visibles para `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` sin depender de `isp_module_enabled`.
2. En `UnifiedNetworkMap.vue`, las Cajas NAP se muestran y su botón de capa está disponible en `/subscribers-map`, `/wallboard` o cuando `opticalBoxes.length > 0`.
3. `_extract_tenant_features` en `auth.py` entrega `hq_latitude` y `hq_longitude` como `float`.
4. Todas las suites unitarias y Karate Labs BDD pasan al 100% en contenedores efímeros (`Regla Cero`) y `./.agents/scripts/certify_task_completion.sh` aprueba las 9/9 compuertas.
