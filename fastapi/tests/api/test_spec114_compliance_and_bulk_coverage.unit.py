# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias de cobertura profunda para Compliance (CIS 28 directivas), Bulk & Updates, Backups y Approvals."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.approvals import (
    _execute_approval_lifecycle,
    _execute_deferred_operation,
    _execute_mcp_deferred_tool,
    approve_request,
    list_approvals,
    reject_request,
)
from src.api.v1.backups import (
    _build_side_by_side_hunks,
    _cleanup_stale_rosgrid_bk_files,
    _execute_router_backup_core,
    _export_via_fresh_ephemeral_session,
    _extract_raw_rsc_text,
    _list_router_files_metadata_safe,
    _read_large_rsc_file,
    _resolve_user_group_ftp_status,
    _try_fallback_rsc_export,
    _try_self_heal_group_ftp_policy,
    get_backup_diff,
    trigger_batch_backups,
)
from src.api.v1.bulk_and_updates import (
    _cleanup_corrupted_npk_downloads,
    _execute_single_router_upgrade,
    _execute_single_step,
    _extract_update_status_text,
    _fetch_latest_version_via_http_fallback,
    _install_routeros_via_fetch_fallback,
    _perform_pre_upgrade_backup,
    _probe_routerboard_safe,
    _probe_single_router_update,
    _resolve_package_update_versions,
    _resolve_upgrade_stages,
    _run_router_template_steps,
    _trigger_router_package_install,
    check_fleet_updates_by_channel,
    create_bulk_job,
    create_template,
    delete_template,
    execute_bulk_job_on_fleet,
    get_fleet_updates_status,
    get_template,
    update_template,
)
from src.api.v1.compliance import (
    _build_default_cis_rules,
    _normalize_rsc_content,
    auto_harden_router,
    check_config_drift,
    list_golden_templates,
    revert_config_drift,
    run_cis_audit,
)
from src.core.crypto import encrypt_aes_gcm
from src.mikrotik.client import (
    MikrotikApiError,
    MikrotikConnectionError,
    MikrotikTimeoutError,
)
from src.models.core import SystemRoleEnum, User
from src.models.inventory import (
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
)
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    BulkJob,
    BulkJobStatusEnum,
    ConfigTemplate,
    CriticalActionTypeEnum,
    GoldenConfigTemplate,
    RouterBackup,
)
from src.schemas.approvals import ApproveRequestPayload, RejectRequestPayload
from src.schemas.backups import BatchBackupTriggerRequest
from src.schemas.bulk_and_updates import (
    BulkJobCreateRequest,
    ConfigTemplateCreateRequest,
    ConfigTemplateUpdateRequest,
    RosUpdateChannelCheckRequest,
    RosUpdateExecuteRequest,
)
from src.schemas.enterprise import (
    CisAutoHardenRequest,
    CisPoliciesConfigResponse,
    CisPolicyRule,
    ConfigDriftRevertRequest,
)
from tests.conftest import make_asserting_audit_mock


class _MockScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class _MockResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None):
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)

    def scalars(self) -> _MockScalars:
        return _MockScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single

    def scalar_one(self) -> Any:
        return self._single

    def scalar(self) -> Any:
        return self._single


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.get = AsyncMock()

    def _add(obj: Any) -> None:
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)
        if hasattr(obj, "updated_at") and getattr(obj, "updated_at", None) is None:
            obj.updated_at = datetime.now(UTC)

    db.add = MagicMock(side_effect=_add)
    return db


def _make_router(tenant_id: uuid.UUID, board_name: str = "RB5009UG+S+") -> Router:
    r_id = uuid.uuid4()
    r = Router(
        id=r_id,
        tenant_id=tenant_id,
        display_name="Core-GW-01",
        ros_identity="Core-GW-01-ID",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
        network_role=RouterNetworkRoleEnum.CORE,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="DC1",
        serial_number="SN-CIS-001",
        board_name=board_name,
        model_name=board_name,
        ros_version="7.16",
        update_available_version="7.16.2",
        firmware_version="7.15",
        upgrade_firmware_version="7.16",
        created_by=uuid.uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    aad = f"{tenant_id}:{r_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"secret", aad)
    r.vault = RouterCredentialsVault(
        router_id=r_id,
        tenant_id=tenant_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
    )
    return r


# ============================================================================
# 1. COMPLIANCE & CIS 28 DIRECTIVES COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_compliance_templates_and_config_drift_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "sec_admin", "rol": "TENANT_ADMIN"}

    # _normalize_rsc_content con líneas vacías y cabeceras dinámicas
    raw_rsc = "\n# jan/02/2026 by RouterOS 7.16\n# model = RB5009\n/ip service set telnet disabled=yes\n"
    assert _normalize_rsc_content(raw_rsc) == ["/ip service set telnet disabled=yes"]

    # list_golden_templates cuando existen plantillas en BD (línea 181)
    db = _make_mock_db()
    tpl = GoldenConfigTemplate(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Corp-Core-Custom",
        network_role="CORE",
        baseline_rsc_content="/ip service set telnet disabled=yes",
        enforce_strict_firewall=True,
        enforce_ntp_dns=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.execute.return_value = _MockResult(items=[tpl])
    res_list = await list_golden_templates(db=db, claims=claims)
    assert len(res_list) == 1
    assert res_list[0].name == "Corp-Core-Custom"

    # check_config_drift: 404 Router no encontrado (línea 265)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc404:
        await check_config_drift(uuid.uuid4(), db=db, claims=claims)
    assert exc404.value.status_code == 404

    # check_config_drift: export_res es str (línea 295-296)
    r_obj = _make_router(tid)
    db.execute.side_effect = [_MockResult(single=r_obj), _MockResult(single=tpl)]
    fake_client = AsyncMock()
    fake_client.request = AsyncMock(return_value="/ip service set telnet disabled=yes")
    fake_client.close = AsyncMock()
    with patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, fake_client))):
        drift_ok = await check_config_drift(r_obj.id, db=db, claims=claims)
    assert drift_ok.drift_detected is False
    fake_client.close.assert_awaited_once()

    # check_config_drift: excepción al exportar activa simulación de drift (líneas 297-305)
    db.execute.side_effect = [_MockResult(single=r_obj), _MockResult(single=None)]
    fake_client_err = AsyncMock()
    fake_client_err.request = AsyncMock(side_effect=RuntimeError("Router unreachable"))
    fake_client_err.close = AsyncMock()
    with patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, fake_client_err))):
        drift_sim = await check_config_drift(r_obj.id, db=db, claims=claims)
    assert drift_sim.drift_detected is True
    assert drift_sim.total_drift_lines > 0

    # revert_config_drift: 404 Router no encontrado (línea 367)
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "UnitTest"
    db.execute.side_effect = None
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc_rev_404:
        await revert_config_drift(
            ConfigDriftRevertRequest(router_id=uuid.uuid4()),
            request=req,
            db=db,
            claims=claims,
        )
    assert exc_rev_404.value.status_code == 404

    # revert_config_drift: con template_id y ejecución real de _apply_revert (líneas 374-395)
    tpl_with_api = GoldenConfigTemplate(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="WithTelnetApi",
        network_role="CORE",
        baseline_rsc_content="/ip service set telnet disabled=yes\n/ip service set api disabled=yes",
        enforce_strict_firewall=True,
        enforce_ntp_dns=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.execute.side_effect = [_MockResult(single=r_obj), _MockResult(single=tpl_with_api)]
    revert_client = AsyncMock()
    revert_client.patch = AsyncMock()
    revert_client.close = AsyncMock()

    async def _run_coro(client: Any, menu: str, action: str, coro_fn: Any, **kw: Any) -> Any:
        return await coro_fn()

    with (
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, revert_client))),
        patch("src.api.v1.compliance.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.compliance.write_audit_log", make_asserting_audit_mock()) as mock_audit,
    ):
        rev_res = await revert_config_drift(
            ConfigDriftRevertRequest(router_id=r_obj.id, template_id=tpl_with_api.id),
            request=req,
            db=db,
            claims=claims,
        )
    assert rev_res.status == "REVERTED_SUCCESSFULLY"
    assert revert_client.patch.await_count == 2
    mock_audit.assert_awaited_once()

    # revert_config_drift: excepción en Safe Mode (líneas 402-403)
    db.execute.side_effect = [_MockResult(single=r_obj)]
    with (
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(side_effect=RuntimeError("Offline"))),
        patch("src.api.v1.compliance.write_audit_log", make_asserting_audit_mock()),
    ):
        rev_err_res = await revert_config_drift(
            ConfigDriftRevertRequest(router_id=r_obj.id),
            request=req,
            db=db,
            claims=claims,
        )
    assert rev_err_res.executed_safemode is True


