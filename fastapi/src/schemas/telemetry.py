# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Telemetría Efímera en Vivo y Eventos WebSocket."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class SystemHealthMetrics(StrictBaseModel):
    uptime: str
    cpu_load_pct: int
    cpu_count: int
    cpu_frequency_mhz: int | None = None
    free_memory_bytes: int
    total_memory_bytes: int
    memory_used_pct: float
    free_hdd_bytes: int
    total_hdd_bytes: int
    temperature_c: float | None = None
    voltage_v: float | None = None


class InterfaceLiveMetrics(StrictBaseModel):
    name: str
    running: bool
    disabled: bool
    rx_bps: int
    tx_bps: int
    rx_pps: int
    tx_pps: int


class TelemetryTickFrame(StrictBaseModel):
    type: str = "TELEMETRY_TICK"
    router_id: uuid.UUID
    timestamp_iso: str
    system: SystemHealthMetrics
    interfaces: list[InterfaceLiveMetrics] = Field(default_factory=list)


class TenantEventFrame(StrictBaseModel):
    type: str = "TENANT_EVENT"
    tenant_id: uuid.UUID
    timestamp_iso: str
    event_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
