# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import hashlib
import json
from typing import Any

GENESIS_AUDIT_HASH = "0" * 64

_SENSITIVE_FIELD_SUBSTRINGS = (
    "password",
    "secret",
    "token",
    "jwt",
    "authorization",
    "key",
    "private",
)


def _is_sensitive_key(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def sanitize_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


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
    from sqlalchemy import select
    from src.models.operations import AuditLog

    stmt = (
        select(AuditLog.record_sha256_hash)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    prev_hash = res.scalar_one_or_none() or GENESIS_AUDIT_HASH

    clean_before = sanitize_sensitive_data(before_state) if before_state else None
    clean_after = sanitize_sensitive_data(after_state) if after_state else None

    record_payload = {
        "tenant_id": str(tenant_id),
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_username": actor_username,
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
        actor_username=actor_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        actor_user_agent=actor_user_agent,
        event_category=event_category,
        event_action=event_action,
        router_id=router_id,
        router_display_name=router_display_name,
        ros_rest_method=ros_rest_method,
        ros_rest_endpoint=ros_rest_endpoint,
        idempotency_key=idempotency_key,
        before_state=clean_before,
        after_state=clean_after,
        status_code=status_code,
        error_message=error_message,
        prev_record_hash=prev_hash,
        record_sha256_hash=rec_hash,
    )
    session.add(log_entry)
    return log_entry

