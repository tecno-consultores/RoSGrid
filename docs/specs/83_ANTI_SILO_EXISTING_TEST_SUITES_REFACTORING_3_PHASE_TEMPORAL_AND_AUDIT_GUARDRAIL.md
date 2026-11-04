# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 83: Refactorización Integral de las Suites de Pruebas Existentes bajo el Criterio Anti-Silo (Propagación Transversal, 3 Fases Temporales, Erradicación de los 49 Mocks Ciegos de `write_audit_log` y Guardrail Estático `verify_anti_silo_test_quality.py` — `Subhito 30.5`)

> **Hito de Referencia:** Hito 30 (Subhito `30.5`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Estado:** Especificación *Flash-Ready* lista para ejecución determinista  
> **Regla de Gobernanza Asociada:** `.agents/rules/mandatory_qa_pyramid_and_doc_sync.md` (Sección `1.5 Anti-Silo Cross-Module State Propagation, 3-Phase Temporal Lifecycle & Semantic Audit Invariant`)

---

## 1. Diagnóstico Forense de las Suites de Pruebas Existentes

Al auditar la totalidad de `fastapi/tests/` y `vue3/src/` frente al nuevo criterio **Anti-Silo de Propagación Transversal, Ciclo de Vida Temporal de 3 Fases y Auditoría Semántica Anti-UUID**, se identificaron **3 brechas estructurales en las pruebas preexistentes**:

1. **49 Mocks Ciegos de `write_audit_log` en 12 Archivos de Prueba de Backend (`patch("...write_audit_log", AsyncMock())` sin captura ni validación):**
   - Los siguientes **12 archivos** todavía reemplazan `write_audit_log` por un `AsyncMock()` vacío sin `as mock_audit` ni validación de argumentos:
     1. `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (`8` ocurrencias: líneas `251`, `289`, `316`, `362`, `402`, `462`, `468`, `515`)
     2. `fastapi/tests/api/test_operations_endpoints_full.unit.py` (`3` ocurrencias: líneas `241`, `412`, `932`)
     3. `fastapi/tests/api/test_hito16_full_coverage.unit.py` (`5` ocurrencias: líneas `287`, `589`, `603`, `643`, `749`)
     4. `fastapi/tests/api/test_hito20_enterprise_suite.unit.py` (`5` ocurrencias: líneas `301`, `360`, `413`, `482`, `826`)
     5. `fastapi/tests/api/test_hito23_mcp_tools.unit.py` (`1` ocurrencia: línea `251`)
     6. `fastapi/tests/api/test_network_services_and_qos.unit.py` (`5` ocurrencias: líneas `191`, `209`, `285`, `312`, `377`)
     7. `fastapi/tests/api/test_orphan_parity_and_layer2_singleton.unit.py` (`2` ocurrencias: líneas `137`, `167`)
     8. `fastapi/tests/api/test_switch_tenant.unit.py` (`1` ocurrencia: línea `227`)
     9. `fastapi/tests/api/test_webfig_endpoints_full.unit.py` (`1` ocurrencia: línea `572`)
     10. `fastapi/tests/api/test_webfig_layer2_universal.unit.py` (`1` ocurrencia: línea `312`)
     11. `fastapi/tests/rbac/test_rbac_30_actions_and_user_overrides.unit.py` (`1` ocurrencia: línea `195`)
     12. `fastapi/tests/test_mcp_endpoint.unit.py` (`16` ocurrencias: líneas `334`, `370`, `408`, `448`, `505`, `546`, `583`, `873`, `912`, `956`, `980`, `1028`, `1053`, `1091`, `1129`, `1171`)
   - Como estos mocks no inspeccionan los argumentos recibidos, cualquier endpoint que pase un UUID crudo o deje `event_action` vacío pasa el test en verde silenciosamente.

2. **Pruebas Preexistentes que Terminan en la Mutación sin Verificar el Consumidor Aguas Abajo (*Silo Testing*):**
   - En `test_maintenance_window_endpoints` (`test_inventory_and_vault_endpoints_full.unit.py` líneas `423–518`), el test crea y cancela ventanas de mantenimiento pero no invoca inmediatamente `resolve_active_maintenance_router_ids` + `build_router_response` sobre las mismas instancias creadas para certificar la transición `PRODUCTION -> MAINTENANCE -> PRODUCTION`.
   - En `test_approvals_endpoints` (`test_operations_endpoints_full.unit.py` líneas `238–250`), al aprobar una solicitud Maker-Checker no se verifica en el mismo flujo que se despache el evento en tiempo real `MAKER_CHECKER_RESOLVED` ni que el registro de auditoría contenga `event_action == "APPROVAL_GRANTED_AND_EXECUTED"`.
   - En `vue3/src/views/views.unit.ts`, los tests de `DashboardHomeView.vue` y `NocWallboardView.vue` prueban cada vista por separado en lugar de verificar que una misma mutación en `useInventoryStore` (`admin_state = 'MAINTENANCE'`) actualice de forma coherente el contador del Centro de Mando (`🛠️ 1 mant.`), el KPI del Wallboard (`MANTENIMIENTO: 1`) y la clasificación semántica de eventos sin UUIDs crudos.

3. **Falta de Aserción Explícita de las 3 Fases Temporales en Suites de Safe Mode (60s) y Bóveda Step-Up (30s):**
   - En `fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py` y `vue3/src/components/common/RgSafeModeBanner.unit.ts`, las pruebas están fragmentadas por método individual pero carecen de un test unificado del **ciclo de vida temporal de 3 fases** (`Fase 1: Pre-mutación / Inyección de scheduler`, `Fase 2: Ventana activa 60s con scheduler vivo y verificación en vivo`, `Fase 3: Confirmación o Expiración/Rollback transaccional`).
   - En `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (`test_vault_endpoints`), falta validar el ciclo de 3 fases de revelación Step-Up (`Fase 1: Rechazo 401 con TOTP inválido`, `Fase 2: Revelación activa con ventana de 30s y auditoría verificada`, `Fase 3: Rotación de clave actualizando current_password y desplazando la anterior a previous_password`).

---

## 2. Instrucciones de Implementación Paso a Paso (Flash-Ready)

### Paso 1: Incorporar `make_asserting_audit_mock` en `fastapi/tests/conftest.py`

Añadir al final de `fastapi/tests/conftest.py` el helper canónico `make_asserting_audit_mock` que valida automáticamente en cada llamada a `write_audit_log` que `tenant_id`, `event_category` y `event_action` estén presentes y que `actor_username` sea válido o cuente con `actor_user_id` para resolución humana:

**`Target` al final de `fastapi/tests/conftest.py` (líneas 385–390):**
```python
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
```

**`Replacement` al final de `fastapi/tests/conftest.py`:**
```python
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def make_asserting_audit_mock(return_value: Any = None) -> Any:
    """Crea un AsyncMock para write_audit_log que valida invariantes Anti-Silo y Anti-UUID en cada invocación."""
    import re
    import uuid
    from unittest.mock import AsyncMock, MagicMock

    uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

    async def _side_effect(*args: Any, **kwargs: Any) -> Any:
        event_category = kwargs.get("event_category") or (args[5] if len(args) > 5 else None)
        event_action = kwargs.get("event_action") or (args[6] if len(args) > 6 else None)
        actor_username = kwargs.get("actor_username") or (args[2] if len(args) > 2 else None)
        actor_user_id = kwargs.get("actor_user_id")

        assert event_category and str(event_category).strip(), "write_audit_log invocado sin event_category"
        assert event_action and str(event_action).strip(), "write_audit_log invocado sin event_action"
        assert actor_username and str(actor_username).strip(), "write_audit_log invocado sin actor_username"

        # Si actor_username parece un UUID crudo, exigir que se haya provisto session o actor_user_id para resolución
        if uuid_re.match(str(actor_username).strip()):
            session_arg = kwargs.get("session") or (args[0] if len(args) > 0 else None)
            assert session_arg is not None or actor_user_id is not None, (
                f"UUID crudo en actor_username ({actor_username}) sin session ni actor_user_id para resolución"
            )

        if return_value is not None:
            return return_value
        entry = MagicMock()
        entry.id = uuid.uuid4()
        entry.event_category = str(event_category)
        entry.event_action = str(event_action)
        entry.actor_username = (
            "resolved_operator" if uuid_re.match(str(actor_username).strip()) else str(actor_username)
        )
        return entry

    return AsyncMock(side_effect=_side_effect)
```

---

### Paso 2: Refactorizar `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (Erradicación de 8 Mocks Ciegos + Propagación Transversal y 3 Fases Temporales en Vault y Maintenance)

1. Importar `make_asserting_audit_mock` desde `tests.conftest` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py`:

**`Target` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (líneas 1–16):**
```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import HTTPException
import pyotp
import pytest
```

**`Replacement` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py`:**
```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import HTTPException
import pyotp
import pytest
from tests.conftest import make_asserting_audit_mock
```

2. Reemplazar los 8 mocks ciegos en `test_router_crud_and_discovery_endpoints`, `test_csv_import_endpoints`, `test_vault_endpoints` y `test_maintenance_window_endpoints`, e incorporar la verificación de las 3 fases temporales y propagación transversal en `test_vault_endpoints` y `test_maintenance_window_endpoints`:

**`Target` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (líneas 248–321):**
```python
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock),
    ):
        # 1. Create router
        created = await create_router(create_payload, fake_request, claims, db)
        assert created.display_name == "New-Router"

        # 2. Update router
        db.get.return_value = test_router_full
        db.execute.return_value = MockDbResult([test_router_full])
        upd_payload = UpdateRouterRequest(
            display_name="Updated-Router",
            tags=["new-tag"],
            api_username="new_admin",
            api_password="new_password_123",
        )
        updated = await update_router(test_router_full.id, upd_payload, fake_request, claims, db)
        assert updated.display_name == "Updated-Router"

        # 3. Delete router
        await delete_router(test_router_full.id, fake_request, claims, db)
        db.delete.assert_awaited_once_with(test_router_full)

    # 4. Sync discovery
    db.get.return_value = test_router_full
    fake_client = AsyncMock()
    fake_client_cm = AsyncMock()
    fake_client_cm.__aenter__.return_value = fake_client
    fake_router_with_vault = test_router_full

    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.perform_discovery", new_callable=AsyncMock),
        patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock),
    ):
        synced = await sync_discovery(test_router_full.id, claims, db)
        assert synced.id == test_router_full.id

    # repin_ssl
    totp_secret = pyotp.random_base32()
    user = User(id=u_id, tenant_id=t_id, totp_enabled=True)
    aad_u = f"{t_id}:{u_id}".encode()
    ct_u, iv_u, tag_u = encrypt_aes_gcm(totp_secret.encode(), aad_u)
    user.totp_secret_ciphertext = ct_u
    user.totp_secret_iv = iv_u
    user.totp_secret_tag = tag_u

    def _mock_get(model: Any, obj_id: Any) -> Any:
        if model == User:
            return user
        return fake_router_with_vault

    db.get.side_effect = _mock_get
    valid_totp = pyotp.TOTP(totp_secret).now()
    repin_payload = SslRepinRequest(
        totp_code=valid_totp,
        reason="Certificate renewed on router",
        expected_new_sha256_fingerprint="b" * 64,
    )

    with patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock):
        repin_res = await repin_ssl(test_router_full.id, repin_payload, fake_request, claims, db)
        assert repin_res["status"] == "SUCCESS"
        assert repin_res["fingerprint"] == "b" * 64
```

**`Replacement` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py`:**
```python
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_inv_audit,
    ):
        # 1. Create router
        created = await create_router(create_payload, fake_request, claims, db)
        assert created.display_name == "New-Router"

        # 2. Update router
        db.get.return_value = test_router_full
        db.execute.return_value = MockDbResult([test_router_full])
        upd_payload = UpdateRouterRequest(
            display_name="Updated-Router",
            tags=["new-tag"],
            api_username="new_admin",
            api_password="new_password_123",
        )
        updated = await update_router(test_router_full.id, upd_payload, fake_request, claims, db)
        assert updated.display_name == "Updated-Router"

        # 3. Delete router
        await delete_router(test_router_full.id, fake_request, claims, db)
        db.delete.assert_awaited_once_with(test_router_full)
        assert mock_inv_audit.await_count >= 3

    # 4. Sync discovery
    db.get.return_value = test_router_full
    fake_client = AsyncMock()
    fake_client_cm = AsyncMock()
    fake_client_cm.__aenter__.return_value = fake_client
    fake_router_with_vault = test_router_full

    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.perform_discovery", new_callable=AsyncMock),
        patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_disc_audit,
    ):
        synced = await sync_discovery(test_router_full.id, claims, db)
        assert synced.id == test_router_full.id
        mock_disc_audit.assert_awaited_once()

    # repin_ssl
    totp_secret = pyotp.random_base32()
    user = User(id=u_id, tenant_id=t_id, totp_enabled=True)
    aad_u = f"{t_id}:{u_id}".encode()
    ct_u, iv_u, tag_u = encrypt_aes_gcm(totp_secret.encode(), aad_u)
    user.totp_secret_ciphertext = ct_u
    user.totp_secret_iv = iv_u
    user.totp_secret_tag = tag_u

    def _mock_get(model: Any, obj_id: Any) -> Any:
        if model == User:
            return user
        return fake_router_with_vault

    db.get.side_effect = _mock_get
    valid_totp = pyotp.TOTP(totp_secret).now()
    repin_payload = SslRepinRequest(
        totp_code=valid_totp,
        reason="Certificate renewed on router",
        expected_new_sha256_fingerprint="b" * 64,
    )

    with patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_repin_audit:
        repin_res = await repin_ssl(test_router_full.id, repin_payload, fake_request, claims, db)
        assert repin_res["status"] == "SUCCESS"
        assert repin_res["fingerprint"] == "b" * 64
        mock_repin_audit.assert_awaited_once()
