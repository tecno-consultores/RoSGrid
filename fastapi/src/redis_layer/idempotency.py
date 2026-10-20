# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import jwt
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.config import settings
from src.redis_layer.client import get_redis_client

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_EXCLUDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/2fa/verify",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/bootstrap",
    "/api/v1/mcp",
    "/metrics",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, TypeError):
        return False


def compute_request_hash(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


async def check_idempotency_state(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("request_hash") != req_hash:
        return (
            JSONResponse(
                status_code=422,
                content={"detail": "Conflicto de Idempotency-Key: la llave ya fue utilizada con un payload diferente"},
            ),
            False,
        )

    if data.get("status") == "IN_PROGRESS":
        return (
            JSONResponse(
                status_code=409,
                content={"detail": "La operación con esta Idempotency-Key ya se encuentra en ejecución en el router"},
            ),
            False,
        )

    # Estado COMPLETED -> Replay
    status_code = int(data.get("status_code", 200))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


def _should_bypass_idempotency(method: str, path: str) -> bool:
    return method not in _MUTATING_METHODS or path in _EXCLUDED_PATHS


async def _capture_response_body(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def _cache_completed_idempotency(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


def _extract_raw_token_idemp(request: Request) -> str | None:
    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if token:
        return token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def _decode_actors_from_token(token: str) -> tuple[str | None, str | None]:
    try:
        payload = jwt.decode(
            token,
            settings.ROSGRID_JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_signature": True},
        )
        tid = payload.get("tid")
        sub = payload.get("sub")
        return str(tid) if tid else None, str(sub) if sub else None
    except Exception:
        return None, None


def _populate_actors_from_token(request: Request, raw_token: str) -> None:
    tid, sub = _decode_actors_from_token(raw_token)
    if tid and not getattr(request.state, "tenant_id", None):
        request.state.tenant_id = tid
    if sub and not getattr(request.state, "user_id", None):
        request.state.user_id = sub


def _extract_and_populate_token_actors(request: Request) -> None:
    raw_token = _extract_raw_token_idemp(request)
    if raw_token:
        _populate_actors_from_token(request, raw_token)


def _resolve_idempotency_actors(request: Request) -> tuple[str, str]:
    tid = getattr(request.state, "tenant_id", None)
    uid = getattr(request.state, "user_id", None)
    if tid and uid:
        return str(tid), str(uid)
    _extract_and_populate_token_actors(request)
    return str(getattr(request.state, "tenant_id", None) or "global"), str(
        getattr(request.state, "user_id", None) or "anonymous"
    )


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id_str, user_id_str = _resolve_idempotency_actors(request)
        redis_key = f"rg:{tenant_id_str}:idemp:{user_id_str}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response


async def _iterate_in_memory(chunks: list[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk
