# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 89: Persistencia Real del Emparejamiento IPv4 de Abonados en `/ipam` (`selectinload` + `populate_existing`) y Respaldo Simultáneo Multi-Equipo por Lote (`POST /api/v1/backups/batch-trigger`) con Selección por Casillas en `/backups`

**Estado:** Completada y Certificada en Docker Efímero (QA 11X)  
**Hito Asociado:** Hito 30.12  
**Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
**Archivos Afectados:**
- `fastapi/src/api/v1/ipam.py`
- `fastapi/src/api/v1/subscribers.py`
- `fastapi/src/schemas/backups.py`
- `fastapi/src/api/v1/backups.py`
- `fastapi/src/api/router.py`
- `vue3/src/views/RscGitDiffViewer.vue`
- `fastapi/tests/api/test_subscribers.unit.py`
- `fastapi/tests/api/test_operations_endpoints_full.unit.py`
- `vue3/src/views/operationsViews.unit.ts`
- `fastapi/test/api_test.feature` (+ réplicas en `docs/examples/fastapi/`)
- `vue3/test/ui_business_flow.feature` (+ réplicas en `docs/examples/vue3/`)

---

## 1. Diagnóstico Forense de las 2 Necesidades Operativas

### 1.1 Causa Raíz 1: Al Emparejar un Abonado con una IP en `/ipam` (`🔗 Emparejar`), la Tabla Sigue Mostrando `⚠️ Sin IP emparejada`
1. En `fastapi/src/models/ipam.py` (líneas 364–371), la propiedad `SubscriberDevice.assigned_ipv4` evita errores `MissingGreenlet` en sesiones asíncronas leyendo exclusivamente del diccionario precargado en memoria:
   ```python
   @property
   def assigned_ipv4(self) -> Optional[str]:
       if hasattr(self, "_assigned_ipv4_cache") and self._assigned_ipv4_cache:
           return self._assigned_ipv4_cache
       ip_obj = self.__dict__.get("ipv4_address")
       if ip_obj is not None and getattr(ip_obj, "address", None):
           return str(ip_obj.address).split("/")[0]
       return None
   ```
2. En `vue3/src/views/IpamManagementView.vue` (líneas 196–215), cuando el usuario pulsa **`🔗 Emparejar`** y guarda (`handleSavePairSubscriber()`):
   - Primero ejecuta `await ipamStore.pairSubscriberNetwork(selectedSubForPair.value.id, ...)` (`PATCH /api/v1/subscriber-devices/{device_id}`).
   - **Inmediatamente después** (línea 215), ejecuta `await ipamStore.fetchCustomerServices()`, el cual llama a `GET /api/v1/ipam/customer-services` (`list_customer_services` en `fastapi/src/api/v1/ipam.py`, línea 394).
3. En `fastapi/src/api/v1/ipam.py` (línea 394), `list_customer_services` ejecutaba:
   ```python
   stmt = select(CustomerService).where(CustomerService.tenant_id == tenant_id)
   ```
   **¡sin `.options(selectinload(CustomerService.ipv4_address))`!**
   Por consiguiente, `self.__dict__.get("ipv4_address")` era siempre `None` al serializar `GET /api/v1/ipam/customer-services`, sobrescribiendo el estado de Pinia con `assigned_ipv4: null` y haciendo que la fila volviera a mostrar **`⚠️ Sin IP emparejada`**.
4. Adicionalmente:
   - En `update_subscriber_device` (`fastapi/src/api/v1/subscribers.py`, líneas 1253–1339), dado que `async_session_maker` tiene `expire_on_commit=False`, cuando `device` se carga inicialmente sin IP (`device.__dict__["ipv4_address"] = None`) y luego se asigna `device.ipv4_address_id = resolved_ip_id`, el `stmt_reload` posterior no actualizaba la relación en el *identity map* si no llevaba `.execution_options(populate_existing=True)` y asignación explícita `device.assigned_ipv4 = ...`.
   - En `create_customer_service` (`POST /api/v1/ipam/customer-services` en `fastapi/src/api/v1/ipam.py`, líneas 405–466), si el operador registraba un abonado indicando `assigned_ipv4` en texto, no se invocaba `_resolve_or_create_subscriber_ipv4` ni se precargaba `ipv4_address`.

