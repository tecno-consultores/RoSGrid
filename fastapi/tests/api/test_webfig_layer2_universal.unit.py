# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para WebFig Capa 2: Motor Dinámico Universal, Inspector de Esquemas y Catálogo."""

import uuid

import pytest
from fastapi import HTTPException

from src.api.v1.webfig_layer2 import (
    _build_catalog_groups,
    _check_l2_write_permission,
    _infer_columns,
    _infer_type_from_val,
    _validate_l2_path,
)
from src.models.core import SystemRoleEnum, UserRouterPermission


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
    # Forbidden roots
    for forbidden in ["user", "user/admin", "system/scheduler", "ip/service"]:
        with pytest.raises(HTTPException) as exc:
            _validate_l2_path(forbidden)
        assert exc.value.status_code == 403
        assert "Acceso prohibido" in exc.value.detail


def test_check_l2_write_permission() -> None:
    # Superadmin & Tenant admin allowed
    admin_claims = {"rol": SystemRoleEnum.TENANT_ADMIN.value}
    _check_l2_write_permission(admin_claims, None)

    # Support L3 with can_write_layer2 allowed
    perm = UserRouterPermission(
        user_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        can_write_layer2=True,
    )
    l3_claims = {"rol": SystemRoleEnum.SUPPORT_L3.value, "all_r": False}
    _check_l2_write_permission(l3_claims, perm)

    # Support L3 without permission denied
    perm_denied = UserRouterPermission(
        user_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        can_write_layer2=False,
    )
    with pytest.raises(HTTPException) as exc1:
        _check_l2_write_permission(l3_claims, perm_denied)
    assert exc1.value.status_code == 403

    # Support L2 denied
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

    # Without optional packages
    std_groups = _build_catalog_groups([])
    std_names = [g.group for g in std_groups]
    assert "Containers" not in std_names
    assert "ZeroTier" not in std_names
