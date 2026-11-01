# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación Técnica 65 — Corrección de Conteo RLS de Flota en Telemetría Anónima (Beacon), Persistencia de `fleet_bucket` en KeyDB y Paridad de Contrato JSON en Administración de Empresas (`/admin/tenants`)

- **Estado:** Planificado (Blueprint Literal *Flash-Ready* para Ejecución Directa por **Gemini 3.8 Flash High**)
- **Hito Asociado:** Hito 28.10 (`ROADMAP.md`)
- **Dominios Afectados:**
  - Backend: `fastapi/src/workers/telemetry_beacon_worker.py`
  - Frontend: `vue3/src/views/admin/TenantsManagementView.vue`
  - Pruebas Unitarias y BDD: `fastapi/tests/workers/test_telemetry_beacon_worker.unit.py`, `vue3/src/views/admin/tenantsManagementView.unit.ts`, `fastapi/test/api_test.feature`, `vue3/test/ui_business_flow.feature` (y réplicas en `docs/examples/`)

---

## 1. Diagnóstico Forense de Causa Raíz (Evidencia UAT)

Durante las pruebas de usuario en `http://localhost:8085/admin/tenants`, la tarjeta **📡 Telemetría Anónima de Instancia (Heartbeat Beacon)** muestra permanentemente:

```text
Instance ID (HMAC-SHA256): 9ce21f55a851ed11a59d48b7c0ba02ad6fd2bdbe5ddf87bdaab637fb344c511f | Flota: 0 routers | Último Latido: Nunca
```

incluso inmediatamente después de presionar **`📡 Emitir Latido Ahora`** y recibir el banner verde `Latido de telemetría anónima emitido exitosamente.` (y aun cuando en la base de datos existen **7 routers CHR activos** y en KeyDB consta `last_sent_at: 2026-11-01T23:08:40Z` y `last_status: http_202`).

La inspección del código fuente y del estado en KeyDB demostró **tres causas raíz exactas**:

### 1.1. Causa Raíz A — Ceguera por PostgreSQL Row-Level Security (`FORCE RLS`) en `_count_active_routers_safe()`
En [`fastapi/src/workers/telemetry_beacon_worker.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/telemetry_beacon_worker.py#L47-L57):
```python
async def _count_active_routers_safe() -> int:
    try:
        async with async_session_maker() as session:
            stmt = select(func.count(Router.id)).where(Router.admin_state == RouterAdminStateEnum.PRODUCTION)
            res = await session.execute(stmt)
            count = res.scalar() or 0
            return int(count)
```
Como la tabla `routers` tiene habilitado **`FORCE ROW LEVEL SECURITY`** en PostgreSQL 17, abrir una sesión de `async_session_maker()` sin invocar previamente `await set_tenant_context(session, None, is_superadmin=True)` provoca que la política RLS filtre el 100% de las filas. En consecuencia, `_count_active_routers_safe()` devuelve **`0`** en lugar de **`7`**, reportando `fleet_bucket: "0"` en vez de `"1-10"`.

### 1.2. Causa Raíz B — Omisión de `fleet_bucket` y `router_count` en KeyDB (`_persist_beacon_state` y `get_telemetry_beacon_status`)
En [`fastapi/src/workers/telemetry_beacon_worker.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/telemetry_beacon_worker.py#L60-L106):
- `_persist_beacon_state()` guarda en el hash `rg:system:telemetry_beacon_state` únicamente `instance_id`, `last_sent_at`, `last_status` y `beacon_url`, **sin persistir `fleet_bucket` ni `router_count`**.
- `get_telemetry_beacon_status()` (`GET /api/v1/system/telemetry-beacon/status`) retorna un diccionario que **no contiene `fleet_bucket` ni `router_count`**, ni incluye el alias `last_heartbeat_at`.

### 1.3. Causa Raíz C — Desajuste de Nombres de Campos en `TenantsManagementView.vue`
En [`vue3/src/views/admin/TenantsManagementView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/admin/TenantsManagementView.vue#L125-L191):
- La plantilla renderiza:
  ```html
  Flota: <strong>{{ beaconStatus?.fleet_bucket || '0' }} routers</strong> |
  Último Latido: <span>{{ beaconStatus?.last_heartbeat_at || 'Nunca' }}</span>
  ```
- Mientras que el backend retorna `last_sent_at` (no `last_heartbeat_at`) y no incluía `fleet_bucket` en `/api/v1/system/telemetry-beacon/status`. Además, al ejecutar `handleTriggerBeacon()`, la llamada posterior a `await loadBeaconStatus()` sobrescribe el estado con la respuesta incompleta de `/status`.

---

## 2. Guía de Implementación Paso a Paso (Flash-Ready Blueprint)

> **INSTRUCCIÓN PARA GEMINI 3.8 FLASH HIGH:**
> Aplica exactamente las modificaciones descritas en los pasos 2.1 a 2.4 manteniendo complejidad ciclomática Radon Grado A (`CC <= 5`) en todas las funciones.

### Paso 2.1: Habilitar Contexto SuperAdmin RLS y Persistir `fleet_bucket` / `router_count` en `fastapi/src/workers/telemetry_beacon_worker.py`

1. En `fastapi/src/workers/telemetry_beacon_worker.py`, importar `set_tenant_context` desde `src.db.session`:
   ```python
   from src.db.session import async_session_maker, set_tenant_context
   ```
2. Actualizar `_count_active_routers_safe()` para activar el contexto `is_superadmin=True` antes de contar los routers en estado `PRODUCTION`:
   ```python
   async def _count_active_routers_safe() -> int:
       """Cuenta routers activos globalmente (bypass RLS SuperAdmin) de forma fail-silent (CC = 2)."""
       try:
           async with async_session_maker() as session:
               await set_tenant_context(session, None, is_superadmin=True)
               stmt = select(func.count(Router.id)).where(Router.admin_state == RouterAdminStateEnum.PRODUCTION)
               res = await session.execute(stmt)
               count = res.scalar() or 0
               return int(count)
       except Exception as exc:
           logger.debug("Fallo no bloqueante al contar routers para beacon: %s", exc)
           return 0
   ```
3. Actualizar `_persist_beacon_state()` para recibir y almacenar `fleet_bucket: str = "0"` y `router_count: int = 0`:
   ```python
   async def _persist_beacon_state(
       instance_id: str,
       now_iso: str,
       status_str: str,
       fleet_bucket: str = "0",
       router_count: int = 0,
   ) -> None:
       """Guarda el último estado del latido en KeyDB sin fallar si KeyDB está mockeado (CC = 2)."""
       try:
           redis = get_redis_client()
           await redis.hset(
               BEACON_STATE_KEY,
               mapping={
                   "instance_id": instance_id,
                   "last_sent_at": now_iso,
                   "last_status": status_str,
                   "fleet_bucket": fleet_bucket,
                   "router_count": str(router_count),
                   "beacon_url": settings.ROSGRID_TELEMETRY_BEACON_URL,
               },
           )
       except Exception as exc:
           logger.debug("Persistencia de beacon en KeyDB omitida: %s", exc)
   ```
4. Añadir un helper ligero `_decode_redis_str(val: Any, default: str | None = None) -> str | None` (Grado A, `CC = 3`) y actualizar `get_telemetry_beacon_status()` para que:
   - Lea `fleet_bucket` y `router_count` desde KeyDB (o calcule `_count_active_routers_safe()` en vivo si aún no existen en KeyDB).
   - Exponga tanto `last_sent_at` como su alias `last_heartbeat_at` (garantizando compatibilidad total con cualquier consumidor UI), además de `fleet_bucket`, `router_count` y `last_status`:
   ```python
   def _decode_redis_str(val: Any, default: str | None = None) -> str | None:
       """Decodifica un valor de KeyDB (bytes o str) de forma segura (CC = 3)."""
       if val is None:
           return default
       return val.decode() if isinstance(val, bytes) else str(val)


   async def get_telemetry_beacon_status() -> dict[str, Any]:
       """Obtiene el estado actual del latido de telemetría para diagnósticos locales (CC = 4)."""
       instance_id = compute_anonymous_instance_id(settings.ROSGRID_JWT_SECRET_KEY[:16])
       last_sent_at: str | None = None
       last_status = "untriggered"
       fleet_bucket: str | None = None
       router_count = await _count_active_routers_safe()

       try:
           redis = get_redis_client()
           raw_state = await redis.hgetall(BEACON_STATE_KEY)
           if raw_state:
               instance_id = _decode_redis_str(raw_state.get("instance_id"), instance_id) or instance_id
               last_sent_at = _decode_redis_str(raw_state.get("last_sent_at"), None)
               last_status = _decode_redis_str(raw_state.get("last_status"), "untriggered") or "untriggered"
               fleet_bucket = _decode_redis_str(raw_state.get("fleet_bucket"), None)
       except Exception as exc:
           logger.debug("Lectura de estado de beacon en KeyDB omitida: %s", exc)

       resolved_bucket = fleet_bucket or resolve_fleet_bucket(router_count)
       return {
           "enabled": settings.ROSGRID_TELEMETRY_BEACON_ENABLED,
           "instance_id": instance_id,
           "beacon_url": settings.ROSGRID_TELEMETRY_BEACON_URL,
           "interval_seconds": settings.ROSGRID_TELEMETRY_BEACON_INTERVAL_SECONDS,
           "last_sent_at": last_sent_at,
           "last_heartbeat_at": last_sent_at,
           "last_status": last_status,
           "fleet_bucket": resolved_bucket,
           "router_count": router_count,
       }
   ```
5. En `send_telemetry_heartbeat_once()`, pasar `fleet_bucket=payload["fleet_bucket"]` y `router_count=router_count` a `_persist_beacon_state(...)`, e incluir `"last_heartbeat_at": now_iso` y `"router_count": router_count` en el diccionario de retorno.

---

### Paso 2.2: Alinear `TenantsManagementView.vue` para Mostrar `router_count` / `fleet_bucket`, `last_sent_at` y `last_status`

En [`vue3/src/views/admin/TenantsManagementView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/admin/TenantsManagementView.vue#L125-L195):
1. Ampliar el tipado de `beaconStatus`:
   ```ts
   const beaconStatus = ref<{
     enabled: boolean;
     instance_id?: string;
     last_sent_at?: string | null;
     last_heartbeat_at?: string | null;
     fleet_bucket?: string;
     router_count?: number;
     last_status?: string;
     status?: string;
   } | null>(null);
   ```
2. En `handleTriggerBeacon()`, asignar directamente los datos devueltos por `POST /api/v1/system/telemetry-beacon/trigger` si están presentes antes de refrescar `loadBeaconStatus()`:
   ```ts
   async function handleTriggerBeacon() {
     isTriggeringBeacon.value = true;
     errorMessage.value = '';
     try {
       const res = await http.post<any>('/api/v1/system/telemetry-beacon/trigger');
       if (res.data && typeof res.data === 'object') {
         beaconStatus.value = { ...beaconStatus.value, ...res.data };
       }
       successMessage.value =
         res.data?.message || 'Latido de telemetría anónima emitido exitosamente.';
       await loadBeaconStatus();
     } catch (err: unknown) {
       const error = err as { message?: string; detail?: string };
       errorMessage.value = error.detail || error.message || 'Error al emitir latido del beacon.';
     } finally {
       isTriggeringBeacon.value = false;
     }
   }
   ```
3. En el `<template>` y `<style scoped>` de `.beacon-card`, mostrar tanto el conteo/rango de flota como la fecha real (`last_sent_at || last_heartbeat_at`) y el código de estado (`last_status`), estilizando el botón `#btn-trigger-beacon` (`.btn-beacon`) con el sistema de diseño táctico NOC (borde `#38bdf8`, fondo translúcido `rgba(56, 189, 248, 0.1)`, hover cian luminoso y jerarquía secundaria bajo `+ Registrar Empresa`) y declarando la familia `.btn-rg` globalmente en `vue3/src/assets/themes.css`:
   ```html
   <p class="beacon-card__meta">
     Instance ID (HMAC-SHA256): <code class="beacon-mono">{{ beaconStatus?.instance_id || 'anónimo' }}</code> |
     Flota: <strong class="beacon-fleet">{{ beaconStatus?.router_count ?? beaconStatus?.fleet_bucket ?? '0' }} routers ({{ beaconStatus?.fleet_bucket || '0' }})</strong> |
     Último Latido: <span class="beacon-timestamp">{{ beaconStatus?.last_sent_at || beaconStatus?.last_heartbeat_at || 'Nunca' }}</span>
     <span v-if="beaconStatus?.last_status && beaconStatus.last_status !== 'untriggered'" class="beacon-status-code">[{{ beaconStatus.last_status }}]</span>
   </p>
   ```

---

### Paso 2.3: Pruebas Unitarias y Escenarios BDD Karate Labs (Pirámide 11X)

1. **Backend (`fastapi/tests/workers/test_telemetry_beacon_worker.unit.py`):**
   - Actualizar `test_count_active_routers_safe_success` verificando que `set_tenant_context` sea invocado con `(mock_session, None, is_superadmin=True)`.
   - Actualizar `test_get_telemetry_beacon_status_with_and_without_state` verificando que el diccionario devuelto incluya `fleet_bucket`, `router_count` y `last_heartbeat_at == last_sent_at`.
2. **Frontend (`vue3/src/views/admin/tenantsManagementView.unit.ts`):**
   - Añadir prueba unitaria verificando que `.beacon-card` muestre `last_sent_at`, `router_count`, `fleet_bucket` y `[http_202]` tras cargar el estado o disparar `#btn-trigger-beacon`.
3. **Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + réplicas en `docs/examples/`):**
   - Añadir validación de contrato en `api_test.feature` asegurando que `GET /api/v1/system/telemetry-beacon/status` incluya `fleet_bucket`, `router_count`, `last_sent_at` y `last_heartbeat_at`.

---

## 3. Criterios de Aceptación y Comandos de Certificación (Regla Cero)

```bash
# 1. Reconstruir imágenes locales de prueba
docker build -t sinfallas/rosgrid-backend:local-test -f fastapi/Dockerfile fastapi/
docker build -t sinfallas/rosgrid-frontend:local-test -f vue3/Dockerfile vue3/

# 2. Ejecutar suite unitaria backend y frontend en contenedores efímeros
make test-backend
make test-frontend
make lint

# 3. Recrear entorno local de producción y verificar en vivo
docker compose -f docker-compose.prod.local.yml up -d --force-recreate
./.agents/scripts/certify_task_completion.sh
```