### 1.2 Necesidad Operativa 2: Respaldo Simultáneo Multi-Equipo (`Batch Backup`) mediante Lista con Casillas de Selección en `/backups` (`RscGitDiffViewer.vue`)
- Actualmente, en `/backups` (`RscGitDiffViewer.vue`), el botón **`+ Crear Respaldo Ahora`** solo permite respaldar 1 router a la vez (`POST /api/v1/routers/{router_id}/backups/trigger`).
- Se requiere un botón **`📦 Respaldo Múltiple`** (`#btn-open-batch-backup`) en la cabecera de `/backups` que abra un modal con la lista de routers del tenant, casillas de verificación (`checkbox`), filtros rápidos (**`☑ Seleccionar Todos`**, **`🟢 Solo Online`**, **`✕ Limpiar`**) y ejecución simultánea contra `POST /api/v1/backups/batch-trigger` con deduplicación SHA-256, cifrado AES-256-GCM y resumen de resultados por equipo.

---

## 2. Instrucciones Paso a Paso para Implementación (Gemini 3.8 Flash High)

### Paso 1: Corregir `list_customer_services` y `create_customer_service` en `fastapi/src/api/v1/ipam.py` y `update_subscriber_device` en `fastapi/src/api/v1/subscribers.py`

#### 1.A. Modificar `list_customer_services` y `create_customer_service` en `fastapi/src/api/v1/ipam.py` (líneas 385–466)
1. Importar `_resolve_or_create_subscriber_ipv4` desde `src.api.v1.subscribers` (o invocarlo dentro de `create_customer_service`).
2. En `list_customer_services`, añadir `.options(selectinload(CustomerService.ipv4_address))`:
```python
@router.get("/customer-services", response_model=list[CustomerServiceResponse])
async def list_customer_services(
    router_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[CustomerServiceStatusEnum] = Query(None),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista todos los abonados (PPPoE, DHCP o Estáticos) del ISP precargando su IPv4 emparejada."""
    tenant_id = get_tenant_id(claims)
    stmt = (
        select(CustomerService)
        .options(selectinload(CustomerService.ipv4_address))
        .where(CustomerService.tenant_id == tenant_id)
    )
    if router_id:
        stmt = stmt.where(CustomerService.router_id == router_id)
    if status_filter:
        stmt = stmt.where(CustomerService.status == status_filter)

    stmt = stmt.order_by(CustomerService.endpoint_identifier.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
```
3. En `create_customer_service` (`fastapi/src/api/v1/ipam.py`, líneas 429–466), resolver `payload.assigned_ipv4` cuando se proporcione y recargar con `selectinload(CustomerService.ipv4_address)`:
```python
    resolved_ipv4_id = payload.ipv4_address_id
    if not resolved_ipv4_id and payload.assigned_ipv4:
        from src.api.v1.subscribers import _resolve_or_create_subscriber_ipv4

        resolved_ipv4_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=payload.router_id,
            raw_ipv4=payload.assigned_ipv4,
            mac_address=payload.onu_mac_address,
            description=f"Abonado FTTH {endpoint_val}",
        )

    svc = CustomerService(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        endpoint_identifier=endpoint_val,
        ipv4_address_id=resolved_ipv4_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        bandwidth_profile_id=payload.bandwidth_profile_id,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        device_serial=payload.device_serial or payload.onu_serial_number,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=payload.optical_box,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=CustomerServiceStatusEnum.PENDING_INSTALL,
        last_reachability_status="ONLINE",
    )
    if payload.assigned_ipv4:
        svc.assigned_ipv4 = payload.assigned_ipv4.strip().split("/")[0].strip()
    db.add(svc)
    await db.commit()

    stmt_reload = (
        select(CustomerService)
        .options(selectinload(CustomerService.ipv4_address))
        .where(CustomerService.id == svc.id)
        .execution_options(populate_existing=True)
    )
    reloaded = (await db.execute(stmt_reload)).scalar_one_or_none()
    if reloaded is not None:
        svc = reloaded
```

