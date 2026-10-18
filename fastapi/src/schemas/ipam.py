# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.ipam import (
    AuthBackendEnum,
    CustomerServiceStatusEnum,
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
    utilization_pct: Decimal
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


class CustomerServiceCreate(BaseModel):
    router_id: uuid.UUID
    customer_name: str = Field(..., min_length=2, max_length=128)
    customer_code: Optional[str] = Field(None, max_length=64)
    service_type: CustomerServiceTypeEnum = CustomerServiceTypeEnum.PPPOE
    auth_backend: AuthBackendEnum = AuthBackendEnum.LOCAL_SECRET
    pppoe_username: Optional[str] = Field(None, max_length=64)
    pppoe_password: Optional[str] = Field(None, min_length=4, max_length=64)
    ipv4_address_id: Optional[uuid.UUID] = None
    ipv6_delegated_prefix: Optional[str] = None
    onu_mode: ONUModeEnum = ONUModeEnum.ROUTER
    onu_mac_address: Optional[str] = Field(None, max_length=17)
    onu_serial_number: Optional[str] = Field(None, max_length=64)
    cpe_wifi_mac_address: Optional[str] = Field(None, max_length=17)
    pon_port: Optional[str] = Field(None, max_length=64)
    optical_box: Optional[str] = Field(None, max_length=64)
    physical_address: Optional[str] = Field(None, max_length=255)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class CustomerServiceUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    service_type: Optional[CustomerServiceTypeEnum] = None
    auth_backend: Optional[AuthBackendEnum] = None
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
    ipv6_delegated_prefix: Optional[str] = None
    onu_mode: Optional[ONUModeEnum] = None
    onu_mac_address: Optional[str] = None
    onu_serial_number: Optional[str] = None
    cpe_wifi_mac_address: Optional[str] = None
    pon_port: Optional[str] = None
    optical_box: Optional[str] = None
    status: Optional[CustomerServiceStatusEnum] = None
    physical_address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class CustomerServiceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    customer_name: str
    customer_code: Optional[str]
    service_type: CustomerServiceTypeEnum
    auth_backend: AuthBackendEnum
    pppoe_username: Optional[str]
    ipv4_address_id: Optional[uuid.UUID]
    ipv6_delegated_prefix: Optional[str]
    onu_mode: ONUModeEnum
    onu_mac_address: Optional[str]
    onu_serial_number: Optional[str]
    cpe_wifi_mac_address: Optional[str]
    pon_port: Optional[str]
    optical_box: Optional[str]
    last_reachability_status: str
    last_seen_at: Optional[datetime]
    status: CustomerServiceStatusEnum
    physical_address: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
