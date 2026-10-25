# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas Unitarias para el Hito 23.27: Detección de Cierre de Navegador y Período de Gracia de 35s en KeyDB."""

import time
import uuid

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.core.crypto import hash_password
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.redis_layer.sessions import (
    cancel_session_closing,
    create_session,
    is_session_closing,
    mark_session_closing,
    sweep_expired_closing_sessions,
)
from src.workers.session_lifecycle_worker import sweep_all_tenants_closing_sessions
from tests.conftest import FakeAsyncRedis


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
async def test_session_closing_endpoint_success(
    async_client: AsyncClient,
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    session_id, _, _ = await create_session(
        tenant_id=str(sample_tenant.id),
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="192.168.10.50",
        user_agent="Mozilla/5.0 Chrome/130.0",
    )

    token = create_jwt_access_token(
        user_id=str(sample_user.id),
        tenant_id=str(sample_tenant.id),
        tenant_slug=sample_tenant.slug,
        session_id=session_id,
        role=sample_user.role.value,
        all_routers=True,
    )

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post(
        "/api/v1/auth/session-closing",
        json={"session_id": session_id, "client_timestamp": int(time.time() * 1000)},
        headers=headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "GRACE_PERIOD_ACTIVE"
    assert data["ttl_seconds"] == 35
    assert data["session_id"] == session_id

    # Verificar que KeyDB contiene la clave de cierre efímera y el sorted set
    closing_key = f"rg:{sample_tenant.id}:sess_closing:{session_id}"
    assert await fake_redis.exists(closing_key) == 1
    zset_key = f"rg:{sample_tenant.id}:closing_sessions_zset"
    assert session_id in fake_redis.zsets.get(zset_key, {})


@pytest.mark.asyncio
async def test_session_closing_endpoint_cookies_and_raw_body(
    async_client: AsyncClient,
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    session_id, _, _ = await create_session(
        tenant_id=str(sample_tenant.id),
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="192.168.10.51",
        user_agent="Firefox/132.0",
    )

    token = create_jwt_access_token(
        user_id=str(sample_user.id),
        tenant_id=str(sample_tenant.id),
        tenant_slug=sample_tenant.slug,
        session_id=session_id,
        role=sample_user.role.value,
        all_routers=True,
    )

    cookies = {"rg_at": token}
    # Enviar simulando beacon con raw json
    response = await async_client.post(
        "/api/v1/auth/session-closing",
        content=f'{{"session_id": "{session_id}"}}',
        headers={"Content-Type": "application/json"},
        cookies=cookies,
    )

    assert response.status_code == 202
    assert response.json()["status"] == "GRACE_PERIOD_ACTIVE"


@pytest.mark.asyncio
async def test_session_closing_mismatch_session_id_403(
    async_client: AsyncClient,
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    token = create_jwt_access_token(
        user_id=str(sample_user.id),
        tenant_id=str(sample_tenant.id),
        tenant_slug=sample_tenant.slug,
        session_id="session-legitimate-1",
        role=sample_user.role.value,
        all_routers=True,
    )

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post(
        "/api/v1/auth/session-closing",
        json={"session_id": "session-attacker-2"},
        headers=headers,
    )

    assert response.status_code == 403
    assert "no coincide" in response.json()["detail"]


@pytest.mark.asyncio
async def test_session_closing_nonexistent_session_404(
    async_client: AsyncClient,
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    token = create_jwt_access_token(
        user_id=str(sample_user.id),
        tenant_id=str(sample_tenant.id),
        tenant_slug=sample_tenant.slug,
        session_id="session-ghost",
        role=sample_user.role.value,
        all_routers=True,
    )

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post(
        "/api/v1/auth/session-closing",
        json={"session_id": "session-ghost"},
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_cancel_and_is_session_closing(
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    tid = str(sample_tenant.id)
    sid, _, _ = await create_session(
        tenant_id=tid,
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="127.0.0.1",
        user_agent="Agent",
    )

    assert await is_session_closing(tid, sid) is False

    # Marcar cierre con 35s
    marked = await mark_session_closing(tid, sid, grace_seconds=35)
    assert marked is True
    assert await is_session_closing(tid, sid) is True

    # Cancelar cierre
    cancelled = await cancel_session_closing(tid, sid)
    assert cancelled is True
    assert await is_session_closing(tid, sid) is False


@pytest.mark.asyncio
async def test_reactive_cancel_on_authenticated_request(
    async_client: AsyncClient,
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    tid = str(sample_tenant.id)
    sid, _, _ = await create_session(
        tenant_id=tid,
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="127.0.0.1",
        user_agent="Agent",
    )

    # 1. Marcar como cerrando
    await mark_session_closing(tid, sid, grace_seconds=35)
    assert await is_session_closing(tid, sid) is True

    # 2. El usuario recarga la página o abre una pestaña (petición autenticada a /api/v1/auth/me)
    token = create_jwt_access_token(
        user_id=str(sample_user.id),
        tenant_id=tid,
        tenant_slug=sample_tenant.slug,
        session_id=sid,
        role=sample_user.role.value,
        all_routers=True,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200

    # 3. La gracia debe haber sido cancelada reactivamente
    assert await is_session_closing(tid, sid) is False
    zset_key = f"rg:{tid}:closing_sessions_zset"
    assert sid not in fake_redis.zsets.get(zset_key, {})


@pytest.mark.asyncio
async def test_sweep_expired_closing_sessions_purges_session(
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    tid = str(sample_tenant.id)
    sid, _, _ = await create_session(
        tenant_id=tid,
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="127.0.0.1",
        user_agent="Agent",
    )

    # Marcar sesión y forzar vencimiento en el zset
    await mark_session_closing(tid, sid, grace_seconds=35)
    # Simular expiración de TTL de la clave efímera borrándola
    closing_key = f"rg:{tid}:sess_closing:{sid}"
    await fake_redis.delete(closing_key)

    # Forzar score en el pasado
    zset_key = f"rg:{tid}:closing_sessions_zset"
    fake_redis.zsets[zset_key][sid] = float(time.time() - 10)

    # Ejecutar barrido
    purged = await sweep_expired_closing_sessions(tid)
    assert sid in purged

    # La sesión debe haber sido purgada de Redis
    sess_key = f"rg:{tid}:sess:{sid}"
    assert await fake_redis.exists(sess_key) == 0


@pytest.mark.asyncio
async def test_session_lifecycle_worker_sweep(
    sample_tenant: Tenant,
    sample_user: User,
    fake_redis: FakeAsyncRedis,
) -> None:
    tid = str(sample_tenant.id)
    sid, _, _ = await create_session(
        tenant_id=tid,
        user_id=str(sample_user.id),
        username=sample_user.username,
        full_name=sample_user.full_name,
        role=sample_user.role.value,
        ip_address="127.0.0.1",
        user_agent="Agent",
    )

    await mark_session_closing(tid, sid, grace_seconds=35)
    closing_key = f"rg:{tid}:sess_closing:{sid}"
    await fake_redis.delete(closing_key)
    zset_key = f"rg:{tid}:closing_sessions_zset"
    fake_redis.zsets[zset_key][sid] = float(time.time() - 5)

    total = await sweep_all_tenants_closing_sessions()
    assert total >= 1