@pytest.mark.asyncio
async def test_run_cis_audit_all_28_directives_pass_fail_and_exceptions() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "cis_auditor", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid)

    # 1. 404 Router no encontrado (línea 989)
    db.execute.return_value = _MockResult(single=None)
    with pytest.raises(HTTPException) as exc404:
        await run_cis_audit(uuid.uuid4(), db=db, claims=claims)
    assert exc404.value.status_code == 404

    # Construir política con las 28 reglas activas + 1 desactivada + 1 personalizada
    all_rules = _build_default_cis_rules("DATACENTER")
    custom_rule = CisPolicyRule(
        code="CIS-CUSTOM-99",
        title="Directiva Personalizada",
        category="CUSTOM",
        weight=5,
        severity="LOW",
        enabled=True,
        remediation_cmd="/system identity print",
        profile_target="ALL",
    )
    disabled_rule = CisPolicyRule(
        code="CIS-DISABLED-00",
        title="Directiva Desactivada",
        category="CUSTOM",
        weight=5,
        severity="LOW",
        enabled=False,
        remediation_cmd="/system identity print",
        profile_target="ALL",
    )
    policy_resp = CisPoliciesConfigResponse(
        tenant_id=tid,
        profile="DATACENTER",
        updated_at=datetime.now(UTC).isoformat(),
        rules=[*all_rules, custom_rule, disabled_rule],
    )

    # 2. Caso ALL PASS (las 28 directivas pasan por sondeo en vivo)
    async def _get_all_passing(endpoint: str) -> Any:
        mapping: dict[str, Any] = {
            "/ip/service": [
                {"name": "telnet", "disabled": "true"},
                {"name": "ftp", "disabled": "true"},
                {"name": "www", "disabled": "true"},
                {"name": "api", "disabled": "true"},
                {"name": "winbox", "disabled": "false", "address": "10.0.0.0/8", "vrf": "mgmt-vrf"},
            ],
            "/user": [{"name": "admin", "disabled": "true"}, {"name": "secadmin", "disabled": "false", "group": "full"}],
            "/ip/dns": {"allow-remote-requests": "no"},
            "/ip/neighbor/discovery-settings": {"discover-interface-list": "lan"},
            "/ip/firewall/filter": [
                {"comment": "CIS-1.8 bruteforce", "src-address-list": "ssh_blacklist", "action": "drop", "chain": "input"},
                {"comment": "CIS-1.7 bogon", "src-address-list": "bogons", "action": "drop", "chain": "input"},
                {"action": "fasttrack-connection", "packet-mark": "!qos-shaped", "comment": "CIS-2.2"},
                {"chain": "input", "dst-port": "53", "action": "drop", "comment": "CIS-ISP-2"},
                {"chain": "input", "limit": "100,50:packet", "action": "accept", "comment": "CoPP"},
            ],
            "/ip/firewall/raw": [{"comment": "CIS-ISP-1 bogon", "src-address-list": "bogons"}],
            "/interface/vlan": [{"name": "vlan99-mgmt", "comment": "cis-1.10"}],
            "/routing/bgp/connection": [{"tcp-md5-key": "yes"}],
            "/tool/bandwidth-server": {"enabled": "no"},
            "/tool/mac-server": {"allowed-interface-list": "none"},
            "/ip/ssh": {"strong-crypto": "yes"},
            "/interface/bridge": [{"dhcp-snooping": "yes"}],
            "/snmp": {"trap-version": "3"},
            "/system/logging": [{"action": "rosgridsyslog", "topics": "account,info"}],
            "/tool/romon": {"enabled": "no"},
            "/system/scheduler": [{"name": "nightly-backup", "on-event": "encryption=aes-sha256"}],
            "/ip/settings": {"send-redirects": "no"},
            "/ip/proxy": {"enabled": "no"},
            "/ip/socks": {"enabled": "no"},
            "/routing/ospf/interface-template": [{"auth": "sha256"}],
            "/ip/ipsec/profile": [{"enc-algorithm": "aes-256", "hash-algorithm": "sha256"}],
            "/system/routerboard": {"current-firmware": "7.16", "upgrade-firmware": "7.16"},
        }
        return mapping.get(endpoint, [])

    pass_client = AsyncMock()
    pass_client.get = AsyncMock(side_effect=_get_all_passing)
    pass_client.close = AsyncMock()
    db.execute.return_value = _MockResult(single=r_obj)

    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=policy_resp)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, pass_client))),
    ):
        audit_pass = await run_cis_audit(r_obj.id, db=db, claims=claims)
    assert audit_pass.passed_directives == 28
    assert audit_pass.security_score >= 95

    # 3. Caso ALL FAIL (las 28 directivas fallan por configuración insegura en vivo)
    async def _get_all_failing(endpoint: str) -> Any:
        mapping: dict[str, Any] = {
            "/ip/service": [
                {"name": "telnet", "disabled": "false"},
                {"name": "winbox", "disabled": "false", "address": "0.0.0.0/0", "vrf": "main"},
            ],
            "/user": [{"name": "admin", "disabled": "false"}],
            "/ip/dns": {"allow-remote-requests": "yes"},
            "/ip/neighbor/discovery-settings": {"discover-interface-list": "all"},
            "/ip/firewall/filter": [{"comment": "allow all", "action": "accept", "chain": "forward"}],
            "/ip/firewall/raw": [],
            "/interface/vlan": [{"name": "vlan10-users"}],
            "/routing/bgp/connection": [{"tcp-md5-key": "no"}],
            "/tool/bandwidth-server": {"enabled": "yes"},
            "/tool/mac-server": {"allowed-interface-list": "all"},
            "/ip/ssh": {"strong-crypto": "no"},
            "/interface/bridge": [{"dhcp-snooping": "no"}],
            "/snmp": {"trap-version": "2"},
            "/system/logging": [{"action": "memory", "topics": "info"}],
            "/tool/romon": {"enabled": "yes"},
            "/system/scheduler": [],
            "/ip/settings": {"send-redirects": "yes"},
            "/ip/proxy": {"enabled": "yes"},
            "/ip/socks": {"enabled": "yes"},
            "/routing/ospf/interface-template": [{"auth": "none"}],
            "/ip/ipsec/profile": [{"enc-algorithm": "3des", "hash-algorithm": "md5"}],
            "/system/routerboard": {"current-firmware": "7.14", "upgrade-firmware": "7.16"},
        }
        return mapping.get(endpoint, [])

    fail_client = AsyncMock()
    fail_client.get = AsyncMock(side_effect=_get_all_failing)
    fail_client.close = AsyncMock()

    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=policy_resp)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, fail_client))),
    ):
        audit_fail = await run_cis_audit(r_obj.id, db=db, claims=claims)
    assert audit_fail.passed_directives == 0
    assert audit_fail.compliance_grade == "F"

    # 4. Caso todas las llamadas client.get lanzan excepción + todas las reglas del tenant deshabilitadas (línea 996 + bloques except)
    all_disabled_policy = CisPoliciesConfigResponse(
        tenant_id=tid,
        profile="CORPORATE",
        updated_at=datetime.now(UTC).isoformat(),
        rules=[disabled_rule],
    )
    exc_client = AsyncMock()
    exc_client.get = AsyncMock(side_effect=RuntimeError("REST endpoint error"))
    exc_client.close = AsyncMock()

    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=all_disabled_policy)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, exc_client))),
    ):
        audit_exc = await run_cis_audit(r_obj.id, db=db, claims=claims)
    assert audit_exc.total_directives == 0


