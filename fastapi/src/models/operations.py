# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import enum
import uuid
from datetime import datetime
from typing import Any

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
from sqlalchemy.dialects.postgresql import CHAR, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.core import SystemRoleEnum


class ApprovalStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED_AND_EXECUTED = "APPROVED_AND_EXECUTED"
    APPROVED_EXECUTION_FAILED = "APPROVED_EXECUTION_FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED_BY_REQUESTER = "CANCELLED_BY_REQUESTER"


class CriticalActionTypeEnum(str, enum.Enum):
    ROUTER_REBOOT_OR_SHUTDOWN = "ROUTER_REBOOT_OR_SHUTDOWN"
    BULK_MULTI_ROUTER_EXECUTION = "BULK_MULTI_ROUTER_EXECUTION"
    ROUTING_BGP_OSPF_DEFAULT_CHANGE = "ROUTING_BGP_OSPF_DEFAULT_CHANGE"
    FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE = "FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE"
    WAN_TRUNK_INTERFACE_OR_IP_CHANGE = "WAN_TRUNK_INTERFACE_OR_IP_CHANGE"
    BACKUP_RESTORE_OR_CUSTOM_SCRIPT = "BACKUP_RESTORE_OR_CUSTOM_SCRIPT"
    ROUTER_INTERNAL_USER_CHANGE = "ROUTER_INTERNAL_USER_CHANGE"


class BulkJobStatusEnum(str, enum.Enum):
    QUEUED = "QUEUED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AlertChannelTypeEnum(str, enum.Enum):
    TELEGRAM_BOT = "TELEGRAM_BOT"
    SMTP_EMAIL = "SMTP_EMAIL"
    GENERIC_WEBHOOK = "GENERIC_WEBHOOK"


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    router_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=True
    )

    action_type: Mapped[CriticalActionTypeEnum] = mapped_column(
        Enum(CriticalActionTypeEnum, name="critical_action_type_enum", create_type=False), nullable=False
    )
    status: Mapped[ApprovalStatusEnum] = mapped_column(
        Enum(ApprovalStatusEnum, name="approval_status_enum", create_type=False),
        nullable=False,
        default=ApprovalStatusEnum.PENDING,
        index=True,
    )

    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_justification: Mapped[str] = mapped_column(Text, nullable=False)
    ros_rest_method: Mapped[str] = mapped_column(String(10), nullable=False)
    ros_rest_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    previous_state_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class RouterBackup(Base):
    __tablename__ = "router_backups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    router_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    backup_type: Mapped[str] = mapped_column(String(20), nullable=False, default="AUTOMATIC_NIGHTLY")
    ros_version_at_backup: Mapped[str] = mapped_column(String(64), nullable=False)

    rsc_sha256_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    rsc_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    rsc_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    rsc_iv: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    rsc_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    diff_lines_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    diff_lines_removed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_backup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("router_backups.id", ondelete="SET NULL"), nullable=True
    )

    binary_backup_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    binary_backup_sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    binary_backup_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    last_verified_identical_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("(NOW() + INTERVAL '30 days')")
    )


class ConfigTemplate(Base):
    __tablename__ = "config_templates"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_template_tenant_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    variables_schema: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    rest_steps_template: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    requires_safemode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BulkJob(Base):
    __tablename__ = "bulk_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[BulkJobStatusEnum] = mapped_column(
        Enum(BulkJobStatusEnum, name="bulk_job_status_enum", create_type=False),
        nullable=False,
        default=BulkJobStatusEnum.QUEUED,
    )

    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config_templates.id", ondelete="SET NULL"), nullable=True
    )
    execution_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    target_router_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    total_routers: Mapped[int] = mapped_column(Integer, nullable=False)
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    approval_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BulkJobItem(Base):
    __tablename__ = "bulk_job_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    bulk_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bulk_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    router_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    response_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_type: Mapped[AlertChannelTypeEnum] = mapped_column(
        Enum(AlertChannelTypeEnum, name="alert_channel_type_enum", create_type=False), nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    config_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    config_iv: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    config_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    subscribed_events: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_username: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[SystemRoleEnum] = mapped_column(
        Enum(SystemRoleEnum, name="system_role_enum", create_type=False), nullable=False
    )
    actor_ip: Mapped[str] = mapped_column(INET, nullable=False)
    actor_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    event_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_action: Mapped[str] = mapped_column(String(128), nullable=False)
    router_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id", ondelete="SET NULL"), nullable=True
    )
    router_display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    ros_rest_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ros_rest_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    prev_record_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    record_sha256_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()"), index=True
    )