```

**`Target` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py` (líneas 360–519):**
```python
    with patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock):
        commit_res = await import_csv_commit(fake_request, claims, db)
        assert commit_res.imported_count == 1
        assert len(commit_res.created_router_ids) == 1


# ============================================================================
# VAULT ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_vault_endpoints(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    t_id = test_router_full.tenant_id
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    totp_secret = pyotp.random_base32()
    user = User(id=u_id, tenant_id=t_id, totp_enabled=True)
    aad_u = f"{t_id}:{u_id}".encode()
    ct_u, iv_u, tag_u = encrypt_aes_gcm(totp_secret.encode(), aad_u)
    user.totp_secret_ciphertext = ct_u
    user.totp_secret_iv = iv_u
    user.totp_secret_tag = tag_u

    def _mock_get(model: Any, obj_id: Any) -> Any:
        if model == User:
            return user
        return test_router_full

    db.get.side_effect = _mock_get
    db.execute.return_value = MockDbResult([test_router_full])

    valid_code = pyotp.TOTP(totp_secret).now()
    reveal_payload = VaultRevealRequest(totp_code=valid_code, reason="Emergency audit inspection")

    with patch("src.api.v1.vault.write_audit_log", new_callable=AsyncMock):
        # 1. Reveal
        fake_response = MagicMock()
        rev = await reveal_credentials(test_router_full.id, reveal_payload, fake_request, fake_response, claims, db)
        assert rev.api_username == "admin"
        assert rev.current_password == "admin_password"

        # 2. Rotate now (success on MikroTik)
        fake_client = AsyncMock()
        fake_client.get.return_value = [{".id": "*1", "name": "admin"}]
        fake_client_cm = AsyncMock()
        fake_client_cm.__aenter__.return_value = fake_client

        with patch("src.api.v1.vault.MikrotikRestClient", return_value=fake_client_cm):
            rot_res = await rotate_router_credentials_now(test_router_full.id, fake_request, claims, db)
            assert rot_res.rotation_status == "SUCCESS"
            assert rot_res.router_id == test_router_full.id


# ============================================================================
# MAINTENANCE WINDOWS ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_maintenance_window_endpoints(fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    now = datetime.now(UTC)
    mw = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=t_id,
        router_id=r_id,
        title="Nightly Upgrade",
        reason="Scheduled OS patch",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        suppress_alerts=True,
        is_cancelled=False,
        created_by=u_id,
        created_at=now,
    )
    db.execute.return_value = MockDbResult([mw])

    # 1. List
    windows = await list_maintenance_windows(router_id=None, is_active=None, is_cancelled=None, claims=claims, db=db)
    assert len(windows) == 1
    assert windows[0].title == "Nightly Upgrade"

    # 2. Create
    create_mw_req = CreateMaintenanceWindowRequest(
        title="Emergency Fix",
        reason="Fix route loop",
        router_id=r_id,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        suppress_alerts=True,
    )
    with patch("src.api.v1.maintenance.write_audit_log", new_callable=AsyncMock):
        created_mw = await create_maintenance_window(create_mw_req, fake_request, claims, db)
        assert created_mw.title == "Emergency Fix"

    # 3. Cancel
    db.get.return_value = mw
    with patch("src.api.v1.maintenance.write_audit_log", new_callable=AsyncMock):
        cancelled = await cancel_maintenance_window(mw.id, fake_request, claims, db)
        assert cancelled.is_cancelled is True

    # 4. Validation error: ends_at <= starts_at
    bad_dates_mw = CreateMaintenanceWindowRequest(
        title="Bad Dates",
        reason="Testing validation",
        router_id=r_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now,
        suppress_alerts=True,
    )
    with pytest.raises(HTTPException) as exc_dates:
        await create_maintenance_window(bad_dates_mw, fake_request, claims, db)
    assert exc_dates.value.status_code == 400

    # 5. Validation error: neither router_id nor target_tag
    no_target_mw = CreateMaintenanceWindowRequest(
        title="No Target",
        reason="Testing validation",
        router_id=None,
        target_tag=None,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        suppress_alerts=True,
    )
    with pytest.raises(HTTPException) as exc_target:
        await create_maintenance_window(no_target_mw, fake_request, claims, db)
    assert exc_target.value.status_code == 400

    # 6. Cancel 404 error
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_cancel:
        await cancel_maintenance_window(uuid.uuid4(), fake_request, claims, db)
    assert exc_cancel.value.status_code == 404

    # 7. Create with multiple router_ids
    r2_id = uuid.uuid4()
    multi_mw_req = CreateMaintenanceWindowRequest(
        title="Multi Router Patch",
        reason="Core cluster upgrade",
        router_ids=[r_id, r2_id],
        starts_at=now,
        ends_at=now + timedelta(hours=3),
        suppress_alerts=True,
    )
    with patch("src.api.v1.maintenance.write_audit_log", new_callable=AsyncMock):
        multi_mw = await create_maintenance_window(multi_mw_req, fake_request, claims, db)
        assert multi_mw.title == "Multi Router Patch"
```

