# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias para Gobernanza Granular de Flags en Perfiles de Usuario (30 Acciones RBAC)."""

import uuid
from typing import Any

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.api.v1.rbac import ACTIONS_METADATA
from src.api.v1.users import (
    _normalize_flag_override_value,
    _sanitize_user_flag_overrides,
)
from src.db.session import get_db_session
from src.main import app
from src.models.core import SystemRoleEnum, User, UserRouterPermission
from src.rbac.policy_matrix import POLICY_MATRIX
from tests.conftest import FakeAsyncRedis, make_asserting_audit_mock


def test_actions_metadata_and_policy_matrix_count() -> None:
    """Verifica que el catálogo de acciones y la matriz de políticas tengan exactamente 30 acciones."""
    assert len(ACTIONS_METADATA) == 30
    metadata_keys = {action["key"] for action in ACTIONS_METADATA}
    assert len(metadata_keys) == 30

    # Las 11 nuevas acciones del Hito 27.17
    new_11_actions = {
        "WEBFIG_L2_RPC_COMMANDS",
        "WEBFIG_L2_BULK_OPS",
        "WEBFIG_L2_EXPORT_RSC",
        "IPAM_VRFS_PREFIXES_MGMT",
        "SUBSCRIBERS_QOS_PROVISIONING",
        "FIELD_OPS_OPTICAL_NAP_MGMT",
        "BGP_LOOKING_GLASS_IPFIX",
        "ENTERPRISE_CIS_DRIFT_COMPLIANCE",
        "ENTERPRISE_SDWAN_SLA_ROGUEDHCP",
        "WIFI_CAPSMAN_PROVISIONING",
        "TOPOLOGY_L2_CVE_SYSLOG_MCP",
    }
    assert new_11_actions.issubset(metadata_keys)

    for role in SystemRoleEnum:
        assert len(POLICY_MATRIX[role]) == 30
        assert set(POLICY_MATRIX[role].keys()) == metadata_keys


def test_normalize_flag_override_values() -> None:
    """Verifica la normalización determinista de valores de override (CC = 4)."""
    assert _normalize_flag_override_value(None) is None
    assert _normalize_flag_override_value(True) == "ALLOW"
    assert _normalize_flag_override_value(False) == "DENY"
    assert _normalize_flag_override_value("allow") == "ALLOW"
    assert _normalize_flag_override_value("MAKER_CHECKER") == "MAKER_CHECKER"
    assert _normalize_flag_override_value("read_only") == "READ_ONLY"
    assert _normalize_flag_override_value("deny") == "DENY"
    assert _normalize_flag_override_value("INVALID_VALUE") is None


def test_sanitize_user_flag_overrides() -> None:
    """Verifica sanitización de mapa de overrides y rechazo de claves o valores inválidos."""
    valid_keys = {"LIVE_DIAGNOSTICS", "CONFIG_STANDARD_L1", "WEBFIG_L2_RPC_COMMANDS"}
    existing = {"LIVE_DIAGNOSTICS": "DENY"}

    # Modificar y agregar
    incoming: dict[str, str | bool | None] = {
        "LIVE_DIAGNOSTICS": "ALLOW",
        "WEBFIG_L2_RPC_COMMANDS": True,
    }
    res = _sanitize_user_flag_overrides(existing, incoming, valid_keys)
    assert res == {"LIVE_DIAGNOSTICS": "ALLOW", "WEBFIG_L2_RPC_COMMANDS": "ALLOW"}

    # Eliminar clave pasando None
    res_del = _sanitize_user_flag_overrides(res, {"LIVE_DIAGNOSTICS": None}, valid_keys)
    assert "LIVE_DIAGNOSTICS" not in res_del
    assert res_del == {"WEBFIG_L2_RPC_COMMANDS": "ALLOW"}

    # Error en clave desconocida
    with pytest.raises(HTTPException) as exc_info:
        _sanitize_user_flag_overrides({}, {"UNKNOWN_FLAG": "ALLOW"}, valid_keys)
    assert exc_info.value.status_code == 400

    # Error en valor no normalizable
    with pytest.raises(HTTPException) as exc_info2:
        _sanitize_user_flag_overrides({}, {"LIVE_DIAGNOSTICS": "UNSUPPORTED_VAL"}, valid_keys)
    assert exc_info2.value.status_code == 400


class MockRbacUserSession:
    def __init__(self, target_user: User):
        self.target_user = target_user
        self.committed = False
        self.refreshed = False

    def add(self, instance: Any) -> None:
        pass

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> Any:
        class MockResult:
            def __init__(self, user: User):
                self.user = user

            def scalar_one_or_none(self) -> User | None:
                return self.user

        return MockResult(self.target_user)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, instance: Any) -> None:
        self.refreshed = True


