# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class TenantStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    MAINTENANCE = "MAINTENANCE"


class SystemRoleEnum(str, enum.Enum):
    SUPERADMIN_GLOBAL = "SUPERADMIN_GLOBAL"
    TENANT_ADMIN = "TENANT_ADMIN"
    SUPERVISOR = "SUPERVISOR"
    SUPPORT_L3 = "SUPPORT_L3"
    SUPPORT_L2 = "SUPPORT_L2"
    SUPPORT_L1 = "SUPPORT_L1"
    FIELD_TECH = "FIELD_TECH"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    AUDITOR = "AUDITOR"
    NOC_MONITOR = "NOC_MONITOR"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[TenantStatusEnum] = mapped_column(
        Enum(TenantStatusEnum, name="tenant_status_enum", create_type=False),
        nullable=False,
        default=TenantStatusEnum.ACTIVE,
        index=True,
    )
    max_routers_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_users_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    require_2fa_all_users: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_safemode_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    
    # Feature Flags & Gobernanza Modular (Specs 32 & 34)
    isp_module_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bgp_looking_glass_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sfp_ddm_telemetry_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ipfix_analytics_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enforce_maker_checker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_safemode_enforced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ai_mcp_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nightly_backups_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    outbound_webhooks_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config_drift_monitoring_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cis_audit_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sdwan_orchestrator_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    capsman_wifi_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sla_tracker_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mass_outage_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    default_locale: Mapped[str] = mapped_column(String(5), nullable=False, default="es")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[SystemRoleEnum] = mapped_column(
        Enum(SystemRoleEnum, name="system_role_enum", create_type=False), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 2FA TOTP
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    totp_secret_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    totp_secret_iv: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    totp_secret_tag: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    totp_recovery_codes_hashes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    allowed_cidr_list: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    has_all_routers_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    router_permissions: Mapped[list["UserRouterPermission"]] = relationship(
        "UserRouterPermission",
        foreign_keys="UserRouterPermission.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserRouterPermission(Base):
    __tablename__ = "user_router_permissions"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", "router_id", name="uq_user_router_perm"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    router_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_write_layer1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_write_layer2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_execute_diagnostics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_trigger_backup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_reboot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bypass_maker_checker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="router_permissions")
