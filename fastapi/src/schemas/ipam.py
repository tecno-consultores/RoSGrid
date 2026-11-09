# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.ipam import (
    AuthBackendEnum,
    CustomerServiceTypeEnum,
    IPAddressStatusEnum,
    IPFamilyEnum,
    IPPrefixRoleEnum,
    IPPrefixStatusEnum,
    ONUModeEnum,
)


class IPAMVrfCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=64)
    route_distinguisher: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=255)


class IPAMVrfUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    route_distinguisher: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=255)


class IPAMVrfResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    route_distinguisher: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IPAMPrefixCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vrf_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    prefix: str = Field(..., description="Notación CIDR ej: 100.64.0.0/10 o 2803:cafe::/32")
    ip_family: IPFamilyEnum
    role: IPPrefixRoleEnum = IPPrefixRoleEnum.CUSTOMER_RESIDENTIAL
    status: IPPrefixStatusEnum = IPPrefixStatusEnum.ACTIVE
    is_pool: bool = False
    default_child_prefix_len: Optional[int] = Field(None, ge=1, le=128)
    description: Optional[str] = Field(None, max_length=255)


class IPAMPrefixUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Optional[IPPrefixRoleEnum] = None
    status: Optional[IPPrefixStatusEnum] = None
    is_pool: Optional[bool] = None
    default_child_prefix_len: Optional[int] = None
    description: Optional[str] = None


class IPAMPrefixResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    vrf_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    prefix: str
    ip_family: IPFamilyEnum
    role: IPPrefixRoleEnum
    status: IPPrefixStatusEnum
    is_pool: bool
    default_child_prefix_len: Optional[int]
    utilization_pct: Optional[Decimal] = Decimal("0.00")
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("prefix", mode="before")
    @classmethod
    def _coerce_prefix_to_str(cls, v: Any) -> str:
        return str(v) if v is not None else ""



class IPAMPrefixNextAvailableResponse(BaseModel):
    prefix_id: uuid.UUID
    next_available: str
    ip_family: IPFamilyEnum
    is_subnet: bool = False
    message: str = "Recurso libre encontrado exitosamente"


class IPAMAddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prefix_id: uuid.UUID
    address: str = Field(..., description="Dirección IP ej: 100.64.10.155/32 o 2803:cafe:1::1/64")
    ip_family: IPFamilyEnum
    status: IPAddressStatusEnum = IPAddressStatusEnum.ALLOCATED
    router_id: Optional[uuid.UUID] = None
    interface_name: Optional[str] = Field(None, max_length=64)
    mac_address: Optional[str] = Field(None, max_length=17)
    dns_ptr: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)


class IPAMAddressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Optional[IPAddressStatusEnum] = None
    router_id: Optional[uuid.UUID] = None
    interface_name: Optional[str] = None
    mac_address: Optional[str] = None
    dns_ptr: Optional[str] = None
    description: Optional[str] = None


class IPAMAddressResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    prefix_id: uuid.UUID
    address: str
    ip_family: IPFamilyEnum
    status: IPAddressStatusEnum
    router_id: Optional[uuid.UUID]
    interface_name: Optional[str]
    mac_address: Optional[str]
    dns_ptr: Optional[str]
    description: Optional[str]
    soft_lock_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("address", mode="before")
    @classmethod
    def _coerce_address_to_str(cls, v: Any) -> str:
        return str(v) if v is not None else ""



class BandwidthProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=64)
    rate_down_kbps: int = Field(..., gt=0)
    rate_up_kbps: int = Field(..., gt=0)
    burst_down_kbps: int = Field(0, ge=0)
    burst_up_kbps: int = Field(0, ge=0)
    burst_threshold_down_kbps: int = Field(0, ge=0)
    burst_threshold_up_kbps: int = Field(0, ge=0)
    burst_time_seconds: int = Field(8, ge=1, le=60)
    priority: int = Field(8, ge=1, le=8)
    queue_type: str = Field("pcq-download-default", max_length=64)


class BandwidthProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=2, max_length=64)
    rate_down_kbps: Optional[int] = Field(None, gt=0)
    rate_up_kbps: Optional[int] = Field(None, gt=0)
    burst_down_kbps: Optional[int] = Field(None, ge=0)
    burst_up_kbps: Optional[int] = Field(None, ge=0)
    burst_threshold_down_kbps: Optional[int] = Field(None, ge=0)
    burst_threshold_up_kbps: Optional[int] = Field(None, ge=0)
    burst_time_seconds: Optional[int] = Field(None, ge=1, le=60)
    priority: Optional[int] = Field(None, ge=1, le=8)
    queue_type: Optional[str] = Field(None, max_length=64)


class BandwidthProfileResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    rate_down_kbps: int
    rate_up_kbps: int
    burst_down_kbps: int
    burst_up_kbps: int
    burst_threshold_down_kbps: int
    burst_threshold_up_kbps: int
    burst_time_seconds: int
    priority: int
    queue_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _normalize_service_type_input(val: Any) -> Any:
    """Normaliza alias operativos FTTH hacia valores canónicos de CustomerServiceTypeEnum."""
    if not isinstance(val, str):
        return val
    upper_val = val.strip().upper()
    alias_map = {
        "FTTH_GPON": CustomerServiceTypeEnum.PPPOE.value,
        "FTTH_PPPOE": CustomerServiceTypeEnum.PPPOE.value,
        "GPON": CustomerServiceTypeEnum.PPPOE.value,
        "FTTH_DHCP": CustomerServiceTypeEnum.DHCP.value,
        "IPOE": CustomerServiceTypeEnum.DHCP.value,
    }
    return alias_map.get(upper_val, upper_val)


def _normalize_onu_mode_input(val: Any) -> Any:
    """Normaliza alias operativos de modo ONU hacia valores canónicos de ONUModeEnum."""
    if not isinstance(val, str):
        return val
    upper_val = val.strip().upper()
    alias_map = {
        "ROUTER_NAT": ONUModeEnum.ROUTER.value,
        "NAT": ONUModeEnum.ROUTER.value,
        "ONT_ROUTER": ONUModeEnum.ROUTER.value,
        "ONU_BRIDGE": ONUModeEnum.BRIDGE.value,
    }
    return alias_map.get(upper_val, upper_val)


class SubscriberDeviceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    router_id: uuid.UUID
    endpoint_identifier: Optional[str] = Field(None, max_length=64)
    service_type: CustomerServiceTypeEnum = CustomerServiceTypeEnum.PPPOE
    auth_backend: AuthBackendEnum = AuthBackendEnum.LOCAL_SECRET
    pppoe_password: Optional[str] = Field(None, min_length=4, max_length=64)
    ipv4_address_id: Optional[uuid.UUID] = None
    assigned_ipv4: Optional[str] = Field(None, max_length=45)
    ipv6_delegated_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: ONUModeEnum = ONUModeEnum.ROUTER
    onu_mac_address: Optional[str] = Field(None, max_length=17)
    device_serial: Optional[str] = Field(None, max_length=64)
    cpe_wifi_mac_address: Optional[str] = Field(None, max_length=17)
    pon_port: Optional[str] = Field(None, max_length=64)
    optical_box: Optional[str] = Field(None, max_length=64)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    optical_box_id: Optional[uuid.UUID] = None
    optical_box_port: Optional[int] = None
    rx_optical_power_dbm: Optional[Decimal] = None
    drop_cable_meters: Optional[int] = None
    is_custom_coordinates: bool = False
    # Compatibilidad con llamadas heredadas
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    pppoe_username: Optional[str] = None
    onu_serial_number: Optional[str] = None
    physical_address: Optional[str] = None

    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, v: Any) -> Any:
        return _normalize_service_type_input(v)

    @field_validator("onu_mode", mode="before")
    @classmethod
    def normalize_onu_mode(cls, v: Any) -> Any:
        return _normalize_onu_mode_input(v)


class SubscriberDeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    router_id: Optional[uuid.UUID] = None
    bng_router_id: Optional[uuid.UUID] = None
    provision_on_router: bool = True
    endpoint_identifier: Optional[str] = None
    service_type: Optional[CustomerServiceTypeEnum] = None
    auth_backend: Optional[AuthBackendEnum] = None
    pppoe_password: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
    assigned_ipv4: Optional[str] = Field(None, max_length=45)
    ipv6_delegated_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: Optional[ONUModeEnum] = None
    onu_mac_address: Optional[str] = None
    device_serial: Optional[str] = None
    cpe_wifi_mac_address: Optional[str] = None
    pon_port: Optional[str] = None
    optical_box: Optional[str] = None
    optical_box_id: Optional[uuid.UUID] = None
    optical_box_port: Optional[int] = None
    rx_optical_power_dbm: Optional[Decimal] = None
    drop_cable_meters: Optional[int] = None
    is_custom_coordinates: Optional[bool] = None
    reset_to_router_coordinates: Optional[bool] = None
    status: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    # Compatibilidad con llamadas heredadas
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    pppoe_username: Optional[str] = None
    onu_serial_number: Optional[str] = None
    physical_address: Optional[str] = None

    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, v: Any) -> Any:
        return _normalize_service_type_input(v)

    @field_validator("onu_mode", mode="before")
    @classmethod
    def normalize_onu_mode(cls, v: Any) -> Any:
        return _normalize_onu_mode_input(v)


class SubscriberLiveCandidateDhcpLease(BaseModel):
    address: str
    mac_address: Optional[str] = None
    host_name: Optional[str] = None
    server: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class SubscriberLiveCandidatePppoe(BaseModel):
    name: str
    address: Optional[str] = None
    caller_id: Optional[str] = None
    service: Optional[str] = None
    uptime: Optional[str] = None
    source: str = "active"


class SubscriberLiveCandidatesResponse(BaseModel):
    device_id: uuid.UUID
    router_id: uuid.UUID
    router_name: str
    access_router_id: Optional[uuid.UUID] = None
    access_router_name: Optional[str] = None
    auto_switched_bng: bool = False
    matched_mac_address: Optional[str] = None
    matched_ipv4: Optional[str] = None
    dhcp_leases: list[SubscriberLiveCandidateDhcpLease] = Field(default_factory=list)
    pppoe_sessions: list[SubscriberLiveCandidatePppoe] = Field(default_factory=list)
    ipam_addresses: list[IPAMAddressResponse] = Field(default_factory=list)


class SubscriberDeviceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    service_type: CustomerServiceTypeEnum
    auth_backend: AuthBackendEnum
    endpoint_identifier: Optional[str] = None
    pppoe_username: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
    assigned_ipv4: Optional[str] = None
    ipv6_delegated_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: ONUModeEnum
    onu_mac_address: Optional[str] = None
    device_serial: Optional[str] = None
    onu_serial_number: Optional[str] = None
    cpe_wifi_mac_address: Optional[str] = None
    pon_port: Optional[str] = None
    optical_box: Optional[str] = None
    optical_box_id: Optional[uuid.UUID] = None
    optical_box_port: Optional[int] = None
    rx_optical_power_dbm: Optional[Decimal] = None
    drop_cable_meters: Optional[int] = None
    is_custom_coordinates: Optional[bool] = False
    last_reachability_status: str = "ONLINE"
    last_seen_at: Optional[datetime] = None
    status: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    physical_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


CustomerServiceCreate = SubscriberDeviceCreate
CustomerServiceUpdate = SubscriberDeviceUpdate
CustomerServiceResponse = SubscriberDeviceResponse


class OpticalBoxCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    router_id: uuid.UUID
    box_code: str
    brand: Optional[str] = None
    model: Optional[str] = None
    capacity_ports: int = 16
    splitter_ratio: str = "1:16"
    installation_type: str = "POLE"
    physical_location: Optional[str] = None
    input_power_dbm: Optional[Decimal] = None
    latitude: Decimal
    longitude: Decimal
    status: str = "ACTIVE"
    notes: Optional[str] = None


class OpticalBoxUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    box_code: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    capacity_ports: Optional[int] = None
    splitter_ratio: Optional[str] = None
    installation_type: Optional[str] = None
    physical_location: Optional[str] = None
    input_power_dbm: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OpticalBoxResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    box_code: str
    brand: Optional[str] = None
    model: Optional[str] = None
    capacity_ports: int
    splitter_ratio: str
    installation_type: str
    physical_location: Optional[str] = None
    input_power_dbm: Optional[Decimal] = None
    latitude: Decimal
    longitude: Decimal
    status: str
    notes: Optional[str] = None
    occupied_ports_count: int = 0
    available_ports_count: int = 16
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpticalBoxPortStatus(BaseModel):
    port_number: int
    is_occupied: bool
    subscriber_id: Optional[uuid.UUID] = None
    subscriber_identifier: Optional[str] = None
    assigned_ipv4: Optional[str] = None
    reachability_status: str = "FREE"
    rx_power_dbm: Optional[Decimal] = None


class OpticalBoxDetailResponse(OpticalBoxResponse):
    ports: list[OpticalBoxPortStatus] = []
    subscribers: list[SubscriberDeviceResponse] = []


class SimulateSubscribersResponse(BaseModel):
    created_count: int
    updated_count: int
    total_subscribers: int
    message: str


class SyncDhcpClientsResponse(BaseModel):
    created_count: int
    updated_count: int
    total_subscribers: int
    message: str


class SubscriberDevicePingResponse(BaseModel):
    device_id: uuid.UUID
    assigned_ipv4: Optional[str] = None
    last_reachability_status: str
    ping_latency_ms: Optional[Decimal] = None
    packet_loss_pct: Optional[Decimal] = None
    message: str
    is_cached: bool = False
    cache_ttl_remaining: int = 0
    status: str = "COMPLETED"
    root_cause_device_name: Optional[str] = None
    operational_lock: Optional[dict[str, Any]] = None
    gateway_ping: Optional[dict[str, Any]] = None
    internet_ping: Optional[dict[str, Any]] = None
    dns_check: Optional[dict[str, Any]] = None
    mtu_test: Optional[dict[str, Any]] = None


class OperationalStatusResponse(BaseModel):
    device_id: uuid.UUID
    is_locked: bool = False
    is_locked_by_other: bool = False
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None
    action: Optional[str] = None
    locked_at: Optional[str] = None
    minutes_ago: int = 0
    message: Optional[str] = None
    root_cause: Optional[dict[str, Any]] = None


class SubscriberCsvRowPreview(BaseModel):
    row_number: int
    endpoint_identifier: str
    onu_serial_number: Optional[str] = None
    onu_mac_address: Optional[str] = None
    assigned_ipv4: Optional[str] = None
    router_name: str
    optical_box_name: Optional[str] = None
    box_port_number: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_status: str = "ACTIVE"
    will_auto_create_box: bool = False
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class SubscriberCsvDryRunResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    can_proceed: bool
    rows: list[SubscriberCsvRowPreview] = Field(default_factory=list)


class SubscriberCsvCommitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[SubscriberCsvRowPreview]


class SubscriberCsvCommitResponse(BaseModel):
    imported_count: int
    created_ids: list[uuid.UUID] = Field(default_factory=list)
    message: str


class OpticalBoxCsvRowPreview(BaseModel):
    row_number: int
    box_code: str
    router_name: str
    capacity_ports: int = 16
    splitter_ratio: str = "1:16"
    installation_type: str = "POLE"
    input_power_dbm: Optional[float] = None
    latitude: float
    longitude: float
    physical_location: Optional[str] = None
    is_update: bool = False
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class OpticalBoxCsvDryRunResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    can_proceed: bool
    rows: list[OpticalBoxCsvRowPreview] = Field(default_factory=list)


class OpticalBoxCsvCommitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[OpticalBoxCsvRowPreview]


class OpticalBoxCsvCommitResponse(BaseModel):
    imported_count: int
    updated_count: int = 0
    box_ids: list[uuid.UUID] = Field(default_factory=list)
    message: str





