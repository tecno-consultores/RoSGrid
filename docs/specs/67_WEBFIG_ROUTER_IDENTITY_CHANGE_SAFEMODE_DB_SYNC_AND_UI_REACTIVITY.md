# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 67: Sincronización Integral de Identidad del Router (`system/identity`), Reactividad Pinia en Tiempo Real y Coherencia en Inventario WebFig

- **Estado:** PENDIENTE DE EJECUCIÓN (Hito 28.12 — Diseñado para ejecución directa por Gemini 3.8 Flash High)
- **Fecha:** 2026-11-02
- **Ámbito:** Frontend (`vue3/src/views/RouterLiveDashboardView.vue`, `vue3/src/views/RouterWebFigLayout.vue`, `vue3/src/views/DynamicLayer2ResourceView.vue`, `vue3/src/views/RouterInventoryView.vue`), Backend (`fastapi/src/schemas/webfig_ops.py`, `fastapi/src/api/v1/webfig_system_tools.py`, `fastapi/src/api/v1/webfig_layer2.py`), Pruebas 11X y Escenarios Karate Labs BDD.
- **Referencias Cruzadas:** Especificaciones [05](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/specs/05_MIKROTIK_V7_REST_CLIENT_AND_SAFEMODE.md), [12](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/specs/12_FRONTEND_WEBFIG_TACTICAL_UI_ARCHITECTURE.md), [54](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/specs/54_WEBFIG_TOTAL_DYNAMIC_SCHEMA_INSPECT_RPC_QUERY_AND_BULK.md) y [60](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docs/specs/60_ORPHAN_API_ENDPOINTS_AUDIT_AND_FRONTEND_PARITY.md).

---

## 1. Diagnóstico Forense de las Causas Raíz

Al pulsar el botón **`🏷️ Cambiar Identity`** (`#btn-change-identity`) dentro de la consola WebFig (`/routers/:id/webfig`), ingresar un nuevo nombre (ej. cambiar `r1` a `r11` en el router `6215d2b1-2cb3-4730-9659-f844e3c4c23f`) y guardar, **el usuario observa que el cambio no surte efecto visual alguno en la consola WebFig ni en la tabla de Inventario**, ni siquiera después de pulsar **`🔄 Sincronizar Hardware (Discovery)`**.

La auditoría forense sobre el código fuente y la base de datos PostgreSQL local (`rosgrid_db_local`) identificó **5 causas raíz encadenadas**:

