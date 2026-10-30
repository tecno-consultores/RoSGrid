# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Interfaces WebFig Capa 1 y Red IP/IPv6."""

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
    protocol_mode: str | None = Field(default=None, max_length=16)
    comment: str | None = None


class BridgeUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    vlan_filtering: bool | None = None
    protocol_mode: str | None = Field(default=None, max_length=16)
    disabled: bool | None = None
    comment: str | None = None


class BridgePortCreateRequest(StrictBaseModel):
    bridge: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    pvid: int = Field(default=1, ge=1, le=4094)
    hw: bool = True
    frame_types: str | None = None
    ingress_filtering: bool = False


class BridgePortUpdateRequest(StrictBaseModel):
    bridge: str | None = Field(default=None, min_length=1, max_length=64)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    pvid: int | None = Field(default=None, ge=1, le=4094)
    hw: bool | None = None
    frame_types: str | None = None
    ingress_filtering: bool | None = None
    horizon: str | None = None
    disabled: bool | None = None
    comment: str | None = None


class BridgeVlanCreateRequest(StrictBaseModel):
    bridge: str = Field(..., min_length=1, max_length=64)
    vlan_ids: str = Field(..., min_length=1, max_length=64)
    tagged: str | None = None
    untagged: str | None = None
    comment: str | None = None
    disabled: bool = False


class BridgeVlanUpdateRequest(StrictBaseModel):
    bridge: str | None = Field(default=None, min_length=1, max_length=64)
    vlan_ids: str | None = Field(default=None, min_length=1, max_length=64)
    tagged: str | None = None
    untagged: str | None = None
    comment: str | None = None
    disabled: bool | None = None


class WireGuardCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    listen_port: int = Field(..., ge=1, le=65535)
    mtu: int | None = Field(default=1420, ge=68, le=65535)
    comment: str | None = None


class WireGuardUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    listen_port: int | None = Field(default=None, ge=1, le=65535)
    mtu: int | None = Field(default=None, ge=68, le=65535)
    disabled: bool | None = None
    comment: str | None = None


class WireGuardPeerCreateRequest(StrictBaseModel):
    interface: str = Field(..., min_length=1, max_length=64)
    public_key: str = Field(..., min_length=32, max_length=64)
    allowed_address: str = Field(..., min_length=3)
    endpoint_address: str | None = None
    endpoint_port: int | None = Field(default=None, ge=1, le=65535)
    persistent_keepalive: int | str | None = None
    comment: str | None = None


class WireGuardPeerUpdateRequest(StrictBaseModel):
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    public_key: str | None = Field(default=None, min_length=4, max_length=128)
    allowed_address: str | None = Field(default=None, min_length=3)
    endpoint_address: str | None = None
    endpoint_port: int | None = Field(default=None, ge=1, le=65535)
    persistent_keepalive: int | str | None = None
    disabled: bool | None = None
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
    check_gateway: str | None = Field(default=None, max_length=16)
    comment: str | None = None
    disabled: bool = False


class IpRouteUpdateRequest(StrictBaseModel):
    dst_address: str | None = Field(default=None, min_length=3, max_length=64)
    gateway: str | None = Field(default=None, min_length=1)
    distance: int | None = Field(default=None, ge=1, le=255)
    routing_table: str | None = Field(default=None, min_length=1, max_length=64)
    check_gateway: str | None = Field(default=None, max_length=16)
    comment: str | None = None
    disabled: bool | None = None


class IpArpCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    mac_address: str = Field(..., min_length=11, max_length=17)
    interface: str = Field(..., min_length=1, max_length=64)
    comment: str | None = None


class IpArpUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    mac_address: str | None = Field(default=None, min_length=11, max_length=17)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    comment: str | None = None
    disabled: bool | None = None


class IpPoolCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    ranges: str = Field(..., min_length=3)
    next_pool: str | None = Field(default=None, max_length=64)


class IpPoolUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    ranges: str | None = Field(default=None, min_length=3)
    next_pool: str | None = Field(default=None, max_length=64)
    comment: str | None = None


class DhcpLeaseUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    rate_limit: str | None = None
    comment: str | None = None


class IpServiceUpdateRequest(StrictBaseModel):
    port: int | None = Field(default=None, ge=1, le=65535)
    address: str | None = None
    disabled: bool | None = None


# ============================================================================
# DHCPv4 SERVER, NETWORKS & CLIENTS
# ============================================================================


class DhcpServerCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    address_pool: str = Field(..., min_length=1, max_length=64)
    lease_time: str = Field(default="10m", max_length=16)
    disabled: bool = False


class DhcpServerUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    address_pool: str | None = Field(default=None, min_length=1, max_length=64)
    lease_time: str | None = Field(default=None, max_length=16)
    disabled: bool | None = None


class DhcpNetworkCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    gateway: str | None = None
    dns_server: str | None = None
    domain: str | None = None
    comment: str | None = None


class DhcpNetworkUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    gateway: str | None = None
    dns_server: str | None = None
    domain: str | None = None
    ntp_server: str | None = None
    comment: str | None = None


class DhcpClientCreateRequest(StrictBaseModel):
    interface: str = Field(..., min_length=1, max_length=64)
    add_default_route: bool = True
    use_peer_dns: bool = True
    use_peer_ntp: bool = True
    disabled: bool = False
    comment: str | None = None


class DhcpClientUpdateRequest(StrictBaseModel):
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    add_default_route: bool | None = None
    use_peer_dns: bool | None = None
    use_peer_ntp: bool | None = None
    default_route_distance: int | None = Field(default=None, ge=1, le=255)
    disabled: bool | None = None
    comment: str | None = None


class DnsSettingsUpdateRequest(StrictBaseModel):
    servers: str | None = None
    allow_remote_requests: bool | None = None
    max_udp_packet_size: int | None = Field(default=None, ge=512, le=65507)
    cache_size: int | str | None = None
    cache_max_ttl: str | None = None
    use_doh_server: str | None = None
    verify_doh_cert: bool | None = None


class DnsStaticCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=3, max_length=64)
    cname: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default="A", max_length=16)
    ttl: str | None = Field(default="1d", max_length=32)
    comment: str | None = None
    disabled: bool = False


class DnsStaticUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=3, max_length=64)
    cname: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, max_length=16)
    ttl: str | None = Field(default=None, max_length=32)
    comment: str | None = None
    disabled: bool | None = None


# ============================================================================
# IPv6: ADDRESSES, DHCPv6 CLIENT/SERVER, POOLS & NDP
# ============================================================================


class Ipv6AddressCreateRequest(StrictBaseModel):
    address: str = Field(..., min_length=3, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    advertise: bool = True
    eui_64: bool = False
    disabled: bool = False
    comment: str | None = None


class Ipv6AddressUpdateRequest(StrictBaseModel):
    address: str | None = Field(default=None, min_length=3, max_length=64)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    advertise: bool | None = None
    eui_64: bool | None = None
    disabled: bool | None = None
    comment: str | None = None


class Ipv6DhcpClientCreateRequest(StrictBaseModel):
    interface: str = Field(..., min_length=1, max_length=64)
    request: str = Field(default="prefix", max_length=16)
    pool_name: str | None = Field(default=None, max_length=64)
    pool_prefix_length: int = Field(default=64, ge=16, le=128)
    add_default_route: bool = True
    disabled: bool = False
    comment: str | None = None


class Ipv6DhcpClientUpdateRequest(StrictBaseModel):
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    request: str | None = Field(default=None, max_length=16)
    pool_name: str | None = Field(default=None, max_length=64)
    pool_prefix_length: int | None = Field(default=None, ge=16, le=128)
    add_default_route: bool | None = None
    use_peer_dns: bool | None = None
    disabled: bool | None = None
    comment: str | None = None


class Ipv6DhcpServerCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    interface: str = Field(..., min_length=1, max_length=64)
    address_pool: str = Field(..., min_length=1, max_length=64)
    lease_time: str = Field(default="10m", max_length=16)
    disabled: bool = False


class Ipv6DhcpServerUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    interface: str | None = Field(default=None, min_length=1, max_length=64)
    address_pool: str | None = Field(default=None, min_length=1, max_length=64)
    lease_time: str | None = Field(default=None, max_length=16)
    disabled: bool | None = None
    comment: str | None = None


class Ipv6PoolCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    prefix: str = Field(..., min_length=3, max_length=64)
    prefix_length: int = Field(default=64, ge=16, le=128)


class Ipv6PoolUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    prefix: str | None = Field(default=None, min_length=3, max_length=64)
    prefix_length: int | None = Field(default=None, ge=16, le=128)
    comment: str | None = None

