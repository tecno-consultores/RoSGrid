# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import time
import uuid
from datetime import UTC, datetime
from typing import Any

import pyotp
import pytest
from httpx import AsyncClient

from src.core.crypto import encrypt_aes_gcm, hash_password
from src.db.session import get_db_session
from src.main import app
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from tests.conftest import FakeAsyncRedis


class MockDbResult:
    def __init__(self, item: Any = None):
        self._item = item

    def scalar_one_or_none(self) -> Any:
        return self._item

    def scalar_one(self) -> Any:
        if self._item is None:
            raise ValueError("No item found")
        return self._item


class MockAsyncSession:
    def __init__(self, tenant: Tenant | None = None, user: User | None = None):
        self.tenant = tenant
        self.user = user
        self.committed = False

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> MockDbResult:
        stmt_str = str(stmt).lower()
        if "from tenants" in stmt_str:
            return MockDbResult(self.tenant)
        if "from users" in stmt_str:
            return MockDbResult(self.user)
        return MockDbResult(None)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


@pytest.fixture
def sample_tenant() -> Tenant:
    t = Tenant()
    t.id = uuid.uuid4()
    t.slug = "acme-corp"
    t.name = "Acme Corporation"
    t.status = TenantStatusEnum.ACTIVE
    return t


@pytest.fixture
def sample_user(sample_tenant: Tenant) -> User:
    u = User()
    u.id = uuid.uuid4()
    u.tenant_id = sample_tenant.id
    u.username = "netadmin"
    u.email = "admin@acme.com"
    u.full_name = "Network Admin"
    u.password_hash = hash_password("ValidPassword2026!")
    u.role = SystemRoleEnum.TENANT_ADMIN
    u.is_active = True
    u.is_locked = False
    u.failed_login_attempts = 0
    u.locked_until = None
    u.totp_enabled = False
    u.has_all_routers_access = True
    return u


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient) -> None:
    res = await async_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rosgrid-api"


