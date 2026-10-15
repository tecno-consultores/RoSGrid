# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0001_core_tenants_users_rls

Revision ID: 0001_core
Revises:
Create Date: 2026-10-14 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ENUMs
    tenant_status_enum = postgresql.ENUM(
        "ACTIVE", "SUSPENDED", "MAINTENANCE", name="tenant_status_enum", create_type=False
    )
    system_role_enum = postgresql.ENUM(
        "SUPERADMIN_GLOBAL",
        "TENANT_ADMIN",
        "SUPERVISOR",
        "SUPPORT_L3",
        "SUPPORT_L2",
        "SUPPORT_L1",
        "FIELD_TECH",
        "INVENTORY_MANAGER",
        "AUDITOR",
        "NOC_MONITOR",
        "SERVICE_ACCOUNT",
        name="system_role_enum",
        create_type=False,
    )
    tenant_status_enum.create(op.get_bind(), checkfirst=True)
    system_role_enum.create(op.get_bind(), checkfirst=True)

    # 2. Table: tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("tax_id", sa.String(64), nullable=True),
        sa.Column("status", tenant_status_enum, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("max_routers_quota", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("max_users_quota", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("require_2fa_all_users", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("default_safemode_seconds", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'", name="chk_tenant_slug_format"),
        sa.CheckConstraint("max_routers_quota > 0", name="chk_max_routers_positive"),
        sa.CheckConstraint("max_users_quota > 0", name="chk_max_users_positive"),
        sa.CheckConstraint("default_safemode_seconds BETWEEN 15 AND 300", name="chk_safemode_range"),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"])
    op.create_index("idx_tenants_status", "tenants", ["status"])

    # 3. Table: users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", system_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("failed_login_attempts", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("totp_secret_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("totp_secret_iv", sa.LargeBinary(), nullable=True),
        sa.Column("totp_secret_tag", sa.LargeBinary(), nullable=True),
        sa.Column(
            "totp_recovery_codes_hashes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "allowed_cidr_list",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("has_all_routers_access", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_ip", postgresql.INET(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        sa.UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
    )
    op.create_index("idx_users_tenant_id", "users", ["tenant_id"])
    op.create_index("idx_users_tenant_role", "users", ["tenant_id", "role"])

    # 4. Table: user_router_permissions
    op.create_table(
        "user_router_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("can_write_layer1", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("can_write_layer2", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("can_execute_diagnostics", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("can_trigger_backup", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("can_reboot", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("bypass_maker_checker", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column(
            "assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "user_id", "router_id", name="uq_user_router_perm"),
    )
    op.create_index("idx_urp_tenant_user", "user_router_permissions", ["tenant_id", "user_id"])
    op.create_index("idx_urp_tenant_router", "user_router_permissions", ["tenant_id", "router_id"])

    # 5. Row-Level Security
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_users ON users
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)

    op.execute("ALTER TABLE user_router_permissions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_router_permissions FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_urp ON user_router_permissions
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_urp ON user_router_permissions;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users;")
    op.drop_table("user_router_permissions")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS system_role_enum;")
    op.execute("DROP TYPE IF EXISTS tenant_status_enum;")
