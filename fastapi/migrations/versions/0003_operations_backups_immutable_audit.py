# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0003_operations_backups_immutable_audit

Revision ID: 0003_operations
Revises: 0002_inventory
Create Date: 2026-10-14 20:32:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_operations"
down_revision: str | None = "0002_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ENUMs
    approval_status_enum = postgresql.ENUM(
        "PENDING",
        "APPROVED_AND_EXECUTED",
        "APPROVED_EXECUTION_FAILED",
        "REJECTED",
        "EXPIRED",
        "CANCELLED_BY_REQUESTER",
        name="approval_status_enum",
        create_type=False,
    )
    critical_action_type_enum = postgresql.ENUM(
        "ROUTER_REBOOT_OR_SHUTDOWN",
        "BULK_MULTI_ROUTER_EXECUTION",
        "ROUTING_BGP_OSPF_DEFAULT_CHANGE",
        "FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE",
        "WAN_TRUNK_INTERFACE_OR_IP_CHANGE",
        "BACKUP_RESTORE_OR_CUSTOM_SCRIPT",
        "ROUTER_INTERNAL_USER_CHANGE",
        name="critical_action_type_enum",
        create_type=False,
    )
    bulk_job_status_enum = postgresql.ENUM(
        "QUEUED",
        "AWAITING_APPROVAL",
        "RUNNING",
        "COMPLETED",
        "PARTIAL_FAILURE",
        "FAILED",
        "CANCELLED",
        name="bulk_job_status_enum",
        create_type=False,
    )
    alert_channel_type_enum = postgresql.ENUM(
        "TELEGRAM_BOT", "SMTP_EMAIL", "GENERIC_WEBHOOK", name="alert_channel_type_enum", create_type=False
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)
    critical_action_type_enum.create(op.get_bind(), checkfirst=True)
    bulk_job_status_enum.create(op.get_bind(), checkfirst=True)
    alert_channel_type_enum.create(op.get_bind(), checkfirst=True)

    # 2. Table: approval_requests
    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("action_type", critical_action_type_enum, nullable=False),
        sa.Column("status", approval_status_enum, nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("summary", sa.String(255), nullable=False),
        sa.Column("requester_justification", sa.Text(), nullable=False),
        sa.Column("ros_rest_method", sa.String(10), nullable=False),
        sa.Column("ros_rest_path", sa.String(255), nullable=False),
        sa.Column(
            "request_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("previous_state_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
        ),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("reviewed_by IS NULL OR requested_by <> reviewed_by", name="chk_maker_not_checker"),
    )
    op.create_index("idx_approvals_tenant_status", "approval_requests", ["tenant_id", "status"])

    # 3. Table: router_backups
    op.create_table(
        "router_backups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("backup_type", sa.String(20), nullable=False, server_default=sa.text("'AUTOMATIC_NIGHTLY'")),
        sa.Column("ros_version_at_backup", sa.String(64), nullable=False),
        sa.Column("rsc_sha256_hash", sa.CHAR(64), nullable=False),
        sa.Column("rsc_size_bytes", sa.Integer(), nullable=False),
        sa.Column("rsc_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("rsc_iv", sa.LargeBinary(), nullable=False),
        sa.Column("rsc_tag", sa.LargeBinary(), nullable=False),
        sa.Column("diff_lines_added", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("diff_lines_removed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "parent_backup_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("router_backups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("binary_backup_file_path", sa.String(512), nullable=True),
        sa.Column("binary_backup_sha256", sa.CHAR(64), nullable=True),
        sa.Column("binary_backup_size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column(
            "last_verified_identical_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("(NOW() + INTERVAL '30 days')"),
        ),
        sa.CheckConstraint("octet_length(rsc_iv) = 12", name="chk_rsc_iv"),
        sa.CheckConstraint("octet_length(rsc_tag) = 16", name="chk_rsc_tag"),
    )
    op.create_index("idx_backups_router_created", "router_backups", ["tenant_id", "router_id", "created_at"])
    op.create_index("idx_backups_expiration", "router_backups", ["expires_at"])

    # 4. Table: config_templates
    op.create_table(
        "config_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "variables_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("rest_steps_template", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requires_safemode", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_template_tenant_name"),
    )

    # 5. Table: bulk_jobs
    op.create_table(
        "bulk_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("status", bulk_job_status_enum, nullable=False, server_default=sa.text("'QUEUED'")),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("config_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "execution_parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("target_router_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total_routers", sa.Integer(), nullable=False),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "approval_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("approval_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # 6. Table: bulk_job_items
    op.create_table(
        "bulk_job_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "bulk_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bulk_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("response_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_bulk_items_job", "bulk_job_items", ["tenant_id", "bulk_job_id"])

    # 7. Table: notification_channels
    op.create_table(
        "notification_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("channel_type", alert_channel_type_enum, nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("config_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("config_iv", sa.LargeBinary(), nullable=False),
        sa.Column("config_tag", sa.LargeBinary(), nullable=False),
        sa.Column(
            "subscribed_events",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text('\'["ROUTER_DOWN", "ROUTER_UP", "SSL_MISMATCH", "APPROVAL_NEEDED"]\'::jsonb'),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("octet_length(config_iv) = 12", name="chk_notif_iv"),
        sa.CheckConstraint("octet_length(config_tag) = 16", name="chk_notif_tag"),
    )

    # 8. Table: audit_logs (Inmutable WORM)
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_username", sa.String(64), nullable=False),
        sa.Column("actor_role", postgresql.ENUM(name="system_role_enum", create_type=False), nullable=False),
        sa.Column("actor_ip", postgresql.INET(), nullable=False),
        sa.Column("actor_user_agent", sa.String(512), nullable=True),
        sa.Column("event_category", sa.String(64), nullable=False),
        sa.Column("event_action", sa.String(128), nullable=False),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("router_display_name", sa.String(120), nullable=True),
        sa.Column("ros_rest_method", sa.String(10), nullable=True),
        sa.Column("ros_rest_endpoint", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(64), nullable=True),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.SmallInteger(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prev_record_hash", sa.CHAR(64), nullable=False),
        sa.Column("record_sha256_hash", sa.CHAR(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_audit_tenant_created", "audit_logs", ["tenant_id", "created_at"])
    op.create_index("idx_audit_tenant_actor", "audit_logs", ["tenant_id", "actor_user_id"])
    op.create_index("idx_audit_tenant_category", "audit_logs", ["tenant_id", "event_category"])
    op.create_index(
        "ix_audit_logs_created_at_brin",
        "audit_logs",
        ["created_at"],
        postgresql_using="brin",
    )

    # 9. Function & Trigger WORM para audit_logs
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'VIOLACIÓN DE SEGURIDAD (RoSGrid WORM): La tabla audit_logs es estrictamente inmutable. Operaciones % están prohibidas.', TG_OP
                USING ERRCODE = '42501';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_immutable_audit_logs
        BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_logs
        FOR EACH STATEMENT
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)

    # 10. RLS
    for table_name in (
        "approval_requests",
        "router_backups",
        "config_templates",
        "bulk_jobs",
        "bulk_job_items",
        "notification_channels",
    ):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table_name} ON {table_name}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
        """)

    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_audit ON audit_logs
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_immutable_audit_logs ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification();")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_audit ON audit_logs;")
    for table_name in (
        "notification_channels",
        "bulk_job_items",
        "bulk_jobs",
        "config_templates",
        "router_backups",
        "approval_requests",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")

    op.drop_table("audit_logs")
    op.drop_table("notification_channels")
    op.drop_table("bulk_job_items")
    op.drop_table("bulk_jobs")
    op.drop_table("config_templates")
    op.drop_table("router_backups")
    op.drop_table("approval_requests")
    op.execute("DROP TYPE IF EXISTS alert_channel_type_enum;")
    op.execute("DROP TYPE IF EXISTS bulk_job_status_enum;")
    op.execute("DROP TYPE IF EXISTS critical_action_type_enum;")
    op.execute("DROP TYPE IF EXISTS approval_status_enum;")
