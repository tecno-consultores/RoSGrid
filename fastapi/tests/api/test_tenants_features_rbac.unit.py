# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_db_session
from src.main import app
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.models.operations import AuditLog
from tests.conftest import FakeAsyncRedis


class MockDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class MockDbResult:
    def __init__(self, item: Any = None, items: list[Any] | None = None):
        self._item = item
        self._items = items or ([item] if item is not None else [])

    def scalar_one_or_none(self) -> Any:
        return self._item

    def scalar_one(self) -> Any:
        if self._item is None:
            raise ValueError("No item found")
        return self._item

    def scalars(self) -> MockDbScalars:
        return MockDbScalars(self._items)


class MockDbSession:
    def __init__(
        self,
        tenants: list[Tenant] | None = None,
        users: list[User] | None = None,
        audit_logs: list[AuditLog] | None = None,
    ):
        self.tenants = tenants or []
        self.users = users or []
        self.audit_logs = audit_logs or []
        self.added: list[Any] = []
        self.committed = False

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> MockDbResult:
        stmt_str = str(stmt).lower()
        if "from audit_logs" in stmt_str or "auditlog" in stmt_str:
            return MockDbResult(self.audit_logs[0] if self.audit_logs else None, self.audit_logs)
        if "from tenants" in stmt_str:
            item = self.tenants[0] if self.tenants else None
            return MockDbResult(item, self.tenants)
        if "from users" in stmt_str:
            item = self.users[0] if self.users else None
            return MockDbResult(item, self.users)
        return MockDbResult(None, [])

    def add(self, instance: Any) -> None:
        now = datetime.now(UTC)
        if getattr(instance, "id", None) is None:
            instance.id = uuid.uuid4()
        if getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if getattr(instance, "is_locked", None) is None:
            instance.is_locked = False
        if getattr(instance, "status", None) is None and hasattr(instance, "status"):
            instance.status = TenantStatusEnum.ACTIVE
        self.added.append(instance)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid.uuid4()
            if getattr(item, "created_at", None) is None:
                item.created_at = now

    async def commit(self) -> None:
        self.committed = True
        await self.flush()

    async def refresh(self, instance: Any) -> None:
        pass

    async def rollback(self) -> None:
        pass


@pytest.fixture
def superadmin_auth(fake_redis: FakeAsyncRedis) -> dict[str, str]:
    sa_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    session_id = "sess-sa-001"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    import asyncio

    asyncio.get_event_loop().run_until_complete(
        fake_redis.hset(
            sess_key,
            mapping={
                "session_id": session_id,
                "user_id": sa_id,
                "username": "superadmin",
                "role": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
            },
        )
    )

    token = create_jwt_access_token(
        sa_id, tenant_id, "global", session_id, SystemRoleEnum.SUPERADMIN_GLOBAL.value, True
    )
    return {"Authorization": f"Bearer {token}", "tid": tenant_id, "sub": sa_id, "sid": session_id}