**`Replacement` en `fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py`:**
```python
    with patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_csv_audit:
        commit_res = await import_csv_commit(fake_request, claims, db)
        assert commit_res.imported_count == 1
        assert len(commit_res.created_router_ids) == 1
        mock_csv_audit.assert_awaited_once()


# ============================================================================
# VAULT ENDPOINTS (3 Fases Temporales Step-Up 30s + Propagación Criptográfica)
# ============================================================================


@pytest.mark.asyncio
async def test_vault_endpoints(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    t_id = test_router_full.tenant_id
    u_id = uuid.uuid4()
    claims = {
        "tid": str(t_id),
        "sub": str(u_id),
        "preferred_username": "admin_vault",
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

    totp_secret = pyotp.random_base32()
    user = User(id=u_id, tenant_id=t_id, username="admin_vault", totp_enabled=True)
    aad_u = f"{t_id}:{u_id}".encode()
    ct_u, iv_u, tag_u = encrypt_aes_gcm(totp_secret.encode(), aad_u)
    user.totp_secret_ciphertext = ct_u
    user.totp_secret_iv = iv_u
    user.totp_secret_tag = tag_u

    def _mock_get(model: Any, obj_id: Any) -> Any:
        if model == User:
            return user
        return test_router_full

    db.get.side_effect = _mock_get
    db.execute.return_value = MockDbResult([test_router_full])

    # Fase 1 (Bloqueado / Pre-Step-Up): Código TOTP inválido o expirado rechaza con 401
    invalid_reveal = VaultRevealRequest(totp_code="000000", reason="Intento fallido")
    with pytest.raises(HTTPException) as exc_totp:
        await reveal_credentials(test_router_full.id, invalid_reveal, fake_request, MagicMock(), claims, db)
    assert exc_totp.value.status_code == 401

    valid_code = pyotp.TOTP(totp_secret).now()
    reveal_payload = VaultRevealRequest(totp_code=valid_code, reason="Emergency audit inspection")

    with patch("src.api.v1.vault.write_audit_log", make_asserting_audit_mock()) as mock_vault_audit:
        # Fase 2 (Ventana Activa 30s): Revelación autorizada con cabeceras no-store y TTL de 30s
        fake_response = MagicMock()
        fake_response.headers = {}
        rev = await reveal_credentials(test_router_full.id, reveal_payload, fake_request, fake_response, claims, db)
        assert rev.api_username == "admin"
        assert rev.current_password == "admin_password"
        assert rev.auto_purge_seconds == 30
        mock_vault_audit.assert_awaited()

        # Fase 3 (Rotación y Propagación Criptográfica): Rotar clave desplaza current -> previous_password
        fake_client = AsyncMock()
        fake_client.get.return_value = [{".id": "*1", "name": "admin"}]
        fake_client_cm = AsyncMock()
        fake_client_cm.__aenter__.return_value = fake_client

        with patch("src.api.v1.vault.MikrotikRestClient", return_value=fake_client_cm):
            rot_res = await rotate_router_credentials_now(test_router_full.id, fake_request, claims, db)
            assert rot_res.rotation_status == "SUCCESS"
            assert rot_res.router_id == test_router_full.id
            rev_after = await reveal_credentials(
                test_router_full.id, reveal_payload, fake_request, fake_response, claims, db
            )
            assert rev_after.previous_password == "admin_password"
            assert rev_after.current_password != "admin_password"


# ============================================================================
# MAINTENANCE WINDOWS ENDPOINTS (Propagación Transversal -> Router.admin_state)
# ============================================================================


@pytest.mark.asyncio
async def test_maintenance_window_endpoints(fake_request: MagicMock) -> None:
    from src.api.v1.inventory_helpers import build_router_response, resolve_active_maintenance_router_ids

    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {
        "tid": str(t_id),
        "sub": str(u_id),
        "preferred_username": "operador_noc",
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

    now = datetime.now(UTC)
    target_router = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="r111-edge",
        api_base_url="https://10.250.3.8:443",
        api_port=443,
        network_role="CORE",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        is_reachable=True,
        physical_location="NOC",
        online_since_date=date(2026, 1, 1),
        serial_number="SN-MAINT-1",
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        created_at=now,
        updated_at=now,
    )
    target_router.tags = []

    mw = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=t_id,
        router_id=r_id,
        title="Nightly Upgrade",
        reason="Scheduled OS patch",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        suppress_alerts=True,
        is_cancelled=False,
        created_by=u_id,
        created_at=now,
    )
    db.execute.return_value = MockDbResult([mw])

    # 1. List
    windows = await list_maintenance_windows(router_id=None, is_active=None, is_cancelled=None, claims=claims, db=db)
    assert len(windows) == 1
    assert windows[0].title == "Nightly Upgrade"

    # 2. Create + Propagación Transversal hacia Router.admin_state == MAINTENANCE
    create_mw_req = CreateMaintenanceWindowRequest(
        title="Emergency Fix",
        reason="Fix route loop",
        router_id=r_id,
        starts_at=now - timedelta(minutes=1),
        ends_at=now + timedelta(hours=1),
        suppress_alerts=True,
    )
    with patch("src.api.v1.maintenance.write_audit_log", make_asserting_audit_mock()) as mock_mw_create_audit:
        created_mw = await create_maintenance_window(create_mw_req, fake_request, claims, db)
        assert created_mw.title == "Emergency Fix"
        mock_mw_create_audit.assert_awaited_once()

    with patch("src.api.v1.maintenance.purge_expired_maintenance_windows", new=AsyncMock(return_value=0)):
        active_ids = await resolve_active_maintenance_router_ids(db, t_id, [target_router])
        assert r_id in active_ids
        router_view_during_mw = build_router_response(
            target_router, {}, in_active_maintenance_window=(r_id in active_ids)
        )
        assert router_view_during_mw.admin_state == RouterAdminStateEnum.MAINTENANCE

    # 3. Cancel + Propagación Transversal restaurando Router.admin_state == PRODUCTION
    db.get.return_value = mw
    with patch("src.api.v1.maintenance.write_audit_log", make_asserting_audit_mock()) as mock_mw_cancel_audit:
        cancelled = await cancel_maintenance_window(mw.id, fake_request, claims, db)
        assert cancelled.is_cancelled is True
        mock_mw_cancel_audit.assert_awaited_once()

    db.execute.return_value = MockDbResult([])
    with patch("src.api.v1.maintenance.purge_expired_maintenance_windows", new=AsyncMock(return_value=0)):
        active_ids_after_cancel = await resolve_active_maintenance_router_ids(db, t_id, [target_router])
        assert r_id not in active_ids_after_cancel
        router_view_after_cancel = build_router_response(
            target_router, {}, in_active_maintenance_window=(r_id in active_ids_after_cancel)
        )
        assert router_view_after_cancel.admin_state == RouterAdminStateEnum.PRODUCTION

    # 4. Validation error: ends_at <= starts_at
    bad_dates_mw = CreateMaintenanceWindowRequest(
        title="Bad Dates",
        reason="Testing validation",
        router_id=r_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now,
        suppress_alerts=True,
    )
    with pytest.raises(HTTPException) as exc_dates:
        await create_maintenance_window(bad_dates_mw, fake_request, claims, db)
    assert exc_dates.value.status_code == 400

    # 5. Validation error: neither router_id nor target_tag
    no_target_mw = CreateMaintenanceWindowRequest(
        title="No Target",
        reason="Testing validation",
        router_id=None,
        target_tag=None,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        suppress_alerts=True,
    )
    with pytest.raises(HTTPException) as exc_target:
        await create_maintenance_window(no_target_mw, fake_request, claims, db)
    assert exc_target.value.status_code == 400

    # 6. Cancel 404 error
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_cancel:
        await cancel_maintenance_window(uuid.uuid4(), fake_request, claims, db)
    assert exc_cancel.value.status_code == 404

    # 7. Create with multiple router_ids
    r2_id = uuid.uuid4()
    multi_mw_req = CreateMaintenanceWindowRequest(
        title="Multi Router Patch",
        reason="Core cluster upgrade",
        router_ids=[r_id, r2_id],
        starts_at=now,
        ends_at=now + timedelta(hours=3),
        suppress_alerts=True,
    )
    with patch("src.api.v1.maintenance.write_audit_log", make_asserting_audit_mock()) as mock_multi_audit:
        multi_mw = await create_maintenance_window(multi_mw_req, fake_request, claims, db)
        assert multi_mw.title == "Multi Router Patch"
        assert mock_multi_audit.await_count == 2
```

