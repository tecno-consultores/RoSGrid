# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para WebFig Capa 2 Next-Gen: RPC, /console/inspect, .query/.proplist, Bulk y Export .rsc."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.webfig_layer2 import (
    _apply_single_bulk_op,
    _build_catalog_groups,
    _build_ros_query_stack,
    _check_l2_write_permission,
    _extract_rsc_section_for_path,
    _filter_items_locally,
    _infer_columns,
    _infer_type_from_val,
    _normalize_proplist,
    _parse_console_inspect_syntax,
    _resolve_rpc_target_and_args,
    _resolve_schema_via_inspect,
    _synthesize_rsc_from_items,
    _validate_l2_path,
    create_resource,
    delete_resource,
    execute_bulk_operation,
    execute_command,
    export_layer2_submenu,
    get_catalog,
    get_resource,
    get_rpc_actions_for_path,
    get_rpc_catalog,
    inspect_layer2_schema,
    query_resource_server_side,
    update_resource,
)
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.schemas.webfig_layer2 import (
    DynamicLayer2BulkRequest,
    DynamicLayer2CommandRequest,
    DynamicLayer2ExportRequest,
    DynamicLayer2QueryRequest,
    DynamicLayer2WriteRequest,
    Layer2QueryFilterItem,
)


def test_validate_l2_path_valid() -> None:
    assert _validate_l2_path("mpls/interface") == "mpls/interface"
    assert _validate_l2_path("/interface/vpls/") == "interface/vpls"
    assert _validate_l2_path("routing/bfd/session") == "routing/bfd/session"


def test_validate_l2_path_traversal() -> None:
    with pytest.raises(HTTPException) as exc1:
        _validate_l2_path("../etc/passwd")
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        _validate_l2_path("mpls/../system")
    assert exc2.value.status_code == 400


def test_validate_l2_path_forbidden() -> None:
    for forbidden in ["user", "user/admin", "system/scheduler", "ip/service"]:
        with pytest.raises(HTTPException) as exc:
            _validate_l2_path(forbidden)
        assert exc.value.status_code == 403
        assert "Acceso prohibido" in exc.value.detail


def test_check_l2_write_permission() -> None:
    admin_claims = {"rol": SystemRoleEnum.TENANT_ADMIN.value}
    _check_l2_write_permission(admin_claims, None)

    perm = UserRouterPermission(
        user_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        can_write_layer2=True,
    )
    l3_claims = {"rol": SystemRoleEnum.SUPPORT_L3.value, "all_r": False}
    _check_l2_write_permission(l3_claims, perm)

    perm_denied = UserRouterPermission(
        user_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        can_write_layer2=False,
    )
    with pytest.raises(HTTPException) as exc1:
        _check_l2_write_permission(l3_claims, perm_denied)
    assert exc1.value.status_code == 403

    l2_claims = {"rol": SystemRoleEnum.SUPPORT_L2.value}
    with pytest.raises(HTTPException) as exc2:
        _check_l2_write_permission(l2_claims, None)
    assert exc2.value.status_code == 403


def test_infer_type_from_val() -> None:
    assert _infer_type_from_val(True) == "boolean_ros"
    assert _infer_type_from_val("true") == "boolean_ros"
    assert _infer_type_from_val("no") == "boolean_ros"
    assert _infer_type_from_val(42) == "integer"
    assert _infer_type_from_val("100") == "integer"
    assert _infer_type_from_val("hello") == "string"


def test_infer_columns() -> None:
    items = [
        {
            ".id": "*1",
            "name": "tunnel1",
            "remote-peer": "10.0.0.1",
            "vpls-id": 100,
            "disabled": "false",
            "dynamic": "false",
        }
    ]
    cols = _infer_columns(items)
    col_map = {c.key: c for c in cols}

    assert col_map[".id"].type == "readonly_id"
    assert col_map[".id"].editable is False
    assert col_map["name"].sortable is True
    assert col_map["disabled"].type == "boolean_ros"
    assert col_map["dynamic"].editable is False