#### 1.B. Blindar `update_subscriber_device` en `fastapi/src/api/v1/subscribers.py` (líneas 1280–1340)
En `update_subscriber_device`:
1. Cuando `raw_assigned_ipv4` resuelve `resolved_ip_id`, asignar también `device.assigned_ipv4 = raw_assigned_ipv4.strip().split("/")[0].strip()`.
2. En `stmt_reload`, añadir `.execution_options(populate_existing=True)` y preservar `clean_paired_ip`:
```python
    raw_assigned_ipv4 = update_dict.pop("assigned_ipv4", None)
    clean_paired_ip: Optional[str] = None
    if raw_assigned_ipv4:
        clean_paired_ip = raw_assigned_ipv4.strip().split("/")[0].strip()
        resolved_ip_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=device.router_id,
            raw_ipv4=raw_assigned_ipv4,
            mac_address=update_dict.get("onu_mac_address") or device.onu_mac_address,
            description=f"Abonado FTTH {update_dict.get('endpoint_identifier') or device.endpoint_identifier}",
        )
        if resolved_ip_id:
            device.ipv4_address_id = resolved_ip_id
        if clean_paired_ip:
            device.assigned_ipv4 = clean_paired_ip
```
y en la recarga posterior al `await db.commit()` (líneas 1333–1339):
```python
    stmt_reload = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.ipv4_address))
        .where(SubscriberDevice.id == device.id)
        .execution_options(populate_existing=True)
    )
    device = (await db.execute(stmt_reload)).scalar_one()
    if clean_paired_ip and not device.assigned_ipv4:
        device.assigned_ipv4 = clean_paired_ip
```

---

### Paso 2: Implementar Respaldo Simultáneo por Lote (`POST /api/v1/backups/batch-trigger`) en Backend

#### 2.A. Añadir esquemas en `fastapi/src/schemas/backups.py`
Al final de `fastapi/src/schemas/backups.py`, agregar:
```python
class BatchBackupTriggerRequest(StrictBaseModel):
    router_ids: list[uuid.UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de UUIDs de routers a respaldar simultáneamente",
    )


class BatchBackupRouterResult(StrictBaseModel):
    router_id: uuid.UUID
    display_name: str
    ip_address: str | None = None
    status: str  # CREATED | IDENTICAL_SKIPPED_DEDUPLICATED | FAILED
    backup_id: uuid.UUID | None = None
    rsc_sha256_hash: str | None = None
    message: str


class BatchBackupTriggerResponse(StrictBaseModel):
    total_requested: int
    created_count: int
    deduplicated_count: int
    failed_count: int
    results: list[BatchBackupRouterResult] = Field(default_factory=list)
```

#### 2.B. Implementar `batch_backups_router` y `_trigger_single_router_backup_record` en `fastapi/src/api/v1/backups.py`
1. Importar `BatchBackupRouterResult`, `BatchBackupTriggerRequest` y `BatchBackupTriggerResponse` desde `src.schemas.backups`.
2. Declarar debajo de `router = APIRouter(...)` (línea 37):
   ```python
   batch_backups_router = APIRouter(prefix="/backups", tags=["Backups & Diff"])
   ```
