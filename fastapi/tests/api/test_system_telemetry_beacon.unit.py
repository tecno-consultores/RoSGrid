# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas de endpoints de diagnóstico y telemetría anónima de instancias activas (Spec 55 / Hito 27.18)."""

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.models.core import SystemRoleEnum
from tests.conftest import FakeAsyncRedis


async def _create_test_session(
    fake_redis: FakeAsyncRedis, role: SystemRoleEnum
) -> tuple[str, dict[str, str]]:
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = f"sess-beacon-{role.value.lower()}"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": f"user_{role.value.lower()}",
            "role": role.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "default-tenant", session_id, role.value, True
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": "test-csrf-token",
    }
    return tenant_id, headers


@pytest.mark.asyncio
async def test_get_telemetry_beacon_status_unauthorized(async_client: AsyncClient) -> None:
    """Verifica que peticiones anónimas sean rechazadas con 401."""
    resp = await async_client.get("/api/v1/system/telemetry-beacon/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_telemetry_beacon_status_forbidden_for_support_roles(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que roles no administrativos (SUPPORT_L1) no puedan inspeccionar el estado del beacon."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)

    _, headers = await _create_test_session(fake_redis, SystemRoleEnum.SUPPORT_L1)
    resp = await async_client.get("/api/v1/system/telemetry-beacon/status", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_telemetry_beacon_status_superadmin_success(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que SUPERADMIN_GLOBAL reciba el estado detallado del beacon."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.workers.telemetry_beacon_worker.get_redis_client", lambda: fake_redis)

    await fake_redis.hset(
        "rg:system:telemetry_beacon_state",
        mapping={
            "instance_id": "test_instance_hash_64",
            "last_sent_at": "2026-11-01T10:00:00Z",
            "last_status": "http_202",
        },
    )

    _, headers = await _create_test_session(fake_redis, SystemRoleEnum.SUPERADMIN_GLOBAL)
    resp = await async_client.get("/api/v1/system/telemetry-beacon/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert data["instance_id"] == "test_instance_hash_64"
    assert data["last_sent_at"] == "2026-11-01T10:00:00Z"
    assert data["last_heartbeat_at"] == "2026-11-01T10:00:00Z"
    assert data["last_status"] == "http_202"
    assert "fleet_bucket" in data
    assert "router_count" in data
    assert "https://rosgrid.net" in data["beacon_url"]


@pytest.mark.asyncio
async def test_get_telemetry_beacon_status_tenant_admin_success(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que TENANT_ADMIN también pueda consultar el estado del beacon."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.workers.telemetry_beacon_worker.get_redis_client", lambda: fake_redis)

    _, headers = await _create_test_session(fake_redis, SystemRoleEnum.TENANT_ADMIN)
    resp = await async_client.get("/api/v1/system/telemetry-beacon/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert len(data["instance_id"]) == 64


@pytest.mark.asyncio
async def test_trigger_telemetry_beacon_manual(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica el disparo manual del latido por parte de SUPERADMIN_GLOBAL."""
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake_redis)
    monkeypatch.setattr("src.workers.telemetry_beacon_worker.get_redis_client", lambda: fake_redis)

    mock_send = AsyncMock(
        return_value={
            "enabled": True,
            "instance_id": "manual_hash_64",
            "last_sent_at": "2026-11-01T10:15:00Z",
            "last_status": "http_202",
            "fleet_bucket": "1-10",
        }
    )
    monkeypatch.setattr("src.api.v1.system.send_telemetry_heartbeat_once", mock_send)

    _, headers = await _create_test_session(fake_redis, SystemRoleEnum.SUPERADMIN_GLOBAL)
    headers["Idempotency-Key"] = str(uuid.uuid4())
    resp = await async_client.post("/api/v1/system/telemetry-beacon/trigger", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["last_status"] == "http_202"
    assert data["fleet_bucket"] == "1-10"
    mock_send.assert_awaited_once()


def test_create_tenant_request_auto_populates_admin_full_name() -> None:
    """Verifica que CreateTenantRequest no lance 422 si el modal de UI omite admin_full_name."""
    from src.schemas.tenants import CreateTenantRequest

    req = CreateTenantRequest(
        slug="caja",
        name="preso",
        tax_id="123456789",
        admin_username="pedro",
        admin_email="pedro@gmail.com",
        admin_password="123456789",
        max_routers_quota=50,
        max_users_quota=20,
        default_safemode_seconds=60,
    )
    assert req.admin_full_name == "pedro"