def test_build_catalog_groups() -> None:
    groups = _build_catalog_groups(["container", "zerotier"])
    group_names = [g.group for g in groups]
    assert "MPLS & VPLS" in group_names
    assert "Certificates & Security" in group_names
    assert "SNMP & Management" in group_names
    assert "Containers" in group_names
    assert "ZeroTier" in group_names

    std_groups = _build_catalog_groups([])
    std_names = [g.group for g in std_groups]
    assert "Containers" not in std_names
    assert "ZeroTier" not in std_names


# ============================================================================
# PRUEBAS UNITARIAS HITO 27.16 (RPC, INSPECT, QUERY, BULK Y EXPORT .RSC)
# ============================================================================


def test_get_rpc_actions_for_path() -> None:
    cert_actions = get_rpc_actions_for_path("certificate")
    action_names = [a.action for a in cert_actions]
    assert "add-acme" in action_names
    assert "sign" in action_names
    assert "export-certificate" in action_names
    assert get_rpc_actions_for_path("unknown/path") == []


def test_parse_console_inspect_syntax_and_fallback() -> None:
    # 1. Salida real de /rest/console/inspect
    raw_inspect = [
        {"type": "arg", "symbol": "name", "text": "Certificate name"},
        {"type": "arg", "symbol": "common-name", "text": "Subject CN"},
        {"type": "arg", "symbol": "trusted", "text": "Trusted flag"},
        {"type": "arg", "symbol": "<numbers>", "text": "Ignored internal symbol"},
    ]
    parsed = _parse_console_inspect_syntax("certificate", raw_inspect)
    keys = [c.key for c in parsed]
    assert ".id" in keys
    assert "name" in keys
    assert "common-name" in keys
    assert "trusted" in keys
    assert "<numbers>" not in keys

    # 2. Fallback tipado cuando /console/inspect devuelve lista vacía
    fallback_cert = _parse_console_inspect_syntax("certificate", [])
    fb_map = {c.key: c for c in fallback_cert}
    assert "common-name" in fb_map
    assert fb_map["key-type"].enum_options == ["rsa", "ec"]

    # 3. Fallback por defecto para ruta desconocida
    fallback_unknown = _parse_console_inspect_syntax("custom/menu", None)
    assert [c.key for c in fallback_unknown] == [".id", "name", "disabled", "comment"]


@pytest.mark.asyncio
async def test_resolve_schema_via_inspect_cache_and_live() -> None:
    tid = uuid.uuid4()
    redis_mock = AsyncMock()
    client_mock = AsyncMock()

    # Caso 1: Cache miss -> consulta /console/inspect y guarda en Redis
    redis_mock.get.return_value = None
    client_mock.post.return_value = [
        {"symbol": "interface", "text": "MPLS interface"},
        {"symbol": "mpls-mtu", "text": "MPLS MTU size"},
    ]
    cols, source = await _resolve_schema_via_inspect(redis_mock, tid, "7.16", "mpls/interface", client_mock)
    assert source == "console_inspect"
    assert any(c.key == "mpls-mtu" for c in cols)
    redis_mock.setex.assert_awaited_once()

    # Caso 2: Cache hit desde Redis
    redis_mock.get.return_value = json.dumps([c.model_dump() for c in cols])
    cached_cols, cached_source = await _resolve_schema_via_inspect(
        redis_mock, tid, "7.16", "mpls/interface", client_mock
    )
    assert cached_source == "console_inspect"
    assert len(cached_cols) == len(cols)


def test_normalize_proplist_and_validation() -> None:
    assert _normalize_proplist(None) == []
    assert _normalize_proplist("name,common-name,.id,trusted") == [".id", "name", "common-name", "trusted"]
    assert _normalize_proplist(["interface", "mpls-mtu"]) == [".id", "interface", "mpls-mtu"]

    with pytest.raises(HTTPException) as exc:
        _normalize_proplist("name;DROP TABLE")
    assert exc.value.status_code == 400


def test_build_ros_query_stack_and_local_filter() -> None:
    filters = [
        Layer2QueryFilterItem(field="disabled", operator="=", value="false"),
        Layer2QueryFilterItem(field="trusted", operator="!=", value="false"),
    ]
    stack = _build_ros_query_stack(filters)
    assert stack == ["disabled=false", "trusted=false", "#!", "#&"]

    rows = [
        {".id": "*1", "name": "cert-a", "disabled": "false", "trusted": "true", "extra": "x"},
        {".id": "*2", "name": "cert-b", "disabled": "true", "trusted": "true", "extra": "y"},
    ]
    filtered = _filter_items_locally(rows, filters, [".id", "name"])
    assert len(filtered) == 1
    assert filtered[0] == {".id": "*1", "name": "cert-a"}


def test_extract_and_synthesize_rsc_section() -> None:
    full_rsc = (
        "/interface bridge\n"
        "add name=bridge1\n"
        "/certificate\n"
        "add common-name=r1.local name=webfig-cert trusted=yes\n"
        "/ip address\n"
        "add address=10.0.0.1/24 interface=bridge1\n"
    )
    sec = _extract_rsc_section_for_path(full_rsc, "certificate")
    assert sec.startswith("/certificate")
    assert "common-name=r1.local" in sec
    assert "/ip address" not in sec

    synth = _synthesize_rsc_from_items("mpls/interface", [{".id": "*1", "interface": "all", "mpls-mtu": "1508"}])
    assert "/mpls interface" in synth
    assert "add interface=all mpls-mtu=1508" in synth


@pytest.mark.asyncio
async def test_apply_single_bulk_op_and_rpc_resolver() -> None:
    client = AsyncMock()
    r_en = await _apply_single_bulk_op(client, "mpls/interface", "enable", "*1", None)
    assert r_en["status"] == "UPDATED"
    client.patch.assert_awaited_with("mpls/interface/*1", {"disabled": "false"})

    r_dis = await _apply_single_bulk_op(client, "mpls/interface", "disable", "*2", None)
    assert r_dis["applied"] == {"disabled": "true"}

    r_cmt = await _apply_single_bulk_op(client, "mpls/interface", "comment", "*3", "Backbone Sur")
    assert r_cmt["applied"] == {"comment": "Backbone Sur"}

    r_rm = await _apply_single_bulk_op(client, "mpls/interface", "remove", "*4", None)
    assert r_rm["status"] == "DELETED"
    client.delete.assert_awaited_with("mpls/interface/*4")

    cmd_req = DynamicLayer2CommandRequest(action="sign", item_id="*9", arguments={"ca": "rosgrid-ca"})
    target_ep, rpc_args, desc = _resolve_rpc_target_and_args("certificate", cmd_req)
    assert target_ep == "certificate/sign"
    assert rpc_args["numbers"] == "*9"
    assert rpc_args["ca"] == "rosgrid-ca"
    assert desc is not None and desc.requires_maker_checker is True


