# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias focalizadas para alcanzar >= 95% de cobertura en Hito 16 (Inventory, Backups, Tenants, Users, FieldOps, Subscribers)."""

import os
import tempfile
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from src.api.v1.backups import (
    _build_side_by_side_hunks,
    _compute_diff_stats,
    _extract_raw_rsc_text,
    download_backup_file,
    export_router_rsc,
)
from src.api.v1.bgp_looking_glass import _parse_communities, _parse_route_item
from src.api.v1.diagnostics_360 import _parse_torch_flows, _parse_torch_rate
from src.api.v1.field_ops import (
    certify_installation,
    detect_fiber_cuts_engine,
    verify_subscriber_live,
)
from src.api.v1.inventory import (
    _apply_query_search_filters,
    _apply_role_filters,
    _check_tenant_router_quota,
    create_custom_network_role,
    delete_custom_network_role,
    import_csv_commit,
    list_network_roles,
)
from src.api.v1.rbac import (
    UpdateRolePermissionsRequest,
    _get_tenant_role_overrides,
    update_role_permissions,
)
from src.api.v1.sdwan import provision_spoke_tunnel
from src.api.v1.sessions import terminate_session
from src.api.v1.subscribers import (
    create_bandwidth_profile,
    generate_subscriber_mikrotik_queue_script,
    get_tenant_id,
    update_subscriber_device,
)
from src.api.v1.switching import get_dhcp_snooping_state
from src.api.v1.tenants import (
    create_tenant,
    get_tenant,
    invalidate_tenant_features_cache,
    update_tenant,
)
from src.api.v1.traffic_flow import _aggregate_connection_stats, _evaluate_anomaly_severity
from src.api.v1.users import (
    list_users,
    reject_user,
)
from src.core.config import Settings
from src.core.crypto import hash_password, verify_password
from src.core.csrf import _extract_cookie_session
from src.core.security_headers import SecurityHeadersMiddleware
from src.mikrotik.client import MikrotikRestClient
from src.mikrotik.normalizers import parse_routeros_duration
from src.mikrotik.safemode import remove_deadmans_switch
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User, UserRouterPermission
from src.models.inventory import (
    Router,
    RouterAdminStateEnum,
    RouterNetworkRoleEnum,
    TenantCustomRole,
)
from src.models.ipam import (
    FiberCutIncident,
    FiberCutStatusEnum,
    ONUModeEnum,
    SubscriberDevice,
)
from src.models.operations import RouterBackup
from src.schemas.enterprise import SdwanProvisionSpokeRequest
from src.schemas.field_ops import (
    FieldCertifyOrderRequest,
    FieldVerifySubscriberRequest,
)
from src.schemas.inventory import (
    CustomNetworkRoleCreate,
    UpdateRouterRequest,
    validate_router_target_url,
)
from src.schemas.ipam import BandwidthProfileCreate, SubscriberDeviceUpdate
from src.schemas.tenants import CreateTenantRequest, UpdateTenantRequest
from src.schemas.users import (
    AssignUserRoutersRequest,
    CreateUserRequest,
    RouterAssignmentItem,
)
from src.workers.runner import main as runner_main


class MockDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class MockDbResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None, scalar_val: Any = None):
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)
        self._scalar_val = scalar_val

    def scalars(self) -> MockDbScalars:
        return MockDbScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single

    def scalar_one(self) -> Any:
        if self._single is None:
            raise ValueError("No single scalar")
        return self._single

    def scalar(self) -> Any:
        return self._scalar_val if self._scalar_val is not None else self._single

    def all(self) -> list[Any]:
        return self._items


@pytest.fixture
def fake_request() -> MagicMock:
    req = MagicMock()
    req.client.host = "192.168.1.100"
    req.headers = {"User-Agent": "UnitTester/1.0", "content-type": "application/json"}
    return req


# ============================================================================
# INVENTORY TESTS (ROLES, FILTERS, QUOTAS, CSV)
# ============================================================================


@pytest.mark.asyncio
async def test_inventory_network_roles_lifecycle(fake_request: MagicMock) -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    role_item = TenantCustomRole(
        id=uuid.uuid4(),
        tenant_id=t_id,
        role_name="TOR_SWITCH",
        description="Top of Rack Switch",
        created_at=datetime.now(UTC),
    )
    db.execute.return_value = MockDbResult([role_item])

    async def fake_refresh(obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)

    db.refresh.side_effect = fake_refresh

    # 1. List
    roles_res = await list_network_roles(claims=claims, db=db)
    assert "TOR_SWITCH" in roles_res.roles
    assert len(roles_res.custom_roles) == 1

    # 2. Create custom role
    db.execute.return_value = MockDbResult([])  # no existing
    payload = CustomNetworkRoleCreate(role_name="DIST_SWITCH", description="Distribution switch")
    created = await create_custom_network_role(payload, fake_request, claims=claims, db=db)
    assert created.role_name == "DIST_SWITCH"

    # 2b. Conflict with default role
    with pytest.raises(HTTPException) as exc_def:
        await create_custom_network_role(CustomNetworkRoleCreate(role_name="CORE"), fake_request, claims=claims, db=db)
    assert exc_def.value.status_code == 400

    # 2c. Conflict with existing custom role
    db.execute.return_value = MockDbResult([role_item])
    with pytest.raises(HTTPException) as exc_exist:
        await create_custom_network_role(
            CustomNetworkRoleCreate(role_name="TOR_SWITCH"), fake_request, claims=claims, db=db
        )
    assert exc_exist.value.status_code == 400

    # 3. Delete custom role
    db.execute.return_value = MockDbResult([role_item])
    await delete_custom_network_role("TOR_SWITCH", fake_request, claims=claims, db=db)
    db.delete.assert_awaited_once_with(role_item)

    # 3b. Cannot delete default role
    with pytest.raises(HTTPException) as exc_del_def:
        await delete_custom_network_role("CORE", fake_request, claims=claims, db=db)
    assert exc_del_def.value.status_code == 400

    # 3c. Delete not found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_del_nf:
        await delete_custom_network_role("UNKNOWN_ROLE", fake_request, claims=claims, db=db)
    assert exc_del_nf.value.status_code == 404


