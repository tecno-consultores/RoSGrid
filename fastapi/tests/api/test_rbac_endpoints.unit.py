# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_db_session
from src.main import app
from src.models.core import SystemRoleEnum
from tests.conftest import FakeAsyncRedis


class MockDbSession:
    def __init__(self):
        self.committed = False

    async def execute(self, stmt, params=None):
        class MockResult:
            def scalar_one_or_none(self):
                return None

            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []

                return MockScalars()

        return MockResult()

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_get_rbac_roles_and_actions(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.rbac.get_redis_client", lambda: fake_redis)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-rbac-001"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "superadmin",
            "role": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "global", session_id, SystemRoleEnum.SUPERADMIN_GLOBAL.value, True
    )
    headers = {"Authorization": f"Bearer {token}"}

    app.dependency_overrides[get_db_session] = lambda: MockDbSession()

    try:
        res_roles = await async_client.get("/api/v1/rbac/roles", headers=headers)
        assert res_roles.status_code == 200, res_roles.text
        roles_data = res_roles.json()
        assert len(roles_data) == 11
        roles_map = {r["role"]: r for r in roles_data}
        assert "SUPERADMIN_GLOBAL" in roles_map
        assert "SUPPORT_L2" in roles_map
        assert "FIELD_TECH" in roles_map
        assert "AUDITOR" in roles_map
        assert "SERVICE_ACCOUNT" in roles_map

        # Comprobar metadatos y descripciones detalladas
        assert roles_map["SUPERADMIN_GLOBAL"]["is_system_reserved"] is True
        assert roles_map["SUPPORT_L2"]["is_system_reserved"] is False
        assert "segundo nivel" in roles_map["SUPPORT_L2"]["description"].lower()

        res_actions = await async_client.get("/api/v1/rbac/actions", headers=headers)
        assert res_actions.status_code == 200, res_actions.text
        actions_data = res_actions.json()
        assert len(actions_data) >= 19
        actions_keys = {a["key"] for a in actions_data}
        assert "CRITICAL_NETWORK_ACTIONS" in actions_keys
        assert "WEBFIG_L2_UNIVERSAL" in actions_keys
        assert "TENANT_MANAGEMENT" in actions_keys
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_put_and_reset_role_permissions(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.rbac.get_redis_client", lambda: fake_redis)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-rbac-002"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "admin_tenant",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "tenant-test", session_id, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    app.dependency_overrides[get_db_session] = lambda: MockDbSession()

    try:
        # 1. Modificar permisos de SUPPORT_L2
        headers_put = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid4()),
        }
        payload = {
            "permissions": {
                "CRITICAL_NETWORK_ACTIONS": "ALLOW",
                "WEBFIG_L2_UNIVERSAL": "MAKER_CHECKER",
            }
        }
        res_put = await async_client.put(
            "/api/v1/rbac/roles/SUPPORT_L2/permissions",
            json=payload,
            headers=headers_put,
        )
        assert res_put.status_code == 200, res_put.text
        assert "actualizados exitosamente" in res_put.json()["message"]

        # 2. Consultar roles y verificar que SUPPORT_L2 tiene custom overrides
        res_roles = await async_client.get("/api/v1/rbac/roles", headers={"Authorization": f"Bearer {token}"})
        assert res_roles.status_code == 200, res_roles.text
        roles_map = {r["role"]: r for r in res_roles.json()}
        assert roles_map["SUPPORT_L2"]["has_custom_overrides"] is True
        assert roles_map["SUPPORT_L2"]["permissions"]["CRITICAL_NETWORK_ACTIONS"] == "ALLOW"

        # 3. Intentar modificar rol inmutable SUPERADMIN_GLOBAL debe fallar con 400
        res_super = await async_client.put(
            "/api/v1/rbac/roles/SUPERADMIN_GLOBAL/permissions",
            json={"permissions": {"CRITICAL_NETWORK_ACTIONS": "DENY"}},
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_super.status_code == 403, res_super.text
        assert "inmutable" in res_super.json()["detail"].lower()

        # 4. Restablecer valores de fábrica
        res_reset = await async_client.post(
            "/api/v1/rbac/roles/SUPPORT_L2/reset",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_reset.status_code == 200, res_reset.text
        assert "restaurados" in res_reset.json()["message"]

        # 5. Comprobar que ya no tiene custom overrides
        res_roles_after = await async_client.get("/api/v1/rbac/roles", headers={"Authorization": f"Bearer {token}"})
        roles_after_map = {r["role"]: r for r in res_roles_after.json()}
        assert roles_after_map["SUPPORT_L2"]["has_custom_overrides"] is False
    finally:
        app.dependency_overrides.pop(get_db_session, None)