---

### Paso 3: Refactorizar los 11 Archivos Restantes de Backend para Erradicar el 100% de Mocks Ciegos de `write_audit_log`

En los 11 archivos restantes de `fastapi/tests/`, importar `from tests.conftest import make_asserting_audit_mock` y sustituir cada `patch("...write_audit_log", AsyncMock())` o `patch("...write_audit_log", new_callable=AsyncMock)` sin captura por `patch("...write_audit_log", make_asserting_audit_mock()) as mock_audit`:

1. **`fastapi/tests/api/test_operations_endpoints_full.unit.py` (líneas `241`, `412`, `932`):**
   - Línea `241`: `patch("src.api.v1.approvals.write_audit_log", make_asserting_audit_mock()) as mock_app_audit,` y verificar `mock_app_audit.assert_awaited_once()`.
   - Línea `412`: `patch("src.api.v1.backups.write_audit_log", make_asserting_audit_mock()) as mock_bkp_audit,` y verificar `mock_bkp_audit.assert_awaited()`.
   - Línea `932`: `patch("src.api.v1.approvals.write_audit_log", make_asserting_audit_mock()) as mock_bulk_app_audit,` y verificar `mock_bulk_app_audit.assert_awaited_once()`.
2. **`fastapi/tests/api/test_hito16_full_coverage.unit.py` (líneas `287`, `589`, `603`, `643`, `749`):**
   - Sustituir las 5 ocurrencias por `patch("...write_audit_log", make_asserting_audit_mock()) as mock_audit`.