@pytest.mark.asyncio
async def test_inventory_quota_and_filters() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()

    # 1. Tenant not found
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_tnf:
        await _check_tenant_router_quota(db, t_id)
    assert exc_tnf.value.status_code == 404

    # 2. Quota exceeded
    tenant = Tenant(id=t_id, slug="t-quota", name="Quota Tenant", max_routers_quota=5)
    db.get.return_value = tenant
    db.execute.return_value = MockDbResult(scalar_val=5)
    with pytest.raises(HTTPException) as exc_quota:
        await _check_tenant_router_quota(db, t_id)
    assert exc_quota.value.status_code == 409

    # 3. Role filters: non-admin without all_r
    mock_query = MagicMock()
    mock_query.where.return_value = mock_query
    claims_tech = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.FIELD_TECH.value, "all_r": False}
    _apply_role_filters(mock_query, claims_tech, t_id, u_id)
    assert mock_query.where.call_count >= 1

    # 4. Search filters
    q = MagicMock()
    q.where.return_value = q
    _apply_query_search_filters(
        q,
        network_role=RouterNetworkRoleEnum.CORE,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        tag="datacenter",
        search="edge-01",
    )
    assert q.where.call_count == 4


@pytest.mark.asyncio
async def test_inventory_csv_commit_multipart_form(fake_request: MagicMock) -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    tenant = Tenant(id=t_id, slug="t-csv", name="CSV Tenant", max_routers_quota=100)
    db.get.return_value = tenant
    db.execute.return_value = MockDbResult([])

    csv_text = (
        "display_name,api_base_url,api_port,api_username,api_password,network_role,admin_state,serial_number\n"
        "SW-ACC-01,https://10.0.0.1,443,admin,Secret123!,ACCESS_SWITCH,PRODUCTION,SN1234567\n"
    )

    fake_form = MagicMock()
    fake_upload = MagicMock(spec=UploadFile)
    fake_upload.read = AsyncMock(return_value=csv_text.encode("utf-8"))
    fake_form.get.return_value = fake_upload

    fake_request.headers = {"content-type": "multipart/form-data; boundary=something"}
    fake_request.form = AsyncMock(return_value=fake_form)

    with (
        patch("src.api.v1.inventory.write_audit_log", AsyncMock()),
        patch("src.api.v1.inventory.perform_discovery", AsyncMock()),
    ):
        res = await import_csv_commit(fake_request, claims=claims, db=db)
        assert res.imported_count == 1
        assert len(res.created_router_ids) == 1


# ============================================================================
# BACKUPS TESTS (RSC EXTRACTION, DIFF HUNKS, EXPORT RSC, DOWNLOAD)
# ============================================================================


def test_backups_diff_and_rsc_extraction() -> None:
    # 1. RSC extraction
    assert _extract_raw_rsc_text({"ret": "# router configuration"}) == "# router configuration"
    assert _extract_raw_rsc_text({"detail": "Error occurred"}) == "Error occurred"
    assert _extract_raw_rsc_text("raw text") == "raw text"

    # 2. Diff stats & hunks
    base = ["/interface ethernet", "set [ find default-name=ether1 ] name=wan1"]
    target = ["/interface ethernet", "set [ find default-name=ether1 ] name=wan1-renamed", "/ip route"]
    added, removed, diff_gen = _compute_diff_stats(base, target)
    assert added >= 1
    assert removed >= 1

    hunks = _build_side_by_side_hunks(diff_gen)
    assert len(hunks) >= 1


@pytest.mark.asyncio
async def test_export_router_rsc_variations() -> None:
    client = AsyncMock()

    # Case 1: file exists and is retrieved & deleted
    async def fake_get_file(path: str) -> list[dict[str, Any]]:
        fname = client.post.call_args[1]["json_data"]["file"]
        return [{"name": f"{fname}.rsc", "contents": "# Config export", ".id": "*1"}]

    client.get.side_effect = fake_get_file
    with patch("src.api.v1.backups.clean_rsc_export_comments", return_value="/interface ethernet\n"):
        res = await export_router_rsc(client)
        assert "/interface ethernet" in res
        client.delete.assert_awaited_once_with("file/*1")

    # Case 2: file not found in file list, fallback to post export
    client.get.side_effect = None
    client.get.return_value = []
    client.post.return_value = {"ret": "/ip address add\n"}
    with patch("src.api.v1.backups.clean_rsc_export_comments", return_value="/ip address add\n"):
        res_fallback = await export_router_rsc(client)
        assert "/ip address" in res_fallback

    # Case 3: cleaned text is empty -> raises 502
    with patch("src.api.v1.backups.clean_rsc_export_comments", return_value=""):
        with pytest.raises(HTTPException) as exc_502:
            await export_router_rsc(client)
        assert exc_502.value.status_code == 502


