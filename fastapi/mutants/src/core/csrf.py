# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import hmac
import os
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.config import settings

_EXCLUDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/2fa/verify",
    "/api/v1/auth/refresh",
    "/metrics",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_generate_csrf_token__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_generate_csrf_token__mutmut)
def generate_csrf_token(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_orig(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_1(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = None
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_2(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode(None)
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_3(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret and settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_4(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("XXutf-8XX")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_5(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("UTF-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_6(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = None
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_7(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(None).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_8(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(17).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_9(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = None
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_10(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(None)
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_11(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = None
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_12(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = None
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_13(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(None, payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_14(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, None, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_15(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, None).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_16(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(payload, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_17(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, hashlib.sha256).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"


def x_generate_csrf_token__mutmut_18(session_id: str, tenant_id: str, secret: str | None = None) -> str:
    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    nonce = os.urandom(16).hex()
    issued_epoch = int(time.time())
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    sig = hmac.new(key, payload, ).hexdigest()
    return f"{nonce}.{issued_epoch}.{sig}"

mutants_x_generate_csrf_token__mutmut['_mutmut_orig'] = x_generate_csrf_token__mutmut_orig # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_1'] = x_generate_csrf_token__mutmut_1 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_2'] = x_generate_csrf_token__mutmut_2 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_3'] = x_generate_csrf_token__mutmut_3 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_4'] = x_generate_csrf_token__mutmut_4 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_5'] = x_generate_csrf_token__mutmut_5 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_6'] = x_generate_csrf_token__mutmut_6 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_7'] = x_generate_csrf_token__mutmut_7 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_8'] = x_generate_csrf_token__mutmut_8 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_9'] = x_generate_csrf_token__mutmut_9 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_10'] = x_generate_csrf_token__mutmut_10 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_11'] = x_generate_csrf_token__mutmut_11 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_12'] = x_generate_csrf_token__mutmut_12 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_13'] = x_generate_csrf_token__mutmut_13 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_14'] = x_generate_csrf_token__mutmut_14 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_15'] = x_generate_csrf_token__mutmut_15 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_16'] = x_generate_csrf_token__mutmut_16 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_17'] = x_generate_csrf_token__mutmut_17 # type: ignore # mutmut generated
mutants_x_generate_csrf_token__mutmut['x_generate_csrf_token__mutmut_18'] = x_generate_csrf_token__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_csrf_token__mutmut)
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


def x_validate_csrf_token__mutmut_orig(
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


def x_validate_csrf_token__mutmut_1(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28801
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


def x_validate_csrf_token__mutmut_2(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token and "." not in token:
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


def x_validate_csrf_token__mutmut_3(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if token or "." not in token:
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


def x_validate_csrf_token__mutmut_4(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "XX.XX" not in token:
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


def x_validate_csrf_token__mutmut_5(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." in token:
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


def x_validate_csrf_token__mutmut_6(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return True
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


def x_validate_csrf_token__mutmut_7(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = None
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


def x_validate_csrf_token__mutmut_8(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(None)
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


def x_validate_csrf_token__mutmut_9(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split("XX.XX")
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


def x_validate_csrf_token__mutmut_10(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) == 3:
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


def x_validate_csrf_token__mutmut_11(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 4:
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


def x_validate_csrf_token__mutmut_12(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return True
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


def x_validate_csrf_token__mutmut_13(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, issued_epoch_str, signature = None
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


def x_validate_csrf_token__mutmut_14(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, issued_epoch_str, signature = parts
    try:
        issued_epoch = None
    except ValueError:
        return False

    now = int(time.time())
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_15(
    token: str, session_id: str, tenant_id: str, secret: str | None = None, max_age_seconds: int = 28800
) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, issued_epoch_str, signature = parts
    try:
        issued_epoch = int(None)
    except ValueError:
        return False

    now = int(time.time())
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_16(
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
        return True

    now = int(time.time())
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_17(
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

    now = None
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_18(
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

    now = int(None)
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_19(
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
    if now - issued_epoch > max_age_seconds and issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_20(
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
    if now + issued_epoch > max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_21(
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
    if now - issued_epoch >= max_age_seconds or issued_epoch > now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_22(
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
    if now - issued_epoch > max_age_seconds or issued_epoch >= now + 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_23(
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
    if now - issued_epoch > max_age_seconds or issued_epoch > now - 60:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_24(
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
    if now - issued_epoch > max_age_seconds or issued_epoch > now + 61:
        return False

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_25(
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
        return True

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_26(
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

    key = None
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_27(
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

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode(None)
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_28(
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

    key = (secret and settings.ROSGRID_CSRF_HMAC_SECRET).encode("utf-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_29(
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

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("XXutf-8XX")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_30(
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

    key = (secret or settings.ROSGRID_CSRF_HMAC_SECRET).encode("UTF-8")
    payload = f"{session_id}:{tenant_id}:{nonce}:{issued_epoch}".encode()
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_31(
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
    payload = None
    expected_sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_32(
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
    expected_sig = None
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_33(
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
    expected_sig = hmac.new(None, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_34(
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
    expected_sig = hmac.new(key, None, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_35(
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
    expected_sig = hmac.new(key, payload, None).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_36(
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
    expected_sig = hmac.new(payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_37(
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
    expected_sig = hmac.new(key, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_38(
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
    expected_sig = hmac.new(key, payload, ).hexdigest()
    return hmac.compare_digest(signature, expected_sig)


def x_validate_csrf_token__mutmut_39(
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
    return hmac.compare_digest(None, expected_sig)


def x_validate_csrf_token__mutmut_40(
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
    return hmac.compare_digest(signature, None)


def x_validate_csrf_token__mutmut_41(
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
    return hmac.compare_digest(expected_sig)


def x_validate_csrf_token__mutmut_42(
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
    return hmac.compare_digest(signature, )

mutants_x_validate_csrf_token__mutmut['_mutmut_orig'] = x_validate_csrf_token__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_1'] = x_validate_csrf_token__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_2'] = x_validate_csrf_token__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_3'] = x_validate_csrf_token__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_4'] = x_validate_csrf_token__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_5'] = x_validate_csrf_token__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_6'] = x_validate_csrf_token__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_7'] = x_validate_csrf_token__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_8'] = x_validate_csrf_token__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_9'] = x_validate_csrf_token__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_10'] = x_validate_csrf_token__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_11'] = x_validate_csrf_token__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_12'] = x_validate_csrf_token__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_13'] = x_validate_csrf_token__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_14'] = x_validate_csrf_token__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_15'] = x_validate_csrf_token__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_16'] = x_validate_csrf_token__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_17'] = x_validate_csrf_token__mutmut_17 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_18'] = x_validate_csrf_token__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_19'] = x_validate_csrf_token__mutmut_19 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_20'] = x_validate_csrf_token__mutmut_20 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_21'] = x_validate_csrf_token__mutmut_21 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_22'] = x_validate_csrf_token__mutmut_22 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_23'] = x_validate_csrf_token__mutmut_23 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_24'] = x_validate_csrf_token__mutmut_24 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_25'] = x_validate_csrf_token__mutmut_25 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_26'] = x_validate_csrf_token__mutmut_26 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_27'] = x_validate_csrf_token__mutmut_27 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_28'] = x_validate_csrf_token__mutmut_28 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_29'] = x_validate_csrf_token__mutmut_29 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_30'] = x_validate_csrf_token__mutmut_30 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_31'] = x_validate_csrf_token__mutmut_31 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_32'] = x_validate_csrf_token__mutmut_32 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_33'] = x_validate_csrf_token__mutmut_33 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_34'] = x_validate_csrf_token__mutmut_34 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_35'] = x_validate_csrf_token__mutmut_35 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_36'] = x_validate_csrf_token__mutmut_36 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_37'] = x_validate_csrf_token__mutmut_37 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_38'] = x_validate_csrf_token__mutmut_38 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_39'] = x_validate_csrf_token__mutmut_39 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_40'] = x_validate_csrf_token__mutmut_40 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_41'] = x_validate_csrf_token__mutmut_41 # type: ignore # mutmut generated
mutants_x_validate_csrf_token__mutmut['x_validate_csrf_token__mutmut_42'] = x_validate_csrf_token__mutmut_42 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut: MutantDict = {}  # type: ignore


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    @_mutmut_mutated(mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut)
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_orig(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_1(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS and request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_2(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_3(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path not in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_4(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(None)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_5(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = None
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_6(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(None, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_7(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, None, None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_8(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr("session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_9(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_10(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", )
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_11(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "XXsession_idXX", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_12(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "SESSION_ID", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_13(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = None

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_14(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(None, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_15(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, None, None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_16(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr("tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_17(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_18(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", )

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_19(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "XXtenant_idXX", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_20(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "TENANT_ID", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_21(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = None
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_22(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get(None)
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_23(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("XXX-CSRF-TokenXX")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_24(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("x-csrf-token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_25(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-TOKEN")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_26(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id or (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_27(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id or tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_28(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header and not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_29(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_30(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_31(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(None, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_32(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, None, str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_33(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), None))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_34(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_35(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_36(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), ))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_37(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(None), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_38(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(None)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_39(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=None, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_40(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content=None)

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_41(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_42(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, )

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_43(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=404, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_44(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"XXdetailXX": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_45(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"DETAIL": "Fallo de validación criptográfica CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_46(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "XXFallo de validación criptográfica CSRFXX"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_47(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "fallo de validación criptográfica csrf"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_48(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "FALLO DE VALIDACIÓN CRIPTOGRÁFICA CSRF"})

        return await call_next(request)
    async def xǁCSRFProtectionMiddlewareǁdispatch__mutmut_49(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Si no hay sesión autenticada o viene de un endpoint público no excluido
        session_id = getattr(request.state, "session_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Si aún no tiene session_id adjunto pero tiene header X-CSRF-Token o viene con cookie
        csrf_header = request.headers.get("X-CSRF-Token")
        if (
            session_id
            and tenant_id
            and (not csrf_header or not validate_csrf_token(csrf_header, str(session_id), str(tenant_id)))
        ):
            return JSONResponse(status_code=403, content={"detail": "Fallo de validación criptográfica CSRF"})

        return await call_next(None)

mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['_mutmut_orig'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_orig # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_1'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_1 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_2'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_2 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_3'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_3 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_4'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_4 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_5'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_5 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_6'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_6 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_7'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_7 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_8'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_8 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_9'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_9 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_10'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_10 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_11'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_11 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_12'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_12 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_13'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_13 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_14'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_14 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_15'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_15 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_16'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_16 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_17'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_17 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_18'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_18 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_19'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_19 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_20'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_20 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_21'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_21 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_22'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_22 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_23'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_23 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_24'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_24 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_25'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_25 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_26'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_26 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_27'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_27 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_28'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_28 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_29'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_29 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_30'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_30 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_31'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_31 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_32'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_32 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_33'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_33 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_34'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_34 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_35'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_35 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_36'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_36 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_37'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_37 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_38'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_38 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_39'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_39 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_40'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_40 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_41'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_41 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_42'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_42 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_43'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_43 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_44'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_44 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_45'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_45 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_46'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_46 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_47'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_47 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_48'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_48 # type: ignore # mutmut generated
mutants_xǁCSRFProtectionMiddlewareǁdispatch__mutmut['xǁCSRFProtectionMiddlewareǁdispatch__mutmut_49'] = CSRFProtectionMiddleware.xǁCSRFProtectionMiddlewareǁdispatch__mutmut_49 # type: ignore # mutmut generated
