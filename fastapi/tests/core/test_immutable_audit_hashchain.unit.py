# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from src.core.audit import (
    GENESIS_AUDIT_HASH,
    compute_audit_record_hash,
    sanitize_log_string,
    sanitize_sensitive_data,
)


def test_genesis_audit_hash() -> None:
    assert len(GENESIS_AUDIT_HASH) == 64
    assert GENESIS_AUDIT_HASH == "0" * 64


def test_sanitize_sensitive_data_keys() -> None:
    payload = {
        "username": "admin",
        "password": "ClearTextPassword123",
        "api_secret": "my-secret-key",
        "access_token": "jwt.header.payload.sig",
        "authorization": "Bearer xxx",
        "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----",
        "safe_field": 42,
        "nested": {
            "token_expiration": 3600,
            "secret_answer": "blue",
            "normal_key_value": "hello",
        },
        "items": [
            {"user_key": "abc", "status": "active"},
            "plain_string",
        ],
    }

    sanitized = sanitize_sensitive_data(payload)

    assert sanitized["username"] == "admin"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_secret"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["ssh_private_key"] == "[REDACTED]"
    assert sanitized["safe_field"] == 42

    assert sanitized["nested"]["secret_answer"] == "[REDACTED]"
    assert sanitized["nested"]["token_expiration"] == "[REDACTED]"
    assert sanitized["nested"]["normal_key_value"] == "[REDACTED]"  # Contains 'key'

    assert sanitized["items"][0]["user_key"] == "[REDACTED]"
    assert sanitized["items"][0]["status"] == "active"
    assert sanitized["items"][1] == "plain_string"


def test_sanitize_primitive_passthrough() -> None:
    assert sanitize_sensitive_data("string") == "string"
    assert sanitize_sensitive_data(123) == 123
    assert sanitize_sensitive_data(None) is None


def test_sanitize_complex_types_jsonb_normalization() -> None:
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from enum import Enum
    import json
    import uuid

    class SampleEnum(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    u = uuid.uuid4()
    now = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)
    d = date(2026, 11, 8)
    dec = Decimal("10.480600")

    payload = {
        "uuid": u,
        "created_at": now,
        "entry_date": d,
        "hq_latitude": dec,
        "status": SampleEnum.ACTIVE,
        "tags": {"admin", "audit"},
        "tuple_items": (1, Decimal("2.5")),
    }

    sanitized = sanitize_sensitive_data(payload)
    assert sanitized["uuid"] == str(u)
    assert sanitized["created_at"] == str(now)
    assert sanitized["entry_date"] == str(d)
    assert isinstance(sanitized["hq_latitude"], float)
    assert sanitized["hq_latitude"] == 10.4806
    assert sanitized["status"] == "active"
    assert isinstance(sanitized["tags"], list)
    assert isinstance(sanitized["tuple_items"], list)
    assert sanitized["tuple_items"][1] == 2.5

    # Certificar serialización JSONB sin TypeError (Spec 105)
    dumped = json.dumps(sanitized)
    assert "10.4806" in dumped
    assert "active" in dumped


def test_compute_audit_record_hash_deterministic() -> None:
    prev_hash = GENESIS_AUDIT_HASH
    record = {
        "action": "USER_CREATE",
        "actor_id": "usr-1",
        "target_id": "usr-2",
        "tenant_id": "ten-1",
    }

    hash1 = compute_audit_record_hash(prev_hash, record)
    hash2 = compute_audit_record_hash(prev_hash, record)

    assert len(hash1) == 64
    assert hash1 == hash2


def test_compute_audit_record_hash_tampering() -> None:
    prev_hash = GENESIS_AUDIT_HASH
    record1 = {"action": "ROUTER_REBOOT", "router_id": "r-1"}
    record2 = {"action": "ROUTER_REBOOT", "router_id": "r-2"}

    h1 = compute_audit_record_hash(prev_hash, record1)
    h2 = compute_audit_record_hash(prev_hash, record2)
    assert h1 != h2

    # Different prev_hash
    h3 = compute_audit_record_hash("a" * 64, record1)
    assert h1 != h3


def test_sanitize_log_string_crlf_and_control_chars() -> None:
    # DISA STIG V-222444 / OWASP 4.3.10 SL-4
    assert sanitize_log_string(None) is None
    malicious = "admin\r\nCRLF_INJECTION: true\x00\x1b[31mRedText"
    cleaned = sanitize_log_string(malicious)
    assert "\r" not in cleaned
    assert "\n" not in cleaned
    assert "\x00" not in cleaned
    assert "\x1b" not in cleaned
    assert "admin  CRLF_INJECTION: true[31mRedText" in cleaned

    long_str = "A" * 600
    truncated = sanitize_log_string(long_str, max_len=100)
    assert len(truncated) == 100