1. **Causa Raíz 1 — Ausencia total de actualización reactiva en Pinia (`useWebFigStore` y `useInventoryStore`) tras `handleChangeIdentity()` y `handleSyncDiscovery()` en [`RouterLiveDashboardView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterLiveDashboardView.vue#L267-L298):**
   - `openIdentityModal()` inicializaba `newIdentityName.value = ''` en blanco en lugar de precargar el identity vigente del router (`ros_identity` o `display_name`).
   - `handleChangeIdentity()` ejecutaba `await http.patch('/api/v1/routers/${routerId.value}/webfig/system/identity', { name: ... })` y cerraba el modal **sin actualizar `webFigStore.currentRouter` ni `inventoryStore.routers`**.
   - Del mismo modo, `handleSyncDiscovery()` ejecutaba `await http.post('/api/v1/inventory/routers/${routerId.value}/sync-discovery')` descartando el `RouterResponse` devuelto por el backend sin sincronizar `webFigStore` ni `inventoryStore`.

2. **Causa Raíz 2 — Trampa de prioridad reactiva en [`RouterWebFigLayout.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue#L28-L45):**
   - En `RouterWebFigLayout.vue`, la propiedad computada `currentRouter` que alimenta a [`RouterContextHeader.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/webfig/RouterContextHeader.vue#L60-L63) (`{{ router?.display_name }} ({{ router?.ros_identity }})`) estaba definida como:
     ```ts
     const currentRouter = computed<RouterItem | null>(() => {
       return (
         inventoryStore.routers.find((r) => r.id === routerId.value) ||
         webFigStore.currentRouter ||
         null
       );
     });
     ```
   - Como `inventoryStore.routers.find(...)` se evaluaba **antes** que `webFigStore.currentRouter`, y `loadRouterData()` solo actualizaba `webFigStore.setCurrentRouter(res.data)` sin llamar a `inventoryStore.updateRouter(res.data)`, la cabecera superior de WebFig y el título de la pestaña quedaban permanentemente congelados con los datos antiguos de `inventoryStore.routers`.

3. **Causa Raíz 3 — Divergencia entre `ros_identity` y `display_name` en la Tabla `routers` de PostgreSQL ([`webfig_system_tools.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/webfig_system_tools.py#L121-L135)) y Omisión de Refresco/Columna en [`RouterInventoryView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterInventoryView.vue#L100):**
   - En la tabla `routers` de PostgreSQL, existen dos columnas: `display_name` (nombre asignado al importar el equipo, ej. `"r1"`) y `ros_identity` (el `/system/identity` del MikroTik). Al ejecutar `PATCH /api/v1/routers/{id}/webfig/system/identity` con `{"name": "r11"}`, `update_identity` actualizaba únicamente `router_obj.ros_identity = "r11"`, dejando `router_obj.display_name = "r1"`.
   - **Por qué sí se veía en la pantalla de actualizar Sistema Operativo (`/bulk-ops` — [`BulkOperationsAndUpdatesView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/BulkOperationsAndUpdatesView.vue#L115-L151)) pero no en WebFig ni en Inventario (`/inventory`):**
     1. `BulkOperationsAndUpdatesView.vue` ejecuta incondicionalmente `await inventoryStore.fetchRouters()` en su `onMounted()` (línea 150) recargando desde PostgreSQL, y además en las líneas 116-118 concatena `${r.display_name} (${r.ros_identity})` (`r1 (r11)`).
     2. Por el contrario, `RouterInventoryView.vue` tenía `if (inventoryStore.routers.length === 0) { inventoryStore.fetchRouters(); }` en su `onMounted()` (línea 283, por lo que no recargaba la BD al volver desde WebFig) y su columna **`Identity`** (línea 100) renderizaba únicamente `display_name` (`"r1"`) ignorando `ros_identity` (`"r11"`).
   - Además, `update_identity` no invalidaba la caché corta de WebFig en KeyDB (`invalidate_webfig_cache`) ni registraba el evento en la bitácora WORM (`write_audit_log`).

4. **Causa Raíz 4 — Edición de `/system/identity` desde WebFig Capa 2 ([`webfig_layer2.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/webfig_layer2.py#L874-L1016) y [`DynamicLayer2ResourceView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/DynamicLayer2ResourceView.vue#L438-L468)) sin persistencia en PostgreSQL ni actualización de stores:**
   - Cuando el operador editaba el recurso singleton **Sistema → Identidad (`/system/identity`)** en Capa 2, `update_singleton_resource` enviaba `POST /rest/system/identity/set` al MikroTik pero **no actualizaba `router_obj.ros_identity` ni `router_obj.display_name` en PostgreSQL**, y `DynamicLayer2ResourceView.vue` tampoco actualizaba `webFigStore` ni `inventoryStore`.

5. **Causa Raíz 5 — Banner de estado sin estilos CSS `.banner--success` / `.banner--error` en [`RouterLiveDashboardView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterLiveDashboardView.vue#L387-L389):**
   - `RouterLiveDashboardView.vue` carecía de las clases `.banner`, `.banner--success` y `.banner--error` en su bloque `<style scoped>` y mostraba cualquier error de red usando `class="banner banner--success"`.

---

## 2. Instrucciones Exactas de Implementación (Flash-Ready `Target` / `Replacement`)

### 2.1. Backend: Esquema `SystemIdentityUpdateRequest` en [`fastapi/src/schemas/webfig_ops.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/webfig_ops.py#L142-L144)

Añadir el atributo `sync_display_name: bool = Field(default=True)` a `SystemIdentityUpdateRequest`:

**Target (`fastapi/src/schemas/webfig_ops.py` líneas 142-145):**
```python
class SystemIdentityUpdateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=128)
```

**Replacement:**
```python
class SystemIdentityUpdateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    sync_display_name: bool = Field(
        default=True,
        description="Sincroniza automáticamente display_name con el nuevo identity en el inventario de RoSGrid",
    )
```

---

### 2.2. Backend: Endpoint `PATCH /api/v1/routers/{router_id}/webfig/system/identity` en [`fastapi/src/api/v1/webfig_system_tools.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/webfig_system_tools.py)

1. Importar `invalidate_webfig_cache` desde `src.api.v1.webfig_common`.
2. En `update_identity`, ejecutar `POST /system/identity/set` con fallback a `PATCH /system/identity`, actualizar `router_obj.ros_identity = new_name` y (si `payload.sync_display_name` es `True`) `router_obj.display_name = new_name`, invalidar la caché de KeyDB para `system/identity`, registrar auditoría WORM (`SYSTEM_IDENTITY_UPDATED`) y retornar `res or {"name": new_name, "ros_identity": router_obj.ros_identity, "display_name": router_obj.display_name}`.

**Target 1 (`fastapi/src/api/v1/webfig_system_tools.py` líneas 14-20):**
```python
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
    intercept_maker_checker_if_needed,
)
```

**Replacement 1:**
```python
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
    intercept_maker_checker_if_needed,
    invalidate_webfig_cache,
)
```

**Target 2 (`fastapi/src/api/v1/webfig_system_tools.py` líneas 121-136):**
```python
@system_router.patch("/identity")
async def update_identity(
    router_id: uuid.UUID,
    payload: SystemIdentityUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Cambia el identity interno del MikroTik y sincroniza la DB de RoSGrid."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    new_name = payload.name.strip()
    async with client:
        res = await client.post("/system/identity/set", json_data={"name": new_name})
    router_obj.ros_identity = new_name
    await db.commit()
    return res or {"name": new_name}
```

**Replacement 2:**
```python
@system_router.patch("/identity")
async def update_identity(
    router_id: uuid.UUID,
    payload: SystemIdentityUpdateRequest,
    request: Request | None = None,
    claims: dict[str, Any] = Depends(require_roles(*_SYSTEM_ADMIN_ROLES, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Cambia el identity interno del MikroTik y sincroniza ros_identity y display_name en la DB de RoSGrid."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    new_name = payload.name.strip()
    previous_identity = getattr(router_obj, "ros_identity", None)
    previous_display_name = getattr(router_obj, "display_name", None)

    async with client:
        try:
            res = await client.post("/system/identity/set", json_data={"name": new_name})
        except Exception:
            res = await client.patch("/system/identity", json_data={"name": new_name})

    router_obj.ros_identity = new_name
    if payload.sync_display_name:
        router_obj.display_name = new_name

    tenant_id = uuid.UUID(str(claims["tid"]))
    try:
        redis = get_redis_client()
        await invalidate_webfig_cache(redis, tenant_id, router_id, "system/identity")
    except Exception:
        pass

    actor_sub = claims.get("sub")
    actor_uid = uuid.UUID(str(actor_sub)) if actor_sub else None
    client_host = request.client.host if request and getattr(request, "client", None) else "127.0.0.1"
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=actor_uid,
        actor_username=str(claims.get("preferred_username") or claims.get("username") or actor_sub or "unknown"),
        actor_role=str(claims.get("rol", SystemRoleEnum.TENANT_ADMIN.value)),
        actor_ip=client_host,
        event_category="WEBFIG_SYSTEM",
        event_action="SYSTEM_IDENTITY_UPDATED",
        router_id=getattr(router_obj, "id", router_id),
        router_display_name=getattr(router_obj, "display_name", new_name),
        ros_rest_method="POST",
        ros_rest_endpoint="/rest/system/identity/set",
        before_state={"ros_identity": previous_identity, "display_name": previous_display_name},
        after_state={"ros_identity": router_obj.ros_identity, "display_name": router_obj.display_name},
        status_code=200,
    )
    await db.commit()
    return res or {
        "name": new_name,
        "ros_identity": router_obj.ros_identity,
        "display_name": router_obj.display_name,
    }
```

---

### 2.3. Backend: Sincronización de `system/identity` desde WebFig Capa 2 en [`fastapi/src/api/v1/webfig_layer2.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/webfig_layer2.py#L893-L1005)

Cuando se actualiza el singleton `system/identity` mediante `PATCH /api/v1/routers/{router_id}/webfig/layer2/resource/system/identity` (o `/singleton/system/identity`), sincronizar también `router_obj.ros_identity` y `router_obj.display_name` en PostgreSQL:

**Target 1 (`fastapi/src/api/v1/webfig_layer2.py` líneas 892-898):**
```python
        else:
            res = await _action_singleton()

        await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, full_path)
```

**Replacement 1:**
```python
        else:
            res = await _action_singleton()

        if full_path == "system/identity" and isinstance(attributes, dict) and attributes.get("name"):
            new_ident = str(attributes["name"]).strip()
            if new_ident:
                router_obj.ros_identity = new_ident
                router_obj.display_name = new_ident

        await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, full_path)
```

**Target 2 (`fastapi/src/api/v1/webfig_layer2.py` líneas 992-998):**
```python
    else:
        res = await _action_singleton()

    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)
```

**Replacement 2:**
```python
    else:
        res = await _action_singleton()

    if clean_path == "system/identity" and isinstance(attributes, dict) and attributes.get("name"):
        new_ident = str(attributes["name"]).strip()
        if new_ident:
            router_obj.ros_identity = new_ident
            router_obj.display_name = new_ident

    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)
```

---

### 2.4. Frontend: Prioridad Reactiva y Sincronización de Stores en [`vue3/src/views/RouterWebFigLayout.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterWebFigLayout.vue#L28-L45)

Priorizar `webFigStore.currentRouter` (cuando su `id` coincide con `routerId.value`) sobre el caché previo de `inventoryStore.routers`, y asegurar que `loadRouterData()` sincronice ambos stores:

**Target (`vue3/src/views/RouterWebFigLayout.vue` líneas 28-46):**
```ts
  const currentRouter = computed<RouterItem | null>(() => {
    return (
      inventoryStore.routers.find((r) => r.id === routerId.value) ||
      webFigStore.currentRouter ||
      null
    );
  });

  async function loadRouterData() {
    if (!routerId.value) return;
    try {
      const res = await http.get<RouterItem>(`/api/v1/inventory/routers/${routerId.value}`);
      if (res.data) {
        webFigStore.setCurrentRouter(res.data);
      }
    } catch {
      // Si falla la petición puntual, se mantiene el dato de caché en inventoryStore
    }
  }
```

**Replacement:**
```ts
  const currentRouter = computed<RouterItem | null>(() => {
    if (webFigStore.currentRouter && webFigStore.currentRouter.id === routerId.value) {
      return webFigStore.currentRouter;
    }
    return (
      inventoryStore.routers.find((r) => r.id === routerId.value) ||
      webFigStore.currentRouter ||
      null
    );
  });

  async function loadRouterData() {
    if (!routerId.value) return;
    try {
      const res = await http.get<RouterItem>(`/api/v1/inventory/routers/${routerId.value}`);
      if (res.data) {
        webFigStore.setCurrentRouter(res.data);
        inventoryStore.updateRouter(res.data);
      }
    } catch {
      // Si falla la petición puntual, se mantiene el dato de caché en inventoryStore
    }
  }
```

---

### 2.5. Frontend: Modal, Reactividad Inmediata y Banners en [`vue3/src/views/RouterLiveDashboardView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterLiveDashboardView.vue)

1. Importar `useInventoryStore` y sincronizar tanto `webFigStore.setCurrentRouter(...)` como `inventoryStore.updateRouter(...)` inmediatamente después de `handleChangeIdentity()` y `handleSyncDiscovery()`.
2. Precargar `newIdentityName.value` con la identidad actual del router al abrir el modal (`openIdentityModal()`) e incluir el checkbox `#chk-sync-display-name` (`syncDisplayName`, activo por defecto).
3. Separar mensajes de éxito (`actionBannerMsg`) y de error (`actionBannerError`) y añadir estilos `.banner`, `.banner--success`, `.banner--error` y `.checkbox-row` en `<style scoped>`.

**Target 1 (`vue3/src/views/RouterLiveDashboardView.vue` líneas 7-17):**
```ts
  import { useLiveTelemetryStore } from '@/stores/useLiveTelemetryStore';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';

  const route = useRoute();
  const telemetryStore = useLiveTelemetryStore();
  const webFigStore = useWebFigStore();
  const authStore = useAuthStore();
  const { t } = useI18n();
```

**Replacement 1:**
```ts
  import { useLiveTelemetryStore } from '@/stores/useLiveTelemetryStore';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import type { RouterItem } from '@/types';

  const route = useRoute();
  const telemetryStore = useLiveTelemetryStore();
  const webFigStore = useWebFigStore();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();
  const { t } = useI18n();
```

**Target 2 (`vue3/src/views/RouterLiveDashboardView.vue` líneas 260-313):**
```ts
  // Modales de Identidad y Reinicio (Spec 60)
  const showIdentityModal = ref(false);
  const newIdentityName = ref('');
  const showRebootModal = ref(false);
  const rebootReason = ref('');
  const actionBannerMsg = ref('');
  const isSubmittingAction = ref(false);

  function openIdentityModal(): void {
    newIdentityName.value = '';
    showIdentityModal.value = true;
  }

  async function handleChangeIdentity(): Promise<void> {
    if (!newIdentityName.value.trim()) return;
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    try {
      await http.patch(`/api/v1/routers/${routerId.value}/webfig/system/identity`, {
        name: newIdentityName.value.trim(),
      });
      actionBannerMsg.value = `Identidad del router actualizada a "${newIdentityName.value.trim()}".`;
      showIdentityModal.value = false;
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerMsg.value = e.detail || e.message || 'Error al actualizar identidad.';
    } finally {
      isSubmittingAction.value = false;
    }
  }

  async function handleSyncDiscovery(): Promise<void> {
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    try {
      await http.post(`/api/v1/inventory/routers/${routerId.value}/sync-discovery`);
      actionBannerMsg.value = 'Sincronización de descubrimiento (Hardware/RouterOS) completada.';
      await fetchDashboardData();
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerMsg.value = e.detail || e.message || 'Error al sincronizar hardware.';
    } finally {
      isSubmittingAction.value = false;
    }
  }

  async function handleRebootRouter(): Promise<void> {
    if (rebootReason.value.trim().length < 3) return;
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/system/reboot`, {
        reason: rebootReason.value.trim(),
      });
      actionBannerMsg.value = 'Orden de reinicio enviada al router MikroTik.';
      showRebootModal.value = false;
      rebootReason.value = '';
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerMsg.value = e.detail || e.message || 'Error al reiniciar el router.';
    } finally {
      isSubmittingAction.value = false;
    }
  }
```

**Replacement 2:**
```ts
  // Modales de Identidad y Reinicio (Spec 60 & Spec 67)
  const showIdentityModal = ref(false);
  const newIdentityName = ref('');
  const syncDisplayName = ref(true);
  const showRebootModal = ref(false);
  const rebootReason = ref('');
  const actionBannerMsg = ref('');
  const actionBannerError = ref('');
  const isSubmittingAction = ref(false);

  function getActiveRouterSnapshot(): RouterItem | null {
    return (
      (webFigStore.currentRouter && webFigStore.currentRouter.id === routerId.value
        ? webFigStore.currentRouter
        : null) ||
      inventoryStore.routers.find((r) => r.id === routerId.value) ||
      webFigStore.currentRouter ||
      null
    );
  }

  function openIdentityModal(): void {
    const cur = getActiveRouterSnapshot();
    newIdentityName.value = cur?.ros_identity || cur?.display_name || '';
    syncDisplayName.value = true;
    actionBannerError.value = '';
    showIdentityModal.value = true;
  }

  async function handleChangeIdentity(): Promise<void> {
    const trimmed = newIdentityName.value.trim();
    if (!trimmed) return;
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      const res = await http.patch<{
        name?: string;
        ros_identity?: string;
        display_name?: string;
      }>(`/api/v1/routers/${routerId.value}/webfig/system/identity`, {
        name: trimmed,
        sync_display_name: syncDisplayName.value,
      });
      const updatedIdentity = res.data?.ros_identity || res.data?.name || trimmed;
      const cur = getActiveRouterSnapshot();
      const updatedDisplayName =
        res.data?.display_name ||
        (syncDisplayName.value ? updatedIdentity : cur?.display_name || updatedIdentity);

      if (cur) {
        const updatedRouter: RouterItem = {
          ...cur,
          ros_identity: updatedIdentity,
          display_name: updatedDisplayName,
        };
        webFigStore.setCurrentRouter(updatedRouter);
        inventoryStore.updateRouter(updatedRouter);
      } else {
        try {
          const fresh = await http.get<RouterItem>(`/api/v1/inventory/routers/${routerId.value}`);
          if (fresh.data) {
            webFigStore.setCurrentRouter(fresh.data);
            inventoryStore.updateRouter(fresh.data);
          }
        } catch {
          // Ignorar fallo secundario de refresco
        }
      }

      actionBannerMsg.value = `Identidad del router actualizada a "${updatedIdentity}".`;
      showIdentityModal.value = false;
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al actualizar identidad.';
    } finally {
      isSubmittingAction.value = false;
    }
  }

  async function handleSyncDiscovery(): Promise<void> {
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      const res = await http.post<RouterItem>(
        `/api/v1/inventory/routers/${routerId.value}/sync-discovery`,
      );
      if (res.data && typeof res.data === 'object' && 'id' in res.data) {
        webFigStore.setCurrentRouter(res.data);
        inventoryStore.updateRouter(res.data);
      }
      actionBannerMsg.value = 'Sincronización de descubrimiento (Hardware/RouterOS) completada.';
      await fetchDashboardData();
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al sincronizar hardware.';
    } finally {
      isSubmittingAction.value = false;
    }
  }

  async function handleRebootRouter(): Promise<void> {
    if (rebootReason.value.trim().length < 3) return;
    isSubmittingAction.value = true;
    actionBannerMsg.value = '';
    actionBannerError.value = '';
    try {
      await http.post(`/api/v1/routers/${routerId.value}/webfig/system/reboot`, {
        reason: rebootReason.value.trim(),
      });
      actionBannerMsg.value = 'Orden de reinicio enviada al router MikroTik.';
      showRebootModal.value = false;
      rebootReason.value = '';
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      actionBannerError.value = e.detail || e.message || 'Error al reiniciar el router.';
    } finally {
      isSubmittingAction.value = false;
    }
  }
