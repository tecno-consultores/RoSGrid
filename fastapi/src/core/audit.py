# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import hashlib
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

GENESIS_AUDIT_HASH = "0" * 64

_SENSITIVE_FIELD_SUBSTRINGS = (
    "password",
    "secret",
    "token",
    "jwt",
    "authorization",
    "api_key",
    "private_key",
    "secret_key",
    "encryption_key",
    "master_key",
    "preshared_key",
    "wpa_key",
    "private",
)


def _is_sensitive_key(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def sanitize_log_string(value: str | None, max_len: int = 512) -> str | None:
    """Elimina secuencias CRLF y caracteres de control para prevenir Log Injection (DISA STIG V-222444 / OWASP 4.3.10)."""
    if value is None:
        return None
    cleaned = value.replace("\r", " ").replace("\n", " ").replace("\x00", "").replace("\x1b", "")
    return cleaned[:max_len]


def sanitize_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    if isinstance(data, (list, tuple, set)):
        return [sanitize_sensitive_data(item) for item in data]
    if isinstance(data, str):
        return sanitize_log_string(data)
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, (uuid.UUID, datetime, date)):
        return str(data)
    return data


_LOOPBACK_ACTOR_IP = "127.0.0.1"


def audit_actor_from_claims(claims: dict[str, Any], request: Any = None) -> dict[str, Any]:
    """Deriva los campos de actor WORM (tenant, usuario, rol, IP y User-Agent) desde los claims JWT."""
    client = getattr(request, "client", None)
    headers = getattr(request, "headers", {})
    sub = claims.get("sub")
    return {
        "tenant_id": uuid.UUID(str(claims.get("tid"))),
        "actor_user_id": uuid.UUID(str(sub)) if sub else None,
        "actor_username": str(claims.get("username") or sub or "system"),
        "actor_role": claims.get("rol"),
        "actor_ip": getattr(client, "host", None) or _LOOPBACK_ACTOR_IP,
        "actor_user_agent": headers.get("user-agent"),
    }


def compute_audit_record_hash(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


async def write_audit_log(
    session: Any,
    tenant_id: Any,
    actor_username: str,
    actor_role: Any,
    actor_ip: str,
    event_category: str,
    event_action: str,
    actor_user_id: Any = None,
    actor_user_agent: str | None = None,
    router_id: Any = None,
    router_display_name: str | None = None,
    ros_rest_method: str | None = None,
    ros_rest_endpoint: str | None = None,
    idempotency_key: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    status_code: int = 200,
    error_message: str | None = None,
) -> Any:
    """Registra de forma inmutable un evento de auditoría en PostgreSQL calculando el hash WORM encadenado."""
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.models.operations import AuditLog

    if type(session) is AsyncSession:
        await session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:tid))"), {"tid": str(tenant_id)})

    stmt = (
        select(AuditLog.record_sha256_hash)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.seq_num.desc(), AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    raw_prev_hash = res.scalar_one_or_none()
    db_prev_hash = raw_prev_hash if isinstance(raw_prev_hash, str) else None
    tid_key = str(tenant_id)
    raw_in_tx = session.__dict__.get("_rg_in_tx_audit_hash")
    in_tx_hashes: dict[str, tuple[str | None, str]] = raw_in_tx if isinstance(raw_in_tx, dict) else {}
    prev_tuple = in_tx_hashes.get(tid_key)
    if isinstance(prev_tuple, tuple) and len(prev_tuple) == 2 and prev_tuple[0] == db_prev_hash:
        prev_hash = prev_tuple[1]
    else:
        prev_hash = db_prev_hash or GENESIS_AUDIT_HASH

    resolved_username = actor_username
    if actor_user_id and (not resolved_username or str(resolved_username).strip() == str(actor_user_id).strip()):
        try:
            from src.models.core import User

            user_obj = await session.get(User, actor_user_id)
            uname = getattr(user_obj, "username", None)
            if isinstance(uname, str) and uname.strip():
                resolved_username = uname.strip()
        except Exception:
            pass

    resolved_router_name = router_display_name
    if router_id and not resolved_router_name:
        try:
            from src.models.inventory import Router

            router_obj = await session.get(Router, router_id)
            rname = getattr(router_obj, "display_name", None)
            if isinstance(rname, str) and rname.strip():
                resolved_router_name = rname.strip()
        except Exception:
            pass

    safe_username = sanitize_log_string(resolved_username, max_len=64) or "system"
    safe_ua = sanitize_log_string(actor_user_agent, max_len=256)
    safe_err = sanitize_log_string(error_message, max_len=512)
    safe_router_name = sanitize_log_string(resolved_router_name, max_len=128)
    clean_before = sanitize_sensitive_data(before_state) if before_state else None
    clean_after = sanitize_sensitive_data(after_state) if after_state else None

    record_payload = {
        "tenant_id": str(tenant_id),
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_username": safe_username,
        "event_category": event_category,
        "event_action": event_action,
        "router_id": str(router_id) if router_id else None,
        "status_code": status_code,
        "before_state": clean_before,
        "after_state": clean_after,
    }
    rec_hash = compute_audit_record_hash(prev_hash, record_payload)

    log_entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_username=safe_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        actor_user_agent=safe_ua,
        event_category=event_category,
        event_action=event_action,
        router_id=router_id,
        router_display_name=safe_router_name,
        ros_rest_method=ros_rest_method,
        ros_rest_endpoint=ros_rest_endpoint,
        idempotency_key=idempotency_key,
        before_state=clean_before,
        after_state=clean_after,
        status_code=status_code,
        error_message=safe_err,
        prev_record_hash=prev_hash,
        record_sha256_hash=rec_hash,
    )
    session.add(log_entry)
    try:
        in_tx_hashes[tid_key] = (db_prev_hash, rec_hash)
        session.__dict__["_rg_in_tx_audit_hash"] = in_tx_hashes
    except Exception:
        pass
    if type(session) is AsyncSession:
        await session.flush()
    return log_entry
