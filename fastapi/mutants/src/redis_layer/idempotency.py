# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.redis_layer.client import get_redis_client

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_EXCLUDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/2fa/verify",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/metrics",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_is_valid_uuid__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_is_valid_uuid__mutmut)
def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, TypeError):
        return False


def x_is_valid_uuid__mutmut_orig(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, TypeError):
        return False


def x_is_valid_uuid__mutmut_1(val: str) -> bool:
    try:
        uuid.UUID(None)
        return True
    except (ValueError, TypeError):
        return False


def x_is_valid_uuid__mutmut_2(val: str) -> bool:
    try:
        uuid.UUID(val)
        return False
    except (ValueError, TypeError):
        return False


def x_is_valid_uuid__mutmut_3(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, TypeError):
        return True

mutants_x_is_valid_uuid__mutmut['_mutmut_orig'] = x_is_valid_uuid__mutmut_orig # type: ignore # mutmut generated
mutants_x_is_valid_uuid__mutmut['x_is_valid_uuid__mutmut_1'] = x_is_valid_uuid__mutmut_1 # type: ignore # mutmut generated
mutants_x_is_valid_uuid__mutmut['x_is_valid_uuid__mutmut_2'] = x_is_valid_uuid__mutmut_2 # type: ignore # mutmut generated
mutants_x_is_valid_uuid__mutmut['x_is_valid_uuid__mutmut_3'] = x_is_valid_uuid__mutmut_3 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_compute_request_hash__mutmut)
def compute_request_hash(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_orig(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_1(method: str, path: str, body: bytes) -> str:
    raw = None
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_2(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode(None, errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_3(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors=None)}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_4(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode(errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_5(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', )}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_6(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('XXutf-8XX', errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_7(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('UTF-8', errors='replace')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_8(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='XXreplaceXX')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_9(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='REPLACE')}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_request_hash__mutmut_10(method: str, path: str, body: bytes) -> str:
    raw = f"{method}:{path}:{body.decode('utf-8', errors='replace')}".encode()
    return hashlib.sha256(None).hexdigest()

mutants_x_compute_request_hash__mutmut['_mutmut_orig'] = x_compute_request_hash__mutmut_orig # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_1'] = x_compute_request_hash__mutmut_1 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_2'] = x_compute_request_hash__mutmut_2 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_3'] = x_compute_request_hash__mutmut_3 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_4'] = x_compute_request_hash__mutmut_4 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_5'] = x_compute_request_hash__mutmut_5 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_6'] = x_compute_request_hash__mutmut_6 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_7'] = x_compute_request_hash__mutmut_7 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_8'] = x_compute_request_hash__mutmut_8 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_9'] = x_compute_request_hash__mutmut_9 # type: ignore # mutmut generated
mutants_x_compute_request_hash__mutmut['x_compute_request_hash__mutmut_10'] = x_compute_request_hash__mutmut_10 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_check_idempotency_state__mutmut)
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


async def x_check_idempotency_state__mutmut_orig(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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


async def x_check_idempotency_state__mutmut_1(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = None
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


async def x_check_idempotency_state__mutmut_2(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(None)
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


async def x_check_idempotency_state__mutmut_3(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if data:
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


async def x_check_idempotency_state__mutmut_4(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(None, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_5(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping=None)
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


async def x_check_idempotency_state__mutmut_6(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_7(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, )
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


async def x_check_idempotency_state__mutmut_8(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"XXstatusXX": "IN_PROGRESS", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_9(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"STATUS": "IN_PROGRESS", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_10(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "XXIN_PROGRESSXX", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_11(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "in_progress", "request_hash": req_hash})
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


async def x_check_idempotency_state__mutmut_12(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "XXrequest_hashXX": req_hash})
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


async def x_check_idempotency_state__mutmut_13(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "REQUEST_HASH": req_hash})
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


async def x_check_idempotency_state__mutmut_14(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(None, 60)
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


async def x_check_idempotency_state__mutmut_15(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, None)
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


async def x_check_idempotency_state__mutmut_16(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(60)
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


async def x_check_idempotency_state__mutmut_17(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, )
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


async def x_check_idempotency_state__mutmut_18(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 61)
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


async def x_check_idempotency_state__mutmut_19(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, False

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


async def x_check_idempotency_state__mutmut_20(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get(None) != req_hash:
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


async def x_check_idempotency_state__mutmut_21(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("XXrequest_hashXX") != req_hash:
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


async def x_check_idempotency_state__mutmut_22(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("REQUEST_HASH") != req_hash:
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


async def x_check_idempotency_state__mutmut_23(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("request_hash") == req_hash:
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


async def x_check_idempotency_state__mutmut_24(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("request_hash") != req_hash:
        return (
            JSONResponse(
                status_code=None,
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


async def x_check_idempotency_state__mutmut_25(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content=None,
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


async def x_check_idempotency_state__mutmut_26(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("request_hash") != req_hash:
        return (
            JSONResponse(
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


async def x_check_idempotency_state__mutmut_27(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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


async def x_check_idempotency_state__mutmut_28(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
    data = await redis_client.hgetall(key)
    if not data:
        # No existe -> Adquirir bloqueo IN_PROGRESS
        await redis_client.hset(key, mapping={"status": "IN_PROGRESS", "request_hash": req_hash})
        await redis_client.expire(key, 60)
        return None, True

    if data.get("request_hash") != req_hash:
        return (
            JSONResponse(
                status_code=423,
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


async def x_check_idempotency_state__mutmut_29(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"XXdetailXX": "Conflicto de Idempotency-Key: la llave ya fue utilizada con un payload diferente"},
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


async def x_check_idempotency_state__mutmut_30(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"DETAIL": "Conflicto de Idempotency-Key: la llave ya fue utilizada con un payload diferente"},
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


async def x_check_idempotency_state__mutmut_31(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "XXConflicto de Idempotency-Key: la llave ya fue utilizada con un payload diferenteXX"},
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


async def x_check_idempotency_state__mutmut_32(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "conflicto de idempotency-key: la llave ya fue utilizada con un payload diferente"},
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


async def x_check_idempotency_state__mutmut_33(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "CONFLICTO DE IDEMPOTENCY-KEY: LA LLAVE YA FUE UTILIZADA CON UN PAYLOAD DIFERENTE"},
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


async def x_check_idempotency_state__mutmut_34(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
            True,
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


async def x_check_idempotency_state__mutmut_35(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get(None) == "IN_PROGRESS":
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


async def x_check_idempotency_state__mutmut_36(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get("XXstatusXX") == "IN_PROGRESS":
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


async def x_check_idempotency_state__mutmut_37(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get("STATUS") == "IN_PROGRESS":
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


async def x_check_idempotency_state__mutmut_38(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get("status") != "IN_PROGRESS":
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


async def x_check_idempotency_state__mutmut_39(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get("status") == "XXIN_PROGRESSXX":
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


async def x_check_idempotency_state__mutmut_40(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    if data.get("status") == "in_progress":
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


async def x_check_idempotency_state__mutmut_41(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                status_code=None,
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


async def x_check_idempotency_state__mutmut_42(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content=None,
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


async def x_check_idempotency_state__mutmut_43(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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


async def x_check_idempotency_state__mutmut_44(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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


async def x_check_idempotency_state__mutmut_45(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                status_code=410,
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


async def x_check_idempotency_state__mutmut_46(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"XXdetailXX": "La operación con esta Idempotency-Key ya se encuentra en ejecución en el router"},
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


async def x_check_idempotency_state__mutmut_47(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"DETAIL": "La operación con esta Idempotency-Key ya se encuentra en ejecución en el router"},
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


async def x_check_idempotency_state__mutmut_48(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "XXLa operación con esta Idempotency-Key ya se encuentra en ejecución en el routerXX"},
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


async def x_check_idempotency_state__mutmut_49(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "la operación con esta idempotency-key ya se encuentra en ejecución en el router"},
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


async def x_check_idempotency_state__mutmut_50(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
                content={"detail": "LA OPERACIÓN CON ESTA IDEMPOTENCY-KEY YA SE ENCUENTRA EN EJECUCIÓN EN EL ROUTER"},
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


async def x_check_idempotency_state__mutmut_51(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
            True,
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


async def x_check_idempotency_state__mutmut_52(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = None
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_53(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(None)
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_54(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get(None, 200))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_55(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get("status_code", None))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_56(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get(200))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_57(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get("status_code", ))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_58(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get("XXstatus_codeXX", 200))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_59(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get("STATUS_CODE", 200))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_60(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    status_code = int(data.get("status_code", 201))
    raw_content = data.get("response_body", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_61(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = None
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_62(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get(None, "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_63(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("response_body", None)
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_64(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_65(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("response_body", )
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_66(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("XXresponse_bodyXX", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_67(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("RESPONSE_BODY", "{}")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_68(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    raw_content = data.get("response_body", "XX{}XX")
    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_69(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
        content = None
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_70(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
        content = json.loads(None)
    except json.JSONDecodeError:
        content = raw_content

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_71(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
        content = None

    replay_resp = JSONResponse(status_code=status_code, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_72(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    replay_resp = None
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_73(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    replay_resp = JSONResponse(status_code=None, content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_74(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    replay_resp = JSONResponse(status_code=status_code, content=None)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_75(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    replay_resp = JSONResponse(content=content)
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_76(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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

    replay_resp = JSONResponse(status_code=status_code, )
    replay_resp.headers["X-Idempotent-Replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_77(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["X-Idempotent-Replay"] = None
    return replay_resp, False


async def x_check_idempotency_state__mutmut_78(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["XXX-Idempotent-ReplayXX"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_79(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["x-idempotent-replay"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_80(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["X-IDEMPOTENT-REPLAY"] = "true"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_81(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["X-Idempotent-Replay"] = "XXtrueXX"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_82(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    replay_resp.headers["X-Idempotent-Replay"] = "TRUE"
    return replay_resp, False


async def x_check_idempotency_state__mutmut_83(redis_client: Any, key: str, req_hash: str) -> tuple[Response | None, bool]:
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
    return replay_resp, True

mutants_x_check_idempotency_state__mutmut['_mutmut_orig'] = x_check_idempotency_state__mutmut_orig # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_1'] = x_check_idempotency_state__mutmut_1 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_2'] = x_check_idempotency_state__mutmut_2 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_3'] = x_check_idempotency_state__mutmut_3 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_4'] = x_check_idempotency_state__mutmut_4 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_5'] = x_check_idempotency_state__mutmut_5 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_6'] = x_check_idempotency_state__mutmut_6 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_7'] = x_check_idempotency_state__mutmut_7 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_8'] = x_check_idempotency_state__mutmut_8 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_9'] = x_check_idempotency_state__mutmut_9 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_10'] = x_check_idempotency_state__mutmut_10 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_11'] = x_check_idempotency_state__mutmut_11 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_12'] = x_check_idempotency_state__mutmut_12 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_13'] = x_check_idempotency_state__mutmut_13 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_14'] = x_check_idempotency_state__mutmut_14 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_15'] = x_check_idempotency_state__mutmut_15 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_16'] = x_check_idempotency_state__mutmut_16 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_17'] = x_check_idempotency_state__mutmut_17 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_18'] = x_check_idempotency_state__mutmut_18 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_19'] = x_check_idempotency_state__mutmut_19 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_20'] = x_check_idempotency_state__mutmut_20 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_21'] = x_check_idempotency_state__mutmut_21 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_22'] = x_check_idempotency_state__mutmut_22 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_23'] = x_check_idempotency_state__mutmut_23 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_24'] = x_check_idempotency_state__mutmut_24 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_25'] = x_check_idempotency_state__mutmut_25 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_26'] = x_check_idempotency_state__mutmut_26 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_27'] = x_check_idempotency_state__mutmut_27 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_28'] = x_check_idempotency_state__mutmut_28 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_29'] = x_check_idempotency_state__mutmut_29 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_30'] = x_check_idempotency_state__mutmut_30 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_31'] = x_check_idempotency_state__mutmut_31 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_32'] = x_check_idempotency_state__mutmut_32 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_33'] = x_check_idempotency_state__mutmut_33 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_34'] = x_check_idempotency_state__mutmut_34 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_35'] = x_check_idempotency_state__mutmut_35 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_36'] = x_check_idempotency_state__mutmut_36 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_37'] = x_check_idempotency_state__mutmut_37 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_38'] = x_check_idempotency_state__mutmut_38 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_39'] = x_check_idempotency_state__mutmut_39 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_40'] = x_check_idempotency_state__mutmut_40 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_41'] = x_check_idempotency_state__mutmut_41 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_42'] = x_check_idempotency_state__mutmut_42 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_43'] = x_check_idempotency_state__mutmut_43 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_44'] = x_check_idempotency_state__mutmut_44 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_45'] = x_check_idempotency_state__mutmut_45 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_46'] = x_check_idempotency_state__mutmut_46 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_47'] = x_check_idempotency_state__mutmut_47 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_48'] = x_check_idempotency_state__mutmut_48 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_49'] = x_check_idempotency_state__mutmut_49 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_50'] = x_check_idempotency_state__mutmut_50 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_51'] = x_check_idempotency_state__mutmut_51 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_52'] = x_check_idempotency_state__mutmut_52 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_53'] = x_check_idempotency_state__mutmut_53 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_54'] = x_check_idempotency_state__mutmut_54 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_55'] = x_check_idempotency_state__mutmut_55 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_56'] = x_check_idempotency_state__mutmut_56 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_57'] = x_check_idempotency_state__mutmut_57 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_58'] = x_check_idempotency_state__mutmut_58 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_59'] = x_check_idempotency_state__mutmut_59 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_60'] = x_check_idempotency_state__mutmut_60 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_61'] = x_check_idempotency_state__mutmut_61 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_62'] = x_check_idempotency_state__mutmut_62 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_63'] = x_check_idempotency_state__mutmut_63 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_64'] = x_check_idempotency_state__mutmut_64 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_65'] = x_check_idempotency_state__mutmut_65 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_66'] = x_check_idempotency_state__mutmut_66 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_67'] = x_check_idempotency_state__mutmut_67 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_68'] = x_check_idempotency_state__mutmut_68 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_69'] = x_check_idempotency_state__mutmut_69 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_70'] = x_check_idempotency_state__mutmut_70 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_71'] = x_check_idempotency_state__mutmut_71 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_72'] = x_check_idempotency_state__mutmut_72 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_73'] = x_check_idempotency_state__mutmut_73 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_74'] = x_check_idempotency_state__mutmut_74 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_75'] = x_check_idempotency_state__mutmut_75 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_76'] = x_check_idempotency_state__mutmut_76 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_77'] = x_check_idempotency_state__mutmut_77 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_78'] = x_check_idempotency_state__mutmut_78 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_79'] = x_check_idempotency_state__mutmut_79 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_80'] = x_check_idempotency_state__mutmut_80 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_81'] = x_check_idempotency_state__mutmut_81 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_82'] = x_check_idempotency_state__mutmut_82 # type: ignore # mutmut generated
mutants_x_check_idempotency_state__mutmut['x_check_idempotency_state__mutmut_83'] = x_check_idempotency_state__mutmut_83 # type: ignore # mutmut generated
mutants_x__should_bypass_idempotency__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__should_bypass_idempotency__mutmut)
def _should_bypass_idempotency(method: str, path: str) -> bool:
    return method not in _MUTATING_METHODS or path in _EXCLUDED_PATHS


def x__should_bypass_idempotency__mutmut_orig(method: str, path: str) -> bool:
    return method not in _MUTATING_METHODS or path in _EXCLUDED_PATHS


def x__should_bypass_idempotency__mutmut_1(method: str, path: str) -> bool:
    return method not in _MUTATING_METHODS and path in _EXCLUDED_PATHS


def x__should_bypass_idempotency__mutmut_2(method: str, path: str) -> bool:
    return method in _MUTATING_METHODS or path in _EXCLUDED_PATHS


def x__should_bypass_idempotency__mutmut_3(method: str, path: str) -> bool:
    return method not in _MUTATING_METHODS or path not in _EXCLUDED_PATHS

mutants_x__should_bypass_idempotency__mutmut['_mutmut_orig'] = x__should_bypass_idempotency__mutmut_orig # type: ignore # mutmut generated
mutants_x__should_bypass_idempotency__mutmut['x__should_bypass_idempotency__mutmut_1'] = x__should_bypass_idempotency__mutmut_1 # type: ignore # mutmut generated
mutants_x__should_bypass_idempotency__mutmut['x__should_bypass_idempotency__mutmut_2'] = x__should_bypass_idempotency__mutmut_2 # type: ignore # mutmut generated
mutants_x__should_bypass_idempotency__mutmut['x__should_bypass_idempotency__mutmut_3'] = x__should_bypass_idempotency__mutmut_3 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__capture_response_body__mutmut)
async def _capture_response_body(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_orig(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_1(response: Response) -> str:
    body_iter = None
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_2(response: Response) -> str:
    body_iter = getattr(None, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_3(response: Response) -> str:
    body_iter = getattr(response, None, None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_4(response: Response) -> str:
    body_iter = getattr("body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_5(response: Response) -> str:
    body_iter = getattr(response, None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_6(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", )
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_7(response: Response) -> str:
    body_iter = getattr(response, "XXbody_iteratorXX", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_8(response: Response) -> str:
    body_iter = getattr(response, "BODY_ITERATOR", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_9(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_10(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = None
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_11(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = None  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_12(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(None)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_13(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode(None, errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_14(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors=None)
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_15(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode(errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_16(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", )
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_17(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(None).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_18(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"XXXX".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_19(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("XXutf-8XX", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_20(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("UTF-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_21(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="XXreplaceXX")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_22(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="REPLACE")
    return str(getattr(response, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_23(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(None)


async def x__capture_response_body__mutmut_24(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode(None, errors="replace"))


async def x__capture_response_body__mutmut_25(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors=None))


async def x__capture_response_body__mutmut_26(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode(errors="replace"))


async def x__capture_response_body__mutmut_27(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", ))


async def x__capture_response_body__mutmut_28(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(None, "body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_29(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, None, b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_30(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", None).decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_31(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr("body", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_32(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_33(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", ).decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_34(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "XXbodyXX", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_35(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "BODY", b"").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_36(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"XXXX").decode("utf-8", errors="replace"))


async def x__capture_response_body__mutmut_37(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("XXutf-8XX", errors="replace"))


async def x__capture_response_body__mutmut_38(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("UTF-8", errors="replace"))


async def x__capture_response_body__mutmut_39(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="XXreplaceXX"))


async def x__capture_response_body__mutmut_40(response: Response) -> str:
    body_iter = getattr(response, "body_iterator", None)
    if body_iter is not None:
        response_body = [section async for section in body_iter]
        response.body_iterator = _iterate_in_memory(response_body)  # type: ignore[attr-defined]
        return b"".join(response_body).decode("utf-8", errors="replace")
    return str(getattr(response, "body", b"").decode("utf-8", errors="REPLACE"))

mutants_x__capture_response_body__mutmut['_mutmut_orig'] = x__capture_response_body__mutmut_orig # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_1'] = x__capture_response_body__mutmut_1 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_2'] = x__capture_response_body__mutmut_2 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_3'] = x__capture_response_body__mutmut_3 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_4'] = x__capture_response_body__mutmut_4 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_5'] = x__capture_response_body__mutmut_5 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_6'] = x__capture_response_body__mutmut_6 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_7'] = x__capture_response_body__mutmut_7 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_8'] = x__capture_response_body__mutmut_8 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_9'] = x__capture_response_body__mutmut_9 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_10'] = x__capture_response_body__mutmut_10 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_11'] = x__capture_response_body__mutmut_11 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_12'] = x__capture_response_body__mutmut_12 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_13'] = x__capture_response_body__mutmut_13 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_14'] = x__capture_response_body__mutmut_14 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_15'] = x__capture_response_body__mutmut_15 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_16'] = x__capture_response_body__mutmut_16 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_17'] = x__capture_response_body__mutmut_17 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_18'] = x__capture_response_body__mutmut_18 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_19'] = x__capture_response_body__mutmut_19 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_20'] = x__capture_response_body__mutmut_20 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_21'] = x__capture_response_body__mutmut_21 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_22'] = x__capture_response_body__mutmut_22 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_23'] = x__capture_response_body__mutmut_23 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_24'] = x__capture_response_body__mutmut_24 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_25'] = x__capture_response_body__mutmut_25 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_26'] = x__capture_response_body__mutmut_26 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_27'] = x__capture_response_body__mutmut_27 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_28'] = x__capture_response_body__mutmut_28 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_29'] = x__capture_response_body__mutmut_29 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_30'] = x__capture_response_body__mutmut_30 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_31'] = x__capture_response_body__mutmut_31 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_32'] = x__capture_response_body__mutmut_32 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_33'] = x__capture_response_body__mutmut_33 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_34'] = x__capture_response_body__mutmut_34 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_35'] = x__capture_response_body__mutmut_35 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_36'] = x__capture_response_body__mutmut_36 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_37'] = x__capture_response_body__mutmut_37 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_38'] = x__capture_response_body__mutmut_38 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_39'] = x__capture_response_body__mutmut_39 # type: ignore # mutmut generated
mutants_x__capture_response_body__mutmut['x__capture_response_body__mutmut_40'] = x__capture_response_body__mutmut_40 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__cache_completed_idempotency__mutmut)
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


async def x__cache_completed_idempotency__mutmut_orig(redis: Any, redis_key: str, response: Response) -> None:
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


async def x__cache_completed_idempotency__mutmut_1(redis: Any, redis_key: str, response: Response) -> None:
    if 201 <= response.status_code < 300:
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


async def x__cache_completed_idempotency__mutmut_2(redis: Any, redis_key: str, response: Response) -> None:
    if 200 < response.status_code < 300:
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


async def x__cache_completed_idempotency__mutmut_3(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code <= 300:
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


async def x__cache_completed_idempotency__mutmut_4(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 301:
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


async def x__cache_completed_idempotency__mutmut_5(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = None
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


async def x__cache_completed_idempotency__mutmut_6(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(None)
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


async def x__cache_completed_idempotency__mutmut_7(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            None,
            mapping={
                "status": "COMPLETED",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_8(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping=None,
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_9(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            mapping={
                "status": "COMPLETED",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_10(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_11(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "XXstatusXX": "COMPLETED",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_12(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "STATUS": "COMPLETED",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_13(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "XXCOMPLETEDXX",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_14(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "completed",
                "status_code": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_15(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "XXstatus_codeXX": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_16(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "STATUS_CODE": str(response.status_code),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_17(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "status_code": str(None),
                "response_body": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_18(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "status_code": str(response.status_code),
                "XXresponse_bodyXX": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_19(redis: Any, redis_key: str, response: Response) -> None:
    if 200 <= response.status_code < 300:
        body_str = await _capture_response_body(response)
        await redis.hset(
            redis_key,
            mapping={
                "status": "COMPLETED",
                "status_code": str(response.status_code),
                "RESPONSE_BODY": body_str,
            },
        )
        await redis.expire(redis_key, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_20(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.expire(None, 86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_21(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.expire(redis_key, None)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_22(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.expire(86400)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_23(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.expire(redis_key, )
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_24(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.expire(redis_key, 86401)
    elif response.status_code >= 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_25(redis: Any, redis_key: str, response: Response) -> None:
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
    elif response.status_code > 500:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_26(redis: Any, redis_key: str, response: Response) -> None:
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
    elif response.status_code >= 501:
        await redis.delete(redis_key)


async def x__cache_completed_idempotency__mutmut_27(redis: Any, redis_key: str, response: Response) -> None:
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
        await redis.delete(None)

mutants_x__cache_completed_idempotency__mutmut['_mutmut_orig'] = x__cache_completed_idempotency__mutmut_orig # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_1'] = x__cache_completed_idempotency__mutmut_1 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_2'] = x__cache_completed_idempotency__mutmut_2 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_3'] = x__cache_completed_idempotency__mutmut_3 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_4'] = x__cache_completed_idempotency__mutmut_4 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_5'] = x__cache_completed_idempotency__mutmut_5 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_6'] = x__cache_completed_idempotency__mutmut_6 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_7'] = x__cache_completed_idempotency__mutmut_7 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_8'] = x__cache_completed_idempotency__mutmut_8 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_9'] = x__cache_completed_idempotency__mutmut_9 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_10'] = x__cache_completed_idempotency__mutmut_10 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_11'] = x__cache_completed_idempotency__mutmut_11 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_12'] = x__cache_completed_idempotency__mutmut_12 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_13'] = x__cache_completed_idempotency__mutmut_13 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_14'] = x__cache_completed_idempotency__mutmut_14 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_15'] = x__cache_completed_idempotency__mutmut_15 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_16'] = x__cache_completed_idempotency__mutmut_16 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_17'] = x__cache_completed_idempotency__mutmut_17 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_18'] = x__cache_completed_idempotency__mutmut_18 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_19'] = x__cache_completed_idempotency__mutmut_19 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_20'] = x__cache_completed_idempotency__mutmut_20 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_21'] = x__cache_completed_idempotency__mutmut_21 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_22'] = x__cache_completed_idempotency__mutmut_22 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_23'] = x__cache_completed_idempotency__mutmut_23 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_24'] = x__cache_completed_idempotency__mutmut_24 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_25'] = x__cache_completed_idempotency__mutmut_25 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_26'] = x__cache_completed_idempotency__mutmut_26 # type: ignore # mutmut generated
mutants_x__cache_completed_idempotency__mutmut['x__cache_completed_idempotency__mutmut_27'] = x__cache_completed_idempotency__mutmut_27 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut: MutantDict = {}  # type: ignore


class IdempotencyMiddleware(BaseHTTPMiddleware):
    @_mutmut_mutated(mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut)
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_orig(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_1(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(None, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_2(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, None):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_3(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_4(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, ):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_5(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(None)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_6(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = None
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_7(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get(None)
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_8(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("XXIdempotency-KeyXX")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_9(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("idempotency-key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_10(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("IDEMPOTENCY-KEY")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_11(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key and not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_12(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_13(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_14(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(None):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_15(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=None,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_16(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content=None,
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_17(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_18(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_19(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_20(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"XXdetailXX": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_21(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"DETAIL": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_22(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "XXCabecera Idempotency-Key (UUID) obligatoria para operaciones mutablesXX"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_23(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "cabecera idempotency-key (uuid) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_24(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "CABECERA IDEMPOTENCY-KEY (UUID) OBLIGATORIA PARA OPERACIONES MUTABLES"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_25(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = None
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_26(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(None, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_27(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, None, "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_28(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_29(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr("tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_30(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_31(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", )
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_32(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "XXtenant_idXX", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_33(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "TENANT_ID", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_34(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "XXglobalXX")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_35(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "GLOBAL")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_36(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = None
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_37(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(None, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_38(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, None, "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_39(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", None)
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_40(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr("user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_41(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_42(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", )
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_43(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "XXuser_idXX", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_44(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "USER_ID", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_45(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "XXanonymousXX")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_46(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "ANONYMOUS")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_47(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = None

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_48(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = None
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_49(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = None

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_50(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(None, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_51(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, None, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_52(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, None)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_53(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_54(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_55(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, )

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_56(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = None
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_57(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = None
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_58(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(None, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_59(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, None, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_60(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, None)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_61(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_62(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_63(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, )
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_64(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_65(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = None
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_66(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(None)
        await _cache_completed_idempotency(redis, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_67(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(None, redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_68(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, None, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_69(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, None)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_70(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis_key, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_71(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, response)
        return response
    async def xǁIdempotencyMiddlewareǁdispatch__mutmut_72(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _should_bypass_idempotency(request.method, request.url.path):
            return await call_next(request)

        idemp_key = request.headers.get("Idempotency-Key")
        if not idemp_key or not is_valid_uuid(idemp_key):
            return JSONResponse(
                status_code=400,
                content={"detail": "Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables"},
            )

        tenant_id = getattr(request.state, "tenant_id", "global")
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"rg:{tenant_id}:idemp:{user_id}:{idemp_key}"

        body = await request.body()
        req_hash = compute_request_hash(request.method, request.url.path, body)

        redis = get_redis_client()
        conflict_or_replay, _is_new = await check_idempotency_state(redis, redis_key, req_hash)
        if conflict_or_replay is not None:
            return conflict_or_replay

        response = await call_next(request)
        await _cache_completed_idempotency(redis, redis_key, )
        return response

mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['_mutmut_orig'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_orig # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_1'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_1 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_2'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_2 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_3'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_3 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_4'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_4 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_5'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_5 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_6'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_6 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_7'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_7 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_8'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_8 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_9'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_9 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_10'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_10 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_11'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_11 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_12'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_12 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_13'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_13 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_14'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_14 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_15'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_15 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_16'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_16 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_17'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_17 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_18'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_18 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_19'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_19 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_20'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_20 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_21'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_21 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_22'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_22 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_23'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_23 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_24'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_24 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_25'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_25 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_26'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_26 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_27'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_27 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_28'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_28 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_29'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_29 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_30'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_30 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_31'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_31 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_32'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_32 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_33'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_33 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_34'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_34 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_35'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_35 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_36'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_36 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_37'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_37 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_38'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_38 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_39'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_39 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_40'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_40 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_41'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_41 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_42'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_42 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_43'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_43 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_44'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_44 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_45'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_45 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_46'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_46 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_47'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_47 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_48'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_48 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_49'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_49 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_50'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_50 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_51'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_51 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_52'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_52 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_53'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_53 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_54'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_54 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_55'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_55 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_56'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_56 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_57'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_57 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_58'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_58 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_59'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_59 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_60'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_60 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_61'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_61 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_62'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_62 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_63'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_63 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_64'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_64 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_65'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_65 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_66'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_66 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_67'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_67 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_68'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_68 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_69'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_69 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_70'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_70 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_71'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_71 # type: ignore # mutmut generated
mutants_xǁIdempotencyMiddlewareǁdispatch__mutmut['xǁIdempotencyMiddlewareǁdispatch__mutmut_72'] = IdempotencyMiddleware.xǁIdempotencyMiddlewareǁdispatch__mutmut_72 # type: ignore # mutmut generated


async def _iterate_in_memory(chunks: list[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk
