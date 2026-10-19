# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CIDR, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class IPFamilyEnum(str, enum.Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"


class IPPrefixRoleEnum(str, enum.Enum):
    CGNAT = "CGNAT"
    PUBLIC_DYNAMIC = "PUBLIC_DYNAMIC"
    PUBLIC_STATIC = "PUBLIC_STATIC"
    INFRA_P2P = "INFRA_P2P"
    LOOPBACK = "LOOPBACK"
    CUSTOMER_RESIDENTIAL = "CUSTOMER_RESIDENTIAL"
    CUSTOMER_CORPORATE = "CUSTOMER_CORPORATE"
    MGMT = "MGMT"


class IPPrefixStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    DEPRECATED = "DEPRECATED"


class IPAddressStatusEnum(str, enum.Enum):
    ALLOCATED = "ALLOCATED"
    RESERVED = "RESERVED"
    SOFT_LOCKED = "SOFT_LOCKED"
    DHCP_STATIC = "DHCP_STATIC"
    DHCP_DYNAMIC = "DHCP_DYNAMIC"
    QUARANTINE = "QUARANTINE"
    DEPRECATED = "DEPRECATED"


class CustomerServiceTypeEnum(str, enum.Enum):
    PPPOE = "PPPOE"
    DHCP = "DHCP"
    STATIC = "STATIC"


class AuthBackendEnum(str, enum.Enum):
    LOCAL_SECRET = "LOCAL_SECRET"
    RADIUS = "RADIUS"


class ONUModeEnum(str, enum.Enum):
    ROUTER = "ROUTER"
    BRIDGE = "BRIDGE"
    UNKNOWN = "UNKNOWN"


class CustomerServiceStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING_INSTALL = "PENDING_INSTALL"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class FieldOrderStatusEnum(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    CERTIFIED = "CERTIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FiberCutStatusEnum(str, enum.Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class IPAMVrf(Base):
    __tablename__ = "ipam_vrfs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ipam_vrfs_tenant_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    route_distinguisher: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    prefixes: Mapped[list["IPAMPrefix"]] = relationship("IPAMPrefix", back_populates="vrf", cascade="all, delete-orphan")


class IPAMPrefix(Base):
    __tablename__ = "ipam_prefixes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "vrf_id", "prefix", name="uq_ipam_prefix_tenant_vrf"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    vrf_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ipam_vrfs.id", ondelete="RESTRICT"), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ipam_prefixes.id", ondelete="CASCADE"), nullable=True)
    prefix: Mapped[str] = mapped_column(CIDR, nullable=False)
    ip_family: Mapped[IPFamilyEnum] = mapped_column(
        Enum(IPFamilyEnum, name="ip_family_enum", create_type=False),
        nullable=False,
    )
    role: Mapped[IPPrefixRoleEnum] = mapped_column(
        Enum(IPPrefixRoleEnum, name="ip_prefix_role_enum", create_type=False),
        nullable=False,
        default=IPPrefixRoleEnum.CUSTOMER_RESIDENTIAL,
    )
    status: Mapped[IPPrefixStatusEnum] = mapped_column(
        Enum(IPPrefixStatusEnum, name="ip_prefix_status_enum", create_type=False),
        nullable=False,
        default=IPPrefixStatusEnum.ACTIVE,
    )
    is_pool: Mapped[bool] = mapped_column(Boolean, default=False)
    default_child_prefix_len: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    utilization_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    vrf: Mapped["IPAMVrf"] = relationship("IPAMVrf", back_populates="prefixes")
    parent: Mapped[Optional["IPAMPrefix"]] = relationship("IPAMPrefix", back_populates="children", remote_side=[id])
    children: Mapped[list["IPAMPrefix"]] = relationship("IPAMPrefix", back_populates="parent", cascade="all, delete-orphan")
    addresses: Mapped[list["IPAMAddress"]] = relationship("IPAMAddress", back_populates="prefix_rel", cascade="all, delete-orphan")


