# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import asyncio
import hashlib
import json
import secrets
import time
from typing import Any

from src.core.config import settings
from src.redis_layer.client import get_redis_client

SESSION_TTL_SECONDS = 28800  # 8 horas


def compute_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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


async def get_session(tenant_id: str, session_id: str) -> dict[str, str] | None:
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    data = await redis.hgetall(sess_key)
    if not data:
        return None
    return {str(k): str(v) for k, v in data.items()}


async def kill_session(
    tenant_id: str,
    session_id: str,
    killed_by: str = "SYSTEM",
    reason: str = "Revocación manual",
    notify_ws: bool = True,
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

    if notify_ws:
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


async def _handle_token_reuse(
    tenant_id: str,
    family_data: dict[Any, Any],
    received_hash: str,
    used_hashes_timed: dict[str, Any],
    grace_period_seconds: int,
) -> tuple[bool, str | None, str | None]:
    now = int(time.time())
    rotation_ts = used_hashes_timed.get(received_hash)
    if rotation_ts is not None and grace_period_seconds > 0 and (now - int(rotation_ts) <= grace_period_seconds):
        last_issued = family_data.get("last_issued_rt")
        if last_issued:
            return True, None, str(last_issued)

    session_id = str(family_data.get("session_id", ""))
    await kill_session(tenant_id, session_id, killed_by="SECURITY_ROBOT", reason="Reúso de Refresh Token detectado")
    return False, "REUSE_DETECTED", None


async def rotate_refresh_token(
    tenant_id: str,
    family_id: str,
    received_token: str,
    grace_period_seconds: int | None = None,
) -> tuple[bool, str | None, str | None]:
    redis = get_redis_client()
    rt_key = f"rg:{tenant_id}:rt_family:{family_id}"
    family_data = await redis.hgetall(rt_key)
    if not family_data:
        return False, "EXPIRED_FAMILY", None

    received_hash = compute_token_hash(received_token)
    current_hash = str(family_data.get("current_rt_hash", ""))
    used_hashes_str = str(family_data.get("used_rt_hashes", "[]"))
    used_hashes_timed_str = str(family_data.get("used_rt_hashes_timed", "{}"))

    try:
        used_hashes = json.loads(used_hashes_str)
    except json.JSONDecodeError:
        used_hashes = []

    try:
        used_hashes_timed = json.loads(used_hashes_timed_str)
    except json.JSONDecodeError:
        used_hashes_timed = {}

    if grace_period_seconds is None:
        grace_period_seconds = settings.ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS

    now = int(time.time())

    if received_hash in used_hashes or received_hash in used_hashes_timed:
        return await _handle_token_reuse(tenant_id, family_data, received_hash, used_hashes_timed, grace_period_seconds)

    if received_hash != current_hash:
        return False, "HASH_MISMATCH", None

    new_token = secrets.token_urlsafe(32)
    new_token_hash = compute_token_hash(new_token)
    used_hashes.append(received_hash)
    used_hashes_timed[received_hash] = now

    pipe = redis.pipeline()
    pipe.hset(
        rt_key,
        mapping={
            "current_rt_hash": new_token_hash,
            "last_issued_rt": new_token,
            "used_rt_hashes": json.dumps(used_hashes),
            "used_rt_hashes_timed": json.dumps(used_hashes_timed),
        },
    )
    pipe.expire(rt_key, SESSION_TTL_SECONDS)
    await pipe.execute()

    return True, None, new_token


CLOSING_GRACE_PERIOD_SECONDS = 35


async def mark_session_closing(
    tenant_id: str, session_id: str, grace_seconds: int = CLOSING_GRACE_PERIOD_SECONDS
) -> bool:
    """Marca una sesión en estado de cierre temporal (período de gracia ante cierre de pestaña/navegador).

    Crea una clave efímera rg:{tenant_id}:sess_closing:{session_id} con TTL de gracia (35s)
    y la registra en el Sorted Set rg:{tenant_id}:closing_sessions_zset.
    """
    redis = get_redis_client()
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    exists = await redis.exists(sess_key)
    if not exists:
        return False

    closing_key = f"rg:{tenant_id}:sess_closing:{session_id}"
    zset_key = f"rg:{tenant_id}:closing_sessions_zset"
    now_epoch = int(time.time())
    expires_at = now_epoch + grace_seconds

    pipe = redis.pipeline()
    pipe.set(closing_key, str(expires_at), ex=grace_seconds)
    pipe.zadd(zset_key, {session_id: float(expires_at)})
    await pipe.execute()
    return True


async def cancel_session_closing(tenant_id: str, session_id: str) -> bool:
    """Cancela el período de gracia de cierre de sesión ante reactivación de pestañas."""
    redis = get_redis_client()
    closing_key = f"rg:{tenant_id}:sess_closing:{session_id}"
    zset_key = f"rg:{tenant_id}:closing_sessions_zset"

    try:
        pipeline_fn = getattr(redis, "pipeline", None)
        if callable(pipeline_fn):
            pipe = pipeline_fn()
            # Si pipeline() devolvió una corrutina (ej. en ciertos mocks)
            if asyncio.iscoroutine(pipe):
                pipe = await pipe
            if hasattr(pipe, "delete") and hasattr(pipe, "zrem") and hasattr(pipe, "execute"):
                pipe.delete(closing_key)
                pipe.zrem(zset_key, session_id)
                res = pipe.execute()
                results = await res if asyncio.iscoroutine(res) else res
                return bool(results and len(results) > 0 and results[0] > 0)
        await redis.delete(closing_key)
        await redis.zrem(zset_key, session_id)
        return True
    except Exception:
        return False


async def is_session_closing(tenant_id: str, session_id: str) -> bool:
    """Verifica si una sesión se encuentra actualmente en período de gracia de cierre."""
    redis = get_redis_client()
    closing_key = f"rg:{tenant_id}:sess_closing:{session_id}"
    return bool(await redis.exists(closing_key))


async def sweep_expired_closing_sessions(tenant_id: str) -> list[str]:
    """Identifica y revoca sesiones cuyo período de gracia de cierre ha expirado en KeyDB.

    Elimina de Redis las sesiones que no tuvieron reactivación dentro de los 35 segundos.
    """
    redis = get_redis_client()
    zset_key = f"rg:{tenant_id}:closing_sessions_zset"
    now_epoch = int(time.time())

    # Obtener sesiones candidatas cuyo expires_at <= now_epoch
    expired_candidates = await redis.zrangebyscore(zset_key, min="-inf", max=now_epoch)
    if not expired_candidates:
        return []

    closed_sessions: list[str] = []
    for sid_raw in expired_candidates:
        sid = sid_raw.decode("utf-8") if isinstance(sid_raw, bytes) else str(sid_raw)
        closing_key = f"rg:{tenant_id}:sess_closing:{sid}"
        is_still_closing = await redis.exists(closing_key)
        # Si la clave con TTL ya expiró en Redis (o ya venció su tiempo)
        if not is_still_closing:
            await kill_session(
                tenant_id,
                sid,
                killed_by="SESSION_LIFECYCLE_WORKER",
                reason="Liberación automática por cierre de pestaña/navegador (Gracia 35s expirada)",
            )
            closed_sessions.append(sid)

        await redis.zrem(zset_key, sid)

    return closed_sessions

