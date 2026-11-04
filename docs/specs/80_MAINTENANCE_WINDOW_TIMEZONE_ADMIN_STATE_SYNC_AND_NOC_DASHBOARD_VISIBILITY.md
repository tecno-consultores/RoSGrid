# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 80: Sincronización Automática de Ventanas de Mantenimiento con `admin_state` del Router, Estado Reactivo `En Curso` / `Programada`, Visibilidad en Wallboard NOC y Centro de Mando, y Resolución Humana de Actores/Routers en Cinta de Eventos WORM

> **Hito Asociado:** Hito 30 (Subhito `30.2`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Estado:** Planificado y Especificado (*Flash-Ready* — Cero Ambigüedad)

---

## 1. Diagnóstico Forense de las 5 Causas Raíz Detectadas en UAT

Al programar una ventana de mantenimiento en `/inventory/maintenance-windows` para el equipo `r111 (10.250.3.8)` con horario `4/11/2026, 14:02:00 → 14:10:00` (siendo las `14:05` hora local del sistema), se evidenciaron **5 brechas técnicas interconectadas**:

1. **Desconexión entre `MaintenanceWindow` y el Estado Administrativo Efectivo (`Router.admin_state`) en el Backend (`fastapi/src/api/v1/inventory.py` y `fastapi/src/api/v1/inventory_helpers.py`):**
   - Al crear una ventana en `POST /api/v1/maintenance/windows` (`fastapi/src/api/v1/maintenance.py`), se inserta el registro en la tabla `maintenance_windows`, pero `GET /api/v1/inventory/routers` (`list_routers`) y `GET /api/v1/inventory/routers/{router_id}` (`get_router`) devuelven únicamente la columna estática `r.admin_state` (`"PRODUCTION"`) sin evaluar si existe una `MaintenanceWindow` activa (`starts_at <= now_utc <= ends_at` y `is_cancelled == False`) que aplique al router por `router_id`, por etiqueta (`target_tag`) o de forma global (`target_tag == "global"`).
   - Como consecuencia, mientras la ventana está en curso, el backend sigue reportando `admin_state: "PRODUCTION"` para `r111`, por lo que `NocWallboardView.vue` muestra `MANTENIMIENTO: 0` y `ONLINE: 7`.

2. **Etiqueta Estática Codificada en Duro (`'Programada'`) en `/inventory/maintenance-windows` (`vue3/src/views/MaintenanceWindowsView.vue`):**
   - En la línea 385 de `MaintenanceWindowsView.vue`, la columna `Estado` renderiza literalmente `{{ w.is_cancelled ? 'Cancelada' : 'Programada' }}`.
   - Nunca compara la hora actual (`nowTick`) contra `w.starts_at` y `w.ends_at`, por lo que una ventana que ya inició a las `14:02` sigue diciendo **`Programada`** a las `14:05` en lugar de cambiar dinámicamente a **`🛠️ En Curso`**, y tampoco refresca `inventoryStore.fetchRouters(true)` al crear o cancelar una ventana.

3. **Ausencia de Contador e Indicador de Mantenimiento en la Pantalla Principal (`Centro de Mando` — `vue3/src/views/DashboardHomeView.vue`):**
   - En `DashboardHomeView.vue` (líneas 31–44), `onlineRouters` cuenta todos los routers alcanzables sin excluir aquellos con `admin_state === 'MAINTENANCE'`, no existe la propiedad computada `maintenanceRouters`, la tarjeta KPI `FLOTA MIKROTIK` solo muestra `7 en línea | 0 desconectado` (ocultando cuántos equipos están en mantenimiento), y la lista inferior `Acceso Rápido a Equipos de la Flota` muestra punto verde (`status-dot--online`) sin insignia `🛠️ MANTENIMIENTO`. Además, `onMounted` solo llamaba a `fetchRouters` si `inventoryStore.routers.length === 0`, mostrando datos obsoletos al volver desde `/inventory/maintenance-windows`.

4. **Falta de Opción `En Mantenimiento` en el Filtro del Mapa NOC y Falsa Alerta RCA por Mantenimiento Programado (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
   - En `UnifiedNetworkMap.vue`, el selector `statusFilter` (`Todos los Estados`) solo ofrecía `ALL`, `ONLINE` y `OFFLINE` (sin opción `MAINTENANCE`) y ni siquiera filtraba la capa `props.routers` en el mapa.
   - Asimismo, `downRouters` (línea 119) incluía `r.admin_state === 'MAINTENANCE'` dentro de la franja roja `🚨 ALERTA RCA: CAÍDA DE ROUTER PRINCIPAL`, tratando un mantenimiento programado como una caída no planificada.

5. **UUID Crudo (`5046a660-b1ba-423d-bf0b-a6f0fd80c40b`) y Etiqueta `MANTENIMIENTO` Universal en la Cinta de Eventos Críticos (`fastapi/src/core/audit.py`, `fastapi/src/api/v1/maintenance.py`, `vue3/src/utils/eventFormatter.ts` y `vue3/src/views/NocWallboardView.vue`):**
   - En `maintenance.py` (líneas 215, 250 y 301), `write_audit_log` recibía `actor_username=claims.get("sub", "")` (que en el JWT de RoSGrid es el UUID del usuario, no su `username`) y omitía `router_display_name`.
   - En `NocWallboardView.vue` (líneas 154 y 288), cualquier evento de auditoría que no fuera `MASS_OUTAGE` o `AUTH` caía en el `else` por defecto `'MAINTENANCE'`, etiquetando respaldos `.rsc` (`ROUTER_BACKUP_CREATED`) y renovaciones de token como `MANTENIMIENTO`.

---

## 2. Instrucciones de Implementación Exactas (*Flash-Ready* `Target` / `Replacement`)

### Paso 1: Resolución Automática de `actor_username` (Usuario) y `router_display_name` (Router) en `fastapi/src/core/audit.py`

Editar `fastapi/src/core/audit.py` para que `write_audit_log` resuelva automáticamente el `username` real desde `User` cuando `actor_username` sea un UUID o coincida con `actor_user_id`, y resuelva `router_display_name` desde `Router` cuando se proporcione `router_id` sin `router_display_name`:

**`Target` en `fastapi/src/core/audit.py`:**
```python
    stmt = (
        select(AuditLog.record_sha256_hash)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    prev_hash = res.scalar_one_or_none() or GENESIS_AUDIT_HASH

    safe_username = sanitize_log_string(actor_username, max_len=64) or "system"
    safe_ua = sanitize_log_string(actor_user_agent, max_len=256)
    safe_err = sanitize_log_string(error_message, max_len=512)
    safe_router_name = sanitize_log_string(router_display_name, max_len=128)
```

**`Replacement` en `fastapi/src/core/audit.py`:**
```python
    stmt = (
        select(AuditLog.record_sha256_hash)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    prev_hash = res.scalar_one_or_none() or GENESIS_AUDIT_HASH

    resolved_username = actor_username
    if actor_user_id and (not resolved_username or str(resolved_username).strip() == str(actor_user_id).strip()):
        try:
            from src.models.core import User

            user_obj = await session.get(User, actor_user_id)
            uname = getattr(user_obj, "username", None)
            if isinstance(uname, str) and uname.strip():
                resolved_username = uname.strip()
        except Exception:
            pass

    resolved_router_name = router_display_name
    if router_id and not resolved_router_name:
        try:
            from src.models.inventory import Router

            router_obj = await session.get(Router, router_id)
            rname = getattr(router_obj, "display_name", None)
            if isinstance(rname, str) and rname.strip():
                resolved_router_name = rname.strip()
        except Exception:
            pass

    safe_username = sanitize_log_string(resolved_username, max_len=64) or "system"
    safe_ua = sanitize_log_string(actor_user_agent, max_len=256)
    safe_err = sanitize_log_string(error_message, max_len=512)
    safe_router_name = sanitize_log_string(resolved_router_name, max_len=128)
```

---

### Paso 2: Motor de Evaluación de Ventanas de Mantenimiento Activas en `fastapi/src/api/v1/inventory_helpers.py` y `fastapi/src/api/v1/inventory.py`

1. En `fastapi/src/api/v1/inventory_helpers.py`, agregar la función `resolve_active_maintenance_router_ids` y el parámetro `in_active_maintenance_window: bool = False` en `build_router_response`:

**`Target` en `fastapi/src/api/v1/inventory_helpers.py`:**
```python
def build_router_response(r: Router, telemetry: dict[str, Any]) -> RouterResponse:
    """Construye esquema de respuesta de Router combinando modelo y métricas en vivo."""
    tag_names = [t.tag_name for t in r.tags] if r.tags else []
    is_effective_reachable = bool(
        r.is_reachable
        or telemetry.get("syslog_active")
        or (telemetry.get("operational_status") == "ONLINE")
    )
    operational_status = telemetry.get("operational_status", "OFFLINE")
    if is_effective_reachable and operational_status == "OFFLINE":
        operational_status = "ONLINE"

    return RouterResponse(
        id=r.id,
        tenant_id=r.tenant_id,
        display_name=r.display_name,
        api_base_url=r.api_base_url,
        api_port=r.api_port,
        network_role=r.network_role,
        admin_state=r.admin_state,
```

**`Replacement` en `fastapi/src/api/v1/inventory_helpers.py`:**
```python
async def resolve_active_maintenance_router_ids(
    db: Any,
    tenant_id: uuid.UUID,
    routers: list[Router] | tuple[Router, ...],
) -> set[uuid.UUID]:
    """Purga ventanas vencidas y devuelve el conjunto de router_id cubiertos por ventanas de mantenimiento en curso."""
    if not routers:
        return set()
    try:
        from sqlalchemy import select

        from src.api.v1.maintenance import purge_expired_maintenance_windows
        from src.models.inventory import MaintenanceWindow

        await purge_expired_maintenance_windows(db, tenant_id=tenant_id, commit=True)
        now_utc = datetime.now(UTC)
        stmt = select(MaintenanceWindow).where(
            MaintenanceWindow.tenant_id == tenant_id,
            MaintenanceWindow.is_cancelled.is_(False),
            MaintenanceWindow.starts_at <= now_utc,
            MaintenanceWindow.ends_at > now_utc,
        )
        res = await db.execute(stmt)
        active_windows = list(res.scalars().all())
    except Exception:
        return set()

    if not active_windows:
        return set()

    matched_ids: set[uuid.UUID] = set()
    has_global = any(
        (getattr(w, "target_tag", None) or "").strip().lower() == "global"
        for w in active_windows
        if hasattr(w, "starts_at")
    )
    direct_router_ids = {
        w.router_id
        for w in active_windows
        if getattr(w, "router_id", None) is not None and hasattr(w, "starts_at")
    }
    active_tags = {
        str(w.target_tag).strip().lower()
        for w in active_windows
        if getattr(w, "target_tag", None) and hasattr(w, "starts_at")
    } - {"global"}

    for r in routers:
        if has_global or r.id in direct_router_ids:
            matched_ids.add(r.id)
            continue
        if active_tags and r.tags:
            router_tags = {str(t.tag_name).strip().lower() for t in r.tags if getattr(t, "tag_name", None)}
            if router_tags & active_tags:
                matched_ids.add(r.id)

    return matched_ids


def build_router_response(
    r: Router,
    telemetry: dict[str, Any],
    in_active_maintenance_window: bool = False,
) -> RouterResponse:
    """Construye esquema de respuesta de Router combinando modelo, ventanas activas y métricas en vivo."""
    tag_names = [t.tag_name for t in r.tags] if r.tags else []
    is_effective_reachable = bool(
        r.is_reachable
        or telemetry.get("syslog_active")
        or (telemetry.get("operational_status") == "ONLINE")
    )
    operational_status = telemetry.get("operational_status", "OFFLINE")
    if is_effective_reachable and operational_status == "OFFLINE":
        operational_status = "ONLINE"

    effective_admin_state = r.admin_state
    if in_active_maintenance_window and r.admin_state != RouterAdminStateEnum.DECOMMISSIONED:
        effective_admin_state = RouterAdminStateEnum.MAINTENANCE

    return RouterResponse(
        id=r.id,
        tenant_id=r.tenant_id,
        display_name=r.display_name,
        api_base_url=r.api_base_url,
        api_port=r.api_port,
        network_role=r.network_role,
        admin_state=effective_admin_state,
```

2. En `fastapi/src/api/v1/inventory.py`, actualizar `list_routers`, `get_router` y `update_router` para aplicar `resolve_active_maintenance_router_ids` (y cuando el operador cambie manualmente `admin_state` a `PRODUCTION` en `update_router`, cancelar cualquier ventana de mantenimiento activa individual sobre ese router):

**`Target` en `fastapi/src/api/v1/inventory.py`:**
```python
from src.api.v1.inventory_helpers import (
    apply_router_scalar_updates,
    build_router_from_csv,
    build_router_response,
    enrich_router_telemetry,
    perform_discovery,
    row_to_commit_item,
    validate_single_csv_row,
)
```

**`Replacement` en `fastapi/src/api/v1/inventory.py`:**
```python
from src.api.v1.inventory_helpers import (
    apply_router_scalar_updates,
    build_router_from_csv,
    build_router_response,
    enrich_router_telemetry,
    perform_discovery,
    resolve_active_maintenance_router_ids,
    row_to_commit_item,
    validate_single_csv_row,
)
```

**`Target` en `list_routers` y `get_router` (`fastapi/src/api/v1/inventory.py`):**
```python
    query = select(Router).options(selectinload(Router.tags), selectinload(Router.vault))
    query = _apply_role_filters(query, claims, tenant_id, user_id)
    query = _apply_query_search_filters(query, network_role, admin_state, tag, search)
    query = query.order_by(Router.display_name.asc())

    result = await db.execute(query)
    routers = result.scalars().all()

    if refresh and routers:
        async def _probe_router(r: Router) -> None:
            if not r.vault:
                return
            try:
                from src.api.v1.inventory_helpers import discover_and_persist_syslog_status
                from src.api.v1.webfig_common import _create_client_from_vault
                client = _create_client_from_vault(r, tenant_id)
                client.timeout = 2.0
                try:
                    await discover_and_persist_syslog_status(client, tenant_id, r.id, redis)
                finally:
                    await client.close()
            except Exception:
                pass

        await asyncio.gather(*[_probe_router(r) for r in routers], return_exceptions=True)

    response_items = []
    for r in routers:
        telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
        response_items.append(build_router_response(r, telemetry))
    return response_items
```

**`Replacement` en `list_routers` (`fastapi/src/api/v1/inventory.py`):**
```python
    query = select(Router).options(selectinload(Router.tags), selectinload(Router.vault))
    query = _apply_role_filters(query, claims, tenant_id, user_id)
    query = _apply_query_search_filters(query, network_role, None, tag, search)
    query = query.order_by(Router.display_name.asc())

    result = await db.execute(query)
    routers = list(result.scalars().all())
    active_mw_router_ids = await resolve_active_maintenance_router_ids(db, tenant_id, routers)

    if refresh and routers:
        async def _probe_router(r: Router) -> None:
            if not r.vault:
                return
            try:
                from src.api.v1.inventory_helpers import discover_and_persist_syslog_status
                from src.api.v1.webfig_common import _create_client_from_vault
                client = _create_client_from_vault(r, tenant_id)
                client.timeout = 2.0
                try:
                    await discover_and_persist_syslog_status(client, tenant_id, r.id, redis)
                finally:
                    await client.close()
            except Exception:
                pass

        await asyncio.gather(*[_probe_router(r) for r in routers], return_exceptions=True)

    response_items = []
    for r in routers:
        telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
        item_resp = build_router_response(
            r,
            telemetry,
            in_active_maintenance_window=(r.id in active_mw_router_ids),
        )
        if admin_state is not None and item_resp.admin_state != admin_state:
            continue
        response_items.append(item_resp)
    return response_items
```

**`Target` en `get_router` y `update_router` (`fastapi/src/api/v1/inventory.py`):**
```python
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(r, telemetry)


@router.put("/routers/{router_id}", response_model=RouterResponse)
async def update_router(
    router_id: uuid.UUID,
    payload: UpdateRouterRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Actualiza metadatos, ubicación o etiquetas de un router."""
    tenant_id = uuid.UUID(claims["tid"])
    query = (
        select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    apply_router_scalar_updates(r, payload)
    if payload.network_role:
        r.network_role = payload.network_role.strip().upper()
        await _ensure_custom_network_roles(
            db,
            tenant_id,
            {r.network_role},
            description="Rol personalizado registrado al actualizar router",
        )

    if payload.tags is not None:
        await db.execute(delete(RouterTag).where(RouterTag.router_id == r.id))
        for tag_name in payload.tags:
            clean_tag = tag_name.strip().lower()
            if clean_tag:
                db.add(RouterTag(tenant_id=tenant_id, router_id=r.id, tag_name=clean_tag))

    await db.commit()
    await db.refresh(r, ["tags"])
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(r, telemetry)
```

**`Replacement` en `get_router` y `update_router` (`fastapi/src/api/v1/inventory.py`):**
```python
    active_mw_router_ids = await resolve_active_maintenance_router_ids(db, tenant_id, [r])
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(
        r,
        telemetry,
        in_active_maintenance_window=(r.id in active_mw_router_ids),
    )


@router.put("/routers/{router_id}", response_model=RouterResponse)
async def update_router(
    router_id: uuid.UUID,
    payload: UpdateRouterRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Actualiza metadatos, ubicación o etiquetas de un router."""
    tenant_id = uuid.UUID(claims["tid"])
    query = (
        select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    apply_router_scalar_updates(r, payload)
    if payload.admin_state == RouterAdminStateEnum.PRODUCTION:
        try:
            from src.models.inventory import MaintenanceWindow

            now_utc = datetime.now(UTC)
            mw_stmt = select(MaintenanceWindow).where(
                MaintenanceWindow.tenant_id == tenant_id,
                MaintenanceWindow.router_id == r.id,
                MaintenanceWindow.is_cancelled.is_(False),
                MaintenanceWindow.ends_at > now_utc,
            )
            mw_res = await db.execute(mw_stmt)
            for active_mw in mw_res.scalars().all():
                active_mw.is_cancelled = True
        except Exception:
            pass

    if payload.network_role:
        r.network_role = payload.network_role.strip().upper()
        await _ensure_custom_network_roles(
            db,
            tenant_id,
            {r.network_role},
            description="Rol personalizado registrado al actualizar router",
        )

    if payload.tags is not None:
        await db.execute(delete(RouterTag).where(RouterTag.router_id == r.id))
        for tag_name in payload.tags:
            clean_tag = tag_name.strip().lower()
            if clean_tag:
                db.add(RouterTag(tenant_id=tenant_id, router_id=r.id, tag_name=clean_tag))

    await db.commit()
    await db.refresh(r, ["tags"])
    active_mw_router_ids = await resolve_active_maintenance_router_ids(db, tenant_id, [r])
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(
        r,
        telemetry,
        in_active_maintenance_window=(r.id in active_mw_router_ids),
    )
```

---

### Paso 3: Estado Reactivo `🛠️ En Curso` vs. `⏳ Programada` y Sincronización con `useInventoryStore` en `vue3/src/views/MaintenanceWindowsView.vue`

Editar `vue3/src/views/MaintenanceWindowsView.vue` para:
1. Mantener un reloj reactivo `nowMsRef = ref(Date.now())` actualizado cada 15 segundos.
2. Evaluar dinámicamente el estado de cada ventana (`getWindowStatus(w)`):
   - `'CANCELLED'` (`Cancelada`) si `w.is_cancelled` es `true`.
   - `'IN_PROGRESS'` (`🛠️ En Curso`) si `starts_at <= nowMsRef.value && nowMsRef.value <= ends_at`.
   - `'SCHEDULED'` (`⏳ Programada`) si `nowMsRef.value < starts_at`.
3. Invocar `await inventoryStore.fetchRouters(true)` al crear una ventana, al cancelarla o cuando el temporizador detecte que una ventana acaba de iniciar o expirar.

**`Target` en `vue3/src/views/MaintenanceWindowsView.vue` (Script):**
```ts
  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const windowsList = ref<MaintenanceWindowItem[]>([]);
  let expirationCheckTimer: ReturnType<typeof setInterval> | null = null;
```

**`Replacement` en `vue3/src/views/MaintenanceWindowsView.vue` (Script):**
```ts
  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const windowsList = ref<MaintenanceWindowItem[]>([]);
  const nowMsRef = ref<number>(Date.now());
  let expirationCheckTimer: ReturnType<typeof setInterval> | null = null;

  function isWindowInProgress(w: MaintenanceWindowItem): boolean {
    if (w.is_cancelled) return false;
    const startMs = new Date(w.starts_at).getTime();
    const endMs = new Date(w.ends_at).getTime();
    if (Number.isNaN(startMs) || Number.isNaN(endMs)) return false;
    return startMs <= nowMsRef.value && nowMsRef.value <= endMs;
  }

  function getWindowStatusLabel(w: MaintenanceWindowItem): string {
    if (w.is_cancelled) return 'Cancelada';
    if (isWindowInProgress(w)) return '🛠️ En Curso';
    return '⏳ Programada';
  }
```

**`Target` en `cancelMaintenanceWindow`, `handleCreateWindow` y `onMounted` (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
    try {
      await http.post(`/api/v1/maintenance/windows/${windowItem.id}/cancel`);
      windowItem.is_cancelled = true;
      successMessage.value = 'Ventana de mantenimiento cancelada exitosamente.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
```

**`Replacement` en `cancelMaintenanceWindow` (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
    try {
      await http.post(`/api/v1/maintenance/windows/${windowItem.id}/cancel`);
      windowItem.is_cancelled = true;
      await inventoryStore.fetchRouters(true);
      successMessage.value = 'Ventana de mantenimiento cancelada exitosamente.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
```

**`Target` en `handleCreateWindow` y `onMounted` (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
      // Si el backend devolvió el objeto creado, lo colocamos arriba
      if (res.data && res.data.id) {
        windowsList.value.unshift(res.data);
      } else {
        await loadMaintenanceWindows();
      }

      // Cerrar modal y limpiar
      isCreateModalOpen.value = false;
      successMessage.value = 'Ventana de mantenimiento programada exitosamente.';
```

**`Replacement` en `handleCreateWindow` (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
      nowMsRef.value = Date.now();
      // Si el backend devolvió el objeto creado, lo colocamos arriba
      if (res.data && res.data.id) {
        windowsList.value.unshift(res.data);
      } else {
        await loadMaintenanceWindows();
      }
      await inventoryStore.fetchRouters(true);

      // Cerrar modal y limpiar
      isCreateModalOpen.value = false;
      successMessage.value = 'Ventana de mantenimiento programada exitosamente.';
```

**`Target` en `onMounted` y Template (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
    expirationCheckTimer = setInterval(() => {
      const nowMs = Date.now();
      const hasExpired = windowsList.value.some((w) => {
        const endMs = new Date(w.ends_at).getTime();
        return !Number.isNaN(endMs) && endMs <= nowMs;
      });
      if (hasExpired) {
        void loadMaintenanceWindows();
      }
    }, 30000);
```

**`Replacement` en `onMounted` (`vue3/src/views/MaintenanceWindowsView.vue`):**
```ts
    expirationCheckTimer = setInterval(() => {
      const prevNow = nowMsRef.value;
      const nowMs = Date.now();
      nowMsRef.value = nowMs;
      const hasExpired = windowsList.value.some((w) => {
        const endMs = new Date(w.ends_at).getTime();
        return !Number.isNaN(endMs) && endMs <= nowMs;
      });
      const hasJustStarted = windowsList.value.some((w) => {
        const startMs = new Date(w.starts_at).getTime();
        return !w.is_cancelled && !Number.isNaN(startMs) && startMs > prevNow && startMs <= nowMs;
      });
      if (hasExpired) {
        void loadMaintenanceWindows();
        void inventoryStore.fetchRouters(true);
      } else if (hasJustStarted) {
        void inventoryStore.fetchRouters(true);
      }
    }, 15000);
```

**`Target` en Template y CSS de `vue3/src/views/MaintenanceWindowsView.vue`:**
```html
            <td>
              <span
                class="badge-status"
                :class="{
                  'badge-status--cancelled': w.is_cancelled,
                  'badge-status--active': !w.is_cancelled,
                }"
              >
                {{ w.is_cancelled ? 'Cancelada' : 'Programada' }}
              </span>
            </td>
```

**`Replacement` en Template de `vue3/src/views/MaintenanceWindowsView.vue`:**
```html
            <td>
              <span
                class="badge-status"
                :class="{
                  'badge-status--cancelled': w.is_cancelled,
                  'badge-status--in-progress': isWindowInProgress(w),
                  'badge-status--active': !w.is_cancelled && !isWindowInProgress(w),
                }"
              >
                {{ getWindowStatusLabel(w) }}
              </span>
            </td>
```

**`Target` en CSS de `vue3/src/views/MaintenanceWindowsView.vue`:**
```css
  .badge-status--active {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }

  .badge-status--cancelled {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
  }
```

**`Replacement` en CSS de `vue3/src/views/MaintenanceWindowsView.vue`:**
```css
  .badge-status--active {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }

  .badge-status--in-progress {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.45);
    font-weight: 700;
  }

  .badge-status--cancelled {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
  }
```

---

### Paso 4: Visibilidad de Equipos en Mantenimiento en la Pantalla Principal (`Centro de Mando` — `vue3/src/views/DashboardHomeView.vue`)

Editar `vue3/src/views/DashboardHomeView.vue` para:
1. Refrescar siempre `inventoryStore.fetchRouters()` al montar la vista (`onMounted`).
2. Incorporar la propiedad computada `maintenanceRouters` y descontar los equipos en mantenimiento de `onlineRouters` y `offlineRouters` (en paridad exacta con el Wallboard NOC).
3. Mostrar `● X en línea | ● Y mant. | ● Z desconectado` en la tarjeta KPI `FLOTA MIKROTIK`.
4. Mostrar el indicador ámbar `status-dot--maintenance` y la insignia `🛠️ MANTENIMIENTO` junto al nombre del equipo en la lista `Acceso Rápido a Equipos de la Flota`.

**`Target` en `vue3/src/views/DashboardHomeView.vue` (Script líneas 19–47):**
```ts
  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters(true);
    }
    inventoryStore.fetchNetworkRoles();
    nocStore.connectEventsWebSocket();
    if (!authStore.user || authStore.canUseUserFeature('AUDIT_LOGS_QUERY', false)) {
      nocStore.fetchRecentAuditLogs();
    }
  });

  // Métricas calculadas
  const totalRouters = computed(() => inventoryStore.routers.length);
  const onlineRouters = computed(
    () =>
      inventoryStore.routers.filter(
        (r) => r.is_reachable || r.operational_status === 'ONLINE' || r.syslog_active,
      ).length,
  );
  const offlineRouters = computed(
    () =>
      inventoryStore.routers.filter(
        (r) => !r.is_reachable && r.operational_status !== 'ONLINE' && !r.syslog_active,
      ).length,
  );
  const availabilityPct = computed(() => {
    if (totalRouters.value === 0) return 100;
    return Math.round((onlineRouters.value / totalRouters.value) * 100);
  });