@pytest.mark.asyncio
async def test_auto_harden_router_all_28_directives_success_and_error_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "sec_ops", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid)
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "UnitTest"

    # 1. 404 Router no encontrado (línea 1567)
    db.execute.return_value = _MockResult(single=None)
    missing_rid = uuid.uuid4()
    with pytest.raises(HTTPException) as exc404:
        await auto_harden_router(
            missing_rid,
            CisAutoHardenRequest(router_id=missing_rid, directive_codes_to_apply=None),
            request=req,
            db=db,
            claims=claims,
        )
    assert exc404.value.status_code == 404

    # Política DATACENTER con las 28 directivas habilitadas
    datacenter_policy = CisPoliciesConfigResponse(
        tenant_id=tid,
        profile="DATACENTER",
        updated_at=datetime.now(UTC).isoformat(),
        rules=_build_default_cis_rules("DATACENTER"),
    )

    async def _run_coro(client: Any, menu: str, action: str, coro_fn: Any, **kw: Any) -> Any:
        return await coro_fn()

    # 2. Éxito en todas las 28 remediaciones de _apply_cis (incluyendo fallbacks de CIS-1.4 y CIS-1.5)
    async def _harden_get(endpoint: str) -> Any:
        if endpoint == "/ip/service":
            return [
                {".id": "*1", "name": "telnet", "disabled": "false"},
                {".id": "*2", "name": "winbox", "disabled": "false"},
            ]
        if endpoint == "/user":
            return [
                {".id": "*u1", "name": "admin", "group": "full", "disabled": "false"},
                {".id": "*u2", "name": "rosgrid", "group": "full", "disabled": "false"},
            ]
        if endpoint == "/ip/firewall/filter":
            return []
        if endpoint == "/routing/bgp/connection":
            return [{".id": "*b1"}]
        if endpoint == "/routing/ospf/interface-template":
            return [{".id": "*o1"}]
        if endpoint == "/interface/bridge":
            return [{".id": "*br1"}]
        return []

    async def _harden_post(endpoint: str, json_data: Any = None, **kw: Any) -> Any:
        if endpoint in ("/ip/dns/set", "/ip/neighbor/discovery-settings/set"):
            raise RuntimeError("Fallback to base path")
        return {"status": "ok"}

    ok_client = AsyncMock()
    ok_client.get = AsyncMock(side_effect=_harden_get)
    ok_client.post = AsyncMock(side_effect=_harden_post)
    ok_client.put = AsyncMock(return_value={".id": "*new"})
    ok_client.patch = AsyncMock(return_value={".id": "*patched"})
    ok_client.close = AsyncMock()
    db.execute.return_value = _MockResult(single=r_obj)

    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=datacenter_policy)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, ok_client))),
        patch("src.api.v1.compliance.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.compliance.write_audit_log", make_asserting_audit_mock()) as mock_audit,
    ):
        res_ok = await auto_harden_router(
            r_obj.id,
            CisAutoHardenRequest(router_id=r_obj.id, directive_codes_to_apply=None),
            request=req,
            db=db,
            claims=claims,
        )
    assert res_ok.new_security_score == 100
    assert res_ok.applied_directives_count == 28
    mock_audit.assert_awaited_once()

    # 3. Excepción en cada remediación individual dentro de _apply_cis (cubre todos los except Exception as e:)
    err_client = AsyncMock()
    err_client.get = AsyncMock(side_effect=RuntimeError("Boom GET"))
    err_client.post = AsyncMock(side_effect=RuntimeError("Boom POST"))
    err_client.put = AsyncMock(side_effect=RuntimeError("Boom PUT"))
    err_client.patch = AsyncMock(side_effect=RuntimeError("Boom PATCH"))
    err_client.close = AsyncMock()

    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=datacenter_policy)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(return_value=(r_obj, err_client))),
        patch("src.api.v1.compliance.execute_safe_mutation", AsyncMock(side_effect=_run_coro)),
        patch("src.api.v1.compliance.write_audit_log", make_asserting_audit_mock()),
    ):
        res_partial = await auto_harden_router(
            r_obj.id,
            CisAutoHardenRequest(router_id=r_obj.id, directive_codes_to_apply=[r.code for r in datacenter_policy.rules]),
            request=req,
            db=db,
            claims=claims,
        )
    assert res_partial.executed_under_safemode is True

    # 4. Excepción externa en get_router_and_client (líneas 1932-1933)
    with (
        patch("src.api.v1.compliance.get_tenant_cis_policies_helper", AsyncMock(return_value=datacenter_policy)),
        patch("src.api.v1.compliance.get_router_and_client", AsyncMock(side_effect=RuntimeError("No client"))),
        patch("src.api.v1.compliance.write_audit_log", make_asserting_audit_mock()),
    ):
        res_outer_err = await auto_harden_router(
            r_obj.id,
            CisAutoHardenRequest(router_id=r_obj.id, directive_codes_to_apply=["CIS-1.1"]),
            request=req,
            db=db,
            claims=claims,
        )
    assert res_outer_err.applied_directives_count == 1


