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

    async def delete(self, instance: Any) -> None:
        if instance in self.users:
            self.users.remove(instance)
        if instance in self.tenants:
            self.tenants.remove(instance)

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


@pytest.mark.asyncio
async def test_tenant_features_endpoints(
    async_client: AsyncClient, superadmin_auth: dict[str, str], fake_redis: FakeAsyncRedis
) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    tenant_id = uuid.uuid4()
    t = Tenant()
    t.id = tenant_id
    t.slug = "corp-features"
    t.name = "Corp Features"
    t.status = TenantStatusEnum.ACTIVE
    t.isp_module_enabled = True
    t.bgp_looking_glass_enabled = False
    t.sfp_ddm_telemetry_enabled = True
    t.ipfix_analytics_enabled = False
    t.enforce_maker_checker = True
    t.auto_safemode_enforced = True
    t.ai_mcp_integration_enabled = True
    t.nightly_backups_enabled = True
    t.outbound_webhooks_enabled = True
    t.config_drift_monitoring_enabled = False
    t.cis_audit_enabled = True
    t.sdwan_orchestrator_enabled = False
    t.capsman_wifi_enabled = False
    t.sla_tracker_enabled = False
    t.mass_outage_threshold = 10
    t.default_locale = "es"

    db = MockDbSession(tenants=[t])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        # 1. Superadmin GET features -> 200
        res_get = await async_client.get(f"/api/v1/tenants/{tenant_id}/features", headers=headers)
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert data_get["isp_module_enabled"] is True
        assert data_get["bgp_looking_glass_enabled"] is False
        assert data_get["mass_outage_threshold"] == 10
        assert data_get["default_locale"] == "es"

        # 2. Superadmin PATCH features -> 200
        patch_body = {
            "isp_module_enabled": False,
            "bgp_looking_glass_enabled": True,
            "mass_outage_threshold": 25,
            "default_locale": "en",
        }
        res_patch = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json=patch_body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_patch.status_code == 200, f"res_patch failed: {res_patch.status_code} - {res_patch.text}"
        data_patch = res_patch.json()
        assert data_patch["isp_module_enabled"] is False
        assert data_patch["bgp_looking_glass_enabled"] is True
        assert data_patch["mass_outage_threshold"] == 25
        assert data_patch["default_locale"] == "en"

        # 3. GET / PATCH 404 si tenant no existe
        db_empty = MockDbSession(tenants=[])
        app.dependency_overrides[get_db_session] = lambda: db_empty
        res_nf_get = await async_client.get(f"/api/v1/tenants/{uuid.uuid4()}/features", headers=headers)
        assert res_nf_get.status_code == 404

        res_nf_patch = await async_client.patch(
            f"/api/v1/tenants/{uuid.uuid4()}/features",
            json=patch_body,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_nf_patch.status_code == 404

        # 4. GET 403 para usuario no superadmin de otro tenant
        other_tenant_id = uuid.uuid4()
        other_user_id = str(uuid.uuid4())
        other_sess_id = "sess-other-001"
        await fake_redis.hset(
            f"rg:{other_tenant_id}:sess:{other_sess_id}",
            mapping={
                "session_id": other_sess_id,
                "user_id": other_user_id,
                "username": "nocmonitor",
                "role": SystemRoleEnum.NOC_MONITOR.value,
            },
        )
        other_user_token = create_jwt_access_token(
            other_user_id, str(other_tenant_id), "other-slug", other_sess_id, SystemRoleEnum.NOC_MONITOR.value, True
        )
        app.dependency_overrides[get_db_session] = lambda: db
        res_forbidden = await async_client.get(
            f"/api/v1/tenants/{tenant_id}/features",
            headers={"Authorization": f"Bearer {other_user_token}"},
        )
        assert res_forbidden.status_code == 403, (
            f"res_forbidden failed: {res_forbidden.status_code} - {res_forbidden.text}"
        )

        # 5. PATCH con payload inválido (locale no soportado) -> 422
        res_invalid = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json={"default_locale": "fr"},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_invalid.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_user_registration_toggle_approve_reject_and_permissions(
    async_client: AsyncClient, superadmin_auth: dict[str, str], fake_redis: FakeAsyncRedis
) -> None:
    headers = {"Authorization": superadmin_auth["Authorization"]}
    tid = uuid.UUID(superadmin_auth["tid"])

    # 1. Toggle public registration
    res_toggle = await async_client.post(
        "/api/v1/users/registration-toggle",
        json={"enabled": True},
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res_toggle.status_code == 200
    assert res_toggle.json()["registration_enabled"] is True

    # 2. Approve user
    target_user = User()
    target_user.id = uuid.uuid4()
    target_user.tenant_id = tid
    target_user.username = "pending_worker"
    target_user.email = "worker@acme.com"
    target_user.full_name = "Pending Worker"
    target_user.is_active = False
    target_user.is_locked = False
    target_user.failed_login_attempts = 0
    target_user.totp_enabled = False
    target_user.created_at = datetime.now(UTC)
    target_user.updated_at = datetime.now(UTC)

    db = MockDbSession(users=[target_user])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        res_approve = await async_client.put(
            f"/api/v1/users/{target_user.id}/approve",
            json={"role": SystemRoleEnum.NOC_MONITOR.value, "has_all_routers_access": True, "allowed_cidr_list": []},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_approve.status_code == 200
        assert res_approve.json()["is_active"] is True

        # 3. Get user permissions
        res_perms = await async_client.get(
            f"/api/v1/users/{target_user.id}/router-permissions",
            headers=headers,
        )
        assert res_perms.status_code == 200

        # 4. Reject user
        res_reject = await async_client.delete(
            f"/api/v1/users/{target_user.id}/reject",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_reject.status_code == 204
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_tenant_admin_cannot_escalate_to_superadmin(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis
) -> None:
    tid = uuid.uuid4()
    admin_id = uuid.uuid4()
    session_id = "sess-ta-001"
    await fake_redis.hset(
        f"rg:{tid}:sess:{session_id}",
        mapping={
            "session_id": session_id,
            "user_id": str(admin_id),
            "username": "tenant_admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )
    # Generar token con rol TENANT_ADMIN (no superadmin)
    token = create_jwt_access_token(
        str(admin_id),
        str(tid),
        "acme",
        session_id,
        SystemRoleEnum.TENANT_ADMIN.value,
        True,
    )
    headers = {"Authorization": f"Bearer {token}"}

    target_user = User()
    target_user.id = uuid.uuid4()
    target_user.tenant_id = tid
    target_user.username = "target_worker"
    target_user.email = "target@acme.com"
    target_user.full_name = "Target Worker"
    target_user.is_active = False
    target_user.is_locked = False
    target_user.failed_login_attempts = 0
    target_user.totp_enabled = False
    target_user.created_at = datetime.now(UTC)
    target_user.updated_at = datetime.now(UTC)

    db = MockDbSession(users=[target_user])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        # Intento de aprobar con SUPERADMIN_GLOBAL
        res_approve = await async_client.put(
            f"/api/v1/users/{target_user.id}/approve",
            json={
                "role": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
                "has_all_routers_access": True,
                "allowed_cidr_list": [],
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_approve.status_code == 403
        assert "SUPERADMIN_GLOBAL" in res_approve.json()["detail"]

        # Intento de crear usuario con SUPERADMIN_GLOBAL
        res_create = await async_client.post(
            "/api/v1/users",
            json={
                "username": "escalated_admin",
                "email": "escalated@acme.com",
                "full_name": "Escalated Admin",
                "password": "ComplexPassword123!",
                "role": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_create.status_code == 403
        assert "SUPERADMIN_GLOBAL" in res_create.json()["detail"]

        # Intento de enviar campo extra en approve
        res_extra = await async_client.put(
            f"/api/v1/users/{target_user.id}/approve",
            json={
                "role": SystemRoleEnum.SUPPORT_L1.value,
                "is_superadmin": True,
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_extra.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_generate_user_mcp_token_success(
    async_client: AsyncClient, superadmin_auth: dict[str, str], fake_redis: FakeAsyncRedis
) -> None:
    tid = uuid.uuid4()
    user_id = uuid.uuid4()
    tenant = Tenant(id=tid, name="ISP Alpha", slug="isp-alpha", status=TenantStatusEnum.ACTIVE)
    sa_user = User(
        id=user_id,
        tenant_id=tid,
        username="mcp_daemon",
        email="mcp@isp.test",
        full_name="MCP Daemon Agent",
        password_hash="argon2_hash",
        role=SystemRoleEnum.SERVICE_ACCOUNT,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=False,
        has_all_routers_access=True,
        allowed_cidr_list=["192.168.1.100/32"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db = MockDbSession(tenants=[tenant], users=[sa_user])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        res = await async_client.post(
            f"/api/v1/users/{user_id}/mcp-token",
            json={"expiry_days": 180},
            headers={**superadmin_auth, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["token_type"] == "Bearer"
        assert len(data["token"]) > 30
        assert data["username"] == "mcp_daemon"
        assert data["tenant_slug"] == "isp-alpha"
        assert data["role"] == "SERVICE_ACCOUNT"
        assert data["expiry_days"] == 180
        assert data["allowed_cidr_list"] == ["192.168.1.100/32"]
        assert "issued_by" in data

        # Verificar que la sesión se registró en Redis y en active_sessions
        session_id = data["session_id"]
        sess_key = f"rg:{tid}:sess:{session_id}"
        sess_redis = await fake_redis.hgetall(sess_key)
        assert sess_redis["is_service_account"] == "true"
        assert sess_redis["role"] == "SERVICE_ACCOUNT"

        active_sessions = await fake_redis.zrange(f"rg:{tid}:active_sessions", 0, -1)
        assert session_id in active_sessions
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_generate_user_mcp_token_rejects_unauthorized_role(
    async_client: AsyncClient, superadmin_auth: dict[str, str], fake_redis: FakeAsyncRedis
) -> None:
    tid = uuid.uuid4()
    user_id = uuid.uuid4()
    tenant = Tenant(id=tid, name="ISP Alpha", slug="isp-alpha", status=TenantStatusEnum.ACTIVE)
    support_user = User(
        id=user_id,
        tenant_id=tid,
        username="tech_l1",
        email="tech@isp.test",
        full_name="Tech L1",
        password_hash="argon2_hash",
        role=SystemRoleEnum.SUPPORT_L1,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=False,
        has_all_routers_access=False,
        allowed_cidr_list=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db = MockDbSession(tenants=[tenant], users=[support_user])
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        res = await async_client.post(
            f"/api/v1/users/{user_id}/mcp-token",
            json={"expiry_days": 30},
            headers={**superadmin_auth, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 400
        assert "roles permitidos" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)