```

**`Replacement` en `vue3/src/views/DashboardHomeView.vue` (Script):**
```ts
  onMounted(() => {
    inventoryStore.fetchRouters(inventoryStore.routers.length === 0);
    inventoryStore.fetchNetworkRoles();
    nocStore.connectEventsWebSocket();
    if (!authStore.user || authStore.canUseUserFeature('AUDIT_LOGS_QUERY', false)) {
      nocStore.fetchRecentAuditLogs();
    }
  });

  // Métricas calculadas
  const totalRouters = computed(() => inventoryStore.routers.length);
  const maintenanceRouters = computed(
    () => inventoryStore.routers.filter((r) => r.admin_state === 'MAINTENANCE').length,
  );
  const onlineRouters = computed(
    () =>
      inventoryStore.routers.filter(
        (r) =>
          r.admin_state !== 'MAINTENANCE' &&
          (r.is_reachable || r.operational_status === 'ONLINE' || r.syslog_active),
      ).length,
  );
  const offlineRouters = computed(
    () =>
      inventoryStore.routers.filter(
        (r) =>
          r.admin_state !== 'MAINTENANCE' &&
          !r.is_reachable &&
          r.operational_status !== 'ONLINE' &&
          !r.syslog_active,
      ).length,
  );
  const availabilityPct = computed(() => {
    const activePool = totalRouters.value - maintenanceRouters.value;
    if (activePool <= 0) return 100;
    return Math.round((onlineRouters.value / activePool) * 100);
  });