@pytest.mark.asyncio
async def test_download_backup_file_endpoints() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    b_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    # 1. 404 when backup not found or tenant mismatch
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_nf:
        await download_backup_file(r_id, b_id, format="rsc", claims=claims, db=db)
    assert exc_nf.value.status_code == 404

    # 2. Binary backup format missing file -> 400
    bk = RouterBackup(
        id=b_id,
        tenant_id=t_id,
        router_id=r_id,
        binary_backup_file_path=None,
    )
    db.get.return_value = bk
    with pytest.raises(HTTPException) as exc_bin:
        await download_backup_file(r_id, b_id, format="backup", claims=claims, db=db)
    assert exc_bin.value.status_code == 400

    # 3. Binary backup format success
    with tempfile.NamedTemporaryFile(suffix=".backup", delete=False) as tf:
        tf.write(b"MIKROTIK_BIN_BACKUP_CONTENT")
        tmp_name = tf.name

    try:
        bk.binary_backup_file_path = tmp_name
        res_bin = await download_backup_file(r_id, b_id, format="backup", claims=claims, db=db)
        assert res_bin.status_code == 200
        assert res_bin.body == b"MIKROTIK_BIN_BACKUP_CONTENT"
        assert "application/octet-stream" in res_bin.media_type
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    # 4. RSC text format success
    with (
        patch("src.api.v1.backups._decrypt_backup_rsc", return_value="# Decrypted Config\n/ip firewall\n"),
        patch("src.api.v1.backups.clean_rsc_export_comments", return_value="/ip firewall\n"),
    ):
        res_rsc = await download_backup_file(r_id, b_id, format="rsc", claims=claims, db=db)
        assert res_rsc.status_code == 200
        assert b"/ip firewall" in res_rsc.body
        assert "text/plain" in res_rsc.media_type


# ============================================================================
# TENANTS TESTS (GET, CREATE, UPDATE, CACHE INVALIDATION)
# ============================================================================


