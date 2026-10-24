# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

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
    name: str = Field(..., min_length=1, max_length=64)
    route_distinguisher: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=255)


class IPAMVrfUpdate(BaseModel):
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


class SubscriberDeviceCreate(BaseModel):
    router_id: uuid.UUID
    endpoint_identifier: Optional[str] = Field(None, max_length=64)
    service_type: CustomerServiceTypeEnum = CustomerServiceTypeEnum.PPPOE
    auth_backend: AuthBackendEnum = AuthBackendEnum.LOCAL_SECRET
    pppoe_password: Optional[str] = Field(None, min_length=4, max_length=64)
    ipv4_address_id: Optional[uuid.UUID] = None
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


class SubscriberDeviceUpdate(BaseModel):
    endpoint_identifier: Optional[str] = None
    service_type: Optional[CustomerServiceTypeEnum] = None
    auth_backend: Optional[AuthBackendEnum] = None
    pppoe_password: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
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


class SubscriberDeviceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    service_type: CustomerServiceTypeEnum
    auth_backend: AuthBackendEnum
    endpoint_identifier: Optional[str] = None
    pppoe_username: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
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