3. Extraer la lógica común de creación/deduplicación de respaldo en un helper `_execute_router_backup_core` (para mantener complejidad ciclomática Radon Grado A `CC <= 5`) y exponer `POST /api/v1/backups/batch-trigger`:
```python
async def _execute_router_backup_core(
    router_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    actor_username: str,
    actor_role: str,
    actor_ip: str,
    claims: dict[str, Any],
    db: AsyncSession,
) -> tuple[ Any, BackupTriggerResponse ]:
    """Ejecuta la exportación .rsc, deduplicación SHA-256, cifrado AES-GCM y registro WORM para un router."""
    router_obj, client = await get_router_and_client(router_id, claims, db)
    cleaned_rsc = await export_router_rsc(client)
    rsc_hash = hashlib.sha256(cleaned_rsc.encode("utf-8")).hexdigest()
    now_utc = datetime.now(UTC)

    latest_stmt = (
        select(RouterBackup)
        .where(RouterBackup.tenant_id == tenant_id, RouterBackup.router_id == router_id)
        .order_by(desc(RouterBackup.created_at))
        .limit(1)
    )
    latest_backup = (await db.execute(latest_stmt)).scalar_one_or_none()

    if latest_backup and latest_backup.rsc_sha256_hash == rsc_hash:
        latest_backup.last_verified_identical_at = now_utc
        await db.commit()
        return router_obj, BackupTriggerResponse(
            status="IDENTICAL_SKIPPED_DEDUPLICATED",
            backup_id=latest_backup.id,
            rsc_sha256_hash=rsc_hash,
            message="Configuración idéntica al último respaldo. Se deduplica sin generar almacenamiento redundante.",
        )

    lines_added, lines_removed = 0, 0
    if latest_backup:
        old_text = clean_rsc_export_comments(_decrypt_backup_rsc(latest_backup, tenant_id))
        lines_added, lines_removed, _ = _compute_diff_stats(old_text.splitlines(), cleaned_rsc.splitlines())

    aad = f"{tenant_id}:{router_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(cleaned_rsc.encode("utf-8"), aad)

    new_backup = RouterBackup(
        tenant_id=tenant_id,
        router_id=router_id,
        backup_type="MANUAL_OPERATOR",
        ros_version_at_backup=router_obj.ros_version or "7.16",
        rsc_sha256_hash=rsc_hash,
        rsc_size_bytes=len(cleaned_rsc.encode("utf-8")),
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
        diff_lines_added=lines_added,
        diff_lines_removed=lines_removed,
        parent_backup_id=latest_backup.id if latest_backup else None,
        triggered_by=user_id,
        created_at=now_utc,
        last_verified_identical_at=now_utc,
        expires_at=now_utc + timedelta(days=30),
    )
    db.add(new_backup)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=actor_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        event_category="BACKUPS",
        event_action="ROUTER_BACKUP_CREATED",
        actor_user_id=user_id,
        router_id=router_id,
        router_display_name=router_obj.display_name,
        after_state={"rsc_sha256_hash": rsc_hash, "lines_added": lines_added, "lines_removed": lines_removed},
        status_code=201,
    )
    await db.commit()
    await db.refresh(new_backup)

    return router_obj, BackupTriggerResponse(
        status="CREATED",
        backup_id=new_backup.id,
        rsc_sha256_hash=rsc_hash,
        message="Respaldo cifrado generado y guardado exitosamente.",
    )


@batch_backups_router.post("/batch-trigger", response_model=BatchBackupTriggerResponse)
async def trigger_batch_backups(
    body: BatchBackupTriggerRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_TRIGGER_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BatchBackupTriggerResponse:
    """Dispara respaldos .rsc simultáneos sobre una selección de múltiples routers con deduplicación SHA-256."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    actor_username = str(claims.get("preferred_username", "operator"))
    actor_role = str(claims.get("rol", SystemRoleEnum.SUPPORT_L3.value))
    actor_ip = request.client.host if request.client else "127.0.0.1"

    unique_ids = list(dict.fromkeys(body.router_ids))
    results: list[BatchBackupRouterResult] = []
    created_count = 0
    deduplicated_count = 0
    failed_count = 0

    for r_id in unique_ids:
        try:
            r_obj, trig_res = await _execute_router_backup_core(
                router_id=r_id,
                tenant_id=tenant_id,
                user_id=user_id,
                actor_username=actor_username,
                actor_role=actor_role,
                actor_ip=actor_ip,
                claims=claims,
                db=db,
            )
            if trig_res.status == "CREATED":
                created_count += 1
            else:
                deduplicated_count += 1
            results.append(
                BatchBackupRouterResult(
                    router_id=r_id,
                    display_name=getattr(r_obj, "display_name", str(r_id)),
                    ip_address=getattr(r_obj, "ip_address", None),
                    status=trig_res.status,
                    backup_id=trig_res.backup_id,
                    rsc_sha256_hash=trig_res.rsc_sha256_hash,
                    message=trig_res.message,
                )
            )
        except HTTPException as http_exc:
            failed_count += 1
            results.append(
                BatchBackupRouterResult(
                    router_id=r_id,
                    display_name=str(r_id)[:8],
                    status="FAILED",
                    message=str(http_exc.detail),
                )
            )
        except Exception as exc:
            failed_count += 1
            results.append(
                BatchBackupRouterResult(
                    router_id=r_id,
                    display_name=str(r_id)[:8],
                    status="FAILED",
                    message=str(exc) or "Error de conexión al exportar respaldo.",
                )
            )

    return BatchBackupTriggerResponse(
        total_requested=len(unique_ids),
        created_count=created_count,
        deduplicated_count=deduplicated_count,
        failed_count=failed_count,
        results=results,
    )
```
4. En `fastapi/src/api/router.py`, importar e incluir `batch_backups_router`:
   ```python
   from src.api.v1.backups import batch_backups_router, router as backups_router
   ...
   api_v1_router.include_router(backups_router)
   api_v1_router.include_router(batch_backups_router)
   ```