```

**Target 3 (`vue3/src/views/RouterLiveDashboardView.vue` líneas 387-390):**
```html
    <div v-if="actionBannerMsg" class="banner banner--success" role="status">
      {{ actionBannerMsg }}
    </div>
```

**Replacement 3:**
```html
    <div v-if="actionBannerMsg" id="banner-identity-success" class="banner banner--success" role="status">
      {{ actionBannerMsg }}
    </div>
    <div v-if="actionBannerError" id="banner-identity-error" class="banner banner--error" role="alert">
      {{ actionBannerError }}
    </div>
```

**Target 4 (`vue3/src/views/RouterLiveDashboardView.vue` líneas 539-578):**
```html
    <!-- Modal Cambiar Identity (Spec 60) -->
    <div v-if="showIdentityModal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="identity-modal-title">
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="identity-modal-title" class="modal-title">🏷️ Cambiar Identidad del Router</h3>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="showIdentityModal = false">✕</button>
        </header>
        <div class="modal-body">
          <div class="form-group">
            <label for="input-router-identity">Nuevo nombre de Identity (/system/identity):</label>
            <input
              id="input-router-identity"
              v-model="newIdentityName"
              type="text"
              class="form-control"
              placeholder="Ej: CCR2004-Borde-Norte"
              maxlength="128"
            />
          </div>
        </div>
        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showIdentityModal = false">Cancelar</button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="isSubmittingAction || !newIdentityName.trim()"
            @click="handleChangeIdentity"
          >
            💾 Guardar Identity
          </button>
        </footer>
      </div>
    </div>