@pytest.mark.asyncio
async def test_tenants_admin_operations() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    other_tid = uuid.uuid4()

    # 1. get_tenant: unauthorized non-superadmin
    claims_user = {"tid": str(t_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    with pytest.raises(HTTPException) as exc_forbid:
        await get_tenant(other_tid, claims=claims_user, db=db)
    assert exc_forbid.value.status_code == 403

    # 2. get_tenant: 404 when not found
    claims_sa = {"tid": str(t_id), "rol": SystemRoleEnum.SUPERADMIN_GLOBAL.value}
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_tnf:
        await get_tenant(t_id, claims=claims_sa, db=db)
    assert exc_tnf.value.status_code == 404

    # 3. get_tenant: 200 success
    now = datetime.now(UTC)
    tenant_obj = Tenant(
        id=t_id,
        slug="corp-alpha",
        name="Corp Alpha",
        tax_id="J-12345678-0",
        status=TenantStatusEnum.ACTIVE,
        max_routers_quota=100,
        max_users_quota=50,
        require_2fa_all_users=True,
        default_safemode_seconds=60,
        created_at=now,
        updated_at=now,
    )
    db.execute.return_value = MockDbResult([tenant_obj])
    res_get = await get_tenant(t_id, claims=claims_sa, db=db)
    assert res_get.slug == "corp-alpha"

    # 4. create_tenant: slug conflict 409
    create_body = CreateTenantRequest(
        slug="corp-alpha",
        name="Corp Alpha 2",
        admin_username="admin2",
        admin_email="admin2@alpha.com",
        admin_full_name="Admin Two",
        admin_password="Password123!",
    )
    db.execute.return_value = MockDbResult([tenant_obj])  # existing slug
    with pytest.raises(HTTPException) as exc_slug:
        await create_tenant(create_body, claims=claims_sa, db=db)
    assert exc_slug.value.status_code == 409

    # 5. create_tenant: success
    db.execute.return_value = MockDbResult([])  # slug available

    async def fake_tenant_refresh(obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now

    db.refresh.side_effect = fake_tenant_refresh
    new_t = await create_tenant(create_body, claims=claims_sa, db=db)
    assert new_t.name == "Corp Alpha 2"

    # 6. update_tenant: 404
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_up_nf:
        await update_tenant(uuid.uuid4(), UpdateTenantRequest(name="Updated"), claims=claims_sa, db=db)
    assert exc_up_nf.value.status_code == 404

    # 7. update_tenant: success with redis delete
    db.execute.return_value = MockDbResult([tenant_obj])
    with patch("src.api.v1.tenants.get_redis_client") as mock_redis_factory:
        mock_redis = AsyncMock()
        mock_redis_factory.return_value = mock_redis
        updated = await update_tenant(t_id, UpdateTenantRequest(name="Corp Alpha New"), claims=claims_sa, db=db)
        assert updated.name == "Corp Alpha New"
        mock_redis.delete.assert_awaited_once_with(f"rg:{t_id}:features")

    # 8. invalidate_tenant_features_cache exception handling
    with patch("src.api.v1.tenants.get_redis_client") as mock_rf:
        mock_rf.return_value.delete.side_effect = Exception("Redis connection error")
        await invalidate_tenant_features_cache(t_id)


# ============================================================================
# USERS TESTS (FILTERS & SOFT-DELETE ROLLBACK)
# ============================================================================


@pytest.mark.asyncio
async def test_users_filtering_and_delete_fallback() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    now = datetime.now(UTC)

    u1 = User(
        id=uuid.uuid4(),
        tenant_id=t_id,
        username="super1",
        email="super1@test.com",
        full_name="Super One",
        role=SystemRoleEnum.SUPERVISOR,
        is_active=False,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=False,
        has_all_routers_access=True,
        allowed_cidr_list=[],
        created_at=now,
        updated_at=now,
    )
    db.execute.return_value = MockDbResult([u1])

    # 1. list_users with combinations
    res_role = await list_users(role=SystemRoleEnum.SUPERVISOR, claims=claims, db=db)
    assert len(res_role) == 1

    res_pending = await list_users(pending_only=True, claims=claims, db=db)
    assert len(res_pending) == 1

    res_active = await list_users(is_active=False, claims=claims, db=db)
    assert len(res_active) == 1

    res_search = await list_users(search="super", claims=claims, db=db)
    assert len(res_search) == 1

    # 2. reject_user: 404 when not found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_u_nf:
        await reject_user(uuid.uuid4(), claims=claims, db=db)
    assert exc_u_nf.value.status_code == 404

    # 3. reject_user: DB error triggers soft-delete fallback
    db.execute.return_value = MockDbResult([u1])
    db.delete.side_effect = Exception("Foreign key constraint")
    await reject_user(u1.id, claims=claims, db=db)
    assert db.rollback.await_count >= 1
    assert u1.is_active is False
    assert u1.is_locked is True


# ============================================================================
# FIELD OPS & SUBSCRIBERS TESTS (LIVE VERIFY, CUT DETECTION, CERTIFY 404)
# ============================================================================


@pytest.mark.asyncio
async def test_field_ops_live_verification_and_fiber_cut(fake_request: MagicMock) -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.FIELD_TECH.value}

    router_obj = Router(id=r_id, tenant_id=t_id, api_base_url="https://10.250.0.1:443", api_port=443)
    subscriber = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-9988",
        service_type="PPPOE",
        pppoe_username="cli-user-99",
        onu_mac_address="AA:BB:CC:11:22:33",
        onu_mode=ONUModeEnum.ROUTER,
    )

    def fake_db_exec(stmt: Any, *args: Any, **kwargs: Any) -> MockDbResult:
        s = str(stmt).lower()
        if "from routers" in s:
            return MockDbResult([router_obj])
        return MockDbResult([subscriber])

    db.execute.side_effect = fake_db_exec
    db.get.return_value = router_obj

    # 1. PPPoE live verification with MikrotikRestClient mock
    mock_client = AsyncMock()
    mock_client.get.return_value = [{"address": "100.64.1.20", "caller-id": "AA:BB:CC:11:22:33"}]

    with (
        patch("src.api.v1.field_ops.MikrotikRestClient") as mock_rc,
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()),
    ):
        mock_rc.return_value.__aenter__.return_value = mock_client
        payload = FieldVerifySubscriberRequest(customer_service_id=subscriber.id, onu_scanned_mac="AA:BB:CC:11:22:33")
        res_v = await verify_subscriber_live(subscriber.id, payload, db=db, claims=claims)
        assert res_v.session_active is True
        assert res_v.detected_mode == "ROUTER"

    # 2. DHCP live verification
    subscriber.service_type = "DHCP"
    subscriber.pppoe_username = None
    mock_client.get.return_value = [{"mac-address": "AA:BB:CC:11:22:33", "address": "100.64.1.50", "status": "bound"}]
    with (
        patch("src.api.v1.field_ops.MikrotikRestClient") as mock_rc,
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()),
    ):
        mock_rc.return_value.__aenter__.return_value = mock_client
        res_dhcp = await verify_subscriber_live(subscriber.id, payload, db=db, claims=claims)
        assert res_dhcp.session_active is True
        assert res_dhcp.assigned_ipv4 == "100.64.1.50"

    # 3. Certify installation 404
    db.execute.side_effect = None
    db.execute.return_value = MockDbResult([])
    cert_payload = FieldCertifyOrderRequest(
        order_id=uuid.uuid4(),
        onu_scanned_serial="SN9988",
        onu_scanned_mac="AA:BB:CC:11:22:33",
        tech_latitude=10.5,
        tech_longitude=-66.9,
    )
    with pytest.raises(HTTPException) as exc_cert_nf:
        await certify_installation(cert_payload, db=db, claims=claims)
    assert exc_cert_nf.value.status_code == 404

    # 4. Fiber cut detection: updating existing incident with mass_outage_threshold
    tenant_mock = Tenant(id=t_id, slug="tenant-qa", name="Tenant QA", mass_outage_threshold=10)
    db.execute.side_effect = [
        MockDbResult(items=[(r_id, "pon-1", "BOX-A", 15)]),  # results of group-by
        MockDbResult([tenant_mock]),  # tenant query
        MockDbResult(
            [
                FiberCutIncident(
                    id=uuid.uuid4(),
                    tenant_id=t_id,
                    router_id=r_id,
                    pon_port="pon-1",
                    status=FiberCutStatusEnum.DETECTED,
                    affected_onus_count=10,
                )
            ]
        ),  # existing incident
    ]
    with (
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()),
        patch("src.redis_layer.client.get_redis_client", MagicMock()),
    ):
        incidents = await detect_fiber_cuts_engine(threshold_onus=5, db=db, claims=claims)
        assert len(incidents) == 1
        assert incidents[0].affected_onus_count == 15


