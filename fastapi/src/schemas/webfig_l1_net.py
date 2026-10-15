# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Interfaces WebFig Capa 1 y Red IP/IPv6."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# DIAGNÓSTICO ÓPTICO SFP Y CABLE TDR
# ============================================================================


class SfpDiagnosticsResponse(BaseModel):
    interface_id: str
    interface_name: str
    status: str = "link-ok"
    rate: str = "10Gbps"
    full_duplex: bool = True
    sfp_module_present: bool = True
    sfp_vendor_name: str | None = None
    sfp_part_number: str | None = None
    sfp_wavelength_nm: int | None = None
    sfp_temperature_c: float | None = None
    sfp_supply_voltage_v: float | None = None
    sfp_tx_bias_ma: float | None = None
    sfp_tx_power_dbm: float | None = None
    sfp_rx_power_dbm: float | None = None
    optical_health: str = "OPTIMAL"  # OPTIMAL, WARNING, CRITICAL_LOW_LIGHT


class CablePairStatus(BaseModel):
    pair: str
    status: str
    length_meters: float | None = None


class CableTestResponse(BaseModel):
    interface_id: str
    interface_name: str
    status: str = "complete"
    pairs: list[CablePairStatus] = Field(default_factory=list)


# ============================================================================
# INTERFACES GENERALES, VLAN, BRIDGE Y WIREGUARD
# ============================================================================


class UpdateInterfaceRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    comment: str | None = None
    mtu: int | None = Field(default=None, ge=68, le=65535)
    disabled: bool | None = None


class VlanCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    vlan_id: int = Field(..., ge=1, le=4094)
    interface: str = Field(..., min_length=1, max_length=64)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    comment: str | None = None


class VlanUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    disabled: bool | None = None
    comment: str | None = None


class BridgeCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    vlan_filtering: bool = False
    comment: str | None = None


class BridgeUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    vlan_filtering: bool | None = None
    disabled: bool | None = None
    comment: str | None = None


class BridgePortCreateRequest(StrictBaseModel):
    bridge: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    pvid: int = Field(default=1, ge=1, le=4094)
    hw: bool = True
    frame_types: str | None = None


class WireGuardCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    listen_port: int = Field(..., ge=1, le=65535)
    mtu: int | None = Field(default=1420, ge=68, le=65535)
    comment: str | None = None


class WireGuardPeerCreateRequest(StrictBaseModel):
    interface: str = Field(..., min_length=1, max_length=64)
    public_key: str = Field(..., min_length=32, max_length=64)
    allowed_address: str = Field(..., min_length=3)
    endpoint_address: str | None = None
    endpoint_port: int | None = Field(default=None, ge=1, le=65535)
    comment: str | None = None


# ============================================================================
# IP / IPv6: ADDRESSES, ROUTES, ARP, POOLS, DHCP, DNS, SERVICES
# ============================================================================


class IpAddressCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)  # ej: 192.168.88.1/24
    network: str | None = None
    interface: str = Field(..., min_length=1, max_length=64)
    comment: str | None = None
    disabled: bool = False


class IpAddressUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    network: str | None = None
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    comment: str | None = None
    disabled: bool | None = None


class IpRouteCreateRequest(StrictBaseModel):
    dst_address: str = Field(default="0.0.0.0/0", min_length=3, max_length=64)
    gateway: str = Field(..., min_length=1)  # Soporta multi-gateway separado por comas (ECMP)
    distance: int = Field(default=1, ge=1, le=255)
    routing_table: str = Field(default="main", min_length=1, max_length=64)
    comment: str | None = None
    disabled: bool = False


class IpRouteUpdateRequest(StrictBaseModel):
    dst_address: str | None = Field(default=None, min_length=3, max_length=64)
    gateway: str | None = Field(default=None, min_length=1)
    distance: int | None = Field(default=None, ge=1, le=255)
    routing_table: str | None = Field(default=None, min_length=1, max_length=64)
    comment: str | None = None
    disabled: bool | None = None


class IpArpCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    mac_address: str = Field(..., min_length=11, max_length=17)
    interface: str = Field(..., min_length=1, max_length=64)
    comment: str | None = None


class IpPoolCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    ranges: str = Field(..., min_length=3)
    next_pool: str | None = Field(default=None, max_length=64)


class DhcpLeaseUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    rate_limit: str | None = None
    comment: str | None = None


class IpServiceUpdateRequest(StrictBaseModel):
    port: int | None = Field(default=None, ge=1, le=65535)
    address: str | None = None
    disabled: bool | None = None