3. **`fastapi/tests/api/test_hito20_enterprise_suite.unit.py` (líneas `301`, `360`, `413`, `482`, `826`):**
   - Sustituir las 5 ocurrencias por `patch("...write_audit_log", make_asserting_audit_mock(return_value=...)) as mock_audit`.
4. **`fastapi/tests/api/test_hito23_mcp_tools.unit.py` (línea `251`):**
   - Sustituir `with patch("src.api.v1.mcp.write_audit_log", AsyncMock()):` por `with patch("src.api.v1.mcp.write_audit_log", make_asserting_audit_mock()) as mock_audit:` y `mock_audit.assert_awaited_once()`.
5. **`fastapi/tests/api/test_network_services_and_qos.unit.py` (líneas `191`, `209`, `285`, `312`, `377`):**
   - Sustituir las 5 ocurrencias por `patch("src.api.v1.network_services.write_audit_log", make_asserting_audit_mock()) as mock_audit`.
6. **`fastapi/tests/api/test_orphan_parity_and_layer2_singleton.unit.py` (líneas `137`, `167`):**
   - Sustituir las 2 ocurrencias por `patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()) as mock_audit`.
7. **`fastapi/tests/api/test_switch_tenant.unit.py` (línea `227`):**
   - Sustituir `patch("src.api.v1.auth.write_audit_log", new_callable=AsyncMock),` por `patch("src.api.v1.auth.write_audit_log", make_asserting_audit_mock()) as mock_audit,`.
