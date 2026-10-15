# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from src.redis_layer.idempotency import (
    IdempotencyMiddleware,
    compute_request_hash,
    is_valid_uuid,
)
from tests.conftest import FakeAsyncRedis


def test_is_valid_uuid() -> None:
    valid_uuid_str = str(uuid.uuid4())
    assert is_valid_uuid(valid_uuid_str) is True
    assert is_valid_uuid("not-a-uuid") is False
    assert is_valid_uuid("") is False
    assert is_valid_uuid("12345678-1234-5678-1234-56781234567g") is False


def test_compute_request_hash() -> None:
    h1 = compute_request_hash("POST", "/api/v1/routers", b'{"name": "router1"}')
    h2 = compute_request_hash("POST", "/api/v1/routers", b'{"name": "router1"}')
    h3 = compute_request_hash("POST", "/api/v1/routers", b'{"name": "router2"}')
    h4 = compute_request_hash("PUT", "/api/v1/routers", b'{"name": "router1"}')

    assert h1 == h2
    assert h1 != h3
    assert h1 != h4
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_idempotency_middleware_allows_safe_methods() -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/routers",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 200
    call_next.assert_awaited_once_with(req)


@pytest.mark.asyncio
async def test_idempotency_middleware_allows_excluded_paths() -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 200
    call_next.assert_awaited_once_with(req)


@pytest.mark.asyncio
async def test_idempotency_middleware_missing_or_invalid_key() -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock()

    # Missing header
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 400
    assert call_next.await_count == 0

    # Invalid UUID format
    headers = Headers({"idempotency-key": "not-a-valid-uuid"})
    scope_invalid = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
    }
    req_inv = Request(scope_invalid)
    res_inv = await middleware.dispatch(req_inv, call_next)
    assert res_inv.status_code == 400
    assert call_next.await_count == 0


@pytest.mark.asyncio
async def test_idempotency_middleware_flow_new_and_replay(fake_redis: FakeAsyncRedis) -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    key_val = str(uuid.uuid4())
    headers = Headers({"idempotency-key": key_val})
    body_content = b'{"name": "router1"}'

    async def receive():
        return {"type": "http.request", "body": body_content, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
        "_body": body_content,
    }
    req = Request(scope, receive=receive)
    req.state.tenant_id = "tenant-1"
    req.state.user_id = "user-1"

    mock_resp = Response(
        content=json.dumps({"id": 101, "status": "created"}).encode("utf-8"),
        status_code=201,
        media_type="application/json",
    )
    call_next = AsyncMock(return_value=mock_resp)

    with patch("src.redis_layer.idempotency.get_redis_client", return_value=fake_redis):
        # 1. Petición inicial exitosa
        res1 = await middleware.dispatch(req, call_next)
        assert res1.status_code == 201
        assert call_next.await_count == 1

        # 2. Petición idéntica posterior (Replay) -> 201 con cabecera X-Idempotent-Replay
        req2 = Request(scope, receive=receive)
        req2.state.tenant_id = "tenant-1"
        req2.state.user_id = "user-1"
        res2 = await middleware.dispatch(req2, call_next)

        assert res2.status_code == 201
        assert res2.headers.get("X-Idempotent-Replay") == "true"
        assert call_next.await_count == 1  # No se volvió a llamar


@pytest.mark.asyncio
async def test_idempotency_middleware_conflict_in_progress(fake_redis: FakeAsyncRedis) -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    key_val = str(uuid.uuid4())
    headers = Headers({"idempotency-key": key_val})
    body_content = b'{"name": "router1"}'

    async def receive():
        return {"type": "http.request", "body": body_content, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
        "_body": body_content,
    }
    req = Request(scope, receive=receive)
    req.state.tenant_id = "tenant-1"
    req.state.user_id = "user-1"

    req_hash = compute_request_hash("POST", "/api/v1/routers", body_content)
    redis_key = f"rg:tenant-1:idemp:user-1:{key_val}"
    # Pre-crear estado IN_PROGRESS en Redis
    await fake_redis.hset(redis_key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})

    call_next = AsyncMock()
    with patch("src.redis_layer.idempotency.get_redis_client", return_value=fake_redis):
        res = await middleware.dispatch(req, call_next)
        assert res.status_code == 409
        assert call_next.await_count == 0


@pytest.mark.asyncio
async def test_idempotency_middleware_payload_mismatch_422(fake_redis: FakeAsyncRedis) -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    key_val = str(uuid.uuid4())
    headers = Headers({"idempotency-key": key_val})
    body_content = b'{"name": "original"}'

    async def receive():
        return {"type": "http.request", "body": b'{"name": "altered"}', "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
        "_body": b'{"name": "altered"}',
    }
    req = Request(scope, receive=receive)
    req.state.tenant_id = "tenant-1"
    req.state.user_id = "user-1"

    # En Redis está guardado con el hash de "original"
    original_hash = compute_request_hash("POST", "/api/v1/routers", body_content)
    redis_key = f"rg:tenant-1:idemp:user-1:{key_val}"
    await fake_redis.hset(redis_key, mapping={"status": "COMPLETED", "request_hash": original_hash})

    call_next = AsyncMock()
    with patch("src.redis_layer.idempotency.get_redis_client", return_value=fake_redis):
        res = await middleware.dispatch(req, call_next)
        assert res.status_code == 422
        assert call_next.await_count == 0


@pytest.mark.asyncio
async def test_idempotency_middleware_deletes_key_on_server_error(fake_redis: FakeAsyncRedis) -> None:
    middleware = IdempotencyMiddleware(app=None)  # type: ignore[arg-type]
    key_val = str(uuid.uuid4())
    headers = Headers({"idempotency-key": key_val})
    body_content = b'{"name": "router1"}'

    async def receive():
        return {"type": "http.request", "body": body_content, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
        "_body": body_content,
    }
    req = Request(scope, receive=receive)
    req.state.tenant_id = "tenant-1"
    req.state.user_id = "user-1"

    call_next = AsyncMock(return_value=Response(content="Error interno", status_code=500))

    with patch("src.redis_layer.idempotency.get_redis_client", return_value=fake_redis):
        res = await middleware.dispatch(req, call_next)
        assert res.status_code == 500

        # Debe haberse eliminado la llave para permitir reintento
        redis_key = f"rg:tenant-1:idemp:user-1:{key_val}"
        data = await fake_redis.hgetall(redis_key)
        assert data == {}
