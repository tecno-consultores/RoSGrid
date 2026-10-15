# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Paquete de integración con RouterOS v7+ REST API, SSL TOFU y Safe Mode."""

from src.mikrotik.client import (
    MikrotikApiError,
    MikrotikAuthFailedError,
    MikrotikClientError,
    MikrotikConnectionError,
    MikrotikRestClient,
    MikrotikTimeoutError,
)
from src.mikrotik.normalizers import (
    clean_rsc_export_comments,
    format_routeros_duration,
    normalize_routeros_bool,
    parse_routeros_bytes,
    parse_routeros_duration,
    to_routeros_bool,
)
from src.mikrotik.safemode import (
    SafeModeError,
    SafeModeRollbackTriggeredError,
    build_rollback_command,
    build_scheduler_payload,
    execute_with_safemode,
    generate_safemode_job_name,
    inject_deadmans_switch,
    remove_deadmans_switch,
    verify_connectivity,
)
from src.mikrotik.ssl_tofu import (
    SSLTrustStatus,
    MikrotikSSLError,
    MikrotikSSLFingerprintMismatchError,
    compute_der_sha256_fingerprint,
    create_tofu_ssl_context,
    evaluate_ssl_fingerprint,
    extract_peer_ssl_fingerprint,
)

__all__ = [
    # SSL TOFU
    "SSLTrustStatus",
    "MikrotikSSLError",
    "MikrotikSSLFingerprintMismatchError",
    "create_tofu_ssl_context",
    "compute_der_sha256_fingerprint",
    "extract_peer_ssl_fingerprint",
    "evaluate_ssl_fingerprint",
    # Client
    "MikrotikRestClient",
    "MikrotikClientError",
    "MikrotikConnectionError",
    "MikrotikTimeoutError",
    "MikrotikAuthFailedError",
    "MikrotikApiError",
    # SafeMode
    "SafeModeError",
    "SafeModeRollbackTriggeredError",
    "generate_safemode_job_name",
    "build_rollback_command",
    "build_scheduler_payload",
    "inject_deadmans_switch",
    "verify_connectivity",
    "remove_deadmans_switch",
    "execute_with_safemode",
    # Normalizers
    "normalize_routeros_bool",
    "to_routeros_bool",
    "parse_routeros_duration",
    "format_routeros_duration",
    "parse_routeros_bytes",
    "clean_rsc_export_comments",
]
