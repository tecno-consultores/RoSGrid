# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from src.core.audit import (
    GENESIS_AUDIT_HASH,
    compute_audit_record_hash,
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
