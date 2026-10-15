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