@pytest.mark.asyncio
async def test_subscribers_device_update_and_script_edge_cases() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    # 1. Update subscriber device 404
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_dev_nf:
        await update_subscriber_device(
            uuid.uuid4(), SubscriberDeviceUpdate(onu_mac_address="00:11:22:33:44:55"), db=db, claims=claims
        )
    assert exc_dev_nf.value.status_code == 404

    # 2. Queue script 404 when device not found
    with pytest.raises(HTTPException) as exc_q_nf:
        await generate_subscriber_mikrotik_queue_script(uuid.uuid4(), db=db, claims=claims)
    assert exc_q_nf.value.status_code == 404

    # 3. Queue script 404 when bandwidth profile does not exist
    dev = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=t_id,
        endpoint_identifier="EP-MISSING-PROF",
        bandwidth_profile_id=uuid.uuid4(),
    )
    db.execute.side_effect = [
        MockDbResult([dev]),  # device found
        MockDbResult([]),  # profile not found
    ]
    with pytest.raises(HTTPException) as exc_prof_nf:
        await generate_subscriber_mikrotik_queue_script(dev.id, db=db, claims=claims)
    assert exc_prof_nf.value.status_code == 404


@pytest.mark.asyncio
async def test_inventory_csv_commit_edge_branches(fake_request: MagicMock) -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    tenant = Tenant(id=t_id, slug="t-csv2", name="CSV Tenant 2", max_routers_quota=100)
    db.get.return_value = tenant
    db.execute.return_value = MockDbResult([], scalar_val=0)

    # 1. upload is None
    fake_form = MagicMock()
    fake_form.get.return_value = None
    fake_request.headers = {"content-type": "multipart/form-data; boundary=xyz"}
    fake_request.form = AsyncMock(return_value=fake_form)

    with pytest.raises(HTTPException) as exc_no_file:
        await import_csv_commit(fake_request, claims=claims, db=db)
    assert exc_no_file.value.status_code == 400

    # 2. UnicodeDecodeError
    fake_upload_bad = MagicMock(spec=UploadFile)
    fake_upload_bad.read = AsyncMock(return_value=b"\xff\xfe\x00\x00bad_unicode")
    fake_form.get.return_value = fake_upload_bad

    with pytest.raises(HTTPException) as exc_bad_utf:
        await import_csv_commit(fake_request, claims=claims, db=db)
    assert exc_bad_utf.value.status_code == 400

    # 3. not items (empty rows or no valid rows)
    fake_upload_empty = MagicMock(spec=UploadFile)
    fake_upload_empty.read = AsyncMock(return_value=b"col1,col2\n")
    fake_form.get.return_value = fake_upload_empty
    db.execute.return_value = MockDbResult([], scalar_val=0)

    with pytest.raises(HTTPException) as exc_empty:
        await import_csv_commit(fake_request, claims=claims, db=db)
    assert exc_empty.value.status_code == 400

    # 4. Oversized CSV file (> 2 MB)
    fake_upload_oversized = MagicMock(spec=UploadFile)
    fake_upload_oversized.read = AsyncMock(return_value=b"x" * (2 * 1024 * 1024 + 1))
    fake_form.get.return_value = fake_upload_oversized
    with pytest.raises(HTTPException) as exc_oversized:
        await import_csv_commit(fake_request, claims=claims, db=db)
    assert exc_oversized.value.status_code == 400
    assert "2 MB" in exc_oversized.value.detail


@pytest.mark.asyncio
async def test_subscribers_alias_and_delete() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    subscriber = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=t_id,
        endpoint_identifier="EP-ALIAS-01",
        device_serial="OLD-SERIAL",
    )
    db.execute.return_value = MockDbResult([subscriber])

    # 1. Update with onu_serial_number alias
    with patch("src.api.v1.subscribers.write_audit_log", AsyncMock()):
        update_res = await update_subscriber_device(
            subscriber.id,
            SubscriberDeviceUpdate(onu_serial_number="NEW-SERIAL-99"),
            db=db,
            claims=claims,
        )
        assert update_res.device_serial == "NEW-SERIAL-99"

    # 2. Delete subscriber device 404
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_del_nf:
        from src.api.v1.subscribers import delete_subscriber_device

        await delete_subscriber_device(uuid.uuid4(), db=db, claims=claims)
    assert exc_del_nf.value.status_code == 404