# ============================================================================
# 2. BULK OPERATIONS & ROUTEROS v7 UPDATES COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_and_updates_helpers_and_templates_crud() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "ops_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid)
    client = AsyncMock()

    # _perform_pre_upgrade_backup: export vacío -> False (líneas 149, 198-200)
    with patch("src.api.v1.backups.export_router_rsc", AsyncMock(return_value="[]")):
        assert await _perform_pre_upgrade_backup(client, r_obj, tid, uid, db) is False

    # _perform_pre_upgrade_backup: hash idéntico deduplicado (líneas 162-164)
    rsc_text = "/system identity set name=Core"
    rsc_hash = hashlib.sha256(rsc_text.encode("utf-8")).hexdigest()
    prev_bk = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        rsc_sha256_hash=rsc_hash,
        rsc_size_bytes=len(rsc_text),
        rsc_ciphertext=b"invalid",
        rsc_iv=b"iv",
        rsc_tag=b"tag",
    )
    db.execute.return_value = _MockResult(single=prev_bk)
    with patch("src.api.v1.backups.export_router_rsc", AsyncMock(return_value=rsc_text)):
        assert await _perform_pre_upgrade_backup(client, r_obj, tid, uid, db) is True

    # _perform_pre_upgrade_backup: hash distinto con fallo en decrypt previo (líneas 168-172)
    prev_bk.rsc_sha256_hash = "different_hash"
    db.execute.return_value = _MockResult(single=prev_bk)
    with patch("src.api.v1.backups.export_router_rsc", AsyncMock(return_value=rsc_text)):
        assert await _perform_pre_upgrade_backup(client, r_obj, tid, uid, db) is True

    # _extract_update_status_text vacío (línea 235)
    assert _extract_update_status_text(12345) == ""

    # _cleanup_corrupted_npk_downloads: fallback get("file"), non-list, non-dict y excepción (líneas 260-274)
    client.post = AsyncMock(return_value="not-a-list")
    client.get = AsyncMock(return_value=["bad-item", {".id": "*f1", "name": "routeros.npk", "size": "0"}])
    client.delete = AsyncMock()
    assert await _cleanup_corrupted_npk_downloads(client) == 1
    client.get = AsyncMock(return_value="still-not-a-list")
    assert await _cleanup_corrupted_npk_downloads(client) == 0
    client.post = AsyncMock(side_effect=RuntimeError("File print error"))
    assert await _cleanup_corrupted_npk_downloads(client) == 0

    # _fetch_latest_version_via_http_fallback: excepción (líneas 297-299)
    client.post = AsyncMock(side_effect=RuntimeError("Fetch failed"))
    assert await _fetch_latest_version_via_http_fallback(client, "stable") is None

    # _install_routeros_via_fetch_fallback: sin versión -> RuntimeError (línea 313)
    with pytest.raises(RuntimeError):
        await _install_routeros_via_fetch_fallback(client, r_obj, "stable", target_version=None)

    # _install_routeros_via_fetch_fallback: UP_TO_DATE (línea 317) y reboot timeout (líneas 325-326)
    up_res = await _install_routeros_via_fetch_fallback(client, r_obj, "stable", target_version="7.16")
    assert up_res["status"] == "UP_TO_DATE"

    async def _post_fetch_reboot(ep: str, *args: Any, **kw: Any) -> Any:
        if ep == "system/reboot":
            raise MikrotikTimeoutError("Rebooting now")
        return {}

    client.post = AsyncMock(side_effect=_post_fetch_reboot)
    inst_res = await _install_routeros_via_fetch_fallback(client, r_obj, "stable", target_version="7.17")
    assert inst_res["status"] == "INSTALLED_VIA_FETCH_FALLBACK"

    # get_template, create_template (400 duplicado), update_template (404, 400 duplicado, éxito), delete_template (404)
    tpl_obj = ConfigTemplate(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="TPL-1",
        category="SYSTEM",
        description="Desc",
        variables_schema=[],
        rest_steps_template=[],
        requires_safemode=True,
        created_by=uid,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.get.return_value = tpl_obj
    got_tpl = await get_template(tpl_obj.id, claims=claims, db=db)
    assert got_tpl.name == "TPL-1"

    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_get_404:
        await get_template(uuid.uuid4(), claims=claims, db=db)
    assert exc_get_404.value.status_code == 404

    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "UnitTest"
    db.execute.return_value = _MockResult(single=tpl_obj)
    with pytest.raises(HTTPException) as exc_dup_create:
        await create_template(
            ConfigTemplateCreateRequest(
                name="TPL-1",
                category="SYSTEM",
                description="D",
                variables_schema=[],
                rest_steps_template=[{"method": "POST", "endpoint": "system/ntp/client/set", "payload": {}}],
            ),
            request=req,
            claims=claims,
            db=db,
        )
    assert exc_dup_create.value.status_code == 400

    # update_template: 404, 400 nombre duplicado y 200 actualización completa
    db.get.return_value = None
    with pytest.raises(HTTPException):
        await update_template(uuid.uuid4(), ConfigTemplateUpdateRequest(name="X"), request=req, claims=claims, db=db)

    db.get.return_value = tpl_obj
    db.execute.return_value = _MockResult(single=tpl_obj)
    with pytest.raises(HTTPException) as exc_dup_upd:
        await update_template(
            tpl_obj.id,
            ConfigTemplateUpdateRequest(name="OTHER-DUP"),
            request=req,
            claims=claims,
            db=db,
        )
    assert exc_dup_upd.value.status_code == 400

    db.execute.return_value = _MockResult(single=None)
    with patch("src.api.v1.bulk_and_updates.write_audit_log", make_asserting_audit_mock()):
        upd_tpl = await update_template(
            tpl_obj.id,
            ConfigTemplateUpdateRequest(
                name="TPL-RENAMED",
                category="SECURITY",
                description="New desc",
                variables_schema=[],
                rest_steps_template=[],
                requires_safemode=False,
            ),
            request=req,
            claims=claims,
            db=db,
        )
    assert upd_tpl.name == "TPL-RENAMED"

    # delete_template: 404
    db.get.return_value = None
    with pytest.raises(HTTPException):
        await delete_template(uuid.uuid4(), request=req, claims=claims, db=db)


@pytest.mark.asyncio
async def test_execute_single_step_and_fleet_upgrade_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "ops_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid)
    client = AsyncMock()

    # 1. PUT system/logging idempotente (ya existe) y con fallo en get (líneas 1537-1555)
    client.get = AsyncMock(return_value=[{"action": "rosgridsyslog", "topics": "account,info"}])
    res_log = await _execute_single_step(
        client,
        {"method": "PUT", "endpoint": "system/logging", "payload": {"action": "rosgridsyslog", "topics": "info,account"}},
    )
    assert res_log["action"] == "rosgridsyslog"

    client.get = AsyncMock(side_effect=RuntimeError("Logging get error"))
    client.put = AsyncMock(return_value={".id": "*L1"})
    await _execute_single_step(
        client,
        {"method": "PUT", "endpoint": "system/logging", "payload": {"action": "rosgridsyslog", "topics": "account"}},
    )

    # 2. PUT duplicate address en ntp y already exists en queue/type (líneas 1571-1577)
    client.put = AsyncMock(side_effect=MikrotikApiError(400, "failure: duplicate address"))
    assert (
        await _execute_single_step(
            client,
            {"method": "PUT", "endpoint": "system/ntp/client/servers", "payload": {"address": "1.1.1.1"}},
        )
        == []
    )
    client.put = AsyncMock(side_effect=MikrotikApiError(400, "failure: entry already exists"))
    assert await _execute_single_step(client, {"method": "PUT", "endpoint": "queue/type", "payload": {}}) == []

    # 3. POST system/package/update/install timeout y POST system/package/update/check-for-updates (líneas 1582-1596)
    client.post = AsyncMock(side_effect=MikrotikConnectionError("Rebooting"))
    inst_step = await _execute_single_step(
        client, {"method": "POST", "endpoint": "system/package/update/install", "payload": {}}
    )
    assert inst_step["status"] == "REBOOTING_FOR_UPGRADE"

    client.get = AsyncMock(return_value=[])
    client.post = AsyncMock(return_value={"checked": True})
    chk_step = await _execute_single_step(
        client, {"method": "POST", "endpoint": "system/package/update/check-for-updates", "payload": {}}
    )
    assert chk_step == {"checked": True}
    post_generic = await _execute_single_step(
        client, {"method": "POST", "endpoint": "tool/fetch", "payload": {"url": "https://example.com"}}
    )
    assert post_generic == {"checked": True}

    # 4. DELETE, PATCH snmp/community/*0 fallback, PATCH 500 fallback, GET y método inválido (líneas 1597-1630)
    client.delete = AsyncMock(return_value={})
    await _execute_single_step(client, "DELETE", "ip/firewall/filter/*1")

    client.patch = AsyncMock(side_effect=[MikrotikApiError(404, "not found"), {"patched": "*5"}])
    client.get = AsyncMock(return_value=[{".id": "*5", "default": "true"}])
    snmp_res = await _execute_single_step(client, "PATCH", "snmp/community/*0", {"name": "pub"})
    assert snmp_res == {"patched": "*5"}

    client.patch = AsyncMock(side_effect=MikrotikApiError(500, "Internal Server Error"))
    client.post = AsyncMock(return_value={"set_fallback": True})
    fb_patch = await _execute_single_step(client, "PATCH", "custom/menu", {"a": "b"})
    assert fb_patch == {"set_fallback": True}

    client.get = AsyncMock(return_value=[{"id": 1}])
    assert await _execute_single_step(client, "GET", "ip/address") == [{"id": 1}]

    with pytest.raises(ValueError):
        await _execute_single_step(client, "HEAD", "ip/address")

    # 5. _run_router_template_steps con install error -> fallback (línea 1652)
    client.post = AsyncMock(return_value={"status": "ERROR: bad HTTP response"})
    with patch("src.api.v1.bulk_and_updates._install_routeros_via_fetch_fallback", AsyncMock()) as mock_fb_inst:
        await _run_router_template_steps(
            client,
            r_obj,
            [{"method": "POST", "endpoint": "system/package/update/install", "payload": {}}],
            {"update_channel": "stable"},
        )
        mock_fb_inst.assert_awaited_once()

    # 6. execute_bulk_job_on_fleet: template en db, UUID inválido, router sin vault, fallo parcial (líneas 1684-1777)
    r_ok = _make_router(tid)
    r_no_vault = _make_router(tid)
    r_no_vault.vault = None
    tpl_db = ConfigTemplate(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="TPL-FLEET",
        category="SYSTEM",
        rest_steps_template=[{"method": "GET", "endpoint": "system/identity", "payload": {}}],
    )
    job = BulkJob(
        id=uuid.uuid4(),
        tenant_id=tid,
        job_type="TEMPLATE_APPLY",
        title="Job Parcial",
        status=BulkJobStatusEnum.QUEUED,
        template_id=tpl_db.id,
        execution_parameters={"variables": {"k": "v"}},
        target_router_ids=["not-a-uuid", str(r_ok.id), str(r_no_vault.id)],
        total_routers=2,
        succeeded_count=0,
        failed_count=0,
        created_by=uid,
        created_at=datetime.now(UTC),
    )
    db.get.return_value = tpl_db
    db.execute.side_effect = [
        _MockResult(items=[]),
        _MockResult(single=r_ok),
        _MockResult(single=r_no_vault),
    ]
    with patch("src.api.v1.bulk_and_updates._create_client_from_vault", return_value=client):
        res_job = await execute_bulk_job_on_fleet(job, db, claims)
    assert res_job.status == BulkJobStatusEnum.PARTIAL_FAILURE
    assert res_job.succeeded_count == 1
    assert res_job.failed_count == 1

    # 7. create_bulk_job como SUPPORT_L2 (líneas 1852-1859)
    l2_claims = {"tid": str(tid), "sub": str(uid), "rol": SystemRoleEnum.SUPPORT_L2.value}
    db.execute.side_effect = None
    db.execute.return_value = _MockResult(items=[])
    db.get.return_value = job
    with patch("src.api.v1.webfig_common.publish_maker_checker_event", AsyncMock()) as mock_pub:
        await create_bulk_job(
            BulkJobCreateRequest(
                job_type="TEMPLATE_APPLY",
                title="L2 Job",
                target_router_ids=[str(r_ok.id)],
            ),
            claims=l2_claims,
            db=db,
        )
        mock_pub.assert_awaited_once()

    # 8. get_fleet_updates_status, _probe_routerboard_safe, _resolve_package_update_versions, check_fleet_updates_by_channel
    db.execute.return_value = _MockResult(items=[r_obj])
    st_fleet = await get_fleet_updates_status(claims=claims, db=db)
    assert st_fleet.pending_update_count == 1

    client.get = AsyncMock(side_effect=RuntimeError("no routerboard present"))
    is_chr_det, _, _ = await _probe_routerboard_safe(client, r_obj, False, "7.15", "7.16")
    assert is_chr_det is True

    client.post = AsyncMock(return_value={})
    client.get = AsyncMock(return_value={"installed-version": "7.15", "latest-version": "7.15", "status": "ERROR: connection timed out"})
    with patch("src.api.v1.bulk_and_updates._fetch_latest_version_via_http_fallback", AsyncMock(return_value="7.16.2")):
        inst_v, lat_v, st_txt = await _resolve_package_update_versions(client, r_obj, "stable", "7.15", "7.15")
    assert lat_v == "7.16.2"
    assert "HTTP fallback" in st_txt

    with patch("src.api.v1.bulk_and_updates._create_client_from_vault", return_value=client):
        client.post = AsyncMock(side_effect=RuntimeError("Offline router"))
        probe_item = await _probe_single_router_update(r_obj, "stable", tid)
    assert "Offline / Cache" in probe_item.status_text

    db.execute.return_value = _MockResult(items=[r_obj])
    with patch("src.api.v1.bulk_and_updates._probe_single_router_update", AsyncMock(return_value=probe_item)):
        chk_resp = await check_fleet_updates_by_channel(
            RosUpdateChannelCheckRequest(channel="stable", router_ids=[r_obj.id]),
            claims=claims,
            db=db,
        )
    assert chk_resp.checked_count == 1

    # 9. _resolve_upgrade_stages, _trigger_router_package_install y _execute_single_router_upgrade
    with patch("src.api.v1.bulk_and_updates.get_cached_topology", AsyncMock(return_value=None)):
        stages = await _resolve_upgrade_stages(tid, [r_obj.id], poe_aware=True)
    assert stages == [[r_obj.id]]

    client.post = AsyncMock(side_effect=MikrotikTimeoutError("Timeout install"))
    res_trig = await _trigger_router_package_install(client, r_obj, "stable", {"status": "New version is available"})
    assert res_trig["status"] == "REBOOTING_FOR_UPGRADE"

    client.post = AsyncMock(return_value={"status": "ERROR: download failed"})
    with patch(
        "src.api.v1.bulk_and_updates._install_routeros_via_fetch_fallback",
        AsyncMock(return_value={"status": "INSTALLED_VIA_FETCH_FALLBACK"}),
    ):
        res_trig_fb = await _trigger_router_package_install(client, r_obj, "stable", {"status": "Checked"})
    assert res_trig_fb["status"] == "INSTALLED_VIA_FETCH_FALLBACK"

    async def _post_rb_err(ep: str, *args: Any, **kw: Any) -> Any:
        if ep.startswith("system/routerboard"):
            raise MikrotikApiError(400, "not a routerboard")
        return {"status": "Upgrading"}

    client.post = AsyncMock(side_effect=_post_rb_err)
    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", AsyncMock(return_value=True)),
    ):
        upg_dict, upg_ok = await _execute_single_router_upgrade(
            r_obj.id,
            RosUpdateExecuteRequest(router_ids=[r_obj.id], channel="stable", auto_upgrade_firmware=True),
            claims,
            db,
            tid,
            uid,
            0,
        )
    assert upg_ok is True
    assert upg_dict["is_chr"] is True


