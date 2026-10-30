# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para WebFig Capa 1: Firewall y Routing v7."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# FIREWALL (FILTER, NAT, MANGLE, RAW, ADDRESS-LISTS, CONNECTIONS)
# ============================================================================


class FirewallRuleMoveRequest(StrictBaseModel):
    numbers: str = Field(..., min_length=1)  # ej: "*1C"
    destination: str = Field(..., min_length=1)  # ej: "*14"


class FirewallRuleCreateRequest(StrictBaseModel):
    chain: str = Field(..., min_length=1, max_length=32)
    action: str = Field(default="accept", min_length=1, max_length=32)
    src_address: str | None = None
    dst_address: str | None = None
    protocol: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    to_addresses: str | None = None
    to_ports: str | None = None
    place_before: str | None = None
    comment: str | None = None
    disabled: bool = False
    extra_params: dict[str, Any] = Field(default_factory=dict)


class FirewallRuleUpdateRequest(StrictBaseModel):
    chain: str | None = None
    action: str | None = None
    src_address: str | None = None
    dst_address: str | None = None
    protocol: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    to_addresses: str | None = None
    to_ports: str | None = None
    comment: str | None = None
    disabled: bool | None = None
    extra_params: dict[str, Any] = Field(default_factory=dict)


class AddressListCreateRequest(StrictBaseModel):
    list: str = Field(..., min_length=1, max_length=64)
    address: str = Field(..., min_length=1, max_length=64)
    timeout: str | None = None
    comment: str | None = None


class AddressListUpdateRequest(StrictBaseModel):
    list: str | None = Field(default=None, min_length=1, max_length=64)
    address: str | None = Field(default=None, min_length=1, max_length=64)
    timeout: str | None = None
    comment: str | None = None
    disabled: bool | None = None


# ============================================================================
# ROUTING AVANZADO v7 (TABLES, RULES, BGP, OSPF, BFD, FILTERS)
# ============================================================================


class RoutingTableCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    fib: bool = True
    comment: str | None = None


class RoutingTableUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    fib: bool | None = None
    comment: str | None = None
    disabled: bool | None = None


class RoutingRuleCreateRequest(StrictBaseModel):
    table: str = Field(..., min_length=1, max_length=64)
    action: str = Field(default="lookup", min_length=1, max_length=32)
    src_address: str | None = None
    dst_address: str | None = None
    routing_mark: str | None = None


class RoutingRuleUpdateRequest(StrictBaseModel):
    table: str | None = Field(default=None, min_length=1, max_length=64)
    action: str | None = Field(default=None, min_length=1, max_length=32)
    src_address: str | None = None
    dst_address: str | None = None
    routing_mark: str | None = None
    disabled: bool | None = None
    comment: str | None = None


class BgpConnectionCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    remote_address: str = Field(..., min_length=1)
    remote_as: int = Field(..., ge=1, le=4294967295)
    local_as: int | None = Field(default=None, ge=1, le=4294967295)
    local_role: str = Field(default="ebgp", min_length=1, max_length=32)
    templates: str | None = None
    connect: bool | None = None
    listen: bool | None = None
    disabled: bool = False


class BgpConnectionUpdateRequest(StrictBaseModel):
    remote_address: str | None = None
    remote_as: int | None = Field(default=None, ge=1, le=4294967295)
    local_as: int | None = Field(default=None, ge=1, le=4294967295)
    local_role: str | None = None
    disabled: bool | None = None


class BgpSessionSummaryItem(BaseModel):
    id: str
    name: str
    remote_address: str
    remote_as: int
    local_as: int
    established: bool
    uptime: str = "0s"
    prefix_count: int = 0
    hold_time: str = "1m30s"
    keepalive_time: str = "30s"


class BgpPeerStatusSummary(BaseModel):
    total_configured_connections: int
    established_sessions_count: int
    sessions: list[BgpSessionSummaryItem] = Field(default_factory=list)


class RoutingFilterRuleCreateRequest(StrictBaseModel):
    chain: str = Field(..., min_length=1, max_length=64)
    rule: str = Field(..., min_length=1)
    comment: str | None = None
    disabled: bool = False


class RoutingFilterRuleUpdateRequest(StrictBaseModel):
    chain: str | None = None
    rule: str | None = None
    comment: str | None = None
    disabled: bool | None = None