8. **`fastapi/tests/api/test_webfig_endpoints_full.unit.py` (línea `572`):**
   - Sustituir `patch("src.api.v1.webfig_layer2.write_audit_log", new_callable=AsyncMock),` por `patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()) as mock_l2_audit,`.
9. **`fastapi/tests/api/test_webfig_layer2_universal.unit.py` (línea `312`):**
   - Sustituir `patch("src.api.v1.webfig_layer2.write_audit_log", AsyncMock()),` por `patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()) as mock_l2_audit,`.
10. **`fastapi/tests/rbac/test_rbac_30_actions_and_user_overrides.unit.py` (línea `195`):**
    - Sustituir `monkeypatch.setattr("src.core.audit.write_audit_log", AsyncMock())` por `fake_audit = make_asserting_audit_mock(); monkeypatch.setattr("src.core.audit.write_audit_log", fake_audit)`.
11. **`fastapi/tests/test_mcp_endpoint.unit.py` (16 ocurrencias en líneas `334`, `370`, `408`, `448`, `505`, `546`, `583`, `873`, `912`, `956`, `980`, `1028`, `1053`, `1091`, `1129`, `1171`):**
    - Sustituir cada `patch("src.api.v1.mcp.write_audit_log", new_callable=AsyncMock),` por `patch("src.api.v1.mcp.write_audit_log", make_asserting_audit_mock()) as mock_mcp_audit,`.