---

### Paso 3: Añadir Botón y Modal de Respaldo Múltiple con Casillas de Selección en `vue3/src/views/RscGitDiffViewer.vue`

1. En `<script setup lang="ts">` de `vue3/src/views/RscGitDiffViewer.vue` (debajo de `backupSuccessMsg`, línea 43), añadir el estado y funciones del modal de respaldo por lote:
```ts
  interface BatchBackupRouterResultItem {
    router_id: string;
    display_name: string;
    ip_address?: string | null;
    status: 'CREATED' | 'IDENTICAL_SKIPPED_DEDUPLICATED' | 'FAILED' | string;
    backup_id?: string | null;
    rsc_sha256_hash?: string | null;
    message: string;
  }

  interface BatchBackupTriggerResponseData {
    total_requested: number;
    created_count: number;
    deduplicated_count: number;
    failed_count: number;
    results: BatchBackupRouterResultItem[];
  }

  const isBatchModalOpen = ref(false);
  const isBatchRunning = ref(false);
  const batchSearchQuery = ref('');
  const selectedBatchRouterIds = ref<string[]>([]);
  const batchResults = ref<BatchBackupTriggerResponseData | null>(null);

  const filteredBatchRouters = computed(() => {
    const q = batchSearchQuery.value.trim().toLowerCase();
    if (!q) return inventoryStore.routers;
    return inventoryStore.routers.filter(
      (r) =>
        r.display_name.toLowerCase().includes(q) ||
        (r.ip_address && r.ip_address.toLowerCase().includes(q)),
    );
  });

  function openBatchBackupModal() {
    batchResults.value = null;
    batchSearchQuery.value = '';
    const onlineIds = inventoryStore.routers
      .filter((r) => r.is_online !== false)
      .map((r) => r.id);
    selectedBatchRouterIds.value =
      onlineIds.length > 0 ? onlineIds : inventoryStore.routers.map((r) => r.id);
    isBatchModalOpen.value = true;
  }

  function selectAllBatchRouters() {
    selectedBatchRouterIds.value = filteredBatchRouters.value.map((r) => r.id);
  }

  function selectOnlineBatchRouters() {
    selectedBatchRouterIds.value = filteredBatchRouters.value
      .filter((r) => r.is_online !== false)
      .map((r) => r.id);
  }

  function clearBatchRouters() {
    selectedBatchRouterIds.value = [];
  }

  async function executeBatchBackup() {
    if (selectedBatchRouterIds.value.length === 0) return;
    isBatchRunning.value = true;
    error.value = null;
    try {
      const res = await http.post<BatchBackupTriggerResponseData>(
        '/api/v1/backups/batch-trigger',
        {
          router_ids: selectedBatchRouterIds.value,
        },
      );
      batchResults.value = res.data;
      backupSuccessMsg.value = `Respaldo múltiple completado: ${res.data.created_count} nuevos, ${res.data.deduplicated_count} sin cambios (deduplicados), ${res.data.failed_count} fallidos.`;
      if (routerId.value && selectedBatchRouterIds.value.includes(routerId.value)) {
        await loadBackups();
      }
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      error.value = e.detail || e.message || 'Error al ejecutar el respaldo múltiple de equipos.';
    } finally {
      isBatchRunning.value = false;
    }
  }
```
2. En `<div class="diff-header-actions">` de `vue3/src/views/RscGitDiffViewer.vue` (al lado del botón `+ Crear Respaldo Ahora`, línea 352), añadir el botón **`📦 Respaldo Múltiple`**:
```html
        <button
          v-if="!route.params.routerId"
          id="btn-open-batch-backup"
          type="button"
          class="btn btn--secondary"
          :disabled="creatingBackup || isBatchRunning"
          @click="openBatchBackupModal"
        >
          📦 Respaldo Múltiple ({{ inventoryStore.routers.length }})
        </button>
```
3. Antes del cierre `</main>` en `vue3/src/views/RscGitDiffViewer.vue` (línea 655), añadir el modal `#modal-batch-backup`:
```html
    <!-- Modal de Respaldo Simultáneo Multi-Equipo -->
    <div
      v-if="isBatchModalOpen"
      id="modal-batch-backup"
      class="batch-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-batch-backup-title"
      @click.self="isBatchModalOpen = false"
    >
      <div class="batch-modal">
        <header class="batch-modal-header">
          <div>
            <h2 id="modal-batch-backup-title" class="batch-modal-title">
              📦 Respaldo Simultáneo de Múltiples Equipos (.rsc)
            </h2>
            <p class="batch-modal-subtitle">
              Selecciona los routers a respaldar. Los equipos sin cambios aplicarán deduplicación inteligente SHA-256.
            </p>
          </div>
          <button
            type="button"
            class="btn-close-batch"
            aria-label="Cerrar modal de respaldo múltiple"
            @click="isBatchModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="batch-toolbar">
          <input
            id="batch-backup-search"
            v-model="batchSearchQuery"
            type="search"
            class="form-select batch-search-input"
            placeholder="Buscar equipo por nombre o IP..."
          />
          <div class="batch-quick-actions">
            <button
              id="btn-batch-select-all"
              type="button"
              class="btn-text"
              @click="selectAllBatchRouters"
            >
              ☑ Todos ({{ filteredBatchRouters.length }})
            </button>
            <button
              id="btn-batch-select-online"
              type="button"
              class="btn-text"
              @click="selectOnlineBatchRouters"
            >
              🟢 Solo Online
            </button>
            <button
              id="btn-batch-clear-all"
              type="button"
              class="btn-text"
              @click="clearBatchRouters"
            >
              ✕ Limpiar
            </button>
          </div>
        </div>

        <div class="batch-routers-list" role="group" aria-label="Lista de equipos para respaldo">
          <label
            v-for="r in filteredBatchRouters"
            :key="r.id"
            class="batch-router-item"
            :class="{
              'batch-router-item--selected': selectedBatchRouterIds.includes(r.id),
            }"
          >
            <input
              :id="`chk-batch-router-${r.id}`"
              v-model="selectedBatchRouterIds"
              type="checkbox"
              :value="r.id"
            />
            <div class="batch-router-info">
              <strong>{{ r.display_name }}</strong>
              <span class="batch-router-ip">{{ r.ip_address || r.api_base_url || '—' }}</span>
            </div>
            <span
              class="badge-pill"
              :class="r.is_online !== false ? 'badge-pill--base' : 'badge-pill--target'"
            >
              {{ r.is_online !== false ? '● ONLINE' : '▲ OFFLINE' }}
            </span>
          </label>
        </div>

        <div v-if="batchResults" class="batch-results-box" role="region" aria-label="Resultados del respaldo por lote">
          <div class="batch-results-summary">
            <span class="badge badge--added">✅ {{ batchResults.created_count }} Nuevos</span>
            <span class="badge badge--bin-available">
              ℹ️ {{ batchResults.deduplicated_count }} Deduplicados
            </span>
            <span v-if="batchResults.failed_count > 0" class="badge badge--removed">
              ⚠️ {{ batchResults.failed_count }} Fallidos
            </span>
          </div>
          <ul class="batch-results-list">
            <li v-for="resItem in batchResults.results" :key="resItem.router_id" class="batch-result-row">
              <strong>{{ resItem.display_name }}</strong>
              <span>
                {{
                  resItem.status === 'CREATED'
                    ? '✅ Creado'
                    : resItem.status === 'IDENTICAL_SKIPPED_DEDUPLICATED'
                      ? 'ℹ️ Sin cambios (Deduplicado)'
                      : `⚠️ ${resItem.message}`
                }}
              </span>
            </li>
          </ul>
        </div>

        <footer class="batch-modal-footer">
          <button type="button" class="btn-text" @click="isBatchModalOpen = false">
            Cerrar
          </button>
          <button
            id="btn-execute-batch-backup"
            type="button"
            class="btn btn--primary"
            :disabled="isBatchRunning || selectedBatchRouterIds.length === 0"
            @click="executeBatchBackup"
          >
            {{
              isBatchRunning
                ? '⏳ Respaldando equipos...'
                : `🚀 Respaldar Equipos Seleccionados (${selectedBatchRouterIds.length})`
            }}
          </button>
        </footer>
      </div>
    </div>
```