@pytest.mark.asyncio
async def test_tenant_features_rbac_superadmin_only_and_audit(
    async_client: AsyncClient,
    superadmin_auth: dict[str, str],
    fake_redis: FakeAsyncRedis,
) -> None:
    """Verifica que solo SUPERADMIN_GLOBAL pueda modificar módulos B2B (Hito 26.2),

    mientras que TENANT_ADMIN u operadores reciben 403 Forbidden.
    Verifica también el registro y consulta WORM de auditoría (Hito 26.4).
    """
    tenant_id = uuid.uuid4()
    t = Tenant()
    t.id = tenant_id
    t.name = "Empresa B2B Telecom"
    t.slug = "telecom-b2b"
    t.is_locked = False
    t.status = TenantStatusEnum.ACTIVE
    t.isp_module_enabled = True
    t.bgp_looking_glass_enabled = False
    t.sla_tracker_enabled = False
    t.syslog_collector_enabled = True
    t.default_locale = "es"

    # Log de auditoría previo para probar consulta forense
    audit_rec = AuditLog()
    audit_rec.id = uuid.uuid4()
    audit_rec.tenant_id = tenant_id
    audit_rec.actor_user_id = uuid.uuid4()
    audit_rec.actor_username = "superadmin"
    audit_rec.actor_role = "SUPERADMIN_GLOBAL"
    audit_rec.actor_ip = "127.0.0.1"
    audit_rec.event_category = "SECURITY"
    audit_rec.event_action = "TENANT_FEATURE_FLAGS_UPDATED"
    audit_rec.status_code = 200
    audit_rec.created_at = datetime.now(UTC)
    audit_rec.before_state = {"isp_module_enabled": False, "bgp_looking_glass_enabled": False}
    audit_rec.after_state = {"isp_module_enabled": True, "bgp_looking_glass_enabled": False}
    audit_rec.record_sha256_hash = "abcdef0123456789"

    db = MockDbSession(tenants=[t], audit_logs=[audit_rec])
    app.dependency_overrides[get_db_session] = lambda: db

    try:
        # 1. Configurar tokens para TENANT_ADMIN y NOC_OPERATOR del mismo tenant
        tenant_admin_id = str(uuid.uuid4())
        tenant_admin_sess = "sess-tadmin-001"
        await fake_redis.hset(
            f"rg:{tenant_id}:sess:{tenant_admin_sess}",
            mapping={
                "session_id": tenant_admin_sess,
                "user_id": tenant_admin_id,
                "username": "admin_empresa",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
        )
        token_tenant_admin = create_jwt_access_token(
            tenant_admin_id,
            str(tenant_id),
            "telecom-b2b",
            tenant_admin_sess,
            SystemRoleEnum.TENANT_ADMIN.value,
            True,
        )

        noc_op_id = str(uuid.uuid4())
        noc_op_sess = "sess-noc-001"
        await fake_redis.hset(
            f"rg:{tenant_id}:sess:{noc_op_sess}",
            mapping={
                "session_id": noc_op_sess,
                "user_id": noc_op_id,
                "username": "support_l1",
                "role": SystemRoleEnum.SUPPORT_L1.value,
            },
        )
        token_noc_op = create_jwt_access_token(
            noc_op_id,
            str(tenant_id),
            "telecom-b2b",
            noc_op_sess,
            SystemRoleEnum.SUPPORT_L1.value,
            True,
        )

        patch_body = {
            "isp_module_enabled": True,
            "bgp_looking_glass_enabled": True,
            "sla_tracker_enabled": True,
        }

        # 2. Intento de modificación por TENANT_ADMIN -> HTTP 403 FORBIDDEN
        res_tadmin = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json=patch_body,
            headers={
                "Authorization": f"Bearer {token_tenant_admin}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        assert res_tadmin.status_code == 403, f"Expected 403, got {res_tadmin.status_code}"

        # 3. Intento de modificación por SUPPORT_L1 -> HTTP 403 FORBIDDEN
        res_noc = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json=patch_body,
            headers={
                "Authorization": f"Bearer {token_noc_op}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        assert res_noc.status_code == 403

        # 4. Modificación autorizada por SUPERADMIN_GLOBAL -> HTTP 200 OK
        res_super = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json=patch_body,
            headers={
                **superadmin_auth,
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        assert res_super.status_code == 200
        data_super = res_super.json()
        assert data_super["bgp_looking_glass_enabled"] is True
        assert data_super["sla_tracker_enabled"] is True

        # 5. Consulta WORM de auditoría por SUPERADMIN_GLOBAL -> HTTP 200 OK
        res_audit_super = await async_client.get(
            f"/api/v1/tenants/{tenant_id}/features/audit",
            headers=superadmin_auth,
        )
        assert res_audit_super.status_code == 200
        audit_data = res_audit_super.json()
        assert len(audit_data) >= 1
        assert audit_data[0]["event_action"] == "TENANT_FEATURE_FLAGS_UPDATED"
        assert audit_data[0]["record_sha256_hash"] == "abcdef0123456789"

        # 6. Consulta WORM de auditoría por TENANT_ADMIN de su propia empresa -> HTTP 200 OK
        res_audit_tadmin = await async_client.get(
            f"/api/v1/tenants/{tenant_id}/features/audit",
            headers={"Authorization": f"Bearer {token_tenant_admin}"},
        )
        assert res_audit_tadmin.status_code == 200
        assert len(res_audit_tadmin.json()) >= 1

        # 7. Consulta WORM de auditoría por usuario de otra empresa -> HTTP 403 FORBIDDEN
        other_tenant_id = uuid.uuid4()
        other_sess = "sess-other-99"
        await fake_redis.hset(
            f"rg:{other_tenant_id}:sess:{other_sess}",
            mapping={
                "session_id": other_sess,
                "user_id": str(uuid.uuid4()),
                "username": "other_admin",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
        )
        token_other = create_jwt_access_token(
            str(uuid.uuid4()),
            str(other_tenant_id),
            "other-corp",
            other_sess,
            SystemRoleEnum.TENANT_ADMIN.value,
            True,
        )
        res_audit_forbidden = await async_client.get(
            f"/api/v1/tenants/{tenant_id}/features/audit",
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert res_audit_forbidden.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db_session, None)
