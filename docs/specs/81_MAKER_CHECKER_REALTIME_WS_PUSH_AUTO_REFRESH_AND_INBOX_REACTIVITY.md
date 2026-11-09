# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 81: Empuje Reactivo por WebSocket (`MAKER_CHECKER_REQUESTED` / `MAKER_CHECKER_RESOLVED`), Auto-Refresco Periódico (15s), Sincronización de Contadores de Pendientes y Botón `[ 🔄 Refrescar ]` en la Bandeja Maker-Checker (`/approvals`)

> **Hito Asociado:** Hito 30 (Subhito `30.3`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Estado:** COMPLETADO al 100% y Certificado en Docker (Regla Cero & QA 11X)

---

## 1. Diagnóstico Forense de las 4 Causas Raíz

Al evaluar cómo se entera un Supervisor, Nivel 3 o Administrador cuando otro operador realiza una modificación que requiere aprobación de 4 ojos (*Maker-Checker*), se identificaron **4 brechas de reactividad**:

1. **Ausencia de Publicación Pub/Sub (`MAKER_CHECKER_REQUESTED` / `MAKER_CHECKER_RESOLVED`) en el Backend (`webfig_common.py`, `bulk_and_updates.py`, `mcp.py` y `approvals.py`):**
   - Aunque el frontend (`useNocEventsStore.ts` línea 79) tenía preparado el código `if (eventName === 'APPROVAL_NEEDED' || eventName === 'MAKER_CHECKER_REQUESTED')`, ninguno de los 3 puntos del backend que interceptan y crean un `ApprovalRequest` (`fastapi/src/api/v1/webfig_common.py`, `fastapi/src/api/v1/bulk_and_updates.py` y `fastapi/src/api/v1/mcp.py`) publicaba el evento en el canal Pub/Sub de KeyDB (`rg:{tenant_id}:events`).
   - Tampoco `approve_request` ni `reject_request` en `fastapi/src/api/v1/approvals.py` publicaban `MAKER_CHECKER_RESOLVED` para descontar el contador de pendientes en tiempo real.

2. **Bandeja Estática Sin Temporizador ni Escucha Reactiva (`vue3/src/views/ApprovalsInboxView.vue`):**
   - En `ApprovalsInboxView.vue` (líneas 133–135), `loadApprovals()` solo se ejecutaba una única vez en `onMounted()`.
   - No existía un intervalo de auto-refresco (`setInterval`) ni un `watch` sobre `useNocEventsStore.pendingApprovalsCount` o un evento global `rosgrid:maker-checker-updated`. Si el encargado tenía abierta la pantalla `/approvals`, las nuevas solicitudes nunca aparecían solas hasta recargar con `F5`.

3. **Ausencia del Botón Táctico `[ 🔄 Refrescar ]` en `/approvals` (`vue3/src/views/ApprovalsInboxView.vue`):**
   - La cabecera `.view-header` de `ApprovalsInboxView.vue` solo contenía el título y las 3 pestañas (`Pendientes de Firma`, `Aprobados (Ejecutados)`, `Rechazados / Expirados`), careciendo de un botón explícito **`[ 🔄 Refrescar ]`** (`#btn-refresh-approvals`) y de la sincronización del contador `nocStore.pendingApprovalsCount` con el número real de solicitudes `AWAITING_APPROVAL`.

4. **Conexión WebSocket Limitada a Dos Vistas (`vue3/src/components/common/RgResponsiveShell.vue`):**
   - `nocStore.connectEventsWebSocket()` solo se invocaba al montar `DashboardHomeView.vue` o `NocWallboardView.vue`, pero no en el contenedor global `RgResponsiveShell.vue`. Si un encargado ingresaba directamente a `/approvals` o `/inventory`, el WebSocket de eventos del tenant ni siquiera estaba conectado.

---

## 2. Instrucciones de Implementación Exactas (*Flash-Ready* `Target` / `Replacement`)

### Paso 1: Publicación de Eventos `MAKER_CHECKER_REQUESTED` y `MAKER_CHECKER_RESOLVED` en KeyDB Pub/Sub (`fastapi/src/api/v1/webfig_common.py`, `fastapi/src/api/v1/bulk_and_updates.py`, `fastapi/src/api/v1/mcp.py` y `fastapi/src/api/v1/approvals.py`)

1. En `fastapi/src/api/v1/webfig_common.py`, añadir la función auxiliar `publish_maker_checker_event` y llamarla al crear el `ApprovalRequest`:

**`Target` en `fastapi/src/api/v1/webfig_common.py` (líneas 290–306):**
```python
        previous_state_snapshot=previous_state_snapshot,
        requested_by=user_id,
        expires_at=now_utc + timedelta(hours=24),
        created_at=now_utc,
    )
    db.add(approval)
    await db.commit()

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "INTERCEPTED_FOR_APPROVAL",
            "approval_request_id": str(approval.id),
            "detail": "Operación enviada a Maker-Checker. En espera de aprobación humana por Nivel 3, Supervisor o Administrador.",
        },
    )
```

**`Replacement` en `fastapi/src/api/v1/webfig_common.py`:**
```python
        previous_state_snapshot=previous_state_snapshot,
        requested_by=user_id,
        expires_at=now_utc + timedelta(hours=24),
        created_at=now_utc,
    )
    db.add(approval)
    await db.commit()

    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_REQUESTED",
        approval_id=approval.id,
        summary=approval.summary,
        router_id=router_id,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "INTERCEPTED_FOR_APPROVAL",
            "approval_request_id": str(approval.id),
            "detail": "Operación enviada a Maker-Checker. En espera de aprobación humana por Nivel 3, Supervisor o Administrador.",
        },
    )


async def publish_maker_checker_event(
    tenant_id: uuid.UUID,
    event_name: str,
    approval_id: uuid.UUID,
    summary: str,
    router_id: uuid.UUID | None = None,
    resolution_status: str | None = None,
) -> None:
    """Publica notificación en tiempo real en KeyDB Pub/Sub para actualizar bandejas Maker-Checker."""
    try:
        redis = get_redis_client()
        payload = {
            "id": str(uuid.uuid4()),
            "event_name": event_name,
            "approval_request_id": str(approval_id),
            "router_id": str(router_id) if router_id else None,
            "severity": "WARNING" if event_name == "MAKER_CHECKER_REQUESTED" else "INFO",
            "message": summary,
            "status": resolution_status or "PENDING",
            "timestamp_iso": datetime.now(UTC).isoformat(),
        }
        await redis.publish(f"rg:{tenant_id}:events", json.dumps(payload))
    except Exception as exc:
        logger.debug("No se pudo publicar evento Maker-Checker en Pub/Sub: %s", exc)
```

2. En `fastapi/src/api/v1/bulk_and_updates.py` y `fastapi/src/api/v1/mcp.py`, invocar `publish_maker_checker_event` cuando se cree un `ApprovalRequest`:

**`Target` en `fastapi/src/api/v1/bulk_and_updates.py` (líneas 1575–1581):**
```python
    await db.commit()
    await db.refresh(bulk_job)

    # Si no requiere aprobación Maker-Checker, despachar inmediatamente en la flota
    if not is_l2:
```

**`Replacement` en `fastapi/src/api/v1/bulk_and_updates.py`:**
```python
    await db.commit()
    await db.refresh(bulk_job)

    if is_l2 and approval_req_id is not None:
        from src.api.v1.webfig_common import publish_maker_checker_event

        await publish_maker_checker_event(
            tenant_id=tenant_id,
            event_name="MAKER_CHECKER_REQUESTED",
            approval_id=approval_req_id,
            summary=f"Acción masiva: {payload.title} sobre {len(target_ids)} routers",
        )

    # Si no requiere aprobación Maker-Checker, despachar inmediatamente en la flota
    if not is_l2:
```

**`Target` en `fastapi/src/api/v1/mcp.py` (líneas 400–408):**
```python
    db.add(req)
    await db.flush()
    return {
        "status": "AWAITING_APPROVAL",
        "approval_request_id": str(req.id),
        "message": "Propuesta enviada exitosamente a la bandeja de aprobación Maker-Checker (Safe Mode 60s)",
    }
```

**`Replacement` en `fastapi/src/api/v1/mcp.py`:**
```python
    db.add(req)
    await db.flush()
    from src.api.v1.webfig_common import publish_maker_checker_event

    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_REQUESTED",
        approval_id=req.id,
        summary=req.summary,
        router_id=router_id,
    )
    return {
        "status": "AWAITING_APPROVAL",
        "approval_request_id": str(req.id),
        "message": "Propuesta enviada exitosamente a la bandeja de aprobación Maker-Checker (Safe Mode 60s)",
    }
```

3. En `fastapi/src/api/v1/approvals.py`, publicar `MAKER_CHECKER_RESOLVED` al aprobar o rechazar una solicitud en `_log_approval_audit`:

**`Target` en `fastapi/src/api/v1/approvals.py` (líneas 17–21 y 236–254):**
```python
from src.api.v1.webfig_common import (
    execute_safe_mutation,
    get_router_and_client,
    invalidate_webfig_cache,
)
```

**`Replacement` en `fastapi/src/api/v1/approvals.py` (líneas 17–21):**
```python
from src.api.v1.webfig_common import (
    execute_safe_mutation,
    get_router_and_client,
    invalidate_webfig_cache,
    publish_maker_checker_event,
)
```

**`Target` en `_log_approval_audit` (`fastapi/src/api/v1/approvals.py` líneas 236–254):**
```python
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "checker"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="MAKER_CHECKER",
        event_action=event_action,
        actor_user_id=checker_user_id,
        router_id=approval.router_id,
        router_display_name=router_name,
        ros_rest_method=approval.ros_rest_method,
        ros_rest_endpoint=approval.ros_rest_path,
        before_state=approval.previous_state_snapshot,
        after_state=approval.request_payload,
        status_code=stat_code,
        error_message=err_msg,
    )
```

**`Replacement` en `_log_approval_audit` (`fastapi/src/api/v1/approvals.py`):**
```python
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "checker"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="MAKER_CHECKER",
        event_action=event_action,
        actor_user_id=checker_user_id,
        router_id=approval.router_id,
        router_display_name=router_name,
        ros_rest_method=approval.ros_rest_method,
        ros_rest_endpoint=approval.ros_rest_path,
        before_state=approval.previous_state_snapshot,
        after_state=approval.request_payload,
        status_code=stat_code,
        error_message=err_msg,
    )
    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_RESOLVED",
        approval_id=approval.id,
        summary=approval.summary,
        router_id=approval.router_id,
        resolution_status=approval.status.value if hasattr(approval.status, "value") else str(approval.status),
    )
```

---

### Paso 2: Propagación Reactiva en `vue3/src/stores/useNocEventsStore.ts` y Conexión Global en `vue3/src/components/common/RgResponsiveShell.vue`

1. En `vue3/src/stores/useNocEventsStore.ts`, despachar el evento global `rosgrid:maker-checker-updated` cuando llegue `APPROVAL_NEEDED`, `MAKER_CHECKER_REQUESTED` o `MAKER_CHECKER_RESOLVED`, y exponer `setPendingApprovalsCount(count: number)`:

**`Target` en `vue3/src/stores/useNocEventsStore.ts` (líneas 79–82):**
```ts
      if (eventName === 'APPROVAL_NEEDED' || eventName === 'MAKER_CHECKER_REQUESTED') {
        pendingApprovalsCount.value += 1;
      }
```

**`Replacement` en `vue3/src/stores/useNocEventsStore.ts`:**
```ts
      if (eventName === 'APPROVAL_NEEDED' || eventName === 'MAKER_CHECKER_REQUESTED') {
        pendingApprovalsCount.value += 1;
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('rosgrid:maker-checker-updated', { detail: payload }));
        }
      } else if (eventName === 'MAKER_CHECKER_RESOLVED') {
        pendingApprovalsCount.value = Math.max(0, pendingApprovalsCount.value - 1);
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('rosgrid:maker-checker-updated', { detail: payload }));
        }
      }
```

**`Target` al final de `vue3/src/stores/useNocEventsStore.ts` (líneas 192–221):**
```ts
  function clearEvents(): void {
    recentEvents.value = [];
    activeAlertsCount.value = 0;
    triggerRef(recentEvents);
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('rosgrid:tenant-switched', () => {
      disconnectEventsWebSocket();
      setTimeout(() => {
        connectEventsWebSocket();
      }, 150);
    });
    window.addEventListener('rosgrid:session-expired', () => {
      disconnectEventsWebSocket();
    });
  }

  return {
    isConnected,
    pendingApprovalsCount,
    activeAlertsCount,
    recentEvents,
    handleIncomingEvent,
    connectEventsWebSocket,
    disconnectEventsWebSocket,
    fetchRecentAuditLogs,
    clearEvents,
    lastDeviceStatusEvent,
  };
```

**`Replacement` al final de `vue3/src/stores/useNocEventsStore.ts`:**
```ts
  function setPendingApprovalsCount(count: number): void {
    pendingApprovalsCount.value = Math.max(0, count);
  }

  function clearEvents(): void {
    recentEvents.value = [];
    activeAlertsCount.value = 0;
    triggerRef(recentEvents);
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('rosgrid:tenant-switched', () => {
      disconnectEventsWebSocket();
      setTimeout(() => {
        connectEventsWebSocket();
      }, 150);
    });
    window.addEventListener('rosgrid:session-expired', () => {
      disconnectEventsWebSocket();
    });
  }

  return {
    isConnected,
    pendingApprovalsCount,
    setPendingApprovalsCount,
    activeAlertsCount,
    recentEvents,
    handleIncomingEvent,
    connectEventsWebSocket,
    disconnectEventsWebSocket,
    fetchRecentAuditLogs,
    clearEvents,
    lastDeviceStatusEvent,
  };
```

2. En `vue3/src/components/common/RgResponsiveShell.vue`, conectar el WebSocket de eventos del tenant en `onMounted()` para que permanezca activo en cualquier pantalla de la aplicación:

**`Target` en `vue3/src/components/common/RgResponsiveShell.vue` (líneas 133–140):**
```ts
  onMounted(() => {
    heartbeatStore.startMonitoring();
    headerClockTimer = setInterval(updateHeaderClock, 1000);
    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onKeydown);
    }
  });
```

**`Replacement` en `vue3/src/components/common/RgResponsiveShell.vue`:**
```ts
  onMounted(() => {
    heartbeatStore.startMonitoring();
    nocStore.connectEventsWebSocket();
    headerClockTimer = setInterval(updateHeaderClock, 1000);
    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onKeydown);
    }
  });
```

---

### Paso 3: Auto-Refresco Periódico (15s), Escucha WebSocket en Vivo y Botón `[ 🔄 Refrescar ]` en `vue3/src/views/ApprovalsInboxView.vue`

Editar `vue3/src/views/ApprovalsInboxView.vue` para:
1. Sincronizar `nocStore.setPendingApprovalsCount(...)` cada vez que se carguen las solicitudes desde `/api/v1/operations/approvals`.
2. Escuchar el evento `rosgrid:maker-checker-updated` en `window` para recargar `loadApprovals()` al instante (< 1s) cuando otro operador envíe una solicitud.
3. Mantener un intervalo de auto-refresco cada **15 segundos** (`approvalsPollTimer`) como respaldo determinista y limpiarlo en `onUnmounted()`.
4. Añadir el botón **`[ 🔄 Refrescar ]`** (`#btn-refresh-approvals`) y el contador en las pestañas dentro de `.view-header`.

**`Target` en `vue3/src/views/ApprovalsInboxView.vue` (líneas 4–14):**
```ts
<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import type { ApprovalRequestItem } from '@/types';

  const authStore = useAuthStore();
  const { t } = useI18n();
```

**`Replacement` en `vue3/src/views/ApprovalsInboxView.vue` (líneas 4–14):**
```ts
<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useI18n } from '@/composables/useI18n';
  import type { ApprovalRequestItem } from '@/types';

  const authStore = useAuthStore();
  const nocStore = useNocEventsStore();
  const { t } = useI18n();
  let approvalsPollTimer: ReturnType<typeof setInterval> | null = null;
```

**`Target` en `loadApprovals` y `onMounted` (`vue3/src/views/ApprovalsInboxView.vue` líneas 58–74 y 133–136):**
```ts
        status: item.status === 'PENDING' ? 'AWAITING_APPROVAL' : (item.status?.startsWith('APPROVED') ? 'APPROVED' : item.status),
      }));
    } catch {
      // Sin datos de demostración en producción
      requests.value = [];
    } finally {
```

**`Replacement` en `loadApprovals` (`vue3/src/views/ApprovalsInboxView.vue`):**
```ts
        status: item.status === 'PENDING' ? 'AWAITING_APPROVAL' : (item.status?.startsWith('APPROVED') ? 'APPROVED' : item.status),
      }));
      const pendingCount = requests.value.filter((r) => r.status === 'AWAITING_APPROVAL').length;
      if (typeof nocStore.setPendingApprovalsCount === 'function') {
        nocStore.setPendingApprovalsCount(pendingCount);
      }
    } catch {
      // Sin datos de demostración en producción
      requests.value = [];
    } finally {
```

**`Target` en `onMounted` y Template (`vue3/src/views/ApprovalsInboxView.vue` líneas 133–182):**
```ts
  onMounted(() => {
    loadApprovals();
  });
</script>

<template>
  <div class="approvals-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">{{ t('approvals.title') }}</h1>
        <p class="view-subtitle">
          {{ t('approvals.subtitle') }}
        </p>
      </div>

      <!-- Pestañas de Aprobación -->
      <nav class="subtabs-bar" role="tablist" :aria-label="t('approvals.subtabs_aria')">
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'pending' }"
          role="tab"
          :aria-selected="activeTab === 'pending'"
          @click="activeTab = 'pending'"
        >
          {{ t('approvals.tab_pending') }}
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'approved' }"
          role="tab"
          :aria-selected="activeTab === 'approved'"
          @click="activeTab = 'approved'"
        >
          {{ t('approvals.tab_approved') }}
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'rejected' }"
          role="tab"
          :aria-selected="activeTab === 'rejected'"
          @click="activeTab = 'rejected'"
        >
          {{ t('approvals.tab_rejected') }}
        </button>
      </nav>
    </header>
```

**`Replacement` en `onMounted` y Template (`vue3/src/views/ApprovalsInboxView.vue`):**
```ts
  function handleMakerCheckerWsUpdate(): void {
    void loadApprovals();
  }

  onMounted(() => {
    void loadApprovals();
    approvalsPollTimer = setInterval(() => {
      void loadApprovals();
    }, 15000);
    if (typeof window !== 'undefined') {
      window.addEventListener('rosgrid:maker-checker-updated', handleMakerCheckerWsUpdate);
    }
  });

  onUnmounted(() => {
    if (approvalsPollTimer !== null) {
      clearInterval(approvalsPollTimer);
      approvalsPollTimer = null;
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('rosgrid:maker-checker-updated', handleMakerCheckerWsUpdate);
    }
  });
</script>

<template>
  <div class="approvals-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">{{ t('approvals.title') }}</h1>
        <p class="view-subtitle">
          {{ t('approvals.subtitle') }}
        </p>
      </div>

      <div class="header-controls">
        <!-- Pestañas de Aprobación -->
        <nav class="subtabs-bar" role="tablist" :aria-label="t('approvals.subtabs_aria')">
          <button
            type="button"
            class="btn-subtab"
            :class="{ 'btn-subtab--active': activeTab === 'pending' }"
            role="tab"
            :aria-selected="activeTab === 'pending'"
            @click="activeTab = 'pending'"
          >
            {{ t('approvals.tab_pending') }}
          </button>
          <button
            type="button"
            class="btn-subtab"
            :class="{ 'btn-subtab--active': activeTab === 'approved' }"
            role="tab"
            :aria-selected="activeTab === 'approved'"
            @click="activeTab = 'approved'"
          >
            {{ t('approvals.tab_approved') }}
          </button>
          <button
            type="button"
            class="btn-subtab"
            :class="{ 'btn-subtab--active': activeTab === 'rejected' }"
            role="tab"
            :aria-selected="activeTab === 'rejected'"
            @click="activeTab = 'rejected'"
          >
            {{ t('approvals.tab_rejected') }}
          </button>
        </nav>

        <button
          id="btn-refresh-approvals"
          type="button"
          class="btn-refresh-approvals"
          :disabled="isLoading"
          aria-label="Refrescar bandeja de aprobaciones"
          @click="loadApprovals"
        >
          {{ isLoading ? '⏳ Refrescando...' : '🔄 Refrescar' }}
        </button>
      </div>
    </header>
```

**`Target` en CSS de `.subtabs-bar` (`vue3/src/views/ApprovalsInboxView.vue` líneas 341–350):**
```css
  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }
```

**`Replacement` en CSS de `.subtabs-bar` (`vue3/src/views/ApprovalsInboxView.vue`):**
```css
  .header-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .btn-refresh-approvals {
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-refresh-approvals:hover:not(:disabled) {
    background: rgba(34, 211, 238, 0.25);
    color: #fff;
  }

  .btn-refresh-approvals:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }
```

---

## 3. Aseguramiento de Calidad Level-11X (Regla Cero)

1. **Pruebas Unitarias Backend (`fastapi/tests/`):**
   - Verificar en `fastapi/tests/api/test_operations_endpoints_full.unit.py` que al interceptarse una operación para aprobación (`HTTP 202`) o al aprobarse/rechazarse en `/api/v1/operations/approvals/{id}/approve`, se publica el evento `MAKER_CHECKER_REQUESTED` / `MAKER_CHECKER_RESOLVED` en KeyDB Pub/Sub.
2. **Pruebas Unitarias Frontend (`vue3/src/views/operationsViews.unit.ts` y `vue3/src/stores/useNocEventsStore.unit.ts`):**
   - Certificar que al recibirse `MAKER_CHECKER_REQUESTED` por WebSocket se dispara `rosgrid:maker-checker-updated` y `ApprovalsInboxView.vue` recarga automáticamente la lista sin intervención del usuario, además de responder al clic en `#btn-refresh-approvals`.
