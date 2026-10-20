# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import time
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from src.core.config import settings
from src.core.csrf import (
    CSRFProtectionMiddleware,
    generate_csrf_token,
    validate_csrf_token,
)


def test_csrf_token_generation_structure() -> None:
    session_id = "sess-12345"
    tenant_id = "tenant-abc"
    token = generate_csrf_token(session_id, tenant_id)

    parts = token.split(".")
    assert len(parts) == 3
    nonce, epoch_str, sig = parts
    assert len(nonce) == 32
    assert epoch_str.isdigit()
    assert len(sig) == 64


def test_csrf_token_validation_success() -> None:
    session_id = "sess-12345"
    tenant_id = "tenant-abc"
    token = generate_csrf_token(session_id, tenant_id)

    assert validate_csrf_token(token, session_id, tenant_id) is True


def test_csrf_token_tampered_components() -> None:
    session_id = "sess-12345"
    tenant_id = "tenant-abc"
    token = generate_csrf_token(session_id, tenant_id)
    nonce, epoch_str, sig = token.split(".")

    # Tampered session_id
    assert validate_csrf_token(token, "sess-other", tenant_id) is False

    # Tampered tenant_id
    assert validate_csrf_token(token, session_id, "tenant-xyz") is False

    # Tampered signature
    tampered_sig = ("0" if sig[0] != "0" else "1") + sig[1:]
    assert validate_csrf_token(f"{nonce}.{epoch_str}.{tampered_sig}", session_id, tenant_id) is False

    # Tampered nonce
    tampered_nonce = ("0" if nonce[0] != "0" else "1") + nonce[1:]
    assert validate_csrf_token(f"{tampered_nonce}.{epoch_str}.{sig}", session_id, tenant_id) is False


def test_csrf_token_invalid_formats() -> None:
    session_id = "sess-12345"
    tenant_id = "tenant-abc"

    assert validate_csrf_token("", session_id, tenant_id) is False
    assert validate_csrf_token("invalid", session_id, tenant_id) is False
    assert validate_csrf_token("a.b", session_id, tenant_id) is False
    assert validate_csrf_token("a.b.c.d", session_id, tenant_id) is False
    assert validate_csrf_token("nonce.notanumber.sig", session_id, tenant_id) is False


def test_csrf_token_expiration() -> None:
    session_id = "sess-1"
    tenant_id = "tenant-1"
    token = generate_csrf_token(session_id, tenant_id)

    # Expirado: tiempo transcurrido > max_age_seconds
    assert validate_csrf_token(token, session_id, tenant_id, max_age_seconds=-1) is False

    # Futuro inválido (> now + 60s)
    future_epoch = int(time.time()) + 120
    key = b"secret"
    import hashlib
    import hmac

    payload = f"{session_id}:{tenant_id}:deadbeef:{future_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    future_token = f"deadbeef.{future_epoch}.{sig}"
    assert validate_csrf_token(future_token, session_id, tenant_id, secret="secret") is False


@pytest.mark.asyncio
async def test_csrf_middleware_allows_safe_methods() -> None:
    middleware = CSRFProtectionMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/users",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)

    assert res.status_code == 200
    call_next.assert_awaited_once_with(req)


@pytest.mark.asyncio
async def test_csrf_middleware_allows_excluded_paths() -> None:
    middleware = CSRFProtectionMiddleware(app=None)  # type: ignore[arg-type]
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
async def test_csrf_middleware_validates_mutating_with_session() -> None:
    middleware = CSRFProtectionMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    token = generate_csrf_token("sess-1", "tenant-1")

    # Caso exitoso: token presente y válido
    headers = Headers({"x-csrf-token": token})
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
    }
    req = Request(scope)
    req.state.session_id = "sess-1"
    req.state.tenant_id = "tenant-1"

    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 200
    call_next.assert_awaited_once_with(req)


@pytest.mark.asyncio
async def test_csrf_middleware_blocks_invalid_or_missing_token() -> None:
    middleware = CSRFProtectionMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock()

    # Falta cabecera X-CSRF-Token
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": [],
    }
    req = Request(scope)
    req.state.session_id = "sess-1"
    req.state.tenant_id = "tenant-1"

    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 403
    assert call_next.await_count == 0

    # Cabecera X-CSRF-Token alterada
    headers = Headers({"x-csrf-token": "tampered.token.here"})
    scope_tampered = {
        "type": "http",
        "method": "DELETE",
        "path": "/api/v1/routers/1",
        "headers": headers.raw,
    }
    req2 = Request(scope_tampered)
    req2.state.session_id = "sess-1"
    req2.state.tenant_id = "tenant-1"

    res2 = await middleware.dispatch(req2, call_next)
    assert res2.status_code == 403
    assert call_next.await_count == 0


@pytest.mark.asyncio
async def test_csrf_middleware_extracts_jwt_from_cookies_and_validates() -> None:
    middleware = CSRFProtectionMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    token_csrf = generate_csrf_token("sess-jwt-1", "tenant-jwt-1")
    jwt_token = jwt.encode(
        {"sid": "sess-jwt-1", "tid": "tenant-jwt-1", "sub": "user-1"},
        settings.ROSGRID_JWT_SECRET_KEY,
        algorithm="HS256",
    )

    # 1. Petición mutable con cookie JWT y cabecera CSRF válida
    headers = Headers({"cookie": f"rg_at={jwt_token}", "x-csrf-token": token_csrf})
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers.raw,
    }
    req = Request(scope)

    res = await middleware.dispatch(req, call_next)
    assert res.status_code == 200
    assert req.state.session_id == "sess-jwt-1"
    assert req.state.tenant_id == "tenant-jwt-1"

    # 2. Petición mutable con cookie JWT pero SIN cabecera CSRF -> 403 Forbidden
    call_next_blocked = AsyncMock()
    headers_no_csrf = Headers({"cookie": f"rg_at={jwt_token}"})
    scope_no_csrf = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/routers",
        "headers": headers_no_csrf.raw,
    }
    req_blocked = Request(scope_no_csrf)
    res_blocked = await middleware.dispatch(req_blocked, call_next_blocked)
    assert res_blocked.status_code == 403
    assert call_next_blocked.await_count == 0