```

**`Target` en Template de `vue3/src/views/DashboardHomeView.vue` (KPI Strip líneas 300–305):**
```html
          <div class="kpi-micro-status">
            <span class="micro-online">● {{ onlineRouters }} {{ t('common.online').toLowerCase() }}</span>
            <span class="micro-sep">|</span>
            <span class="micro-offline">● {{ offlineRouters }} {{ t('common.offline').toLowerCase() }}</span>
          </div>
```

**`Replacement` en Template de `vue3/src/views/DashboardHomeView.vue` (KPI Strip):**
```html
          <div class="kpi-micro-status">
            <span class="micro-online">● {{ onlineRouters }} {{ t('common.online').toLowerCase() }}</span>
            <template v-if="maintenanceRouters > 0">
              <span class="micro-sep">|</span>
              <span class="micro-maintenance">🛠️ {{ maintenanceRouters }} mant.</span>
            </template>
            <span class="micro-sep">|</span>
            <span class="micro-offline">● {{ offlineRouters }} {{ t('common.offline').toLowerCase() }}</span>
          </div>
```

**`Target` en Template de `vue3/src/views/DashboardHomeView.vue` (Quick Routers List líneas 453–462):**
```html
              <div class="router-name-line">
                <span
                  class="status-dot-sm"
                  :class="r.is_reachable ? 'status-dot--online' : 'status-dot--offline'"
                  :title="r.is_reachable ? 'Online' : 'Offline'"
                ></span>
                <span class="router-name">{{ r.display_name }}</span>
                <span v-if="r.network_role" class="badge-role-sm">{{ t(`enums.network_role.${r.network_role}`, r.network_role) }}</span>
              </div>
