# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para WebFig Capa 1: PPPoE, Queues, System y Tools."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# PPPoE / VPNs
# ============================================================================


class PppSecretCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)
    service: str = Field(default="any", min_length=1, max_length=32)
    profile: str = Field(default="default", min_length=1, max_length=64)
    local_address: str | None = None
    remote_address: str | None = None
    comment: str | None = None
    disabled: bool = False


class PppSecretUpdateRequest(StrictBaseModel):
    password: str | None = None
    service: str | None = None
    profile: str | None = None
    local_address: str | None = None
    remote_address: str | None = None
    comment: str | None = None
    disabled: bool | None = None


class PppProfileCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    local_address: str | None = None
    remote_address: str | None = None
    rate_limit: str | None = None
    dns_server: str | None = None
    address_list: str | None = None
    only_one: str | None = None


class PppProfileUpdateRequest(StrictBaseModel):
    local_address: str | None = None
    remote_address: str | None = None
    rate_limit: str | None = None
    dns_server: str | None = None
    address_list: str | None = None
    only_one: str | None = None


class PppoeServerCreateRequest(StrictBaseModel):
    service_name: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    default_profile: str = Field(default="default", min_length=1, max_length=64)
    max_mtu: int = Field(default=1480, ge=576, le=65535)
    max_mru: int | None = Field(default=None, ge=576, le=65535)
    one_session_per_host: bool | None = None
    disabled: bool = False


# ============================================================================
# QUEUES (BANDWIDTH CONTROL)
# ============================================================================


class QueueSimpleCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    target: str = Field(..., min_length=1)
    max_limit: str = Field(..., min_length=1)  # ej: "100M/100M"
    limit_at: str | None = None
    burst_limit: str | None = None
    comment: str | None = None
    disabled: bool = False


class QueueSimpleUpdateRequest(StrictBaseModel):
    name: str | None = None
    target: str | None = None
    max_limit: str | None = None
    limit_at: str | None = None
    burst_limit: str | None = None
    comment: str | None = None
    disabled: bool | None = None


class QueueMoveRequest(StrictBaseModel):
    numbers: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)


class QueueTreeCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    parent: str = Field(..., min_length=1, max_length=64)
    packet_mark: str | None = None
    queue: str = Field(default="default", min_length=1, max_length=64)
    max_limit: str | None = None
    priority: int = Field(default=8, ge=1, le=8)


class QueueTreeUpdateRequest(StrictBaseModel):
    parent: str | None = None
    packet_mark: str | None = None
    queue: str | None = None
    max_limit: str | None = None
    priority: int | None = Field(default=None, ge=1, le=8)
    disabled: bool | None = None


# ============================================================================
# SYSTEM
# ============================================================================


class SystemIdentityUpdateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class SystemUserCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)
    group: str = Field(default="read", min_length=1, max_length=32)
    address: str | None = None
    comment: str | None = None


class SystemUserUpdateRequest(StrictBaseModel):
    password: str | None = None
    group: str | None = None
    address: str | None = None
    comment: str | None = None
    disabled: bool | None = None


class SystemScriptCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    source: str = Field(..., min_length=1)
    policy: str = Field(default="read,write,test", min_length=1)


class SystemRebootRequest(StrictBaseModel):
    reason: str = Field(..., min_length=3, max_length=255)


# ============================================================================
# DIAGNÓSTICO EN VIVO (TOOLS)
# ============================================================================


class RouterPingRequest(StrictBaseModel):
    address: str = Field(..., min_length=1)
    count: int = Field(default=5, ge=1, le=20)
    size: int = Field(default=64, ge=28, le=65507)
    src_address: str | None = None
    interface: str | None = None
    routing_table: str = Field(default="main", min_length=1)
    do_not_fragment: bool = False


class RouterPingResponse(BaseModel):
    target: str
    sent: int
    received: int
    packet_loss_pct: float
    min_rtt_ms: float | None = None
    avg_rtt_ms: float | None = None
    max_rtt_ms: float | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)


class RouterTracerouteRequest(StrictBaseModel):
    address: str = Field(..., min_length=1)
    count: int = Field(default=3, ge=1, le=10)
    max_hops: int = Field(default=20, ge=1, le=30)
    timeout: str = Field(default="1s", min_length=1)


class RouterTorchRequest(StrictBaseModel):
    interface: str = Field(..., min_length=1)
    duration_seconds: int = Field(default=3, ge=1, le=10)
    src_address: str | None = None
    dst_address: str | None = None
    port: str | None = None
    protocol: str | None = None
