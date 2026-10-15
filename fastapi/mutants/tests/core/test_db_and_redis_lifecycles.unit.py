# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request

from src.db.session import get_db_session, get_tenant_db_session, set_tenant_context
from src.redis_layer.client import close_redis_client, get_redis_client


@pytest.mark.asyncio
async def test_redis_client_lifecycle() -> None:
    # 1. Obtener cliente cuando no está inicializado
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_instance = AsyncMock()
        mock_from_url.return_value = mock_instance
        await close_redis_client()

        client1 = get_redis_client()
        client2 = get_redis_client()
        assert client1 is client2
        assert client1 is mock_instance

        # 2. Cerrar cliente
        await close_redis_client()
        mock_instance.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_db_session_lifecycles() -> None:
    # 1. get_db_session generator
    mock_session = AsyncMock()
    with patch("src.db.session.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        gen = get_db_session()
        sess = await anext(gen)
        assert sess is mock_session
        with pytest.raises(StopAsyncIteration):
            await anext(gen)

    # 2. set_tenant_context
    session_ctx = AsyncMock()
    tid = uuid.uuid4()
    await set_tenant_context(session_ctx, tid, is_superadmin=True)
    session_ctx.execute.assert_awaited_once()

    # 3. get_tenant_db_session
    scope = {"type": "http", "state": {"tenant_id": tid, "is_superadmin_global": True}}
    req = Request(scope)
    with patch("src.db.session.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        t_gen = get_tenant_db_session(req)
        t_sess = await anext(t_gen)
        assert t_sess is mock_session
        with pytest.raises(StopAsyncIteration):
            await anext(t_gen)