@pytest.mark.asyncio
async def test_users_permissions_and_approve_404() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    db.execute.return_value = MockDbResult([])

    from src.api.v1.users import (
        ApproveUserRequest,
        approve_user,
        assign_router_permissions,
        get_user_router_permissions,
    )
    from src.schemas.users import AssignUserRoutersRequest

    # 1. get_user_router_permissions 404
    with pytest.raises(HTTPException) as exc_perm_nf:
        await get_user_router_permissions(uuid.uuid4(), claims=claims, db=db)
    assert exc_perm_nf.value.status_code == 404

    # 2. assign_router_permissions 404
    with pytest.raises(HTTPException) as exc_assign_nf:
        await assign_router_permissions(uuid.uuid4(), AssignUserRoutersRequest(permissions=[]), claims=claims, db=db)
    assert exc_assign_nf.value.status_code == 404

    # 3. approve_user 404
    with pytest.raises(HTTPException) as exc_app_nf:
        await approve_user(
            uuid.uuid4(),
            ApproveUserRequest(role=SystemRoleEnum.SUPPORT_L1, has_all_routers_access=True, allowed_cidr_list=[]),
            claims=claims,
            db=db,
        )
    assert exc_app_nf.value.status_code == 404


@pytest.mark.asyncio
async def test_users_permissions_and_management_success_flow() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(admin_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    now = datetime.now(UTC)

    target_user = User(
        id=u_id,
        tenant_id=t_id,
        username="tech1",
        email="tech1@test.com",
        full_name="Tech One",
        role=SystemRoleEnum.SUPPORT_L1,
        is_active=False,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=True,
        totp_secret_ciphertext="secret",
        totp_secret_iv="iv",
        totp_secret_tag="tag",
        has_all_routers_access=False,
        allowed_cidr_list=[],
        created_at=now,
        updated_at=now,
    )

    tag_mock = MagicMock()
    tag_mock.tag_name = "Core-Zone"

    router_obj = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Router-01",
        network_role=RouterNetworkRoleEnum.CORE,
    )
    router_obj.tags = [tag_mock]

    perm_obj = UserRouterPermission(
        id=uuid.uuid4(),
        tenant_id=t_id,
        user_id=u_id,
        router_id=r_id,
        can_read=True,
        can_write_layer1=False,
        can_write_layer2=False,
        can_execute_diagnostics=True,
        can_trigger_backup=False,
        can_reboot=False,
        bypass_maker_checker=False,
        assigned_by=admin_id,
    )

    from src.api.v1.users import (
        ApproveUserRequest,
        Reset2FARequest,
        ToggleRegistrationRequest,
        approve_user,
        assign_router_permissions,
        get_user_router_permissions,
        reset_user_2fa,
        toggle_registration,
    )
    from src.schemas.users import AssignUserRoutersRequest, RouterAssignmentItem

    def fake_users_db_exec(stmt: Any, *args: Any, **kwargs: Any) -> MockDbResult:
        s = str(stmt).lower()
        if "set_config" in s:
            return MockDbResult([])
        if "from users" in s:
            return MockDbResult([target_user])
        if "from routers" in s:
            return MockDbResult([router_obj])
        if "from user_router_permissions" in s:
            return MockDbResult([perm_obj])
        return MockDbResult([])

    db.execute.side_effect = fake_users_db_exec
    db.refresh = AsyncMock()

    # 1. get_user_router_permissions: success
    perms_res = await get_user_router_permissions(u_id, claims=claims, db=db)
    assert perms_res["has_all_routers_access"] is False
    assert len(perms_res["permissions"]) == 1
    assert perms_res["permissions"][0]["router_name"] == "Router-01"
    assert perms_res["permissions"][0]["tag"] == "Core-Zone"
    assert perms_res["permissions"][0]["can_read"] is True

    # 2. assign_router_permissions: success
    assign_req = AssignUserRoutersRequest(
        has_all_routers_access=True,
        router_assignments=[
            RouterAssignmentItem(
                router_id=r_id,
                can_read=True,
                can_write_layer1=True,
                can_execute_diagnostics=True,
            )
        ],
    )
    assign_res = await assign_router_permissions(u_id, assign_req, claims=claims, db=db)
    assert assign_res["status"] == "success"
    assert assign_res["assigned_count"] == 1
    assert target_user.has_all_routers_access is True

    # 3. approve_user: success
    app_req = ApproveUserRequest(
        role=SystemRoleEnum.FIELD_TECH,
        has_all_routers_access=False,
        allowed_cidr_list=["192.168.1.0/24"],
    )
    approved_user = await approve_user(u_id, app_req, claims=claims, db=db)
    assert approved_user.role == SystemRoleEnum.FIELD_TECH
    assert target_user.is_active is True

    # 4. reset_user_2fa: success
    with patch("src.api.v1.users.kill_all_user_sessions", AsyncMock()):
        r2fa_res = await reset_user_2fa(u_id, Reset2FARequest(admin_totp_code="123456"), claims=claims, db=db)
        assert r2fa_res["status"] == "2fa_reset_completed"
        assert target_user.totp_enabled is False
        assert target_user.totp_secret_ciphertext is None

    # 5. toggle_registration: success
    with patch("src.api.v1.users.get_redis_client") as mock_rf:
        mock_redis = AsyncMock()
        mock_rf.return_value = mock_redis
        toggle_res = await toggle_registration(ToggleRegistrationRequest(enabled=True), claims=claims)
        assert toggle_res["registration_enabled"] is True
        mock_redis.set.assert_awaited_once_with("rg:config:public_registration_enabled", "true")


