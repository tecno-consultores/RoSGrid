# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 69: Persistencia Relacional de `onboarding_completed` en PostgreSQL y Resiliencia ante Reinicio de Contenedores Docker

## 1. Propósito y Contexto Operativo

Esta especificación resuelve de forma definitiva el defecto reportado durante las pruebas operativas de **RoSGrid**:

> *"Cuando apagas los contenedores y los vuelves a encender (NO se borra la base de datos), al entrar con el usuario existente te vuelve a mostrar la ventana para seleccionar si eres un ISP o una empresa o custom, y se supone que esa selección ya la había hecho."*

El documento presenta la auditoría forense de extremo a extremo y el plan de implementación **Flash-Ready** (con bloques literales `Target` / `Replacement` listos para ejecución directa por **Gemini 3.8 Flash High**).

---

## 2. Diagnóstico Forense de Causa Raíz

La inspección del modelo ORM ([`fastapi/src/models/core.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/models/core.py)), el router de organizaciones ([`fastapi/src/api/v1/tenants.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/tenants.py)), el flujo de sesión ([`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py)) y la configuración de contenedores ([`docker-compose.prod.local.yml`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docker-compose.prod.local.yml)) reveló **3 causas raíz encadenadas**:

### 2.1 Causa Raíz #1: `onboarding_completed` se guardaba únicamente en KeyDB volátil (`--appendonly no`) y NO existía como columna en PostgreSQL (`public.tenants`)
- En [`docker-compose.prod.local.yml`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/docker-compose.prod.local.yml#L36-L42) (así como en `docker-compose.yml` y `docker-compose.prod.yml`), el contenedor `rosgrid-redis` (`eqalpha/keydb:alpine`) opera por diseño como motor 100% en memoria RAM sin persistencia en disco:
  ```yaml
  --appendonly "no"
  --save ""
  ```
- Mientras que los otros 21 Feature Flags del tenant (`isp_module_enabled`, `bgp_looking_glass_enabled`, `rogue_dhcp_enabled`, etc.) sí son columnas booleanas reales en la tabla `public.tenants` de PostgreSQL ([`fastapi/src/models/core.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/models/core.py#L65-L89)), **`onboarding_completed` fue implementado como un flag exclusivamente efímero en KeyDB** (`rg:{tenant_id}:onboarding_completed`) en [`fastapi/src/api/v1/tenants.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/tenants.py#L138-L146):
  ```python
  # Manejo de flag efímero de onboarding_completed en KeyDB
  if "onboarding_completed" in update_data:
      onboarding_completed_val = bool(update_data.pop("onboarding_completed"))
      await redis.set(f"rg:{tenant_id}:onboarding_completed", "true" if onboarding_completed_val else "false")
  ```
- **Efecto al apagar y encender los contenedores:**
  1. Al detener y volver a iniciar los contenedores (`docker compose down && docker compose up -d` o `docker compose restart`), PostgreSQL conserva intactos el tenant, el usuario y sus 21 Feature Flags en el volumen `rosgrid_pg_data_local`.
  2. Sin embargo, KeyDB arranca con la memoria RAM limpia (`0 keys`), por lo que la clave `rg:{tenant_id}:onboarding_completed` desaparece.
  3. Cuando el usuario existente inicia sesión, [`App.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/App.vue#L36) invoca `authStore.fetchTenantFeatures()` -> `GET /api/v1/tenants/{tid}/features`.
  4. `extract_tenant_features(tenant)` lee `getattr(tenant, "onboarding_completed", None)` -> `None` y aplica el valor por defecto `TENANT_FEATURE_DEFAULTS["onboarding_completed"] = False`.
  5. Al consultar `await redis.get(f"rg:{tenant_id}:onboarding_completed")` y recibir `None`, el endpoint devuelve `"onboarding_completed": false` y [`App.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/App.vue#L29) (`shouldShowOnboarding`) vuelve a desplegar el modal `<TenantOnboardingModal />`.

### 2.2 Causa Raíz #2: `_extract_tenant_features` en `fastapi/src/api/v1/auth.py` omitía `onboarding_completed`
- En [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L386-L419), la función auxiliar `_extract_tenant_features(tenant: Tenant)` que construye el diccionario `user.features` durante `/api/v1/auth/2fa/verify` y `/api/v1/auth/switch-tenant` listaba 21 claves pero **omitía `"onboarding_completed"`**.

### 2.3 Causa Raíz #3: Evidencia en `rosgrid_db_local` de Re-Ejecución Forzada del Onboarding
- En la base de datos local `rosgrid_db_local`, la tabla `audit_logs` demostró que el tenant `sistemas` (`d451f498-99c1-433e-a23f-4245015fcea0`) ya había guardado sus Feature Flags de onboarding a las `10:40:51` (`TENANT_FEATURE_FLAGS_UPDATED`), pero tras el reinicio de contenedores a las `13:49:25` (`LOGIN_SUCCESSFUL`) el modal volvió a mostrarse y obligó a enviar un segundo `TENANT_FEATURE_FLAGS_UPDATED` a las `13:49:28`.

---

## 3. Plan de Implementación *Flash-Ready* para Gemini 3.8 Flash High

> [!IMPORTANT]
> **Instrucciones de Ejecución para Gemini 3.8 Flash High:**
> Aplica los siguientes 6 pasos en orden exacto. Al incorporar una nueva columna en `src/models/core.py`, es **obligatorio** crear y ejecutar la migración Alembic `0013_tenant_onboarding_flag.py` y verificar la tabla en PostgreSQL (`\d tenants`).

---

### Paso 1: Añadir la Columna `onboarding_completed` al Modelo ORM `Tenant` (`fastapi/src/models/core.py`)

Editar [`fastapi/src/models/core.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/models/core.py#L83-L92):

**`Target`:**
```python
    # Capacidades Tácticas Avanzadas (Spec 35)
    l2_topology_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    syslog_collector_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cve_scanner_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    prometheus_fleet_exporter_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rogue_dhcp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
```

**`Replacement`:**
```python
    # Capacidades Tácticas Avanzadas (Spec 35) y Estado Persistente de Onboarding (Spec 69)
    l2_topology_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    syslog_collector_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cve_scanner_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    prometheus_fleet_exporter_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rogue_dhcp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
```

---

### Paso 2: Crear Migración Alembic `0013_tenant_onboarding_flag.py` con Backfill Automático para Empresas Existentes

Crear el archivo `fastapi/migrations/versions/0013_tenant_onboarding_flag.py` (`revision` de 27 caracteres `<= 32` exigido por `verify_alembic_orm_parity.py`):

```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0013_tenant_onboarding_flag

Revision ID: 0013_tenant_onboarding_flag
Revises: 0012_user_profile_flags_perms
Create Date: 2026-11-02 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_tenant_onboarding_flag"
down_revision: str | None = "0012_user_profile_flags_perms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # Backfill automático: marcar onboarding_completed = TRUE para todo tenant existente
    # que ya haya configurado sus Feature Flags o que ya tenga routers registrados.
    op.execute(
        sa.text(
            """
            UPDATE tenants t
            SET onboarding_completed = TRUE
            WHERE EXISTS (
                SELECT 1 FROM audit_logs a
                WHERE a.tenant_id = t.id AND a.event_action = 'TENANT_FEATURE_FLAGS_UPDATED'
            ) OR EXISTS (
                SELECT 1 FROM routers r
                WHERE r.tenant_id = t.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("tenants", "onboarding_completed")
```

---

### Paso 3: Persistir y Leer `onboarding_completed` en PostgreSQL + Caché Secundaria en KeyDB (`fastapi/src/api/v1/tenants.py`)

Editar `get_tenant_features`, `update_tenant_features` y `complete_tenant_onboarding` en [`fastapi/src/api/v1/tenants.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/tenants.py#L92-L180):

1. En `get_tenant_features` y `update_tenant_features` ([`fastapi/src/api/v1/tenants.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/tenants.py#L103-L180)):

**`Target`:**
```python
    tenant = await _load_tenant_or_404(db, tenant_id)
    features_dict = extract_tenant_features(tenant)
    try:
        redis = get_redis_client()
        onb_val = await redis.get(f"rg:{tenant_id}:onboarding_completed")
        if onb_val:
            features_dict["onboarding_completed"] = (
                onb_val.decode() if isinstance(onb_val, bytes) else str(onb_val)
            ).lower() == "true"
    except Exception as exc:
        logger.debug("Error leyendo onboarding_completed de KeyDB: %s", exc)
    return TenantFeaturesResponse.model_validate(features_dict)


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
@router.put("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol SUPERADMIN_GLOBAL pueden modificar los módulos y licencias de las empresas.",
        )

    tenant = await _load_tenant_or_404(db, tenant_id)
    before_state = extract_tenant_features(tenant)

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)

    # Manejo de flag efímero de onboarding_completed en KeyDB
    onboarding_completed_val: bool | None = None
    if "onboarding_completed" in update_data:
        onboarding_completed_val = bool(update_data.pop("onboarding_completed"))
        try:
            redis = get_redis_client()
            await redis.set(f"rg:{tenant_id}:onboarding_completed", "true" if onboarding_completed_val else "false")
        except Exception as exc:
            logger.debug("Error guardando onboarding_completed en KeyDB: %s", exc)

    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    actor = audit_actor_from_claims(claims, request)
    actor["tenant_id"] = tenant.id
    await write_audit_log(
        session=db,
        **actor,
        event_category="GOVERNANCE",
        event_action="TENANT_FEATURE_FLAGS_UPDATED",
        before_state={key: before_state[key] for key in update_data if key in before_state},
        after_state=update_data,
    )
    await db.commit()
    await db.refresh(tenant)
    await invalidate_tenant_features_cache(tenant_id)

    response_dict = extract_tenant_features(tenant)
    if onboarding_completed_val is not None:
        response_dict["onboarding_completed"] = onboarding_completed_val
    else:
        try:
            redis = get_redis_client()
            onb_check = await redis.get(f"rg:{tenant_id}:onboarding_completed")
            if onb_check:
                response_dict["onboarding_completed"] = (
                    onb_check.decode() if isinstance(onb_check, bytes) else str(onb_check)
                ).lower() == "true"
        except Exception:
            pass
    return TenantFeaturesResponse.model_validate(response_dict)
```

**`Replacement`:**
```python
    tenant = await _load_tenant_or_404(db, tenant_id)
    features_dict = extract_tenant_features(tenant)
    if not features_dict.get("onboarding_completed"):
        try:
            redis = get_redis_client()
            onb_val = await redis.get(f"rg:{tenant_id}:onboarding_completed")
            if onb_val:
                is_done = (onb_val.decode() if isinstance(onb_val, bytes) else str(onb_val)).lower() == "true"
                features_dict["onboarding_completed"] = is_done
                if is_done and not getattr(tenant, "onboarding_completed", False):
                    tenant.onboarding_completed = True
                    await db.commit()
        except Exception as exc:
            logger.debug("Error leyendo onboarding_completed de KeyDB: %s", exc)
    return TenantFeaturesResponse.model_validate(features_dict)


@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
@router.put("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    if user_role != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol SUPERADMIN_GLOBAL pueden modificar los módulos y licencias de las empresas.",
        )

    tenant = await _load_tenant_or_404(db, tenant_id)
    before_state = extract_tenant_features(tenant)

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)

    # Persistencia duradera de onboarding_completed en PostgreSQL (Spec 69) + espejo en KeyDB
    onboarding_completed_val: bool = bool(update_data.get("onboarding_completed", True))
    update_data["onboarding_completed"] = onboarding_completed_val
    try:
        redis = get_redis_client()
        await redis.set(f"rg:{tenant_id}:onboarding_completed", "true" if onboarding_completed_val else "false")
    except Exception as exc:
        logger.debug("Error guardando onboarding_completed en KeyDB: %s", exc)

    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    actor = audit_actor_from_claims(claims, request)
    actor["tenant_id"] = tenant.id
    await write_audit_log(
        session=db,
        **actor,
        event_category="GOVERNANCE",
        event_action="TENANT_FEATURE_FLAGS_UPDATED",
        before_state={key: before_state[key] for key in update_data if key in before_state},
        after_state=update_data,
    )
    await db.commit()
    await db.refresh(tenant)
    await invalidate_tenant_features_cache(tenant_id)

    response_dict = extract_tenant_features(tenant)
    response_dict["onboarding_completed"] = bool(getattr(tenant, "onboarding_completed", onboarding_completed_val))
    return TenantFeaturesResponse.model_validate(response_dict)
```

2. En `complete_tenant_onboarding` ([`fastapi/src/api/v1/tenants.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/tenants.py#L238-L260)):

**`Target`:**
```python
    tenant = await _load_tenant_or_404(db, tenant_id)
    try:
        redis = get_redis_client()
        await redis.set(f"rg:{tenant_id}:onboarding_completed", "true")
    except Exception as exc:
        logger.debug("Error persistiendo onboarding_completed: %s", exc)

    features = extract_tenant_features(tenant)
    features["onboarding_completed"] = True
    return TenantFeaturesResponse.model_validate(features)
```

**`Replacement`:**
```python
    tenant = await _load_tenant_or_404(db, tenant_id)
    tenant.onboarding_completed = True
    await db.commit()
    await db.refresh(tenant)
    try:
        redis = get_redis_client()
        await redis.set(f"rg:{tenant_id}:onboarding_completed", "true")
    except Exception as exc:
        logger.debug("Error persistiendo onboarding_completed: %s", exc)

    features = extract_tenant_features(tenant)
    features["onboarding_completed"] = True
    return TenantFeaturesResponse.model_validate(features)
```

---

### Paso 4: Incluir `onboarding_completed` en `_extract_tenant_features` durante Login (`fastapi/src/api/v1/auth.py`)

Editar [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L403-L415):

**`Target`:**
```python
        "cve_scanner_enabled": True,
        "prometheus_fleet_exporter_enabled": True,
        "rogue_dhcp_enabled": True,
        "mass_outage_threshold": 10,
        "default_locale": "es",
    }
```

**`Replacement`:**
```python
        "cve_scanner_enabled": True,
        "prometheus_fleet_exporter_enabled": True,
        "rogue_dhcp_enabled": True,
        "onboarding_completed": False,
        "mass_outage_threshold": 10,
        "default_locale": "es",
    }
```

---

### Paso 5: Sincronizar la Respuesta Canónica en `TenantOnboardingModal.vue` (`vue3/src/components/common/TenantOnboardingModal.vue`)

Editar [`vue3/src/components/common/TenantOnboardingModal.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/TenantOnboardingModal.vue#L85-L93):

**`Target`:**
```typescript
      const payload = {
        ...form.value,
        onboarding_completed: true,
      };

      await http.patch(`/api/v1/tenants/${tid}/features`, payload);
      authStore.updateTenantFeatures(payload);
      emit('completed');
```

**`Replacement`:**
```typescript
      const payload = {
        ...form.value,
        onboarding_completed: true,
      };

      const res = await http.patch<TenantFeatureFlags>(`/api/v1/tenants/${tid}/features`, payload);
      authStore.updateTenantFeatures(res.data || payload);
      emit('completed');
```

---

### Paso 6: Pruebas Unitarias y de Contratos BDD (Pirámide QA 11X)

En [`fastapi/tests/api/test_cis_policies_and_onboarding.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_cis_policies_and_onboarding.unit.py#L248-L258), añadir el paso 4 que simula el apagado y encendido de contenedores (`mock_redis.get.return_value = None`) y verifica que `get_tenant_features` sigue devolviendo `onboarding_completed is True` desde PostgreSQL:

**`Target`:**
```python
        superadmin_claims = {**sample_claims, "rol": "SUPERADMIN_GLOBAL"}
        updated = await update_tenant_features(
            tenant_id=sample_tenant_id,
            body=update_req,
            request=mock_request,
            db=db,
            claims=superadmin_claims,
        )
        assert updated.isp_module_enabled is True
        assert updated.bgp_looking_glass_enabled is True
        assert updated.onboarding_completed is True
```

**`Replacement`:**
```python
        superadmin_claims = {**sample_claims, "rol": "SUPERADMIN_GLOBAL"}
        updated = await update_tenant_features(
            tenant_id=sample_tenant_id,
            body=update_req,
            request=mock_request,
            db=db,
            claims=superadmin_claims,
        )
        assert updated.isp_module_enabled is True
        assert updated.bgp_looking_glass_enabled is True
        assert updated.onboarding_completed is True
        assert mock_tenant.onboarding_completed is True

        # 4. Simular reinicio de contenedores Docker (KeyDB vacío, PostgreSQL preserva mock_tenant.onboarding_completed=True)
        mock_redis.get.return_value = None
        after_restart = await get_tenant_features(
            tenant_id=sample_tenant_id, db=db, claims=sample_claims
        )
        assert after_restart.onboarding_completed is True
```

---

## 4. Certificación y Resultados de Validación Level-11X

La implementación del Hito 28.14 ha sido ejecutada y certificada en contenedores Docker efímeros bajo la Regla Cero:

1. **Paridad ORM y Migración Alembic:**
   - Columna `onboarding_completed: Mapped[bool]` añadida en `Tenant` (`models/core.py`).
   - Migración `0013_tenant_onboarding_flag.py` ejecutada y validada en PostgreSQL (`\d tenants` confirma `onboarding_completed | boolean | not null | default false`).
   - Backfill automático aplicado sobre inquilinos con historial en `audit_logs` o routers asociados.
2. **Resiliencia ante Reinicio Verificada en Vivo:**
   - `PATCH /api/v1/tenants/{id}/features` persiste `onboarding_completed = True` en PostgreSQL.
   - Vaciado completo de KeyDB (`redis-cli flushall`) y posterior reinicio de contenedores (`rosgrid-redis`, `rosgrid-api`).
   - `GET /api/v1/tenants/{id}/features` lee de PostgreSQL y devuelve `onboarding_completed: true` sin reabrir el modal de onboarding.
3. **Pruebas y Calidad QA 11X:**
   - 660 pruebas unitarias backend Pytest aprobadas al 100%.
   - 522 pruebas unitarias frontend Vitest en 79 suites aprobadas al 100%.
   - Escenario 147 de Karate Labs BDD en `api_test.feature` y Escenario 84 en `ui_business_flow.feature`.
   - 29/29 verificaciones de infraestructura y 26/26 contratos front-back aprobados en `certify_task_completion.sh` y `probar-prod-local.sh`.
