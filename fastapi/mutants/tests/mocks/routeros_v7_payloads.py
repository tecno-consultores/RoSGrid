# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from typing import Any

MOCK_SYSTEM_RESOURCE: dict[str, Any] = {
    "uptime": "14d06h22m15s",
    "version": "7.16.1 (stable)",
    "build-time": "2026-09-10 12:00:00",
    "factory-software": "7.8",
    "free-memory": "784334848",
    "total-memory": "1073741824",
    "cpu": "ARM64",
    "cpu-count": "4",
    "cpu-frequency": "1400",
    "cpu-load": "19",
    "free-hdd-space": "419430400",
    "total-hdd-space": "536870912",
    "architecture-name": "arm64",
    "board-name": "RB4011iGS+",
    "platform": "MikroTik",
}

MOCK_SYSTEM_ROUTERBOARD: dict[str, Any] = {
    "routerboard": "true",
    "model": "RB4011iGS+",
    "serial-number": "D4460B123456",
    "firmware-type": "al2",
    "factory-firmware": "7.8",
    "current-firmware": "7.16.1",
    "upgrade-firmware": "7.16.1",
}

MOCK_SYSTEM_HEALTH: list[dict[str, str]] = [
    {".id": "*1", "name": "temperature", "value": "44", "type": "C"},
    {".id": "*2", "name": "voltage", "value": "24.2", "type": "V"},
]

MOCK_SFP_MONITOR: list[dict[str, str]] = [
    {
        "name": "sfp-sfpplus1",
        "status": "link-ok",
        "auto-negotiation": "done",
        "rate": "10Gbps",
        "full-duplex": "true",
        "sfp-module-present": "true",
        "sfp-vendor-name": "MikroTik",
        "sfp-vendor-part-number": "S+31DLC10D",
        "sfp-wavelength": "1310",
        "sfp-temperature": "42",
        "sfp-supply-voltage": "3.31",
        "sfp-tx-bias-current": "18",
        "sfp-tx-power": "-3.12",
        "sfp-rx-power": "-6.45",
    }
]