async def test_extended_coverage_helpers() -> None:
    # 1. Settings default URLs logic
    s1 = Settings(
        POSTGRES_USER="test_u",
        POSTGRES_PASSWORD="test_p",
        POSTGRES_DB="test_db",
        REDIS_PASSWORD="redis_p",
        ROSGRID_DATABASE_URL="",
        ROSGRID_SYNC_DATABASE_URL="",
        ROSGRID_REDIS_URL="",
    )
    assert "test_u:test_p@" in s1.ROSGRID_DATABASE_URL
    assert ":redis_p@" in s1.ROSGRID_REDIS_URL

    s2 = Settings(
        POSTGRES_USER="test_u2",
        POSTGRES_PASSWORD="",
        POSTGRES_DB="test_db",
        REDIS_PASSWORD="",
        ROSGRID_DATABASE_URL="",
        ROSGRID_SYNC_DATABASE_URL="",
        ROSGRID_REDIS_URL="",
        ROSGRID_CORS_ORIGINS="http://localhost:3000,http://localhost:8080",
    )
    assert "test_u2@" in s2.ROSGRID_DATABASE_URL
    assert "redis://rosgrid_redis:6379/0" == s2.ROSGRID_REDIS_URL
    assert "http://localhost:3000" in s2.cors_origins_list

    # 2. Inventory schemas & validator
    assert validate_router_target_url(None) is None
    assert validate_router_target_url("") == ""
    assert validate_router_target_url("   ") == "   "
    up_req = UpdateRouterRequest(api_base_url="https://203.0.113.1")
    assert up_req.api_base_url == "https://203.0.113.1"

    # 3. Users schemas validators
    assert CreateUserRequest.normalize_cidr_list(None) == []
    assert CreateUserRequest.normalize_cidr_list("10.0.0.0/24, 192.168.1.0/24") == [
        "10.0.0.0/24",
        "192.168.1.0/24",
    ]
    assert CreateUserRequest.normalize_cidr_list(["10.0.0.1/32"]) == ["10.0.0.1/32"]
    assert CreateUserRequest.normalize_cidr_list(12345) == []

    u_req = CreateUserRequest(
        username="coverage_user",
        email="cov@example.com",
        password="ValidPassword123!",
        role=SystemRoleEnum.NOC_MONITOR,
        full_name="   ",
    )
    assert u_req.temporary_password == "ValidPassword123!"
    assert u_req.full_name == "coverage_user"

    u_req2 = CreateUserRequest(
        username="coverage_user2",
        email="cov2@example.com",
        temporary_password="TempPassword123!",
        role=SystemRoleEnum.NOC_MONITOR,
        full_name="Full Name Two",
    )
    assert u_req2.temporary_password == "TempPassword123!"

    with pytest.raises(ValueError, match="Se requiere una contraseña"):
        CreateUserRequest(
            username="bad_pass_user",
            email="cov3@example.com",
            role=SystemRoleEnum.NOC_MONITOR,
        )

    r_assign_item = RouterAssignmentItem(router_id=uuid.uuid4())
    assign_req = AssignUserRoutersRequest(permissions=[r_assign_item])
    assert assign_req.router_assignments == [r_assign_item]

    # 4. CSRF extract cookie session exception branch
    class DummyRequest:
        cookies = {"__Host-rg_at": "invalid_jwt_token_payload"}
        headers: dict[str, str] = {}
        state = None

    sid, tid = _extract_cookie_session(DummyRequest())  # type: ignore[arg-type]
    assert sid is None and tid is None

    # 5. BGP Looking Glass helpers
    assert _parse_communities("65000:100, 65000:200") == ["65000:100", "65000:200"]
    assert _parse_communities(12345) == ["12345"]
    route_parsed = _parse_route_item({"scope": "invalid_int", "active": "yes"})
    assert route_parsed.scope is None
    assert route_parsed.active is True

    # 6. Diagnostics 360 Torch helpers
    assert _parse_torch_rate(50000) == 50.0
    assert _parse_torch_rate(None) == 0.0
    assert _parse_torch_rate("1500") == 1.5
    assert _parse_torch_rate("10mbps") == 10000.0
    assert _parse_torch_rate("100kbps") == 100.0
    assert _parse_torch_rate("1000bps") == 1.0
    assert _parse_torch_rate("bad_rate") == 0.0
    assert _parse_torch_flows(None) == []
    flows = _parse_torch_flows(
        [
            "not-a-dict",
            {"protocol": "tcp", "port": "bad_port", "tx": 1000},
        ]
    )
    assert len(flows) == 1
    assert flows[0].port is None

    # 7. SecurityHeadersMiddleware
    sec_mw = SecurityHeadersMiddleware(app=MagicMock())
    req_api = MagicMock(spec=Request)
    req_api.url = URL("http://localhost:8000/api/v1/health")

    async def _dummy_call_next(r: Request) -> Response:
        return Response(content="ok")

    sec_res = await sec_mw.dispatch(req_api, _dummy_call_next)
    assert sec_res.headers["Server"] == "RoSGrid"
    assert "no-store" in sec_res.headers["Cache-Control"]

    # 8. Crypto helpers
    assert verify_password("", "") is False
    valid_hash = hash_password("CorrectPass123!")
    assert verify_password("WrongPass123!", valid_hash) is False
    assert verify_password("CorrectPass123!", valid_hash) is True
    with pytest.raises(ValueError, match="no puede estar vacía"):
        hash_password("")

    # 9. Sessions terminate 404
    with patch("src.api.v1.sessions.kill_session", AsyncMock(return_value=False)):
        with pytest.raises(HTTPException) as exc_info:
            await terminate_session(
                session_id="nonexistent_sid",
                claims={"tid": "t_1", "sub": "u_1"},
                body=None,
            )
        assert exc_info.value.status_code == 404

    # 10. Subscribers get_tenant_id 401
    with pytest.raises(HTTPException) as sub_exc:
        get_tenant_id({})
    assert sub_exc.value.status_code == 401

    # 11. Tenants invalidate cache redis error
    with patch("src.api.v1.tenants.get_redis_client") as mock_rc:
        mock_r = AsyncMock()
        mock_r.delete.side_effect = RuntimeError("redis down")
        mock_rc.return_value = mock_r
        await invalidate_tenant_features_cache(uuid.uuid4())

    # 12. MikroTik normalizers & client & safemode
    assert parse_routeros_duration("42") == 42
    mock_resp = httpx.Response(status_code=200, text="raw-response-text")
    mt_client = MikrotikRestClient(host="10.0.0.1", username="admin", password="p")
    assert mt_client._parse_response_body(mock_resp) == "raw-response-text"
    mock_mt = AsyncMock()
    mock_mt.get.side_effect = RuntimeError("network failed")
    assert await remove_deadmans_switch(mock_mt, "test_job") is False

    # 13. Workers runner KeyboardInterrupt
    with (
        patch("asyncio.run", side_effect=KeyboardInterrupt),
        patch("src.workers.runner.main_workers_runner", AsyncMock()),
    ):
        with pytest.raises(SystemExit):
            runner_main()

    # 14. Traffic flow anomalies & stats
    atype1, sev1 = _evaluate_anomaly_severity(10, 50, 50, ["udp"])
    assert atype1 == "HIGH_PPS_BURST" and sev1 == "HIGH"
    atype2, sev2 = _evaluate_anomaly_severity(10, 10, 50, ["udp"])
    assert atype2 == "HIGH_CONNECTION_COUNT" and sev2 == "HIGH"
    stats_map = _aggregate_connection_stats(
        [
            "not-a-dict",
            {"src-address": ""},
            {"src-address": "198.51.100.1:1234", "orig-packets": "bad-int"},
        ]
    )
    assert "198.51.100.1" in stats_map

    # 15. RBAC role overrides & exceptions
    with patch("src.api.v1.rbac.get_redis_client") as mock_rc:
        mock_r = AsyncMock()
        mock_r.get.side_effect = RuntimeError("redis error")
        mock_rc.return_value = mock_r
        assert await _get_tenant_role_overrides("tid_1", "role_1") is None

    mock_rbac_db = AsyncMock()
    with pytest.raises(HTTPException) as rbac_exc1:
        await update_role_permissions(
            role_name="INVALID_ROLE_NAME",
            payload=UpdateRolePermissionsRequest(permissions={}),
            claims={"tid": str(uuid.uuid4()), "sub": "admin"},
            db=mock_rbac_db,
        )
    assert rbac_exc1.value.status_code == 400

    with pytest.raises(HTTPException) as rbac_exc2:
        await update_role_permissions(
            role_name=SystemRoleEnum.SUPERADMIN_GLOBAL.value,
            payload=UpdateRolePermissionsRequest(permissions={}),
            claims={"tid": str(uuid.uuid4()), "sub": "admin"},
            db=mock_rbac_db,
        )
    assert rbac_exc2.value.status_code == 403

    # 16. SDWAN & Switching & Subscribers duplicate 404/409
    mock_res_none = MagicMock()
    mock_res_none.scalar_one_or_none.return_value = None

    mock_sd_db = AsyncMock()
    mock_sd_db.execute.return_value = mock_res_none
    with pytest.raises(HTTPException) as sd_exc:
        await provision_spoke_tunnel(
            payload=SdwanProvisionSpokeRequest(
                hub_router_id=uuid.uuid4(),
                spoke_router_id=uuid.uuid4(),
                spoke_name="spoke-1",
            ),
            request=MagicMock(),
            claims={"tid": str(uuid.uuid4())},
            db=mock_sd_db,
        )
    assert sd_exc.value.status_code == 404

    mock_sw_db = AsyncMock()
    mock_sw_db.execute.return_value = mock_res_none
    with pytest.raises(HTTPException) as sw_exc:
        await get_dhcp_snooping_state(
            router_id=uuid.uuid4(),
            claims={"tid": str(uuid.uuid4())},
            db=mock_sw_db,
        )
    assert sw_exc.value.status_code == 404

    mock_res_found = MagicMock()
    mock_res_found.scalar_one_or_none.return_value = MagicMock()
    mock_sub_db = AsyncMock()
    mock_sub_db.execute.return_value = mock_res_found
    with pytest.raises(HTTPException) as bp_exc:
        await create_bandwidth_profile(
            payload=BandwidthProfileCreate(name="Gold", rate_down_kbps=100000, rate_up_kbps=50000),
            claims={"tid": str(uuid.uuid4())},
            db=mock_sub_db,
        )
    assert bp_exc.value.status_code == 409
