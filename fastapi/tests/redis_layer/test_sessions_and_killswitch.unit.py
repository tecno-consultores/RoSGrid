# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from unittest.mock import patch

import pytest

from src.redis_layer.sessions import (
    create_session,
    get_session,
    kill_all_user_sessions,
    kill_session,
    rotate_refresh_token,
)
from tests.conftest import FakeAsyncRedis


@pytest.mark.asyncio
async def test_create_and_get_session(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        session_id, family_id, rt = await create_session(
            tenant_id="tenant-1",
            user_id="user-1",
            username="admin",
            full_name="Admin User",
            role="SUPERADMIN_GLOBAL",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        assert len(session_id) == 32
        assert len(family_id) == 32
        assert len(rt) > 20

        sess_data = await get_session("tenant-1", session_id)
        assert sess_data is not None
        assert sess_data["user_id"] == "user-1"
        assert sess_data["username"] == "admin"
        assert sess_data["role"] == "SUPERADMIN_GLOBAL"
        assert sess_data["refresh_family_id"] == family_id


@pytest.mark.asyncio
async def test_kill_session_and_pubsub_event(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        session_id, _family_id, _ = await create_session(
            tenant_id="tenant-1",
            user_id="user-1",
            username="admin",
            full_name="Admin User",
            role="SUPERADMIN_GLOBAL",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Matar sesión
        killed = await kill_session("tenant-1", session_id, killed_by="SOC_OPERATOR", reason="Compromiso sospechoso")
        assert killed is True

        # Sesión ya no debe existir
        sess_data = await get_session("tenant-1", session_id)
        assert sess_data is None

        # Re-intentar matar sesión ya destruida -> False
        killed_again = await kill_session("tenant-1", session_id)
        assert killed_again is False


@pytest.mark.asyncio
async def test_kill_all_user_sessions(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        # Crear 2 sesiones para el mismo usuario
        s1, _, _ = await create_session(
            tenant_id="tenant-1",
            user_id="user-42",
            username="analyst",
            full_name="Network Analyst",
            role="OPERATIONS_ANALYST",
            ip_address="10.0.0.1",
            user_agent="Agent1",
        )
        s2, _, _ = await create_session(
            tenant_id="tenant-1",
            user_id="user-42",
            username="analyst",
            full_name="Network Analyst",
            role="OPERATIONS_ANALYST",
            ip_address="10.0.0.2",
            user_agent="Agent2",
        )

        count = await kill_all_user_sessions("tenant-1", "user-42")
        assert count == 2

        assert await get_session("tenant-1", s1) is None
        assert await get_session("tenant-1", s2) is None


@pytest.mark.asyncio
async def test_rotate_refresh_token_lifecycle(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        session_id, family_id, initial_rt = await create_session(
            tenant_id="tenant-1",
            user_id="user-1",
            username="admin",
            full_name="Admin User",
            role="SUPERADMIN_GLOBAL",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # 1. Rotación válida 1
        success, err, new_rt_1 = await rotate_refresh_token("tenant-1", family_id, initial_rt)
        assert success is True
        assert err is None
        assert new_rt_1 is not None
        assert new_rt_1 != initial_rt

        # 2. Rotación con token incorrecto (hash mismatch)
        success, err, _ = await rotate_refresh_token("tenant-1", family_id, "wrong_token_value")
        assert success is False
        assert err == "HASH_MISMATCH"

        # 3. Detección de reúso de refresh token (Token Reuse Attack fuera de grace period)
        # Intentar volver a usar initial_rt que ya fue utilizado en el paso 1
        success, err, _ = await rotate_refresh_token("tenant-1", family_id, initial_rt, grace_period_seconds=0)
        assert success is False
        assert err == "REUSE_DETECTED"

        # La sesión debe haber sido liquidada por el Kill Switch
        assert await get_session("tenant-1", session_id) is None


@pytest.mark.asyncio
async def test_rotate_refresh_token_grace_period_success(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        session_id, family_id, initial_rt = await create_session(
            tenant_id="tenant-1",
            user_id="user-1",
            username="admin",
            full_name="Admin User",
            role="SUPERADMIN_GLOBAL",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Rotación 1
        success, err, new_rt = await rotate_refresh_token("tenant-1", family_id, initial_rt, grace_period_seconds=10)
        assert success is True
        assert new_rt is not None

        # Reintento concurrente con initial_rt dentro de los 10s de gracia
        success2, err2, replayed_rt = await rotate_refresh_token(
            "tenant-1", family_id, initial_rt, grace_period_seconds=10
        )
        assert success2 is True
        assert err2 is None
        assert replayed_rt == new_rt

        # La sesión NO debe haber sido liquidada
        sess = await get_session("tenant-1", session_id)
        assert sess is not None


@pytest.mark.asyncio
async def test_rotate_refresh_token_expired_family(fake_redis: FakeAsyncRedis) -> None:
    with patch("src.redis_layer.sessions.get_redis_client", return_value=fake_redis):
        success, err, _ = await rotate_refresh_token("tenant-1", "non-existent-family", "token")
        assert success is False
        assert err == "EXPIRED_FAMILY"
