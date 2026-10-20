# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import hmac
import os
import time

import jwt
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.config import settings

_EXCLUDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/2fa/verify",
    "/api/v1/auth/refresh",
    "/api/v1/auth/bootstrap",
    "/api/v1/mcp",
    "/metrics",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def validate_csrf_token(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, issued_epoch_str, signature = parts
    try:
        issued_epoch = int(issued_epoch_str)
    except ValueError:
        return False

    now = int(time.time())
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def _extract_cookie_session(request: Request) -> tuple[str | None, str | None]:
    raw_cookie = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    session_id = getattr(request.state, "session_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not raw_cookie and not (session_id and tenant_id and not request.headers.get("Authorization")):
        return None, None

    if session_id and tenant_id:
        return str(session_id), str(tenant_id)

    if raw_cookie:
        try:
            payload = jwt.decode(
                raw_cookie,
                settings.ROSGRID_JWT_SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_signature": True},
            )
            sid = payload.get("sid")
            tid = payload.get("tid")
            sub = payload.get("sub")
            if sid and tid:
                request.state.session_id = str(sid)
                request.state.tenant_id = str(tid)
                if sub:
                    request.state.user_id = str(sub)
                return str(sid), str(tid)
        except Exception:
            pass

    return None, None


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        session_id, tenant_id = _extract_cookie_session(request)
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, session_id, tenant_id))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
