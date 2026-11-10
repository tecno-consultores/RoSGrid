# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias completas para endpoints de Inventario, Bóveda, Mantenimiento y Canales de Notificación (NFKC)."""

import io
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pyotp
import pytest
from fastapi import HTTPException, UploadFile

from src.api.v1.inventory import (
    create_router,
    delete_router,
    get_router,
    import_csv_commit,
    import_csv_dry_run,
    list_routers,
    repin_ssl,
    sync_discovery,
    update_router,
)
from src.api.v1.maintenance import (
    cancel_maintenance_window,
    create_maintenance_window,
    list_maintenance_windows,
)
from src.api.v1.notification_channels import (
    create_channel,
    delete_channel,
    list_channels,
    update_channel,
)
from src.api.v1.notification_channels import (
    test_channel as api_test_channel,
)
from src.api.v1.vault import (
    reveal_credentials,
    rotate_now,
)
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum, User
from src.models.inventory import (
    MaintenanceWindow,
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
    RouterTag,
    SSLTrustStatusEnum,
)
from src.models.operations import AlertChannelTypeEnum, NotificationChannel
from src.schemas.inventory import (
    CreateMaintenanceWindowRequest,
    CreateRouterRequest,
    CsvCommitRequest,
    CsvCommitRowItem,
    RePinSSLRequest,
    UpdateRouterRequest,
    VaultRevealRequest,
)
from src.schemas.notifications import (
    NotificationChannelCreateRequest,
    NotificationChannelUpdateRequest,
    NotificationTestRequest,
)
from tests.conftest import make_asserting_audit_mock


class MockDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class MockDbResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None):
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)

    def scalars(self) -> MockDbScalars:
        return MockDbScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single

    def scalar(self) -> Any:
        return self._single


async def _fake_refresh(instance: Any, *args: Any, **kwargs: Any) -> None:
    now = datetime.now(UTC)
    if getattr(instance, "id", None) is None:
        instance.id = uuid.uuid4()
    if getattr(instance, "created_at", None) is None:
        instance.created_at = now
    if getattr(instance, "updated_at", None) is None:
        instance.updated_at = now
    if hasattr(instance, "is_cancelled") and instance.is_cancelled is None:
        instance.is_cancelled = False
    if hasattr(instance, "tags") and instance.tags is None:
        instance.tags = []
    if hasattr(instance, "is_reachable") and getattr(instance, "is_reachable", None) is None:
        instance.is_reachable = False
    if hasattr(instance, "ssl_trust_status") and getattr(instance, "ssl_trust_status", None) is None:
        instance.ssl_trust_status = SSLTrustStatusEnum.PENDING_TOFU


def _fake_add(instance: Any, *args: Any, **kwargs: Any) -> None:
    if hasattr(instance, "id") and getattr(instance, "id", None) is None:
        instance.id = uuid.uuid4()


@pytest.fixture
def fake_request() -> MagicMock:
    req = MagicMock()
    req.client.host = "192.168.1.50"
    req.headers.get.return_value = "TestAgent/1.0"
    return req