---

### Paso 4: Añadir el Ciclo de Vida Temporal de 3 Fases en `fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py`

Añadir al final de `fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py` el test integral `test_safemode_three_phase_temporal_lifecycle_and_rollback` que certifica en una sola secuencia las 3 fases temporales del motor Safe Mode (60s):

**`Target` al final de `fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py` (líneas 254–271):**
```python
@pytest.mark.asyncio
async def test_execute_with_safemode_loss_of_connectivity() -> None:
    client = AsyncMock()
    # verify_connectivity fails
    client.get.side_effect = Exception("Network down")

    async def suicidal_mutation() -> None:
        pass

    with pytest.raises(SafeModeRollbackTriggeredError) as exc_info:
        await execute_with_safemode(
            client=client,
            rollback_cli='/interface/set ether1 disabled=no',
            operation_fn=suicidal_mutation,
            interval_seconds=60,
            job_name="rosgrid-safemode-loss",
        )
    assert "rosgrid-safemode-loss" in str(exc_info.value)
```

**`Replacement` al final de `fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py`:**
```python
@pytest.mark.asyncio
async def test_execute_with_safemode_loss_of_connectivity() -> None:
    client = AsyncMock()
    # verify_connectivity fails
    client.get.side_effect = Exception("Network down")

    async def suicidal_mutation() -> None:
        pass

    with pytest.raises(SafeModeRollbackTriggeredError) as exc_info:
        await execute_with_safemode(
            client=client,
            rollback_cli='/interface/set ether1 disabled=no',
            operation_fn=suicidal_mutation,
            interval_seconds=60,
            job_name="rosgrid-safemode-loss",
        )
    assert "rosgrid-safemode-loss" in str(exc_info.value)


@pytest.mark.asyncio
async def test_safemode_three_phase_temporal_lifecycle_and_rollback() -> None:
    """Certifica las 3 fases temporales de Safe Mode (60s): (1) Inyección, (2) Ventana Activa en Espera, (3) Confirmación o Reversión."""
    client = AsyncMock()
    client.get.return_value = {"name": "Core-BNG"}
    client.put.return_value = {".id": "*sched99"}

    # Fase 1 y Fase 2: Se inyecta el Dead Man's Switch y se mantiene activo durante la ventana de 60s
    res = await execute_with_safemode(
        client=client,
        rollback_cli='/ip/address/set [find address="10.250.3.8/24"] disabled=no',
        operation_fn=AsyncMock(return_value={"status": "APPLIED_IN_SAFEMODE"}),
        interval_seconds=60,
        job_name="rosgrid-sm-3phase",
        keep_alive_for_confirmation=True,
    )
    assert res == {"status": "APPLIED_IN_SAFEMODE"}
    client.delete.assert_not_awaited()

    # Fase 3a (Reversión explícita dentro o al vencer la ventana): restaura el estado previo y limpia scheduler
    client.get.side_effect = [
        [{".id": "*sched99", "name": "rosgrid-sm-3phase"}],
        [{".id": "*script99", "name": "rosgrid-sm-3phase"}],
    ]
    reverted = await execute_rollback_on_router(
        client=client,
        job_name="rosgrid-sm-3phase",
        menu="/ip/address",
        action="patch",
        item_id="*addr1",
        before_state={"disabled": False},
        mutated_keys=["disabled"],
    )
    assert reverted is True
    client.patch.assert_awaited_once_with("/ip/address/*addr1", json_data={"disabled": False})
    assert client.delete.await_count == 2
```

---

### Paso 5: Crear el Script Guardrail `.agents/scripts/verify_anti_silo_test_quality.py` e Integrarlo en `.agents/scripts/certify_task_completion.sh`

1. Crear el archivo `.agents/scripts/verify_anti_silo_test_quality.py`:

