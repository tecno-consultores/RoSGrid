# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class RouterNetworkRoleEnum(str, enum.Enum):
    CORE = "CORE"
    EDGE_BGP = "EDGE_BGP"
    WAN_BALANCER = "WAN_BALANCER"
    BRAS_PPPOE = "BRAS_PPPOE"
    DISTRIBUTION_SWITCH = "DISTRIBUTION_SWITCH"
    TOWER_AP = "TOWER_AP"
    CORPORATE_CPE = "CORPORATE_CPE"


class RouterAdminStateEnum(str, enum.Enum):
    PRODUCTION = "PRODUCTION"
    MAINTENANCE = "MAINTENANCE"
    STAGING_LAB = "STAGING_LAB"
    RETIRED = "RETIRED"


class SSLTrustStatusEnum(str, enum.Enum):
    PENDING_TOFU = "PENDING_TOFU"
    TRUSTED_PINNED = "TRUSTED_PINNED"
    FINGERPRINT_MISMATCH = "FINGERPRINT_MISMATCH"


class Router(Base):
    __tablename__ = "routers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "display_name", name="uq_routers_tenant_name"),
        UniqueConstraint("tenant_id", "api_base_url", name="uq_routers_tenant_url"),
        UniqueConstraint("tenant_id", "serial_number", name="uq_routers_tenant_serial"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    api_base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    api_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    network_role: Mapped[RouterNetworkRoleEnum] = mapped_column(
        Enum(RouterNetworkRoleEnum, name="router_network_role_enum", create_type=False), nullable=False
    )
    admin_state: Mapped[RouterAdminStateEnum] = mapped_column(
        Enum(RouterAdminStateEnum, name="router_admin_state_enum", create_type=False),
        nullable=False,
        default=RouterAdminStateEnum.PRODUCTION,
    )
    physical_location: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    online_since_date: Mapped[date] = mapped_column(Date, nullable=False)
    operational_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    site_contact_info: Mapped[str | None] = mapped_column(String(255), nullable=True)

    serial_number: Mapped[str] = mapped_column(String(64), nullable=False)
    ros_identity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    board_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    architecture_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ros_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    upgrade_firmware_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_available_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    ssl_trust_status: Mapped[SSLTrustStatusEnum] = mapped_column(
        Enum(SSLTrustStatusEnum, name="ssl_trust_status_enum", create_type=False),
        nullable=False,
        default=SSLTrustStatusEnum.PENDING_TOFU,
    )
    ssl_sha256_fingerprint: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    ssl_cert_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ssl_cert_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ssl_pinned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_reachable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_discovery_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_connection_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    tags: Mapped[list["RouterTag"]] = relationship("RouterTag", back_populates="router", cascade="all, delete-orphan")
    vault: Mapped[Optional["RouterCredentialsVault"]] = relationship(
        "RouterCredentialsVault", back_populates="router", uselist=False, cascade="all, delete-orphan"
    )


class RouterTag(Base):
    __tablename__ = "router_tags"
    __table_args__ = (UniqueConstraint("tenant_id", "router_id", "tag_name", name="uq_router_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    router_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
    )
    tag_name: Mapped[str] = mapped_column(String(48), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    router: Mapped["Router"] = relationship("Router", back_populates="tags")


class RouterCredentialsVault(Base):
    __tablename__ = "router_credentials_vault"

    router_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    api_username: Mapped[str] = mapped_column(String(64), nullable=False)

    current_password_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    current_password_iv: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    current_password_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    previous_password_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    previous_password_iv: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    previous_password_tag: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    auto_rotate_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rotation_interval_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=30)
    last_rotated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    next_rotation_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_rotation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    router: Mapped["Router"] = relationship("Router", back_populates="vault")


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    router_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=True
    )
    target_tag: Mapped[str | None] = mapped_column(String(48), nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suppress_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