@pytest.mark.asyncio
async def test_login_unknown_tenant(async_client: AsyncClient) -> None:
    session = MockAsyncSession(tenant=None, user=None)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": "unknown-org", "email": "a@a.com", "password": "pass"},
        )
        assert res.status_code == 401
        assert "Credenciales inválidas" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_unknown_user(async_client: AsyncClient, sample_tenant: Tenant) -> None:
    session = MockAsyncSession(tenant=sample_tenant, user=None)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": "unknown@acme.com", "password": "pass"},
        )
        assert res.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_account_locked(async_client: AsyncClient, sample_tenant: Tenant, sample_user: User) -> None:
    sample_user.is_locked = True
    sample_user.locked_until = datetime.fromtimestamp(time.time() + 600, UTC)

    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "pass"},
        )
        assert res.status_code == 423
        assert "Cuenta bloqueada" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_failed_attempts_boundary_4_and_5(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User
) -> None:
    # Intento 4: no se debe bloquear aún
    sample_user.failed_login_attempts = 3
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res.status_code == 401
        assert sample_user.failed_login_attempts == 4
        assert sample_user.is_locked is False

        # Intento 5 (Límite exacto de bloqueo: >= 5)
        res2 = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res2.status_code == 401
        assert sample_user.failed_login_attempts == 5
        assert sample_user.is_locked is True
        assert sample_user.locked_until is not None
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_success_triggers_enroll_2fa(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    sample_user.totp_enabled = False
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "ValidPassword2026!"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_step"] == "ENROLL_2FA_REQUIRED"
        assert data["totp_provisioning_uri"] is not None
        assert "otpauth://" in data["totp_provisioning_uri"]

        # Verificar que el pre-auth challenge fue guardado en Redis
        challenge_id = data["challenge_id"]
        preauth = await fake_redis.hgetall(f"rg:{sample_tenant.id}:preauth:{challenge_id}")
        assert preauth["user_id"] == str(sample_user.id)
        assert preauth["status"] == "ENROLL_2FA_REQUIRED"
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_success_triggers_verify_2fa(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    sample_user.totp_enabled = True
    sample_user.totp_secret_ciphertext = "encrypted_secret_data"
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "ValidPassword2026!"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_step"] == "VERIFY_2FA_TOTP"
        assert data["totp_provisioning_uri"] is None

        # Verify challenge in Redis
        challenge_id = data["challenge_id"]
        preauth = await fake_redis.hgetall(f"rg:{sample_tenant.id}:preauth:{challenge_id}")
        assert preauth["user_id"] == str(sample_user.id)
        assert preauth["status"] == "VERIFY_2FA_TOTP"
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_verify_2fa_enrollment_lifecycle(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        # 1. Simular preauth en Redis para enrolamiento
        challenge_id = "test-challenge-1"
        secret = pyotp.random_base32()
        preauth_key = f"rg:{sample_tenant.id}:preauth:{challenge_id}"
        await fake_redis.hset(
            preauth_key,
            mapping={
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "tenant_slug": sample_tenant.slug,
                "status": "ENROLL_2FA_REQUIRED",
                "temp_totp_secret": secret,
            },
        )

        # 2. Código TOTP erróneo -> 401
        bad_res = await async_client.post(
            "/api/v1/auth/2fa/verify",
            json={"challenge_id": challenge_id, "totp_code": "000000"},
        )
        assert bad_res.status_code == 401

        # 3. Código TOTP correcto -> 200, guarda secreto cifrado con AES-GCM
        valid_code = pyotp.TOTP(secret).now()
        good_res = await async_client.post(
            "/api/v1/auth/2fa/verify",
            json={"challenge_id": challenge_id, "totp_code": valid_code},
        )
        assert good_res.status_code == 200
        data = good_res.json()
        assert "session_id" in data
        assert data["user"]["email"] == sample_user.email
        assert sample_user.totp_enabled is True
        assert sample_user.totp_secret_ciphertext is not None
        assert sample_user.totp_secret_iv is not None
        assert sample_user.totp_secret_tag is not None

        # Cookies deben haberse establecido en la respuesta
        cookies = good_res.cookies
        assert "rg_at" in cookies or "__Host-rg_at" in cookies
        assert "rg_csrf" in cookies
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_verify_2fa_verification_lifecycle(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    # Configurar usuario con 2FA ya activo y secreto cifrado en la BD
    raw_secret = pyotp.random_base32()
    aad = f"{sample_tenant.id}:{sample_user.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(raw_secret.encode("utf-8"), aad)
    sample_user.totp_enabled = True
    sample_user.totp_secret_ciphertext = ct
    sample_user.totp_secret_iv = iv
    sample_user.totp_secret_tag = tag

    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        challenge_id = "test-challenge-verify"
        preauth_key = f"rg:{sample_tenant.id}:preauth:{challenge_id}"
        await fake_redis.hset(
            preauth_key,
            mapping={
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "tenant_slug": sample_tenant.slug,
                "status": "VERIFY_2FA_TOTP",
            },
        )

        valid_code = pyotp.TOTP(raw_secret).now()
        res = await async_client.post(
            "/api/v1/auth/2fa/verify",
            json={"challenge_id": challenge_id, "totp_code": valid_code},
        )
        assert res.status_code == 200
        assert res.json()["user"]["username"] == sample_user.username
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_auth_me_and_users_me_alias(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    session_id = "sess-me-123"
    sess_key = f"rg:{sample_tenant.id}:sess:{session_id}"
    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": str(sample_user.id),
            "username": sample_user.username,
            "role": sample_user.role.value,
        },
    )

    from src.api.v1.auth import create_jwt_access_token

    token = create_jwt_access_token(
        str(sample_user.id),
        str(sample_tenant.id),
        sample_tenant.slug,
        session_id,
        sample_user.role.value,
        True,
    )

    headers = {"Authorization": f"Bearer {token}"}

    # Probar /api/v1/auth/me
    res_me = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["sub"] == str(sample_user.id)

    # Probar alias /users/me para compatibilidad con Karate Labs
    res_alias = await async_client.get("/users/me", headers=headers)
    assert res_alias.status_code == 200
    assert res_alias.json()["sub"] == str(sample_user.id)


@pytest.mark.asyncio
async def test_auth_logout(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    session_id = "sess-logout-123"
    sess_key = f"rg:{sample_tenant.id}:sess:{session_id}"
    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": str(sample_user.id),
            "username": sample_user.username,
            "role": sample_user.role.value,
        },
    )

    from src.api.v1.auth import create_jwt_access_token

    token = create_jwt_access_token(
        str(sample_user.id),
        str(sample_tenant.id),
        sample_tenant.slug,
        session_id,
        sample_user.role.value,
        True,
    )

    headers = {"Authorization": f"Bearer {token}"}
    res = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert res.status_code == 204

    # Sesión eliminada de Redis
    assert await fake_redis.hgetall(sess_key) == {}


@pytest.mark.asyncio
async def test_refresh_token_missing_cookies(async_client: AsyncClient) -> None:
    res = await async_client.post("/api/v1/auth/refresh")
    assert res.status_code == 401
    assert "Cookie de Refresh Token ausente" in res.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_success_and_reuse(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User, fake_redis: FakeAsyncRedis
) -> None:
    from src.api.v1.auth import create_jwt_access_token
    from src.redis_layer.sessions import create_session

    session_id, _family_id, initial_rt = await create_session(
        str(sample_tenant.id),
        str(sample_user.id),
        sample_user.username,
        sample_user.full_name,
        sample_user.role.value,
        "127.0.0.1",
        "TestAgent",
    )
    at = create_jwt_access_token(
        str(sample_user.id),
        str(sample_tenant.id),
        sample_tenant.slug,
        session_id,
        sample_user.role.value,
        True,
    )
    cookies = {"rg_rt": initial_rt, "rg_at": at}
    res = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert res.status_code == 200
    assert res.json()["status"] == "refreshed"

    # Reuse attack: reutilizar el token anterior 'initial_rt'
    res_reuse = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert res_reuse.status_code == 401
    assert "Fallo de rotación" in res_reuse.json()["detail"]


@pytest.mark.asyncio
async def test_verify_2fa_invalid_scenarios(async_client: AsyncClient, fake_redis: FakeAsyncRedis) -> None:
    res = await async_client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": "non-existent-challenge", "totp_code": "123456"},
    )
    assert res.status_code == 401
    assert "inválido o expirado" in res.json()["detail"]


@pytest.mark.asyncio
async def test_auth_deps_failure_scenarios(async_client: AsyncClient) -> None:
    # 1. Sin token
    res = await async_client.get("/users/me")
    assert res.status_code == 401

    # 2. Token inválido
    res_inv = await async_client.get("/users/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert res_inv.status_code == 401

    # 3. Esquema no Bearer
    res_bad = await async_client.get("/users/me", headers={"Authorization": "Basic 12345"})
    assert res_bad.status_code == 401
