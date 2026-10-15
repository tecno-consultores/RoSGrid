# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para normalizadores deterministas de RouterOS v7."""

import pytest

from src.mikrotik.normalizers import (
    clean_rsc_export_comments,
    format_routeros_duration,
    normalize_routeros_bool,
    parse_routeros_bytes,
    parse_routeros_duration,
    to_routeros_bool,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (1.5, True),
        (0.0, False),
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("YES", True),
        ("1", True),
        ("on", True),
        ("enabled", True),
        ("false", False),
        ("no", False),
        ("0", False),
        ("off", False),
        ("disabled", False),
        ("", False),
        (None, False),
        ([], False),
    ],
)
def test_normalize_routeros_bool(raw: object, expected: bool) -> None:
    assert normalize_routeros_bool(raw) is expected


def test_to_routeros_bool() -> None:
    assert to_routeros_bool(True) == "true"
    assert to_routeros_bool(False) == "false"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, 0),
        ("", 0),
        (60, 60),
        (120.5, 120),
        ("45", 45),
        ("00:01:30", 90),
        ("02:00:00", 7200),
        ("15:30", 930),
        ("10", 10),
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
        ("1w", 604800),
        ("1w2d3h4m5s", 604800 + 2 * 86400 + 3 * 3600 + 4 * 60 + 5),
        ("invalid_duration", 0),
    ],
)
def test_parse_routeros_duration(raw: object, expected: int) -> None:
    assert parse_routeros_duration(raw) == expected  # type: ignore[arg-type]


def test_format_routeros_duration() -> None:
    assert format_routeros_duration(0) == "00:00:00"
    assert format_routeros_duration(-10) == "00:00:00"
    assert format_routeros_duration(65) == "00:01:05"
    assert format_routeros_duration(3661) == "01:01:01"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, 0),
        ("", 0),
        (1024, 1024),
        (2048.0, 2048),
        ("500", 500),
        ("1k", 1024),
        ("2M", 2 * 1024**2),
        ("1G", 1024**3),
        ("1T", 1024**4),
        ("1.5M", int(1.5 * 1024**2)),
        ("invalid", 0),
        ("100X", 0),
        ("abcM", 0),
    ],
)
def test_parse_routeros_bytes(raw: object, expected: int) -> None:
    assert parse_routeros_bytes(raw) == expected  # type: ignore[arg-type]


def test_clean_rsc_export_comments() -> None:
    rsc = """# 2026-10-15 10:00:00 by RouterOS 7.16.1
# model = RB4011
/interface ethernet
set ether1 comment="WAN"
"""
    cleaned = clean_rsc_export_comments(rsc)
    assert "# 2026-10-15 10:00:00 by RouterOS 7.16.1" not in cleaned
    assert "# model = RB4011" in cleaned
    assert 'set ether1 comment="WAN"' in cleaned
