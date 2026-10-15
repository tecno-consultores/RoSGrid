# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from unittest.mock import AsyncMock

import pytest
from fastapi import Request, Response

from src.core.security_headers import SecurityHeadersMiddleware


@pytest.mark.asyncio
async def test_security_headers_injected_on_api_path() -> None:
    middleware = SecurityHeadersMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)

    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert res.headers["Permissions-Policy"] == "geolocation=(), camera=(), microphone=()"
    assert "default-src 'none'" in res.headers["Content-Security-Policy"]
    assert res.headers["Server"] == "RoSGrid"
    assert res.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert res.headers["Pragma"] == "no-cache"


@pytest.mark.asyncio
async def test_security_headers_on_non_api_path() -> None:
    middleware = SecurityHeadersMiddleware(app=None)  # type: ignore[arg-type]
    call_next = AsyncMock(return_value=Response(content="metrics", status_code=200))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "headers": [],
    }
    req = Request(scope)
    res = await middleware.dispatch(req, call_next)

    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["Server"] == "RoSGrid"
    assert "Cache-Control" not in res.headers