class IPAMAddress(Base):
    __tablename__ = "ipam_ip_addresses"
    __table_args__ = (
        UniqueConstraint("prefix_id", "address", name="uq_ipam_addresses_prefix_addr"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    prefix_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ipam_prefixes.id", ondelete="CASCADE"), nullable=False)
    address: Mapped[str] = mapped_column(INET, nullable=False)
    ip_family: Mapped[IPFamilyEnum] = mapped_column(
        Enum(IPFamilyEnum, name="ip_family_enum", create_type=False),
        nullable=False,
    )
    status: Mapped[IPAddressStatusEnum] = mapped_column(
        Enum(IPAddressStatusEnum, name="ip_address_status_enum", create_type=False),
        nullable=False,
        default=IPAddressStatusEnum.ALLOCATED,
    )
    router_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("routers.id", ondelete="SET NULL"), nullable=True)
    interface_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    dns_ptr: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    soft_lock_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    prefix_rel: Mapped["IPAMPrefix"] = relationship("IPAMPrefix", back_populates="addresses")


class SubscriberDeviceStatusEnum(str, enum.Enum):
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    ISOLATED_ADMINISTRATIVE = "ISOLATED_ADMINISTRATIVE"
    SUSPENDED_TECHNICAL = "SUSPENDED_TECHNICAL"
    DECOMMISSIONED = "DECOMMISSIONED"


class BandwidthProfile(Base):
    __tablename__ = "bandwidth_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_bandwidth_profiles_tenant_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    rate_down_kbps: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_up_kbps: Mapped[int] = mapped_column(Integer, nullable=False)
    burst_down_kbps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    burst_up_kbps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    burst_threshold_down_kbps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    burst_threshold_up_kbps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    burst_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=8)
    queue_type: Mapped[str] = mapped_column(String(64), nullable=False, default="pcq-download-default")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    subscriber_devices: Mapped[list["SubscriberDevice"]] = relationship("SubscriberDevice", back_populates="bandwidth_profile")


class SubscriberDevice(Base):
    __tablename__ = "subscriber_devices"
    __table_args__ = (
        UniqueConstraint("router_id", "endpoint_identifier", name="uq_subscriber_devices_router_endpoint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    router_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routers.id", ondelete="RESTRICT"), nullable=False)
    service_type: Mapped[CustomerServiceTypeEnum] = mapped_column(
        Enum(CustomerServiceTypeEnum, name="customer_service_type_enum", create_type=False),
        nullable=False,
        default=CustomerServiceTypeEnum.PPPOE,
    )
    auth_backend: Mapped[AuthBackendEnum] = mapped_column(
        Enum(AuthBackendEnum, name="auth_backend_enum", create_type=False),
        nullable=False,
        default=AuthBackendEnum.LOCAL_SECRET,
    )
    endpoint_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pppoe_password_vault_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    ipv4_address_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ipam_ip_addresses.id", ondelete="SET NULL"), nullable=True)
    ipv6_delegated_prefix: Mapped[Optional[str]] = mapped_column(CIDR, nullable=True)
    bandwidth_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("bandwidth_profiles.id", ondelete="SET NULL"), nullable=True)
    onu_mode: Mapped[ONUModeEnum] = mapped_column(
        Enum(ONUModeEnum, name="onu_mode_enum", create_type=False),
        nullable=False,
        default=ONUModeEnum.ROUTER,
    )
    onu_mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    device_serial: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cpe_wifi_mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    pon_port: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    optical_box: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_reachability_status: Mapped[str] = mapped_column(String(20), default="ONLINE")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_ACTIVATION")
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    ipv4_address: Mapped[Optional["IPAMAddress"]] = relationship("IPAMAddress")
    bandwidth_profile: Mapped[Optional["BandwidthProfile"]] = relationship("BandwidthProfile", back_populates="subscriber_devices")
    field_orders: Mapped[list["FieldInstallationOrder"]] = relationship("FieldInstallationOrder", back_populates="subscriber_device", cascade="all, delete-orphan")

    @property
    def pppoe_username(self) -> Optional[str]:
        return self.endpoint_identifier

    @pppoe_username.setter
    def pppoe_username(self, val: Optional[str]) -> None:
        self.endpoint_identifier = val

    @property
    def onu_serial_number(self) -> Optional[str]:
        return self.device_serial

    @onu_serial_number.setter
    def onu_serial_number(self, val: Optional[str]) -> None:
        self.device_serial = val


CustomerService = SubscriberDevice


class FieldInstallationOrder(Base):
    __tablename__ = "field_installation_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subscriber_devices.id", ondelete="CASCADE"), nullable=False)
    assigned_tech_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[FieldOrderStatusEnum] = mapped_column(
        Enum(FieldOrderStatusEnum, name="field_order_status_enum", create_type=False),
        nullable=False,
        default=FieldOrderStatusEnum.ASSIGNED,
    )
    onu_scanned_serial: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    onu_scanned_mac: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    detected_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ping_avg_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    ping_loss_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    traffic_rx_kbps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    traffic_tx_kbps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    tech_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    tech_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)

    subscriber_device: Mapped["SubscriberDevice"] = relationship("SubscriberDevice", back_populates="field_orders")

    @property
    def customer_service(self) -> "SubscriberDevice":
        return self.subscriber_device


class FiberCutIncident(Base):
    __tablename__ = "fiber_cut_incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    router_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routers.id", ondelete="RESTRICT"), nullable=False)
    pon_port: Mapped[str] = mapped_column(String(64), nullable=False)
    optical_box: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    affected_onus_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[FiberCutStatusEnum] = mapped_column(
        Enum(FiberCutStatusEnum, name="fiber_cut_status_enum", create_type=False),
        nullable=False,
        default=FiberCutStatusEnum.DETECTED,
    )
    incident_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.now)
