# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0002_inventory_vault_maintenance

Revision ID: 0002_inventory
Revises: 0001_core
Create Date: 2026-10-14 20:31:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_inventory"
down_revision: str | None = "0001_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ENUMs
    router_network_role_enum = postgresql.ENUM(
        "CORE",
        "EDGE_BGP",
        "WAN_BALANCER",
        "BRAS_PPPOE",
        "DISTRIBUTION_SWITCH",
        "TOWER_AP",
        "CORPORATE_CPE",
        name="router_network_role_enum",
        create_type=False,
    )
    router_admin_state_enum = postgresql.ENUM(
        "PRODUCTION", "MAINTENANCE", "STAGING_LAB", "RETIRED", name="router_admin_state_enum", create_type=False
    )
    ssl_trust_status_enum = postgresql.ENUM(
        "PENDING_TOFU", "TRUSTED_PINNED", "FINGERPRINT_MISMATCH", name="ssl_trust_status_enum", create_type=False
    )
    router_network_role_enum.create(op.get_bind(), checkfirst=True)
    router_admin_state_enum.create(op.get_bind(), checkfirst=True)
    ssl_trust_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Table: routers
    op.create_table(
        "routers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("api_base_url", sa.String(255), nullable=False),
        sa.Column("api_port", sa.Integer(), nullable=False, server_default=sa.text("443")),
        sa.Column("network_role", router_network_role_enum, nullable=False),
        sa.Column("admin_state", router_admin_state_enum, nullable=False, server_default=sa.text("'PRODUCTION'")),
        sa.Column("physical_location", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("online_since_date", sa.Date(), nullable=False),
        sa.Column("operational_notes", sa.Text(), nullable=True),
        sa.Column("site_contact_info", sa.String(255), nullable=True),
        sa.Column("serial_number", sa.String(64), nullable=False),
        sa.Column("ros_identity", sa.String(128), nullable=True),
        sa.Column("board_name", sa.String(64), nullable=True),
        sa.Column("model_name", sa.String(128), nullable=True),
        sa.Column("architecture_name", sa.String(64), nullable=True),
        sa.Column("ros_version", sa.String(64), nullable=True),
        sa.Column("firmware_version", sa.String(64), nullable=True),
        sa.Column("upgrade_firmware_version", sa.String(64), nullable=True),
        sa.Column("update_available_version", sa.String(64), nullable=True),
        sa.Column("ssl_trust_status", ssl_trust_status_enum, nullable=False, server_default=sa.text("'PENDING_TOFU'")),
        sa.Column("ssl_sha256_fingerprint", sa.CHAR(64), nullable=True),
        sa.Column("ssl_cert_subject", sa.String(255), nullable=True),
        sa.Column("ssl_cert_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ssl_pinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_reachable", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_discovery_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_connection_error", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("api_base_url ~ '^https://[a-zA-Z0-9._-]+(:[0-9]{1,5})?$'", name="chk_api_https_url"),
        sa.CheckConstraint("api_port BETWEEN 1 AND 65535", name="chk_api_port_range"),
        sa.CheckConstraint("latitude IS NULL OR (latitude BETWEEN -90.0 AND 90.0)", name="chk_lat_range"),
        sa.CheckConstraint("longitude IS NULL OR (longitude BETWEEN -180.0 AND 180.0)", name="chk_lng_range"),
        sa.UniqueConstraint("tenant_id", "display_name", name="uq_routers_tenant_name"),
        sa.UniqueConstraint("tenant_id", "api_base_url", name="uq_routers_tenant_url"),
        sa.UniqueConstraint("tenant_id", "serial_number", name="uq_routers_tenant_serial"),
    )
    op.create_index("idx_routers_tenant_role", "routers", ["tenant_id", "network_role"])
    op.create_index("idx_routers_tenant_state", "routers", ["tenant_id", "admin_state"])

    # 3. Foreign key to user_router_permissions
    op.create_foreign_key(
        "fk_urp_router",
        "user_router_permissions",
        "routers",
        ["router_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Table: router_tags
    op.create_table(
        "router_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tag_name", sa.String(48), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("tag_name ~ '^[a-z0-9-]+$'", name="chk_tag_slug"),
        sa.UniqueConstraint("tenant_id", "router_id", "tag_name", name="uq_router_tag"),
    )
    op.create_index("idx_router_tags_lookup", "router_tags", ["tenant_id", "tag_name"])

    # 5. Table: router_credentials_vault
    op.create_table(
        "router_credentials_vault",
        sa.Column(
            "router_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("routers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("api_username", sa.String(64), nullable=False),
        sa.Column("current_password_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("current_password_iv", sa.LargeBinary(), nullable=False),
        sa.Column("current_password_tag", sa.LargeBinary(), nullable=False),
        sa.Column("previous_password_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("previous_password_iv", sa.LargeBinary(), nullable=True),
        sa.Column("previous_password_tag", sa.LargeBinary(), nullable=True),
        sa.Column("auto_rotate_enabled", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("rotation_interval_days", sa.SmallInteger(), nullable=False, server_default=sa.text("30")),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("next_rotation_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rotation_status", sa.String(32), nullable=False, server_default=sa.text("'SUCCESS'")),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("octet_length(current_password_iv) = 12", name="chk_curr_iv_len"),
        sa.CheckConstraint("octet_length(current_password_tag) = 16", name="chk_curr_tag_len"),
        sa.CheckConstraint(
            "previous_password_iv IS NULL OR octet_length(previous_password_iv) = 12", name="chk_prev_iv_len"
        ),
        sa.CheckConstraint(
            "previous_password_tag IS NULL OR octet_length(previous_password_tag) = 16", name="chk_prev_tag_len"
        ),
        sa.CheckConstraint("rotation_interval_days BETWEEN 1 AND 365", name="chk_rotation_days"),
    )

    # 6. Table: maintenance_windows
    op.create_table(
        "maintenance_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("target_tag", sa.String(48), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suppress_alerts", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("ends_at > starts_at", name="chk_window_dates"),
        sa.CheckConstraint("router_id IS NOT NULL OR target_tag IS NOT NULL", name="chk_window_target"),
    )

    # 7. RLS
    op.execute("ALTER TABLE routers ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE routers FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_routers ON routers
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    """)

    op.execute("ALTER TABLE router_tags ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE router_tags FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_router_tags ON router_tags
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    """)

    op.execute("ALTER TABLE router_credentials_vault ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE router_credentials_vault FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_vault ON router_credentials_vault
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)

    op.execute("ALTER TABLE maintenance_windows ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE maintenance_windows FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_maint ON maintenance_windows
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_maint ON maintenance_windows;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_vault ON router_credentials_vault;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_router_tags ON router_tags;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_routers ON routers;")
    op.drop_table("maintenance_windows")
    op.drop_table("router_credentials_vault")
    op.drop_table("router_tags")
    op.drop_constraint("fk_urp_router", "user_router_permissions", type_="foreignkey")
    op.drop_table("routers")
    op.execute("DROP TYPE IF EXISTS ssl_trust_status_enum;")
    op.execute("DROP TYPE IF EXISTS router_admin_state_enum;")
    op.execute("DROP TYPE IF EXISTS router_network_role_enum;")
