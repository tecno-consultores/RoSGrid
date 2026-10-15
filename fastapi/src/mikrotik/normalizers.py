# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Normalizadores deterministas de tipos de RouterOS v7+ para Python y Pydantic."""

import re
from typing import Any

_DURATION_REGEX = re.compile(
    r"((?P<weeks>\d+)w)?((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?"
)
_BYTES_MULTIPLIERS = {
    "k": 1024,
    "m": 1024**2,
    "g": 1024**3,
    "t": 1024**4,
}


def normalize_routeros_bool(val: Any) -> bool:
    """Convierte cualquier representación booleana de RouterOS en bool nativo de Python."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        cleaned = val.strip().lower()
        return cleaned in {"true", "yes", "1", "on", "enabled"}
    return False


def to_routeros_bool(val: bool) -> str:
    """Convierte un bool de Python a la cadena 'true' o 'false' esperada por RouterOS v7."""
    return "true" if val else "false"


def _parse_time_colon_format(val: str) -> int:
    parts = val.split(":")
    if len(parts) == 3:
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    if len(parts) == 2:
        m, s = map(int, parts)
        return m * 60 + s
    return int(parts[0])


def _parse_time_unit_format(val: str) -> int:
    match = _DURATION_REGEX.fullmatch(val)
    if not match:
        return 0
    w = int(match.group("weeks") or 0)
    d = int(match.group("days") or 0)
    h = int(match.group("hours") or 0)
    m = int(match.group("minutes") or 0)
    s = int(match.group("seconds") or 0)
    return w * 604800 + d * 86400 + h * 3600 + m * 60 + s


def parse_routeros_duration(val: str | float | None) -> int:
    """Parsea representaciones de tiempo de RouterOS (ej. '00:01:00', '1h30m', '10s') a segundos."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    cleaned = str(val).strip().lower()
    if not cleaned:
        return 0
    if ":" in cleaned:
        return _parse_time_colon_format(cleaned)
    if cleaned.isdigit():
        return int(cleaned)
    return _parse_time_unit_format(cleaned)


def format_routeros_duration(seconds: int) -> str:
    """Formatea segundos en formato 'HH:MM:SS' de RouterOS."""
    total = max(0, seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_routeros_bytes(val: str | float | None) -> int:
    """Parsea tamaños y capacidades con sufijos ('100M', '1G', '512k') a bytes enteros."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    cleaned = str(val).strip().lower()
    if not cleaned:
        return 0
    if cleaned.isdigit():
        return int(cleaned)

    unit = cleaned[-1]
    multiplier = _BYTES_MULTIPLIERS.get(unit)
    if multiplier is not None:
        num_part = cleaned[:-1].strip()
        try:
            return int(float(num_part) * multiplier)
        except ValueError:
            return 0
    return 0


def clean_rsc_export_comments(content: str) -> str:
    """Elimina comentarios de fecha/hora dinámicos de scripts .rsc para diffs deterministas."""
    cleaned_lines = []
    for line in content.splitlines():
        trimmed = line.strip()
        # Filtrar comentarios tipo '# 2026-10-14 21:00:00 by RouterOS 7.x'
        if trimmed.startswith("#") and "by routeros" in trimmed.lower():
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip() + "\n"
