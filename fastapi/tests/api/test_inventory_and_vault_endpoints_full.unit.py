# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias completas para endpoints de Inventario, Bóveda, Mantenimiento y Canales de Notificación."""

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
    test_channel,
    update_channel,
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
    VaultRotateRequest,
)
from src.schemas.notifications import (
    NotificationChannelCreateRequest,
    NotificationChannelUpdateRequest,
    NotificationTestRequest,
)


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
        return MockScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single


class MockScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


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
    )
    return r


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_and_get_routers(test_router_full: Router) -> None:
    db = AsyncMock()
    db.execute.return_value = MockDbResult([test_router_full])
    claims = {
        "tid": str(test_router_full.tenant_id),
        "sub": str(test_router_full.created_by),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "all_r": True,
    }

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {"state": "ONLINE", "cpu": "20", "ram": "40"}

    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.inventory_helpers.get_redis_client", return_value=fake_redis),
    ):
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
async def test_create_and_update_and_delete_router(
    test_router_full: Router, fake_request: MagicMock
) -> None:
    db = AsyncMock()
    # Check duplicate query returns empty
    db.execute.return_value = MockDbResult([])
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
        patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock),
    ):
        # 1. Create router
        created = await create_router(create_payload, fake_request, claims, db)
        assert created.display_name == "New-Router"
        db.add.assert_called()

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


@pytest.mark.asyncio
async def test_sync_discovery_and_repin_ssl(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
    db.execute.return_value = MockDbResult([test_router_full])
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
        patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock),
    ):
        synced = await sync_discovery(test_router_full.id, fake_request, claims, db)
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

    with patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock):
        repin_res = await repin_ssl(test_router_full.id, repin_payload, fake_request, claims, db)
        assert repin_res["status"] == "SUCCESS"
        assert repin_res["fingerprint"] == "b" * 64


@pytest.mark.asyncio
async def test_csv_dry_run_and_commit(fake_request: MagicMock) -> None:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    db = AsyncMock()
    db.execute.return_value = MockDbResult([])

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

    with patch("src.api.v1.inventory.write_audit_log", new_callable=AsyncMock):
        commit_res = await import_csv_commit(commit_payload, fake_request, claims, db)
        assert commit_res.imported_count == 1
        assert len(commit_res.created_router_ids) == 1


# ============================================================================
# VAULT ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_reveal_and_rotate_credentials(test_router_full: Router, fake_request: MagicMock) -> None:
    db = AsyncMock()
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
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }

    valid_code = pyotp.TOTP(totp_secret).now()
    reveal_payload = VaultRevealRequest(totp_code=valid_code)

    with patch("src.api.v1.vault.write_audit_log", new_callable=AsyncMock):
        # 1. Reveal
        fake_response = MagicMock()
        rev = await reveal_credentials(test_router_full.id, reveal_payload, fake_request, fake_response, claims, db)
        assert rev.api_username == "admin"
        assert rev.current_password == "admin_password"

        # 2. Rotate Now
        fake_client = AsyncMock()
        fake_client.patch.return_value = {}
        with patch("src.api.v1.vault._create_client_from_vault", return_value=fake_client):
            rot = await rotate_now(test_router_full.id, fake_request, claims, db)
            assert rot.status == "SUCCESS"
            assert rot.new_password is not None


# ============================================================================
# MAINTENANCE WINDOW ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_maintenance_window_endpoints(fake_request: MagicMock) -> None:
    db = AsyncMock()
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


# ============================================================================
# NOTIFICATION CHANNELS ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_notification_channel_endpoints() -> None:
    db = AsyncMock()
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
        patch("src.api.v1.notification_channels._decrypt_channel_config", return_value={"bot_token": "token"}),
        patch("src.api.v1.notification_channels._encrypt_channel_config", return_value=(b"c", b"i", b"t")),
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
        test_res = await test_channel(ch.id, test_payload, claims=claims, db=db)
        assert test_res.status == "SUCCESS"

        # 5. Delete
        await delete_channel(ch.id, claims=claims, db=db)
        db.delete.assert_awaited_once_with(ch)