---

## 3. Aseguramiento de Calidad Level-11X Obligatorio (Pytest, Vitest y Karate Labs BDD)

### 3.1. Prueba Unitaria de Persistencia de IP Emparejada en `GET /api/v1/ipam/customer-services` y `PATCH /api/v1/subscriber-devices/{id}`
En `fastapi/tests/api/test_subscribers.unit.py`, verificar que tras ejecutar `PATCH /api/v1/subscriber-devices/{id}` con `assigned_ipv4: "10.250.3.55"`, tanto la respuesta del `PATCH` como la consulta subsiguiente a `GET /api/v1/ipam/customer-services` devuelven `assigned_ipv4 == "10.250.3.55"` (nunca `None`).

### 3.2. Prueba Unitaria de `POST /api/v1/backups/batch-trigger` en `fastapi/tests/api/test_operations_endpoints_full.unit.py`
Añadir prueba unitaria en `fastapi/tests/api/test_operations_endpoints_full.unit.py` verificando `POST /api/v1/backups/batch-trigger` con múltiples `router_ids`, validando el conteo de `created_count`, `deduplicated_count` y el registro WORM `ROUTER_BACKUP_CREATED`.

### 3.3. Prueba Unitaria Frontend en `vue3/src/views/operationsViews.unit.ts`
En `vue3/src/views/operationsViews.unit.ts`, verificar que en `RscGitDiffViewer.vue` (cuando `route.params.routerId` no está forzado o al abrir `openBatchBackupModal`), se seleccionan los equipos con casillas `#chk-batch-router-<id>`, se invoca `POST /api/v1/backups/batch-trigger` al pulsar `#btn-execute-batch-backup` y se renderiza el resumen `.batch-results-box`.

### 3.4. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + réplicas en `docs/examples/`)
1. Añadir `Scenario: 165` en `fastapi/test/api_test.feature` (+ `docs/examples/fastapi/api_test.feature.example`) validando `POST /api/v1/backups/batch-trigger`.
2. Añadir `Scenario: 103` en `vue3/test/ui_business_flow.feature` (+ `docs/examples/vue3/ui_business_flow.feature.example`) validando el modal `#modal-batch-backup` y la persistencia de `assigned_ipv4` tras emparejar en `/ipam`.