@pytest.mark.asyncio
async def test_layer2_nextgen_endpoints_integration() -> None:
    router_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    claims = {
        "tid": str(tenant_id),
        "sub": str(user_id),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "preferred_username": "admin_noc",
    }
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    router_obj = SimpleNamespace(id=router_id, display_name="R1-Core", ros_version="7.16.1")
    client = AsyncMock()
    req = MagicMock()
    req.client.host = "127.0.0.1"

    async def _fake_safe_mutation(_c: object, _m: str, _a: str, fn: object, **_kw: object) -> object:
        return await fn()  # type: ignore[operator]

    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", AsyncMock(return_value=(router_obj, client))),
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=AsyncMock(get=AsyncMock(return_value=None))),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", AsyncMock(return_value=[])),
        patch("src.api.v1.webfig_layer2.write_audit_log", AsyncMock()),
        patch(
            "src.api.v1.webfig_layer2.execute_safe_mutation",
            AsyncMock(side_effect=_fake_safe_mutation),
        ),
    ):
        # 0. Catálogo de menús y CRUD base (create, update, delete)
        cat_res = await get_catalog(router_id, refresh=False, claims=claims, db=db)
        assert cat_res.router_id == router_id

        write_req = DynamicLayer2WriteRequest.model_validate({"interface": "ether2", "enable_safemode": True})
        client.put.return_value = {".id": "*10"}
        await create_resource(router_id, "mpls/interface", write_req, req, idempotency_key="ik-c", claims=claims, db=db)

        client.get.return_value = {".id": "*10", "interface": "ether2"}
        client.patch.return_value = {".id": "*10", "interface": "ether3"}
        await update_resource(
            router_id, "mpls/interface", "*10", write_req, req, idempotency_key="ik-u", claims=claims, db=db
        )

        client.delete.return_value = None
        await delete_resource(router_id, "mpls/interface", "*10", req, idempotency_key="ik-d", claims=claims, db=db)

        # 1. Catálogo RPC
        rpc_cat = await get_rpc_catalog(router_id, "certificate", claims=claims, db=db)
        assert len(rpc_cat) == 3

        # 2. Endpoint /inspect
        client.post.return_value = [{"symbol": "name", "text": "Cert name"}]
        insp = await inspect_layer2_schema(router_id, "certificate", claims=claims, db=db)
        assert insp.ros_path == "certificate"
        assert "name" in insp.completions

        # 3. GET /resource con tabla vacía -> usa fallback /console/inspect
        res_empty = await get_resource(
            router_id, "certificate", refresh=False, proplist="name,common-name", claims=claims, db=db
        )
        assert res_empty.is_server_filtered is True
        assert len(res_empty.columns_schema) >= 2
        assert len(res_empty.available_rpc_actions) == 3

        # 4. POST /query (.query + .proplist)
        client.post.return_value = [{".id": "*1", "name": "webfig-tls", "trusted": "true"}]
        q_req = DynamicLayer2QueryRequest(
            proplist=[".id", "name", "trusted"],
            filters=[Layer2QueryFilterItem(field="trusted", operator="=", value="true")],
        )
        q_res = await query_resource_server_side(router_id, "certificate", q_req, claims=claims, db=db)
        assert q_res.is_server_filtered is True
        assert q_res.payload_reduction_pct > 0
        assert len(q_res.items) == 1

        # 5. POST /bulk (enable lote)
        bulk_req = DynamicLayer2BulkRequest(action="enable", item_ids=["*1", "*2"], enable_safemode=True)
        bulk_res = await execute_bulk_operation(
            router_id, "mpls/interface", bulk_req, req, idempotency_key="ik-1", claims=claims, db=db
        )
        assert bulk_res.succeeded_count == 2
        assert bulk_res.safemode_applied is True

        # 6. POST /export (.rsc + diff)
        client.post.return_value = "/certificate\nadd name=webfig-tls common-name=r1.local\n"
        db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
        exp_req = DynamicLayer2ExportRequest(mode="compact", compare_with_latest_backup=True)
        exp_res = await export_layer2_submenu(router_id, "certificate", exp_req, req, claims=claims, db=db)
        assert exp_res.cli_header == "/certificate"
        assert exp_res.has_drift is True
        assert "+add name=webfig-tls" in exp_res.unified_diff

        # 7. POST /command con acción RPC
        client.post.return_value = {"ret": "done"}
        cmd_payload = DynamicLayer2CommandRequest(
            action="add-acme",
            arguments={"dns-name": "r1.isp.local"},
            enable_safemode=False,
        )
        cmd_res = await execute_command(router_id, "certificate", cmd_payload, req, claims=claims, db=db)
        assert cmd_res == {"ret": "done"}

