# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite unitaria de cobertura profunda (Spec 114) para Subscribers, Wi-Fi CAPsMAN,
IPAM, Inventory, WebFig Layer 2, Auth, DiagnosticGovernor y SyslogCollector."""

from __future__ import annotations

import asyncio
import io
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pyotp
import pytest
from fastapi import HTTPException, UploadFile

from src.api.v1.auth import (
    _build_auth_session_response,
    _execute_2fa_verification,
    _fetch_preauth_state,
    _verify_user_credentials,
    get_bootstrap_status,
    logout,
    refresh_access_token,
    register_user,
    session_closing,
    switch_tenant,
    verify_2fa,
)
from src.api.v1.inventory import (
    _ensure_custom_network_roles,
    delete_router,
    import_csv_dry_run,
    list_network_roles,
    list_routers,
    repin_ssl,
    sync_discovery,
    sync_router_syslog,
    update_router,
)
from src.api.v1.ipam import (
    _get_router_client as ipam_get_router_client,
)
from src.api.v1.ipam import (
    _sync_all_tenant_routers_ipam,
    _sync_single_router_ipam,
    create_address,
    create_customer_service,
    create_prefix,
    create_vrf,
    get_next_available_resource,
    list_addresses,
    list_customer_services,
    list_prefixes,
)
from src.api.v1.ipam import (
    get_tenant_id as ipam_get_tenant_id,
)
from src.api.v1.subscribers import (
    _collect_router_live_candidates,
    _discover_and_pair_live_ip_from_router,
    _find_mac_match_in_candidates,
    _get_or_create_default_vrf,
    _get_router_client,
    _normalize_mac_address,
    _provision_subscriber_on_mikrotik,
    _resolve_and_validate_nap_port,
    _resolve_or_create_subscriber_ipv4,
    _validate_subscriber_csv_row,
    create_subscriber_device,
    delete_bandwidth_profile,
    generate_mikrotik_bandwidth_script,
    get_device_operational_status,
    get_subscriber_live_pairing_candidates,
    import_subscribers_csv_commit,
    import_subscribers_csv_dry_run,
    list_subscriber_devices,
    ping_subscriber_device_live,
    simulate_subscribers_from_dhcp,
    sync_dhcp_clients,
    update_bandwidth_profile,
    update_subscriber_device,
)
from src.api.v1.webfig_layer2 import (
    _build_ros_query_stack,
    _extract_rsc_section_for_path,
    _fetch_latest_backup_section,
    _fetch_live_submenu_rsc,
    _filter_items_locally,
    _get_cached_l2_schema,
    _is_ros_package_active,
    _normalize_proplist,
    _parse_console_inspect_syntax,
    _resolve_rpc_target_and_args,
    _resolve_schema_via_inspect,
    _set_cached_l2_schema,
    _synthesize_rsc_from_items,
    execute_bulk_operation,
    execute_command,
    get_resource,
    query_resource_server_side,
    update_resource,
    update_singleton_resource,
)
from src.api.v1.wifi import (
    _record_wifi_audit,
    create_capsman_configuration,
    create_capsman_ssid,
    create_provisioning_rule,
    create_security_profile,
    delete_provisioning_rule,
    delete_security_profile,
    delete_wifi_client,
    get_capsman_overview,
    list_capsman_ssids,
    list_provisioning_rules,
    list_security_profiles,
    list_wifi_clients,
    quick_setup_wifi,
    reprovision_capsman_fleet,
    update_capsman_configuration,
)
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.models.inventory import (
    MaintenanceWindow,
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    SSLTrustStatusEnum,
)
from src.models.ipam import (
    BandwidthProfile,
    CustomerService,
    CustomerServiceStatusEnum,
    CustomerServiceTypeEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    IPFamilyEnum,
    OpticalBox,
    SubscriberDevice,
)
from src.models.operations import RouterBackup
from src.schemas.auth import (
    RegisterUserRequest,
    SwitchTenantRequest,
    Verify2FARequest,
)
from src.schemas.enterprise import (
    WifiConfigurationCreate,
    WifiConfigurationUpdate,
    WifiProvisioningRuleCreate,
    WifiQuickSetupRequest,
    WifiSecurityProfileCreate,
    WifiSsidProfile,
)
from src.schemas.inventory import RePinSSLRequest, UpdateRouterRequest
from src.schemas.ipam import (
    BandwidthProfileUpdate,
    CustomerServiceCreate,
    IPAMAddressCreate,
    IPAMPrefixCreate,
    IPAMVrfCreate,
    SubscriberDeviceCreate,
    SubscriberDeviceUpdate,
    SubscriberLiveCandidateDhcpLease,
)
from src.schemas.webfig_layer2 import (
    ColumnSchemaItem,
    DynamicLayer2BulkRequest,
    DynamicLayer2CommandRequest,
    DynamicLayer2QueryRequest,
    DynamicLayer2WriteRequest,
    Layer2QueryFilterItem,
    Layer2RpcActionDescriptor,
)
from src.services.diagnostic_governor import DiagnosticGovernor
from src.workers.syslog_collector import (
    SyslogUdpProtocol,
    load_ip_router_map,
    parse_syslog_message,
    syslog_collector_worker_loop,
)
from tests.conftest import make_asserting_audit_mock


class _MockScalars:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def all(self) -> list[Any]:
        return list(self._items)

    def first(self) -> Any:
        return self._items[0] if self._items else None


class _MockResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None) -> None:
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single

    def scalars(self) -> _MockScalars:
        return _MockScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single

    def scalar_one(self) -> Any:
        return self._single

    def scalar(self) -> Any:
        return self._single

    def all(self) -> list[Any]:
        return list(self._items)


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock(return_value=_MockResult())
    db.scalar = AsyncMock(return_value=None)
    db.get = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


def _make_router(tenant_id: uuid.UUID, router_id: uuid.UUID | None = None, name: str = "r1") -> Router:
    rid = router_id or uuid.uuid4()
    aad = f"{tenant_id}:{rid}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"Secret123!", aad)
    vault = RouterCredentialsVault(
        router_id=rid,
        tenant_id=tenant_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
    )
    r = Router(
        id=rid,
        tenant_id=tenant_id,
        display_name=name,
        ros_identity=name,
        api_base_url="https://192.0.2.10",
        api_port=443,
        network_role="BNG_PPPOE",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="Caracas HQ",
        serial_number=f"SN-{rid.hex[:8].upper()}",
        is_reachable=True,
        ros_version="7.16.1",
        board_name="CCR2004",
        latitude=Decimal("10.480600"),
        longitude=Decimal("-66.903600"),
        online_since_date=datetime.now(UTC).date(),
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        created_by=uuid.uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    r.vault = vault
    r.tags = []
    return r


# ============================================================================
# 1. SUBSCRIBERS COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_subscribers_bandwidth_filters_sync_and_simulate() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "isp_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r1")

    # 1. 404 y 409 en bandwidth profiles (líneas 194, 228, 234, 261)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as e1:
        await update_bandwidth_profile(uuid.uuid4(), BandwidthProfileUpdate(name="New"), db=db, claims=claims)
    assert e1.value.status_code == 404

    with pytest.raises(HTTPException) as e2:
        await delete_bandwidth_profile(uuid.uuid4(), db=db, claims=claims)
    assert e2.value.status_code == 404

    with pytest.raises(HTTPException) as e3:
        await generate_mikrotik_bandwidth_script(uuid.uuid4(), db=db, claims=claims)
    assert e3.value.status_code == 404

    bp = BandwidthProfile(id=uuid.uuid4(), tenant_id=tid, name="100M", rate_up_kbps=100000, rate_down_kbps=100000)
    db.execute.side_effect = [_MockResult(single=bp), _MockResult(single=3)]
    with pytest.raises(HTTPException) as e409:
        await delete_bandwidth_profile(bp.id, db=db, claims=claims)
    assert e409.value.status_code == 409
    db.execute.side_effect = None

    # 2. list_subscriber_devices con los 5 filtros activos (líneas 327, 329, 331, 333, 335)
    db.execute.return_value = _MockResult(items=[])
    res_list = await list_subscriber_devices(
        router_id=r_obj.id,
        pon_port="gpon1",
        optical_box="NAP-01",
        bandwidth_profile_id=bp.id,
        status_filter="ACTIVE",
        db=db,
        claims=claims,
    )
    assert res_list == []

    # 3. _get_router_client con excepción de bóveda (líneas 348-349)
    with patch("src.api.v1.subscribers._create_client_from_vault", side_effect=RuntimeError("vault err")):
        fallback_cli = _get_router_client(r_obj, tid)
        assert fallback_cli.username == "admin"

    # 4. sync_dhcp_clients: reset_existing=True + 404 sin routers (líneas 379-386, 396)
    dev_existing = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        endpoint_identifier="PC-OFICINA-01 (192.168.10.50)",
        is_custom_coordinates=False,
        status=CustomerServiceStatusEnum.ACTIVE,
    )
    db.execute.side_effect = [
        _MockResult(single=Tenant(id=tid, isp_module_enabled=False)),
        _MockResult(items=[dev_existing]),
        _MockResult(items=[]),
    ]
    with pytest.raises(HTTPException) as exc_no_r:
        await sync_dhcp_clients(reset_existing=True, db=db, claims=claims)
    assert exc_no_r.value.status_code == 404
    db.execute.side_effect = None

    # 5. sync_dhcp_clients en modo corporativo con excepción de cliente + fallback DB IPAM + actualización (líneas 417-465)
    ip_row = IPAMAddress(
        id=uuid.uuid4(),
        tenant_id=tid,
        prefix_id=uuid.uuid4(),
        router_id=r_obj.id,
        address="192.168.10.50/32",
        mac_address="AA:BB:CC:DD:EE:01",
        ip_family=IPFamilyEnum.IPv4,
        status=IPAddressStatusEnum.DHCP_DYNAMIC,
    )
    bad_client = AsyncMock()
    bad_client.__aenter__ = AsyncMock(return_value=bad_client)
    bad_client.__aexit__ = AsyncMock(return_value=None)
    bad_client.get = AsyncMock(side_effect=RuntimeError("offline"))

    db.execute.side_effect = [
        _MockResult(single=Tenant(id=tid, isp_module_enabled=False)),
        _MockResult(items=[r_obj]),
        _MockResult(items=[ip_row]),
        _MockResult(single=dev_existing),
        _MockResult(single=1),
    ]
    with patch("src.api.v1.subscribers._get_router_client", return_value=bad_client):
        sync_corp = await sync_dhcp_clients(reset_existing=False, db=db, claims=claims)
    assert sync_corp.updated_count == 1
    db.execute.side_effect = None

    # Lease vacío (línea 442) y modo ISP (líneas 488-492)
    empty_lease_cli = AsyncMock()
    empty_lease_cli.__aenter__ = AsyncMock(return_value=empty_lease_cli)
    empty_lease_cli.__aexit__ = AsyncMock(return_value=None)
    empty_lease_cli.get = AsyncMock(return_value=[{"address": ""}])
    db.execute.side_effect = [
        _MockResult(single=Tenant(id=tid, isp_module_enabled=False)),
        _MockResult(items=[r_obj]),
        _MockResult(single=0),
    ]
    with patch("src.api.v1.subscribers._get_router_client", return_value=empty_lease_cli):
        await sync_dhcp_clients(reset_existing=False, db=db, claims=claims)
    db.execute.side_effect = None

    db.execute.side_effect = [
        _MockResult(single=Tenant(id=tid, isp_module_enabled=True)),
        _MockResult(items=[r_obj]),
        _MockResult(items=[dev_existing]),
        _MockResult(single=1),
    ]
    sync_isp = await sync_dhcp_clients(reset_existing=False, db=db, claims=claims)
    assert sync_isp.updated_count == 1
    db.execute.side_effect = None

    # 6. simulate_subscribers_from_dhcp: reset_existing=True + 404 sin routers y modo con client_ips (líneas 530-587, 625-633)
    db.execute.side_effect = [
        _MockResult(items=[dev_existing]),
        _MockResult(items=[]),
    ]
    with pytest.raises(HTTPException) as exc_sim404:
        await simulate_subscribers_from_dhcp(reset_existing=True, db=db, claims=claims)
    assert exc_sim404.value.status_code == 404
    db.execute.side_effect = None

    ip_vpcs = IPAMAddress(
        id=uuid.uuid4(),
        tenant_id=tid,
        prefix_id=uuid.uuid4(),
        router_id=r_obj.id,
        address="192.168.10.50/32",
        mac_address="00:50:79:66:68:01",
        description="DHCP VPCS Host",
        interface_name="ether3",
        ip_family=IPFamilyEnum.IPv4,
        status=IPAddressStatusEnum.DHCP_DYNAMIC,
    )
    db.execute.side_effect = [
        _MockResult(items=[r_obj]),
        _MockResult(items=[ip_vpcs]),
        _MockResult(single=dev_existing),
        _MockResult(single=1),
    ]
    with patch("src.api.v1.subscribers.write_audit_log", make_asserting_audit_mock()):
        sim_res = await simulate_subscribers_from_dhcp(reset_existing=False, db=db, claims=claims)
    assert sim_res.updated_count == 1
    db.execute.side_effect = None


@pytest.mark.asyncio
async def test_subscribers_provisioning_csv_live_candidates_and_ping() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "isp_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r1")
    r_bng = _make_router(tid, name="r-bng")

    # 1. _resolve_and_validate_nap_port 404, _get_or_create_default_vrf, _resolve_or_create_subscriber_ipv4 (líneas 723-772)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_nap:
        await _resolve_and_validate_nap_port(db, tid, uuid.uuid4(), 1, None)
    assert exc_nap.value.status_code == 404

    vrf = await _get_or_create_default_vrf(db, tid)
    assert vrf.name == "default"

    assert await _resolve_or_create_subscriber_ipv4(db, tid, r_obj.id, "   ") is None
    with pytest.raises(HTTPException) as exc_ip422:
        await _resolve_or_create_subscriber_ipv4(db, tid, r_obj.id, "invalid-ip")
    assert exc_ip422.value.status_code == 422

    existing_ip = IPAMAddress(
        id=uuid.uuid4(),
        tenant_id=tid,
        prefix_id=uuid.uuid4(),
        router_id=r_obj.id,
        address="100.64.0.10",
        ip_family=IPFamilyEnum.IPv4,
        status=IPAddressStatusEnum.ALLOCATED,
    )
    db.execute.return_value = _MockResult(single=existing_ip)
    resolved_id = await _resolve_or_create_subscriber_ipv4(
        db, tid, r_obj.id, "100.64.0.10", mac_address="AA:BB:CC:DD:EE:FF", description="Updated"
    )
    assert resolved_id == existing_ip.id
    assert existing_ip.mac_address == "AA:BB:CC:DD:EE:FF"

    # create_subscriber_device 409 conflict (línea 845)
    db.execute.side_effect = [_MockResult(single=r_obj), _MockResult(single=SubscriberDevice(id=uuid.uuid4()))]
    with pytest.raises(HTTPException) as exc_sub409:
        await create_subscriber_device(
            SubscriberDeviceCreate(router_id=r_obj.id, endpoint_identifier="DUP-01"),
            db=db,
            claims=claims,
        )
    assert exc_sub409.value.status_code == 409
    db.execute.side_effect = None

    # 2. _normalize_mac_address, _collect_router_live_candidates y _find_mac_match_in_candidates (líneas 955-1050)
    assert _normalize_mac_address("invalid-mac") == "INVALID-MAC"

    cand_cli = AsyncMock()
    cand_cli.__aenter__ = AsyncMock(return_value=cand_cli)
    cand_cli.__aexit__ = AsyncMock(return_value=None)
    cand_cli.get = AsyncMock(
        side_effect=[
            ["not-a-dict", {"address": ""}, {"address": "100.64.1.2", "mac-address": "aabb.ccdd.ee01"}],
            ["not-a-dict", {"name": ""}, {"name": "ppp1", "address": "100.64.2.2", "caller-id": "aabb.ccdd.ee02"}],
            ["not-a-dict", {"name": ""}, {"name": "ppp1"}, {"name": "ppp2", "remote-address": "100.64.2.3", "caller-id": "aabb.ccdd.ee03"}],
        ]
    )
    with patch("src.api.v1.subscribers._get_router_client", return_value=cand_cli):
        d_cands, p_cands = await _collect_router_live_candidates(r_obj, tid)
    assert len(d_cands) == 1
    assert len(p_cands) == 2
    assert _find_mac_match_in_candidates("AA:BB:CC:DD:EE:02", d_cands, p_cands) == "100.64.2.2"
    assert _find_mac_match_in_candidates("AA:BB:CC:DD:EE:99", d_cands, p_cands) is None

    err_cand_cli = AsyncMock()
    err_cand_cli.__aenter__ = AsyncMock(side_effect=RuntimeError("timeout"))
    err_cand_cli.__aexit__ = AsyncMock(return_value=None)
    with patch("src.api.v1.subscribers._get_router_client", return_value=err_cand_cli):
        await _collect_router_live_candidates(r_obj, tid)

    # 3. _provision_subscriber_on_mikrotik: DHCP dynamic lease make-static + patch, PPPoE patch + post + exception (líneas 1075-1128)
    prov_cli = AsyncMock()
    prov_cli.__aenter__ = AsyncMock(return_value=prov_cli)
    prov_cli.__aexit__ = AsyncMock(return_value=None)
    prov_cli.get = AsyncMock(
        return_value=["raw", {".id": "*L1", "address": "100.64.1.10", "mac-address": "AA:BB:CC:DD:EE:10", "dynamic": "true"}]
    )
    prov_cli.post = AsyncMock()
    prov_cli.patch = AsyncMock()
    with patch("src.api.v1.subscribers._get_router_client", return_value=prov_cli):
        await _provision_subscriber_on_mikrotik(
            r_obj, tid, CustomerServiceTypeEnum.DHCP, "SUB-10", "100.64.1.10", "AA:BB:CC:DD:EE:10"
        )
    prov_cli.post.assert_awaited_once_with("/ip/dhcp-server/lease/make-static", {".id": "*L1"})
    prov_cli.patch.assert_awaited_once()

    # PPPoE secret existente y nuevo sin password
    prov_cli.get = AsyncMock(return_value=[{".id": "*S1", "name": "ppp-user-1"}])
    with patch("src.api.v1.subscribers._get_router_client", return_value=prov_cli):
        await _provision_subscriber_on_mikrotik(
            r_obj, tid, CustomerServiceTypeEnum.PPPOE, "ppp-user-1", "100.64.1.11", "AA:BB:CC:DD:EE:11", "Pass123!"
        )
    prov_cli.get = AsyncMock(return_value=[])
    with patch("src.api.v1.subscribers._get_router_client", return_value=prov_cli):
        await _provision_subscriber_on_mikrotik(
            r_obj, tid, CustomerServiceTypeEnum.PPPOE, "ppp-user-2", None, None, None
        )
    with patch("src.api.v1.subscribers._get_router_client", return_value=err_cand_cli):
        await _provision_subscriber_on_mikrotik(
            r_obj, tid, CustomerServiceTypeEnum.PPPOE, "ppp-err", None, None, None
        )

    # 4. _validate_subscriber_csv_row y endpoints CSV dry-run / commit (líneas 1146-1394)
    p_err1 = _validate_subscriber_csv_row(
        {
            "endpoint_identifier": "",
            "router_name": "",
            "onu_serial_number": "X" * 70,
            "onu_mac_address": "BAD-MAC",
            "assigned_ipv4": "999.999.999.999",
            "box_port_number": "99",
            "latitude": "100.0",
            "longitude": "-200.0",
            "service_status": "INVALID",
        },
        2,
        {"r1": r_obj},
        set(),
        set(),
        set(),
        set(),
    )
    assert not p_err1.is_valid
    assert len(p_err1.errors) >= 6

    p_err2 = _validate_subscriber_csv_row(
        {
            "endpoint_identifier": "A" * 70,
            "router_name": "r1",
            "onu_serial_number": "DUP-SN",
            "box_port_number": "abc",
            "latitude": "not-a-float",
            "longitude": "10.0",
        },
        3,
        {"r1": r_obj},
        {(r_obj.id, ("A" * 70).lower())},
        {"DUP-SN"},
        set(),
        set(),
    )
    assert not p_err2.is_valid

    # CSV dry-run errores (>2MB, bad UTF-8, >500 filas)
    big_file = UploadFile(filename="big.csv", file=io.BytesIO(b"a" * (2 * 1024 * 1024 + 10)))
    with pytest.raises(HTTPException) as exc_big:
        await import_subscribers_csv_dry_run(file=big_file, db=db, claims=claims)
    assert exc_big.value.status_code == 400

    bad_utf8 = UploadFile(filename="bad.csv", file=io.BytesIO(b"\xff\xfe\x00\x00"))
    with pytest.raises(HTTPException) as exc_utf8:
        await import_subscribers_csv_dry_run(file=bad_utf8, db=db, claims=claims)
    assert exc_utf8.value.status_code == 400

    many_rows = "endpoint_identifier,router_name\n" + "\n".join(f"CLI-{i},r1" for i in range(505))
    many_file = UploadFile(filename="many.csv", file=io.BytesIO(many_rows.encode("utf-8")))
    db.execute.side_effect = [_MockResult(items=[r_obj]), _MockResult(items=[]), _MockResult(items=[])]
    with pytest.raises(HTTPException) as exc_many:
        await import_subscribers_csv_dry_run(file=many_file, db=db, claims=claims)
    assert exc_many.value.status_code == 400
    db.execute.side_effect = None

    # CSV commit: multipart sin archivo y con UTF-8 inválido
    req_mp = MagicMock()
    req_mp.headers = {"content-type": "multipart/form-data"}
    req_mp.form = AsyncMock(return_value={})
    db.execute.side_effect = [_MockResult(items=[r_obj]), _MockResult(items=[]), _MockResult(items=[])]
    with pytest.raises(HTTPException) as exc_mp1:
        await import_subscribers_csv_commit(req_mp, db=db, claims=claims)
    assert exc_mp1.value.status_code == 400

    bad_upload = MagicMock()
    bad_upload.read = AsyncMock(return_value=b"\xff\xfe\x00\x00")
    req_mp.form = AsyncMock(return_value={"file": bad_upload})
    db.execute.side_effect = [_MockResult(items=[r_obj]), _MockResult(items=[]), _MockResult(items=[])]
    with pytest.raises(HTTPException) as exc_mp2:
        await import_subscribers_csv_commit(req_mp, db=db, claims=claims)
    assert exc_mp2.value.status_code == 400
    db.execute.side_effect = None

    # 5. get_subscriber_live_pairing_candidates (404s y auto-switch BNG vía cand_match y fallback_bng, líneas 1496-1551)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_lc1:
        await get_subscriber_live_pairing_candidates(uuid.uuid4(), db=db, claims=claims)
    assert exc_lc1.value.status_code == 404

    sub_dev = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        optical_box_id=uuid.uuid4(),
        endpoint_identifier="CLI-01 (100.64.9.9)",
        onu_mac_address="AA:BB:CC:DD:EE:55",
        device_serial="SN55",
        service_type=CustomerServiceTypeEnum.DHCP,
    )
    box_obj = OpticalBox(id=sub_dev.optical_box_id, tenant_id=tid, router_id=r_obj.id, box_code="NAP-1")
    db.execute.side_effect = [
        _MockResult(single=sub_dev),
        _MockResult(single=box_obj),
        _MockResult(single=r_obj),
        _MockResult(single=None),
    ]
    with pytest.raises(HTTPException) as exc_lc2:
        await get_subscriber_live_pairing_candidates(sub_dev.id, db=db, claims=claims)
    assert exc_lc2.value.status_code == 404
    db.execute.side_effect = None

    # Auto-switch BNG por fallback_bng (líneas 1545-1551)
    db.execute.side_effect = [
        _MockResult(single=sub_dev),
        _MockResult(single=box_obj),
        _MockResult(single=r_obj),
        _MockResult(single=r_obj),
        _MockResult(items=[r_bng]),
        _MockResult(items=[]),
    ]
    with patch(
        "src.api.v1.subscribers._collect_router_live_candidates",
        AsyncMock(
            side_effect=[
                ([], []),
                ([SubscriberLiveCandidateDhcpLease(address="100.64.5.5", mac_address="11:22:33:44:55:66", status="bound")], []),
            ]
        ),
    ):
        lc_fb = await get_subscriber_live_pairing_candidates(sub_dev.id, bng_router_id=None, db=db, claims=claims)
    assert lc_fb.auto_switched_bng is True
    assert lc_fb.router_id == r_bng.id
    db.execute.side_effect = None

    # 6. update_subscriber_device con bng_router_id, pppoe_username y coordenadas (líneas 1631-1670)
    db.execute.side_effect = [
        _MockResult(single=sub_dev),
        _MockResult(single=r_bng),
        _MockResult(single=r_bng),
        _MockResult(single=sub_dev),
    ]
    with (
        patch("src.api.v1.subscribers._provision_subscriber_on_mikrotik", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.invalidate_cached_ping", AsyncMock()),
        patch("src.api.v1.subscribers.write_audit_log", make_asserting_audit_mock()) as mock_audit,
    ):
        upd_dev = await update_subscriber_device(
            sub_dev.id,
            SubscriberDeviceUpdate(
                bng_router_id=r_bng.id,
                pppoe_username="new_ppp_user",
                latitude=Decimal("10.500000"),
                longitude=Decimal("-66.800000"),
                pppoe_password="SecretPassword",
            ),
            db=db,
            claims=claims,
        )
    assert upd_dev.is_custom_coordinates is True
    mock_audit.assert_awaited_once()
    db.execute.side_effect = None

    # 7. _discover_and_pair_live_ip_from_router por DHCP lease y excepción (líneas 1759, 1774-1792)
    disc_cli = AsyncMock()
    disc_cli.__aenter__ = AsyncMock(return_value=disc_cli)
    disc_cli.__aexit__ = AsyncMock(return_value=None)
    disc_cli.get = AsyncMock(
        side_effect=[
            ["not-a-dict"],
            ["not-a-dict", {"address": ""}, {"address": "100.64.8.8", "mac-address": "AA:BB:CC:DD:EE:55"}],
        ]
    )
    sub_dev.onu_mac_address = None
    sub_dev.endpoint_identifier = "host-match"
    disc_cli.get = AsyncMock(
        side_effect=[
            ["not-a-dict"],
            ["not-a-dict", {"address": ""}, {"address": "100.64.8.8", "mac-address": "AA:BB:CC:DD:EE:88", "host-name": "host-match"}],
        ]
    )
    with (
        patch("src.api.v1.subscribers._get_router_client", return_value=disc_cli),
        patch("src.api.v1.subscribers._resolve_or_create_subscriber_ipv4", AsyncMock(return_value=uuid.uuid4())),
    ):
        disc_ip = await _discover_and_pair_live_ip_from_router(db, tid, r_obj, sub_dev)
    assert disc_ip == "100.64.8.8"
    assert sub_dev.onu_mac_address == "AA:BB:CC:DD:EE:88"

    # 8. ping_subscriber_device_live: sub inválido, 404s, IP desde paréntesis, time inválido, extended=True (líneas 1843-2015)
    bad_claims = {"tid": str(tid), "sub": "not-a-uuid", "username": "tech1"}
    db.execute.return_value = _MockResult(single=None)
    with (
        patch("src.api.v1.subscribers.DiagnosticGovernor.check_user_rate_limit", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.get_cached_ping", AsyncMock(return_value=None)),
        pytest.raises(HTTPException) as exc_p404,
    ):
        await ping_subscriber_device_live(uuid.uuid4(), force=False, extended=False, db=db, claims=bad_claims)
    assert exc_p404.value.status_code == 404

    sub_dev.assigned_ipv4 = None
    sub_dev.endpoint_identifier = "PC-01 (100.64.7.7)"
    db.execute.side_effect = [_MockResult(single=sub_dev), _MockResult(single=None)]
    with (
        patch("src.api.v1.subscribers.DiagnosticGovernor.check_user_rate_limit", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.invalidate_cached_ping", AsyncMock()),
        pytest.raises(HTTPException) as exc_pr404,
    ):
        await ping_subscriber_device_live(sub_dev.id, force=True, extended=True, db=db, claims=bad_claims)
    assert exc_pr404.value.status_code == 404
    db.execute.side_effect = None

    ping_cli = AsyncMock()
    ping_cli.__aenter__ = AsyncMock(return_value=ping_cli)
    ping_cli.__aexit__ = AsyncMock(return_value=None)
    ping_cli.post = AsyncMock(
        return_value=[
            {"status": "echo reply", "time": "invalid_ms"},
            {"status": "echo reply", "time": "2.5ms"},
        ]
    )
    db.execute.side_effect = [_MockResult(single=sub_dev), _MockResult(single=r_obj)]
    with (
        patch("src.api.v1.subscribers.DiagnosticGovernor.check_user_rate_limit", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.invalidate_cached_ping", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.check_root_cause_router_health", AsyncMock(return_value=None)),
        patch("src.api.v1.subscribers._get_router_client", return_value=ping_cli),
        patch("src.api.v1.subscribers.DiagnosticGovernor.record_router_success", AsyncMock()),
        patch("src.api.v1.subscribers.DiagnosticGovernor.acquire_device_operational_lock", AsyncMock(return_value={})),
        patch("src.api.v1.subscribers.DiagnosticGovernor.set_cached_ping", AsyncMock()),
    ):
        ping_ext = await ping_subscriber_device_live(sub_dev.id, force=True, extended=True, db=db, claims=bad_claims)
    assert ping_ext.assigned_ipv4 == "100.64.7.7"
    assert ping_ext.gateway_ping is not None
    assert ping_ext.mtu_test is not None
    db.execute.side_effect = None

    # get_device_operational_status 404 (línea 2072)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_op404:
        await get_device_operational_status(uuid.uuid4(), db=db, claims=claims)
    assert exc_op404.value.status_code == 404


# ============================================================================
# 2. WI-FI CAPSMAN COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_wifi_capsman_fallbacks_errors_and_quick_setup() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "wifi_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r-wifi")

    # 1. _record_wifi_audit exception (líneas 109-110)
    with patch("src.api.v1.wifi.write_audit_log", AsyncMock(side_effect=RuntimeError("db down"))) as mock_err_audit:
        await _record_wifi_audit(db, claims, r_obj.id, "ACT", "POST", "/rest/wifi", {})
        mock_err_audit.assert_awaited_once()

    # 2. 404 Router no encontrado en endpoints de lectura/escritura (líneas 130, 296, 375, 1284, 1401)
    db.execute.return_value = _MockResult(single=None)
    for coro in (
        get_capsman_overview(uuid.uuid4(), db=db, claims=claims),
        list_capsman_ssids(uuid.uuid4(), db=db, claims=claims),
        create_capsman_ssid(
            uuid.uuid4(), WifiSsidProfile(id="1", name="n", ssid="s", security_type="wpa2-psk"), db=db, claims=claims
        ),
        list_wifi_clients(uuid.uuid4(), db=db, claims=claims),
        quick_setup_wifi(
            uuid.uuid4(),
            WifiQuickSetupRequest(corporate_ssid="Corp", corporate_passphrase="Password123!"),
            db=db,
            claims=claims,
        ),
    ):
        with pytest.raises(HTTPException) as exc404:
            await coro
        assert exc404.value.status_code == 404

    # Validación 422 en quick_setup_wifi (líneas 1388, 1393)
    with pytest.raises(HTTPException) as exc_qs1:
        await quick_setup_wifi(
            r_obj.id,
            WifiQuickSetupRequest(corporate_ssid="Corp", corporate_passphrase="short"),
            db=db,
            claims=claims,
        )
    assert exc_qs1.value.status_code == 422

    with pytest.raises(HTTPException) as exc_qs2:
        await quick_setup_wifi(
            r_obj.id,
            WifiQuickSetupRequest(
                corporate_ssid="Corp",
                corporate_passphrase="Password123!",
                guest_ssid_enabled=True,
                guest_ssid="Guest",
                guest_passphrase="short",
            ),
            db=db,
            claims=claims,
        )
    assert exc_qs2.value.status_code == 422

    # 3. get_capsman_overview, list_capsman_ssids, create_capsman_ssid con fallbacks legacy y excepciones (líneas 145-181, 305-352, 385-396)
    db.execute.return_value = _MockResult(single=r_obj)
    legacy_cli = AsyncMock()
    legacy_cli.__aenter__ = AsyncMock(return_value=legacy_cli)
    legacy_cli.__aexit__ = AsyncMock(return_value=None)

    async def _legacy_get(ep: str) -> Any:
        if ep.startswith("/interface/wifi"):
            raise RuntimeError("No wifiwave2")
        if ep == "/caps-man/manager":
            return {"enabled": "true"}
        if ep == "/caps-man/remote-cap":
            return [{"radios": 2}]
        if ep == "/caps-man/registration-table":
            return ["raw", {"mac-address": ""}, {"mac-address": "AA:BB:CC:11:22:33", "signal": "bad", "snr": "bad", "tx-rate": "bad", "rx-rate": "bad"}]
        if ep == "/caps-man/configuration":
            return ["raw", {"name": "c1", "ssid": "s1"}]
        if ep == "/caps-man/security":
            return ["raw", {"name": "sec1"}]
        if ep == "/caps-man/provisioning":
            return ["raw", {"name": "prov1"}]
        return []

    legacy_cli.get = AsyncMock(side_effect=_legacy_get)
    legacy_cli.put = AsyncMock(side_effect=RuntimeError("put failed"))
    with patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, legacy_cli))):
        ov = await get_capsman_overview(r_obj.id, db=db, claims=claims)
        assert ov.capsman_running is True
        assert ov.active_radios_count == 2
        assert ov.connected_clients_count == 3

        ssids = await list_capsman_ssids(r_obj.id, db=db, claims=claims)
        assert len(ssids) == 1

        await create_capsman_ssid(
            r_obj.id,
            WifiSsidProfile(id="1", name="c1", ssid="s1", security_type="wpa2-psk", vlan_id=20, client_isolation=True),
            db=db,
            claims=claims,
        )
        secs = await list_security_profiles(r_obj.id, db=db, claims=claims)
        assert len(secs) == 1
        provs = await list_provisioning_rules(r_obj.id, db=db, claims=claims)
        assert len(provs) == 1
        w_clients = await list_wifi_clients(r_obj.id, db=db, claims=claims)
        assert len(w_clients) == 1
        assert w_clients[0].signal_rssi_dbm == -70

    # Excepción total en ambos drivers y en get_router_and_client
    all_err_cli = AsyncMock()
    all_err_cli.__aenter__ = AsyncMock(return_value=all_err_cli)
    all_err_cli.__aexit__ = AsyncMock(return_value=None)
    all_err_cli.get = AsyncMock(side_effect=RuntimeError("all failed"))
    with patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, all_err_cli))):
        await get_capsman_overview(r_obj.id, db=db, claims=claims)
        await list_capsman_ssids(r_obj.id, db=db, claims=claims)
        await list_security_profiles(r_obj.id, db=db, claims=claims)
        await list_provisioning_rules(r_obj.id, db=db, claims=claims)
        await list_wifi_clients(r_obj.id, db=db, claims=claims)

    with patch("src.api.v1.wifi.get_router_and_client", AsyncMock(side_effect=RuntimeError("conn error"))):
        await get_capsman_overview(r_obj.id, db=db, claims=claims)
        await list_capsman_ssids(r_obj.id, db=db, claims=claims)
        await create_capsman_ssid(
            r_obj.id, WifiSsidProfile(id="1", name="n", ssid="s", security_type="wpa2-psk"), db=db, claims=claims
        )
        await list_security_profiles(r_obj.id, db=db, claims=claims)
        await list_provisioning_rules(r_obj.id, db=db, claims=claims)
        await list_wifi_clients(r_obj.id, db=db, claims=claims)

    # 4. Re-raise HTTPException en mutaciones y ramas de delete_capsman_configuration / reprovision / delete_wifi_client
    with patch("src.api.v1.wifi.get_router_and_client", AsyncMock(side_effect=HTTPException(status_code=409, detail="conflict"))):
        for coro_mut in (
            create_capsman_configuration(r_obj.id, WifiConfigurationCreate(name="c", ssid="s"), db=db, claims=claims),
            update_capsman_configuration(r_obj.id, "*1", WifiConfigurationUpdate(ssid="s"), db=db, claims=claims),
            create_security_profile(
                r_obj.id, WifiSecurityProfileCreate(name="s", passphrase="Password123!"), db=db, claims=claims
            ),
            delete_security_profile(r_obj.id, "*1", db=db, claims=claims),
            create_provisioning_rule(
                r_obj.id, WifiProvisioningRuleCreate(name="prov", master_configuration="cfg"), db=db, claims=claims
            ),
            delete_provisioning_rule(r_obj.id, "*1", db=db, claims=claims),
        ):
            with pytest.raises(HTTPException) as exc_re:
                await coro_mut
            assert exc_re.value.status_code == 409

    # reprovision_capsman_fleet: legacy remote-cap + excepciones (líneas 1173-1191)
    reprov_cli = AsyncMock()
    reprov_cli.__aenter__ = AsyncMock(return_value=reprov_cli)
    reprov_cli.__aexit__ = AsyncMock(return_value=None)
    reprov_cli.get = AsyncMock(side_effect=[RuntimeError("no modern"), [{".id": "*r1"}]])
    reprov_cli.post = AsyncMock(side_effect=RuntimeError("prov err"))
    with (
        patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, reprov_cli))),
        patch("src.api.v1.wifi.write_audit_log", make_asserting_audit_mock()),
    ):
        rep_res = await reprovision_capsman_fleet(r_obj.id, db=db, claims=claims)
    assert rep_res.provisioned_radios_count == 1

    # delete_wifi_client: fallback a /caps-man y /interface/wireless + excepción 502 (líneas 1250-1265)
    kick_cli = AsyncMock()
    kick_cli.__aenter__ = AsyncMock(return_value=kick_cli)
    kick_cli.__aexit__ = AsyncMock(return_value=None)
    kick_cli.delete = AsyncMock(side_effect=[RuntimeError("e1"), RuntimeError("e2"), RuntimeError("e3")])
    with patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, kick_cli))):
        await delete_wifi_client(r_obj.id, "*c1", db=db, claims=claims)

    # 5. quick_setup_wifi: moderno con errores internos + legado con guest SSID y errores internos (líneas 1439-1589)
    async def _run_coro(client: Any, menu: str, action: str, coro_fn: Any, **kw: Any) -> Any:
        return await coro_fn()

    qs_mod_cli = AsyncMock()
    qs_mod_cli.__aenter__ = AsyncMock(return_value=qs_mod_cli)
    qs_mod_cli.__aexit__ = AsyncMock(return_value=None)
    qs_mod_cli.get = AsyncMock(return_value={"enabled": "yes"})
    qs_mod_cli.post = AsyncMock(return_value={})
    qs_mod_cli.put = AsyncMock(side_effect=RuntimeError("put err"))
    with (
        patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, qs_mod_cli))),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.wifi.write_audit_log", make_asserting_audit_mock()),
    ):
        await quick_setup_wifi(
            r_obj.id,
            WifiQuickSetupRequest(
                corporate_ssid="Corp",
                corporate_passphrase="Password123!",
                guest_ssid_enabled=True,
                guest_ssid="Guest",
                guest_passphrase="GuestPass123!",
            ),
            db=db,
            claims=claims,
        )

    qs_leg_cli = AsyncMock()
    qs_leg_cli.__aenter__ = AsyncMock(return_value=qs_leg_cli)
    qs_leg_cli.__aexit__ = AsyncMock(return_value=None)
    qs_leg_cli.get = AsyncMock(side_effect=RuntimeError("no modern"))
    qs_leg_cli.post = AsyncMock(return_value={})
    qs_leg_cli.put = AsyncMock(return_value={".id": "*1"})
    with (
        patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, qs_leg_cli))),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.wifi.write_audit_log", make_asserting_audit_mock()),
    ):
        qs_leg_ok = await quick_setup_wifi(
            r_obj.id,
            WifiQuickSetupRequest(
                corporate_ssid="Corp",
                corporate_passphrase="Password123!",
                guest_ssid_enabled=True,
                guest_ssid="Guest",
                guest_passphrase="GuestPass123!",
            ),
            db=db,
            claims=claims,
        )
    assert qs_leg_ok.corporate_ssid == "Corp"

    qs_leg_cli.put = AsyncMock(side_effect=RuntimeError("legacy put err"))
    with (
        patch("src.api.v1.wifi.get_router_and_client", AsyncMock(return_value=(r_obj, qs_leg_cli))),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.wifi.write_audit_log", make_asserting_audit_mock()),
    ):
        await quick_setup_wifi(
            r_obj.id,
            WifiQuickSetupRequest(
                corporate_ssid="Corp",
                corporate_passphrase="Password123!",
                guest_ssid_enabled=True,
                guest_ssid="Guest",
                guest_passphrase="GuestPass123!",
            ),
            db=db,
            claims=claims,
        )


# ============================================================================
# 3. IPAM COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_ipam_endpoints_and_mikrotik_sync_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "ipam_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r-ipam")

    # 1. get_tenant_id 401, create_vrf 409, list_prefixes auto_sync (líneas 56, 89, 138-142)
    with pytest.raises(HTTPException) as exc401:
        ipam_get_tenant_id({})
    assert exc401.value.status_code == 401

    db.execute.return_value = _MockResult(single=IPAMVrf(id=uuid.uuid4(), tenant_id=tid, name="default"))
    with pytest.raises(HTTPException) as exc_vrf409:
        await create_vrf(IPAMVrfCreate(name="default"), db=db, claims=claims)
    assert exc_vrf409.value.status_code == 409

    db.execute.side_effect = [_MockResult(items=[]), _MockResult(items=[])]
    with patch("src.api.v1.ipam._sync_all_tenant_routers_ipam", AsyncMock(side_effect=RuntimeError("sync err"))):
        await list_prefixes(vrf_id=None, ip_family=None, role=None, auto_sync=True, db=db, claims=claims)
    db.execute.side_effect = None

    # 2. create_prefix: discordancia de familia 422 y duplicado 409 (líneas 180, 192)
    vrf_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_fam:
        await create_prefix(
            IPAMPrefixCreate(vrf_id=vrf_id, prefix="2001:db8::/32", ip_family=IPFamilyEnum.IPv4),
            db=db,
            claims=claims,
        )
    assert exc_fam.value.status_code == 422

    db.execute.return_value = _MockResult(single=IPAMPrefix(id=uuid.uuid4()))
    with pytest.raises(HTTPException) as exc_pfx409:
        await create_prefix(
            IPAMPrefixCreate(vrf_id=vrf_id, prefix="10.0.0.0/24", ip_family=IPFamilyEnum.IPv4),
            db=db,
            claims=claims,
        )
    assert exc_pfx409.value.status_code == 409

    # 3. get_next_available_resource: 404 prefijo, 404 IPv6 lleno, 404 IPv4 lleno (líneas 240, 261, 301)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_na1:
        await get_next_available_resource(uuid.uuid4(), db=db, claims=claims)
    assert exc_na1.value.status_code == 404

    pfx_v6 = IPAMPrefix(
        id=uuid.uuid4(),
        tenant_id=tid,
        vrf_id=vrf_id,
        prefix="2001:db8::/63",
        ip_family=IPFamilyEnum.IPv6,
        default_child_prefix_len=64,
    )
    db.execute.side_effect = [
        _MockResult(single=pfx_v6),
        _MockResult(items=["2001:db8::/64", "2001:db8:0:1::/64"]),
    ]
    with pytest.raises(HTTPException) as exc_na_v6:
        await get_next_available_resource(pfx_v6.id, db=db, claims=claims)
    assert exc_na_v6.value.status_code == 404

    pfx_v4 = IPAMPrefix(
        id=uuid.uuid4(),
        tenant_id=tid,
        vrf_id=vrf_id,
        prefix="10.0.0.0/30",
        ip_family=IPFamilyEnum.IPv4,
    )
    db.execute.side_effect = [
        _MockResult(single=pfx_v4),
        _MockResult(items=["10.0.0.1/32", "10.0.0.2/32"]),
    ]
    with pytest.raises(HTTPException) as exc_na_v4:
        await get_next_available_resource(pfx_v4.id, db=db, claims=claims)
    assert exc_na_v4.value.status_code == 404
    db.execute.side_effect = None

    # 4. list_addresses con status_filter y create_address (422, SOFT_LOCKED, 409; líneas 320, 341-364)
    db.execute.return_value = _MockResult(items=[])
    await list_addresses(prefix_id=pfx_v4.id, status_filter=IPAddressStatusEnum.ALLOCATED, db=db, claims=claims)

    with pytest.raises(HTTPException) as exc_a422:
        await create_address(
            IPAMAddressCreate(prefix_id=pfx_v4.id, address="bad-ip", ip_family=IPFamilyEnum.IPv4),
            db=db,
            claims=claims,
        )
    assert exc_a422.value.status_code == 422

    soft_addr = IPAMAddress(
        id=uuid.uuid4(),
        tenant_id=tid,
        prefix_id=pfx_v4.id,
        address="10.0.0.1/32",
        ip_family=IPFamilyEnum.IPv4,
        status=IPAddressStatusEnum.SOFT_LOCKED,
    )
    db.execute.return_value = _MockResult(single=soft_addr)
    confirmed = await create_address(
        IPAMAddressCreate(
            prefix_id=pfx_v4.id,
            address="10.0.0.1/32",
            ip_family=IPFamilyEnum.IPv4,
            status=IPAddressStatusEnum.ALLOCATED,
        ),
        db=db,
        claims=claims,
    )
    assert confirmed.status == IPAddressStatusEnum.ALLOCATED

    with pytest.raises(HTTPException) as exc_a409:
        await create_address(
            IPAMAddressCreate(prefix_id=pfx_v4.id, address="10.0.0.1/32", ip_family=IPFamilyEnum.IPv4),
            db=db,
            claims=claims,
        )
    assert exc_a409.value.status_code == 409

    # 5. list_customer_services y create_customer_service 409 (líneas 402, 404, 430)
    db.execute.return_value = _MockResult(items=[])
    await list_customer_services(router_id=r_obj.id, status_filter=CustomerServiceStatusEnum.ACTIVE, db=db, claims=claims)

    db.execute.return_value = _MockResult(single=CustomerService(id=uuid.uuid4()))
    with pytest.raises(HTTPException) as exc_cs409:
        await create_customer_service(
            CustomerServiceCreate(router_id=r_obj.id, endpoint_identifier="DUP-CS"),
            db=db,
            claims=claims,
        )
    assert exc_cs409.value.status_code == 409

    # 6. _get_router_client y _sync_single_router_ipam / _sync_all_tenant_routers_ipam (líneas 508-814)
    with patch("src.api.v1.ipam._create_client_from_vault", side_effect=RuntimeError("vault err")):
        assert ipam_get_router_client(r_obj, tid).username == "admin"

    # Primera pasada: todos los GET de _sync_single_router_ipam lanzan excepción (líneas 539-568)
    err_cli = AsyncMock()
    err_cli.__aenter__ = AsyncMock(return_value=err_cli)
    err_cli.__aexit__ = AsyncMock(return_value=None)
    err_cli.get = AsyncMock(side_effect=RuntimeError("ros err"))
    db.execute.return_value = _MockResult(items=[])
    def_vrf = IPAMVrf(id=vrf_id, tenant_id=tid, name="default")
    with patch("src.api.v1.ipam._get_router_client", return_value=err_cli):
        await _sync_single_router_ipam(r_obj, tid, db, def_vrf)

    # Segunda pasada: pools con distintos formatos, addresses e ítems existentes
    rich_cli = AsyncMock()
    rich_cli.__aenter__ = AsyncMock(return_value=rich_cli)
    rich_cli.__aexit__ = AsyncMock(return_value=None)

    async def _rich_get(ep: str) -> Any:
        if ep == "/ip/address":
            return [
                "not-a-dict",
                {"address": ""},
                {"address": "invalid-cidr"},
                {"address": "10.20.0.1/24", "interface": "ether2"},
                {"address": "10.30.0.1/24", "interface": "ether1"},
            ]
        if ep == "/ip/pool":
            return [
                "not-a-dict",
                {"name": "empty", "ranges": ""},
                {"name": "bad-ip", "ranges": "bad-ip-range"},
                {"name": "pool-addr-match", "ranges": "10.20.0.10-10.20.0.50", "total": "bad", "used": "bad"},
                {"name": "pool-fallback24", "ranges": "10.40.0.10-10.40.0.50", "total": 100, "used": 25},
                {"name": "pool-v6-unmatched", "ranges": "2001:db8:99::1-2001:db8:99::ff"},
            ]
        if ep == "/ip/dhcp-server":
            return [{"name": "dhcp1", "address-pool": "pool-fallback24", "interface": "ether3"}]
        if ep == "/ip/dhcp-server/network":
            return [{"address": "bad-net"}, {"address": "10.30.0.0/24"}]
        if ep == "/ip/dhcp-server/lease":
            return [
                "not-a-dict",
                {"address": ""},
                {"address": "bad-lease-ip"},
                {"address": "192.0.2.99"},
                {"address": "10.20.0.15", "mac-address": "AA:BB:CC:DD:EE:15", "host-name": "h1", "dynamic": "false"},
            ]
        return []

    rich_cli.get = AsyncMock(side_effect=_rich_get)
    existing_pfx = IPAMPrefix(id=uuid.uuid4(), tenant_id=tid, vrf_id=vrf_id, prefix="10.30.0.0/24", ip_family=IPFamilyEnum.IPv4)
    existing_addr = IPAMAddress(id=uuid.uuid4(), tenant_id=tid, prefix_id=existing_pfx.id, address="10.30.0.1", ip_family=IPFamilyEnum.IPv4)
    existing_lease = IPAMAddress(id=uuid.uuid4(), tenant_id=tid, prefix_id=existing_pfx.id, address="10.20.0.15", ip_family=IPFamilyEnum.IPv4)
    db.execute.side_effect = [
        _MockResult(items=[existing_pfx]),
        _MockResult(single=None),
        _MockResult(single=existing_addr),
        _MockResult(single=existing_lease),
    ]
    with patch("src.api.v1.ipam._get_router_client", return_value=rich_cli):
        p_cnt, i_cnt = await _sync_single_router_ipam(r_obj, tid, db, def_vrf)
    assert p_cnt >= 2
    assert i_cnt >= 1
    db.execute.side_effect = None

    # _sync_all_tenant_routers_ipam creando default_vrf (líneas 811-814)
    db.execute.side_effect = [_MockResult(single=None), _MockResult(items=[])]
    await _sync_all_tenant_routers_ipam(tid, db)
    db.execute.side_effect = None


# ============================================================================
# 4. INVENTORY, WEBFIG LAYER 2 & AUTH COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_inventory_missing_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "inv_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r-inv")

    # 1. _ensure_custom_network_roles con excepción DB y list_network_roles con sincronización automática (líneas 118-119, 159-170)
    db.execute.side_effect = RuntimeError("db err")
    created_roles = await _ensure_custom_network_roles(db, tid, {"CUSTOM_BNG"})
    assert len(created_roles) == 1
    db.execute.side_effect = None

    db.execute.side_effect = [
        _MockResult(items=[]),
        _MockResult(items=["TOWER_METRO_X"]),
        _MockResult(items=[]),
    ]
    roles_resp = await list_network_roles(claims=claims, db=db)
    assert "TOWER_METRO_X" in roles_resp.roles
    db.execute.side_effect = None

    # 2. list_routers con refresh=True y filtro admin_state + sync_router_syslog (líneas 375-401, 423-455)
    db.execute.side_effect = [_MockResult(items=[r_obj]), _MockResult(items=[])]
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=AsyncMock()),
        patch("src.api.v1.inventory_helpers.discover_and_persist_syslog_status", AsyncMock(return_value=True)),
        patch("src.api.v1.inventory.enrich_router_telemetry", AsyncMock(return_value={})),
    ):
        filtered_list = await list_routers(
            refresh=True,
            admin_state=RouterAdminStateEnum.MAINTENANCE,
            claims=claims,
            db=db,
        )
    assert filtered_list == []
    db.execute.side_effect = None

    db.execute.return_value = _MockResult(single=None)
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=AsyncMock()),
        pytest.raises(HTTPException) as exc_sys404,
    ):
        await sync_router_syslog(uuid.uuid4(), claims=claims, db=db)
    assert exc_sys404.value.status_code == 404

    db.execute.return_value = _MockResult(single=r_obj)
    mock_redis = AsyncMock()
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.inventory_helpers.discover_and_persist_syslog_status", AsyncMock(side_effect=RuntimeError("err"))),
        patch("src.api.v1.inventory.enrich_router_telemetry", AsyncMock(return_value={})),
    ):
        await sync_router_syslog(r_obj.id, claims=claims, db=db)
    mock_redis.set.assert_awaited()

    # 3. update_router cancelando MaintenanceWindow activa, delete_router 404, sync_discovery 404, repin_ssl (líneas 609-772)
    mw = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        starts_at=datetime.now(UTC) - timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=1),
        reason="Test",
        is_cancelled=False,
        created_by=uid,
    )
    db.execute.side_effect = [
        _MockResult(single=r_obj),
        _MockResult(items=[mw]),
        _MockResult(items=[]),
        _MockResult(items=[]),
    ]
    with (
        patch("src.api.v1.inventory.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.inventory.enrich_router_telemetry", AsyncMock(return_value={})),
    ):
        await update_router(
            r_obj.id,
            UpdateRouterRequest(
                admin_state=RouterAdminStateEnum.PRODUCTION,
                network_role="CUSTOM_ROLE_2",
                tags=["core"],
            ),
            claims=claims,
            db=db,
        )
    assert mw.is_cancelled is True
    db.execute.side_effect = None

    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_del404:
        await delete_router(uuid.uuid4(), claims=claims, db=db)
    assert exc_del404.value.status_code == 404

    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_disc404:
        await sync_discovery(uuid.uuid4(), claims=claims, db=db)
    assert exc_disc404.value.status_code == 404

    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "UnitTest"
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_rp400:
        await repin_ssl(
            r_obj.id,
            RePinSSLRequest(expected_new_sha256_fingerprint="a" * 64, totp_code="123456"),
            request=req,
            claims=claims,
            db=db,
        )
    assert exc_rp400.value.status_code == 400

    secret = pyotp.random_base32()
    aad_u = f"{tid}:{uid}".encode()
    ct_u, iv_u, tag_u = encrypt_aes_gcm(secret.encode("utf-8"), aad_u)
    admin_u = User(
        id=uid,
        tenant_id=tid,
        username="admin",
        email="a@b.c",
        full_name="Admin",
        password_hash="h",
        role=SystemRoleEnum.TENANT_ADMIN,
        totp_enabled=True,
        totp_secret_ciphertext=ct_u,
        totp_secret_iv=iv_u,
        totp_secret_tag=tag_u,
    )
    db.get.side_effect = [admin_u, None]
    with pytest.raises(HTTPException) as exc_rp404:
        await repin_ssl(
            r_obj.id,
            RePinSSLRequest(expected_new_sha256_fingerprint="a" * 64, totp_code=pyotp.TOTP(secret).now()),
            request=req,
            claims=claims,
            db=db,
        )
    assert exc_rp404.value.status_code == 404
    db.get.side_effect = None

    # 4. import_csv_dry_run (>2MB, bad UTF-8, >500 filas, custom roles; líneas 842-890)
    big_csv = UploadFile(filename="b.csv", file=io.BytesIO(b"x" * (2 * 1024 * 1024 + 5)))
    with pytest.raises(HTTPException):
        await import_csv_dry_run(file=big_csv, claims=claims, db=db)

    bad_csv = UploadFile(filename="u.csv", file=io.BytesIO(b"\xff\xfe\x00"))
    with pytest.raises(HTTPException):
        await import_csv_dry_run(file=bad_csv, claims=claims, db=db)


@pytest.mark.asyncio
async def test_webfig_layer2_missing_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "l2_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid, name="r-l2")
    client = AsyncMock()
    client.close = AsyncMock()
    req = MagicMock()
    req.client.host = "127.0.0.1"

    # 1. Helpers de esquema, caché, proplist, query, rsc y packages (líneas 425-584)
    assert len(_parse_console_inspect_syntax("mpls/ldp", [])) >= 1
    assert await _get_cached_l2_schema(None, "k") is None
    bad_redis = AsyncMock()
    bad_redis.get = AsyncMock(side_effect=RuntimeError("r err"))
    bad_redis.setex = AsyncMock(side_effect=RuntimeError("r err"))
    assert await _get_cached_l2_schema(bad_redis, "k") is None
    await _set_cached_l2_schema(None, "k", [])
    await _set_cached_l2_schema(bad_redis, "k", [ColumnSchemaItem(key=".id", label="ID", type="string", editable=False)])

    client.post = AsyncMock(side_effect=RuntimeError("inspect failed"))
    cols, src = await _resolve_schema_via_inspect(bad_redis, tid, "7.16", "mpls/interface", client)
    assert src == "fallback"
    assert _normalize_proplist(None) == []
    assert _build_ros_query_stack([]) == []
    filtered = _filter_items_locally(
        [{".id": "*1", "name": "a"}, {".id": "*2", "name": "b"}],
        [Layer2QueryFilterItem(field="name", operator="=", value="a"), Layer2QueryFilterItem(field="name", operator="!=", value="b")],
        [".id", "name"],
    )
    assert len(filtered) == 1
    assert _extract_rsc_section_for_path("   ", "mpls/ldp") == ""
    assert "mpls ldp" in _synthesize_rsc_from_items("mpls/ldp", ["not-dict", {"name": "inst1"}])
    assert _is_ros_package_active({"name": ""}) is False
    assert _is_ros_package_active({"name": "mpls", "version": ""}) is False

    # 2. get_resource re-raise HTTPException y query_resource_server_side fallback (líneas 769, 822-842)
    with (
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=bad_redis),
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", AsyncMock(side_effect=HTTPException(status_code=502, detail="timeout"))),
        pytest.raises(HTTPException) as exc502,
    ):
        await get_resource(r_obj.id, "mpls/interface", claims=claims, db=db)
    assert exc502.value.status_code == 502

    client.post = AsyncMock(side_effect=RuntimeError("print unsupported"))
    with (
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=bad_redis),
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", AsyncMock(return_value=[])),
    ):
        q_res = await query_resource_server_side(
            r_obj.id,
            "mpls/interface",
            DynamicLayer2QueryRequest(filters=[Layer2QueryFilterItem(field="disabled", operator="=", value="false")]),
            claims=claims,
            db=db,
        )
    assert q_res.items == []

    # 3. update_resource singleton (`system/identity`) y update_singleton_resource + execute_bulk_operation (líneas 937-1069, 1214)
    async def _run_coro(client_arg: Any, menu: str, action: str, coro_fn: Any, **kw: Any) -> Any:
        return await coro_fn()

    client.get = AsyncMock(return_value={"name": "OldIdent"})
    client.post = AsyncMock(side_effect=RuntimeError("set failed"))
    client.patch = AsyncMock(return_value={"name": "NewIdent"})
    with (
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=bad_redis),
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.webfig_layer2.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.webfig_layer2.invalidate_webfig_cache", AsyncMock()),
        patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()),
    ):
        await update_resource(
            r_obj.id,
            "system",
            "identity",
            DynamicLayer2WriteRequest(attributes={"name": "NewIdent"}, enable_safemode=True),
            request=req,
            claims=claims,
            db=db,
        )
        assert r_obj.display_name == "NewIdent"
        await update_resource(
            r_obj.id,
            "mpls/interface",
            "*1",
            DynamicLayer2WriteRequest(attributes={"mpls-mtu": "1500"}, enable_safemode=False),
            request=req,
            claims=claims,
            db=db,
        )
        await update_singleton_resource(
            r_obj.id,
            "system/identity",
            DynamicLayer2WriteRequest(attributes={"name": "Ident2"}, enable_safemode=True),
            request=req,
            claims=claims,
            db=db,
        )
        await update_singleton_resource(
            r_obj.id,
            "system/identity",
            DynamicLayer2WriteRequest(attributes={"name": "Ident3"}, enable_safemode=False),
            request=req,
            claims=claims,
            db=db,
        )
        await execute_bulk_operation(
            r_obj.id,
            "mpls/interface",
            DynamicLayer2BulkRequest(action="enable", item_ids=["*1"], enable_safemode=False),
            request=req,
            claims=claims,
            db=db,
        )

    # 4. _fetch_live_submenu_rsc, _fetch_latest_backup_section, _resolve_rpc_target_and_args y execute_command (líneas 1255-1399)
    client.post = AsyncMock(return_value={"ret": "/mpls interface\nadd mpls-mtu=1500"})
    assert "mpls interface" in await _fetch_live_submenu_rsc(client, "mpls/interface", "compact")
    client.post = AsyncMock(side_effect=RuntimeError("export unsupported"))
    client.get = AsyncMock(return_value=[{"mpls-mtu": "1500"}])
    assert "add mpls-mtu=1500" in await _fetch_live_submenu_rsc(client, "mpls/interface", "terse")

    aad_bk = f"{tid}:{r_obj.id}".encode()
    ct_bk, iv_bk, tag_bk = encrypt_aes_gcm(b"/mpls interface\nadd mpls-mtu=1508\n", aad_bk)
    bk_ok = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        rsc_ciphertext=ct_bk,
        rsc_iv=iv_bk,
        rsc_tag=tag_bk,
        rsc_sha256_hash="h",
        rsc_size_bytes=32,
        created_at=datetime.now(UTC),
    )
    db.execute.return_value = _MockResult(single=bk_ok)
    sec_str, ts_str = await _fetch_latest_backup_section(db, tid, r_obj.id, "mpls/interface")
    assert "mpls-mtu=1508" in sec_str
    assert ts_str is not None

    bk_bad = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        rsc_ciphertext=b"corrupt",
        rsc_iv=b"iv",
        rsc_tag=b"tag",
        rsc_sha256_hash="h",
        rsc_size_bytes=10,
    )
    db.execute.return_value = _MockResult(single=bk_bad)
    sec_fb, _ = await _fetch_latest_backup_section(db, tid, r_obj.id, "mpls/interface")
    assert "/mpls interface" in sec_fb

    ep_empty, _, desc_none = _resolve_rpc_target_and_args(
        "mpls/interface", DynamicLayer2CommandRequest(action="", arguments={})
    )
    assert ep_empty == "mpls/interface"
    assert desc_none is None

    mc_desc = Layer2RpcActionDescriptor(
        action="sign",
        label="Sign",
        description="Sign cert",
        ros_endpoint="certificate/sign",
        id_param_key="numbers",
        requires_safemode=True,
        requires_maker_checker=True,
    )
    with (
        patch("src.api.v1.webfig_layer2._resolve_rpc_target_and_args", return_value=("certificate/sign", {}, mc_desc)),
        patch("src.api.v1.webfig_layer2.intercept_maker_checker_if_needed", AsyncMock(return_value={"status": "AWAITING_APPROVAL"})),
    ):
        mc_res = await execute_command(
            r_obj.id,
            "certificate",
            DynamicLayer2CommandRequest(action="sign", item_id="*1", arguments={}),
            request=req,
            claims=claims,
            db=db,
        )
    assert mc_res["status"] == "AWAITING_APPROVAL"


@pytest.mark.asyncio
async def test_auth_governor_and_syslog_collector_missing_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    db = _make_mock_db()
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "UnitTest"
    req.url.scheme = "https"
    resp = MagicMock()

    # 1. Auth: usuario inactivo en _verify_user_credentials (líneas 246-257)
    inactive_u = User(
        id=uid,
        tenant_id=tid,
        username="u_inact",
        email="u@a.c",
        full_name="Inactive",
        password_hash="h",
        role=SystemRoleEnum.NOC_MONITOR,
        is_active=False,
        has_all_routers_access=False,
        failed_login_attempts=0,
    )
    with (
        patch("src.api.v1.auth.verify_password", return_value=True),
        patch("src.api.v1.auth._log_login_event", AsyncMock()),
        pytest.raises(HTTPException) as exc403,
    ):
        await _verify_user_credentials(db, inactive_u, "Pass123!", request=req)
    assert exc403.value.status_code == 403

    # 2. _fetch_preauth_state, _execute_2fa_verification, _build_auth_session_response y verify_2fa (líneas 346-575)
    mock_redis = AsyncMock()
    with pytest.raises(HTTPException):
        await _fetch_preauth_state(mock_redis, "bad id!")

    mock_redis.get = AsyncMock(return_value=b"tid-bytes")
    mock_redis.hgetall = AsyncMock(return_value={})
    with pytest.raises(HTTPException):
        await _fetch_preauth_state(mock_redis, "abcd1234abcd1234")

    with pytest.raises(HTTPException) as exc_2fa_corrupt:
        await _execute_2fa_verification(db, inactive_u, "123456", b"aad")
    assert exc_2fa_corrupt.value.status_code == 401

    with (
        patch("src.api.v1.auth.kill_all_user_sessions", AsyncMock(return_value=2)),
        patch("src.api.v1.auth._log_login_event", AsyncMock()) as mock_log_ev,
        patch("src.api.v1.auth.create_session", AsyncMock(return_value=("sid1", "fam1", "rt1"))),
    ):
        await _build_auth_session_response(req, resp, tid, "acme", "Acme", inactive_u, db=db)
    assert mock_log_ev.await_count >= 2

    # verify_2fa: usuario no encontrado (401) y usuario bloqueado (423)
    with (
        patch("src.api.v1.auth.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.auth._fetch_preauth_state", AsyncMock(return_value=("k", {"user_id": str(uid), "tenant_id": str(tid)}))),
    ):
        db.execute.return_value = _MockResult(single=None)
        with pytest.raises(HTTPException) as exc_u401:
            await verify_2fa(Verify2FARequest(challenge_id="abcd1234", totp_code="123456"), req, resp, db=db)
        assert exc_u401.value.status_code == 401

        locked_u = User(
            id=uid,
            tenant_id=tid,
            username="locked",
            email="l@a.c",
            full_name="L",
            password_hash="h",
            role=SystemRoleEnum.TENANT_ADMIN,
            is_locked=True,
            locked_until=datetime.now(UTC) + timedelta(minutes=10),
        )
        db.execute.return_value = _MockResult(single=locked_u)
        with pytest.raises(HTTPException) as exc_u423:
            await verify_2fa(Verify2FARequest(challenge_id="abcd1234", totp_code="123456"), req, resp, db=db)
        assert exc_u423.value.status_code == 423

    # 3. refresh_access_token con usuario inactivo en DB y logout con rol inválido (líneas 664-673, 714-715)
    mock_redis.hgetall = AsyncMock(return_value={"role": "TENANT_ADMIN", "refresh_family_id": "fam1"})
    db.get.return_value = inactive_u
    with (
        patch("src.api.v1.auth._extract_refresh_cookies", return_value=("rt1", "at1")),
        patch(
            "src.api.v1.auth._decode_refresh_claims",
            return_value={"tid": str(tid), "sid": "sid1", "sub": str(uid), "rol": "TENANT_ADMIN", "tslug": "acme"},
        ),
        patch("src.api.v1.auth.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.auth.kill_session", AsyncMock()),
        pytest.raises(HTTPException) as exc_ref401,
    ):
        await refresh_access_token(req, resp, db=db)
    assert exc_ref401.value.status_code == 401
    db.get.return_value = None

    with (
        patch("src.api.v1.auth.kill_session", AsyncMock()),
        patch("src.api.v1.auth._log_login_event", AsyncMock()),
    ):
        await logout(req, resp, claims={"tid": str(tid), "sid": "sid1", "sub": str(uid), "rol": "INVALID_ROLE"}, db=db)

    # 4. session_closing, switch_tenant, get_bootstrap_status y register_user (líneas 754-1065)
    req_sc = MagicMock()
    req_sc.body = AsyncMock(return_value=b'{"session_id": "abcd1234abcd1234"}')
    mock_redis.keys = AsyncMock(return_value=[b"rg:" + str(tid).encode() + b":sess:abcd1234abcd1234"])
    with (
        patch("src.api.v1.auth.extract_token_from_request", return_value=None),
        patch("src.api.v1.auth.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.auth.mark_session_closing", AsyncMock(return_value=True)),
    ):
        sc_res = await session_closing(req_sc, payload=None)
    assert sc_res.status == "GRACE_PERIOD_ACTIVE"

    # switch_tenant: 404, 400 inactivo y 401 usuario no encontrado
    sa_claims = {"tid": str(tid), "sid": "sid1", "sub": str(uid), "rol": SystemRoleEnum.SUPERADMIN_GLOBAL.value}
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as exc_st404:
        await switch_tenant(SwitchTenantRequest(target_tenant_id=uuid.uuid4()), req, resp, claims=sa_claims, db=db)
    assert exc_st404.value.status_code == 404

    db.scalar.return_value = Tenant(id=tid, slug="susp", name="Susp", status=TenantStatusEnum.SUSPENDED)
    with pytest.raises(HTTPException) as exc_st400:
        await switch_tenant(SwitchTenantRequest(target_tenant_slug="susp"), req, resp, claims=sa_claims, db=db)
    assert exc_st400.value.status_code == 400

    db.scalar.side_effect = [Tenant(id=tid, slug="act", name="Act", status=TenantStatusEnum.ACTIVE), None]
    with pytest.raises(HTTPException) as exc_st401:
        await switch_tenant(SwitchTenantRequest(target_tenant_slug="act"), req, resp, claims=sa_claims, db=db)
    assert exc_st401.value.status_code == 401
    db.scalar.side_effect = None

    # get_bootstrap_status y register_user
    mock_redis.get = AsyncMock(return_value=b"false")
    db.scalar.side_effect = [1, 1]
    db.execute.return_value = _MockResult(single=Tenant(id=tid, slug="acme", name="Acme"))
    with patch("src.api.v1.auth.get_redis_client", return_value=mock_redis):
        bs = await get_bootstrap_status(db=db)
    assert bs.registration_enabled is False
    assert bs.default_tenant_slug == "acme"
    db.scalar.side_effect = None

    # register_user: búsqueda por nombre, fallback single tenant, 409 conflicto
    mock_redis.get = AsyncMock(return_value=b"true")
    db.scalar.side_effect = [1, 1]
    db.execute.side_effect = [
        _MockResult(single=None),
        _MockResult(single=None),
        _MockResult(single=Tenant(id=tid, slug="acme", name="Acme")),
        _MockResult(single=inactive_u),
    ]
    with (
        patch("src.api.v1.auth.get_redis_client", return_value=mock_redis),
        pytest.raises(HTTPException) as exc_reg409,
    ):
        await register_user(
            RegisterUserRequest(
                tenant_slug="unknown",
                username="u_inact",
                email="u@a.c",
                full_name="User Test",
                password="Password123!",
            ),
            db=db,
        )
    assert exc_reg409.value.status_code == 409
    db.scalar.side_effect = None
    db.execute.side_effect = None

    # 5. DiagnosticGovernor: excepciones de Redis y casos borde (líneas 55-319)
    err_redis = AsyncMock()
    err_redis.get = AsyncMock(return_value='["not-a-dict"]')
    with patch("src.services.diagnostic_governor.get_redis_client", return_value=err_redis):
        assert await DiagnosticGovernor.get_cached_ping(tid, uid) is None

    err_redis.get = AsyncMock(side_effect=RuntimeError("redis down"))
    err_redis.set = AsyncMock(side_effect=RuntimeError("redis down"))
    err_redis.delete = AsyncMock(side_effect=RuntimeError("redis down"))
    err_redis.incr = AsyncMock(side_effect=RuntimeError("redis down"))
    err_redis.decr = AsyncMock(side_effect=RuntimeError("redis down"))
    with patch("src.services.diagnostic_governor.get_redis_client", return_value=err_redis):
        assert await DiagnosticGovernor.get_cached_ping(tid, uid) is None
        await DiagnosticGovernor.set_cached_ping(tid, uid, {"device_id": uid})
        await DiagnosticGovernor.invalidate_cached_ping(tid, uid)
        await DiagnosticGovernor.check_user_rate_limit(tid, uid)
        async with DiagnosticGovernor.acquire_router_slot(tid, uid):
            pass
        await DiagnosticGovernor.record_router_failure(tid, uid)
        await DiagnosticGovernor.record_router_success(tid, uid)
        assert await DiagnosticGovernor.check_root_cause_router_health(tid, uid) is None
        assert await DiagnosticGovernor.acquire_device_operational_lock(tid, uid, "t1", "Tech") == {}
        assert await DiagnosticGovernor.get_device_operational_lock(tid, uid) == {"is_locked": False}

    # Cuota por minuto en router (>30) y locked_at inválido
    quota_redis = AsyncMock()
    quota_redis.get = AsyncMock(return_value=None)
    quota_redis.incr = AsyncMock(return_value=31)
    with (
        patch("src.services.diagnostic_governor.get_redis_client", return_value=quota_redis),
        pytest.raises(HTTPException) as exc_r429,
    ):
        async with DiagnosticGovernor.acquire_router_slot(tid, uid):
            pass
    assert exc_r429.value.status_code == 429

    bad_lock_redis = AsyncMock()
    bad_lock_redis.get = AsyncMock(return_value=json.dumps({"technician_id": "t1", "locked_at": "invalid-iso"}))
    with patch("src.services.diagnostic_governor.get_redis_client", return_value=bad_lock_redis):
        lk = await DiagnosticGovernor.get_device_operational_lock(tid, uid, "t2")
        assert lk["is_locked_by_other"] is True

    # 6. SyslogCollector: tópicos inferidos, datagram_received por hostname, load_router_syslog_maps y worker loop
    assert parse_syslog_message("<13>Nov  9 12:00:00 r1 user admin logged in").topics == "system,info,account"
    assert parse_syslog_message("<13>Nov  9 12:00:00 r1 ether1 link down").topics == "interface,warning"
    assert parse_syslog_message("<13>Nov  9 12:00:00 r1 bgp peer down").topics == "route,bgp"
    assert parse_syslog_message("<13>Nov  9 12:00:00 r1 ospf neighbor down").topics == "route,ospf"
    assert parse_syslog_message("<13>Nov  9 12:00:00 r1 dhcp lease offered").topics == "dhcp"

    proto = SyslogUdpProtocol({}, {"r-core": (tid, uid)})
    with patch("src.workers.syslog_collector.push_event_to_ringbuffer", AsyncMock()):
        proto.datagram_received(b"<13>Nov  9 12:00:00 r-core system,info test message", ("172.18.0.1", 5514))

    mock_sess_ctx = AsyncMock()
    mock_sess_ctx.__aenter__ = AsyncMock(return_value=db)
    mock_sess_ctx.__aexit__ = AsyncMock(return_value=None)
    db.execute.return_value = _MockResult(items=[(uid, tid, "https://192.0.2.55:443"), (uid,)])
    with patch("src.db.session.async_session_maker", return_value=mock_sess_ctx):
        ip_m = await load_ip_router_map()
        assert "192.0.2.55" in ip_m

    # Worker loop: error al enlazar socket y ciclo de refresco + CancelledError
    fake_loop = MagicMock()
    fake_loop.create_datagram_endpoint = AsyncMock(side_effect=OSError("bind failed"))
    with (
        patch("src.workers.syslog_collector.load_router_syslog_maps", AsyncMock(return_value=({}, {}))),
        patch("asyncio.get_running_loop", return_value=fake_loop),
    ):
        await syslog_collector_worker_loop()

    fake_transport = MagicMock()
    fake_transport.is_closing.return_value = False
    fake_proto = SyslogUdpProtocol({}, {})
    fake_loop.create_datagram_endpoint = AsyncMock(return_value=(fake_transport, fake_proto))
    with (
        patch("src.workers.syslog_collector.load_router_syslog_maps", AsyncMock(return_value=({"1.1.1.1": (tid, uid)}, {"r1": (tid, uid)}))),
        patch("asyncio.get_running_loop", return_value=fake_loop),
        patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()])),
    ):
        await syslog_collector_worker_loop()
    fake_transport.close.assert_called_once()
