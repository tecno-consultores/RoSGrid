# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Catálogo de respuestas simuladas deterministas de la REST API de RouterOS v7."""

from typing import Any

MOCK_SYSTEM_IDENTITY: dict[str, Any] = {
    "name": "RoSGrid-Core-GW01",
}

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

MOCK_INTERFACES: list[dict[str, Any]] = [
    {
        ".id": "*1",
        "name": "ether1",
        "type": "ether",
        "mtu": "1500",
        "actual-mtu": "1500",
        "running": "true",
        "disabled": "false",
        "comment": "Uplink WAN",
        "mac-address": "CC:2D:E0:11:22:33",
    },
    {
        ".id": "*2",
        "name": "ether2",
        "type": "ether",
        "mtu": "1500",
        "actual-mtu": "1500",
        "running": "true",
        "disabled": "false",
        "comment": "LAN Local",
        "mac-address": "CC:2D:E0:11:22:34",
    },
]

MOCK_IP_ADDRESSES: list[dict[str, Any]] = [
    {
        ".id": "*1",
        "address": "192.168.88.1/24",
        "network": "192.168.88.0",
        "interface": "ether2",
        "disabled": "false",
        "dynamic": "false",
        "comment": "default defconf",
    },
    {
        ".id": "*2",
        "address": "203.0.113.10/29",
        "network": "203.0.113.8",
        "interface": "ether1",
        "disabled": "false",
        "dynamic": "false",
        "comment": "WAN Public",
    },
]

MOCK_IP_ROUTES: list[dict[str, Any]] = [
    {
        ".id": "*1",
        "dst-address": "0.0.0.0/0",
        "gateway": "203.0.113.9",
        "distance": "1",
        "scope": "30",
        "target-scope": "10",
        "active": "true",
        "disabled": "false",
    }
]

MOCK_FIREWALL_FILTER_RULES: list[dict[str, str]] = [
    {
        ".id": "*1",
        "chain": "input",
        "action": "accept",
        "connection-state": "established,related,untracked",
        "bytes": "98451200",
        "packets": "124500",
        "dynamic": "false",
        "invalid": "false",
        "disabled": "false",
        "comment": "Accept established/related",
    },
    {
        ".id": "*2",
        "chain": "input",
        "action": "drop",
        "connection-state": "invalid",
        "bytes": "14200",
        "packets": "310",
        "dynamic": "false",
        "invalid": "false",
        "disabled": "false",
        "comment": "Drop invalid",
    },
]

MOCK_BGP_SESSIONS: list[dict[str, str]] = [
    {
        ".id": "*3000001",
        "name": "ISP-Carrier-1-1",
        "remote.address": "186.10.20.1",
        "remote.as": "65001",
        "local.address": "186.10.20.2",
        "local.as": "65500",
        "established": "true",
        "uptime": "2w4d10h12m",
        "prefix-count": "942100",
    }
]

MOCK_PPP_SECRETS: list[dict[str, Any]] = [
    {
        ".id": "*1",
        "name": "client_pppoe_101",
        "service": "pppoe",
        "profile": "default-encryption",
        "local-address": "10.10.10.1",
        "remote-address": "10.10.10.101",
        "disabled": "false",
        "comment": "Customer 101",
    }
]

MOCK_SIMPLE_QUEUES: list[dict[str, Any]] = [
    {
        ".id": "*1",
        "name": "queue_client_101",
        "target": "10.10.10.101/32",
        "max-limit": "50M/100M",
        "burst-limit": "0/0",
        "disabled": "false",
        "comment": "50M upload / 100M download",
    }
]

MOCK_PACKAGE_UPDATE: dict[str, Any] = {
    "channel": "stable",
    "installed-version": "7.16.1",
    "latest-version": "7.17.0",
    "status": "New version is available",
}

MOCK_BACKUP_RSC_CONTENT: str = """# 2026-10-15 10:00:00 by RouterOS 7.16.1
# software id = TEST-1234
#
# model = RB4011iGS+
/interface ethernet
set [ find default-name=ether1 ] comment="Uplink WAN"
/ip address
add address=192.168.88.1/24 interface=ether2 network=192.168.88.0
/system identity
set name=RoSGrid-Core-GW01
"""