```

**`Replacement` en Template de `vue3/src/views/DashboardHomeView.vue` (Quick Routers List):**
```html
              <div class="router-name-line">
                <span
                  class="status-dot-sm"
                  :class="
                    r.admin_state === 'MAINTENANCE'
                      ? 'status-dot--maintenance'
                      : r.is_reachable
                        ? 'status-dot--online'
                        : 'status-dot--offline'
                  "
                  :title="
                    r.admin_state === 'MAINTENANCE'
                      ? 'En Mantenimiento'
                      : r.is_reachable
                        ? 'Online'
                        : 'Offline'
                  "
                ></span>
                <span class="router-name">{{ r.display_name }}</span>
                <span v-if="r.admin_state === 'MAINTENANCE'" class="badge-maintenance-sm">
                  🛠️ MANTENIMIENTO
                </span>
                <span v-if="r.network_role" class="badge-role-sm">{{ t(`enums.network_role.${r.network_role}`, r.network_role) }}</span>
              </div>
```

**`Target` en CSS de `vue3/src/views/DashboardHomeView.vue`:**
```css
  .micro-online {
    color: #6ee7b7;
  }
  .micro-offline {
    color: #f87171;
  }
  .micro-sep {
    color: var(--rg-border-panel, #334155);
  }
```

**`Replacement` en CSS de `vue3/src/views/DashboardHomeView.vue`:**
```css
  .micro-online {
    color: #6ee7b7;
  }
  .micro-maintenance {
    color: #fbbf24;
    font-weight: 700;
  }
  .micro-offline {
    color: #f87171;
  }
  .micro-sep {
    color: var(--rg-border-panel, #334155);
  }
```

**`Target` en CSS de `.status-dot--offline` (`vue3/src/views/DashboardHomeView.vue`):**
```css
  .status-dot--offline {
    background: transparent;
    border: 2px solid var(--rg-status-critical, #ef4444);
  }

  .router-name {
```

**`Replacement` en CSS de `.status-dot--offline` (`vue3/src/views/DashboardHomeView.vue`):**
```css
  .status-dot--maintenance {
    background: #f59e0b;
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.45);
  }
  .status-dot--offline {
    background: transparent;
    border: 2px solid var(--rg-status-critical, #ef4444);
  }

  .badge-maintenance-sm {
    font-size: 0.62rem;
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 1px 6px;
    border-radius: 3px;
    font-weight: 700;
    font-family: var(--rg-font-mono, monospace);
  }

  .router-name {
```

---

### Paso 5: Clasificación Precisa de Eventos, Ocultación de UUIDs Crudos y Filtro de Mapa `MAINTENANCE` en `vue3/src/utils/eventFormatter.ts`, `vue3/src/views/NocWallboardView.vue` y `vue3/src/components/network/UnifiedNetworkMap.vue`

1. En `vue3/src/utils/eventFormatter.ts`, añadir `SESSION_TOKEN_RENEWED` y `MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED`, y sanitizar UUIDs crudos en `formatEventMessage`:

**`Target` en `vue3/src/utils/eventFormatter.ts`:**
```ts
  LOGIN_SUCCESSFUL: 'Inicio de sesión exitoso',
  '2FA_VERIFICATION_FAILED': 'Fallo en verificación de segundo factor (2FA)',
  SESSION_KILLED_DUPLICATE_LOGIN: 'Sesión finalizada por ingreso concurrente',

  // Caídas, Disponibilidad y Alertas Masivas (docs/specs/32)
  MASS_OUTAGE_TRIGGERED: 'Alerta de caída masiva activada',
  MASS_OUTAGE_DETECTED: 'Caída masiva detectada en la red',
  ROUTER_DOWN: 'Router fuera de línea (sin respuesta)',
  ROUTER_UP: 'Router restablecido y operativo',
  ROUTER_REBOOT_TRIGGERED: 'Reinicio remoto de equipo ejecutado',
  HIGH_CPU: 'Alerta de consumo elevado de CPU',
  SSL_MISMATCH: 'Discrepancia en huella criptográfica SSL (TOFU)',
  MAINTENANCE: 'Ventana de mantenimiento programada',
  MAINTENANCE_WINDOW_CREATED: 'Ventana de mantenimiento creada',
  MAINTENANCE_WINDOW_CANCELLED: 'Ventana de mantenimiento cancelada',
```

**`Replacement` en `vue3/src/utils/eventFormatter.ts`:**
```ts
  LOGIN_SUCCESSFUL: 'Inicio de sesión exitoso',
  SESSION_TOKEN_RENEWED: 'Sesión de operador renovada',
  '2FA_VERIFICATION_FAILED': 'Fallo en verificación de segundo factor (2FA)',
  SESSION_KILLED_DUPLICATE_LOGIN: 'Sesión finalizada por ingreso concurrente',

  // Caídas, Disponibilidad y Alertas Masivas (docs/specs/32)
  MASS_OUTAGE_TRIGGERED: 'Alerta de caída masiva activada',
  MASS_OUTAGE_DETECTED: 'Caída masiva detectada en la red',
  ROUTER_DOWN: 'Router fuera de línea (sin respuesta)',
  ROUTER_UP: 'Router restablecido y operativo',
  ROUTER_REBOOT_TRIGGERED: 'Reinicio remoto de equipo ejecutado',
  HIGH_CPU: 'Alerta de consumo elevado de CPU',
  SSL_MISMATCH: 'Discrepancia en huella criptográfica SSL (TOFU)',
  MAINTENANCE: 'Ventana de mantenimiento programada',
  MAINTENANCE_WINDOW_CREATED: 'Ventana de mantenimiento creada',
  MAINTENANCE_WINDOW_CANCELLED: 'Ventana de mantenimiento cancelada',
  MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED: 'Ventana de mantenimiento finalizada',
```

**`Target` al final de `vue3/src/utils/eventFormatter.ts`:**
```ts
export function formatEventMessage(
  action: string | null | undefined,
  actor?: string | null,
): string {
  const actionText = formatEventAction(action);
  const normalizedActor = (actor || '').trim();

  if (!normalizedActor || normalizedActor.toLowerCase() === 'sistema' || normalizedActor.toLowerCase() === 'system') {
    return actionText;
  }

  return `${actionText} (por ${normalizedActor})`;
}
```

**`Replacement` al final de `vue3/src/utils/eventFormatter.ts`:**
```ts
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isRawUuid(val: string | null | undefined): boolean {
  if (!val || typeof val !== 'string') return false;
  return UUID_V4_REGEX.test(val.trim());
}

export function formatEventMessage(
  action: string | null | undefined,
  actor?: string | null,
): string {
  const actionText = formatEventAction(action);
  const normalizedActor = (actor || '').trim();

  if (
    !normalizedActor ||
    normalizedActor.toLowerCase() === 'sistema' ||
    normalizedActor.toLowerCase() === 'system' ||
    isRawUuid(normalizedActor)
  ) {
    return actionText;
  }

  return `${actionText} (por ${normalizedActor})`;
}
```

2. En `vue3/src/views/NocWallboardView.vue`, corregir la clasificación de tipos de evento (`determineEventType` y `loadEvents`), evitar mostrar UUIDs crudos como `router_identity` y resaltar la tarjeta KPI `MANTENIMIENTO` cuando `maintenanceRouters > 0`:

**`Target` en `vue3/src/views/NocWallboardView.vue` (líneas 12–26):**
```ts
  import { formatEventAction, formatEventMessage } from '@/utils/eventFormatter';

  const router = useRouter();
  const nocEventsStore = useNocEventsStore();
  const { t } = useI18n();

  interface NocEvent {
    id: string;
    timestamp: string;
    type: 'ROUTER_DOWN' | 'ROUTER_UP' | 'HIGH_CPU' | 'SSL_MISMATCH' | 'MAINTENANCE';
    router_identity: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
  }
```

**`Replacement` en `vue3/src/views/NocWallboardView.vue`:**
```ts
  import { formatEventAction, formatEventMessage, isRawUuid } from '@/utils/eventFormatter';

  const router = useRouter();
  const nocEventsStore = useNocEventsStore();
  const { t } = useI18n();

  interface NocEvent {
    id: string;
    timestamp: string;
    type: 'ROUTER_DOWN' | 'ROUTER_UP' | 'HIGH_CPU' | 'SSL_MISMATCH' | 'MAINTENANCE' | 'BACKUP' | 'OPERATION';
    router_identity: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
  }
```

**`Target` en `determineEventType`, `loadEvents` y `getBadgeLabel` (`vue3/src/views/NocWallboardView.vue`):**
```ts
  function determineEventType(name: string): NocEvent['type'] {
    if (name.includes('DOWN')) return 'ROUTER_DOWN';
    if (name.includes('UP')) return 'ROUTER_UP';
    return 'MAINTENANCE';
  }
```

**`Replacement` en `determineEventType` (`vue3/src/views/NocWallboardView.vue`):**
```ts
  function determineEventType(name: string, category?: string): NocEvent['type'] {
    const upper = (name || '').toUpperCase();
    if (upper.includes('DOWN') || upper.includes('OUTAGE')) return 'ROUTER_DOWN';
    if (upper.includes('MAINTENANCE')) return 'MAINTENANCE';
    if (upper.includes('BACKUP')) return 'BACKUP';
    if (upper.includes('SSL') || upper.includes('TOFU')) return 'SSL_MISMATCH';
    if (upper.includes('CPU')) return 'HIGH_CPU';
    if (upper.includes('UP') || category === 'AUTH') return 'ROUTER_UP';
    return 'OPERATION';
  }
```

**`Target` en `loadEvents` y `getBadgeLabel` (`vue3/src/views/NocWallboardView.vue`):**
```ts
      liveEvents.value = items.slice(0, 20).map((log) => ({
        id: String(log.id),
        timestamp: log.created_at
          ? new Date(log.created_at as string).toLocaleTimeString()
          : new Date().toLocaleTimeString(),
        type:
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED'
            ? 'ROUTER_DOWN'
            : log.event_category === 'AUTH'
              ? 'ROUTER_UP'
              : 'MAINTENANCE',
        router_identity: (log.router_display_name as string) || (log.actor_username as string) || 'Sistema',
        message: formatEventMessage(log.event_action as string, log.actor_username as string),
        severity:
          log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
          log.event_action === 'MASS_OUTAGE_DETECTED'
            ? 'critical'
            : Number(log.status_code || 0) >= 400
              ? 'critical'
              : 'info',
      }));
```

**`Replacement` en `loadEvents` (`vue3/src/views/NocWallboardView.vue`):**
```ts
      liveEvents.value = items.slice(0, 20).map((log) => {
        const rawRouterName = (log.router_display_name as string) || '';
        const rawActor = (log.actor_username as string) || '';
        const cleanIdentity =
          rawRouterName && !isRawUuid(rawRouterName)
            ? rawRouterName
            : rawActor && !isRawUuid(rawActor)
              ? rawActor
              : 'Sistema';
        return {
          id: String(log.id),
          timestamp: log.created_at
            ? new Date(log.created_at as string).toLocaleTimeString()
            : new Date().toLocaleTimeString(),
          type: determineEventType(log.event_action as string, log.event_category as string),
          router_identity: cleanIdentity,
          message: formatEventMessage(log.event_action as string, rawActor),
          severity:
            log.event_action === 'MASS_OUTAGE_TRIGGERED' ||
            log.event_action === 'MASS_OUTAGE_DETECTED'
              ? 'critical'
              : Number(log.status_code || 0) >= 400
                ? 'critical'
                : String(log.event_action || '').includes('MAINTENANCE')
                  ? 'warning'
                  : 'info',
        };
      });
```

**`Target` en `getBadgeLabel` (`vue3/src/views/NocWallboardView.vue`):**
```ts
      case 'MAINTENANCE':
        return 'MANTENIMIENTO';
      default:
        return formatEventAction(type);
```

**`Replacement` en `getBadgeLabel` (`vue3/src/views/NocWallboardView.vue`):**
```ts
      case 'MAINTENANCE':
        return 'MANTENIMIENTO';
      case 'BACKUP':
        return 'RESPALDO';
      case 'OPERATION':
        return 'OPERACIÓN';
      default:
        return formatEventAction(type);
```

3. En `vue3/src/components/network/UnifiedNetworkMap.vue`, añadir `<option value="MAINTENANCE">` al filtro de estado del mapa, filtrar `props.routers` según `statusFilter` y evitar que un router en `MAINTENANCE` dispare falsamente la alerta roja `🚨 ALERTA RCA: CAÍDA DE ROUTER PRINCIPAL`:

**`Target` en `vue3/src/components/network/UnifiedNetworkMap.vue` (líneas 97–122):**
```ts
  // Filtro de estado
  const statusFilter = ref<'ALL' | 'ONLINE' | 'OFFLINE'>('ALL');
```

**`Replacement` en `vue3/src/components/network/UnifiedNetworkMap.vue`:**
```ts
  // Filtro de estado
  const statusFilter = ref<'ALL' | 'ONLINE' | 'OFFLINE' | 'MAINTENANCE'>('ALL');
```

**`Target` en `downRouters` (`vue3/src/components/network/UnifiedNetworkMap.vue` líneas 117–121):**
```ts
  const downRouters = computed<RouterItem[]>(() => {
    return props.routers.filter(
      (r) => !r.is_reachable || r.admin_state === 'DECOMMISSIONED' || r.admin_state === 'MAINTENANCE',
    );
  });
```

**`Replacement` en `downRouters` (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
  const downRouters = computed<RouterItem[]>(() => {
    return props.routers.filter(
      (r) => (!r.is_reachable && r.admin_state !== 'MAINTENANCE') || r.admin_state === 'DECOMMISSIONED',
    );
  });
```

**`Target` en `renderAllLayers` y `<select v-model="statusFilter">` (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
    // 1. Capa de Routers de Red (con soporte para Sitios Compartidos / Co-ubicados)
    if (showRouters.value && routersLayer) {
      const groups = buildLocationGroups(props.routers);
```

**`Replacement` en `renderAllLayers` (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
    // 1. Capa de Routers de Red (con soporte para Sitios Compartidos / Co-ubicados)
    if (showRouters.value && routersLayer) {
      const filteredMapRouters = props.routers.filter((r) => {
        if (statusFilter.value === 'MAINTENANCE') return r.admin_state === 'MAINTENANCE';
        if (statusFilter.value === 'ONLINE') return r.is_reachable && r.admin_state !== 'MAINTENANCE';
        if (statusFilter.value === 'OFFLINE') return !r.is_reachable && r.admin_state !== 'MAINTENANCE';
        return true;
      });
      const groups = buildLocationGroups(filteredMapRouters);
```

**`Target` en `<select v-model="statusFilter">` (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```html
      <div class="filter-controls-group">
        <select v-model="statusFilter" class="rg-select-filter" aria-label="Filtrar por estado">
          <option value="ALL">{{ t('network_map.filter_all') }}</option>
          <option value="ONLINE">{{ t('network_map.filter_online') }}</option>
          <option value="OFFLINE">{{ t('network_map.filter_offline') }}</option>
        </select>
      </div>
```

**`Replacement` en `<select v-model="statusFilter">` (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```html
      <div class="filter-controls-group">
        <select v-model="statusFilter" class="rg-select-filter" aria-label="Filtrar por estado">
          <option value="ALL">{{ t('network_map.filter_all') }}</option>
          <option value="ONLINE">{{ t('network_map.filter_online') }}</option>
          <option value="MAINTENANCE">{{ t('enums.admin_state.MAINTENANCE', 'En Mantenimiento') }}</option>
          <option value="OFFLINE">{{ t('network_map.filter_offline') }}</option>
        </select>
      </div>
```

---

### Paso 6: Botón Táctico `[ 🔄 Refrescar ]` en `NocWallboardView.vue` (`/noc-wallboard`) y Auto-Refresco Periódico (30s) + Botón `[ 🔄 Refrescar ]` en `SubscribersMapView.vue` (`/subscribers/map`)

1. En `vue3/src/views/NocWallboardView.vue`, permitir que `performAutoRefresh(forceProbe = false)` y `loadRouters(forceProbe = false)` acepten el parámetro opcional `forceProbe` (`?refresh=true`), e incorporar el botón **`[ 🔄 Refrescar ]`** (`#btn-wallboard-refresh`) junto al botón `[ Modo TV ]` en `.wallboard-header`:

**`Target` en `performAutoRefresh` (`vue3/src/views/NocWallboardView.vue` líneas 141–149):**
```ts
  async function performAutoRefresh() {
    if (isRefreshing.value) return;
    isRefreshing.value = true;
    try {
      await Promise.allSettled([loadRouters(), loadOpticalBoxes(), loadSubscribers(), loadEvents()]);
    } finally {
      isRefreshing.value = false;
    }
  }
```

**`Replacement` en `performAutoRefresh` (`vue3/src/views/NocWallboardView.vue`):**
```ts
  async function performAutoRefresh(forceProbe = false) {
    if (isRefreshing.value) return;
    isRefreshing.value = true;
    try {
      await Promise.allSettled([
        loadRouters(forceProbe),
        loadOpticalBoxes(),
        loadSubscribers(),
        loadEvents(),
      ]);
    } finally {
      isRefreshing.value = false;
    }
  }
```

**`Target` en `loadRouters` (`vue3/src/views/NocWallboardView.vue` líneas 197–202):**
```ts
  async function loadRouters() {
    try {
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>(
        '/api/v1/inventory/routers',
      );
```

**`Replacement` en `loadRouters` (`vue3/src/views/NocWallboardView.vue`):**
```ts
  async function loadRouters(forceProbe = false) {
    try {
      const url = forceProbe ? '/api/v1/inventory/routers?refresh=true' : '/api/v1/inventory/routers';
      const res = await http.get<RouterItem[] | { items: RouterItem[] }>(url);
```

**`Target` en `.wallboard-header` (`vue3/src/views/NocWallboardView.vue` líneas 425–433):**
```html
      <button
        type="button"
        class="btn-fullscreen"
        :aria-label="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa NOC'"
        @click="toggleFullscreen"
      >
        {{ isFullscreen ? t('wallboard.exit_tv') : t('wallboard.mode_tv') }}
      </button>
    </header>
```

**`Replacement` en `.wallboard-header` (`vue3/src/views/NocWallboardView.vue`):**
```html
      <div class="wallboard-header-actions">
        <button
          id="btn-wallboard-refresh"
          type="button"
          class="btn-wallboard-refresh"
          :disabled="isRefreshing"
          aria-label="Refrescar estado del Wallboard NOC"
          @click="performAutoRefresh(true)"
        >
          {{ isRefreshing ? '⏳ Refrescando...' : '🔄 Refrescar' }}
        </button>
        <button
          type="button"
          class="btn-fullscreen"
          :aria-label="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa NOC'"
          @click="toggleFullscreen"
        >
          {{ isFullscreen ? t('wallboard.exit_tv') : t('wallboard.mode_tv') }}
        </button>
      </div>
    </header>
```

**`Target` en CSS de `.btn-fullscreen` (`vue3/src/views/NocWallboardView.vue` líneas 795–805):**
```css
  .btn-fullscreen {
    background: #1f2937;
    border: 1px solid #4b5563;
    color: #f3f4f6;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
```

**`Replacement` en CSS de `.btn-fullscreen` (`vue3/src/views/NocWallboardView.vue`):**
```css
  .wallboard-header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-wallboard-refresh {
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-wallboard-refresh:hover:not(:disabled) {
    background: rgba(56, 189, 248, 0.25);
    color: #fff;
  }

  .btn-wallboard-refresh:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-fullscreen {
    background: #1f2937;
    border: 1px solid #4b5563;
    color: #f3f4f6;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
```

2. En `vue3/src/views/SubscribersMapView.vue` (`/subscribers/map`), incorporar auto-refresco periódico cada **30 segundos** (`mapAutoRefreshTimer`) y el botón **`[ 🔄 Refrescar ]`** (`#btn-subscribers-map-refresh`) junto a `[ 🔄 Sincronizar Clientes DHCP ]`:

**`Target` en `vue3/src/views/SubscribersMapView.vue` (líneas 4–6 y 325–332):**
```ts
  import { ref, computed, onMounted, watch } from 'vue';
```

**`Replacement` en `vue3/src/views/SubscribersMapView.vue` (líneas 4–6):**
```ts
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
```

**`Target` en `onMounted` (`vue3/src/views/SubscribersMapView.vue` líneas 325–332):**
```ts
  onMounted(async () => {
    await Promise.all([
      loadSubscriberDevices(),
      loadRouters(),
      isIspMode.value ? fieldStore.fetchOpticalBoxes() : Promise.resolve(),
    ]);
  });
```

**`Replacement` en `onMounted` (`vue3/src/views/SubscribersMapView.vue`):**
```ts
  const isRefreshingMap = ref<boolean>(false);
  let mapAutoRefreshTimer: ReturnType<typeof setInterval> | null = null;

  async function handleRefreshSubscribersMap(): Promise<void> {
    if (isRefreshingMap.value) return;
    isRefreshingMap.value = true;
    try {
      await Promise.allSettled([
        loadSubscriberDevices(),
        loadRouters(),
        isIspMode.value ? fieldStore.fetchOpticalBoxes() : Promise.resolve(),
      ]);
    } finally {
      isRefreshingMap.value = false;
    }
  }

  onMounted(async () => {
    await handleRefreshSubscribersMap();
    mapAutoRefreshTimer = setInterval(() => {
      void handleRefreshSubscribersMap();
    }, 30000);
  });

  onUnmounted(() => {
    if (mapAutoRefreshTimer !== null) {
      clearInterval(mapAutoRefreshTimer);
      mapAutoRefreshTimer = null;
    }
  });
```

**`Target` en `.sync-actions` (`vue3/src/views/SubscribersMapView.vue` líneas 459–473):**
```html
      <!-- Acciones de Sincronización Bimodal -->
      <div class="sync-actions">
        <!-- Botón Modo Empresa / Común: Sincronizar leases DHCP reales desde MikroTik -->
        <button
          type="button"
          class="btn-sync-dhcp"
          :disabled="isSyncingDhcp"
          aria-label="Sincronizar Dispositivos DHCP"
          @click="handleSyncDhcpClients"
        >
          <span v-if="isSyncingDhcp">⏳</span>
          <span v-else>🔄</span>
          {{ isSyncingDhcp ? t('subscribers_map.syncing_dhcp') : t('subscribers_map.btn_sync_dhcp') }}
        </button>
      </div>
```

**`Replacement` en `.sync-actions` (`vue3/src/views/SubscribersMapView.vue`):**
```html
      <!-- Acciones de Sincronización Bimodal -->
      <div class="sync-actions">
        <button
          id="btn-subscribers-map-refresh"
          type="button"
          class="btn-sync-dhcp"
          :disabled="isRefreshingMap"
          aria-label="Refrescar datos del mapa"
          @click="handleRefreshSubscribersMap"
        >
          <span v-if="isRefreshingMap">⏳</span>
          <span v-else>🔄</span>
          {{ isRefreshingMap ? 'Refrescando...' : 'Refrescar' }}
        </button>
        <!-- Botón Modo Empresa / Común: Sincronizar leases DHCP reales desde MikroTik -->
        <button
          type="button"
          class="btn-sync-dhcp"
          :disabled="isSyncingDhcp"
          aria-label="Sincronizar Dispositivos DHCP"
          @click="handleSyncDhcpClients"
        >
          <span v-if="isSyncingDhcp">⏳</span>
          <span v-else>🔄</span>
          {{ isSyncingDhcp ? t('subscribers_map.syncing_dhcp') : t('subscribers_map.btn_sync_dhcp') }}
        </button>
      </div>
```

---

## 3. Aseguramiento de Calidad Level-11X y Nuevo Criterio Anti-Silo (Regla Cero)

1. **Actualización de Suite Unitaria Frontend (`vue3/src/views/inventory/maintenanceWindowsView.unit.ts`):**
   - Debido a que ahora `MaintenanceWindowsView.vue` invoca `inventoryStore.fetchRouters(true)` al expirar una ventana o cancelar/crear una ventana (para sincronizar en tiempo real el `admin_state` en el Centro de Mando y Wallboard), actualizar `vue3/src/views/inventory/maintenanceWindowsView.unit.ts` para espiar `inventoryStore.fetchRouters` y certificar las **3 fases temporales** (`⏳ Programada`, `🛠️ En Curso` y `Expirada/Purgada`):

**`Target` en `vue3/src/views/inventory/maintenanceWindowsView.unit.ts` (líneas 44–46 y 335–353):**
```ts
    const inventoryStore = useInventoryStore();
    inventoryStore.setRouters([SAMPLE_ROUTER_1, SAMPLE_ROUTER_2]);
```

**`Replacement` en `vue3/src/views/inventory/maintenanceWindowsView.unit.ts` (líneas 44–46):**
```ts
    const inventoryStore = useInventoryStore();
    inventoryStore.setRouters([SAMPLE_ROUTER_1, SAMPLE_ROUTER_2]);
    vi.spyOn(inventoryStore, 'fetchRouters').mockResolvedValue();
```

**`Target` en `vue3/src/views/inventory/maintenanceWindowsView.unit.ts` (líneas 335–353):**
```ts
    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    // La ventana ya expirada no debe mostrarse, pero la próxima a expirar sí
    expect(wrapper.text()).toContain('Ventana Próxima a Expirar');
    expect(wrapper.text()).not.toContain('Ventana Ya Expirada');
```

**`Replacement` en `vue3/src/views/inventory/maintenanceWindowsView.unit.ts` (líneas 335–353):**
```ts
    const wrapper = mount(MaintenanceWindowsView);
    await flushPromises();

    // La ventana ya expirada no debe mostrarse, pero la próxima a expirar sí y en estado En Curso
    expect(wrapper.text()).toContain('Ventana Próxima a Expirar');
    expect(wrapper.text()).toContain('En Curso');
    expect(wrapper.text()).not.toContain('Ventana Ya Expirada');
```

2. **Pruebas de Propagación Transversal sin Mocks Intermedios (*Cross-Module State Propagation*) y Auditoría Anti-UUID Crudo en Backend (`fastapi/tests/`):**
   - En `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py`:
     - Certificar el flujo cruzado completo **sin mocks intermedios**: crear una `MaintenanceWindow` activa (`starts_at <= now_utc <= ends_at`, `is_cancelled == False`) para un router con `admin_state == PRODUCTION` $\rightarrow$ invocar `list_routers` (`GET /api/v1/inventory/routers`) y `get_router` (`GET /api/v1/inventory/routers/{id}`) $\rightarrow$ verificar que ambos retornan `admin_state == "MAINTENANCE"` $\rightarrow$ cancelar o expirar la ventana $\rightarrow$ verificar que `list_routers` retorna automáticamente `admin_state == "PRODUCTION"`.
     - Certificar en `test_audit_log` que `write_audit_log` resuelve `actor_username` desde `User.username` y `router_display_name` desde `Router.display_name` cuando recibe un UUID crudo en `actor_username`, garantizando 0 UUIDs crudos en la Cinta de Eventos Críticos.
3. **Ejecución en Contenedor Docker Efímero (`Rule Zero`):**
   - Ejecutar `docker compose -f vue3/docker-compose.qa.yml run --rm --T vue3-qa npx vitest run` y `docker compose -f fastapi/docker-compose.qa.yml run --rm -T fastapi-qa pytest` certificando 100% de aprobación.
