# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import time
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.core.crypto import hash_password
from src.db.session import get_db_session
from src.main import app
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
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
    def __init__(self, tenants: list[Tenant] | None = None, users: list[User] | None = None):
        self.tenants = tenants or []
        self.users = users or []
        self.added: list[Any] = []
        self.committed = False

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> MockDbResult:
        stmt_str = str(stmt).lower()
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
            if getattr(item, "updated_at", None) is None:
                item.updated_at = now
            if getattr(item, "is_locked", None) is None:
                item.is_locked = False
            if getattr(item, "status", None) is None and hasattr(item, "status"):
                item.status = TenantStatusEnum.ACTIVE

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    async def refresh(self, instance: Any) -> None:
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
async def test_tenants_crud_endpoints(async_client: AsyncClient, superadmin_auth: dict[str, str]) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    t = Tenant()
    t.id = uuid.uuid4()
    t.slug = "corp-1"
    t.name = "Corp One"
    t.status = TenantStatusEnum.ACTIVE
    t.max_routers_quota = 50
    t.max_users_quota = 20
    t.require_2fa_all_users = True
    t.default_safemode_seconds = 60
    now = datetime.now(UTC)
    t.created_at = now
    t.updated_at = now

    # 1. Listar tenants
    db = MockDbSession(tenants=[t])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        res = await async_client.get("/api/v1/tenants", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1

        # 2. Crear nuevo tenant (db vacío para no conflicto de slug)
        db_empty = MockDbSession(tenants=[])
        app.dependency_overrides[get_db_session] = lambda: db_empty
        body_create = {
            "slug": "new-tenant",
            "name": "New Tenant SA",
            "max_routers_quota": 20,
            "max_users_quota": 5,
            "require_2fa_all_users": True,
            "default_safemode_seconds": 60,
            "admin_username": "orgadmin",
            "admin_email": "admin@newtenant.com",
            "admin_full_name": "Org Administrator",
            "admin_password": "InitialSecurePass2026!",
        }
        idemp_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        res_create = await async_client.post("/api/v1/tenants", json=body_create, headers=idemp_headers)
        assert res_create.status_code == 201

        # 3. Modificar tenant
        app.dependency_overrides[get_db_session] = lambda: db
        patch_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        res_patch = await async_client.patch(
            f"/api/v1/tenants/{t.id}",
            json={"name": "Corp One Updated"},
            headers=patch_headers,
        )
        assert res_patch.status_code == 200
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_users_endpoints(async_client: AsyncClient, superadmin_auth: dict[str, str]) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    u = User()
    u.id = uuid.uuid4()
    u.tenant_id = uuid.UUID(superadmin_auth["tid"])
    u.username = "tech1"
    u.email = "tech1@acme.com"
    u.full_name = "Field Technician"
    u.password_hash = hash_password("Secret123!")
    u.role = SystemRoleEnum.FIELD_TECH
    u.is_active = True
    u.is_locked = False
    u.totp_enabled = True
    u.has_all_routers_access = False
    u.failed_login_attempts = 0
    u.allowed_cidr_list = []
    now = datetime.now(UTC)
    u.created_at = now
    u.updated_at = now
    u.last_login_at = None

    db = MockDbSession(users=[u])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        # 1. Listar usuarios
        res = await async_client.get("/api/v1/users", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1

        # 2. Reset 2FA de usuario
        idemp_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        res_reset = await async_client.post(
            f"/api/v1/users/{u.id}/reset-2fa",
            json={"admin_totp_code": "123456"},
            headers=idemp_headers,
        )
        assert res_reset.status_code == 200
        assert res_reset.json()["status"] == "2fa_reset_completed"
        assert u.totp_enabled is False

        # 3. Crear usuario usando alias password
        db_create = MockDbSession(users=[])
        app.dependency_overrides[get_db_session] = lambda: db_create
        body_user = {
            "username": "operador_l2",
            "email": "l2@acme.com",
            "full_name": "Operador Nivel 2",
            "password": "PasswordSegura123!",
            "role": "SUPPORT_L2",
            "has_all_routers_access": False,
            "allowed_cidr_list": [],
        }
        res_create = await async_client.post(
            "/api/v1/users",
            json=body_user,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["username"] == "operador_l2"
        assert data_create["email"] == "l2@acme.com"
        assert data_create["role"] == "SUPPORT_L2"
        assert data_create["is_active"] is True
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_sessions_and_killswitch_endpoints(
    async_client: AsyncClient, superadmin_auth: dict[str, str], fake_redis: FakeAsyncRedis
) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    tid = superadmin_auth["tid"]
    sid = superadmin_auth["sid"]

    # Añadir sesión propia y otra sesión ajena
    other_sid = "sess-other-999"
    await fake_redis.hset(
        f"rg:{tid}:sess:{other_sid}",
        mapping={"session_id": other_sid, "user_id": str(uuid.uuid4()), "username": "other", "role": "FIELD_TECH"},
    )
    await fake_redis.zadd(
        f"rg:{tid}:active_sessions",
        {sid: float(time.time()), other_sid: float(time.time())},
    )

    # 1. Listar sesiones activas
    res = await async_client.get("/api/v1/sessions/active", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_active_sessions"] == 2

    # 2. Terminar una sesión ajena (Kill-Switch)
    idemp_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    res_kill = await async_client.delete(f"/api/v1/sessions/{other_sid}", headers=idemp_headers)
    assert res_kill.status_code == 200
    assert res_kill.json()["status"] == "terminated"

    # 3. Terminar todas las sesiones de otro usuario
    other_user_id = str(uuid.uuid4())
    idemp_headers_all = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    res_kill_all = await async_client.delete(f"/api/v1/sessions/user/{other_user_id}/all", headers=idemp_headers_all)
    assert res_kill_all.status_code == 200
    assert res_kill_all.json()["status"] == "terminated_all"


@pytest.mark.asyncio
async def test_create_user_and_conflicts(async_client: AsyncClient, superadmin_auth: dict[str, str]) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    db_empty = MockDbSession(users=[])
    app.dependency_overrides[get_db_session] = lambda: db_empty
    try:
        # Crear usuario con éxito
        body = {
            "username": "nocoperator",
            "email": "noc@acme.com",
            "full_name": "NOC Operator",
            "temporary_password": "InitialPassword2026!",
            "role": SystemRoleEnum.NOC_MONITOR.value,
            "has_all_routers_access": True,
            "allowed_cidr_list": ["10.0.0.0/8"],
        }
        res = await async_client.post(
            "/api/v1/users",
            json=body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 201
        assert res.json()["username"] == "nocoperator"

        # Conflicto al crear usuario con username existente
        existing_user = User()
        existing_user.id = uuid.uuid4()
        existing_user.tenant_id = uuid.UUID(superadmin_auth["tid"])
        existing_user.username = "nocoperator"
        existing_user.email = "noc@acme.com"
        db_conflict = MockDbSession(users=[existing_user])
        app.dependency_overrides[get_db_session] = lambda: db_conflict
        res_conflict = await async_client.post(
            "/api/v1/users",
            json=body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_conflict.status_code == 409
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_assign_router_permissions_and_not_found(
    async_client: AsyncClient, superadmin_auth: dict[str, str]
) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    u = User()
    u.id = uuid.uuid4()
    u.tenant_id = uuid.UUID(superadmin_auth["tid"])
    u.username = "fieldtech"
    u.email = "tech@acme.com"

    db = MockDbSession(users=[u])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        body = {
            "has_all_routers_access": False,
            "router_assignments": [
                {
                    "router_id": str(uuid.uuid4()),
                    "can_read": True,
                    "can_write_layer1": True,
                    "can_write_layer2": False,
                    "can_execute_diagnostics": True,
                    "can_trigger_backup": True,
                    "can_reboot": False,
                    "bypass_maker_checker": False,
                }
            ],
        }
        res = await async_client.put(
            f"/api/v1/users/{u.id}/router-permissions",
            json=body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # Not found case
        db_empty = MockDbSession(users=[])
        app.dependency_overrides[get_db_session] = lambda: db_empty
        res_nf = await async_client.put(
            f"/api/v1/users/{uuid.uuid4()}/router-permissions",
            json=body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_nf.status_code == 404

        # Reset 2FA not found
        res_reset_nf = await async_client.post(
            f"/api/v1/users/{uuid.uuid4()}/reset-2fa",
            json={"admin_totp_code": "123456"},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_reset_nf.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db_session, None)