```

**Replacement 4:**
```html
    <!-- Modal Cambiar Identity (Spec 60 & Spec 67) -->
    <div v-if="showIdentityModal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="identity-modal-title">
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="identity-modal-title" class="modal-title">🏷️ Cambiar Identidad del Router</h3>
          <button type="button" class="btn-close" aria-label="Cerrar" @click="showIdentityModal = false">✕</button>
        </header>
        <form @submit.prevent="handleChangeIdentity">
          <div class="modal-body">
            <div class="form-group">
              <label for="input-router-identity">Nuevo nombre de Identity (/system/identity):</label>
              <input
                id="input-router-identity"
                v-model="newIdentityName"
                type="text"
                class="form-control"
                placeholder="Ej: CCR2004-Borde-Norte"
                maxlength="128"
                required
              />
            </div>
            <div class="form-group checkbox-row">
              <input
                id="chk-sync-display-name"
                v-model="syncDisplayName"
                type="checkbox"
              />
              <label for="chk-sync-display-name">
                Sincronizar también el nombre visible en el Inventario RoSGrid
              </label>
            </div>
          </div>
          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showIdentityModal = false">Cancelar</button>
            <button
              id="btn-confirm-identity"
              type="submit"
              class="btn btn-primary"
              :disabled="isSubmittingAction || !newIdentityName.trim()"
            >
              {{ isSubmittingAction ? '⏳ Guardando...' : '💾 Guardar Identity' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
```

**Target 5 (`vue3/src/views/RouterLiveDashboardView.vue` líneas 828-846):**
```css
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid var(--border-color);
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
  }
  .text-warning {
    color: var(--status-warning, #f59e0b);
    font-size: 0.8rem;
    margin-bottom: 12px;
  }
</style>
```

**Replacement 5:**
```css
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid var(--border-color);
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
  }
  .checkbox-row {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }
  .banner {
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
  }
  .banner--success {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid var(--status-online, #10b981);
    color: var(--status-online, #10b981);
  }
  .banner--error {
    background: rgba(239, 68, 68, 0.14);
    border: 1px solid var(--status-offline, #ef4444);
    color: var(--status-offline, #ef4444);
  }
  .text-warning {
    color: var(--status-warning, #f59e0b);
    font-size: 0.8rem;
    margin-bottom: 12px;
  }
</style>
```

---

### 2.6. Frontend: Sincronización Reactiva desde Capa 2 (`system/identity`) en [`vue3/src/views/DynamicLayer2ResourceView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/DynamicLayer2ResourceView.vue#L438-L468)

1. Importar `useInventoryStore` en `DynamicLayer2ResourceView.vue`.
2. Cuando `handleSaveRecord()` guarda el singleton `system/identity`, actualizar inmediatamente `webFigStore.currentRouter` e `inventoryStore.routers`:

**Target 1 (`vue3/src/views/DynamicLayer2ResourceView.vue` líneas 7-15):**
```ts
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const { t } = useI18n();
```

**Replacement 1:**
```ts
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const inventoryStore = useInventoryStore();
  const { t } = useI18n();
```

**Target 2 (`vue3/src/views/DynamicLayer2ResourceView.vue` líneas 441-447):**
```ts
      if (resourceData.value.is_singleton) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
          { attributes: resourceData.value.form_data, enable_safemode: true },
        );
        showSuccessBanner('Configuración singleton actualizada con Safe Mode.');
      } else {
```

**Replacement 2:**
```ts
      if (resourceData.value.is_singleton) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
          { attributes: resourceData.value.form_data, enable_safemode: true },
        );
        if (
          rosPath.value === 'system/identity' &&
          resourceData.value.form_data &&
          typeof resourceData.value.form_data.name === 'string' &&
          resourceData.value.form_data.name.trim()
        ) {
          const newIdent = resourceData.value.form_data.name.trim();
          const cur =
            webFigStore.currentRouter ||
            inventoryStore.routers.find((r) => r.id === routerId.value) ||
            null;
          if (cur) {
            const updatedRouter = {
              ...cur,
              ros_identity: newIdent,
              display_name: newIdent,
            };
            webFigStore.setCurrentRouter(updatedRouter);
            inventoryStore.updateRouter(updatedRouter);
          }
        }
        showSuccessBanner('Configuración singleton actualizada con Safe Mode.');
      } else {
```

---

### 2.7. Frontend: Columna `Identity` y Refresco Automático al Montar en [`vue3/src/views/RouterInventoryView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/RouterInventoryView.vue#L98-L103) y [`vue3/src/stores/useInventoryStore.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/stores/useInventoryStore.ts#L98-L106)

1. En `RouterInventoryView.vue`, formatear la columna `display_name` (`Identity`) exactamente igual que en `BulkOperationsAndUpdatesView.vue` (mostrando `${r.display_name} (${r.ros_identity})` cuando difieren, o `r.display_name` cuando coinciden) e invocar `inventoryStore.fetchRouters()` siempre en `onMounted()`.
2. En `useInventoryStore.ts`, proteger `fetchRouters()` (`if (items.length > 0 || routers.value.length === 0) { setRouters(items); }`) para no sobrescribir con un arreglo vacío `[]` los routers pre-sembrados en pruebas unitarias aisladas cuando `http.get` devuelve `data: []`.

**Target 1 (`vue3/src/views/RouterInventoryView.vue` líneas 99-102):**
```ts
  const tableColumns = computed<TableColumn<Record<string, unknown>>[]>(() => [
    { key: 'display_name', label: t('inventory.col_name'), sortable: true },
    {
```

**Replacement 1:**
```ts
  const tableColumns = computed<TableColumn<Record<string, unknown>>[]>(() => [
    {
      key: 'display_name',
      label: t('inventory.col_name'),
      sortable: true,
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        if (r.ros_identity && r.ros_identity !== r.display_name) {
          return `${r.display_name} (${r.ros_identity})`;
        }
        return r.display_name;
      },
    },
    {
```

**Target 2 (`vue3/src/views/RouterInventoryView.vue` líneas 282-287):**
```ts
  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    }
    inventoryStore.fetchNetworkRoles();
  });
```

**Replacement 2:**
```ts
  onMounted(() => {
    inventoryStore.fetchRouters();
    inventoryStore.fetchNetworkRoles();
  });
```

**Target 3 (`vue3/src/stores/useInventoryStore.ts` líneas 100-104):**
```ts
        syslog_event_count: Number(item.syslog_event_count || 0),
      }));
      setRouters(items);
    } catch (err) {
```

**Replacement 3:**
```ts
        syslog_event_count: Number(item.syslog_event_count || 0),
      }));
      if (items.length > 0 || routers.value.length === 0) {
        setRouters(items);
      }
    } catch (err) {
```

---

## 3. Pirámide de Pruebas 11X y Contratos Karate Labs BDD

1. **Pruebas Unitarias Backend (`fastapi/tests/api/test_webfig_endpoints_full.unit.py`):**
   - Verificar que `update_identity` actualiza tanto `r.ros_identity` como `r.display_name` cuando `sync_display_name=True` (valor por defecto), preserva `r.display_name` si `sync_display_name=False`, invalida la caché de KeyDB e invoca `write_audit_log` con `SYSTEM_IDENTITY_UPDATED`.
2. **Pruebas Unitarias Frontend (`vue3/src/views/webfigViews.unit.ts`):**
   - Verificar en `RouterLiveDashboardView.vue` que al abrir `#btn-change-identity`, el input `#input-router-identity` precarga el identity actual del router, y que al enviar el formulario (`#btn-confirm-identity`), se ejecuta `PATCH /api/v1/routers/{id}/webfig/system/identity` y se actualizan reactivamente tanto `webFigStore.currentRouter` como `inventoryStore.routers`.
   - Verificar en `RouterWebFigLayout.vue` que `RouterContextHeader` refleja inmediatamente el nuevo `ros_identity` y `display_name` sin requerir recarga de página.
3. **Escenarios Karate Labs BDD (`fastapi/test/api_test.feature`, `vue3/test/ui_business_flow.feature` y espejos en `docs/examples/`):**
   - Validar el contrato `PATCH /api/v1/routers/{id}/webfig/system/identity` y la presencia e interactividad de `#btn-change-identity`, `#input-router-identity`, `#chk-sync-display-name` y `#btn-confirm-identity`.