@pytest.mark.asyncio
async def test_get_user_effective_permissions_endpoint(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica GET /api/v1/users/{user_id}/effective-permissions consolidando rol y overrides."""
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    session_id = "sess-eff-perms-01"

    monkeypatch.setattr("src.api.v1.users.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.api.v1.rbac.get_redis_client", lambda: fake_redis)

    # Sesión activa para admin
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": str(admin_id),
            "username": "admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    # Usuario objetivo SUPPORT_L2 con override individual
    target_user = User(
        id=target_user_id,
        tenant_id=tenant_id,
        username="tech_l2",
        email="tech@rosgrid.com",
        password_hash="fakehash",
        full_name="Tech L2",
        role=SystemRoleEnum.SUPPORT_L2,
        is_active=True,
        has_all_routers_access=False,
        feature_flags_override={"WEBFIG_L2_RPC_COMMANDS": "ALLOW", "LIVE_DIAGNOSTICS": "DENY"},
    )
    mock_db = MockRbacUserSession(target_user)
    app.dependency_overrides[get_db_session] = lambda: mock_db

    token = create_jwt_access_token(
        str(admin_id), str(tenant_id), "org", session_id, SystemRoleEnum.TENANT_ADMIN.value, False
    )

    try:
        resp = await async_client.get(
            f"/api/v1/users/{target_user_id}/effective-permissions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == str(target_user_id)
        assert data["role"] == "SUPPORT_L2"
        assert len(data["actions_catalog"]) == 30
        assert data["effective_permissions"]["WEBFIG_L2_RPC_COMMANDS"] == "ALLOW"
        assert data["effective_permissions"]["LIVE_DIAGNOSTICS"] == "DENY"
        # En SUPPORT_L2 base es MAKER_CHECKER para SCHEDULE_MAINTENANCE
        assert data["effective_permissions"]["SCHEDULE_MAINTENANCE"] == "MAKER_CHECKER"
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_patch_user_feature_flags_endpoint(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica PATCH /api/v1/users/{user_id}/feature-flags con actualización de overrides e invalidación."""
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    session_id = "sess-patch-flags-01"

    fake_audit = make_asserting_audit_mock()
    monkeypatch.setattr("src.api.v1.users.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.core.audit.write_audit_log", fake_audit)

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": str(admin_id),
            "username": "admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    target_user = User(
        id=target_user_id,
        tenant_id=tenant_id,
        username="operator_01",
        email="op01@rosgrid.com",
        password_hash="fakehash",
        full_name="Operator 01",
        role=SystemRoleEnum.SUPPORT_L1,
        is_active=True,
        has_all_routers_access=False,
        feature_flags_override={"LIVE_DIAGNOSTICS": "ALLOW"},
    )
    mock_db = MockRbacUserSession(target_user)
    app.dependency_overrides[get_db_session] = lambda: mock_db

    token = create_jwt_access_token(
        str(admin_id), str(tenant_id), "org", session_id, SystemRoleEnum.TENANT_ADMIN.value, False
    )

    try:
        # 1. Aplicar cambios: booleano True a ALLOW, y valor explícito READ_ONLY
        payload = {
            "feature_flags_override": {
                "WEBFIG_L2_RPC_COMMANDS": True,
                "BGP_LOOKING_GLASS_IPFIX": "READ_ONLY",
            }
        }
        resp = await async_client.patch(
            f"/api/v1/users/{target_user_id}/feature-flags",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "01928900-0000-7000-8000-000000000240",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["feature_flags_override"]["WEBFIG_L2_RPC_COMMANDS"] == "ALLOW"
        assert data["feature_flags_override"]["BGP_LOOKING_GLASS_IPFIX"] == "READ_ONLY"
        assert data["feature_flags_override"]["LIVE_DIAGNOSTICS"] == "ALLOW"
        assert mock_db.committed is True

        # 2. Eliminar un flag pasando null
        del_payload = {"feature_flags_override": {"LIVE_DIAGNOSTICS": None}}
        resp_del = await async_client.patch(
            f"/api/v1/users/{target_user_id}/feature-flags",
            json=del_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "01928900-0000-7000-8000-000000000255",
            },
        )
        assert resp_del.status_code == 200
        assert "LIVE_DIAGNOSTICS" not in resp_del.json()["feature_flags_override"]

        # 3. Validar error 400 ante clave desconocida
        resp_bad = await async_client.patch(
            f"/api/v1/users/{target_user_id}/feature-flags",
            json={"feature_flags_override": {"INVALID_FLAG_KEY": "ALLOW"}},
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "01928900-0000-7000-8000-000000000265",
            },
        )
        assert resp_bad.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db_session, None)


def test_user_router_permission_10_flags() -> None:
    """Verifica que el modelo UserRouterPermission contenga los 10 flags granulares."""
    perm = UserRouterPermission(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        can_read=True,
        can_write_layer1=True,
        can_write_layer2=True,
        can_execute_l2_rpc=False,
        can_bulk_edit_l2=False,
        can_export_l2_rsc=True,
        can_execute_diagnostics=True,
        can_trigger_backup=False,
        can_reboot=False,
        bypass_maker_checker=False,
    )
    assert perm.can_read is True
    assert perm.can_write_layer1 is True
    assert perm.can_write_layer2 is True
    assert perm.can_execute_l2_rpc is False
    assert perm.can_bulk_edit_l2 is False
    assert perm.can_export_l2_rsc is True
    assert perm.can_execute_diagnostics is True
    assert perm.can_trigger_backup is False
    assert perm.can_reboot is False
    assert perm.bypass_maker_checker is False