```python
#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Guardrail estático QA 11X para el Invariante Anti-Silo (Sección 1.5).

Verifica:
1. Cero mocks ciegos de `write_audit_log` en `fastapi/tests/**/*.py` (prohibido usar
   `patch("...write_audit_log", AsyncMock())` sin captura `as mock_...` ni `make_asserting_audit_mock`).
2. Presencia de pruebas de las 3 fases temporales (`Programada`, `En Curso`, `Expirada`) en:
   - Ventanas de Mantenimiento (`test_inventory_and_vault_endpoints_full.unit.py` y `maintenanceWindowsView.unit.ts`)
   - Safe Mode 60s (`test_safemode_deadman_switch.unit.py` y `RgSafeModeBanner.unit.ts`)
   - Bóveda Step-Up 30s (`test_inventory_and_vault_endpoints_full.unit.py` y `vaultRevealModal.unit.ts`)
3. Presencia de aserciones Anti-UUID crudo en auditoría y Cinta de Eventos Críticos.
"""

from __future__ import annotations

import glob
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def check_no_blind_audit_mocks() -> list[str]:
    errors: list[str] = []
    pattern = str(REPO_ROOT / "fastapi" / "tests" / "**" / "*.py")
    for file_path in sorted(glob.glob(pattern, recursive=True)):
        rel = Path(file_path).relative_to(REPO_ROOT)
        if rel.name == "conftest.py":
            continue
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if "write_audit_log" in stripped and ("patch(" in stripped or "setattr(" in stripped):
                has_capture = (
                    " as " in stripped
                    or "fake_audit" in stripped
                    or "make_asserting_audit_mock" in stripped
                )
                if not has_capture:
                    errors.append(f"{rel}:{idx} -> Mock ciego de write_audit_log sin aserción: {stripped}")
    return errors


def check_mandatory_3phase_and_cross_module_suites() -> list[str]:
    errors: list[str] = []
    required_markers = [
        (
            "fastapi/tests/api/test_inventory_and_vault_endpoints_full.unit.py",
            [
                "test_resolve_active_maintenance_router_ids_3_temporal_phases",
                "test_write_audit_log_resolves_usernames_and_router_names",
                "make_asserting_audit_mock",
            ],
        ),
        (
            "fastapi/tests/mikrotik/test_safemode_deadman_switch.unit.py",
            ["test_safemode_three_phase_temporal_lifecycle_and_rollback"],
        ),
        (
            "vue3/src/views/inventory/maintenanceWindowsView.unit.ts",
            ["En Curso", "Programada"],
        ),
        (
            "vue3/src/components/common/RgNotificationCenterBell.unit.ts",
            ["Session token renewed", "approve"],
        ),
    ]
    for rel_path, markers in required_markers:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"Archivo de prueba obligatorio no encontrado: {rel_path}")
            continue
        content = full_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(f"{rel_path} -> Falta marcador obligatorio Anti-Silo / 3-Fases: '{marker}'")
    return errors


def main() -> int:
    print("🔍 Auditando invariante Anti-Silo, 3 Fases Temporales y Cero Mocks Ciegos de Auditoría...")
    blind_errors = check_no_blind_audit_mocks()
    suite_errors = check_mandatory_3phase_and_cross_module_suites()
    all_errors = blind_errors + suite_errors

    if all_errors:
        print("❌ Violaciones detectadas en la calidad de pruebas Anti-Silo:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✔ 0 mocks ciegos de write_audit_log y 100% de suites 3-Fases / Anti-Silo verificadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

2. Integrar `verify_anti_silo_test_quality.py` en `.agents/scripts/certify_task_completion.sh` justo debajo del paso `[4/9]`:

**`Target` en `.agents/scripts/certify_task_completion.sh` (líneas 29–33):**
```bash
# 4. Invariante de Cero Componentes Vue Huérfanos
echo -e "\n🧩 [4/9] Verificando cobertura de componentes Vue (invariante cero componentes huérfanos)..."
python3 "${REPO_ROOT}/.agents/scripts/verify_zero_orphan_vue_components.py"
echo "✔ Todos los componentes Vue cuentan con suite de prueba activa."
```

**`Replacement` en `.agents/scripts/certify_task_completion.sh`:**
```bash
# 4. Invariante de Cero Componentes Vue Huérfanos y Calidad Anti-Silo (3 Fases + 0 Mocks Ciegos)
echo -e "\n🧩 [4/9] Verificando cobertura de componentes Vue y calidad Anti-Silo de pruebas..."
python3 "${REPO_ROOT}/.agents/scripts/verify_zero_orphan_vue_components.py"
python3 "${REPO_ROOT}/.agents/scripts/verify_anti_silo_test_quality.py"
echo "✔ Todos los componentes Vue y suites Anti-Silo (0 mocks ciegos / 3 fases temporales) verificados."
```

---

## 3. Comandos de Verificación en Contenedores Efímeros (`Rule Zero`)

```bash
# 1. Ejecutar el nuevo guardrail estático Anti-Silo
python3 .agents/scripts/verify_anti_silo_test_quality.py

# 2. Ejecutar la suite completa de Pytest en contenedor Docker efímero
docker compose -f fastapi/docker-compose.qa.yml run --rm -e COVERAGE_FILE=/tmp/.coverage fastapi-qa \
  sh -c "uv run pytest tests/ && uv run ruff check src/ tests/"

# 3. Ejecutar Vitest en contenedor Docker efímero
docker compose -f vue3/docker-compose.qa.yml run --rm --entrypoint sh vue3-qa \
  -c "pnpm exec vitest run && pnpm exec vue-tsc --noEmit"
```