@pytest.fixture
def test_router_full() -> Router:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="Edge-Core-01",
        api_base_url="https://192.168.88.1:443",
        api_port=443,
        network_role=RouterNetworkRoleEnum.CORE,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="Datacenter Room 1",
        latitude=Decimal("10.4806"),
        longitude=Decimal("-66.9036"),
        online_since_date=date.today(),
        serial_number="SN-FULL-01",
        is_reachable=True,
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        ssl_sha256_fingerprint="a" * 64,
        created_by=u_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    r.tags = [RouterTag(id=uuid.uuid4(), tenant_id=t_id, router_id=r.id, tag_name="core")]
    aad = f"{t_id}:{r.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"admin_password", aad)
    r.vault = RouterCredentialsVault(
        router_id=r.id,
        tenant_id=t_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
        auto_rotate_enabled=True,
        last_rotated_at=datetime.now(UTC),
    )
    return r


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_and_get_routers(test_router_full: Router) -> None:
    db = AsyncMock()
    db.execute.return_value = MockDbResult([test_router_full])
    db.refresh.side_effect = _fake_refresh
    claims = {
        "tid": str(test_router_full.tenant_id),
        "sub": str(test_router_full.created_by),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "all_r": True,
    }

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {"state": "ONLINE", "cpu": "20", "ram": "40"}

    with patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis):
        # 1. list_routers
        res_list = await list_routers(
            network_role=None,
            admin_state=None,
            tag=None,
            search=None,
            claims=claims,
            db=db,
        )
        assert len(res_list) == 1
        assert res_list[0].display_name == "Edge-Core-01"

        # 2. get_router
        res_get = await get_router(test_router_full.id, claims, db)
        assert res_get.id == test_router_full.id

        # 3. get_router 404
        db.execute.return_value = MockDbResult([])
        with pytest.raises(HTTPException) as exc:
            await get_router(uuid.uuid4(), claims, db)
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_and_update_and_delete_router(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    # Check duplicate query returns empty (scalar() -> None)
    db.execute.return_value = MockDbResult([], single=None)
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    fake_tenant = MagicMock()
    fake_tenant.max_routers_quota = 100
    db.get.return_value = fake_tenant
    claims = {
        "tid": str(test_router_full.tenant_id),
        "sub": str(test_router_full.created_by),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

    create_payload = CreateRouterRequest(
        display_name="New-Router",
        api_base_url="https://10.0.0.1",
        api_port=443,
        api_username="admin",
        api_password="SuperPassword123",
        network_role=RouterNetworkRoleEnum.DISTRIBUTION_SWITCH,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="Branch Office",
        online_since_date=date.today(),
        serial_number="SN-NEW-99",
        tags=["branch", "distribution"],
        connect_and_discover_now=False,
    )

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {}

    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_inv_audit,
    ):
        # 1. Create router
        created = await create_router(create_payload, fake_request, claims, db)
        assert created.display_name == "New-Router"

        # 2. Update router
        db.execute.return_value = MockDbResult([test_router_full])
        update_payload = UpdateRouterRequest(
            display_name="Updated-Name",
            tags=["core", "edge"],
        )
        updated = await update_router(test_router_full.id, update_payload, claims, db)
        assert updated.display_name == "Updated-Name"

        # 3. Delete router
        db.get.return_value = test_router_full
        await delete_router(test_router_full.id, claims, db)
        db.delete.assert_awaited_once_with(test_router_full)
        mock_inv_audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_discovery_and_repin_ssl(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.execute.return_value = MockDbResult([test_router_full])
    db.refresh.side_effect = _fake_refresh
    claims = {
        "tid": str(test_router_full.tenant_id),
        "sub": str(test_router_full.created_by),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {}

    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory.perform_discovery", new_callable=AsyncMock),
    ):
        synced = await sync_discovery(test_router_full.id, claims, db)
        assert synced.id == test_router_full.id

    # repin_ssl
    totp_secret = pyotp.random_base32()
    u = User(
        id=test_router_full.created_by,
        tenant_id=test_router_full.tenant_id,
        username="admin",
        role=SystemRoleEnum.TENANT_ADMIN,
        totp_enabled=True,
    )
    aad_user = f"{test_router_full.tenant_id}:{u.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(totp_secret.encode(), aad_user)
    u.totp_secret_ciphertext = ct
    u.totp_secret_iv = iv
    u.totp_secret_tag = tag

    db.get.side_effect = [u, test_router_full]
    valid_code = pyotp.TOTP(totp_secret).now()
    repin_payload = RePinSSLRequest(
        totp_code=valid_code,
        expected_new_sha256_fingerprint="b" * 64,
    )

    with patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_repin_audit:
        repin_res = await repin_ssl(test_router_full.id, repin_payload, fake_request, claims, db)
        assert repin_res["status"] == "SUCCESS"
        assert repin_res["fingerprint"] == "b" * 64
        mock_repin_audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_csv_dry_run_and_commit(fake_request: MagicMock) -> None:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    db = AsyncMock()
    db.execute.return_value = MockDbResult([], single=None)
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    fake_tenant = MagicMock()
    fake_tenant.max_routers_quota = 100
    db.get.return_value = fake_tenant

    csv_content = b"display_name,api_base_url,api_port,network_role,admin_state,physical_location,serial_number,api_username,api_password,tags\nR1,https://10.0.0.1,443,CORE,PRODUCTION,DC1,SN001,admin,pass,core"
    upload_file = UploadFile(file=io.BytesIO(csv_content), filename="routers.csv")

    dry_run = await import_csv_dry_run(upload_file, claims, db)
    assert dry_run.total_rows == 1
    assert dry_run.valid_rows_count == 1
    assert dry_run.can_proceed is True

    # Commit
    row_item = CsvCommitRowItem(
        display_name="R1",
        api_base_url="https://10.0.0.1",
        api_port=443,
        network_role=RouterNetworkRoleEnum.CORE,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="DC1",
        online_since_date=date.today(),
        serial_number="SN001",
        api_username="admin",
        api_password="pass",
        tags=["core"],
    )
    commit_payload = CsvCommitRequest(rows=[row_item])

    fake_request.headers.get.return_value = "application/json"
    fake_request.json = AsyncMock(return_value=commit_payload.model_dump(mode="json"))

    with patch("src.api.v1.inventory.write_audit_log", make_asserting_audit_mock()) as mock_csv_audit:
        commit_res = await import_csv_commit(fake_request, claims, db)
        assert commit_res.imported_count == 1
        assert len(commit_res.created_router_ids) == 1
        mock_csv_audit.assert_awaited_once()


# ============================================================================
# VAULT ENDPOINTS (3 Fases Temporales Step-Up 30s + Propagación Criptográfica)
# ============================================================================


@pytest.mark.asyncio
async def test_reveal_and_rotate_credentials(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    totp_secret = pyotp.random_base32()
    u = User(
        id=test_router_full.created_by,
        tenant_id=test_router_full.tenant_id,
        username="admin",
        role=SystemRoleEnum.TENANT_ADMIN,
        totp_enabled=True,
    )
    aad_user = f"{test_router_full.tenant_id}:{u.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(totp_secret.encode(), aad_user)
    u.totp_secret_ciphertext = ct
    u.totp_secret_iv = iv
    u.totp_secret_tag = tag

    db.get.return_value = u
    db.execute.return_value = MockDbResult([test_router_full])
    claims = {
        "tid": str(test_router_full.tenant_id),
        "sub": str(u.id),
        "preferred_username": "admin",
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

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
        assert rev.display_ttl_seconds == 30
        mock_vault_audit.assert_awaited()

        # Fase 3 (Rotación y Propagación Criptográfica): Rotar clave desplaza current -> previous_password
        with patch("src.api.v1.vault._rotate_on_device", new_callable=AsyncMock):
            rot = await rotate_now(test_router_full.id, fake_request, claims, db)
            assert rot.status == "SUCCESS"
            assert rot.router_id == test_router_full.id
            assert rot.last_rotated_at is not None
            rev_after = await reveal_credentials(
                test_router_full.id, reveal_payload, fake_request, fake_response, claims, db
            )
            assert rev_after.previous_password == "admin_password"
            assert rev_after.current_password != "admin_password"


# ============================================================================
# MAINTENANCE WINDOW ENDPOINTS (Propagación Transversal -> Router.admin_state)
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
        network_role=RouterNetworkRoleEnum.CORE,
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


# ============================================================================
# NOTIFICATION CHANNELS ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_notification_channel_endpoints() -> None:
    db = AsyncMock()
    db.refresh.side_effect = _fake_refresh
    db.add = MagicMock(side_effect=_fake_add)
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    ch = NotificationChannel(
        id=uuid.uuid4(),
        tenant_id=t_id,
        name="Telegram NOC",
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        is_enabled=True,
        config_ciphertext=b"ct",
        config_iv=b"iv",
        config_tag=b"tag",
        subscribed_events=["ROUTER_OFFLINE"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.execute.return_value = MockDbResult([ch])

    with (
        patch(
            "src.api.v1.notification_channels._decrypt_channel_config",
            return_value={"bot_token": "token", "chat_id": "123"},
        ),
        patch("src.api.v1.notification_channels._encrypt_channel_config", return_value=(b"c", b"i", b"t")),
        patch("src.api.v1.notification_channels._dispatch_telegram", new_callable=AsyncMock),
    ):
        # 1. List
        ch_list = await list_channels(claims=claims, db=db)
        assert len(ch_list) == 1
        assert ch_list[0].name == "Telegram NOC"

        # 2. Create
        create_req = NotificationChannelCreateRequest(
            name="New Telegram",
            channel_type=AlertChannelTypeEnum.TELEGRAM_BOT.value,
            config={"bot_token": "token", "chat_id": "123"},
            subscribed_events=["ROUTER_DOWN"],
            is_enabled=True,
        )
        created_ch = await create_channel(create_req, claims=claims, db=db)
        assert created_ch.name == "New Telegram"

        # 3. Update
        db.get.return_value = ch
        update_req = NotificationChannelUpdateRequest(name="Updated NOC Channel")
        updated_ch = await update_channel(ch.id, update_req, claims=claims, db=db)
        assert updated_ch.name == "Updated NOC Channel"

        # 4. Test notification dispatch
        test_payload = NotificationTestRequest()
        test_res = await api_test_channel(ch.id, test_payload, claims=claims, db=db)
        assert test_res.status == "SUCCESS"

        # 5. Delete
        await delete_channel(ch.id, claims=claims, db=db)
        db.delete.assert_awaited_once_with(ch)


@pytest.mark.asyncio
async def test_build_router_response_reachability_consolidation() -> None:
    """Verifica que build_router_response consolide is_reachable = True si syslog_active es True."""
    from datetime import date

    from src.api.v1.inventory_helpers import build_router_response
    from src.models.inventory import Router, RouterAdminStateEnum, SSLTrustStatusEnum

    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="r-test-syslog",
        api_base_url="https://10.250.3.8:443",
        api_port=443,
        network_role="CORE",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="NOC",
        online_since_date=date(2026, 1, 1),
        serial_number="SN-TEST-1",
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        is_reachable=False,  # En Postgres figuraba False
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Telemetría viva con Syslog activo
    telemetry = {
        "operational_status": "OFFLINE",
        "cpu_load_percent": None,
        "memory_used_percent": None,
        "syslog_active": True,
        "syslog_event_count": 42,
    }

    resp = build_router_response(r, telemetry)
    assert resp.is_reachable is True
    assert resp.operational_status == "ONLINE"
    assert resp.syslog_active is True


@pytest.mark.asyncio
async def test_resolve_active_maintenance_router_ids_3_temporal_phases():
    """Hito 30.2: Certifica resolución de ventanas en curso a través de 3 fases temporales y tags."""
    from src.api.v1.inventory_helpers import build_router_response, resolve_active_maintenance_router_ids
    from src.models.inventory import MaintenanceWindow, Router, RouterAdminStateEnum, RouterTag

    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)
    r1 = Router(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        display_name="r111-core",
        api_base_url="https://10.250.3.8:443",
        api_port=443,
        network_role="CORE",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        is_reachable=True,
        physical_location="NOC Principal",
        online_since_date=date(2026, 1, 1),
        serial_number="SN-R111",
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        created_at=now,
        updated_at=now,
    )
    r1.tags = [RouterTag(tenant_id=tenant_id, router_id=r1.id, tag_name="bng-edge")]

    r2 = Router(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        display_name="r222-access",
        api_base_url="https://10.250.3.9:443",
        api_port=443,
        network_role="ACCESS",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        is_reachable=True,
        physical_location="Pop Sur",
        online_since_date=date(2026, 1, 1),
        serial_number="SN-R222",
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        created_at=now,
        updated_at=now,
    )
    r2.tags = []

    now = datetime.now(UTC)

    # 1. Ventana activa directa para r1
    active_mw = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        router_id=r1.id,
        title="Ventana Activa",
        reason="Upgrade",
        starts_at=now - timedelta(minutes=5),
        ends_at=now + timedelta(minutes=10),
        is_cancelled=False,
    )

    # Fase 1: Activa (starts_at <= now <= ends_at) -> r1 debe resolverse a MAINTENANCE
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [active_mw]
    mock_db.execute.return_value = mock_res

    with patch("src.api.v1.maintenance.purge_expired_maintenance_windows", new=AsyncMock(return_value=0)):
        active_ids = await resolve_active_maintenance_router_ids(mock_db, tenant_id, [r1, r2])
        assert r1.id in active_ids
        assert r2.id not in active_ids

        resp_r1 = build_router_response(r1, {}, in_active_maintenance_window=True)
        assert resp_r1.admin_state == RouterAdminStateEnum.MAINTENANCE

        resp_r2 = build_router_response(r2, {}, in_active_maintenance_window=False)
        assert resp_r2.admin_state == RouterAdminStateEnum.PRODUCTION

        # Fase 2: Programada (Futura) -> DB query retorna vacío
        mock_res_scheduled = MagicMock()
        mock_res_scheduled.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_res_scheduled

        active_ids_sched = await resolve_active_maintenance_router_ids(mock_db, tenant_id, [r1, r2])
        assert len(active_ids_sched) == 0

        # Fase 3: Global tag -> aplica a todos los routers del tenant
        global_mw = MaintenanceWindow(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            router_id=None,
            target_tag="global",
            title="Ventana Global",
            reason="Core BGP Switchover",
            starts_at=now - timedelta(minutes=2),
            ends_at=now + timedelta(minutes=15),
            is_cancelled=False,
        )
        mock_res_global = MagicMock()
        mock_res_global.scalars.return_value.all.return_value = [global_mw]
        mock_db.execute.return_value = mock_res_global

        active_ids_glob = await resolve_active_maintenance_router_ids(mock_db, tenant_id, [r1, r2])
        assert r1.id in active_ids_glob
        assert r2.id in active_ids_glob


@pytest.mark.asyncio
async def test_write_audit_log_resolves_usernames_and_router_names():
    """Hito 30.2: Certifica que write_audit_log resuelva User.username y Router.display_name erradicando UUIDs."""
    from src.core.audit import write_audit_log
    from src.models.core import User
    from src.models.inventory import Router

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    router_id = uuid.uuid4()

    mock_user = User(id=user_id, username="operador_carlos", tenant_id=tenant_id)
    mock_router = Router(id=router_id, display_name="CCR2004-Caracas-Core", tenant_id=tenant_id)

    mock_session = AsyncMock()
    mock_hash_res = MagicMock()
    mock_hash_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_hash_res

    async def mock_get(model, pk):
        if model is User and pk == user_id:
            return mock_user
        if model is Router and pk == router_id:
            return mock_router
        return None

    mock_session.get.side_effect = mock_get

    log_entry = await write_audit_log(
        session=mock_session,
        tenant_id=tenant_id,
        actor_username=str(user_id),  # UUID crudo que debe ser resuelto
        actor_role="TENANT_ADMIN",
        actor_ip="127.0.0.1",
        event_category="MAINTENANCE",
        event_action="MAINTENANCE_WINDOW_CREATED",
        actor_user_id=user_id,
        router_id=router_id,
        router_display_name=None,  # Nombre omitido que debe ser resuelto
    )

    assert log_entry.actor_username == "operador_carlos"
    assert log_entry.router_display_name == "CCR2004-Caracas-Core"


@pytest.mark.asyncio
async def test_update_router_cancels_active_maintenance_windows_when_set_to_production():
    """Hito 30.2: Certifica que cambiar admin_state a PRODUCTION cancele ventanas activas del router."""
    from src.api.v1.inventory import update_router
    from src.models.inventory import MaintenanceWindow, Router, RouterAdminStateEnum
    from src.schemas.inventory import UpdateRouterRequest

    tenant_id = uuid.uuid4()
    router_id = uuid.uuid4()
    claims = {"tid": str(tenant_id), "sub": str(uuid.uuid4()), "rol": "TENANT_ADMIN"}
    now = datetime.now(UTC)

    r = Router(
        id=router_id,
        tenant_id=tenant_id,
        display_name="r111",
        api_base_url="https://10.250.3.8:443",
        api_port=443,
        network_role="CORE",
        admin_state=RouterAdminStateEnum.MAINTENANCE,
        is_reachable=True,
        physical_location="Datacenter",
        online_since_date=date(2026, 1, 1),
        serial_number="SN-TEST-R111",
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        created_at=now,
        updated_at=now,
    )
    r.tags = []

    active_mw = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        router_id=router_id,
        title="Mantenimiento r111",
        reason="Prueba",
        starts_at=datetime.now(UTC) - timedelta(minutes=5),
        ends_at=datetime.now(UTC) + timedelta(minutes=20),
        is_cancelled=False,
    )

    mock_db = AsyncMock()
    mock_router_res = MagicMock()
    mock_router_res.scalar_one_or_none.return_value = r

    mock_mw_res = MagicMock()
    mock_mw_res.scalars.return_value.all.return_value = [active_mw]

    def side_execute(stmt):
        stmt_str = str(stmt).lower()
        if "maintenance_windows" in stmt_str:
            return mock_mw_res
        return mock_router_res

    mock_db.execute.side_effect = side_execute

    with (
        patch("src.api.v1.inventory.get_redis_client"),
        patch("src.api.v1.inventory.enrich_router_telemetry", new=AsyncMock(return_value={})),
        patch("src.api.v1.inventory.resolve_active_maintenance_router_ids", new=AsyncMock(return_value=set())),
    ):
        payload = UpdateRouterRequest(admin_state=RouterAdminStateEnum.PRODUCTION)
        resp = await update_router(router_id, payload, claims=claims, db=mock_db)

        assert resp.admin_state == RouterAdminStateEnum.PRODUCTION
        assert active_mw.is_cancelled is True
