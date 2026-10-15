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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__is_sensitive_key__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_sensitive_key__mutmut)
def _is_sensitive_key(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def x__is_sensitive_key__mutmut_orig(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def x__is_sensitive_key__mutmut_1(key: str) -> bool:
    lower_k = None
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def x__is_sensitive_key__mutmut_2(key: str) -> bool:
    lower_k = key.upper()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def x__is_sensitive_key__mutmut_3(key: str) -> bool:
    lower_k = key.lower()
    return any(None)


def x__is_sensitive_key__mutmut_4(key: str) -> bool:
    lower_k = key.lower()
    return any(sub not in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)

mutants_x__is_sensitive_key__mutmut['_mutmut_orig'] = x__is_sensitive_key__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_sensitive_key__mutmut['x__is_sensitive_key__mutmut_1'] = x__is_sensitive_key__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_sensitive_key__mutmut['x__is_sensitive_key__mutmut_2'] = x__is_sensitive_key__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_sensitive_key__mutmut['x__is_sensitive_key__mutmut_3'] = x__is_sensitive_key__mutmut_3 # type: ignore # mutmut generated
mutants_x__is_sensitive_key__mutmut['x__is_sensitive_key__mutmut_4'] = x__is_sensitive_key__mutmut_4 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_sanitize_sensitive_data__mutmut)
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


def x_sanitize_sensitive_data__mutmut_orig(data: Any) -> Any:
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


def x_sanitize_sensitive_data__mutmut_1(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = None
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_2(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(None):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_3(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(None)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_4(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = None
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_5(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "XX[REDACTED]XX"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_6(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[redacted]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_7(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = None
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_8(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(None)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


def x_sanitize_sensitive_data__mutmut_9(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(None) for item in data]
    return data

mutants_x_sanitize_sensitive_data__mutmut['_mutmut_orig'] = x_sanitize_sensitive_data__mutmut_orig # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_1'] = x_sanitize_sensitive_data__mutmut_1 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_2'] = x_sanitize_sensitive_data__mutmut_2 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_3'] = x_sanitize_sensitive_data__mutmut_3 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_4'] = x_sanitize_sensitive_data__mutmut_4 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_5'] = x_sanitize_sensitive_data__mutmut_5 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_6'] = x_sanitize_sensitive_data__mutmut_6 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_7'] = x_sanitize_sensitive_data__mutmut_7 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_8'] = x_sanitize_sensitive_data__mutmut_8 # type: ignore # mutmut generated
mutants_x_sanitize_sensitive_data__mutmut['x_sanitize_sensitive_data__mutmut_9'] = x_sanitize_sensitive_data__mutmut_9 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_compute_audit_record_hash__mutmut)
def compute_audit_record_hash(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_orig(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_1(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = None
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_2(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(None, sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_3(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=None, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_4(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=None)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_5(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_6(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_7(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, )
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_8(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=False, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_9(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=str)
    raw = None
    return hashlib.sha256(raw).hexdigest()


def x_compute_audit_record_hash__mutmut_10(prev_hash: str, record_data: dict[str, Any]) -> str:
    serialized = json.dumps(record_data, sort_keys=True, default=str)
    raw = f"{prev_hash}:{serialized}".encode()
    return hashlib.sha256(None).hexdigest()

mutants_x_compute_audit_record_hash__mutmut['_mutmut_orig'] = x_compute_audit_record_hash__mutmut_orig # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_1'] = x_compute_audit_record_hash__mutmut_1 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_2'] = x_compute_audit_record_hash__mutmut_2 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_3'] = x_compute_audit_record_hash__mutmut_3 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_4'] = x_compute_audit_record_hash__mutmut_4 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_5'] = x_compute_audit_record_hash__mutmut_5 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_6'] = x_compute_audit_record_hash__mutmut_6 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_7'] = x_compute_audit_record_hash__mutmut_7 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_8'] = x_compute_audit_record_hash__mutmut_8 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_9'] = x_compute_audit_record_hash__mutmut_9 # type: ignore # mutmut generated
mutants_x_compute_audit_record_hash__mutmut['x_compute_audit_record_hash__mutmut_10'] = x_compute_audit_record_hash__mutmut_10 # type: ignore # mutmut generated