# ============================================================================
# 3. BACKUPS & APPROVALS COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_backups_and_approvals_missing_branches() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    claims = {"tid": str(tid), "sub": str(uid), "preferred_username": "checker_admin", "rol": "TENANT_ADMIN"}
    db = _make_mock_db()
    r_obj = _make_router(tid)
    client = AsyncMock()

    # Backups helpers
    assert _extract_raw_rsc_text(123) == ""

    client.post = AsyncMock(side_effect=[RuntimeError("file/get err"), RuntimeError("file/read err")])
    assert await _read_large_rsc_file(client, "test.rsc", "*1", 8192) == ""

    client.post = AsyncMock(return_value={"ret": ""})
    assert await _read_large_rsc_file(client, "test.rsc", "", 8192) == ""

    client.get = AsyncMock(side_effect=[RuntimeError("filter err"), [{"name": "bk.rsc", ".id": "*1"}]])
    client.post = AsyncMock(side_effect=RuntimeError("print err"))
    files_meta = await _list_router_files_metadata_safe(client, "bk.rsc")
    assert len(files_meta) == 1

    client.get = AsyncMock(side_effect=RuntimeError("all failed"))
    assert await _list_router_files_metadata_safe(client, None) == []

    client.post = AsyncMock(return_value=["not-a-dict", {".id": "*9", "name": "rosgrid_bk_old.rsc"}])
    client.delete = AsyncMock(side_effect=RuntimeError("del err"))
    await _cleanup_stale_rosgrid_bk_files(client, exclude_name="rosgrid_bk_keep.rsc")

    client.patch = AsyncMock(side_effect=RuntimeError("patch group err"))
    assert await _try_self_heal_group_ftp_policy(client, {".id": "*g1", "name": "api", "policy": "api,policy"}) is False

    client.get = AsyncMock(return_value="not-a-list")
    assert await _resolve_user_group_ftp_status(client) == ("rosgrid-api-group", False)

    client.username = "unknown_user"
    client.get = AsyncMock(side_effect=[[{"name": "admin", "group": "full"}], [{"name": "other", "policy": "ftp"}]])
    assert await _resolve_user_group_ftp_status(client) == ("rosgrid-api-group", False)

    # _export_via_fresh_ephemeral_session: éxito y excepción
    client.host = "10.0.0.1"
    client.port = 443
    client.ssl_pinned_fingerprint = None
    client.timeout = 5.0
    client.post = AsyncMock(return_value={"ret": "*u99"})
    client.delete = AsyncMock(side_effect=RuntimeError("cleanup user err"))
    with (
        patch("src.api.v1.backups.asyncio.sleep", AsyncMock()),
        patch("src.api.v1.backups._read_and_cleanup_rsc_file", AsyncMock(return_value="/ip address add address=1.1.1.1/32")),
        patch("src.api.v1.backups.MikrotikRestClient") as mock_tmp_cls,
    ):
        tmp_inst = AsyncMock()
        mock_tmp_cls.return_value = tmp_inst
        eph_txt = await _export_via_fresh_ephemeral_session(client, "full", "rosgrid_bk_1")
    assert "/ip address" in eph_txt

    client.post = AsyncMock(side_effect=RuntimeError("user/add failed"))
    assert await _export_via_fresh_ephemeral_session(client, "full", "rosgrid_bk_2") == ""

    with patch("src.api.v1.backups._resolve_user_group_ftp_status", AsyncMock(side_effect=RuntimeError("err"))):
        assert await _try_fallback_rsc_export(client, "f") == ("", None)

    hunks = _build_side_by_side_hunks(["--- base.rsc", "+++ target.rsc", "@@ -1,2 +1,2 @@", "/ip service", "+set telnet disabled=yes", "-set telnet disabled=no"])
    assert len(hunks) == 2
    assert hunks[0].section_header == "/ip service"

    # _execute_router_backup_core con respaldo previo para calcular diff (líneas 512-513) y trigger_batch_backups
    aad = f"{tid}:{r_obj.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"/ip service set telnet disabled=no", aad)
    prev_backup = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        rsc_sha256_hash="old_hash",
        rsc_size_bytes=32,
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
        created_at=datetime.now(UTC),
    )
    db.execute.return_value = _MockResult(single=prev_backup)
    with (
        patch("src.api.v1.backups.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.backups.export_router_rsc", AsyncMock(return_value="/ip service set telnet disabled=yes")),
        patch("src.api.v1.backups.write_audit_log", make_asserting_audit_mock()),
    ):
        _, trig_res = await _execute_router_backup_core(r_obj.id, tid, uid, "admin", "TENANT_ADMIN", "127.0.0.1", claims, db)
    assert trig_res.status == "CREATED"

    req = MagicMock()
    req.client.host = "127.0.0.1"
    with patch("src.api.v1.backups._execute_router_backup_core", AsyncMock(side_effect=RuntimeError("Conn reset"))):
        batch_res = await trigger_batch_backups(BatchBackupTriggerRequest(router_ids=[r_obj.id]), request=req, claims=claims, db=db)
    assert batch_res.failed_count == 1

    # get_backup_diff con LIVE y excepción en export (líneas 684-689)
    db.get.return_value = prev_backup
    with (
        patch("src.api.v1.backups.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.backups.export_router_rsc", AsyncMock(side_effect=RuntimeError("Live export err"))),
    ):
        diff_live = await get_backup_diff(r_obj.id, base_backup_id=prev_backup.id, target_backup_id="LIVE", claims=claims, db=db)
    assert diff_live.lines_removed >= 1

    # Approvals: _execute_deferred_operation con prefijo rest/ (línea 93)
    app_req = ApprovalRequest(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        status=ApprovalStatusEnum.PENDING,
        summary="Test",
        requester_justification="Just",
        ros_rest_method="DELETE",
        ros_rest_path="rest/ip/firewall/filter/*1",
        request_payload={},
        requested_by=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )

    async def _run_coro(client: Any, menu: str, action: str, coro_fn: Any, **kw: Any) -> Any:
        return await coro_fn()

    client.delete = AsyncMock(return_value={"deleted": True})
    with patch("src.api.v1.approvals.execute_safe_mutation", AsyncMock(side_effect=_run_coro)):
        def_res = await _execute_deferred_operation(client, app_req)
    assert def_res == {"deleted": True}

    # list_approvals cuando db.get lanza excepción (líneas 193-194) y cuando type(db) is AsyncSession (líneas 163-182)
    db.execute.side_effect = [_MockResult(single=1), _MockResult(items=[app_req])]
    db.get.side_effect = RuntimeError("Mock get error")
    list_res = await list_approvals(status_filter=None, limit=10, offset=0, claims=claims, db=db)
    assert list_res.total == 1

    real_like_db = AsyncSession.__new__(AsyncSession)
    u_mock = User(id=app_req.requested_by, tenant_id=tid, username="maker_u", email="m@x.com", full_name="M", password_hash="x", role=SystemRoleEnum.SUPPORT_L2)
    real_like_db.execute = AsyncMock(  # type: ignore[method-assign]
        side_effect=[
            _MockResult(single=1),
            _MockResult(items=[app_req]),
            _MockResult(items=[u_mock]),
            _MockResult(items=[r_obj]),
        ]
    )
    list_real = await list_approvals(status_filter=None, limit=10, offset=0, claims=claims, db=real_like_db)
    assert list_real.items[0].requested_by_username == "maker_u"
    assert list_real.items[0].router_name == r_obj.display_name

    # _execute_mcp_deferred_tool con herramienta desconocida -> None (línea 278)
    app_req.request_payload = {"mcp_tool": "unknown_tool"}
    assert await _execute_mcp_deferred_tool(app_req, claims, db, tid, uid) is None

    # _execute_approval_lifecycle con resultado MCP (líneas 294-297)
    with patch("src.api.v1.approvals._execute_mcp_deferred_tool", AsyncMock(return_value={"status": "OK"})):
        act_str, code = await _execute_approval_lifecycle(None, app_req, datetime.now(UTC), claims, db, tid, uid)
    assert code == 200
    assert act_str == "MAKER_CHECKER_APPROVED_AND_EXECUTED"

    # approve_request: con totp_code y BULK_MULTI_ROUTER_EXECUTION fallido y sin job adjunto (líneas 368-370, 425-438, 459)
    app_bulk = ApprovalRequest(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=r_obj.id,
        action_type=CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION,
        status=ApprovalStatusEnum.PENDING,
        summary="Bulk",
        requester_justification="Just",
        ros_rest_method="POST",
        ros_rest_path="rest/operations/bulk-jobs",
        request_payload={},
        requested_by=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )
    failed_job = BulkJob(
        id=uuid.uuid4(),
        tenant_id=tid,
        job_type="TEMPLATE_APPLY",
        title="FailJob",
        status=BulkJobStatusEnum.FAILED,
        succeeded_count=0,
        failed_count=2,
        total_routers=2,
    )
    db.get.side_effect = None
    db.get.return_value = app_bulk
    db.execute.side_effect = [_MockResult(single=failed_job)]
    with (
        patch("src.api.v1.vault._verify_admin_totp", AsyncMock()) as mock_totp,
        patch("src.api.v1.approvals.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.approvals.execute_bulk_job_on_fleet", AsyncMock(return_value=failed_job)),
        patch("src.api.v1.approvals.write_audit_log", make_asserting_audit_mock()),
        patch("src.api.v1.approvals.publish_maker_checker_event", AsyncMock()),
    ):
        app_res_fail = await approve_request(
            app_bulk.id,
            ApproveRequestPayload(review_comment="Try", totp_code="123456"),
            request=req,
            claims=claims,
            db=db,
        )
    assert app_res_fail.status == ApprovalStatusEnum.APPROVED_EXECUTION_FAILED.value
    mock_totp.assert_awaited_once()

    # approve_request: BULK_MULTI_ROUTER_EXECUTION sin BulkJob adjunto (líneas 435-438)
    app_bulk.status = ApprovalStatusEnum.PENDING
    db.execute.side_effect = [_MockResult(single=None)]
    with (
        patch("src.api.v1.approvals.get_router_and_client", AsyncMock(return_value=(r_obj, client))),
        patch("src.api.v1.approvals.write_audit_log", make_asserting_audit_mock()),
        patch("src.api.v1.approvals.publish_maker_checker_event", AsyncMock()),
    ):
        app_res_nojob = await approve_request(
            app_bulk.id,
            ApproveRequestPayload(review_comment="NoJob"),
            request=req,
            claims=claims,
            db=db,
        )
    assert app_res_nojob.execution_result == {"status": "NO_BULK_JOB_ATTACHED"}

    # reject_request: con totp_code y BULK_MULTI_ROUTER_EXECUTION marcando job FAILED (líneas 503-505, 552-555)
    app_bulk.status = ApprovalStatusEnum.PENDING
    db.execute.side_effect = [_MockResult(single=failed_job)]
    with (
        patch("src.api.v1.vault._verify_admin_totp", AsyncMock()),
        patch("src.api.v1.approvals.write_audit_log", make_asserting_audit_mock()),
        patch("src.api.v1.approvals.publish_maker_checker_event", AsyncMock()),
    ):
        rej_res = await reject_request(
            app_bulk.id,
            RejectRequestPayload(review_comment="Reject", totp_code="654321"),
            request=req,
            claims=claims,
            db=db,
        )
    assert rej_res.status == ApprovalStatusEnum.REJECTED.value
