# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import json
import secrets
import time

from src.redis_layer.client import get_redis_client

SESSION_TTL_SECONDS = 28800  # 8 horas


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_compute_token_hash__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_compute_token_hash__mutmut)
def compute_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def x_compute_token_hash__mutmut_orig(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def x_compute_token_hash__mutmut_1(token: str) -> str:
    return hashlib.sha256(None).hexdigest()


def x_compute_token_hash__mutmut_2(token: str) -> str:
    return hashlib.sha256(token.encode(None)).hexdigest()


def x_compute_token_hash__mutmut_3(token: str) -> str:
    return hashlib.sha256(token.encode("XXutf-8XX")).hexdigest()


def x_compute_token_hash__mutmut_4(token: str) -> str:
    return hashlib.sha256(token.encode("UTF-8")).hexdigest()

mutants_x_compute_token_hash__mutmut['_mutmut_orig'] = x_compute_token_hash__mutmut_orig # type: ignore # mutmut generated
mutants_x_compute_token_hash__mutmut['x_compute_token_hash__mutmut_1'] = x_compute_token_hash__mutmut_1 # type: ignore # mutmut generated
mutants_x_compute_token_hash__mutmut['x_compute_token_hash__mutmut_2'] = x_compute_token_hash__mutmut_2 # type: ignore # mutmut generated
mutants_x_compute_token_hash__mutmut['x_compute_token_hash__mutmut_3'] = x_compute_token_hash__mutmut_3 # type: ignore # mutmut generated
mutants_x_compute_token_hash__mutmut['x_compute_token_hash__mutmut_4'] = x_compute_token_hash__mutmut_4 # type: ignore # mutmut generated
mutants_x_create_session__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_create_session__mutmut)
async def create_session(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_orig(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_1(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = None
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_2(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(None)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_3(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(17)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_4(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = None
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_5(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(None)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_6(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(17)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_7(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = None
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_8(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(None)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_9(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(33)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_10(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = None

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_11(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(None)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_12(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = None
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_13(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = None
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_14(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(None)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_15(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = None

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_16(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime(None, time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_17(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", None)

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_18(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime(time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_19(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", )

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_20(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("XX%Y-%m-%dT%H:%M:%SZXX", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_21(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%y-%m-%dt%h:%m:%sz", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_22(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%M-%DT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_23(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(None))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_24(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = None

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_25(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "XXsession_idXX": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_26(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "SESSION_ID": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_27(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "XXuser_idXX": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_28(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "USER_ID": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_29(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "XXusernameXX": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_30(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "USERNAME": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_31(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "XXfull_nameXX": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_32(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "FULL_NAME": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_33(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "XXroleXX": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_34(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "ROLE": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_35(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "XXip_addressXX": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_36(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "IP_ADDRESS": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_37(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "XXuser_agentXX": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_38(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "USER_AGENT": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_39(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "XXcurrent_router_idXX": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_40(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "CURRENT_ROUTER_ID": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_41(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "XXXX",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_42(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "XXcurrent_router_nameXX": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_43(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "CURRENT_ROUTER_NAME": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_44(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "XXXX",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_45(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "XXcurrent_view_pathXX": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_46(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "CURRENT_VIEW_PATH": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_47(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "XX/dashboardXX",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_48(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/DASHBOARD",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_49(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "XXcreated_atXX": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_50(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "CREATED_AT": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_51(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "XXlast_activity_atXX": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_52(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "LAST_ACTIVITY_AT": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_53(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "XXrefresh_family_idXX": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_54(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "REFRESH_FAMILY_ID": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_55(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = None
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_56(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = None
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_57(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = None
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_58(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = None

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_59(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = None
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_60(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(None, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_61(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=None)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_62(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_63(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, )  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_64(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(None, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_65(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, None)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_66(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_67(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, )

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_68(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        None,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_69(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping=None,
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_70(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_71(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_72(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "XXcurrent_rt_hashXX": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_73(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "CURRENT_RT_HASH": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_74(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "XXused_rt_hashesXX": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_75(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "USED_RT_HASHES": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_76(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps(None),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_77(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "XXuser_idXX": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_78(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "USER_ID": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_79(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "XXsession_idXX": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_80(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "SESSION_ID": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_81(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(None, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_82(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, None)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_83(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_84(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, )

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_85(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(None, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_86(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, None)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_87(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_88(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, )
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_89(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(None, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_90(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, None)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_91(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_92(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, )

    pipe.zadd(active_sess_key, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_93(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(None, {session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_94(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, None)
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_95(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd({session_id: float(now_epoch)})
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_96(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, )
    await pipe.execute()

    return session_id, family_id, initial_rt


async def x_create_session__mutmut_97(
    tenant_id: str,
    user_id: str,
    username: str,
    full_name: str,
    role: str,
    ip_address: str,
    user_agent: str,
) -> tuple[str, str, str]:
    session_id = secrets.token_hex(16)
    family_id = secrets.token_hex(16)
    initial_rt = secrets.token_urlsafe(32)
    initial_rt_hash = compute_token_hash(initial_rt)

    redis = get_redis_client()
    now_epoch = int(time.time())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch))

    session_mapping = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "current_router_id": "",
        "current_router_name": "",
        "current_view_path": "/dashboard",
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }

    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    active_sess_key = f"rg:{tenant_id}:active_sessions"

    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=session_mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, SESSION_TTL_SECONDS)

    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": initial_rt_hash,
            "used_rt_hashes": json.dumps([]),
            "user_id": user_id,
            "session_id": session_id,
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)

    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, SESSION_TTL_SECONDS)

    pipe.zadd(active_sess_key, {session_id: float(None)})
    await pipe.execute()

    return session_id, family_id, initial_rt

mutants_x_create_session__mutmut['_mutmut_orig'] = x_create_session__mutmut_orig # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_1'] = x_create_session__mutmut_1 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_2'] = x_create_session__mutmut_2 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_3'] = x_create_session__mutmut_3 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_4'] = x_create_session__mutmut_4 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_5'] = x_create_session__mutmut_5 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_6'] = x_create_session__mutmut_6 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_7'] = x_create_session__mutmut_7 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_8'] = x_create_session__mutmut_8 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_9'] = x_create_session__mutmut_9 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_10'] = x_create_session__mutmut_10 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_11'] = x_create_session__mutmut_11 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_12'] = x_create_session__mutmut_12 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_13'] = x_create_session__mutmut_13 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_14'] = x_create_session__mutmut_14 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_15'] = x_create_session__mutmut_15 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_16'] = x_create_session__mutmut_16 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_17'] = x_create_session__mutmut_17 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_18'] = x_create_session__mutmut_18 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_19'] = x_create_session__mutmut_19 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_20'] = x_create_session__mutmut_20 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_21'] = x_create_session__mutmut_21 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_22'] = x_create_session__mutmut_22 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_23'] = x_create_session__mutmut_23 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_24'] = x_create_session__mutmut_24 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_25'] = x_create_session__mutmut_25 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_26'] = x_create_session__mutmut_26 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_27'] = x_create_session__mutmut_27 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_28'] = x_create_session__mutmut_28 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_29'] = x_create_session__mutmut_29 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_30'] = x_create_session__mutmut_30 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_31'] = x_create_session__mutmut_31 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_32'] = x_create_session__mutmut_32 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_33'] = x_create_session__mutmut_33 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_34'] = x_create_session__mutmut_34 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_35'] = x_create_session__mutmut_35 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_36'] = x_create_session__mutmut_36 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_37'] = x_create_session__mutmut_37 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_38'] = x_create_session__mutmut_38 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_39'] = x_create_session__mutmut_39 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_40'] = x_create_session__mutmut_40 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_41'] = x_create_session__mutmut_41 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_42'] = x_create_session__mutmut_42 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_43'] = x_create_session__mutmut_43 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_44'] = x_create_session__mutmut_44 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_45'] = x_create_session__mutmut_45 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_46'] = x_create_session__mutmut_46 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_47'] = x_create_session__mutmut_47 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_48'] = x_create_session__mutmut_48 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_49'] = x_create_session__mutmut_49 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_50'] = x_create_session__mutmut_50 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_51'] = x_create_session__mutmut_51 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_52'] = x_create_session__mutmut_52 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_53'] = x_create_session__mutmut_53 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_54'] = x_create_session__mutmut_54 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_55'] = x_create_session__mutmut_55 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_56'] = x_create_session__mutmut_56 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_57'] = x_create_session__mutmut_57 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_58'] = x_create_session__mutmut_58 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_59'] = x_create_session__mutmut_59 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_60'] = x_create_session__mutmut_60 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_61'] = x_create_session__mutmut_61 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_62'] = x_create_session__mutmut_62 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_63'] = x_create_session__mutmut_63 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_64'] = x_create_session__mutmut_64 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_65'] = x_create_session__mutmut_65 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_66'] = x_create_session__mutmut_66 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_67'] = x_create_session__mutmut_67 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_68'] = x_create_session__mutmut_68 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_69'] = x_create_session__mutmut_69 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_70'] = x_create_session__mutmut_70 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_71'] = x_create_session__mutmut_71 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_72'] = x_create_session__mutmut_72 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_73'] = x_create_session__mutmut_73 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_74'] = x_create_session__mutmut_74 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_75'] = x_create_session__mutmut_75 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_76'] = x_create_session__mutmut_76 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_77'] = x_create_session__mutmut_77 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_78'] = x_create_session__mutmut_78 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_79'] = x_create_session__mutmut_79 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_80'] = x_create_session__mutmut_80 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_81'] = x_create_session__mutmut_81 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_82'] = x_create_session__mutmut_82 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_83'] = x_create_session__mutmut_83 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_84'] = x_create_session__mutmut_84 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_85'] = x_create_session__mutmut_85 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_86'] = x_create_session__mutmut_86 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_87'] = x_create_session__mutmut_87 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_88'] = x_create_session__mutmut_88 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_89'] = x_create_session__mutmut_89 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_90'] = x_create_session__mutmut_90 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_91'] = x_create_session__mutmut_91 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_92'] = x_create_session__mutmut_92 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_93'] = x_create_session__mutmut_93 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_94'] = x_create_session__mutmut_94 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_95'] = x_create_session__mutmut_95 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_96'] = x_create_session__mutmut_96 # type: ignore # mutmut generated
mutants_x_create_session__mutmut['x_create_session__mutmut_97'] = x_create_session__mutmut_97 # type: ignore # mutmut generated
mutants_x_get_session__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_session__mutmut)
async def get_session(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_orig(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_1(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = None
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_2(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = None
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_3(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = None
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_4(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(None)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_5(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def x_get_session__mutmut_6(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(None): str(v) for k, v in data.items()}


async def x_get_session__mutmut_7(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(None) for k, v in data.items()}

mutants_x_get_session__mutmut['_mutmut_orig'] = x_get_session__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_1'] = x_get_session__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_2'] = x_get_session__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_3'] = x_get_session__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_4'] = x_get_session__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_5'] = x_get_session__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_6'] = x_get_session__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_session__mutmut['x_get_session__mutmut_7'] = x_get_session__mutmut_7 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_kill_session__mutmut)
async def kill_session(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_orig(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_1(
    tenant_id: str, session_id: str, killed_by: str = "XXSYSTEMXX", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_2(
    tenant_id: str, session_id: str, killed_by: str = "system", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_3(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "XXRevocación manualXX"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_4(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_5(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "REVOCACIÓN MANUAL"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_6(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = None
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_7(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = None
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_8(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = None
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_9(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(None)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_10(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_11(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return True

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_12(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = None
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_13(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(None)
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_14(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get(None, ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_15(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", None))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_16(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get(""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_17(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_18(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("XXuser_idXX", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_19(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("USER_ID", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_20(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", "XXXX"))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_21(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = None

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_22(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(None)

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_23(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get(None, ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_24(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", None))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_25(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get(""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_26(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_27(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("XXrefresh_family_idXX", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_28(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("REFRESH_FAMILY_ID", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_29(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", "XXXX"))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_30(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = None
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_31(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(None)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_32(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(None)
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_33(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(None, session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_34(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", None)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_35(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_36(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", )
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_37(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(None, session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_38(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", None)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_39(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_40(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", )

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_41(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = None
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_42(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        None
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_43(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "XXeventXX": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_44(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "EVENT": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_45(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "XXSESSION_KILLEDXX",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_46(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "session_killed",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_47(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "XXtarget_session_idXX": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_48(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "TARGET_SESSION_ID": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_49(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "XXtarget_user_idXX": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_50(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "TARGET_USER_ID": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_51(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "XXreasonXX": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_52(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "REASON": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_53(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "XXkilled_byXX": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_54(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "KILLED_BY": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_55(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(None, event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_56(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", None)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_57(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(event_payload)
    await pipe.execute()
    return True


async def x_kill_session__mutmut_58(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", )
    await pipe.execute()
    return True


async def x_kill_session__mutmut_59(
    tenant_id: str, session_id: str, killed_by: str = "SYSTEM", reason: str = "Revocación manual"
) -> bool:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    session_data = await redis.hgetall(sess_key)
    if not session_data:
        return False

    user_id = str(session_data.get("user_id", ""))
    family_id = str(session_data.get("refresh_family_id", ""))

    pipe = redis.pipeline()
    pipe.delete(sess_key)
    if family_id:
        pipe.delete(f"rg:{tenant_id}:rt_family:{family_id}")
    if user_id:
        pipe.srem(f"rg:{tenant_id}:user_sessions:{user_id}", session_id)
    pipe.zrem(f"rg:{tenant_id}:active_sessions", session_id)

    event_payload = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
    )
    pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)
    await pipe.execute()
    return False

mutants_x_kill_session__mutmut['_mutmut_orig'] = x_kill_session__mutmut_orig # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_1'] = x_kill_session__mutmut_1 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_2'] = x_kill_session__mutmut_2 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_3'] = x_kill_session__mutmut_3 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_4'] = x_kill_session__mutmut_4 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_5'] = x_kill_session__mutmut_5 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_6'] = x_kill_session__mutmut_6 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_7'] = x_kill_session__mutmut_7 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_8'] = x_kill_session__mutmut_8 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_9'] = x_kill_session__mutmut_9 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_10'] = x_kill_session__mutmut_10 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_11'] = x_kill_session__mutmut_11 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_12'] = x_kill_session__mutmut_12 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_13'] = x_kill_session__mutmut_13 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_14'] = x_kill_session__mutmut_14 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_15'] = x_kill_session__mutmut_15 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_16'] = x_kill_session__mutmut_16 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_17'] = x_kill_session__mutmut_17 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_18'] = x_kill_session__mutmut_18 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_19'] = x_kill_session__mutmut_19 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_20'] = x_kill_session__mutmut_20 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_21'] = x_kill_session__mutmut_21 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_22'] = x_kill_session__mutmut_22 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_23'] = x_kill_session__mutmut_23 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_24'] = x_kill_session__mutmut_24 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_25'] = x_kill_session__mutmut_25 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_26'] = x_kill_session__mutmut_26 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_27'] = x_kill_session__mutmut_27 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_28'] = x_kill_session__mutmut_28 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_29'] = x_kill_session__mutmut_29 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_30'] = x_kill_session__mutmut_30 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_31'] = x_kill_session__mutmut_31 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_32'] = x_kill_session__mutmut_32 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_33'] = x_kill_session__mutmut_33 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_34'] = x_kill_session__mutmut_34 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_35'] = x_kill_session__mutmut_35 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_36'] = x_kill_session__mutmut_36 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_37'] = x_kill_session__mutmut_37 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_38'] = x_kill_session__mutmut_38 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_39'] = x_kill_session__mutmut_39 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_40'] = x_kill_session__mutmut_40 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_41'] = x_kill_session__mutmut_41 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_42'] = x_kill_session__mutmut_42 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_43'] = x_kill_session__mutmut_43 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_44'] = x_kill_session__mutmut_44 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_45'] = x_kill_session__mutmut_45 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_46'] = x_kill_session__mutmut_46 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_47'] = x_kill_session__mutmut_47 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_48'] = x_kill_session__mutmut_48 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_49'] = x_kill_session__mutmut_49 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_50'] = x_kill_session__mutmut_50 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_51'] = x_kill_session__mutmut_51 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_52'] = x_kill_session__mutmut_52 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_53'] = x_kill_session__mutmut_53 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_54'] = x_kill_session__mutmut_54 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_55'] = x_kill_session__mutmut_55 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_56'] = x_kill_session__mutmut_56 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_57'] = x_kill_session__mutmut_57 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_58'] = x_kill_session__mutmut_58 # type: ignore # mutmut generated
mutants_x_kill_session__mutmut['x_kill_session__mutmut_59'] = x_kill_session__mutmut_59 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_kill_all_user_sessions__mutmut)
async def kill_all_user_sessions(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_orig(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_1(
    tenant_id: str, user_id: str, killed_by: str = "XXSYSTEMXX", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_2(
    tenant_id: str, user_id: str, killed_by: str = "system", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_3(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "XXKill-Switch global de usuarioXX"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_4(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "kill-switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_5(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "KILL-SWITCH GLOBAL DE USUARIO"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_6(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = None
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_7(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = None
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_8(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = None
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_9(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(None)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_10(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = None
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_11(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 1
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_12(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(None, str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_13(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, None, killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_14(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=None, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_15(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=None):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_16(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(str(sid), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_17(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_18(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_19(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, ):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_20(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(None), killed_by=killed_by, reason=reason):
            count += 1
    return count


async def x_kill_all_user_sessions__mutmut_21(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count = 1
    return count


async def x_kill_all_user_sessions__mutmut_22(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count -= 1
    return count


async def x_kill_all_user_sessions__mutmut_23(
    tenant_id: str, user_id: str, killed_by: str = "SYSTEM", reason: str = "Kill-Switch global de usuario"
) -> int:
    redis = get_redis_client()
    user_sess_key = f"rg:{tenant_id}:user_sessions:{user_id}"
    session_ids = await redis.smembers(user_sess_key)
    count = 0
    for sid in session_ids:
        if await kill_session(tenant_id, str(sid), killed_by=killed_by, reason=reason):
            count += 2
    return count

mutants_x_kill_all_user_sessions__mutmut['_mutmut_orig'] = x_kill_all_user_sessions__mutmut_orig # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_1'] = x_kill_all_user_sessions__mutmut_1 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_2'] = x_kill_all_user_sessions__mutmut_2 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_3'] = x_kill_all_user_sessions__mutmut_3 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_4'] = x_kill_all_user_sessions__mutmut_4 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_5'] = x_kill_all_user_sessions__mutmut_5 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_6'] = x_kill_all_user_sessions__mutmut_6 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_7'] = x_kill_all_user_sessions__mutmut_7 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_8'] = x_kill_all_user_sessions__mutmut_8 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_9'] = x_kill_all_user_sessions__mutmut_9 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_10'] = x_kill_all_user_sessions__mutmut_10 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_11'] = x_kill_all_user_sessions__mutmut_11 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_12'] = x_kill_all_user_sessions__mutmut_12 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_13'] = x_kill_all_user_sessions__mutmut_13 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_14'] = x_kill_all_user_sessions__mutmut_14 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_15'] = x_kill_all_user_sessions__mutmut_15 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_16'] = x_kill_all_user_sessions__mutmut_16 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_17'] = x_kill_all_user_sessions__mutmut_17 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_18'] = x_kill_all_user_sessions__mutmut_18 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_19'] = x_kill_all_user_sessions__mutmut_19 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_20'] = x_kill_all_user_sessions__mutmut_20 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_21'] = x_kill_all_user_sessions__mutmut_21 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_22'] = x_kill_all_user_sessions__mutmut_22 # type: ignore # mutmut generated
mutants_x_kill_all_user_sessions__mutmut['x_kill_all_user_sessions__mutmut_23'] = x_kill_all_user_sessions__mutmut_23 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_rotate_refresh_token__mutmut)
async def rotate_refresh_token(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_orig(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_1(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = None
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_2(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = None
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_3(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = None
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_4(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(None)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_5(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_6(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return True, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_7(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "XXEXPIRED_FAMILYXX", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_8(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "expired_family", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_9(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = None
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_10(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(None)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_11(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = None
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_12(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(None)
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_13(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get(None, ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_14(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", None))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_15(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get(""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_16(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_17(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("XXcurrent_rt_hashXX", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_18(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("CURRENT_RT_HASH", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_19(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", "XXXX"))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_20(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = None

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_21(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(None)

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_22(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get(None, "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_23(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", None))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_24(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_25(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", ))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_26(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("XXused_rt_hashesXX", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_27(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("USED_RT_HASHES", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_28(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "XX[]XX"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_29(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = None
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_30(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(None)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_31(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = None

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_32(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash not in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_33(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = None
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_34(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(None)
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_35(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get(None, ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_36(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", None))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_37(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get(""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_38(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_39(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("XXsession_idXX", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_40(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("SESSION_ID", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_41(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", "XXXX"))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_42(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(None, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_43(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, None, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_44(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by=None, reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_45(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason=None)
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_46(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_47(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_48(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_49(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", )
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_50(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="XXSECURITY_ROBOTXX", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_51(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="security_robot", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_52(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="XXReúso de Refresh Token detectadoXX")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_53(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="reúso de refresh token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_54(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="REÚSO DE REFRESH TOKEN DETECTADO")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_55(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return True, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_56(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "XXREUSE_DETECTEDXX", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_57(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "reuse_detected", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_58(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash == current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_59(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return True, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_60(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "XXHASH_MISMATCHXX", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_61(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "hash_mismatch", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_62(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = None
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_63(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(None)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_64(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(33)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_65(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = None
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_66(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(None)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_67(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(None)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_68(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = None
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_69(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        None,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_70(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping=None,
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_71(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_72(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_73(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "XXcurrent_rt_hashXX": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_74(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "CURRENT_RT_HASH": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_75(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "XXused_rt_hashesXX": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_76(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "USED_RT_HASHES": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_77(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(None),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_78(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(None, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_79(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, None)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_80(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_81(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, )
    await pipe.execute()

    return True, None, new_token


async def x_rotate_refresh_token__mutmut_82(
    tenant_id: str, family_id: str, received_token: str
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    if received_hash in used_hashes:
        # ROBO DE TOKEN DETECTADO -> Kill Switch inmediato
        session_id = str(family_data.get("session_id", ""))
        await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
        return False, "REUSE_DETECTED", None

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "used_rt_hashes": json.dumps(used_hashes),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return False, None, new_token

mutants_x_rotate_refresh_token__mutmut['_mutmut_orig'] = x_rotate_refresh_token__mutmut_orig # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_1'] = x_rotate_refresh_token__mutmut_1 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_2'] = x_rotate_refresh_token__mutmut_2 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_3'] = x_rotate_refresh_token__mutmut_3 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_4'] = x_rotate_refresh_token__mutmut_4 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_5'] = x_rotate_refresh_token__mutmut_5 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_6'] = x_rotate_refresh_token__mutmut_6 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_7'] = x_rotate_refresh_token__mutmut_7 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_8'] = x_rotate_refresh_token__mutmut_8 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_9'] = x_rotate_refresh_token__mutmut_9 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_10'] = x_rotate_refresh_token__mutmut_10 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_11'] = x_rotate_refresh_token__mutmut_11 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_12'] = x_rotate_refresh_token__mutmut_12 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_13'] = x_rotate_refresh_token__mutmut_13 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_14'] = x_rotate_refresh_token__mutmut_14 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_15'] = x_rotate_refresh_token__mutmut_15 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_16'] = x_rotate_refresh_token__mutmut_16 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_17'] = x_rotate_refresh_token__mutmut_17 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_18'] = x_rotate_refresh_token__mutmut_18 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_19'] = x_rotate_refresh_token__mutmut_19 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_20'] = x_rotate_refresh_token__mutmut_20 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_21'] = x_rotate_refresh_token__mutmut_21 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_22'] = x_rotate_refresh_token__mutmut_22 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_23'] = x_rotate_refresh_token__mutmut_23 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_24'] = x_rotate_refresh_token__mutmut_24 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_25'] = x_rotate_refresh_token__mutmut_25 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_26'] = x_rotate_refresh_token__mutmut_26 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_27'] = x_rotate_refresh_token__mutmut_27 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_28'] = x_rotate_refresh_token__mutmut_28 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_29'] = x_rotate_refresh_token__mutmut_29 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_30'] = x_rotate_refresh_token__mutmut_30 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_31'] = x_rotate_refresh_token__mutmut_31 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_32'] = x_rotate_refresh_token__mutmut_32 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_33'] = x_rotate_refresh_token__mutmut_33 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_34'] = x_rotate_refresh_token__mutmut_34 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_35'] = x_rotate_refresh_token__mutmut_35 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_36'] = x_rotate_refresh_token__mutmut_36 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_37'] = x_rotate_refresh_token__mutmut_37 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_38'] = x_rotate_refresh_token__mutmut_38 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_39'] = x_rotate_refresh_token__mutmut_39 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_40'] = x_rotate_refresh_token__mutmut_40 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_41'] = x_rotate_refresh_token__mutmut_41 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_42'] = x_rotate_refresh_token__mutmut_42 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_43'] = x_rotate_refresh_token__mutmut_43 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_44'] = x_rotate_refresh_token__mutmut_44 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_45'] = x_rotate_refresh_token__mutmut_45 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_46'] = x_rotate_refresh_token__mutmut_46 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_47'] = x_rotate_refresh_token__mutmut_47 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_48'] = x_rotate_refresh_token__mutmut_48 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_49'] = x_rotate_refresh_token__mutmut_49 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_50'] = x_rotate_refresh_token__mutmut_50 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_51'] = x_rotate_refresh_token__mutmut_51 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_52'] = x_rotate_refresh_token__mutmut_52 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_53'] = x_rotate_refresh_token__mutmut_53 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_54'] = x_rotate_refresh_token__mutmut_54 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_55'] = x_rotate_refresh_token__mutmut_55 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_56'] = x_rotate_refresh_token__mutmut_56 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_57'] = x_rotate_refresh_token__mutmut_57 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_58'] = x_rotate_refresh_token__mutmut_58 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_59'] = x_rotate_refresh_token__mutmut_59 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_60'] = x_rotate_refresh_token__mutmut_60 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_61'] = x_rotate_refresh_token__mutmut_61 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_62'] = x_rotate_refresh_token__mutmut_62 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_63'] = x_rotate_refresh_token__mutmut_63 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_64'] = x_rotate_refresh_token__mutmut_64 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_65'] = x_rotate_refresh_token__mutmut_65 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_66'] = x_rotate_refresh_token__mutmut_66 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_67'] = x_rotate_refresh_token__mutmut_67 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_68'] = x_rotate_refresh_token__mutmut_68 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_69'] = x_rotate_refresh_token__mutmut_69 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_70'] = x_rotate_refresh_token__mutmut_70 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_71'] = x_rotate_refresh_token__mutmut_71 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_72'] = x_rotate_refresh_token__mutmut_72 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_73'] = x_rotate_refresh_token__mutmut_73 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_74'] = x_rotate_refresh_token__mutmut_74 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_75'] = x_rotate_refresh_token__mutmut_75 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_76'] = x_rotate_refresh_token__mutmut_76 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_77'] = x_rotate_refresh_token__mutmut_77 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_78'] = x_rotate_refresh_token__mutmut_78 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_79'] = x_rotate_refresh_token__mutmut_79 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_80'] = x_rotate_refresh_token__mutmut_80 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_81'] = x_rotate_refresh_token__mutmut_81 # type: ignore # mutmut generated
mutants_x_rotate_refresh_token__mutmut['x_rotate_refresh_token__mutmut_82'] = x_rotate_refresh_token__mutmut_82 # type: ignore # mutmut generated
